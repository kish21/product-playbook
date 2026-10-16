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
    python gate.py --ticket M1-X-01 --close    (the close gate: the same, then - on a pass - the close's order + rules;
                                               it fails when the full suite or CI never runs the ticket's test files)

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


def windows_program(cmd: str, win: bool = os.name == "nt") -> str:
    """A shell=True command on Windows runs in cmd.exe, which reads `/Scripts` in `.venv/Scripts/python.exe` as an
    option ("'.venv' is not recognized" - a logged run's dev server never booted and its close gate failed). On
    Windows each program word - the first, and the first after `&&` `||` `|` `&` - gets backslashes; arguments,
    quoted text and URLs stay as written. Elsewhere the command is unchanged. (One copy per script: each is run
    standalone; tools/test_build_tools.py checks every copy.)"""
    if not win:
        return cmd
    out, i, n, start = [], 0, len(cmd), True
    while i < n:
        c = cmd[i]
        if start and c.isspace():
            out.append(c)
            i += 1
            continue
        if c == '"':
            j = cmd.find('"', i + 1)
            j = n if j < 0 else j + 1
        elif start:
            j = i
            while j < n and not cmd[j].isspace() and cmd[j] not in '&|"':
                j += 1
        elif c in "&|":
            j = i
            while j < n and cmd[j] in "&|":
                j += 1
            out.append(cmd[i:j])
            i, start = j, True
            continue
        else:
            out.append(c)
            i += 1
            continue
        tok = cmd[i:j]
        out.append(tok.replace("/", "\\") if start and "://" not in tok else tok)
        i, start = j, False
    return "".join(out)


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
            misses = suite_misses() if close else None
            record(folder, cmds, True, ticket, ticket_cmds, reused=prior["head"], tree=tree, misses=misses)
            if close:
                if not feature_docs_plain():  # both said in one run: the doc's gaps, and (above) the suite's misses
                    return 1
                if misses:
                    return 1
                print_close_rules()
            return 0
    stamp = time.strftime("%H%M%S")
    failed = 0
    for n, cmd in enumerate(cmds, 1):
        t0 = time.time()
        r = subprocess.run(windows_program(cmd), shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
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
    misses = suite_misses() if close and not failed else None
    record(folder, cmds, not failed, ticket, ticket_cmds, tree=tree, misses=misses)
    if close and not failed:  # the close starts here: its order and rules arrive now, not at the start of the run
        if not feature_docs_plain():  # both said in one run: the doc's gaps, and (above) the suite's misses
            return 1
        if misses:
            return 1
        print_close_rules()
    return 1 if failed else 0


def feature_docs_plain() -> bool:
    """The close gate: every docs/features/*.md this branch changed has a top half a person can read (featuredoc.py).
    The doc is only a record, so a failure here never makes the commands' passing run stale."""
    from featuredoc import top_half_gaps, warnings
    base = next((b for b in (git_out("merge-base", "HEAD", ref) for ref in ("origin/HEAD", "main", "master")) if b), "")
    changed = ((git_out("diff", "--name-only", base, "HEAD").splitlines() if base else [])
               + git_out("diff", "--name-only", "HEAD").splitlines()
               + git_out("ls-files", "--others", "--exclude-standard").splitlines())
    top = Path(git_out("rev-parse", "--show-toplevel") or ".")
    docs = sorted({c for c in changed if re.match(r"(?i)^docs/features/[^/]+\.md$", c)
                   and Path(c).name.lower() != "readme.md" and (top / c).is_file()})
    if not docs:
        print("feature doc: none on this branch yet - once written, check its top half: python "
              f"\"{Path(__file__).with_name('featuredoc.py')}\" docs/features/<feature>.md")
        return True
    bad = [(d, g) for d in docs for g in top_half_gaps((top / d).read_text(encoding="utf-8", errors="replace"))]
    for d, g in bad:
        print(f"FEATURE DOC {d}: {g}")
    for d in docs:  # numbering and sentence length are said, never a gate failure
        for w in warnings((top / d).read_text(encoding="utf-8", errors="replace")):
            print(f"warn {d}: {w}")
    if bad:
        print("GATE FAIL - the feature doc's top half is for people (templates/feature-doc.md): fix it and run the "
              "close gate again - the checks' passing run is reused")
    return not bad


# AG-B2: a logged project put each module's tests in app/<module>/tests while pytest's testpaths, the Makefile's
# `check` and CI ran tests/ only - the ticket's own tests passed by path, never ran in the full suite or in CI, and
# nothing noticed. The close gate asks each full-suite command which test files it would run.
TEST_FILE = re.compile(r"(?:^|/)(?:test_[^/]*\.py|[^/]*_test\.py|[^/]+\.(?:test|spec)\.[cm]?[jt]sx?)$")
UNRESOLVED = re.compile(r"\$\(|\$\{|\{\{|%\w+%")  # a make / just / CI variable: the command cannot run as written
# the runner as the PROGRAM of a command (never `pip install pytest`): pytest, a path to it, python -m pytest, or a
# project runner's `run pytest`; vitest / jest, bare or through npx / pnpm exec / yarn / bunx
PYTEST = re.compile(r"^(?:\w+=\S*\s+)*(?:(?:\S*[/\\])?python[\d.]*(?:\.exe)?\s+-m\s+|(?:uv|poetry|pdm|pipenv|rye)\s+run"
                    r"(?:\s+-\S+)*\s+|\S*[/\\])?py\.?test(?:\.exe)?(?=\s|$)")
JS_RUNNER = re.compile(r"^(?:\w+=\S*\s+)*(?:npx\s+|pnpm\s+(?:exec\s+)?|yarn\s+|bunx\s+|\S*[/\\])?(vitest|jest)(?=\s|$)")


def branch_files() -> list[str]:
    """The files this branch changed - committed since the default branch, uncommitted, or new."""
    base = next((b for b in (git_out("merge-base", "HEAD", ref) for ref in ("origin/HEAD", "main", "master")) if b), "")
    return sorted(set((git_out("diff", "--name-only", base, "HEAD").splitlines() if base else [])
                      + git_out("diff", "--name-only", "HEAD").splitlines()
                      + git_out("ls-files", "--others", "--exclude-standard").splitlines()) - {""})


def recipe_lines(recipe: str) -> list[tuple[str, str]]:
    """(where, command) for every command the full-suite recipe runs - its body, the targets it depends on and the
    targets / scripts it calls - plus every test command in the CI workflows. Read only, never run here."""
    out: list[tuple[str, str]] = []
    if recipe in ("just check", "make check"):
        f = (next((Path(n) for n in ("justfile", "Justfile", ".justfile") if Path(n).is_file()), None)
             if recipe == "just check" else Path("Makefile"))
        text = f.read_text(encoding="utf-8", errors="replace") if f else ""
        targets: dict[str, tuple[list[str], list[str]]] = {}
        cur = None
        for ln in text.splitlines():
            m = re.match(r"^([A-Za-z0-9_.-]+)(?:\s+[^:=\n]*)?:(?![=:])\s*(.*)$", ln)
            if m:
                cur = m.group(1)
                targets[cur] = ([w for w in m.group(2).split("#")[0].split()], [])
            elif cur and ln[:1] in ("\t", " ") and ln.strip():
                targets[cur][1].append(ln.strip().lstrip("@-").strip())
            elif ln.strip() and not ln.startswith("#"):
                cur = None
        seen: set[str] = set()

        def walk(name: str) -> None:
            if name in seen or name not in targets:
                return
            seen.add(name)
            deps, body = targets[name]
            for dep in deps:
                walk(dep)
            for ln in body:
                out.append((f"{f.name} `{name}`", ln))
                for m in re.finditer(r"(?:\$\(MAKE\)|\bmake|\bjust)\s+([A-Za-z0-9_.-]+)", ln):
                    walk(m.group(1))
        walk("check")
    elif recipe == "npm run check":
        try:
            scripts = json.loads(Path("package.json").read_text(encoding="utf-8")).get("scripts") or {}
        except ValueError:
            scripts = {}
        seen_js: set[str] = set()

        def walk_js(name: str) -> None:
            if name in seen_js or name not in scripts:
                return
            seen_js.add(name)
            out.append((f"package.json `{name}`", str(scripts[name])))
            for m in re.finditer(r"\b(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?([\w:.-]+)", str(scripts[name])):
                walk_js(m.group(1))
        walk_js("check")
    wfs = Path(".github") / "workflows"
    for wf in sorted(wfs.glob("*.y*ml")) if wfs.is_dir() else []:
        for ln in wf.read_text(encoding="utf-8", errors="replace").splitlines():
            ln = re.sub(r"^\s*(?:-\s*)?(?:run:\s*)?", "", ln).strip()
            if not re.match(r"[\w-]+:(?:\s|$)|#", ln) and list_command(ln):
                out.append((f"CI {wf.as_posix()}", ln))
    return out


def list_command(cmd: str) -> str | None:
    """The command's test-runner part in the runner's own "list what you would run" form; None for a command that
    runs no test runner this knows (pytest, vitest, jest)."""
    for seg in re.split(r"&&|\|\||;", cmd):
        seg = seg.strip()
        if PYTEST.search(seg):
            return seg + " --collect-only -q"
        m = JS_RUNNER.search(seg)
        if m:
            if seg.startswith(m.group(1)):
                seg = "npx " + seg
            if m.group(1) == "vitest":
                return re.sub(r"\bvitest(?:\s+(?:run|watch))?(?=\s|$)", "vitest list --filesOnly", seg, count=1)
            return seg + " --listTests"
    return None


def collected(path: str, out: str) -> bool:
    """`path` (relative to the project folder) is in a runner's listing: a pytest node id (`path::test`), a
    collection ERROR line, or a listed file, relative or absolute."""
    out = out.replace("\\", "/")
    here = re.escape(Path.cwd().resolve().as_posix())
    return bool(re.search(rf"(?im)(?:^|\s|{here}/){re.escape(path)}(?:::|\s|$)", out))


def suite_misses() -> list[str] | None:
    """The ticket's test files that a full-suite command never runs ([] = every command runs them all); None when it
    cannot tell - it says why, and never fails the gate on a guess."""
    top = Path(git_out("rev-parse", "--show-toplevel") or ".").resolve()
    here = Path.cwd().resolve()
    mine = []
    for f in branch_files():
        p = (top / f).resolve()
        if TEST_FILE.search(f) and p.is_file():
            try:
                mine.append(p.relative_to(here).as_posix())
            except ValueError:
                continue
    if not mine:
        return []
    recipe = (ticket_commands("")[0] or [""])[0]
    runs = [(where, cmd, lc) for where, cmd in recipe_lines(recipe) for lc in (list_command(cmd),) if lc]
    if not runs:
        print(f"! suite check: cannot tell whether the full suite runs {', '.join(mine[:4])} - "
              + (f"`{recipe}` calls no pytest / vitest / jest line I can read" if recipe else
                 "no check recipe (justfile / Makefile / package.json `check`)")
              + ": check by hand that the full suite and CI run them")
        return None
    misses: dict[str, list[str]] = {}
    unknown = []
    for where, cmd, listing in runs:
        if UNRESOLVED.search(cmd):
            unknown.append(f"{where}: `{cmd[:80]}` (it uses a variable)")
            continue
        try:
            r = subprocess.run(windows_program(listing), shell=True, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=600)
        except subprocess.TimeoutExpired:
            unknown.append(f"{where}: `{listing[:80]}` timed out")
            continue
        out = (r.stdout or "") + (r.stderr or "")
        py = bool(PYTEST.search(listing))
        # pytest: 0 listed, 2 collection errors (files still named), 5 none collected; a runner that did not start
        # (not installed, a usage error) proves nothing either way
        if (py and r.returncode not in (0, 2, 5)) or (not py and r.returncode != 0):
            unknown.append(f"{where}: `{listing[:80]}` exit {r.returncode}")
            continue
        for f in mine:
            if f.endswith(".py") == py and not collected(f, out):
                misses.setdefault(f, []).append(f"{where}: `{cmd[:70]}`")
    for u in unknown:
        print(f"! suite check: could not list the tests of {u} - check by hand that it runs this ticket's tests")
    if not misses:
        return None if len(unknown) == len(runs) else []
    for f, where in misses.items():
        print(f"SUITE MISSES {f} - not run by {' · '.join(where)}")
    print("GATE FAIL - the full suite never runs this ticket's tests (they pass only when run by path): add their "
          "folder to each command named above (the Makefile / justfile / package.json recipe, CI's test step), or to "
          "pytest's `testpaths` (pyproject.toml [tool.pytest.ini_options]) when the command names no folder - or "
          "move the tests under the folder it runs; then run the close gate again")
    return sorted(misses)


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
           reused: str = "", tree: str = "", misses: list[str] | None = None) -> None:
    """The run `status.py ticket` reads: which commands passed on which commit. A logged build's DoD said
    "`just check` green" while its gate ran three of the recipe's six checks; a row now needs a passing run of the
    project's own check recipe on the final code (R3-5)."""
    dirty = dirty_files()
    with open(folder / "results.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"branch": git_out("rev-parse", "--abbrev-ref", "HEAD"), "head": git_out("rev-parse", "HEAD"),
                            "dirty": dirty, "commands": cmds, "passed": passed, "ticket": ticket,
                            "ticket_cmds": ticket_cmds or [], "reused": reused, "tree": tree,
                            "date": time.strftime("%Y-%m-%d"),
                            **({} if misses is None else {"suite_misses": misses})}) + "\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
