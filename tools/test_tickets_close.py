"""tools/test_tickets_close.py - /tickets' one start command and its close in code (P1, P17, P20, P25, P37, P43, P45).

A logged Claude /tickets run took 38 calls and 6.84M tokens: rule files read whole, five section reads, a 33K-character
grep of the contract files, three calls to find the templates, a checker of its own, a commit the hook refused, and
two owner decisions guessed from "proceed". Now `next --phase tickets` prints what the backlog derives from and the
two question rounds; `set tickets filled --commit` checks docs/issues/ and TICKETS.md, every problem in one list, and
saves; `--dry-run` lists the same gaps and writes nothing.

The project below is the record a model would realistically write for a B2B HR product with a read-only AI agent, a
Python monolith in six module lanes, built by two people with coding agents (P17: no saved run of this skill on the
current test project exists). It must close the first time; each check is shown red by breaking exactly what it
checks; a copy with every fault at once is refused in ONE list.
Run: python tools/test_tickets_close.py   (check.py runs it, check 36b)
"""
from __future__ import annotations

import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import status  # noqa: E402

TODAY = "2026-10-06"

PLAN = """\
- **Phases / milestones (core first):**
  - M1 — Core slice: one fake employee, two months; the agent finds the causes and drafts the reply in one language; the consultant approves or edits it on screen; the log records outcome and times.
  - M2 — Trustworthy drafts: known-answer set; Dutch + French; "not sure" hold; cost cap; stop switch; AI-drafted label; prompt-injection defence.
  - M3 — Usability check + baseline: consultants attempt the core task unaided on fake data; today's no-tool time measured.
  - M4 — Pilot: go live via `/deploy` with the company login for the 5–10 consultant pilot team.
- **Timeline:**
  - Capacity: two developers, each with an AI coding agent, about 15 h a week each. Start: 2026-10-05.
  - M1 2026-10-05 → 2026-10-23 · M2 2026-10-26 → 2026-11-20 · M3 2026-11-23 → 2026-12-04 · M4 2026-12-07 → 2027-06-30.
- **Exit criteria per milestone:**
  - M1: for one fake employee, the consultant sees a draft listing each cause, its amount and the rule behind it, approves or edits it, every figure matches the fake payroll data, and the log shows the outcome and times.
  - M2: every known-answer case matches in Dutch and French; a mismatch is held as "not sure"; a run over €0.10 stops; the stop switch turns drafting off; planted injection text changes nothing.
  - M3: at least 5 consultants complete the core task unaided; today's no-tool time is measured.
  - M4: the pilot team signs in with the company login at a public URL.
- **Four-risks row per milestone (value · usability · feasibility · viability):**
  - M1: feasibility — the end-to-end draft with exact figures works on one employee.
- **Detail:** `docs/plan.md` (reasoning + workings; this section stays a RECORD)
- **Read (file · date · verbatim quote):** Read: none - only PRODUCT.md sections
"""
SCOPE = """\
- **THE core feature (the one thing):** The agent finds why an employee's net pay changed between two months and drafts the reply with each cause, its amount and the rule behind it. The consultant approves or edits it.
- **Non-goals (deliberately never building):**
  - Sending the reply to the client automatically — never, a consultant approves every reply.
  - Changing payroll data — never, the agent is read-only.
"""
CONTRACTS = """\
- **Typed models / schemas / migrations:** Pydantic v2 at every boundary; SQLAlchemy Core tables; Alembic.
  - Schemas: `app/payroll/schemas.py` · `app/explain/schemas.py` · `app/agent/schemas.py` · `app/review/schemas.py`
  - Tables: `app/audit/store.py`; migrations: `migrations/versions/0002_domain.py`
  - Routes (declared, 501 until `/build`): `app/review/routes.py`, registered in `app/main.py`.
  - `evidence: uv run pytest app/payroll/tests/test_contracts.py → 9 passed · app/payroll/schemas.py · 2026-10-05`
- **Boundary units/scale agreed:** money is integer euro cents (`*_cents`); time is aware UTC.
"""
FILES = {
    "app/payroll/schemas.py": '''"""Payroll contracts: read-only, one employee, two months."""
from pydantic import BaseModel


class PayslipLine(BaseModel):
    code: str
    label: str
    amount_cents: int


class PayslipMonth(BaseModel):
    employee_id: str
    month: str
    gross_cents: int
    net_cents: int
    lines: list[PayslipLine]


class PayrollSource:
    def two_months(self, employee_id: str, month: str) -> tuple[PayslipMonth, PayslipMonth]: ...
''',
    "app/explain/schemas.py": '''from pydantic import BaseModel


class Cause(BaseModel):
    code: str
    amount_cents: int
    rule: str


class NetPayDifference(BaseModel):
    employee_id: str
    delta_cents: int
    causes: list[Cause]
''',
    "app/agent/schemas.py": '''from enum import Enum

from pydantic import BaseModel


class DraftStatus(str, Enum):
    ready = "ready"
    not_sure = "not_sure"
    stopped = "stopped"


class Draft(BaseModel):
    draft_id: str
    employee_id: str
    language: str
    body: str
    status: DraftStatus
    cost_cents: int
''',
    "app/review/schemas.py": '''from pydantic import BaseModel


class Decision(BaseModel):
    draft_id: str
    approved: bool
    edited_body: str | None = None
''',
    "app/review/routes.py": '''from fastapi import APIRouter

router = APIRouter()


@router.get("/drafts/{draft_id}")
def show_draft(draft_id: str): ...


@router.post("/drafts/{draft_id}/decision")
def decide(draft_id: str): ...
''',
    "app/audit/store.py": '''from sqlalchemy import Column, Integer, MetaData, String, Table

metadata = MetaData()
agent_events = Table("agent_events", metadata, Column("id", Integer), Column("draft_id", String),
                     Column("outcome", String), Column("seconds_to_decision", Integer))
''',
    "migrations/versions/0002_domain.py": "revision = '0002'\n",
    "app/main.py": "def create_app(): ...\n",
    "config/settings.py": "class Settings: ...\n",
}
STRUCTURE = """\
# STRUCTURE

Domain modules in app/, one lane each.

## Modules

| Path | What it is for | Depends on |
|---|---|---|
| `app/auth/` | Company login over OIDC, the consultant role check. Its own `tests/`. | `app/platform/` |
| `app/payroll/` | Read-only access to one employee's payslips for two months. Its own `tests/`. | `app/platform/` |
| `app/explain/` | Computes the net-pay difference, each cause, its amount and its rule. Its own `tests/`. | `app/payroll/` |
| `app/agent/` | The drafting agent: loop, caps, kill switch, guards, adapters. Its own `tests/`. | `app/explain/` |
| `app/review/` | The consultant's review screen: approve or edit. Its own `tests/`. | `app/agent/` |
| `app/audit/` | Append-only `agent_events` log and each draft's outcome and times. Its own `tests/`. | `app/platform/` |

## Hub files

| Path | Why every lane touches it (by one line) |
|---|---|
| `app/main.py` | The registry — each module adds one `register_<module>(app)` line. |
| `config/settings.py` | The typed config loader — a new knob adds one field. |
"""
TICKET = """\
<!-- Ticket file = issue body (docs/issues/). Written by /tickets from the backlog confirmed {today}; plan in TICKETS.md. -->

# [{tid}] {title}

### 🎯 Goal
**{ms}.** {goal}

### 🧭 Slice Strategy
- [x] ↕️ Vertical — thin end-to-end increment, demoable on merge
- [ ] ↔️ Horizontal — single architectural layer
- [ ] 🐛 Ad-hoc — bug · edge-case · tech-debt · security

### 🗂️ Epic
[{epic}] {epic_name}

### 🛣️ Lane
{lane}

### 👤 Owner
Senior

### 🧱 Layer(s)
- [x] ⚙️ Pure domain service — business logic, state transitions, validation
- [x] 🧪 Cross-layer verification — integration across the real seam, adversarial/security

### 📁 Target Files
{targets}

### 🔌 Contract — Inputs → Outputs
- **Consumes:**
{consumes}
- **Exposes:**
{exposes}

### 🔗 Depends On
{depends}

### 🧩 Builds Against
{builds}

### 👀 Demo — what works after this merges
{demo}

### 🛠️ Implementation Tasks
- [ ] 1. Write the failing test first, then the code in the files above.
- [ ] 2. Update the feature doc.

### 🔒 Definition of Done (security included)
- [ ] Inputs validated at the boundary (no injection, no raw HTML, no unvalidated payloads).
- [ ] No secrets in source — config and credentials in `.env` only, read through `config/settings.py`.
- [ ] No swallowed errors; fallbacks fail **closed** on anything auth- or security-related.
- [ ] Payroll data is fake and never logged in full.
- [ ] Tests written and passing for everything this ticket touches; `just check` green.
- [ ] **Mergeable alone** — a PR containing only these files is reviewable on its own, and the PR carries its `lane: {lane}` label.

### 🧪 Verification Command
```bash
uv run pytest {test}
```
"""
# (ID, title, epic, epic name, lane, targets, consumes, exposes, depends, builds against, demo)
BACKLOG = [
    ("M1-PAY-01", "Consultant loads one fake employee's two months", "M1-PAY", "Payslips arrive", "payroll",
     ["app/payroll/service.py", "app/payroll/adapters/fake_source.py", "app/payroll/tests/test_two_months.py",
      "docs/features/payslips.md"],
     ["`PayrollSource.two_months`", "`PayslipMonth`"], ["(new) `load_two_months(employee_id, month) -> tuple[PayslipMonth, PayslipMonth]`"],
     "None", "None", "Run the fake source for employee E-001: two typed months come back, net 2,431.18 and 2,388.40 EUR."),
    ("M1-EXPL-01", "Net-pay difference split into causes with amount and rule", "M1-EXPL", "Causes are computed",
     "explain", ["app/explain/service.py", "app/explain/tests/test_causes.py", "docs/features/causes.md"],
     ["`PayslipMonth.lines`", "`NetPayDifference`", "`Cause.rule`"], ["(new) `explain(before, after) -> NetPayDifference`"],
     "None", "M1-PAY-01", "For E-001 the difference -42.78 EUR splits into two causes, each with its amount and rule."),
    ("M1-DRAFT-01", "Agent drafts the reply from the computed causes", "M1-DRAFT", "Drafts are written", "agent",
     ["app/agent/loop.py", "app/agent/tools/get_causes.py", "app/agent/tests/test_draft.py", "docs/features/drafts.md"],
     ["`NetPayDifference.causes`", "`Draft`", "`DraftStatus.ready`"], ["(new) `draft_reply(employee_id, month) -> Draft`"],
     "M1-EXPL-01", "None", "A draft for E-001 names both causes with their amounts; every figure equals the computed one."),
    ("M1-REV-01", "Consultant approves a draft", "M1-REV", "Consultant decides", "review",
     ["app/review/service.py", "app/review/templates/draft.html", "app/review/tests/test_approve.py",
      "docs/features/review.md"],
     ["`show_draft`", "`decide`", "`Decision.approved`"], ["(new) `approve(draft_id, consultant) -> Decision`"],
     "None", "M1-DRAFT-01", "Open /drafts/D-1 with a stub draft, press Approve: the draft reads approved."),
    ("M1-REV-02", "Consultant edits a draft before approving", "M1-REV", "Consultant decides", "review",
     ["app/review/service.py", "app/review/templates/draft.html", "app/review/tests/test_edit.py",
      "docs/features/review.md"],
     ["`Decision.edited_body`"], ["(new) `edit_and_approve(draft_id, consultant, body) -> Decision`"],
     "M1-REV-01", "None", "Change one sentence of the draft, approve it: the stored decision holds the edited text."),
    ("M1-LOG-01", "Each draft's outcome and times are logged", "M1-LOG", "Outcomes are logged", "audit",
     ["app/audit/service.py", "app/audit/tests/test_outcome_log.py", "docs/features/outcome-log.md"],
     ["`agent_events`", "`Decision`"], ["(new) `record_outcome(draft_id, outcome, seconds) -> None`"],
     "None", "M1-REV-01", "Approve a draft: one agent_events row with its outcome and the seconds to decision."),
    ("M1-AUTH-01", "Consultant signs in on the dev stub, refused outside dev", "M1-AUTH", "Consultants sign in",
     "auth", ["app/auth/service.py", "app/auth/adapters/dev_stub.py", "app/auth/tests/test_dev_login.py",
              "docs/features/sign-in.md"],
     ["`Settings`"], ["(new) `current_consultant(request) -> Consultant`"],
     "None", "None", "In ENV=dev the stub signs a consultant in; with ENV=prod the same request gets 401."),
    ("M2-SURE-01", "A figure that does not match holds the draft as not sure", "M2-SURE", "Drafts stay true",
     "agent", ["app/agent/guards/figures.py", "app/agent/tests/test_not_sure.py", "docs/features/not-sure.md"],
     ["`Draft.status`", "`DraftStatus.not_sure`", "`Cause.amount_cents`"], ["(new) `check_figures(draft, difference) -> Draft`"],
     "None", "None", "Plant a wrong amount in a draft: it is held as not sure and never reaches the screen as ready."),
    ("M2-CAP-01", "A run over EUR 0.10 stops and says so", "M2-SURE", "Drafts stay true", "agent",
     ["app/agent/guards/cost_cap.py", "app/agent/tests/test_cost_cap.py", "docs/features/cost-cap.md"],
     ["`Draft.cost_cents`", "`DraftStatus.stopped`"], ["(new) `enforce_cap(run) -> None`"],
     "M2-SURE-01", "None", "A run priced at 11 cents stops; the consultant sees 'stopped: over the cost cap'."),
]
TICKETS_MD = """\
# Tickets — HR drafting

> The plan: epics, lanes, and who starts what. Status lives on GitHub, on the Delivery Board, and never in this file.

## M1 — Core slice

| Epic | Lane | Owner | Tickets in build order |
|---|---|---|---|
| `M1-PAY` Payslips arrive | payroll | Senior | `M1-PAY-01` Consultant loads one fake employee's two months |
| `M1-EXPL` Causes are computed | explain | Senior | `M1-EXPL-01` Net-pay difference split into causes with amount and rule |
| `M1-DRAFT` Drafts are written | agent | Senior | `M1-DRAFT-01` Agent drafts the reply from the computed causes |
| `M1-REV` Consultant decides | review | Senior | `M1-REV-01` Consultant approves a draft · `M1-REV-02` Consultant edits a draft before approving |
| `M1-LOG` Outcomes are logged | audit | Senior | `M1-LOG-01` Each draft's outcome and times are logged |
| `M1-AUTH` Consultants sign in | auth | Senior | `M1-AUTH-01` Consultant signs in on the dev stub, refused outside dev |

## M2 — Trustworthy drafts

| Epic | Lane | Owner | Tickets in build order |
|---|---|---|---|
| `M2-SURE` Drafts stay true | agent | Senior | `M2-SURE-01` A figure that does not match holds the draft as not sure · `M2-CAP-01` A run over EUR 0.10 stops and says so |

## M3 — Usability check + baseline

M3: no tickets - a usability session and a time measurement the owner runs on M2's build (evidence, not code).

## M4 — Pilot

M4: no tickets - go-live and the company login connection are /deploy's (handed to later phases below).

## Lanes

| Lane | Owner | Epics | Runs alongside |
|---|---|---|---|
| payroll | Senior | `M1-PAY` | auth, audit |
| explain | Senior | `M1-EXPL` | auth, audit |
| agent | Senior | `M1-DRAFT`, `M2-SURE` | review, audit |
| review | Senior | `M1-REV` | agent |
| audit | Senior | `M1-LOG` | payroll, explain |
| auth | Senior | `M1-AUTH` | payroll, explain |

## Coordination points

- `M1-EXPL-01` (explain) builds against `M1-PAY-01` (payroll) — `PayslipMonth` is frozen; a stub pair of months is enough.
- `M1-DRAFT-01` (agent) waits for `M1-EXPL-01` (explain) to merge — the draft narrates the computed causes.
- `M1-REV-01` (review) builds against `M1-DRAFT-01` (agent) — `Draft` is frozen; a stub draft is enough.
- `M1-LOG-01` (audit) builds against `M1-REV-01` (review) — `Decision` is frozen.

## Hub files

- `app/main.py` — every lane adds one register line.
- `config/settings.py` — auth and agent add one field each.

## Flow graph

```mermaid
flowchart LR
  lane_payroll["payroll · Senior"]
  lane_explain["explain · Senior"]
  lane_agent["agent · Senior"]
  lane_review["review · Senior"]
  lane_audit["audit · Senior"]
  lane_auth["auth · Senior"]
  lane_payroll -.->|"M1-EXPL-01 builds against M1-PAY-01"| lane_explain
  lane_explain -->|"M1-DRAFT-01 waits for M1-EXPL-01"| lane_agent
  lane_agent -.->|"M1-REV-01 builds against M1-DRAFT-01"| lane_review
  lane_review -.->|"M1-LOG-01 builds against M1-REV-01"| lane_audit
```

Solid arrow: wait for the merge. Dotted arrow: build against the contract — a stub is enough to start.

## Day 1 — who starts what

| Seat | Lane | Starts | Why it does not wait |
|---|---|---|---|
| SR1 | payroll | `M1-PAY-01` Consultant loads one fake employee's two months | depends on nothing |
| SR2 | explain | `M1-EXPL-01` Net-pay difference split into causes | builds against `M1-PAY-01` with a stub |
| — | agent | nothing on day one | `M1-DRAFT-01` waits for `M1-EXPL-01` to merge |
| SR2 (after M1-EXPL-01) | auth | `M1-AUTH-01` Consultant signs in on the dev stub | depends on nothing |

## Handed to later phases

- The company login connection and the public URL → `/deploy`, at M4.
"""


def run(d: Path, *args: str) -> tuple[int, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = status.main(["--file", str(d / "STATUS.md"), "--today", TODAY, *args])
    return code, out.getvalue() + err.getvalue()


def ticket_text(row: tuple) -> str:
    tid, title, epic, epic_name, lane, targets, consumes, exposes, depends, builds, demo = row
    return TICKET.format(today=TODAY, tid=tid, title=title, ms=tid.split("-")[0], goal=title + ".", epic=epic,
                         epic_name=epic_name, lane=lane, targets="\n".join(f"- [ ] `{t}`" for t in targets),
                         consumes="\n".join(f"  - {c}" for c in consumes), exposes="\n".join(f"  - {e}" for e in exposes),
                         depends=depends, builds=builds, demo=demo,
                         test=next((t for t in targets if "test" in t), "app"))


def project(d: Path, backlog=BACKLOG, tickets_md: str = TICKETS_MD, extra: dict[str, str] | None = None) -> None:
    for rel, text in FILES.items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text(text, encoding="utf-8")
    (d / "PRODUCT.md").write_text("# PRODUCT\n\n## Scope\n" + SCOPE + "\n## Plan\n" + PLAN + "\n## Contracts\n"
                                  + CONTRACTS + "\n## Dev-complete\n", encoding="utf-8")
    (d / "STRUCTURE.md").write_text(STRUCTURE, encoding="utf-8")
    shutil.rmtree(d / "docs" / "issues", ignore_errors=True)
    (d / "docs" / "issues").mkdir(parents=True)
    for row in backlog:
        slug = row[1].lower().replace(" ", "-").replace("'", "")[:40]
        (d / "docs" / "issues" / f"{row[0]}_{slug}.md").write_text(ticket_text(row), encoding="utf-8")
    (d / "TICKETS.md").write_text(tickets_md, encoding="utf-8")
    for rel, text in (extra or {}).items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text(text, encoding="utf-8")


def edit(tid: str, **kw) -> list[tuple]:
    keys = ("tid", "title", "epic", "epic_name", "lane", "targets", "consumes", "exposes", "depends", "builds", "demo")
    return [tuple(kw.get(k, v) for k, v in zip(keys, row)) if row[0] == tid else row for row in BACKLOG]


def main() -> int:
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        project(d)
        code, out = run(d, "init", "--product", "HR drafting")
        status.Status.load  # noqa: B018 - the module loaded
        # the realistic record closes the first time
        gaps = status.tickets_gaps(d)
        if gaps:
            fails.append(f"the realistic HR backlog should pass /tickets' check: {gaps}")

        # the one start: what the backlog derives from, the rounds, the shape, the refusals - and readable on Claude
        code, start = run(d, "next", "--phase", "tickets")
        for want in ("set tickets filled --commit", "--dry-run", "Round 1",
                     "Round 2", "1. Who builds: how many seats", "\"Looks good - write and save\" / \"Change something\"", "PayslipMonth(employee_id",
                     "decide() [POST /drafts/{draft_id}/decision]", "agent_events(table: id, draft_id",
                     "STRUCTURE.md ## Modules", "STRUCTURE.md ## Hub files", "M1 — Core slice",
                     "### 🛣️ Lane", "refuses, every problem in one list", "§Waiting or building against",
                     "Remote: none", "never a reason in your words", "does not draw docs/issues/ yet",
                     "never product code"):
            if want not in start:
                fails.append(f"the /tickets start lacks {want!r}")
        for banned in ("Four-risks row", "Read (file · date", "close with, in order", "--section-from <file>"):
            if banned in start:
                fails.append(f"the /tickets start should not carry {banned!r} (not used by this phase)")
        if len(start) > 30000:
            fails.append(f"the /tickets start is {len(start)} characters - Claude Code shows 30,000")
        if "0002_domain" in start:
            fails.append("the start lists a migration's internals as names a ticket consumes")
        code, rules = run(d, "rules", "tickets")
        if "## §Size by behaviour" not in rules or "## §The flow graph" not in rules:
            fails.append(f"`rules tickets` should print the slicing and TICKETS.md rules word for word: {rules[:200]}")

        # --dry-run on the good record: no gap, nothing written
        before = (d / "STATUS.md").read_text(encoding="utf-8")
        code, out = run(d, "set", "tickets", "filled", "--dry-run")
        if code != 0 or "DRY RUN - nothing written. no gap" not in out or \
                (d / "STATUS.md").read_text(encoding="utf-8") != before:
            fails.append(f"set tickets filled --dry-run on a clean backlog: {code} {out[:300]}")

        # each check red alone: break exactly what it checks
        hub_less = TICKETS_MD.replace("- `config/settings.py` — auth and agent add one field each.\n", "")
        breaks = (
            ("T1", dict(backlog=edit("M1-PAY-01", targets=["app/payroll/", "docs/features/payslips.md",
                                                           "app/payroll/tests/test_x.py"])), "names no exact target file"),
            ("T2", dict(backlog=edit("M1-PAY-01", lane="backend")), "M1-PAY-01=backend"),
            ("T5", dict(backlog=edit("M1-DRAFT-01", consumes=["`PayrollGateway`"])), "M1-DRAFT-01:PayrollGateway"),
            ("T8", dict(extra={"docs/issues/notes.md": "# notes\n"}), "notes.md"),
            ("T9", dict(extra={"docs/issues/M1-PAY-01_copy.md": ticket_text(BACKLOG[0])}),
             "ID is used by two files (dedup matches the ID): M1-PAY-01"),
            ("T10", dict(extra={"docs/issues/M1-AUTH-01_consultant-signs-in-on-the-dev-stub,-refuse.md":
                                "---\ntitle: x\n---\n" + ticket_text(BACKLOG[6])}), "opens with front matter"),
            ("T12", dict(backlog=edit("M1-LOG-01", targets=["app/audit/service.py", "app/audit/tests/test_o.py",
                                                            "docs/features/outcome-log.md", "CHANGELOG.md"])),
             "lists a spine file or TICKETS.md"),
            ("T13", dict(backlog=edit("M1-LOG-01", targets=["app/audit/service.py", "app/audit/tests/test_o.py"])),
             "lists no docs/features/<feature>.md"),
            ("T13b", dict(backlog=edit("M1-LOG-01", targets=["app/audit/service.py", "docs/features/outcome-log.md"])),
             "lists no test file"),
            ("T15", dict(backlog=edit("M2-CAP-01", demo="n/a")), "vertical slice with no Demo"),
            ("T16", dict(backlog=edit("M1-REV-01", depends="M1-REV-02")), "Depends On cycle"),
            ("T17", dict(backlog=edit("M1-REV-02", depends="None")),
             "M1-REV-01+M1-REV-02:app/review/service.py"),
            ("T17b", dict(backlog=[r if r[0] not in ("M1-PAY-01", "M1-AUTH-01") else r[:5] + (r[5] + ["config/settings.py"],)
                                   + r[6:] for r in BACKLOG], tickets_md=hub_less),
             "M1-AUTH-01+M1-PAY-01:config/settings.py"),
            ("T18", dict(tickets_md=TICKETS_MD.replace('  lane_auth["auth · Senior"]\n', "")),
             "no `lane_<name>[\"<name> · <owner>\"]` box for lane(s) auth"),
            ("T19", dict(tickets_md=TICKETS_MD.replace("| SR1 | payroll |", "| SR1 ✅ | payroll |")), "status mark"),
            ("T20", dict(extra={"docs/issues/README.md": "# old plan\n"}), "docs/issues/README.md remains"),
            ("T21", dict(tickets_md=TICKETS_MD.replace("| — | agent | nothing on day one | `M1-DRAFT-01` waits",
                                                       "| SR3 | agent | `M1-DRAFT-01` drafts | waits")),
             "start on day 1 in TICKETS.md but have a Depends On: M1-DRAFT-01"),
            ("T6", dict(tickets_md=TICKETS_MD.replace("M4: no tickets - go-live", "M4 go-live")),
             "#Plan milestone M4 has no ticket"),
        )
        for name, kw, want in breaks:
            project(d, **kw)
            got = " | ".join(status.tickets_gaps(d))
            if want not in got:
                fails.append(f"{name}: the tickets check should report {want!r}: {got[:300]!r}")
        # T13 owner default (2026-10-04): a docs-only ticket (every target file a doc) needs no test file; a ticket
        # with one code file still does
        project(d, backlog=edit("M1-LOG-01", targets=["docs/features/outcome-log.md", "README.md"]))
        if "lists no test file" in " | ".join(status.tickets_gaps(d)):
            fails.append(f"T13: a docs-only ticket should need no test file: {status.tickets_gaps(d)}")
        project(d, backlog=edit("M1-LOG-01", targets=["docs/features/outcome-log.md", "README.md", "app/audit/x.py"]))
        if "lists no test file in Target Files (a ticket whose target files are all docs needs none): M1-LOG-01"                 not in " | ".join(status.tickets_gaps(d)):
            fails.append(f"T13: a code ticket with no test file should still be named: {status.tickets_gaps(d)}")
        # T11 a Slice Strategy with none ticked
        project(d)
        f = next((d / "docs" / "issues").glob("M1-AUTH-01_*.md"))
        f.write_text(f.read_text(encoding="utf-8").replace("- [x] ↕️ Vertical", "- [ ] ↕️ Vertical"), encoding="utf-8")
        if "does not tick exactly one Slice Strategy: M1-AUTH-01=0" not in " | ".join(status.tickets_gaps(d)):
            fails.append(f"T11: no Slice Strategy ticked should be named: {status.tickets_gaps(d)}")
        # T14 an empty Owner
        f.write_text(ticket_text(BACKLOG[6]).replace("### 👤 Owner\nSenior\n", "### 👤 Owner\n\n"), encoding="utf-8")
        if "has no Owner: M1-AUTH-01" not in " | ".join(status.tickets_gaps(d)):
            fails.append(f"T14: an empty Owner should be named: {status.tickets_gaps(d)}")

        # every fault at once: ONE refusal naming each, nothing written
        project(d, backlog=edit("M1-PAY-01", lane="backend", targets=["app/payroll/"]),
                tickets_md=TICKETS_MD.replace("```mermaid", "```text").replace("| SR1 | payroll |", "| SR1 ✅ | payroll |"),
                extra={"docs/issues/README.md": "# old\n"})  # it remains from an earlier backlog
        before = (d / "STATUS.md").read_text(encoding="utf-8")
        code, out = run(d, "set", "tickets", "filled")
        for want in ("REFUSED - #tickets:", "every one at once", "names no exact target file", "M1-PAY-01=backend",
                     "no Mermaid lane flow graph", "status mark", "docs/issues/README.md remains"):
            if want not in out:
                fails.append(f"the all-faults refusal should name {want!r}: {out[:600]}")
        if code != 1 or (d / "STATUS.md").read_text(encoding="utf-8") != before:
            fails.append("a refused set tickets filled must exit 1 and leave STATUS.md as it was")
        if out.count("\n  - ") < 5:
            fails.append(f"the refusal should put every problem on its own line: {out[:400]}")
        code, out = run(d, "set", "tickets", "filled", "--dry-run")
        if code != 0 or "DRY RUN - nothing written." not in out or "names no exact target file" not in out:
            fails.append(f"--dry-run on the broken copy should list the gaps and exit 0: {code} {out[:300]}")

        # the save inside set: --commit on the clean record saves and prints the close
        project(d)
        subprocess.run(["git", "init", "-q"], cwd=d)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m",
                        "start"], cwd=d)
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=d)
        subprocess.run(["git", "config", "user.name", "t"], cwd=d)
        code, out = run(d, "set", "tickets", "filled", "--commit", "tickets: 9 tickets in 7 epics across 6 lanes")
        for want in ("#tickets: empty -> filled", "saved", "The rest of the close", "Saved: commit",
                     "Open a NEW conversation and type"):
            if want not in out:
                fails.append(f"set tickets filled --commit should print {want!r}: {out[-900:]}")
        if subprocess.run(["git", "status", "--porcelain"], cwd=d, capture_output=True, text=True).stdout.strip():
            fails.append("set --commit left files uncommitted")
    for f in fails:
        print("FAIL", f)
    print("OK - /tickets start and close" if not fails else f"{len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
