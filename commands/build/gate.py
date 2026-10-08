"""gate.py - every check a build step needs, in ONE call, printing only what the next step needs.

A logged build spent ~40 of its 120 model calls running one check per call (tests, then lint, then types, then the
structure check), each call re-sending a 200k-token conversation to read one exit code. This runs them all:

    python gate.py "just lint" "uv run pytest app/shops/tests -q" "python scripts/check_structure.py"

For each command, in order: PASS or FAIL with its exit code and seconds, the result line a record quotes
(`86 passed in 24.2s`), and for a FAIL the lines that say what failed (FAILED / ERROR / error: / the end of a
traceback) - never the whole output. The whole output goes to a log file inside .git (never committed, one per
checkout), named on the last line, for the rare case that needs more.

    python gate.py --ticket M1-X-01            (the project's check recipe + the ticket's Verification Command)
    python gate.py --fresh "<cmd>"             (run again even when these exact files already passed)
    python gate.py --ticket M1-X-01 --close    (the close gate: the same, then - on a pass - the close's order + rules)

Every command runs even after a failure, so one call shows the whole picture; --stop stops at the first failure.
A run records the exact files it checked (a git tree of the working tree, committed or not), so a pass still counts
after the commit that follows it, and the same commands over the same files are reused, never run twice.
Exit 0 = every command passed, 1 = one failed, 2 = no command given.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

RESULT = re.compile(r"(\d+ (?:passed|failed|errors?)\b.*?\bin [\d.]+s|Found \d+ errors?.*|Success: .*|All checks passed!?"
                    r"|\d+ files? (?:already formatted|would be reformatted|reformatted).*|No new upgrade operations.*"
                    r"|Tests?:?\s+\d+ (?:passed|failed).*|^OK\b.*|^FAIL\b.*)", re.M)
FAILED = re.compile(r"^(FAILED|ERROR|E\s{2,}|.*\berror\b:|.*Error:|.*\bFAIL\b|\s*File \".*\", line \d+|.*assert )", re.I)
EXCERPT = 25


def log_dir() -> Path:
    r = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True)
    base = Path(r.stdout.strip()) if r.returncode == 0 else Path(".")
    d = base / "playbook-gate"
    d.mkdir(parents=True, exist_ok=True)
    return d


def excerpt(out: str) -> list[str]:
    lines = out.splitlines()
    hits = [ln for ln in lines if FAILED.match(ln)]
    picked = hits[-EXCERPT:] if hits else lines[-EXCERPT:]
    return [ln[:240] for ln in picked]


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    stop, close, only, fresh = "--stop" in argv, "--close" in argv, "--only" in argv, "--fresh" in argv
    ticket = argv[argv.index("--ticket") + 1] if "--ticket" in argv and argv.index("--ticket") + 1 < len(argv) else ""
    cmds = [a for i, a in enumerate(argv) if a not in ("--stop", "--close", "--ticket", "--only", "--fresh")
            and not (i and argv[i - 1] == "--ticket")]
    ticket_cmds: list[str] = []
    if ticket and not only:  # the project's recipe + the ticket's own verification, THEN any named extra commands -
        # named commands add to the automatic checks, never replace them (an extra secret scan once dropped the
        # recipe and the ticket's tests silently); `--only` replaces, and says so
        recipe, ticket_cmds = ticket_commands(ticket)
        cmds = recipe + ticket_cmds + [c for c in cmds if c not in recipe + ticket_cmds]
        if not cmds:
            print(f"gate: no check recipe (justfile / Makefile / package.json `check`) and no Verification Command "
                  f"in {ticket}'s file - name the commands: gate.py \"<cmd>\" ...")
            return 2
        print("gate: " + " · ".join(cmds))
        if not ticket_cmds:
            print(f"! UNVERIFIED: {ticket}'s file names no Verification Command, so this gate does not check the "
                  f"ticket's own behaviour - a `--dod yes` row is refused; `--dod partial`, or add the command")
    elif only:
        print("gate: --only - the named commands replace the project's recipe and the ticket's command")
    if close and not ticket:
        print("gate: --close needs --ticket <id> (the close gate runs the project's recipe and the ticket's tests)")
        return 2
    if not cmds:
        print(__doc__.strip().splitlines()[0])
        print('usage: python gate.py [--stop] "<command>" ["<command>" ...]\n'
              '       python gate.py --ticket <id> [--close]   (the recipe + the ticket\'s tests; --close: the close gate)')
        return 2
    folder = log_dir()
    tree = worktree_tree(folder)  # the files this run checks - taken BEFORE the commands, which may write files
    if not fresh:  # a passing gate is reused when nothing a check reads has changed since - never a second full
        # suite over identical files (a logged /test ran `just check` 4 times: before and after each commit);
        # any code, config, test or DESIGN.md change (committed, uncommitted or new) runs it
        prior = reusable_run(folder, cmds, ticket, tree)
        if prior:
            print(f"gate: REUSED the passing run at {prior['head'][:9]} ({prior.get('date', '?')}) - the same "
                  f"commands, and only docs/status changed since: {' · '.join(cmds)}\nGATE PASS (reused; --fresh "
                  f"runs it again)")
            record(folder, cmds, True, ticket, ticket_cmds, reused=prior["head"], tree=tree)
            if close:
                print_close_rules()
            return 0
    stamp = time.strftime("%H%M%S")
    failed = 0
    for n, cmd in enumerate(cmds, 1):
        t0 = time.time()
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        secs = time.time() - t0
        out = (r.stdout or "") + (r.stderr or "")
        log = folder / f"{stamp}-{n}.log"
        log.write_text(f"$ {cmd}\n(exit {r.returncode}, {secs:.1f}s)\n\n{out}", encoding="utf-8")
        results = [m.group(0).strip() for m in RESULT.finditer(out)]
        head = "PASS" if r.returncode == 0 else f"FAIL (exit {r.returncode})"
        print(f"{head:15} {secs:6.1f}s  {cmd}")
        if results:
            print(f"                result: {results[-1][:200]}")
        if r.returncode != 0:
            failed += 1
            for ln in excerpt(out):
                print(f"                | {ln}")
            if stop:
                break
    print(f"{'GATE PASS' if not failed else f'GATE FAIL - {failed} of {len(cmds)} failed'} · full output: {folder}/{stamp}-*.log")
    record(folder, cmds, not failed, ticket, ticket_cmds, tree=tree)
    if close and not failed:  # the close starts here: its order and rules arrive now, not at the start of the run
        print_close_rules()
    return 1 if failed else 0


def print_close_rules() -> None:
    st = status_script()
    if st:
        r = subprocess.run([sys.executable, str(st), "rules", "build", "--close"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        print("\n" + (r.stdout or r.stderr).strip())


# the same "cannot change a check's result" rule as status.py's DOC_ONLY: only the run's own records - the feature
# doc, the status record, the changelog. Any other file, Markdown too, may be a check's input (check_structure.py
# reads STRUCTURE.md, and a logged close edited it after the gate), so it makes an earlier run stale
DOC_ONLY = re.compile(r"(?i)^docs/features/[^/]+\.md$|^STATUS\.md$|^status/|^CHANGELOG|^\.status\.lock$")  # the lock: status.py's own


def reusable_run(folder: Path, cmds: list[str], ticket: str, tree: str = "") -> dict | None:
    """A passing run of the SAME commands for the SAME ticket on this branch, with nothing but docs/status changed
    since - committed, uncommitted or untracked. None when anything a check could read differs."""
    f = folder / "results.jsonl"
    if not f.is_file():
        return None
    branch = git_out("rev-parse", "--abbrev-ref", "HEAD")
    for line in reversed(f.read_text(encoding="utf-8").splitlines()):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if not (r.get("passed") and r.get("branch") == branch and r.get("ticket") == ticket and r.get("head")
                and r.get("commands", []) == cmds):  # in order: the gate runs them in order
            continue
        if tree and r.get("tree"):  # the exact files both runs checked
            changed = [n for n in git_out("diff", "--name-only", r["tree"], tree).splitlines() if n]
            if [n for n in changed if not DOC_ONLY.search(n)]:
                continue
            return r
        # an older record has no tree: its commit, clean, and nothing but docs/status changed since
        if r.get("dirty") or [n for n in dirty_files(untracked=True) if not DOC_ONLY.search(n)]:
            continue
        if not git_out("rev-parse", "--verify", "--quiet", r["head"]):
            continue
        changed = [n for n in git_out("diff", "--name-only", r["head"], "HEAD").splitlines() if n]
        return None if [n for n in changed if not DOC_ONLY.search(n)] else r
    return None


def status_script() -> Path | None:
    """status.py beside this skill: the plugin's tools/, or a copy install's product-playbook/ folder."""
    root = Path(__file__).resolve().parents[2]
    return next((p for p in (root / "tools" / "status.py", root / "product-playbook" / "status.py") if p.is_file()),
                None)


def ticket_commands(tid: str) -> tuple[list[str], list[str]]:
    """(the project's full check recipe - the DoD says it is green, the ticket file's Verification Command)."""
    cmds: list[str] = []
    mine: list[str] = []
    for name in ("justfile", "Justfile", ".justfile"):
        f = Path(name)
        if f.is_file() and re.search(r"^check(?:\s+[^:\n=]*)?:(?!=)", f.read_text(encoding="utf-8", errors="replace"), re.M):
            cmds.append("just check")
            break
    else:
        if Path("Makefile").is_file() and re.search(r"^check\s*:", Path("Makefile").read_text(encoding="utf-8",
                                                                                            errors="replace"), re.M):
            cmds.append("make check")
        elif Path("package.json").is_file():
            try:
                if "check" in (json.loads(Path("package.json").read_text(encoding="utf-8")).get("scripts") or {}):
                    cmds.append("npm run check")
            except ValueError:
                pass
    folder = Path("docs") / "issues"
    files = sorted(folder.glob("*.md")) if folder.is_dir() else []
    tf = next((f for f in files if f.stem == tid or f.name.startswith(f"{tid}_")), None)
    if tf:
        text = tf.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"(?im)^#{2,3} .*verification command.*$\s*```[^\n]*\n(.*?)```", text, re.S)
        if m:
            mine = [l.strip() for l in m.group(1).splitlines() if l.strip() and not l.strip().startswith("#")]
    return cmds, mine


def git_out(*args: str) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip() if r.returncode == 0 else ""


def dirty_files(untracked: bool = False) -> list[str]:
    """Changed paths from `git status --porcelain`, read raw: git_out() strips the output, which took the first
    line's leading space and so the first letter of its path (a logged gate recorded STATUS.md as "TATUS.md")."""
    r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    out = []
    for ln in (r.stdout if r.returncode == 0 else "").splitlines():
        if len(ln) > 3 and (untracked or not ln.startswith("??")):
            out.append(ln[3:].split(" -> ")[-1].strip().strip('"'))
    return out


def worktree_tree(folder: Path) -> str:
    """The working tree as a git tree id - tracked and untracked files, ignored ones left out - built in a scratch
    index inside .git, so the project's own index and staged changes are never touched. "" when git can't."""
    gd = git_out("rev-parse", "--git-dir")
    if not gd:
        return ""
    idx = folder / "tree.index"
    real = Path(gd) / "index"
    try:
        if real.is_file():
            shutil.copyfile(real, idx)
        elif idx.exists():
            idx.unlink()
    except OSError:
        return ""
    env = {**os.environ, "GIT_INDEX_FILE": str(idx.resolve())}
    top = git_out("rev-parse", "--show-toplevel") or "."
    if subprocess.run(["git", "add", "-A"], cwd=top, env=env, capture_output=True).returncode:
        return ""
    r = subprocess.run(["git", "write-tree"], cwd=top, env=env, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def record(folder: Path, cmds: list[str], passed: bool, ticket: str = "", ticket_cmds: list[str] | None = None,
           reused: str = "", tree: str = "") -> None:
    """The run `status.py ticket` reads: which commands passed on which commit. A logged build's DoD said
    "`just check` green" while its gate ran three of the recipe's six checks; a row now needs a passing run of the
    project's own check recipe on the final code (R3-5)."""
    dirty = dirty_files()
    with open(folder / "results.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"branch": git_out("rev-parse", "--abbrev-ref", "HEAD"), "head": git_out("rev-parse", "HEAD"),
                            "dirty": dirty, "commands": cmds, "passed": passed, "ticket": ticket,
                            "ticket_cmds": ticket_cmds or [], "reused": reused, "tree": tree,
                            "date": time.strftime("%Y-%m-%d")}) + "\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
