"""featuredoc.py - a feature doc's top half is for people: plain words, no code names, no rule codes.

The feature doc /build writes (docs/features/<feature>.md) has two halves (templates/feature-doc.md): the TOP half,
for the owner, under `## In short` · `## What you can do now` · `## What it protects you from` · `## Not done yet`;
then a `---` line and `## For developers and coding agents` with the contract, files, evidence and review.
A logged build's doc opened with a CLI line and code names (a persona id, a class name, a boolean field, R3/R4/R6,
`Archetype: none`) and buried the one point that mattered; the owner could not read it.

This refuses, in the top half: a missing or out-of-order heading, no developer half, a backticked span anywhere but
the ONE command under "What you can do now", a fenced code block, a rule code (R3, R3-1, D2, DP1, LP1, §Gates,
#Contracts), a snake_case name, a source file name, and the trace lines that belong below (Archetype:, Live-path
checks walked:, Real-world reach:). The developer half is not checked here: status.py checks what it must hold.
It WARNS (never refuses - the owner's rule for prose, and earlier tickets' docs predate numbering): a heading with no
number (`## 1. In short`, `### 5.4 Review`), and a top half whose sentences average over 18 words, has one over 30,
or joins ideas with em-dashes or ` · `.

    python featuredoc.py docs/features/<feature>.md [...]     exit 0 = every doc's top half is plain, 1 = a gap
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PEOPLE = ("In short", "What you can do now", "What it protects you from", "Not done yet")
DEV = "For developers and coding agents"
HEAD = re.compile(r"^##\s+(?:\d+\.\s+)?(.+?)\s*$", re.M)  # a number prefix (`## 1. In short`) is allowed
RULE_CODE = re.compile(r"(?<![\w-])(?:R\d+(?:-\d+)?|D\d+|DP\d+|LP\d+|RV\d+|DB\d+|T\d+)(?![\w-])"
                       r"|§\s*\w|(?<![\w&/])#[A-Z][A-Za-z-]+")
SNAKE = re.compile(r"\b[a-z][a-z0-9]*_[a-z0-9_]+\b")
SOURCE_FILE = re.compile(r"\b[\w./-]+\.(?:py|ts|tsx|js|jsx|go|rs|rb|java|kt|sql|ya?ml|toml|json)\b")
TRACE = re.compile(r"(?im)^\W*(archetype|live-path checks walked|real-world reach)\s*:")
H2_OK = re.compile(r"^(?:\d+\.\s+\S|Appendix\b)")
H3_OK = re.compile(r"^(?:\d+\.\d+\.?\s+\S|[A-Z]\.\d+\.?\s+\S)")


def warnings(text: str) -> list[str]:
    """What makes the doc harder to read or point at, said and never refused: an unnumbered heading, long
    sentences and dash chains in the top half."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    out, fence, bad = [], False, []
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"^(#{2,3})\s+(.+?)\s*$", line)
        if m and not (H2_OK if len(m.group(1)) == 2 else H3_OK).match(m.group(2)):
            bad.append(line.strip())
    if bad:
        out.append(f"{len(bad)} heading(s) without a number - `## 1. In short` ... `## 5. For developers and coding "
                   f"agents`, `### 5.4 Review` (first: {bad[0][:40]!r})")
    dev = re.search(rf"(?im)^##\s+(?:\d+\.\s+)?{re.escape(DEV)}", text)
    top = text[:dev.start()] if dev else text
    body = "\n".join(l for l in top.splitlines() if not l.startswith("#") and not l.lstrip().startswith(("|", "`")))
    sentences = [x for x in re.split(r"(?<=[.!?])\s+|\n\s*[-*\d.)]+\s+|\n{2,}", body) if len(x.split()) >= 3]
    words = [len(x.split()) for x in sentences]
    long = [w for w in words if w > 30]
    if words and (sum(words) / len(words) > 18 or long):
        out.append(f"the top half's sentences average {sum(words) / len(words):.0f} words, {len(long)} over 30 - one "
                   f"idea per sentence, about 15-18 words")
    dashes = sum(l.count(" — ") + l.count(" – ") + l.count(" · ") for l in body.splitlines())
    if dashes:
        out.append(f"{dashes} em-dash or ` · ` join(s) in the top half - one idea per sentence instead")
    return out


def top_half_gaps(text: str) -> list[str]:
    """What keeps a feature doc's top half from being readable by someone who never reads code; [] = none."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)  # the template's own instructions
    heads = [(m.group(1).strip(), m.start(), m.end()) for m in HEAD.finditer(text)]
    names = [h for h, _, _ in heads]
    gaps: list[str] = []
    dev = next((i for i, h in enumerate(names) if h.lower() == DEV.lower()), None)
    if dev is None:
        return [f"no `## {DEV}` heading - the contract, files, evidence and review go under it, after a --- line"]
    top = [h.lower() for h in names[:dev]]
    want = [p.lower() for p in PEOPLE]
    if top != want:
        gaps.append(f"the top half's headings are {names[:dev] or 'none'} - they must be exactly, in order: "
                    + " · ".join(PEOPLE))
    if not re.search(r"(?m)^---\s*$", text[:heads[dev][1]]):
        gaps.append(f"no --- line before `## {DEV}` - it is where a reader who never reads code stops")
    body = text[:heads[dev][1]]
    spans: dict[str, str] = {}
    for i, (name, _, end) in enumerate(heads[:dev]):
        nxt = heads[i + 1][1] if i + 1 < len(heads) else len(text)
        spans[name.lower()] = text[end:nxt]
    if "```" in body:
        gaps.append("a fenced code block in the top half - give the one command inline under What you can do now")
    code = re.findall(r"`[^`\n]+`", body)
    command_ok = len(re.findall(r"`[^`\n]+`", spans.get("what you can do now", ""))) <= 1
    if len(code) > 1 or not command_ok or (code and not re.search(r"`[^`\n]+`", spans.get("what you can do now", ""))):
        gaps.append(f"{len(code)} backticked name(s) in the top half ({', '.join(code[:4])}) - only ONE, the command "
                    f"under What you can do now; say the rest in plain words")
    plain = re.sub(r"`[^`\n]+`", " ", body)
    for label, rx in (("a rule code", RULE_CODE), ("a code name", SNAKE), ("a file name", SOURCE_FILE)):
        hits = sorted({m.group(0) for m in rx.finditer(plain)})
        if hits:
            gaps.append(f"{label} in the top half ({', '.join(hits[:5])}) - say what it means in plain words, or "
                        f"move it under `## {DEV}`")
    trace = sorted({m.group(1) for m in TRACE.finditer(plain)})
    if trace:
        gaps.append(f"a trace line in the top half ({', '.join(trace)}) - it belongs under `## {DEV}`")
    return gaps


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    if not argv:
        print(__doc__.strip().splitlines()[-1].strip())
        return 2
    bad = 0
    for arg in argv:
        p = Path(arg)
        gaps = top_half_gaps(p.read_text(encoding="utf-8", errors="replace")) if p.is_file() else [f"{arg} not found"]
        for g in gaps:
            print(f"FEATURE DOC {arg}: {g}")
        for w in warnings(p.read_text(encoding="utf-8", errors="replace")) if p.is_file() else []:
            print(f"warn {arg}: {w} (a warning: fix it if you are editing the doc anyway)")
        bad += bool(gaps)
    if not bad:
        print(f"feature doc: the top half is plain words ({len(argv)} file(s))")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
