"""tools/test_support_v2.py - the 2.0 alignment pass of /playbook, /validate, /drift-check, /adopt, /frontend-audit and
/new-component (P1, P2, P17, P20, P25, P37, P41, P43, P44, P45).

Each skill gets ONE start command that prints what its first step needs, and - where it writes a record - a close
checked in code (every problem in one refusal, `--dry-run` writes nothing). No saved run of these skills on the
current test project exists (P17), so each close is replayed on the record a model would realistically write for a
real project: the good record must pass the first time, a broken copy must be refused in ONE list naming each fault.
Each check here was shown red first (break exactly what it checks, watch it fail, restore).
Run: python tools/test_support_v2.py   (check.py runs it)
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import status  # noqa: E402

TODAY = "2026-10-06"
STATUS_PY = str(ROOT / "tools" / "status.py")


def run(d: Path, *args: str, env: dict | None = None) -> tuple[int, str]:
    e = {**os.environ, "PYTHONIOENCODING": "utf-8", **(env or {})}
    p = subprocess.run([sys.executable, STATUS_PY, "--today", TODAY, *args], cwd=d, capture_output=True,
                       encoding="utf-8", errors="replace", env=e)
    return p.returncode, p.stdout + p.stderr


def skill(name: str) -> str:
    return (ROOT / "commands" / name / "SKILL.md").read_text(encoding="utf-8")


def git_init(d: Path) -> None:
    for args in (["init", "-q"], ["config", "user.email", "t@example.com"], ["config", "user.name", "t"]):
        subprocess.run(["git", *args], cwd=d, capture_output=True)


# ---- /playbook ------------------------------------------------------------------------------------------------------
def test_playbook(fails: list[str]) -> None:
    """`route` keeps its facts at the end (Antigravity shows only the last ~4 KB of an output, and route's 4.6 KB put
    Where/Next at the top, the part it cuts) and lists every skill in the 2.0 order from one table (P41); the skill
    shows that list instead of re-typing it, and ends a phase with the line the phase's close printed - no second
    `route` call after it (a single-command turn re-sends the whole conversation, L1)."""
    names = sorted(p.name for p in (ROOT / "commands").iterdir() if (p / "SKILL.md").is_file())
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        code, out = run(d, "route")
        tail = out[-3500:]
        if code or "Next: /vision" not in tail or "Where: a fresh start" not in tail:
            fails.append(f"route's Where/Next lines are not in its last 3.5 KB (a tool that cuts the top loses "
                         f"them): {out[:200]!r}")
        mapped = re.findall(r"(?<![\w:])/([a-z][a-z-]+)\b", out[out.find("Skills"):] if "Skills" in out else "")
        order = list(dict.fromkeys(m for m in mapped if m in names))
        if sorted(order) != names:
            fails.append(f"route's skill list misses {sorted(set(names) - set(order))} - every skill, one source")
        chain = [c for c in order if c in status.CHAIN]
        if chain != [c for c in status.CHAIN if c in chain]:
            fails.append(f"route lists the chain phases out of order: {chain}")
    text = skill("playbook")
    step1 = re.search(r"^## Step 1\b(.*?)^## ", text, re.M | re.S)
    if step1 and re.search(r"vision → scope → plan", step1.group(1)):
        fails.append("/playbook Step 1 re-types the map - show route's `Skills` lines (one source, P41)")
    if re.search(r"Run `status.py route` once more", text):
        fails.append("/playbook runs `route` again after a phase's close - the close already printed the "
                     "`Open a NEW conversation` line (an extra call re-sends the finished phase)")
    if not re.search(r"(?i)\bmust not\b", text):
        fails.append("/playbook does not say what it must NOT do (P44)")


# ---- /validate ------------------------------------------------------------------------------------------------------
# The record a model would realistically write for the walk-in waitlist test_status.py's #Vision describes (riskiest
# assumption: guests answer a text): a hand-run trial at two restaurants, due in two weeks, the bar dated before it.
VAL_LABELS = ("- **Assumption under test (falsifiable: <user> will <behaviour> because <reason>):** ",
              "- **Experiment (type · who it reaches · time box · due date):** ",
              "- **Pass/fail threshold (written BEFORE the result):** ",
              "- **Measured result (number / quoted evidence · date · raw notes in docs/validation/):** ",
              "- **Verdict (proceed / pivot / kill) + one-line reason:** ")
VAL_BET = ("Walk-in guests at small restaurants will reply to a text and come back to the door when it says their "
           "table is ready, because they would rather wait nearby than stand at the door.")
VAL_TEST = ("concierge test (rung 4): the host texts walk-ins by hand from a shared phone on 3 Friday evenings at 2 "
            "restaurants on one street, 2026-10-09 → 2026-10-23, due 2026-10-24.")
VAL_BAR = ("set 2026-10-06: at least 60% of the parties texted come back within 10 minutes, over at least 30 parties; "
           "each party is one dated row in the host's sheet (party name; time texted; time back), so every count is "
           "tied to one party.")
VAL_TAIL = ("- **If the user overrode this gate · what stays untested, checked against #Vision** (the state itself: "
            "`status.py set validate overridden`): not overridden\n"
            "- **Detail:** `docs/validation.md` (reasoning + workings; this section stays a RECORD)\n")


def val_record(bet=VAL_BET, test=VAL_TEST, bar=VAL_BAR, result="PENDING - due 2026-10-24", verdict="PENDING") -> str:
    return "".join(l + v + "\n" for l, v in zip(VAL_LABELS, (bet, test, bar, result, verdict))) + VAL_TAIL


VAL_RESULT = ("34 parties texted, 23 came back within 10 minutes (68%) · 2026-10-23 · raw notes in "
              "`docs/validation/2026-10-23-friday-texts.md`")
VAL_VERDICT = "proceed - 68% is above the 60% bar on 34 parties; one restaurant's guests came back faster than the other's"


def val_heading(d: Path) -> None:
    """The template's spine has `## Validation` between #Vision and #Scope; test_status.py's fixture leaves it out."""
    p = d / "PRODUCT.md"
    p.write_text(p.read_text(encoding="utf-8").replace("\n## Scope", "\n## Validation\n\n## Scope"), encoding="utf-8")


def test_validate(fails: list[str]) -> None:
    """/validate: `next --phase validate` prints what the experiment tests and the two rounds; `set validate
    running|filled|overridden --section-from` refuses findings E and G, a bar dated after its result, a re-run that
    drops the earlier entry and an override that blanks a field - every problem in one list; the realistic record
    passes the first time."""
    import test_status as ts
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "proj"
        d.mkdir()
        ts.scope_ready(d)
        val_heading(d)
        git_init(d)
        (d / "docs" / "validation.md").write_text("# Validation\n\n## In short\n\nWe test whether guests answer a "
                                                  "text within 10 minutes. The bar is 60% of 34 parties.\n\n"
                                                  "Why a hand-run trial.\n\n## Owner's answers\n\n"
                                                  "1. Guests answer a text.\n", encoding="utf-8")
        src = Path(t) / "validation-section.md"

        def rec(body: str, state: str, *extra: str) -> tuple[int, str]:
            src.write_text(body, encoding="utf-8")
            return ts.run(d, "set", "validate", state, "--section-from", str(src), *extra)

        code, out = ts.run(d, "next", "--phase", "validate")
        for want in ("/validate start", "the riskiest assumption: guests answer a text", "===== PRINCIPLES.md =====",
                     "no confirm or save question", "- **Pass/fail threshold (written BEFORE the result):**",
                     "set validate running --due"):
            if code or want not in out:
                fails.append(f"next --phase validate should print {want!r}: {out[-300:]!r}")
        ts.ag_start_fits(d, "validate", fails)
        running = ("--due", "2026-10-24", "--reason", "parties back within 10 min · pass: at least 60% of 30")
        # every fault at once, one refusal (E, G, no number, no date, no `will`)
        before = (d / "PRODUCT.md").read_text(encoding="utf-8")
        bad = val_record(bet="Owners let the AI send the text unchecked",
                         test="5 interviews asking owners whether they would let it send texts",
                         bar="most owners say yes")
        code, out = rec(bad, "running", *running)
        for want in ("not falsifiable", "has no number", "how each count is recorded", "has no date"):
            if code == 0 or want not in out:
                fails.append(f"set validate running should refuse with {want!r} in one list: {out.strip()[:500]!r}")
        if (d / "PRODUCT.md").read_text(encoding="utf-8") != before:
            fails.append("a refused /validate record changed PRODUCT.md")
        code, out = rec(val_record(bet="Owners will let the AI send order-status texts unchecked because it saves "
                                       "them time", test="8 interviews asking owners whether they would allow it"),
                        "running", *running)
        if code == 0 or "only asks them" not in out:
            fails.append(f"a bet about what people do, tested by asking, should be refused (G): {out.strip()[:300]!r}")
        comp = d / "docs" / "validation.md"
        comp_text = comp.read_text(encoding="utf-8")
        comp.write_text(comp_text.replace("## Owner's answers", "## Notes"), encoding="utf-8")
        code, out = rec(val_record(), "running", *running)
        if code == 0 or "Owner's answers" not in out:
            fails.append(f"a companion without the owner's answers should be refused: {out.strip()[:300]!r}")
        comp.write_text(comp_text, encoding="utf-8")
        code, out = rec(val_record(), "running", *running, "--dry-run")
        if code or "DRY RUN" not in out or ts.status.Status.load(d / "STATUS.md").state("validate") != "empty":
            fails.append(f"--dry-run on the good record should pass and write nothing: {out.strip()[:300]!r}")
        code, out = rec(val_record(), "running", *running)
        if code or "Open a NEW conversation" not in out:
            fails.append(f"the realistic running record should pass the first time and print the handoff: "
                         f"{out.strip()[-400:]!r}")
        # the result lands: dated before the bar, a verdict word missing, raw notes not written -> one refusal
        code, out = rec(val_record(result="34 parties, 23 back (68%) · 2026-10-01 · `docs/validation/missing.md`",
                                   verdict="looks good"), "filled", "--note", "68% vs 60%")
        for want in ("after the result", "do not exist", "proceed, pivot or kill"):
            if code == 0 or want not in out:
                fails.append(f"set validate filled should refuse with {want!r}: {out.strip()[:500]!r}")
        (d / "docs" / "validation").mkdir()
        (d / "docs" / "validation" / "2026-10-23-friday-texts.md").write_text("| party | texted | back |\n",
                                                                                encoding="utf-8")
        good = val_record(result=VAL_RESULT, verdict=VAL_VERDICT)
        code, out = rec(good, "filled", "--note", "68% back vs a 60% bar", "--commit", "validation recorded")
        if code or "saved: commit" not in out:
            fails.append(f"the realistic filled record should pass the first time: {out.strip()[-400:]!r}")
        # a re-validation keeps the earlier entry: dropping it is refused, appending passes
        again = val_record(bet=VAL_BET.replace("small restaurants", "food trucks"), result=VAL_RESULT,
                           verdict=VAL_VERDICT)
        code, out = rec(again, "filled", "--note", "re-run")
        if code == 0 or "append-only" not in out:
            fails.append(f"a re-validation that drops the earlier entry should be refused: {out.strip()[:300]!r}")
        code, out = rec(good + "\n**Re-run 2026-11-02** (food trucks)\n\n" + again.replace(VAL_TAIL, ""), "filled",
                        "--note", "re-run")
        if code:
            fails.append(f"a re-validation that appends a dated entry should pass: {out.strip()[-400:]!r}")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "proj"
        d.mkdir()
        ts.scope_ready(d)
        val_heading(d)
        src = Path(t) / "validation-section.md"
        args = ("--reason", "pre-sold to two restaurants already", "--gate", "validate", "--section-from", str(src))
        src.write_text(val_record(bet="", test="", result="", verdict=""), encoding="utf-8")
        code, out = ts.run(d, "set", "validate", "overridden", *args)
        if code == 0 or "never blank it" not in out or "override field" in out:
            fails.append(f"an override that blanks the fields should be refused: {out.strip()[:300]!r}")
        mark = "— not run (override 2026-10-06)"
        src.write_text(val_record(test=mark, bar=mark, result=mark, verdict=mark).replace("not overridden", ""),
                       encoding="utf-8")
        code, out = ts.run(d, "set", "validate", "overridden", *args)
        if code == 0 or "override field is empty" not in out:
            fails.append(f"an override that says nothing about what stays untested should be refused: "
                         f"{out.strip()[:300]!r}")
        src.write_text(val_record(test=mark, bar=mark, result=mark, verdict=mark).replace(
            "not overridden", "the guests' reply rate stays untested; #Vision's customer is unchanged"),
            encoding="utf-8")
        code, out = ts.run(d, "set", "validate", "overridden", *args)
        if code or "Open a NEW conversation" not in out:
            fails.append(f"an override that keeps every field should pass: {out.strip()[-300:]!r}")
    text = skill("validate")
    if "status.py next --phase validate`" not in text or "read all of `PRINCIPLES.md`" in text:
        fails.append("/validate Step 0 should be the one start command, never whole-file reads")
    if re.search(r"Ask one block at a time", text):
        fails.append("/validate asks one block at a time - two rounds, each ONE message (P37)")


# ---- /drift-check ---------------------------------------------------------------------------------------------------
def test_drift_check(fails: list[str]) -> None:
    """`next --phase drift-check` resolves the spine itself (no STATUS.md needed), prints what drift is judged
    against and what the script measured: a stalled running gate, an evidence line whose artefact is gone, missing
    agent instructions, the largest sections; `drift` prints the handoff. A code-only folder is Tier 3, never a
    refusal."""
    import test_status as ts
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "proj"
        d.mkdir()
        (d / "src").mkdir()
        (d / "src" / "app.py").write_text("print('waitlist')\n", encoding="utf-8")
        code, out = ts.run(d, "next", "--phase", "drift-check")
        if code or "Tier 3" not in out or "never 'on-track'" not in out:
            fails.append(f"drift start on code only should say Tier 3, not refuse: {out[-300:]!r}")
        (d / "README.md").write_text("# Waitlist\n", encoding="utf-8")
        code, out = ts.run(d, "next", "--phase", "drift-check")
        if code or "Tier 2" not in out or "README.md" not in out:
            fails.append(f"drift start with only a README should say Tier 2: {out[-300:]!r}")
        ts.scope_ready(d)
        val_heading(d)
        prod = d / "PRODUCT.md"
        prod.write_text(prod.read_text(encoding="utf-8").replace("## Scope\n", "## Scope\n" + SCOPE_REC), encoding="utf-8")
        code, out = ts.run(d, "set", "validate", "running", "--due", "2026-09-20", "--reason", "texts · pass: 60%")
        assert code == 0, out
        code, out = ts.run(d, "next", "--phase", "drift-check")
        for want in ("Tier 1", "Non-goals:", "payments - never", "STALLED gate: #validate", "largest sections",
                     "CONTRADICTED before any run", "src/missing_test.py", "NO agent instructions",
                     "===== PRINCIPLES.md =====", "Open a NEW conversation and type:"):
            if code or want not in out:
                fails.append(f"drift start on a filled project should print {want!r}: {out[-500:]!r}")
        if out.rfind("Open a NEW conversation") < out.rfind("===== MECHANISMS.md ====="):
            fails.append("drift start: the close line should come after the rules (the last line, tail-safe)")
        code, out = ts.run(d, "drift", "--found", "a booking page was built; it is a Non-goal", "--rec", "cut it")
        if code or "Open a NEW conversation" not in out:
            fails.append(f"`drift` should record and print the handoff: {out[-300:]!r}")
        ts.ag_start_fits(d, "drift-check", fails)
    text = skill("drift-check")
    if "status.py next --phase drift-check`" not in text or "read all of `PRINCIPLES.md`" in text:
        fails.append("/drift-check Step 0 should be the one start command, never whole-file reads")
    if not re.search(r"(?i)\bmust not\b", text):
        fails.append("/drift-check does not say what it must NOT do (P44)")


SCOPE_REC = ("- **THE core feature (the one thing):** a guest gets a text when their table is ready\n"
             "- **Non-goals (deliberately never building):**\n  - payments - never\n  - a booking page - never\n"
             "- **Deferred (out for now, with the trigger):**\n  - online booking — when 5 restaurants ask\n"
             "  - `evidence: pytest src/missing_test.py → 3 passed · src/missing_test.py · 2026-10-01`\n")


# ---- /adopt ---------------------------------------------------------------------------------------------------------
ADOPT_REPO = {
    "README.md": "# Toolshed\n\nNeighbours lend and borrow tools instead of buying them. A member reserves a drill "
                 "for a weekend; the lender approves it.\n",
    "pyproject.toml": "[project]\nname = \"toolshed\"\ndescription = \"a neighbourhood tool library\"\n"
                      "dependencies = [\"flask>=3\"]\n",
    "app.py": "from flask import Flask\napp = Flask(__name__)\n\n\n@app.route(\"/tools\")\ndef tools():\n    return []\n"
              "\n\n@app.post(\"/reservations\")\ndef reserve():\n    return {}, 201\n",
    "tests/test_app.py": "def test_tools():\n    assert True\n",
    ".github/workflows/ci.yml": "on: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: pytest\n",
}
ADOPT_DRAFT = """\
# PRODUCT — Toolshed
_Adopted 2026-10-06 from: README.md, pyproject.toml, app.py, tests/test_app.py, .github/workflows/ci.yml_

## Vision
- **Vision:** neighbours lend and borrow tools instead of buying them
- **Who it's for:** the households of one street's tool library (owner: "about 40 households")
- **North star — target + date:**
- **Riskiest assumption:**

## Validation

## Scope
- **THE core feature (the one thing):** a member reserves a tool for a date range; the lender approves it
- **In scope (now):**
  - list the tools (`GET /tools`, app.py)
  - reserve a tool (`POST /reservations`, app.py)
- **Non-goals (deliberately never building):**

## Plan

## Architecture
- **Stack + tools:** Python · Flask 3 (pyproject.toml) · pytest (tests/) · GitHub Actions (.github/workflows/ci.yml)

## Tests
- **What runs:** pytest in CI (.github/workflows/ci.yml)
"""


def test_adopt(fails: list[str]) -> None:
    """/adopt: the start surveys the repo itself (docs, metadata, entry points, routes, tests, CI); `set adopt
    filled --section-from <draft>` writes PRODUCT.md and STATUS.md in one call and refuses a line still tagged
    `(inferred — confirm)`, a missing or wrong provenance line and a filled section changed - every problem once."""
    import test_status as ts
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "proj"
        for rel, body in ADOPT_REPO.items():
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text(body, encoding="utf-8")
        git_init(d)
        code, out = ts.run(d, "next", "--phase", "adopt")
        for want in ("README says: Neighbours lend", "pyproject.toml", "entry points: app.py", "/tools (app.py)",
                     "/reservations", "tests: tests", ".github/workflows", "_Adopted <YYYY-MM-DD> from:",
                     "no confirm or save question", "===== MECHANISMS.md ====="):
            if code or want not in out:
                fails.append(f"next --phase adopt should print {want!r}: {out[-400:]!r}")
        ts.ag_start_fits(d, "adopt", fails)
        src = Path(t) / "draft.md"
        src.write_text(ADOPT_DRAFT.replace("tests/test_app.py,", "docs/spec.md,").replace(
            "(`POST /reservations`, app.py)", "(`POST /reservations`, app.py) (inferred — confirm)"), encoding="utf-8")
        code, out = ts.run(d, "set", "adopt", "filled", "--section-from", str(src), "--product", "Toolshed")
        for want in ("still tagged", "docs/spec.md, which is not in the repo"):
            if code == 0 or want not in out:
                fails.append(f"set adopt filled should refuse with {want!r} in one list: {out.strip()[:400]!r}")
        if (d / "PRODUCT.md").exists() or (d / "STATUS.md").exists():
            fails.append("a refused /adopt record wrote PRODUCT.md or STATUS.md")
        src.write_text(ADOPT_DRAFT.replace("_Adopted 2026-10-06 from: README.md", "_Drawn from: README.md"),
                       encoding="utf-8")
        code, out = ts.run(d, "set", "adopt", "filled", "--section-from", str(src), "--product", "Toolshed")
        if code == 0 or "no provenance line" not in out:
            fails.append(f"a draft with no provenance line should be refused: {out.strip()[:300]!r}")
        src.write_text(ADOPT_DRAFT, encoding="utf-8")
        code, out = ts.run(d, "set", "adopt", "filled", "--section-from", str(src), "--product", "Toolshed",
                           "--dry-run")
        if code or "no gap" not in out or (d / "PRODUCT.md").exists():
            fails.append(f"--dry-run on the good draft should pass and write nothing: {out.strip()[:300]!r}")
        code, out = ts.run(d, "set", "adopt", "filled", "--section-from", str(src), "--product", "Toolshed",
                           "--commit", "adopt the project")
        st = ts.status.Status.load(d / "STATUS.md") if (d / "STATUS.md").exists() else None
        if code or st is None or "saved: commit" not in out or "Open a NEW conversation" not in out:
            fails.append(f"the realistic draft should be recorded and saved in one call: {out.strip()[-400:]!r}")
        elif not re.search(r"Open a NEW conversation and type: /(?:[\w-]+:)?vision - #Vision has no vision sentence", out):
            fails.append(f"adopt's last line should follow Step 4 (no value proposition -> /vision): {out[-300:]!r}")
        elif [st.state(p) for p in ("vision", "scope", "architect", "test", "plan")] != \
                ["filled", "filled", "filled", "empty", "empty"]:
            fails.append(f"adopt recorded the wrong rows: {[st.state(p) for p in ('vision', 'scope', 'architect', 'test', 'plan')]}")
        # re-adopting: a filled section is never overwritten; an empty one is filled
        code, out = ts.run(d, "next", "--phase", "adopt")
        if "STOP: PRODUCT.md exists" not in out or "#Structure" not in out:
            fails.append(f"the start over an existing PRODUCT.md should stop and list its empty sections: {out[-300:]!r}")
        src.write_text(ADOPT_DRAFT.replace("instead of buying them", "and share ladders"), encoding="utf-8")
        code, out = ts.run(d, "set", "adopt", "filled", "--section-from", str(src))
        if code == 0 or "#Vision is already filled" not in out:
            fails.append(f"re-adopting over a filled #Vision should be refused: {out.strip()[:300]!r}")
        src.write_text(ADOPT_DRAFT.replace("## Plan\n", "## Plan\n- **Phases / milestones (core first):** M1 "
                                                         "reservations work end to end\n"), encoding="utf-8")
        code, out = ts.run(d, "set", "adopt", "filled", "--section-from", str(src))
        prod = (d / "PRODUCT.md").read_text(encoding="utf-8")
        if code or "M1 reservations" not in prod or "instead of buying them" not in prod:
            fails.append(f"re-adopting should fill only the empty #Plan: {out.strip()[-300:]!r}")
    vis = "- **Vision:** v\n- **Who it's for:** w\n- **Value proposition:** p\n"
    for secs, want in (({"Vision": vis, "Scope": "- **THE core feature:** c\n"}, "scope"),
                       ({"Vision": vis, "Scope": "- **THE core feature:** c\n- **Non-goals:** n\n"}, "playbook")):
        if ts.status.adopt_next(secs)[0] != want:
            fails.append(f"adopt_next should route {list(secs)} to /{want}, not /{ts.status.adopt_next(secs)[0]}")
    text = skill("adopt")
    if "status.py next --phase adopt`" not in text or "read all of `PRINCIPLES.md`" in text:
        fails.append("/adopt Step 0 should be the one start command, never whole-file reads")
    if "one at a time" in text:
        fails.append("/adopt confirms one section at a time - two rounds, each ONE message (P37)")


def test_side_ops_24(fails: list[str]) -> None:
    """2.4 (#54, #63, #62, #47, #53, #60): /adopt's draft is the sections a repo evidences, never the template copied
    whole - the start prints each section's field names, the record writes the title and policy, the provenance and
    only the drafted sections (a missing section is added to an existing PRODUCT.md, an unknown one refused); /adopt's
    and /deploy's rounds say how to ask more than 4 questions; the /validate and /drift-check starts print
    §Spine resolution only without PRODUCT.md, and /validate §Re-run semantics only on a re-run; docs/validation.md is
    numbered when the record saves. Each shown red alone."""
    import test_status as ts
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "proj"
        for rel, body in ADOPT_REPO.items():
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text(body, encoding="utf-8")
        git_init(d)
        code, out = ts.run(d, "next", "--phase", "adopt")
        for want in ("never the template copied whole", "## Vision: Vision | In plain words",
                     "## Scope: THE core feature | Capacity", "more than 4 questions"):
            if want not in out:
                fails.append(f"the /adopt start lacks {want!r}")
        if "templates/PRODUCT.md" in out:
            fails.append("the /adopt start still points at the whole PRODUCT.md template")
        if "## §Spine resolution" not in out:
            fails.append("the /adopt start on a repo with no PRODUCT.md should print §Spine resolution")
        src = Path(t) / "adopt-draft.md"
        src.write_text(ADOPT_DRAFT.replace("## Tests\n", "## Overview\n- **What:** tools\n\n## Tests\n"),
                       encoding="utf-8")
        code, out = ts.run(d, "set", "adopt", "filled", "--section-from", str(src), "--product", "Toolshed",
                           "--dry-run")
        if "`## Overview` is not a PRODUCT.md section" not in out:
            fails.append(f"a draft section PRODUCT.md does not have should be a gap: {out.strip()[:300]!r}")
        src.write_text(ADOPT_DRAFT, encoding="utf-8")
        code, out = ts.run(d, "set", "adopt", "filled", "--section-from", str(src), "--product", "Toolshed")
        prod = (d / "PRODUCT.md").read_text(encoding="utf-8") if (d / "PRODUCT.md").is_file() else ""
        heads = re.findall(r"(?m)^## (\S+)", prod)
        if code or heads != ["Project", "Vision", "Scope", "Architecture", "Tests"]:
            fails.append(f"an adopted PRODUCT.md holds the policy and only the drafted sections, in order: {heads} "
                         f"{out.strip()[-300:]!r}")
        if "_Adopted 2026-10-06 from: README.md" not in prod or "# PRODUCT — Toolshed" not in prod:
            fails.append(f"the adopted PRODUCT.md lacks its title or provenance line: {prod[:300]!r}")
        code, out = ts.run(d, "next", "--phase", "adopt")
        if "#Structure" not in out or "## §Spine resolution" in out:
            fails.append(f"over an existing PRODUCT.md the start lists a missing #Structure as empty and leaves §Spine "
                         f"resolution out: {out[-400:]!r}")
        code, out = ts.run(d, "next", "--phase", "drift-check")
        if "## §Spine resolution" in out:
            fails.append("the /drift-check start prints §Spine resolution although PRODUCT.md exists")
        # a PRODUCT.md made by #63 (title + policy only) gets the drafted sections added, never silently nothing
        e = Path(t) / "header-only"
        for rel, body in ADOPT_REPO.items():
            (e / rel).parent.mkdir(parents=True, exist_ok=True)
            (e / rel).write_text(body, encoding="utf-8")
        git_init(e)
        (e / "PRODUCT.md").write_text(status.product_header("Toolshed"), encoding="utf-8")
        code, out = ts.run(e, "set", "adopt", "filled", "--section-from", str(src), "--product", "Toolshed")
        prod = (e / "PRODUCT.md").read_text(encoding="utf-8")
        if code or "## Vision" not in prod or "a member reserves a tool" not in prod:
            fails.append(f"adopt over a header-only PRODUCT.md should add the drafted sections: {out.strip()[-300:]!r}")
        # /validate: the start's rules follow the run's facts
        v = Path(t) / "val"
        v.mkdir()
        ts.scope_ready(v)
        val_heading(v)
        git_init(v)
        code, out = ts.run(v, "next", "--phase", "validate")
        for banned in ("## §Spine resolution", "## §Re-run semantics", "## §Declined runs"):
            if banned in out:
                fails.append(f"a first /validate on a project with PRODUCT.md should not print {banned!r}")
        if "the one question round" not in status.START_HOLDS["validate"] or "two rounds" in \
                status.RELEASEOPS_HOLDS["eval"] + status.RELEASEOPS_HOLDS["learn"] + status.RELEASEOPS_HOLDS["deploy"]:
            fails.append("the Antigravity start files still describe two question rounds")
        (v / "docs").mkdir(exist_ok=True)
        (v / "docs" / "validation.md").write_text("# Validation\n\n## In short\n\nWe test whether guests answer a "
                                                  "text.\n\n## Why a hand-run trial\n\nIt watches the action.\n\n"
                                                  "## Owner's answers\n\n1. Guests answer a text.\n", encoding="utf-8")
        src.write_text(val_record(), encoding="utf-8")
        code, out = ts.run(v, "set", "validate", "running", "--section-from", str(src), "--due", "2026-10-20",
                           "--reason", "34 parties texted · pass: 60% come back")
        doc = (v / "docs" / "validation.md").read_text(encoding="utf-8")
        if code or "## 2. Why a hand-run trial" not in doc or "## 3. Owner's answers" not in doc:
            fails.append(f"a saved /validate record numbers docs/validation.md's headings: {code} {out[-300:]!r}")
    if "ask once more" in skill("validate"):
        fails.append("/validate still asks the bar question a second time (an extra turn)")
    for name in ("eval", "learn"):
        if "no `--commit` on a no" in skill(name):
            fails.append(f"/{name} says to drop --commit on a no - `set` saves unless --no-commit (saved against a no)")


# ---- /frontend-audit and /new-component -----------------------------------------------------------------------------
UI_REPO = {
    "DESIGN.md": "# Design\n\n## 2. Tokens\nThe app's tokens: `app/static/tokens.css`.\n",
    "app/static/tokens.css": ":root {\n  --background: #ffffff;\n  --foreground: #1a1a1a;\n  --primary: #0b5cad;\n"
                             "  --primary-foreground: #ffffff;\n}\n@media (prefers-color-scheme: dark) {\n"
                             "  .dark { --background: #111111; --foreground: #f2f2f2; }\n}\n",
    "app/templates/index.html": "<!doctype html><html><head><meta name=\"viewport\" content=\"width=device-width\">"
                                "</head><body><h1>Tools</h1></body></html>\n",
    "STRUCTURE.md": "# Structure\n\n- `src/components/` - UI components, one file per component\n",
    "docs/issues/M1-UI-01_reserve-button.md": "# [M1-UI-01] Reserve button\n\n## Target Files\n"
                                              "- `src/components/button.tsx`\n- `src/components/reserve-card.tsx`\n",
    "docs/issues/M1-UI-02_list.md": "# [M1-UI-02] Tool list\n\nNo sections yet.\n",
    "src/components/button.tsx": "export function Button() { return null }\n",
}


def ui_repo(d: Path) -> None:
    for rel, body in UI_REPO.items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text(body, encoding="utf-8")
    git_init(d)
    subprocess.run(["git", "add", "-A"], cwd=d, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", "ui"], cwd=d, capture_output=True)


def test_frontend_audit_and_new_component(fails: list[str]) -> None:
    """`next --phase frontend-audit` names the installed engine (a logged build searched the plugin cache and ran
    1.9.0), DESIGN.md, the UI folders and ONE command, with --baseline HEAD when UI files changed - and that command
    runs as printed. `next --phase new-component` lists the tokens the stylesheet DESIGN.md names really defines,
    where components live, and the pending components from the tickets, naming a ticket it cannot read."""
    import test_status as ts
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "proj"
        d.mkdir()
        ui_repo(d)
        code, out = ts.run(d, "next", "--phase", "frontend-audit")
        engine = str(ROOT / "commands" / "frontend-audit" / "audit.py").replace("\\", "/")
        for want in (f"Engine (the installed one): {engine}", "DESIGN.md: found", "UI in the project: app",
                     "engine copy:", "Must NOT", "Run /frontend-audit again"):
            if code or want not in out:
                fails.append(f"next --phase frontend-audit should print {want!r}: {out[-400:]!r}")
        if "--baseline HEAD" in out:
            fails.append("frontend-audit start asked for --baseline on a clean checkout")
        (d / "app" / "templates" / "index.html").write_text(UI_REPO["app/templates/index.html"].replace(
            "Tools", "All tools"), encoding="utf-8")
        code, out = ts.run(d, "next", "--phase", "frontend-audit")
        cmd = next((l.split("one call: ", 1)[1] for l in out.splitlines() if "Run, one call:" in l), "")
        if "--baseline HEAD" not in cmd or "1 UI file(s) changed against HEAD (app/templates/index.html)" not in out:
            fails.append(f"a changed UI file should be named and get --baseline HEAD: {cmd!r}")
        import shlex
        p = subprocess.run(shlex.split(cmd), cwd=d, capture_output=True, encoding="utf-8", errors="replace")
        if p.returncode not in (0, 1) or "engine" not in (p.stdout + p.stderr).lower():
            fails.append(f"the printed audit command should run as printed: {cmd!r} -> {p.returncode} "
                         f"{(p.stdout + p.stderr)[-300:]!r}")
        ts.ag_start_fits(d, "frontend-audit", fails)
        code, out = ts.run(d, "next", "--phase", "new-component")
        for want in ("Tokens defined in app/static/tokens.css (4)", "--primary-foreground",
                     "`src/components/` - UI components", "[x] src/components/button.tsx (M1-UI-01)",
                     "[ ] src/components/reserve-card.tsx (M1-UI-01) - pending",
                     "no `Target Files` section", "M1-UI-02_list.md", f"python \"{engine}\" app/static/tokens.css",
                     "===== PRINCIPLES.md =====", "Must NOT"):
            if code or want not in out:
                fails.append(f"next --phase new-component should print {want!r}: {out[-500:]!r}")
        ts.ag_start_fits(d, "new-component", fails)
        (d / "DESIGN.md").write_text("# Design\n\nTokens: `app/static/missing.css`.\n", encoding="utf-8")
        code, out = ts.run(d, "next", "--phase", "new-component")
        if "never emitted" not in out:
            fails.append(f"a DESIGN.md naming no existing stylesheet should stop the component: {out[-300:]!r}")
    for name in ("frontend-audit", "new-component"):
        text = skill(name)
        if f"status.py next --phase {name}`" not in text:
            fails.append(f"/{name} should start with its one start command")
        if not re.search(r"(?i)\bmust not\b", text):
            fails.append(f"/{name} does not say what it must NOT do (P44)")


# ---- the learnings pass (2026-10-06 afternoon): P47, P48, P23, W32/W66, the early handoff ----------------------------
CLAUDE_CUT = 30000  # characters Claude Code shows of one command's output (its Bash tool text); over it -> a file


def test_learnings(fails: list[str]) -> None:
    """P47: every start this pass made fits Claude's 30,000-character cut (a /structure start crept to 59K with the
    rule written down and nothing measuring it). P48 + L19: the support starts carry the run habits - stop after a
    playbook command fails twice (a harness bug cost one run 11.4M tokens editing the playbook's script), never open
    the scripts, no drawn option circles. W32/W66: the audit's arguments and exit codes are printed, so nothing runs
    --help or reads audit.py (449K + ~1M in the design round). The handoff printed at the start says it comes last
    (a Cursor run said it before the owner's yes). P23: /validate's desk check counts products, not people - its bar
    must pass the "how each count is recorded" check."""
    import test_status as ts
    outs = {}
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "p"
        d.mkdir()
        ts.scope_ready(d)
        val_heading(d)
        for ph in ("validate", "drift-check"):
            outs[ph] = ts.run(d, "next", "--phase", ph)[1]
        outs["route"] = ts.run(d, "route")[1]
        e = Path(t) / "a"
        for rel, body in ADOPT_REPO.items():
            (e / rel).parent.mkdir(parents=True, exist_ok=True)
            (e / rel).write_text(body, encoding="utf-8")
        outs["adopt"] = ts.run(e, "next", "--phase", "adopt")[1]
        u = Path(t) / "u"
        u.mkdir()
        ui_repo(u)
        for ph in ("frontend-audit", "new-component"):
            outs[ph] = ts.run(u, "next", "--phase", ph)[1]
        # P23: a desk check (rung 1) counts products found, each with its page - a realistic record must pass
        (d / "docs" / "validation.md").write_text("# Validation\n\n## In short\n\nA desk check: do owners pay for "
                                                  "this today?\n\n## Owner's answers\n\n1. Do they pay today?\n",
                                                  encoding="utf-8")
        (d / "docs" / "validation").mkdir()
        (d / "docs" / "validation" / "2026-10-06-desk.md").write_text("| tool | price | page |\n", encoding="utf-8")
        src = Path(t) / "desk.md"
        src.write_text(val_record(
            bet="Small restaurants will pay for a walk-in waitlist tool because paper lists lose guests on busy nights.",
            test="desk check (rung 1): paid waitlist tools for small restaurants and what they charge, 2026-10-06.",
            bar="set 2026-10-06: at least 3 tools charge small restaurants for a waitlist today, each with its "
                "pricing page link in docs/validation/2026-10-06-desk.md.",
            result="5 tools charge 19-79 EUR a month · 2026-10-06 · `docs/validation/2026-10-06-desk.md`",
            verdict="proceed - 5 paid tools against a bar of 3: restaurants already pay for this job"), encoding="utf-8")
        code, out = ts.run(d, "set", "validate", "filled", "--section-from", str(src), "--note", "5 vs 3", "--dry-run")
        if code or "no gap" not in out:
            fails.append(f"a realistic desk-check record should pass first time (P23): {out.strip()[:400]!r}")
    for ph, out in outs.items():
        if len(out) >= CLAUDE_CUT:
            fails.append(f"{ph}'s start is {len(out):,} characters - over Claude's {CLAUDE_CUT:,} cut (P47)")
    for ph in ("drift-check", "adopt", "frontend-audit", "new-component"):
        out = outs[ph]
        for want in ("fewest calls", "fails twice: stop", "never open or edit the playbook's scripts"):
            if want not in out:
                fails.append(f"{ph}'s start lacks the run habit {want!r} (P48, W66)")
        if "Open a NEW conversation" in out and "after the report, never before" not in out:
            fails.append(f"{ph}'s start prints the handoff without saying it comes last")
    for ph in ("frontend-audit", "new-component"):
        if "exit 0 = no ERROR, 1 = an ERROR, 2 = git cannot answer" not in outs[ph]:
            fails.append(f"{ph}'s start does not print audit.py's arguments and exit codes (W32)")


# ---- 2.3 (#47 #53 #54 #55 #56): the side skills on the 2.1/2.2 patterns -------------------------------------------
def committed(d: Path) -> list[str]:
    return subprocess.run(["git", "show", "--name-only", "--format=", "HEAD"], cwd=d, capture_output=True,
                          encoding="utf-8").stdout.split()


def test_sideskills_23(fails: list[str]) -> None:
    """No save question and no typed reason: /drift-check records every drift in ONE call and saves only STATUS.md
    and its rows (the user's own unfinished file stays out); /adopt saves unasked, only PRODUCT.md and STATUS.md;
    /validate's unmet gate and skipped test are options with a fixed reason. Plain's side-skill prompts ask for the
    layout at phone, tablet and desktop, a component's empty/loading/error states and a commit: the starts print them."""
    import test_status as ts
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "proj"
        d.mkdir()
        ts.scope_ready(d)
        val_heading(d)
        git_init(d)
        subprocess.run(["git", "add", "-A"], cwd=d, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=d, capture_output=True)
        (d / "docs" / "vision.md").write_text("# Vision\n", encoding="utf-8")
        code, out = ts.run(d, "next", "--phase", "drift-check")
        for want in ("The human docs to hold against the code (Step 2 item 7): docs/vision.md", "scoped but dropped",
                     "ONE call records and saves every drift", "Change anything?"):
            if code or want not in out:
                fails.append(f"drift start should print {want!r}: {out[-400:]!r}")
        if "Record these drifts?" in out:
            fails.append("drift start still asks a save question (\"Record these drifts?\")")
        (d / "notes.txt").write_text("the user's own unfinished work\n", encoding="utf-8")
        code, out = ts.run(d, "drift", "--found", "a", "--rec", "b", "--found", "c")
        if code == 0 or "each --found needs its own --rec" not in out:
            fails.append(f"unpaired --found/--rec should be refused: {out.strip()[:300]!r}")
        code, out = ts.run(d, "drift", "--found", "a booking page was built; it is a Non-goal", "--rec", "cut it",
                           "--found", "online booking was scoped and dropped", "--rec", "re-scope with a trigger")
        st = ts.status.Status.load(d / "STATUS.md")
        files = committed(d)
        if code or len(st.rows["Drift"]) != 2 or "saved: commit" not in out or "Open a NEW conversation" not in out:
            fails.append(f"two drifts in one call should be recorded, saved and handed off: {out.strip()[-400:]!r}")
        elif "notes.txt" in files or len([f for f in files if "drift" in f]) != 2:
            fails.append(f"the drift save should hold STATUS.md and its rows only, never the user's file: {files}")
    text = skill("drift-check")
    if "Record these drifts?" in text or text.index("## Step 0 —") > text.index("## Step 0b"):
        fails.append("/drift-check: a save question left, or Step 0 not first")
    # /adopt: saves unasked, and only what it wrote
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "proj"
        for rel, body in ADOPT_REPO.items():
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text(body, encoding="utf-8")
        git_init(d)
        subprocess.run(["git", "add", "-A"], cwd=d, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=d, capture_output=True)
        code, out = ts.run(d, "next", "--phase", "adopt")
        for want in ("ONE question round", "Keep every inferred line (Recommended)", "Don't know yet - leave it empty"):
            if code or want not in out:
                fails.append(f"adopt start should print {want!r}: {out[-400:]!r}")
        if "round 2" in out:
            fails.append("adopt start still names a round 2")
        (d / "app.py").write_text(ADOPT_REPO["app.py"] + "\n# half-done edit\n", encoding="utf-8")
        src = Path(t) / "draft.md"
        src.write_text(ADOPT_DRAFT, encoding="utf-8")
        code, out = ts.run(d, "set", "adopt", "filled", "--section-from", str(src), "--product", "Toolshed")
        files = committed(d)
        if code or "saved: commit" not in out:
            fails.append(f"adopt with no --commit should still save (#62): {out.strip()[-300:]!r}")
        elif "app.py" in files or "PRODUCT.md" not in files:
            fails.append(f"the adopt save should hold PRODUCT.md and STATUS.md only, never the user's edit: {files}")
    if "round 2" in skill("adopt") or "--commit \"<one line>\"" in skill("adopt"):
        fails.append("/adopt SKILL.md still names a round 2 or a --commit to remember")
    # /validate: the gate cascade rule
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "proj"
        d.mkdir()
        ts.scope_ready(d)
        val_heading(d)
        prod = d / "PRODUCT.md"
        code, out = ts.run(d, "next", "--phase", "validate")
        if code or "Skip it: already shown elsewhere" not in out or "the reason is the chosen option's words" not in out:
            fails.append(f"validate start should offer the skip as options, never a typed reason: {out[-400:]!r}")
        prod.write_text(re.sub(r"(?m)^- \*\*Riskiest assumption[^\n]*\n", "", prod.read_text(encoding="utf-8")),
                        encoding="utf-8")
        code, out = ts.run(d, "next", "--phase", "validate")
        if code or "Run /vision first (Recommended)" not in out or status.VALIDATE_NO_BET not in out:
            fails.append(f"validate with no riskiest assumption should ask ONE options question: {out[-400:]!r}")
    text = skill("validate")
    for bad in ("Round 2", "round 2's answer", "Two rounds", "the user's own words"):
        if bad in text:
            fails.append(f"/validate SKILL.md still says {bad!r} (one round, no save question, no typed reason)")
    # /frontend-audit and /new-component: what plain is asked for
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "proj"
        d.mkdir()
        ui_repo(d)
        code, out = ts.run(d, "next", "--phase", "frontend-audit")
        if code or "render_check.py" not in out or "375 / 768 / 1280" not in out or "NOT RUN" not in out:
            fails.append(f"frontend-audit start should print the 3-width layout check: {out[-400:]!r}")
        code, out = ts.run(d, "next", "--phase", "new-component")
        for want in ("src/components/reserve-card.tsx (Recommended)", "empty, loading and error",
                     "git commit -m", "never `git add -A`"):
            if code or want not in out:
                fails.append(f"new-component start should print {want!r}: {out[-400:]!r}")
    if "empty · loading · error" not in skill("new-component"):
        fails.append("/new-component's exit criteria lack the data states (empty, loading, error)")
    if "20 laws" in skill("frontend-audit"):
        fails.append("/frontend-audit says 20 laws; /design-system sets 26")


def test_review_23(fails: list[str]) -> None:
    """The 2.3 wording review, side skills. /adopt and /drift-check save unasked, so a project folder inside a
    PARENT repo must not commit PRODUCT.md into the parent (save_commit refused that case; save_paths did not). A
    no-git save tells the user one plain line - never an unformatted `offer git init` question. /new-component's menu
    question holds at most 4 options (Claude's question tool takes 4). /frontend-audit says who starts the app."""
    import test_status as ts
    with tempfile.TemporaryDirectory() as t:
        parent = Path(t)
        git_init(parent)
        (parent / "README.md").write_text("# outer repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=parent, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "outer"], cwd=parent, capture_output=True)
        d = parent / "proj"
        for rel, body in ADOPT_REPO.items():
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text(body, encoding="utf-8")
        src = parent / "draft.md"
        src.write_text(ADOPT_DRAFT, encoding="utf-8")
        code, out = ts.run(d, "set", "adopt", "filled", "--section-from", str(src), "--product", "Toolshed")
        log = subprocess.run(["git", "log", "--oneline"], cwd=parent, capture_output=True, encoding="utf-8").stdout
        if code or "PARENT folder" not in out or len(log.splitlines()) != 1:
            fails.append(f"adopt inside a parent repo should not commit there and should say so: {out.strip()[-300:]!r}"
                         f" / parent log: {log!r}")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "proj"
        for rel, body in ADOPT_REPO.items():
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text(body, encoding="utf-8")
        src = Path(t) / "draft.md"
        src.write_text(ADOPT_DRAFT, encoding="utf-8")
        code, out = ts.run(d, "set", "adopt", "filled", "--section-from", str(src), "--product", "Toolshed")
        if code or "offer `git init` once" in out or "Run `git init` to keep versions" not in out:
            fails.append(f"a no-git save should print one plain line for the user, no offer: {out.strip()[-300:]!r}")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "proj"
        d.mkdir()
        ui_repo(d)
        tk = d / "docs" / "issues" / "M1-UI-03_more.md"
        tk.write_text("# [M1-UI-03] More\n\n## Target Files\n" + "".join(
            f"- `src/components/extra-{i}.tsx`\n" for i in range(5)), encoding="utf-8")
        code, out = ts.run(d, "next", "--phase", "new-component")
        q = next((l for l in out.splitlines() if "ONE options question" in l), "")
        if code or "(Recommended)" not in q or "Other - type any name from the menu" not in q \
                or "the other pending ones" in q or q.count(".tsx") > 3:
            fails.append(f"new-component's menu question should hold at most 4 options: {q!r}")
        code, out = ts.run(d, "next", "--phase", "frontend-audit")
        if code or "Never start a server in the foreground" not in out or "Start your app, then run " \
                "/frontend-audit again" not in out:
            fails.append(f"frontend-audit should say who starts the app: {out[-500:]!r}")
        (d / "package.json").write_text('{"scripts": {"dev": "vite --port 5173"}}', encoding="utf-8")
        code, out = ts.run(d, "next", "--phase", "frontend-audit")
        if code or "start --cmd \"npm run dev\" --port 5173" not in out or "stop --port 5173" not in out:
            fails.append(f"a project with a dev recipe should get the background start/stop pair: {out[-600:]!r}")


def test_review_24_ops_side(fails: list[str]) -> None:
    """2.4 wording review (ops, side). /validate with no riskiest assumption prints the declined line for the stop
    (the skill said it did; it never did, so the stop went unrecorded) and that line records; the skill writes the
    strictest bar into the record (not a "(Recommended)" label) and names the `## 1. In short` opening `set` requires.
    "trigger" is a plain word in docs/learnings.md and docs/deployment.md (/learn asks a trigger per deferred item) -
    no playbook-word warning there; docs/scope.md still warns. templates/deployment.md says what it means in plain
    words. Each shown red before the fix."""
    import test_status as ts
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "proj"
        d.mkdir()
        ts.scope_ready(d)
        val_heading(d)
        prod = d / "PRODUCT.md"
        prod.write_text(re.sub(r"(?m)^- \*\*Riskiest assumption[^\n]*\n", "", prod.read_text(encoding="utf-8")),
                        encoding="utf-8")
        code, out = ts.run(d, "next", "--phase", "validate")
        line = 'set validate declined --reason "#Vision has no riskiest assumption" --gate vision'
        if code or line not in out:
            fails.append(f"validate with no riskiest assumption should print the declined line for the stop: "
                         f"{out[-500:]!r}")
        code, out = ts.run(d, "set", "validate", "declined", "--reason", "#Vision has no riskiest assumption",
                           "--gate", "vision")
        if code or "declined" not in (d / "STATUS.md").read_text(encoding="utf-8"):
            fails.append(f"the printed declined line should record the stop: {out.strip()[-300:]!r}")
    text = skill("validate")
    if "as *(Recommended)*; no extra question" in text or "strictest bar offered into `Pass/fail threshold`" not in text:
        fails.append("/validate Step 2 item 3 should write the strictest bar into `Pass/fail threshold`, not a label")
    step3 = text[text.find("## Step 3 "):text.find("## Step 3b")]
    if "opening with `## 1. In short`" not in step3:
        fails.append("/validate Step 3 should say docs/validation.md opens with `## 1. In short`")
    doc = "# Learnings\n\n## 1. In short\n\nWe keep the digest. The trigger to revisit it is 50 users.\n"
    for rel, warn in (("docs/learnings.md", False), ("docs/deployment.md", False), ("docs/scope.md", True)):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / rel).parent.mkdir(parents=True)
            (Path(t) / rel).write_text(doc, encoding="utf-8")
            got = any("playbook words" in w for w in status.companion_warnings(Path(t), rel))
            if got != warn:
                fails.append(f"{rel}: the word 'trigger' should {'' if warn else 'not '}warn as a playbook word")
    dep = " ".join((ROOT / "templates" / "deployment.md").read_text(encoding="utf-8").split())
    for bad in ("milestone check had not passed", "fails open, without a sound", "DNS still spreading",
                "stranger can trigger"):
        if bad in dep:
            fails.append(f"templates/deployment.md still says {bad!r} - say it in plain words")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    fails: list[str] = []
    test_playbook(fails)
    test_validate(fails)
    test_drift_check(fails)
    test_adopt(fails)
    test_frontend_audit_and_new_component(fails)
    test_learnings(fails)
    test_sideskills_23(fails)
    test_review_23(fails)
    test_side_ops_24(fails)
    test_review_24_ops_side(fails)
    for f in fails:
        print(f"  x {f}")
    print("OK - the support skills' starts and closes behave" if not fails else f"FAIL - {len(fails)} test(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
