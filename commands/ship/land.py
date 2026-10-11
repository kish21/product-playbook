#!/usr/bin/env python3
"""land.py - /ship's last step: merge the PR, or hand it to a reviewer, and the post-merge steps - each read back.

A logged /ship opened its PR and stopped: the issue stayed open, the board card stayed at Todo and the local folder
never moved to the merged main, because those steps were commands in the close that a new user does not know to run.
The user answers ONE question (merge now / leave it for review); this script does the rest and reads every part back.

Usage:  python land.py merge  --pr <n> [--method merge|squash|rebase]   CI green -> merge, then `after`
        python land.py review --pr <n> --seat <SR2>                     CI green -> card In Review, the reviewer named
        python land.py after  --pr <n>                                  a merged PR: issue CLOSED, card Done, the local
                                                                        folder on the updated base branch, its area
                                                                        rule files rewritten when the merge moved them
Exit:   0 every step read back OK · 1 a step or a read-back failed · 2 refused before changing anything
`--method merge` is the default: it keeps the branch's commits, which the ticket rows cite, in the base branch's
history (a squash gives them new ids). Portable: stdlib + the `gh` and `git` CLIs. Never merges unless asked to by
`merge` - the user's answer to the question is that word.
"""
import importlib.util, json, subprocess, sys
from pathlib import Path

FAILED = {"FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE", "ERROR"}
PASSED = {"SUCCESS", "NEUTRAL", "SKIPPED"}


def board_module():
    """The shared card mover (tools/board.py): beside the skills on a plugin or clone, in the companions folder
    (product-playbook/board.py) on a copy install. /build moves cards with the same module."""
    here = Path(__file__).resolve().parent
    for f in (here.parent.parent / "tools" / "board.py", here.parent.parent / "product-playbook" / "board.py",
              here / "board.py"):
        if f.is_file():
            spec = importlib.util.spec_from_file_location("playbook_board", f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    return None


def status_script():
    """The playbook's status.py, found as board_module() finds board.py: tools/ on a plugin or clone, the companions
    folder on a copy install (which keeps TOOL, the tool it serves, beside it)."""
    here = Path(__file__).resolve().parent
    for f in (here.parent.parent / "tools" / "status.py", here.parent.parent / "product-playbook" / "status.py"):
        if f.is_file():
            return f
    return None


class Refused(Exception):
    """Nothing was changed."""


def real_run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout, p.stderr


class Land:
    """Every gh and git call goes through `run`, so a test puts a fake behind it."""

    def __init__(self, run=real_run, log=print):
        self.run, self.log, self.bad = run, log, 0

    def ok(self, what, line):
        self.log(f"OK   {what}: {line}")

    def fail(self, what, line):
        self.bad += 1
        self.log(f"FAIL {what}: {line}")

    def gh_json(self, *args):
        code, out, err = self.run(["gh", *args])
        if code != 0:
            raise RuntimeError(f"gh {' '.join(args[:3])} failed: {(err or out).strip()[:300]}")
        return json.loads(out) if out.strip() else None

    def git(self, *args):
        code, out, err = self.run(["git", *args])
        return code, (out or "").strip(), (err or "").strip()

    # --- the PR ---
    def pr(self, n):
        try:
            return self.gh_json("pr", "view", str(n), "--json", "number,state,url,headRefName,headRefOid,baseRefName,"
                                "closingIssuesReferences,statusCheckRollup,mergeCommit")
        except RuntimeError as e:
            raise Refused(f"PR #{n} could not be read - {e}") from None

    @staticmethod
    def ci(pr):
        """green / pending / failed / none, and the names of the checks that are not green."""
        checks = pr.get("statusCheckRollup") or []
        if not checks:
            return "none", []
        failed = [c.get("name") or c.get("context") for c in checks
                  if (c.get("conclusion") or c.get("state") or "").upper() in FAILED]
        pending = [c.get("name") or c.get("context") for c in checks
                   if (c.get("status") and c.get("status").upper() != "COMPLETED")
                   or (c.get("state") or "").upper() in ("PENDING", "EXPECTED")]
        if failed:
            return "failed", failed
        if pending:
            return "pending", pending
        return "green", []

    def ready(self, pr):
        if pr.get("state") != "OPEN":
            raise Refused(f"PR #{pr['number']} is {pr.get('state')}, not open")
        state, names = self.ci(pr)
        if state == "failed":
            raise Refused(f"CI failed on PR #{pr['number']}: {', '.join(names)} - fix it on the branch (the PR "
                          f"updates), then run this again")
        if state == "pending":
            raise Refused(f"CI is still running on PR #{pr['number']} ({', '.join(names[:5])}) - wait with `gh pr "
                          f"checks {pr['number']} --watch`, then run this again")
        self.ok("CI", "green" if state == "green" else "no CI checks on this PR - nothing to wait for")

    # --- the board card ---
    def repo(self):
        code, out, _ = self.run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
        if code != 0 or "/" not in out:
            raise RuntimeError("no GitHub repository for this folder")
        return out.strip().split("/", 1)

    def move(self, issue, want, fallback_ok=False):
        """Set every board card of the issue to `want` (never backwards) and read it back - tools/board.py."""
        board = board_module()
        if board is None:
            self.fail(f"card #{issue}", f"board.py is not installed - move the card to {want} by hand")
            return
        try:
            repo = "/".join(self.repo())
        except RuntimeError as e:
            self.fail(f"card #{issue}", f"the board could not be read ({e})")
            return
        for kind, line in board.move_issue(issue, want, repo, board.graphql_via(self.run), missing_option_ok=fallback_ok):
            what, text = line.split(": ", 1)
            self.ok(what, text) if kind == "OK" else self.fail(what, text) if kind == "FAIL" else self.log(f"NOTE {line}")

    # --- the steps ---
    def carried(self, pr):
        """2.4: `status.py release` commits the release row after the PR opened; a merge without it leaves the merged
        base with no release record. Local commits on the PR's branch that its head lacks -> refuse."""
        head, branch = pr.get("headRefOid") or "", pr.get("headRefName") or ""
        code, out, _ = self.git("rev-list", "--count", f"{head}..refs/heads/{branch}") if head and branch else (1, "", "")
        if code == 0 and out.isdigit() and int(out):
            raise Refused(f"PR #{pr['number']} lacks {out} commit(s) on your local {branch} (the release row?) - "
                          f"`git push origin {branch}`, wait for its CI, then run this again")

    def merge(self, n, method="merge"):
        pr = self.pr(n)
        self.carried(pr)
        self.ready(pr)
        code, out, err = self.run(["gh", "pr", "merge", str(n), f"--{method}"])
        if code != 0:
            self.fail("merge", (err or out).strip()[:300])
            return self.bad
        self.ok("merge", f"PR #{n} merged ({method})")
        return self.after(n)

    def review(self, n, seat):
        pr = self.pr(n)
        self.ready(pr)
        issues = [i["number"] for i in pr.get("closingIssuesReferences") or []]
        for i in issues:
            self.move(i, "In Review", fallback_ok=True)
        code, out, err = self.run(["gh", "pr", "comment", str(n), "--body",
                                   f"Ready for review by seat {seat}. Merge when approved; the next /build or /ship "
                                   f"run does the post-merge steps."])
        (self.ok("reviewer", f"seat {seat} named on PR #{n}") if code == 0
         else self.fail("reviewer", (err or out).strip()[:300]))
        if not issues:
            self.log(f"NOTE PR #{n} closes no issue (no `Closes #N` in its body) - no card to move")
        return self.bad

    def after(self, n):
        pr = self.pr(n)
        if pr.get("state") != "MERGED":
            self.fail("merged", f"PR #{n} is {pr.get('state')} - nothing to do until it merges")
            return self.bad
        sha = ((pr.get("mergeCommit") or {}).get("oid") or "")[:9]
        issues = [i["number"] for i in pr.get("closingIssuesReferences") or []]
        if not issues:
            self.log(f"NOTE PR #{n} closes no issue (no `Closes #N` in its body) - no issue or card to check")
        for i in issues:
            state = (self.gh_json("issue", "view", str(i), "--json", "state") or {}).get("state")
            if state != "CLOSED":  # a merge closes nothing on its own when the keyword missed (it fails silently)
                self.run(["gh", "issue", "close", str(i), "--comment", f"Shipped in #{n} ({sha})."])
                state = (self.gh_json("issue", "view", str(i), "--json", "state") or {}).get("state")
            (self.ok(f"issue #{i}", "CLOSED") if state == "CLOSED" else self.fail(f"issue #{i}", f"reads {state}"))
            self.move(i, "Done")
        before = self.bad
        self.local(pr["baseRefName"], sha)
        if self.bad == before:
            self.area_rules(pr["baseRefName"])
        return self.bad

    def area_rules(self, base):
        """2.4 review: a ticket that adds a STRUCTURE.md module line leaves the per-folder area rule files behind the
        records, and only /tickets wrote them - rarely re-run. On the merged base: a project that has them gets them
        rewritten (left uncommitted: the next ticket's first save carries them); a project with none gets none."""
        script = status_script()
        tool_file = script.parent / "TOOL" if script else None
        tool = tool_file.read_text(encoding="utf-8").strip().lower() if tool_file and tool_file.is_file() else "claude"
        if not script or tool not in ("claude", "codex", "cursor"):
            return
        code, out, _ = self.run([sys.executable, str(script), "area-rules", "--check", "--tool", tool])
        states = [ln.split()[:2] for ln in out.splitlines()[1:] if ln.strip()]
        stale = [f.rstrip(":") for st, f in states if st in ("drift", "missing")]
        if code != 1 or not stale or not any(st in ("ok", "drift") for st, _ in states):
            return  # in step, or this project never had area rule files
        code, out, err = self.run([sys.executable, str(script), "area-rules", "--write", "--tool", tool])
        if code != 0:
            self.fail("area rules", f"rewrite failed: {(err or out).strip()[:200]}")
            return
        self.ok("area rules", f"{len(stale)} file(s) rewritten to match the merged STRUCTURE.md and records on {base} "
                              f"({', '.join(stale[:4])}) - uncommitted: the next ticket's first save carries them")

    def local(self, base, sha):
        _, dirty, _ = self.git("status", "--porcelain", "--untracked-files=no")
        if dirty:
            self.fail("local folder", f"uncommitted changes - not switched to {base}; commit or stash them, then run "
                                      f"`land.py after` again")
            return
        for args in (("fetch", "origin", base), ("switch", base), ("pull", "--ff-only", "origin", base)):
            code, out, err = self.git(*args)
            if code != 0:
                self.fail("local folder", f"git {' '.join(args)} failed: {(err or out)[:200]}")
                return
        _, head, _ = self.git("rev-parse", "HEAD")
        _, remote, _ = self.git("rev-parse", f"origin/{base}")
        code = self.git("merge-base", "--is-ancestor", sha, "HEAD")[0] if sha else 0
        if head and head == remote and code == 0:
            self.ok("local folder", f"on {base} @ {head[:9]}, the same as origin/{base}, with the merge in it")
        else:
            self.fail("local folder", f"HEAD {head[:9]} is not origin/{base} {remote[:9]} with the merge {sha}")


def main(argv, run=real_run, log=print):
    cmd = argv[0] if argv else ""
    opts = dict(zip(argv[1::2], argv[2::2]))
    n = opts.get("--pr", "").lstrip("#")
    if cmd not in ("merge", "review", "after") or not n.isdigit() or (cmd == "review" and not opts.get("--seat")):
        log(__doc__)
        return 2
    method = opts.get("--method", "merge")
    if method not in ("merge", "squash", "rebase"):
        log("--method is merge, squash or rebase")
        return 2
    land = Land(run, log)
    try:
        bad = (land.merge(n, method) if cmd == "merge" else land.review(n, opts["--seat"]) if cmd == "review"
               else land.after(n))
    except Refused as e:
        log(f"REFUSED - nothing changed: {e}")
        return 2
    except RuntimeError as e:
        log(f"FAIL {e}")
        return 1
    log("all read back OK" if not bad else f"{bad} step(s) failed - say each to the user in the close")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
