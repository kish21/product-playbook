"""Behaviour tests for /build's start and close fixes of #57 (run by tools/check.py, check 53f).

  1. the board card: moved to In Progress at the start and In Review at the record, read back; a Seat filled only
     when empty; another seat's card is a STOP line; no board, no option, no gh -> one line, never "moved";
  3. no ticket id: the start picks the seat's Day-1 ticket, then the next one whose Depends On are built;
  6. the lean run loads SKILL.md only: the full path lives in references/full.md, which the full start names;
  8. "Security review: REQUIRED" never fires on the ticket template's own DoD lines;
  9. the close gate prints /build's close - lean: its five steps; full: no generic `--section-from` step;
 10. the start names the exact per-edit commands from the project's own tools;
 11. LOW findings left unfixed need a grouped issue (--low) or a reason;
 12. the feature doc's top half is checked by `status.py ticket` too (the full path writes it after its gate).
Each case shows the old behaviour red on its own input before the fixed behaviour is asserted green.

    python tools/test_build_close.py      exit 0 = all pass
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
os.environ["PLAYBOOK_BOARD"] = "off"
import status  # noqa: E402
import board  # noqa: E402

TODAY = "2026-10-08"
TEMPLATE = ROOT / "templates" / "feature_ticket_template.md"
EXAMPLE = ROOT / "templates" / "feature-doc-example.md"


def run(d: Path, *args: str) -> tuple[int, str]:
    out, cwd = io.StringIO(), os.getcwd()
    os.chdir(d)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            try:
                code = status.main(["--file", str(d / "STATUS.md"), "--today", TODAY, *args])
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 2
    finally:
        os.chdir(cwd)
    return code, out.getvalue()


# ---- 8. the template's boilerplate DoD lines are not a security surface ------------------------------------------
def security_cases(fails: list[str]) -> None:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    dod = tpl[tpl.index("### 🔒 Definition of Done"):tpl.index("### 🧪 Verification Command")]
    seeder = "# [M1-SEED-01] Two demo customers\n\nSeed two demo customers for the walkthrough.\n\n" + dod
    if not status.SECURITY_TICKET.findall(seeder):
        fails.append("setup: the template's DoD no longer names credentials/auth - this case proves nothing")
    if status.ticket_security_words(seeder):
        fails.append(f"a seeder whose only security words are the template's DoD lines was marked sensitive: "
                     f"{status.ticket_security_words(seeder)}")
    own = seeder + "- [ ] Each tenant sees only its own customers.\n"
    if status.ticket_security_words(own) != ["tenant"]:
        fails.append(f"a ticket line of its own naming a tenant should still count: {status.ticket_security_words(own)}")
    # every phase reads a TICKET's security words the same way (the /test start used the raw pattern on the whole
    # spec, so a seeder showed "security surface: auth, credentials"); the raw pattern stays only for code and diffs
    import re as _re
    src = (ROOT / "tools" / "status.py").read_text(encoding="utf-8")
    raw = [m.group(0) for m in _re.finditer(r"SECURITY_TICKET\.findall\((\w+)\)", src)
           if m.group(1) not in ("own", "added", "text")]
    if raw:
        fails.append(f"a phase matches a ticket's security words without ticket_security_words(): {raw}")


# ---- 1. the board card --------------------------------------------------------------------------------------------
class FakeBoard:
    """A Delivery Board behind the same gql(query, variables) door board.py uses."""

    def __init__(self, status: str = "Todo", seat: str = "", options=("Todo", "In Progress", "In Review", "Done"),
                 broken: str = ""):
        self.status, self.seat, self.options, self.broken, self.sets = status, seat, options, broken, []

    def __call__(self, query: str, variables: dict) -> dict:
        if self.broken:
            raise board.BoardError(self.broken)
        if query.startswith("mutation"):
            name = next(o for o in self.options + ("SR1", "SR2") if f"opt-{o}" == variables["o"])
            self.sets.append((variables["f"], name))
            if variables["f"] == "f-status":
                self.status = name
            else:
                self.seat = name
            return {}
        opts = lambda names: [{"id": f"opt-{n}", "name": n} for n in names]  # noqa: E731
        card = {"id": "item-1", "project": {"id": "p-1", "title": "Demo — Delivery Board",
                                            "status": {"id": "f-status", "options": opts(self.options)},
                                            "seat": {"id": "f-seat", "options": opts(("SR1", "SR2"))}},
                "statusValue": {"name": self.status} if self.status else None,
                "seatValue": {"name": self.seat} if self.seat else None}
        return {"search": {"nodes": [{"number": 28, "title": "[M1-SEED-01] Two demo customers", "state": "OPEN",
                                      "projectItems": {"nodes": [card]}}]}}


def board_cases(fails: list[str]) -> None:
    os.environ.pop("PLAYBOOK_BOARD", None)
    try:
        fb = FakeBoard()
        line = board.move("M1-SEED-01", "In Progress", "SR1", repo="o/r", gql=fb)
        if fb.status != "In Progress" or fb.seat != "SR1" or "reads Status In Progress, Seat SR1 (read back)" not in line:
            fails.append(f"board: a Todo card with no Seat should move to In Progress and take the seat: {line}")
        line = board.move("M1-SEED-01", "In Review", None, repo="o/r", gql=fb)
        if fb.status != "In Review" or "(read back)" not in line:
            fails.append(f"board: the record should move the card to In Review: {line}")
        fb2 = FakeBoard(status="Done", seat="SR1")
        line = board.move("M1-SEED-01", "In Progress", "SR1", repo="o/r", gql=fb2)
        if fb2.sets or "already Done" not in line:
            fails.append(f"board: a card past In Progress must never be pulled back: {line}")
        fb3 = FakeBoard(seat="SR2")
        line = board.move("M1-SEED-01", "In Progress", "SR1", repo="o/r", gql=fb3)
        if fb3.seat != "SR2" or "! its Seat is SR2" not in line or "STOP" not in line:
            fails.append(f"board: another seat's card should be a STOP line and keep its seat: {line}")
        fb4 = FakeBoard(status="In Progress", options=("Todo", "In Queue", "In Progress", "Done"))
        line = board.move("M1-SEED-01", "In Review", None, repo="o/r", gql=fb4)
        if fb4.sets or "no 'In Review' option" not in line or "(read back)" in line:
            fails.append(f"board: a board with no In Review option should say so, never claim a move: {line}")
        line = board.move("M1-SEED-01", "In Progress", None, repo="o/r", gql=FakeBoard(broken="gh lacks the "
                                                                                       "`project` scope"))
        if not line.startswith("Board: not moved - gh lacks") or "by hand" not in line:
            fails.append(f"board: a GitHub that cannot be asked should be ONE line naming the fix: {line}")
        # /ship's card move: the fix is named once, and a timeout never sends the user to re-authenticate
        scope = board.explain("INSUFFICIENT_SCOPES")
        [(kind, line)] = board.move_issue(28, "Done", "o/r", gql=FakeBoard(broken=scope))
        if kind != "FAIL" or line.count("gh auth refresh") != 1:
            fails.append(f"board: a missing scope should name `gh auth refresh` once: {line}")
        [(kind, line)] = board.move_issue(28, "Done", "o/r", gql=FakeBoard(broken="GitHub did not answer in 30s"))
        if kind != "FAIL" or "gh auth" in line or "GitHub did not answer in 30s" not in line:
            fails.append(f"board: a timeout should say so and never send the user to re-authenticate: {line}")
        with tempfile.TemporaryDirectory() as t:
            subprocess.run(["git", "init", "-q"], cwd=t)
            line = board.move("M1-SEED-01", "In Progress", None, base=t, gql=FakeBoard())
            if not line.startswith("Board: none - this project has no GitHub remote"):
                fails.append(f"board: no GitHub remote should say there is no card, and call nothing: {line}")
    finally:
        os.environ["PLAYBOOK_BOARD"] = "off"


# ---- the project used by the start/close cases ----------------------------------------------------------------------
TICKETS_MD = """# Tickets — Demo

## M1 — Customers

| Epic | Lane | Owner | Tickets in build order |
|---|---|---|---|
| `M1-SEED` Demo data | customers | Senior | `M1-SEED-01` two demo customers · `M1-SEED-02` a seeded moment |
| `M1-SCORE` Scoring | scoring | Senior | `M1-SCORE-01` score a customer |

## Lanes

| Lane | Owner | Seat | Epics | Runs alongside |
|---|---|---|---|---|
| customers | Senior | SR1 | `M1-SEED` | scoring |
| scoring | Senior | SR2 | `M1-SCORE` | customers |

## Day 1 — who starts what

| Seat | Lane | Starts | Why it does not wait |
|---|---|---|---|
| SR1 | customers | `M1-SEED-01` two demo customers | depends on nothing |
| SR2 | scoring | `M1-SCORE-01` score a customer | builds against `M1-SEED-01` with a stub |
"""


def ticket_file(tid: str, title: str, depends: str = "None") -> str:
    return (f"# [{tid}] {title}\n\n### 📁 Target Files\n- `app/customers/seed.py`\n- `app/customers/tests/test_seed.py`"
            f"\n\n### 🔗 Depends On\n{depends}\n\n### 🧪 Verification Command\n```bash\npytest -q\n```\n")


def project(d: Path) -> None:
    g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=d)
    code, out = run(d, "init", "--product", "Demo")
    assert code == 0, out
    (d / "TICKETS.md").write_text(TICKETS_MD, encoding="utf-8")
    (d / "docs" / "issues").mkdir(parents=True)
    for tid, title, dep in (("M1-SEED-01", "two demo customers", "None"),
                            ("M1-SEED-02", "a seeded moment", "- `M1-SEED-01`"),
                            ("M1-SCORE-01", "score a customer", "None")):
        (d / "docs" / "issues" / f"{tid}_x.md").write_text(ticket_file(tid, title, dep), encoding="utf-8")
    (d / "pyproject.toml").write_text("[project]\nname='demo'\n\n[tool.ruff]\nline-length = 100\n", encoding="utf-8")
    (d / "uv.lock").write_text("", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=d)
    subprocess.run([*g, "commit", "-qm", "base"], cwd=d)


def start_cases(fails: list[str]) -> None:
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        project(d)
        # 3. no id, seat SR1, nothing built: SR1's Day-1 ticket
        code, out = run(d, "next", "--phase", "build", "--seat", "SR1", "--mode", "lean")
        if code != 0 or "picked M1-SEED-01 - SR1's Day-1 ticket" not in out or "[M1-SEED-01]" not in out:
            fails.append(f"no ticket id: the start should pick SR1's Day-1 ticket and print its start: {out[:500]}")
        # SR2 is never handed SR1's lane
        code, out = run(d, "next", "--phase", "build", "--seat", "SR2", "--mode", "lean")
        if "picked M1-SCORE-01" not in out:
            fails.append(f"no ticket id: SR2 should get its own lane's ticket: {out[:300]}")
        # M1-SEED-01 built (its record committed in this checkout): SR1's next is M1-SEED-02, which waited for it
        st = status.Status.load(d / "STATUS.md")
        picked, why = status.pick_build_ticket(st, "SR1")
        if picked != "M1-SEED-01":
            fails.append(f"pick: with nothing built SR1 should start M1-SEED-01, got {picked}: {why}")
        # M1-SEED-01 recorded on another branch (not in this checkout): M1-SEED-02 still waits for its merge
        st.rows["Tickets"].append(["M1-SEED-01", TODAY, "yes", "x", "1", "x", "docs/features/x.md"])
        picked, why = status.pick_build_ticket(st, "SR1")
        if picked is not None or "waits for M1-SEED-01" not in why:
            fails.append(f"pick: M1-SEED-02 waits for M1-SEED-01, which is not in this checkout - nothing startable: "
                         f"{picked} {why}")
        # 6 + 10 + 8: the lean start names the per-edit commands and no full-path file; the security line is quiet
        code, out = run(d, "next", "--phase", "build", "--ticket", "M1-SEED-01", "--mode", "lean")
        if "Per edit" not in out or "uv run pytest -q app/customers/tests/test_seed.py" not in out \
                or "uv run ruff format app/customers/seed.py" not in out:
            fails.append(f"the start should name the exact per-edit commands from the project's tools: "
                         f"{[l for l in out.splitlines() if 'Per edit' in l or 'ruff' in l or 'pytest' in l][:4]}")
        if "Security review: not required" not in out:
            fails.append("a ticket naming no security surface of its own should not REQUIRE the security review")
        if "references/full.md" in out:
            fails.append("the lean start should not point at the full path's file")
        if "Board: not checked (PLAYBOOK_BOARD=off)" not in out:
            fails.append(f"the start should carry the board line: {[l for l in out.splitlines() if 'Board' in l]}")
        code, out = run(d, "next", "--phase", "build", "--ticket", "M1-SEED-01", "--mode", "full")
        if "Mode: full - open " not in out or "references/full.md now, whole" not in out:
            fails.append(f"the full start should name references/full.md to open whole: {out[:300]}")
        # 9: the close gate's close is /build's own
        os.environ["PLAYBOOK_MODE"] = "lean"
        try:
            code, lean = run(d, "next", "--phase", "build", "--ticket", "M1-SEED-01", "--mode", "lean")
            code, lean = run(d, "rules", "build", "--close")
        finally:
            os.environ.pop("PLAYBOOK_MODE", None)
        code, full = run(d, "next", "--phase", "build", "--ticket", "M1-SEED-01", "--mode", "full")
        code, full = run(d, "rules", "build", "--close")
        if "The close (lean path)" not in lean or "--section-from" in lean or "three short blocks" not in lean \
                or "--low" not in lean or len(lean) > 3000:
            fails.append(f"the lean close gate should print /build's five-step close, short: {lean[:400]}")
        own = full.split("Rules for the close")[0]  # the rule files' own words follow, quoted as they are
        if "--section-from" in own or "set <phase>" in own or "The close, in this order" not in own:
            fails.append(f"the full close should be /build's, never the generic `set <phase> --section-from`: "
                         f"{full[:400]}")


# ---- 11 + 12: the record checks the LOW findings and the feature doc's top half -------------------------------------
def record_cases(fails: list[str]) -> None:
    review_low = ("| Severity | Where | What goes wrong | Fixed by |\n|---|---|---|---|\n"
                  "| MEDIUM | app/x.py:3 | a rerun corrupts scoring | fixed in 1a2b3c4 |\n"
                  "| LOW | app/db.py:9 | the shared session is never closed | recorded, not patched (outside the ticket) |\n")
    gap, note = status.low_findings(review_low, None, "M1-SEED-01")
    if "1 LOW finding(s)" not in gap or "gh issue create" not in gap or "--low" not in gap:
        fails.append(f"an unfixed LOW finding with no --low should be a gap naming the grouped issue: {gap}")
    gap, note = status.low_findings(review_low, "#41", "M1-SEED-01")
    if gap or "#41" not in note:
        fails.append(f"--low \"#41\" should clear the gap and be said in the close: {gap} / {note}")
    gap, _ = status.low_findings(review_low.replace("recorded, not patched (outside the ticket)", "fixed in 9f8e7d6"),
                                 None, "M1-SEED-01")
    if gap:
        fails.append(f"a LOW finding fixed by a commit needs no issue: {gap}")
    bad = "# Demo\n\n## In short\nIt seeds `late_walkin` via seed_service.py (R3).\n"
    if not status.feature_doc_gaps("docs/features/demo.md", bad):
        fails.append("`status.py ticket` should refuse a feature doc whose top half is written for the agent")
    if status.feature_doc_gaps("docs/features/demo.md", EXAMPLE.read_text(encoding="utf-8")):
        fails.append("`status.py ticket` should accept the template's example feature doc")
    if status.feature_doc_gaps("docs/records/M1-SEED-01.md", bad):
        fails.append("a per-ticket record #Project policy names is not a feature doc: no top-half check")


# ---- 6: SKILL.md is the lean path; the full path is its own file ------------------------------------------------------
def skill_cases(fails: list[str]) -> None:
    skill = (ROOT / "commands" / "build" / "SKILL.md").read_text(encoding="utf-8")
    full = ROOT / "commands" / "build" / "references" / "full.md"
    if not full.is_file() or "## Step 0" not in full.read_text(encoding="utf-8"):
        fails.append("commands/build/references/full.md should hold the full path (Step 0 onwards)")
    if "## Step 0" in skill or "## Contract" in skill or len(skill) > 6000:
        fails.append(f"SKILL.md should hold only the lean path and the pointer ({len(skill)} chars): a lean run loads "
                     f"it whole")
    if "references/full.md" not in skill:
        fails.append("SKILL.md should say where the full path is")


def cost_cases(fails: list[str]) -> None:
    """#57 item 5: `show --cost` sums Claude Code's own totals per milestone, from the conversations that started or
    recorded a ticket; a conversation still open is counted apart; no logs at all is one line saying so."""
    import json
    sc = status.session_costs()
    real = sc.project_log_dir
    with tempfile.TemporaryDirectory() as t:
        logs, proj = Path(t) / "logs", Path(t) / "proj"
        logs.mkdir()
        proj.mkdir()
        ended = lambda usd: json.dumps({"type": "cost-state", "totalCostUSD": usd})  # noqa: E731
        call = lambda cmd: json.dumps({"type": "assistant", "message": {"id": cmd, "content": [  # noqa: E731
            {"type": "tool_use", "name": "Bash", "input": {"command": cmd}}]}})
        (logs / "a.jsonl").write_text("\n".join([call('python "x/status.py" next --phase build --ticket M1-SEED-01'),
                                                 call('python "x/status.py" ticket M1-SEED-01 --commit'),
                                                 ended(1.5)]), encoding="utf-8")
        (logs / "b.jsonl").write_text("\n".join([call("python status.py ticket M1-SCORE-01"), ended(0.5)]),
                                      encoding="utf-8")
        (logs / "c.jsonl").write_text("\n".join([call("python status.py next --phase build --ticket M2-PAY-01"),
                                                 call("python status.py ticket M1-SCORE-02"), ended(2.0)]),
                                      encoding="utf-8")
        (logs / "d.jsonl").write_text(call("python status.py next --phase build --ticket M2-PAY-02"), encoding="utf-8")
        (logs / "e.jsonl").write_text("\n".join([call("python status.py next --phase vision"), ended(9.0)]),
                                      encoding="utf-8")
        sc.project_log_dir = lambda base: logs
        try:
            out = "\n".join(status.milestone_costs(proj))
        finally:
            sc.project_log_dir = real
        for want in ("  M1: $3.00 · 3 conversation(s) · 3 ticket(s): M1-SCORE-01, M1-SCORE-02, M1-SEED-01",
                     "  M2: $1.00 · 1 conversation(s) · 1 ticket(s): M2-PAY-01",
                     "(1 conversation(s) still open", "an API-equivalent estimate, not a bill"):
            if want not in out:
                fails.append(f"cost: `show --cost` lacks {want!r}: {out}")
        if "$9" in out or "$12" in out:
            fails.append(f"cost: a conversation that built no ticket was counted: {out}")
        sc.project_log_dir = lambda base: Path(t) / "none"
        try:
            out = "\n".join(status.milestone_costs(proj))
        finally:
            sc.project_log_dir = real
        if not out.startswith("Cost per milestone: not recorded"):
            fails.append(f"cost: no logs should be one 'not recorded' line: {out}")
        run(proj, "init", "--product", "Demo")
        code, shown = run(proj, "show", "--cost")
        if "Cost per milestone" not in shown:
            fails.append(f"cost: `status.py show --cost` prints no cost line: {shown[-300:]}")


def reviewer_cases(fails: list[str]) -> None:
    """#58 item 2: the lean start names ONE independent reviewer (a fresh context that did not write the code) in the
    tool's own route, with its brief; a tool with no helper agent gets the stated fallback (self-review, never a
    security sign-off); Claude Code with no security surface needs no helper (`/code-review` starts its own)."""
    if not (ROOT / "agents" / "build-reviewer.md").is_file():
        fails.append("the reviewer's brief agents/build-reviewer.md is missing")
    real = status.playbook_tool
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        project(d)
        code, out = run(d, "next", "--phase", "build", "--ticket", "M1-SEED-01", "--mode", "lean")
        if "Reviewer: `/code-review` (it starts its own reviewer with a fresh context)" not in out:
            fails.append(f"reviewer: Claude with no security surface should name /code-review alone: "
                         f"{[l for l in out.splitlines() if 'Reviewer' in l]}")
        try:
            for tool, want, fallback in (
                    ("claude", "the agent whose name ends `build-reviewer`", False),
                    ("codex", "spawn_agent - this skill explicitly asks you to spawn ONE reviewer agent", True),
                    ("cursor", "a Task sub-agent: `build-reviewer`", True),
                    ("antigravity", "`invoke_subagent` - ONLY if it is in your tool list", True)):
                status.playbook_tool = lambda tool=tool: tool
                line = status.reviewer_line(d, "M1-SEED-01", "m1-seed-01-x", True)
                if want not in line or "build-reviewer.md" not in line or "review-stretch.md §In the helper" not in line \
                        or "never edits" not in line:
                    fails.append(f"reviewer ({tool}): the start should name its route, brief and rules: {line}")
                if fallback != ("record `self-review` - a self-review never signs off security" in line):
                    fails.append(f"reviewer ({tool}): the no-helper fallback {'missing' if fallback else 'not needed'}:"
                                 f" {line}")
                if ("`code and security`" in line) != (tool != "claude"):
                    fails.append(f"reviewer ({tool}): a tool without /code-review gives the helper both reviews: {line}")
                if tool == "claude" and "run_in_background: true" not in line:
                    fails.append(f"reviewer (claude): the helper must run in the background, or `/code-review` "
                                 f"meanwhile cannot overlap it: {line}")
            # 2.4 review: off Claude with no security surface the helper is given `code` - its brief must know it,
            # and must never tell the helper to call a review command it has no tool for
            brief = (ROOT / "agents" / "build-reviewer.md").read_text(encoding="utf-8")
            for tool in ("codex", "cursor", "antigravity"):
                status.playbook_tool = lambda tool=tool: tool
                line = status.reviewer_line(d, "M1-SEED-01", "b", False)
                which = line.split("the review `", 1)[1].split("`", 1)[0] if "the review `" in line else None
                if not which or f"**{which}**" not in brief:
                    fails.append(f"reviewer ({tool}): the brief does not know the review it is given: {which!r}")
            if "Never call a review command" not in brief or "run it here, as your own work" in brief:
                fails.append("the reviewer's brief should review by hand, never call a review command (it has no "
                             "Skill tool)")
        finally:
            status.playbook_tool = real


def numbered_doc_cases(fails: list[str]) -> None:
    """#60: the feature doc numbers its headings (`### 5.4 Review`); /ship's start still finds the review part."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        (d / "docs" / "features").mkdir(parents=True)
        (d / "docs" / "features" / "x.md").write_text(
            "# X\n\n---\n\n## 5. For developers and coding agents\n\n### 5.4 Review\n\nR1 1 finding\n\n"
            "| LOW | `a.py:1` | slow | fixed abc1234 |\n", encoding="utf-8")
        got = status.feature_review(d, "docs/features/x.md")
        if "R1 1 finding" not in got or "a.py:1" not in got:
            fails.append(f"numbered: `### 5.4 Review` should be read as the review part: {got!r}")


def main() -> int:
    fails: list[str] = []
    for case in (security_cases, board_cases, start_cases, record_cases, skill_cases, cost_cases, reviewer_cases,
                 numbered_doc_cases):
        try:
            case(fails)
        except Exception as e:  # a crash is a failure with its cause, never a silent pass
            fails.append(f"{case.__name__} crashed: {type(e).__name__}: {e}")
    for f in fails:
        print(f"  x {f}")
    print("OK - /build's start and close (#57) behave" if not fails else f"FAIL - {len(fails)} /build close test(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
