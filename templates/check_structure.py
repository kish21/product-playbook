#!/usr/bin/env python3
"""check_structure.py - STRUCTURE.md's map and the real tree must agree BOTH ways.

Copied into a project by /structure (into scripts/ or tools/) and run at its Step 3b gate. It is
committed, not a scratch file: a gate whose evidence is a script that no longer exists is a claim, and
`evidence:` lines are re-run by the transition guard in later sessions.

What it checks, in both directions:
  * every folder DRAWN in the fenced tree block of STRUCTURE.md exists on disk
  * every folder ON DISK (minus the ignore list) appears in the map
  * every path listed under a `## Hub files` heading exists - one per table row or list item, the first
    backticked token (the files every lane may touch by one line; a hub file that has moved leaves
    /tickets pointing at nothing)
  * the sections a builder needs exist: `## Modules`, `## Inside a module`, `## Where does a new file go?`,
    `## Where decisions live`, `## Hub files`
  * every module under `## Modules` has its own tests/ (a module is a complete lane)
  * every home under `## Where decisions live` exists (Alembic recorded -> migrations/ on disk); a backticked
    name that is not a path (`LLMProvider`) is skipped, never failed
  * no placeholder test (`assert True`) and no task-runner target that only prints and exits 0: both
    report green on nothing
  * a commit-hook config that exists runs this check (pre-commit, lefthook, husky), so a skipped run is
    caught at the next commit
  * no `superseded` line outside `## Changes`: the map shows only the current tree, so a builder never
    sees two homes for one part (a replaced row is deleted; its dated line goes under `## Changes`)

A drawn-but-uncreated folder is silent doc<->code drift; an undrawn folder on disk is a layout decision
nobody recorded. Reading 25 folders by eye is slower and less reliable than this, and it turns a
judgement call into a deterministic one.

Usage:  python scripts/check_structure.py [STRUCTURE.md] [project-root] [--suggest]
        --suggest also prints, for each folder on disk the map lacks, the tree line to add under its parent -
        it never writes STRUCTURE.md: the one-line note of what goes there is yours to write.
Exit:   non-zero on any mismatch (CI-friendly).  Portable: stdlib only.
"""
import os
import re
import sys

# Directories that are never part of the recorded layout: tooling caches, dependency trees, build
# output, VCS. Extend it in the project rather than loosening the check.
IGNORE = {
    ".git", ".github", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build", ".next", ".nuxt", ".turbo", ".svelte-kit",
    "coverage", ".coverage", "htmlcov", ".idea", ".vscode", ".claude", "target", ".gradle",
}
# The playbook's own status folder (status.py writes one file per open item, ticket, release and drift row there):
# not part of the product's layout, so a project never has to draw it - and never edits this list to hide it.
STATUS_KINDS = {"open", "tickets", "releases", "drift"}


def playbook_folder(root, dirpath, d):
    """True for the root-level status/ that holds only status.py's item folders."""
    if os.path.normpath(dirpath) != os.path.normpath(root) or d != "status":
        return False
    full = os.path.join(root, d)
    if not os.path.isdir(full):
        return False
    subs = {x for x in os.listdir(full) if os.path.isdir(os.path.join(full, x))}
    return bool(subs) and subs <= STATUS_KINDS


def walk(root):
    """os.walk over the project, minus the ignore list, hidden folders and the playbook's status folder."""
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE and not d.startswith(".")
                       and not playbook_folder(root, dirpath, d)]
        yield dirpath, dirnames, files


# A tree line: any box-drawing or indentation, then `name/`, optionally followed by a `#` comment.
TREE_LINE = re.compile(r"^[\s|`+\-│├└─]*([A-Za-z0-9._\-]+)/\s*(?:#.*)?$")



def read_text(path, errors="strict"):
    """A file's whole text, closed after reading."""
    with open(path, encoding="utf-8", errors=errors) as f:
        return f.read()

def drawn_folders(structure_md):
    """Folder names drawn inside ``` fenced blocks in STRUCTURE.md."""
    text = read_text(structure_md)
    names = set()
    for block in re.findall(r"```[^\n]*\n(.*?)```", text, re.DOTALL):
        for line in block.splitlines():
            m = TREE_LINE.match(line.rstrip())
            if m and m.group(1) not in (".", ".."):
                names.add(m.group(1))
    return names


def hub_files(structure_md):
    """The hub paths under the `## Hub files` heading, if the map has one.

    One path per row: the FIRST backticked token of every table row (| `path` | ... |) or list item
    (- `path` ...). Prose in the section is ignored, so a sentence like "run `pnpm api`" there cannot
    fail the gate - only what the section actually lists as a hub is verified.
    """
    text = read_text(structure_md)
    m = re.search(r"^##\s+Hub files.*?$(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        return None
    paths = set()
    for line in m.group(1).splitlines():
        row = re.match(r"^\s*(?:\||[-*])\s*`([^`\n]+)`", line)
        if row:
            paths.add(row.group(1))
    return sorted(paths)


SECTIONS = ("## Modules", "## Inside a module", "## Where does a new file go?", "## Where decisions live",
            "## Hub files")
TEST_DIRS = ("tests", "test", "__tests__")
# A superseded record: a table row with empty leading cells, or a list item, that starts with "superseded".
SUPERSEDED_LINE = re.compile(r"^\s*(?:\|(?:\s*\|)*|[-*])\s*_?superseded\b", re.IGNORECASE)
PLACEHOLDER = re.compile(r"assertTrue\(\s*True\s*\)|^\s*assert\s+True\s*$|expect\(\s*true\s*\)\.toBe\(\s*true\s*\)", re.MULTILINE)
TEST_FILE = re.compile(r"^(test_.*\.py|.*_test\.py|.*\.(test|spec)\.[jt]sx?)$")
# A target that lists the tasks is allowed to only print.
LISTING = {"help", "default", "list"}
# `echo "arrives with /foundation" && exit 1` (or `; false`) on one line fails, so it is not print-only.
FAILS = re.compile(r"(?:&&|;|\|\|)\s*(?:@?exit\s+[1-9]|false\b)")


def section(text, heading):
    """The body under a `## heading` line, or None when the heading is absent."""
    m = re.search(r"^" + re.escape(heading) + r"\s*$(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else None


def first_paths(body, cell=1):
    """The first backticked token in column `cell` of each table row (header and divider rows skipped)."""
    out = []
    for line in (body or "").splitlines():
        if not line.lstrip().startswith("|") or set(line.strip()) <= set("|-: "):
            continue
        cells = line.strip().strip("|").split("|")
        if len(cells) >= cell:
            m = re.search(r"`([^`\n]+)`", cells[cell - 1])
            if m:
                out.append(m.group(1).rstrip("/"))
    return out


# Files with no extension that are still paths; any other backticked token with no slash, no dot and a capital
# letter or a ':' / space is a name (`LLMProvider`, `version:`), not a path - a logged run was failed 6 times for
# backticking interface names in this section (2026-10-03).
EXTENSIONLESS = {"Dockerfile", "Containerfile", "Makefile", "GNUmakefile", "Justfile", "Procfile", "Gemfile",
                 "Rakefile", "Vagrantfile", "Taskfile", "Brewfile", "LICENSE", "README", "CODEOWNERS"}


def is_path(token):
    if re.search(r"[\s:()=,<>]", token):
        return False
    return ("/" in token or "\\" in token or "." in token or token in EXTENSIONLESS
            or re.fullmatch(r"[a-z0-9_\-]+", token) is not None)


def decision_homes(body):
    """The home of each row under `## Where decisions live`: the first backticked PATH in the column whose header
    says path / home / where / location (the second column when no header says so). A backticked name such as
    `LLMProvider` is skipped, never failed as a missing path."""
    out, col = [], None
    for line in (body or "").splitlines():
        if not line.lstrip().startswith("|") or set(line.strip()) <= set("|-: "):
            continue
        cells = line.strip().strip("|").split("|")
        if col is None:
            col = next((i for i, c in enumerate(cells) if "`" not in c
                        and re.search(r"(?i)\b(?:path|home|where|location|folder|file)s?\b", c)), None)
            if col is not None:
                continue  # the header row
            col = 1
        if len(cells) > col:
            token = next((t for t in re.findall(r"`([^`\n]+)`", cells[col]) if is_path(t)), None)
            if token:
                out.append(token.rstrip("/"))
    return out


def print_only_targets(root):
    """Makefile / justfile targets whose every command is an echo: `make seed` reports success on nothing."""
    bad = []
    for name in ("Makefile", "justfile"):
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            continue
        target, cmds = None, []
        for line in read_text(path).splitlines() + ["__end__:"]:
            m = re.match(r"^([A-Za-z0-9_.-]+)\s*:(?!=)", line)
            if m and not line[:1].isspace():
                if target and cmds and target not in LISTING and all(re.match(r"@?echo\b", c) and not FAILS.search(c)
                                                                      for c in cmds):
                    bad.append(f"{name}: {target}")
                target, cmds = m.group(1), []
            elif target and line[:1].isspace() and line.strip() and not line.strip().startswith("#"):
                cmds.append(line.strip())
    return bad


HOOK_CONFIGS = (".pre-commit-config.yaml", "lefthook.yml", "lefthook.yaml", ".lefthook.yml",
                os.path.join(".husky", "pre-commit"))


def hooks_without_check(root):
    """Commit-hook configs in the project that never run check_structure: a model that skipped the check is
    then caught by nobody."""
    return [h for h in HOOK_CONFIGS if os.path.isfile(os.path.join(root, h))
            and "check_structure" not in open(os.path.join(root, h), encoding="utf-8", errors="replace").read()]


def placeholder_tests(root):
    bad = []
    for dirpath, dirnames, files in walk(root):
        for f in files:
            if TEST_FILE.match(f):
                full = os.path.join(dirpath, f)
                if PLACEHOLDER.search(read_text(full, errors="replace")):
                    bad.append(os.path.relpath(full, root))
    return bad


def disk_folders(root):
    names = set()
    for dirpath, dirnames, _ in walk(root):
        for d in dirnames:
            names.add(d)
    return names


def folder_paths(root, names):
    """Where each named folder sits on disk, as a path from the root ('scripts/frontend-audit')."""
    out = []
    for dirpath, dirnames, _ in walk(root):
        out += [os.path.relpath(os.path.join(dirpath, d), root).replace(os.sep, "/") for d in dirnames if d in names]
    return sorted(out)


def main(argv):
    suggest = "--suggest" in argv
    argv = [a for a in argv if a != "--suggest"]
    structure_md = argv[0] if argv else "STRUCTURE.md"
    root = argv[1] if len(argv) > 1 else "."
    if not os.path.exists(structure_md):
        print(f"check_structure: {structure_md} not found - /structure writes it")
        return 2
    drawn, disk = drawn_folders(structure_md), disk_folders(root)
    if not drawn:
        print(f"check_structure: no folder tree found in {structure_md} - the map must be a fenced "
              f"block drawing the layout, or this check silently passes on nothing")
        return 2
    # the playbook's status folder may be drawn or not; either way it is not a layout mismatch
    own = {"status"} | set(os.listdir(os.path.join(root, "status"))) if playbook_folder(root, root, "status") else set()
    missing = sorted(drawn - disk - own)   # drawn in the map, absent on disk
    unmapped = sorted(disk - drawn)  # on disk, absent from the map
    hubs = hub_files(structure_md)
    lost = [h for h in (hubs or []) if not os.path.exists(os.path.join(root, h))]

    text = read_text(structure_md)
    problems = [f"no `{h}` section in {structure_md}" for h in SECTIONS if section(text, h) is None]
    for mod in first_paths(section(text, "## Modules")):
        if not os.path.isdir(os.path.join(root, mod)):
            problems.append(f"module {mod}/ is listed under ## Modules but not on disk")
        elif not any(os.path.isdir(os.path.join(root, mod, t)) for t in TEST_DIRS):
            problems.append(f"module {mod}/ has no tests/ - a module is a complete lane")
    for home in decision_homes(section(text, "## Where decisions live")):
        if not os.path.exists(os.path.join(root, home)):
            problems.append(f"decision home not on disk: {home} (listed under ## Where decisions live)")
    changes = section(text, "## Changes") or ""
    outside = text.replace(changes, "") if changes else text
    problems += [f"superseded line outside ## Changes (delete the replaced row; keep its dated line under "
                 f"## Changes): {line.strip()[:80]}" for line in outside.splitlines() if SUPERSEDED_LINE.match(line)]
    problems += [f"commit hook {h} never runs check_structure.py - add it, so every commit re-checks the map"
                 for h in hooks_without_check(root)]
    problems += [f"placeholder test (asserts True, tests nothing): {t}" for t in placeholder_tests(root)]
    problems += [f"task only prints and exits 0 - make it fail with 'arrives with /foundation': {t}"
                 for t in print_only_targets(root)]
    for p in problems:
        print(f"  [FAIL] {p}")
    for name in missing:
        print(f"  [FAIL] drawn in {structure_md} but not on disk: {name}/")
    for name in unmapped:
        print(f"  [FAIL] on disk but not in {structure_md}: {name}/")
    if suggest and unmapped:
        print(f"Lines to add to the tree in {structure_md} (not written - add each under its parent, with what goes there):")
        for path in folder_paths(root, set(unmapped)):
            parent, _, name = path.rpartition("/")
            print(f"  under {parent + '/' if parent else 'the root'}:  {name}/   # <what goes here, one line>")
    for path in lost:
        print(f"  [FAIL] listed under Hub files in {structure_md} but not on disk: {path}")
    checked = len(drawn | disk)
    hub_note = f", {len(hubs)} hub files" if hubs is not None else ", no Hub files section"
    if missing or unmapped or lost or problems:
        print(f"check_structure: {len(missing)} missing | {len(unmapped)} unmapped | {len(lost)} hub "
              f"files lost | {len(problems)} other ({checked} folders compared{hub_note})")
        return 1
    print(f"check_structure: map and tree agree both ways ({checked} folders compared{hub_note})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
