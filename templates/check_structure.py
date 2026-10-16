#!/usr/bin/env python3
# Copyright (c) 2026 kish21 - MIT License (product-playbook).
"""check_structure.py - STRUCTURE.md's map and the real tree must agree BOTH ways.

Copied into a project by /structure (into scripts/ or tools/) and run at its
Step 3b gate. It is committed, not a scratch file: a gate whose evidence is a
script that no longer exists is a claim, and `evidence:` lines are re-run by the
transition guard in later sessions.

What it checks, in both directions:
  * every folder DRAWN in the fenced tree block of STRUCTURE.md exists on disk
  * every folder ON DISK (minus the ignore list) appears in the map
  * every path listed under a `## Hub files` heading exists - one per table row
    or list item, the first backticked token (the files every lane may touch by
    one line; a hub file that has moved leaves /tickets pointing at nothing)
  * the sections a builder needs exist: `## Modules`, `## Inside a module`,
    `## Where does a new file go?`, `## Where decisions live`, `## Hub files`
  * every module under `## Modules` has its own tests/ (a module is a complete
    lane)
  * every home under `## Where decisions live` exists (Alembic recorded ->
    migrations/ on disk); a backticked name that is not a path (`LLMProvider`)
    is skipped, never failed
  * no placeholder test (`assert True`) and no task-runner target that only
    prints and exits 0: both report green on nothing
  * a commit-hook config that exists runs this check (pre-commit, lefthook,
    husky), so a skipped run is caught at the next commit
  * no `superseded` line outside `## Changes`: the map shows only the current
    tree, so a builder never sees two homes for one part (a replaced row is
    deleted; its dated line goes under `## Changes`)
A heading may carry its number (`## 2. Modules`): it is read like `## Modules`.

A drawn-but-uncreated folder is silent doc<->code drift; an undrawn folder on
disk is a layout decision nobody recorded. Reading 25 folders by eye is slower
and less reliable than this, and it turns a judgement call into a deterministic
one.

This file passes `ruff check --select ALL` and `ruff format --check` at line
length 88 and 100, so a project never has to exclude it from its own lint.

Usage:  python scripts/check_structure.py [STRUCTURE.md] [project-root] [--suggest]
        --suggest also prints, for each folder on disk the map lacks, the tree
        line to add under its parent - it never writes STRUCTURE.md: the
        one-line note of what goes there is yours to write.
Exit:   non-zero on any mismatch (CI-friendly).  Portable: stdlib only.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

# Directories that are never part of the recorded layout: tooling caches,
# dependency trees, build output, VCS. Extend it in the project rather than
# loosening the check.
IGNORE = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".turbo",
    ".svelte-kit",
    "coverage",
    ".coverage",
    "htmlcov",
    ".idea",
    ".vscode",
    ".claude",
    "target",
    ".gradle",
}
# The playbook's own status folder (status.py writes one file per open item,
# ticket, release and drift row there): not part of the product's layout, so a
# project never has to draw it - and never edits this list to hide it.
STATUS_KINDS = {"open", "tickets", "releases", "drift"}
# Exit codes: 1 = the map and the tree disagree, 2 = there is no map to compare.
MISMATCH, NO_MAP = 1, 2


def say(line: str) -> None:
    """One output line (stdout, read by CI and by the playbook's status.py)."""
    sys.stdout.write(line + "\n")


def playbook_folder(root: str | Path, dirpath: str | Path, d: str) -> bool:
    """Return True for the root status/ that holds only status.py's item folders."""
    if Path(dirpath) != Path(root) or d != "status":
        return False
    full = Path(root) / d
    if not full.is_dir():
        return False
    subs = {x.name for x in full.iterdir() if x.is_dir()}
    return bool(subs) and subs <= STATUS_KINDS


def walk(root: str | Path) -> Iterator[tuple[str, list[str], list[str]]]:
    """Walk the project, minus the ignore list, hidden folders and the status folder."""
    for dirpath, dirnames, files in os.walk(root):
        keep = [d for d in dirnames if d not in IGNORE and not d.startswith(".")]
        dirnames[:] = [d for d in keep if not playbook_folder(root, dirpath, d)]
        yield dirpath, dirnames, files


# A tree line: any box-drawing or indentation, then `name/`, optionally a `#`
# comment.
TREE_LINE = re.compile(r"^[\s|`+\-│├└─]*([A-Za-z0-9._\-]+)/\s*(?:#.*)?$")


def read_text(path: str | Path, errors: str = "strict") -> str:
    """Return a file's whole text."""
    return Path(path).read_text(encoding="utf-8", errors=errors)


def drawn_folders(structure_md: str | Path) -> set[str]:
    """Folder names drawn inside ``` fenced blocks in STRUCTURE.md."""
    text = read_text(structure_md)
    names = set()
    for block in re.findall(r"```[^\n]*\n(.*?)```", text, re.DOTALL):
        for line in block.splitlines():
            m = TREE_LINE.match(line.rstrip())
            if m and m.group(1) not in {".", ".."}:
                names.add(m.group(1))
    return names


def hub_files(structure_md: str | Path) -> list[str] | None:
    """Return the hub paths under the `## Hub files` heading, if the map has one.

    One path per row: the FIRST backticked token of every table row
    (| `path` | ... |) or list item (- `path` ...). Prose in the section is
    ignored, so a sentence like "run `pnpm api`" there cannot fail the gate -
    only what the section actually lists as a hub is verified.
    """
    text = read_text(structure_md)
    body = section(text, "## Hub files", loose=True)
    if body is None:
        return None
    paths = set()
    for line in body.splitlines():
        row = re.match(r"^\s*(?:\||[-*])\s*`([^`\n]+)`", line)
        if row:
            paths.add(row.group(1))
    return sorted(paths)


SECTIONS = (
    "## Modules",
    "## Inside a module",
    "## Where does a new file go?",
    "## Where decisions live",
    "## Hub files",
)
TEST_DIRS = ("tests", "test", "__tests__")
# A superseded record: a table row with empty leading cells, or a list item,
# that starts with "superseded".
SUPERSEDED = r"^\s*(?:\|(?:\s*\|)*|[-*])\s*_?superseded\b"
SUPERSEDED_LINE = re.compile(SUPERSEDED, re.IGNORECASE)
PLACEHOLDER = re.compile(
    r"assertTrue\(\s*True\s*\)|^\s*assert\s+True\s*$"
    r"|expect\(\s*true\s*\)\.toBe\(\s*true\s*\)",
    re.MULTILINE,
)
TEST_FILE = re.compile(r"^(test_.*\.py|.*_test\.py|.*\.(test|spec)\.[jt]sx?)$")
# A target that lists the tasks is allowed to only print.
LISTING = {"help", "default", "list"}
# `echo "arrives with /foundation" && exit 1` (or `; false`) on one line fails:
# not print-only.
FAILS = re.compile(r"(?:&&|;|\|\|)\s*(?:@?exit\s+[1-9]|false\b)")
# a heading's number, as the playbook's documents write it: `## 2. Modules`, `##
# 2) Modules`
NUMBER = r"(?:\d+(?:\.\d+)*[.)]?\s+)?"
DIVIDER = set("|-: ")


def section(text: str, heading: str, *, loose: bool = False) -> str | None:
    """Return the body under a `## heading` line (numbered or not), or None when absent.

    `loose`: the heading may have more words after the name.
    """
    name = re.escape(heading.removeprefix("## "))
    tail = r"[^\n]*$" if loose else r"\s*$"
    m = re.search(
        r"^##\s+" + NUMBER + name + tail + r"(.*?)(?=^##\s|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return m.group(1) if m else None


def table_rows(body: str | None) -> Iterator[list[str]]:
    """Yield the cells of each table row in `body` (divider rows skipped)."""
    for line in (body or "").splitlines():
        if not line.lstrip().startswith("|") or set(line.strip()) <= DIVIDER:
            continue
        yield line.strip().strip("|").split("|")


def first_paths(body: str | None, cell: int = 1) -> list[str]:
    """Return the first backticked token in column `cell` of each table row."""
    out = []
    for cells in table_rows(body):
        if len(cells) >= cell:
            m = re.search(r"`([^`\n]+)`", cells[cell - 1])
            if m:
                out.append(m.group(1).rstrip("/"))
    return out


# Files with no extension that are still paths; any other backticked token with
# no slash, no dot and a capital letter or a ':' / space is a name
# (`LLMProvider`, `version:`), not a path - a logged run was failed 6 times for
# backticking interface names in this section.
EXTENSIONLESS = {
    "Dockerfile",
    "Containerfile",
    "Makefile",
    "GNUmakefile",
    "Justfile",
    "Procfile",
    "Gemfile",
    "Rakefile",
    "Vagrantfile",
    "Taskfile",
    "Brewfile",
    "LICENSE",
    "README",
    "CODEOWNERS",
}
HOME_HEADER = re.compile(r"(?i)\b(?:path|home|where|location|folder|file)s?\b")


def is_home_header(cell: str) -> bool:
    """Return True for a header cell that names the home column (path, where...)."""
    return "`" not in cell and HOME_HEADER.search(cell) is not None


def is_path(token: str) -> bool:
    """Return True when a backticked token names a file or folder, not a code name."""
    if re.search(r"[\s:()=,<>]", token):
        return False
    return (
        "/" in token
        or "\\" in token
        or "." in token
        or token in EXTENSIONLESS
        or re.fullmatch(r"[a-z0-9_\-]+", token) is not None
    )


def decision_homes(body: str | None) -> list[str]:
    """Return the home of each row under `## Where decisions live`.

    The first backticked PATH in the column whose header says path / home /
    where / location (the second column when no header says so). A backticked
    name such as `LLMProvider` is
    skipped, never failed as a missing path.
    """
    out: list[str] = []
    col = None
    for cells in table_rows(body):
        if col is None:
            col = next(
                (i for i, c in enumerate(cells) if is_home_header(c)),
                None,
            )
            if col is not None:
                continue  # the header row
            col = 1
        if len(cells) > col:
            tokens = re.findall(r"`([^`\n]+)`", cells[col])
            token = next((t for t in tokens if is_path(t)), None)
            if token:
                out.append(token.rstrip("/"))
    return out


def print_only(target: str | None, cmds: list[str]) -> bool:
    """Return True when every command of a task-runner target is a bare echo."""
    return bool(
        target
        and cmds
        and target not in LISTING
        and all(re.match(r"@?echo\b", c) and not FAILS.search(c) for c in cmds),
    )


def print_only_targets(root: str | Path) -> list[str]:
    """Return the Makefile / justfile targets whose every command is an echo.

    `make seed` would report success on nothing.
    """
    bad = []
    for name in ("Makefile", "justfile"):
        path = Path(root) / name
        if not path.is_file():
            continue
        target, cmds = None, []
        for line in [*read_text(path).splitlines(), "__end__:"]:
            m = re.match(r"^([A-Za-z0-9_.-]+)\s*:(?!=)", line)
            if m and not line[:1].isspace():
                if print_only(target, cmds):
                    bad.append(f"{name}: {target}")
                target, cmds = m.group(1), []
            elif target and line[:1].isspace() and line.strip()[:1] not in {"", "#"}:
                cmds.append(line.strip())
    return bad


HOOK_CONFIGS = (
    ".pre-commit-config.yaml",
    "lefthook.yml",
    "lefthook.yaml",
    ".lefthook.yml",
    ".husky/pre-commit",
)


def hooks_without_check(root: str | Path) -> list[str]:
    """Return the commit-hook configs that never run check_structure.

    A model that skipped the check is then caught by nobody.
    """
    return [
        h
        for h in HOOK_CONFIGS
        if (Path(root) / h).is_file()
        and "check_structure" not in read_text(Path(root) / h, errors="replace")
    ]


def placeholder_tests(root: str | Path) -> list[str]:
    """Test files that assert True: green on nothing."""
    bad = []
    for dirpath, _, files in walk(root):
        for f in files:
            if TEST_FILE.match(f):
                full = Path(dirpath) / f
                if PLACEHOLDER.search(read_text(full, errors="replace")):
                    bad.append(os.path.relpath(full, root))
    return bad


def disk_folders(root: str | Path) -> set[str]:
    """Every folder name on disk the walk reaches."""
    names: set[str] = set()
    for _, dirnames, _ in walk(root):
        names.update(dirnames)
    return names


# never walked even for a drawn name: installed dependencies and git's own files
HEAVY = {".git", ".venv", "venv", "node_modules", "__pycache__"}


def hidden_folders(root: str | Path) -> set[str]:
    """Folder names on disk inside a hidden or ignored folder (`.github/workflows/`).

    The walk leaves them out of the layout, so drawing one is fine and never
    "drawn but not on
    disk" (a logged run was refused for `.github/`).
    """
    names = set()
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in HEAVY]
        rel = os.path.relpath(dirpath, root)
        hidden = [p for p in Path(rel).parts if p in IGNORE or p.startswith(".")]
        inside = rel != "." and bool(hidden)
        names.update(d for d in dirnames if inside or d in IGNORE or d.startswith("."))
    return names


def modules(body: str | None) -> list[str]:
    """Return the modules under `## Modules`.

    A row that names a sub-folder of another listed module (`app/x/tests/`,
    `app/x/adapters/`)
    or a test folder describes that module, it is not a module of its own.
    """
    paths = first_paths(body)
    return [
        m
        for m in paths
        if m.rsplit("/", 1)[-1] not in TEST_DIRS
        and not any(m != o and m.startswith(o.rstrip("/") + "/") for o in paths)
    ]


def folder_paths(root: str | Path, names: set[str]) -> list[str]:
    """Return where each named folder sits, from the root ('scripts/frontend-audit')."""
    out = []
    for dirpath, dirnames, _ in walk(root):
        out += [
            Path(os.path.relpath(Path(dirpath) / d, root)).as_posix()
            for d in dirnames
            if d in names
        ]
    return sorted(out)


HOOK_MSG = "never runs check_structure.py - add it, so every commit re-checks the map"
PLACEHOLDER_MSG = "placeholder test (asserts True, tests nothing)"
NOT_ON_DISK = "but not on disk"
SUPERSEDED_MSG = (
    "superseded line outside ## Changes (delete the replaced row; keep its dated "
    "line under ## Changes)"
)
PRINT_ONLY = "task only prints and exits 0"
FAIL_HINT = "make it fail with 'arrives with /foundation'"
NO_TREE = "the map must be a fenced block drawing the layout"
SILENT = "or this check silently passes on nothing"


def map_problems(text: str, structure_md: str, root: Path) -> list[str]:
    """Return every problem but the folder comparison (sections, homes, hooks...)."""
    absent = [h for h in SECTIONS if section(text, h) is None]
    problems = [f"no `{h}` section in {structure_md}" for h in absent]
    for mod in modules(section(text, "## Modules")):
        if not (root / mod).is_dir():
            problems.append(f"module {mod}/ is listed under ## Modules but not on disk")
        elif not any((root / mod / t).is_dir() for t in TEST_DIRS):
            no_tests = f"module {mod}/ has no tests/ - a module is a complete lane"
            problems.append(no_tests)
    problems += [
        f"decision home not on disk: {home} (listed under ## Where decisions live)"
        for home in decision_homes(section(text, "## Where decisions live"))
        if not (root / home).exists()
    ]
    changes = section(text, "## Changes") or ""
    outside = text.replace(changes, "") if changes else text
    old = [ln.strip()[:80] for ln in outside.splitlines() if SUPERSEDED_LINE.match(ln)]
    problems += [f"{SUPERSEDED_MSG}: {line}" for line in old]
    problems += [f"commit hook {h} {HOOK_MSG}" for h in hooks_without_check(root)]
    problems += [f"{PLACEHOLDER_MSG}: {t}" for t in placeholder_tests(root)]
    problems += [f"{PRINT_ONLY} - {FAIL_HINT}: {t}" for t in print_only_targets(root)]
    return problems


def suggest_lines(root: Path, unmapped: list[str], structure_md: str) -> None:
    """Print the tree line to add for each folder the map lacks (never written)."""
    say(
        f"Lines to add to the tree in {structure_md} (not written - add each under its "
        "parent, with what goes there):",
    )
    for path in folder_paths(root, set(unmapped)):
        parent, _, name = path.rpartition("/")
        under = parent + "/" if parent else "the root"
        say(f"  under {under}:  {name}/   # <what goes here, one line>")


def main(argv: list[str]) -> int:
    """Compare STRUCTURE.md with the tree, print every mismatch, return the exit."""
    suggest = "--suggest" in argv
    argv = [a for a in argv if a != "--suggest"]
    structure_md = argv[0] if argv else "STRUCTURE.md"
    root = Path(argv[1] if len(argv) > 1 else ".")
    if not Path(structure_md).exists():
        say(f"check_structure: {structure_md} not found - /structure writes it")
        return NO_MAP
    drawn, disk = drawn_folders(structure_md), disk_folders(root)
    if not drawn:
        no_tree = f"no folder tree found in {structure_md}"
        say(f"check_structure: {no_tree} - {NO_TREE}, {SILENT}")
        return NO_MAP
    # the playbook's status folder may be drawn or not; either way it is not a
    # layout mismatch
    own = (
        {"status"} | {x.name for x in (root / "status").iterdir()}
        if playbook_folder(root, root, "status")
        else set()
    )
    missing = sorted(drawn - disk - own - hidden_folders(root))  # drawn, absent on disk
    unmapped = sorted(disk - drawn)  # on disk, absent from the map
    hubs = hub_files(structure_md)
    lost = [h for h in (hubs or []) if not (root / h).exists()]
    problems = map_problems(read_text(structure_md), structure_md, root)
    for p in problems:
        say(f"  [FAIL] {p}")
    for name in missing:
        say(f"  [FAIL] drawn in {structure_md} but not on disk: {name}/")
    for name in unmapped:
        say(f"  [FAIL] on disk but not in {structure_md}: {name}/")
    if suggest and unmapped:
        suggest_lines(root, unmapped, structure_md)
    for path in lost:
        say(f"  [FAIL] listed under Hub files in {structure_md} {NOT_ON_DISK}: {path}")
    checked = len(drawn | disk)
    hub_note = ", no Hub files section"
    if hubs is not None:
        hub_note = f", {len(hubs)} hub files"
    if missing or unmapped or lost or problems:
        say(
            f"check_structure: {len(missing)} missing | {len(unmapped)} unmapped | "
            f"{len(lost)} hub files lost | {len(problems)} other ({checked} folders "
            f"compared{hub_note})",
        )
        return MISMATCH
    agree = f"map and tree agree both ways ({checked} folders compared{hub_note})"
    say(f"check_structure: {agree}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
