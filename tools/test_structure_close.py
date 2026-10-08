"""tools/test_structure_close.py - /structure's one start command and its close in code (P1, P4, P8, P17, P20, P25).

A logged Claude /structure read PRINCIPLES.md, MECHANISMS.md and PRODUCT.md whole before writing anything and
re-sent them on each of its 26 calls; a logged Gemini run passed its close with lanes without tests/, an
assertTrue(True) test, print-only tasks, `make lint` running the structure check, and Alembic and a container
recorded with no migrations/ and no Dockerfile. Now `next --phase structure` prints what the phase derives from,
and `set structure filled` runs the structure check and refuses every countable gap in one list.

The project below is the record a model would realistically write for a B2B HR product with an AI agent, a Python
monolith (P17: no saved run of this skill on the current test project exists). It must close the first time; each
check is shown red by breaking exactly what it checks; a copy with every fault at once is refused in ONE list.
Run: python tools/test_structure_close.py   (check.py runs it with tools/test_check_structure.py, check 53b)
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import status  # noqa: E402

TODAY = "2026-10-03"

ARCHITECTURE = """\
- **Constraint set (the owner's answers):**
  - two people, ~15 h/week each, Python · EU hosting only (payroll data) · ≤ €150/month at the pilot
- **System kind:** a B2B web app for payroll consultants (review screen) and a background worker that runs the
  explanation agent. UI: yes. Agent: yes (read-only: it drafts, a consultant approves).
- **Stack + tools (and why):**
  - Python 3.13 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 + psycopg 3 · Alembic · arq (Redis queue) for agent runs.
    ADR-0001. _default taken, not user-chosen (Python user-chosen)_
  - UI binding: Jinja2 + HTMX, server-rendered, no JS build; this binds the UI only. ADR-0003.
  - LLM: Mistral Large via the `mistralai` SDK, EU endpoint, only inside an adapter. ADR-0004.
- **Data custody + why:** managed Postgres, Scaleway Paris (EU residency, `pg_dump` exit); a second database is the
  isolated test datastore. ADR-0002.
- **Runtime target per deployable unit:**
  - `web` (FastAPI) → container on a PaaS: Scaleway Serverless Containers, Paris.
  - `worker` (agent runs) → the same image as a second container.
- **Identity custody:** the company login (OIDC via Microsoft Entra ID), no passwords of our own. ADR-0005.
- **Dev tooling (hook runner · secret scanner · task runner · formatter/linter · dependency manifest):**
  - hook runner: pre-commit · secret scanner: gitleaks (hook + CI) · task runner: make · formatter/linter: Ruff ·
    dependency manifest: `pyproject.toml` + `uv.lock` (uv) · tests: pytest. _default taken, not user-chosen_
- **Externals behind provider/adapter interfaces (+ resilience strategy each):**
  - `LLMProvider` (Mistral): 30 s timeout · retry 2 on 429/5xx · failure → the cause is handed to the consultant.
  - `PayrollProvider` (fake payroll data now; the real payroll system later): read-only, 10 s timeout.
  - `IdentityProvider` (Entra ID OIDC): token validation; failure → closed.
- **Key decisions / ADRs:** 0001 monolith + arq · 0002 Scaleway Paris · 0003 Jinja2 + HTMX · 0004 Mistral EU ·
  0005 company login.
"""

PRODUCT = """\
# PRODUCT — Pay change explainer

## Vision
- **Who it's for:** payroll consultants at a payroll bureau, answering employees' "why did my pay change?"
- **AI:** yes - the agent finds why net pay changed between two months and drafts the reply; a consultant approves.

## Scope
- **THE core feature (the one thing):** the agent finds why an employee's net pay changed between two months and
  drafts the reply with each cause, its amount and the rule; the consultant approves or edits it.
- **In scope (now):**
  - read-only access to two months of fake payroll data for one employee
  - a review screen where the consultant approves or edits the draft
  - a log of each draft's outcome, edits and timestamps
  - a stop switch per team

## Plan
- **Milestones:** M1 the agent explains one fake employee.

## Architecture
""" + ARCHITECTURE + """
## Structure         <!-- /structure --> (see STRUCTURE.md for the full folder map)

## Design
"""

STATUS = """\
# STATUS — Pay change explainer

<!-- Written by status.py. Never edit by hand: run `status.py <command>` (STATE-MODEL.md §2h). -->

Updated: 2026-10-02 · Stage: architect · UI: yes · AI product: yes · Agent: yes

Order: chain order

Next: /structure

## Phases

| Phase | State | Since | Due | Verdict | Note |
|---|---|---|---|---|---|
| vision | filled | 2026-10-01 |  |  |  |
| validate | empty |  |  |  |  |
| scope | filled | 2026-10-01 |  |  |  |
| plan | filled | 2026-10-02 |  |  |  |
| architect | filled | 2026-10-02 |  |  |  |
""" + "".join(f"| {p} | empty |  |  |  |  |\n" for p in status.CHAIN[status.CHAIN.index("structure"):]) + """
## Open items

| # | Since | From | What | Clears when | Closed |
|---|---|---|---|---|---|

## Tickets

| Ticket | Date | DoD met | How verified | Full-suite runs | Review | Doc |
|---|---|---|---|---|---|---|

## Releases

| Date | What shipped | Reviews | Skipped phases | Docs reconciled | Release record | Rollback | PR |
|---|---|---|---|---|---|---|---|

## Drift

| Date | Drift found | Recommendation |
|---|---|---|
"""

STRUCTURE = """\
# STRUCTURE — where things go, and why

## In short

**Domain modules, not layers.** Each folder under `app/` is one thing the product does, with its routes, rules,
tables, adapters, pages and tests. Why: five concerns with their own rules; layers would spread "review a draft"
over four folders. **One app, no `frontend/`** - a recorded exception: Jinja2 + HTMX pages with no JS build
(ADR-0003), so each module keeps its pages in `templates/`.

```
./
├── app/              # the one Python package: web and worker run from it
│   ├── payslips/     # read-only payroll data for one employee, two months, behind PayrollProvider
│   │   ├── adapters/ # the fake payroll source now; the real payroll system later
│   │   └── tests/
│   ├── explain/      # the agent: finds each cause of a pay change and drafts the reply
│   │   ├── adapters/ # Mistral behind LLMProvider + the tracer: the only files importing mistralai
│   │   ├── guards/   # input.py (employee text is data) · output.py (check before a draft is stored) · scope.py
│   │   ├── tools/    # one file per tool (read payslip, read contract) + registry.py, all read-only
│   │   └── tests/    # agent tests against the fake model in fakes.py
│   ├── review/       # the consultant's screen: approve or edit a draft
│   │   ├── templates/
│   │   └── tests/
│   ├── audit/        # append-only action log: every lookup and draft, with time and consultant
│   │   └── tests/
│   ├── accounts/     # company login (OIDC), teams, the stop switch per team
│   │   ├── adapters/ # Entra ID token validation behind IdentityProvider
│   │   └── tests/
│   ├── platform/     # ONLY what no module owns: db engine, queue connection, logging, clock
│   ├── config/       # the typed loader + platform.yaml + product.yaml
│   ├── prompts/      # versioned prompt YAML, loaded by id
│   └── ui/           # the shared base layout only
│       └── templates/
├── migrations/       # Alembic: the only way the schema changes
├── evals/            # golden cases: 30 fake employees with the exact expected causes
│   └── agent/
│       └── labels/   # the human labels the judge is checked against
├── tests/            # tests that cross modules: tenant isolation, the test-DB guard
├── scripts/          # check_structure.py
└── docs/
    └── adr/          # architecture decisions, never deleted
```

## Modules

| Module | What it does | Lane owns |
|---|---|---|
| `app/payslips` | Read-only payroll data behind `PayrollProvider` | `adapters/` · `tests/` |
| `app/explain` | The agent that drafts the explanation | `adapters/` · `guards/` · `tools/` · `tests/` |
| `app/review` | Approve or edit a draft | `templates/` · `tests/` |
| `app/audit` | Append-only action log | `tests/` |
| `app/accounts` | Company login, teams, stop switch | `adapters/` · `tests/` |

## Entry points

| Process | Entry file | Start command | Runs where | Schedule or trigger |
|---|---|---|---|---|
| Web app | `app/main.py` | `make dev` | Scaleway container | requests |
| Worker | `app/worker.py` | `uv run arq app.worker.Settings` | Scaleway container | jobs on the Redis queue |

## Dependency rules

```
inside a module: routes → service → store and adapters
between modules: a module imports another only through its service.py
```

| Rule | Why | Enforced by |
|---|---|---|
| Only `app/explain/adapters/` imports the model vendor's SDK. | ADR-0004 | Not enforced yet: added by /foundation |

## Inside a module

| File | What goes in it |
|---|---|
| `routes.py` | HTTP handlers, thin; one line in `app/main.py` |
| `service.py` | The module's rules; the only code other modules call |
| `schemas.py` | Pydantic models that cross the boundary |
| `store.py` | This module's tables and queries |
| `adapters/` | Vendor implementations of the ports - the only place a vendor SDK is imported |
| `tests/` | This module's tests |

## Where does a new file go?

| Path | When |
|---|---|
| `app/<module>/` | a new thing the product does: a module with its own tests/, one line in `app/main.py` |
| `app/<module>/adapters/` | a new outside service: a port in the module + its adapter |
| `app/prompts/` | a new prompt, versioned |

## Tests and fixtures

| Level | Lives in | Naming and markers | May call an outside service? | Command |
|---|---|---|---|---|
| Module tests | `app/<module>/tests/` | `test_<thing>.py` | no - stand-ins only | `make test` |
| Cross-module tests | `tests/` | `test_<flow>.py` | no | `make test` |
| Golden cases | `evals/agent/` | one file per fake employee | only behind a flag | `make eval` |

**Fixtures:** inputs live in `evals/agent/`, expected causes in `evals/agent/labels/`; real payroll data, model
transcripts and secrets are never committed.

## Root files

| File | Purpose | Chosen in |
|---|---|---|
| `pyproject.toml` | the dependency manifest and tool settings | ADR-0001 |
| `.env.example` | the secrets the app reads, with placeholders | ADR-0001 |

## Where decisions live

| Decision | Home | What is there |
|---|---|---|
| Modular monolith (ADR-0001) | `app/` | the five modules + shared packages |
| Migrations: Alembic (ADR-0001) | `migrations/` | one history; `alembic.ini` arrives with /foundation |
| Agent runs on arq, a Redis queue (ADR-0001) | `app/worker.py` | the job registry, one line per module |
| Container on Scaleway (ADR-0002) | `Dockerfile` | one image for web and worker |
| `LLMProvider`: Mistral EU (ADR-0004) | `app/explain/adapters/` | the only file importing mistralai |
| `PayrollProvider`: fake data now | `app/payslips/adapters/` | read-only |
| `IdentityProvider`: Entra ID (ADR-0005) | `app/accounts/adapters/` | token validation |
| Prompts as YAML | `app/prompts/` | every prompt, the judge's too |
| Hook runner: pre-commit | `.pre-commit-config.yaml` | gitleaks, Ruff, the structure check |
| Task runner: make | `Makefile` | `make help` lists every task |

## Hub files

| Path | Why every lane touches it |
|---|---|
| `app/main.py` | route registry, one line per module |
| `app/worker.py` | job registry, one line per module |
| `app/config/loader.py` | a new setting adds one typed field |
| `.env.example` | a new secret adds one name |
| `pyproject.toml` | a new dependency adds one line |

## Naming and placement rules

| Rule | Enforced by |
|---|---|
| No `utils/`, `common/` or `shared/` folder; a helper lives with the module that owns it. | review |

## Checks you run

| Check | Command | Last result |
|---|---|---|
| Structure check | `python scripts/check_structure.py` | 2026-10-03: OK |

## Not here yet

| What | Added by |
|---|---|
| `alembic.ini` and the first migration | /foundation |

## Changes

- 2026-10-03: first layout.
"""

ENV_EXAMPLE = """\
# Copy to .env (never committed) and replace every value; the app refuses to start on CHANGE_ME.
APP_ENV=CHANGE_ME__APP_ENV__CHANGE_ME

# Scaleway console -> Managed Database -> the "hr" database -> connection string
DATABASE_URL=CHANGE_ME__DATABASE_URL__CHANGE_ME
# A SEPARATE database named "hr_test" - must differ from DATABASE_URL; the suite refuses the dev one
TEST_DATABASE_URL=CHANGE_ME__TEST_DATABASE_URL__CHANGE_ME
REDIS_URL=CHANGE_ME__REDIS_URL__CHANGE_ME

# Mistral console -> API keys (EU workspace)
MISTRAL_API_KEY=CHANGE_ME__MISTRAL_API_KEY__CHANGE_ME

# Entra ID -> App registrations -> the app -> client id and a client secret
OIDC_CLIENT_ID=CHANGE_ME__OIDC_CLIENT_ID__CHANGE_ME
OIDC_CLIENT_SECRET=CHANGE_ME__OIDC_CLIENT_SECRET__CHANGE_ME
# Signs the session cookie. Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
SESSION_SECRET=CHANGE_ME__SESSION_SECRET__CHANGE_ME
"""

GITIGNORE = """\
# .env and every variant or backup; only .env.example is committed
.env
.env.*
*.env
*.env.local
*.env.bak
!.env.example
__pycache__/
.venv/
.pytest_cache/
.ruff_cache/
"""

MAKEFILE = """\
.PHONY: help dev test lint check seed
help:
\t@echo "make dev | test | lint | check | seed"
dev:
\tuv run uvicorn app.main:app --reload
test:
\tuv run pytest
lint:
\tuv run ruff check . && uv run ruff format --check .
check: lint test
\tpython scripts/check_structure.py
seed:
\t@echo "seed arrives with /foundation" && exit 1
"""

PRE_COMMIT = """\
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.24.0
    hooks: [{id: gitleaks}]
  - repo: local
    hooks:
      - {id: structure, name: structure map, entry: python scripts/check_structure.py, language: system, pass_filenames: false}
"""

CLAUDE_MD = """\
# Agent instructions - a pointer, not a copy

Read `PRODUCT.md` and `STRUCTURE.md` by section, never whole (`status.py section <file> "<heading>"`).

## The rules an agent breaks first
- Every value goes through `app/config/loader.py`; secrets only in `.env`.
- Prompts are YAML under `app/prompts/`, never inline.
- A vendor SDK is imported only in a module's `adapters/`.
"""

SECTION_OK = """\
- **Folder → purpose map (summary):** domain modules under `app/` - payslips (read-only payroll data), explain (the
  agent that drafts), review (approve or edit), audit (action log), accounts (company login, teams, stop switch);
  shared: platform, config, prompts, ui. Full map: `STRUCTURE.md`.
- **Prompts location (AI):** `app/prompts/` (backend sub-package; YAML, never inline)
- evidence: python scripts/check_structure.py → map and tree agree both ways · STRUCTURE.md · 2026-10-03
- evidence: uv lock → Resolved 41 packages in 1.92s · 2026-10-03
- evidence: uv run ruff check . → All checks passed! · 2026-10-03
- evidence: uv run pytest tests/test_smoke.py -q → 6 passed in 0.41s · 2026-10-03
"""
# the runnable end (owner 2026-10-04): a lock the package manager wrote, ONE smoke test over every module
UV_LOCK = 'version = 1\nrequires-python = ">=3.13"\n\n[[package]]\nname = "hr"\nversion = "0.1.0"\nsource = { editable = "." }\n'
SMOKE = """\
\"\"\"Smoke: every module imports, and a CHANGE_ME value fails the boot.\"\"\"
import importlib

import pytest

from app.config.loader import load

MODULES = ["app.payslips", "app.explain", "app.review", "app.audit", "app.accounts"]


@pytest.mark.parametrize("name", MODULES)
def test_every_module_imports(name):
    importlib.import_module(name)


def test_a_placeholder_fails_the_boot(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "CHANGE_ME__SESSION_SECRET__CHANGE_ME")
    with pytest.raises(ValueError):
        load()
"""


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


def write(d: Path, rel: str, text: str = "") -> None:
    f = d / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8", newline="\n")


def hr_project(d: Path) -> None:
    """The HR project after a realistic /structure run, before `set structure filled`."""
    if d.exists():
        shutil.rmtree(d, onerror=lambda f, p, e: (os.chmod(p, 0o700), f(p)))  # git objects are read-only
    d.mkdir(parents=True)
    files = {
        "PRODUCT.md": PRODUCT, "STATUS.md": STATUS, "STRUCTURE.md": STRUCTURE, "README.md": "# Pay change explainer\n",
        "CONTRIBUTING.md": "# Contributing\n", "SECURITY.md": "# Security\nReport privately.\n",
        "CHANGELOG.md": "# Changelog\n\n## [Unreleased]\n", ".gitignore": GITIGNORE,
        ".gitattributes": "* text=auto eol=lf\n", ".env.example": ENV_EXAMPLE, ".gitleaks.toml": "[extend]\nuseDefault = true\n",
        ".pre-commit-config.yaml": PRE_COMMIT, "Makefile": MAKEFILE, "pyproject.toml": "[project]\nname = \"hr\"\n",
        "Dockerfile": "FROM python:3.13-slim\n", "CLAUDE.md": CLAUDE_MD, "AGENTS.md": "See CLAUDE.md.\n",
        "app/__init__.py": "", "app/main.py": "", "app/worker.py": "", "uv.lock": UV_LOCK, "tests/test_smoke.py": SMOKE,
        "app/config/__init__.py": "", "app/config/loader.py": "", "app/config/platform.yaml": "llm_timeout_s: 30\n",
        "app/config/product.yaml": "max_tool_calls: 8\n", "app/prompts/explain.yaml": "id: explain\nversion: 1\n",
        "app/platform/__init__.py": "", "app/ui/templates/.gitkeep": "", "migrations/.gitkeep": "",
        "evals/agent/labels/README.md": "human labels\n", "tests/.gitkeep": "", "docs/adr/0001-monolith.md": "# 0001\n",
    }
    for mod, subs in (("payslips", ("adapters", "tests")), ("explain", ("adapters", "guards", "tools", "tests")),
                      ("review", ("templates", "tests")), ("audit", ("tests",)), ("accounts", ("adapters", "tests"))):
        files[f"app/{mod}/__init__.py"] = ""
        for s in subs:
            files[f"app/{mod}/{s}/{'.gitkeep' if s == 'templates' else '__init__.py'}"] = ""
    for rel, text in files.items():
        write(d, rel, text)
    (d / "scripts").mkdir()
    shutil.copy(ROOT / "templates" / "check_structure.py", d / "scripts" / "check_structure.py")


def close(d: Path, section: str = SECTION_OK) -> tuple[int, str]:
    src = d.parent / f"{d.name}-structure-section.md"  # outside the project, as the skill says
    src.write_text(section, encoding="utf-8")
    return run(d, "set", "structure", "filled", "--section-from", str(src))


# (what breaks, how, the words the refusal must hold) - each check shown red by breaking only what it checks
def rm(rel):
    return lambda d: (shutil.rmtree(d / rel) if (d / rel).is_dir() else (d / rel).unlink())


def edit(rel, old, new):
    def f(d):
        t = (d / rel).read_text(encoding="utf-8")
        assert old in t, (rel, old)
        (d / rel).write_text(t.replace(old, new), encoding="utf-8")
    return f


BREAKS = [
    ("a module without tests/", rm("app/review/tests"), "app/review/ has no tests/"),
    ("a placeholder test", lambda d: write(d, "tests/test_golden.py", "def test_golden():\n    assert True\n"),
     "placeholder test"),
    ("a task that only prints", edit("Makefile", '\t@echo "seed arrives with /foundation" && exit 1',
                                     '\t@echo "seeding [wired in /foundation]"'), "task only prints"),
    ("Alembic with no migrations/", lambda d: (rm("migrations")(d), edit("STRUCTURE.md", "├── migrations/       # Alembic: the only way the schema changes\n", "")(d),
                                              edit("STRUCTURE.md", "| Migrations: Alembic (ADR-0001) | `migrations/` | one history; `alembic.ini` arrives with /foundation |\n", "")(d)),
     "records Alembic, and there is no migrations/"),
    ("a container with no Dockerfile", lambda d: (rm("Dockerfile")(d), edit("STRUCTURE.md", "| Container on Scaleway (ADR-0002) | `Dockerfile` | one image for web and worker |\n", "")(d)),
     "records a container, and there is no Dockerfile"),
    ("a worker with no home", lambda d: (edit("STRUCTURE.md", "| Agent runs on arq, a Redis queue (ADR-0001) | `app/worker.py` | the job registry, one line per module |\n", "")(d),
                                         edit("STRUCTURE.md", "one image for web and worker", "one image")(d)),
     "no worker or queue row"),
    ("an adapter with no home", lambda d: (edit("STRUCTURE.md", "| `IdentityProvider`: Entra ID (ADR-0005) | `app/accounts/adapters/` | token validation |\n", "")(d),
                                           edit("STRUCTURE.md", "behind IdentityProvider", "behind the login port")(d)),
     "adapter `IdentityProvider` has no home"),
    ("a hook runner nobody chose", lambda d: write(d, "lefthook.yml", "pre-commit:\n  commands: {}\n"),
     "lefthook.yml is a hook runner the Dev tooling line does not name"),
    ("the named hook runner missing", rm(".pre-commit-config.yaml"), "names pre-commit (hook runner) - no .pre-commit-config.yaml"),
    ("lint that skips the linter", edit("Makefile", "\tuv run ruff check . && uv run ruff format --check .",
                                        "\tpython scripts/check_structure.py"), "`lint` does not run Ruff"),
    ("a compose file the target does not use", lambda d: write(d, "docker-compose.yml", "services: {}\n"),
     "docker-compose file at the root"),
    (".env variant not ignored", edit(".gitignore", "*.env.local\n", ""), ".gitignore does not ignore prod.env.local"),
    (".env.example ignored", edit(".gitignore", "!.env.example\n", ""), ".gitignore ignores .env.example"),
    ("a realistic secret", edit(".env.example", "SESSION_SECRET=CHANGE_ME__SESSION_SECRET__CHANGE_ME",
                                "SESSION_SECRET=replace-me-with-32-plus-random-characters"),
     "SESSION_SECRET holds a value that could pass a check"),
    ("a secret with no how-to comment", edit(".env.example", "# Mistral console -> API keys (EU workspace)\n", ""),
     "MISTRAL_API_KEY has no comment"),
    ("no test datastore", edit(".env.example", "TEST_DATABASE_URL=CHANGE_ME__TEST_DATABASE_URL__CHANGE_ME\n", ""),
     "no isolated test datastore"),
    ("the test datastore is the dev one", lambda d: (edit(".env.example", "DATABASE_URL=CHANGE_ME__DATABASE_URL__CHANGE_ME", "DATABASE_URL=postgresql://localhost/hr")(d),
                                                     edit(".env.example", "TEST_DATABASE_URL=CHANGE_ME__TEST_DATABASE_URL__CHANGE_ME", "TEST_DATABASE_URL=postgresql://localhost/hr")(d)),
     "TEST_DATABASE_URL has the same value as DATABASE_URL"),
    ("no product.yaml", rm("app/config/product.yaml"), "no platform.yaml + product.yaml"),
    ("no typed loader", lambda d: (rm("app/config/loader.py")(d), rm("app/config/__init__.py")(d),
                                   edit("STRUCTURE.md", "| `app/config/loader.py` | a new setting adds one typed field |\n", "")(d)),
     "no typed loader for app/config/platform.yaml"),
    ("no prompts/", lambda d: (rm("app/prompts")(d), edit("STRUCTURE.md", "│   ├── prompts/      # versioned prompt YAML, loaded by id\n", "")(d),
                               edit("STRUCTURE.md", "| Prompts as YAML | `app/prompts/` | every prompt, the judge's too |\n", "")(d)),
     "AI product: no prompts/ folder"),
    ("no guards/", lambda d: (rm("app/explain/guards")(d), edit("STRUCTURE.md", "│   │   ├── guards/   # input.py (employee text is data) · output.py (check before a draft is stored) · scope.py\n", "")(d),
                              edit("STRUCTURE.md", " `guards/` ·", "")(d)),
     "app/explain/ has no guards/"),
    ("no evals/", lambda d: (rm("evals")(d), edit("STRUCTURE.md", "├── evals/            # golden cases: 30 fake employees with the exact expected causes\n│   └── agent/\n│       └── labels/   # the human labels the judge is checked against\n", "")(d)),
     "Agent: no evals/ folder"),
    ("an agent file that copies the spine", edit("CLAUDE.md", "## The rules", "## Vision\n- **Who it's for:** payroll consultants\n\n## The rules"),
     "CLAUDE.md copies PRODUCT.md's #Vision"),
    ("no .gitattributes", rm(".gitattributes"), "no .gitattributes"),
    ("no [Unreleased]", edit("CHANGELOG.md", "## [Unreleased]", "## 0.1.0"), "no `[Unreleased]`"),
    ("no README", rm("README.md"), "no README.md"),
    ("a superseded row in the map", edit("STRUCTURE.md", "| `app/audit` | Append-only action log | `tests/` |\n",
                                         "| `app/audit` | Append-only action log | `tests/` |\n| | | _superseded 2026-10-03: audit lived in platform/_ |\n"),
     "superseded line outside ## Changes"),
    ("no shape named", lambda d: (edit("STRUCTURE.md", "**Domain modules, not layers.**", "**The tree.**")(d),
                                  edit("STRUCTURE.md", "layers would spread", "anything else would spread")(d)),
     "STRUCTURE.md names no shape"),
    # owner 2026-10-05: STRUCTURE.md is templates/structure.md filled
    ("no Entry points section", edit("STRUCTURE.md", "## Entry points", "## Processes"),
     "missing section(s) of the template: Entry points"),
    ("sections out of order", lambda d: (edit("STRUCTURE.md", "## Not here yet", "## Later")(d),
                                         edit("STRUCTURE.md", "## In short", "## Not here yet\n\nNothing.\n\n## In short")(d)),
     "out of the template's order"),
    ("a template comment left", edit("STRUCTURE.md", "## Root files\n", "## Root files\n\n<!-- Each file in the root -->\n"),
     "still holds template comments"),
    ("the check copy edited", edit("scripts/check_structure.py", '".git", ".github",', '".git", ".github", "status",'),
     "differs from the playbook's check"),
    ("audit in platform/", edit("STRUCTURE.md", "| `app/audit` | Append-only action log | `tests/` |",
                                "| `app/audit` | Append-only action log; the writer was `app/platform/audit.py` | `tests/` |"),
     "audit log sits in platform/"),
    ("no Dev tooling line", edit("PRODUCT.md", "- **Dev tooling (hook runner", "- **Tooling (hook runner"),
     "no Dev tooling line"),
    # the runnable end (owner decision 2026-10-04)
    ("no lockfile", rm("uv.lock"), "pyproject.toml has no lockfile"),
    ("a stub lockfile", lambda d: write(d, "uv.lock", "version = 1\n"), "uv.lock is a stub"),
    ("no smoke test", rm("tests/test_smoke.py"), "no smoke test"),
    ("a smoke test without CHANGE_ME", lambda d: write(d, "tests/test_smoke.py", SMOKE.replace("CHANGE_ME", "PLACEHOLDER")),
     "never shows a CHANGE_ME value failing the boot"),
    ("a smoke test missing modules", lambda d: write(d, "tests/test_smoke.py", "from app.config.loader import load\n\n"
                                                     "def test_boot():\n    assert load() is not None  # CHANGE_ME\n"),
     "does not import every module (payslips, explain, review, audit)"),
    (".venv not ignored", lambda d: ((d / ".venv").mkdir(), edit(".gitignore", ".venv/\n", "")(d)),
     ".gitignore does not ignore .venv/"),
    ("a Dockerfile copying a missing file", lambda d: write(d, "Dockerfile", "FROM python:3.13-slim\nCOPY pyproject.toml "
                                                            "uv.lock ./\nCOPY app/ app/\nCOPY poetry.lock ./\n"),
     "Dockerfile copies poetry.lock, which is not in the repo"),
]
SECTION_BREAKS = [
    ("no evidence line", SECTION_OK.replace("- evidence: python scripts/check_structure.py → map and tree agree both ways"
                                            " · STRUCTURE.md · 2026-10-03\n", ""), "no `evidence:` line"),
    ("no prompts location", SECTION_OK.replace("- **Prompts location (AI):** `app/prompts/` (backend sub-package; YAML, "
                                               "never inline)\n", "- **Prompts location (AI):** -\n"),
     "Prompts location is empty"),
    ("no smoke evidence", SECTION_OK.replace("- evidence: uv run pytest tests/test_smoke.py -q → 6 passed in 0.41s · "
                                             "2026-10-03\n", ""), "no evidence line for the smoke test"),
    ("a failing smoke test", SECTION_OK.replace("6 passed in 0.41s", "1 failed, 5 passed in 0.52s"),
     "the smoke test's evidence shows no pass"),
    ("no lint evidence", SECTION_OK.replace("- evidence: uv run ruff check . → All checks passed! · 2026-10-03\n", ""),
     "no evidence line for the linter"),
    ("a failing linter", SECTION_OK.replace("All checks passed!", "Found 3 errors."), "the linter's evidence shows a failure"),
]


def test_start(d: Path, fails: list[str]) -> None:
    hr_project(d)  # then back to what /structure meets: the spine and the ADRs, no code
    for f in list(d.iterdir()):
        if f.name not in ("PRODUCT.md", "STATUS.md", "docs"):
            shutil.rmtree(f) if f.is_dir() else f.unlink()
    code, out = run(d, "next", "--phase", "structure")
    for want in ("/structure start", "#Architecture, whole", "hook runner: pre-commit → .pre-commit-config.yaml",
                 "task runner: make → Makefile", "migrations → migrations/", "`LLMProvider` → its module's adapters/",
                 "§Structure — a home for every agent part", "Placeholders must FAIL", "THE ORDER",
                 "Root scaffolding — the files every shape needs", "the concerns that become modules",
                 "no code yet", "scaffold --from", "scripts/check_structure.py", "- **Prompts location (AI):**",
                 "`set structure filled` refuses, every problem in one list"):
        if want not in out:
            fails.append(f"next --phase structure should print {want!r}")
    # P2/P24: what this run does not need stays out - the generic close checklist, re-run and declined rules on a
    # first run, the AI-security and rollout bullets, and an order to open AGENT.md (it is printed)
    for unwanted in ("This phase closes with, in order", "§Re-run semantics", "§Declined runs", "AI-specific security",
                     "Rollout safety", "open now:", "An input gate"):
        if unwanted in out:
            fails.append(f"next --phase structure printed {unwanted!r}, which a first /structure run does not use")
    size = len(out)
    if size > 25000:  # Claude Code cuts a command's output at 30,000 characters; the open items vary per project
        fails.append(f"next --phase structure is {size} characters on the HR project: keep it under 25,000")
    code, out = run(d, "rules", "structure")
    if code != 0 or "## Production safeguards" not in out or "AI-specific security" not in out:
        fails.append(f"rules structure should print its sections whole: {out[:200]!r}")
    # Antigravity: a short output pointing at a file that holds the start
    real_tool = status.playbook_tool
    pf = Path(status.__file__).resolve().parent / "structure-start.md"
    try:
        status.playbook_tool = lambda: "antigravity"
        code, out = run(d, "next", "--phase", "structure")
        written = pf.read_text(encoding="utf-8") if pf.is_file() else ""
    finally:
        status.playbook_tool = real_tool
        pf.unlink(missing_ok=True)
    if len(out.encode("utf-8")) > 3500 or "structure-start.md" not in out or "/structure start" not in written:
        fails.append(f"Antigravity's /structure start should be short ({len(out.encode('utf-8'))} bytes) and point "
                     f"at a file holding the start")


def test_close(d: Path, fails: list[str]) -> None:
    hr_project(d)
    code, out = close(d)
    if code != 0:
        fails.append(f"the realistic HR record should close the first time: {out.strip()[:1500]!r}")
        return
    for want in ("#structure: empty -> filled", "The rest of the close, in order", "Save this version",
                 "the map against the tree both ways"):
        if want not in out:
            fails.append(f"set structure filled should print {want!r} after a pass")


def test_each_check_red(d: Path, fails: list[str]) -> None:
    for what, brk, want in BREAKS:
        hr_project(d)
        brk(d)
        code, out = close(d)
        if code == 0 or want not in out:
            fails.append(f"{what}: set structure filled should refuse with {want!r}: {out.strip()[:600]!r}")
    for what, section, want in SECTION_BREAKS:
        hr_project(d)
        code, out = close(d, section)
        if code == 0 or want not in out:
            fails.append(f"{what}: set structure filled should refuse with {want!r}: {out.strip()[:600]!r}")


def test_one_refusal(d: Path, fails: list[str]) -> None:
    """P20 + P17's broken copy: every fault of the logged Gemini run at once, named in ONE refusal; PRODUCT.md is
    put back."""
    hr_project(d)
    picked = ("a module without tests/", "a placeholder test", "a task that only prints", "lint that skips the linter",
              "Alembic with no migrations/", "a container with no Dockerfile", "no .gitattributes")
    for what, brk, _ in BREAKS:
        if what in picked:
            brk(d)
    before = (d / "PRODUCT.md").read_text(encoding="utf-8")
    code, out = close(d)
    missing = [want for what, _, want in BREAKS if what in picked and want not in out]
    if code == 0 or missing:
        fails.append(f"the broken copy should be refused once, naming every fault - missing {missing}: {out[:800]!r}")
    if out.count("REFUSED") != 1:
        fails.append(f"the broken copy should get ONE refusal, got {out.count('REFUSED')}")
    if (d / "PRODUCT.md").read_text(encoding="utf-8") != before:
        fails.append("a refused /structure close changed PRODUCT.md")


def test_honest_formats(d: Path, fails: list[str]) -> None:
    """P8: what other models honestly write is never refused - a Dev tooling table, a justfile, an inline comment on
    a secret, a .gitignore by glob, `**Label:**` with no `- `, a lint task that fails until /foundation."""
    hr_project(d)
    edit("PRODUCT.md", "  - hook runner: pre-commit · secret scanner: gitleaks (hook + CI) · task runner: make · formatter/linter: Ruff ·\n"
                       "    dependency manifest: `pyproject.toml` + `uv.lock` (uv) · tests: pytest. _default taken, not user-chosen_",
         "  | Slot | Tool |\n  |---|---|\n  | hook runner | pre-commit |\n  | secret scanner | gitleaks |\n"
         "  | task runner | just |\n  | formatter/linter | ruff |\n  | dependency manifest | uv (pyproject.toml) |")(d)
    os.replace(d / "Makefile", d / "justfile")
    edit("justfile", "\tuv run ruff check . && uv run ruff format --check .", "\truff check .")(d)
    edit("STRUCTURE.md", "| Task runner: make | `Makefile` |", "| Task runner: just | `justfile` |")(d)
    edit(".env.example", "# Mistral console -> API keys (EU workspace)\nMISTRAL_API_KEY=CHANGE_ME__MISTRAL_API_KEY__CHANGE_ME",
         "MISTRAL_API_KEY=CHANGE_ME__MISTRAL_API_KEY__CHANGE_ME  # Mistral console -> API keys")(d)
    edit(".gitignore", ".env\n.env.*\n*.env\n*.env.local\n*.env.bak\n", "**/.env\n.env*\n*.env*\n")(d)
    code, out = close(d, SECTION_OK.replace("- **Folder", "**Folder").replace("- **Prompts", "**Prompts"))
    if code != 0:
        fails.append(f"honest formats should close the first time: {out.strip()[:1200]!r}")


def git_init(d: Path) -> None:
    import subprocess
    for args in (["init", "-q"], ["config", "user.email", "t@example.com"], ["config", "user.name", "t"],
                 ["config", "core.autocrlf", "false"]):
        subprocess.run(["git", *args], cwd=d, check=True, capture_output=True)


def git_out(d: Path, *args: str) -> str:
    import subprocess
    return subprocess.run(["git", *args], cwd=d, capture_output=True, text=True, encoding="utf-8").stdout


LOADER = "import yaml\n\n\ndef load(here):\n    return yaml.safe_load((here / 'platform.yaml').read_text())\n"


def test_findings_2026_10_04(d: Path, fails: list[str]) -> None:
    """The 2026-10-04 self-review findings, each replayed from a logged run (next.67): the save committed the
    playbook's install after the run replaced .gitignore; a loader outside config/ refused, and a second loader added;
    domain logic written at /structure; two save instructions and the handoff printed before the yes; no way to see
    every gap but reading the scripts or running the check by hand."""
    # S1: .gitignore replaced -> the committed line it lost is refused, and the install is never saved
    hr_project(d)
    git_init(d)
    write(d, ".gitignore", GITIGNORE + ".agents/\n")
    git_out(d, "add", ".gitignore")
    git_out(d, "commit", "-qm", "before /structure")
    write(d, ".gitignore", GITIGNORE)  # the run's own file, written over the old one
    write(d, ".agents/skills/structure/SKILL.md", "# installed skill\n")
    code, out = close(d)
    if code == 0 or ".gitignore lost 1 line(s) the committed one had: .agents/" not in out:
        fails.append(f"a replaced .gitignore that lost `.agents/` should be refused: {out.strip()[:600]!r}")
    write(d, ".gitignore", GITIGNORE + ".agents/\n")
    code, out = close(d)
    if code != 0:
        fails.append(f"a merged .gitignore should close: {out.strip()[:800]!r}")
    elif "AFTER the answer" not in out or "git add" in out:
        fails.append(f"the close should give ONE save path and put the handoff after the answer: {out[-1500:]!r}")
    write(d, ".gitignore", GITIGNORE)  # the save never takes the install, even unignored
    code, out = run(d, "save", "-m", "structure")
    committed = git_out(d, "show", "--name-only", "--format=", "HEAD")
    if code != 0 or ".agents/" in committed or "STRUCTURE.md" not in committed or "left out the playbook's install" \
            not in out:
        fails.append(f"save should commit the project and leave the install out: {out.strip()[:400]!r} / "
                     f"{committed[:300]!r}")
    # the install folder with no git history and no ignore line
    hr_project(d)
    write(d, ".agents/skills/structure/SKILL.md", "# installed skill\n")
    code, out = close(d)
    if code == 0 or "does not ignore the playbook's install .agents/" not in out:
        fails.append(f"an unignored install folder should be refused: {out.strip()[:600]!r}")
    # the loader where STRUCTURE.md names it (not beside the YAML) closes; a second loader is refused
    hr_project(d)
    rm("app/config/loader.py")(d)
    rm("app/config/__init__.py")(d)
    write(d, "app/platform/settings.py", LOADER)
    edit("STRUCTURE.md", "| `app/config/loader.py` |", "| `app/platform/settings.py` |")(d)
    code, out = close(d)
    if code != 0:
        fails.append(f"a loader where STRUCTURE.md names it should close: {out.strip()[:600]!r}")
    write(d, "app/config/loader.py", LOADER)
    code, out = close(d)
    if code == 0 or "2 config loaders read platform.yaml" not in out:
        fails.append(f"a second loader should be refused: {out.strip()[:600]!r}")
    # no product logic: a module file over 40 lines of code
    hr_project(d)
    write(d, "app/review/service.py", "".join(f"RATE_{i} = 0.{i:02d}\n" for i in range(45)))
    code, out = close(d)
    if code == 0 or "app/review/service.py has 45 lines of code" not in out:
        fails.append(f"product logic in a module should be refused: {out.strip()[:600]!r}")
    # --dry-run: every gap, nothing written - on a broken copy and on a good one
    hr_project(d)
    rm("app/review/tests")(d)
    before = {f: (d / f).read_text(encoding="utf-8") for f in ("PRODUCT.md", "STATUS.md")}
    code, out = close_dry(d)
    if code != 0 or "DRY RUN - nothing written" not in out or "app/review/ has no tests/" not in out:
        fails.append(f"--dry-run should list every gap and exit 0: {out.strip()[:600]!r}")
    hr_project(d)
    code, out = close_dry(d)
    if code != 0 or "no gap" not in out:
        fails.append(f"--dry-run on a good record should say no gap: {out.strip()[:600]!r}")
    if any((d / f).read_text(encoding="utf-8") != t for f, t in before.items()):
        fails.append("--dry-run wrote PRODUCT.md or STATUS.md")


BUNDLE = """\
>>> folders: app/payslips/adapters app/payslips/tests migrations
>>> file: app/__init__.py
\"\"\"The one Python package: web and worker run from it.\"\"\"
>>> file: app/payslips/__init__.py
\"\"\"Read-only payroll data for one employee, two months, behind PayrollProvider.\"\"\"
>>> file: app/payslips/tests/__init__.py
>>> file: app/payslips/tests/.gitkeep
>>> file: migrations/.gitkeep
>>> file: .gitignore
.env
.venv/
>>> file: README.md
# replaced?

Never: an existing file is kept.
"""


def test_runnable_and_one_call_scaffold(d: Path, fails: list[str]) -> None:
    """Owner decisions 2026-10-04: the boilerplate in ONE call (a logged run wrote 74 files in 74 calls) and a
    runnable end - `prove` runs the lock, install, lint and smoke test and prints the evidence lines; offline it prints
    `lock pending`, which `set` accepts in place of the lockfile and the run lines."""
    import subprocess
    d.mkdir(parents=True, exist_ok=True)
    for f in list(d.iterdir()):
        shutil.rmtree(f) if f.is_dir() else f.unlink()
    write(d, "PRODUCT.md", PRODUCT)
    write(d, "STATUS.md", STATUS)
    write(d, ".gitignore", ".agents/\n.env\n")
    write(d, "README.md", "# Pay change explainer\n")
    bundle = d.parent / "bundle.txt"
    bundle.write_text(BUNDLE, encoding="utf-8")
    code, out = run(d, "scaffold", "--from", str(bundle))
    gi = (d / ".gitignore").read_text(encoding="utf-8")
    if code != 0 or "wrote 4 file(s)" not in out or "kept 1 existing file(s), not overwritten: README.md" not in out:
        fails.append(f"scaffold should write the bundle in one call and keep README.md: {out.strip()[:500]!r}")
    if not gi.startswith(".agents/\n.env\n.venv/\n") or ".env.*\n!.env.example\n" not in gi or (d / "README.md").read_text(encoding="utf-8") != "# Pay change explainer\n":
        fails.append(f"scaffold should add to .gitignore (never replace it) and keep an existing file: {gi!r}")
    if (d / "app/payslips/tests/.gitkeep").exists() or not (d / "migrations/.gitkeep").exists() or \
            not (d / "app/payslips/adapters").is_dir():
        fails.append("scaffold: a .gitkeep beside a file is dropped, one in an empty folder kept, every folder made")
    engine = (ROOT / "templates" / "check_structure.py").read_bytes()
    if (d / "scripts/check_structure.py").read_bytes() != engine or not (d / ".gitattributes").is_file() or \
            not (d / ".gitleaks.toml").is_file():
        fails.append("scaffold should copy check_structure.py, .gitattributes and the gitleaks config from the playbook")
    if '"""Read-only payroll data' not in (d / "app/payslips/__init__.py").read_text(encoding="utf-8"):
        fails.append("scaffold should write each file's content as given")
    bad = d.parent / "bad.txt"
    bad.write_text(">>> file: ../outside.txt\nx\n>>> file: .agents/x.md\ny\n>>> file: PRODUCT.md\nz\n", encoding="utf-8")
    code, out = run(d, "scaffold", "--from", str(bad))
    if code == 0 or "nothing written" not in out or "not a path inside the project" not in out or \
            "playbook's install" not in out or "is the spine" not in out or (d.parent / "outside.txt").exists():
        fails.append(f"scaffold should refuse every bad path at once and write nothing: {out.strip()[:500]!r}")
    # prove: the commands run in order, the evidence lines printed; a real failure stops; no network = lock pending
    py = subprocess.list2cmdline([sys.executable])
    code, out = run(d, "prove", f"{py} -c \"print('Resolved 3 packages')\"", f"{py} -c \"print('6 passed in 0.4s')\"")
    if code != 0 or f"evidence: {py} -c \"print('6 passed in 0.4s')\" → 6 passed in 0.4s · {TODAY}" not in out:
        fails.append(f"prove should print one evidence line per command: {out.strip()[:500]!r}")
    code, out = run(d, "prove", f"{py} -c \"import sys; print('1 failed'); sys.exit(1)\"", f"{py} -c \"print('never')\"")
    if code != 1 or "FAILED (exit 1)" not in out or "→ never" in out:
        fails.append(f"prove should stop at the first failure: {out.strip()[:500]!r}")
    code, out = run(d, "prove", f"{py} -c \"import sys; print('error: Could not resolve host: pypi.org'); sys.exit(2)\"")
    if code != 0 or "evidence: lock pending - no network" not in out:
        fails.append(f"prove with no network should print a lock pending line, not fail: {out.strip()[:500]!r}")
    # set accepts `lock pending` in place of the lockfile and the run lines; the smoke test must still exist
    hr_project(d)
    rm("uv.lock")(d)
    write(d, "Dockerfile", "FROM python:3.13-slim\nCOPY pyproject.toml uv.lock ./\n")
    pending = "\n".join(l for l in SECTION_OK.splitlines() if "uv " not in l) + \
        f"\n- evidence: lock pending - no network (error: Could not resolve host: pypi.org) · {TODAY}\n"
    code, out = close(d, pending)
    if code != 0:
        fails.append(f"`lock pending` should close without a lockfile or run lines: {out.strip()[:600]!r}")
    hr_project(d)
    rm("tests/test_smoke.py")(d)
    code, out = close(d, pending)
    if code == 0 or "no smoke test" not in out:
        fails.append(f"`lock pending` still needs the smoke test file: {out.strip()[:400]!r}")
    # the start prints the bundle format, the commands for this stack and the runnable refusals
    code, out = run(d, "next", "--phase", "structure")
    for want in ("status.py scaffold --from <bundle>", ">>> file: <path>", 'prove "uv lock" "uv sync" "uv run ruff '
                 'check ." "uv run pytest tests/test_smoke.py -q"', "lock pending", "a stub lockfile"):
        if want not in out:
            fails.append(f"next --phase structure should print {want!r}")
    if "cp " in out and "scripts/check_structure.py` - never edit" in out:
        fails.append("the start should not send the run to copy the check by hand - scaffold copies it")


def close_dry(d: Path) -> tuple[int, str]:
    src = d.parent / f"{d.name}-structure-section.md"
    src.write_text(SECTION_OK, encoding="utf-8")
    return run(d, "set", "structure", "filled", "--section-from", str(src), "--dry-run")


def test_findings_2026_10_06(d: Path, fails: list[str]) -> None:
    """A live run typed "All checks passed!" into STRUCTURE.md's Checks you run before `prove` ran; prove then stopped
    at a `lock pending` it should not have printed (the same call's `uv lock` had just reached the network)."""
    base = d.parent / "checks-table"
    base.mkdir(parents=True, exist_ok=True)
    table = ("## Checks you run\n\n| Check | Command | Last result |\n|---|---|---|\n"
             "| Lint | `uv run ruff check .` | 2026-10-06: All checks passed! |\n"
             "| Structure check | `python scripts/check_structure.py` | 2026-10-06: map and tree agree |\n\n"
             "## Not here yet\n")
    typed = "- evidence: lock pending - no network (error: Failed to download `x==1`) · 2026-10-06\n"
    printed = "evidence: uv run ruff check . → All checks passed! · 2026-10-06\n"
    gaps = [g for g in status.structure_run_gaps(base, table, typed) if "Checks you run" in g]
    if len(gaps) != 1 or "All checks passed!" not in gaps[0]:
        fails.append(f"a Checks-you-run result no evidence line printed should be refused once: {gaps!r}")
    if [g for g in status.structure_run_gaps(base, table, printed) if "Checks you run" in g]:
        fails.append("a Checks-you-run result copied from prove's line was refused")
    code, out = status.prove(base, [f'"{sys.executable}" -c "print(1)"',
                                    f'"{sys.executable}" -c "import sys; print(\'error: Failed to download x\'); '
                                    f'sys.exit(1)"'], "2026-10-06")
    if code == 0 or "lock pending" in out:
        fails.append(f"prove called a failure 'no network' after an earlier command succeeded: {out[-200:]!r}")


def test_p46_starters_and_order(d: Path, fails: list[str]) -> None:
    """P46 (2026-10-06): a logged run typed 45 starter files (31,561 chars) - the root docs, the .gitignore lines and 31
    package/README files the same in every project. `scaffold` now writes them from templates/ and STRUCTURE.md's own
    tables; the realistic record must still close the first time with only STRUCTURE.md in the bundle. P47: the start
    stays under 25,000 characters on a re-run too, and tells the order and what never to run."""
    hr_project(d)
    generated = ["CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md", "app/__init__.py", "migrations/.gitkeep"]
    for mod, subs in (("payslips", ("adapters", "tests")), ("explain", ("adapters", "guards", "tools", "tests")),
                      ("review", ("tests",)), ("audit", ("tests",)), ("accounts", ("adapters", "tests"))):
        generated += [f"app/{mod}/__init__.py"] + [f"app/{mod}/{s}/__init__.py" for s in subs]
    for rel in generated:
        (d / rel).unlink()
    for rel in ("migrations", "app/review/tests", "app/audit/tests"):
        (d / rel).rmdir()
    bundle = d.parent / "p46-bundle.txt"
    bundle.write_text(">>> file: STRUCTURE.md\n" + (d / "STRUCTURE.md").read_text(encoding="utf-8"), encoding="utf-8")
    (d / "STRUCTURE.md").unlink()
    code, out = run(d, "scaffold", "--from", str(bundle))
    if code != 0 or "from the playbook's templates: CHANGELOG.md, SECURITY.md, CONTRIBUTING.md" not in out or \
            "from STRUCTURE.md's tables" not in out:
        fails.append(f"scaffold should write the root docs and the folders' files itself: {out.strip()[:600]!r}")
    missing = [rel for rel in generated if rel != "migrations/.gitkeep" and not (d / rel).is_file()]
    if missing or not (d / "migrations" / "README.md").is_file():
        fails.append(f"scaffold left out files STRUCTURE.md's tables name: {missing[:6]} (migrations/README.md: "
                     f"{(d / 'migrations' / 'README.md').is_file()})")
    init = (d / "app/payslips/__init__.py").read_text(encoding="utf-8") if (d / "app/payslips/__init__.py").is_file() else ""
    log = (d / "CHANGELOG.md").read_text(encoding="utf-8") if (d / "CHANGELOG.md").is_file() else ""
    if "Read-only payroll data" not in init or "[Unreleased]" not in log or "Pay change explainer" not in log:
        fails.append(f"a module's package file says what goes there; CHANGELOG.md names the product: {init!r} "
                     f"{log[:80]!r}")
    if ".ruff_cache/" not in (d / ".gitignore").read_text(encoding="utf-8"):
        fails.append("scaffold should add the stack's standard .gitignore lines")
    code, out = close(d)
    if code != 0:
        fails.append(f"the record should close the first time after scaffold wrote the starters: {out.strip()[:900]!r}")
    # a file the bundle holds wins over the template
    hr_project(d)
    (d / "CHANGELOG.md").unlink()
    bundle.write_text(">>> file: CHANGELOG.md\n# Changelog\n\n## [Unreleased]\n- ours\n", encoding="utf-8")
    run(d, "scaffold", "--from", str(bundle))
    if "- ours" not in (d / "CHANGELOG.md").read_text(encoding="utf-8"):
        fails.append("scaffold replaced a file the bundle wrote with its template")
    # a package docstring naming the config files is not a second loader (a logged run was refused for one)
    write(d, "app/config/loader.py", "import yaml\nPLATFORM = 'platform.yaml'\n")
    write(d, "app/config/__init__.py", '"""platform.yaml, product.yaml and their one loader."""\n')
    loaders = [p.relative_to(d).as_posix() for p in status.structure_loaders(d)]
    if loaders != ["app/config/loader.py"]:
        fails.append(f"a docstring naming platform.yaml was counted as a config loader: {loaders}")
    # P46/P47: the start says the order and what never to run, and stays under 25,000 characters on a re-run
    code, out = run(d, "next", "--phase", "structure")
    for want in ("THE ORDER", "NEVER run", "--commit", "`scaffold` writes", "Where does a new file go?"):
        if want not in out:
            fails.append(f"next --phase structure should print {want!r}")
    hr_project(d)
    close(d)
    code, out = run(d, "next", "--phase", "structure")
    if len(out) > 25000 or "§Re-run semantics" not in out:
        fails.append(f"the re-run start is {len(out)} characters (keep it under 25,000) or lacks §Re-run semantics")


def main() -> int:
    fails: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="structure-close-"))
    try:
        d = tmp / "hr"
        for t in (test_start, test_close, test_each_check_red, test_one_refusal, test_honest_formats,
                  test_findings_2026_10_04, test_runnable_and_one_call_scaffold, test_findings_2026_10_06,
                  test_p46_starters_and_order):
            t(d, fails)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for f in fails:
        print(f"  x {f}")
    print("OK - /structure's start and close behave" if not fails else f"FAIL - {len(fails)} /structure test(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
