#!/usr/bin/env python3
"""Consistency check for product-playbook — run locally or in CI.

Eats our own dog food: the toolkit preaches "CI that verifies its own rules", so this verifies the
toolkit's rules. Exits non-zero (fails the build) on any violation.

Checks:
  1. The skill set is identical across commands/, manifest.json, evals/evals.json, and VISION.md
     (flat `commands/*.md` AND directory-form `commands/<name>/SKILL.md`).
  2. manifest.json + evals/evals.json are valid JSON (so are the plugin manifests, if present).
  3. Every canonical PHASE skill (the vision->learn chain) has the template structure
     (Contract · Exit criteria · PRINCIPLES.md · Step 3b · Step 3c · Step 4 Handoff). The entry (playbook),
     cross-cutting (drift-check) and the UI suite are not phases in that chain, so the full template
     does not apply — but every skill that a build step DEPENDS ON must still declare a contract and
     name its principles, so design-system and new-component are checked for those two. frontend-audit
     stays exempt: its contract is enforced by audit.py's exit code, not by prose.
  4. Every skill file is under the SKILL line budget (500).
  5. One version everywhere: the newest CHANGELOG release is the source of truth, and
     manifest.json, .claude-plugin/plugin.json and the README badge must all match it.
  6. Every `#Section` a skill references is a real heading in templates/PRODUCT.md (a skill pointing at
     a section the template never defines is doc<->code drift inside the toolkit itself).
  7. A plugin install ships every skill: each directory-form skill's folder is listed under
     `skills` in .claude-plugin/plugin.json (Claude Code only scans skills/ by default).
  8. Every eval case is STRUCTURALLY sound: the required fields exist and are non-empty, ids are
     unique, no field name has drifted, and each skill carries at least MIN_EVAL_CASES cases.
     This does not execute the evals - it only stops the file from decaying while CI stays green.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINE_BUDGET = 500
# evals/evals.json: skill-creator's schema (references/schemas.md) requires id + prompt +
# expected_output; `files` (input fixtures) and `expectations` (individually gradeable statements)
# are optional. `skill` and `expected_artifacts` are this repo's documented extensions.
EVAL_REQUIRED = ("id", "skill", "prompt", "expected_output")
EVAL_OPTIONAL = ("files", "expectations", "expected_artifacts")
EVAL_LIST_FIELDS = ("files", "expectations", "expected_artifacts")
MIN_EVAL_CASES = 2  # the file's own note promises "2-3 trigger/behaviour checks per skill"
errors: list[str] = []

# Canonical phase-template skills (the vision->learn chain /playbook walks).
TEMPLATE = {"vision", "validate", "scope", "plan", "architect", "structure", "foundation", "contracts",
            "tickets", "build", "dev-check", "test", "eval", "ship", "learn"}
# Not phases, but load-bearing for a build step -> must still declare a contract + name their principles.
CONTRACTED = {"design-system", "new-component"}


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
        if c in CONTRACTED:
            for token in ("## Contract", "PRINCIPLES.md"):
                if token not in text:
                    fail(f"{c} missing {token!r} (a skill /build depends on must declare its contract)")
        if c in TEMPLATE:
            for token in ("## Contract", "Exit criteria", "PRINCIPLES.md", "Step 3b", "Step 3c", "Step 4 - Handoff"):
                # match the literal heading regardless of hyphen/dash style
                if token not in text and token.replace(" - ", " — ") not in text:
                    fail(f"{c} missing {token!r}")
    # 5. one version across CHANGELOG + manifest + plugin manifest + README badge
    check_versions(manifest)
    # 6. every referenced spine section actually exists in the template
    check_section_refs(files)
    # 7. plugin install ships every skill (directory-form ones need an explicit skills path)
    check_plugin_skill_paths(files)
    # 8. the eval cases themselves are well-formed (nothing executes them, so nothing else would notice)
    check_eval_cases(evals)

    return done(len(cmds))


def released_version() -> str | None:
    """The newest version declared in CHANGELOG.md — the single source of truth for a release."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^##\s*\[(\d+\.\d+\.\d+)\]", text, re.MULTILINE)
    return m.group(1) if m else None


def check_versions(manifest: dict) -> None:
    """5. Every version surface agrees with the newest CHANGELOG release."""
    want = released_version()
    if not want:
        fail("CHANGELOG.md has no '## [x.y.z]' release heading to version against")
        return
    surfaces: list[tuple[str, str | None]] = [("manifest.json", manifest.get("version"))]

    plugin = ROOT / ".claude-plugin" / "plugin.json"
    if plugin.exists():
        surfaces.append((".claude-plugin/plugin.json",
                         json.loads(plugin.read_text(encoding="utf-8")).get("version")))

    badge = re.search(r"badge/version-(\d+\.\d+\.\d+)-",
                      (ROOT / "README.md").read_text(encoding="utf-8"))
    surfaces.append(("README.md badge", badge.group(1) if badge else None))

    for name, got in surfaces:
        if got != want:
            fail(f"{name} version is {got!r}, but CHANGELOG declares {want!r}")


def check_section_refs(files: dict[str, Path]) -> None:
    """6. A skill may only reference spine sections the PRODUCT.md template actually defines.

    Only `#Capitalised` references of 3+ chars are treated as section names, so a CSS `#hex` or an
    issue `#N` is not mistaken for one. Caught `/ship` and `/learn` reading `#Eval` against a template
    that defines `## Evaluation` - a contract that had never matched.
    """
    tpl = (ROOT / "templates" / "PRODUCT.md").read_text(encoding="utf-8")
    headings = {m.group(1).split("<!--")[0].strip()
                for m in re.finditer(r"^##\s+(.+)$", tpl, re.MULTILINE)}
    for name, path in files.items():
        text = path.read_text(encoding="utf-8")
        for ref in sorted(set(re.findall(r"`#([A-Z][A-Za-z][A-Za-z \-]*?)`", text))):
            if ref not in headings:
                fail(f"{name} references `#{ref}`, which templates/PRODUCT.md does not define "
                     f"(sections: {', '.join(sorted(headings))})")


def check_plugin_skill_paths(files: dict[str, Path]) -> None:
    """7. Directory-form skills load as a plugin only if plugin.json points `skills` at their folder."""
    plugin = ROOT / ".claude-plugin" / "plugin.json"
    if not plugin.exists():
        return
    declared = {Path(s).as_posix().strip("./").rstrip("/")
                for s in json.loads(plugin.read_text(encoding="utf-8")).get("skills", [])}
    for name, path in files.items():
        if path.name != "SKILL.md":
            continue
        folder = path.parent.parent.relative_to(ROOT).as_posix()
        if folder not in declared:
            fail(f"{name} is directory-form ({folder}/{name}/SKILL.md) but plugin.json `skills` "
                 f"does not list ./{folder}/ - a plugin install would drop it")


def check_eval_cases(evals: dict) -> None:
    """8. Structural gate on evals/evals.json - the only thing standing between it and rot.

    CI never RUNS these cases, so a malformed one stays green forever. Six cases had already drifted
    to `assertions`/`expected_artifacts` with no `expected_output` at all before this existed: two
    schemas in one file, invisible because check 1 only ever compared the set of skill NAMES.
    """
    allowed = set(EVAL_REQUIRED) | set(EVAL_OPTIONAL)
    seen: set = set()
    per_skill: dict[str, int] = {}
    for i, case in enumerate(evals.get("evals", [])):
        where = case.get("id", f"index {i}")
        for field in EVAL_REQUIRED:
            value = case.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                fail(f"eval {where!r} is missing a non-empty {field!r} "
                     f"(required by skill-creator's eval schema)")
        for field in sorted(set(case) - allowed):
            fail(f"eval {where!r} has unknown field {field!r} "
                 f"(allowed: {', '.join(sorted(allowed))})")
        for field in EVAL_LIST_FIELDS:
            if field in case and not isinstance(case[field], list):
                fail(f"eval {where!r} field {field!r} must be a list, got {type(case[field]).__name__}")
        cid = case.get("id")
        if cid is not None:
            if cid in seen:
                fail(f"eval id {cid!r} is used more than once")
            seen.add(cid)
        skill = case.get("skill")
        if skill:
            per_skill[skill] = per_skill.get(skill, 0) + 1
    for skill, n in sorted(per_skill.items()):
        if n < MIN_EVAL_CASES:
            fail(f"{skill} has {n} eval case(s); evals.json promises at least {MIN_EVAL_CASES} per skill")


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
