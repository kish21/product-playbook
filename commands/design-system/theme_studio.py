# AI AGENT: STOP - do not read this file. The phase's start (`status.py next --phase <phase>`) printed every command
# and flag you need. A refusal names its fix: make it and run the SAME command again; `status.py set <phase> filled
# ... --dry-run` lists every gap at once. This source is not the instructions; reading it only fills your context.
"""theme_studio.py - puts the Theme Studio (references/theme-studio.md) into the sample page, so a run never
reads or re-types its code (L4: the block is ~15k characters a run carried on every later call).

Usage: python theme_studio.py <sample.html> --preset "Name|oklch(light)|oklch(dark)" (3 to 5 --preset)
       python theme_studio.py <sample.html> --remove --approved "<the owner's answer, word for word>"   (after the
       owner's looks-good: the approved sample is the page as users see it - the studio's floating button covered
       phone controls in 4 of 4 logged samples; refused with no answer or a "Change something" answer)

It inserts the block before </body> with the presets given (one palettes.md Accents row each), replaces a block
an earlier run inserted, and names every "The sample must" requirement of theme-studio.md the page misses.
Exit 0 = inserted (warnings are printed, act on them); 1 = refused, nothing written.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REF = Path(__file__).resolve().parent / "references" / "theme-studio.md"
START, END = "<!-- ===== THEME STUDIO", "<!-- ===== /THEME STUDIO ===== -->"
OKLCH = re.compile(r"^oklch\(\s*[\d.]+%?\s+[\d.]+\s+[\d.]+\s*\)$")
# theme-studio.md "The sample must" + §Notes, as tests on the page's text: (what it looks for, what is missing)
NEEDS = (
    (r":root\s*\{", "a :root (light) token block"),
    (r"\.dark\s*\{", "a .dark token block (Law 22)"),
    (r":root:not\(\.light\)", "the :root:not(.light) system-dark escape hatch (theme-studio.md §Notes, T5-6)"),
    (r"--font-sans\s*:", "--font-sans"),
    (r"font-size:\s*var\(--font-size-base", "html { font-size: var(--font-size-base, 16px) }"),
    (r'id=["\']ts_stage["\']', 'the page content wrapped in <div id="ts_stage" style="container-type:inline-size"> '
                              '(theme-studio.md §Notes, T5-1)'),
)

NOT_APPROVED = ("REFUSED - --remove is the step AFTER the owner approved the sample. First ask the confirm with your "
                "question tool: the sample at phone, tablet and desktop, what both checks found, and two options: \"I "
                "tried it - looks good (Recommended)\" · \"Change something\". After their looks-good run this again "
                "with --approved \"<their answer, word for word>\". Never open this script: this message is the "
                "instructions.")


def block(presets: list[list[str]]) -> str:
    text = REF.read_text(encoding="utf-8")
    m = re.search(r"```html\n(.*?)\n```", text, re.S)
    if not m:
        raise SystemExit("REFUSED - no ```html block in " + REF.as_posix())
    code, n = re.subn(r"var PRESETS=\[.*?\];", lambda _: "var PRESETS=" + json.dumps(presets) + ";", m.group(1),
                      count=1)
    if n != 1:
        raise SystemExit("REFUSED - no PRESETS array in the Theme Studio block of " + REF.as_posix())
    return code


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="theme_studio.py")
    ap.add_argument("page")
    ap.add_argument("--preset", action="append", default=[], help='"Name|oklch(light)|oklch(dark)"')
    ap.add_argument("--remove", action="store_true", help="take the Theme Studio out of the page (after approval)")
    ap.add_argument("--approved", default="", help="with --remove: the owner's answer to the sample confirm, word for "
                                                   "word")
    a = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # § on a cp1252 console
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    page = Path(a.page)
    if a.remove:
        # AG-DS1: a logged run removed the studio itself and saved a look the owner never saw - the after-approval step
        # needs the owner's answer
        if not a.approved.strip():
            print(NOT_APPROVED, file=sys.stderr)
            return 1
        if re.search(r"(?i)\bchange\b", a.approved):
            print("REFUSED - the owner asked for a change: regenerate the sample, run both checks again and ask the "
                  "same confirm again; --remove waits for \"looks good\"", file=sys.stderr)
            return 1
        if not page.is_file():
            print(f"REFUSED - {page.as_posix()} not found", file=sys.stderr)
            return 1
        html = page.read_text(encoding="utf-8")
        s, e = html.find(START), html.find(END)
        if s == -1 or e == -1:
            print(f"no Theme Studio in {page.as_posix()} - nothing to remove")
            return 0
        page.write_text(html[:s].rstrip() + "\n" + html[e + len(END):].lstrip("\n"), encoding="utf-8", newline="\n")
        print(f"Theme Studio removed from {page.as_posix()}")
        return 0
    try:
        if not 3 <= len(a.preset) <= 5:
            raise ValueError(f"give 3 to 5 --preset (palettes.md Accents rows vetted for the archetype), got "
                             f"{len(a.preset)}")
        presets = []
        for p in a.preset:
            parts = [x.strip() for x in p.split("|")]
            if len(parts) != 3 or not all(OKLCH.match(x) for x in parts[1:]):
                raise ValueError(f"preset {p!r} is not Name|oklch(L C H)|oklch(L C H)")
            presets.append(parts)
        if not page.is_file():
            raise ValueError(f"{page.as_posix()} not found")
        html = page.read_text(encoding="utf-8")
        s, e = html.find(START), html.find(END)
        if s != -1 and e != -1:
            html = html[:s].rstrip() + "\n" + html[e + len(END):].lstrip("\n")
        at = html.lower().rfind("</body>")
        if at == -1:
            raise ValueError(f"{page.as_posix()} has no </body>")
    except ValueError as err:
        print(f"REFUSED - {err}", file=sys.stderr)
        return 1
    html = html[:at] + block(presets) + "\n" + html[at:]
    page.write_text(html, encoding="utf-8", newline="\n")
    print(f"Theme Studio inserted into {page.as_posix()} with {len(presets)} presets: "
          + ", ".join(p[0] for p in presets))
    body = html[:html.find(START)]
    for pat, what in NEEDS:
        if not re.search(pat, body):
            print(f"  ! the page misses {what}: add it, then run this again")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
