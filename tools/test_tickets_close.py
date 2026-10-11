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


STRUCTURE_TREE = STRUCTURE.replace("Domain modules in app/, one lane each.\n", """Domain modules in app/, one lane each.

```
app/            # the product
  payroll/      # payslips
docs/           # the record
  features/     # one feature doc per built ticket, written by /build
```
""") + "\n## Changes\n\n- 2026-10-05 - first layout.\n"
# the fields a model writes for the realistic backlog above (#42 item 9): the script renders every file from them
LANES = {"payroll": "SR1", "explain": "SR2", "agent": "SR2", "review": "SR1", "audit": "SR2", "auth": "SR1"}
SERVES = {"M2-SURE-01": ["M2.2"], "M2-SURE-02": ["M2.3"]}


def fields_for(backlog=BACKLOG) -> dict:
    epics, tickets = {}, []
    rename = {"M2-CAP-01": "M2-SURE-02"}  # an ID is epic-scoped: the fields derive the epic from it
    for tid, title, epic, epic_name, lane, targets, consumes, exposes, depends, builds, demo in backlog:
        tid, depends = rename.get(tid, tid), rename.get(depends, depends)
        epics[epic] = {"name": epic_name, "lane": lane}
        tickets.append({"id": tid, "title": title, "serves": SERVES.get(tid, ["M1.1"]), "goal": title + ".",
                        "layers": ["domain", "verify"], "files": targets,
                        "consumes": [c.strip("`") for c in consumes], "exposes": exposes,
                        "depends": [] if depends == "None" else [depends],
                        "builds": [] if builds == "None" else [builds], "demo": demo,
                        "tasks": ["Write the failing test first, then the code in the files above.",
                                  "Update the feature doc."],
                        "dod": ["Payroll data is fake and never logged in full."],
                        "verify": "uv run pytest " + next((t for t in targets if "test" in t), "app")})
    return {"seats": [{"id": "SR1", "operator": "person"}, {"id": "SR2", "operator": "agent+person"}],
            "lanes": {k: {"owner": "Senior", "seat": v} for k, v in LANES.items()},
            "milestones": {"M1": {"strategy": "vertical"},
                           "M2": {"strategy": "vertical", "uncovered": {
                               "M2.1": "the known-answer set is /eval's", "M2.4": "the stop switch is M2-STOP, added "
                               "after /eval", "M2.5": "the injection defence is /eval's adversarial set"}},
                           "M3": {"skip": "a usability session and a time measurement the owner runs (evidence, not code)"},
                           "M4": {"skip": "go-live and the company login connection are /deploy's"}},
            "epics": epics, "tickets": tickets,
            "hubs": {"app/main.py": "every lane adds one register line",
                     "config/settings.py": "auth and agent add one field each"},
            "later": ["The company login connection and the public URL -> /deploy, at M4."]}


def fields_tests() -> list[str]:
    """#42 items 2, 3, 5, 6, 9: the model writes one fields file; `set` renders the ticket files and TICKETS.md, copies
    the templates, draws docs/issues/ in STRUCTURE.md; publish.py derives plan.json from the committed files."""
    import importlib.util
    import json
    fails: list[str] = []
    spec = importlib.util.spec_from_file_location("publish", ROOT / "commands" / "tickets" / "publish.py")
    publish = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(publish)
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        project(d, backlog=[], tickets_md="")
        (d / "TICKETS.md").unlink()
        (d / "STRUCTURE.md").write_text(STRUCTURE_TREE, encoding="utf-8")
        run(d, "init", "--product", "HR drafting")
        src = d / "fields.json"
        src.write_text(json.dumps(fields_for()), encoding="utf-8")
        code, out = run(d, "set", "tickets", "filled", "--from-fields", str(src), "--dry-run")
        if code != 0 or "no gap" not in out:
            fails.append(f"fields: the rendered realistic backlog should have no gap: {out[-1500:]}")
        files = sorted(p.name for p in (d / "docs" / "issues").glob("*.md"))
        if len(files) != len(BACKLOG):
            fails.append(f"fields: {len(BACKLOG)} ticket files expected, got {files}")
        one = next((d / "docs" / "issues").glob("M1-PAY-01_*.md")).read_text(encoding="utf-8")
        for want in ("# [M1-PAY-01] Consultant loads one fake employee's two months", "- `M1.1` for one fake employee",
                     "- [x] ↕️ Vertical", "[M1-PAY] Payslips arrive", "### 🛣️ Lane\npayroll", "- [ ] `app/payroll/service.py`",
                     "  - `PayslipMonth`", "  - (new) `load_two_months", "lane: payroll", "No secrets in source",
                     "- [ ] Payroll data is fake", "uv run pytest app/payroll/tests/test_two_months.py"):
            if want not in one:
                fails.append(f"fields: the rendered ticket lacks {want!r}")
        if "<!--" in one or one.lstrip().startswith("---"):
            fails.append("fields: a rendered ticket keeps a template comment or its front matter")
        plan_md = (d / "TICKETS.md").read_text(encoding="utf-8")
        for want in ("# Tickets — HR drafting", "## M1 — Core slice", "| payroll | Senior | SR1 | senior | person | `M1-PAY` |",
                     "| explain | Senior | SR2 | senior | agent, a person reviews its PRs | `M1-EXPL` |",
                     "M3: no tickets - a usability session", "M2.4: no ticket - the stop switch",
                     "- `M1-DRAFT-01` (agent) waits for `M1-EXPL-01` (explain) to merge.",
                     'lane_explain -->|"M1-DRAFT-01 waits for M1-EXPL-01"| lane_agent',
                     "| SR1 | payroll | `M1-PAY-01`", "| SR2 | explain | `M1-EXPL-01`", "builds against `M1-PAY-01` with a stub"):
            if want not in plan_md:
                fails.append(f"fields: the rendered TICKETS.md lacks {want!r}")
        if (d / ".github" / "ISSUE_TEMPLATE" / "feature_ticket.md").is_file() is False or \
                not (d / ".github" / "PULL_REQUEST_TEMPLATE.md").is_file():
            fails.append("fields: `set` should copy the two missing templates (#42 item 14)")
        smd = (d / "STRUCTURE.md").read_text(encoding="utf-8")
        if "  issues/  # one file per ticket, written by /tickets" not in smd or \
                "docs/issues/ added: one file per ticket" not in smd.split("## Changes", 1)[-1]:
            fails.append(f"fields: `set` should draw docs/issues/ in STRUCTURE.md's tree and date it: {smd[-600:]}")
        # the save, then publish's plan read from the committed files: no plan.json typed, no scratch path
        subprocess.run(["git", "init", "-q"], cwd=d)
        for k, v in (("user.email", "t@t"), ("user.name", "t")):
            subprocess.run(["git", "config", k, v], cwd=d)
        src.unlink()
        code, out = run(d, "set", "tickets", "filled", "--commit", "tickets: 9 tickets in 7 epics across 6 lanes")
        if code != 0 or "Saved (commit" not in out:
            fails.append(f"fields: the rendered backlog should close and save: {out[-800:]}")
        plan, epics = publish.derive_plan(str(d))
        if plan["product"] != "HR drafting" or plan["seats"] != ["SR1", "SR2"]:
            fails.append(f"derive_plan: product and seats wrong: {plan['product']!r} {plan['seats']}")
        if [m["title"] for m in plan["milestones"]] != ["M1 — Core slice", "M2 — Trustworthy drafts"] or \
                plan["milestones"][0]["due"] != "2026-10-23":
            fails.append(f"derive_plan: milestones wrong: {plan['milestones']}")
        if plan.get("seat_info") != {"SR1": "senior · person", "SR2": "senior · agent, a person reviews its PRs"}:
            fails.append(f"derive_plan: what each seat is (#42 item 18) is not read from TICKETS.md: "
                         f"{plan.get('seat_info')}")
        if epics["M1-EXPL"]["seat"] != "SR2" or epics["M1-PAY"]["lane"] != "payroll" or \
                epics["M1-REV"]["name"] != "Consultant decides":
            fails.append(f"derive_plan: epics wrong: {epics}")
        t2 = next(x for x in plan["tickets"] if x["id"] == "M1-REV-02")
        if t2["depends_on"] != ["M1-REV-01"] or not t2["file"].startswith("docs/issues/M1-REV-02_consultant-edits-a-draft") \
                or t2["title"] != "Consultant edits a draft before approving":
            fails.append(f"derive_plan: ticket wrong: {t2}")
        # T22 exit-criterion traceability, by number: red when a criterion of a ticketed milestone loses its ticket
        f = dict(fields_for())
        f["milestones"] = {**f["milestones"], "M2": {"strategy": "vertical", "uncovered": {"M2.1": "eval's"}}}
        src.write_text(json.dumps(f), encoding="utf-8")
        code, out = run(d, "set", "tickets", "filled", "--from-fields", str(src), "--dry-run")
        if "#Plan exit criteria M2.4, M2.5 of M2 are served by no ticket" not in out:
            fails.append(f"T22: an unserved criterion should be named: {out[-700:]}")
        f = fields_for()
        f["tickets"][0]["serves"] = ["M1.7"]
        src.write_text(json.dumps(f), encoding="utf-8")
        code, out = run(d, "set", "tickets", "filled", "--from-fields", str(src), "--dry-run")
        if "exit criterion number(s) #Plan does not have: M1-PAY-01:M1.7" not in out:
            fails.append(f"T22: a criterion number #Plan lacks should be named: {out[-700:]}")
        f["tickets"][0]["serves"] = []
        src.write_text(json.dumps(f), encoding="utf-8")
        code, out = run(d, "set", "tickets", "filled", "--from-fields", str(src), "--dry-run")
        if "name no #Plan exit criterion under Exit Criterion" not in out or "M1-PAY-01" not in out:
            fails.append(f"T22: a ticket serving no criterion should be named: {out[-700:]}")
        # item 6: a TICKETS.md hub STRUCTURE.md does not name is a warning for /structure, never a refusal
        f = fields_for()
        f["hubs"]["app/shared.py"] = "two lanes add a helper"
        src.write_text(json.dumps(f), encoding="utf-8")
        code, out = run(d, "set", "tickets", "filled", "--from-fields", str(src), "--dry-run")
        if code != 0 or "! hub file(s) app/shared.py are not under STRUCTURE.md ## Hub files" not in out \
                or "config/settings.py are not" in out:
            fails.append(f"item 6: an unnamed hub should warn, a named one never: {out[-600:]}")
        if "no operator" in out or "but seat" in out:
            fails.append(f"seats: every seat has an operator and every owner fits its seat - no seat warning: {out[-600:]}")
        # 2.3 review: a bare seat id drops round 1's person/agent answer, and a Junior lane on an SR seat contradicts
        # itself - both warn, the record still saves
        f = fields_for()
        f["seats"] = ["SR1", {"id": "SR2", "operator": "agent+person"}]
        f["lanes"]["payroll"]["owner"] = "Junior"
        src.write_text(json.dumps(f), encoding="utf-8")
        code, out = run(d, "set", "tickets", "filled", "--from-fields", str(src))
        want = ('! seat SR1: no operator - write round 1\'s answer: "person", "agent" or "agent+person"',
                "! lane payroll: owner Junior but seat SR1 is senior - give the lane a JR seat, or make the owner Senior",
                "a warning, not a refusal: the record is saved as written")
        if code != 0 or any(w not in out for w in want) or out.count("seat SR1: no operator") != 1:
            fails.append(f"seats: a bare seat id and an owner that does not fit its seat should warn, never refuse: "
                         f"{out[-900:]}")
        # a broken fields file is refused with every problem, before any check
        src.write_text(json.dumps({"lanes": {}, "epics": {}, "tickets": [{"id": "X-1"}, {"id": "M1-ZZ-01", "title": "x"}]}),
                       encoding="utf-8")
        code, out = run(d, "set", "tickets", "filled", "--from-fields", str(src))
        if code != 1 or "ticket id 'X-1' is not M<n>-<EPIC>-<nn>" not in out or "epic M1-ZZ is not under" not in out:
            fails.append(f"fields: a broken fields file should be refused with each problem: {out[-500:]}")
    # every contract name is printed (#42 item 12): no 300-character cut
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        big = "from pydantic import BaseModel\n\n" + "".join(
            f"class Model{i}(BaseModel):\n    field_{i}_a: int\n    field_{i}_b: str\n\n\n" for i in range(30))
        project(d, extra={"app/payroll/schemas.py": big})
        run(d, "init", "--product", "HR drafting")
        code, start = run(d, "next", "--phase", "tickets")
        if "Model29(field_29_a, field_29_b)" not in start or "more: open the file" in start:
            fails.append("the start should print every name a contract file defines (Model29 was cut)")
        if "§Size by behaviour" not in start or len(start) > 28000:
            fails.append(f"the start should carry the slicing rules inline within 28,000 characters: {len(start)}")
    return fails


def file_name_tests() -> list[str]:
    """#42 leftovers: a ticket file's name cuts the title at a whole word, stays put while its title is unchanged,
    and a renamed ticket (title or id) leaves no old file behind. A seat's operator must be one the question offers."""
    import json
    fails: list[str] = []
    long_title = "Consultant edits a draft before approving the letter"
    if status._tk_slug(long_title) != "consultant-edits-a-draft-before":
        fails.append(f"slug: the 40-character cut should end on a whole word: {status._tk_slug(long_title)!r}")
    if status._tk_slug("x" * 50) != "x" * 40 or status._tk_slug("Sign in") != "sign-in":
        fails.append("slug: one long word is cut at 40, a short title is kept whole")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        project(d, backlog=[], tickets_md="")
        (d / "TICKETS.md").unlink()
        (d / "STRUCTURE.md").write_text(STRUCTURE_TREE, encoding="utf-8")
        run(d, "init", "--product", "HR drafting")
        src, issues = d / "fields.json", d / "docs" / "issues"
        f = fields_for()
        pay = next(x for x in f["tickets"] if x["id"] == "M1-PAY-01")
        pay["title"] = long_title
        src.write_text(json.dumps(f), encoding="utf-8")
        run(d, "set", "tickets", "filled", "--from-fields", str(src), "--dry-run")
        names = sorted(p.name for p in issues.glob("M1-PAY-01_*.md"))
        if names != ["M1-PAY-01_consultant-edits-a-draft-before.md"]:
            fails.append(f"names: the rendered file should be cut at a whole word: {names}")
        # stable: a file named by the older mid-word cut keeps its name while its title is unchanged
        (issues / names[0]).rename(issues / "M1-PAY-01_consultant-edits-a-draft-before-approvin.md")
        run(d, "set", "tickets", "filled", "--from-fields", str(src), "--dry-run")
        names = sorted(p.name for p in issues.glob("M1-PAY-01_*.md"))
        if names != ["M1-PAY-01_consultant-edits-a-draft-before-approvin.md"]:
            fails.append(f"names: an unchanged title should keep its file name, never a second file: {names}")
        # a new title: the file under the old name goes
        pay["title"] = "Consultant loads two months"
        src.write_text(json.dumps(f), encoding="utf-8")
        code, out = run(d, "set", "tickets", "filled", "--from-fields", str(src), "--dry-run")
        names = sorted(p.name for p in issues.glob("M1-PAY-01_*.md"))
        if names != ["M1-PAY-01_consultant-loads-two-months.md"] or "removed docs/issues/M1-PAY-01_consultant" not in out:
            fails.append(f"names: a renamed title should replace the old file and say so: {names} {out[-400:]}")
        # a new id: the old id's file goes
        f["tickets"] = [x if x["id"] != "M1-REV-02" else {**x, "id": "M1-REV-03"} for x in f["tickets"]]
        for x in f["tickets"]:
            x["depends"] = ["M1-REV-03" if dep == "M1-REV-02" else dep for dep in x.get("depends") or []]
            x["builds"] = ["M1-REV-03" if b == "M1-REV-02" else b for b in x.get("builds") or []]
        src.write_text(json.dumps(f), encoding="utf-8")
        code, out = run(d, "set", "tickets", "filled", "--from-fields", str(src), "--dry-run")
        if list(issues.glob("M1-REV-02_*.md")) or not list(issues.glob("M1-REV-03_*.md")) or \
                "removed docs/issues/M1-REV-02_" not in out:
            fails.append(f"names: a renamed id should leave no file under the old id: "
                         f"{sorted(p.name for p in issues.glob('M1-REV-0*'))} {out[-400:]}")
        # a seat operator the round-1 question does not offer is refused, nothing written or removed
        before = sorted(p.name for p in issues.glob("*.md"))
        f["seats"][1]["operator"] = "robot"
        f["tickets"] = [x for x in f["tickets"] if x["id"] != "M1-PAY-01"]
        src.write_text(json.dumps(f), encoding="utf-8")
        code, out = run(d, "set", "tickets", "filled", "--from-fields", str(src), "--dry-run")
        if code == 0 or "seat SR2: operator 'robot' is not one of person, agent, agent+person" not in out or \
                sorted(p.name for p in issues.glob("*.md")) != before:
            fails.append(f"seats: an unknown operator should be refused before any file changes: {out[-400:]}")
    return fails


def seat_tests() -> list[str]:
    """#42 body items 2, 3, 6 and the owner's 2026-10-04 note: TICKETS.md shows each seat's load, the PRs a person
    reviews for agent seats, the longest chain of waits and each agent seat's own folder; an idle seat, seats far apart
    in load and two seats writing one file across milestones unordered each warn (saved as written)."""
    import json
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        project(d, backlog=[], tickets_md="")
        (d / "TICKETS.md").unlink()
        (d / "STRUCTURE.md").write_text(STRUCTURE_TREE, encoding="utf-8")
        run(d, "init", "--product", "HR drafting")
        src = d / "fields.json"

        def render(f: dict) -> tuple[str, str]:
            src.write_text(json.dumps(f), encoding="utf-8")
            out = run(d, "set", "tickets", "filled", "--from-fields", str(src), "--dry-run")[1]
            return out, (d / "TICKETS.md").read_text(encoding="utf-8")

        out, md = render(fields_for())
        for want in ("## Seat load", "| SR1 | person | 4 | payroll, review, auth |",
                     "| SR2 | agent, a person reviews its PRs | 5 | explain, agent, audit |",
                     "PRs a person reviews for agent seats: 5 (SR2 5)",
                     "Longest chain of waits: 2 tickets", "`M1-EXPL-01` → `M1-DRAFT-01`",
                     "Agent seats (SR2): each works in its own folder and branch", "git worktree add",
                     # 2.4 review: a new worktree has no .env and no project-scope install (git holds neither), and
                     # a seat's next ticket needs its own branch from the merged main
                     "copy `.env` into it", "or install the playbook at user scope",
                     "each next ticket of that seat, in the same folder: `git fetch`, then `git switch -c"):
            if want not in md:
                fails.append(f"seats: TICKETS.md lacks {want!r}")
        if "idle" in out or "carries" in out or "write one file" in out:
            fails.append(f"seats: the realistic backlog should raise no seat-load warning: {out[-600:]}")
        # an idle seat: named, never refused
        f = fields_for()
        f["seats"].append({"id": "JR1", "operator": "agent"})
        out, md = render(f)
        if "! seat JR1 has no ticket: it is idle from day 1" not in out or "| JR1 | agent | 0 | - |" not in md:
            fails.append(f"seats: a seat with no lane should warn as idle: {out[-600:]}")
        # far apart: one seat carries almost everything
        f = fields_for()
        f["lanes"] = {k: {"owner": "Senior", "seat": "SR1" if k != "auth" else "SR2"} for k in LANES}
        out, md = render(f)
        if "! seat SR1 carries 8 tickets, seat SR2 1: move a lane from SR1 to SR2" not in out:
            fails.append(f"seats: an uneven split should warn: {out[-600:]}")
        # two seats, two milestones, one file, no order: both can be open at once
        f = fields_for()
        sure = next(x for x in f["tickets"] if x["id"] == "M2-SURE-01")
        sure["files"] = sure["files"] + ["app/payroll/service.py"]
        out, md = render(f)
        if "pair(s) of tickets on different seats write one file" not in out or \
                "M1-PAY-01 (SR1) + M2-SURE-01 (SR2): app/payroll/service.py" not in out:
            fails.append(f"seats: two seats writing one file across milestones unordered should warn: {out[-700:]}")
        sure["depends"] = ["M1-PAY-01"]
        out, md = render(f)
        if "write one file" in out:
            fails.append(f"seats: a Depends On between them orders the two - no warning: {out[-500:]}")
    return fails


def area_tests() -> list[str]:
    """#58 wired (owner 2026-10-09): `set tickets filled` writes one area rule file per module for the tool this
    install serves, saved with the backlog - the module row, #Contracts' project rules beside the code that stores
    data, DESIGN.md's Do's & Don'ts beside the UI; /build's start names a file that drifted, and on Codex the
    ticket's area files to open; Antigravity keeps them in the root file, said in one line."""
    import json
    fails: list[str] = []
    real_tool = status.playbook_tool
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        project(d, backlog=[], tickets_md="")
        (d / "TICKETS.md").unlink()
        (d / "STRUCTURE.md").write_text(STRUCTURE_TREE.replace(
            "Append-only `agent_events` log", "Append-only store of `agent_events`"), encoding="utf-8")
        (d / "DESIGN.md").write_text("# DESIGN\n\n## 8. Do's & Don'ts\n\n- Do use the spacing tokens.\n- Don't use "
                                     "pure black text.\n\n## 9. Responsive\n\n- mobile first\n", encoding="utf-8")
        run(d, "init", "--product", "HR drafting")
        src = d / "fields.json"
        src.write_text(json.dumps(fields_for()), encoding="utf-8")
        code, out = run(d, "set", "tickets", "filled", "--from-fields", str(src), "--dry-run")
        if "area rule files (claude, one per module" not in out or "would write app/payroll/CLAUDE.md" not in out \
                or (d / "app" / "payroll" / "CLAUDE.md").exists():
            fails.append(f"area: a dry run should say which area files it would write, and write none: {out[-700:]}")
        for k, v in (("init", "-q"),):
            subprocess.run(["git", k, v], cwd=d)
        for k, v in (("user.email", "t@t"), ("user.name", "t")):
            subprocess.run(["git", "config", k, v], cwd=d)
        code, out = run(d, "set", "tickets", "filled", "--from-fields", str(src), "--commit", "tickets: backlog")
        tracked = subprocess.run(["git", "ls-files"], cwd=d, capture_output=True, text=True).stdout
        if code != 0 or "app/payroll/CLAUDE.md" not in tracked or "wrote app/review/CLAUDE.md" not in out:
            fails.append(f"area: `set tickets filled --commit` should write and save one file per module: {out[-700:]}")
        audit = (d / "app" / "audit" / "CLAUDE.md").read_text(encoding="utf-8") \
            if (d / "app" / "audit" / "CLAUDE.md").is_file() else ""
        review = (d / "app" / "review" / "CLAUDE.md").read_text(encoding="utf-8") \
            if (d / "app" / "review" / "CLAUDE.md").is_file() else ""
        payroll = (d / "app" / "payroll" / "CLAUDE.md").read_text(encoding="utf-8") \
            if (d / "app" / "payroll" / "CLAUDE.md").is_file() else ""
        if "money is integer euro cents" not in audit or "money is integer euro cents" in review:
            fails.append(f"area: #Contracts' rules belong with the module that stores data only: {audit!r}")
        if "follow DESIGN.md" not in review or "Don't use pure black text." not in review or "follow DESIGN.md" in payroll:
            fails.append(f"area: DESIGN.md's Do's & Don'ts belong with the UI module only: {review!r}")
        if status.area_drift_line(d, ["app/payroll/service.py"]):
            fails.append("area: right after the save /build's start should print nothing about area files on Claude")
        (d / "STRUCTURE.md").write_text((d / "STRUCTURE.md").read_text(encoding="utf-8").replace(
            "Read-only access to one employee's payslips", "Read-only access to payslips"), encoding="utf-8")
        line = status.area_drift_line(d, ["app/payroll/service.py"])
        if "! area rule file(s) no longer match" not in line or "app/payroll/CLAUDE.md" not in line:
            fails.append(f"area: /build's start should name an area file that drifted from STRUCTURE.md: {line!r}")
        try:
            status.playbook_tool = lambda: "codex"
            status.area_rules_cmd(d, ["codex"], write=True, check=False)
            line = status.area_drift_line(d, ["app/payroll/service.py"])
            if "open each once, before the first edit): app/payroll/AGENTS.md" not in line:
                fails.append(f"area: on Codex /build's start should name the ticket's area file to open: {line!r}")
            status.playbook_tool = lambda: "antigravity"
            note = status.tickets_area_rules(d, dry=True)
            if "none on Antigravity" not in note or status.area_drift_line(d, ["app/payroll/service.py"]):
                fails.append(f"area: Antigravity should get one line and nothing written or checked: {note!r}")
        finally:
            status.playbook_tool = real_tool
    return fails


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
        for want in ("set tickets filled --from-fields <file> --commit", "--dry-run", "ONE question round",
                     "no proposal turn", "1. Who builds: how many seats", "the close shows the whole result", "PayslipMonth(employee_id",
                     "decide() [POST /drafts/{draft_id}/decision]", "agent_events(table: id, draft_id",
                     "STRUCTURE.md ## Modules", "STRUCTURE.md ## Hub files", "M1 — Core slice",
                     "--from-fields", "refuses, every problem in one list", "§Waiting or building against",
                     "Remote: none", "never a reason in your words", "`M1.1` for one fake employee",
                     "`M2.3` a run over €0.10 stops", "never product code", "Every milestone of #Plan is ticketed",
                     "\"serves\"", "all of them - never grep"):
            if want not in start:
                fails.append(f"the /tickets start lacks {want!r}")
        for banned in ("Four-risks row", "Read (file · date", "close with, in order", "--section-from <file>",
                       "rules tickets` in your first call", "<scratch>/plan.json", "cp ", "### 🛣️ Lane"):
            if banned in start:
                fails.append(f"the /tickets start should not carry {banned!r} (not used by this phase)")
        if len(start) > 30000:
            fails.append(f"the /tickets start is {len(start)} characters - Claude Code shows 30,000")
        # the start prints the install path in its commands: a LONG install path (a deep plugin cache, a long user
        # name) must not push it over the inline limit, where the slicing rules drop out (2.2 groups saw "lacks
        # §Waiting or building against" from a worktree path ~20 characters longer). Projected to a 240-character path.
        root = ROOT.as_posix()
        if start.count(root) == 0:
            fails.append("setup: the start no longer prints the install path - the long-path case proves nothing")
        long_size = len(start) + start.count(root) * (240 - len(root))
        if long_size > status.TICKETS_INLINE:
            fails.append(f"with a 240-character install path the /tickets start would be {long_size} characters, over "
                         f"its {status.TICKETS_INLINE} inline limit - the slicing rules would drop out")
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
            ("T17b", dict(backlog=[r if r[0] not in ("M1-PAY-01", "M1-AUTH-01") else r[:5] + (r[5] + ["app/shared.py"],)
                                   + r[6:] for r in BACKLOG], tickets_md=hub_less),
             "M1-AUTH-01+M1-PAY-01:app/shared.py"),
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
        # item 6: a STRUCTURE.md hub (a one-line registry) written by two unordered tickets is no finding
        project(d, backlog=[r if r[0] not in ("M1-PAY-01", "M1-AUTH-01") else r[:5] + (r[5] + ["config/settings.py"],)
                            + r[6:] for r in BACKLOG], tickets_md=hub_less)
        if "config/settings.py" in " | ".join(status.tickets_gaps(d)):
            fails.append(f"T17: a STRUCTURE.md hub file should never be a same-file finding: {status.tickets_gaps(d)}")
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
        for want in ("#tickets: empty -> filled", "saved", "The rest of the close", "Saved (commit",
                     "Open a NEW conversation and type",
                     # #42 item 19: the close reconciles against #Plan, as the skill says - never "against #Vision"
                     "(a ticket count, a seat count, a date) against #Plan's milestones and dates"):
            if want not in out:
                fails.append(f"set tickets filled --commit should print {want!r}: {out[-900:]}")
        if subprocess.run(["git", "status", "--porcelain"], cwd=d, capture_output=True, text=True).stdout.strip():
            fails.append("set --commit left files uncommitted")
    fails += fields_tests()
    fails += file_name_tests()
    fails += seat_tests()
    fails += area_tests()
    for f in fails:
        print("FAIL", f)
    print("OK - /tickets start and close" if not fails else f"{len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
