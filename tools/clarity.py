"""clarity.py - the clarity standard's checks (docs/clarity-standard.md), run by tools/check.py (checks 49-52).

Each check counts its findings per file and compares them to tools/clarity-baseline.json:
  - a count ABOVE the baseline fails: the change added a vague word, a broken pointer, a tool-only name;
  - a count BELOW the baseline also fails until the baseline is lowered, so every clean-up is locked in;
  - a skill ABOVE its character budget fails; budgets only go down, after that skill's review.

The baseline is the debt the clarity review pays off, file by file. It is edited only by hand, or by
`python tools/clarity.py --write-baseline` after a deliberate clean-up - and that diff is reviewed like code.

    python tools/clarity.py                  run the checks (what check.py does)
    python tools/clarity.py --report [path]  list every finding, file:line, for the review
    python tools/clarity.py --write-baseline rewrite the counts to what the files hold now (budgets kept)
"""
from __future__ import annotations
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "tools" / "clarity-baseline.json"

# The files an agent is told to follow. Case files and LESSONS are history: bound by C4 (their titles are
# pointer targets) but not by C2, because a story may quote the vague sentence that caused it.
RULE_FILES = ["PRINCIPLES.md", "references/mechanisms.md", "references/mechanisms-on-demand.md",
              "docs/state-model.md", "references/capabilities.md"]


def instruction_files() -> list[Path]:
    out = [ROOT / f for f in RULE_FILES if (ROOT / f).exists()]
    out += sorted((ROOT / "commands").rglob("*.md"))
    out += sorted((ROOT / "templates").glob("*.md"))
    return out


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


# ---- C2: no judgement word without a method -------------------------------------------------------
# A banned word passes when the SAME SENTENCE carries its method: a `code span`, a digit, or a pointer
# (a section sign or an arrow). "if/when unsure" passes only as "ask the user" or "the stricter option".
# Known limit: a sentence that carries an unrelated code span passes too; the review reads every hit.
VAGUE = re.compile(
    r"\b(affected|relevant|appropriate|if in doubt|(?:as|if|when) needed|(?:where|if) possible|enough|"
    r"obvious(?:ly)?|non-trivial|trivial|significant(?:ly)?|substantial|reasonable|sensible|meaningful|"
    r"consider|carefully|properly|thoroughly|just in case|small|large|big|minor|major|a few|several)\b",
    re.IGNORECASE)
UNSURE = re.compile(r"\b(?:if|when) (?:unsure|in doubt)\b", re.IGNORECASE)
METHOD = re.compile(r"`[^`]+`|\d|§|→")
UNSURE_OK = re.compile(r"\bask\b|stricter", re.IGNORECASE)


def sentences(text: str) -> list[tuple[int, str]]:
    """Sentences with the line each starts on. Code fences are skipped: a command is not prose."""
    out, buf, start, fence = [], [], 0, False
    for n, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if not line.strip() or line.lstrip().startswith(("#", "|", "- ", "* ")) or re.match(r"\s*\d+\.", line):
            if buf:
                out.append((start, " ".join(buf)))
            buf, start = [], n
        if line.strip():
            if not buf:
                start = n
            buf.append(line.strip())
    if buf:
        out.append((start, " ".join(buf)))
    split = []
    for n, s in out:
        for part in re.split(r"(?<=[.!?])[\"”’)*_]*\s+(?=[A-Z*_`(\"“])", s):
            split.append((n, part))
    return split


def vague_hits(path: Path) -> list[tuple[int, str]]:
    hits = []
    for n, s in sentences(path.read_text(encoding="utf-8")):
        u = UNSURE.search(s)
        if u and not UNSURE_OK.search(s):
            hits.append((n, u.group(0)))
        m = VAGUE.search(s)
        if m and not METHOD.search(s):
            hits.append((n, m.group(0)))
    return hits


# ---- C4: every pointer resolves ----------------------------------------------------------------------
TARGETS = {"PRINCIPLES": "PRINCIPLES.md", "MECHANISMS": "references/mechanisms.md",
           "MECHANISMS-ON-DEMAND": "references/mechanisms-on-demand.md", "STATE-MODEL": "docs/state-model.md",
           "LESSONS": "references/lessons.md", "CAPABILITIES": "references/capabilities.md"}
POINTER = re.compile(r"\b(PRINCIPLES|MECHANISMS-ON-DEMAND|MECHANISMS|STATE-MODEL|LESSONS|CAPABILITIES)(?:\.md)?`? ?§ ?"
                     r"([^,;|*)`\n]{1,60})")
CASE_POINTER = re.compile(r"case file: [\"“]?([A-Z][^)\"…]{2,60})")


def anchors(path: Path) -> list[str]:
    """What a pointer may name: a heading's short name (before ' — '), its number (2a), or a **bold term**."""
    text = path.read_text(encoding="utf-8")
    out = []
    for h in re.findall(r"^#{1,4} (.+)$", text, re.M):
        h = h.strip().lstrip("§").strip()
        out.append(re.split(r" — | \(", h)[0].strip().lower())
        num = re.match(r"(\d+[a-z]?)\.", h)
        if num:
            out.append(num.group(1))
    out += [b.strip().rstrip(".").lower() for b in re.findall(r"\*\*([^*]{3,60})\*\*", text)]
    return [a for a in out if a]


def pointer_hits(path: Path, cache: dict) -> list[tuple[int, str]]:
    hits = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for m in POINTER.finditer(line):
            target = ROOT / TARGETS[m.group(1)]
            if not target.exists():
                hits.append((n, f"{m.group(1)} (file missing)"))
                continue
            names = cache.setdefault(target, anchors(target))
            want = m.group(2).strip().lower()
            if not any(want.startswith(a) for a in names):
                hits.append((n, f"{m.group(1)} §{m.group(2).strip()[:40]}"))
        for m in CASE_POINTER.finditer(line):
            want = m.group(1).strip().strip('"“”').lower()
            titles = cache.setdefault("case", [t.strip().strip('"“”').lower() for f in (ROOT / "references").glob("case-files-*.md")
                                               for t in re.findall(r"^#{2,4} (.+)$", f.read_text(encoding="utf-8"), re.M)])
            if not any(want.startswith(t) or t.startswith(want) for t in titles):
                hits.append((n, f"case file: {m.group(1)[:40]}"))
    return hits


# ---- C7: tool-neutral -----------------------------------------------------------------------------------
# One tool's command named in a skill, outside the capability map. A skill names the capability and points
# to references/capabilities.md, where each tool's native way lives. ${CLAUDE_PLUGIN_ROOT} is not listed:
# it is the plugin route's path, and a copy install rewrites it (check 41).
TOOL_ONLY = re.compile(r"(?<![\w/.-])/(code-review|security-review|run|loop|schedule|deep-research|compact)\b(?![/\w-])"
                       r"|\bAskUserQuestion\b|\bClaude Code\b")


def tool_hits(path: Path) -> list[tuple[int, str]]:
    if rel(path) == "references/capabilities.md":
        return []
    return [(n, m.group(0)) for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
            for m in TOOL_ONLY.finditer(line)]


# ---- C8: skill size -------------------------------------------------------------------------------------
def skill_entry_files() -> list[Path]:
    c = ROOT / "commands"
    return sorted(list(c.glob("*.md")) + list(c.glob("*/SKILL.md")))


def measure() -> dict:
    files = instruction_files()
    cache: dict = {}
    counts = {"vague": {}, "pointers": {}, "tool_only": {}}
    for p in files:
        for key, fn in (("vague", vague_hits), ("pointers", lambda x: pointer_hits(x, cache)), ("tool_only", tool_hits)):
            n = len(fn(p))
            if n:
                counts[key][rel(p)] = n
    counts["chars"] = {rel(p): len(p.read_text(encoding="utf-8")) for p in skill_entry_files()}
    return counts


NAMES = {"vague": "C2 vague words without a method", "pointers": "C4 pointers that name no existing heading",
         "tool_only": "C7 one tool's command named outside the capability map"}


def run(fail) -> None:
    """Checks 49-52. `fail` is check.py's collector."""
    if not BASELINE.exists():
        fail("tools/clarity-baseline.json is missing - the clarity checks have nothing to hold the line against")
        return
    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    now = measure()
    for key, label in NAMES.items():
        b, n = base.get(key, {}), now[key]
        for f in sorted(set(b) | set(n)):
            was, got = b.get(f, 0), n.get(f, 0)
            if got > was:
                fail(f"{label}: {f} has {got}, baseline {was} - the change added {got - was}; "
                     f"`python tools/clarity.py --report {f}` lists them")
            elif got < was:
                fail(f"{label}: {f} has {got}, baseline {was} - lock the clean-up in: lower the baseline to {got} "
                     f"(`python tools/clarity.py --write-baseline`)")
    budgets = base.get("char_budget", {})
    for f, size in sorted(now["chars"].items()):
        if f not in budgets:
            fail(f"C8 {f} has no character budget in tools/clarity-baseline.json")
        elif size > budgets[f]:
            fail(f"C8 {f} is {size} characters, budget {budgets[f]} - cut it (rule inventory before = after), "
                 f"or raise the budget in the same change with the reason in the PR")


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    if "--write-baseline" in argv:
        now = measure()
        old = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}
        budgets = old.get("char_budget") or dict(now["chars"])
        for f, size in now["chars"].items():
            budgets.setdefault(f, size)
        out = {"vague": now["vague"], "pointers": now["pointers"], "tool_only": now["tool_only"],
               "char_budget": dict(sorted(budgets.items()))}
        BASELINE.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {rel(BASELINE)}: " + ", ".join(f"{k} {sum(v.values())}" for k, v in out.items() if k != "char_budget"))
        return 0
    if "--report" in argv:
        only = argv[argv.index("--report") + 1:] or None
        cache: dict = {}
        for p in instruction_files():
            if only and rel(p) not in only:
                continue
            for key, fn in (("C2", vague_hits), ("C4", lambda x: pointer_hits(x, cache)), ("C7", tool_hits)):
                for n, what in fn(p):
                    print(f"{key}  {rel(p)}:{n}  {what}")
        return 0
    errs: list[str] = []
    run(errs.append)
    for e in errs:
        print(f"  x {e}")
    print("OK - clarity baseline holds" if not errs else f"FAIL - {len(errs)} clarity finding(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
