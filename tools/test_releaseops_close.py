"""tools/test_releaseops_close.py - the release phases' one start command and their close in code (P1 P2 P17 P20 P37
P41-P45): /eval, /learn, /ship, /deploy.

Each read PRINCIPLES.md, MECHANISMS.md and PRODUCT.md whole in its first message and closed on prose alone. Now
`next --phase <phase>` prints the spine lines the phase works from, what to write, what the close refuses and the
rules; the close is one call that refuses every countable gap in ONE list (`--dry-run` lists them, writes nothing).

No saved run of these phases on the current test project exists (P17), so the project below is the record a model
would realistically write for a B2B HR product with a read-only AI agent that drafts payslip answers for
consultants. Each realistic record must close the first time; each check is shown red by breaking exactly what it
checks; a copy with every fault at once is refused in ONE list.
Run: python tools/test_releaseops_close.py   (check.py runs it, check 61)
"""
from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import status  # noqa: E402

# A machine with no git identity (a fresh CI runner) cannot commit; the saves under test commit through status.py.
for _k, _v in (("GIT_AUTHOR_NAME", "t"), ("GIT_AUTHOR_EMAIL", "t@t"), ("GIT_COMMITTER_NAME", "t"), ("GIT_COMMITTER_EMAIL", "t@t")):
    os.environ.setdefault(_k, _v)

TODAY = "2026-10-06"

VISION = """\
- **Vision (ONE sentence — the world this product creates, not what it does):** Every payroll consultant answers "why did my net pay change?" in minutes, with the rule behind each euro.
- **Who it's for:** payroll consultants at a payroll bureau with 40 consultants.
- **North star — target + date (e.g. "40 restaurants seating 100+ walk-ins a week by 2027-03-31"):** median consultant time per pay-change question 5 minutes by 2027-06-30 (today about 25).
- **North star — 2–3 input metrics (the numbers that move between events/releases and drive it):** drafts approved without edits (share); known-answer accuracy.
- **North star — 1 guardrail (what must NOT get worse while chasing it):** no wrong figure ever reaches a client.
- **North star — instrumentation (how it gets measured; "nothing records this yet" is a finding):** the review log records opened, approved and sent times per question.
- **AI (what it does · what a person decides · accuracy bar · cost per use; "n/a" when it uses no AI):** drafts the answer; the consultant approves every one; 90% of known-answer cases with every figure right; under €0.10 a draft.
"""
ARCHITECTURE = """\
- **Runtime target (each deployable unit):** one web service on Render (PaaS) · `user-chosen` · Postgres on Render.
- **Performance budget:** p95 draft time under 8 s (aspirational, re-measured in /eval).
- **AI cost budget:** under €0.10 per draft; a run over it stops.
"""
EVALUATION = """\
- **Is it good? (measured vs a recorded baseline; regression fails):** 38 of 40 known-answer cases drafted with every figure right (95%) vs baseline 90% (the #Vision accuracy bar, docs/evaluation.md) - no regression. The north star (5 minutes per question) is not readable until after the pilot (M4): it needs real consultants.
- **Metrics + confidence score:** accuracy 95% (38/40) · "not sure" holds 2 of 40, both correct · guardrail: wrong figures shown to a consultant 0 of 40 · p95 draft time 6.2 s (budget 8 s). Confidence 70%: solid - figures and holds on the known-answer set; risky - only 12 Dutch cases; to raise it - 20 French cases from the pilot team.
  - `evidence: uv run python evals/run_known_answers.py → 38/40 right, 0 wrong figures · evals/known_answers.jsonl · 2026-10-06`
- **Cost-per-run · (AI) scoring-bias:** €0.031 per draft (40 runs, €1.24 in total, from the provider's usage page); scored by exact match of each figure against the fake payroll data - no model grades itself; wording read by one consultant (one person's view, noted).
- **Operational failures (separated from quality):** 1 of 41 runs timed out at the provider (excluded from the 40); 0 blocked.
- **Detail:** `docs/evaluation.md` (reasoning + workings; this section stays a RECORD)
"""
FILES = {
    "evals/known_answers.jsonl": '{"case": 1, "employee": "E-001", "months": ["2026-08", "2026-09"]}\n',
    "evals/run_known_answers.py": "\"\"\"Runs the known-answer set and prints right/wrong counts.\"\"\"\n",
    "docs/evaluation.md": "# Evaluation\n\n## In short\n\n38 of 40 known-answer drafts had every figure right. "
                          "That beats the 90% bar. Next we add French cases before the pilot grows.\n"
                          "\n## Baseline\n\nThe #Vision accuracy bar, 90%, is the baseline.\n"
                          "\n## Owner's answers\n\n1. The 40 known-answer cases and 10 real anonymised payslips.\n"
                          "2. Yes, this result is the baseline.\n",
    "app/main.py": "from fastapi import FastAPI\n\napp = FastAPI()\n",
}


def run(d: Path, *args: str) -> tuple[int, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = status.main(["--file", str(d / "STATUS.md"), "--today", TODAY, *args])
        except SystemExit as e:  # argparse: an option this status.py does not know (an older copy)
            code = e.code if isinstance(e.code, int) else 2
    return code, out.getvalue() + err.getvalue()


def git(d: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=d, capture_output=True, text=True).stdout


def project(d: Path, sections: dict[str, str], extra: dict[str, str] | None = None) -> None:
    for rel, text in {**FILES, **(extra or {})}.items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text(text, encoding="utf-8")
    tpl = (ROOT / "templates" / "PRODUCT.md").read_text(encoding="utf-8")
    text = tpl
    for name, body in sections.items():
        text = status.replace_section(text, name, body)
    (d / "PRODUCT.md").write_text(text, encoding="utf-8")


def states(d: Path, **rows: tuple[str, str]) -> None:
    """Set phase rows directly (the earlier phases' own closes are tested in their own files)."""
    st = status.Status.load(d / "STATUS.md")
    last = max(status.CHAIN.index(p.replace("_", "-")) for p in rows)
    for p in status.CHAIN[:last]:  # every phase before the ones named ran (deploy and validate are optional)
        if p not in ("deploy", "validate"):
            # the phases whose own check reads project files: tested in their own files, overridden here
            gate = p in ("structure", "design-system", "foundation", "contracts", "tickets")
            st.phase(p)[1:6] = ["overridden" if gate else "filled", TODAY, "", "pass" if p in status.VERIFY else "",
                                "Override: tested in its own file - bypassed /" + p if gate else ""]
    for phase, (state, verdict) in rows.items():
        r = st.phase(phase.replace("_", "-"))
        r[1:6] = [state, TODAY, "", verdict, ""]
    st.header["AI product"] = "yes"
    st.save(d / "STATUS.md")


def fresh(t: str, sections: dict[str, str], extra: dict[str, str] | None = None) -> Path:
    d = Path(tempfile.mkdtemp(dir=t))
    project(d, sections, extra)
    run(d, "init", "--product", "HR drafting")
    git(d, "init", "-q")
    git(d, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    git(d, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "base")
    return d


def section_file(d: Path, body: str) -> str:
    f = d.parent / f"{d.name}-section.md"
    f.write_text(body, encoding="utf-8")
    return str(f)


def test_eval(t: str, fails: list[str]) -> None:
    spine = {"Vision": VISION, "Architecture": ARCHITECTURE}
    d = fresh(t, spine)
    states(d, dev_check=("filled", "pass"), test=("filled", "pass"))

    # the one start: the goal, the gates, the budget, the dataset, the fields, the refusals, the rules
    code, start = run(d, "next", "--phase", "eval")
    for want in ("/eval start", "median consultant time per pay-change question 5 minutes by 2027-06-30",
                 "no wrong figure ever reaches a client", "both passed", "p95 draft time under 8 s",
                 "none recorded - this first result becomes the baseline", "evals/known_answers.jsonl",
                 "REPORT ONLY", "never its fix step", "Is it good? (measured vs a recorded baseline",
                 "refuses, every problem in one list", "ONE question round", "never a separate save or",
                 "set eval filled --verdict pass|fail --section-from <file> --commit", "===== PRINCIPLES.md =====",
                 "the bullets this phase applies", "it never changes product code", "inside a subagent", "Run only",
                 "a playbook command fails twice"):
        if want not in start:
            fails.append(f"the /eval start lacks {want!r}")
    for banned in ("close with, in order", "## §Step 3b", "read all of"):
        if banned in start:
            fails.append(f"the /eval start should not carry {banned!r} (the close's rules print at the close)")
    if len(start) > 30000:
        fails.append(f"the /eval start is {len(start)} characters - Claude Code shows 30,000")

    # the realistic record closes the first time: --dry-run first, then the record call saves and prints the close
    f = section_file(d, EVALUATION)
    code, out = run(d, "set", "eval", "filled", "--verdict", "pass", "--section-from", f, "--dry-run")
    if code != 0 or "no gap" not in out:
        fails.append(f"the realistic #Evaluation should pass --dry-run: {out[-600:]}")
    code, out = run(d, "set", "eval", "filled", "--verdict", "pass", "--section-from", f, "--commit",
                    "eval: known-answer set 95% vs 90% baseline")
    for want in ("#eval: empty -> filled", "saved", "The rest of the close", "Open a NEW conversation and type: " + status.skill_command("ship"),
                 "a guardrail the result made worse"):
        if want not in out:
            fails.append(f"set eval filled on the realistic record lacks {want!r}: {out[-800:]}")
    if "Read: none - only PRODUCT.md sections" not in (d / "PRODUCT.md").read_text(encoding="utf-8").replace(
            "**Read (file · date · verbatim quote):** ", "Read: "):
        fails.append("set eval filled did not write the Read: default line")
    if "files outside /eval's record" in out:
        fails.append(f"a clean tree was warned about product files: {out[-400:]}")

    # each check red alone: break exactly what it checks
    breaks = {
        "`Operational failures` is empty": ("- **Operational failures (separated from quality):** 1 of 41 runs timed out at the provider (excluded from the 40); 0 blocked.",
                                            "- **Operational failures (separated from quality):**"),
        "no measured number against a named baseline": ("38 of 40 known-answer cases drafted with every figure right (95%) vs baseline 90% (the #Vision accuracy bar, docs/evaluation.md) - no regression. The north star (5 minutes per question) is not readable until after the pilot (M4): it needs real consultants.",
                                                        "the drafts look good to the team."),
        "not when it will be": ("not readable until after the pilot (M4)", "not readable yet"),
        "no confidence percentage": ("Confidence 70%", "Confidence: fair"),
        "confidence is 100%": ("Confidence 70%", "Confidence 100%"),
        "does not report it": ("guardrail: wrong figures shown to a consultant 0 of 40", "wrong figures shown to a consultant 0 of 40"),
        "has no count": ("1 of 41 runs timed out at the provider (excluded from the 40); 0 blocked.", "a timeout happened once at the provider."),
        "scoring-bias check": ("€0.031 per draft (40 runs, €1.24 in total, from the provider's usage page); scored by exact match of each figure against the fake payroll data - no model grades itself; wording read by one consultant (one person's view, noted).",
                               "cheap per draft, from the provider's usage page."),
        "with no `evidence:` line": ("  - `evidence: uv run python evals/run_known_answers.py → 38/40 right, 0 wrong figures · evals/known_answers.jsonl · 2026-10-06`\n", ""),
    }
    for name, (old, new) in breaks.items():
        if old not in EVALUATION:
            fails.append(f"eval break {name!r}: its text is not in the record")
            continue
        d2 = fresh(t, spine)
        states(d2, dev_check=("filled", "pass"), test=("filled", "pass"))
        code, out = run(d2, "set", "eval", "filled", "--verdict", "pass", "--section-from",
                        section_file(d2, EVALUATION.replace(old, new)), "--dry-run")
        if name not in out:
            fails.append(f"/eval check {name!r} did not go red on its own break: {out[-500:]}")
    # every fault at once: ONE refusal naming each, PRODUCT.md put back
    d3 = fresh(t, spine)
    states(d3, dev_check=("filled", "pass"), test=("filled", "pass"))
    bad = EVALUATION
    for old, new in breaks.values():
        bad = bad.replace(old, new)
    before = (d3 / "PRODUCT.md").read_text(encoding="utf-8")
    code, out = run(d3, "set", "eval", "filled", "--verdict", "pass", "--section-from", section_file(d3, bad))
    hit = [n for n in ("`Operational failures` is empty", "no measured number against a named baseline",
                       "no confidence percentage", "does not report it", "scoring-bias check",
                       "with no `evidence:` line") if n in out]
    if code == 0 or out.count("REFUSED") != 1 or len(hit) < 6:
        fails.append(f"every /eval fault at once should be ONE refusal naming each (named {hit}): {out[-900:]}")
    if (d3 / "PRODUCT.md").read_text(encoding="utf-8") != before:
        fails.append("a refused set eval filled left PRODUCT.md changed - it must be put back")
    # a fail verdict with nothing measurable yet is an honest record, not a refusal
    d4 = fresh(t, spine)
    states(d4, dev_check=("filled", "pass"), test=("filled", "pass"))
    honest = EVALUATION.replace(breaks["with no `evidence:` line"][0], "")
    code, out = run(d4, "set", "eval", "filled", "--verdict", "fail", "--section-from", section_file(d4, honest),
                    "--dry-run")
    if "no gap" not in out:
        fails.append(f"--verdict fail without an evidence line should pass: {out[-400:]}")
    # the start names an unpassed gate with the override command; a product file changed is warned, never refused
    d5 = fresh(t, spine, {"Dockerfile": "FROM python:3.12\n"})
    states(d5, dev_check=("filled", "pass"), test=("empty", ""))
    (d5 / ".github" / "workflows").mkdir(parents=True)
    (d5 / ".github" / "workflows" / "ci.yml").write_text("on: push\n", encoding="utf-8")
    code, start = run(d5, "next", "--phase", "eval")
    if "/test has not passed (empty)" not in start or "status.py bypass --from eval --gate test" not in start \
            or "Stop - run /test first (Recommended)" not in start:
        fails.append(f"the /eval start should name the unpassed /test and the bypass command: {start[:900]}")
    code, out = run(d5, "set", "eval", "filled", "--verdict", "pass", "--section-from", section_file(d5, EVALUATION))
    if code != 0 or "files outside /eval's record changed" not in out or ".github/" not in out:
        fails.append(f"a CI file an audit wrote should be warned (never refused): {code} {out[-600:]}")


SCOPE = """\
- **THE core feature (the one thing):** the agent drafts why net pay changed, each cause with its amount and rule.
- **Non-goals (deliberately never building):** sending replies to clients automatically - never, a consultant approves every reply.
- **Deferred (with the trigger that brings each back):** a client self-service view - when 3 bureaus ask for it.
"""
LEARNINGS = """\
- **Success metric + result (instrumented, not guessed):** median consultant time per pay-change question 11 minutes over the pilot's first 4 weeks (from the review log: opened → sent, 212 questions), against the target of 5 by 2027-06-30 and about 25 before.
  - `evidence: uv run python scripts/review_times.py --since 2026-09-07 → median 11.0 min, n=212 · scripts/review_times.py · 2026-10-06`
- **User/usage signal incorporated:** 6 pilot consultants interviewed (docs/learnings.md): Dutch drafts are trusted, French drafts are edited in 4 of 10 cases; 3 support tickets asked for the rule link to open the payroll code.
- **Retro (what worked / what to change):** worked - the known-answer set caught 2 wrong-rule drafts before the pilot; change - French cases were thin in /eval, so add 20 French known-answer cases before widening the pilot.
- **Decided next — build / iterate / KILL (from evidence):** iterate on French drafts (20 known-answer cases, then re-run /eval); KILL the email digest - 0 of 6 consultants opened it in 4 weeks; the client self-service view stays deferred - trigger: 3 bureaus ask for it.
- **Observability + cost watch in place:** weekly review-log query of median time and edit rate; the provider spend alert at €40 a month (€0.031 a draft now); both re-read every Monday by the owner.
- **Detail:** `docs/learnings.md` (reasoning + workings; this section stays a RECORD)
"""
LEARN_FILES = {"scripts/review_times.py": "\"\"\"Median opened -> sent time from the review log.\"\"\"\n",
               "docs/learnings.md": "# Learnings\n\n## In short\n\nWe iterate on French drafts. The pilot median "
                                    "is 11 minutes against a target of 5.\n\n## Cycle 2026-10-06\n\nInterviews with 6 "
                                    "pilot consultants.\n"
                                    "\n## Owner's answers\n\n1. 11 minutes, from the review log.\n2. Interviews.\n"}


def test_learn(t: str, fails: list[str]) -> None:
    spine = {"Vision": VISION, "Architecture": ARCHITECTURE, "Scope": SCOPE, "Evaluation": EVALUATION}

    def ready(extra: dict[str, str] | None = None, release: bool = True) -> Path:
        d = fresh(t, spine, {**LEARN_FILES, **(extra or {})})
        states(d, ship=("filled", ""), eval=("filled", "pass"))
        if release:
            run(d, "release", "--what", "M4 pilot: drafts for 10 consultants", "--reviews", "R1 (diff) 3 findings · "
                "R2 skipped by the user: doc-only fixes · gate ×1 a1b2c3d · deps: pip-audit 0", "--skipped", "none",
                "--docs", "README + PRODUCT.md claims checked", "--record",
                "n/a — releases recorded in the host's release page", "--rollback", "revert PR",
                "--pr", "local-only: main @ a1b2c3d")
        return d

    d = ready()
    code, start = run(d, "next", "--phase", "learn")
    for want in ("/learn start", "median consultant time per pay-change question 5 minutes by 2027-06-30",
                 "M4 pilot: drafts for 10 consultants", "38 of 40 known-answer cases", "a client self-service view",
                 "First cycle", "it builds nothing", "Success metric + result (instrumented, not guessed)",
                 "refuses, every problem in one list", "\"Not readable until after the pilot (M4) (Recommended)\"",
                 "the decision stays (proposed)", "set learn filled --section-from <file> --commit", "Run only", "§Production "
                 "safeguards - the bullets", "**Measure for real**"):
        if want not in start:
            fails.append(f"the /learn start lacks {want!r}")
    if "close with, in order" in start or len(start) > 30000:
        fails.append(f"the /learn start carries the close checklist or is over 30,000 characters ({len(start)})")
    nothing = ready(release=False)
    code, early = run(nothing, "next", "--phase", "learn")
    if "NOTHING - no release row" not in early or "bypass --from learn --gate ship" not in early:
        fails.append(f"the /learn start with no release should say premature and print the bypass: {early[:700]}")

    f = section_file(d, LEARNINGS)
    code, out = run(d, "set", "learn", "filled", "--section-from", f, "--dry-run")
    if code != 0 or "no gap" not in out:
        fails.append(f"the realistic #Learnings should pass --dry-run: {out[-600:]}")
    code, out = run(d, "set", "learn", "filled", "--section-from", f, "--commit", "learn: cycle 1 - iterate French")
    for want in ("#learn: empty -> filled", "saved", "The rest of the close", "non-goal comes back unrecorded",
                 "Open a NEW conversation and type: " + status.skill_command("scope")):
        if want not in out:
            fails.append(f"set learn filled on the realistic record lacks {want!r}: {out[-700:]}")

    breaks = {
        "`Observability + cost watch in place` is empty": (
            "- **Observability + cost watch in place:** weekly review-log query of median time and edit rate; the provider spend alert at €40 a month (€0.031 a draft now); both re-read every Monday by the owner.",
            "- **Observability + cost watch in place:**"),
        "the measured number and where it was read": (
            "median consultant time per pay-change question 11 minutes over the pilot's first 4 weeks (from the review log: opened → sent, 212 questions), against the target of 5 by 2027-06-30 and about 25 before.\n  - `evidence: uv run python scripts/review_times.py --since 2026-09-07 → median 11.0 min, n=212 · scripts/review_times.py · 2026-10-06`",
            "about 11 minutes, the consultants say."),
        "names no real source": (
            "6 pilot consultants interviewed (docs/learnings.md): Dutch drafts are trusted, French drafts are edited in 4 of 10 cases; 3 support tickets asked for the rule link to open the payroll code.",
            "the team thinks the drafts are good."),
        "needs both halves": (
            "worked - the known-answer set caught 2 wrong-rule drafts before the pilot; change - French cases were thin in /eval, so add 20 French known-answer cases before widening the pilot.",
            "worked - the known-answer set caught 2 wrong-rule drafts before the pilot."),
        "names no decision": (
            "iterate on French drafts (20 known-answer cases, then re-run /eval); KILL the email digest - 0 of 6 consultants opened it in 4 weeks; the client self-service view stays deferred - trigger: 3 bureaus ask for it.",
            "we will look at it again after more data."),
    }
    solo = {"names no cost watch": ("the provider spend alert at €40 a month (€0.031 a draft now); both re-read",
                                    "both re-read"),
            "not when": ("median consultant time per pay-change question 11 minutes over the pilot's first 4 weeks (from the review log: opened → sent, 212 questions), against the target of 5 by 2027-06-30 and about 25 before.\n  - `evidence: uv run python scripts/review_times.py --since 2026-09-07 → median 11.0 min, n=212 · scripts/review_times.py · 2026-10-06`",
                         "not readable yet - the pilot is too small."),
            "no real user signal yet": ("6 pilot consultants interviewed (docs/learnings.md): Dutch drafts are trusted, French drafts are edited in 4 of 10 cases; 3 support tickets asked for the rule link to open the payroll code.",
                                        "none yet - the pilot started this week."),
            "without the trigger": ("the client self-service view stays deferred - trigger: 3 bureaus ask for it.",
                                    "the client self-service view stays deferred.")}
    for name, (old, new) in {**breaks, **solo}.items():
        if old not in LEARNINGS:
            fails.append(f"learn break {name!r}: its text is not in the record")
            continue
        d2 = ready()
        code, out = run(d2, "set", "learn", "filled", "--section-from", section_file(d2, LEARNINGS.replace(old, new)),
                        "--dry-run")
        if name not in out:
            fails.append(f"/learn check {name!r} did not go red on its own break: {out[-500:]}")
    d3 = ready()
    bad = LEARNINGS
    for old, new in breaks.values():
        bad = bad.replace(old, new)
    code, out = run(d3, "set", "learn", "filled", "--section-from", section_file(d3, bad))
    hit = [n for n in breaks if n in out]
    if code == 0 or out.count("REFUSED") != 1 or len(hit) != len(breaks):
        fails.append(f"every /learn fault at once should be ONE refusal naming each (named {hit}): {out[-900:]}")
    # none yet + an open item is the honest record
    d4 = ready()
    run(d4, "open", "--from", "learn", "--what", "no user signal yet: the pilot started this week",
        "--clears", "the first 5 consultant interviews are in")
    code, out = run(d4, "set", "learn", "filled", "--section-from",
                    section_file(d4, LEARNINGS.replace(*solo["no real user signal yet"])), "--dry-run")
    if "no gap" not in out:
        fails.append(f"no user signal yet WITH an open item should pass: {out[-400:]}")
    # append-only: cycle 2 replaces the section; cycle 1's decision must survive in docs/learnings.md
    cycle2 = LEARNINGS.replace(breaks["names no decision"][0], "build the French known-answer set into CI; iterate "
                               "on the rule link (3 support tickets)")
    code, out = run(d, "set", "learn", "filled", "--section-from", section_file(d, cycle2), "--dry-run")
    if "append-only" not in out:
        fails.append(f"a second cycle that drops the first cycle's decision should be refused: {out[-500:]}")
    (d / "docs" / "learnings.md").write_text(LEARN_FILES["docs/learnings.md"] + "\n## Cycle 2026-10-06 (decided)\n\n"
                                             + breaks["names no decision"][0] + "\n", encoding="utf-8")
    code, out = run(d, "set", "learn", "filled", "--section-from", section_file(d, cycle2), "--dry-run")
    if "no gap" not in out:
        fails.append(f"cycle 2 with cycle 1's decision kept in docs/learnings.md should pass: {out[-400:]}")


POLICY = """\
- **merge:** never
- **deploy:**
- **release record:**
- **reviews run in:**
- **per-ticket record:**
"""
SHIP_FILES = {"CHANGELOG.md": "# Changelog\n\n## 0.4.0 - 2026-10-06\n\n- Drafts in French.\n",
              "uv.lock": "version = 1\n", "pyproject.toml": "[project]\nname = \"hr-drafting\"\n",
              "tests/test_boot_guard.py": "def test_placeholder_secret_refuses_to_boot():\n    assert True\n"}
RELEASE = {"--what": "M4 pilot: French drafts and the company login",
           "--reviews": "R1 (diff) 3 findings · R2 (files R1's fixes touched) clean · sec R1 clean · deps: pip-audit 0 · "
                        "gate ×1 9f3e2a1",
           "--skipped": "none", "--docs": "README + PRODUCT.md + docs/features/review.md claims checked against the code",
           "--record": "CHANGELOG 0.4.0", "--rollback": "revert the PR (no migration in this release)",
           "--pr": "https://example.org/hr-drafting/pull/41"}


def test_ship(t: str, fails: list[str]) -> None:
    spine = {"Vision": VISION, "Architecture": ARCHITECTURE, "Evaluation": EVALUATION, "Project policy": POLICY}

    def ready(remote: bool = True, gates: str = "pass", extra: dict[str, str] | None = None) -> Path:
        d = fresh(t, spine, {**SHIP_FILES, **(extra or {})})
        states(d, eval=("filled", gates))
        st = status.Status.load(d / "STATUS.md")
        st.rows["Tickets"].append(["M4-AUTH-01", "2026-10-05", "yes", "gate ×1", "1",
                                   "R1 (diff) 2 findings · R2 clean · sec R1 clean", "docs/features/login.md"])
        st.save(d / "STATUS.md")
        git(d, "checkout", "-q", "-b", "release/m4")
        (d / "app" / "auth").mkdir(parents=True, exist_ok=True)
        (d / "app" / "auth" / "session.py").write_text("SESSION_COOKIE = 'hr_session'  # httponly, secure\n",
                                                        encoding="utf-8")
        git(d, "add", "-A")
        git(d, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "M4: company login session")
        if remote:
            git(d, "remote", "add", "origin", "https://example.org/hr-drafting.git")
        return d

    def release(d: Path, *extra: str, **change: str) -> tuple[int, str]:
        args = [x for k, v in {**RELEASE, **change}.items() for x in (k.replace("_", "-") if k.startswith("--")
                                                                       else "--" + k, v)]
        return run(d, "release", *args, *extra)

    d = ready()
    code, start = run(d, "next", "--phase", "ship")
    for want in ("/ship start - release/m4", "app/auth/session.py", "M4-AUTH-01 2026-10-05: review R1 (diff) 2 "
                 "findings", "Security surface in the diff: session token" if False else "Security surface in the diff:",
                 "inside a subagent", "- **merge:** never", "CHANGELOG.md - its top", "tests/test_boot_guard.py",
                 "uv run pip-audit", "Git remote: origin", "--pr pending --dry-run", "a gap here means do not open the "
                 "PR", "local-only: <branch> @ <sha>", "`status.py release` refuses, every problem in one list",
                 "## Composed skills", "it starts no new feature", "Run only", "no save or \"open the PR?\" question"):
        if want not in start:
            fails.append(f"the /ship start lacks {want!r}")
    if "close with, in order" in start or len(start) > 30000:
        fails.append(f"the /ship start carries the close checklist or is over 30,000 characters ({len(start)})")

    # before the PR: --pr pending --dry-run passes and writes nothing; after it: the record call saves and closes
    before = (d / "STATUS.md").read_text(encoding="utf-8")
    code, out = release(d, "--dry-run", **{"--pr": "pending"})
    if "no gap: open the PR" not in out or (d / "STATUS.md").read_text(encoding="utf-8") != before:
        fails.append(f"release --pr pending --dry-run on the realistic row should pass and write nothing: {out[-500:]}")
    code, out = release(d, "--commit", "ship: M4 pilot release")
    for want in ("release recorded", "saved", "The rest of the close", "every manifest surface",
                 "Open a NEW conversation and type: " + status.skill_command("learn")):
        if want not in out:
            fails.append(f"release on the realistic row lacks {want!r}: {out[-700:]}")
    if not list((d / "status" / "releases").glob("*.md")):
        fails.append("the release row was not written to status/releases/")

    breaks = {
        "names no round 1": {"--reviews": "reviewed it · sec clean · deps: pip-audit 0 · gate ×1 9f3e2a1"},
        "round 2 is not recorded": {"--reviews": "R1 (diff) 3 findings · sec R1 clean · deps: pip-audit 0 · gate ×1 9f3"},
        "no gate count": {"--reviews": "R1 (diff) clean · sec R1 clean · deps: pip-audit 0"},
        "no security review": {"--reviews": "R1 (diff) clean · deps: pip-audit 0 · gate ×1 9f3e2a1"},
        "no dependency scan": {"--reviews": "R1 (diff) clean · sec R1 clean · gate ×1 9f3e2a1"},
        "without where releases are recorded": {"--record": "n/a"},
        "does not say what was reconciled": {"--docs": "done"},
        "has no link": {"--pr": "opened"},
    }
    for name, change in breaks.items():
        code, out = release(ready(), "--dry-run", **change)
        if name not in out:
            fails.append(f"/ship check {name!r} did not go red on its own break: {out[-500:]}")
    solo = [("names a CHANGELOG entry and there is no CHANGELOG.md", ready(extra={"CHANGELOG.md": ""}), {}),
            ("--skipped says none, but #test", ready(gates="pass"), {}),
            ("a local-only release records", ready(remote=False), {}),
            ("CHANGELOG.md is retired", ready(extra={"CHANGELOG.md": "# Changelog\n\nRetired - do not add entries; "
                                                                      "see the releases page.\n"}), {})]
    for name, d2, change in solo:
        if "no CHANGELOG.md" in name:
            (d2 / "CHANGELOG.md").unlink()
        if "#test" in name:
            st = status.Status.load(d2 / "STATUS.md")
            st.phase("test")[1:6] = ["empty", TODAY, "", "", ""]
            st.save(d2 / "STATUS.md")
        code, out = release(d2, "--dry-run", **change)
        if name not in out:
            fails.append(f"/ship check {name!r} did not go red on its own break: {out[-500:]}")
    d3 = ready()
    st = status.Status.load(d3 / "STATUS.md")
    st.phase("deploy")[1:6] = ["filled", TODAY, "", "", ""]
    st.save(d3 / "STATUS.md")
    code, out = release(d3, "--dry-run")
    if "does not cite docs/deployment.md" not in out:
        fails.append(f"/deploy ran and the rollback does not cite docs/deployment.md - should be a gap: {out[-400:]}")
    # every fault at once: ONE refusal, nothing written
    d4 = ready()
    before = (d4 / "STATUS.md").read_text(encoding="utf-8")
    code, out = release(d4, **{"--reviews": "looked at it", "--docs": "done", "--pr": "opened", "--record": "n/a"})
    hit = [n for n in ("names no round 1", "no gate count", "no security review", "no dependency scan",
                       "does not say what was reconciled", "has no link", "without where") if n in out]
    if code == 0 or out.count("REFUSED") != 1 or len(hit) != 7 or (d4 / "STATUS.md").read_text(encoding="utf-8") != before:
        fails.append(f"every /ship fault at once should be ONE refusal naming each, nothing written (named {hit}): "
                     f"{out[-900:]}")
    # #51 (f): a --reviews over 200 characters is one more gap in the SAME list, not a second refusal
    code, out = release(ready(), **{"--reviews": "looked at it " + "x" * 200, "--docs": "done"})
    if out.count("REFUSED") != 1 or "--reviews is 213 characters" not in out or "does not say what was reconciled" not in out:
        fails.append(f"the 200-character cap should sit in the one gap list with the other gaps: {out[-700:]}")
    test_ship_22(t, fails, ready, release)
    test_ship_push(t, fails, ready, release)


def test_ship_push(t: str, fails: list[str], ready, release) -> None:
    """2.4: the release row is committed AFTER the PR opened, so `release` pushes that commit to the PR's branch -
    else `land.py merge` merges a PR without it. Origin is a local bare repository: no outside call. Local-only and
    a branch with no copy on origin: nothing pushed."""
    d = ready(remote=False)
    bare = Path(t) / f"origin-{d.name}.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], capture_output=True)
    git(d, "remote", "add", "origin", str(bare))
    git(d, "push", "-q", "-u", "origin", "release/m4")
    code, out = release(d, "--commit", "ship: M4 pilot release")
    head = git(d, "rev-parse", "HEAD").strip()
    on_origin = subprocess.run(["git", "rev-parse", "release/m4"], cwd=bare, capture_output=True, text=True).stdout.strip()
    if code != 0 or "saved" not in out or head != on_origin or "pushed: release/m4" not in out:
        fails.append(f"release with a PR should push its commit to the PR's branch (origin {on_origin[:9]}, "
                     f"local {head[:9]}): {out[-600:]}")
    d2 = ready(remote=False)
    code, out = release(d2, "--commit", "ship: local", **{"--pr": "local-only: release/m4 @ abc1234"})
    if code != 0 or "saved" not in out or "push" in out.lower().replace("never get pushed", ""):
        fails.append(f"a local-only release should save and say nothing about a push: {out[-500:]}")
    d3 = ready()  # a remote, but the branch was never pushed there: no push attempted (no outside call), said once
    code, out = release(d3, "--commit", "ship: M4")
    if code != 0 or "not pushed: release/m4 has no copy on origin" not in out:
        fails.append(f"a branch with no copy on origin should be named, not pushed: {out[-500:]}")


def test_ship_22(t: str, fails: list[str], ready, release) -> None:
    """2.2 (#51 items 12, 13, 15, 16, (e), (g)): the start prints the ticket's whole row, what changed since /build's
    review, the feature doc's review table and the diff; names the gate's dependency audit; says a red CI on main
    first; asks the merge question; and a per-ticket PR never bumps the version."""
    def g(d: Path, *a: str) -> str:
        return git(d, "-c", "user.email=t@t", "-c", "user.name=t", *a)

    def ticket_ready(seats: str = "SR1") -> Path:
        d = ready(extra={"justfile": "check:\n    uv run pytest -q\n    uv run pip-audit\n",
                         "TICKETS.md": f"# Tickets\n\n## M4\n\n| Seat | Lane |\n|---|---|\n| {seats} | auth |\n",
                         "docs/features/login.md": "# Login\n\n---\n\n### Review\n\ncode review + security review R1 "
                                                   "2 findings · R2 (1 file) 0 findings\n\n| Severity | File:line | "
                                                   "What goes wrong | Fixed by |\n|---|---|---|---|\n| MEDIUM | "
                                                   "`app/auth/session.py:1` | a stolen cookie works forever | expiry "
                                                   "+ test_session_expires |\n\n### Later\n\nnot this\n"})
        prod = d / "PRODUCT.md"
        prod.write_text(prod.read_text(encoding="utf-8").replace("- **merge:** never", "- **merge:**"), encoding="utf-8")
        g(d, "checkout", "-q", "-b", "m4-auth-01-login")
        st = status.Status.load(d / "STATUS.md")
        st.rows["Tickets"] = [["M4-AUTH-01", "2026-10-05", "yes", "gate ×1", "1", "R1 (diff) 2 findings · R2 clean · "
                               "sec R1 clean", "docs/features/login.md"]]
        st.save(d / "STATUS.md")
        g(d, "add", "-A")
        g(d, "commit", "-q", "-m", "M4-AUTH-01: record the ticket row")
        (d / "app" / "auth" / "expiry.py").write_text("MAX_AGE = 3600\n", encoding="utf-8")
        g(d, "add", "-A")
        g(d, "commit", "-q", "-m", "M4-AUTH-01: a fix after the build review")
        return d

    code, out = run(ready(), "next", "--phase", "ship")
    if "#Project policy says merge: never - no question" not in out or "Merge now" in out:
        fails.append("with merge: never in #Project policy the start should ask no merge question")
    d = ticket_ready()
    code, start = run(d, "next", "--phase", "ship")
    for want in ("DoD met: yes | How verified: gate ×1", "/build reviewed M4-AUTH-01 at", "1 file(s) changed since - "
                 "round 1 and security cover ONLY these: app/auth/expiry.py", "a stolen cookie works forever",
                 "```diff", "+MAX_AGE = 3600", "already runs pip-audit", "never a second run", "no lint or type run per "
                 "file", "Merge now (Recommended - one seat builds)", "land.py\" merge --pr <n>", "## [Unreleased]",
                 "Owner turns, at most two", "run /code-review here (it starts its own reviewer - never inside a helper)",
                 "moves the ticket's card to In Review (read back)"):
        if want not in start:
            fails.append(f"the 2.2 /ship start lacks {want!r}")
    if "not this" in start:
        fails.append("the /ship start printed past the feature doc's ### Review part")
    first = git(d, "rev-list", "--max-parents=0", "HEAD").strip()[:9]
    named = status.ticket_reviewed_at(d, ["M4-AUTH-01", "", "", "", "", f"R1 clean · reviewed @ {first}", ""])
    if named != first:
        fails.append(f"a ticket row naming its reviewed commit should be read first: {named!r} vs {first!r}")
    code, two = run(ticket_ready("SR1 | auth |\n| SR2"), "next", "--phase", "ship")
    if "Leave it for review (Recommended - 2 seats: SR1, SR2" not in two or "Merge now (Recommended" in two:
        fails.append(f"with 2 seats in TICKETS.md the merge question should recommend review: "
                     f"{two[two.find('Merge (no remote'):][:600]}")
    # 2.4 review: each tool starts /ship's reviewers its own way - Codex only when the skill explicitly asks; off
    # Claude ONE helper does code and security (no tool there has /code-review to run here)
    tool = status.playbook_tool
    # Antigravity (and Cursor on a long start) gets a short pointer; the start itself is in this file
    held = Path(status.__file__).resolve().parent / "ship-start.md"
    try:
        for name, want in (("codex", "explicitly asks you to spawn ONE reviewer agent"),
                           ("cursor", "ONE Task sub-agent reviews code and security"),
                           ("antigravity", "`invoke_subagent` - ONLY if it is in your tool list")):
            status.playbook_tool = lambda name=name: name
            held.unlink(missing_ok=True)
            code, other = run(d, "next", "--phase", "ship")
            if "ship-start.md" in other and held.is_file():
                other = held.read_text(encoding="utf-8")
            at = other.find("The order:")
            order = other[at:][:400] if at >= 0 else ""
            if want not in order or "/code-review" in order:
                fails.append(f"/ship on {name}: the review order should be {want!r}, never /code-review: "
                             f"{order or other[-400:]}")
    finally:
        status.playbook_tool = tool
        held.unlink(missing_ok=True)
    # CI on main: a red last run is said first; gh unreadable says nothing
    real = getattr(status, "gh_json", None)
    try:
        status.gh_json = lambda base, *a: ([{"conclusion": "failure", "status": "completed", "workflowName": "ci",
                                             "url": "https://github.com/x/y/actions/runs/1"}] if a[:2] == ("run", "list")
                                           else None)
        code, red = run(d, "next", "--phase", "ship")
        if "IS FAILING - say this to the user FIRST" not in red[red.find("/ship start"):][:600]:
            fails.append(f"a failed last CI run on main should be the start's first line after the header: {red[:600]}")
        status.gh_json = lambda base, *a: None
        code, quiet = run(d, "next", "--phase", "ship")
        if "CI ON" in quiet:
            fails.append("with gh unreadable the start should say nothing about CI")
    finally:
        status.gh_json = real
    # a per-ticket PR that bumps the version or adds a version heading: a gap in the list
    d2 = ticket_ready()
    (d2 / "CHANGELOG.md").write_text("# Changelog\n\n## 0.5.0 - 2026-10-06\n\n- Login.\n\n## 0.4.0 - 2026-10-06\n\n"
                                     "- Drafts in French.\n", encoding="utf-8")
    (d2 / "pyproject.toml").write_text("[project]\nname = \"hr-drafting\"\nversion = \"0.5.0\"\n", encoding="utf-8")
    code, out = release(d2, "--dry-run", **{"--what": "M4-AUTH-01: company login"})
    if "adds a version heading" not in out or "bumps the version in pyproject.toml" not in out:
        fails.append(f"a per-ticket /ship that bumps the version should be a gap: {out[-600:]}")
    d3 = ticket_ready()
    (d3 / "CHANGELOG.md").write_text("# Changelog\n\n## [Unreleased]\n\n- Login.\n\n## 0.4.0 - 2026-10-06\n\n"
                                     "- Drafts in French.\n", encoding="utf-8")
    code, out = release(d3, "--dry-run", **{"--what": "M4-AUTH-01: company login"})
    if "version" in out:
        fails.append(f"a per-ticket entry under [Unreleased] should pass the version check: {out[-600:]}")
    # 2.4 (#51 item 14): the record with the PR's link moves the ticket's card to In Review and says how it went (a
    # standalone /ship that /build never moved); a local-only release moves nothing
    moved = []
    real_line = status.board_line
    status.board_line = lambda base, tid, st_, seat=None: moved.append((tid, st_)) or f"Board: {tid} -> {st_} (read back)"
    try:
        code, out = release(d3, **{"--what": "M4-AUTH-01: company login"})
        if code != 0 or moved != [("M4-AUTH-01", "In Review")] or "Board: M4-AUTH-01 -> In Review" not in out:
            fails.append(f"a release with its PR link should move the ticket's card to In Review: {moved} {out[-500:]}")
        moved.clear()
        code, out = release(ticket_ready(), "--dry-run", **{"--what": "M4-AUTH-01: company login"})
        if moved:
            fails.append("a dry run must move no card")
    finally:
        status.board_line = real_line
    # the post-merge line: a release row's PR merged since -> `land.py after` first, in /build's and /ship's start
    st = status.Status.load(d / "STATUS.md")
    st.rows["Releases"].append([TODAY, "M4-AUTH-01: login", "R1 clean", "none", "README", "CHANGELOG", "revert",
                                "https://github.com/x/y/pull/41"])
    st.save(d / "STATUS.md")
    try:
        status.gh_json = lambda base, *a: {"state": "MERGED", "number": 41} if a[:2] == ("pr", "view") else None
        code, out = run(d, "next", "--phase", "ship")
        if "PR #41 (M4-AUTH-01: login) was merged since the last /ship" not in out or "after --pr 41" not in out:
            fails.append(f"a merged PR left for review should put `land.py after` first: {out[-800:]}")
        status.gh_json = lambda base, *a: {"state": "OPEN", "number": 41} if a[:2] == ("pr", "view") else None
        code, out = run(d, "next", "--phase", "ship")
        if "is still open, waiting for review" not in out:
            fails.append("an open PR left for review should be one line")
    finally:
        status.gh_json = real


class FakeHost:
    """gh + git for land.py: one PR, one issue, one board card."""

    def __init__(self, ci="SUCCESS", options=("Todo", "In Progress", "In Review", "Done"), dirty="", sticky=False):
        self.pr = {"number": 41, "state": "OPEN", "url": "https://github.com/x/y/pull/41", "headRefName": "m4",
                   "baseRefName": "main", "closingIssuesReferences": [{"number": 7}], "mergeCommit": None,
                   "statusCheckRollup": [{"name": "ci", "status": "COMPLETED" if ci != "PENDING" else "IN_PROGRESS",
                                          "conclusion": ci if ci != "PENDING" else ""}]}
        self.issue, self.status, self.options = "OPEN", "Todo", options
        self.dirty, self.sticky, self.calls, self.head = dirty, sticky, [], "aaa"
        self.area = ""  # what `status.py area-rules --check` prints: "" = no area rule file is out of step
        self.ahead = "0"  # `git rev-list --count <PR head>..<branch>`: local commits the PR does not carry
        self.pr["headRefOid"] = "hhh000111"

    def __call__(self, args):
        import json
        self.calls.append(args)
        a = args[1:]
        if "area-rules" in args:
            if "--write" in args:
                return 0, "area-rules (claude): 2 module(s)\n  wrote web/CLAUDE.md (90 characters)\n", ""
            return (1 if "drift" in self.area or "missing" in self.area else 0), \
                "area-rules (claude): 2 module(s)\n" + self.area, ""
        if args[0] == "git":
            if a[0] == "status":
                return 0, self.dirty, ""
            if a[0] == "pull":
                self.head = "mmm111222"
            if a[0] == "rev-list":
                return 0, self.ahead, ""
            if a[0] == "rev-parse":
                return 0, self.head if a[1] == "HEAD" else "mmm111222", ""
            return 0, "", ""
        if a[:2] == ["pr", "view"]:
            return 0, json.dumps(self.pr), ""
        if a[:2] == ["pr", "merge"]:
            self.pr.update(state="MERGED", mergeCommit={"oid": "mmm111222"})
            return 0, "", ""
        if a[:2] == ["pr", "comment"]:
            return 0, "", ""
        if a[:2] == ["issue", "view"]:
            return 0, json.dumps({"state": self.issue}), ""
        if a[:2] == ["issue", "close"]:
            self.issue = "CLOSED"
            return 0, "", ""
        if a[:2] == ["repo", "view"]:
            return 0, "x/y\n", ""
        if a[:2] == ["api", "graphql"]:
            q = a[3]
            if "mutation" in q:
                opt = next(x for x in a if x.startswith("o=opt-")).split("=", 1)[1]
                if not self.sticky:
                    self.status = opt.replace("opt-", "")
                return 0, json.dumps({"data": {}}), ""
            field = {"id": "F", "options": [{"id": f"opt-{o}", "name": o} for o in self.options]}
            node = {"id": "C", "project": {"id": "P", "title": "Board", "status": field},
                    "statusValue": {"name": self.status}}
            return 0, json.dumps({"data": {"repository": {"issue": {"projectItems": {"nodes": [node]}}}}}), ""
        return 1, "", f"unexpected {args}"


def test_land(t: str, fails: list[str]) -> None:
    """commands/ship/land.py (#51 item 16): merge only on green CI, then issue CLOSED, card Done, local folder on main -
    each read back; review sets In Review and names the seat; every read-back shown red by breaking it."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("land", ROOT / "commands" / "ship" / "land.py")
    land = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(land)

    def go(host, *argv):
        lines = []
        return land.main(list(argv), run=host, log=lines.append), "\n".join(lines), host

    prev_board = os.environ.pop("PLAYBOOK_BOARD", None)
    shared = land.board_module()
    if shared is None or not hasattr(shared, "move_issue"):
        fails.append("land.py does not find the shared tools/board.py - /build and /ship move cards with one module")
        return
    code, out, h = go(FakeHost(ci="PENDING"), "merge", "--pr", "41")
    if code != 2 or "CI is still running" not in out or any(c[1:3] == ["pr", "merge"] for c in h.calls):
        fails.append(f"land.py merge on pending CI should refuse and never merge: {out}")
    code, out, h = go(FakeHost(ci="FAILURE"), "merge", "--pr", "41")
    if code != 2 or "CI failed" not in out:
        fails.append(f"land.py merge on failed CI should refuse: {out}")
    code, out, h = go(FakeHost(), "merge", "--pr", "41")
    for want in ("OK   merge: PR #41 merged (merge)", "OK   issue #7: CLOSED", "OK   card #7: Status reads Done",
                 "OK   local folder: on main", "all read back OK"):
        if want not in out:
            fails.append(f"land.py merge lacks {want!r}: {out}")
    if code != 0 or h.issue != "CLOSED" or h.status != "Done":
        fails.append(f"land.py merge should close the issue and move the card: {out}")
    code, out, h = go(FakeHost(sticky=True), "merge", "--pr", "41")
    if code != 1 or "FAIL card #7: Status reads Todo, not Done" not in out:
        fails.append(f"a card that did not move should read back red: {out}")
    code, out, h = go(FakeHost(dirty=" M app/x.py"), "merge", "--pr", "41")
    if code != 1 or "uncommitted changes - not switched" not in out:
        fails.append(f"a dirty folder should not be switched, and say so: {out}")
    # 2.4 review: after the merge, area rule files out of step with the merged records are rewritten on main - only
    # in a project that has them, never on a dirty folder; in step: no write
    def writes(h):
        return [c for c in h.calls if "area-rules" in c and "--write" in c]
    host = FakeHost()
    host.area = "  ok app/CLAUDE.md\n  drift web/CLAUDE.md: does not match STRUCTURE.md\n"
    code, out, h = go(host, "merge", "--pr", "41")
    if code != 0 or len(writes(h)) != 1 or "OK   area rules: 1 file(s) rewritten" not in out \
            or "web/CLAUDE.md" not in out:
        fails.append(f"land.py after should rewrite area rule files the merge moved: {out}")
    for area, why in (("  ok app/CLAUDE.md\n", "in step"),
                      ("  missing app/CLAUDE.md\n  missing web/CLAUDE.md\n", "a project that never had area rule files")):
        host = FakeHost()
        host.area = area
        code, out, h = go(host, "merge", "--pr", "41")
        if writes(h) or "area rules" in out:
            fails.append(f"land.py after should write no area rule file ({why}): {out}")
    host = FakeHost(dirty=" M app/x.py")
    host.area = "  drift web/CLAUDE.md\n"
    code, out, h = go(host, "merge", "--pr", "41")
    if writes(h):
        fails.append(f"land.py after on a dirty folder should write no area rule file: {out}")
    # 2.4: the release row's commit never reached the PR (local branch ahead of the PR head) -> refuse, never merge
    host = FakeHost()
    host.ahead = "1"
    code, out, h = go(host, "merge", "--pr", "41")
    if code != 2 or "lacks 1 commit" not in out or any(c[1:3] == ["pr", "merge"] for c in h.calls):
        fails.append(f"land.py merge should refuse a PR whose branch lacks a local commit (the release row): {out}")
    code, out, h = go(FakeHost(), "after", "--pr", "41")
    if code != 1 or "nothing to do until it merges" not in out:
        fails.append(f"land.py after on an open PR should say it is not merged: {out}")
    code, out, h = go(FakeHost(), "review", "--pr", "41", "--seat", "SR2")
    if code != 0 or "Status reads In Review" not in out or "seat SR2 named on PR #41" not in out:
        fails.append(f"land.py review should set In Review and name the seat: {out}")
    code, out, h = go(FakeHost(options=("Todo", "In Progress", "Done")), "review", "--pr", "41", "--seat", "SR2")
    if code != 0 or "has no Status option 'In Review'" not in out or h.status != "Todo":
        fails.append(f"a board without In Review should be named, the card left alone: {out}")
    # never backwards: a card someone already moved to Done is not pulled back to In Review by a hand-off
    host = FakeHost()
    host.status = "Done"
    code, out, h = go(host, "review", "--pr", "41", "--seat", "SR2")
    if code != 0 or h.status != "Done" or "never moved back" not in out or any(
            "mutation" in " ".join(c) for c in h.calls):
        fails.append(f"land.py review must never pull a Done card back to In Review: {out}")
    code, out, h = go(FakeHost(), "review", "--pr", "41")
    if code != 2:
        fails.append("land.py review without --seat should print the usage and exit 2")
    if prev_board is not None:
        os.environ["PLAYBOOK_BOARD"] = prev_board


DEPLOY_ARCH = ARCHITECTURE + """\
- **Deployable units:** api (FastAPI) and web (Vite static site); data custody: EU region; migrations: Alembic, applied on deploy.
"""
DEPLOY_PLAN = "- **Phases / milestones (core first):**\n  - M4 — Pilot: go live via `/deploy` with the company login.\n"
DEPLOYMENT = """\
- **Host (copied from #Architecture, never re-decided) · category — one per deployable unit:** api: Render web service (PaaS) · `user-chosen` · web: Render static site (static site / CDN) · `user-chosen`
- **Live URL · why now (the #Plan milestone or the user's reason):** https://hr-drafting.example.org (web) · https://api.hr-drafting.example.org (api) - M4 pilot: 10 consultants sign in with the company login.
- **Env vars set on the host (names only — values are the user's to paste):** api: DATABASE_URL, SECRET_KEY, OIDC_CLIENT_SECRET (pasted, secret) · web: VITE_API_BASE (committed in web/.env.production) - the table is docs/deployment.md §2.
- **Migrations on deploy (the command, where it runs, what happens on failure):** `uv run alembic upgrade head` as the host's pre-deploy command on one instance; a failure aborts the deploy and the old version keeps serving.
- **Who can get in (credentials in the built output · every way to a session · what a visitor sees · previews · what a stranger can spend):** built-output scan found no password strings and no typed-in sign-in calls; the company login is the only way in (no sign-up, no demo buttons); visitors see our domain only; previews off; no proxy.
- **Proof it answers:** `evidence: curl -s https://api.hr-drafting.example.org/healthz → 200 {"status":"ok"} · docs/deployment.md · 2026-10-06` · the web root and https://hr-drafting.example.org/drafts/123 → 200 · owner-verified (manual) 2026-10-06: signed in with the company login → saw the draft queue
- **Rollback path:** redeploy the previous build from the host's deploy list; migrations are forward-only, so a rollback restores the pre-deploy database backup (docs/deployment.md §7).
  - Rehearsed 2026-10-06 on a local copy: a bad release with one extra migration, rolled back by restoring the backup → the old build answers, schema back to 4 · `evidence: curl -s http://127.0.0.1:8001/healthz → 200 after the rollback · docs/deployment.md · 2026-10-06`
- **Known gaps:** none.
"""
DEPLOY_DOC = """\
# Deployment

**In short:** The API and the site run on Render. Only the pilot consultants can sign in. Redeploy the previous build to roll back.

| Unit | Host | Category | Chosen in `#Architecture` | Live URL |
|---|---|---|---|---|
| api | Render web service | PaaS | user-chosen | https://api.hr-drafting.example.org |
| web | Render static site | static site / CDN | user-chosen | https://hr-drafting.example.org |

**Last deployed:** 2026-10-06 · **Why now:** M4 pilot - 10 consultants sign in with the company login.

## 1. Build and start

| | api | web |
|---|---|---|
| Install | `uv sync --frozen` | `npm ci` |
| Build | none | `npm run build` |
| Start | `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT` | none — static |
| Folder the host builds from | the repo root | `web/` |

## 2. Environment variables the host needs

| Variable | Unit | Secret? | Read at | Lives in | How to get the value |
|---|---|---|---|---|---|
| DATABASE_URL | api | yes | boot | pasted into host | the host's Postgres connection string |
| SECRET_KEY | api | yes | boot | pasted into host | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| OIDC_CLIENT_SECRET | api | yes | boot | pasted into host | the company identity provider's app page |
| VITE_API_BASE | web | no | build | committed in web/.env.production | https://api.hr-drafting.example.org |

**`.env.example` differences:** it lacks OIDC_CLIENT_SECRET and VITE_API_BASE (added); it lists LEGACY_FLAG, which nothing reads (removed). TEST_DATABASE_URL is test only.

## 3. Migrations on deploy

The pre-deploy command `uv run alembic upgrade head` runs on one instance; a failure aborts the deploy.

## 4. First deploy — the steps that were actually taken

Deploy order: the api and its migrations first, then the web merge. The custom domain was attached by the owner at the dashboard.

1. Connected the repository; set the build and start commands above.
2. The owner pasted the three secrets into the host.

## 5. Who can get in

The built output was searched for password strings, sign-in calls with typed-in values and real emails: none. Only the company login; previews off.

## 6. Proof it works

`evidence: curl -s https://api.hr-drafting.example.org/healthz → 200 {"status":"ok"} · docs/deployment.md · 2026-10-06`

## 7. Rollback

Redeploy the previous build from the deploy list; migrations are forward-only, so a rollback restores the pre-deploy database backup.

- **Rehearsed:** 2026-10-06 on a local copy: one extra migration, then the rollback (backup restored) → the old build answers.

## 8. Known gaps

None.

## Owner's answers

1. The M4 pilot needs the URL.
2. Previews off.
"""
DEPLOY_FILES = {
    "app/config.py": 'import os\n\nDATABASE_URL = os.environ["DATABASE_URL"]\nSECRET_KEY = os.getenv("SECRET_KEY")\n'
                     'OIDC_CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET")\nPORT = os.getenv("PORT", "8000")\n',
    "web/src/api.ts": "export const API_BASE = import.meta.env.VITE_API_BASE;\n",
    "tests/conftest.py": 'import os\n\nTEST_DB = os.environ["TEST_DATABASE_URL"]\n',
    ".env.example": "DATABASE_URL=postgresql://localhost/hr\nSECRET_KEY=change-me\nTEST_DATABASE_URL=postgresql://localhost/hr_test\n"
                    "LEGACY_FLAG=0\n",
    "render.yaml": "services: []\n",
    "docs/deployment.md": DEPLOY_DOC,
}


def test_deploy(t: str, fails: list[str]) -> None:
    spine = {"Vision": VISION, "Architecture": DEPLOY_ARCH, "Plan": DEPLOY_PLAN}

    def ready(extra: dict[str, str] | None = None, dev: bool = True) -> Path:
        d = fresh(t, spine, {**DEPLOY_FILES, **(extra or {})})
        states(d, dev_check=("filled", "pass") if dev else ("empty", ""))
        if not dev:
            st = status.Status.load(d / "STATUS.md")
            st.phase("dev-check")[1:6] = ["empty", TODAY, "", "", ""]
            st.save(d / "STATUS.md")
        return d

    d = ready()
    code, start = run(d, "next", "--phase", "deploy")
    for want in ("/deploy start", "Render (PaaS)", "M4 — Pilot: go live via `/deploy`",
                 "read at boot: DATABASE_URL, OIDC_CLIENT_SECRET, SECRET_KEY", "VITE_API_BASE",
                 "test only (not the host's - leave out): TEST_DATABASE_URL",
                 ".env.example lacks: OIDC_CLIENT_SECRET, VITE_API_BASE", "lists but nothing reads: LEGACY_FLAG",
                 "render.yaml", "all eight numbered `##` sections", "never writes or asks for a secret",
                 "Host (copied from #Architecture", "refuses, every problem in one list", "the date the USER gives",
                 "previews off" if False else "preview deployments: off (Recommended)", "§Production safeguards - the bullets",
                 "set deploy filled --section-from <file> --commit", "ONE long wait",
                 "at most 1 search and 2 documentation pages", "5. what a visitor can see", "6. a proxy",
                 "(default taken, not user-chosen)"):
        if want not in start:
            fails.append(f"the /deploy start lacks {want!r}")
    if "read at boot:" in start and "PORT" in start.split("read at boot:")[1].split("\n")[0]:
        fails.append("the /deploy start lists PORT (set by the host) as a variable to paste")
    if "close with, in order" in start or len(start) > 30000:
        fails.append(f"the /deploy start carries the close checklist or is over 30,000 characters ({len(start)})")

    f = section_file(d, DEPLOYMENT)
    code, out = run(d, "set", "deploy", "filled", "--section-from", f, "--dry-run")
    if code != 0 or "no gap" not in out:
        fails.append(f"the realistic #Deployment should pass --dry-run: {out[-700:]}")
    code, out = run(d, "set", "deploy", "filled", "--section-from", f, "--commit", "deploy: api + web live for M4")
    for want in ("#deploy: empty -> filled", "saved", "The rest of the close", "STRUCTURE.md's tree",
                 "Open a NEW conversation and type: " + status.skill_command("test")):
        if want not in out:
            fails.append(f"set deploy filled on the realistic record lacks {want!r}: {out[-700:]}")

    rec_breaks = {
        "has no `evidence:` line": ("`evidence: curl -s https://api.hr-drafting.example.org/healthz → 200 {\"status\":\"ok\"} · docs/deployment.md · 2026-10-06` · the web root and https://hr-drafting.example.org/drafts/123 → 200 · owner-verified (manual) 2026-10-06: signed in with the company login → saw the draft queue",
                                    "it works, we clicked around."),
        "does not say what happens to preview deployments": ("previews off; ", ""),
        "does not say what happens when the migration fails": ("; a failure aborts the deploy and the old version keeps serving.", "."),
    }
    solo_rec = {
        "hit no public https URL": (rec_breaks["has no `evidence:` line"][0],
                                    "`evidence: curl -s http://localhost:8000/healthz → 200 · docs/deployment.md · 2026-10-06` and http://localhost:5173/drafts/1"),
        "the root AND a deep link": (" · the web root and https://hr-drafting.example.org/drafts/123 → 200", ""),
    }
    for name, (old, new) in {**rec_breaks, **solo_rec}.items():
        if old not in DEPLOYMENT:
            fails.append(f"deploy break {name!r}: its text is not in the record")
            continue
        d2 = ready()
        code, out = run(d2, "set", "deploy", "filled", "--section-from", section_file(d2, DEPLOYMENT.replace(old, new)),
                        "--dry-run")
        if name not in out:
            fails.append(f"/deploy check {name!r} did not go red on its own break: {out[-500:]}")
    file_breaks = {
        "is missing section(s) of the template": {"docs/deployment.md": DEPLOY_DOC.replace("## 5. Who can get in\n", "")},
        "template placeholders": {"docs/deployment.md": DEPLOY_DOC.replace("Redeploy the previous build", "`<command>`")},
        "the code reads OIDC_CLIENT_SECRET": {"app/config.py": DEPLOY_FILES["app/config.py"] + 'X = os.getenv("SENTRY_DSN")\n'},
        "looks like a secret value": {"docs/deployment.md": DEPLOY_DOC + '\napi_key = "sk-live1234567890abcdefXYZ"\n'},
        "the built output carries a credential-like value": {"dist/assets/app.js": 'login({email:"a@b.nl",password:"Demo-Pass-2026"})'},
    }
    for name, extra in file_breaks.items():
        d2 = ready(extra)
        code, out = run(d2, "set", "deploy", "filled", "--section-from", section_file(d2, DEPLOYMENT), "--dry-run")
        want = "SENTRY_DSN" if "OIDC" in name else name
        if want not in out:
            fails.append(f"/deploy check {name!r} did not go red on its own break: {out[-500:]}")
    # #Architecture marks a host only when it was "default taken" (templates/PRODUCT.md): a user-chosen host copied
    # word for word carries no mark and must pass; a default-taken one must keep its mark (waste audit W53/P45)
    unmarked = DEPLOYMENT.replace(" · `user-chosen`", "")
    d6 = ready()
    code, out = run(d6, "set", "deploy", "filled", "--section-from", section_file(d6, unmarked), "--dry-run")
    if "no gap" not in out:
        fails.append(f"a user-chosen host copied unmarked from #Architecture should pass: {out[-400:]}")
    d7 = fresh(t, {**spine, "Architecture": DEPLOY_ARCH.replace("`user-chosen`", "default taken, not user-chosen")},
               DEPLOY_FILES)
    states(d7, dev_check=("filled", "pass"))
    code, out = run(d7, "set", "deploy", "filled", "--section-from", section_file(d7, unmarked), "--dry-run")
    if "has no provenance" not in out:
        fails.append(f"a default-taken host copied without its mark should be refused: {out[-400:]}")
    d3 = ready(dev=False)  # a guest mode with nothing recorded about what a stranger can trigger
    guest = DEPLOYMENT.replace("the company login is the only way in (no sign-up, no demo buttons)",
                               "the company login, and a guest mode for demos")
    code, out = run(d3, "set", "deploy", "filled", "--section-from", section_file(d3, guest), "--dry-run")
    if "does not record what a stranger can reach and spend" not in out:
        fails.append(f"#Dev-complete empty and no spend recorded should be a gap: {out[-500:]}")
    # the owner's own machine passes honestly with a local proof (#284 deploy.md:90)
    own = (DEPLOYMENT.replace("https://hr-drafting.example.org (web) · https://api.hr-drafting.example.org (api)",
                              "own machine - not public, reachable by the owner only")
           .replace(rec_breaks["has no `evidence:` line"][0],
                    "`evidence: curl -s http://localhost:8000/healthz → 200 · docs/deployment.md · 2026-10-06` and "
                    "http://localhost:5173/drafts/1 → 200"))
    d4 = ready()
    code, out = run(d4, "set", "deploy", "filled", "--section-from", section_file(d4, own), "--dry-run")
    if "no gap" not in out:
        fails.append(f"the owner's own machine with a local proof should pass: {out[-500:]}")
    # every fault at once: ONE refusal, PRODUCT.md put back
    d5 = ready({"docs/deployment.md": DEPLOY_DOC.replace("## 5. Who can get in\n", ""),
                "dist/assets/app.js": 'login({password:"Demo-Pass-2026"})'})
    bad = DEPLOYMENT
    for old, new in rec_breaks.values():
        bad = bad.replace(old, new)
    before = (d5 / "PRODUCT.md").read_text(encoding="utf-8")
    code, out = run(d5, "set", "deploy", "filled", "--section-from", section_file(d5, bad))
    hit = [n for n in (*rec_breaks, "is missing section(s)", "the built output carries") if n in out]
    if code == 0 or out.count("REFUSED") != 1 or len(hit) != 5 or (d5 / "PRODUCT.md").read_text(encoding="utf-8") != before:
        fails.append(f"every /deploy fault at once should be ONE refusal naming each, PRODUCT.md put back (named "
                     f"{hit}): {out[-900:]}")


def open_to_others(p: Path, on: bool) -> None:
    """Make a file readable by other users (on) or by its owner only (off), on this OS."""
    if os.name != "nt":
        os.chmod(p, 0o644 if on else 0o600)
    elif on:
        subprocess.run(["icacls", str(p), "/grant", "Everyone:R"], capture_output=True)
    else:
        subprocess.run(["icacls", str(p), "/remove", "Everyone"], capture_output=True)


def test_deploy_rehearsal_secrets(t: str, fails: list[str]) -> None:
    """#52 items 1, 5, 11 (2.2): a logged /deploy wrote a rollback path it never tried; plain Claude rehearsed one on a
    fake host folder and found the two traps (no down-migrations -> the rollback is the database backup; a copied
    release folder runs the old code). It also locked the secrets file and checked the logs. The start prints the
    rehearsal steps and the secrets checks; the close refuses an untried rollback path, a secrets file others can
    read on the owner's machine, and a secret value in a log; the built-output facts are the script's."""
    spine = {"Vision": VISION, "Architecture": DEPLOY_ARCH, "Plan": DEPLOY_PLAN}
    own = (DEPLOYMENT.replace("https://hr-drafting.example.org (web) · https://api.hr-drafting.example.org (api)",
                              "own machine - not public, reachable by the owner only")
           .replace("`evidence: curl -s https://api.hr-drafting.example.org/healthz → 200 {\"status\":\"ok\"} · "
                    "docs/deployment.md · 2026-10-06` · the web root and https://hr-drafting.example.org/drafts/123 → 200",
                    "`evidence: curl -s http://localhost:8000/healthz → 200 · docs/deployment.md · 2026-10-06` and "
                    "http://localhost:5173/drafts/1 → 200"))
    secret = "s3cr3t-value-for-the-test-only"

    def ready(extra: dict[str, str] | None = None) -> Path:
        d = fresh(t, spine, {**DEPLOY_FILES, ".env": f"DATABASE_URL=sqlite:///hr.db\nSECRET_KEY={secret}\n",
                             **(extra or {})})
        states(d, dev_check=("filled", "pass"))
        open_to_others(d / ".env", False)
        return d

    d = ready()
    code, start = run(d, "next", "--phase", "deploy")
    for want in ("Rehearse the rollback before you record it", "never copy a release folder", "ONE extra migration",
                 "the rollback IS restoring the step-1 backup", "not rehearsed - <why>", "`chmod 600 .env`",
                 "for each secret value of .env, naming the variable, never the value", "a rollback path not rehearsed"):
        if want not in start:
            fails.append(f"the /deploy start lacks {want!r}")
    if secret in start:
        fails.append("the /deploy start printed a secret value")
    code, out = run(d, "set", "deploy", "filled", "--section-from", section_file(d, own), "--dry-run")
    if "no gap" not in out:
        fails.append(f"an owner-only .env, clean logs and a rehearsed rollback should pass: {out[-500:]}")
    rehearsal = DEPLOYMENT.split("  - Rehearsed")[1].split("\n")[0]
    breaks = {"was written, not tried": own.replace("  - Rehearsed" + rehearsal + "\n", ""),
              "says not rehearsed with no open item": own.replace("  - Rehearsed" + rehearsal,
                                                                  "  - not rehearsed - no copy of the host to run")}
    for name, body in breaks.items():
        code, out = run(d, "set", "deploy", "filled", "--section-from", section_file(d, body), "--dry-run")
        if name not in out:
            fails.append(f"/deploy check {name!r} did not go red on its own break: {out[-500:]}")
    run(d, "open", "--from", "deploy", "--what", "rollback not rehearsed: no copy of the host to run",
        "--clears", "a rollback rehearsal is recorded")
    code, out = run(d, "set", "deploy", "filled", "--section-from",
                    section_file(d, breaks["says not rehearsed with no open item"]), "--dry-run")
    if "no gap" not in out:
        fails.append(f"`not rehearsed` WITH an open item should pass: {out[-400:]}")
    # the secrets file: red when others can read it on the owner's machine, green once locked
    d2 = ready()
    open_to_others(d2 / ".env", True)
    code, out = run(d2, "set", "deploy", "filled", "--section-from", section_file(d2, own), "--dry-run")
    if "lock it to its owner" not in out:
        fails.append(f"a .env others can read on the owner's machine should be refused: {out[-500:]}")
    if secret in out:
        fails.append("the refusal printed a secret value")
    code, out = run(d2, "set", "deploy", "filled", "--section-from", section_file(d2, DEPLOYMENT), "--dry-run")
    if "lock it to its owner" in out:
        fails.append("a PaaS host (the secrets live in the host's dashboard) should not be refused for the local .env")
    open_to_others(d2 / ".env", False)
    # a secret value in a log: named by variable, never by value
    d3 = ready({"logs/app.log": f"INFO boot ok\nDEBUG settings SECRET_KEY={secret}\n"})
    code, out = run(d3, "set", "deploy", "filled", "--section-from", section_file(d3, own), "--dry-run")
    if "a log holds the value of SECRET_KEY (app.log)" not in out or secret in out:
        fails.append(f"a secret value in a log should be refused by its variable name only: {out[-500:]}")
    d4 = ready({"logs/app.log": "INFO boot ok\nDEBUG settings SECRET_KEY=***\n"})
    code, out = run(d4, "set", "deploy", "filled", "--section-from", section_file(d4, own), "--dry-run")
    if "a log holds" in out:
        fails.append(f"a masked log should pass: {out[-400:]}")
    # warnings (never refusals): forward-only migrations with no backup in the rollback; a build value not built in
    nobackup = own.replace(", so a rollback restores the pre-deploy database backup", "").replace(
        " by restoring the backup", "")
    d5 = ready({"web/.env.production": "VITE_API_BASE=https://api.hr-drafting.example.org\n",
                "web/dist/index.html": "<script src=\"https://cdn.vendor-x.net/a.js\"></script>"
                                       "<script>fetch('http://localhost:8000/api')</script>"})
    code, start = run(d5, "next", "--phase", "deploy")
    if "hostnames a visitor's browser calls: cdn.vendor-x.net" not in start or \
            "build-time values NOT in it: VITE_API_BASE" not in start:
        fails.append(f"the /deploy start should print the built output's hostnames and missing build values: "
                     f"{start[start.find('Built output'):][:300]}")
    code, out = run(d5, "set", "deploy", "filled", "--section-from", section_file(d5, nobackup), "--no-commit")
    if code != 0 or "names no database backup" not in out or "does not contain the committed value of VITE_API_BASE" \
            not in out:
        fails.append(f"/deploy should warn (and still record) on no backup in the rollback and a build value not "
                     f"built in: {out[-700:]}")


def test_lean_rules(t: str, fails: list[str]) -> None:
    """A start prints only the safeguard bullets its phase applies, and the re-run / declined sections only when they
    apply - every call re-sends the start, and those parts were ~4-5 KB of each 14-17 KB start. The full sections stay
    one command away (`status.py rules <phase>`), and a re-run or an unmet gate brings its section back."""
    want = {"eval": ("**Measure for real**", "**Perf & cost budgets**"),
            "learn": ("**Measure for real**", "**Observability & audit**"),
            "ship": ("**Secrets never get pushed**", "**Rollout safety**", "**Placeholders must FAIL the boot"),
            "deploy": ("**Secrets never get pushed**", "**Placeholders must FAIL the boot", "**Rollout safety**")}
    not_here = {"eval": "**Secrets never get pushed**", "learn": "**Rollout safety**",
                "ship": "**Measure for real**", "deploy": "**Measure for real**"}
    d = fresh(t, {"Vision": VISION, "Architecture": DEPLOY_ARCH, "Evaluation": EVALUATION, "Scope": SCOPE})
    states(d, eval=("filled", "pass"))  # every phase before /ship passed; /eval itself filled
    run(d, "release", "--what", "M4", "--reviews", "R1 (diff) clean · deps: pip-audit 0 · gate ×1 a1b2c3d",
        "--skipped", "none", "--docs", "README checked", "--record", "n/a — releases recorded in the host",
        "--rollback", "revert PR", "--pr", "local-only: main @ a1b2c3d")
    for ph, bullets in want.items():
        code, start = run(d, "next", "--phase", ph)
        for b in bullets:
            if b not in start:
                fails.append(f"the /{ph} start lacks its safeguard bullet {b!r}")
        if not_here[ph] in start:
            fails.append(f"the /{ph} start prints {not_here[ph]!r}, a bullet it does not apply")
        if "status.py rules " + ph not in start:
            fails.append(f"the /{ph} start does not name `status.py rules {ph}` for every section whole")
        rerun = "## §Re-run semantics" in start
        if ph == "eval" and not rerun:
            fails.append("a /eval re-run (#eval is filled) should print §Re-run semantics")
        if ph in ("learn", "deploy") and rerun:  # /ship is filled here: its release row exists
            fails.append(f"a first /{ph} run should not print §Re-run semantics")
        if ph in ("learn", "deploy") and "## §Declined runs" in start:
            fails.append(f"/{ph} with its gates met should not print §Declined runs")
    d2 = fresh(t, {"Vision": VISION})
    states(d2, dev_check=("filled", "pass"))  # /test not passed -> /eval's gate is unmet
    code, start = run(d2, "next", "--phase", "eval")
    if "## §Declined runs" not in start:
        fails.append("/eval with an unmet gate should print §Declined runs")
    code, full = run(d2, "rules", "eval")
    if "## Production safeguards" not in full or "**Secrets never get pushed**" not in full:
        fails.append("`status.py rules eval` should still print §Production safeguards whole")


def test_review_findings(t: str, fails: list[str]) -> None:
    """From the cost and output reviews of other phases: the owner's round-1 answers kept word for word in the
    companion (an answer saved as "a" was misread as a date), and the wordings a model naturally writes are not
    refused (format refusals were the biggest refusal family: 284K-826K a run)."""
    spine = {"Vision": VISION, "Architecture": ARCHITECTURE}
    d = fresh(t, spine, {"docs/evaluation.md": FILES["docs/evaluation.md"].split("\n## Owner's answers")[0]})
    states(d, dev_check=("filled", "pass"), test=("filled", "pass"))
    code, out = run(d, "set", "eval", "filled", "--verdict", "pass", "--section-from", section_file(d, EVALUATION),
                    "--dry-run")
    if "## Owner's answers" not in out:
        fails.append(f"docs/evaluation.md without `## Owner's answers` should be a gap: {out[-300:]}")
    d2 = fresh(t, spine)
    states(d2, dev_check=("filled", "pass"), test=("filled", "pass"))
    code, out = run(d2, "set", "eval", "filled", "--verdict", "pass", "--section-from",
                    section_file(d2, EVALUATION.replace("Confidence 70%:", "70% confidence:")), "--dry-run")
    if "no gap" not in out:
        fails.append(f"'70% confidence' is a confidence percentage and should pass: {out[-300:]}")
    code, start = run(d2, "next", "--phase", "eval")
    for want in ("`Confidence 70%: solid", "`0 of 40`", "real · owner samples · synthetic", "## Owner's answers"):
        if want not in start:
            fails.append(f"the /eval start should print the accepted form {want!r}")
    lspine = {"Vision": VISION, "Architecture": ARCHITECTURE, "Scope": SCOPE, "Evaluation": EVALUATION}
    d3 = fresh(t, lspine, LEARN_FILES)
    states(d3, ship=("filled", ""), eval=("filled", "pass"))
    natural = (LEARNINGS.replace("iterate on French drafts", "continue with French drafts")
               .replace("6 pilot consultants interviewed (docs/learnings.md): Dutch drafts are trusted, French drafts "
                        "are edited in 4 of 10 cases; 3 support tickets asked for the rule link to open the payroll "
                        "code.", "the pilot users said French drafts need edits in 4 of 10 cases.")
               .replace("KILL the email digest", "drop the email digest"))
    code, out = run(d3, "set", "learn", "filled", "--section-from", section_file(d3, natural), "--dry-run")
    if "no gap" not in out:
        fails.append(f"natural /learn wording (continue, the pilot users said) should pass: {out[-400:]}")
    d4 = fresh(t, lspine, {**LEARN_FILES, "docs/learnings.md": "# Learnings\n\nNotes only.\n"})
    states(d4, ship=("filled", ""), eval=("filled", "pass"))
    code, out = run(d4, "set", "learn", "filled", "--section-from", section_file(d4, LEARNINGS), "--dry-run")
    if "## Owner's answers" not in out:
        fails.append(f"docs/learnings.md without `## Owner's answers` should be a gap: {out[-300:]}")
    dspine = {"Vision": VISION, "Architecture": DEPLOY_ARCH, "Plan": DEPLOY_PLAN}
    d5 = fresh(t, dspine, {**DEPLOY_FILES, "docs/deployment.md": DEPLOY_DOC.split("\n## Owner's answers")[0]})
    states(d5, dev_check=("filled", "pass"))
    code, out = run(d5, "set", "deploy", "filled", "--section-from", section_file(d5, DEPLOYMENT), "--dry-run")
    if "## Owner's answers" not in out:
        fails.append(f"docs/deployment.md without `## Owner's answers` should be a gap: {out[-300:]}")
    code, start = run(d5, "next", "--phase", "deploy")
    if "## §Context hygiene" in start:
        fails.append("the /deploy start still prints §Context hygiene whole (its lines repeat the start's own)")


LEARN_TICKETS = """# Tickets - the plan

## M1 Core
| Epic | Lane | Owner | Tickets in build order |
|---|---|---|---|
| [M1-A] Part a | a | Senior | M1-A-01 Build part a · M1-A-02 Build part a2 |

## Day 1 — who starts what
| Seat | Lane | Day-1 ticket | Why |
|---|---|---|---|
| SR1 | a | M1-A-01 | no dependencies |
"""
LEARN_PLAN = ("- **Phases / milestones (core first):**\n  - M1 Core: one consultant gets one draft (2026-10-01 → 10-14)\n"
              "- **Exit criteria per milestone:**\n  - M1: the consultant approves one draft\n")
NO_METRIC = LEARNINGS.replace(
    "median consultant time per pay-change question 11 minutes over the pilot's first 4 weeks (from the review log: "
    "opened → sent, 212 questions), against the target of 5 by 2027-06-30 and about 25 before.\n  - `evidence: uv run "
    "python scripts/review_times.py --since 2026-09-07 → median 11.0 min, n=212 · scripts/review_times.py · 2026-10-06`",
    "not readable until after the pilot (M4) - nothing records review times yet.")


def test_learn_retro(t: str, fails: list[str]) -> None:
    """#50 items 3-4 (2.2): with no metric readable, a logged /learn decided on "opinion"; plain Claude read the repo
    (tickets built vs planned, docs vs code, commits since the last merged ticket) and decided "iterate". The start
    prints that process retro; a retro citing no number while the metric is not readable is a warning; "iterate the
    plan" is a decision and hands off to /tickets."""
    spine = {"Vision": VISION, "Architecture": ARCHITECTURE, "Scope": SCOPE, "Evaluation": EVALUATION,
             "Plan": LEARN_PLAN}
    if NO_METRIC == LEARNINGS:
        fails.append("NO_METRIC's replaced text is not in LEARNINGS")

    def ready(release: bool = True) -> Path:
        d = fresh(t, spine, {**LEARN_FILES, "TICKETS.md": LEARN_TICKETS})
        states(d, ship=("filled", ""), eval=("filled", "pass"))
        (d / "app" / "a.py").write_text("A = 1\nB = 2\n", encoding="utf-8")
        (d / "status" / "tickets").mkdir(parents=True, exist_ok=True)
        (d / "status" / "tickets" / "2026-10-03-m1-a-01.md").write_text(
            "<!-- One ticket, written by status.py. Never edit by hand. -->\nTicket: M1-A-01\nDate: 2026-10-03\nDoD met: "
            "yes\nHow verified: pytest -> 2 passed\nFull-suite runs: 1\nReview: R1 clean\nDoc: docs/features/a.md\n",
            encoding="utf-8")
        git(d, "add", "-A")
        git(d, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "M1-A-01: build part a")
        run(d, "release", "--what", "M1-A-01 part a", "--reviews", "R1 (diff) clean · gate ×1 a1b2c3d · deps: pip-audit "
            "0", "--skipped", "none", "--docs", "README checked", "--record", "n/a — releases recorded in the host",
            "--rollback", "revert PR", "--pr", "local-only: main @ a1b2c3d")
        run(d, "open", "--from", "learn", "--what", "no metric yet: nothing records review times",
            "--clears", "the review log records times")
        git(d, "add", "-A")  # the release record names the ticket: its commit is the last merged ticket's
        git(d, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "M1-A-01 release: part a")
        (d / "docs" / "notes.md").write_text("one\ntwo\nthree\n", encoding="utf-8")
        git(d, "add", "-A")
        git(d, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "docs: notes")
        return d

    d = ready()
    code, start = run(d, "next", "--phase", "learn")
    for want in ("Process retro from the repo", "M1 (planned 2026-10-01 → 2026-10-14: day 6 of 14): 1 of 2 tickets built, "
                 "1 merged here - M1-A-01 2026-10-03", "Day 1 starters (TICKETS.md): M1-A-01 built 2026-10-03",
                 "Since the last merged ticket (M1-A-01, ", "1 commit(s), lines added - docs 3 · product code 0 · tests 0",
                 "The repo now: docs ", "Findings still open: 1 open item(s) - /learn 1",
                 "iterate the plan (change named unbuilt tickets", "pivot (back to /scope)"):
        if want not in start:
            fails.append(f"the /learn start lacks {want!r}: {start[start.find('Process retro'):][:900]}")
    no_num = NO_METRIC.replace(
        "worked - the known-answer set caught 2 wrong-rule drafts before the pilot; change - French cases were thin in "
        "/eval, so add 20 French known-answer cases before widening the pilot.",
        "worked - the team shipped part a; change - write fewer documents before building.")
    code, out = run(d, "set", "learn", "filled", "--section-from", section_file(d, no_num), "--no-commit")
    if code != 0 or "cites no number while the metric is not readable" not in out:
        fails.append(f"a retro citing no number while the metric is not readable should warn: {out[-600:]}")
    with_num = no_num.replace("the team shipped part a; change - write fewer documents",
                              "1 of 2 M1 tickets built by day 6; change - 3 doc lines and 0 code lines since then, so "
                              "build M1-A-02 before more documents")
    d2 = ready()
    code, out = run(d2, "set", "learn", "filled", "--section-from", section_file(d2, with_num))
    if code != 0 or "cites no number" in out:
        fails.append(f"a retro citing the repo's numbers should record with no warning: {out[-500:]}")
    if "Open a NEW conversation and type: " + status.skill_command("tickets") in out:
        fails.append("a decision other than 'iterate the plan' should not hand off to /tickets")
    # "iterate the plan" is a decision, and the next step is /tickets (red: the decision above kept its handoff)
    iterate = with_num.replace("iterate on French drafts (20 known-answer cases, then re-run /eval)",
                               "iterate the plan: split M1-A-02 in two and drop its export step (unbuilt)")
    if iterate == with_num:
        fails.append("the iterate replacement text is not in the record")
    d3 = ready()
    code, out = run(d3, "set", "learn", "filled", "--section-from", section_file(d3, iterate))
    if code != 0 or "Open a NEW conversation and type: " + status.skill_command("tickets") not in out:
        fails.append(f"'iterate the plan' should record and hand off to /tickets: {out[-500:]}")


def test_companions_24(t: str, fails: list[str]) -> None:
    """2.4 (#60, R5 of #49 #50 #52, #62, #50 item 5): the document each phase writes for a person opens with a summary
    (`## 1. In short`; deployment.md an `**In short:**` line), `set` numbers the headings left unnumbered (keeping
    the numbered ones and the document's own links) only when the record has no gap, the plain-English estimates
    warn and never refuse, the starts leave §Spine resolution out when PRODUCT.md exists, the /deploy round says how
    to ask more than 4 questions, and /scope and /plan carry the last /learn decision. Each shown red alone."""
    spine = {"Vision": VISION, "Architecture": ARCHITECTURE}
    evdoc = FILES["docs/evaluation.md"]
    # red: no summary first -> refused by name; the refused call leaves the document as the run wrote it
    d = fresh(t, spine, {"docs/evaluation.md": evdoc.replace("## In short\n\n", "## Results\n\n")})
    states(d, dev_check=("filled", "pass"), test=("filled", "pass"))
    before = (d / "docs" / "evaluation.md").read_text(encoding="utf-8")
    code, out = run(d, "set", "eval", "filled", "--verdict", "pass", "--section-from", section_file(d, EVALUATION))
    if code == 0 or "does not open with `## 1. In short`" not in out:
        fails.append(f"docs/evaluation.md without a summary first should be refused by name: {out[-400:]}")
    if (d / "docs" / "evaluation.md").read_text(encoding="utf-8") != before:
        fails.append("a refused set eval filled renumbered docs/evaluation.md - it numbers only a record it keeps")
    # red: an empty summary
    d = fresh(t, spine, {"docs/evaluation.md": evdoc.replace(
        "38 of 40 known-answer drafts had every figure right. That beats the 90% bar. Next we add French cases "
        "before the pilot grows.\n", "")})
    states(d, dev_check=("filled", "pass"), test=("filled", "pass"))
    code, out = run(d, "set", "eval", "filled", "--verdict", "pass", "--section-from", section_file(d, EVALUATION),
                    "--dry-run")
    if "`## 1. In short` is empty" not in out:
        fails.append(f"an empty `## In short` should be a gap: {out[-300:]}")
    # green: the record saves, the headings are numbered in the saved commit, an in-document link follows its heading
    linked = evdoc.replace("The #Vision accuracy bar", "See [the baseline](#baseline). The #Vision accuracy bar")
    d = fresh(t, spine, {"docs/evaluation.md": linked})
    states(d, dev_check=("filled", "pass"), test=("filled", "pass"))
    code, out = run(d, "set", "eval", "filled", "--verdict", "pass", "--section-from", section_file(d, EVALUATION))
    saved = git(d, "show", "HEAD:docs/evaluation.md")
    for want in ("## 1. In short", "## 2. Baseline", "## 3. Owner's answers", "(#2-baseline)"):
        if want not in saved:
            fails.append(f"the saved docs/evaluation.md lacks {want!r} (set numbers unnumbered headings): {saved[:400]}")
    if code != 0 or "playbook words" not in out or "a warning, not a refusal" not in out:
        fails.append(f"#Vision in docs/evaluation.md should WARN (playbook words), never refuse: {code} {out[-500:]}")
    # the start: §Spine resolution only for a project without PRODUCT.md
    code, start = run(d, "next", "--phase", "learn")
    if "## §Spine resolution" in start:
        fails.append("the /learn start prints §Spine resolution although PRODUCT.md exists")
    if "opens with `## In short`" not in start:
        fails.append("the /learn start does not say docs/learnings.md opens with `## In short`")
    (d / "PRODUCT.md").rename(d / "PRODUCT.bak")
    code, start = run(d, "next", "--phase", "eval")
    if "## §Spine resolution" not in start:
        fails.append("the /eval start on a project WITHOUT PRODUCT.md should print §Spine resolution")
    # learn: the summary rule; deploy: the summary line, the >4-questions line, a numbered section kept as numbered
    lspine = {"Vision": VISION, "Architecture": ARCHITECTURE, "Scope": SCOPE, "Evaluation": EVALUATION}
    d = fresh(t, lspine, {**LEARN_FILES, "docs/learnings.md": LEARN_FILES["docs/learnings.md"].replace(
        "## In short\n\n", "## Summary of interviews\n\n")})
    states(d, ship=("filled", ""), eval=("filled", "pass"))
    code, out = run(d, "set", "learn", "filled", "--section-from", section_file(d, LEARNINGS), "--dry-run")
    if "docs/learnings.md does not open with `## 1. In short`" not in out:
        fails.append(f"docs/learnings.md without a summary first should be a gap: {out[-300:]}")
    dspine = {"Vision": VISION, "Architecture": DEPLOY_ARCH, "Plan": DEPLOY_PLAN}
    for doc in (DEPLOY_DOC.replace("**In short:** ", "**Summary:** "),
                DEPLOY_DOC.replace("**In short:** The API", "**In short:** `<3 plain sentences>` The API")):
        d = fresh(t, dspine, {**DEPLOY_FILES, "docs/deployment.md": doc})
        states(d, dev_check=("filled", "pass"))
        code, out = run(d, "set", "deploy", "filled", "--section-from", section_file(d, DEPLOYMENT), "--dry-run")
        if "no filled `**In short:**` line" not in out:
            fails.append(f"docs/deployment.md without a filled In short line should be a gap: {out[-300:]}")
    code, start = run(d, "next", "--phase", "deploy")
    if "more than 4 questions: two question-tool calls in the same reply" not in start:
        fails.append("the /deploy start (6 questions) does not say how to ask more than the tool's 4 at a time")
    if "the `**In short:**` line first" not in start:
        fails.append("the /deploy start does not name the `**In short:**` line")
    numbered = status.number_missing("# D\n\n## 1. Build and start\n\n## 7. Rollback\n\n## Owner's answers\n\n"
                                     "### First round\n\n## Appendix — Notes\n")
    for want in ("## 1. Build and start", "## 7. Rollback", "## 8. Owner's answers", "### 8.1 First round",
                 "## Appendix A — Notes"):
        if want not in numbered:
            fails.append(f"number_missing should keep set numbers and fill the rest: {want!r} not in {numbered!r}")
    # #50 item 5: /scope and /plan print the last cycle's decision
    d = fresh(t, {**lspine, "Learnings": LEARNINGS})
    states(d, ship=("filled", ""), eval=("filled", "pass"))
    for ph in ("scope", "plan"):
        code, start = run(d, "next", "--phase", ph)
        if "#Learnings, the last cycle's decision" not in start or "KILL the email digest" not in start:
            fails.append(f"the /{ph} start does not carry #Learnings' last decision: {start[:600]}")
    d = fresh(t, lspine)
    code, start = run(d, "next", "--phase", "scope")
    if "#Learnings, the last cycle's decision" in start:
        fails.append("the /scope start names a #Learnings decision on a project with none")


def round_options(start: str, head: str) -> list[tuple[str, list[str]]]:
    """Each numbered question of the start's ONE round (the line holding `head`) with its options, Other left out."""
    line = next((ln for ln in start.splitlines() if head in ln), "")
    qs = []
    for m in __import__("re").finditer(r"(?:^|\s)(\d)\. (.*?)(?=\s\d\. |\. Then |$)", line):
        if "(Recommended)" not in m.group(2):
            continue  # a question with no options (the gate line) is not a choice
        opts = [o.strip() for o in m.group(2).split(" · ")]
        qs.append((m.group(1), [o for o in opts if not o.startswith("Other") and not o.startswith('"Other')]))
    return qs


def test_review_24_ops(t: str, fails: list[str]) -> None:
    """2.4 wording review (ops): a re-run of /eval or /learn measures again - the RE-RUN line never says "nothing
    differs: stop" (their rules never change between runs); /scope and /plan carry a decision /learn saved as
    (proposed) as a proposal to offer, never one to apply; every question in the /deploy and /learn rounds has at
    least 2 real options besides Other (Claude Code's question tool takes 2-4). Each shown red before the fix."""
    spine = {"Vision": VISION, "Architecture": ARCHITECTURE, "Evaluation": EVALUATION}
    d = fresh(t, spine)
    states(d, dev_check=("filled", "pass"), test=("filled", "pass"), eval=("filled", "pass"))
    code, start = run(d, "next", "--phase", "eval")
    rerun = next((ln for ln in start.splitlines() if "RE-RUN" in ln), "")
    if "a new measurement" not in rerun or "Nothing differs" in rerun or "keep the earlier" not in rerun:
        fails.append(f"a /eval re-run should measure again and keep the earlier entry, never stop: {rerun!r}")
    lspine = {**spine, "Scope": SCOPE, "Learnings": LEARNINGS}
    d = fresh(t, lspine, LEARN_FILES)
    states(d, ship=("filled", ""), eval=("filled", "pass"), learn=("filled", ""))
    code, start = run(d, "next", "--phase", "learn")
    rerun = next((ln for ln in start.splitlines() if "RE-RUN" in ln), "")
    if "a new cycle" not in rerun or "Nothing differs" in rerun:
        fails.append(f"a /learn re-run should run a new cycle, never stop: {rerun!r}")
    # a decision saved (proposed) is offered, never applied; a kept one is quoted in this phase's document
    kept = "KILL the email digest"
    d = fresh(t, {**lspine, "Learnings": LEARNINGS.replace(kept, kept + " (proposed)")})
    states(d, ship=("filled", ""), eval=("filled", "pass"))
    code, start = run(d, "next", "--phase", "scope")
    if "proposed, not yet kept by the owner" not in start or "never apply it unasked" not in start:
        fails.append(f"a (proposed) #Learnings decision should be offered as (Recommended), never applied: "
                     f"{start[:700]}")
    d = fresh(t, lspine)
    states(d, ship=("filled", ""), eval=("filled", "pass"))
    code, start = run(d, "next", "--phase", "plan")
    if "proposed, not yet kept" in start or "quote the decision line in docs/" not in start \
            or "name each one this run touches" in start:
        fails.append(f"a kept #Learnings decision is quoted in this phase's document: {start[:700]}")
    # every question offers 2+ real options (one real option + Other fails Claude Code's question tool)
    d = fresh(t, {"Vision": VISION, "Architecture": DEPLOY_ARCH, "Plan": DEPLOY_PLAN}, DEPLOY_FILES)
    states(d, dev_check=("filled", "pass"))
    code, dstart = run(d, "next", "--phase", "deploy")
    d = fresh(t, {**spine, "Scope": SCOPE}, LEARN_FILES)
    states(d, ship=("filled", ""), eval=("filled", "pass"))
    code, lstart = run(d, "next", "--phase", "learn")
    for ph, start, head in (("deploy", dstart, "1. why the URL is needed now"), ("learn", lstart, "1. the success metric")):
        qs = round_options(start, head)
        if len(qs) < 3:
            fails.append(f"the /{ph} round was not found in its start: {qs}")
        for n, opts in qs:
            if len(opts) < 2:
                fails.append(f"/{ph} question {n} has one real option besides Other: {opts}")


def main() -> int:
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as t:
        test_companions_24(t, fails)
        test_eval(t, fails)
        test_learn(t, fails)
        test_learn_retro(t, fails)
        test_ship(t, fails)
        test_land(t, fails)
        test_deploy(t, fails)
        test_deploy_rehearsal_secrets(t, fails)
        test_lean_rules(t, fails)
        test_review_findings(t, fails)
        test_review_24_ops(t, fails)
    for f in fails:
        print(f"  x {f}")
    print("OK - the release phases' starts and closes" if not fails else f"FAIL - {len(fails)} problem(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
