"""rule_inventory.py - proves a rewritten skill kept every rule of the version it rewrote (clarity standard C8).

A rules file, tools/rules/<skill>.json, pins the version before the rewrite (`base`, a commit) and lists:
  - rules:   each rule by id, with `old` phrases (found in the base text) and `new` phrases (found in the skill
             today, or in the file named by `home` when the rewrite moved the rule behind a pointer);
  - dropped: each removed sentence that carried no rule (the why, history, a duplicate), with the reason.

It fails when:
  - an `old` or dropped phrase is not in the base text (the inventory describes some other version);
  - a `new` phrase is missing (a rule the rewrite promised to keep is gone);
  - a line of the base text that is not kept verbatim still has more than SLACK words once every `old` and
    dropped phrase is taken out of it (words nobody accounted for - the inventory is incomplete).
Phrases are compared with runs of whitespace collapsed, so re-wrapping a line never matters.

Usage: python tools/rule_inventory.py [skill ...]   (default: every tools/rules/*.json)
Exit 0 = every rule accounted for; 1 = a finding; 2 = the base commit is not in this clone (shallow CI).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = ROOT / "tools" / "rules"
# Words a changed line may keep outside every phrase: joins such as "and", "then", "—", a list marker "1.".
SLACK = 3


def norm(s: str) -> str:
    return " ".join(s.split())


def base_text(rev: str, path: str) -> str | None:
    r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None


def check(spec_path: Path) -> tuple[list[str], bool]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    # A skill may have moved from commands/<skill>.md to commands/<skill>/SKILL.md since its base.
    flat, folder = f"commands/{spec['skill']}.md", f"commands/{spec['skill']}/SKILL.md"
    skill_path = folder if (ROOT / folder).exists() else flat
    old = base_text(spec["base"], flat) or base_text(spec["base"], folder)
    if old is None:
        return [f"{spec_path.name}: base {spec['base']} not in this clone"], False
    new = (ROOT / skill_path).read_text(encoding="utf-8")
    old_n, new_n = norm(old), norm(new)
    fails: list[str] = []
    anchors: list[str] = []
    for r in spec["rules"]:
        home = (ROOT / r["home"]).read_text(encoding="utf-8") if r.get("home") else new
        for p in r["old"]:
            anchors.append(norm(p))
            if norm(p) not in old_n:
                fails.append(f"{r['id']}: old phrase not in base {spec['base']}: {p!r}")
        for p in r["new"]:
            if norm(p) not in norm(home):
                fails.append(f"{r['id']} ({r['what']}): lost - {p!r} not in {r.get('home') or skill_path}")
    for d in spec["dropped"]:
        anchors.append(norm(d["old"]))
        if norm(d["old"]) not in old_n:
            fails.append(f"dropped phrase not in base {spec['base']}: {d['old']!r}")
    kept = {norm(line) for line in new.splitlines()}
    start = max(old.find("## Contract"), 0)  # a skill with no Contract block (frontend-audit): the whole text
    for n, line in enumerate(old[start:].splitlines(), old[:start].count("\n") + 1):
        ln = norm(line)
        if not ln or ln in kept:
            continue
        rest = ln
        for a in sorted(anchors, key=len, reverse=True):
            rest = rest.replace(a, " ")
        words = re.findall(r"[A-Za-z0-9#/$<>'][\w#/$<>'.-]*", rest)
        if len(words) > SLACK:
            fails.append(f"base line {n}: words nobody accounted for: {' '.join(words)[:120]!r}")
    return fails, True


def main(argv: list[str]) -> int:
    specs = [RULES / f"{s}.json" for s in argv] if argv else sorted(RULES.glob("*.json"))
    fails: list[str] = []
    missing_base = False
    for s in specs:
        f, ok = check(s)
        fails += f
        missing_base |= not ok
    for f in fails:
        print(f"  x {f}")
    if missing_base:
        return 2
    print("OK - every rule accounted for" if not fails else f"FAIL - {len(fails)} rule-inventory finding(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
