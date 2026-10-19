"""gate.py - every check a build step needs, in ONE call, printing only what the next step needs.

A logged build spent ~40 of its 120 model calls running one check per call (tests, then lint, then types, then the
structure check), each call re-sending a 200k-token conversation to read one exit code. This runs them all:

    python gate.py "just lint" "uv run pytest app/shops/tests -q" "python scripts/check_structure.py"

For each command, in order: PASS or FAIL with its exit code and seconds, the result line a record quotes
(`86 passed in 24.2s`), and for a FAIL the lines that say what failed (FAILED / ERROR / error: / the end of a
traceback) - never the whole output. The whole output goes to a log file inside .git (never committed, one per
checkout; .playbook-state/ when .git cannot be written), named on the last line, for the rare case that needs more.
The ticket's own commands run in the project's environment: a bare `pytest` / `python` / `ruff` / `mypy` goes through
the project's runner (`uv run`, `poetry run` ...), and a .venv's programs come first on PATH.

    python gate.py --ticket M1-X-01            (the project's check recipe + the ticket's Verification Command)
    python gate.py --fresh "<cmd>"             (run again even when these exact files already passed)
    python gate.py --ticket M1-X-01 --close    (the close gate: the same, then - on a pass - the close's order + rules;
                                               it fails when the full suite or CI never runs the ticket's test files)
    python gate.py --ticket M1-X-01 --close --suite "<cmd>"   (the project's full-suite command, when the gate cannot
                                               read one - remembered for this checkout)

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


STATE_FALLBACK = ".playbook-state"


def state_dir(base: Path | None = None, common: bool = False) -> Path:
    """Where the playbook's never-committed records live: the git folder, or - when it cannot be written (Codex's
    sandbox write-protects .git: a PermissionError and an approval retry on every start of a logged run) -
    .playbook-state/ at the project root, which ignores itself, so the repo stays clean. Once that folder exists every
    script uses it. (One copy per script: each is run standalone; tools/test_build_tools.py checks every copy.)"""
    base = Path(base) if base is not None else Path(".")
    r = subprocess.run(["git", "rev-parse", "--git-common-dir" if common else "--git-dir", "--show-toplevel"],
                       cwd=base, capture_output=True, text=True)
    lines = r.stdout.strip().splitlines() if r.returncode == 0 else []
    if len(lines) < 2:
        return base / lines[0] if lines else base
    gd = Path(lines[0]) if Path(lines[0]).is_absolute() else base / lines[0]
    fb = Path(lines[1]) / STATE_FALLBACK
    if not fb.is_dir():
        try:
            probe = gd / f".playbook-probe-{os.getpid()}"
            probe.write_text("", encoding="utf-8")
            probe.unlink()
            return gd
        except OSError:
            fb.mkdir(parents=True, exist_ok=True)
    if not (fb / ".gitignore").is_file():
        (fb / ".gitignore").write_text("*\n", encoding="utf-8")
    return fb


def log_dir() -> Path:
    d = state_dir() / "playbook-gate"
    d.mkdir(parents=True, exist_ok=True)
    return d


# GT2: a ticket's bare `pytest ...` ran outside the project's environment - it failed, a logged agent edited PATH,
# then it passed. The ticket's commands run the way the project's own recipe runs its tools.
RUNNER_LOCKS = (("uv.lock", "uv run"), ("poetry.lock", "poetry run"), ("pdm.lock", "pdm run"),
                ("Pipfile.lock", "pipenv run"))
PY_TOOL = re.compile(r"^(?:py\.?test|python[\d.]*|ruff|mypy|pyright|coverage|alembic)(?=\s|$)")


def in_runner(cmd: str) -> str:
    """`cmd` through the project's runner when its program is a bare Python tool and the project locks its
    environment with uv / poetry / pdm / pipenv; otherwise unchanged."""
    prefix = next((p for f, p in RUNNER_LOCKS if Path(f).is_file()), "")
    return f"{prefix} {cmd.strip()}" if prefix and PY_TOOL.match(cmd.strip()) else cmd


def project_env() -> dict:
    """The environment every command runs in: the project's .venv programs first on PATH (bash and Windows)."""
    env = dict(os.environ)
    for sub in ("Scripts", "bin"):
        d = Path(".venv") / sub
        if d.is_dir():
            env["PATH"] = str(d.resolve()) + os.pathsep + env.get("PATH", "")
            break
    return env


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
    suite = argv[argv.index("--suite") + 1] if "--suite" in argv and argv.index("--suite") + 1 < len(argv) else ""
    cmds = [a for i, a in enumerate(argv) if a not in ("--stop", "--close", "--ticket", "--only", "--fresh", "--suite")
            and not (i and argv[i - 1] in ("--ticket", "--suite"))]
    if suite:  # GS2: the project's full-suite command, said once and remembered for this checkout
        (log_dir() / "suite.json").write_text(json.dumps({"command": suite}), encoding="utf-8")
        print(f"gate: the full-suite command for this checkout is now `{suite}` (remembered)")
    ticket_cmds: list[str] = []
    if ticket and not only:  # the project's recipe + the ticket's own verification, THEN any named extra commands -
        # named commands add to the automatic checks, never replace them (an extra secret scan once dropped the
        # recipe and the ticket's tests silently); `--only` replaces, and says so
        recipe, ticket_cmds = ticket_commands(ticket)
        for c in ticket_cmds:
            if in_runner(c) != c:
                print(f"gate: `{c}` runs as `{in_runner(c)}` - the project's runner, as its recipe runs it (never "
                      f"edit PATH)")
        ticket_cmds = [in_runner(c) for c in ticket_cmds]
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
                if not feature_docs_plain() or misses:  # both said in one run: the doc's gaps, the suite's misses
                    print_fail_hint(ticket)
                    return 1
                print_close_rules()
            return 0
    stamp = time.strftime("%H%M%S")
    failed = 0
    for n, cmd in enumerate(cmds, 1):
        t0 = time.time()
        r = subprocess.run(windows_program(cmd), shell=True, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=project_env())
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
        if not feature_docs_plain() or misses:  # both said in one run: the doc's gaps, and (above) the suite's misses
            print_fail_hint(ticket)
            return 1
        print_close_rules()
    if failed:
        print_fail_hint(ticket)
    return 1 if failed else 0


def print_fail_hint(ticket: str) -> None:
    """GT1: a logged agent offered "record it as partial" after a failing gate in two sessions - the record refuses
    every --dod (yes, partial, no) without a passing gate, and nothing carried that to the next session."""
    if not ticket:
        return
    st = status_script()
    exe = Path(sys.executable).as_posix()  # the interpreter that ran this gate, never a bare `python` (CX-B3)
    run = f'{exe if " " not in exe else chr(34) + exe + chr(34)} "{st.as_posix()}"' if st else "status.py"
    print(f"The record (`status.py ticket {ticket}`) refuses EVERY --dod - yes, partial and no - until this gate "
          f"passes: never offer \"record as partial\". Fix what failed and run the gate again; stopping here instead: "
          f"file it in one call - {run} open --from build --what \"{ticket}: the gate fails - <what failed>\" "
          f"--clears \"gate.py --ticket {ticket} --close passes\"")


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
            if not re.match(r"[\w-]+:(?:\s|$)|#", ln) and (list_command(ln) or script_pytest(ln)):
                out.append((f"CI {wf.as_posix()}", ln))
    # GS2: a step that runs a Python script which itself calls pytest (`uv run python scripts/tasks.py test`) - a
    # logged project ran its whole suite that way, the check read nothing and passed on 13 ticket tests. The script's
    # pytest call is read as the project's default pytest run (its own testpaths), through the project's runner.
    return [(w, c) for w, line in out
            for c in ((line,) if list_command(line) or not script_pytest(line) else (line, in_runner("pytest")))]


SCRIPT_CALL = re.compile(r"(?:^|\s)(?:\S*[/\\])?python[\d.]*(?:\.exe)?\s+((?:[\w.-]+[/\\])*[\w.-]+\.py)\b")
CALLS_PYTEST = re.compile(r"""["']py\.?test["']|\bpytest\.main\(|-m\s+pytest\b""")


def script_pytest(cmd: str) -> str:
    """The first Python script `cmd` runs whose source calls pytest; "" for none."""
    for m in SCRIPT_CALL.finditer(cmd):
        f = Path(m.group(1))
        try:
            if f.is_file() and CALLS_PYTEST.search(f.read_text(encoding="utf-8", errors="replace")):
                return f.as_posix()
        except OSError:
            continue
    return ""


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
    lines = recipe_lines(recipe)
    told = remembered_suite()
    if told:  # GS2: the full-suite command the project named (`--suite`), read like a recipe line
        lines.append(("the recorded full-suite command", told))
        if not list_command(told) and script_pytest(told):
            lines.append((f"the recorded full-suite command (via {script_pytest(told)})", in_runner("pytest")))
    runs = [(where, cmd, lc) for where, cmd in lines for lc in (list_command(cmd),) if lc]
    if not runs:
        return suite_unverified(mine, (f"`{recipe}` calls no pytest / vitest / jest line I can read" if recipe else
                                       "no check recipe (justfile / Makefile / package.json `check`) and no CI test "
                                       "step I can read") + (f", nor does `{told}`" if told else ""))
    misses: dict[str, list[str]] = {}
    # GS1: a ticket test is covered when ANY command of the same runner in the same place - the local recipe, or
    # one CI workflow file - runs it: a CI step that runs one eval file on purpose made a logged close refuse a
    # correct ticket that the full-suite step beside it ran
    cover: dict[tuple[str, bool], dict[str, list[str] | None]] = {}
    unknown = []
    for where, cmd, listing in runs:
        if UNRESOLVED.search(cmd):
            unknown.append(f"{where}: `{cmd[:80]}` (it uses a variable)")
            continue
        try:
            r = subprocess.run(windows_program(listing), shell=True, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=600, env=project_env())
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
        seen = cover.setdefault((where if where.startswith("CI ") else "recipe", py), {})
        for f in mine:
            if f.endswith(".py") != py:
                continue
            if collected(f, out):
                seen[f] = None
            elif seen.get(f, []) is not None:
                seen.setdefault(f, []).append(f"{where}: `{cmd[:70]}`")
    for seen in cover.values():
        for f, where_list in seen.items():
            if where_list:
                misses.setdefault(f, []).extend(where_list)
    for u in unknown:
        print(f"! suite check: could not list the tests of {u} - check by hand that it runs this ticket's tests")
    if not misses:
        return suite_unverified(mine, "no full-suite command could list its tests") if len(unknown) == len(runs) \
            else []
    for f, where in misses.items():
        print(f"SUITE MISSES {f} - not run by {' · '.join(where)}")
    print("GATE FAIL - the full suite never runs this ticket's tests (they pass only when run by path): add their "
          "folder to each command named above (the Makefile / justfile / package.json recipe, CI's test step), or to "
          "pytest's `testpaths` (pyproject.toml [tool.pytest.ini_options]) when the command names no folder - or "
          "move the tests under the folder it runs; then run the close gate again")
    return sorted(misses)


def remembered_suite() -> str:
    f = log_dir() / "suite.json"
    try:
        return str(json.loads(f.read_text(encoding="utf-8")).get("command") or "") if f.is_file() else ""
    except ValueError:
        return ""


def suite_unverified(mine: list[str], why: str) -> list[str]:
    """GS2: the check cannot tell whether the full suite runs the ticket's tests - fail closed (a pass here once
    meant only the 13 ticket tests ran) and ask for the project's full-suite command ONCE: it is remembered."""
    print(f"SUITE UNVERIFIED - cannot tell whether the full suite runs {', '.join(mine[:4])}: {why}.\n"
          "GATE FAIL - name the command that runs the project's WHOLE test suite once (ask the user when the project "
          "does not say), and run the close gate again with it: gate.py --ticket <id> --close --suite \"<command>\" "
          "(remembered for this checkout; a command that runs a Python script calling pytest is followed)")
    return ["(full suite unverified)"]


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
