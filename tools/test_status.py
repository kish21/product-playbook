"""Behaviour tests for tools/status.py (run by tools/check.py, check 53). Each test drives the real command line.

The legal-transition table is held to STATE-MODEL.md §2b: the state model states it, status.py enforces it,
and this file fails when the two disagree.
"""
from __future__ import annotations
import contextlib
import io
import itertools
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "status.py"
sys.path.insert(0, str(ROOT / "tools"))
import status  # noqa: E402

TODAY = "2026-09-24"
# a feature doc's top half for people (#57 item 8: `status.py ticket` checks it); the fixtures' developer halves follow
TOP_HALF = ("## In short\nGuests can leave the door.\n\n## What you can do now\nOpen the list.\n\n"
            "## What it protects you from\nTexting the wrong person.\n\n## Not done yet\nNothing.\n\n---\n\n"
            "## For developers and coding agents\n\n")
# the suite runs on the plugin route, where /build and /dev-check default to the lean path: the full procedure's checks
# are what most tests exercise, so full is the default here; test_lean_mode switches to lean on purpose
os.environ["PLAYBOOK_MODE"] = "full"
os.environ["PLAYBOOK_ACTION_CHECK"] = "off"  # 2.3: /foundation's close never asks github.com in tests
os.environ["PLAYBOOK_BOARD"] = "off"  # #57 item 1: a build start or record never asks a real GitHub in tests


def run(d: Path, *args: str) -> tuple[int, str]:
    """In-process: a subprocess per call made this suite take minutes on Windows. test_cli covers the real CLI."""
    out, cwd = io.StringIO(), os.getcwd()
    os.chdir(d)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            try:
                code = status.main(["--file", str(d / "STATUS.md"), "--today", TODAY, *args])
            except SystemExit as e:  # argparse refuses an unknown flag by exiting
                code = e.code if isinstance(e.code, int) else 2
    finally:
        os.chdir(cwd)
    return code, out.getvalue()


def test_guesses_get_the_answer(d: Path, fails: list[str]) -> None:
    """A logged run guessed `status.py status`, `how structure` and `bypass -h` to find the override: a wrong
    command prints every command, and a BLOCKED next line prints the exact bypass command."""
    for bad in (("status",), ("how", "structure")):
        code, out = run(d, *bad)
        if code != 2 or "Which status.py command records what" not in out:
            fails.append(f"`status.py {' '.join(bad)}` should fail with the command list: {out.strip()[:200]}")
    fresh(d, ui="no")
    for p in ("vision", "scope", "plan"):
        run(d, "set", p, "filled")
    run(d, "set", "validate", "running", "--due", "2026-10-01", "--reason", "pre-sale")
    code, out = run(d, "next")
    if 'status.py bypass --from architect --gate validate --reason "<their words>"' not in out:
        fails.append(f"a BLOCKED next should print the exact bypass command: {out.strip()}")


def test_how_lists_every_command(d: Path, fails: list[str]) -> None:
    """`status.py how` is the one home of which-command-when; a command it does not list is one no run finds."""
    code, out = run(d, "how")
    firsts = {c.split()[0] for _, c in status.HOW}
    for cmd in ("next", "init", "migrate", "set", "bypass", "ticket", "release", "drift", "open", "close", "flag",
                "check"):
        if cmd not in firsts:
            fails.append(f"`status.py how` does not list the {cmd!r} command")
    if code != 0 or "bypass --from" not in out:
        fails.append(f"`status.py how` did not print its table: {out[:200]!r}")


def test_git_bash_path_rewrite(d: Path, fails: list[str]) -> None:
    """Git Bash turned "/architect" into "C:/Program Files/Git/architect" on a logged run; status.py undoes it."""
    fresh(d)
    run(d, "open", "--from", "vision", "--what", "decide reminders",
        "--clears", "C:/Program Files/Git/architect records both decisions")
    run(d, "set", "vision", "declined", "--reason", "x", "--gate", "D:/tools/Git/scope")
    st = status.Status.load(d / "STATUS.md")
    if st.rows["Open items"][0][4] != "/architect records both decisions":
        fails.append(f"a Git Bash path rewrite survived in an open item: {st.rows['Open items'][0][4]!r}")
    if "run /scope first" not in st.phase("vision")[5]:
        fails.append(f"a Git Bash path rewrite survived in --gate: {st.phase('vision')[5]!r}")
    if status.undo_msys_path("C:/Users/me/project/notes.md") != "C:/Users/me/project/notes.md":
        fails.append("a real Windows path was changed")


def test_cli(d: Path, fails: list[str]) -> None:
    """One real process: the script runs as a command and a refusal reaches the caller readable, as UTF-8."""
    fresh(d)
    p = subprocess.run([sys.executable, str(SCRIPT), "--file", str(d / "STATUS.md"), "--today", TODAY,
                        "set", "vision", "declined"], capture_output=True, cwd=d)
    err = p.stderr.decode("utf-8", errors="strict") if p.stderr else ""
    if p.returncode != 1 or "REFUSED" not in err:
        fails.append(f"the CLI did not refuse with a readable message: exit {p.returncode}, {err!r}")


# A #Vision that `set vision filled` accepts (status.vision_gaps): a test that closes /vision as an example phase
# starts from it and adds the lines it is about.
VISION_OK = ("- **Vision:** nobody waits at the door guessing\n"
             "- **In plain words:** guests wait outside; the app texts them when their table is ready\n"
             "- **Worked example:** Mia's party of 4 joins the list at 19:05 and gets a text at 19:32\n"
             "- **Who it's for:** small restaurants\n"
             "- **Problem (why now):** walk-ins leave\n- **Value proposition:** a text when the table is ready\n"
             "- **Current-year market:** Waitwhile, Yelp Guest Manager\n"
             "- **North star — target + date:** 40 restaurants by 2027-03-31\n"
             "- **North star — input metrics:** texts sent per week\n- **North star — guardrail:** no-show rate\n"
             "- **North star — instrumentation:** nothing records this yet\n"
             "- **Job-to-be-done:** when the room is full, I want a list, so I can seat people\n"
             "- **Riskiest assumption:** guests answer a text\n- **Business model:** paid\n"
             "- **First users:** 10 restaurants on one street, visited in person; they switch because paper lists fail\n"
             "- **Constraints:** a guest's phone number is personal data (GDPR) · English · the restaurant's own list\n")
# the companion as next.55's start describes it: the owner's answers, a search list with a link per line and its
# why-now, same-job and rules lines, the terms table with where each number came from
VISION_SEARCHES = ("### A.2 Search list\n\n"
                   "- why now · `restaurant waitlist 2026` · settled: walk-ins grew · https://example.org/a1\n"
                   "- local · `wachtlijst restaurant app Gent` · two local apps · https://example.org/local\n"
                   "- same job · `restaurant waitlist app` · Waitwhile, Yelp Guest Manager · https://example.org/same\n"
                   "- rules · `restaurant guest phone number GDPR` · personal data · https://example.org/rules\n\n")
# next.57: a founder's document first, the workings in an appendix (the checks find their headings anywhere)
# 2.2 (#60, #61): numbered headings, a diagram, In / Out of scope and open questions - the layout `set` refuses without
VISION_LAYOUT = ("# Vision\n\n## 1. Vision in one line\n\n**Nobody waits at the door.**\n\n"
                 "## 2. How it works\n\n```mermaid\nflowchart LR\n  A[guest joins] --> B[text sent]\n```\n\n"
                 "## 3. Scope at a glance\n\n- **In scope:** the list and the text\n- **Out of scope:** bookings\n\n"
                 "## 4. Open questions\n\n1. Do guests answer a text?\n\n")
VISION_DOC = (VISION_LAYOUT.replace("## 2. How it works", "## 5. Who it is for\n\nSmall restaurants.\n\n"
                                    "## 6. Competitors\n\n| Product | Market | Same job / nearby |\n|---|---|---|\n"
                                    "| Waitwhile | worldwide | same job |\n\n## 2. How it works") +
              "## Appendix A — Workings\n\n### A.1 Owner's answers\n\n1. A waitlist for small restaurants.\n\n"
              + VISION_SEARCHES +
              "### A.3 North-star terms\n| Term | Number | From |\n|---|---|---|\n"
              "| restaurant | 1+ location, 20+ walk-ins a week | owner |\n")


def vision_ready(d: Path, doc_extra: str = "") -> None:
    """docs/vision.md and the AI answer `set vision filled` needs; the test writes #Vision itself."""
    (d / "docs").mkdir(exist_ok=True)
    (d / "docs" / "vision.md").write_text(VISION_DOC + doc_extra, encoding="utf-8")
    code, out = run(d, "flag", "--ai", "no")
    assert code == 0, out


def fresh(d: Path, **flags: str) -> None:
    import shutil
    for f in d.glob("*"):
        if f.is_file():
            f.unlink()
    shutil.rmtree(d / status.FRAG_DIR, ignore_errors=True)  # a project's item files go with its STATUS.md
    ui = flags.pop("ui", None)  # init takes no --ui: /vision cannot know it; a later phase flags it
    extra = [x for k, v in flags.items() for x in (f"--{k}", v)]
    code, out = run(d, "init", "--product", "Demo", *extra)
    assert code == 0, out
    if ui:
        code, out = run(d, "flag", "--ui", ui)
        assert code == 0, out


def args_for(state: str) -> list[str]:
    return {"declined": ["--reason", "no scope yet", "--gate", "scope"],
            "overridden": ["--reason", "the user's words", "--gate", "validate"],
            "running": ["--due", "2026-10-01", "--reason", "pre-sale count"],
            "filled": ["--note", "7 of 10 pre-sold vs bar 5 - proceed"]}.get(state, [])


def reach(d: Path, state: str) -> None:
    """Put #vision into `state` by a legal path."""
    if state == "empty":
        return
    path = {"filled": ["filled"], "declined": ["declined"], "running": ["running"],
            "overridden": ["overridden"]}[state]
    for s in path:
        code, out = run(d, "set", "vision", s, *args_for(s))
        assert code == 0, out


def test_table_matches_state_model(fails: list[str]) -> None:
    text = (ROOT / "docs" / "state-model.md").read_text(encoding="utf-8")
    block = re.search(r"### 2b\..*?```(.*?)```", text, re.S)
    if not block:
        fails.append("STATE-MODEL.md §2b has no transition block")
        return
    doc = set(re.findall(r"^(\w+) ──▶ (\w+)", block.group(1), re.M))
    if doc != status.LEGAL:
        fails.append(f"status.py LEGAL != STATE-MODEL.md §2b: only in code {sorted(status.LEGAL - doc)}, "
                     f"only in the model {sorted(doc - status.LEGAL)}")


def test_every_transition(d: Path, fails: list[str]) -> None:
    for old, new in itertools.product(status.STATES, repeat=2):
        fresh(d)
        reach(d, old)
        before = (d / "STATUS.md").read_text(encoding="utf-8")
        code, out = run(d, "set", "vision", new, *args_for(new))
        legal = (old, new) in status.LEGAL
        if legal and code != 0:
            fails.append(f"{old} -> {new} is legal but was refused: {out.strip()}")
        if not legal and (code == 0 or (d / "STATUS.md").read_text(encoding="utf-8") != before):
            fails.append(f"{old} -> {new} is illegal but was accepted, or the file changed")


def test_required_details(d: Path, fails: list[str]) -> None:
    for state, missing in (("declined", ["--reason", "x"]), ("overridden", ["--gate", "scope"]),
                           ("running", ["--reason", "x"])):
        fresh(d)
        code, _ = run(d, "set", "vision", state, *missing)
        if code == 0:
            fails.append(f"set {state} without all its details was accepted")


def test_running_closes_only_on_a_result(d: Path, fails: list[str]) -> None:
    """Finding F: a running experiment must not become filled with no measured result."""
    fresh(d)
    run(d, "set", "validate", "running", *args_for("running"))
    code, _ = run(d, "set", "validate", "filled")
    if code == 0:
        fails.append("running -> filled with no --note (the measured result) was accepted")
    (d / "PRODUCT.md").write_text("# PRODUCT\n\n## Validation\n- **Measured result:** PENDING - due 2026-10-01\n\n"
                                  "## Scope\n", encoding="utf-8")
    code, _ = run(d, "set", "validate", "filled", "--note", "done")
    if code == 0:
        fails.append("running -> filled was accepted while PRODUCT.md#Validation still reads PENDING")
    (d / "PRODUCT.md").write_text("# PRODUCT\n\n## Validation\n- **Measured result:** 7 of 10 pre-sold\n\n"
                                  "## Scope\n", encoding="utf-8")
    code, out = run(d, "set", "validate", "filled", "--note", "7 of 10 pre-sold vs bar 5 - proceed")
    if code != 0:
        fails.append(f"running -> filled with a result recorded was refused: {out.strip()}")
    (d / "PRODUCT.md").unlink()


def test_caps_and_pipes(d: Path, fails: list[str]) -> None:
    fresh(d)
    code, _ = run(d, "ticket", "T-1", "--dod", "yes", "--verified", "x" * 241, "--doc", "docs/features/t.md")
    if code == 0:
        fails.append("a 241-character How verified was accepted (limit 240)")
    code, out = run(d, "ticket", "T-1", "--dod", "yes", "--verified", "pytest -q | tail -1 -> 3 passed",
                    "--doc", "docs/features/t.md", "--runs", "2", "--review", "R1 3 findings")
    st = status.Status.load(d / "STATUS.md")
    if code != 0 or st.rows["Tickets"][0][3] != "pytest -q | tail -1 -> 3 passed":
        fails.append(f"a value with a pipe did not round-trip: {out.strip()} {st.rows['Tickets']}")
    if st.state("build") != "filled":
        fails.append("the first ticket did not mark #build filled")


def test_next(d: Path, fails: list[str]) -> None:
    fresh(d, ui="no")
    run(d, "set", "vision", "filled")
    run(d, "set", "validate", "running", "--due", "2026-10-01", "--reason", "pre-sale")
    code, out = run(d, "next")
    for token in ("never a save question", "What I skipped or couldn't do",
                  "Test this yourself", "set <phase> filled"):
        if token not in out:
            fails.append(f"next should print the close checklist ({token!r} missing): {out.strip()}")
    if "Next: /scope - provisional" not in out:
        fails.append(f"a running #validate should make /scope provisional: {out.strip()}")
    for p in ("scope", "plan"):
        run(d, "set", p, "filled")
    code, out = run(d, "next")
    if "Next: /architect - BLOCKED" not in out:
        fails.append(f"a running #validate should block /architect: {out.strip()}")
    for p in ("architect", "structure"):
        run(d, "set", p, "filled")
    run(d, "set", "validate", "overridden", "--reason", "moving on", "--gate", "validate")
    code, out = run(d, "next")
    if "Next: /foundation" not in out or "override: #validate" not in out:
        fails.append(f"UI=no should skip design-system and surface the override: {out.strip()}")
    run(d, "set", "foundation", "declined", "--reason", "no stack", "--gate", "architect")
    code, out = run(d, "next")
    if "already tried 2026-09-24" not in out:
        fails.append(f"a declined frontier should name the earlier attempt: {out.strip()}")
    real_gaps, status.tests_gaps = status.tests_gaps, lambda st, verdict: []  # the chain's order, not the record test
    try:
        run(d, "set", "test", "filled", "--verdict", "pass")
    finally:
        status.tests_gaps = real_gaps
    code, out = run(d, "next")
    if "out of order: #test is filled but #foundation is empty" not in out:
        fails.append(f"an inversion should be named: {out.strip()}")


def test_verdicts_and_tickets(d: Path, fails: list[str]) -> None:
    fresh(d, ui="no")
    for p in ("vision", "validate", "scope", "plan", "architect", "structure", "foundation", "contracts",
              "tickets"):
        run(d, "set", p, "filled")
    (d / "TICKETS.md").write_text("# Tickets — Demo\n\n## M1 — First\n\n| Epic | Lane | Owner | Tickets |\n"
                                  "|---|---|---|---|\n| `M1-A` A | a | Senior | `M1-A-01` one · `M1-A-02` two |\n\n"
                                  "## Lanes\n\n| `M9-Z-01` not a ticket of a milestone |\n", encoding="utf-8")
    run(d, "ticket", "M1-A-01", "--dod", "yes", "--verified", "pytest -> 1 passed", "--doc", "docs/features/a.md")
    code, out = run(d, "next")
    if "Next: /ship M1-A-01 - built, not shipped yet" not in out:  # 2.1 (#62): a built ticket's next step is its PR
        fails.append(f"a built, unshipped ticket should make /ship the next step: {out.strip()}")
    st = status.Status.load(d / "STATUS.md")
    st.rows["Releases"].append([TODAY, "M1-A-01: one", "R1 clean", "none", "README", "CHANGELOG.md", "revert", "#1"])
    st.save(d / "STATUS.md")
    code, out = run(d, "next")
    if "Next: /build M1-A-02 - merge the shipped PR first (#1)" not in out or "not yet: M1-A-02" not in out:
        fails.append(f"build with an unrecorded ticket should stay the next phase: {out.strip()}")
    run(d, "ticket", "M1-A-02", "--dod", "yes", "--verified", "pytest -> 2 passed", "--doc", "docs/features/b.md")
    st = status.Status.load(d / "STATUS.md")
    st.rows["Releases"].append([TODAY, "M1-A-02: two", "R1 clean", "none", "README", "CHANGELOG.md", "revert", "#2"])
    st.save(d / "STATUS.md")
    code, out = run(d, "next")
    if "Next: /dev-check" not in out:
        fails.append(f"every ticket recorded should move on to /dev-check: {out.strip()}")
    code, _ = run(d, "set", "dev-check", "filled")
    if code == 0:
        fails.append("a verification phase was set filled without --verdict")
    code, _ = run(d, "set", "scope", "filled", "--verdict", "pass")
    if code == 0:
        fails.append("--verdict was accepted on a phase that is not a verification gate")
    run(d, "set", "dev-check", "filled", "--verdict", "fail")
    code, out = run(d, "next")
    if "Next: /dev-check - last verdict FAIL" not in out:
        fails.append(f"a FAIL verdict should keep the project at /dev-check: {out.strip()}")
    real_gaps, status.dev_check_gaps = status.dev_check_gaps, lambda st: []  # the chain's order, not the gate's checks
    try:
        run(d, "set", "dev-check", "filled", "--verdict", "pass")
    finally:
        status.dev_check_gaps = real_gaps
    code, out = run(d, "next")
    if "Next: /test" not in out:
        fails.append(f"a PASS verdict should move on to /test: {out.strip()}")


def test_bypass(d: Path, fails: list[str]) -> None:
    fresh(d, ui="no")
    run(d, "set", "vision", "filled")
    run(d, "set", "validate", "filled")
    code, out = run(d, "bypass", "--from", "plan", "--gate", "scope", "--reason", "we know the scope")
    run(d, "set", "plan", "filled")
    code, out = run(d, "next")
    if "Next: /scope" not in out or "bypassed /scope" not in out:
        fails.append(f"a bypassed gate should stay owed and be surfaced: {out.strip()}")
    code, out = run(d, "bypass", "--from", "plan", "--gate", "vision", "--reason", "x")
    if code == 0:
        fails.append("a bypass of a gate that is already met was accepted")
    run(d, "set", "scope", "filled")
    code, out = run(d, "next")
    if "bypassed /scope" in out:
        fails.append(f"filling the bypassed phase should close its bypass item: {out.strip()}")


def test_override_carries(d: Path, fails: list[str]) -> None:
    """One override of a running gate carries to the later phases until the gate is filled or overdue: the owner
    answered the same reason at /architect, /structure and again at every phase before this."""
    fresh(d, ui="no")
    for p in ("vision", "scope", "plan"):
        run(d, "set", p, "filled")
    run(d, "set", "validate", "running", "--due", "2026-10-01", "--reason", "trial")
    run(d, "bypass", "--from", "architect", "--gate", "validate", "--reason", "test project")
    run(d, "set", "architect", "filled")
    code, out = run(d, "next")
    if "Next: /structure - proceeding under the override recorded at /architect" not in out or "BLOCKED" in out:
        fails.append(f"the /architect override should carry to /structure: {out.strip()}")
    code, out = run(d, "bypass", "--from", "structure", "--gate", "validate", "--reason", "same again")
    st = status.Status.load(d / "STATUS.md")
    if "already covered" not in out or len(st.rows["Open items"]) != 1:
        fails.append(f"a second override of a carried gate should record nothing: {out.strip()}")
    with contextlib.redirect_stdout(io.StringIO()):  # a later day: the running gate is now past its due date
        status.main(["--file", str(d / "STATUS.md"), "--today", "2026-10-05", "set", "structure", "filled"])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):  # overdue is judged by today, not by a date stored in the file
        status.main(["--file", str(d / "STATUS.md"), "--today", "2026-10-05", "next"])
    out = buf.getvalue()
    if "BLOCKED" not in out:
        fails.append(f"once the running gate is overdue, the override stops carrying and the gate asks again: "
                     f"{out.strip()}")


PRODUCT = """# PRODUCT — Demo

_Last updated: 2026-09-20 · Stage: build · AI product? yes_

## Vision            <!-- /vision -->
- **Who it's for:** small shops

## Validation        <!-- /validate -->
_Running 2026-09-10, due 2026-09-30: pre-sale count._
_**Override 2026-09-12: "moving on anyway" — bypassed this phase's gate.**_
- **Assumption under test:** shops pay

## Scope             <!-- /scope -->
- **THE core feature:**
- **Detail:** `docs/scope.md` (reasoning + workings; this section stays a RECORD)

## Architecture      <!-- /architect -->
- **Stack + tools:** Python
_**Override 2026-09-13 (1 of 2): "later" — bypassed this phase's identity-custody criterion.**_

## Design             <!-- /design-system -->
- **Has user-facing UI?** no

## Tests             <!-- /test -->
_Not run 2026-09-21: `#Dev-complete` is empty — run `/dev-check` first._

## Build log         <!-- /build -->
| Feature | DoD (incl. security) met? | How verified | Doc |
|---|---|---|---|
| `T-1` login | yes | `pytest -q` -> 3 passed | docs/features/login.md |
Old paragraph that belongs to no row.

## Ship log          <!-- /ship -->
| Date | What shipped | Review + /security-review | Skipped phases | Docs reconciled | CHANGELOG | Rollback / flag | PR |
|---|---|---|---|---|---|---|---|
"""


def test_migrate(d: Path, fails: list[str]) -> None:
    fresh(d)
    (d / "STATUS.md").unlink()
    (d / "PRODUCT.md").write_text(PRODUCT, encoding="utf-8")
    code, out = run(d, "migrate", "--write")
    if code != 0:
        fails.append(f"migrate failed: {out.strip()}")
        return
    st = status.Status.load(d / "STATUS.md")
    want = {"vision": "filled", "validate": "overridden", "scope": "empty", "architect": "filled",
            "test": "declined", "build": "filled", "ship": "empty"}
    got = {p: st.state(p) for p in want}
    if got != want:
        fails.append(f"migrate states {got} != {want}")
    if st.header["AI product"] != "yes" or st.header["UI"] != "no":
        fails.append(f"migrate header wrong: {st.header}")
    if not any("identity-custody" in r[3] for r in st.rows["Open items"]):
        fails.append("a criterion override did not become an open item")
    new = (d / "PRODUCT.md").read_text(encoding="utf-8")
    arch = (d / "docs" / "status-archive.md").read_text(encoding="utf-8")
    if "identity-custody" not in new:
        fails.append("a criterion override was removed from PRODUCT.md (it is part of the section's record)")
    for line in PRODUCT.splitlines():
        if line and line not in new.splitlines() and line not in arch.splitlines():
            fails.append(f"migrate lost a line: {line!r}")
    code, out = run(d, "check", "--product", "PRODUCT.md")
    if code != 0:
        fails.append(f"check after migrate failed: {out.strip()}")
    (d / "PRODUCT.md").write_text(new + "\n_Not run 2026-09-24: x — run `/plan` first._\n", encoding="utf-8")
    code, out = run(d, "check", "--product", "PRODUCT.md")
    if code == 0:
        fails.append("check passed a PRODUCT.md that still holds a Not run line")


def test_agent_flag(d: Path, fails: list[str]) -> None:
    """The agent track: an Agent flag next to UI and AI, asked before /architect, refused on a non-AI product,
    and an older STATUS.md without the field still reads as unknown."""
    fresh(d, ai="yes")
    for p in ("vision", "validate", "scope", "plan"):
        run(d, "set", p, "filled")
    code, out = run(d, "next")
    if "Agent flag unknown" not in out:
        fails.append(f"an AI product at /architect with no Agent flag should be told to ask: {out.strip()}")
    run(d, "flag", "--agent", "yes")
    text = (d / "STATUS.md").read_text(encoding="utf-8")
    if "· Agent: yes" not in text:
        fails.append(f"flag --agent yes did not reach the header: {text.splitlines()[4]}")
    code, out = run(d, "next")
    if "has a section for /architect, /structure, /foundation" not in out:
        fails.append(f"Agent: yes should list the phases AGENT.md has sections for: {out.strip()}")
    run(d, "set", "validate", "filled", "--note", "done")
    run(d, "set", "architect", "filled")
    code, out = run(d, "next")
    if "any other phase has none" not in out:
        fails.append(f"Agent: yes should say phases without a section have nothing to apply: {out.strip()}")
    fresh(d, ai="no")
    code, _ = run(d, "flag", "--agent", "yes")
    if code == 0:
        fails.append("an agent was flagged on a product recorded as not using AI")
    old = text.replace(" · Agent: yes", "")
    if status.Status.parse(old).header["Agent"] != "unknown":
        fails.append("a STATUS.md written before the Agent field should read Agent as unknown")


def test_rules_version_and_rerun(d: Path, fails: list[str]) -> None:
    """From the agent test's /structure re-run: Gemini skipped the conditional AGENT.md line (Y1), asked "re-run?"
    and recommended no (Y2), and /architect, filled before the framework table existed, was never flagged (Y3)."""
    fresh(d, ai="yes")
    for p in ("vision", "validate", "scope", "plan"):
        run(d, "set", p, "filled")
    run(d, "flag", "--agent", "yes")
    run(d, "set", "architect", "filled")
    row = next(r for r in status.Status.load(d / "STATUS.md").rows["Phases"]
               if r[0] == "architect")
    if len(row) != 7 or row[6] != status.playbook_version():
        fails.append(f"set filled should record the playbook version in the Rules column: {row}")
    code, out = run(d, "next", "--phase", "structure")
    if "AGENT.md §Structure, word for word" not in out or "a home for every agent part" not in out:
        fails.append(f"next --phase structure on an agent product should print AGENT.md §Structure: {out}")
    code, out = run(d, "next", "--phase", "architect")
    if "RE-RUN" not in out or "never ask whether to re-run" not in out:
        fails.append(f"next --phase on a filled phase should give the re-run order: {out}")
    code, out = run(d, "next", "--phase", "design-system")
    if "no section for /design-system" not in out:
        fails.append(f"next --phase on a phase AGENT.md has no section for should say so: {out}")
    code, out = run(d, "next", "--phase", "nonsense")
    if code == 0:
        fails.append("next --phase with an unknown phase should be refused")
    # A row filled before versions were recorded (a 6-column file) or under an older version is flagged.
    text = (d / "STATUS.md").read_text(encoding="utf-8")
    old = text.replace("| Note | Rules |", "| Note |").replace("|---|---|---|---|---|---|---|", "|---|---|---|---|---|---|")
    old = "\n".join(re.sub(r" \| [^|]* \|$", " |", l) if l.startswith("| ") and l.split(" | ")[0][2:] in status.CHAIN
                    else l for l in old.splitlines()) + "\n"
    (d / "STATUS.md").write_text(old, encoding="utf-8")
    code, out = run(d, "check")
    if code != 0:
        fails.append(f"a STATUS.md written before the Rules column should still be valid: {out}")
    code, out = run(d, "next")
    if "rules changed since #architect was filled" not in out or "framework" not in out:
        fails.append(f"a phase filled before a rule change should be flagged with the change: {out}")
    if 'status.py set architect filled --note "kept:' not in out:
        fails.append(f"the rule-change note should print how to keep the section as it is: {out}")
    run(d, "set", "architect", "filled")
    code, out = run(d, "next")
    if "rules changed since #architect" in out:
        fails.append(f"a re-filled phase should no longer be flagged: {out}")
    st = status.Status.load(d / "STATUS.md")
    st.phase("architect")[6] = "1.73.0-next.13"
    (d / "STATUS.md").write_text(st.render(), encoding="utf-8")
    code, out = run(d, "next")
    if "rules changed since #architect was filled under 1.73.0-next.13" not in out:
        fails.append(f"a phase filled under an older version should be flagged: {out}")
    fresh(d, ai="yes")
    for p in ("vision", "validate", "scope", "plan", "architect"):
        run(d, "set", p, "filled")
    run(d, "flag", "--agent", "no")
    st = status.Status.load(d / "STATUS.md")
    st.phase("architect")[6:] = [""]
    (d / "STATUS.md").write_text(st.render(), encoding="utf-8")
    code, out = run(d, "next")
    if "rules changed" in out:
        fails.append(f"an agent-track rule change should not flag a product that is not an agent: {out}")


GOOD_STRUCTURE = """# STRUCTURE

```
app/
├── orders/      # order lookup
│   └── tests/
scripts/         # project checks
```

## Modules

| Module | What |
|---|---|
| `app/orders` | order lookup |

## Inside a module

`service.py` · `tests/`

## Where does a new file go?

A route: its module.

## Where decisions live

| Decision | Home |
|---|---|
| checks | `scripts/check_structure.py` |

## Hub files

| File | Why |
|---|---|
| `scripts/check_structure.py` | the map check |
"""


def test_phase_runs_its_own_checks(d: Path, fails: list[str]) -> None:
    """R1 + R2: a model that never runs the phase's check could still mark the phase done. `set structure filled`
    runs the current structure check itself and needs the committed copy; `set design-system filled` runs the
    audit engine; `next` re-runs the checks of every filled phase and names one that fails now."""
    # /structure's close checks the whole record, so this runs on test_structure_close.py's realistic one
    import test_structure_close as tsc
    tsc.hr_project(d)
    (d / "scripts/check_structure.py").unlink()
    code, out = tsc.close(d)
    if code == 0 or "check_structure.py" not in out:
        fails.append(f"set structure filled with no committed check_structure.py should be refused: {out}")
    (d / "scripts/check_structure.py").write_text((ROOT / "templates/check_structure.py").read_text(encoding="utf-8"),
                                                  encoding="utf-8")
    code, out = tsc.close(d)
    if code != 0:
        fails.append(f"a structure that passes its check should be filled: {out}")
    (d / "app/billing").mkdir(parents=True)  # a folder on disk that the map never drew
    code, out = tsc.close(d)
    if code == 0 or "billing" not in out:
        fails.append(f"set structure filled should run the check and refuse on a failure: {out}")
    code, out = run(d, "next")
    if "#structure's check fails now" not in out or "billing" not in out:
        fails.append(f"next should re-run a filled phase's check and name what fails now: {out}")
    (d / "app/billing").rmdir()
    (d / "DESIGN.md").write_text("# DESIGN\n\n```css\n:root { --background: #ffffff; --foreground: #fefefe; }\n```\n",
                                 encoding="utf-8")
    code, out = run(d, "set", "design-system", "filled")
    if code == 0 or "audit" not in out:
        fails.append(f"set design-system filled should run the audit engine and refuse on a failed law: {out}")
    (d / "DESIGN.md").unlink()
    code, out = run(d, "set", "design-system", "filled")
    if code == 0 or "DESIGN.md" not in out:
        fails.append(f"set design-system filled with no DESIGN.md should be refused: {out}")
    # V2: an audit that checked nothing is not a pass, unless the user's override is recorded
    (d / "DESIGN.md").write_text("# DESIGN\n\nThe host's own components; no tokens.\n", encoding="utf-8")
    code, out = run(d, "set", "design-system", "filled")
    if code == 0 or "checked 0 things" not in out:
        fails.append(f"a DESIGN.md the audit checks nothing in should be refused: {out}")
    (d / "PRODUCT.md").write_text("## Structure\n- **Shape:** modules\n\n## Design\n- Override 2026-09-26: the user "
                                  "chose the host's look, no own tokens\n", encoding="utf-8")
    code, out = run(d, "set", "design-system", "filled")
    # the bare fixture is refused for /design-system's record gaps (tools/test_design_close.py); this rule's own
    # message must be gone
    if "checked 0 things" in out:
        fails.append(f"0 checks with the user's override recorded in #Design should be accepted: {out}")
    # D2: the token stylesheet DESIGN.md names is imported by an app file, or an open item hands it to /foundation
    # (the fixture's app/ui and docs/design are not in its small map: recorded, so #structure's gate lets this pass)
    run(d, "open", "--from", "design-system", "--what", "Override: #structure's check fails - test fixture folders",
        "--clears", "#structure's check passes")
    tokens = (":root { --background: oklch(1 0 0); --foreground: oklch(0.2 0 0); --primary: oklch(0.45 0.1 250); "
              "--primary-foreground: oklch(1 0 0); }\n.dark { --background: oklch(0.15 0 0); --foreground: "
              "oklch(0.95 0 0); --primary: oklch(0.7 0.1 250); --primary-foreground: oklch(0.1 0 0); }")
    (d / "DESIGN.md").write_text(f"# DESIGN\n\nStylesheet: `app/ui/tokens.css`\n\n```css\n{tokens}\n```\n",
                                 encoding="utf-8")
    (d / "app/ui").mkdir(parents=True, exist_ok=True)
    (d / "app/ui/tokens.css").write_text(tokens, encoding="utf-8")
    (d / "docs/design").mkdir(parents=True, exist_ok=True)
    (d / "docs/design/sample.html").write_text('<link rel="stylesheet" href="../../app/ui/tokens.css">',
                                               encoding="utf-8")
    code, out = run(d, "set", "design-system", "filled")
    if code == 0 or "imported by no app file" not in out:
        fails.append(f"a token stylesheet only a docs/ sample links should be refused: {out}")
    code, out = run(d, "open", "--from", "design-system", "--what", "the root entry imports tokens.css",
                    "--clears", "/foundation creates the entry")
    n = re.search(r"\d+", out)
    code, out = run(d, "set", "design-system", "filled")
    if "imported by no app file" in out:
        fails.append(f"an open item handing the tokens.css import to /foundation should answer D2: {out}")
    run(d, "close", n.group(0) if n else "1", "--how", "test")
    (d / "app/ui/base.html").write_text('<link rel="stylesheet" href="/static/tokens.css">', encoding="utf-8")
    code, out = run(d, "set", "design-system", "filled")
    if "imported by no app file" in out:
        fails.append(f"a token stylesheet the app's base page imports should answer D2: {out}")
    import shutil
    shutil.rmtree(d / "docs")
    shutil.rmtree(d / "app/ui")
    (d / "DESIGN.md").unlink()
    for f in ("PRODUCT.md", "STRUCTURE.md"):
        (d / f).unlink()


def test_provenance_values(d: Path, fails: list[str]) -> None:
    """Q2: a logged run wrote "default taken, confirmed by user" 35 times - a third value that claims a choice the
    user never made. `set architect filled` refuses it; the two real values, and a bare mention in a superseded
    note, pass."""
    fresh(d, ui="no")
    for p in ("vision", "validate", "scope", "plan"):
        run(d, "set", p, "filled")
    ok = ("## Architecture\n- **Stack:** FastAPI (_default taken, not user-chosen_) · Postgres (_user-chosen_)\n"
          "- superseded 2026-09-25: \"a plain loop\" (ADR-0005, default taken)\n")
    (d / "PRODUCT.md").write_text(ok, encoding="utf-8")
    code, out = run(d, "set", "architect", "filled")  # a partial record: the full check refuses it for other gaps
    if "provenance" in out and "is not one of the two values" in out:
        fails.append(f"the two provenance values should pass: {out}")
    (d / "PRODUCT.md").write_text(ok.replace("default taken, not user-chosen", "default taken, confirmed by user"),
                                  encoding="utf-8")
    code, out = run(d, "set", "architect", "filled")
    if code == 0 or "confirmed by user" not in out:
        fails.append(f"a third provenance value should be refused, naming it: {out}")
    # G2: an AI product's model row carries its release date; a model id stamped over a year ago is refused.
    fresh(d, ui="no", ai="yes")
    for p in ("vision", "validate", "scope", "plan"):
        run(d, "set", p, "filled")
    ai_ok = ("## Architecture\n- **Model:** `claude-opus-5`, released 2026-07-24 (search 16) (_user-chosen_)\n"
             "- superseded 2026-09-25: `claude-3-5-haiku-20241022` was the first pick\n")
    (d / "PRODUCT.md").write_text(ai_ok, encoding="utf-8")
    code, out = run(d, "set", "architect", "filled")  # a partial record: only the model rule is under test here
    if "rule S" in out:
        fails.append(f"a current model with its release date should pass (a superseded old id is a quotation): {out}")
    (d / "PRODUCT.md").write_text("## Architecture\n- **Model:** `claude-3-5-haiku-20241022` · `gpt-4o-mini`, "
                                  "released 2024-10-22 (_default taken, not user-chosen_)\n", encoding="utf-8")
    code, out = run(d, "set", "architect", "filled")
    if code == 0 or "claude-3-5-haiku-20241022" not in out:
        fails.append(f"a model id stamped over a year ago should be refused, naming it: {out}")
    (d / "PRODUCT.md").write_text("## Architecture\n- **Model:** `gpt-5-mini` (_default taken, not user-chosen_)\n",
                                  encoding="utf-8")
    code, out = run(d, "set", "architect", "filled")
    if code == 0 or "released" not in out:
        fails.append(f"an AI product's #Architecture with no model release date should be refused: {out}")


def test_evidence_and_foundation_checks(d: Path, fails: list[str]) -> None:
    """E1: an evidence line's files and tests must exist (a logged run cited ten tests nobody wrote). /foundation's
    own check: hooks installed (E6), a lockfile per manifest (E10), no fallback for a CHANGE_ME variable (E3), the
    test datastore on #Architecture's engine (E4), CI ran or an open item says so (E5). E7: `next` names an
    uncommitted STATUS.md. Each is proven red before green."""
    import shutil
    for sub in d.iterdir():
        if sub.is_dir():
            shutil.rmtree(sub)
    fresh(d)
    for p in ("vision", "validate", "scope", "plan", "architect", "structure"):
        st = status.Status.load(d / "STATUS.md")
        st.phase(p)[1:3] = ["filled", TODAY]
        (d / "STATUS.md").write_text(st.render(), encoding="utf-8")
    (d / "tests").mkdir()
    (d / "tests/test_guard.py").write_text("def test_refuses_dev():\n    assert True\n", encoding="utf-8")
    (d / "app").mkdir()
    (d / "app/loader.py").write_text('import os\nKEY = os.environ["APP_SECRET_KEY"]\n', encoding="utf-8")
    ev_ok = ("- `evidence: pytest tests/test_guard.py::test_refuses_dev → 1 passed · app/loader.py · 2026-09-26`\n"
             "- `evidence: planted a raw hex in app/ui/_planted.html; git commit → exit 1 · 2026-09-26`\n")
    ev_bad = "- `evidence: pytest tests/test_guard.py::test_never_written → 1 passed · tests/nope.py · 2026-09-26`\n"
    arch = "## Architecture\n- **Datastore:** PostgreSQL 17, managed\n\n"
    for text, want, why in ((ev_bad, "does not define", "a cited test the file does not define"),
                            (ev_bad, "tests/nope.py", "a cited file that does not exist")):
        (d / "PRODUCT.md").write_text(arch + "## Foundation\n" + text, encoding="utf-8")
        code, out = run(d, "set", "foundation", "filled")
        if code == 0 or want not in out:
            fails.append(f"E1: set foundation filled should refuse {why}: {out.strip()[:200]}")
    (d / "PRODUCT.md").write_text(arch + "## Foundation\n" + ev_ok, encoding="utf-8")
    code, out = run(d, "set", "foundation", "filled")
    if "evidence cites" in out:
        fails.append(f"E1: true evidence (and a planted-then-removed file) was refused: {out.strip()[:200]}")
    # the foundation gaps, one at a time, on a tree that meets all of them
    subprocess.run(["git", "init", "-q"], cwd=d)
    (d / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
    (d / ".git/hooks/pre-commit").write_text("#!/bin/sh\n", encoding="utf-8")
    (d / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (d / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    (d / ".env.example").write_text("APP_SECRET_KEY=CHANGE_ME__APP_SECRET_KEY__CHANGE_ME\n"
                                    "TEST_DATABASE_URL=postgresql://localhost/test\n", encoding="utf-8")
    (d / ".github/workflows").mkdir(parents=True)
    (d / ".github/workflows/ci.yml").write_text("jobs: {}\n", encoding="utf-8")
    ci_item = re.search(r"open item (\w+) recorded",
                        run(d, "open", "--from", "foundation", "--what", "CI has not run on a remote", "--clears",
                            "first push")[1]).group(1)
    if status.foundation_gaps(d):
        fails.append(f"a tree meeting every foundation check should have no gaps: {status.foundation_gaps(d)}")
    breaks = (("E6", lambda: (d / ".git/hooks/pre-commit").unlink(), "not installed",
               lambda: (d / ".git/hooks/pre-commit").write_text("#!/bin/sh\n", encoding="utf-8")),
              ("E10", lambda: (d / "uv.lock").unlink(), "no lockfile",
               lambda: (d / "uv.lock").write_text("version = 1\n", encoding="utf-8")),
              ("E3", lambda: (d / "app/loader.py").write_text(
                  'import os\nKEY = os.getenv("APP_SECRET_KEY", "dev-key")\n', encoding="utf-8"),
               "APP_SECRET_KEY a fallback", lambda: (d / "app/loader.py").write_text(
                  'import os\nKEY = os.environ["APP_SECRET_KEY"]\n', encoding="utf-8")),
              ("E4", lambda: (d / "tests/conftest.py").write_text('URL = "sqlite:///test.db"\n', encoding="utf-8"),
               "use SQLite", lambda: (d / "tests/conftest.py").unlink()),
              ("E5", lambda: run(d, "close", ci_item, "--how", "test"), "CI has never run", lambda: None))
    for name, brk, want, fix in breaks:
        brk()
        got = "; ".join(status.foundation_gaps(d))
        if want not in got:
            fails.append(f"{name}: the foundation check should report {want!r}: {got[:200]!r}")
        fix()
    # E7: an uncommitted STATUS.md is named by next
    subprocess.run(["git", "add", "-A"], cwd=d)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x", "--no-verify"], cwd=d)
    code, out = run(d, "next")
    if "STATUS.md has changes" in out:
        fails.append("E7: next warned about STATUS.md with nothing uncommitted")
    run(d, "open", "--from", "foundation", "--what", "x", "--clears", "y")
    code, out = run(d, "next")
    if "STATUS.md or status/ has changes that are not committed" not in out:
        fails.append(f"E7: next should name an uncommitted STATUS.md: {out.strip()[-200:]}")
    shutil.rmtree(d / ".git", onerror=lambda f, p, e: (os.chmod(p, 0o700), f(p)))
    for f in ("PRODUCT.md", ".pre-commit-config.yaml", "pyproject.toml", "uv.lock", ".env.example"):
        (d / f).unlink(missing_ok=True)
    for sub in ("tests", "app", ".github"):
        shutil.rmtree(d / sub, ignore_errors=True)


def test_contracts_checks(d: Path, fails: list[str]) -> None:
    """/contracts' own check, each claim proven red on a tree that meets all of them: C1 the record's paths exist,
    C2 a migration file and no schema built by app code, C3 an evidence line ran a migration, C4 no float money,
    C5 the tenant key on every table (or named with why), C6 an exported contract or N/A, C7 Agent: yes rows."""
    import shutil
    fresh(d)
    st = status.Status.load(d / "STATUS.md")
    st.header["Agent"] = "yes"
    (d / "STATUS.md").write_text(st.render(), encoding="utf-8")
    files = {
        "migrations/versions/0001_core.py": 'op.create_table("shops", sa.Column("id", sa.Text()))\n'
                                            'op.create_table("orders", sa.Column("shop_id", sa.Text()),\n'
                                            '    sa.Column("amount_cents", sa.BigInteger()))\n'
                                            'op.drop_table("orders")\n',
        "app/orders/schemas.py": "class Order(BaseModel):\n    amount_cents: int\n    feedback_score: float\n"
                                 "    total_tokens: float\n",
        "docs/contracts/openapi.v1.json": "{}\n",
    }
    for rel, text in files.items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text(text, encoding="utf-8")
    good = ("## Architecture\n- **Datastore:** PostgreSQL 17\n\n## Contracts\n"
            "- **Typed models / schemas / migrations:** `app/orders/schemas.py` · `migrations/versions/0001_core.py`\n"
            "  - `evidence: alembic upgrade head → 0001, exit 0 · 2026-09-26`\n"
            "- **Boundary units/scale agreed:** money in integer cents\n"
            "- **Contract versioning / back-compat approach:** /v1 additive-only · `docs/contracts/openapi.v1.json`\n"
            "- **PII/sensitive fields classified · tenant-owner key · idempotency/natural key:** `shop_id` on every "
            "table\n  - shops has no shop_id: it is the tenant table itself\n"
            "- **(Agent) the AGENT.md §Contracts rows (tool schemas · action policy · model output · trace · hand-off "
            "· eval case) — or N/A:** tool schemas `app/orders/schemas.py` · action policy N/A — none yet · model "
            "output N/A · trace N/A · hand-off N/A · eval case N/A\n")
    (d / "PRODUCT.md").write_text(good, encoding="utf-8")
    if status.contracts_gaps(d):
        fails.append(f"a tree meeting every contracts check should have no gaps: {status.contracts_gaps(d)}")
    sub = lambda old, new: (lambda: (d / "PRODUCT.md").write_text(good.replace(old, new), encoding="utf-8"))  # noqa
    put = lambda rel, text: (lambda: (d / rel).write_text(text, encoding="utf-8"))  # noqa: E731
    breaks = (
        ("C1", sub("`app/orders/schemas.py` ·", "`app/orders/models.py` ·"), "points at app/orders/models.py"),
        ("C2 none", lambda: (d / "migrations/versions/0001_core.py").rename(d / "core.bak"), "no migration file"),
        ("C2 boot", put("app/db.py", "Base.metadata.create_all(engine)\n"), "app/db.py builds the schema"),
        ("C3", sub("alembic upgrade head", "pytest"), "ran a migration"),
        ("C4 py", put("app/orders/schemas.py", "class Order(BaseModel):\n    refund_amount: float\n"),
         "(refund_amount)"),
        ("C4 sql", put("migrations/versions/0002.sql", "CREATE TABLE fees (\n  shop_id text,\n  unit_price REAL\n);\n"),
         "(unit_price)"),
        ("C5 table", sub("  - shops has no shop_id: it is the tenant table itself\n", ""), "table shops"),
        ("C5 key", sub("`shop_id` on every", "a shop key on every"), "names no tenant key"),
        ("C6", sub(" · `docs/contracts/openapi.v1.json`", ""), "no exported contract file"),
        ("C7", sub("eval case N/A", ""), "lacks eval case"),
    )
    for name, brk, want in breaks:
        brk()
        got = "; ".join(status.contracts_gaps(d))
        if want not in got:
            fails.append(f"{name}: the contracts check should report {want!r}: {got[:240]!r}")
        (d / "PRODUCT.md").write_text(good, encoding="utf-8")
        if (d / "core.bak").exists():
            (d / "core.bak").rename(d / "migrations/versions/0001_core.py")
        (d / "app/db.py").unlink(missing_ok=True)
        (d / "migrations/versions/0002.sql").unlink(missing_ok=True)
        (d / "app/orders/schemas.py").write_text(files["app/orders/schemas.py"], encoding="utf-8")
    # the exemptions: a float named on a line of #Contracts with why; a versioning field that says N/A
    put("app/orders/schemas.py", "class Order(BaseModel):\n    price_per_mtok: float\n")()
    sub("money in integer cents", "money in integer cents; `price_per_mtok` stays a float: a vendor rate")()
    if status.contracts_gaps(d):
        fails.append(f"a float named in #Contracts with why should pass: {status.contracts_gaps(d)}")
    sub(" · `docs/contracts/openapi.v1.json`", " · N/A — nothing outside the app calls it")()
    (d / "docs/contracts/openapi.v1.json").unlink()
    if any("exported contract" in g for g in status.contracts_gaps(d)):
        fails.append("a versioning field saying N/A should need no exported contract")
    put("app/db.py", "Base.metadata.create_all(engine)\n")()
    code, out = run(d, "set", "contracts", "filled")
    if code == 0 or "app/db.py builds the schema" not in out:
        fails.append(f"set contracts filled should run the contracts check: {out.strip()[:200]}")
    for f in ("PRODUCT.md",):
        (d / f).unlink(missing_ok=True)
    for s in ("migrations", "app", "docs"):
        shutil.rmtree(d / s, ignore_errors=True)


CONTRACTS_START_MAX = 23700  # characters on the test project (23.1K); a realistic one printed 24.3K (P47)


def test_contracts_close(d: Path, fails: list[str]) -> None:
    """/contracts' own close (next.68): one start call; `set contracts filled` names an earlier phase's failing check
    and the record's gaps in ONE refusal, and --dry-run lists them all; at its own close only, the pay words of a
    payroll product, a float value in code or config, the tenant sentence and docs/contracts.md's shape; a library
    in .venv is never the project's code; a rate is not money. Every break is named on a tree that passes."""
    import shutil
    fresh(d)
    st = status.Status.load(d / "STATUS.md")
    st.header.update({"Agent": "yes", "AI product": "yes", "UI": "yes"})
    (d / "STATUS.md").write_text(st.render(), encoding="utf-8")
    files = {
        "migrations/versions/0001_core.py": 'op.create_table("employers", sa.Column("id", sa.Text()))\n'
                                            'op.create_table("payslips", sa.Column("employer_id", sa.Text()),\n'
                                            '    sa.Column("net_pay_cents", sa.BigInteger()))\n'
                                            'op.create_table("agent_events", sa.Column("employer_id", sa.Text()),\n'
                                            '    sa.Column("run_id", sa.Text()))\n',
        "app/payroll/schemas.py": "class Payslip(BaseModel):\n    net_pay_cents: int\n    rate_bp: int\n",
        "config/product.yaml": "run_caps:\n  spend_micro_eur: 100000   # EUR 0.10 per answer\n  wall_time_s: 120\n",
        "docs/contracts/agent.schema.json": "{}\n",
        "docs/contracts.md": "# Contracts\n\n## 1. Overview\n\nPayslips per employer.\n\n```mermaid\nerDiagram\n"
                             "    employers ||--o{ payslips : employer_id\n```\n\n## 2. PII\n\n| Field | Why | How long "
                             "| Deletion |\n|---|---|---|---|\n| payslips | answers | 24 months | purge job |\n\n"
                             "## 3. Owner's answers\n\n1. Nothing outside the app calls it.\n",
    }
    for rel, text in files.items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text(text, encoding="utf-8")
    good = ("## Architecture\n- **Datastore:** PostgreSQL 17\n\n## Contracts\n"
            "- **Typed models / schemas / migrations:** `app/payroll/schemas.py` · `migrations/versions/0001_core.py`\n"
            "  - `evidence: alembic upgrade head → 0001, exit 0 · migrations/versions/0001_core.py · 2026-10-04`\n"
            "- **Boundary units/scale agreed:** money in integer euro cents; rates in basis points\n"
            "- **Contract versioning / back-compat approach:** N/A — nothing outside the app calls it; agent schemas "
            "in `docs/contracts/agent.schema.json`\n"
            "- **PII/sensitive fields classified · tenant-owner key · idempotency/natural key:** tenant key "
            "`employer_id` on every table.\n  - `employers` has no tenant key: it is the tenant table itself.\n"
            "  - Idempotency: agent event (`run_id`, `step`).\n"
            "- **(Agent) the AGENT.md §Contracts rows (tool schemas · action policy · model output · trace · hand-off "
            "· eval case) — or N/A:** tool schemas N/A · action policy N/A · model output N/A · trace N/A · hand-off "
            "N/A · eval case N/A\n"
            "- **Detail:** `docs/contracts.md` (reasoning + workings; this section stays a RECORD)\n")
    (d / "PRODUCT.md").write_text(good, encoding="utf-8")
    if status.contracts_gaps(d, close=True):
        fails.append(f"a payroll tree meeting every /contracts close check should pass: "
                     f"{status.contracts_gaps(d, close=True)}")
    put = lambda rel, text: (d / rel).parent.mkdir(parents=True, exist_ok=True) or (d / rel).write_text(  # noqa
        text, encoding="utf-8")
    sub = lambda rel, old, new: put(rel, (d / rel).read_text(encoding="utf-8").replace(old, new))  # noqa: E731
    breaks = (  # (name, break, the words the close names, also named outside the close?)
        ("pay word", lambda: sub("app/payroll/schemas.py", "net_pay_cents: int", "net_pay: float"), "(net_pay)", False),
        ("config value", lambda: sub("config/product.yaml", "spend_micro_eur: 100000", "spend_eur: 0.10"),
         "config/product.yaml keeps money", False),
        ("code value", lambda: put("app/agent/runner.py", 'run(spend_cap=state.get("spend_cap", 0.10))\n'),
         "(spend_cap)", False),
        ("tenant sentence", lambda: sub("migrations/versions/0001_core.py",
                                        'op.create_table("agent_events", sa.Column("employer_id", sa.Text()),',
                                        'op.create_table("agent_events",'), "table agent_events", False),
        ("no overview", lambda: sub("docs/contracts.md", "## 1. Overview", "## 1. Notes"), "start with `## Overview`",
         False),
        ("no diagram", lambda: sub("docs/contracts.md", "```mermaid", "```text"), "start with `## Overview`", False),
        ("no PII table", lambda: sub("docs/contracts.md", "| Field | Why | How long | Deletion |",
                                     "| Table | Notes | Owner | Size |"), "no personal-data table", False),
        ("no owner's answers", lambda: sub("docs/contracts.md", "## 3. Owner's answers", "## 3. Answers"),
         "no `## Owner's answers`", False),
        ("Any money", lambda: put("app/agent/caps.py", "class Caps:\n    refund_cap: Any = None\n"), "(refund_cap)",
         True),
    )
    for name, brk, want, always in breaks:
        snap = {rel: (d / rel).read_text(encoding="utf-8") for rel in files}
        brk()
        got = "; ".join(status.contracts_gaps(d, close=True))
        if want not in got:
            fails.append(f"/contracts close, {name}: expected {want!r}: {got[:240]!r}")
        if (want in "; ".join(status.contracts_gaps(d))) != always:  # phase_check: never blocks a later phase
            fails.append(f"/contracts {name}: {'missing from' if always else 'must stay out of'} phase_check")
        for rel, text in snap.items():
            (d / rel).write_text(text, encoding="utf-8")
        for rel in ("app/agent/runner.py", "app/agent/caps.py"):
            (d / rel).unlink(missing_ok=True)
    # #43 items 2 + 4: the personal-data table is read by its columns, any heading; every heading numbered (#60)
    snap = (d / "docs/contracts.md").read_text(encoding="utf-8")
    sub("docs/contracts.md", "## 2. PII", "## 2. Personal data")
    if status.contracts_gaps(d, close=True):
        fails.append(f"a numbered docs/contracts.md with a `## 2. Personal data` table should pass: "
                     f"{status.contracts_gaps(d, close=True)}")
    (d / "docs/contracts.md").write_text(snap, encoding="utf-8")
    # not money, not the project's code: never a refusal
    put("app/payroll/rates.py", "class Line:\n    withholding_tax_rate: float\n    feedback_score: float\n")
    put(".venv/Scripts/charge.py", "class Charge:\n    amount: float\n")  # the folder's name
    put("env313/Lib/site-packages/sqlmodel/main.py", "SQLModel.metadata.create_all(engine)\n")  # a venv of any name
    if status.contracts_gaps(d, close=True) or status.contracts_gaps(d):
        fails.append(f"a rate, a score or a library in a project environment is no /contracts gap: "
                     f"{status.contracts_gaps(d, close=True)}")
    # a float rate is a WARNING (owner default 2026-10-04): integer basis points are recommended, never refused
    warns = "; ".join(status.contracts_warnings(d))
    if "withholding_tax_rate" not in warns or "basis points" not in warns or "feedback_score" in warns             or ".venv" in warns:
        fails.append(f"a float rate should be warned (basis points), a score and a library not: {warns!r}")
    # #43 item 1: a score compared with a threshold is warned (basis points), never refused; a lone score is not
    put("app/payroll/review.py", "class Gate:\n    approve_threshold: float = 0.8\n")
    warns = "; ".join(status.contracts_warnings(d))
    if "approve_threshold" not in warns or "feedback_score" not in warns or "0.78 = 7800" not in warns:
        fails.append(f"a float threshold and the scores compared with it should be warned: {warns!r}")
    if status.contracts_gaps(d, close=True):
        fails.append(f"a float threshold is a warning, never a refusal: {status.contracts_gaps(d, close=True)}")
    (d / "app/payroll/review.py").unlink()
    for p in (".venv", "env313"):
        shutil.rmtree(d / p)
    (d / "app/payroll/rates.py").unlink()
    if status.contracts_warnings(d):
        fails.append(f"rates kept in basis points need no warning: {status.contracts_warnings(d)}")
    # ONE refusal: an earlier filled phase's failing check and the record's own gap together; --dry-run lists both
    st = status.Status.load(d / "STATUS.md")
    for p in ("vision", "scope", "plan", "architect", "structure"):
        st.phase(p)[1:3] = ["filled", TODAY]
    (d / "STATUS.md").write_text(st.render(), encoding="utf-8")  # structure filled, no STRUCTURE.md: its check fails
    sub("app/payroll/schemas.py", "net_pay_cents: int", "net_pay: float")
    section = d.parent / f"{d.name}-contracts-section.md"
    section.write_text(status.product_sections(good)["Contracts"], encoding="utf-8")
    before = (d / "PRODUCT.md").read_text(encoding="utf-8")
    code, out = run(d, "set", "contracts", "filled", "--section-from", str(section), "--dry-run")
    if code != 0 or "DRY RUN" not in out or "#structure's check fails now" not in out or "(net_pay)" not in out:
        fails.append(f"set contracts filled --dry-run should list the earlier gate AND the record's gaps: {out[:400]!r}")
    if (d / "PRODUCT.md").read_text(encoding="utf-8") != before or status.Status.load(d / "STATUS.md").state(
            "contracts") != "empty":
        fails.append("--dry-run must write nothing")
    code, out = run(d, "set", "contracts", "filled", "--section-from", str(section))
    if code == 0 or "#structure's check fails now" not in out or "(net_pay)" not in out:
        fails.append(f"set contracts filled should name the earlier gate and its own gaps in ONE refusal: {out[:400]!r}")
    # the start: one call, the questions, the steps and proofs, the record's shape, the refusal list - not the close
    code, out = run(d, "next", "--phase", "contracts")
    for want in ("This phase closes with ONE call - `status.py set contracts filled", "Round 1 - ONE message",
                 "1. Who calls it from outside the app", "3. How long is each kind of personal data kept",
                 "## 2. Persistence schema and a migration", "## Migration applies", "- **Typed models / schemas / "
                 "migrations:**", "`set contracts filled` refuses, every problem in one list", "## §Context hygiene",
                 "## §Contracts — the agent's typed shapes", "What this phase must NOT do", "--dry-run",
                 "STRUCTURE.md's map"):
        if want not in out:
            fails.append(f"next --phase contracts should print {want!r}")
    for close_only in ("## §Step 3b", "## §Commit the work", "## §Plain-language close", "## The exit-criteria gate"):
        if close_only in out:
            fails.append(f"next --phase contracts prints {close_only!r} - the close's rules come with `set`")
    if "status.py rules contracts`" in out.split("/contracts start")[0]:
        fails.append("the start is one call: it must not send the run to `status.py rules contracts`")
    if len(out.encode("utf-8")) > 34 * 1024:
        fails.append(f"next --phase contracts is {len(out.encode('utf-8')) // 1024} KB - over its 34 KB budget")
    # P47: a size rule needs a check - a realistic project's start (31K before, over Claude Code's 30K cut) must stay
    # under 25,000 characters; this test project prints ~1.3K less
    if len(out) > CONTRACTS_START_MAX:
        fails.append(f"next --phase contracts prints {len(out)} characters on the test project - over "
                     f"{CONTRACTS_START_MAX}: a realistic project's start would pass 25,000 (P47)")
    # P46: reads and questions first, docs/contracts.md last - after round 2, saved in the same message
    for want in ("reads first, the long document last", "in ONE call now",
                 "no confirm or save question: docs/contracts.md", "after it in that same message, `set contracts"):
        if want not in out:
            fails.append(f"next --phase contracts should give the P46 order: {want!r}")
    if "Personal data` (a table" in out:
        fails.append("next --phase contracts should leave docs/contracts.md's shape to the dry-run (P46)")
    # /foundation is not filled here: the run may stop or go on - both commands printed, the section by name (its
    # ~900 characters put the start over the size cap on a real install's long path)
    if ("status.py set contracts declined --reason" not in out or "status.py bypass --from contracts --gate"
            not in out or "## §Declined runs" in out):
        fails.append("next --phase contracts should print §Declined runs' two commands while an earlier gate is "
                     "unmet, and the section by name")
    st = status.Status.load(d / "STATUS.md")
    st.phase("foundation")[1:3] = ["filled", TODAY]
    (d / "STATUS.md").write_text(st.render(), encoding="utf-8")
    code, out = run(d, "next", "--phase", "contracts")
    if "## §Declined runs" in out or "§Declined runs (before stopping" not in out:
        fails.append("next --phase contracts should name §Declined runs, not print it, once every earlier gate is "
                     "filled (P47)")
    st.phase("foundation")[1:3] = ["empty", ""]
    (d / "STATUS.md").write_text(st.render(), encoding="utf-8")
    doc = (d / "docs/contracts.md").read_text(encoding="utf-8")
    (d / "docs/contracts.md").unlink()
    code, out = run(d, "set", "contracts", "filled", "--section-from", str(section), "--dry-run")
    for want in ("(net_pay)", "is not written yet", "Personal data` (a table", "after it - `set contracts filled"):
        if want not in out:
            fails.append(f"a dry-run before docs/contracts.md should print {want!r}: {out[-300:]!r}")
    if "docs/contracts.md, which does not exist" in out or "no docs/contracts.md" in out:
        fails.append(f"a dry-run before docs/contracts.md should not refuse its absence (P46): {out[:300]!r}")
    code, out = run(d, "set", "contracts", "filled", "--section-from", str(section))
    if code == 0 or "docs/contracts.md, which does not exist" not in out:
        fails.append(f"the save (no --dry-run) must still refuse a missing docs/contracts.md: {out[:300]!r}")
    (d / "docs/contracts.md").write_text(doc, encoding="utf-8")
    # the close: printed by `set` once the record passes
    (d / "app/payroll/schemas.py").write_text(files["app/payroll/schemas.py"], encoding="utf-8")
    run(d, "open", "--from", "contracts", "--what", "Override: #structure's check fails - test only",
        "--clears", "#structure's check passes")
    code, out = run(d, "set", "contracts", "filled", "--section-from", str(section))
    if code != 0 or "The rest of the close" not in out or "the tenant key per table" not in out or \
            "Change anything? If not:" not in out:
        fails.append(f"set contracts filled should record and print /contracts' close: {out[-500:]!r}")
    section.unlink()
    (d / "PRODUCT.md").unlink()
    for s in ("migrations", "app", "docs", "config"):
        shutil.rmtree(d / s, ignore_errors=True)


def test_environment_gaps(fails: list[str]) -> None:
    """E13: the project runs in its own environment, on the version it pins, and its task runner goes through it.
    A good tree has no gap; each break is named; stdlib helper scripts on a bare python are allowed."""
    import shutil
    for have, spec, want in (((3, 13, 14), ">=3.13,<3.14", True), ((3, 9, 1), ">=3.12", False),
                             ((3, 13, 2), "~=3.12", True), ((4, 0, 0), "~=3.12", False), ((20, 11, 1), "^20.1", True),
                             ((21, 0, 0), "^20.1", False), ((20, 3, 0), "20.x", True), ((19, 0, 0), "18 || 20", False)):
        if status.version_ok(have, spec) != want:
            fails.append(f"E13: version {have} against {spec!r} should be {want}")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        (d / "pyproject.toml").write_text('[project]\nname = "x"\nrequires-python = ">=3.12"\n', encoding="utf-8")
        (d / "uv.lock").write_text("version = 1\n", encoding="utf-8")
        (d / ".venv").mkdir()
        (d / ".venv/pyvenv.cfg").write_text("home = C:/py\nversion = 3.13.14\n", encoding="utf-8")
        good_make = "test:\n\tuv run pytest -q\nlayout:\n\tpython scripts/check_structure.py\nrun:\n\t$(PY) -m uvicorn app:app\n"
        (d / "Makefile").write_text(good_make, encoding="utf-8")
        if status.env_gaps(d):
            fails.append(f"E13: a project with its own environment should have no gap: {status.env_gaps(d)}")
        breaks = (
            ("no environment", lambda: (shutil.rmtree(d / ".venv"), (d / "uv.lock").unlink()), "no project environment"),
            ("old version", lambda: (d / ".venv/pyvenv.cfg").write_text("version = 3.9.1\n", encoding="utf-8"),
             "runs Python 3.9.1"),
            ("bare pytest", lambda: (d / "Makefile").write_text("test:\n\tpython -m pytest\n", encoding="utf-8"),
             "Makefile:2 runs `python -m pytest`"),
        )
        for name, brk, want in breaks:
            brk()
            got = "; ".join(status.env_gaps(d))
            if want not in got:
                fails.append(f"E13 {name}: expected {want!r}: {got[:200]!r}")
            (d / ".venv").mkdir(exist_ok=True)
            (d / ".venv/pyvenv.cfg").write_text("version = 3.13.14\n", encoding="utf-8")
            (d / "uv.lock").write_text("version = 1\n", encoding="utf-8")
            (d / "Makefile").write_text(good_make, encoding="utf-8")


def test_next26_items(d: Path, fails: list[str]) -> None:
    """next.26: `refs` prints a skill's small references whole and a big one's headings; `set <phase> filled` refuses
    while an earlier filled phase's check fails, unless the user's reason is recorded; the handoff lists open items
    with the close command; money typed Any or converted from a float is flagged."""
    code, out = run(d, "refs", "contracts")
    for want in ("## 2. Persistence schema and a migration", "## Migration applies"):
        if code != 0 or want not in out:
            fails.append(f"refs contracts should print both step files whole (missing {want!r})")
    code, out = run(d, "refs", "foundation")
    if "headings only" not in out or "## 6. The auto-layer" not in out or "## Guards" not in out:
        fails.append(f"refs foundation: skeleton-steps.md (over 8 KB) by headings, verify.md whole: {out[:300]!r}")
    code, out = run(d, "refs", "vision")  # "none" is an answer: a logged Cursor /vision was sent here by the start
    if code != 0 or "nothing to read" not in out:
        fails.append(f"refs of a phase with no reference files should say so, not refuse: {code} {out[:200]!r}")
    fresh(d)
    st = status.Status.load(d / "STATUS.md")
    for p in ("vision", "validate", "scope", "plan", "architect", "structure"):
        st.phase(p)[1:3] = ["filled", TODAY]
    (d / "STATUS.md").write_text(st.render(), encoding="utf-8")
    (d / "PRODUCT.md").write_text("## Scope\n- **Core:** x\n", encoding="utf-8")  # structure filled, no STRUCTURE.md
    code, out = run(d, "set", "scope", "filled")
    if code == 0 or "#structure's check fails now" in out:
        pass  # scope comes before structure: an earlier gate only
    code, out = run(d, "set", "foundation", "filled")
    if code == 0 or "#structure's check fails now" not in out or "Override: #structure's check fails" not in out:
        fails.append(f"a later phase must not close while an earlier phase's check fails: {out[:300]!r}")
    run(d, "open", "--from", "foundation", "--what", "Override: #structure's check fails - testing only",
        "--clears", "#structure's check passes")
    code, out = run(d, "set", "foundation", "filled")
    if "#structure's check fails now" in out:
        fails.append(f"a recorded override should let the later phase past the earlier check: {out[:300]!r}")
    (d / "PRODUCT.md").write_text("## Vision\n" + VISION_OK + "\n## Scope\n- **Core:** x\n", encoding="utf-8")
    vision_ready(d)
    code, out = run(d, "set", "vision", "filled")
    if "Open items - close each one" not in out or "status.py close <n> --how" not in out or \
            not re.search(r"\n  o\w{3}: Override", out):
        fails.append(f"the handoff should list open items with the close command: {out[-400:]!r}")
    (d / "PRODUCT.md").unlink()
    for text, name in (("class Order:\n    refund_cap: Any = None\n", "refund_cap"),
                       ("cap_cents = int(refund_cap * 100)\n", "refund_cap"), ("x = float(amount)\n", "amount")):
        (d / "app").mkdir(exist_ok=True)
        (d / "app/money.py").write_text(text, encoding="utf-8")
        got = "; ".join(status.contracts_gaps(d))
        if f"({name})" not in got:
            fails.append(f"money back door {text.strip()!r} should be flagged: {got[:200]!r}")
    (d / "app/money.py").write_text("class Usage:\n    total_tokens: Any = None\n    feedback: Any = None\n",
                                    encoding="utf-8")
    if "keeps money" in "; ".join(status.contracts_gaps(d)):
        fails.append("a non-money field typed Any is not money")
    import shutil
    shutil.rmtree(d / "app")


def test_team_safe(fails: list[str]) -> None:
    """Format 2 (team-safe): two branches that each record a ticket and an open item merge with no conflict and keep
    both; eight runs at once in one folder keep all eight items with distinct ids; a format-1 STATUS.md moves its
    rows into item files on the first write and loses none; build counts as filled from a ticket file alone and the
    phase table is not edited for it. Measured on format 1: 4 conflicts, both items numbered 1, 5 of 8 kept."""
    import threading
    S = str(ROOT / "tools" / "status.py")

    def sh(d, *a):
        return subprocess.run(a, cwd=d, capture_output=True, text=True, encoding="utf-8", errors="replace")

    def st_cmd(d, *a, today="2026-09-27"):
        return sh(d, sys.executable, S, "--today", today, *a)

    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        sh(d, "git", "init", "-q", "-b", "main")
        sh(d, "git", "config", "user.email", "t@t")
        sh(d, "git", "config", "user.name", "t")
        st_cmd(d, "init", "--product", "Demo", today="2026-09-26")
        sh(d, "git", "add", "-A")
        sh(d, "git", "commit", "-qm", "base")
        before = (d / "STATUS.md").read_text(encoding="utf-8")
        for br, tid, day in (("a", "M1-ORD-01", "2026-09-27"), ("b", "M1-REF-01", "2026-09-28")):
            sh(d, "git", "checkout", "-q", "-b", br, "main")
            st_cmd(d, "rules", "build", today=day)  # what cmd_ticket asks of a build: rules read, a reviewed doc
            (d / "docs").mkdir(exist_ok=True)
            (d / "docs" / f"{tid}.md").write_text("# T\n\n## Review\nCLEAN\n", encoding="utf-8")
            gate_pass(d)
            st_cmd(d, "ticket", tid, "--dod", "yes", "--verified", "pytest -> 5 passed", "--doc", f"docs/{tid}.md",
                   "--no-cuts", "docs-only test ticket", today=day)
            st_cmd(d, "open", "--from", "build", "--what", f"follow-up from {tid}", "--clears", "next ticket", today=day)
            sh(d, "git", "add", "-A")
            sh(d, "git", "commit", "-qm", tid)
        sh(d, "git", "checkout", "-q", "main")
        sh(d, "git", "merge", "-q", "a")
        m = sh(d, "git", "merge", "-q", "b", "-m", "merge b")
        shown = st_cmd(d, "show").stdout
        if m.returncode != 0 or "<<<<<<<" in (d / "STATUS.md").read_text(encoding="utf-8"):
            fails.append(f"two branches that each record a ticket and an item should merge clean: {m.stdout}{m.stderr}")
        for want in ("M1-ORD-01", "M1-REF-01", "follow-up from M1-ORD-01", "follow-up from M1-REF-01"):
            if want not in shown:
                fails.append(f"after the merge, show should list {want!r}")
        if (d / "STATUS.md").read_text(encoding="utf-8") != before:
            fails.append("a ticket or an open item edited STATUS.md - every branch would then conflict on it")
        st = status.Status.load(d / "STATUS.md")
        if st.state("build") != "filled":
            fails.append("a ticket file should count #build as filled (derived, not written)")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        st_cmd(d, "init", "--product", "Demo")
        ths = [threading.Thread(target=st_cmd, args=(d, "open", "--from", "build", "--what", f"item {i}", "--clears",
                                                      "x")) for i in range(8)]
        [x.start() for x in ths]
        [x.join() for x in ths]
        ids = [r[0] for r in status.Status.load(d / "STATUS.md").rows["Open items"]]
        if len(ids) != 8 or len(set(ids)) != 8:
            fails.append(f"8 runs at once should keep 8 items with distinct ids: {ids}")
        if (d / status.LOCK).exists():
            fails.append("the lock file was left behind")
        # the lock's own case: runs that all rewrite STATUS.md at once (a set each) must not overwrite each other.
        # under a loaded machine six runs in a row outlasted the 30 s lock wait and one was REFUSED (a timeout,
        # not a lost write) - the test waits up to 10 min and tells a timeout from a lost write: red = a lock bug.
        phases = ["vision", "validate", "scope", "plan", "architect", "structure"]
        res: dict[str, subprocess.CompletedProcess] = {}
        env = {**os.environ, "STATUS_LOCK_WAIT": "600"}

        def set_one(p):
            res[p] = subprocess.run([sys.executable, S, "--today", "2026-09-27", "set", p, "declined", "--reason",
                                     "parallel", "--gate", "vision"], cwd=d, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", env=env)
        ths = [threading.Thread(target=set_one, args=(p,)) for p in phases]
        [x.start() for x in ths]
        [x.join() for x in ths]
        st = status.Status.load(d / "STATUS.md")
        timed_out = [p for p in phases if res[p].returncode != 0]
        lost = [p for p in phases if st.state(p) != "declined" and p not in timed_out]
        if lost:
            fails.append(f"{len(phases)} set runs at once lost {lost} although each exited 0 - the lock let two "
                         f"writes overlap")
        if timed_out:
            fails.append(f"set runs refused while waiting for the lock: "
                         f"{[(p, (res[p].stdout + res[p].stderr).strip()[-160:]) for p in timed_out]}")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        st_cmd(d, "init", "--product", "Demo")
        old = status.Status.load(d / "STATUS.md")
        old.rows["Open items"] += [["1", "2026-09-20", "architect", "Override: bypassed /validate - trial",
                                    "/validate is filled", ""],
                                   ["2", "2026-09-21", "plan", "a cost is a guess", "/eval measures it",
                                    "2026-09-22: done"]]
        old.rows["Tickets"].append(["M0-X-01", "2026-09-22", "yes", "pytest -> 3 passed", "2", "none recorded",
                                    "docs/x.md"])
        v1 = old.render().replace("Format: 2 ·", "Updated: 2026-09-22 · Stage: build ·")
        for sec in ("Open items", "Tickets"):  # the format-1 tables, rows inline
            v1 += (f"\n## {sec}\n\n| " + " | ".join(status.COLUMNS[sec]) + " |\n|" + "---|" * len(status.COLUMNS[sec])
                   + "\n" + "".join("| " + " | ".join(r) + " |\n" for r in old.rows[sec]))
        (d / "STATUS.md").write_text(v1, encoding="utf-8")
        st_cmd(d, "flag", "--ui", "yes")
        new = status.Status.load(d / "STATUS.md")
        for sec in ("Open items", "Tickets"):
            if sorted(new.rows[sec]) != sorted(old.rows[sec]):
                fails.append(f"a format-1 {sec} table lost or changed rows on its first write: {new.rows[sec]}")
        text = (d / "STATUS.md").read_text(encoding="utf-8")
        if "## Open items" in text or "Format: 2" not in text or not (d / "status/open/1.md").is_file():
            fails.append("the first write should move format-1 rows into item files and mark STATUS.md Format: 2")


def test_questions_name_no_product(fails: list[str]) -> None:
    """The question status.py makes every model ask word for word names no AI product: a logged Gemini build told its
    user to 'run the review in your other agent (e.g. Claude Code)' - one vendor's tool, pushed on another's user."""
    q = status.SELF_REVIEW_QUESTION
    named = re.findall(r"(?i)claude|anthropic|gemini|antigravity|cursor|codex|copilot|openai|chatgpt|grok", q)
    if named:
        fails.append(f"the self-review question names a product {sorted(set(named))}: say 'a different AI coding tool'")


def test_engine_protection(fails: list[str]) -> None:
    """A checker edited after install is refused (a logged run added its own folders to the installed
    check_structure.py's IGNORE list), and a project copy of the check that differs from the playbook's is named."""
    engine = status.tool_file("templates", "check_structure.py")
    if status.engine_changed(engine):
        fails.append(f"the shipped checker should match tools/engine.sha256: {status.engine_changed(engine)}")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        fresh(d)
        (d / "STRUCTURE.md").write_text(GOOD_STRUCTURE, encoding="utf-8")
        (d / "app/orders/tests").mkdir(parents=True)
        (d / "scripts").mkdir()
        (d / "scripts/check_structure.py").write_text(engine.read_text(encoding="utf-8"), encoding="utf-8")
        if status.phase_check("structure", d):
            fails.append(f"a matching tree with the real checker should pass: {status.phase_check('structure', d)}")
        real = status.engine_hashes
        status.engine_hashes = lambda: {"check_structure.py": "0" * 64}
        try:
            got = status.phase_check("structure", d) or ""
        finally:
            status.engine_hashes = real
        if "was changed after install" not in got:
            fails.append(f"a checker that no longer matches its fingerprint should be refused: {got!r}")
        st = status.Status.load(d / "STATUS.md")
        (d / "PRODUCT.md").write_text("## Vision\n- x\n", encoding="utf-8")
        if any("differs from the playbook's check" in n for n in status.next_phase(st)["notes"]):
            fails.append("a project copy equal to the playbook's check should not be named")
        # what a project's formatter hook does to the copy on its first commit (a logged refresh: ruff format rewrote
        # 99 lines): break a bracket across lines, re-indent the module docstring - the same code, so not named
        src = engine.read_text(encoding="utf-8")
        doc_end = src.index('"""', src.index('"""') + 3)
        formatted = src[:doc_end].replace("\n  * ", "\n      * ") + src[doc_end:]
        formatted = formatted.replace("problems += [f\"superseded", "problems += [\n        f\"superseded")
        if formatted == src:
            fails.append("the formatter simulation changed nothing (the test setup is stale)")
        (d / "scripts/check_structure.py").write_text(formatted, encoding="utf-8")
        if any("differs from the playbook's check" in n for n in status.next_phase(st)["notes"]):
            fails.append("a project copy only a formatter rewrote should not be named: it would be flagged forever")
        # E741 is in ruff's DEFAULT rules: a checker using l / O / I as a name fails every Python project's commit hook
        import ast
        bad = sorted({n.id for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Name) and n.id in ("l", "O", "I")})
        if bad:
            fails.append(f"the shipped checker uses ambiguous names {bad} (ruff E741 refuses the project's commit)")
        (d / "scripts/check_structure.py").write_text(
            engine.read_text(encoding="utf-8").replace('".gradle",', '".gradle", "status", "open",'), encoding="utf-8")
        if not any("scripts/check_structure.py differs from the playbook's check" in n
                   for n in status.next_phase(st)["notes"]):
            fails.append("a project copy edited to ignore folders should be named by next")


def gate_pass(d: Path, *cmds: str, passed: bool = True, ticket: str = "M1-A-01") -> None:
    """A gate.py record at HEAD of the current branch, as gate.py writes it (the ticket row needs one, R3-5)."""
    import json
    git_ = lambda *a: subprocess.run(["git", *a], cwd=d, capture_output=True, text=True).stdout.strip()  # noqa: E731
    f = d / ".git" / "playbook-gate"
    f.mkdir(exist_ok=True)
    with open(f / "results.jsonl", "a", encoding="utf-8") as h:
        h.write(json.dumps({"branch": git_("rev-parse", "--abbrev-ref", "HEAD"), "head": git_("rev-parse", "HEAD"),
                            "dirty": [], "commands": list(cmds or ("pytest -q",)), "passed": passed,
                            "ticket": ticket}) + "\n")


def test_lean_mode(fails: list[str]) -> None:
    """The lean path (owner, 2026-09-28): Claude Code runs /build and /dev-check lean - no rule files, no cuts, no
    per-file review list - every other tool runs the full procedure; PLAYBOOK_MODE overrides. The cheap checks that
    caught what plain Claude missed stay in both: the Real-world reach line, the gate, the security review."""
    real_env, real_tool = os.environ.get("PLAYBOOK_MODE"), status.playbook_tool
    try:
        os.environ.pop("PLAYBOOK_MODE", None)
        if status.playbook_mode("build") != "lean" or status.playbook_mode("dev-check") != "lean":
            fails.append("the Claude Code plugin route should run /build and /dev-check lean by default")
        if status.playbook_mode("contracts") != "full":
            fails.append("a phase with no lean path should always run full")
        status.playbook_tool = lambda: "antigravity"
        if status.playbook_mode("build") != "full":
            fails.append("another tool should run /build full by default")
        status.playbook_tool = real_tool
        os.environ["PLAYBOOK_MODE"] = "full"
        if status.playbook_mode("build") != "full":
            fails.append("PLAYBOOK_MODE=full should override the lean default")
        os.environ["PLAYBOOK_MODE"] = "lean"
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d)
            fresh(d)
            (d / "docs" / "issues").mkdir(parents=True)
            (d / "docs" / "issues" / "M1-B-01_seed.md").write_text(
                "# [M1-B-01] seed\n\n### 👀 Demo — what works after this merges\nRun the script: the store gains one "
                "order per case, its status as the case says.\n\n### 🧪 Verification Command\n```bash\npytest -q\n```\n",
                encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=d)
            subprocess.run([*g, "commit", "-qm", "base"], cwd=d)
            code, out = run(d, "next", "--phase", "dev-check")
            if "Mode: lean" not in out or "this phase's rules" in out or "Context hygiene" in out:
                fails.append(f"a lean /dev-check start should say Mode: lean and carry no rule files: {out[:400]}")
            code, out = run(d, "next", "--phase", "build", "--ticket", "M1-B-01")
            if "Mode: lean" not in out or "wire cuts" in out or "Demo claims" in out or "Rules for coding" in out \
                    or "This ticket must NOT: merge" not in out or "fails twice: stop" not in out \
                    or "a check the gate does not" not in out:
                fails.append(f"a lean /build start should carry no cuts, claims or rule texts: {out[:600]}")
            subprocess.run(["git", "checkout", "-q", "-b", "m1-b-01"], cwd=d)
            (d / "app").mkdir()
            (d / "app" / "seed.py").write_text("import httpx\n\n\ndef seed():\n    return httpx.post('x')\n", encoding="utf-8")
            (d / "app" / "test_seed.py").write_text("def test_refuses_live_shop():\n    pass\n", encoding="utf-8")
            (d / "docs" / "features").mkdir(parents=True)
            (d / "docs" / "features" / "seed.md").write_text("# Seed\n\n" + TOP_HALF + "## Review\nCLEAN.\n", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=d)
            subprocess.run([*g, "commit", "-qm", "work"], cwd=d)
            ticket = ["ticket", "M1-B-01", "--dod", "yes", "--verified", "pytest -> 1 passed", "--doc",
                      "docs/features/seed.md"]
            code, out = run(d, *ticket)
            if re.search(r"no wirecut\.py run|Demo claim|call\(s\) an outside service|does not name", out):
                fails.append(f"a lean ticket was refused for a full-path-only check: {out.strip()[:500]}")
            # v2 (P20): --dry-run lists the same gaps the row is refused for and writes nothing
            rows = (d / "status" / "tickets").glob("*.md") if (d / "status" / "tickets").is_dir() else []
            before = sorted(p.name for p in rows)
            code2, dry = run(d, *ticket, "--dry-run")
            gaps = [ln for ln in out.splitlines() if ln.startswith("  - ")]
            after = sorted(p.name for p in (d / "status" / "tickets").glob("*.md")) \
                if (d / "status" / "tickets").is_dir() else []
            if code2 != 0 or "DRY RUN" not in dry or not gaps or any(g not in dry for g in gaps) or after != before:
                fails.append(f"`ticket --dry-run` should list every gap the row is refused for and write nothing: "
                             f"{dry.strip()[:500]}")
            # owner 2026-10-06: the gate is never re-run to be safe - the dry run answers whether it is stale, also
            # before the feature doc has its Review section
            seed = d / "docs" / "features" / "seed.md"
            keep = seed.read_text(encoding="utf-8")
            seed.write_text("# Seed\n", encoding="utf-8")
            code2, dry = run(d, *ticket, "--dry-run")
            seed.write_text(keep, encoding="utf-8")
            if "no Review section" not in dry or "gate.py run" not in dry:
                fails.append(f"`ticket --dry-run` should name the gate's state even before the Review section: "
                             f"{dry.strip()[:500]}")
            # the user's word wins over the default, and holds for the ticket check (`/build <id> full`)
            code, out2 = run(d, "next", "--phase", "build", "--ticket", "M1-B-01", "--mode", "full")
            if "Mode: lean" in out2 or "wire cuts" not in out2:
                fails.append(f"`--mode full` should run the full start although the default is lean: {out2[:400]}")
            code, out2 = run(d, *ticket)
            if "Demo claim" not in out2:
                fails.append(f"the ticket check should follow the user's `--mode full`: {out2.strip()[:400]}")
            # v2: Antigravity shows ~4 KB of output - the ~29 KB full start goes to a file it opens once
            f = Path(status.__file__).resolve().parent / "build-start.md"
            real_tool = status.playbook_tool
            try:
                status.playbook_tool = lambda: "antigravity"
                code, out2 = run(d, "next", "--phase", "build", "--ticket", "M1-B-01", "--mode", "full")
                held = f.read_text(encoding="utf-8") if f.is_file() else ""
            finally:
                status.playbook_tool = real_tool
                f.unlink(missing_ok=True)
            if "build-start.md" not in out2 or "Commands (one call each" in out2 \
                    or "Commands (one call each" not in held or "This ticket must NOT" not in held:
                fails.append(f"an Antigravity /build start should point at build-start.md, which holds the start: "
                             f"{out2[-500:]}")
            run(d, "next", "--phase", "build", "--ticket", "M1-B-01")  # no word: the default decides again
            if "Real-world reach" not in out:
                fails.append(f"a lean ticket calling an outside service still needs its Real-world reach line: "
                             f"{out.strip()[:500]}")
            # /test has one path on every tool (no lean split): its start prints the targets, the criteria beside the
            # tests, the applicability lines and the bug rule; #Tests names each kind of case
            code, out = run(d, "next", "--phase", "test")
            if "Mode: lean" in out or "===== tests:" not in out or "expected failure" not in out \
                    or "Browser / real-user-environment cases:" not in out or "Rules for /test" not in out:
                fails.append(f"the /test start (one path) should print its targets, applicability and rules: {out[:600]}")
            (d / "PRODUCT.md").write_text("# P\n\n## Tests\n- unit tests added\n", encoding="utf-8")
            code, out = run(d, "set", "test", "filled", "--verdict", "fail")
            if code == 0 or "no line for the live path" not in out or "no line for security" not in out:
                fails.append(f"a lean #Tests naming no live path or security cases was recorded: {out.strip()[:400]}")
            (d / "PRODUCT.md").write_text("# P\n\n## Tests\n- Live path: /healthz 200\n- Security: forged token 401\n"
                                          "- Regression: #1 key fixture\n- Outside-service reach: "
                                          "test_refuses_live_shop\n", encoding="utf-8")
            code, out = run(d, "set", "test", "filled", "--verdict", "pass")
            if code == 0 or "no passing gate.py run" not in out:
                fails.append(f"a lean test PASS without the gate green on this code was recorded: {out.strip()[:400]}")
            code, out = run(d, "set", "test", "filled", "--verdict", "fail")
            if code != 0:
                fails.append(f"a lean test FAIL naming every kind of case should record: {out.strip()[:400]}")
    finally:
        status.playbook_tool = real_tool
        if real_env is None:
            os.environ.pop("PLAYBOOK_MODE", None)
        else:
            os.environ["PLAYBOOK_MODE"] = real_env


def test_test_record_in_few_calls(fails: list[str]) -> None:
    """next.46, from the 2026-09-29 /test 3-way: the gate's pass counts on the exact files it checked, committed or
    not (Claude paused for a commit and re-ran the gate; Gemini ran it 4 times); /test writes its own #Tests after the
    gate in ONE `set --section-from` call (Antigravity's two PRODUCT.md edits put ~90 KB each into its conversation);
    every receipt in one `quote` call; the start names built security code (a run skipped a broken injection guard as
    "not built"); Antigravity is told not to poll (89 of 183 calls)."""
    gate = ROOT / "commands" / "build" / "gate.py"
    ok = f'"{sys.executable}" -c "print(\'1 passed in 0.1s\')"'
    real_tool = status.playbook_tool
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d)
        fresh(d)
        prod = "# P\n\n## Vision\n- v\n\n## Tests             <!-- /test -->\n\n## Evaluation\n- e\n"
        (d / "PRODUCT.md").write_text(prod, encoding="utf-8")
        (d / "app" / "guards").mkdir(parents=True)
        (d / "app" / "guards" / "input.py").write_text("def wrap(t):\n    return t\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "base"], cwd=d)
        code, out = run(d, "next", "--phase", "test")
        if "Security code already built" not in out or "app/guards/input.py (named in tests: 0)" not in out \
                or "Dev check: empty" not in out or "--section-from" not in out:
            fails.append(f"the /test start should name built security code, the phase states and the one-call "
                         f"record: {out[-900:]}")
        # v2: ONE start call carries the suite's rules (it was `next` + `rules test`, 27 KB of all 18 sections) and
        # what the phase must NOT do; the close's sections are left to `set`
        if "Rules for /test" not in out or "## Plain-language close" in out or "must NOT" not in out \
                or "status.py rules test  (run it now" in out:
            fails.append(f"the /test start should carry its rules in one call, not the close's, and say what it must "
                         f"not do: {out[:900]}")
        # next.51: the edit tool's JSON input decodes \u043e into the raw character the linter rejects (a logged run
        # spent 7 patch scripts on it) - look-alikes are written as chr(0x...) or \N{...}, never raw, never \u
        if "chr(0x043E)" not in out or "CYRILLIC SMALL LETTER O" not in out or "written as " + chr(92) + "u escapes" in out:
            fails.append(f"the /test start should say look-alikes are written as chr(0x043E) or a named escape: {out[-900:]}")
        (d / "tests").mkdir()
        (d / "tests" / "test_guard.py").write_text("from app.guards import input\n", encoding="utf-8")
        subprocess.run([sys.executable, str(gate), ok], cwd=d, capture_output=True)  # uncommitted tests, gated
        body = d.parent / f"{d.name}-tests.md"
        body.write_text("## Tests\n- Live path: /healthz 200\n- Security: forged token 401\n- Regression: #2 xfail\n",
                        encoding="utf-8")
        try:
            before = (d / "PRODUCT.md").read_text(encoding="utf-8")
            for f, changed in (("PRODUCT.md", prod.replace("- v", "- v2")), ("app/guards/input.py", "X = 2\n")):
                keep = (d / f).read_text(encoding="utf-8")
                (d / f).write_text(changed, encoding="utf-8")
                code, out = run(d, "set", "test", "filled", "--verdict", "pass", "--section-from", str(body))
                if code == 0 or "no passing gate.py run" not in out:
                    fails.append(f"{f} changed after the gate and the pass still counted: {out.strip()[:300]}")
                if (d / "PRODUCT.md").read_text(encoding="utf-8") != (changed if f == "PRODUCT.md" else before):
                    fails.append("a refused --section-from should put PRODUCT.md back")
                if f == "app/guards/input.py" and "app/guards/input.py" not in out:  # a logged run guessed and re-ran
                    fails.append(f"the refusal should list the files changed since the passing gate: {out.strip()[:300]}")
                if f == "app/guards/input.py":  # Q40: a PASS with the live path not run is refused for it
                    keep_body = body.read_text(encoding="utf-8")
                    body.write_text("## Tests\n- Live path: UNVERIFIED - not run\n- Security: forged token 401\n"
                                    "- Regression: #2 xfail\n", encoding="utf-8")
                    code, out = run(d, "set", "test", "filled", "--verdict", "pass", "--section-from", str(body),
                                    "--dry-run")
                    body.write_text(keep_body, encoding="utf-8")
                    if "the live path (the running app, the observable result) not run" not in out:
                        fails.append(f"a /test PASS with the live path not run should be refused: {out.strip()[:400]}")
                if f == "app/guards/input.py":  # v2: --dry-run lists the same gaps and writes nothing
                    code, out = run(d, "set", "test", "filled", "--verdict", "pass", "--section-from", str(body),
                                    "--dry-run")
                    if code != 0 or "DRY RUN" not in out or "no passing gate.py run" not in out \
                            or (d / "PRODUCT.md").read_text(encoding="utf-8") != before:
                        fails.append(f"`set test filled --dry-run` should list the gaps and write nothing: "
                                     f"{out.strip()[:300]}")
                (d / f).write_text(keep, encoding="utf-8")
            # the phase's own companion is its record, like its own section: a logged run edited docs/tests.md after the
            # gate and its pass was voided, although the refusal said docs may change after it
            (d / "docs").mkdir(exist_ok=True)
            (d / "docs" / "tests.md").write_text("# Tests" + chr(10) + "why each case exists" + chr(10), encoding="utf-8")
            code, out = run(d, "set", "test", "filled", "--verdict", "pass", "--section-from", str(body))
            now = (d / "PRODUCT.md").read_text(encoding="utf-8")
            if code != 0 or "- Regression: #2 xfail\n\n## Evaluation" not in now or "## Tests             <!--" \
                    not in now or "## Vision\n- v\n" not in now:
                fails.append(f"a gate over the uncommitted final files + #Tests written after it should record in one "
                             f"call: {out.strip()[:300]} / {now!r}")
            if "The rest of the close" not in out or "#Contracts and #Architecture" not in out:
                fails.append(f"`set test filled` should print the rest of the close: {out.strip()[-600:]}")
        finally:
            body.unlink()
        (d / "a.md").write_text("the refund limit is fifty euros per order\n", encoding="utf-8")
        (d / "b.md").write_text("tokens expire after one minute exactly\n", encoding="utf-8")
        code, out = run(d, "quote", "a.md", "refund limit is fifty euros", "b.md", "expire after one minute")
        if code != 0 or out.count(" · ") < 4 or "b.md" not in out:
            fails.append(f"quote should print every receipt of several pairs in one call: {out!r}")
        code, out = run(d, "quote", "a.md", "refund limit is fifty euros", "b.md", "no such words in this file")
        if code == 0 or "x b.md" not in out or "a.md" not in out:
            fails.append(f"quote should print the good receipts and refuse the bad pair: {out!r}")
        try:
            status.playbook_tool = lambda: "antigravity"
            code, out = run(d, "next", "--phase", "test")
            if "TimerCondition = its task id" not in out:
                fails.append(f"an Antigravity start should forbid polling: {out[:400]}")
        finally:
            status.playbook_tool = real_tool
            (Path(status.__file__).resolve().parent / "test-start.md").unlink(missing_ok=True)
        code, out = run(d, "next", "--phase", "test")
        if "Antigravity:" in out:
            fails.append("the Antigravity line should print on Antigravity only")


def test_decided_locally(fails: list[str]) -> None:
    """next.47 - decide locally, not in the model: a stopped database named by one socket check (a logged run spent
    8 calls finding it), the module's import row printed (STRUCTURE.md re-read 10 times), a second ticket in one
    conversation warned (40M tokens), and every refusal says the scripts are not to be read (status.py read 10x)."""
    import socket
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen()
        up = srv.getsockname()[1]
        closed = socket.socket()
        closed.bind(("127.0.0.1", 0))
        down = closed.getsockname()[1]
        closed.close()
        try:
            (d / ".env").write_text(f"DATABASE_URL=postgresql+psycopg://u:p@127.0.0.1:{up}/dev\n", encoding="utf-8")
            if status.env_precheck(d) is not None:
                fails.append("a database that answers should raise no pre-check line")
            (d / ".env").write_text(f"DATABASE_URL=postgresql://u:p@127.0.0.1:{up}/dev\n"
                                    f"TEST_DATABASE_URL='postgresql://u:p@127.0.0.1:{down}/test'\n", encoding="utf-8")
            (d / "justfile").write_text("db:\n    docker start shop-pg\n", encoding="utf-8")
            out = status.env_precheck(d) or ""
            if f"TEST_DATABASE_URL 127.0.0.1:{down}" not in out or "docker start shop-pg" not in out \
                    or f"127.0.0.1:{up}" in out:
                fails.append(f"the pre-check should name the database that does not answer and the project's start "
                             f"command: {out!r}")
        finally:
            srv.close()
        (d / "STRUCTURE.md").write_text(
            "# S\n\n| Module | What |\n|---|---|\n| `app/orders` | orders |\n\n## Module dependencies\n\n"
            "| Package | May import | Why |\n|---|---|---|\n| `config` | — | bottom |\n"
            "| `orders` | `platform`, `config`, `shops` | needs the token |\n", encoding="utf-8")
        out = status.module_rules(d, ["app/orders/adapters/seed.py", "app/orders/tests/test_seed.py", "scripts/x.py"])
        if not out or "orders may import: `platform`, `config`, `shops`" not in out or "config may" in out:
            fails.append(f"the build start should print the touched module's import row only: {out!r}")
    log = ('{"command":"python status.py ticket M1-A-01 --dod yes"} ... python "C:/x/status.py" ticket M1-B-02 '
           '--dod partial ... status.py next --phase build --ticket M1-C-03')
    if status.other_tickets(log, "M1-C-03") != ["M1-A-01", "M1-B-02"] or status.other_tickets(log, "M1-A-01") != ["M1-B-02"]:
        fails.append(f"other_tickets should list the tickets this conversation recorded: {status.other_tickets(log, 'M1-C-03')}")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        fresh(d)
        code, out = run(d, "set", "vision", "nonsense-state")
        if code == 0 or "Never open the playbook's scripts" not in out:
            fails.append(f"every refusal should say what to change is in it and the scripts are not to be read: {out!r}")
        code, out = run(d, "next")
        if "run this same `next` again" not in out or "independent reads and commands in ONE call" not in out:
            fails.append(f"every start should carry the fewest-calls and summarised-conversation line: {out[:300]}")
        # next.50: a logged next.49 /test re-ran three files the gate had just passed, and a real-app test 8 times
        if "cite the gate for every test file it ran" not in out:
            fails.append(f"every close should make a passing gate the evidence for the files it ran: {out[:300]}")
        if "never a python/sed script that rewrites files" not in out:
            fails.append(f"every start should forbid patch scripts (a logged /test lost ~4 min to six): {out[:300]}")
        # next.48: every phase's close writes its section and its receipts in one call each
        if "set <phase> filled --section-from <file>" not in out or "prints every line to paste in ONE call" not in out:
            fails.append(f"the close every phase prints should use --section-from and one quote call: {out[:600]}")
        # next.48: /test names the code that can reach an outside service and needs the record line for it (a
        # playbook run and plain Claude both missed the dev app calling real Shopify)
        (d / "app").mkdir()
        (d / "app" / "shop_client.py").write_text("import httpx\n\n\ndef get():\n    return httpx.get('x')\n",
                                                  encoding="utf-8")
        (d / "PRODUCT.md").write_text("# P\n\n## Tests\n- Live path: /healthz 200\n- Security: forged token 401\n"
                                      "- Regression: #2 xfail\n", encoding="utf-8")
        code, out = run(d, "next", "--phase", "test")
        if "Outside-service reach - these files call an outside service: app/shop_client.py" not in out \
                or "automated, re-runnable test that starts the real entry point" not in out and "Live path" in out:
            fails.append(f"the /test start should list the outside-service files: {out[-900:]}")
        code, out = run(d, "set", "test", "filled", "--verdict", "fail")
        if code == 0 or "Outside-service reach:" not in out:
            fails.append(f"#Tests without an Outside-service reach line was recorded: {out.strip()[:300]}")
        # the fixup cycles of a logged Antigravity /test, told before they happen: evidence cited devserver.py (refused
        # twice), 71 ToolCalls built without reading the type, raw look-alike characters failed the linter
        if "never a playbook script" not in out and "never a playbook" not in run(d, "next")[1]:
            fails.append("every phase's close should print the evidence format (a file in THIS repo, never a script)")
        code, out2 = run(d, "next", "--phase", "test")
        if "read the ones you need in ONE call" not in out2 or "typed input's definition" not in out2:
            fails.append(f"the /test start should ask for one-call reads and reading a type before building it: {out2[-600:]}")
        (d / "justfile").write_text("check:\n    pytest\n\nseed-dev:\n    python seed.py\n", encoding="utf-8")
        if status.seed_recipe(d) != "just seed-dev":
            fails.append(f"seed_recipe should find the project's seed recipe: {status.seed_recipe(d)!r}")
        (d / "justfile").unlink()
        if status.seed_recipe(d) is not None:
            fails.append("seed_recipe should be None when the project has no seed recipe")
        with open(d / "PRODUCT.md", "a", encoding="utf-8") as h:
            h.write("- Outside-service reach: test_dev_app_uses_the_fake (xfail #4)\n")
        code, out = run(d, "set", "test", "filled", "--verdict", "fail")
        if code != 0:
            fails.append(f"#Tests naming its outside-service reach should record: {out.strip()[:300]}")


def test_test_close_first_try(fails: list[str]) -> None:
    """next.52: a /test close written the way the six logged runs wrote theirs records on the FIRST call. 4 of the 6
    were refused for citing gate.py (the close says cite the gate); one split its reach line after a long-line warning
    and lost the label; one debugged its live-path test for 3 runs over a Windows fact docs/runbook.md holds; a
    section with two problems was refused twice, one at a time."""
    gate = ROOT / "commands" / "build" / "gate.py"
    ok = f'"{sys.executable}" -c "print(\'1 passed in 0.1s\')"'
    nl = chr(10)
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d)
        fresh(d)
        (d / "PRODUCT.md").write_text(nl.join([
            "# P", "", "## Vision", "- v", "", "## Foundation", "- Health: `/healthz` on localhost:8000", "",
            "## Tests             <!-- /test -->", "", "## Evaluation", "- e", ""]), encoding="utf-8")
        for f, body in (
                ("app/shop_client.py", "import httpx" + nl * 3 + "def get():" + nl + "    return httpx.get('x')" + nl),
                ("app/guards/input.py", "def wrap(t):" + nl + "    return t" + nl),
                ("tests/test_reach.py", "def test_dev_app_uses_the_fake():" + nl + "    pass" + nl),
                ("justfile", "dev:" + nl + "    uvicorn app.main:app --reload --port 8000" + nl),
                ("docs/runbook.md", "# Runbook" + nl + nl + "## First boot" + nl + nl + "**Windows only:** always "
                 "start the web process with `just dev` (it uses `--reload`). Without `--reload`, uvicorn picks the "
                 "Proactor event loop, which psycopg cannot use." + nl + nl + "## CI" + nl + "- runs `just dev`? no."
                 + nl)):
            (d / f).parent.mkdir(parents=True, exist_ok=True)
            (d / f).write_text(body, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "base"], cwd=d)
        code, out = run(d, "next", "--phase", "test")
        if "Proactor event loop" not in out:
            fails.append(f"the /test start should print the runbook's rule for starting the app (a logged run spent "
                         f"3 live-path runs finding it): {out[-700:]}")
        if "300 characters" not in out:
            fails.append("the /test start should give the line limit before the section is written, not after")
        subprocess.run([sys.executable, str(gate), ok], cwd=d, capture_output=True)
        (d / "docs" / "tests.md").write_text("# Tests" + nl + "why each case exists" + nl, encoding="utf-8")
        ev = '`evidence: python gate.py "just check" → GATE PASS, {} · tests/test_reach.py · 2026-09-29`'
        section = nl.join([
            "- **Live-path verified (not just isolated units):** the app on a free port; `/healthz` 200.",
            "  - " + ev.format("test_dev_app_uses_the_fake passed"),
            "- **Adversarial/security (prompt-injection, authz) cases:** a forged token is refused.",
            "  - Outside-service reach (`tests/test_reach.py`), each file started as the project runs it:",
            "    - pass: `test_dev_app_uses_the_fake`",
            "  - " + ev.format("reach 1 passed"),
            "- **Regression:** #2 locked as a strict xfail. " + " ".join(
                f"Case {i} holds the refund cap at the boundary, `a.b; c` untouched." for i in range(8)),
            "- **Defect hunt:** input domains, cleanup on failure - none found.",
            "- **Detail:** `docs/tests.md`", ""])
        body = d.parent / f"{d.name}-close.md"
        try:
            body.write_text(section, encoding="utf-8")
            code, out = run(d, "set", "test", "filled", "--verdict", "pass", "--section-from", str(body))
            if code != 0 or nl + "  ! " in out:
                fails.append(f"a close written the way the logged runs wrote it (the gate cited, the reach line with "
                             f"its label, docs/tests.md after the gate) should record first time, no warning: "
                             f"{out.strip()[:500]}")
            now = (d / "PRODUCT.md").read_text(encoding="utf-8")
            if "- **Regression:** #2 locked as a strict xfail." not in now or now.count("Case ") != 8                     or "`a.b; c` untouched." not in now:
                fails.append("a long line should be split into sub-bullets by the script, every word and its label "
                             "kept (a logged run rewrote its lines after the warning and lost a required label)")
            # one refusal names every problem, each once: a missing reach line AND a cited file that does not exist
            bad = section.replace("Outside-service reach (", "Reach (").replace("tests/test_reach.py ·",
                                                                                "tests/test_gone.py ·")
            body.write_text(bad, encoding="utf-8")
            code, out = run(d, "set", "test", "filled", "--verdict", "pass", "--section-from", str(body))
            if code == 0 or "Outside-service reach" not in out or out.count("test_gone.py") != 1:
                fails.append(f"a close with two problems should be refused once, naming each problem once: "
                             f"{out.strip()[:600]}")
        finally:
            body.unlink()


def test_dev_check_gate(fails: list[str]) -> None:
    """A checkpoint PASS needs every milestone ticket recorded, done and merged into THIS checkout, and a passing gate on
    this code: a logged checkpoint branch held two tickets that passed alone and failed 12 tests merged. FAIL always
    records; the start prints each ticket's state."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d)
        fresh(d)  # first: it clears the folder's files
        (d / "TICKETS.md").write_text("# Tickets\n\n## M1 core\n| `M1-A-01` | a |\n| `M1-A-02` | b |\n",
                                      encoding="utf-8")
        (d / "app.py").write_text("X = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "base"], cwd=d)
        subprocess.run(["git", "checkout", "-q", "-b", "a01"], cwd=d)
        (d / "a.py").write_text("A = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "a.py"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "a01 work"], cwd=d)
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
        subprocess.run(["git", "checkout", "-q", "main"], cwd=d)
        rec = d / "status" / "tickets"
        rec.mkdir(parents=True, exist_ok=True)
        row = ("<!-- One ticket, written by status.py. Never edit by hand. -->\nTicket: {id}\nDate: 2026-09-28\nDoD met: "
               "yes\nHow verified: pytest -> 1 passed\nFull-suite runs: 1\nReview: helper agent R1 clean · {sha} · "
               "2026-09-28\nDoc: docs/features/a.md\n")
        (rec / "2026-09-28-m1-a-01.md").write_text(row.format(id="M1-A-01", sha=sha), encoding="utf-8")
        code, out = run(d, "set", "dev-check", "filled", "--verdict", "pass")
        for want in ("not recorded: M1-A-02", "not in this checkout: M1-A-01", "no passing gate.py run"):
            if code == 0 or want not in out:
                fails.append(f"a checkpoint PASS was not refused for '{want}': {out.strip()[:400]}")
        subprocess.run(["git", "branch", "m1-a-02-draft", "a01"], cwd=d)  # F5: a ticket branch nobody merged
        code, out = run(d, "next", "--phase", "dev-check")
        if "M1-A-02: not recorded" not in out or "M1-A-01: not in this checkout" not in out or "gate.py" not in out:
            fails.append(f"the checkpoint start should print each ticket's state and the gate: {out.strip()[-600:]}")
        if "NOT merged into this checkout" not in out or "m1-a-02-draft" not in out:
            fails.append(f"the checkpoint start should list ticket branches not merged here (F5): {out.strip()[-600:]}")
        subprocess.run([*g, "merge", "-q", "--no-edit", "a01"], cwd=d)
        (rec / "2026-09-28-m1-a-02.md").write_text(row.format(id="M1-A-02", sha=sha), encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "records"], cwd=d)
        gate_pass(d, ticket="")
        code, out = run(d, "set", "dev-check", "filled", "--verdict", "pass")
        if code != 0:
            fails.append(f"a checkpoint with every ticket done and merged and the gate passing was refused: "
                         f"{out.strip()[:400]}")
        subprocess.run(["git", "checkout", "-q", "-b", "later", "HEAD~2"], cwd=d)
        # F1: a FAIL records only when #Dev-complete shows every check run - never one skipped because an earlier was
        # red (a logged checkpoint left security, scope and the live run "stopped on red"); F4: a commented example
        # evidence line is not evidence
        head = "# P\n\n## Dev-complete\n<!-- `evidence: pytest tests/none.py::test_nope → 1 passed · x · 2026-01-01` -->\n"
        (d / "PRODUCT.md").write_text(head + "- Gate: just check → 12 failed\n- Security: UNVERIFIED - stopped on red\n",
                                      encoding="utf-8")
        code, out = run(d, "set", "dev-check", "filled", "--verdict", "fail")
        if code == 0 or "skipped because an earlier one failed" not in out or "no line for the live path" not in out:
            fails.append(f"a FAIL whose checks stopped on red was recorded (F1): {out.strip()[:400]}")
        (d / "PRODUCT.md").write_text(head + "- Gate: just check → 12 failed\n- Live path: /healthz 200, /api/log 501\n"
                                      "- Security: each built ticket's DoD holds\n- Scope: no creep found\n"
                                      "- Secret scan: gitleaks detect → no leaks\n- Dependency scan: pip-audit → 0\n",
                                      encoding="utf-8")
        code, out = run(d, "set", "dev-check", "filled", "--verdict", "fail", "--security-from", sec_table(d, "CLEAN"))
        if code != 0:
            fails.append(f"a checkpoint FAIL with every check shown must record (F1; a commented example is not "
                         f"evidence, F4): {out.strip()[:400]}")


# 2.4 (#45): the security helper's table, saved to a file outside the repo and passed with --security-from
REAL_TABLE = """| Severity | File:line | What goes wrong |
|---|---|---|
| MEDIUM | app/dev.py:12 | the dev server uses the real store adapter by default |
| LOW | app/session.py:40 | the session cookie has no SameSite |
| LOW | app/log.py:8 | a request id is logged in full |
"""


def sec_table(d: Path, text: str) -> str:
    f = d.parent / f"{d.name}-security.md"
    f.write_text(text, encoding="utf-8")
    return str(f)


# a realistic checkpoint record, shaped like a logged lean run's #Dev-complete (names made generic)
DEV_COMPLETE_REAL = """**Verdict: FAIL (2026-09-28, lean run).** Only 1 of 2 M1 tickets is built, and the gate is red on the merged code.

- [ ] Every core-scope feature built & runs. **FAIL:** M1-A-02 is not recorded.
  - Unmerged ticket branches, not checked here: `m1-a-02-draft`.
- [ ] Gate (builds green). **FAIL:** `evidence: just check (run through the playbook gate) → FAIL, 12 failed, 115 passed · .git/playbook-gate/163043.log · 2026-09-28` (issue #1)
- [x] Live path runs. `evidence: just dev (port 8000, started by the dev-server helper) → /healthz 200 · GET /api/session good token 200, garbage token 401 · 2026-09-28`
- [ ] Security DoD. **FAIL (1 MEDIUM):** security review helper (read-only, each finding checked in code) → #2 the dev server uses the real store adapter by default; LOWs grouped in #3.
  - Checked OK: account id only from the verified token; token encrypted at rest; fail-closed 401/503.
- [x] Scope re-check: nothing crept in. `evidence: grep -rniE 'billing|subscription|dashboard' app/ → 1 hit, a help string in app/config/loader.py:47 (not creep) · 2026-09-28`
- [ ] No hardcoding · prompts externalized · contracts typed. **UNVERIFIED:** `just check` (lint, contracts, imports) did not reach a green result.
- [x] Secret scan: `just secrets` → no leaks found (2026-09-28).
- [ ] Dependency scan: `just vuln` → 1 known CVE, LOW (issue #3).

| Ticket | Built | Runs | DoD incl. security |
|---|---|---|---|
| M1-A-01 install + session | yes (merged) | yes, `/api/session` 200/401 | open: #2 (MEDIUM) |
| M1-A-02 orders | no | - | - |
"""


def test_dev_check_close(fails: list[str]) -> None:
    """The aligned checkpoint (v2): ONE start call carries the facts and the checks' rules (a full run made a second
    `rules` call for 27 KB, re-sent on each of 67 calls); ONE close call - `set dev-check filled --section-from` -
    names every gap at once (the PASS gaps and the missing checks were two refusals in turn) and --dry-run lists them
    without writing; a realistic FAIL records the first time and prints the rest of the close and the handoff."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d)
        fresh(d)
        (d / "TICKETS.md").write_text("# Tickets\n\n## M1 core\n| `M1-A-01` | a |\n| `M1-A-02` | b |\n",
                                      encoding="utf-8")
        (d / "PRODUCT.md").write_text("# P\n\n## Scope\n- **Non-goals:** billing\n\n## Dev-complete\n\n## Tests\n",
                                      encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "base"], cwd=d)
        code, out = run(d, "next", "--phase", "dev-check")
        if code != 0 or "Rules for /dev-check" not in out or "status.py rules dev-check  (run it now" in out \
                or "--section-from" not in out or "must NOT" not in out or "## Plain-language close" in out:
            fails.append(f"a full /dev-check start should carry its checks' rules in ONE call, name the one close "
                         f"call and what it must not do, and leave the close's rules to `set`: {out[-700:]}")
        # sources pass (2026-10-06): P48 stop rule, no unasked checks, P9 project-level notes labelled, P3 re-run offers
        # a count, P47 the start under Claude Code's 30,000-character cut
        real_next = status.next_phase
        status.next_phase = lambda st_, run_=None: (lambda n: {**n, "notes": n["notes"] + [
            "#foundation's check fails now: hooks not installed", "rules changed since #plan was filled: x"]})(
            real_next(st_, run_))
        try:
            for ph in ("dev-check", "test"):
                code, out = run(d, "next", "--phase", ph)
                if "fails twice: stop" not in out or "not asked for" not in out or len(out) > 30000 \
                        or "NOT THIS PHASE'S - tell the user in the close, never change it here: #foundation" not in out \
                        or "1 earlier phases were filled under older rules" not in out:
                    fails.append(f"the /{ph} start should carry the stop rule, no unasked checks, label project-level "
                                 f"notes, count re-run offers and stay under 30,000 characters ({len(out)}): "
                                 f"{out[:900]}")
        finally:
            status.next_phase = real_next
        src = Path(t) / "dc.md"
        src.write_text("- Gate: just check → 12 failed\n- Security: UNVERIFIED - stopped on red\n", encoding="utf-8")
        before = (d / "PRODUCT.md").read_text(encoding="utf-8")
        args = ["set", "dev-check", "filled", "--verdict", "pass", "--section-from", str(src)]
        code, out = run(d, *args, "--dry-run")
        if code != 0 or "DRY RUN" not in out or "tickets not recorded: M1-A-01, M1-A-02" not in out \
                or "no line for the live path" not in out or (d / "PRODUCT.md").read_text(encoding="utf-8") != before:
            fails.append(f"--dry-run should list the PASS gaps and the missing checks together and write nothing: "
                         f"{out.strip()[:600]}")
        code, out = run(d, *args)
        if code == 0 or out.count("REFUSED") != 1 or "tickets not recorded" not in out \
                or "skipped because an earlier one failed" not in out \
                or (d / "PRODUCT.md").read_text(encoding="utf-8") != before:
            fails.append(f"one refusal should name the PASS gaps and the missing checks, PRODUCT.md put back: "
                         f"{out.strip()[:600]}")
        # Q40: a PASS whose live path was never run is a saving made of a skipped check - refused; a line naming the
        # same command beside its own UNVERIFIED (a logged record's "No hardcoding ... `just check`") is not a skip
        src.write_text("- Gate: just check → 120 passed\n- No hardcoding: UNVERIFIED - `just check` lint not reached\n"
                       "- Live path: UNVERIFIED - not run\n- Security: each built ticket's DoD holds\n"
                       "- Scope: no creep found\n", encoding="utf-8")
        code, out = run(d, *args, "--dry-run")
        if "the live path (/run, the observable result) not run" not in out or "the gate (the project's full" in out:
            fails.append(f"a PASS with the live path not run should be refused for it (and only it): {out.strip()[:700]}")
        (d / "app" / "config").mkdir(parents=True)  # the file the scope evidence cites
        (d / "app" / "config" / "loader.py").write_text("HELP = 'the Partner Dashboard'\n", encoding="utf-8")
        src.write_text(DEV_COMPLETE_REAL, encoding="utf-8")
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=d)
        subprocess.run(["git", "config", "user.name", "t"], cwd=d)
        head0 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout
        code, out = run(d, "set", "dev-check", "filled", "--verdict", "fail", "--section-from", str(src), "--no-commit",
                        "--security-from", sec_table(d, REAL_TABLE))
        if code != 0 or "saved: commit" in out \
                or subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout != head0:
            fails.append(f"`--no-commit` should record without saving: {out.strip()[:300]}")
        st = status.Status.load(d / "STATUS.md")  # a real project reaches the checkpoint with every earlier phase past
        for r in st.rows["Phases"]:
            if status.CHAIN.index(r[0]) < status.CHAIN.index("build"):
                r[1:6] = ["overridden", TODAY, "", "", "Override: the checkpoint's fixture"]
        st.save(d / "STATUS.md")
        code, out = run(d, "set", "dev-check", "filled", "--verdict", "fail", "--section-from", str(src),
                        "--security-from", sec_table(d, REAL_TABLE))
        if code != 0 or "The rest of the close" not in out or "Open a NEW conversation and type:" not in out \
                or "M1-A-01 install + session" not in (d / "PRODUCT.md").read_text(encoding="utf-8"):
            fails.append(f"a realistic checkpoint FAIL should record the first time and print the close and the "
                         f"handoff: {out.strip()[:600]}")
        # owner 2026-10-06: the record is saved without a question (a separate save turn cost ~680K across 4 tools)
        last = subprocess.run(["git", "log", "-1", "--format=%s"], cwd=d, capture_output=True, text=True).stdout
        if "saved: commit" not in out or not last.startswith("dev-check: FAIL"):
            fails.append(f"`set dev-check filled` should save the project unasked: {last!r} / {out.strip()[-400:]}")
        # owner 2026-10-06: after a FAIL the handoff names the work - the first ticket still to build - not /dev-check
        if not re.search(r"Open a NEW conversation and type: /\S*build M1-A-01 - the checkpoint failed with 2 ticket", out):
            fails.append(f"a checkpoint FAIL with tickets missing should hand off to /build <first missing ticket>: "
                         f"{out.strip()[-500:]}")


DC_TICKETS = """# Tickets - the plan

## M1 Core slice
| Epic | Lane | Owner | Tickets in build order |
|---|---|---|---|
| [M1-A] Part a | a | Senior | M1-A-01 Build part a · M1-A-02 Build part a2 |
| [M1-B] Part b | b | Senior | M1-B-01 Build part b |

## M2 Later
| Epic | Lane | Owner | Tickets in build order |
|---|---|---|---|
| [M2-A] More | a | Senior | M2-A-01 More of a |

## Day 1 — who starts what
| Seat | Lane | Day-1 ticket | Why |
|---|---|---|---|
| SR1 | a | M1-A-01 | no dependencies |
| SR2 | b | M1-B-01 | no dependencies |
"""
DC_PLAN = """- **Phases / milestones (core first):**
  - M1 Core slice: one customer sees one step (2026-09-21 → 09-30)
  - M2 Later: more customers (10-01 → 10-20)
- **Timeline:** 2 people × 20 h/week, start 2026-09-21
- **Exit criteria per milestone:**
  - M1: a seeded customer is shown one step, approve and ignore each write a log row, and a customer with no moment gets no step. Needs: seeded customers (M1)
    - superseded 2026-09-22: the log row is written by the audit module (owner)
  - M2: the scoring script reports the catch rate
"""
DC_RECORD = """**Verdict: FAIL (2026-09-24).** 1 of 3 M1 tickets built.
- Gate: `just check` → 40 passed.
- Secret scan: `just secrets` → no leaks.
- Dependency scan: `just vuln` → 0 known vulnerabilities.
- Live path: GET /api/items → 200.
- Security: the 3 listed files reviewed, 0 findings.
- Scope: no creep found.
- Exit criterion 1 (a seeded customer is shown one step ...): partly - the step shows, no log row yet.
- Exit criterion 2 (a customer with no moment gets no step): not met - M1-B-01 is not built.
- Schedule: M1 ends 2026-09-30 and 2 of 3 tickets are left; at the pace so far it ends about 2 days late.
- Later milestones: M2 0 of 1 built.
"""


def test_dev_check_milestone(fails: list[str]) -> None:
    """#45 (2.2): a logged checkpoint judged "M6" and "1 of 48" while M1 was being built - TICKETS.md listed its ids
    bare, and the start read only backticked ones. The start now judges the CURRENT milestone (later ones one line),
    prints #Plan's exit criteria split, the schedule computed from #Plan's dates and pace, the scan commands, the
    routes, and the files no /build or /ship review saw; the close refuses a record that maps no criterion, has no
    schedule line or no scan line, and warns on a bare UNVERIFIED."""
    row = "| [M1-A] Part a | a | Senior | M1-A-01 Build part a · M1-A-02 Build part a2 |"
    if status.TICKET_ID.findall(row) or status.TICKET_ID_BARE.findall(row) != ["M1-A-01", "M1-A-02"]:
        fails.append("bare ticket ids in an epic table should be read (the backticked form alone reads none: red)")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d)
        fresh(d)
        (d / "TICKETS.md").write_text(DC_TICKETS, encoding="utf-8")
        (d / "PRODUCT.md").write_text(f"# P\n\n## Scope\n- **Non-goals:** billing\n\n## Plan\n{DC_PLAN}\n"
                                      f"## Dev-complete\n\n## Tests\n", encoding="utf-8")
        (d / "justfile").write_text("check:\n    pytest\n\nsecrets:\n    gitleaks detect\n\nvuln:\n    pip-audit\n\n"
                                    "audit:\n    python audit.py\n", encoding="utf-8")
        (d / "app").mkdir()
        (d / "app" / "__init__.py").write_text("", encoding="utf-8")
        (d / "app" / "foundation.py").write_text("SECRET = 'x'\n", encoding="utf-8")
        (d / "app" / "routes.py").write_text("from fastapi import APIRouter\nrouter = APIRouter(prefix=\"/api\")\n\n"
                                             "@router.get(\"/items\")\ndef items():\n    return []\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "foundation: skeleton"], cwd=d)
        (d / "app" / "a.py").write_text("A = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "M1-A-01: build part a"], cwd=d)
        rec = d / "status" / "tickets"
        rec.mkdir(parents=True, exist_ok=True)
        (rec / "2026-09-24-m1-a-01.md").write_text(
            "<!-- One ticket, written by status.py. Never edit by hand. -->\nTicket: M1-A-01\nDate: 2026-09-24\nDoD met: "
            "yes\nHow verified: gate.py -> 3 passed\nFull-suite runs: 1\nReview: code + security R1 clean\n"
            "Doc: docs/features/a.md\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "M1-A-01: ticket record"], cwd=d)
        code, out = run(d, "next", "--phase", "dev-check")
        for want in ("===== checkpoint: M1 ", "Tickets of M1", "M1-A-01: done · 2026-09-24", "M1-A-02: not recorded",
                     "Later milestones - not judged now", "M2 0 of 1 built",
                     "1. a seeded customer is shown one step, approve and ignore each write a log row",
                     "2. a customer with no moment gets no step", "(note: superseded 2026-09-22",
                     "Schedule: M1 runs 2026-09-21 → 2026-09-30; today is 2026-09-24 (6 days left); 2 of 3 tickets left",
                     "1 ticket(s) in 4 day(s)", "done about 2026-10-02 - 2 days LATE", "about 34 h",
                     "secret scan: `just secrets`", "dependency scan: `just vuln`", "GET /api/items · app/routes.py",
                     "app/ (2): foundation.py, routes.py", "M1-A-01 at "):
            if want not in out:
                fails.append(f"the checkpoint start lacks {want!r}: {out[out.find('====='):][:2500]}")
        if "a.py" in out.split("Security review")[1].split("Skip")[0] or "__init__" in out.split("Security review")[1]:
            fails.append("the security review list should skip a file /build reviewed (unchanged since) and empty files")
        src = Path(t) / "dc.md"
        breaks = {"maps none of M1's 2 #Plan exit criteria": DC_RECORD.replace("partly", "open").replace("not met", "open"),
                  "no `Schedule:` line": DC_RECORD.replace("- Schedule:", "- Pace:"),
                  "no line for the secret scan": DC_RECORD.replace("- Secret scan: `just secrets` → no leaks.\n", ""),
                  "no line for the dependency scan": DC_RECORD.replace("- Dependency scan: `just vuln` → 0 known "
                                                                       "vulnerabilities.\n", "")}
        for name, body in breaks.items():
            src.write_text(body, encoding="utf-8")
            code, out = run(d, "set", "dev-check", "filled", "--verdict", "fail", "--section-from", str(src), "--dry-run")
            if name not in out:
                fails.append(f"/dev-check close check {name!r} did not go red on its own break: {out.strip()[-500:]}")
        src.write_text(DC_RECORD + "- No hardcoding: UNVERIFIED.\n", encoding="utf-8")
        code, out = run(d, "set", "dev-check", "filled", "--verdict", "fail", "--section-from", str(src), "--no-commit",
                        "--security-from", sec_table(d, "CLEAN - the 3 files read whole, nothing found"))
        if code != 0 or "UNVERIFIED without why" not in out or "a warning, not a refusal" not in out:
            fails.append(f"a full checkpoint record should save, warning on a bare UNVERIFIED: {out.strip()[-700:]}")


def test_dev_check_security_receipt(fails: list[str]) -> None:
    """#45 (parked in 2.0, built in 2.4): a `Security:` line that claims a result needs the helper's table -
    `--security-from <file>` - counted per severity against the line, kept as a receipt in .git/playbook-review/;
    a later record reuses it while no code file changed; UNVERIFIED needs none. Each check red on its own break."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "p"
        d.mkdir()
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d)
        fresh(d)
        (d / "TICKETS.md").write_text(DC_TICKETS, encoding="utf-8")
        (d / "PRODUCT.md").write_text(f"# P\n\n## Scope\n- **Non-goals:** billing\n\n## Plan\n{DC_PLAN}\n"
                                      f"## Dev-complete\n\n## Tests\n", encoding="utf-8")
        (d / "app").mkdir()
        (d / "app" / "dev.py").write_text("STORE = 'real'\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "base"], cwd=d)
        src = Path(t) / "dc.md"
        one_medium = DC_RECORD.replace("- Security: the 3 listed files reviewed, 0 findings.",
                                       "- Security: helper review of the 3 listed files - 1 MEDIUM, 2 LOW (issues #2, #3).")
        base_args = ["set", "dev-check", "filled", "--verdict", "fail", "--section-from", str(src)]
        receipt = d / ".git" / "playbook-review" / "dev-check-security.json"
        reds = {"no review table backs it": (one_medium, []),
                "the review table has 2 - say": (one_medium.replace("1 MEDIUM, 2 LOW", "1 MEDIUM, 1 LOW"),
                                                ["--security-from", sec_table(d, REAL_TABLE)]),
                "says 0 finding(s), the review table has 3": (DC_RECORD, ["--security-from", sec_table(d, REAL_TABLE)]),
                "holds no findings row": (one_medium, ["--security-from", sec_table(d, "looked at it, fine")]),
                "no such file, or it is empty": (one_medium, ["--security-from", str(Path(t) / "missing.md")]),
                # 2.4 review: a table saved in the repo gets committed (findings public); a self-review never signs
                # off security, by the table or by the line
                "is inside the project": (one_medium, ["--security-from", str(d / "notes" / "security.md")]),
                "says it is a self-review": (one_medium, ["--security-from", sec_table(d, REAL_TABLE)]),
                "claims a result from a self-review": (
                    one_medium.replace("helper review of the 3 listed files", "self-review of the 3 listed files"),
                    ["--security-from", sec_table(d, REAL_TABLE)])}
        inside = d / "notes" / "security.md"
        inside.parent.mkdir()
        inside.write_text(REAL_TABLE, encoding="utf-8")
        for name, (body, extra) in reds.items():
            src.write_text(body, encoding="utf-8")
            if extra and extra[1].endswith("-security.md"):  # each red case writes its own table last
                sec_table(d, REAL_TABLE if name != "holds no findings row" else "looked at it, fine")
                if name == "says it is a self-review":
                    sec_table(d, REAL_TABLE + "\nNo helper on this tool - a self-review of the 3 files.\n")
            code, out = run(d, *base_args, *extra, "--dry-run")
            if name not in out:
                fails.append(f"security receipt check {name!r} did not go red on its own break: {out.strip()[-600:]}")
        inside.unlink()
        inside.parent.rmdir()
        # 2.4 review: the start names each tool's way to start the ONE security helper, and the fallback
        tool = status.playbook_tool
        try:
            for name, want in (("claude", "ONE helper (the Agent tool (run_in_background: true))"),
                               ("codex", "this skill explicitly asks you to spawn ONE agent; then ONE `wait_agent`")):
                status.playbook_tool = lambda name=name: name
                code, out = run(d, "next", "--phase", "dev-check")
                if want not in out or "self-review only, <n> findings`, with no --security-from" not in out \
                        or "scratch file OUTSIDE the repo" not in out:
                    fails.append(f"/dev-check's start on {name} should name its security helper route and the "
                                 f"self-review fallback: {out[out.find('Security review'):][:500]}")
        finally:
            status.playbook_tool = tool
        if receipt.exists():
            fails.append("a refused or dry-run record must write no security receipt")
        src.write_text(one_medium, encoding="utf-8")
        code, out = run(d, *base_args, "--security-from", sec_table(d, REAL_TABLE))
        if code != 0 or "security receipt: 1 MEDIUM, 2 LOW" not in out or not receipt.is_file():
            fails.append(f"a security line matching the helper's table should record and keep a receipt: "
                         f"{out.strip()[-600:]}")
        # a re-run with no code change reuses the receipt; a changed code file needs a new review
        code, out = run(d, *base_args)
        if code != 0:
            fails.append(f"an unchanged checkout should reuse the security receipt: {out.strip()[-500:]}")
        (d / "app" / "dev.py").write_text("STORE = 'fake'\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "fix the store default"], cwd=d)
        code, out = run(d, *base_args, "--dry-run")
        if "the security receipt is for" not in out or "app/dev.py" not in out:
            fails.append(f"a receipt for older code should be refused, naming the changed file: {out.strip()[-500:]}")
        src.write_text(one_medium.replace("- Security: helper review of the 3 listed files - 1 MEDIUM, 2 LOW (issues #2, #3).",
                                          "- Security: UNVERIFIED - the helper returned nothing twice"), encoding="utf-8")
        code, out = run(d, *base_args, "--dry-run")
        if "security receipt" in out or "no review table" in out:
            fails.append(f"an UNVERIFIED security line needs no table: {out.strip()[-500:]}")
        # Claude Code only, warn-only: a helper named in the line and no helper call in the newest log
        logs = Path(t) / "logs"
        logs.mkdir()
        (logs / "s.jsonl").write_text('{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash",'
                                      '"input":{"command":"just check"}}]}}\n', encoding="utf-8")
        real = status.session_costs
        status.session_costs = lambda: type("SC", (), {"project_log_dir": staticmethod(lambda b: logs)})
        try:
            body = "- Security: helper review - 1 MEDIUM\n"
            if not status.security_helper_warning(d, body):
                fails.append("a helper named with no helper call in the log should warn")
            (logs / "s.jsonl").write_text('{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Agent",'
                                          '"input":{"prompt":"Security review of these files"}}]}}\n', encoding="utf-8")
            if status.security_helper_warning(d, body):
                fails.append("a logged helper call about security should not warn")
        finally:
            status.session_costs = real


def test_verify_phases_24(fails: list[str]) -> None:
    """2.4 (#62, #60): /dev-check's and /test's starts print Spine resolution, Re-run semantics and Declined runs only
    when the case is real (decided from the project's facts); docs/tests.md numbers every heading (refused) and is
    plain English (warned); the checking phases' close is short and points at the record."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d)
        fresh(d)
        (d / "TICKETS.md").write_text("# Tickets\n\n## M1 core\n| `M1-A-01` | a |\n", encoding="utf-8")
        (d / "PRODUCT.md").write_text("# P\n\n## Scope\n- **Non-goals:** billing\n\n## Dev-complete\n\n## Tests\n",
                                      encoding="utf-8")
        for ph in ("dev-check", "test"):
            code, out = run(d, "next", "--phase", ph)
            for sec in ("§Spine resolution", "§Re-run semantics", "§Declined runs"):
                if sec in out:
                    fails.append(f"a first /{ph} run on a project with PRODUCT.md should not print {sec}")
        st = status.Status.load(d / "STATUS.md")
        for ph in ("dev-check", "test"):
            st.phase(ph)[1:6] = ["filled", TODAY, "", "fail", ""]
        st.save(d / "STATUS.md")
        for ph in ("dev-check", "test"):
            code, out = run(d, "next", "--phase", ph)
            if "§Re-run semantics" not in out:
                fails.append(f"a /{ph} re-run (its section filled) should print §Re-run semantics")
        # /test asked the dev-check question (failed, milestone finished): the Stop answer is a declined run
        st = status.Status.load(d / "STATUS.md")
        st.phase("test")[1:6] = ["empty", "", "", "", ""]
        st.save(d / "STATUS.md")
        real = status.milestone_unfinished
        status.milestone_unfinished = lambda st_: None
        try:
            if "Declined runs" in status.verify_skip("test", _with_base(d)):
                fails.append("/test should keep §Declined runs while its gate line asks the dev-check question")
        finally:
            status.milestone_unfinished = real
        # docs/tests.md: an unnumbered heading is refused, a numbered one is not; long sentences warn
        (d / "docs").mkdir(exist_ok=True)
        (d / "docs" / "tests.md").write_text("# Tests\n\n## What the tests prove\n\nThe login works.\n",
                                             encoding="utf-8")
        src = d.parent / f"{d.name}-tests.md"
        src.write_text("- Live path: UNVERIFIED - no server yet\n- Security: forged token 401\n- Regression: none\n",
                       encoding="utf-8")
        # 2.4 review: `set` numbers a heading without one (as /validate's, /eval's, /learn's and /deploy's do) -
        # never a refusal and a rewrite; a dry run leaves the file as the run wrote it
        code, out = run(d, "set", "test", "filled", "--verdict", "fail", "--section-from", str(src), "--dry-run")
        doc = (d / "docs" / "tests.md").read_text(encoding="utf-8")
        if "without a number" in out or "## What the tests prove" not in doc:
            fails.append(f"docs/tests.md with an unnumbered heading should not be refused, and a dry run should "
                         f"leave it as written: {out.strip()[-500:]}")
        code, out = run(d, "set", "test", "filled", "--verdict", "fail", "--section-from", str(src), "--no-commit")
        doc = (d / "docs" / "tests.md").read_text(encoding="utf-8")
        if code != 0 or "## 1. What the tests prove" not in doc:
            fails.append(f"`set test filled` should number docs/tests.md's unnumbered heading: {out.strip()[-500:]}")
        long = " ".join(["word"] * 35) + "."
        (d / "docs" / "tests.md").write_text(f"# Tests\n\n## 1. What the tests prove\n\n{long} The login works \u2014 "
                                             f"mostly.\n", encoding="utf-8")
        code, out = run(d, "set", "test", "filled", "--verdict", "fail", "--section-from", str(src), "--dry-run")
        if "without a number" in out:
            fails.append(f"a numbered docs/tests.md should pass the layout check: {out.strip()[-400:]}")
        warns = status.test_warnings(d)
        if not any("docs/tests.md: sentences average" in w for w in warns) or not any("em-dash" in w for w in warns):
            fails.append(f"docs/tests.md's long sentences and dash joins should warn: {warns}")
        tpl = (ROOT / "templates" / "tests.md").read_text(encoding="utf-8")
        if status.unnumbered_headings(tpl):
            fails.append(f"templates/tests.md has unnumbered headings: {status.unnumbered_headings(tpl)}")
    # the checking phases' close: short, pointing at the record; a document phase keeps its own short close
    for ph in ("dev-check", "test", "ship"):
        if "at most 12 lines" not in status.close_steps_text(ph, "saved: commit abc1234"):
            fails.append(f"/{ph}'s close should be the short checking-phase close")
    if "at most 12 lines" in status.close_steps_text("vision", "saved: commit abc1234"):
        fails.append("/vision's close keeps its own short close")


def _with_base(d: Path):
    st = status.Status.load(d / "STATUS.md")
    st.base = d
    return st


def test_demo_proof_checks(fails: list[str]) -> None:
    """DP1-DP3, what a logged Gemini build hid behind a fake that accepted any request: every Demo claim needs a RED
    cut tagged D<n> (or --uncut with a reason the user hears), a changed file calling an outside service needs a RED
    cut of its own, and the feature doc names what real thing the code could touch and the test that refuses it."""
    import json
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d)
        (d / "README.md").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "base"], cwd=d)
        fresh(d)
        (d / "docs" / "issues").mkdir(parents=True)
        (d / "docs" / "issues" / "M1-B-01_seed.md").write_text(
            "# [M1-B-01] seed\n\n### 👀 Demo — what works after this merges\nRun the script: the store gains one order "
            "per case, its status as the case says.\n\n### 🧪 Verification Command\n```bash\npytest -q\n```\n",
            encoding="utf-8")
        if status.demo_claims((d / "docs/issues/M1-B-01_seed.md").read_text(encoding="utf-8")) != \
                ["the store gains one order per case", "its status as the case says"]:
            fails.append(f"demo_claims split the Demo wrongly: {status.demo_claims((d / 'docs/issues/M1-B-01_seed.md').read_text(encoding='utf-8'))}")
        subprocess.run(["git", "checkout", "-q", "-b", "m1-b-01"], cwd=d)
        (d / "app").mkdir()
        (d / "app" / "seed.py").write_text("import httpx\n\n\ndef seed():\n    return httpx.post('x')\n", encoding="utf-8")
        (d / "app" / "test_seed.py").write_text("def test_refuses_live_shop():\n    pass\n", encoding="utf-8")
        (d / "docs" / "features").mkdir(parents=True)
        doc = d / "docs" / "features" / "seed.md"
        body = "# Seed\n\n" + TOP_HALF + "## Review\nCLEAN.\n\n### Files reviewed\n- app/seed.py: request - nothing found\n\n## Next\nx\n"
        doc.write_text(body, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "work"], cwd=d)
        run(d, "rules", "build")
        ticket = ["ticket", "M1-B-01", "--dod", "yes", "--verified", "pytest -> 1 passed", "--doc", "docs/features/seed.md",
                  "--not-wired", "x"]
        code, out = run(d, *ticket)
        if code == 0 or "2 Demo claim(s) with no RED cut" not in out:
            fails.append(f"Demo claims with no cut were not refused (DP1): {out.strip()[:400]}")
        if "app/seed.py call(s) an outside service" not in out:
            fails.append(f"a file calling an outside service with no cut was not refused (DP2): {out.strip()[:400]}")
        if "no `Real-world reach:` line" not in out:
            fails.append(f"a feature doc with no Real-world reach line was not refused (DP3): {out.strip()[:400]}")
        wc = d / ".git" / "playbook-wirecut"
        wc.mkdir(exist_ok=True)
        (wc / "results.jsonl").write_text(json.dumps({"branch": "m1-b-01", "red": 1, "total": 2, "cuts": [
            {"file": "app/seed.py", "claim": "D1", "result": "RED"},
            {"file": "app/seed.py", "claim": "D2", "result": "NOT CAUGHT"}]}) + "\n", encoding="utf-8")
        doc.write_text(body + "\nReal-world reach: a live shop - guarded by test_nothing_here\n", encoding="utf-8")
        code, out = run(d, *ticket)
        if "1 Demo claim(s) with no RED cut: D2" not in out:
            fails.append(f"a claim whose cut was NOT CAUGHT counted as proven (DP1): {out.strip()[:400]}")
        if "call(s) an outside service" in out:
            fails.append("a file with a RED cut was still refused as an uncut outside call (DP2)")
        if "names no test that exists" not in out:
            fails.append(f"a Real-world reach line naming a missing test was accepted (DP3): {out.strip()[:400]}")
        doc.write_text(body + "\nReal-world reach: a live shop - guarded by `test_refuses_live_shop`\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "doc"], cwd=d)
        gate_pass(d, ticket="M1-B-01")
        with open(wc / "results.jsonl", "a", encoding="utf-8") as h:  # LP1 still wants one run with every cut RED
            h.write(json.dumps({"branch": "m1-b-01", "red": 1, "total": 1,
                                "cuts": [{"file": "app/seed.py", "claim": "D1", "result": "RED"}]}) + "\n")
        code, out = run(d, *ticket, "--uncut", "D2: status needs the real API")
        if code != 0:
            fails.append(f"all three met (D2 uncut with a reason) was still refused: {out.strip()[:400]}")
        elif "D2 is not proven by a test - status needs the real API" not in out:
            fails.append(f"an --uncut claim was not said to the user: {out.strip()[:400]}")
        # audit 6: code the branch adds that touches a password needs a security review though the ticket never said
        # so; and a gate run that names no ticket is no one's - it does not satisfy --dod yes
        (d / "app" / "seed.py").write_text("import httpx\n\n\ndef seed(password):\n    return httpx.post('x')\n",
                                           encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "a password"], cwd=d)
        gate_pass(d, ticket="")
        code, out = run(d, *ticket, "--uncut", "D2: status needs the real API", "--uncut", "D1: x",
                        "--uncut", "app/seed.py: x")
        if code == 0 or "the code this branch added touches password" not in out:
            fails.append(f"a password the ticket never named reached the code with no security review (audit 6): "
                         f"{out.strip()[:400]}")
        if "needs the ticket's own Verification Command" not in out:
            fails.append(f"a gate run naming no ticket satisfied --dod yes (audit 6): {out.strip()[:400]}")


def test_build_ticket_checks(fails: list[str]) -> None:
    """A ticket row needs what a logged Gemini build skipped: `rules build` run today, the ticket branch (never main -
    it merged its own branch), and a feature doc whose Review section names every changed code file (it recorded
    "R1 pass 0 findings" after one `git diff`). Each broken on its own is refused; all three met is recorded."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d)
        (d / "README.md").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "base"], cwd=d)
        fresh(d)
        ticket = ["ticket", "M1-A-01", "--dod", "yes", "--verified", "pytest -> 3 passed", "--doc", "docs/features/a.md"]
        code, out = run(d, *ticket)
        if code == 0 or "on main" not in out or "rules build" not in out:
            fails.append(f"a ticket on main with no `rules build` was recorded: {out.strip()[:300]}")
        subprocess.run(["git", "checkout", "-q", "-b", "m1-a-01"], cwd=d)
        (d / "app").mkdir()
        (d / "app" / "shops.py").write_text("def f():\n    return 1\n", encoding="utf-8")
        (d / "app" / "test_shops.py").write_text("def test_f():\n    pass\n", encoding="utf-8")
        subprocess.run(["git", "add", "app"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "work"], cwd=d)
        run(d, "rules", "build")
        (d / "docs" / "features").mkdir(parents=True)
        doc = d / "docs" / "features" / "a.md"
        doc.write_text("# A\n\n" + TOP_HALF + "## How verified\npytest\n", encoding="utf-8")
        code, out = run(d, *ticket)
        if code == 0 or "no Review section" not in out:
            fails.append(f"a feature doc with no Review section was accepted: {out.strip()[:300]}")
        doc.write_text("# A\n\n" + TOP_HALF + "## Review\nR1 0 findings.\n\n## Files\napp/shops.py\n", encoding="utf-8")
        code, out = run(d, *ticket)
        if code == 0 or "app/shops.py" not in out:
            fails.append(f"a Review section that names no changed file was accepted: {out.strip()[:300]}")
        # RV5: the file list sits under a sub-heading inside ## Review (a Gemini build had to flatten one to pass)
        doc.write_text("# A\n\n" + TOP_HALF + "## Review\nCLEAN.\n\n### Files reviewed\n- app/shops.py: input bounds, error paths - "
                       "nothing found\n\n## Next\nx\n", encoding="utf-8")
        # LP1: no wire cut run, and nothing outside app/ uses what the branch adds (the Gemini audit service)
        code, out = run(d, *ticket)
        if code == 0 or "no wirecut.py run" not in out or "nothing outside its own module uses" not in out:
            fails.append(f"a ticket with no wire cut and an unwired addition was recorded: {out.strip()[:300]}")
        if "does not name" in out:
            fails.append("files listed under a sub-heading of ## Review were not counted (RV5)")
        wc = d / ".git" / "playbook-wirecut"
        wc.mkdir(exist_ok=True)
        (wc / "results.jsonl").write_text('{"branch": "m1-a-01", "red": 2, "total": 3}\n', encoding="utf-8")
        (d / "main.py").write_text("from app.shops import f\n\nf()\n", encoding="utf-8")
        doc.write_text("# A\n\n" + TOP_HALF + "## Review\nCLEAN.\n\n### Files reviewed\n- app/shops.py: input bounds - nothing found\n"
                       "- main.py: the call site - nothing found\n\n## Next\nx\n", encoding="utf-8")
        subprocess.run(["git", "add", "main.py"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "wire"], cwd=d)
        code, out = run(d, *ticket)
        if code == 0 or "no wirecut.py run" not in out:
            fails.append("a wire-cut run with a cut NOT CAUGHT was accepted")
        (wc / "results.jsonl").write_text('{"branch": "m1-a-01", "red": 3, "total": 3}\n', encoding="utf-8")
        # R3-5: no gate run over the final code - refused; a failing one, or one before the last code commit - refused
        code, out = run(d, *ticket)
        if code == 0 or "no passing gate.py run" not in out:
            fails.append(f"a ticket with no gate run over the final code was recorded (R3-5): {out.strip()[:300]}")
        gate_pass(d, passed=False)
        code, out = run(d, *ticket)
        if code == 0 or "no passing gate.py run" not in out:
            fails.append("a failing gate run was accepted as the close gate (R3-5)")
        gate_pass(d)
        (d / "app" / "shops.py").write_text("def f():\n    return 2\n", encoding="utf-8")
        subprocess.run(["git", "add", "app"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "a code change after the gate"], cwd=d)
        code, out = run(d, *ticket)
        if code == 0 or "no passing gate.py run" not in out:
            fails.append("a gate run older than the last code commit was accepted (R3-5)")
        (d / "justfile").write_text("check: lint test\n\nlint:\n    ruff check .\n", encoding="utf-8")
        subprocess.run(["git", "add", "justfile"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "recipe"], cwd=d)
        gate_pass(d, "uv run ruff check .", "uv run pytest -q")
        code, out = run(d, *ticket)
        if code == 0 or "just check" not in out:
            fails.append(f"a gate that skipped the project's `just check` recipe was accepted (R3-5): {out.strip()[:300]}")
        gate_pass(d, "just check")
        # R3-4: the row's count and the Review table disagree - refused; a review with no table and no CLEAN - refused
        code, out = run(d, *ticket, "--review", "helper agent R1 3 findings")
        if code == 0 or "must agree" not in out:
            fails.append(f"--review '3 findings' against a CLEAN table was accepted (R3-4): {out.strip()[:300]}")
        body = doc.read_text(encoding="utf-8")
        doc.write_text(body.replace("CLEAN.", "The reviewer returned nothing."), encoding="utf-8")
        code, out = run(d, *ticket)
        if code == 0 or "did not run" not in out:
            fails.append(f"a Review section with no findings table and no CLEAN was accepted: {out.strip()[:300]}")
        doc.write_text(body.replace("CLEAN.", "| Severity | File:line | What | Fixed by |\n|---|---|---|---|\n"
                                    "| MEDIUM | app/shops.py:2 | wrong value | abc123 |\n"), encoding="utf-8")
        code, out = run(d, *ticket, "--review", "helper agent R1 1 finding")
        if code != 0:
            fails.append(f"a review count that matches its table was refused (R3-4): {out.strip()[:300]}")
        # severity in the second column is still a finding row (a lean build's real review was refused over it)
        doc.write_text(body.replace("CLEAN.", "| # | Severity | File:line | What | Fixed by |\n|---|---|---|---|---|\n"
                                    "| 1 | **MEDIUM** | app/shops.py:2 | wrong value | abc123 |\n"), encoding="utf-8")
        code, out = run(d, *ticket, "--review", "helper agent R1 1 finding")
        if code != 0:
            fails.append(f"a findings table with severity in its second column was refused: {out.strip()[:300]}")
        doc.write_text(body.replace("CLEAN.", "| Severity | File:line | What | Fixed by |\n|---|---|---|---|\n"
                                    "| MEDIUM | app/shops.py:2 | wrong value | abc123 |\n"), encoding="utf-8")
        code, out = run(d, *ticket)
        if code != 0:
            fails.append(f"a ticket with rules read, on its branch, cuts RED, wired, every file reviewed was refused: "
                         f"{out.strip()[:300]}")
        (d / ".git" / status.RULES_MARK / "build").write_text("2026-01-01", encoding="utf-8")
        code, out = run(d, *ticket)
        if code == 0 or "rules build" not in out:
            fails.append("a `rules build` mark from another day was accepted")
        run(d, "rules", "build")
        # the stated reasons stand in for a cut and a caller, and land in the row
        (wc / "results.jsonl").unlink()
        (d / "main.py").unlink()
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "unwire"], cwd=d)
        gate_pass(d, "just check")
        code, out = run(d, *ticket, "--no-cuts", "a pure formatter", "--not-wired", "M1-A-02 calls it")
        rows = status.Status.load(d / "STATUS.md").rows["Tickets"]
        if code != 0 or not any("no cuts: a pure formatter" in r[3] and "not wired: M1-A-02" in r[3] for r in rows):
            fails.append(f"--no-cuts / --not-wired were not accepted and recorded in the row: {out.strip()[:300]}")
        # DB1: #Architecture's Postgres against a SQLite test setup - refused; the user's override - a note to say it
        (d / "PRODUCT.md").write_text("# P\n\n## Architecture\n- Database: Postgres 17\n\n## Foundation\n- ok\n",
                                      encoding="utf-8")
        (d / "conftest.py").write_text('URL = "sqlite+aiosqlite:///:memory:"\n', encoding="utf-8")
        code, out = run(d, *ticket, "--no-cuts", "x", "--not-wired", "y")
        if code == 0 or "tests run on SQLite" not in out:
            fails.append(f"tests on SQLite under a Postgres architecture were accepted (DB1): {out.strip()[:300]}")
        # R3-1: an override line the branch itself added to #Foundation does not count (a Gemini build wrote its own)
        (d / "PRODUCT.md").write_text("# P\n\n## Architecture\n- Database: Postgres 17\n\n## Foundation\n- Override "
                                      "2026-09-26: tests on SQLite until M2\n", encoding="utf-8")
        code, out = run(d, *ticket, "--no-cuts", "x", "--not-wired", "y")
        if code == 0 or "added on this branch" not in out:
            fails.append(f"an override the branch wrote into #Foundation itself was accepted (R3-1): {out.strip()[:300]}")
        run(d, "open", "--from", "build", "--what", "Override: tests on SQLite - the user's words: fine until M2",
            "--clears", "tests run on Postgres")
        code, out = run(d, *ticket, "--no-cuts", "x", "--not-wired", "y")
        if code != 0 or "the tests ran on SQLite, production is Postgres" not in out:
            fails.append(f"an override recorded as the user's open item should record with a note (DB1): {out.strip()[:300]}")
        (d / "conftest.py").unlink()
        # RV3 + RV4: on a copy install for another tool, a Claude-only command in --review is refused, a named route
        # is recorded, and the run is told to say which review ran
        real = status.playbook_tool
        status.playbook_tool = lambda: "antigravity"
        try:
            base = [*ticket, "--no-cuts", "x", "--not-wired", "y"]
            code, out = run(d, *base, "--review", "/code-review -> R1 clean")
            if code == 0 or "Claude Code command antigravity does not have" not in out:
                fails.append(f"Antigravity claiming /code-review was recorded (RV3): {out.strip()[:300]}")
            code, out = run(d, *base, "--review", "R1 clean")
            if code == 0 or "does not say which review ran" not in out:
                fails.append("a review record naming no route was accepted on Antigravity (RV3)")
            code, out = run(d, *base, "--review", "helper agent R1 1 finding")
            if code != 0 or "which review ran on antigravity" not in out:
                fails.append(f"a helper-agent review on Antigravity should record and tell the user (RV3/RV4): "
                             f"{out.strip()[:300]}")
            # R3-3: a self-review cannot sign off security work - the user's words can
            (d / "docs" / "issues").mkdir(parents=True, exist_ok=True)
            (d / "docs" / "issues" / "M1-A-01_install.md").write_text(
                "# [M1-A-01] Install\n\n### 🎯 Goal\nVerify the session token before any exchange.\n\n"
                "### 📁 Target Files\n- [ ] `app/shops.py`\n\n### 🧪 Verification Command\n```bash\npytest -q\n```\n",
                encoding="utf-8")
            doc.write_text(doc.read_text(encoding="utf-8") + "\nReal-world reach: another shop - guarded by `test_f`\n",
                           encoding="utf-8")  # DP3: an auth ticket names what real thing it could touch
            gate_pass(d, "just check", "pytest -q")
            code, out = run(d, *base, "--review", "self-review (code + security) R1 1 finding")
            if code == 0 or "only a self-review ran" not in out:
                fails.append(f"a self-review signed off an auth ticket on Antigravity (R3-3): {out.strip()[:300]}")
            # fix 1: the question is the code's, word for word, with the SAFE choice recommended
            if "Run an independent security review first (Recommended)" not in out or "EXACTLY" not in out:
                fails.append(f"the refusal should carry the exact question, independent review recommended: {out[:400]}")
            for label in ("(Recommended) Approve self-review", "Approve", "yes", "ok fine"):
                code, out = run(d, *base, "--review", "self-review (code + security) R1 1 finding",
                                "--self-review-ok", label)
                if code == 0 or "option label or too short" not in out:
                    fails.append(f"--self-review-ok {label!r} (an option label, not a reason) was accepted: {out[:200]}")
            code, out = run(d, *base, "--review", "self-review (code + security) R1 1 finding", "--self-review-ok",
                            "the user: it is a test project, nothing real is exposed")
            if code != 0:
                fails.append(f"--self-review-ok with the user's words was refused (R3-3): {out.strip()[:300]}")
            # fix 2: another tool's security review counts as independent - no self-review sign-off needed
            code, out = run(d, *base, "--review", "self-review + another tool: Claude Code security review R1 1 finding")
            if code != 0:
                fails.append(f"a security review by another tool should record without --self-review-ok: {out[:300]}")
        finally:
            status.playbook_tool = real
        # the files the ticket does not name are explained in the doc; the demo's entry point is called by a test
        (d / "app" / "extra.py").write_text("X = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "app"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "extra"], cwd=d)
        gate_pass(d, "just check", "pytest -q")
        code, out = run(d, *ticket, "--no-cuts", "x", "--not-wired", "y", "--review", "helper agent: code + security review R1 1 finding")
        if code == 0 or "app/extra.py" not in out or "the ticket does not name" not in out:
            fails.append(f"a changed file outside Target Files, unexplained, was accepted: {out.strip()[:300]}")
        doc.write_text(doc.read_text(encoding="utf-8") + "\n## Deviations\n- app/extra.py: a shared constant\n",
                       encoding="utf-8")
        tfile = d / "docs" / "issues" / "M1-A-01_install.md"
        tfile.write_text(tfile.read_text(encoding="utf-8") + "\n### 👀 Demo\n`GET /api/session` installs the shop.\n",
                         encoding="utf-8")
        code, out = run(d, *ticket, "--no-cuts", "x", "--review", "helper agent: code + security review R1 1 finding")
        if code == 0 or "/api/session" not in out:
            fails.append(f"a demo entry point no test calls was accepted (R3-2): {out.strip()[:300]}")
        (d / "app" / "test_shops.py").write_text("def test_f(client):\n    client.get('/api/session')\n", encoding="utf-8")
        (d / "main.py").write_text("from app.shops import f\n\nf()\n", encoding="utf-8")
        doc.write_text(doc.read_text(encoding="utf-8").replace("## Next", "- app/extra.py: a constant - nothing found\n"
                                                               "- main.py: the call site - nothing found\n\n## Next"),
                       encoding="utf-8")
        subprocess.run(["git", "add", "app", "main.py"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "entry test"], cwd=d)
        gate_pass(d, "just check")
        code, out = run(d, *ticket, "--no-cuts", "x", "--review", "helper agent: code + security review R1 1 finding")
        if code == 0 or "needs the ticket's own Verification Command" not in out:
            fails.append(f"--dod yes with a close gate that never ran the ticket's own command was recorded (audit 3, "
                         f"finding 2): {out.strip()[:300]}")
        code, out = run(d, *ticket, "--no-cuts", "x", "--review", "helper agent: code review R1 1 finding")
        if code == 0 or "names no security review" not in out:
            fails.append(f"an auth ticket whose review names no security review was recorded: {out.strip()[:300]}")
        # a gate run for ANOTHER ticket that happened to run this ticket's command does not count (audit 5, fix 1)
        import json as _json
        gf = d / ".git" / "playbook-gate" / "results.jsonl"
        gf.write_text("", encoding="utf-8")
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
        gf.write_text(_json.dumps({"branch": "m1-a-01", "head": head, "dirty": [], "commands": ["just check", "pytest -q"],
                                   "passed": True, "ticket": "M1-B-02", "ticket_cmds": ["pytest -q"]}) + "\n",
                      encoding="utf-8")
        code, out = run(d, *ticket, "--no-cuts", "x", "--review", "helper agent: code + security review R1 1 finding")
        if code == 0 or "needs the ticket's own Verification Command" not in out:
            fails.append(f"another ticket's gate run satisfied this ticket's --dod yes: {out.strip()[:300]}")
        # a change to a check INPUT after the gate - a non-Markdown file under docs/, or DESIGN.md - makes it stale
        # (audit 3, finding 4: docs/contracts/openapi.json feeds a project's `just check`)
        gate_pass(d, "just check", "pytest -q")
        for f, body in (("docs/contracts/api.json", "{}\n"), ("DESIGN.md", "# D\n"), ("STRUCTURE.md", "# S\n")):
            (d / f).parent.mkdir(parents=True, exist_ok=True)
            (d / f).write_text(body, encoding="utf-8")
            subprocess.run(["git", "add", f], cwd=d)
            subprocess.run([*g, "commit", "-qm", f"change {f} after the gate"], cwd=d)
            code, out = run(d, *ticket, "--no-cuts", "x", "--review", "helper agent: code + security review R1 1 finding")
            if code == 0 or "no passing gate.py run" not in out:
                fails.append(f"{f} changed after the gate and its evidence still counted: {out.strip()[:200]}")
            gate_pass(d, "just check", "pytest -q")
        (d / "docs" / "features" / "note.md").write_text("# a doc-only change\n", encoding="utf-8")
        subprocess.run(["git", "add", "docs/features/note.md"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "doc after the gate"], cwd=d)
        code, out = run(d, *ticket, "--no-cuts", "x", "--review", "helper agent: code + security review R1 1 finding",
                        "--uncut", "D1: the test fixture has no code to cut")
        if code != 0:
            fails.append(f"a ticket whose entry point a test calls, extra file explained, was refused: {out.strip()[:300]}")
        if "close's step (6)" not in out or "Rules for the close" in out:
            fails.append(f"a recorded row should point at the close's step (6), not reprint the close's rules (the "
                         f"close gate printed them): {out[-300:]}")
        # /build never writes the spine: a branch that changed PRODUCT.md is refused, committed or not
        subprocess.run(["git", "add", "PRODUCT.md"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "the spine edited on a ticket branch"], cwd=d)
        gate_pass(d, "just check", "pytest -q")
        code, out = run(d, *ticket, "--no-cuts", "x", "--review", "helper agent: code + security review R1 1 finding")
        if code == 0 or "never writes the spine" not in out:
            fails.append(f"a ticket branch that changed PRODUCT.md was recorded: {out.strip()[:300]}")
        subprocess.run(["git", "rm", "-q", "--cached", "PRODUCT.md"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "undo the spine edit"], cwd=d)
        gate_pass(d, "just check")
        # LEAN start: one call prints the ticket, its files, the coding rules - not the close's - and marks rules read
        (d / ".git" / status.RULES_MARK / "build").unlink()
        code, out = run(d, "next", "--phase", "build", "--ticket", "M1-A-01")
        if code != 0 or "app/shops.py" not in out or "Per-feature contract" not in out or "Step 3c" in out \
                or not (d / ".git" / status.RULES_MARK / "build").is_file():
            fails.append(f"`next --phase build --ticket` should print the ticket, its files and the coding rules only, "
                         f"and mark the rules read: {out.strip()[:300]}")
        if "Git remote: none" not in out or "Never write" in out:
            fails.append(f"with no remote the start should say so, with the base it uses: {[l for l in out.splitlines() if 'remote' in l.lower()][:2]}")
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/x/y.git"], cwd=d)
        code, out2 = run(d, "next", "--phase", "build", "--ticket", "M1-A-01")
        subprocess.run(["git", "remote", "remove", "origin"], cwd=d)
        if "Git remote: origin = https://github.com/x/y.git (github)" not in out2 or "Never write \"no remote\"" not in out2:
            fails.append(f"with a remote the start should name it and forbid a stale 'no remote': {out2[-400:]}")
        if "Security review: REQUIRED" not in out:
            fails.append("the start should mark the security review REQUIRED for a ticket that touches a session token")
        if len(out) > 30000:
            fails.append(f"the lean start printed {len(out)} characters - past the inline limit it exists to stay under")
        # the start carries #Contracts' project-wide rules - never its file lists - so the build reads no spine itself
        (d / "PRODUCT.md").write_text("# P\n\n## Contracts\n- **Typed models / schemas:** Pydantic\n  - Schemas: "
                                      "`app/x.py` · `app/y.py`\n- **Boundary units/scale agreed:** one table\n  - Email: "
                                      "trimmed and lower-cased.\n  - `evidence: pytest -> 3 passed · x · 2026-09-27`\n",
                                      encoding="utf-8")
        code, out = run(d, "next", "--phase", "build", "--ticket", "M1-A-01")
        if "Email: trimmed and lower-cased" not in out or "Schemas: `app/x.py`" in out or "evidence: pytest" in out:
            fails.append(f"the start should print #Contracts' rules (units, formats) and not its file lists or "
                         f"evidence: {out[-600:]}")
        (d / "PRODUCT.md").write_text("# P\n\n## Contracts\n", encoding="utf-8")
        code, out = run(d, "next", "--phase", "build", "--ticket", "M1-A-01")
        if "#Contracts is empty" not in out:
            fails.append("the start should warn when #Contracts is empty")
        # the close's order + rules print on demand for /build only, trimmed to what a ticket's close uses (A15)
        code, out = run(d, "rules", "build", "--close")
        if code != 0 or "The close, in this order" not in out or "Step 3c" not in out \
                or "Per-feature contract" in out or "Re-run semantics" in out or len(out) > 16000:
            fails.append(f"`rules build --close` should print the close order + the close's rules only, under 16 KB "
                         f"({len(out)} chars): {out[:200]}")
        other = [p for p in status.CHAIN if p != "build" and p not in status.PHASE_CLOSE_RULES]
        code, out = run(d, "rules", other[0], "--close") if other else (1, "")
        if code == 0:
            fails.append("`rules <other phase> --close` should be refused - the close list is /build's")
        # the start prints ready-to-run commands (audit 4): the gate with this ticket's id; the dev server's command,
        # port and health URL from the project - or MISSING, never a placeholder to guess
        code, out = run(d, "next", "--phase", "build", "--ticket", "M1-A-01")
        if "--ticket M1-A-01" not in out or "<the project's full check recipe>" in out or "MISSING: the dev start" not in out:
            fails.append(f"the start should print the gate for this ticket and mark an unknown dev command MISSING: "
                         f"{out[-500:]}")
        jf = (d / "justfile").read_text(encoding="utf-8")
        (d / "justfile").write_text(jf + "\ndev:\n    uv run uvicorn app.main:app --reload --port 8123\n", encoding="utf-8")
        (d / "PRODUCT.md").write_text("# P\n\n## Foundation\n- Web with `/healthz` (process + database)\n\n## Contracts\n"
                                      "- **Boundary units/scale agreed:** one table\n", encoding="utf-8")
        code, out = run(d, "next", "--phase", "build", "--ticket", "M1-A-01")
        if '--cmd "just dev" --port 8123 --health http://localhost:8123/healthz' not in out \
                or "demo's entry: /api/session" not in out:
            fails.append(f"the start should read the dev command, port, health URL and the demo's entry from the "
                         f"project: {[l for l in out.splitlines() if 'live path' in l]}")
        (d / "justfile").write_text(jf, encoding="utf-8")
        # a project-level fix the start reports is marked as not this ticket's (a lean build did it on its branch)
        (d / "scripts").mkdir(exist_ok=True)
        (d / "scripts" / "check_structure.py").write_text("# an old copy\n", encoding="utf-8")
        code, out = run(d, "next", "--phase", "build", "--ticket", "M1-A-01")
        if "differs from the playbook's check" in out and "NOT THIS TICKET'S" not in out:
            fails.append(f"a project-level fix in a build start was not marked as not this ticket's: {out[:300]}")
        if "differs from the playbook's check" not in out:
            fails.append("the start no longer reports a project check copy that differs (the test setup is stale)")
        code, out = run(d, "next", "--phase", "build", "--ticket", "M1-NOPE-09")
        if code == 0 or "no ticket file" not in out:
            fails.append("a start for a ticket with no file was not refused")


def test_tickets_checks(fails: list[str]) -> None:
    """/tickets' own check: a good backlog passes; each claim broken on its own is named - an exact target file (T1),
    a STRUCTURE.md lane (T2), a security DoD line (T3), dependencies that exist (T4), consumed names the code or a
    sibling ticket has (T5, the eleven issues filed against an invented API), every milestone ticketed or explained
    (T6), the plan's lane graph (T7)."""
    import shutil
    ticket = """# [{tid}] {title}

### 🧭 Slice Strategy
- [x] ↕️ Vertical — thin end-to-end increment, demoable on merge

### 🛣️ Lane
{lane}

### 👤 Owner
Senior

### 📁 Target Files
- [ ] `{target}`
- [ ] `app/orders/tests/test_orders.py`
- [ ] `docs/features/orders.md`

### 🔌 Contract — Inputs → Outputs
- **Consumes:** {consumes}
- **Exposes:**
  - (new) `{exposes}(order_id) -> OrderView`

### 🔗 Depends On
{depends}

### 👀 Demo — what works after this merges
A reviewer looks an order up and sees it.

### 🔒 Definition of Done (security included)
- [ ] {dod}
"""
    good = {"M1-ORD-01": dict(title="Look up an order", lane="orders", target="app/orders/service.py",
                              consumes="`OrderQuery` from `app/orders/schemas.py`", exposes="find_order", depends="None",
                              dod="Inputs validated at the boundary; no secrets in source."),
            "M1-ORD-02": dict(title="Show tracking", lane="app/orders", target="app/orders/routes.py",
                              consumes="`find_order` (M1-ORD-01)", exposes="tracking_view", depends="M1-ORD-01",
                              dod="Every call scoped to its tenant.")}
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)

        graph = "# TICKETS\n\n```mermaid\nflowchart LR\n  lane_orders[\"orders · Senior\"]\n```\n"

        def write(tickets=good, plan="## Plan\n- M1 Core slice\n", tickets_md=graph):
            shutil.rmtree(d / "docs", ignore_errors=True)
            (d / "docs/issues").mkdir(parents=True)
            for tid, v in tickets.items():
                (d / f"docs/issues/{tid}_x.md").write_text(ticket.format(tid=tid, **v), encoding="utf-8")
            (d / "PRODUCT.md").write_text(plan, encoding="utf-8")
            (d / "TICKETS.md").write_text(tickets_md, encoding="utf-8")

        (d / "app/orders").mkdir(parents=True)
        (d / "app/orders/schemas.py").write_text("class OrderQuery(BaseModel):\n    order_id: str\n", encoding="utf-8")
        (d / "STRUCTURE.md").write_text("# S\n\n## Modules\n\n| Module | What |\n|---|---|\n| `app/orders` | orders |\n",
                                        encoding="utf-8")
        write()
        if status.tickets_gaps(d):
            fails.append(f"a good backlog should pass /tickets' check: {status.tickets_gaps(d)}")
        edit = lambda tid, **kw: {**good, tid: {**good[tid], **kw}}  # noqa: E731
        breaks = (
            ("T1", dict(tickets=edit("M1-ORD-01", target="app/orders/")), "names no exact target file"),
            ("T2", dict(tickets=edit("M1-ORD-01", lane="billing")), "M1-ORD-01=billing"),
            ("T3", dict(tickets=edit("M1-ORD-02", dod="Tests pass.")), "no security line"),
            ("T4", dict(tickets=edit("M1-ORD-02", depends="M1-ORD-09")), "M1-ORD-02->M1-ORD-09"),
            ("T5", dict(tickets=edit("M1-ORD-02", consumes="`OrderLookupService` (invented)")),
             "M1-ORD-02:OrderLookupService"),
            ("T6", dict(plan="## Plan\n- M1 Core slice\n- M2 Refunds\n"), "milestone M2 has no ticket"),
            ("T7", dict(tickets_md="# TICKETS\n\nno graph\n"), "no Mermaid lane flow graph"),
            ("T17", dict(tickets=edit("M1-ORD-02", depends="None")), "M1-ORD-01+M1-ORD-02:app/orders/tests/test_orders.py"),
            ("T18", dict(tickets_md=graph.replace("lane_orders", "lane_billing")), "box for lane(s) orders"),
        )
        for name, kw, want in breaks:
            write(**kw)
            got = "; ".join(status.tickets_gaps(d))
            if want not in got:
                fails.append(f"{name}: the tickets check should report {want!r}: {got[:240]!r}")
        write(plan="## Plan\n- M1 Core slice\n- M2 Refunds\n",
              tickets_md=graph + "\n## M2 - Refunds\n\nNo tickets: the trial decides.\n")
        if status.tickets_gaps(d):
            fails.append(f"a milestone TICKETS.md explains under its heading needs no ticket: {status.tickets_gaps(d)}")
        write()
        run(d, "init", "--product", "Demo")
        (d / "docs/issues/M1-ORD-01_x.md").write_text(ticket.format(tid="M1-ORD-01", **{**good["M1-ORD-01"],
                                                      "dod": "Tests pass."}), encoding="utf-8")
        code, out = run(d, "set", "tickets", "filled")
        if code == 0 or "#tickets: 1 problem(s), every one at once" not in out or "no security line" not in out:
            fails.append(f"set tickets filled should run the tickets check: {out[:200]}")


def test_plan_a_items(d: Path, fails: list[str]) -> None:
    """A1 the handoff card in the tool's spelling · A3 `quote` prints the receipt line · A5 the third choice beside
    re-run and keep · A6 an over-size section is warned, never refused. Each proven red by its missing output."""
    fresh(d)
    (d / "PRODUCT.md").write_text("## Vision\n" + VISION_OK + "- **Who:** shop owners\n", encoding="utf-8")
    vision_ready(d)
    code, out = run(d, "set", "vision", "filled")
    # /validate is optional (owner, 2026-09-30): the chain goes /vision -> /scope
    if code != 0 or f"Open a NEW conversation and type: {status.skill_command('scope')}" not in out:
        fails.append(f"A1: set vision filled should end with the next command to type (/scope): {out!r}")
    st_ = status.Status.load(d / "STATUS.md")
    st_.base = d
    if status.next_phase(st_)["phase"] != "scope":
        fails.append(f"after /vision the next phase should be /scope, not optional /validate: "
                     f"{status.next_phase(st_)['phase']!r}")
    (d / "PRODUCT.md").write_text((d / "PRODUCT.md").read_text(encoding="utf-8") + "\n## Scope\n- **Core:** x\n",
                                  encoding="utf-8")
    run(d, "set", "scope", "filled")
    st_ = status.Status.load(d / "STATUS.md")
    st_.base = d
    if any("#validate is empty" in x for x in status.next_phase(st_)["notes"]):
        fails.append("an empty optional /validate should never be reported as out of order")
    if status.skill_command("validate") not in ("/validate", "/product-playbook:validate"):
        fails.append(f"A1: a clone is a plugin route, spelled /<plugin>:<phase>: {status.skill_command('validate')!r}")
    (d / "notes.md").write_text("# Notes\n- The refund limit is 50 euros per order, set by the owner.\n",
                                encoding="utf-8")
    code, out = run(d, "quote", "notes.md", "refund limit is 50  euros")
    want = f'  - notes.md · {TODAY} · "The refund limit is 50 euros per order, set by the owner."'
    if code != 0 or out.strip("\n") != want:
        fails.append(f"A3: quote should print the whole line as a receipt: {out!r}")
    for words, why in (("refund limit is 90 euros", "words not in the file"), ("refund", "too few words")):
        code, out = run(d, "quote", "notes.md", words)
        if code == 0:
            fails.append(f"A3: quote should refuse {why}: {out!r}")
    (d / "PRODUCT.md").write_text("## Vision\n- The refund limit is 50 euros per order, set by the owner.\n",
                                  encoding="utf-8")
    code, out = run(d, "quote", "notes.md", "refund limit is 50 euros")
    if code == 0 or "already holds" not in out:
        fails.append(f"A3: a quote PRODUCT.md already holds would be refused as copied - quote should say so: {out!r}")
    st = status.Status.load(d / "STATUS.md")
    st.base = d
    notes = " ".join(status.next_phase(st, "vision")["notes"])
    if "update one decision" not in notes:
        fails.append(f"A5: a re-run should offer to update one decision: {notes[:300]!r}")
    body = "## Architecture\n" + ("- **Stack:** " + "x" * 200 + "\n") * 45
    if not status.big_sections(body) or "move the reasoning" not in status.big_sections(body)[0]:
        fails.append("A6: a section over the limit should be warned with where the reasoning goes")
    if status.big_sections("## Architecture\n" + ("- **Stack:** " + "x" * 200 + "\n") * 30):
        fails.append("A6: a section under the limit should not be warned")
    for f in ("PRODUCT.md", "notes.md"):
        (d / f).unlink(missing_ok=True)


def test_playbook_receipts(d: Path, fails: list[str]) -> None:
    """RR1 (owner's choice): a Read receipt may quote a playbook file the phase opened - the plugin-root agent.md,
    a skill's own reference - and the quote is checked there; a wrong quote or an unknown file is still refused."""
    fresh(d)
    agent_line = next(l.strip() for l in (ROOT / "references" / "agent.md").read_text(encoding="utf-8").splitlines()
                      if len(l.strip()) > 40 and '"' not in l)
    shape_line = next(l.strip() for l in (ROOT / "commands" / "structure" / "references" / "choosing-the-shape.md")
                      .read_text(encoding="utf-8").splitlines() if len(l.strip()) > 40 and '"' not in l)
    for name, quote, ok in (("references/agent.md", agent_line, True),
                            ("references/choosing-the-shape.md", shape_line, True),
                            ("references/agent.md", "a sentence the playbook never wrote anywhere at all", False),
                            ("references/no-such-file.md", agent_line, False)):
        (d / "PRODUCT.md").write_text(f"## Structure\n- **Shape:** modules\n- **Read (file · date · verbatim "
                                      f"quote):** {name} (2026-09-26) — \"{quote}\"\n", encoding="utf-8")
        code, out = run(d, "check", "--product", "PRODUCT.md")
        if ok and "Read receipt" in out:
            fails.append(f"a true quote from the playbook file {name} was refused: {out.strip()[:200]}")
        if not ok and "Read receipt" not in out:
            fails.append(f"a false receipt ({name}, {quote[:30]!r}) was accepted: {out.strip()[:200]}")
    (d / "PRODUCT.md").unlink()


def test_receipts_and_latex(d: Path, fails: list[str]) -> None:
    """A Read quote must be in the file it names and once in PRODUCT.md (a copied receipt fails); LaTeX warns."""
    fresh(d)
    run(d, "set", "vision", "filled")
    (d / "docs").mkdir(exist_ok=True)
    (d / "docs" / "vision.md").write_text("# Vision\n\nOwners answer the same five questions every evening.\n",
                                          encoding="utf-8")
    good = ("## Vision\n- **Vision:** a calm inbox\n"
            "- **Read (file · date · verbatim quote):** docs/vision.md (2026-09-25) — "
            "\"Owners answer the same five questions every evening.\"\n")
    (d / "PRODUCT.md").write_text(good, encoding="utf-8")
    code, out = run(d, "check", "--product", "PRODUCT.md")
    if "Read receipt" in out:
        fails.append(f"a receipt quoting its file once was refused: {out.strip()}")
    copied = good + ("\n## Scope\n- **Core:** x\n- **Read (file · date · verbatim quote):** docs/vision.md "
                     "(2026-09-25) — \"Owners answer the same five questions every evening.\"\n")
    (d / "PRODUCT.md").write_text(copied, encoding="utf-8")
    code, out = run(d, "check", "--product", "PRODUCT.md")
    if code == 0 or "appears 2 times" not in out:
        fails.append(f"a receipt copied from an earlier one was accepted: {out.strip()}")
    code, out = run(d, "set", "scope", "filled")
    if code == 0:
        fails.append("set scope filled accepted a #Scope whose receipt was copied - the phase must fix it first")
    fresh(d)
    vision_ready(d, "\nOwners answer the same five questions every evening.\n")
    (d / "PRODUCT.md").write_text("## Vision\n" + VISION_OK + "- **Detail:** `docs/vision.md` (reasoning)\n"
                                  + good.split("\n", 2)[2], encoding="utf-8")
    code, out = run(d, "set", "vision", "filled")
    if code != 0 or "size: #Vision" not in out or "docs/vision.md" not in out or "Read quotes checked: 1" not in out:
        fails.append(f"set filled should print the size line and the quotes it checked: {out.strip()}")
    (d / "PRODUCT.md").write_text(good.replace("same five questions", "same six questions"), encoding="utf-8")
    code, out = run(d, "check", "--product", "PRODUCT.md")
    if code == 0 or "is not in docs/vision.md" not in out:
        fails.append(f"a quote that is not in its file was accepted: {out.strip()}")
    (d / "PRODUCT.md").write_text(good + "- **Note:** refunds $\\le$ 30 and a bar of $\\ge 3/8$; price $29–$79/mo\n",
                                  encoding="utf-8")
    code, out = run(d, "check", "--product", "PRODUCT.md")
    if "LaTeX" not in out:
        fails.append(f"LaTeX math in PRODUCT.md was not warned about: {out.strip()}")
    (d / "PRODUCT.md").write_text(good + "- **Price:** $29–$79/mo, up to €30\n", encoding="utf-8")
    code, out = run(d, "check", "--product", "PRODUCT.md")
    if "LaTeX" in out:
        fails.append(f"plain prices were mistaken for LaTeX: {out.strip()}")


def test_agent_trial_fixes(d: Path, fails: list[str]) -> None:
    """Fixes from the logged agent test (4 tools, one product): a readable header, plain notes, no UI flag at
    init, and `next` naming the playbook copy it belongs to."""
    fresh(d)
    text = (d / "STATUS.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    for key in ("Order:",):  # Next is computed by next/show, never stored (format 2)
        i = next((n for n, x in enumerate(lines) if x.startswith(key)), None)
        if i is None or lines[i - 1].strip():
            fails.append(f"header line {key!r} follows another line directly - a Markdown viewer joins them")
    if status.Status.parse(text).header["Order"] != "chain order":
        fails.append("the blank-line header does not parse back")
    for bad in ("bar >=3/8", "refunds <= 30", "2026-09-28..10-11", "x => y", "a != b"):
        code, _ = run(d, "set", "validate", "running", "--due", "2026-10-01", "--reason", bad)
        if code == 0:
            fails.append(f"a note with an operator was accepted: {bad!r}")
            fresh(d)
    code, out = run(d, "set", "validate", "running", "--due", "2026-10-01", "--reason",
                    "8 owners, 2-week trial · pass: at least 3 of 8 allow unchecked replies, 2 of 8 refunds up to 30")
    if code != 0:
        fails.append(f"a plain note was refused: {out.strip()}")
    (d / "STATUS.md").unlink()  # so a refusal can only be about --ui
    code, _ = run(d, "init", "--product", "X", "--ui", "yes")
    fresh(d)
    if code == 0:
        fails.append("init accepted --ui - /vision cannot know whether there is a screen")
    (d / "STATUS.md").unlink()  # a brand-new project: the first run is where two copies get mixed
    code, out = run(d, "next")
    first = out.splitlines()[0] if out else ""
    if not first.startswith("Playbook ") or "rule files in" not in first or "unknown" in first:
        fails.append(f"next does not name the playbook copy first: {first!r}")
    elif not (Path(first.split("rule files in ", 1)[1]) / "PRINCIPLES.md").is_file():
        fails.append(f"next names a folder without the rule files in it: {first!r}")


def test_vision_close(d: Path, fails: list[str]) -> None:
    """P4 for /vision: `set vision filled` refuses the countable gaps, all in one list; a new project starts from
    `next` with no STATUS.md - one command that prints its rules - and one `set` makes PRODUCT.md, STATUS.md, the AI
    flags and the README receipt; the rest of the close prints as a short checklist."""
    fresh(d)
    (d / "STATUS.md").unlink()
    (d / "README.md").write_text("# Demo\n\nA waitlist for small restaurants.\n", encoding="utf-8")
    with tempfile.TemporaryDirectory() as empty:  # d holds earlier tests' code: a fresh start is an empty folder
        (Path(empty) / "README.md").write_text("# Demo\n", encoding="utf-8")
        code, out = run(Path(empty), "next", "--phase", "vision")
    if code != 0 or "### target - " not in out or "Fresh start" not in out \
            or "===== PRINCIPLES.md =====" not in out or "--product" not in out:
        fails.append(f"next --phase vision on a new project should start it with its rules, not refuse: {out[-300:]!r}")
    if "## §Re-run semantics" in out or "## §Declined runs" in out or "## §Spine resolution" in out:
        fails.append("a new project's start should leave out re-run, declined and spine-resolution rules")
    if "vision-research.md" not in out or "Research helper" not in out:
        fails.append(f"the start should name the research helper and its brief: {out[-400:]!r}")
    # some tools cut long output at the top (a logged Antigravity run never saw the helper line): it ends the start too
    real_tool = status.playbook_tool
    start_file = Path(status.__file__).resolve().parent / status.START_FILE
    try:
        status.playbook_tool = lambda: "antigravity"
        short = status.fit_start(status.vision_start_text(new=True) + "\n" + status.phase_rules_text("vision"))
        written = start_file.read_text(encoding="utf-8") if start_file.is_file() else ""
        if len(short.encode("utf-8")) > 3500 or "view_file" not in short or "### target - " not in written:
            fails.append(f"Antigravity's start should fit its ~4 KB window and point at a file holding the full start "
                         f"(the field labels): {len(short)} chars, file has labels: {'### target - ' in written}")
        # /scope's start is ~12 KB and /plan's ~14 KB: the same cut, the same file (next.64)
        for phase in ("scope", "plan"):
            big = f"/{phase} start\n- **{phase} label:**\n" + "y" * 12000
            short = status.fit_start(big, phase)
            pf = start_file.parent / f"{phase}-start.md"
            written = pf.read_text(encoding="utf-8") if pf.is_file() else ""
            pf.unlink(missing_ok=True)
            if len(short.encode("utf-8")) > 1200 or "view_file" not in short or f"{phase}-start.md" not in short \
                    or f"- **{phase} label:**" not in written or "y" * 12000 not in written:
                fails.append(f"Antigravity's /{phase} start should be a short pointer to a file holding it whole: "
                             f"{len(short)} chars, file has it: {big in written}")
        status.playbook_tool = lambda: "claude"
        if status.fit_start("x" * 9000) != "x" * 9000 or status.fit_start("x" * 9000, "plan") != "x" * 9000:
            fails.append("other tools' starts should be printed whole, unchanged")
        # Codex drops a helper result that arrives after its turn ended, then queues the user's messages forever:
        # spawn and wait in ONE turn, after round 1 - and only Codex is told so
        status.playbook_tool = lambda: "codex"
        cx = status.vision_helper_line()
        status.playbook_tool = lambda: "cursor"
        cu = status.vision_helper_line()
        if "NOT in your first reply" not in cx or "wait_agent" not in cx or "NOT in your first reply" in cu \
                or "your FIRST tool call, before you write round 1" not in cu:
            fails.append(f"Codex's helper starts after round 1 and waits in that turn; other tools start it at once: "
                         f"{cx[:160]!r} / {cu[:120]!r}")
        status.playbook_tool = lambda: "antigravity"
        tail = status.vision_last()
        status.playbook_tool = lambda: "cursor"
        other = status.vision_last()
    finally:
        status.playbook_tool = real_tool
        start_file.unlink(missing_ok=True)
    if "Playbook " not in tail or "invoke_subagent" not in tail or "vision-research" not in tail or other:
        fails.append(f"only Antigravity's start should end with the version line and the helper step (with its "
                     f"no-subagent fallback): {tail[-300:]!r} / other tool: {other!r}")
    code, out = run(d, "next", "--phase", "scope")
    if code == 0:
        fails.append("next --phase scope with no STATUS.md should still be refused")
    code, out = run(d, "rules", "vision")
    if code != 0 or "## Communication" not in out or "§Plain-language close" in out:
        fails.append(f"rules vision should print the start's sections only: {out[:200]!r}")
    src = d.parent / f"{d.name}-vision-section.md"  # outside the project, as the close's step 1 says

    def close(body: str, *extra: str) -> tuple[int, str]:
        src.write_text(body, encoding="utf-8")
        return run(d, "set", "vision", "filled", "--section-from", str(src), *extra)

    # a new project: ONE `set` makes PRODUCT.md and STATUS.md, records the AI answer, fills the README receipt
    (d / "docs").mkdir(exist_ok=True)
    doc = d / "docs" / "vision.md"
    doc.write_text(VISION_DOC, encoding="utf-8")
    read_line = "- **Read (file · date · verbatim quote):**\n"
    code, out = close(VISION_OK + read_line)
    if code == 0 or "--product" not in out or (d / "STATUS.md").exists():
        fails.append(f"set vision with no STATUS.md and no --product should name --product: {out.strip()[:200]!r}")
    code, out = close(VISION_OK.replace("- **Business model:** paid", "- **Business model:**") + read_line,
                      "--product", "Demo", "--ai", "no")
    if code == 0 or (d / "STATUS.md").exists() or (d / "PRODUCT.md").exists():
        fails.append("a refused first `set vision` must leave no STATUS.md or PRODUCT.md behind")
    code, out = close(VISION_OK + read_line, "--product", "Demo", "--ai", "yes", "--agent", "no")
    if code == 0 or "the AI line" not in out:
        fails.append(f"--ai yes on `set` should hold the section to the AI line: {out.strip()[:200]!r}")
    code, out = close(VISION_OK + read_line, "--product", "Demo", "--ai", "no")
    st_text = (d / "STATUS.md").read_text(encoding="utf-8") if (d / "STATUS.md").exists() else ""
    prod = (d / "PRODUCT.md").read_text(encoding="utf-8") if (d / "PRODUCT.md").exists() else ""
    if code != 0 or "AI product: no" not in st_text or "Demo" not in st_text:
        fails.append(f"set vision --product --ai should make STATUS.md with the AI answer: {out.strip()[:300]!r}")
    if f'README.md · {TODAY} · "A waitlist for small restaurants."' not in prod:
        fails.append("set vision should fill the empty Read: line from README.md")
    if "The rest of the close" not in out or "## §Plain-language close" in out or "not saved:" not in out \
            or "README.md says 'A waitlist for small restaurants.'" not in out:
        fails.append(f"set vision should print the short close checklist and the save/3c facts: {out.strip()[-500:]!r}")
    code, out = run(d, "section", "PRODUCT.md", "# Vision")
    if code != 0 or "nobody waits" not in out:
        fails.append(f"section PRODUCT.md \"# Vision\" should print the section: {out[:200]!r}")
    code, out = run(d, "rules", "vision", "--close")
    if "## §Plain-language close" not in out:
        fails.append("rules vision --close should still print the close's rules in full, on request")
    doc.write_text(VISION_DOC.replace("- same job ·", "- other ·").replace("Waitwhile", "a list app"), encoding="utf-8")
    code, out = run(d, "check", "--product", "PRODUCT.md")
    if "#vision's check" not in out or "same job" not in out:
        fails.append(f"check --product should run the filled /vision's own check: {out[-300:]!r}")
    (d / "README.md").unlink()

    fresh(d)
    vision_ready(d)
    no_link = VISION_DOC.replace(" · https://example.org/a1", "")
    for body, text, want in (
            (VISION_OK.replace("- **Business model:** paid", "- **Business model:**"), VISION_DOC,
             "#Vision field empty: the business model"),
            (VISION_OK.replace("- **Constraints:** a guest's phone number is personal data (GDPR) · English · the "
                               "restaurant's own list", "- **Constraints:**"), VISION_DOC,
             "#Vision field empty: the constraints line - the line `- **Constraints"),
            (VISION_OK.replace("40 restaurants by 2027-03-31", "more restaurants"), VISION_DOC, "a number and a date"),
            (VISION_OK.replace("40 restaurants by 2027-03-31", "restaurants by 2027-03-31"), VISION_DOC,
             "a number and a date"),
            (VISION_OK.replace("40 restaurants by 2027-03-31", "40 restaurants soon"), VISION_DOC, "a number and a date"),
            (VISION_OK, None, "no docs/vision.md"),
            (VISION_OK, VISION_DOC.replace("why now · ", ""), "why now has no search line"),
            (VISION_OK, VISION_DOC.replace(VISION_SEARCHES, "### A.2 Search list\n\n"), "lists no search"),
            (VISION_OK, VISION_DOC.replace("- local ·", "- market ·"), "no `local ·` search line"),
            (VISION_OK, VISION_DOC.replace("https://example.org/local", "https://vertexaisearch.cloud.google.com/"
                                           "grounding-api-redirect/AUZIYQE2pl"), "links a search redirect"),
            (VISION_OK, VISION_DOC.replace("https://example.org/rules", "https://eur-lex.europa.eu"),
             "cites a site's homepage for a fact"),
            (VISION_OK, no_link, "search line has no source link"),
            (VISION_OK, VISION_DOC.replace("- same job ·", "- market ·").replace("Waitwhile", "a list app"),
             "no `same job ·` search line"),
            (VISION_OK, VISION_DOC.replace("- rules ·", "- users ·").replace("GDPR", "").replace("personal data",
                                                                                                   "common"),
             "no `rules ·` search line"),
            (VISION_OK, VISION_DOC.replace("### A.1 Owner's answers", "### A.1 Notes"), "no `## Owner's answers`"),
            # 2.2 (#60, #61): the layout is countable - a heading without its number, no diagram, no In/Out of scope
            (VISION_OK, VISION_DOC.replace("## 5. Who it is for", "## Who it is for"), "heading(s) without a number"),
            (VISION_OK, VISION_DOC.replace("### A.1 Owner's", "### Owner's"), "heading(s) without a number"),
            (VISION_OK, VISION_DOC.replace("```mermaid", "```text"), "lacks a ```mermaid diagram"),
            (VISION_OK, VISION_DOC.replace("- **Out of scope:** bookings\n", ""), "an `Out of scope` list"),
            (VISION_OK, VISION_DOC.replace("## 4. Open questions", "## 4. Next steps"), "an `Open questions` section"),
            # #59 fix A: a brief the user gave is answered point by point
            (VISION_OK, VISION_DOC.replace("1. A waitlist for small restaurants.", "1. Brief: the challenge text."),
             "Brief point | Our answer"),
            (VISION_OK, VISION_DOC.replace("1. A waitlist for small restaurants.", "1. Brief: the challenge text.")
             .replace("## 4. Open questions", "## 7. Your brief, answered\n\n| Brief point | Our answer |\n|---|---|\n"
                      "| Who is it for? | small restaurants |\n| Why now? | |\n\n## 4. Open questions"),
             "an answer for the brief point 'Why now?'"),
            (VISION_OK, VISION_DOC.replace("| Term | Number | From |\n|---|---|---|", "| Term | Number |\n|---|---|")
             .replace(" | owner |", " |"), "no `From` column"),
            (VISION_OK, VISION_DOC.replace("| owner |", "| guess |"), "From is 'guess'"),
            (VISION_OK, VISION_DOC.split("### A.3 North-star")[0], "no north-star terms table"),
            (VISION_OK, VISION_DOC + "| active | TBD | owner |\n", "'active' has no definition"),
            (VISION_OK.replace("Mia's party of 4 joins the list at 19:05 and gets a text at 19:32",
                               "a guest joins the list and gets a text"), VISION_DOC, "worked example has no numbers"),
            (VISION_OK.replace("- **Worked example:**", "- **Example:**"), VISION_DOC,
             "#Vision field empty: the worked example"),
            ("Vision: nobody waits\nWho it's for: small restaurants\n", VISION_DOC, "no fields found"),
            (VISION_OK + "\n## Pricing\n- **Price:** 10 euro\n", VISION_DOC, "starts a new PRODUCT.md section"),
            (VISION_OK, VISION_DOC + "\nat least $\\ge 20$ a week\n", "has LaTeX")):
        if text is None:
            doc.unlink()
        else:
            doc.write_text(text, encoding="utf-8")
        code, out = close(body)
        if code == 0 or want not in out:
            fails.append(f"set vision filled should refuse with {want!r}: {out.strip()[:300]!r}")
        if want == "no fields found" and "field empty" in out:
            fails.append("no parsed field at all should be ONE line, not an empty-field line per field (P20)")
        if (d / "PRODUCT.md").exists():
            fails.append("a refused /vision close left behind the PRODUCT.md it made")
    # no market named is an honest local line, not a gap (the playbook serves any product, any country)
    doc.write_text(VISION_DOC.replace("`wachtlijst restaurant app Gent` · two local apps",
                                      "no market named · searched worldwide"), encoding="utf-8")
    code, out = close(VISION_OK)
    if code != 0 or "`local ·`" in out:
        fails.append(f"`local · no market named` should count as the local search line: {out.strip()[:300]!r}")
    (d / "PRODUCT.md").unlink(missing_ok=True)
    # a heading that mentions searches is not the search list (a logged Antigravity run's "## Problem (Then How It
    # Happens, From the Searches)" had its numbered causes refused as search lines without links); and a long
    # `·`-separated line is wrapped, not warned about (its Constraints line made it re-run `set` three times)
    doc.write_text(VISION_DOC.replace("## 5. Who it is for", "## 7. Problem (Then How It Happens, From the Searches)"
                                      "\n\n1. **Social security:** a fixed share of gross.\n2. **Tax:** brackets change "
                                      "in January.\n\n## 5. Who it is for"), encoding="utf-8")
    long_c = ("- **Constraints:** " + " · ".join(f"rule number {i} that applies to guest phone numbers here"
                                                for i in range(7)))
    code, out = close(VISION_OK.replace("- **Constraints:** a guest's phone number is personal data (GDPR) · English · "
                                        "the restaurant's own list", long_c))
    if code != 0 or "source link" in out or "a line of" in out:
        fails.append(f"a heading naming searches is not the search list, and a long `·` line is wrapped without a "
                     f"warning: {out.strip()[:400]!r}")
    elif any(len(l) > 300 for l in (d / "PRODUCT.md").read_text(encoding="utf-8").splitlines()):
        fails.append("a long `·`-separated field should be wrapped under 300 characters")
    (d / "PRODUCT.md").unlink(missing_ok=True)
    doc.write_text(VISION_DOC.replace("why now · ", ""), encoding="utf-8")
    code, out = close(VISION_OK.replace("walk-ins leave", "walk-ins leave; why now: the owner’s claim, not verified"))
    if code != 0:
        fails.append(f"a why now marked as the owner's claim (curly apostrophe) should close without a search line: "
                     f"{out.strip()[:300]!r}")
    # P8: the shapes two logged runs wrote - no "- " before the labels (Cursor, Codex) and a `# Vision` heading
    # (Codex) - record first time, written back in the one shape the spine uses
    fresh(d)
    vision_ready(d)
    bare = "# Vision\n\n" + re.sub(r"(?m)^- (\*\*)", r"\1", VISION_OK)
    code, out = close(bare)
    prod = (d / "PRODUCT.md").read_text(encoding="utf-8") if (d / "PRODUCT.md").exists() else ""
    if code != 0 or "- **Vision:** nobody waits" not in prod or "# Vision\n" in prod.split("## Vision", 1)[-1]:
        fails.append(f"labels without '- ' and a `# Vision` heading should record, bullets added, heading dropped: "
                     f"{out.strip()[:300]!r}")
    fresh(d)
    vision_ready(d)
    # P18: the skill's own examples, read from its text, and a logged owner's payroll terms, written exactly as
    # told, pass the check that judges them (the first digit-only rule refused "Monday to Sunday" and "zero changes");
    # so do a search that found nothing, a comparable pointing at its search, and a metric with no bar
    skill = (ROOT / "commands" / "vision" / "SKILL.md").read_text(encoding="utf-8")
    pairs = [(" ".join(t.split()), " ".join(n.split())) for t, n in re.findall(r'"([^"]+)" = "([^"]+)"', skill)]
    target = re.search(r'"(40 restaurants[^"]+)"', skill)
    if len(pairs) < 2 or not target:
        fails.append(f"P18: the skill's term examples or its target example moved: {pairs} {target}")
    payroll = [("Pay-change question", "A customer question asking why an employee's net pay differs between two "
                "months"), ("Approved without edits", "Consultant approves the draft with zero changes to text or "
                "figures"), ("Pilot team", "One Belgian SME payroll team of 5-10 consultants"),
               ("Drafts approved without edits", "bar: not set")]
    doc.write_text(VISION_LAYOUT + "## Appendix A — Workings\n\n### A.1 Owner's answers\n\n1. A waitlist.\n\n"
                   + VISION_SEARCHES.rstrip("\n") +
                   "\n- `restaurant waitlist complaints` · nothing found\n- Waitwhile · search 2\n"
                   "- Not searched · Yelp Guest Manager · the owner uses it today\n\n"
                   "### A.3 North-star terms\n| Term | Number | From |\n|---|---|---|\n" +
                   "".join(f"| {t} | {n} | proposed |\n" for t, n in pairs + payroll), encoding="utf-8")
    code, out = close(VISION_OK.replace("40 restaurants by 2027-03-31", target.group(1) if target else ""))
    if code != 0:
        fails.append(f"P18: the skill's own examples and exact definitions without a digit must pass: "
                     f"{out.strip()[:400]!r}")
    # an AI product answers the AI line; a product with no AI does not (the review's AI questions, 2026-09-30)
    fresh(d)
    vision_ready(d)
    run(d, "flag", "--ai", "yes", "--agent", "no")
    for line, ok in (("", False), ("- **AI (what it does):** n/a\n", False),
                     ("- **AI (what it does):** it drafts the reply; the consultant approves · figures 100% exact · "
                      "under 0.10 euro per answer\n", True)):
        code, out = close(VISION_OK + line)
        if (code == 0) != ok or (not ok and "the AI line" not in out):
            fails.append(f"an AI product {'with' if ok else 'without'} its AI line: {out.strip()[:300]!r}")
        if ok:
            break
    fresh(d)
    vision_ready(d)
    code, out = close(VISION_OK.replace("- **First users:**", "- **Channels:**"))
    if code == 0 or "#Vision field empty: the first users" not in out:
        fails.append(f"a #Vision without its first users should be refused: {out.strip()[:300]!r}")
    code, out = run(d, "set", "vision", "declined", "--reason", "stopped after the first verdict: not now",
                    "--gate", "vision")
    if code != 0 or "stopped after the first verdict" not in (d / "STATUS.md").read_text(encoding="utf-8"):
        fails.append(f"a stop after the first verdict should record as declined, as `next` says: {out.strip()!r}")
    fresh(d)
    (d / "docs" / "vision.md").write_text(VISION_DOC.split("### A.3 North-star")[0], encoding="utf-8")
    code, out = close(VISION_OK.replace("- **Riskiest assumption:** guests answer a text", "- **Riskiest assumption:**"))
    if code == 0 or not all(w in out for w in ("the riskiest assumption", "no north-star terms table", "AI answer")):
        fails.append(f"one refusal should name every problem: {out.strip()[:400]!r}")
    code, out = close("- **Vision:** inferred from the code\n", "--note", "adopted 2026-09-30")
    if code != 0 or "The rest of the close" in out:
        fails.append(f"/adopt's inferred record is not held to /vision's close: {out.strip()[:300]!r}")
    fresh(d)
    vision_ready(d)
    code, out = close(VISION_OK)
    if code != 0 or "made from the playbook's template" not in out or "The rest of the close" not in out \
            or "nobody waits" not in (d / "PRODUCT.md").read_text(encoding="utf-8"):
        fails.append(f"a complete /vision should close into a new PRODUCT.md and print the close's checklist: "
                     f"{out.strip()[:300]!r}")
    (d / "docs" / "vision.md").unlink()
    if status.phase_check("vision", d) is not None:
        fails.append("a filled /vision must not block later phases through the earlier-phase re-check")
    src.unlink()


def test_long_lines_warned(d: Path, fails: list[str]) -> None:
    """PRINCIPLES.md 'Readable documents': a phase closing on a 400-character PRODUCT.md line is told to split it;
    table rows and a short field are not."""
    fresh(d)
    long_field = "- **Value proposition:** " + "word " * 80
    table_row = "| " + " | ".join(["cell text"] * 40) + " |"
    body = ["# PRODUCT", "", "## Vision", VISION_OK, long_field, table_row, "- **Who:** shops", "", "## Validation", ""]
    (d / "PRODUCT.md").write_text("\n".join(body), encoding="utf-8")
    vision_ready(d)
    code, out = run(d, "set", "vision", "filled")
    if code != 0 or "split it" not in out or "Value proposition" not in out:
        fails.append(f"a 400-character field did not get a split-it warning: {out.strip()[:160]!r}")
    if out.count("split it") != 1:
        fails.append(f"the warning fired on a table row or a short field: {out.count('split it')} warnings")
    code, out = run(d, "check", "--product", "PRODUCT.md")
    if "split it" not in out:
        fails.append("check --product does not warn on the long PRODUCT.md line")
    (d / "PRODUCT.md").unlink()


def test_sections_and_phase_rules(d: Path, fails: list[str]) -> None:
    """L1-L3: `section` prints named sections word for word (a heading inside a code fence is text, not a section;
    --own stops at the first sub-heading; an unknown name is refused with the list). `next --phase` prints the
    phase's rule sections, and every PRINCIPLES.md / MECHANISMS.md section its skill cites is among them - a
    cited rule the output leaves out is a rule the run never sees."""
    doc = ["# Title", "intro line", "", "## §Alpha — first", "alpha body", "```md", "## Not a heading", "```",
           "### Alpha child", "child body", "## 2. Beta <!-- note -->", "beta body"]
    (d / "doc.md").write_text("\n".join(doc) + "\n", encoding="utf-8")
    code, out = run(d, "section", "doc.md", "alpha")
    if code != 0 or out.rstrip("\n") != "\n".join(doc[3:10]):
        fails.append(f"section alpha is not lines 4-10 word for word (fence kept, child kept): {out!r}")
    code, out = run(d, "section", "doc.md", "--own", "Alpha")
    if "child body" in out or "## Not a heading" not in out:
        fails.append(f"--own should stop at the first real sub-heading, not a fenced line: {out!r}")
    code, out = run(d, "section", "doc.md", "intro", "beta")
    if code != 0 or out.rstrip("\n") != "# Title\nintro line\n\n## 2. Beta <!-- note -->\nbeta body":
        fails.append(f"intro + a numbered heading with a comment did not print word for word: {out!r}")
    # a step file says to ask for a step by its number ("6."); the key drops numbers, so this was refused
    for name in ("2.", "§2.", "2"):
        code, out = run(d, "section", "doc.md", name)
        if code != 0 or out.rstrip("\n") != "## 2. Beta <!-- note -->\nbeta body":
            fails.append(f"section {name!r} should print the heading numbered 2: {out!r}")
    code, out = run(d, "section", "doc.md", "gamma")
    if code == 0 or "Its sections: intro; # title; ## alpha — first" not in out:
        fails.append(f"an unknown section should be refused with the list of sections: {out!r}")
    code, out = run(d, "section", "doc.md", "--headings")
    if out.splitlines() != ["# Title", "## §Alpha — first", "### Alpha child", "## 2. Beta <!-- note -->"]:
        fails.append(f"--headings should list every heading line outside a fence: {out!r}")
    (d / "doc.md").unlink()
    fresh(d)
    for phase, files in status.PHASE_RULES.items():
        code, out = run(d, "next", "--phase", phase)
        # /vision's start prints its rules itself (one start command); the others point at them
        if f"status.py rules {phase}" not in out and "===== PRINCIPLES.md =====" not in out:
            fails.append(f"next --phase {phase} neither prints its rules nor points at `status.py rules {phase}`")
        code, out = run(d, "rules", phase)
        for name, secs in files.items():
            if f"===== {name} =====" not in out:
                fails.append(f"next --phase {phase} does not print its {name} sections")
            text = status.rule_file(name).read_text(encoding="utf-8")
            for s in secs:
                body = status.print_sections(status.rule_file(name), [s])
                if body not in out or body not in text:
                    fails.append(f"next --phase {phase}: {name} §{s} is not printed word for word")
        late = status.PHASE_CLOSE_RULES.get(phase, {})
        if late:  # the close's sections, printed when `set <phase> filled` passes, word for word too
            code, close_out = run(d, "rules", phase, "--close")
            for name, secs in late.items():
                for s in secs:
                    if status.print_sections(status.rule_file(name), [s]) not in close_out:
                        fails.append(f"rules {phase} --close: {name} §{s} is not printed word for word")
        skill = (ROOT / "commands" / phase / "SKILL.md").read_text(encoding="utf-8")
        for m in re.finditer(r"`(MECHANISMS|PRINCIPLES)\.md` §([\w-]+(?: [\w-]+)*)", skill):
            name, cited = f"{m.group(1)}.md", status.heading_key(m.group(2))
            # a § names a heading, or a bolded rule inside a printed section (§Secrets never get pushed)
            if not any(cited.startswith(status.heading_key(s)) for s in files.get(name, []) + late.get(name, [])) and \
                    f"**{m.group(2).lower()}**" not in out.lower():
                fails.append(f"/{phase} cites {name} §{m.group(2)} but `status.py rules {phase}` does not print it")
    for phase, want in (("contracts", True), ("build", True), ("vision", False), ("scope", False)):
        code, out = run(d, "next", "--phase", phase)
        if ("## §Context hygiene" in out) != want:  # the section itself; a printed rule may name it
            fails.append(f"next --phase {phase} should {'' if want else 'not '}print §Context hygiene")
    # the agent-instructions file: the old read-everything block is named, the template's new one is not
    (d / "PRODUCT.md").write_text("## Vision\n" + "x" * 3000 + "\n", encoding="utf-8")
    (d / "CLAUDE.md").write_text("# Agent instructions\n\n## Read before you touch anything\n\n1. PRODUCT.md\n",
                                 encoding="utf-8")
    code, out = run(d, "next")
    if "CLAUDE.md tells every conversation to read" not in out:
        fails.append(f"next should name a CLAUDE.md that orders whole-file reads: {out.strip()[-200:]}")
    (d / "CLAUDE.md").write_text((ROOT / "templates" / "AGENTS.md").read_text(encoding="utf-8"), encoding="utf-8")
    code, out = run(d, "next")
    if "tells every conversation to read" in out or "Never open their source" not in out:
        fails.append(f"the template's own block was flagged, or the reading lines are missing: {out.strip()[-200:]}")
    (d / "CLAUDE.md").unlink()
    (d / "PRODUCT.md").unlink()
    # a phase with no list (/learn had none until the v2 alignment; a name no phase uses stays listless)
    code, out = run(d, "rules", "no-such-phase")
    if code == 0 or "open PRINCIPLES.md and MECHANISMS.md whole" not in out:
        fails.append(f"rules for a phase with no list should be refused, telling it to open the files: {out!r}")


def test_route(fails: list[str]) -> None:
    """/playbook's start (`status.py route`). Seven logged /playbook runs started in a folder with no STATUS.md, where
    `next` printed a phase-close checklist and refused, so every run fell back to `ls`. `route` answers there, and
    each `status.py` command and each `route` line the skill names is run here exactly as the skill writes it (P18)."""
    import shutil
    skill = (ROOT / "commands" / "playbook" / "SKILL.md").read_text(encoding="utf-8")
    seen: list[str] = []

    def route(d: Path, want: list[str], unwanted: list[str] = ()) -> str:
        code, out = run(d, "route")
        seen.append(out)
        if code != 0:
            fails.append(f"route exited {code} in {sorted(p.name for p in d.iterdir())}: {out.strip()[-200:]}")
        for w in want:
            if w not in out:
                fails.append(f"route in {sorted(p.name for p in d.iterdir())} should print {w!r}: {out[:400]!r}")
        for w in (*unwanted, "This phase closes with", "REFUSED"):
            if w in out:
                fails.append(f"route in {sorted(p.name for p in d.iterdir())} should not print {w!r}")
        return out

    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        for name in ("README.md", ".gitignore"):
            (d / name).write_text("x\n", encoding="utf-8")
        route(d, ["Where: a fresh start", "Next: /vision", "Size: short", "Map: show it"], ["Batch:"])
        if sorted(p.name for p in d.iterdir()) != [".gitignore", "README.md"]:
            fails.append("route wrote a file in a fresh folder - it only reads")
        (d / "src").mkdir()
        (d / "src" / "app.py").write_text("print(1)\n", encoding="utf-8")
        route(d, ["Where: existing code", "src/app.py", "Next: /adopt", "Map: show it"], ["Next: /vision"])
        shutil.rmtree(d / "src")
        (d / "PRODUCT.md").write_text("# Demo\n\n## Vision\nx\n", encoding="utf-8")
        route(d, ["Next: /adopt"], ["Next: /vision"])
        (d / "PRODUCT.md").write_text(PRODUCT, encoding="utf-8")  # the old `_Last updated: ... Stage:` header
        route(d, ["Next: status.py migrate (a dry run)", "migrate --write only on their yes"], ["Next: /adopt"])
        # the migrate route, run as the skill writes it: a dry run, then --write
        for args in (("migrate",), ("migrate", "--write")):
            code, out = run(d, *args)
            if code != 0:
                fails.append(f"`status.py {' '.join(args)}` as /playbook Step 0 writes it failed: {out.strip()[-200:]}")

    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        fresh(d)
        route(d, ["Done: nothing yet", "Next: /vision", "Size: short", "Map: skip it"], ["Batch:", "Map: show it"])
        for p in ("vision", "validate", "scope", "plan"):
            run(d, "set", p, "filled")
        route(d, ["Done: /vision, /validate, /scope, /plan", "Next: /architect", "Size: short"], ["agent track"])
        run(d, "flag", "--ai", "yes", "--agent", "yes")  # the agent track makes /architect a long sitting
        route(d, ["Next: /architect", "Size: long", "the agent track adds its own section", "room left on the plan"])
        run(d, "flag", "--agent", "no")
        run(d, "set", "architect", "filled")
        run(d, "flag", "--ui", "no")
        route(d, ["Next: /structure", "Size: long", "room left on the plan",
                  "Batch: legal - /structure + /foundation + /contracts + /tickets"])
        run(d, "flag", "--ui", "yes")
        route(d, ["Next: /structure"], ["Batch:"])  # design-system is an input phase: it splits the batch
        for p in ("structure", "design-system"):
            run(d, "set", p, "filled")
        route(d, ["Next: /foundation", "Batch: legal - /foundation + /contracts + /tickets"])
        # the override the skill records, run as it writes it; route then prints it so the skill never re-asks
        code, out = run(d, "flag", "--order-override", "the user's reason")
        route(d, ["order: Override"])
        if code != 0:
            fails.append(f"`status.py flag --order-override` as /playbook writes it failed: {out.strip()}")
        # the bypass the skill offers for an inversion, run as it writes it
        fresh(d, ui="no")
        for p in ("vision", "scope", "plan"):
            run(d, "set", p, "filled")
        run(d, "set", "validate", "running", "--due", "2026-10-01", "--reason", "pre-sale")
        route(d, ["BLOCKED: #validate is still running"])
        code, out = run(d, "bypass", "--from", "architect", "--gate", "validate", "--reason", "the user's words")
        if code != 0:
            fails.append(f"`status.py bypass` as /playbook writes it failed: {out.strip()}")

    # every status.py command the skill names is one of the round trips above
    named = set(re.findall(r"`(?:python \S+ )?(?:status\.py )?(route|migrate|bypass|flag|next|set|init|open|close)\b",
                           skill))
    if named - {"route", "migrate", "bypass", "flag"}:
        fails.append(f"/playbook names status.py {sorted(named - {'route', 'migrate', 'bypass', 'flag'})} - add its "
                     f"round trip to test_route")
    # every `route` line the skill tells the model to look for is one route really prints
    for token in re.findall(r"`((?:Where|Done|Next|Size|Batch|Map):[^`]*)`", skill):
        if not any(token in out for out in seen):
            fails.append(f"/playbook looks for route's {token!r}, which route never prints")
    # the sections the skill cites are printed word for word
    for m in re.finditer(r"`(MECHANISMS|PRINCIPLES)\.md` §([\w-]+(?: [\w-]+)*)", skill):
        name = f"{m.group(1)}.md"
        if not any(status.heading_key(m.group(2)).startswith(status.heading_key(s))
                   for s in status.ROUTER_RULES.get(name, [])):
            fails.append(f"/playbook cites {name} §{m.group(2)} but `status.py route` does not print it")
    for name, secs in status.ROUTER_RULES.items():
        body = status.print_sections(status.rule_file(name), secs)
        if not seen or body not in seen[0]:
            fails.append(f"route does not print {name} {secs} word for word")


# ---- /scope (next.55): the start prints what scope needs, `set scope filled` refuses the countable gaps ----------
SCOPE_STAKES_OK = ("  - password reset (N-A: \"no accounts\")\n"
                   "  - email verification: N/A - no accounts, the host uses the restaurant's login\n"
                   "  - account deletion + data export: in now\n"
                   "  - empty / loading / error states: in now\n"
                   "  - privacy policy + terms: in now · accessibility baseline: in now (WCAG 2.2 AA)\n"
                   "  - a way for a user to report a problem: deferred - when the first restaurant asks\n"
                   "  - the rules that apply (data protection · AI law · sector law): in now - GDPR for guest phone "
                   "numbers\n"
                   "  - the languages its users need: N/A - only English at launch\n")
SCOPE_OK = ("- **THE core feature (the one thing):** a guest gets a text when their table is ready\n"
            "- **Capacity:** solo, ~20 h a week, 3 weeks (owner)\n"
            "- **In scope (now):**\n"
            "  - the host adds a party in one step (moves: texts sent per week) - done when a party shows on the list\n"
            "  - the host marks a party seated - done when it leaves the list\n"
            "- **Deferred (out for now + the trigger that would bring it in):**\n"
            "  - online booking — when 5 restaurants (proposed) ask for it\n"
            "  - a guest app: after the first 10 restaurants (from vision: owner's answer) use texts\n"
            "- **Non-goals (deliberately never building):** a full reservation system · payments\n"
            "- **Table stakes (the list `next` prints):**\n" + SCOPE_STAKES_OK +
            "- **Detail:** `docs/scope.md` (reasoning)\n"
            "- **Read (file · date · verbatim quote):** none - this phase opened no input file\n")


def ag_start_fits(d: Path, phase: str, fails: list[str]) -> None:
    """The real `next --phase <phase>` on Antigravity: short enough for its ~4 KB window, and the file it points at
    holds the phase's start whole (next.64: a logged /vision lost its field labels to the cut)."""
    real_tool = status.playbook_tool
    pf = Path(status.__file__).resolve().parent / f"{phase}-start.md"
    try:
        status.playbook_tool = lambda: "antigravity"
        code, out = run(d, "next", "--phase", phase)
        written = pf.read_text(encoding="utf-8") if pf.is_file() else ""
    finally:
        status.playbook_tool = real_tool
        pf.unlink(missing_ok=True)
    if code != 0 or len(out.encode("utf-8")) > 3500 or f"{phase}-start.md" not in out \
            or f"/{phase} start" not in written or f"/{phase} start" in out:
        fails.append(f"Antigravity's next --phase {phase} should print a short start ({len(out.encode('utf-8'))} "
                     f"bytes) pointing at a file that holds /{phase}'s start: file has it: {f'/{phase} start' in written}")


# 2.2 (#60, #64): numbered headings and the core-loop diagram, as templates/scope.md lays it out
SCOPE_DOC = ("# Scope\n\n## 1. The core feature we will test\n\n**A guest gets a text when the table is ready.**\n\n"
             "```mermaid\nflowchart LR\n  A[party joins] --> B[text sent]\n```\n\n"
             "## Appendix A — Workings\n\n### A.1 Owner's answers\n\n1. The text when the table is ready.\n")


def scope_ready(d: Path) -> None:
    """A project with #Vision filled and docs/scope.md written; the test writes #Scope itself."""
    fresh(d)
    vision_ready(d)
    (d / "PRODUCT.md").write_text("## Vision\n" + VISION_OK + "- **Detail:** `docs/vision.md` (reasoning)\n"
                                  "\n## Scope\n\n## Plan\n", encoding="utf-8")
    code, out = run(d, "set", "vision", "filled")
    assert code == 0, out
    (d / "docs" / "scope.md").write_text(SCOPE_DOC, encoding="utf-8")


def test_next65_save(fails: list[str]) -> None:
    """(a logged 4-tool round: the cost was the number of calls): `set --commit` saves in the record's own call,
    the close never asks the save question again, /scope's Read line is the script's, a warning says no re-run, and
    the handoff is printed to copy. Each proven red by removing its code."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        scope_ready(d)
        for c in (["init", "-q", "-b", "main"], ["config", "user.email", "t@example.org"], ["config", "user.name", "t"]):
            subprocess.run(["git", *c], cwd=d, check=True)
        # a live save failed on git 2.46 when the install folder is in .gitignore (the usual case): an exclude that
        # names an ignored path makes `git add` exit 1
        (d / ".gitignore").write_text(".agents/" + chr(10), encoding="utf-8")
        (d / ".agents").mkdir()
        (d / ".agents" / "x.md").write_text("install" + chr(10), encoding="utf-8")
        src = d.parent / f"{d.name}-scope-section.md"
        long_item = "  - " + " ".join(["the host sees the whole list on one screen"] * 9) + "\n"
        seated = "  - the host marks a party seated - done when it leaves the list\n"
        src.write_text(SCOPE_OK.replace(seated, seated + long_item.replace("\n", " - done when it shows\n")),
                       encoding="utf-8")
        code, out = run(d, "set", "scope", "filled", "--section-from", str(src), "--commit", "scope recorded")
        log = subprocess.run(["git", "log", "--oneline"], cwd=d, capture_output=True, text=True).stdout
        if code != 0 or "saved: commit" not in out or "scope recorded" not in log:
            fails.append(f": set --commit should record and save in one call: {out[-500:]!r} / log {log!r}")
        tracked = subprocess.run(["git", "ls-files"], cwd=d, capture_output=True, text=True).stdout
        if ".agents/" in tracked:
            fails.append("save committed the playbook's install (.agents/)")
        if "Save this version of your project?" in out or "for the save question" in out:
            fails.append(f": after --commit the close must not ask the save question again: {out[-500:]!r}")
        if "this call was the save: never ask a save question" not in out:
            fails.append(f": step 4 should say the save is done: {out[-500:]!r}")
        if status.READ_NONE not in (d / "PRODUCT.md").read_text(encoding="utf-8"):
            fails.append(": /scope's Read line should be written by set when the run opened nothing beyond next")
        if "! PRODUCT.md#Scope" in out and "never re-run `set` for it" not in out:
            fails.append(f": a warning after a passing set should say no re-run: {out[-500:]!r}")
        if "! PRODUCT.md#Scope" not in out:
            fails.append(f" test setup: the long line should be warned: {out[-300:]!r}")
        if "copied word for word" not in out or "Open a NEW conversation and type:" not in out:
            fails.append(f": the close should print the handoff line to copy word for word: {out[-300:]!r}")
        code, out = run(d, "save", "-m", "nothing new")
        if "nothing to save" not in out:
            fails.append(f": save with no change should say so: {out!r}")
        src.unlink()


def test_scope_close(d: Path, fails: list[str]) -> None:
    """P1/P4/P8/P18/P20 for /scope. The start printed ~4 KB and told the run to read ~48 KB whole; every stop was a
    sentence. Now `next` prints the #Vision fields and this product's table stakes, and `set scope filled` refuses
    the countable gaps in one list, in any honest format, including the skill's own examples."""
    scope_ready(d)
    src = d.parent / f"{d.name}-scope-section.md"  # outside the project, as the skill says

    def close(body: str, *extra: str) -> tuple[int, str]:
        src.write_text(body, encoding="utf-8")
        return run(d, "set", "scope", "filled", "--section-from", str(src), *extra)

    code, out = run(d, "next", "--phase", "scope")
    for want in ("/scope start", "who it's for: small restaurants", "north-star target: 40 restaurants by 2027-03-31",
                 "      the languages its users need", "===== PRINCIPLES.md =====", "`(proposed)`",
                 "### table stakes [table: Item | Decision]"):
        if want not in out:
            fails.append(f"next --phase scope should print {want!r}: {out[-400:]!r}")
    if "prompt injection" in out or "a stop switch" in out:
        fails.append("next --phase scope printed AI/agent table stakes for a product flagged AI: no")
    ag_start_fits(d, "scope", fails)
    code, out = run(d, "rules", "scope")
    if code != 0 or "## Communication" not in out or "§Plain-language close" in out:
        fails.append(f"rules scope should print the start's sections only: {out[:200]!r}")
    # P20: every problem in one refusal; PRODUCT.md is put back
    before = (d / "PRODUCT.md").read_text(encoding="utf-8")
    bad = (SCOPE_OK.replace("a full reservation system · payments", "")
           .replace("online booking — when 5 restaurants (proposed) ask for it", "online booking")
           .replace("  - the languages its users need: N/A - only English at launch\n", ""))
    code, out = close(bad)
    for want in ("#Scope field empty: Non-goals", "Deferred item with no trigger: 'online booking'",
                 "no line for 'the languages its users need'"):
        if code == 0 or want not in out:
            fails.append(f"set scope filled should refuse with {want!r} in one list: {out.strip()[:400]!r}")
    if (d / "PRODUCT.md").read_text(encoding="utf-8") != before:
        fails.append("a refused /scope close changed PRODUCT.md")
    for body, want in (
            (SCOPE_OK.replace("a guest gets a text when their table is ready",
                              "texts to guests · a booking page · a host tablet"), "names more than one thing"),
            (SCOPE_OK.replace("a guest gets a text when their table is ready",
                              "1. texts to guests 2. a booking page"), "names more than one thing"),
            (SCOPE_OK.replace("  - password reset (N-A: \"no accounts\")\n", "  - password reset\n"),
             "table-stakes line not sorted: 'password reset'"),
            (SCOPE_OK.replace("the languages its users need: N/A - only English at launch",
                              "the languages its users need: N/A"), "N/A with no reason"),
            (SCOPE_OK.replace("deferred - when the first restaurant asks", "deferred"), "deferred with no trigger"),
            (SCOPE_OK.replace("when 5 restaurants (proposed) ask", "when 25 restaurants ask"), "number '25'"),
            # a whole number: #Vision's "19:05" does not make an invented 5 the owner's
            (SCOPE_OK.replace("when 5 restaurants (proposed) ask", "when 5 restaurants ask"), "number '5'"),
            # 2.2 (#64): capacity asked, a Done when per item, a carried number says where it came from
            (SCOPE_OK.replace("- **Capacity:** solo, ~20 h a week, 3 weeks (owner)\n", ""), "no `Capacity` line"),
            (SCOPE_OK.replace(" - done when it leaves the list", ""), "no Done when: 'the host marks a party seated'"),
            (SCOPE_OK.replace(" (from vision: owner's answer)", ""), "number '10' is carried from #Vision"),
            (SCOPE_OK.replace("- **In scope (now):**\n", "- **In scope (now):** -\n")
             .replace("  - the host adds a party in one step (moves: texts sent per week) - done when a party shows "
                      "on the list\n  - the host marks a party seated - done when it leaves the list\n", ""),
             "#Scope field empty: In scope (now)")):
        code, out = close(body)
        if code == 0 or want not in out:
            fails.append(f"set scope filled should refuse with {want!r}: {out.strip()[:400]!r}")
    for doc, want in ((SCOPE_DOC.replace("## 1. The core", "## The core"), "heading(s) without a number"),
                      (SCOPE_DOC.replace("```mermaid", "```text"), "no ```mermaid diagram")):
        (d / "docs" / "scope.md").write_text(doc, encoding="utf-8")
        code, out = close(SCOPE_OK)
        if code == 0 or want not in out:
            fails.append(f"set scope filled should refuse docs/scope.md with {want!r}: {out.strip()[:300]!r}")
    (d / "docs" / "scope.md").unlink()
    code, out = close(SCOPE_OK)
    if code == 0 or "no docs/scope.md" not in out:
        fails.append(f"set scope filled should refuse with no docs/scope.md: {out.strip()[:300]!r}")
    (d / "docs" / "scope.md").write_text(SCOPE_DOC, encoding="utf-8")
    # P8: the shapes other tools wrote - no "- " before a label, a table, dashes, bold verdicts, a verdict first
    honest = (SCOPE_OK.replace("- **THE core", "**THE core").replace("- **Non-goals", "**Non-goals")
              .replace("their table is ready", "their table is ready; the host sends it in one tap")
              .replace(SCOPE_STAKES_OK,
                       "| Item | Verdict | Why / trigger |\n|---|---|---|\n"
                       "| password reset | N/A | no accounts |\n| email verification | N/A | no accounts |\n"
                       "| account deletion + data export | in now | a legal duty |\n"
                       "| empty / loading / error states | **in scope now** | |\n"
                       "| privacy policy + terms | in now | |\n| accessibility baseline | in now | WCAG 2.2 |\n"
                       "| report a problem | deferred | when a host asks |\n"
                       "| rules that apply | in now | GDPR |\n| languages | N/A | English only at launch |\n"))
    code, out = close(honest)
    if code != 0:
        fails.append(f"an honest #Scope (no '- ', a table) should close: {out.strip()[:400]!r}")
    # a ';' inside ONE sorted line is a sentence, not more items (all 4 tools were refused on a logged run)
    scope_ready(d)
    semi = SCOPE_OK.replace(SCOPE_STAKES_OK, SCOPE_STAKES_OK.replace(
        "  - password reset (N-A: \"no accounts\")\n",
        # the replay's logged sentences: "verification" and "login" inside a sentence are not hidden required items
        "  - password reset: N/A - hosts use the restaurant's login; no separate passwords; no self sign-up; "
        "anything requiring verification is flagged by the host\n"
        "  - the rules that apply: in now - GDPR (a phone number is personal data); the AI disclosure rule (Art. 50); "
        "a high-risk list deferred - when real data arrives, and before 2027-12-02\n"))
    code, out = close(semi)
    if code != 0:
        fails.append(f": a sorted table-stakes line with ';' inside should close: {out.strip()[:400]!r}")
    scope_ready(d)
    code, out = close(SCOPE_OK.replace(SCOPE_STAKES_OK, SCOPE_STAKES_OK.replace(
        "  - password reset (N-A: \"no accounts\")\n", "  - password reset; email verification\n")))
    if code == 0 or "not sorted: 'password reset'" not in out or "not sorted: 'email verification'" not in out:
        fails.append(f": two unsorted items joined by ';' are still two refusals: {out.strip()[:400]!r}")
    # the replay of a logged run: a required item hidden behind a ';' in another item's sorted line is still unsorted
    scope_ready(d)
    code, out = close(SCOPE_OK.replace(SCOPE_STAKES_OK, SCOPE_STAKES_OK
                                       .replace("  - account deletion + data export: in now\n", "")
                                       .replace("  - password reset (N-A: \"no accounts\")\n",
                                                "  - password reset: N/A - no accounts; account deletion + data export\n")))
    if code == 0 or "not sorted: 'account deletion + data export'" not in out:
        fails.append(f" replay: a required item after a ';' with no verdict must be refused: {out.strip()[:400]!r}")
    # the replay of a logged Claude run: `set` wraps a line over 300 characters at its ';' - the wrapped half is the
    # same item, not one with no verdict
    scope_ready(d)
    long_rules = ("  - the rules that apply: in now - GDPR for guest phone numbers (a phone number is personal data and "
                  "the list keeps it for one evening only); the AI disclosure rule (Art. 50, a guest is told a text is "
                  "automatic); the local consumer law on reservations (no deposit is taken, so it does not bite); a "
                  "high-risk list deferred - when real data arrives, and before 2027-12-02\n")
    code, out = close(SCOPE_OK.replace(SCOPE_STAKES_OK, SCOPE_STAKES_OK.replace(
        "  - the rules that apply (data protection · AI law · sector law): in now - GDPR for guest phone numbers\n",
        long_rules)))
    if code != 0:
        fails.append(f" replay: a long sorted line wrapped by set at its ';' should close: {out.strip()[:400]!r}")
    # P8, a logged Cursor shape: a group heading with its verdicts on the deeper lines under it
    scope_ready(d)
    grouped = ("  - the rules that apply:\n    - GDPR for guest phone numbers: in now\n"
               "    - the AI disclosure rule: N/A - the product sends no AI text\n")
    code, out = close(SCOPE_OK.replace(SCOPE_STAKES_OK, SCOPE_STAKES_OK.replace(
        "  - the rules that apply (data protection · AI law · sector law): in now - GDPR for guest phone numbers\n",
        grouped)))
    if code != 0:
        fails.append(f"P8: a group heading with sorted lines under it should close: {out.strip()[:400]!r}")
    code, out = close(SCOPE_OK.replace(SCOPE_STAKES_OK, SCOPE_STAKES_OK.replace(
        "  - the rules that apply (data protection · AI law · sector law): in now - GDPR for guest phone numbers\n",
        grouped.replace(": in now", ""))))
    if code == 0 or "not sorted: 'the rules that apply: GDPR for guest phone numbers'" not in out:
        fails.append(f"P8: an unsorted line under a group heading is still refused: {out.strip()[:400]!r}")
    scope_ready(d)
    # P18: the skill's own one-line formats, written exactly as Step 2 gives them, and its N-A example
    skill = (ROOT / "commands" / "scope" / "SKILL.md").read_text(encoding="utf-8")
    # #63: the skill gives them as `table stakes` rows; the script renders a row as `<item>: <decision>` in #Scope
    rows = re.search(r"one `table stakes` row each: `([^`]+)` · `([^`]+)` · `([^`]+)`", skill)
    forms = [": ".join(c.strip() for c in r.strip().strip("|").split("|")) for r in rows.groups()] if rows else []
    if not rows or "N-A: \"no accounts\"" not in skill:
        fails.append("/scope Step 2 lost its one-line table-stakes formats or its N-A example - update this test")
    else:
        lines = [forms[0].replace("<item>", "account deletion + data export"),
                 forms[1].replace("<item>", "a way for a user to report a problem")
                 .replace("<trigger>", "the first host asks"),
                 forms[2].replace("<item>", "the languages its users need").replace("<reason>", "English only"),
                 "password reset (N-A: \"no accounts\")", "email verification (N-A: \"no accounts\")",
                 forms[0].replace("<item>", "empty / loading / error states"),
                 forms[0].replace("<item>", "privacy policy + terms"),
                 forms[0].replace("<item>", "accessibility baseline"),
                 forms[0].replace("<item>", "the rules that apply")]
        code, out = close(SCOPE_OK.replace(SCOPE_STAKES_OK, "".join(f"  - {l}\n" for l in lines)))
        if code != 0:
            fails.append(f"the skill's own table-stakes formats should close: {out.strip()[:400]!r}")
        elif "The rest of the close" not in out or "compare with #Vision" not in out or "search links" in out \
                or "not saved:" not in out:
            fails.append(f"set scope filled should print /scope's close checklist and the save facts: {out[-400:]!r}")
    # the owner's answers are kept word for word, as /vision and /plan keep them (next.56)
    scope_ready(d)
    (d / "docs" / "scope.md").write_text("# Scope\n\nThe owner's answers, word for word.\n", encoding="utf-8")
    code, out = close(SCOPE_OK)
    if code == 0 or "no `## Owner's answers`" not in out:
        fails.append(f"a docs/scope.md without `## Owner's answers` should be refused: {out.strip()[:300]!r}")
    # an AI agent sorts the AI and agent items too; a running #Validation needs the `provisional` mark
    scope_ready(d)
    code, out = run(d, "flag", "--ai", "yes", "--agent", "yes")
    code, out = run(d, "next", "--phase", "scope")
    if "prompt injection" not in out or "a stop switch that halts it" not in out:
        fails.append(f"next --phase scope should print the AI + agent table stakes for an agent: {out[-400:]!r}")
    code, out = close(SCOPE_OK)
    for want in ("no line for 'prompt injection: text from users or data that tries to steer the AI'",
                 "no line for 'a stop switch that halts it'"):
        if code == 0 or want not in out:
            fails.append(f"an agent's #Scope without its items should be refused with {want!r}: {out.strip()[:300]!r}")
    scope_ready(d)
    code, out = run(d, "set", "validate", "running", "--due", "2026-10-30", "--reason", "5 hosts try texts")
    code, out = close(SCOPE_OK)
    if code == 0 or "provisional" not in out:
        fails.append(f"#Validation running: a #Scope with no `provisional` mark should be refused: {out.strip()[:300]!r}")
    code, out = close(SCOPE_OK.replace("a guest app: after", "a guest app (provisional): after"))
    if code != 0:
        fails.append(f"a #Scope marked provisional should close while #Validation runs: {out.strip()[:300]!r}")
    # /adopt's inferred record is never refused by the new check (a project filled under older rules)
    scope_ready(d)
    code, out = close("- **THE core feature (the one thing):** texts\n", "--note", "adopted: inferred from the code")
    if code != 0:
        fails.append(f"an adopted #Scope should not meet /scope's own close checks: {out.strip()[:300]!r}")
    src.unlink(missing_ok=True)


# ---- /plan: the start (P1) and `set plan filled`'s own checks (P4, P8, P18, P20) ---------------------------------
PLAN_SCOPE = ("- **THE core feature (the one thing):** a text when the table is ready\n"
              "- **Non-goals (deliberately never building):** a booking system\n")
PLAN_ANSWERS_DOC = ("# Plan\n\n## 1. In short\n\n**The text works by November.** The demo will not prove demand yet.\n\n"
                    "## 2. Milestones\n\n### 2.1 M1 Core slice\n\nDone when a guest gets a text.\n\n"
                    "### 2.2 M2 Pilot\n\nDone when 3 restaurants use it.\n\n"
                    "## Appendix A — Workings\n\n### A.1 Owner's answers\n1. solo, 20 h/week\n2. from 2026-10-12\n"
                    "3. texts first, then the host screen\n4. keep it and flag it\n")


def plan_ok(skill: str) -> str:
    """A #Plan written exactly as SKILL.md says - its own `Needs:`, `(derived: ...)` and `Read: none` forms, read out
    of the skill text so the round trip follows any edit (P18) - with a four-risks TABLE (a logged run's shape, P8)."""
    needs = re.search(r"`(Needs: <prerequisite> \(<the milestone or person that delivers it>\))`", skill).group(1)
    derived = re.search(r"`(\(derived: <hours> ÷ <hours a week>\))`", skill).group(1)
    # the skill says to leave the `read` field out when only PRODUCT.md was read: the script writes `none`
    read_none = "none - only PRODUCT.md sections" if "no `read` field (`none` is written)" in skill else "MISSING"
    return ("- **Phases / milestones (core first):**\n"
            "  - M1 Core slice · a guest joins the list and gets a text\n"
            "  - M2 Pilot · restaurants use it for real\n"
            "- **Timeline:** solo, 20 h/week, from 2026-10-12\n"
            "  - M1 2026-10-12 → 11-22 " + derived.replace("<hours>", "120 h").replace("<hours a week>", "20") + "\n"
            "  - M2 11-23 → 2027-04-30\n"
            "  - North star: the plan ends 2027-04-30, after 2027-03-31 - kept and flagged (answer 4)\n"
            "- **Exit criteria per milestone:**\n"
            "  - **M1:** a guest on the list gets a text within 1 minute of 'table ready' (proposed)\n"
            "    - " + needs.replace("<prerequisite>", "nothing outside this milestone").replace(
                " (<the milestone or person that delivers it>)", "") + "\n"
            "  - **M2:** 3 restaurants seat walk-ins from the list for 14 days (proposed)\n"
            "    - " + needs.replace("<prerequisite>", "a public URL").replace(
                "<the milestone or person that delivers it>", "/deploy, M2") + "\n"
            "- **Four-risks row per milestone (value · usability · feasibility · viability):**\n"
            "  | Milestone | Retires | How you'll know |\n  |---|---|---|\n"
            "  | M1 | feasibility | the text arrives |\n"
            "  | M2 | value · usability | 3 restaurants keep using it (proposed) |\n"
            "- **Usability checkpoint before going public (which milestone, and its exit criterion):** M2 - 5 hosts "
            "run the list unaided (proposed)\n"
            "- **Concern-area coverage (security · ai · observability · DX · testing · infra · docs · product):** "
            "security: now · ai-specific: N-A (no AI) · observability: next · developer-experience: now · "
            "testing: now · infra: next · documentation: now · product: now · GDPR: now, in M1 · English: now\n"
            "- **Schedule risks + buffer:** the text provider's sign-up may slip a week - 1 week of slack in M2\n"
            "- **Open items:** none - every number is the user's\n"
            "- **Detail:** `docs/plan.md` (reasoning + workings; this section stays a RECORD)\n"
            "- **Read (file · date · verbatim quote):** " + read_none + "\n")


def test_early_doc_warnings(fails: list[str]) -> None:
    """2.2 (#60): the plain-English rules for a phase document only WARN - a logged playbook vision averaged 19.7 words
    a sentence, with 41 dash joins and 16 provenance labels in the body (plain: 17.5, 0, 0). Each warning shown on
    that shape, none on a plain one; the appendix may hold the labels; a dead in-document link is named."""
    bad = ("# Vision\n\n## 1. Vision in one line\n\nAI can spot life moments for every customer in every channel at "
           "the right time and in the right tone — the owner's claim; vendor writing says it works (not opened) and "
           "the spine records it for /scope and PRODUCT.md and everyone downstream to read later on.\n\n"
           "See [the terms](#north-star-terms).\n\n## Appendix A — Workings\n\n### A.1 North-star terms\n\n"
           "- derived: 40 · the owner's claim\n")
    warns = " | ".join(status.early_doc_warnings("docs/vision.md", bad))
    for want in ("over 30", "em-dash", "owner's claim", "not opened", "PRODUCT.md", "/scope", "spine",
                 "#north-star-terms"):
        if want not in warns:
            fails.append(f"early_doc_warnings should name {want!r}: {warns[:400]!r}")
    if "derived" in warns:
        fails.append("a label inside the appendix is where it belongs - no warning for it")
    good = ("# Vision\n\n## 1. Vision in one line\n\n**Nobody waits at the door.** Guests wait outside today. The app "
            "texts them when the table is ready [1].\n\nSee [the terms](#a1-north-star-terms).\n\n"
            "## Appendix A — Workings\n\n### A.1 North-star terms\n\n- derived: 40\n")
    warns = status.early_doc_warnings("docs/vision.md", good)
    if warns:
        fails.append(f"a plain document should get no warning: {warns}")
    tpl = (ROOT / "templates" / "vision.md").read_text(encoding="utf-8")
    for name in ("vision.md", "scope.md", "plan.md"):
        text = (ROOT / "templates" / name).read_text(encoding="utf-8")
        if status.unnumbered_headings(text):
            fails.append(f"templates/{name} has unnumbered headings: {status.unnumbered_headings(text)}")
    # #12: an owner's number shown as what a search settled
    doc = (VISION_DOC.replace("1. A waitlist for small restaurants.", "1. A waitlist; 35% of walk-ins leave.")
           .replace("settled: walk-ins grew", "settled: 35% of walk-ins leave"))
    if not any("35%" in w for w in status.early_doc_owner_numbers(doc)):
        fails.append("a search line stating the owner's own number should be warned")
    if status.early_doc_owner_numbers(VISION_DOC):
        fails.append("a search line with its own numbers should not be warned")
    # #63: the diagram is a field (`how it works`), the rest is the layout the script renders
    fields_tpl = (ROOT / "templates" / "product-vision.md").read_text(encoding="utf-8")
    if "```mermaid" not in fields_tpl or "In scope" not in tpl or "Open questions" not in tpl \
            or "Brief point" not in tpl:
        fails.append("templates/vision.md lost a part the close checks (diagram, In scope, Open questions, brief table)")


def test_plan_close(d: Path, fails: list[str]) -> None:
    """One start call prints the spine facts + the rules; `set plan filled` accepts the skill's own shapes and refuses
    each countable gap, all in ONE refusal. Each case proven red by breaking plan_gaps / plan_start_text."""
    skill = (ROOT / "commands" / "plan" / "SKILL.md").read_text(encoding="utf-8")
    src = d.parent / f"{d.name}-plan-section.md"  # outside the project, as Step 3 says

    def setup(validation: str = "") -> None:
        fresh(d)
        (d / "PRODUCT.md").write_text("## Vision\n" + VISION_OK + "\n## Validation\n" + validation + "\n## Scope\n"
                                      + PLAN_SCOPE + "\n## Plan\n\n## Architecture\n", encoding="utf-8")
        vision_ready(d)
        for p in ("vision", "scope"):
            code, out = run(d, "set", p, "filled", *(("--note", "adopted: /plan's test setup") if p == "scope" else ()))
            assert code == 0, out
        (d / "docs" / "plan.md").write_text(PLAN_ANSWERS_DOC, encoding="utf-8")

    def close(body: str) -> tuple[int, str]:
        src.write_text(body, encoding="utf-8")
        return run(d, "set", "plan", "filled", "--section-from", str(src))

    setup()
    code, out = run(d, "next", "--phase", "plan")
    for want in ("/plan start", "#Scope, whole:", "a text when the table is ready", "40 restaurants by 2027-03-31",
                 "empty (/validate is optional", "## Production-readiness concern areas", "### milestones [table:",
                 "status.py rules plan"):
        if want not in out:
            fails.append(f"next --phase plan should print {want!r} (one start call, P1)")
    if "(run it now" in out or "## §Step 3b" in out:
        fails.append("next --phase plan should neither send the run to a second rules call nor print the close's rules")
    ag_start_fits(d, "plan", fails)
    good = plan_ok(skill)
    code, out = close(good)
    if code != 0 or "The rest of the close" not in out or "compare with #Scope" not in out or "search links" in out:
        fails.append(f"a #Plan written as SKILL.md says should record, then print /plan's close checklist: "
                     f"{out[-600:]!r}")
    # #Vision's constraints get a line in #Plan (the /plan session's review: every run missed law and languages)
    setup()
    code, out = close(good.replace(" · GDPR: now, in M1 · English: now", ""))
    if code == 0 or "constraint" not in out or "GDPR" not in out or "'English'" not in out:
        fails.append(f"a #Plan that leaves #Vision's constraints unscheduled should be refused: {out[-400:]!r}")
    setup()
    code, out = close(good.replace("GDPR: now, in M1 · English: now", "GDPR: later - when real data arrives · "
                                                                       "English: N-A, the only language"))
    if code != 0:
        fails.append(f"a constraint deferred with a trigger should record: {out[-400:]!r}")
    setup()  # a ',' inside brackets is one constraint ("GDPR, the ePrivacy Directive" are one rules line)
    prod = d / "PRODUCT.md"
    prod.write_text(prod.read_text(encoding="utf-8").replace("(GDPR) ·", "(GDPR, the ePrivacy Directive) ·"), encoding="utf-8")
    code, out = close(good)
    if code != 0:
        fails.append(f": a ',' inside a #Vision constraint's brackets should not split it: {out[-400:]!r}")
    setup()  # P8: `**Label:**` without the leading "- " (two logged tools wrote it) reads the same
    code, out = close(re.sub(r"(?m)^- \*\*", "**", good))
    if code != 0:
        fails.append(f"#Plan fields without the leading '- ' should read the same: {out[-400:]!r}")
    setup()  # a logged run's shape: nothing asked, invented timeline, #Vision as evidence, its own output receipted
    bad = (good.replace("solo, 20 h/week, from 2026-10-12", "4-6 weeks total")
           .replace("  - M1 2026-10-12 → 11-22", "  - M1 weeks 1-2").replace("  - M2 11-23 → 2027-04-30\n", "")
           .replace("  - North star: the plan ends 2027-04-30, after 2027-03-31 - kept and flagged (answer 4)\n", "")
           .replace("  - **M2:** 3 restaurants", "  - **M2:** 4 restaurants").replace("    - Needs: a public URL (/deploy, M2)\n", "")
           .replace("  | M1 | feasibility | the text arrives |", "  | M1 | as in #Vision | the text arrives |")
           .replace("M2 - 5 hosts", "5 hosts").replace("infra: next · ", "")
           .replace("none - only PRODUCT.md sections", "docs/plan.md · 2026-09-24 · \"core first\"")
           .replace("keep using it (proposed) |\n", "keep using it (proposed) |\n  | M3 | nothing | x |\n"))
    (d / "docs" / "plan.md").write_text("# Plan\n\ncore first, $\\ge 3$ restaurants\n", encoding="utf-8")
    code, out = close(bad.replace("  - M2 Pilot", "  - M2 Pilot\n  - M3 Later"))
    for want in ("the Timeline has no capacity", "the Timeline has no start date", "M2's exit criterion names no "
                 "prerequisite", "M3 has no exit criterion", "M3's four-risks row names none", "cite #Vision",
                 "names none of the plan's milestones", "infra is not marked", "docs/plan.md, which this phase wrote",
                 "no `## Owner's answers` block", "unmarked", "docs/plan.md has LaTeX",
                 # 2.2 (#65): the whole plan in docs/plan.md, numbered; Open items; schedule risks
                 "docs/plan.md does not show M1, M2"):
        if want not in out:
            fails.append(f"set plan filled should refuse {want!r} in its one list: {out[-300:]!r}")
    if code == 0 or out.count("REFUSED") != 1:
        fails.append("set plan filled should name every problem in ONE refusal (P20)")
    # 2.2 (#65): schedule risks + buffer and Open items are fields; a number nobody gave listed under Open items is
    # named as undecided; a #Scope table stake "in now" sits in an exit criterion; docs/plan.md headings are numbered
    setup()
    code, out = close(good.replace("- **Open items:** none - every number is the user's\n", "")
                      .replace("- **Schedule risks + buffer:** the text provider's sign-up may slip a week - 1 week of "
                               "slack in M2\n", ""))
    for want in ("no `Open items` line", "#Plan field empty: the schedule risks + buffer"):
        if code == 0 or want not in out:
            fails.append(f"set plan filled should refuse {want!r}: {out[-300:]!r}")
    setup()
    code, out = close(good.replace("within 1 minute of 'table ready' (proposed)", "within 7 minutes of 'table ready'"))
    if code == 0 or "unmarked" not in out:
        fails.append(f"an unmarked new number should be refused: {out[-300:]!r}")
    code, out = close(good.replace("within 1 minute of 'table ready' (proposed)", "within 7 minutes of 'table ready'")
                      .replace("none - every number is the user's", "the text delay: 7 minutes · recommended: 7"))
    if code != 0:
        fails.append(f"a number listed under Open items should record: {out[-300:]!r}")
    setup()
    prod = d / "PRODUCT.md"
    prod.write_text(prod.read_text(encoding="utf-8").replace(
        "- **Non-goals (deliberately never building):** a booking system\n",
        "- **Non-goals (deliberately never building):** a booking system\n- **Table stakes:**\n"
        "  - accessibility baseline: in now\n  - empty / loading / error states: in now\n"), encoding="utf-8")
    code, out = close(good)
    if code == 0 or "'accessibility baseline' is in now" not in out or "'empty / loading / error states'" not in out:
        fails.append(f"a #Scope table stake in now with no milestone should be refused: {out[-400:]!r}")
    code, out = close(good.replace("within 1 minute of 'table ready' (proposed)", "within 1 minute of 'table ready' "
                                   "(proposed), with an error state and the accessibility baseline met"))
    if code != 0:
        fails.append(f"stakes covered by an exit criterion should record: {out[-400:]!r}")
    setup()
    (d / "docs" / "plan.md").write_text(PLAN_ANSWERS_DOC.replace("## 1. In short", "## In short"), encoding="utf-8")
    code, out = close(good)
    if code == 0 or "heading(s) without a number" not in out:
        fails.append(f"an unnumbered heading in docs/plan.md should be refused: {out[-300:]!r}")
    setup()  # past the north-star date with no word about it; value untested while #Validation is empty; an empty field
    code, out = close(re.sub(r"(?m)^(- \*\*Concern-area coverage[^\n]*?\*\*).*$", r"\1 TBD", good)
                      .replace("  - North star: the plan ends 2027-04-30, after 2027-03-31 - kept and flagged "
                               "(answer 4)\n", "").replace("value · usability", "usability"))
    for want in ("after the north-star date 2027-03-31", "#Validation is empty, so value",
                 "#Plan field empty: the concern-area coverage"):
        if want not in out:
            fails.append(f"set plan filled should refuse {want!r}: {out[-300:]!r}")
    setup()  # a running experiment: the plan starts before its due date and is not marked provisional
    code, out = run(d, "set", "validate", "running", "--due", "2026-11-01", "--reason", "pre-sale count")
    assert code == 0, out
    code, out = close(good)
    if "before the running experiment's due date 2026-11-01" not in out:
        fails.append(f"set plan filled should refuse a timeline before a running experiment's due date: {out[-300:]!r}")
    code, out = close(good.replace("- **Timeline:**", "_Provisional: the pre-sale lands 2026-11-01._\n- **Timeline:**"))
    if code != 0:
        fails.append(f"a provisional #Plan over a running experiment should record: {out[-300:]!r}")
    src.unlink(missing_ok=True)


ARCH_SPINE = (
    "## Vision\n- **Who it's for:** owners of small online shops answering order questions\n"
    "- **North star — target + date:** 40 shops by 2027-03-31\n- **Business model (free / paid / internal):** paid, "
    "€29 a month per shop\n- **Constraints (the rules that apply · languages):** GDPR · English\n"
    "- **AI (what it does · cost per use):** looks orders up and drafts replies · the owner approves refunds · under "
    "€0.05 per conversation\n\n## Scope\n- **THE core feature (the one thing):** the agent answers where an order is\n"
    "- **In scope (now):**\n  - order lookup\n- **Deferred (out for now + the trigger):**\n  - refunds over €50 - when "
    "10 shops ask\n- **Non-goals (never):**\n  - a phone channel - never\n- **Table stakes:**\n  - prompt injection: "
    "in now\n\n## Plan\n- **Phases / milestones (core first):**\n  - M1 — order lookup answered\n- **Timeline:**\n"
    "  - Capacity: solo, 20 h/week. Start: 2026-10-05.\n  - Paid infra: from M1 go-live — trigger: /deploy\n"
    "- **Concern-area coverage:**\n  - security: now — secret scan\n\n## Architecture\n")
ARCH_OK = """- **Stack + tools:** one TypeScript app; details below.
  - Constraint set: solo, 20 h/week, knows TypeScript; €40 a month for hosting and AI; managed only; any vendor, code portable
  - Language: TypeScript on Node 24 — user-chosen
  - Web: Next.js 16 (one app; the owner's inbox is a page) — default taken, not user-chosen
  - UI components: shadcn/ui with Tailwind CSS — default taken, not user-chosen
  - Datastore: PostgreSQL 17 with Drizzle; payloads typed (zod) — default taken, not user-chosen
  - LLM: claude-sonnet-5-5, released 2026-08-19, behind `LLMProvider` — default taken, not user-chosen
- **Data custody:** managed-serverless Postgres in the EU (GDPR; the free tier holds 0.5 GB) — default taken, not user-chosen
- **Runtime target per deployable unit:**

  | Unit | Target | Cost and limits | Provenance |
  |---|---|---|---|
  | web app + API | PaaS container, EU region | $7/month; the free tier sleeps after 15 min idle | user-chosen |
  | nightly eval | CI | 2,000 free minutes a month, then billed | default taken, not user-chosen |
- **Identity custody:** the PaaS's auth add-on, email + a magic link — default taken, not user-chosen
- **Dev tooling:** husky · gitleaks · npm scripts · biome (format + lint) · package.json with package-lock.json
- **Key decisions / ADRs:** ADR-0001 one app · ADR-0002 no agent framework · ADR-0003 action tiers · ADR-0004 staged autonomy — `docs/adr/`
- **Externals behind provider/adapter interfaces (+ resilience strategy each):**
  - LLM: `LLMProvider` - timeout 30 s; retry transient errors twice; fallback: hand the conversation to the owner
  - Shop orders: `OrderSource` (the shop platform's API; it can be slow, so a 10 s timeout) - one retry, then a circuit breaker
- **Resilience · perf/cost budget · migrations approach:**
  - Resilience: per external above.
  - Budget: under €0.05 per conversation (#Vision) - ~6k input tokens × $3/1M + 800 output tokens × $15/1M ≈ €0.03 per conversation (derived; aspirational until /eval measures it).
  - Migrations: Drizzle migrations, never a schema push at boot.
  - Security: no secret in code (.env, gitleaks); every row carries the shop key.
  - Observability: structured JSON logs and the conversation log.
- **(AI) prompt-versioning · eval harness · tracing:**
  - Prompt versioning: versioned prompt files; the version stamped on every reply.
  - Eval harness: a golden set of 40 order questions in CI.
  - Tracing: OpenTelemetry spans per agent step — default taken, not user-chosen
  - Model runtime config: claude-sonnet-5-5 · thinking off · max_tokens 1,000 · timeout 30 s · retry 2, a refusal hands over · prompt caching on the system prompt.
- **(Agent) the ten AGENT.md §Architect rows:**
  1. Framework: no framework - the vendor SDK and a plain tool loop (ADR-0002) — user-chosen
  2. Action tiers: get_order = read; refund = needs approval; delete = forbidden (ADR-0003) — default taken, not user-chosen
  3. Caps: 6 steps, 8 tool calls, €0.05, 60 s; a cap hit hands over — default taken, not user-chosen
  4. Untrusted input: messages and order notes are data; every call checked against the shop and customer; 3 injection cases for /test — default taken, not user-chosen
  5. Hand-off to a person: a cap hit, a refund, the customer asks — default taken, not user-chosen
  6. Staged autonomy and kill switch: shadow, then approve; a switch per shop and a global one (ADR-0004) — user-chosen
  7. Audit log: every action, append-only, per shop — default taken, not user-chosen
  8. Memory: nothing persists between conversations — default taken, not user-chosen
  9. Agent evals: the golden set scores tool, arguments and outcome — default taken, not user-chosen
  10. AI disclosure: the reply footer says it is AI-written — default taken, not user-chosen
"""
ARCH_DOC_OK = """# Architecture — Shop reply agent

> **Status:** `draft` · written 2026-09-24 from the vision, scope and plan. **Owner:** read Overview, What drives the
> design, Decisions, Monthly cost and Risks and open questions. **Developers and coding agents:** all of it.

## Overview

One TypeScript app on a PaaS answers order questions for small shops. The agent looks orders up through the shop's
API and drafts a reply; the owner approves refunds. Orders are read, never changed, and everything runs in the EU.

```mermaid
flowchart LR
  Owner -->|approves| App[web app + API]
  App --> DB[(Postgres)]
  App --> LLM[LLMProvider]
  App --> Shop[OrderSource]
```

| Area | Choice | Why, in one line (C# / A#) | D# |
|---|---|---|---|
| Kind of product | web app, AI agent | the owner reads drafts on a page (C1) | D1 |
| Language and framework | TypeScript, Next.js | the owner knows TypeScript (A1) | D1 |
| Where it runs | PaaS container, EU region | managed only (A3) | D3 |
| Data store | PostgreSQL | standard and portable (A4) | D3 |

## What drives the design

| # | Constraint | Number | Source | Proven by |
|---|---|---|---|---|
| C1 | A refund is never made without the owner | 0 refunds without approval | scope | the approval test |
| C2 | Hosting and AI stay within budget | under 40 euro a month | A2 | the monthly bill |

**Out of scope for this architecture:** changing orders; sending replies on its own.

## Rules the code must keep

| # | Rule | From | Enforced by [block] | Proven by |
|---|---|---|---|---|
| R1 | The agent NEVER changes an order; it has read tools only. | D2, C1 | the tool registry [`agent/`] | the registry test |

## How it works, step by step

1. **A customer writes** [`inbox/`: the webhook]. The message is stored.
2. **The agent drafts a reply** [`agent/`: draft]. The order is read through OrderSource.
3. **The owner approves** [`inbox/`: approve]. A refund waits for this step.

```mermaid
sequenceDiagram
  actor C as Customer
  participant I as inbox/
  participant A as agent/
  Note over C,I: Step 1
  C->>I: question
  Note over I,A: Step 2
  I->>A: draft
```

**When a step fails:**

| Step | What can go wrong | What the product does | What the user or operator sees |
|---|---|---|---|
| 2 | The model is down | retry once, then hold | the message waits in the inbox |

## Building blocks

| Block | Responsible for (in plain words) | Owns (data it may change) | Calls |
|---|---|---|---|
| `inbox/` | messages and approvals | messages | I1, in-process |
| `agent/` | drafting | drafts | OrderSource, HTTP |

## Data

| Entity | Key fields and links | Sensitivity now → with real data | Stored in | Kept for · deleted how |
|---|---|---|---|---|
| Message | id, shop, text | personal → personal | PostgreSQL | 90 days, a nightly delete |

## Conventions and terms

| Concern | Convention | Enforced where |
|---|---|---|
| Money | amounts are integer cents | a type |

**Terms:** **Draft** - a reply the owner has not approved yet.

## Decisions

**Defaults waiting for the owner's confirmation:** D2.

### D1. One TypeScript app
- **Why:** the owner works alone and knows TypeScript (A1).
- **Trade-off we accept:** one process carries the inbox and the agent.
- **Rejected:** two services - more to run alone.
- **Revisit when:** more than 50 shops.
- **Rule:** none · **ADR:** [ADR-0001](adr/0001-one-app.md) · **Provenance:** user-chosen

### D2. No agent framework
- **Why:** three tools and a fixed flow (C2).
- **Trade-off we accept:** retries are written by hand.
- **Rejected:** Mastra - more than three tools need.
- **Revisit when:** a fourth tool.
- **Rule:** R1 · **ADR:** [ADR-0002](adr/0002-no-agent-framework.md) · **Provenance:** default taken, not user-chosen

## Security and privacy

| Concern | How it is handled | Enforced by (layer) |
|---|---|---|
| Identity of people | the owner logs in with a passkey | the PaaS login |

## AI part

- **What the model does, and what it never does:** drafts replies; never changes an order.
- **Cost per use:** (3,000 × 3 + 500 × 15) / 1,000,000 ≈ 0.02 dollar per reply.

## Running it

| Part | Runs on (host, region) | Network (public, private) | Runs as (identity) | Data in it |
|---|---|---|---|---|
| web app + API | PaaS container, EU | public | the app role | messages |

## Mapping to the plan

| Milestone | Needs from the architecture | Decisions it may reopen |
|---|---|---|
| M1 | inbox and agent | D2 |

## Risks and open questions

| # | Risk | Likelihood · impact | What reduces it | Watched by |
|---|---|---|---|---|
| RK1 | the shop API changes | low · high | OrderSource adapter | the nightly eval |

---

## Appendix A — Owner's answers

1. "just me, about 20 hours a week, I know TypeScript"
2. "40 euro a month to start"

## Appendix B — Search list

- runtime · PaaS pricing free tier 2026 · the free tier sleeps after 15 min; $7/month always on · https://example-paas.com/pricing
- framework · best TypeScript agent frameworks 2026 tool-calling support agent · a plain loop fits 3 tools · https://example-review.dev/ts-agents-2026

## Appendix C — Options considered

### Framework options

| Option | Fits | Cost to run | Lock-in | Version · date · source |
|---|---|---|---|---|
| No framework (vendor SDK + a loop) | yes | none | low | 0.71.0 · 2026-09-20 · https://www.npmjs.com/package/@anthropic-ai/sdk |
| Mastra | yes | none | low | 0.24.1 · 2026-09-12 · https://www.npmjs.com/package/@mastra/core |
| VoltAgent | yes | none | low | 1.3.0 · 2026-09-02 · https://www.npmjs.com/package/@voltagent/core |

## Appendix D — Sources and what is not verified

**Not verified:** the PaaS price after 2026.
"""
ARCH_ADRS = {"0001-one-app.md": "one app", "0002-no-agent-framework.md": "no agent framework, a plain tool loop",
             "0003-action-tiers.md": "action tiers enforced in code",
             "0004-staged-autonomy.md": "staged autonomy and a kill switch per shop"}

# 2.3 (#63, #40): the ONE fields file a run writes; the script renders #Architecture and docs/architecture.md from it
ARCH_FIELDS_OK = """### constraints
- team: solo, 20 h/week, knows TypeScript
- money: €40 a month for hosting and AI
- infrastructure: managed only
- lock-in: any vendor, code portable
- data location: EU only
- login: none: its own accounts

### stack
- Language: TypeScript on Node 24 — user-chosen
- Web: Next.js 16, one app; the owner's inbox is a page — default taken, not user-chosen
- UI components: shadcn/ui with Tailwind CSS — default taken, not user-chosen
- Datastore: PostgreSQL 17 with Drizzle; payloads typed with zod — default taken, not user-chosen
- LLM: claude-sonnet-5-5, released 2026-08-19, behind LLMProvider — default taken, not user-chosen

### data custody
managed-serverless Postgres in the EU (GDPR; the free tier holds 0.5 GB) — default taken, not user-chosen

### runtime
| Unit | Category | Host and region | Cost and free-tier limits | Provenance |
|---|---|---|---|---|
| web app + API | PaaS container | a PaaS, EU region | $7/month; the free tier sleeps after 15 min idle | user-chosen |
| nightly eval | CI | the CI service | 2,000 free minutes a month, then billed | default taken, not user-chosen |

### identity
the PaaS's auth add-on, email + a magic link — default taken, not user-chosen

### dev tooling
- hook runner: husky
- secret scanner: gitleaks
- task runner: npm scripts
- formatter/linter: biome (format + lint)
- dependency manifest: package.json with package-lock.json
- type checker: tsc --noEmit

### externals
| External | Used for | Adapter interface | Timeout · retry · if it is down | Stand-in | How to replace it |
|---|---|---|---|---|---|
| LLM | drafting replies | LLMProvider | 30 s; retry transient errors twice; hand the conversation to the owner | a recorded reply | another provider behind LLMProvider |
| Shop orders | order lookup | OrderSource | 10 s; one retry, then a circuit breaker | a fake shop | another shop platform |

### concerns
- resilience: per external above
- budget: under €0.05 per conversation (#Vision), derived from the model call; aspirational until /eval measures it
- migrations: Drizzle migrations, never a schema push at boot
- security: no secret in code (.env, gitleaks); every row carries the shop key
- observability: structured JSON logs and the conversation log

### ai
- prompt versioning: versioned prompt files; the version stamped on every reply
- eval harness: a golden set of 40 order questions in CI
- tracing: OpenTelemetry spans per agent step
- model: claude-sonnet-5-5, released 2026-08-19, EU endpoint
- runtime config: thinking off · max_tokens 1,000 · timeout 30 s · retry 2, a refusal hands over · prompt caching on the system prompt · no streaming

### cost per use
- use: conversation
- calls per use: 2
- worst case calls: 6
- input tokens: 6,000
- output tokens: 800
- input price per 1M: 3
- output price per 1M: 15
- currency: $
- source: https://example-llm.com/pricing

### agent
1. Framework: no framework - the vendor SDK and a plain tool loop (D2) — user-chosen
2. Action tiers: get_order = read; refund = needs approval; delete = forbidden — default taken, not user-chosen
3. Caps: 6 steps, 8 tool calls, €0.05, 60 s; a cap hit hands over — default taken, not user-chosen
4. Untrusted input: messages and order notes are data; 3 injection cases for /test — default taken, not user-chosen
5. Hand-off to a person: a cap hit, a refund, the customer asks — default taken, not user-chosen
6. Staged autonomy and kill switch: shadow, then approve; a switch per shop — user-chosen
7. Audit log: every action, append-only, per shop — default taken, not user-chosen
8. Memory: nothing persists between conversations — default taken, not user-chosen
9. Agent evals: the golden set scores tool, arguments and outcome — default taken, not user-chosen
10. AI disclosure: the reply footer says it is AI-written — default taken, not user-chosen

### decisions
#### D1. One TypeScript app
- problem: one person builds and runs everything
- options: one app · two services
- why: the owner works alone and knows TypeScript (A1)
- costs: one process carries the inbox and the agent
- revisit: more than 50 shops
- rule: none
- provenance: user-chosen

#### D2. No agent framework, a plain tool loop
- problem: three tools and a fixed flow
- options: no framework · Mastra · VoltAgent
- why: three tools need no framework (C2)
- costs: retries are written by hand
- revisit: a fourth tool
- rule: R1
- provenance: default taken, not user-chosen

#### D3. Managed Postgres in the EU
- problem: orders and messages are personal data
- options: managed Postgres · SQLite on a disk
- why: managed only (A3), EU only (A5)
- costs: a monthly bill after the free tier
- revisit: over 0.5 GB
- provenance: default taken, not user-chosen

#### D4. Refunds wait for the owner
- problem: a wrong refund costs money
- options: approve each refund · a refund limit
- why: 0 refunds without approval (C1)
- costs: the owner must answer quickly
- revisit: 10 shops ask for auto refunds
- rule: R1
- provenance: user-chosen

### overview
One TypeScript app on a PaaS answers order questions for small shops. The agent looks orders up through the shop's
API and drafts a reply; the owner approves refunds. Orders are read, never changed, and everything runs in the EU.

```mermaid
flowchart LR
  Owner -->|approves or ignores a draft| App[web app + API]
  App -->|order questions| Shop[shop platform]
```

| Area | Choice | Why, in one line (C# / A#) | D# |
|---|---|---|---|
| Kind of product | web app, AI agent | the owner reads drafts on a page (C1) | D1 |

### what drives the design
| # | Constraint | Number | Source | Proven by |
|---|---|---|---|---|
| C1 | A refund is never made without the owner | 0 refunds without approval | scope | the approval test |

**Out of scope for this architecture:** changing orders.

### rules
| # | Rule | From | Enforced by [block] | Proven by |
|---|---|---|---|---|
| R1 | The agent NEVER changes an order; it has read tools only. | D2, C1 | the tool registry [`agent/`] | the registry test |

### how it works
1. **A customer writes** [`inbox/`: the webhook]. The message is stored.
2. **The agent drafts a reply** [`agent/`]. The order is read through OrderSource.

```mermaid
sequenceDiagram
  actor C as Customer
  participant I as inbox/
  Note over C,I: Step 1
  C->>I: question
  alt a refund
    I->>C: waits for the owner
  end
```

### building blocks
| Block | Responsible for | Owns | Calls |
|---|---|---|---|
| `inbox/` | messages and approvals | messages | I1, in-process |

### data
| Entity | Key fields and links | Sensitivity now → with real data | Stored in | Kept for · deleted how |
|---|---|---|---|---|
| Message | id, shop, text | personal → personal | PostgreSQL | 90 days, a nightly delete |

### conventions and terms
| Concern | Convention | Enforced where |
|---|---|---|
| Money | amounts are integer cents | a type |

### security and privacy
| Concern | How it is handled | Enforced by (layer) |
|---|---|---|
| Identity of people | the owner logs in with a magic link | the PaaS login |

### ai part
- **What the model does, and what it never does:** drafts replies; never changes an order.

### running it
- **Started by:** requests.

### mapping to the plan
| Milestone | Needs from the architecture | Decisions it may reopen |
|---|---|---|
| M1 | inbox and agent | D2 |

**Scope items:** order lookup - `agent/` through OrderSource; prompt injection - R1.

### risks and open questions
| # | Risk | Likelihood · impact | What reduces it | Watched by |
|---|---|---|---|---|
| RK1 | the shop API changes | low · high | OrderSource adapter | the nightly eval |

### answers
A1. Who builds and runs it? "just me, about 20 hours a week, I know TypeScript"
A2. Money a month? "40 euro a month to start"

### searches
- runtime · PaaS pricing free tier 2026 · the free tier sleeps after 15 min · https://example-paas.com/pricing
- framework · TypeScript agent frameworks 2026 · a plain loop fits 3 tools · https://example-review.dev/ts-agents-2026

### options
#### Framework options
| Option | Fits | Cost to run | Lock-in | Version · date · source |
|---|---|---|---|---|
| No framework (vendor SDK + a loop) | yes | none | low | 0.71.0 · 2026-09-20 · https://www.npmjs.com/package/@anthropic-ai/sdk |
| Mastra | yes | none | low | 0.24.1 · 2026-09-12 · https://www.npmjs.com/package/@mastra/core |
| VoltAgent | yes | none | low | 1.3.0 · 2026-09-02 · https://www.npmjs.com/package/@voltagent/core |
"""


ARCH_START_MAX = 17800  # characters on the test project; a realistic one adds ~6.4K - 16.8K -> 23.2K (P47)


def test_architect_close(d: Path, fails: list[str]) -> None:
    """One start call prints the spine facts, AGENT.md §Architect and the rules; the run writes ONE fields file and
    `set architect filled --from-fields` renders #Architecture and a numbered docs/architecture.md from it (#63, #40),
    refusing only what it can count; checks that read prose warn (2.3). The legacy `--section-from` path still
    records a hand-written record. Each case proven red by breaking architect_gaps / arch_render / the start."""
    import shutil
    src = d.parent / f"{d.name}-architect-section.md"  # outside the project, as the start says
    fld = d.parent / f"{d.name}-architect-fields.md"

    def setup(ai: str = "yes", agent: str = "yes", doc: str = ARCH_DOC_OK, adrs: dict | None = None,
              spine: str = ARCH_SPINE) -> None:
        fresh(d, ui="yes")
        shutil.rmtree(d / "docs", ignore_errors=True)
        (d / "docs").mkdir(parents=True)
        (d / "PRODUCT.md").write_text(spine, encoding="utf-8")
        for p in ("vision", "scope", "plan"):
            code, out = run(d, "set", p, "filled", "--note", "adopted: /architect's test setup")
            assert code == 0, out
        for flag, v in (("--ai", ai), ("--agent", agent)):
            code, out = run(d, "flag", flag, v)
            assert code == 0, out
        if doc:
            (d / "docs" / "architecture.md").write_text(doc, encoding="utf-8")
        for name, what in (adrs or {}).items():
            (d / "docs" / "adr").mkdir(exist_ok=True)
            (d / "docs" / "adr" / name).write_text(f"# ADR — {what}\n\n- **Status:** `accepted`\n", encoding="utf-8")

    def close(body: str, *extra: str) -> tuple[int, str]:
        src.write_text(body, encoding="utf-8")
        return run(d, "set", "architect", "filled", "--section-from", str(src), *extra)

    def save(fields: str, *extra: str) -> tuple[int, str]:
        fld.write_text(fields, encoding="utf-8")
        return run(d, "set", "architect", "filled", "--from-fields", str(fld), *extra)

    # ---- the start ---------------------------------------------------------------------------------------------
    setup(doc="")
    code, out = run(d, "next", "--phase", "architect")
    for want in ("/architect start", "#Scope (a part built for a Deferred item", "refunds over €50",
                 "answer 1 (team): 'Capacity: solo, 20 h/week", "'€0.05 per conversation'",
                 "## §Architect — the ten agent decisions", "printed at the end of this start",
                 "## Architecture & quality bar", "**Resilience by design**", "status.py rules architect",
                 "`set architect filled --from-fields <file>`", "`status.py fields architect` in the same message",
                 "No ADR on a first run", "never `declined`", "never its `/json` data", "is a warning"):
        if want not in out:
            fails.append(f"next --phase architect should print {want!r} (one start call, P1; #63 fields)")
    # SETUP-10 (2.3 review): "in the call that writes the fields file" read as one chained call (`&&`), which the
    # one-command-per-call rule forbids
    sf = d / "STATUS.md"
    sf.write_text(sf.read_text(encoding="utf-8").replace("UI: yes", "UI: unknown", 1), encoding="utf-8")
    code, ui_out = run(d, "next", "--phase", "architect")
    if "UI unknown" not in ui_out or "in the message that writes the fields file, as its own command before `set`" \
            not in ui_out:
        fails.append("next --phase architect: UI unknown - the flag goes in the fields file's message as its own "
                     "command (SETUP-10)")
    setup(doc="")
    for unwanted in ("(run it now", "## §Step 3b", "## §Re-run semantics", "## §Spine resolution", "open now:",
                     "**Placeholders must FAIL the boot", "This phase closes with, in order", "templates/adr.md",
                     "`## Superseding`", "the one read of", "--section-from"):
        if unwanted in out:
            fails.append(f"next --phase architect should not print {unwanted!r} (P2; #40: no template read, no ADR)")
    if len(out) > ARCH_START_MAX:
        fails.append(f"next --phase architect prints {len(out)} characters on the test project - over "
                     f"{ARCH_START_MAX}: a realistic project's start would pass 25,000 (P47)")
    ag_start_fits(d, "architect", fails)
    code, out = run(d, "fields", "architect")
    for want in ("### <field>", "- decisions", "- cost per use", "- agent", "- plan notes", "- open items",
                 "#### D1.", "Writing rules"):
        if want not in out:
            fails.append(f"`status.py fields architect` should print {want!r} (the fields file's shape, #40 item 9)")
    if "change D<n>" in out or "<!--" in out or len(out) > 11000:
        fails.append(f"`status.py fields architect` on a first run prints no change field, no comment, under 11K "
                     f"({len(out)} chars)")
    # ---- the fields file: rendered, written once, numbered, saved -------------------------------------------------
    before = (d / "PRODUCT.md").read_text(encoding="utf-8")
    code, out = save(ARCH_FIELDS_OK, "--dry-run")
    if code != 0 or "no gap" not in out or (d / "PRODUCT.md").read_text(encoding="utf-8") != before \
            or (d / "docs" / "architecture.md").exists():
        fails.append(f"--from-fields --dry-run should check everything and write nothing: {out[-400:]!r}")
    code, out = save(ARCH_FIELDS_OK)
    doc = (d / "docs" / "architecture.md").read_text(encoding="utf-8") if (d / "docs" / "architecture.md").exists() else ""
    rec = status.product_sections((d / "PRODUCT.md").read_text(encoding="utf-8")).get("Architecture", "")
    if code != 0 or "The rest of the close" not in out or "wrote #Architecture, docs/architecture.md" not in out:
        fails.append(f"a complete fields file should record first time and print the close: {out[-700:]!r}")
    for want in ("## 1. Overview", "## 8. Decisions", "### 8.1 D1. One TypeScript app", "## Appendix A — Owner's "
                 "answers", "### C.1 Framework options", "**Defaults waiting for the owner's confirmation:** D2 · D3",
                 "- **Problem it solves:** one person builds and runs everything", "**External systems, each behind "
                 "an adapter:**", "| Shop orders | order lookup | OrderSource |", "- **Tooling:** hook runner: husky", "type checker: tsc --noEmit",
                 "= $0.06 per conversation"):
        if want not in doc:
            fails.append(f"the rendered docs/architecture.md should hold {want!r}")
    if status.unnumbered_headings(doc):
        fails.append(f"every heading of the rendered document is numbered (#60): {status.unnumbered_headings(doc)}")
    for want in ("D1 One TypeScript app (user-chosen)", "  - Constraint set: team solo, 20 h/week",
                 "dev tooling", "hook runner: husky · secret scanner: gitleaks", "  - Shop orders: OrderSource - 10 s",
                 "(6,000 input tokens × $3 per 1M + 800 output tokens × $15 per 1M) / 1,000,000 = $0.03 per call",
                 "worst case 6 calls = $0.18 per conversation"):
        if want.lower() not in rec.lower():
            fails.append(f"the rendered #Architecture should hold {want!r}: {rec[:300]!r}")
    if doc.count("three tools need no framework") != 1 or "three tools need no framework" in rec:
        fails.append("a decision's reasoning is written once: in docs/architecture.md §Decisions, not in #Architecture "
                     "(#63)")
    if (d / "docs" / "adr").exists() and list((d / "docs" / "adr").glob("*.md")):
        fails.append("a first /architect run writes no ADR file (owner 2026-10-07, #40)")
    if "! the worst case (6 calls, $0.18)" not in out and "not compared" not in out:
        fails.append(f"the cost per use is checked against #Vision's cap by the script (#40 item 14): {out[-500:]!r}")
    # ---- refusals: only what can be counted, every one at once, every file put back ------------------------------
    setup(doc="")
    before = (d / "PRODUCT.md").read_text(encoding="utf-8")
    bad = (ARCH_FIELDS_OK.replace("- login: none: its own accounts\n", "- login: Entra ID\n")
           .replace("the PaaS's auth add-on, email + a magic link — default taken, not user-chosen", "N/A")
           .replace("| nightly eval | CI |", "| nightly eval |  |")
           .replace("| Shop orders | order lookup | OrderSource |", "| Shop orders | order lookup |  |")
           .replace("- revisit: a fourth tool\n", "")
           .replace("- provenance: user-chosen\n\n#### D2", "- provenance: confirmed by the owner\n\n#### D2")
           .replace("| M1 | inbox and agent | D2 |", "| later | inbox and agent | D2 |")
           .replace("- input tokens: 6,000", "- input tokens: lots")
           .replace("### rules\n", "### rulez\n"))
    code, out = save(bad)
    for want in ("no `### rules`", "identity is N/A, but answer 6 (login) is 'Entra ID'",
                 "runtime row 'nightly eval' has no Category", "external 'Shop orders' has no Adapter interface",
                 "D2 has no `- revisit: ...`", "D1 provenance 'confirmed by the owner'",
                 "has no row for M1", "`input tokens: lots` is not a number"):
        if want not in out:
            fails.append(f"set architect filled --from-fields should refuse {want!r} in its one list: {out[-400:]!r}")
    if code == 0 or out.count("REFUSED") != 1 or (d / "PRODUCT.md").read_text(encoding="utf-8") != before \
            or (d / "docs" / "architecture.md").exists():
        fails.append("a refused fields file names every gap in ONE refusal and writes nothing (P20, P45)")
    # #40 item 13: the owner's own words never refuse - "runs on the laptop only" recorded a refusal on a live run
    setup(doc="")
    code, out = save(ARCH_FIELDS_OK.replace("- infrastructure: managed only", "- infrastructure: runs on the laptop only"))
    if code != 0:
        fails.append(f"the owner's own words for answer 3 ('laptop only') must record (#40 item 13): {out[-400:]!r}")
    # #40 items 10-11 + M3: the user's answer wins - the script writes the #Plan note and the open items, in the save
    setup(doc="")
    code, out = save(ARCH_FIELDS_OK + "\n### plan notes\n- M1: answered on the owner's laptop, no web address - because "
                     "answer 3: laptop only\n\n### open items\n- the PaaS price after 2026 | /deploy re-reads the "
                     "pricing page\n")
    plan = status.product_sections((d / "PRODUCT.md").read_text(encoding="utf-8")).get("Plan", "")
    st = status.Status.load(d / "STATUS.md")
    if code != 0 or "— superseded 2026-09-24 by /architect: answered on the owner's laptop" not in plan:
        fails.append(f"a plan note is written by the script on the #Plan line it names (#40 item 10): {out[-300:]!r}")
    if not any("the PaaS price after 2026" in o[3] and not o[5] for o in st.rows["Open items"]):
        fails.append("an open item in the fields file is in STATUS.md when the save commits (#40 item 11)")
    setup(doc="")
    code, out = save(ARCH_FIELDS_OK + "\n### plan notes\n- M9: something - because x\n")
    if code == 0 or "no #Plan line holds 'M9'" not in out:
        fails.append(f"a plan note naming no #Plan line is refused: {out[-300:]!r}")
    # #40 (owner 2026-10-07): an ADR only when a recorded decision CHANGES - written by the script from `### change`
    setup(doc="")
    code, out = save(ARCH_FIELDS_OK)
    changed = ARCH_FIELDS_OK.replace("#### D2. No agent framework, a plain tool loop", "#### D2. Mastra as the agent "
                                     "framework")
    code, out = save(changed)
    if code == 0 or "D2 changed (was 'No agent framework, a plain tool loop'" not in out:
        fails.append(f"a re-run that changes a decision with no `### change D2` is refused (#40): {out[-300:]!r}")
    code, out = save(changed + "\n### change D2\n- was: no agent framework, a plain tool loop\n- now: Mastra as the "
                     "agent framework\n- why: a fourth tool arrived\n- affects: agent/ and its tests\n")
    adrs = sorted((d / "docs" / "adr").glob("*.md")) if (d / "docs" / "adr").exists() else []
    doc = (d / "docs" / "architecture.md").read_text(encoding="utf-8")
    if code != 0 or [p.name for p in adrs] != ["0001-mastra-as-the-agent-framework.md"] \
            or "## What it was" not in adrs[0].read_text(encoding="utf-8") \
            or "- **Superseded:** ADR-0001 (2026-09-24) - was: no agent framework" not in doc:
        fails.append(f"`### change D2` writes ADR-0001 and marks D2 superseded: {[p.name for p in adrs]} "
                     f"{out[-300:]!r}")
    # ---- the legacy --section-from path: a hand-written record still records; prose only warns ------------------
    setup()
    code, out = close(ARCH_OK)
    if code != 0 or "The rest of the close" not in out:
        fails.append(f"a realistic hand-written #Architecture with no ADR files should record: {out[-700:]!r}")
    setup()  # P8: `**Label:**` without the leading "- " reads the same
    code, out = close(re.sub(r"(?m)^- \*\*", "**", ARCH_OK))
    if code != 0:
        fails.append(f"#Architecture fields without the leading '- ' should read the same: {out[-500:]!r}")
    setup()  # #40 item 13: the owner's words for answer 3 are a warning at most
    code, out = close(ARCH_OK.replace("solo, 20 h/week, knows TypeScript; €40 a month for hosting and AI; managed only",
                                      "solo, 20 h/week, knows TypeScript; €40 a month for hosting and AI; runs on the "
                                      "laptop only"))
    if code != 0 or "! the constraint set may have no the infrastructure" not in out:
        fails.append(f"'laptop only' records with a warning, never a refusal (#40 item 13): {out[-400:]!r}")
    setup(ai="no", agent="no")  # no AI: those fields may be N/A
    code, out = close(re.sub(r"(?s)- \*\*\(AI\).*", "- **(AI) prompt-versioning:** N/A - no AI\n- **(Agent):** N/A - "
                                                    "no agent\n", ARCH_OK))
    if code != 0:
        fails.append(f"a product with no AI should record without the AI and agent rows: {out[-400:]!r}")
    setup(doc="")  # "kept:" is the user's decision to keep an older record: not re-checked for the new rules
    code, out = close(re.sub(r"(?m)^  - Constraint set:.*\n", "", ARCH_OK), "--note", "kept: the owner keeps it")
    if code != 0:
        fails.append(f"`set architect filled --note \"kept: ...\"` should record without the new checks: {out[-300:]!r}")
    # a logged Gemini run's shape: counted gaps refuse in ONE list; what reads words rides along as warnings
    setup(doc="# Architecture\n\n## Searches\n- hosting · render · https://render.com\n\n## Framework options\n\n"
              "| Option | Fit |\n|---|---|\n| LangGraph | good |\n| CrewAI | ok |\n| Pydantic AI | ok |\n\n"
              "Confidence: 100%\n")
    bad = ("- **Stack + tools:**\n  - Backend: FastAPI — default taken, confirmed by user\n  - Cache: Redis\n"
           "  - LLM: claude-3-5-haiku-20241022 — VERIFIED (https://docs.anthropic.com)\n"
           "- **Data custody:** Postgres — default taken, not user-chosen\n"
           "- **Runtime target per deployable unit:**\n  - API: Render — user-chosen\n"
           "- **Identity custody:** vendor auth — user-chosen\n- **Dev tooling:** make · ruff · pyproject.toml · "
           "hook runner TBD\n- **Key decisions:** monolith\n"
           "- **Externals behind adapters:**\n  - LLM: the Anthropic SDK called from the service\n"
           "- **Resilience · perf/cost budget · migrations approach:** well under the cap $\\le$ €0.05\n"
           "- **(AI) prompt-versioning · eval harness · tracing:** prompts in code\n"
           "- **(Agent) the ten rows:**\n  1. Framework: LangGraph — user-chosen\n")
    code, out = close(bad)
    for want in ("'default taken, confirmed by user' is not one of the two values", "stamped 2024-10-22",
                 "2 row(s) with no provenance", "no `Constraint set:` row", "VERIFIED with no `evidence:`",
                 "no `## Owner's answers`", "only a homepage", "package registry page",
                 "docs/architecture.md states 100% confidence", "#Architecture has LaTeX",
                 "! the Dev tooling line may name no secret scanner", "(a warning)", "leaves a slot undecided (TBD)",
                 "no category word", "no adapter interface name", "no resilience words", "the perf/cost budget",
                 "prompt-versioning", "the migrations approach", "may set no max_tokens", "no cost per use found",
                 "4 untrusted input", "one of AGENT.md's examples"):
        if want not in out:
            fails.append(f"set architect filled should name {want!r} in its one list: {out[-300:]!r}")
    if code == 0 or out.count("REFUSED") != 1 or out.count("confirmed by user") != 1 or "ADR file" in out:
        fails.append("set architect filled should name every problem in ONE refusal, each once, and ask for no ADR "
                     "(P20, #40)")
    setup()  # the flags are part of the record (flag cannot set unknown back, so the file is edited)
    st = status.Status.load(d / "STATUS.md")
    st.header["UI"], st.header["Agent"] = "unknown", "unknown"
    st.save(d / "STATUS.md")
    code, out = run(d, "next", "--phase", "architect")  # round 1 asks the agent question: a yes needs no 2nd start
    if "applies only if round 1's agent answer is yes" not in out or "## §Architect" not in out:
        fails.append("next --phase architect on an AI product with Agent unknown should print AGENT.md §Architect, "
                     "marked as applying on a yes")
    code, out = close(ARCH_OK)
    if code == 0 or "the UI answer is not recorded" not in out or "the Agent answer is not recorded" not in out:
        fails.append(f"set architect filled should refuse unknown UI and Agent flags: {out[-300:]!r}")
    setup(doc="# Architecture\n\n## Owner's answers\n\n1. \"just me\"\n\n## Search list\n\n- runtime · PaaS "
              "pricing · settled the plan\n\n## Framework options\n\n| Option | Fits |\n|---|---|\n| VoltAgent | yes |\n")
    code, out = close(ARCH_OK.replace("the PaaS's auth add-on, email + a magic link — default taken, not user-chosen", "")
                      + "- **Read (file · date · verbatim quote):** docs/architecture.md · 2026-09-24 · \"just me\"\n")
    for want in ("#Architecture field empty: Identity custody", "quotes docs/architecture.md, which this phase wrote",
                 "search line(s) with no link", "no framework table of 3-4 options"):
        if want not in out:
            fails.append(f"set architect filled should refuse {want!r}: {out[-300:]!r}")
    setup(doc="")
    code, out = close(ARCH_OK)
    if code == 0 or "no docs/architecture.md - write the fields file" not in out:
        fails.append(f"set architect filled should refuse a run with no docs/architecture.md: {out[-300:]!r}")
    # owner 2026-10-05 + #60: the document's shape, numbered headings accepted by every parser
    reader, appendix = ARCH_DOC_OK.split("---\n\n## Appendix A")
    numbered = ARCH_DOC_OK
    for n, name in enumerate(("Overview", "What drives the design", "Rules the code must keep",
                              "How it works, step by step", "Building blocks", "Data", "Conventions and terms",
                              "Decisions", "Security and privacy", "AI part", "Running it", "Mapping to the plan",
                              "Risks and open questions"), 1):
        numbered = numbered.replace(f"\n## {name}\n", f"\n## {n}. {name}\n")
    numbered = numbered.replace("### D1.", "### 8.1 D1.").replace("### D2.", "### 8.2 D2.")
    setup(doc=numbered)
    code, out = close(ARCH_OK)
    if code != 0:
        fails.append(f"a docs/architecture.md with numbered headings (#60) should record: {out[-400:]!r}")
    if status.structure_blocks(d) != ["`inbox/` messages and approvals", "`agent/` drafting"]:
        fails.append(f"/structure reads the numbered `## 5. Building blocks`: {status.structure_blocks(d)}")
    for what, doc, want in (
            ("no Overview", ARCH_DOC_OK.replace("## Overview", "## Summary"), "missing section(s) of the template: Overview"),
            ("no diagram", ARCH_DOC_OK.replace("```mermaid\nflowchart", "```text\nflowchart"),
             "`## Overview` has no ```mermaid"),
            ("no flow diagram", ARCH_DOC_OK.replace("```mermaid\nsequenceDiagram", "```text\nsequenceDiagram"),
             "`## How it works, step by step` has no ```mermaid"),
            ("no Decisions", ARCH_DOC_OK.replace("## Decisions", "## Choices"), "missing section(s) of the template: Decisions"),
            ("workings first", "# Architecture\n\n## Appendix A" + appendix + reader.replace("# Architecture", ""),
             "out of the template's order"),
            ("no MUST rule", ARCH_DOC_OK.replace("The agent NEVER changes", "The agent does not change"),
             "has no R# rule written with MUST or NEVER"),
            ("a comment left", ARCH_DOC_OK.replace("## Data\n", "## Data\n\n<!-- The main entities -->\n"),
             "still holds template comments"),
            ("a milestone with no home", ARCH_DOC_OK.replace("| M1 | inbox and agent | D2 |", "| later | x | D2 |"),
             "`## Mapping to the plan` has no row for M1"),
            ("a superseded decision with no ADR file", ARCH_DOC_OK.replace(
                "- **Revisit when:** a fourth tool.", "- **Revisit when:** a fourth tool.\n- **Superseded:** ADR-0007 "
                "(2026-09-20) - was: Mastra"), "superseded by ADR-0007, but docs/adr/0007-*.md is missing")):
        setup(doc=doc)
        code, out = close(ARCH_OK)
        if code == 0 or want not in out:
            fails.append(f"set architect filled should refuse a docs/architecture.md with {what} (A5): {out[-300:]!r}")
    setup(doc=ARCH_DOC_OK.replace("**Out of scope for this architecture:**", "**Out of scope:** " + " ".join(
        f"a{i}/b{i}/c{i}" for i in range(11))))
    code, out = close(ARCH_OK)
    if code != 0 or "is written in shorthand: 11" not in out:
        fails.append(f"shorthand reads prose: a warning, never a refusal (2.3): {out[-300:]!r}")
    for what, body in (  # false refusals of logged runs (P42): each must record
            ("a plain acronym-led interface name", ARCH_OK.replace("`LLMProvider` - timeout", "LLMProvider - timeout")),
            ("a plain AIClient", ARCH_OK.replace("`LLMProvider` - timeout", "AIClient - timeout")),
            ("a labelled N/A external", ARCH_OK.replace("  - Shop orders:", "  - Third-party approval gate: N/A — the "
                                                        "pilot uses fake data, default taken, not user-chosen\n"
                                                        "  - Shop orders:")),
            ("a later-host row of the same unit", ARCH_OK.replace(
                "  | nightly eval |", "  | from M2, Render in Frankfurt | €9 a month, no free tier | default taken, "
                                     "not user-chosen |\n  | nightly eval |")),
            ("an external with no interface name (a warning now)",
             ARCH_OK.replace("`LLMProvider` - timeout", "the llm client - timeout")),
            ("a brand-only runtime row (a warning now)",
             ARCH_OK.replace("  | web app + API | PaaS container, EU region |", "  | web app + API | Render |"))):
        setup()
        code, out = close(body)
        if code != 0:
            fails.append(f"set architect filled should record {what}: {out[-400:]!r}")
    setup()  # A1 on the legacy path reads #Scope's words: a warning (on the fields path, answer 6 decides: a refusal)
    (d / "PRODUCT.md").write_text(ARCH_SPINE.replace("  - prompt injection: in now\n", "  - prompt injection: in "
                                  "now\n  - password reset: N/A - shop staff use the company login\n"), encoding="utf-8")
    code, out = close(ARCH_OK.replace("the PaaS's auth add-on, email + a magic link — default taken, not user-chosen",
                                      "N/A - no accounts of our own — default taken, not user-chosen"))
    if code != 0 or "! Identity custody is N/A, but #Scope says" not in out:
        fails.append(f"identity N/A while #Scope names the company login warns on the legacy path (A1): {out[-300:]!r}")
    # P46: the dry-run before the document points at the fields file and asks for no ADR
    setup(doc="")
    before = (d / "PRODUCT.md").read_text(encoding="utf-8")
    code, out = close(ARCH_OK, "--dry-run")
    for want in ("no gap", "is not written yet", "--from-fields <file>", "no ADR files", "The save refuses:"):
        if want not in out:
            fails.append(f"set architect filled --dry-run before the document should print {want!r}: {out[-300:]!r}")
    if code != 0 or "no docs/architecture.md" in out or (d / "PRODUCT.md").read_text(encoding="utf-8") != before:
        fails.append(f"a dry-run before the document neither refuses its absence nor writes (P46): {out[-300:]!r}")
    setup()  # N5: a cost per use with no working is a WARNING (owner 2026-10-04)
    code, out = close(ARCH_OK.replace("~6k input tokens × $3/1M + 800 output tokens × $15/1M ≈", "about"))
    if code != 0 or "! the cost per use shows no working" not in out or "a warning, not a refusal" not in out:
        fails.append(f"a cost per use with no tokens × price should record with a warning (N5): {out[-400:]!r}")
    setup()
    code, out = close(ARCH_OK)
    if "shows no working" in out:
        fails.append("a cost per use that shows its working should get no N5 warning")
    big = status.big_sections("## Architecture\n" + ("- **Stack:** " + "x" * 200 + "\n") * 60)
    if not big or "over 8 KB" in big[0] or "not a cap" not in big[0]:
        fails.append(f"the size signal names no cap (the template says no byte cap): {big!r}")
    saved = status.close_steps_text("architect", 'saved: commit b1ad62b "x" (7 file(s))')
    if "its first line: `Saved (commit b1ad62b).`" not in saved or "Saved (commit" in status.close_steps_text("architect"):
        fails.append("the close leads with `Saved (commit <hash>).` only when set saved (A6)")
    # SETUP-1 (2.3 review): the close's step 3 said "ask which wins" to phases whose skill says ask nothing and
    # never edit an earlier phase's record - a model following the printed line edited #Architecture
    for ph in ("structure", "foundation", "contracts", "design-system"):
        step3 = " ".join(status.close_steps_text(ph).split())
        if "ask which wins" in step3 or "ask nothing, never edit an earlier phase's record" not in step3 or                 f"status.py open --from {ph} --what" not in step3:
            fails.append(f"/{ph}'s close step 3 should record a clash as an open item, ask nothing (SETUP-1)")
    if "ask which wins" not in status.close_steps_text("architect"):
        fails.append("/architect's close step 3 still asks which side wins")
    agent_md = (ROOT / "references" / "agent.md").read_text(encoding="utf-8").lower()
    gone = [x for x in status.AGENT_EXAMPLES if x not in agent_md]
    if gone:
        fails.append(f"status.AGENT_EXAMPLES names frameworks AGENT.md no longer lists: {gone} - keep the two in step")
    tpl = status.product_sections((ROOT / "templates" / "PRODUCT.md").read_text(encoding="utf-8")).get("Architecture", "")
    lost = [k for k, v in status.ARCH_LABELS.items() if f"- **{v}:**" not in tpl]
    if lost:
        fails.append(f"status.ARCH_LABELS and templates/PRODUCT.md#Architecture differ for {lost} - keep them in step")
    src.unlink(missing_ok=True)
    fld.unlink(missing_ok=True)


def test_shared_fixes_68(fails: list[str]) -> None:
    """next.68 shared bugs. SKIP_DIRS was assigned twice - the second (three names) won, so every walk entered
    .git, .venv and the installed playbook (.agents/), and a check looking for a project file by name found the
    playbook's copy. a table row written inside a bullet or a quote (`- | ... |`) was warned 'split it into
    sub-bullets or a table' - a warning reflow cannot satisfy and a rewrite it invites."""
    for name in (".git", ".venv", ".agents", ".claude", ".cursor", ".codex", ".gemini", "node_modules", "__pycache__"):
        if name not in status.SKIP_DIRS:
            fails.append(f"SKIP_DIRS should hold {name!r} (one definition, used everywhere): {sorted(status.SKIP_DIRS)}")
    src = (ROOT / "tools" / "status.py").read_text(encoding="utf-8")
    if len(re.findall(r"(?m)^SKIP_DIRS\s*=", src)) != 1:
        fails.append("SKIP_DIRS is assigned more than once in status.py - the last one silently wins")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        for rel in (".agents/skills/structure/check_structure.py", ".venv/lib/site-packages/x/models.py"):
            (d / rel).parent.mkdir(parents=True)
            (d / rel).write_text("x = 1\n", encoding="utf-8")
        if status.find_in_project(d, "check_structure.py") is not None:
            fails.append("find_in_project found the installed playbook's check_structure.py under .agents/")
        if any(".venv" in p.parts or ".agents" in p.parts for p in status.project_files(d)):
            fails.append("project_files walked .venv or .agents")
    row = "| " + " | ".join(["cell text"] * 40) + " |"
    for line in (row, "  " + row, "- " + row, "> " + row, "  - " + row):
        if status.long_lines(f"# P\n\n## Architecture\n{line}\n"):
            fails.append(f"a table row was warned as a long line (reflow cannot wrap it): {line[:12]!r}...")
        body, n = status.reflow(line + "\n")
        if n or body.strip() != line.strip():
            fails.append(f"reflow rewrote a table row: {line[:12]!r}...")
    if not status.long_lines("# P\n\n## Vision\n- **Value proposition:** " + "word " * 80 + "\n"):
        fails.append("a long bullet should still be warned")


SAVE_TURN = re.compile(r"(?i)save this version|looks good - (write and )?save|don't save yet|open the PR and save")


def test_no_save_turn_left(fails: list[str]) -> None:
    """2.1 (#62): a 17-phase run needed 58 owner turns vs plain's 27, the save question the biggest cause. No printed
    text and no skill, reference or template may ask it again."""
    files = [ROOT / "tools" / "status.py", *sorted((ROOT / "commands").rglob("*.md")),
             *sorted((ROOT / "references").rglob("*.md"))]
    for f in files:
        for i, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if SAVE_TURN.search(ln):
                fails.append(f"{f.relative_to(ROOT).as_posix()}:{i} still asks a separate save question: {ln.strip()[:140]}")
    if tuple(status.AUTO_SAVE) != tuple(status.CHAIN):
        fails.append(f"every phase saves unasked (#62), AUTO_SAVE is {status.AUTO_SAVE}")
    text = status.close_steps_text("scope", None) + status.close_steps_text("scope", "saved: commit abc1234 \"x\"")
    if "Change anything? If not:" not in text or SAVE_TURN.search(text) or "Saved (commit abc1234)." not in text:
        fails.append(f"the close should end with \"Change anything?\" and never ask to save: {text[-600:]}")


def git_repo(d: Path) -> None:
    for c in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *c], cwd=d, capture_output=True)


def git_head(d: Path) -> str:
    return subprocess.run(["git", "log", "-1", "--format=%s"], cwd=d, capture_output=True, text=True).stdout.strip()


def test_every_phase_saves_unasked(fails: list[str]) -> None:
    """2.1 (#62): `set <phase> filled` saves for every phase (it was /dev-check and /test only); `--no-commit` records
    without saving; `release` saves without --commit."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        git_repo(d)
        fresh(d, ui="no")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=d, capture_output=True)
        for ph in ("vision", "scope", "plan", "architect", "structure", "foundation", "contracts", "tickets", "deploy",
                   "learn"):
            code, out = run(d, "set", ph, "filled")
            if code != 0 or "saved: commit" not in out or not git_head(d).startswith(f"{ph}: recorded"):
                fails.append(f"`set {ph} filled` should save unasked: {git_head(d)!r} / {out.strip()[:300]}")
            if SAVE_TURN.search(out) or "ask \"Save" in out:
                fails.append(f"`set {ph} filled` printed a save question: {out.strip()[-400:]}")
        code, out = run(d, "set", "eval", "filled", "--verdict", "fail")
        if "saved: commit" not in out or not git_head(d).startswith("eval: FAIL"):
            fails.append(f"`set eval filled --verdict fail` should save unasked: {git_head(d)!r}")
        before = git_head(d)
        code, out = run(d, "set", "scope", "filled", "--no-commit")
        if code != 0 or "saved: commit" in out or git_head(d) != before or "Not saved." not in out:
            fails.append(f"`--no-commit` should record without saving and the close say Not saved: {out.strip()[-400:]}")
        real = status.ship_release_gaps
        status.ship_release_gaps = lambda *a: []
        try:
            code, out = run(d, "release", "--what", "M1-A-01: orders", "--reviews", "R1 clean", "--skipped", "none",
                            "--docs", "README", "--record", "CHANGELOG.md", "--rollback", "revert", "--pr", "#7")
        finally:
            status.ship_release_gaps = real
        if code != 0 or "saved: commit" not in out or not git_head(d).startswith("ship: recorded - release record"):
            fails.append(f"`release` should save without --commit: {git_head(d)!r} / {out.strip()[:400]}")


def milestone_project(d: Path, built: tuple[str, ...], released: tuple[str, ...] = ()) -> None:
    """A git project mid-milestone: TICKETS.md with M1 = 3 tickets, `built` recorded and committed, `released` named
    in a release row; /dev-check filled FAIL."""
    git_repo(d)
    fresh(d, ui="no")
    (d / "TICKETS.md").write_text("# Tickets\n\n## M1 core\n| `M1-A-01` | a |\n| `M1-A-02` | b |\n| `M1-A-03` | c |\n",
                                  encoding="utf-8")
    st = status.Status.load(d / "STATUS.md")
    for r in st.rows["Phases"]:
        if status.CHAIN.index(r[0]) < status.CHAIN.index("build"):
            r[1:6] = ["filled", TODAY, "", "", ""]
    for tid in built:
        st.rows["Tickets"].append([tid, TODAY, "yes", "pytest -> 1 passed", "1", "R1 clean", f"docs/{tid}.md"])
    for tid in released:
        st.rows["Releases"].append([TODAY, f"{tid}: a part", "R1 clean", "none", "README", "CHANGELOG.md", "revert",
                                    "#9"])
    dc = next(r for r in st.rows["Phases"] if r[0] == "dev-check")
    dc[1:6] = ["filled", TODAY, "", "fail", ""]
    st.save(d / "STATUS.md")
    subprocess.run(["git", "add", "-A"], cwd=d)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=d, capture_output=True)


def test_gate_cascade(fails: list[str]) -> None:
    """2.1 (#62): /dev-check FAIL that only means "the milestone isn't finished" is one printed line and an override
    recorded with a fixed reason - no question; any other unpassed gate is ONE options question, never a typed reason;
    a bypass of a gate that holds a FAIL is accepted (a logged run could not record one)."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        milestone_project(d, ("M1-A-01",), ("M1-A-01",))
        for ph in ("test", "eval", "deploy"):
            code, out = run(d, "next", "--phase", ph)
            gate = "\n".join(ln for ln in out.splitlines() if "dev-check" in ln.lower())
            if "/dev-check says M1 isn't finished (1 of 3 tickets)" not in gate \
                    or re.search(r"own words|their words|bypass --from", gate):
                fails.append(f"the /{ph} start should print the one milestone line, no reason question: {gate[:1500]}")
        code, out = run(d, "set", "eval", "filled", "--verdict", "fail")
        items = [o for o in status.Status.load(d / "STATUS.md").rows["Open items"] if not o[5]]
        if code != 0 or "recorded as an override, no question" not in out or len(items) != 1 \
                or status.MILESTONE_REASON not in items[0][3]:
            fails.append(f"`set eval` mid-milestone should record the override with the fixed reason: {items} / "
                         f"{out.strip()[:400]}")
        run(d, "set", "learn", "filled")
        if len([o for o in status.Status.load(d / "STATUS.md").rows["Open items"] if not o[5]]) != 1:
            fails.append("the milestone override is recorded once, not once per phase")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        milestone_project(d, ("M1-A-01", "M1-A-02", "M1-A-03"), ("M1-A-01", "M1-A-02", "M1-A-03"))
        code, out = run(d, "next", "--phase", "eval")
        gate = "\n".join(ln for ln in out.splitlines() if "dev-check" in ln.lower())
        if "isn't finished" in gate or "Stop - run /dev-check first (Recommended)" not in gate \
                or "Proceed anyway (reason: /dev-check not passed - the user chose to go on)" not in gate \
                or re.search(r"own words|their words", gate):
            fails.append(f"a /dev-check FAIL with every ticket built and merged should ask ONE options question: "
                         f"{gate[:1500]}")
        code, out = run(d, "bypass", "--from", "eval", "--gate", "dev-check", "--reason",
                        status.gate_proceed_reason("dev-check"))
        if code != 0 or "proceeds with /dev-check bypassed" not in out:
            fails.append(f"a bypass of a gate that holds a FAIL should be accepted: {out.strip()[:300]}")


HUNT_CODE = {  # one file per defect a plain /test found and the playbook's checklist did not (#48 2026-10-08)
    "app/ids.py": "import re\n\nCUSTOMER = re.compile(r\"^C\\d{5}$\")\n",
    "app/health.py": "def health():\n    return {'status': 'ok'}\n",
    "app/migrate.py": "def migrate(conn):\n    version = conn.schema_version()\n",
    "app/store.py": "def connect(url):\n    conn = open(url)\n    conn.setup()\n    return conn\n",
    "app/logjson.py": "def record(event, **extra):\n    out = {'event': event}\n    out.update(extra)\n    return out\n",
    "app/seed_population.py": "import random\n\ndef customers(n, seed=1):\n    return [random.Random(seed).random()]\n",
    "app/lint_runner.py": "import subprocess\n\ndef lint():\n    return subprocess.run([\"ruff\", \"check\", \".\"])\n",
}


def test_defect_hunt_and_eval_design_check(fails: list[str]) -> None:
    """#48 items 2-5 and #49 items 1 and 4. /test's start lists the defect probes with the files each applies to, the
    generated-data hash pin, the command-line tools to fake and the one per-edit command; `set test filled` warns
    (never refuses) when #Tests names no defect hunt. /eval mid-milestone offers the measures check (Recommended)
    instead of a bare stop, and a recorded decline saves."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        milestone_project(d, ("M1-A-01",), ("M1-A-01",))
        for rel, text in {**HUNT_CODE, "pyproject.toml": "[project]\nname = 'x'\n", "uv.lock": ""}.items():
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text(text, encoding="utf-8")
        code, out = run(d, "next", "--phase", "test")
        hunt = out[out.find("Defect hunt -"):]
        for want in ("Defect hunt -", "leap day", "non-ASCII digits", "here: app/ids.py", "here: app/health.py",
                     "here: app/migrate.py", "here: app/store.py", "here: app/logjson.py", "`Defect hunt:`",
                     "Generated data - app/seed_population.py", "pins it", "app/lint_runner.py (ruff)",
                     "recording fake", "run only `uv run pytest <the test file> -q`"):
            if want not in out:
                fails.append(f"the /test start should carry {want!r}: {hunt[:1500]}")
        # red: the ASCII flag clears the digit probe, a hashing test clears the pin, no shell-out clears the tools
        code_ = [("app/ids.py", "import re\nX = re.compile(r\"\\d+\", re.ASCII)\n")]
        text = "\n".join(status.test_hunt_text(code_, ""))
        if "non-ASCII digits" in text or "Generated data" in text or "Command-line tools" in text:
            fails.append(f"the hunt should list only the probes the code shows: {text[:600]}")
        text = "\n".join(status.test_hunt_text([("app/seed_population.py", "x = 1\n")], "import hashlib\n"))
        if "already hashes an output" not in text:
            fails.append(f"a test that already hashes an output should be named, not asked for again: {text[:400]}")
        body = ("- **Live-path verified:** /healthz 200 (tests/test_live.py)\n- **Adversarial/security:** forged token "
                "401\n- **Regression:** #2 xfail\n")
        prod = (ROOT / "templates" / "PRODUCT.md").read_text(encoding="utf-8")
        (d / "PRODUCT.md").write_text(status.replace_section(prod, "Tests", body), encoding="utf-8")
        for ph in ("structure", "design-system", "foundation", "contracts", "tickets"):  # tested in their own files
            run(d, "open", "--from", "test", "--what", f"Override: #{ph}'s check fails - a fixture", "--clears",
                f"#{ph}'s check passes")
        code, out = run(d, "set", "test", "filled", "--verdict", "fail", "--no-commit")
        if code != 0 or "no `Defect hunt:` line" not in out or "a warning, not a refusal" not in out:
            fails.append(f"#Tests with no defect hunt should record with a warning: {code} {out.strip()[:500]}")
        (d / "PRODUCT.md").write_text(status.replace_section(prod, "Tests", body + "- **Defect hunt:** 6 probes, "
                                                             "1 bug (#7 xfail)\n"), encoding="utf-8")
        code, out = run(d, "set", "test", "filled", "--verdict", "fail", "--no-commit")
        if code != 0 or "Defect hunt:` line" in out:
            fails.append(f"#Tests naming its defect hunt should record with no warning: {out.strip()[:400]}")
        # /eval before the features exist: the measures check is the recommended option, not a bare stop
        code, out = run(d, "next", "--phase", "eval")
        for want in ("Check the measures and the test data now (Recommended)", "Stop and record why",
                     "Can each target fail AND pass?", "Is every target set?", "Hard negatives", "Scale:",
                     "## Design check", "set eval declined"):
            if want not in out:
                fails.append(f"the /eval start mid-milestone should carry {want!r}: {out[:1500]}")
        if "Stop - run /test first (Recommended)" in out:
            fails.append("the /eval start mid-milestone should ask the measures question only, not the gate question")
        (d / "docs").mkdir(exist_ok=True)
        (d / "docs" / "evaluation.md").write_text("# Evaluation\n\n## Design check\n\n1. none\n", encoding="utf-8")
        code, out = run(d, "set", "eval", "declined", "--reason", "features not built - measures checked: 1 finding "
                        "in docs/evaluation.md", "--gate", "dev-check")
        if code != 0 or "saved: commit" not in out or not git_head(d).startswith("eval: declined - features not built"):
            fails.append(f"a recorded decline should save like a filled record: {git_head(d)!r} / {out.strip()[:400]}")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        milestone_project(d, ("M1-A-01", "M1-A-02", "M1-A-03"), ("M1-A-01", "M1-A-02", "M1-A-03"))
        code, out = run(d, "next", "--phase", "eval")
        if "Check the measures and the test data now" in out:
            fails.append("every ticket built: /eval measures, the measures check is not offered")


def test_next_after_build(fails: list[str]) -> None:
    """2.1 (#62): after one built ticket the next step is /ship <ticket>, not /dev-check; after its PR, merge it and
    /build the next ticket; every ticket built and shipped -> /dev-check."""
    for built, released, want in ((("M1-A-01",), (), "Next: /ship M1-A-01 - built, not shipped yet"),
                                  (("M1-A-01",), ("M1-A-01",), "Next: /build M1-A-02 - merge the shipped PR first"),
                                  (("M1-A-01", "M1-A-02", "M1-A-03"), ("M1-A-01", "M1-A-02", "M1-A-03"),
                                   "Next: /dev-check")):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            milestone_project(d, built, released)
            st = status.Status.load(d / "STATUS.md")
            dc = next(r for r in st.rows["Phases"] if r[0] == "dev-check")
            dc[1:6] = ["empty", "", "", "", ""]
            st.save(d / "STATUS.md")
            code, out = run(d, "show")
            if want not in out:
                fails.append(f"{len(built)} built / {len(released)} shipped: `show` should print {want!r}: "
                             f"{[ln for ln in out.splitlines() if ln.startswith('Next:')]}")
            if built == ("M1-A-01",) and not released:
                card = status.handoff_card(status.Status.load(d / "STATUS.md"), "build")
                if not re.search(r"type: /\S*ship M1-A-01", card):
                    fails.append(f"the /build close should hand off to /ship M1-A-01: {card}")


def test_derived_note(fails: list[str]) -> None:
    """2.1 (owner): `set tickets filled` writes a static Note on the build and ship rows once - never a count; a ticket
    recorded later leaves STATUS.md unchanged."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        fresh(d, ui="no")
        run(d, "set", "tickets", "filled", "--no-commit")
        text = (d / "STATUS.md").read_text(encoding="utf-8")
        for ph, note in status.DERIVED_NOTE.items():
            if not re.search(rf"^\| {ph} \| empty \|[^\n]*{re.escape(note)}", text, re.M):
                fails.append(f"the {ph} row should read state empty with the Note {note!r}: "
                             f"{[ln for ln in text.splitlines() if ln.startswith(f'| {ph} ')]}")
        run(d, "set", "tickets", "filled", "--no-commit")
        again = (d / "STATUS.md").read_text(encoding="utf-8")
        if again.count(status.DERIVED_NOTE["build"]) != 1:
            fails.append("the build Note should be written once, not appended again")
        st = status.Status.load(d / "STATUS.md")
        st.rows["Tickets"].append(["M1-A-01", TODAY, "yes", "pytest -> 1 passed", "1", "R1 clean", "docs/a.md"])
        st.save(d / "STATUS.md")
        if (d / "STATUS.md").read_text(encoding="utf-8") != again:
            fails.append("a ticket recorded after /tickets edited STATUS.md - two branches would conflict on it")



def main() -> int:
    for stream in (sys.stdout, sys.stderr):  # a failure message quoting status.py output may hold ≤ or →
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    fails: list[str] = []
    test_table_matches_state_model(fails)
    test_environment_gaps(fails)
    test_team_safe(fails)
    test_engine_protection(fails)
    test_questions_name_no_product(fails)
    test_demo_proof_checks(fails)
    test_dev_check_gate(fails)
    test_dev_check_close(fails)
    test_dev_check_milestone(fails)
    test_dev_check_security_receipt(fails)
    test_verify_phases_24(fails)
    test_lean_mode(fails)
    test_test_record_in_few_calls(fails)
    test_test_close_first_try(fails)
    test_decided_locally(fails)
    test_tickets_checks(fails)
    test_build_ticket_checks(fails)
    test_route(fails)
    test_next65_save(fails)
    test_no_save_turn_left(fails)
    test_every_phase_saves_unasked(fails)
    test_gate_cascade(fails)
    test_defect_hunt_and_eval_design_check(fails)
    test_next_after_build(fails)
    test_derived_note(fails)
    test_early_doc_warnings(fails)
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        test_every_transition(d, fails)
        test_required_details(d, fails)
        test_running_closes_only_on_a_result(d, fails)
        test_caps_and_pipes(d, fails)
        test_next(d, fails)
        test_verdicts_and_tickets(d, fails)
        test_bypass(d, fails)
        test_migrate(d, fails)
        test_cli(d, fails)
        test_git_bash_path_rewrite(d, fails)
        test_how_lists_every_command(d, fails)
        test_agent_trial_fixes(d, fails)
        test_agent_flag(d, fails)
        test_rules_version_and_rerun(d, fails)
        test_provenance_values(d, fails)
        test_phase_runs_its_own_checks(d, fails)
        test_receipts_and_latex(d, fails)
        test_guesses_get_the_answer(d, fails)
        test_override_carries(d, fails)
        test_long_lines_warned(d, fails)
        test_vision_close(d, fails)
        test_scope_close(d, fails)
        test_sections_and_phase_rules(d, fails)
        test_playbook_receipts(d, fails)
        test_evidence_and_foundation_checks(d, fails)
        test_contracts_checks(d, fails)
        test_contracts_close(d, fails)
        test_plan_a_items(d, fails)
        test_plan_close(d, fails)
        test_architect_close(d, fails)
        test_next26_items(d, fails)
    for f in fails:
        print(f"  x {f}")
    print("OK - status.py behaves" if not fails else f"FAIL - {len(fails)} status.py test(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
