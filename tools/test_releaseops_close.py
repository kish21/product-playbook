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
    "docs/evaluation.md": "# Evaluation\n\n## Baseline\n\nThe #Vision accuracy bar, 90%, is the baseline.\n"
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
                 "refuses, every problem in one list", "Round 1", "\"Looks good - save (Recommended)\"",
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
    if "NOT PASSED: /test" not in start or "status.py bypass --from eval --gate <phase>" not in start:
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
               "docs/learnings.md": "# Learnings\n\n## Cycle 2026-10-06\n\nInterviews with 6 pilot consultants.\n"
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
                 "refuses, every problem in one list", "\"Keep as proposed - save (Recommended)\"",
                 "never record it unseen", "set learn filled --section-from <file> --commit", "Run only", "§Production "
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
                 "## Composed skills", "it starts no new feature", "Run only", "the save goes in the same message"):
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
- **Rollback path:** redeploy the previous build from the host's deploy list; migrations are forward-only (docs/deployment.md §7).
- **Known gaps:** none.
"""
DEPLOY_DOC = """\
# Deployment

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

Redeploy the previous build from the deploy list; migrations are forward-only.

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
                 "render.yaml", "all eight `##` sections", "never writes or asks for a secret",
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


def main() -> int:
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as t:
        test_eval(t, fails)
        test_learn(t, fails)
        test_ship(t, fails)
        test_deploy(t, fails)
        test_lean_rules(t, fails)
        test_review_findings(t, fails)
    for f in fails:
        print(f"  x {f}")
    print("OK - the release phases' starts and closes" if not fails else f"FAIL - {len(fails)} problem(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
