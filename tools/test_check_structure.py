"""Behaviour tests for templates/check_structure.py (run by tools/check.py). Each case builds a small project,
breaks one rule, and expects the check to fail on exactly that. From a logged /structure run on a second model:
5 of 6 modules had no tests/, no file convention was written, Alembic and a container were recorded with no
migrations/ folder or Dockerfile, four task-runner targets printed and exited 0, and a test was assertTrue(True).
"""
from __future__ import annotations
import contextlib
import io
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True  # the template folder is copied by install.sh: no __pycache__ in it
sys.path.insert(0, str(ROOT / "templates"))
import check_structure  # noqa: E402

GOOD = """# STRUCTURE

## The tree

```
app/
├── orders/      # order lookup
│   └── tests/
├── platform/    # only what no module owns
migrations/      # schema changes, never deleted (superseded instead)
```

## Modules

| Module | What it does |
|---|---|
| `app/orders` | order lookup |

## Inside a module

`routes.py` · `service.py` · `store.py` · `schemas.py` · `tests/`

## Where does a new file go?

A new route: its module's `routes.py`.

## Where decisions live

| Decision (#Architecture) | Home |
|---|---|
| Alembic migrations | `migrations/` |
| Container on Render | `Dockerfile` |

## Hub files

| File | Why |
|---|---|
| `app/main.py` | registers each module's routes |

## Changes

- _superseded 2026-09-25: guards was a file; it is the guards/ folder now_
"""

MAKEFILE = "help:\n\t@echo \"targets\"\n\ncheck:\n\tpython scripts/check_structure.py\n\ndev:\n\t@echo \"arrives with /foundation\"\n\t@exit 1\n"
# the one-line form the refusal's own words ask for ("make it fail with 'arrives with /foundation'") is not print-only:
# a realistic HR record wrote it this way and the check refused it (2026-10-03)
MAKEFILE += "\nseed:\n\t@echo \"arrives with /foundation\" && exit 1\n\nreset:\n\t@echo \"arrives with /foundation\"; false\n"


def build(d: Path) -> None:
    if d.exists():
        shutil.rmtree(d)
    for p in ("app/orders/tests", "app/platform", "migrations"):
        (d / p).mkdir(parents=True)
    (d / "app/main.py").write_text("", encoding="utf-8")
    (d / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    (d / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    (d / "app/orders/tests/test_orders.py").write_text("def test_x():\n    assert lookup(1) == 1\n", encoding="utf-8")
    (d / "STRUCTURE.md").write_text(GOOD, encoding="utf-8")


def run(d: Path) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = check_structure.main([str(d / "STRUCTURE.md"), str(d)])
    return code, out.getvalue()


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "p"
        build(d)
        code, out = run(d)
        if code != 0:
            fails.append(f"a complete project should pass: {out.strip()}")
        cases = [
            ("a module with no tests/ (U)", lambda: shutil.rmtree(d / "app/orders/tests"), "no tests/"),
            ("no ## Inside a module (M1)",
             lambda: (d / "STRUCTURE.md").write_text(GOOD.replace("## Inside a module", "## Inside"), encoding="utf-8"),
             "## Inside a module"),
            ("no ## Where does a new file go? (M1)",
             lambda: (d / "STRUCTURE.md").write_text(GOOD.replace("## Where does a new file go?", "## New"),
                                                    encoding="utf-8"), "## Where does a new file go?"),
            ("no ## Modules (U)",
             lambda: (d / "STRUCTURE.md").write_text(GOOD.replace("## Modules", "## Mods"), encoding="utf-8"),
             "## Modules"),
            ("a recorded decision with no home on disk (H1)", lambda: (d / "Dockerfile").unlink(), "Dockerfile"),
            ("no ## Where decisions live (H1)",
             lambda: (d / "STRUCTURE.md").write_text(GOOD.replace("## Where decisions live", "## Decisions"),
                                                    encoding="utf-8"), "## Where decisions live"),
            ("a placeholder test (V)",
             lambda: (d / "app/orders/tests/test_orders.py").write_text(
                 "import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        self.assertTrue(True)\n",
                 encoding="utf-8"), "placeholder test"),
            ("a task that only prints and succeeds (V)",
             lambda: (d / "Makefile").write_text(MAKEFILE + "\nseed:\n\t@echo \"wired in /foundation\"\n",
                                                 encoding="utf-8"), "seed"),
            ("a superseded row left in the map (S2)",
             lambda: (d / "STRUCTURE.md").write_text(GOOD.replace(
                 "| `app/orders` | order lookup |",
                 "| `app/orders` | order lookup |\n| | _superseded 2026-09-25: was `app/lookup`_ |"), encoding="utf-8"),
             "superseded"),
            ("a just recipe that only prints and succeeds (V)",
             lambda: (d / "justfile").write_text("lint:\n    @echo \"arrives with /foundation\"\n", encoding="utf-8"),
             "lint"),
            ("a commit hook that never runs this check (R2)",
             lambda: (d / ".pre-commit-config.yaml").write_text(
                 "repos:\n  - repo: local\n    hooks:\n      - id: ruff\n        entry: ruff check\n", encoding="utf-8"),
             "commit hook"),
        ]
        build(d)
        (d / ".pre-commit-config.yaml").write_text(
            "repos:\n  - repo: local\n    hooks:\n      - id: layout\n        entry: python scripts/check_structure.py\n",
            encoding="utf-8")
        code, out = run(d)
        if code != 0:
            fails.append(f"a commit hook that runs check_structure.py should pass: {out.strip()}")
        for what, breakit, needle in cases:
            build(d)
            breakit()
            code, out = run(d)
            if code == 0 or needle not in out:
                fails.append(f"{what} should fail naming {needle!r}: {out.strip()}")
        # --suggest prints the tree line for an unmapped folder under its parent, and never writes the map
        build(d)
        (d / "scripts/frontend-audit").mkdir(parents=True)
        (d / "scripts/check_structure.py").write_text("", encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_structure.main([str(d / "STRUCTURE.md"), str(d), "--suggest"])
        if code == 0 or "under scripts/:  frontend-audit/" not in out.getvalue() \
                or "under the root:  scripts/" not in out.getvalue():
            fails.append(f"--suggest should print each unmapped folder's line under its parent: {out.getvalue()}")
        if (d / "STRUCTURE.md").read_text(encoding="utf-8") != GOOD:
            fails.append("--suggest wrote STRUCTURE.md - it only prints")
        code, plain = run(d)
        if "Lines to add" in plain:
            fails.append("without --suggest, no lines to add are printed")
        # the playbook's own status/ (status.py's item files) is not the product's layout: drawn or not, it passes;
        # a status/ holding anything else is an ordinary folder the map must draw (a logged run hid it by editing IGNORE)
        build(d)
        (d / "status/open").mkdir(parents=True)
        (d / "status/open/o7k2.md").write_text("#: o7k2\n", encoding="utf-8")
        code, out = run(d)
        if code != 0:
            fails.append(f"the playbook's status/ folder should not need drawing: {out.strip()}")
        (d / "STRUCTURE.md").write_text(GOOD.replace("migrations/ ", "status/          # status.py's files\n"
                                                     "│   └── open/\nmigrations/ "), encoding="utf-8")
        code, out = run(d)
        if code != 0:
            fails.append(f"a drawn playbook status/ folder should pass too: {out.strip()}")
        (d / "STRUCTURE.md").write_text(GOOD, encoding="utf-8")
        (d / "status/exports").mkdir()
        code, out = run(d)
        if code == 0 or "status/" not in out:
            fails.append(f"a status/ with a folder status.py never writes is the product's and must be drawn: {out}")
        # a backticked NAME is not a path: a logged run's table put the path first and backticked the interface names
        # in the second column - 6 FAILs for `LLMProvider`, `Tracer` ... (2026-10-03). The header says which column
        # holds the path; a backticked path there that is missing still fails.
        build(d)
        (d / "app/orders/adapters").mkdir()
        named = GOOD.replace(
            "| Decision (#Architecture) | Home |\n|---|---|\n| Alembic migrations | `migrations/` |\n"
            "| Container on Render | `Dockerfile` |\n",
            "| Path | Decision (#Architecture) |\n|---|---|\n| `migrations/` | Alembic, `version:` in each file |\n"
            "| `Dockerfile` | Container on Render |\n| `app/orders/adapters/` | `LLMProvider` and `Tracer` |\n")
        named = named.replace("│   └── tests/", "│   ├── adapters/\n│   └── tests/")
        (d / "STRUCTURE.md").write_text(named, encoding="utf-8")
        code, out = run(d)
        if named == GOOD or code != 0:
            fails.append(f"backticked names beside a path column must not fail as missing paths: {out.strip()}")
        shutil.rmtree(d / "app/orders/adapters")
        (d / "STRUCTURE.md").write_text(GOOD.replace("| Container on Render | `Dockerfile` |",
                                                     "| Container on Render | `Dockerfile` |\n"
                                                     "| `LLMProvider` | `app/orders/adapters/` |"), encoding="utf-8")
        code, out = run(d)
        if code == 0 or "decision home not on disk: app/orders/adapters" not in out:
            fails.append(f"a missing path in the Home column must still fail: {out.strip()}")
    for f in fails:
        print(f"  x {f}")
    print("OK - check_structure.py behaves" if not fails else f"FAIL - {len(fails)} check_structure.py test(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
