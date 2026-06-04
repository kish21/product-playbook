#!/usr/bin/env python3
"""Consistency check for product-playbook — run locally or in CI.

Eats our own dog food: the toolkit preaches "CI that verifies its own rules", so this verifies the
toolkit's rules. Exits non-zero (fails the build) on any violation.

Checks:
  1. The skill set is identical across commands/, manifest.json, evals/evals.json, and VISION.md.
  2. manifest.json + evals/evals.json are valid JSON (so are the plugin manifests, if present).
  3. Every skill file has the required structure (Contract · Exit criteria · references PRINCIPLES.md;
     phase skills also have a Step-3b gate + a Handoff).
  4. Every skill file is under the SKILL line budget (500).
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINE_BUDGET = 500
errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def main() -> int:
    cmds = sorted(p.stem for p in (ROOT / "commands").glob("*.md"))
    if not cmds:
        fail("no skills found in commands/")
        return done()

    # 2. JSON validity
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    evals = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
    for p in (ROOT / ".claude-plugin" / "plugin.json", ROOT / ".claude-plugin" / "marketplace.json"):
        if p.exists():
            json.loads(p.read_text(encoding="utf-8"))

    # 1. set equality across the four surfaces
    man = sorted(c["id"] for c in manifest["commands"])
    evs = sorted(e["skill"] for e in evals["evals"])
    vision = (ROOT / "VISION.md").read_text(encoding="utf-8")
    vis_refs = set(re.findall(r"`/([a-z-]+)`", vision))
    if man != cmds:
        fail(f"manifest ids != commands/: only-in-manifest={set(man)-set(cmds)} only-in-commands={set(cmds)-set(man)}")
    if evs != cmds:
        fail(f"evals skills != commands/: {set(evs)^set(cmds)}")
    missing_in_vision = set(cmds) - vis_refs
    if missing_in_vision:
        fail(f"VISION.md does not reference: {missing_in_vision}")

    # 3 + 4. per-skill structure + line budget
    for c in cmds:
        text = (ROOT / "commands" / f"{c}.md").read_text(encoding="utf-8")
        n = len(text.splitlines())
        if n > LINE_BUDGET:
            fail(f"{c}.md is {n} lines (> {LINE_BUDGET})")
        for token in ("## Contract", "Exit criteria", "PRINCIPLES.md"):
            if token not in text:
                fail(f"{c}.md missing {token!r}")
        # playbook (entry) and drift-check (cross-cutting) don't advance the chain
        if c not in ("playbook", "drift-check"):
            for token in ("Step 3b", "Step 4 — Handoff"):
                if token not in text:
                    fail(f"{c}.md missing {token!r}")
    return done(len(cmds))


def done(n: int = 0) -> int:
    if errors:
        print("FAIL — product-playbook consistency check:")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print(f"OK — {n} skills consistent across commands/ · manifest · evals · VISION; structure + line budget pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
