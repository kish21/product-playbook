#!/usr/bin/env python3
"""Print the CHANGELOG.md section for one version — the body of its GitHub Release.

Used by .github/workflows/release.yml (and by hand) so the release notes are the changelog
entry itself, never a second copy that can drift.

Usage:
  python tools/release_notes.py            # newest version's section, to stdout
  python tools/release_notes.py 1.6.0      # a specific version's section
  python tools/release_notes.py --version  # just the newest version string, e.g. 1.6.1
  python tools/release_notes.py --title    # release title: "v1.6.1 — <first bold phrase>"
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADING = re.compile(r"^##\s*\[(\d+\.\d+\.\d+)\]", re.MULTILINE)


def sections() -> list[tuple[str, str]]:
    """[(version, body)] in file order — newest first, as the changelog is written."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    heads = list(HEADING.finditer(text))
    out = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body_start = text.find("\n", m.end())   # body begins after the heading LINE (which carries the date)
        out.append((m.group(1), text[body_start:end].strip() if body_start != -1 else ""))
    return out


def section(version: str | None = None) -> tuple[str, str]:
    secs = sections()
    if not secs:
        sys.exit("CHANGELOG.md has no '## [x.y.z]' heading")
    if version is None:
        return secs[0]
    for v, body in secs:
        if v == version:
            return v, body
    sys.exit(f"CHANGELOG.md has no section for {version}")


def title(version: str, body: str) -> str:
    """'v1.6.1 — <first bold phrase>' — the changelog opens every bullet with a bold summary."""
    m = re.search(r"\*\*(.+?)\*\*", body)
    headline = m.group(1).rstrip(".:") if m else ""
    return f"v{version} — {headline}" if headline else f"v{version}"


def main(argv: list[str]) -> None:
    # the changelog uses em dashes; never let a cp1252 console (Windows) mangle them on the way out
    sys.stdout.reconfigure(encoding="utf-8")
    flag = argv[1] if len(argv) > 1 and argv[1].startswith("--") else None
    want = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else None
    version, body = section(want)
    if flag == "--version":
        print(version)
    elif flag == "--title":
        print(title(version, body))
    else:
        # the date line is in the heading, not the body; put it back so the release says when
        line = re.search(rf"^##\s*\[{re.escape(version)}\][^\n]*", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.MULTILINE)
        date = line.group(0).split("]", 1)[1].strip(" -—") if line else ""
        print(f"_Released {date}_ · [full changelog](CHANGELOG.md)\n\n{body}" if date else body)


if __name__ == "__main__":
    main(sys.argv)
