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

A drawn-but-uncreated folder is silent doc<->code drift; an undrawn folder on disk is a layout decision
nobody recorded. Reading 25 folders by eye is slower and less reliable than this, and it turns a
judgement call into a deterministic one.

Usage:  python scripts/check_structure.py [STRUCTURE.md] [project-root]
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
# A tree line: any box-drawing or indentation, then `name/`, optionally followed by a `#` comment.
TREE_LINE = re.compile(r"^[\s|`+\-│├└─]*([A-Za-z0-9._\-]+)/\s*(?:#.*)?$")


def drawn_folders(structure_md):
    """Folder names drawn inside ``` fenced blocks in STRUCTURE.md."""
    text = open(structure_md, encoding="utf-8").read()
    names = set()
    for block in re.findall(r"```[^\n]*\n(.*?)```", text, re.S):
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
    text = open(structure_md, encoding="utf-8").read()
    m = re.search(r"^##\s+Hub files.*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return None
    paths = set()
    for line in m.group(1).splitlines():
        row = re.match(r"^\s*(?:\||[-*])\s*`([^`\n]+)`", line)
        if row:
            paths.add(row.group(1))
    return sorted(paths)


def disk_folders(root):
    names = set()
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE and not d.startswith(".")]
        for d in dirnames:
            names.add(d)
    return names


def main(argv):
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
    missing = sorted(drawn - disk)   # drawn in the map, absent on disk
    unmapped = sorted(disk - drawn)  # on disk, absent from the map
    hubs = hub_files(structure_md)
    lost = [h for h in (hubs or []) if not os.path.exists(os.path.join(root, h))]

    for name in missing:
        print(f"  [FAIL] drawn in {structure_md} but not on disk: {name}/")
    for name in unmapped:
        print(f"  [FAIL] on disk but not in {structure_md}: {name}/")
    for path in lost:
        print(f"  [FAIL] listed under Hub files in {structure_md} but not on disk: {path}")
    checked = len(drawn | disk)
    hub_note = f", {len(hubs)} hub files" if hubs is not None else ", no Hub files section"
    if missing or unmapped or lost:
        print(f"check_structure: {len(missing)} missing | {len(unmapped)} unmapped | {len(lost)} hub "
              f"files lost ({checked} folders compared{hub_note})")
        return 1
    print(f"check_structure: map and tree agree both ways ({checked} folders compared{hub_note})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
