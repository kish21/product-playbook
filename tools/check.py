#!/usr/bin/env python3
"""Consistency check for product-playbook — run locally or in CI.

Eats our own dog food: the toolkit preaches "CI that verifies its own rules", so this verifies the
toolkit's rules. Exits non-zero (fails the build) on any violation.

Checks:
  1. The skill set is identical across commands/, manifest.json, evals/evals.json, and VISION.md
     (flat `commands/*.md` AND directory-form `commands/<name>/SKILL.md`).
  2. manifest.json + evals/evals.json are valid JSON (so are the plugin manifests, if present).
  3. Every canonical PHASE skill (the vision->learn chain) has the template structure
     (Contract · Exit criteria · PRINCIPLES.md · Step 3b · Step 4 Handoff). The entry (playbook),
     cross-cutting (drift-check) and the UI suite (design-system, frontend-audit, new-component)
     have their own formats — they get registration + line-budget checks only.
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

# Canonical phase-template skills (the vision->learn chain /playbook walks).
TEMPLATE = {"vision", "scope", "plan", "architect", "structure", "foundation", "contracts",
            "build", "dev-check", "test", "eval", "ship", "learn"}


def fail(msg: str) -> None:
    errors.append(msg)


def skill_files() -> dict[str, Path]:
    """name -> path: flat commands/*.md AND directory-form commands/<name>/SKILL.md."""
    out: dict[str, Path] = {}
    for p in (ROOT / "commands").glob("*.md"):
        out[p.stem] = p
    for p in (ROOT / "commands").iterdir():
        if p.is_dir() and (p / "SKILL.md").exists():
            out[p.name] = p / "SKILL.md"
    return out


def main() -> int:
    files = skill_files()
    cmds = sorted(files)
    if not cmds:
        fail("no skills found in commands/")
        return done()

    # 2. JSON validity
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    evals = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
    for p in (ROOT / ".claude-plugin" / "plugin.json", ROOT / ".claude-plugin" / "marketplace.json"):
        if p.exists():
            json.loads(p.read_text(encoding="utf-8"))

    # 1. set equality across the four surfaces (evals may have many cases per skill -> set)
    man = sorted(c["id"] for c in manifest["commands"])
    evs = sorted({e["skill"] for e in evals["evals"]})
    vis_refs = set(re.findall(r"`/([a-z-]+)`", (ROOT / "VISION.md").read_text(encoding="utf-8")))
    if man != cmds:
        fail(f"manifest ids != commands/: only-in-manifest={set(man)-set(cmds)} only-in-commands={set(cmds)-set(man)}")
    if evs != cmds:
        fail(f"evals skills != commands/: {set(evs)^set(cmds)}")
    missing_in_vision = set(cmds) - vis_refs
    if missing_in_vision:
        fail(f"VISION.md does not reference: {missing_in_vision}")

    # 3 + 4. per-skill line budget; template structure for the canonical phases only
    for c in cmds:
        text = files[c].read_text(encoding="utf-8")
        n = len(text.splitlines())
        if n > LINE_BUDGET:
            fail(f"{c} is {n} lines (> {LINE_BUDGET})")
        if c in TEMPLATE:
            for token in ("## Contract", "Exit criteria", "PRINCIPLES.md", "Step 3b", "Step 4 - Handoff"):
                # match the literal heading regardless of hyphen/dash style
                if token not in text and token.replace(" - ", " — ") not in text:
                    fail(f"{c} missing {token!r}")
    return done(len(cmds))


def done(n: int = 0) -> int:
    if errors:
        print("FAIL - product-playbook consistency check:")
        for e in errors:
            print(f"  x {e}")
        return 1
    print(f"OK - {n} skills consistent across commands/ + manifest + evals + VISION; structure + line budget pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
