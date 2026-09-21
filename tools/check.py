#!/usr/bin/env python3
"""Consistency check for product-playbook — run locally or in CI.

Eats our own dog food: the playbook preaches "CI that verifies its own rules", so this verifies the
playbook's rules. Exits non-zero (fails the build) on any violation.

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
     manifest.json, .claude-plugin/plugin.json and the audit engine must all match it. The README states
     no version: a hard-coded one reads as current between a merge and the next release.
  6. Every `#Section` a skill references is a real heading in templates/PRODUCT.md (a skill pointing at
     a section the template never defines is doc<->code drift inside the playbook itself).
  7. A plugin install ships every skill: each directory-form skill's folder is listed under
     `skills` in .claude-plugin/plugin.json (Claude Code only scans skills/ by default).
  8. Every eval case is STRUCTURALLY sound: the required fields exist and are non-empty, ids are
     unique, no field name has drifted, and each skill carries at least MIN_EVAL_CASES cases.
     This does not execute the evals - it only stops the file from decaying while CI stays green.
  9. Every phase skill's `Step 0 - ... prior-gate check` actually GATES: its body names a prior
     `#Section`, offers an override, AND requires that override to be RECORDED with a reason.
     Offering a way through is half the rule; a bypass nobody can see afterwards turns a gated
     workflow into an advisory one, so the heading can never again stand in for the behaviour.
 10. Every `§Section` pointer RESOLVES: a skill saying "`MECHANISMS.md` §Declined runs" must name a
     heading that file really has. ~100 pointers were rewritten when the mechanisms moved out of
     PRINCIPLES.md, and a dangling cross-reference is worse than the fat file it came from.
 11. No governing file is over the SIZE threshold it sets for everyone else. PRINCIPLES.md reached
     25.8KB against its own ~15KB prune rule, because a rule with no check is a suggestion. Skill files
     carry no size cap (#287): at the cap, a needed line could only land by cutting working instructions.
 12. Every phase skill declares its GATE TYPE - input (the answer lives only in the user's head, so it
     can never be batched) - derivation (computable from prior sections) - verification (pass/fail on
     repo evidence). Declared per skill because it is a property of the gate; a global '--auto' flag
     would be a mode that merely hopes each skill behaves. Rejected with reasons in docs/state-model.md.
 13. Every skill that writes a spine section declares its STATE-MODEL participation - declined,
     override, superseded - each implemented or marked n/a WITH A REASON. Re-run semantics covered 6 of
     16 skills and nobody could tell which gaps were intentional; that ambiguity was the defect.
 14. Every EVIDENCE line that exists is well-formed: `evidence: <command> -> <result> · <artefact> ·
     <date>`, the one representation settled in docs/state-model.md 2f. Evidence is optional - a
     criterion that was judged rather than measured carries none and is reported UNVERIFIED, which is
     honest - but a line that LOOKS re-runnable and is not is strictly worse than prose.
 15. One skill COUNT everywhere: every "N skills" / "N commands" claim in README.md (badge and prose)
     and the VISION.md skills comment must equal the real number of skills in commands/. The repo
     description on GitHub quoted a stale 18 for months while the README said 21 - a wrong count on
     a project whose thesis is docs-match-reality. The description lives outside the repo, but the
     number it quotes now has exactly one source.
 16. Every skill that writes a spine section (/adopt included) RUNS THE TRANSITION GUARD where it closes
     its gate: a clause naming the guard, pointing beside itself at MECHANISMS.md 3b item 4 where it is
     defined once, and saying UNVERIFIED does not block. Read in the Step 3b->3c region and in a window
     around the phrase, because both words already occur elsewhere. /drift-check is the one exemption -
     it OWNS the claim-to-evidence pass the guard runs, so a pointer back to itself would be circular. The
     guard was deferred (docs/state-model.md 4) until 131 made evidence re-runnable; a guard nobody
     invokes is the opt-in /drift-check it was meant to stop relying on, so participation is checked.
 17. Every skill that writes a spine section CLOSES IT PROPERLY: the gate-closing region names
     MECHANISMS.md Commit the work (offer the commit, never just suggest a message) and Plain-language
     close (what just happened + what YOU do next). Both rules pre-existed and neither was executed
     anywhere - three phases behaved three ways and a real project sat at zero commits after two of
     them - so the obligation is checked in the region, not trusted to the prose that defines it.
 21. A spine section with a COMPANION doc declares it, the template points at it, and the phase both
     reports the size of what it wrote and receipts every companion it opened with a verbatim quotation.
     The "a section is a RECORD" rule had no container for eight sections, and Follow the pointer - the
     guard that makes moving detail out safe - was named in 2 of 22 skills and checked by none.
 18. Every STATE docs/state-model.md defines is implemented by at least one skill. The `running` state
     was improvised in two live runs before it existed in the model; the mirror failure is a state
     defined in the model that no skill writes, which reads as a rule the product does not have.
 22. Every phase skill's HANDOFF names the phase that follows it in the canonical chain (optional phases
     may be skipped over). /contracts said "run /build" while the chain says contracts -> tickets -> build;
     on a live run the owner did what the skill said and /tickets never ran. Sixteen handoffs, one wrong,
     and nothing compared them to the order /playbook walks - so the chain had a hole only a user could find.
 41. Every rule file a skill names (PRINCIPLES, MECHANISMS, MECHANISMS-ON-DEMAND, LESSONS) is given by
     PATH: `${CLAUDE_PLUGIN_ROOT}/...`, which must exist in the repo, and a copy install (install.sh run for
     real) rewrites each such path to a file it installed. A plugin run grepped for MECHANISMS.md at the
     plugin root, found nothing, and went on without opening any rule file (#287).
 42. Every skill that names a rule file tells the run to OPEN `PRINCIPLES.md` and `MECHANISMS.md` before its
     first step - the two files that state they are read on every run - and does NOT pull the situational
     companions into that set. Naming a file is not reading it: with #287's paths in place, one run opened
     PRINCIPLES.md and not MECHANISMS.md, another the reverse (#290).
 23. The long derivation phases (foundation, contracts, tickets, build) carry the CONTEXT-HYGIENE rule -
     bulky command output goes to a file, one progress line per named step, close metrics measured or
     "not measured". Four phases in a row ignored /build's "bulky output to files" sentence and cost
     $70-75 each, ~60% of it re-reading tool output; a rule in one skill's prose bound nobody.
"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECTION_SIGN = "§"
ARROW = "→"
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
# /vision opens the chain: there is no earlier section for it to gate on, so check 9 skips it.
NO_PRIOR_PHASE = {"vision"}
# The affordance that makes a prior-gate a gate and not a wall: the user can proceed anyway.
# Standalone use is first-class in this playbook, so every gate must offer a way through.
# Each phrase is the one a real skill uses today: 12 say "allow override", /ship records "an override"
# on the release, /learn says "continue if the user wants". Widen it only alongside a skill that needs it.
OVERRIDE_PHRASES = ("allow override", "an override", "continue if the user wants")
# ... and the other half of the rule: the bypass leaves a trace. PRINCIPLES.md permitted a bare
# "warn but allow override" at :110 while :170 required a dated, reasoned line - and skills implemented
# :110. 10 of 14 gates could be waved through leaving nothing behind, so a later reader could not tell a
# gate that HELD from a gate that was bypassed. Each token below is required in the Step 0 body:
# the recorded form, the rule it comes from, and the user's own reason.
OVERRIDE_RECORD = ("Override <date>", "Declined runs")
OVERRIDE_REASON = ("reason in the user's own words", "reason in the user's words")


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


SKILL_LOCAL_HEADER = "This skill's OWN reference files are a DIFFERENT folder"


def check_skill_local_references(files: dict[str, Path]) -> None:
    """42. `references/<file>.md` means two different folders, so every citation must resolve.

    The plugin root has `references/` (MECHANISMS.md, MECHANISMS-ON-DEMAND.md, LESSONS.md,
    case-files-build.md) and each directory-form skill has its own `references/` beside SKILL.md.
    Both are spelled the same way inline. Once #287 made the plugin-root path explicit, runs learned
    "`references/` means the plugin root" - true for 4 files, false for 18. A logged run resolved
    `references/decisions.md` against the plugin root, found nothing, declared four shipped files
    missing, fell back to inline guidance and still reported every guard PASS.

    So: a bare `references/<file>.md` inside a skill must exist beside that SKILL.md, a
    `${CLAUDE_PLUGIN_ROOT}/references/<file>.md` must exist at the plugin root, and any skill with a
    local references/ folder must carry the header line that tells the two apart.
    """
    bare = re.compile(r"(?<!\{CLAUDE_PLUGIN_ROOT\}/)(?<![\w/])references/([a-z0-9-]+\.md)")
    rooted = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/references/([a-z0-9-]+\.md)")
    for name, path in sorted(files.items()):
        if path.name != "SKILL.md":
            continue
        local_dir = path.parent / "references"
        text = path.read_text(encoding="utf-8")
        where = path.relative_to(ROOT).as_posix()
        for m in rooted.finditer(text):
            if not (ROOT / "references" / m.group(1)).exists():
                fail(f"{where} points at plugin-root references/{m.group(1)}, which does not ship")
        cited = {m.group(1) for m in bare.finditer(text)} - {m.group(1) for m in rooted.finditer(text)}
        for ref in sorted(cited):
            if not (local_dir / ref).exists():
                at_root = (ROOT / "references" / ref).exists()
                extra = (" - it ships at the PLUGIN ROOT, so write it as "
                         "${CLAUDE_PLUGIN_ROOT}/references/" + ref) if at_root else ""
                fail(f"{where} cites bare references/{ref}, but no such file sits beside it"
                     f" in {local_dir.relative_to(ROOT).as_posix()}{extra}")
        # A skill that owns reference files must disambiguate the two folders, or the citations above
        # are readable as plugin-root paths again the moment someone reads only the header.
        if local_dir.is_dir() and any(local_dir.glob("*.md")):
            if SKILL_LOCAL_HEADER not in text:
                fail(f"{where} has its own references/ folder but never says so in the header - "
                     f"a run that learned the plugin-root rule will look in the wrong place")


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
    # 5. one version across CHANGELOG + manifest + plugin manifest + audit engine; none in the README
    check_versions(manifest)
    # 6. every referenced spine section actually exists in the template
    check_section_refs(files)
    # 7. plugin install ships every skill (directory-form ones need an explicit skills path)
    check_plugin_skill_paths(files)
    # 8. the eval cases themselves are well-formed (nothing executes them, so nothing else would notice)
    check_eval_cases(evals)
    # 9. a Step 0 titled "prior-gate check" actually gates
    check_prior_gates(files)
    # 10. every `§Section` pointer resolves to a real heading
    check_section_pointers(files)
    # 11. no governing file is over the size threshold it sets
    check_file_sizes(files)
    # 12. every phase skill declares where its answer lives
    check_gate_types(files)
    # 13. every section-writing skill declares its state-model participation
    check_state_model(files)
    # 14. every evidence line that exists is re-runnable
    check_evidence_lines(files)
    # 15. every stated skill count matches the real one
    check_skill_count(len(cmds), files)
    # 16. every section-writing skill actually invokes the transition guard at its Step 3b
    check_transition_guard(files)
    check_close_the_loop(files)
    check_states_are_implemented(files)
    # 19. §Commit the work checks THIS project's repo, not any ancestor's
    check_commit_repo_root()
    # 20. every exit criterion cites a spine field that actually exists
    check_criteria_have_a_home(files)
    # 21. a section with a companion declares it, and proves the pointer was followed
    check_companion_docs(files)
    # 22. every handoff names the next phase in the chain /playbook walks
    check_handoff_chain(files)
    # 23. the long derivation phases carry the context-hygiene rule
    check_context_hygiene(files)
    # 24. /tickets groups by module lane, stamps the board, shows the list it confirms
    check_lanes_and_board(files)
    check_ticket_sizing(files)
    # 25. a skill that composes a reviewer says the plain close is the run's last message
    check_close_is_last(files)
    # 26. a module folder is a complete lane; hub files are named; /build gates on the seat
    check_module_is_a_lane(files)
    # 27. batch mode is a mechanism, and the phases that may offer it do
    check_batch_mode_offered(files)
    # 28. /adopt routes in chain order and never to a phase whose Step 0 would reject the project
    check_adopt_routes_in_chain_order(files)
    # 29. /architect's benchmark is one search per open decision row, recorded
    check_architect_search_bound(files)
    # 30. /build's loop carries its overhead rules: read limit, triggered checks, flaky capture, board status,
    #     and the re-run condition that says when cited evidence stops counting
    check_build_loop_overhead(files)
    # 31. the audit runs the INSTALLED engine, and /foundation wires a project copy into hooks + CI
    check_audit_engine_resolution(files)
    check_audit_engine_behaviour()
    # 32. /foundation proves the boot at the end of Step 2 item 1, and 3b cites a boot only under /build's condition
    check_foundation_boot_evidence(files)
    # 33. /vision records every search its market read ran, with no count, and 3b checks the comparables against it
    check_vision_search_record(files)
    # 34. no private project is named anywhere in the repo; the names come from the environment, never the repo
    check_no_private_names()
    # 35. /playbook's offers state a measured, version-labelled sitting from one table and warn to start with room left
    check_sitting_lengths(files)
    # 36. /tickets groups milestone -> epic -> ticket and writes the plan, never the status, to a root TICKETS.md
    check_epic_plan(files)
    # 37. /tickets' verification runs over the local files before publishing and reads GitHub back after
    check_verification_publish_split(files)
    # 38. a shape-changing /structure re-run rewrites the moved paths in the tickets and TICKETS.md and syncs the issues
    check_structure_rerun_syncs_issues(files)
    # 39. an issue body is its ticket file, so "edited on GitHub" means what it says
    check_issue_body_is_ticket_file()
    # 40. the Theme Studio export is all of DESIGN.md §2, per mode, with the higher-contrast button text
    check_theme_studio_export()
    # 41. every rule file a skill names is opened by path, on the plugin AND the copy-install route
    check_rule_file_paths(files)
    check_copy_install_rule_paths()
    # 42. a skill's OWN references/ is a different folder from the plugin-root one, and says so
    check_skill_local_references(files)
    # 42. the run is told to OPEN the two rule files that are read on every run
    check_rule_files_are_opened(files)

    return done(len(cmds))


def released_version() -> str | None:
    """The newest version declared in CHANGELOG.md — the single source of truth for a release."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^##\s*\[(\d+\.\d+\.\d+)\]", text, re.MULTILINE)
    return m.group(1) if m else None


# A version the README states: a version badge, "version 1.2.3" / "release 1.2.3", or a bare "v1.2.3".
README_VERSION = re.compile(r"badge/version-[^)\s]*|\b(?:version|release)\s+v?\d+\.\d+\.\d+|\bv\d+\.\d+\.\d+\b",
                            re.IGNORECASE)


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

    # The README used to carry a version badge. Master moves ahead of the newest release between a merge and the
    # next release, so a hard-coded number there read as wrong to the owner; the Releases page carries it now.
    stated = README_VERSION.search((ROOT / "README.md").read_text(encoding="utf-8"))
    if stated:
        fail(f"README.md states a version ({stated.group(0)!r}) - a hard-coded version goes stale between releases; "
             f"the Releases page carries the current one")

    # A project's hooks and CI run a committed copy of the audit engine; its ENGINE_VERSION is how the
    # installed engine tells an old copy from a current one, so it moves with every release.
    engine = re.search(r'^ENGINE_VERSION = "([^"]*)"', AUDIT_ENGINE.read_text(encoding="utf-8"), re.MULTILINE)
    surfaces.append(("commands/frontend-audit/audit.py ENGINE_VERSION", engine.group(1) if engine else None))

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


def check_prior_gates(files: dict[str, Path]) -> None:
    """9. A Step 0 titled "prior-gate check" must contain a gate, not just the title.

    `/eval` carried the heading for five releases while gating on nothing an earlier phase writes: a
    user three phases early got no "run /dev-check then /test first", which is the orientation the
    playbook exists to give. A heading is not a behaviour, so this checks the body - the Step 0 block
    must name a prior `#Section` AND offer an override (standalone use is first-class here).
    """
    for name in sorted(TEMPLATE - NO_PRIOR_PHASE):
        text = files[name].read_text(encoding="utf-8")
        m = re.search(r"^## Step 0 .*?$(.*?)(?=^## )", text, re.MULTILINE | re.DOTALL)
        if not m:
            fail(f"{name} has no `## Step 0` block (every phase gates on what came before)")
            continue
        body = m.group(1)
        if not re.search(r"`#[A-Z][A-Za-z][A-Za-z \-]*`", body):
            fail(f"{name} Step 0 names no prior `#Section` - the heading says prior-gate check, "
                 f"but nothing is gated on")
        if not any(phrase in body.lower() for phrase in OVERRIDE_PHRASES):
            fail(f"{name} Step 0 gates with no override - standalone use is first-class, so a gate "
                 f"must warn and offer the missing phase, not block")
            continue
        for token in OVERRIDE_RECORD:
            if token not in body:
                fail(f"{name} Step 0 offers an override without requiring it to be RECORDED "
                     f"(missing {token!r}) - a bypass nobody can see afterwards makes the gate advisory")
        if not any(token in body for token in OVERRIDE_REASON):
            fail(f"{name} Step 0 records an override without capturing the user's OWN reason - "
                 f"'user said continue' is not a reason, and the agent's paraphrase is not the user's")


# Every shape in which the README or VISION states how many skills there are. Each is a claim that
# can go stale independently: the badge, the prose, the install table, the uninstall instructions.
COUNT_PATTERNS = (
    r"badge/Claude%20Code-(\d+)%20skills",
    r"\b(\d+)\s+(?:Claude Code\s+)?skills?\b",
    r"\b(\d+)\s+(?:step-by-step|custom Markdown)\s+commands\b",
)


# Where a `§`-pointer's file name resolves to on disk. Skills name the INSTALLED filename (companions
# land beside each other in ~/.claude/product-playbook/), not the repo path.
POINTER_FILES = {"PRINCIPLES.md": "PRINCIPLES.md", "MECHANISMS.md": "references/mechanisms.md",
                 "MECHANISMS-ON-DEMAND.md": "references/mechanisms-on-demand.md",
                 "LESSONS.md": "references/lessons.md"}
# ~15KB is the prune threshold for the governing files every session loads. Skill files had the same cap
# until #287: /tickets sat 2 bytes under it, so the one line naming where the rule files are could only land
# by cutting working instructions - and no playbook change may lower output quality. A skill is loaded only
# when invoked; the line budget (check 4) still bounds it, and moving situational mechanism into its own
# `references/` stays the way to keep one short.
SIZE_LIMIT = 15 * 1024
# MECHANISMS-ON-DEMAND first: the alternation is ordered longest-first so a pointer at the companion can
# never be matched as the shorter MECHANISMS.md branch and validated against the wrong file's headings.
POINTER_RE = re.compile(r"`?(MECHANISMS-ON-DEMAND\.md|PRINCIPLES\.md|MECHANISMS\.md)`?\s+§([^\n]{2,60})")


def headings(path: Path) -> set[str]:
    """`## §Name — trailing prose` -> the pointer-addressable name, with and without the marker."""
    out: set[str] = set()
    text = path.read_text(encoding="utf-8")
    names = [m.group(1) for m in re.finditer(r"^##\s+(.+)$", text, re.MULTILINE)]
    # a pointer may also name a BULLET rule inside a section - `PRINCIPLES.md §Secrets never get pushed`
    # is one of the Production-safeguards bullets, not a heading of its own.
    names += [m.group(1) for m in re.finditer(r"^\s*-\s+\*\*(.+?)\*\*", text, re.MULTILINE)]
    for name in names:
        name = name.strip()
        for form in (name, name.split(" — ")[0].split(" (")[0].strip()):
            out.add(form)
            out.add(form.lstrip("§"))
    return out


def check_section_pointers(files: dict[str, Path]) -> None:
    """10. A `<FILE>.md §Name` pointer names a heading that file actually has.

    The mechanisms moved out of PRINCIPLES.md into MECHANISMS.md and ~100 pointers were rewritten. A
    pointer is matched by PREFIX against the real headings, because skills write them inline ("per
    `MECHANISMS.md` §Step 3c, check what this phase produced...") - the text after the marker runs on
    into the sentence, so it can never be matched whole.
    """
    known: dict[str, set[str]] = {}
    for label, rel in POINTER_FILES.items():
        path = ROOT / rel
        if not path.exists():
            fail(f"{rel} is missing, but skills point at it as {label}")
            return
        known[label] = headings(path)
    # The template is copied into every project and the evals state what a run must say, so a stale pointer
    # there ships to users; "PRINCIPLES.md §Declined runs" sat in both, unseen, after the section moved (#287).
    extra = {ROOT / "README.md", ROOT / "VISION.md", ROOT / "PRINCIPLES.md",
             ROOT / "references" / "mechanisms.md",
             ROOT / "references" / "mechanisms-on-demand.md",
             ROOT / "templates" / "PRODUCT.md", ROOT / "evals" / "evals.json"}
    for path in sorted(set(files.values()) | extra):
        text = path.read_text(encoding="utf-8")
        where = path.relative_to(ROOT).as_posix()
        for m in POINTER_RE.finditer(text):
            label, rest = m.group(1), m.group(2)
            if not any(rest.startswith(h) for h in known[label] if h):
                fail(f"{where} points at {label} §{rest.split(',')[0].strip()!r}, which that file "
                     f"has no heading for - a dangling pointer is worse than the fat file it came from")
        # A BARE `§Name` is deliberately not checked: it also addresses other documents (a product's
        # own `DESIGN.md` §Tokens) and appears mid-sentence as ordinary prose. Only a pointer that
        # names one of the governing files is a claim this repo can be held to.


def content_size(path: Path) -> int:
    """Bytes with LF line endings - what CI measures. A Windows checkout under core.autocrlf=true adds a
    byte per line, so the same file read 15.0KB in CI and 15.1KB locally and the gate flipped with the
    line endings instead of the content."""
    return len(path.read_bytes().replace(b"\r\n", b"\n"))


def check_file_sizes(files: dict[str, Path]) -> None:
    """11. The ~15KB prune rule applies to the file that wrote it.

    PRINCIPLES.md set the threshold and exempted itself, reaching 25.8KB - and unlike any single skill it
    is loaded by EVERY skill, so its size is the per-session attention cost of the whole system. A rule
    with no check is how it got there.
    """
    for rel in ("PRINCIPLES.md", "references/mechanisms.md", "references/mechanisms-on-demand.md",
                "references/lessons.md"):
        size = content_size(ROOT / rel)
        if size > SIZE_LIMIT:
            fail(f"{rel} is {size / 1024:.1f}KB (> {SIZE_LIMIT // 1024}KB) - the prune rule it defines "
                 f"applies to it first: move mechanism into references/, or condense")


# Skills that must declare a gate type. frontend-audit is a verification gate by nature but carries no
# `## Contract` block by design (check 3 exempts it — its contract is audit.py's exit code, not prose), so
# requiring a prose declaration there would reintroduce exactly what that exemption avoids. See
# docs/state-model.md §2d.
GATE_DECLARING = TEMPLATE | CONTRACTED | {"adopt"}
GATE_TYPES = ("input", "derivation", "verification")
# Skills that write a PRODUCT.md section must declare their state-model participation. /playbook writes
# nothing (it routes); /new-component and /frontend-audit write code and a scorecard, not the spine.
STATE_DECLARING = TEMPLATE | {"design-system", "drift-check"}
STATE_MARKERS = ("`declined`", "`override`", "`superseded`")


def check_gate_types(files: dict[str, Path]) -> None:
    """12. Every phase skill declares WHERE ITS ANSWER LIVES, and an input gate declares it never batches.

    The distinction is not user experience level, it is derivability: /vision's answers exist only in the
    user's head, so autopiloting it does not skip a confirmation - it has the agent invent the product's
    premise. That is a property of the gate, so it is declared once per skill and checked here; a global
    `--auto` flag would be unenforceable by construction, being a mode that merely hopes each skill behaves
    (rejected, with reasons, in docs/state-model.md §3).
    """
    for name in sorted(GATE_DECLARING):
        text = files[name].read_text(encoding="utf-8")
        m = re.search(r"^- \*\*Gate type:\*\*\s*`([a-z]+)`(.*)$", text, re.MULTILINE)
        if not m:
            fail(f"{name} declares no `**Gate type:**` - an undeclared gate cannot be batched safely, "
                 f"because nothing says whether its answer is derivable (docs/state-model.md §2d)")
            continue
        kind, rest = m.group(1), m.group(2).lower()
        if kind not in GATE_TYPES:
            fail(f"{name} declares gate type {kind!r}, which is not one of {GATE_TYPES}")
        elif kind == "input" and "never batched" not in rest:
            fail(f"{name} is an `input` gate but does not declare that it is NEVER BATCHED - skipping an "
                 f"input gate fabricates the product's premise, so the ban is asserted, not assumed")


def check_state_model(files: dict[str, Path]) -> None:
    """13. Every skill that writes a spine section declares which state markers it implements.

    Re-run semantics covered 6 of 16 skills. Some of those omissions were correct - an append-only log
    cannot erase its own history - but with no declared rule, an intentional omission and a hole were
    indistinguishable, and THAT ambiguity was the defect. A marker is now either implemented or marked
    `n/a` with a reason; a bare `n/a` fails.
    """
    for name in sorted(STATE_DECLARING):
        text = files[name].read_text(encoding="utf-8")
        m = re.search(r"^- \*\*State model\*\*.*$", text, re.MULTILINE)
        if not m:
            fail(f"{name} writes a spine section but declares no `**State model**` - an omission and a "
                 f"deliberate exemption must never look the same (docs/state-model.md §2c)")
            continue
        line = m.group(0)
        for marker in STATE_MARKERS:
            if marker not in line:
                fail(f"{name} State model declares nothing for {marker}")
                continue
            after = line.split(marker, 1)[1]
            claim = after.split("·")[0]
            if "n/a" in claim and "—" not in claim.split("n/a", 1)[1]:
                fail(f"{name} marks {marker} n/a with no reason - an exemption without one is a hole "
                     f"wearing an exemption's clothes")


# The ONE evidence representation (docs/state-model.md §2f), as a pattern. Four fields, one line:
#   `evidence: <command> -> <result> · <artefact> · <YYYY-MM-DD>`
# Evidence is OPTIONAL - a criterion that was judged rather than measured carries none, and /drift-check
# reports it UNVERIFIED, which is honest. A line that LOOKS like evidence and names no command or no date
# is not: it stops anyone going to look, which is the whole failure mode this format exists to end.
EVIDENCE_RE = re.compile(r"`evidence:\s*(?P<body>[^`]+)`")
EVIDENCE_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
# The docs that TEACH the format necessarily contain placeholder specimens (`<command>`, `<date>`), so
# they are read for the grammar rather than graded against it.
EVIDENCE_TEACHING = {"docs/state-model.md", "templates/PRODUCT.md", "PRINCIPLES.md",
                     "commands/dev-check.md", "commands/drift-check.md"}


def check_evidence_lines(files: dict[str, Path]) -> None:
    """15. An evidence line that exists carries all four fields, or it is not evidence.

    "AI doesn't get to SAY something is true - it has to point to evidence that makes the claim true."
    A prose checkbox cannot be re-verified, so a checked box and a checked box with fabricated
    justification read identically to any later session. The fix is a re-runnable record; the risk the fix
    introduces is a record that LOOKS re-runnable and is not, which is strictly worse than prose, so the
    grammar is checked wherever it is used for real.
    """
    scan = set(files.values()) | {ROOT / "README.md", ROOT / "VISION.md", ROOT / "PRINCIPLES.md",
                                  ROOT / "templates" / "PRODUCT.md"}
    scan |= set((ROOT / "docs").glob("*.md"))
    for path in sorted(scan):
        where = path.relative_to(ROOT).as_posix()
        if where in EVIDENCE_TEACHING:
            continue
        for m in EVIDENCE_RE.finditer(path.read_text(encoding="utf-8")):
            body = m.group("body")
            if "->" not in body and "→" not in body:
                fail(f"{where} has an evidence line with no `command -> result`: {body.strip()!r} - "
                     f"evidence that names no command cannot be re-run, which is the only thing it is for")
            if not EVIDENCE_DATE_RE.search(body):
                fail(f"{where} has an evidence line with no YYYY-MM-DD date: {body.strip()!r} - "
                     f"undated evidence cannot be told from evidence that has gone stale")
            if body.count("·") < 2 and body.count(" - ") < 2:
                fail(f"{where} has an evidence line missing a field: {body.strip()!r} - the settled form "
                     f"is `command -> result · artefact · date` (docs/state-model.md §2f)")


# The guard is DEFINED once in MECHANISMS.md 3b item 4 and INVOKED by every skill that writes a spine
# section - /adopt included: it writes the whole spine from repo evidence, so reconciling intended against
# actual is its subject matter, not an extra. /drift-check is the ONE exemption, and the reason is that it
# OWNS the claim-to-evidence pass the guard re-uses (docs/state-model.md 2h): a pointer back to itself
# would say nothing.
GUARD_DECLARING = (STATE_DECLARING | {"adopt"}) - {"drift-check"}
GUARD_POINTER = "§Step 3b"
# How far from the phrase the pointer may sit. Every gate-closing region ALREADY says "Close the loop
# (MECHANISMS.md §Step 3b)", so searching the whole region for the pointer would pass no matter what the
# guard clause itself said - a check that cannot fail. It is read beside the phrase instead.
GUARD_POINTER_WINDOW = 160
# The clause itself runs longer than that, so the obligation it most often loses in the shortening -
# "UNVERIFIED does not block" - is read in a wider window. Both are windows rather than region-wide greps
# for the same reason: the words already occur elsewhere in some gate-closing regions.
GUARD_CLAUSE_WINDOW = 400


def check_transition_guard(files: dict[str, Path]) -> None:
    """16. A phase that writes a section reconciles intended against actual before it closes.

    docs/state-model.md 4 deferred this because a guard needs a re-runnable record to check; 131 shipped
    one, so the deferral was reopened deliberately rather than left to rot. The failure it ends: a section
    goes empty -> filled carrying an evidence line nobody has re-run since it was typed, and nothing
    notices until a human remembers to run /drift-check. A gate that only runs when you remember it is not
    a gate - so the invocation is checked, not hoped for.
    """
    for name in sorted(GUARD_DECLARING):
        text = files[name].read_text(encoding="utf-8")
        # The GATE-CLOSING REGION: Step 3b's heading through Step 3c's (or the end of the file). Not
        # Step 3b's own block - /scope and others carry a sub-section between the two and close the loop
        # after it. Reading a region rather than the whole file is what separates a skill that RUNS the
        # guard from one that merely mentions it somewhere: check 9's lesson, that a heading is not a
        # behaviour, applies to the clause that names one too.
        start = re.search(r"^#{2,4}\s*Step 3b\b", text, re.MULTILINE)
        if not start:
            fail(f"{name} writes a spine section but has no `Step 3b` block to close its gate in")
            continue
        rest = text[start.end():]
        stop = re.search(r"^#{2,4}\s*Step 3c\b", rest, re.MULTILINE)
        # the clause is read as prose: markdown wraps it mid-sentence, so lines mean nothing here
        body = " ".join(rest[: stop.start() if stop else len(rest)].split())
        hits = [m.end() for m in re.finditer(r"transition\s*\**\s*guard", body, re.IGNORECASE)]
        if not hits:
            fail(f"{name} writes a spine section but never runs the **transition guard** where it closes "
                 f"its gate (Step 3b) - "
                 f"its evidence lines would then be re-checked only when someone opts into /drift-check "
                 f"(MECHANISMS.md §Step 3b item 4, docs/state-model.md §4)")
            continue
        if not any(GUARD_POINTER in body[max(0, i - GUARD_POINTER_WINDOW):i + GUARD_POINTER_WINDOW]
                   for i in hits):
            fail(f"{name} names the transition guard but does not point at {GUARD_POINTER}, where it is "
                 f"defined once - a restated gate drifts from the definition it copied")
        # Read in the same window as the pointer, and for the same reason: the word appears elsewhere in
        # some gate-closing regions, so a region-wide grep would pass a clause that had dropped it.
        if not any("UNVERIFIED" in body[max(0, i - GUARD_CLAUSE_WINDOW):i + GUARD_CLAUSE_WINDOW]
                   for i in hits):
            fail(f"{name} runs the guard without saying that `UNVERIFIED` is a normal outcome - a guard "
                 f"read as a hard block gets skipped wherever measurement is legitimately impossible")


def check_close_the_loop(files: dict[str, Path]) -> None:
    """17. A phase that writes a section commits it and closes in plain language.

    Both rules existed and neither was executed anywhere. PRINCIPLES.md has demanded plain language since
    v1.0 while every run ended in playbook dialect, and MECHANISMS.md only ever said *suggest* a commit
    message - so three phases behaved three different ways and a real project sat at zero commits after
    two of them. That is the decide-but-never-execute failure inside the file that names it, which is why
    the obligation is checked in the gate-closing region rather than trusted to the prose that defines it.
    """
    for name in sorted(GUARD_DECLARING):
        text = files[name].read_text(encoding="utf-8")
        start = re.search(r"^#{2,4}\s*Step 3b\b", text, re.MULTILINE)
        if not start:
            continue  # check 16 already failed this file; one message per defect
        rest = text[start.end():]
        stop = re.search(r"^#{2,4}\s*Step 3c\b", rest, re.MULTILINE)
        body = " ".join(rest[: stop.start() if stop else len(rest)].split())
        for pointer, what, why in CLOSE_OBLIGATIONS:
            if pointer not in body:
                fail(f"{name} closes its gate without {what} ({pointer}) - {why}")


CLOSE_OBLIGATIONS = (
    ("§Commit the work", "offering to commit what it just wrote",
     "a phase that only names a commit message leaves its own output uncommitted"),
    ("§Plain-language close", "closing in plain language",
     "a run that ends in gates, states and verdicts has not told the user what happened or what they do next"),
)


def check_states_are_implemented(files: dict[str, Path]) -> None:
    """18. Every state docs/state-model.md defines is implemented by at least one skill.

    The `running` state existed in two live runs before it existed in the model: a section full of text
    with its gate still open, improvised well and identically, with no state, no transition, no
    downstream rule and no check. The reverse failure is the one this catches - a state defined in the
    model that no skill ever writes is a rule the product does not have, and it reads as though it does.
    """
    model = (ROOT / "docs" / "state-model.md").read_text(encoding="utf-8")
    block = model.split("### 2a.", 1)[-1].split("### 2b.", 1)[0]
    states = {m.group(1) for m in re.finditer(r"^\|\s*\*\*(\w+)\*\*\s*\|", block, re.MULTILINE)}
    states -= {"superseded"}  # a property of an entry, not a section - §2a says so explicitly
    corpus = "\n".join(p.read_text(encoding="utf-8") for p in sorted(set(files.values())))
    for state in sorted(states):
        if state not in corpus:
            fail(f"docs/state-model.md defines the `{state}` state and no skill implements it - a state "
                 f"nothing writes is a rule the product does not actually have")


def check_commit_repo_root() -> None:
    """19. §Commit the work compares the repo ROOT to the project, not merely that a repo exists.

    Shipped in #177 as "No `.git` -> offer `git init`", which passes for the wrong reason: git resolves
    upward, so an accidentally `git init`-ed home directory answers for every folder beneath it. Found on
    a real machine - an empty project under a `~` repo with 126 dirty entries, where the rule would have
    committed PRODUCT.md into the user's home directory and reported "committed on `main`", exactly what
    a correct run reports (#187). The prose is the whole guard - nothing executes it - so the thing to
    guarantee is that it keeps saying the load-bearing part.
    """
    text = (ROOT / "references" / "mechanisms.md").read_text(encoding="utf-8")
    heading = "## " + SECTION_SIGN + "Commit the work"
    if heading not in text:
        fail(f"references/mechanisms.md has no {heading!r} section")
        return
    rest = text.split(heading, 1)[1]
    nxt = re.search(r"^## ", rest, re.MULTILINE)
    body = " ".join(rest[: nxt.start() if nxt else len(rest)].split())
    for token, why in COMMIT_ROOT_OBLIGATIONS:
        if token not in body:
            fail(f"§Commit the work no longer states {token!r} - {why}")


COMMIT_ROOT_OBLIGATIONS = (
    ("git rev-parse", "without resolving the repo root the rule cannot tell THIS project's repo from a parent's"),
    ("PARENT directory", "the parent-repo case is the defect; an unnamed case is an unhandled one"),
    ("STOP. Do not commit", "detecting the wrong repo and proceeding anyway is the bug, not the fix"),
    ("repository root", "a close that names only the branch lets a commit land in `~` looking normal"),
)


def criteria_of(text: str) -> list[str]:
    """Exit criteria as whole criteria - a `- [ ]` line plus its wrapped continuation lines.

    A criterion that wraps is still one criterion; reading line-by-line would demand a citation on the
    first physical line and put the arrow mid-sentence.
    """
    if "**Exit criteria:**" not in text:
        return []
    block = text.split("**Exit criteria:**", 1)[1].split("\n## ", 1)[0]
    out: list[str] = []
    for line in block.splitlines():
        s = line.strip()
        if s.startswith("- [ ]"):
            out.append(s[5:].strip())
        elif out and s and not s.startswith("- ") and not s.startswith("<!--"):
            out[-1] += " " + s
    return out


def check_criteria_have_a_home(files: dict[str, Path]) -> None:
    """20. Every exit criterion cites the spine field that records it, and that field exists.

    /vision demanded "a single sentence vision" from the first commit while templates/PRODUCT.md had no
    field for it, Step 2 never asked and Step 3 never wrote it - three months of runs skipped it and the
    principle-gate passed them, because Step 3b walks the document it just wrote rather than the
    checklist (#188, #192). A run cannot notice a question it was never handed a box for.

    Two cheaper designs were measured and rejected. Token overlap between a criterion and its section's
    field labels flags 39 criteria that are correct today. Auto-mapping by best overlap proposes wrong
    fields - "a real request succeeded against the deployed URL" maps to `Rollback path`. So the link is
    DECLARED, not inferred: a criterion ends with an arrow and one or more backticked field labels, and
    every label must occur verbatim in the template - which is exactly what the missing one did not.

    CRITERIA_CITED is the migrated set, not the whole repo: the other 12 section-writing skills carry 87
    criteria needing a human decision each, and a wrong citation is worse than an absent one because it
    reads as verified. Tracked in #192; each skill joins the set as it is migrated.
    """
    tpl = (ROOT / "templates" / "PRODUCT.md").read_text(encoding="utf-8")
    for name in sorted(CRITERIA_CITED):
        if name not in files:
            fail(f"CRITERIA_CITED names {name!r}, which is not a skill")
            continue
        text = files[name].read_text(encoding="utf-8")
        if "**Exit criteria:**" not in text:
            fail(f"{name} is in CRITERIA_CITED but declares no exit criteria")
            continue
        for crit in criteria_of(text):
            if ARROW not in crit:
                fail(f"{name}: exit criterion cites no spine field - {crit[:70]!r} - a criterion with "
                     f"nowhere to be written is skipped silently while the gate still passes")
                continue
            cited = re.findall(r"`([^`]+)`", crit.rsplit(ARROW, 1)[1])
            if not cited:
                fail(f"{name}: exit criterion has a citation arrow but names no field - {crit[:70]!r}")
                continue
            for label in cited:
                if label not in tpl:
                    fail(f"{name}: exit criterion cites {label!r}, which templates/PRODUCT.md does not "
                         f"contain - the criterion has nowhere to be recorded")


# Skills whose exit criteria have been migrated to cite their spine field (#192). Grows one skill at a
# time; each migration is a human decision per criterion, so the set is explicit rather than inferred.
CRITERIA_CITED = {"vision", "validate", "scope", "plan", "contracts", "dev-check", "deploy",
                  "test", "eval", "ship", "learn", "drift-check"}


# A spine section whose detail lives in a companion file -> skill that owns it. The six older pairings
# (#Architecture->docs/adr, #Structure->STRUCTURE.md, #Design->DESIGN.md, #Foundation->docs/runbook.md,
# #Build log->docs/features, #Deployment->docs/deployment.md) predate the receipt and are not in this set
# yet; each joins as its skill is migrated, exactly as CRITERIA_CITED grows.
COMPANION = {"vision": "docs/vision.md", "validate": "docs/validation.md", "scope": "docs/scope.md",
             "plan": "docs/plan.md", "contracts": "docs/contracts.md", "test": "docs/tests.md",
             "eval": "docs/evaluation.md", "learn": "docs/learnings.md"}
COMPANION_OBLIGATIONS = (
    ("MECHANISMS-ON-DEMAND.md §Section is a record", "reporting the size of what it just wrote and "
     "applying the record test",
     "a spine nobody measures reached 73KB, and a spine measured against a NUMBER was trimmed instead of "
     "relocated - #Vision lost 30 bytes of answers while its companion was written in addition (#200)"),
    ("MECHANISMS-ON-DEMAND.md §Read receipt", "receipting the companions it opened",
     "a pointer nobody can prove was followed is how a phase reads the record, invents what the artefact "
     "would have said, and publishes eleven wrong issues"),
)


def check_companion_docs(files: dict[str, Path]) -> None:
    """21. A section with a companion DECLARES it, the template POINTS at it, and the phase PROVES it read it.

    Two failures with one cause. `templates/PRODUCT.md` has said "a section is a RECORD, not a container"
    since v1.38.0, and eight sections had no container to be the alternative to - so every one of them
    wrote its detail into the spine, and /vision wrote 5.1KB of reasoning into the FIRST section of a live
    run with nothing to catch it. There is NO byte cap (#200: the template's 95 required fields make one
    unreachable by construction, and a cap trims answers instead of relocating reasoning); the instrument
    is the record test - decision stays, reasoning moves. Moving that detail out is only safe if following a pointer is
    verifiable, and MECHANISMS.md Follow the pointer - the guard against exactly that - was named in 2 of
    22 skills and enforced by NO check, while claiming to be "greppable, so it is a gate, not an
    intention". Nothing grepped it. So the split and the proof ship together, and this is the grep.
    """
    tpl = (ROOT / "templates" / "PRODUCT.md").read_text(encoding="utf-8")
    for name, comp in sorted(COMPANION.items()):
        if name not in files:
            fail(f"COMPANION names {name!r}, which is not a skill")
            continue
        if comp not in tpl:
            fail(f"templates/PRODUCT.md never names {comp} - the section it belongs to points nowhere, so "
                 f"its detail has only the spine to go into, which is how it filled with reasoning")
        text = files[name].read_text(encoding="utf-8")
        if f"`{comp}`" not in text:
            fail(f"{name} writes a section that must be a RECORD but never names its companion {comp} - a "
                 f"phase with nowhere to put the reasoning puts it in the spine")
        start = re.search(r"^#{2,4}\s*Step 3b\b", text, re.MULTILINE)
        if not start:
            continue  # check 16 already failed this file; one message per defect
        rest = text[start.end():]
        stop = re.search(r"^#{2,4}\s*Step 3c\b", rest, re.MULTILINE)
        body = " ".join(rest[: stop.start() if stop else len(rest)].split())
        for pointer, what, why in COMPANION_OBLIGATIONS:
            if pointer not in body:
                fail(f"{name} closes its gate without {what} ({pointer}) - {why}")


def check_skill_count(n: int, files: dict[str, Path]) -> None:
    """15. Nobody states a skill count that disagrees with commands/.

    The GitHub repo description said "18 commands" while the README said 21 in five places. That one
    is a setting, not a file - but the number has one true source (commands/), so every place in the
    repo that quotes it is checked against that source, and the description is copied from here.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for pattern in COUNT_PATTERNS:
        for m in re.finditer(pattern, readme):
            got = int(m.group(1))
            if got != n:
                line = readme[: m.start()].count("\n") + 1
                fail(f"README.md:{line} claims {got} skills/commands, but commands/ has {n} "
                     f"({m.group(0).strip()!r})")

    vision = (ROOT / "VISION.md").read_text(encoding="utf-8")
    m = re.search(r"<!--\s*skills:(.*?)-->", vision, re.DOTALL)
    if not m:
        fail("VISION.md has no `<!-- skills: ... -->` comment to count the skill set against")
        return
    listed = re.findall(r"`/([a-z-]+)`", m.group(1))
    if sorted(listed) != sorted(files):
        fail(f"VISION.md skills comment lists {len(listed)} skills, commands/ has {n}: "
             f"{set(listed) ^ set(files)}")


# The canonical phase order /playbook walks (commands/playbook.md Step 0, one source — check 22 asserts this
# list equals it). A handoff may skip over an OPTIONAL phase: design-system runs for UI products only, and
# deploy only when the product must be reachable before /test.
CHAIN = ["vision", "validate", "scope", "plan", "architect", "structure", "design-system", "foundation",
         "contracts", "tickets", "build", "dev-check", "deploy", "test", "eval", "ship", "learn"]
OPTIONAL_PHASES = {"design-system", "deploy"}
# The phases that run real commands for most of a session, where tool output is what grows the context.
HYGIENE_DECLARING = {"foundation", "contracts", "tickets", "build"}
HYGIENE_POINTER = f"{SECTION_SIGN}Context hygiene"


def handoff_region(text: str) -> str:
    """The skill's closing text: from its handoff heading (else its last `Step N` heading) to the end."""
    heads = list(re.finditer(r"^#{2,3}\s*Step\s+\d+[a-z]?\b.*$", text, re.MULTILINE))
    if not heads:
        return ""
    named = [h for h in heads if "handoff" in h.group(0).lower()]
    return text[(named or heads)[-1].end():]


def check_handoff_chain(files: dict[str, Path]) -> None:
    """22. Every phase skill hands off to the phase that follows it in the canonical chain.

    /contracts closed with "run /build" while /playbook's order is contracts -> tickets -> build. On a
    logged test run (2026-09-13) the owner did what the skill said, /tickets never ran, and M1 reached
    /build undivided. Sixteen skills each name their own "next" and nothing compared those sixteen words
    to the one order /playbook walks - a hole in the chain that only a user following it could find.
    """
    # One source for the order: the Step 0 line in playbook.md. Keep CHAIN equal to it (deploy is drawn
    # as a branch on a later line there, so it is not part of this comparison).
    pb = files["playbook"].read_text(encoding="utf-8")
    m = re.search(r"in order:\s*(.*?)\.\s*That's the next phase", pb, re.DOTALL)
    if not m:
        fail("playbook.md Step 0 no longer states the phase order as 'in order: A -> B ... That's the next phase' "
             "- check 22 reads the canonical chain from that sentence")
    else:
        listed = []
        for raw in m.group(1).split(ARROW):
            word = re.sub(r"\(.*?\)|\*", "", raw).strip().lower()
            listed.append("design-system" if word.startswith("design") else word)
        want = [c for c in CHAIN if c != "deploy"]
        if listed != want:
            fail(f"check 22's CHAIN {want} differs from playbook.md Step 0 {listed} - the chain has one source")
    for i, name in enumerate(CHAIN[:-1]):
        if name not in files:
            continue
        allowed: list[str] = []
        for nxt in CHAIN[i + 1:]:
            allowed.append(nxt)
            if nxt not in OPTIONAL_PHASES:
                break
        region = handoff_region(files[name].read_text(encoding="utf-8"))
        if not region:
            fail(f"{name} has no handoff region (no `## Step N` heading) - check 22 cannot see what it hands off to")
            continue
        if not any(f"/{a}" in region for a in allowed):
            fail(f"{name} hands off without naming the next phase in the chain "
                 f"({' or '.join('/' + a for a in allowed)}) - a user who follows the skill skips a step the "
                 f"chain requires (contracts said 'run /build' and /tickets never ran on a live run)")


def check_context_hygiene(files: dict[str, Path]) -> None:
    """23. The long derivation phases point at the context-hygiene rule where they close their gate.

    /build has said "bulky output to files, broad searches to subagents" since #31, and on a logged test
    run /foundation (385 calls) and /contracts (326 calls) each cost ~$70-75 with ~60% of it cache
    re-reads of tool output - full test logs, whole files read back, long shell output. A sentence in one
    skill's Step 1 bound nobody; the rule now lives once in MECHANISMS-ON-DEMAND.md and each phase that
    runs commands for most of a session must point at it. Reporting and context only - the rule changes
    nothing a phase checks, writes or verifies.
    """
    ondemand = " ".join((ROOT / "references" / "mechanisms-on-demand.md").read_text(encoding="utf-8").split())
    if REREAD_RULE not in ondemand:
        fail(f"MECHANISMS-ON-DEMAND.md {HYGIENE_POINTER} never says to {REREAD_RULE!r} - two logged builds re-read "
             f"whole files they had just edited (22k and ~45k characters), carried through every later step")
    if PATCH_SCRIPT_RULE not in ondemand:
        fail(f"MECHANISMS-ON-DEMAND.md {HYGIENE_POINTER} never says to change files with the edit tool, "
             f"{PATCH_SCRIPT_RULE!r} - on a logged build, patch scripts cost 10-14% of the run: the code enters "
             f"the conversation twice, and the script broke on quoting four times")
    # The on-demand file alone did not bind: a logged 1.66.0 build never opened it and wrote 12 patch scripts.
    build_text = " ".join(files["build"].read_text(encoding="utf-8").split())
    if PATCH_SCRIPT_RULE not in build_text:
        fail(f"/build SKILL.md never says {PATCH_SCRIPT_RULE!r} where code is written - the rule only in "
             f"MECHANISMS-ON-DEMAND.md was never read: a logged build that did not open it wrote 12 patch scripts")
    for name in sorted(HYGIENE_DECLARING):
        text = files[name].read_text(encoding="utf-8")
        if HYGIENE_POINTER not in text:
            fail(f"{name} never points at MECHANISMS-ON-DEMAND.md {HYGIENE_POINTER} - a phase that runs "
                 f"commands for most of a session re-reads every byte of their output on every later call "
                 f"unless the rule is in front of it")


# The tickets skill's obligations for a backlog that never assumes one builder (#213). Each token is an
# obligation the skill's exit criteria or Step 3A must name; the board fields are checked one by one
# because a card with one of them unset is invisible on that view (case-files-build.md, the read-back).
BOARD_TOKENS = ("Delivery Board", "Status", "Owner", "Lane", "Seat", "read back")
LANE_TOKENS = ("Lanes are modules", "STRUCTURE.md", "Owner", "coordination points", "hub files")
TEMPLATE_HEADINGS = ("### 🛣️ Lane", "### 👤 Owner")


def check_lanes_and_board(files: dict[str, Path]) -> None:
    """24. /tickets groups by module lane, files every ticket on the board, and shows the list it confirms.

    On a logged test run (2026-09-13) /tickets wrote 15 vertical slices as one dependency chain with
    15 one-ticket lanes and no board - its README said "one person builds this". The owner then asked
    whether two people could take it, and they could not. The grouping the modules already offered was
    never used because the skill's only two strategies were "thin slice per milestone" and "one ticket
    per layer". This check reads the obligations, not the outcome: the skill must name module lanes,
    the four board fields and the read-back, the template must carry Lane and Owner, and Step 3A.1 must
    print the proposal it asks the user to confirm (#210: "as proposed (17)" with no list above it).
    """
    text = files["tickets"].read_text(encoding="utf-8")
    m = re.search(r"Exit criteria:\*\*(.*?)^## Step 0", text, re.MULTILINE | re.DOTALL)
    criteria = m.group(1) if m else ""
    for token in LANE_TOKENS:
        if token not in criteria:
            fail(f"tickets exit criteria never name {token!r} - a backlog that is not grouped by module "
                 f"lane assumes one builder, and the day a second person arrives it has to be re-planned")
    for token in BOARD_TOKENS:
        if token not in criteria:
            fail(f"tickets exit criteria never name {token!r} - a ticket that is not a board card with "
                 f"every field set is invisible on the lane view the team actually reads")
    m = re.search(r"^### 3A\.1\b(.*?)^### 3A\.2", text, re.MULTILINE | re.DOTALL)
    step = " ".join((m.group(1) if m else "").split())
    if not m or "print the whole proposal" not in step or "confirmed again" not in step:
        fail("tickets Step 3A.1 does not print the whole proposal before asking for a yes, or does not "
             "re-confirm a set that changed after it - a confirmation of a count is not a confirmation of a list")
    template = (ROOT / "templates" / "feature_ticket_template.md").read_text(encoding="utf-8")
    for heading in TEMPLATE_HEADINGS:
        if heading not in template:
            fail(f"templates/feature_ticket_template.md has no {heading!r} heading - the ticket form is "
                 f"where the lane and its owner are written, and the board only mirrors them")
    pub = (ROOT / "commands" / "tickets" / "references" / "publishing.md").read_text(encoding="utf-8")
    for token in ("§The Delivery Board", "project", "lowercase"):
        if token not in pub:
            fail(f"tickets/references/publishing.md never mentions {token!r} - the board procedure, its "
                 f"permission scope and the lowercase read-back keys are what make the stamping real")


# A fixed ticket count per milestone ("2-4 tickets", "3–5 slices"), in any dash. Matched wherever the
# tickets skill is described, because the cap came back through the evals and the docs as easily as
# through the skill itself.
TICKET_CAP_RE = re.compile(r"\b\d+\s*(?:[-–—]|to)\s*\d+\s+[^\d.;|]{0,40}?\b(?:tickets|slices)\b")
# The sizing rules (#247), as (token, where it must appear, what losing it means).
SIZING_TOKENS = (
    ("§Size by behaviour", "tickets Step 1", "the pointer from the rule to its mechanism"),
    ("visible behaviour", "tickets Step 1", "the size unit - one behaviour a user can see"),
    ('"and"', "tickets Step 1", 'the "and"-title rule'),
    ("never smaller than one visible behaviour", "tickets Step 1", "the floor"),
    ('"and"', "tickets Step 3A.1", 'flagging a title with "and" in the proposal the user confirms'),
    ("## §Size by behaviour", "slicing.md", "the sizing mechanism"),
    ("No count limit", "slicing.md", "rule 1 - no count cap"),
    ("fifteen minutes", "slicing.md", "rule 2 - one behaviour, one session, one PR readable in ~15 min"),
    ('The "and" test', "slicing.md", 'rule 3 - the "and" test'),
    ("No layer halves", "slicing.md", "rule 4 - no backend-only or UI-only half"),
    ("The floor", "slicing.md", "rule 5 - never smaller than one visible behaviour"),
)


def check_ticket_sizing(files: dict[str, Path]) -> None:
    """24b. /tickets sizes tickets by behaviour; no fixed count per milestone survives anywhere it is described.

    The exit criterion said every milestone becomes 2-4 tickets. On a real backlog that cap forced bundling:
    one ticket carried three behaviours (edit, delete, remove another user's entry), another carried deploy,
    a link preview and an accessibility audit - each a PR nobody could review in one sitting, each lengthening
    the chain behind it (#247). The replacement is a size, not a number: one visible behaviour, one session,
    one readable PR, an "and"-title flagged, no layer halves, and a floor so the fixed per-build overhead is
    not paid for nothing. The check fails on any count cap in the skill, its slicing reference, its evals
    and the how-it-works row, and on any of the five rules going missing.
    """
    skill = files["tickets"].read_text(encoding="utf-8")
    slicing = (ROOT / "commands" / "tickets" / "references" / "slicing.md").read_text(encoding="utf-8")
    evals = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
    tickets_cases = json.dumps([c for c in evals.get("evals", []) if c.get("skill") == "tickets"],
                               ensure_ascii=False)
    how = (ROOT / "docs" / "how-it-works.md").read_text(encoding="utf-8")
    how_lines = "\n".join(ln for ln in how.splitlines() if "/tickets" in ln)
    for where, text in (("commands/tickets/SKILL.md", skill), ("tickets/references/slicing.md", slicing),
                        ("evals/evals.json (tickets cases)", tickets_cases),
                        ("docs/how-it-works.md (/tickets lines)", how_lines)):
        m = TICKET_CAP_RE.search(" ".join(text.split()))
        if m:
            fail(f"{where} caps the ticket count ({m.group(0)!r}) - a fixed number per milestone forces "
                 f"several behaviours into one ticket; size by behaviour and let the count follow")
    step1 = re.search(r"^## Step 1\b(.*?)^## Step 2\b", skill, re.MULTILINE | re.DOTALL)
    step3a1 = re.search(r"^### 3A\.1\b(.*?)^### 3A\.2", skill, re.MULTILINE | re.DOTALL)
    regions = {"tickets Step 1": " ".join((step1.group(1) if step1 else "").split()),
               "tickets Step 3A.1": " ".join((step3a1.group(1) if step3a1 else "").split()),
               "slicing.md": " ".join(slicing.split())}
    for token, where, what in SIZING_TOKENS:
        if token not in regions[where]:
            fail(f"{where} lost {what} (expected {token!r}) - without it the backlog drifts back to "
                 f"bundled tickets that no one can review in one sitting")


# Skills whose gate-closing region composes another skill that prints its own report. The report is the
# thing most likely to be mistaken for the close, so these are the skills that must say the close comes last.
COMPOSING_REVIEWERS = {"build", "ship", "test", "eval", "dev-check"}
# Skills that run /security-review. Its instructions end the turn on its own report, so it must run where
# its report comes back as a result - a subagent - and the skill must say so where it invokes it (#212).
SECURITY_REVIEW_INVOKERS = {"build", "ship", "dev-check"}
SUBAGENT = "inside a subagent"
DEV_CHECK_FILING_TOKENS = (
    ("**File what the checkpoint finds, IN THIS RUN**", "filing its findings in the run - handed back as a list, "
     "they are filed by nobody"),
    ("never handed to the user as a list to file or a decision to make", "the ban on handing findings back"),
    ("reopens that issue", "reopening an issue closed as fixed when the finding is still in the code"),
    ("The checkpoint never edits code", "the checkpoint staying a checkpoint - it files what it finds and fixes "
     "nothing, so what it verified is what was built"),
    ("**A security finding on a PUBLIC repo is never filed publicly**", "keeping a public repo's security "
     "findings out of issues and committed files - filing one there is a disclosure"),
    ("`docs/dev-check.md` and `PRODUCT.md` included", "naming the checkpoint's own committed files as public "
     "on a public repo - the findings table it writes is one of them"),
)
CLOSE_LAST = "The close is the run's last message"


def check_close_is_last(files: dict[str, Path]) -> None:
    """25. A skill that composes a reviewer says the plain close is the run's LAST message.

    A logged test run, M1-SLICE-01 (2026-09-13): /build committed, then ran /security-review, and the review's
    report was the final message of the session - no plain close, no verdict per criterion, no cost
    line, no commit offer, and the security verdict reached no record because the Build-log row had
    been written before it ran. One session later the same skill ran the review mid-session and closed
    properly. The rule lives once in MECHANISMS.md §Plain-language close; each composing skill must
    repeat the one sentence where it closes its gate, because that is the region the agent is reading
    when the composed report comes back.
    """
    mech = (ROOT / "references" / "mechanisms.md").read_text(encoding="utf-8")
    if "LAST message" not in mech:
        fail("references/mechanisms.md §Plain-language close no longer says the close is the run's LAST "
             "message - a composed skill's report will be taken for the close again")
    for name in sorted(COMPOSING_REVIEWERS):
        text = files[name].read_text(encoding="utf-8")
        start = re.search(r"^#{2,4}\s*Step 3b\b", text, re.MULTILINE)
        if not start:
            continue  # check 16 already failed this file
        rest = text[start.end():]
        stop = re.search(r"^#{2,4}\s*Step 3c\b", rest, re.MULTILINE)
        body = " ".join(rest[: stop.start() if stop else len(rest)].split())
        if CLOSE_LAST not in body:
            fail(f"{name} composes a reviewer but its gate-closing region never says {CLOSE_LAST!r} - "
                 f"on a live run the reviewer's report became the final message and the user never got "
                 f"the plain close, the verdicts or their next steps")
    # A logged /build #8 (2026-09-14): the sentence above was present and the run still ended on the
    # /security-review report - it sits at the close, the review is invoked steps earlier, and the
    # review's own instructions end the turn. The fix acts where it is invoked.
    if SUBAGENT not in " ".join(mech.split()):
        fail(f"references/mechanisms.md §Plain-language close no longer says a reviewer that ends on its own "
             f"report runs {SUBAGENT!r}")
    for name in sorted(SECURITY_REVIEW_INVOKERS):
        body = " ".join(files[name].read_text(encoding="utf-8").split())
        spots = [m.start() for m in re.finditer(r"/security-review", body)]
        if not any(SUBAGENT in body[max(0, p - 300): p + 400] for p in spots):
            fail(f"{name} runs /security-review but never says, where it invokes it, to run it {SUBAGENT!r} - "
                 f"invoked inline its report takes over the turn and ends the run before the commit, the "
                 f"record and the close")
    # A logged /dev-check (2026-09-21) found 4 MEDIUM security findings and an issue closed as "completed"
    # whose fix never landed - and handed both to the user to file, reopen or "decide". /build files its own
    # findings since 1.63.0; the checkpoint, which reviews everything built, had no such rule.
    dev = " ".join(files["dev-check"].read_text(encoding="utf-8").split())
    for token, what in DEV_CHECK_FILING_TOKENS + FINDING_GROUP_TOKENS:
        if token not in dev:
            fail(f"dev-check lost {what} (expected {token!r})")


# The obligations that make a module folder a complete lane (#215). Each token names a rule the shape
# reference must carry, and the exit criterion that binds /structure to it.
LANE_SHAPE_TOKENS = ("complete lane", "registry line", "routes", "tests", "platform/", "frontend", "Hub files")
BUILD_SEAT_TOKENS = ("Owner", "seat", "STOP")


def check_module_is_a_lane(files: dict[str, Path]) -> None:
    """26. /structure makes a module a complete lane and names the hub files; /build gates on the seat.

    A logged test run (2026-09-12/13): /structure chose domain modules and drew them, then put every module's
    handlers in one http/ folder, every store in one platform/ folder and all the wiring in index.ts;
    the frontend was by tool throughout. /tickets then named index.ts in seven of fifteen tickets, and
    the backlog could not be split between two people however it was grouped - the folders each person
    would change were the shared ones. The rule is one registry line per module and everything else
    inside the module; the hub files are named in STRUCTURE.md so /tickets can treat
    them as shared, and check_structure.py verifies each exists. On the /build side, a real two-developer
    project's junior-ticket command refuses a ticket whose owner label is not its own - lane ownership is a gate.
    """
    shape = (ROOT / "commands" / "structure" / "references" / "choosing-the-shape.md").read_text(encoding="utf-8")
    for token in LANE_SHAPE_TOKENS:
        if token not in shape:
            fail(f"structure/references/choosing-the-shape.md never says {token!r} - a module that keeps "
                 f"its rules and sends its routes, store and tests to shared folders is by-tool where two "
                 f"people collide")
    text = files["structure"].read_text(encoding="utf-8")
    m = re.search(r"Exit criteria:\*\*(.*?)^## Step 0", text, re.MULTILINE | re.DOTALL)
    criteria = m.group(1) if m else ""
    for token in ("complete lane", "Hub files", "check_structure.py"):
        if token not in criteria:
            fail(f"structure exit criteria never name {token!r} - the rule exists in the reference but "
                 f"nothing binds the phase to it")
    tmpl = (ROOT / "templates" / "check_structure.py").read_text(encoding="utf-8")
    if "Hub files" not in tmpl:
        fail("templates/check_structure.py does not verify the Hub files section - a hub file that moved "
             "leaves /tickets pointing at nothing")
    build = files["build"].read_text(encoding="utf-8")
    m = re.search(r"^## Step 0\b(.*?)^## Step 1\b", build, re.MULTILINE | re.DOTALL)
    step0 = m.group(1) if m else ""
    for token in BUILD_SEAT_TOKENS:
        if token not in step0:
            fail(f"build Step 0 never mentions {token!r} - a ticket's lane and owner are a gate, and a "
                 f"session working another seat's lane must stop before it cuts a branch")


BATCH_POINTER = f"{SECTION_SIGN}Batch mode"
BATCH_OFFERING = {"playbook", "structure", "design-system"}


def check_batch_mode_offered(files: dict[str, Path]) -> None:
    """27. Batch mode exists as a mechanism, and the phases that may offer it do.

    docs/state-model.md §2d has said since #121 that derivation phases "may batch and end in one
    review", /structure's contract line repeats it, and nothing ever offered it: /playbook proposed
    exactly one phase and every handoff was singular (#204). A rule the playbook wrote about itself and
    never built. The mechanism lives once in MECHANISMS-ON-DEMAND.md; /playbook and the two handoffs
    that precede a legal batch must point at it, and §2d must say where the offer lives.
    """
    ondemand = (ROOT / "references" / "mechanisms-on-demand.md").read_text(encoding="utf-8")
    if not re.search(r"^##\s+§Batch mode", ondemand, re.MULTILINE):
        fail("references/mechanisms-on-demand.md has no §Batch mode section - the rule is back to living "
             "only in a table nothing executes")
    for name in sorted(BATCH_OFFERING):
        text = files[name].read_text(encoding="utf-8")
        region = text if name == "playbook" else handoff_region(text)
        if BATCH_POINTER not in region:
            fail(f"{name} never offers a batch ({BATCH_POINTER}) where one is legal - a user runs the "
                 f"derivation phases one session each because that is the only thing they are shown")
    sm = (ROOT / "docs" / "state-model.md").read_text(encoding="utf-8")
    if BATCH_POINTER not in sm:
        fail("docs/state-model.md §2d does not say where the batch offer lives - rule and mechanism will "
             "drift apart again")
    # Chain (#205): the input -> derivation neighbour of batch. Defined beside it, offered by /architect
    # at Step 0 (never the default), and named in §2d so the two terms cannot drift.
    if "Chain mode" not in ondemand:
        fail("references/mechanisms-on-demand.md §Batch mode no longer defines chain mode - /architect "
             "would offer a mode nothing specifies")
    arch = files["architect"].read_text(encoding="utf-8")
    m = re.search(r"^## Step 0\b(.*?)^## Step 1\b", arch, re.MULTILINE | re.DOTALL)
    step0 = m.group(1) if m else ""
    if "chain" not in step0.lower() or BATCH_POINTER not in step0 or "default" not in step0:
        fail("architect Step 0 does not offer the chain into /structure as an option with stop-after as the "
             "default - a chain that is never offered is a table entry, and one that is the default "
             "collapses an input gate")
    if "Chain" not in sm:
        fail("docs/state-model.md §2d does not define chain next to batch - the two terms will drift")


ADOPT_ORDER = ["/vision", "/validate", "/scope", "/playbook"]


def check_adopt_routes_in_chain_order(files: dict[str, Path]) -> None:
    """28. /adopt's handoff recommends phases in chain order and guards on the target's prerequisites.

    On a real adoption (2026-09-13) the handoff rules were "no Non-goals -> /scope" first, and non-goals
    are almost never inferable from a repo, so /scope was recommended to a project whose #Vision was
    empty; /scope's own Step 0 refused it and sent the user to /vision (#216). A handoff is a routing
    decision: it walks the chain in order and never names a phase whose Step 0 would reject the project.
    """
    region = handoff_region(files["adopt"].read_text(encoding="utf-8"))
    positions = [region.find(p) for p in ADOPT_ORDER]
    if any(pos < 0 for pos in positions):
        fail(f"adopt handoff does not name every phase it may route to ({', '.join(ADOPT_ORDER)}) - the "
             f"earliest unmet phase must be a candidate, or the user is sent past it")
    elif positions != sorted(positions):
        fail("adopt handoff lists its phases out of chain order - the first matching rule fires, so the "
             "order of the rules IS the routing, and /scope before /vision sends a user to a gate that "
             "sends them back")
    if "Step 0" not in region:
        fail("adopt handoff has no guard against recommending a phase whose own Step 0 would reject the "
             "project - a skill that will not start is not a next step")


SEARCH_BOUND_TOKENS = ("one search per open decision", "docs/architecture.md")


def check_architect_search_bound(files: dict[str, Path]) -> None:
    """29. /architect's benchmark is bounded and its searches are recorded.

    On a logged test run (2026-09-12) /architect ran 17 web searches; each result page entered the context
    once at the cache-write rate and the searches were the phase's largest cost after its own output
    (#203). The benchmark is load-bearing and stays; what changes is that it is one search per open
    decision row, and the list is written down, so a later reader can see what each search settled.
    """
    text = files["architect"].read_text(encoding="utf-8")
    m = re.search(r"^## Step 1\b(.*?)^## Step 2\b", text, re.MULTILINE | re.DOTALL)
    step1 = m.group(1) if m else ""
    for token in SEARCH_BOUND_TOKENS:
        if token not in step1:
            fail(f"architect Step 1 never says {token!r} - an unbounded benchmark is the phase's largest "
                 f"cost after its own output, and an unrecorded one settles nothing a reader can check")


# /vision's search record (#252), as (token, region, what losing it means).
VISION_SEARCH_TOKENS = (
    ("Record every search in `docs/vision.md`", "vision Step 2", "the rule that every search is written down"),
    ("query · what it settled", "vision Step 2", "the line shape - a list of queries does not say which "
     "comparable each one verified"),
    ("No count on searches", "vision Step 2", "the ruling that searches are not counted - a bound cuts the "
     "complaint search a sharpening insight comes from"),
    ("· no search —", "vision Step 2", "the line for a comparable named without a search"),
    ("Every search the market read ran is recorded in `docs/vision.md`", "vision exit criteria",
     "the exit criterion the record is held to"),
    ("named without a search", "vision exit criteria", "the exit criterion marking a comparable nobody searched"),
    ("against the search list in `docs/vision.md`", "vision Step 3b", "Step 3b checking the named comparables "
     "against the list - without it, 'not from memory' is an assertion"),
)
# A count or limit on /vision's searches, in more wordings than a copy of /architect's rule would use. A number
# beside the searches reads as a norm to the run even when it was written as evidence, so the skill and its evals
# keep none; a time cap ("searches under ten minutes") is a limit too. Excluded only where it provably is not a
# count of searches: a step, item or issue number, a `#` reference, a year, the record's own shape ("one line
# each"), a noun the word modifies ("three search results"), and a bare "search to" ("narrow the search to one
# segment"). It fails CLOSED on negation: a limit word straight after "no" passes ("no search limit", "no search
# budget"), any other negated limit ("never a search budget") is flagged - the ruling is pinned as "No count on
# searches", so a second wording of it costs a rewrite, while a negation window let "do not exceed the search
# budget" through.
SEARCH_COUNT = (r"(?:(?<!step )(?<!item )(?<!issue )(?<!#)(?!(?:19|20)\d\d\b)\d+(?:\s*(?:[-–—]|to)\s*\d+)?"
                r"|one|two|three|four|five|six|seven|eight|nine|ten|a\s+couple\s+of|a\s+few|a\s+handful\s+of)")
RECORD_LINE = r"(?:lines?|per|rows?|entry|entries|sentences?)"
NOT_A_RECORD_LINE = rf"(?!\s+{RECORD_LINE}\b)"
SEARCH_AS_MODIFIER = r"(?!\s+(?:results?|terms?|engines?|bars?|box(?:es)?|operators?|pages?|history|keywords?)\b)"
LIMIT_VERB = (r"(?:limit(?:s|ed|ing)?|cap(?:s|ped|ping)?|keep(?:s|ing)?|kept|restrict(?:s|ed|ing)?"
              r"|hold(?:s|ing)?|held)")
VISION_SEARCH_CAP_RE = re.compile(
    # "three searches", "two Google searches", "one search per comparable", "up to 100 searches"
    rf"\b{SEARCH_COUNT}(?:\s+(?!{RECORD_LINE}\b)[\w-]+)?\s+search(?:es)?\b{SEARCH_AS_MODIFIER}"
    # "searches at most 3", "keep the searches under ten minutes", "searches limited to three"
    r"|\bsearch(?:es)?\s+(?:(?:limited|capped|restricted|held|kept|bounded)\s+(?:to|at)|at(?:\s+most)?"
    rf"|max(?:imum)?(?:\s+of)?|under|below|within|up\s+to|no\s+more\s+than)\s+{SEARCH_COUNT}\b{NOT_A_RECORD_LINE}"
    # "cap searches at four", "limit the web searches to three" - never "keep the searches to one line each"
    rf"|\b{LIMIT_VERB}\s+(?:the\s+|your\s+|its\s+)?(?:[\w-]+\s+)?search(?:es)?\s+(?:to|at)\s+(?:most\s+)?"
    rf"{SEARCH_COUNT}\b{NOT_A_RECORD_LINE}"
    # "a search budget", "the benchmark is bounded" - but not "no search limit" (and not "piano search limit" either)
    r"|(?<!\bno )\bsearch(?:es)?\s+(?:budget|limit|cap|bound|quota)s?\b"
    r"|\b(?:benchmark|search(?:es)?)\s+(?:is|are)\s+(?:bounded|capped|limited)\b",
    re.IGNORECASE)


def check_vision_search_record(files: dict[str, Path]) -> None:
    """33. /vision records every search its market read ran, with no count, and Step 3b checks the named comparables
    against that list.

    A logged /vision test run wrote its three queries on one line above a table of eight comparables and ten
    source links, and nothing said which search verified which product. Step 3b's "real named products (not from
    memory)" was an assertion. #252 first proposed /architect's bound (one search per comparable). The owner's
    re-review of seven logged runs found 1-4 searches each, so a bound saves nothing, and two of the 4-search runs
    spent a query on user complaints - where a sharpening insight comes from, and exactly what a per-comparable
    bound forbids. So the record is required, and a count or limit on the searches fails the check.
    """
    text = files["vision"].read_text(encoding="utf-8")
    step2 = re.search(r"^## Step 2\b(.*?)^## Step 3\b", text, re.MULTILINE | re.DOTALL)
    step3b = re.search(r"^## Step 3b\b(.*?)^## Step 3c\b", text, re.MULTILINE | re.DOTALL)
    regions = {"vision Step 2": " ".join((step2.group(1) if step2 else "").split()),
               "vision exit criteria": " ".join(" ".join(criteria_of(text)).split()),
               "vision Step 3b": " ".join((step3b.group(1) if step3b else "").split())}
    for token, where, what in VISION_SEARCH_TOKENS:
        if token not in regions[where]:
            fail(f"{where} lost {what} (expected {token!r})")
    evals = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
    cases = json.dumps([c for c in evals.get("evals", []) if c.get("skill") == "vision"], ensure_ascii=False)
    for where, body in (("commands/vision.md", text), ("evals/evals.json (vision cases)", cases)):
        m = VISION_SEARCH_CAP_RE.search(" ".join(body.split()))
        if m:
            fail(f"{where} bounds the market read's searches ({m.group(0)!r}) - #252 declined a count: the runs "
                 f"made 1-4, and a bound cuts the complaint search a sharpening insight comes from (stating the "
                 f"ruling? it is worded 'No count on searches')")


def done(n: int = 0) -> int:
    # A failure message quotes the file it read, so it can carry any character the repo contains. On a
    # Windows console (cp1252) printing an arrow or an em-dash then raises UnicodeEncodeError and the
    # checker dies WHILE REPORTING A FAILURE - the worst possible moment, and invisible in Linux CI.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # a stream that cannot be reconfigured
        pass
    if errors:
        print("FAIL - product-playbook consistency check:")
        for e in errors:
            print(f"  x {e}")
        return 1
    print(f"OK - {n} skills consistent across commands/ + manifest + evals + VISION; structure + line budget pass.")
    return 0




# The rules that keep /build's fixed overhead down (#236, #237, #238). Each token names one rule the skill
# must carry; the live-path companion must give every check a trigger so the walk skips what cannot apply.
BUILD_OVERHEAD_TOKENS = (
    ("Read the ticket's slice", "a read limit in Step 0 - both logged builds pasted whole modules into the "
     "conversation in the first two minutes, and every later call re-read them"),
    ("whose trigger matches", "a triggered live-path walk - 17 untagged checks were weighed on every ticket"),
    ("the full suite once at the gate", "targeted test runs while iterating"),
    ("FLAKY", "the flaky-test rule - build #8 re-investigated the flake build #7 never wrote down"),
    ("Never re-run until green", "the ban on re-running a flaky test until it passes"),
    ("In Progress", "moving the board card when work starts - #7's card read Todo after it merged"),
    ("**Done**", "moving the board card when the PR merges"),
    ("citing the evidence Step 2 already captured", "Step 3b citing Step 2's evidence instead of re-running it"),
)

# When cited evidence stops counting (#255). One sentence, word for word, in /build Step 3b and in /foundation's
# `runs end-to-end` line (check 32, #251). A logged M2-SLICE-02 build cited a 13:25 audit after a 13:31 review fix
# rewrote the form it had checked - "re-run only when its files changed" left "its files" to judgement, and
# judgement skipped the audit.
RERUN_CONDITION = ("re-run a check when any code, config or test file it reads changed after its evidence "
                   "was captured; a review fix counts, a doc-only change does not")
RERUN_TOKENS = (
    (RERUN_CONDITION, "Step 3b's re-run condition, word for word"),
    ("never doc-only for that check", "a check's own input counting as a change - DESIGN.md is markdown, and "
     "/frontend-audit's verdict moves when its tokens do"),
    ("Uncommitted and scripted edits count", "counting edits no commit holds yet - that build's fix was an "
     "uncommitted script run, and a commit-to-commit comparison sees nothing"),
    ("when unsure whether anything changed or whether a change is doc-only, re-run", "failing toward the re-run - "
     "the same build edited STRUCTURE.md, which a CI check reads, after that CI ran"),
)
# /build's reviews are checks its fixes can outrun; /foundation composes no review, so these stay /build's.
# The rule as first written ("until a round changes no code, config or test file") had no end: nothing about a
# review fix is a fixed point, so on a logged test run (2026-09-20) a build coded for 47 minutes and reviewed
# for 78 - a code review and four security rounds, each over the whole diff, each followed by the whole gate -
# until the owner killed it. Two rounds, the second scoped to the fix, then stop: the close gate covers a
# round-2 fix, and a round-2 finding that would fail the DoD goes to the user.
REVIEW_RERUN_TOKENS = (
    ("The reviews are checks too", "re-reviewing a review fix - nothing reviewed that build's fix either"),
    ("over **the files round 1's fixes touched, only**", "the second round scoped to the fix - four rounds each "
     "re-read a 14-file diff to inspect a three-line fix"),
    ("**No round 3.**", "the bound on review rounds - without it a build ran four security rounds and was killed"),
    ("**STOP and tell the user**", "the escalation - a blocking round-2 finding goes to the user, never to a "
     "silent third round"),
    ("**This gate runs ONCE, after Step 5's last round**", "the gate running once - one logged build re-ran the "
     "full check, the live path and the spine update after each of five rounds"),
)
UNBOUNDED_REVIEW = "until a round changes no code, config or test file"
# The owner's ruling (2026-09-20), after stopping two builds during their reviews: what a user can SEE of a
# review is time and money going - never what it caught. One round runs; the run then says, in plain words, what
# it caught and what it has cost; a second round is the user's decision, asked with a recommendation and its
# reason, and a skipped one is recorded. A check whose value the user never sees gets switched off - and then it
# guards nothing.
REVIEW_VISIBLE_TOKENS = (
    ("**Then show the user what the reviews caught**", "making a review's value visible - the owner stopped two "
     "builds mid-review having been shown only a running reviewer and a rising cost"),
    ("**Round 2 is the user's call, never automatic.**", "the second round being asked, not assumed"),
    ("recommend YES when the fixes touched an auth/data surface", "the recommendation that keeps round 2 where "
     "it matters - on one logged build it found 15 real defects in round 1's fixes"),
    ("**A skipped round 2 is RECORDED**", "a skipped round never being silent - a bypass is recorded with its reason"),
)
# What a review finds that is not this ticket's to fix. The first live run on the bounded loop (2026-09-20,
# #301) listed five findings in its close and told the owner to file them, while its feature doc said "Filed"
# with nothing filed; and a prompt-injection gap - a line of the AI DoD - was deferred as a finding because its
# fix lived in a file the ticket had not changed. Unprompted, the same run checked whether the repository was
# public before filing security findings: a public issue is a disclosure.
REVIEW_FINDING_TOKENS = (
    ('**A finding that leaves a DoD line unmet is never "outside"**', "the DoD overriding the file test - a "
     "prompt-injection gap was deferred because its fix lived in a file the ticket had not changed"),
    ("filed IN THIS RUN", "the run filing its own findings - one listed five in its close and told the owner to "
     "file them, and its feature doc said 'Filed' with nothing filed"),
    ("**A security finding on a PUBLIC repo is never filed publicly**", "keeping a security finding out of a "
     "public issue - filing it there is a disclosure"),
)
# One issue per finding filled a logged project's board: a checkpoint filed 11 in one run, the builds 13 before
# it, and the owner saw 42 open issues. Severity decides the shape: MEDIUM+ alone, LOW and unrated grouped per run
# - every finding still on its own line, none lost. Held in /build and /dev-check alike.
FINDING_GROUP_TOKENS = (
    ("**MEDIUM or above: one issue each**", "a finding that matters keeping its own issue"),
    ("**LOW and unrated: ONE issue for the run**", "grouping the low findings - one issue each buried the ones "
     "that matter under a board the owner called exploded"),
    ("every finding on its own line with its file and what goes wrong", "grouping without losing a finding"),
)
# What a build carries (#306). Cost is steps x context, and over half a build's cost falls after its first
# review, when every step re-reads 250-350k tokens - so what is carried in early is paid for ~100 times. On a
# logged test run (2026-09-20) the Build log was 36 lines and 53,610 characters after four builds, ~13k per
# "row", and every build loaded it: each ticket cost more than the last. One build had a flake's cause in one
# traceback and ran the suite ~10 more times to characterise it; its reviewer was killed by a usage limit and
# the skill had no rule for that. Nothing here changes what a build checks - only what it carries.
STEP3C_HOME = "**Step 3c's result goes in the feature doc**"
BUILD_WEIGHT_TOKENS = (
    ("ONE table row", "the Build-log row being one line - rows of ~13k characters made a 53k log every build read"),
    ("never load the log", "appending without reading the log back - a log every build reads makes each ticket "
     "cost more than the last"),
    ("`#Build log` holds table rows and nothing else", "the log holding rows only - a 1.67.0 build kept its row to "
     "one line and still wrote a 1,600-character Step 3c paragraph under the table, copying the 15 the older "
     "builds had left there; 'never in the row' did not forbid it"),
    ("**Attribution is one traceback, not an investigation**", "the bound on attributing a flake - one build ran "
     "the suite ~10 more times after the traceback had already named a file it never changed"),
    ("**A review that never returns has found nothing**", "the dead-reviewer rule - a reviewer killed by a usage "
     "limit left the run with no instruction"),
    ("never into an issue or a committed file", "a public repo's security finding staying out of committed files "
     "too - the spine of a public repo is public"),
)
# The companions a build opens on demand must leave a trace. Two logged builds (2026-09-20) never opened
# feature-archetypes.md or live-path-checks.md - no tool call even named them - and one of the two was a gate
# and an AI feature, exactly the first file's trigger; the two builds before them had opened both. An owner
# ruling (#257) already says every trigger is read on every run. A cluster applied from memory is a cluster not
# applied, and nothing showed the difference.
BUILD_GUIDE_TOKENS = (
    ("**Name the archetype in it**", "the DoD naming the feature's archetype - a gate feature was built without its "
     "cluster ever being opened, and nothing showed it"),
    ("Open the file on EVERY build", "the live-path triggers being read on every build - a trigger nobody read "
     "cannot match (owner ruling, #257)"),
    ("Live-path checks walked", "the feature doc listing the live-path checks that matched - the trace that "
     "makes a skipped companion visible"),
)
PATCH_SCRIPT_RULE = "not with a patch script"
# 1.63.0 sent a public repo's security finding to the Step 3c note - which lives in PRODUCT.md, a committed file.
PUBLIC_NOTE_LEAK = "record it in the Step 3c note and put it to the user"
REREAD_RULE = "read back the lines you changed, never the file"
# Scoping a re-run to a check's own inputs (#298) may never cost coverage: /build carries both guards.
GATE_SCOPE_TOKENS = (
    ("**Scope by what a check reads**", "the scoping rule itself - without it the two guards below guard "
     "nothing, and a run is back to re-running the whole gate for any change"),
    ("when you cannot name the files a check reads, re-run it", "the fail-toward-re-run guard on scoping - "
     "a guessed-narrow input set is exactly how a check gets outrun (#255)"),
    ("the whole gate runs once more at the close", "the close-gate safety net - scoping may remove repetition "
     "inside the loop, never coverage of the committed tree"),
)

LOOSE_RERUN = "only when its files changed"


def check_build_loop_overhead(files: dict[str, Path]) -> None:
    """30. /build carries the rules that cut its fixed overhead, and every live-path check has a trigger.

    Logged /build #7 and #8 (2026-09-14): #8 needed half the code of #7 and took nearly the same working
    time (35 vs 42 min). The logs showed the overhead, not the ticket: whole modules pasted into the
    conversation up front, a flaky test re-investigated because the previous build never recorded it,
    full suites on every iteration, 17 live-path checks with no triggers, Step 3b asking for evidence
    Step 2 had already produced - and a board card still at Todo after the ticket merged.
    """
    text = " ".join(files["build"].read_text(encoding="utf-8").split())
    for token, what in (BUILD_OVERHEAD_TOKENS + RERUN_TOKENS + REVIEW_RERUN_TOKENS + REVIEW_FINDING_TOKENS
                        + REVIEW_VISIBLE_TOKENS + BUILD_GUIDE_TOKENS + BUILD_WEIGHT_TOKENS + GATE_SCOPE_TOKENS
                        + FINDING_GROUP_TOKENS):
        if token not in text:
            fail(f"build lost {what} (expected {token!r})")
    # Step 3c said what to check but never where its result goes, so a run followed the log's old paragraphs.
    step3c = re.search(r"## Step 3c\b(.*?)(?=\n## |\Z)", files["build"].read_text(encoding="utf-8"), re.S)
    if not step3c or STEP3C_HOME not in " ".join(step3c.group(1).split()):
        fail(f"/build's Step 3c section never says {STEP3C_HOME!r} - it named what to check and not where the "
             f"result goes, and a logged build wrote it as a paragraph in #Build log")
    for p in sorted((ROOT / "commands").rglob("*.md")):
        flat_p = " ".join(p.read_text(encoding="utf-8").split())
        if LOOSE_RERUN in flat_p:
            fail(f"{p.relative_to(ROOT).as_posix()} says re-run {LOOSE_RERUN!r} - which files is a judgement "
                 f"call; name the condition instead: {RERUN_CONDITION!r}")
        if PUBLIC_NOTE_LEAK in flat_p:
            fail(f"{p.relative_to(ROOT).as_posix()} sends a public repo's security finding to the Step 3c note - "
                 f"that note is in PRODUCT.md, a committed file, so it is published with the repo")
        if UNBOUNDED_REVIEW in flat_p:
            fail(f"{p.relative_to(ROOT).as_posix()} re-reviews {UNBOUNDED_REVIEW!r} - a loop with no end; "
                 f"/build Step 5 bounds it at two rounds, the second scoped to the fix")
    lp = (ROOT / "commands" / "build" / "references" / "live-path-checks.md").read_text(encoding="utf-8")
    untagged = [ln[:60] for ln in lp.splitlines() if ln.startswith("- **")]
    if untagged:
        fail(f"live-path-checks.md has {len(untagged)} check(s) with no *[always]* / *[when ...]* trigger - "
             f"/build walks the checks whose trigger matches, so an untagged one is weighed on every ticket "
             f"or silently skipped: {untagged[0]!r}")


AUDIT_ENGINE = ROOT / "commands" / "frontend-audit" / "audit.py"
AUDIT_ENGINE_PATH = '"${CLAUDE_PLUGIN_ROOT}/commands/frontend-audit/audit.py"'
# Every skill that RUNS the audit names the installed engine and forbids the cache search.
AUDIT_RUNNERS = ("frontend-audit", "design-system", "build", "new-component", "foundation")
# A runnable audit line that names neither the installed engine, a placeholder for it, nor the project copy.
AUDIT_BARE_RUN = re.compile(r'python3?\s+"?(?!\$\{CLAUDE_PLUGIN_ROOT\}|<engine>|<tooling>)[^\s"`]*audit\.py')
FOUNDATION_AUDIT_TOKENS = (
    ("the frontend audit runs in the commit hooks AND CI", "the exit criterion wiring the audit into hooks + CI"),
    ("plant a raw hex colour", "Step 3b's proof that the audit gate goes red"),
)
SKELETON_AUDIT_TOKENS = (
    ("<tooling>/frontend-audit/audit.py", "where the project copy lives - the installed engine finds it by that ending"),
    ("**Commit it**", "committing the copy - a clean clone has no plugin"),
    ("never only the staged files", "auditing the whole UI - Law 14b resolves tokens across files"),
    ("a WARN prints and passes", "the ERROR-blocks / WARN-reports tiering"),
)


def check_audit_engine_resolution(files: dict[str, Path]) -> None:
    """31a. The audit runs the INSTALLED engine, and /foundation wires a project copy into hooks + CI (#256).

    A logged build, M2-SLICE-02 (2026-09-14, plugin 1.46.0 installed) looked for the script with
    `ls -d ~/.claude/plugins/cache/*/product-playbook/*/commands/frontend-audit/audit.py | tail -1`. The cache
    keeps every version, and as text 1.9.0 sorts after 1.48.0 - so the "frontend-audit clean" criterion was met
    by an engine with eight law checks where the installed one has thirteen. The skills had said
    `python commands/frontend-audit/audit.py`, a path that exists only inside this repo, so every run in a real
    project had to go searching. And the audit ran only when /build remembered it: /foundation's auto-layer
    wired lint, secret-scan and CVE scans into the hooks and CI, and never the audit.
    """
    for p in sorted((ROOT / "commands").rglob("*.md")):
        text = p.read_text(encoding="utf-8")
        rel = p.relative_to(ROOT).as_posix()
        m = AUDIT_BARE_RUN.search(text)
        if m:
            fail(f"{rel} runs the audit as {m.group(0)!r} - name the installed engine {AUDIT_ENGINE_PATH} "
                 f"(or the project copy); a path only this repo has sends a real run searching the plugin cache")
        if "plugins/cache" in text:
            fail(f"{rel} names the plugin cache path - it keeps every old version, and a text sort picks 1.9.0 "
                 f"over 1.48.0; the installed engine is {AUDIT_ENGINE_PATH}")
    for name in AUDIT_RUNNERS:
        flat = " ".join(files[name].read_text(encoding="utf-8").split())
        if AUDIT_ENGINE_PATH not in flat:
            fail(f"{name} runs the audit without naming the installed engine {AUDIT_ENGINE_PATH}")
        if "never search the plugin cache" not in flat.lower():
            fail(f"{name} never says 'never search the plugin cache' - that search is how a build ran 1.9.0")
    fa = " ".join(files["frontend-audit"].read_text(encoding="utf-8").split())
    for token, what in (("## Which engine runs", "the one resolution rule the other skills point at"),
                        ("engine copy:", "telling the user when the project copy differs from the engine"),
                        ("OLDER", "saying when the project copy is older than the installed engine")):
        if token not in fa:
            fail(f"frontend-audit lost {what} (expected {token!r})")
    found = " ".join(files["foundation"].read_text(encoding="utf-8").split())
    for token, what in FOUNDATION_AUDIT_TOKENS:
        if token not in found:
            fail(f"foundation lost {what} (expected {token!r}) - a gate you must remember is not a gate")
    steps = " ".join((ROOT / "commands" / "foundation" / "references" / "skeleton-steps.md")
                     .read_text(encoding="utf-8").split())
    for token, what in SKELETON_AUDIT_TOKENS:
        if token not in steps:
            fail(f"foundation skeleton-steps.md lost {what} (expected {token!r})")


def check_audit_engine_behaviour() -> None:
    """31b. The engine itself: ERROR blocks, WARN passes, and it names an older project copy by NUMBER.

    Exercised, not read: a scratch git project runs the real engine the way a hook, CI and a skill would.
    The older copy is 1.9.0 on purpose - the exact version a text sort picked over 1.48.0.
    """
    import shutil
    import subprocess
    import tempfile

    if shutil.which("git") is None:
        fail("check 31 needs git on PATH to exercise the audit engine's project-copy check")
        return
    engine = AUDIT_ENGINE.read_text(encoding="utf-8")
    m = re.search(r'^ENGINE_VERSION = "([^"]*)"', engine, re.MULTILINE)
    if not m:
        fail("audit.py has no ENGINE_VERSION line - a project copy cannot say which checks it carries")
        return
    current = m.group(1)

    def as_tuple(v: str) -> tuple[int, ...]:
        return tuple(int(n) for n in re.findall(r"\d+", v))

    older = "1.9.0" if as_tuple(current) > (1, 9, 0) else "0.0.1"
    # A non-ASCII folder on purpose: git prints UTF-8, and a Windows console decoding it as cp1252 garbles
    # the path, so a copy stops recognising itself.
    with tempfile.TemporaryDirectory(prefix="audit-José-") as tmp:
        t = Path(tmp)

        def run(script: Path, *targets: str) -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, str(script), *targets], cwd=tmp, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", timeout=120)

        def put_copy(version: str, extra: str) -> Path:
            dest = t / "scripts" / "frontend-audit" / "audit.py"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(engine.replace(f'ENGINE_VERSION = "{current}"', f'ENGINE_VERSION = "{version}"')
                            + extra, encoding="utf-8")
            subprocess.run(["git", "-C", tmp, "add", "-A"], check=True, capture_output=True)
            return dest

        subprocess.run(["git", "init", "-q", tmp], check=True, capture_output=True)
        (t / "ui").mkdir()
        (t / "ui" / "Button.tsx").write_text('<button className="btn">Go</button>\n', encoding="utf-8")
        css = t / "ui" / "button.css"
        css.write_text(".btn { color: var(--primary); }\n:root { --primary: oklch(0.2 0 0); }\n", encoding="utf-8")

        r = run(AUDIT_ENGINE, "ui")
        if r.returncode != 0 or " 0 error" not in r.stdout or "0 warn" in r.stdout:
            fail(f"audit engine: a WARN-only UI must exit 0 with warnings reported - got exit {r.returncode}")
        if "none committed" not in r.stdout:
            fail("audit engine: a project with no committed copy is not told its hooks and CI skip the audit")
        if f"engine {current}" not in r.stdout.splitlines()[0]:
            fail("audit engine: the scorecard's first line does not name the engine version")

        css.write_text(css.read_text(encoding="utf-8") + ".btn-danger { color: #ff0000; }\n", encoding="utf-8")
        r = run(AUDIT_ENGINE, "ui")
        if r.returncode == 0:
            fail("audit engine: a planted raw hex colour (ERROR) exits 0 - a hook or CI would let it through")

        # The copy is compared as parsed code, so a difference must be CODE: a comment is not a check.
        cases = (
            (older, "\nAN_OLDER_ENGINE = 1\n", f"is {older}, OLDER than this engine {current}"),
            ("999.0.0", "\nA_NEWER_ENGINE = 1\n", "NEWER than this engine"),
            (current, "\nEDITED_IN_PLACE = 1\n", "edited in place"),
            ("0.0.1", "", "has the same checks as this engine"),
            (older, "\n# only a comment added\n", "has the same checks as this engine"),
        )
        for version, extra, expected in cases:
            put_copy(version, extra)
            r = run(AUDIT_ENGINE, "ui")
            if expected not in r.stdout:
                fail(f"audit engine: a project copy at {version!r} with {extra.strip()!r} should report "
                     f"{expected!r} - it did not")

        # A project's formatter rewrites its committed copy - one import per line, sorted, blank lines added.
        # Same checks, so it must not be called OLDER: a logged build was told to refresh a copy that
        # differed from the installed engine in its version line and its formatting only.
        dest = put_copy(older, "")
        text = dest.read_text(encoding="utf-8")
        imp = re.search(r"^import (\w+(?:, \w+)+)\n", text, re.MULTILINE)
        if not imp:
            fail("check 31: audit.py has no one-line multi-import left to reformat - update this reformat case")
        else:
            split = "".join(f"import {n}\n" for n in sorted(imp.group(1).split(", ")))
            dest.write_text(text.replace(imp.group(0), "\n" + split + "\n", 1).replace("\n", "\r\n"),
                            encoding="utf-8", newline="")
            subprocess.run(["git", "-C", tmp, "add", "-A"], check=True, capture_output=True)
            r = run(AUDIT_ENGINE, "ui")
            if "has the same checks as this engine" not in r.stdout:
                fail("audit engine: a copy the project's formatter reformatted (same checks, split imports, "
                     "CRLF) is reported as different - every release would tell the user to refresh it")

        copy = put_copy(current, "")
        r = run(copy, "ui")
        if r.returncode == 0 or "engine copy:" in r.stdout:
            fail("audit engine: the project copy (as a hook/CI runs it) must fail on the planted ERROR "
                 "and must not report on itself")

        # A team copy install (`install.sh --project`) COMMITS the installed engine under .claude/commands/.
        # It matches the copy's path ending too, and must still judge the project's copy, not go quiet.
        skill_engine = t / ".claude" / "commands" / "frontend-audit" / "audit.py"
        skill_engine.parent.mkdir(parents=True, exist_ok=True)
        skill_engine.write_text(engine, encoding="utf-8")
        put_copy(older, "\nAN_OLDER_ENGINE = 1\n")
        r = run(skill_engine, "ui")
        if f"is {older}, OLDER" not in r.stdout:
            fail("audit engine: an engine committed by a project-level copy install (.claude/commands/) took "
                 "itself for the project copy and never reported the older copy hooks and CI run")


# Step 2 of /foundation, before its list reaches item 2: the proof that item 1's skeleton boots.
FOUNDATION_BOOT_PROOF = (
    ("Item 1 ends by proving it boots", "the boot proof at the end of item 1"),
    ("hit the health path", "hitting the health path, not only starting the process"),
    ("plain-language line", "telling the user in plain words that the app runs"),
    ("how to see it", "telling the user how to see it for themselves"),
    ("stop whatever you started", "stopping the process the proof started"),
    ("A line, not a pause", "keeping a batched run moving - the proof prints, it never asks"),
    ("fix it before item 2", "a failed boot being fixed before seven items land on it"),
)
# Step 3b's `runs end-to-end` line, beside RERUN_TOKENS.
FOUNDATION_BOOT_CITE = (
    ("(this line only)", "keeping the citation to this one line - the guard proofs are new work, not repeats"),
    ("The item-1 boot never qualifies", "ruling out the item-1 boot - Step 2's items 3-8 change the boot path"),
    ("a CI health check on the final tree", "a CI run counting only when it hit the health path, on the final tree"),
)
# Step 3b's guard proofs: #251 applied cite-don't-re-run to the boot line alone, and these always run.
FOUNDATION_GUARD_PROOFS = (
    ("actually log in with the seeded account", "the login proof - a health path is not a usable app"),
    ("trigger it with a missing secret", "the fail-closed proof"),
    ("point it at the dev datastore on purpose", "the test-isolation proof"),
    ("copy `.env.example` to `.env` **unedited**", "the placeholder replay"),
)


def check_foundation_boot_evidence(files: dict[str, Path]) -> None:
    """32. /foundation proves the boot at the end of Step 2 item 1, and Step 3b cites a boot only under /build's condition.

    A logged /foundation run (2026-09-13, 229 tool calls): item 1 already produced an app with a health path, and the
    first boot came at call 133, 22 minutes in, with most of the skeleton on top of it. And an earlier boot does
    not vouch for a later one: at 08:17 the container boot failed where the 08:12 local boot had passed, and the
    run edited the boot entry before it came up. #251 moved the proof to item 1 and let 3b's `runs end-to-end`
    line cite a boot only under /build's RERUN_CONDITION, word for word - never the item-1 boot, and never for a
    guard proof.
    """
    text = files["foundation"].read_text(encoding="utf-8")
    step2 = re.search(r"^## Step 2\b(.*?)^2\. ", text, re.MULTILINE | re.DOTALL)
    region = " ".join(step2.group(1).split()) if step2 else ""
    for token, what in FOUNDATION_BOOT_PROOF:
        if token not in region:
            fail(f"foundation Step 2 lost {what} (expected {token!r} before item 2) - the app runs after item 1, "
                 f"and a boot first shown at the end of the phase hides a broken one under seven steps")
    step3b = re.search(r"^## Step 3b\b(.*?)^## Step 3c\b", text, re.MULTILINE | re.DOTALL)
    body = step3b.group(1) if step3b else ""
    line = re.search(r"^- runs end-to-end\b.*(?:\n[ \t]+\S.*)*", body, re.MULTILINE)
    if not line:
        fail("foundation Step 3b lost its `- runs end-to-end` line")
        return
    boot = " ".join(line.group(0).split())
    for token, what in [(t, f"/build's clause on {w}") for t, w in RERUN_TOKENS] + list(FOUNDATION_BOOT_CITE):
        if token not in boot:
            fail(f"foundation Step 3b's runs end-to-end line lost {what} (expected {token!r})")
    flat = " ".join(text.split())
    if flat.count(RERUN_CONDITION) != 1:
        fail(f"foundation carries the re-run condition {flat.count(RERUN_CONDITION)} times - once, on the runs "
             f"end-to-end line; anywhere else it lets a guard proof cite old evidence")
    flat3b = " ".join(body.split())
    for token, what in FOUNDATION_GUARD_PROOFS:
        if token not in flat3b:
            fail(f"foundation Step 3b lost {what} (expected {token!r}) - a guard is proven by making it fire")


# Check 34 (#270). The names live outside the repo, or the check would break the rule it holds.
PRIVATE_NAMES_ENV = "PLAYBOOK_PRIVATE_NAMES"             # comma-separated; CI reads the repository secret of this name
PRIVATE_NAMES_REQUIRED_ENV = "PLAYBOOK_PRIVATE_NAMES_REQUIRED"  # "true"/"false"; unset means true in CI, false locally


def repo_files() -> list[str]:
    """Every file git would commit: tracked, plus untracked files not ignored, so a new file is checked before `git add`."""
    import subprocess
    out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                         cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
    return sorted({p for p in out.split("\0") if p})


def check_no_private_names() -> None:
    """34. No private project is named anywhere in the playbook - not in a file, not in a file's path (#270).

    The playbook ships to people building every kind of product. Case files, check docstrings, rule examples,
    evals, a case study and CHANGELOG history had named the maintainer's own test projects and tools in 79
    places: context no user can act on, and a general rule that reads as tuned to one project. Evidence is
    written as "a logged test run" and examples are invented.

    The names are not stored here. They come from PRIVATE_NAMES_ENV and match case-insensitively at the start
    of a word, so a plural or a possessive is caught and a name glued after other letters is not. A space in a
    name matches any whitespace, so a two-word name the prose wraps across a line break is caught; a hyphenated
    and a spaced spelling are still two entries. With no names it would pass every file, so it FAILS wherever
    names are required - in CI by default - and a local run says it skipped. CI marks names not required only for a
    fork's pull request, which GitHub gives no secrets; the push to master after the merge runs it with them. A hit
    is reported by path, line and the name's position in the list, so the check never prints the list itself.
    """
    names = [n.strip() for n in os.environ.get(PRIVATE_NAMES_ENV, "").split(",") if n.strip()]
    if not names:
        default = "true" if os.environ.get("CI") else "false"
        if os.environ.get(PRIVATE_NAMES_REQUIRED_ENV, default).strip().lower() != "false":
            fail(f"check 34: {PRIVATE_NAMES_ENV} is empty where it is required - set the repository secret of that "
                 f"name; a private-name check with no names passes every file")
        else:
            print(f"note: check 34 skipped - set {PRIVATE_NAMES_ENV} (comma-separated) to check that no private "
                  f"project is named")
        return
    patterns = [(i, re.compile(r"(?<![A-Za-z0-9])" + r"\s+".join(map(re.escape, n.split())), re.IGNORECASE))
                for i, n in enumerate(names, 1)]
    for rel in repo_files():
        where = [(f"{rel} (path)", i) for i, p in patterns if p.search(rel)]
        try:
            text = (ROOT / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):  # deleted since the listing, or binary: no text to name anything in
            text = ""
        # the whole file, not line by line, so a wrapped name still matches; each hit reports the line it starts on
        hits = {(text.count("\n", 0, m.start()) + 1, i) for i, p in patterns for m in p.finditer(text)}
        where += [(f"{rel}:{n}", i) for n, i in sorted(hits)]
        for loc, i in where:
            fail(f"{loc} names private project #{i} of {PRIVATE_NAMES_ENV} - write \"a logged test run\" for "
                 f"evidence and an invented example for a rule")


# Check 35 (#259). Every phase /playbook can offer - /adopt for an existing codebase, then the chain - has a row.
SITTING_SECTION = re.compile(r"^## Sitting lengths\b.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)
SITTING_PHASES = ["adopt"] + CHAIN
SITTING_ROW = re.compile(r"^\|\s*`/([a-z-]+)`\s*\|([^|\n]*)\|([^|\n]*)\|([^|\n]*)\|\s*$", re.MULTILINE)
SITTING_FIGURE = re.compile(r"\b\d+(?:\s*[–-]\s*\d+)?\s*(?:min|minutes?|h|hours?)\b", re.IGNORECASE)
SITTING_RANGE = re.compile(r"\d\s*[–-]\s*\d+\s*(?:min|minutes?|h|hours?)\b", re.IGNORECASE)
SITTING_VERSIONS = re.compile(r"(\d+\.\d+\.\d+)(?:\s*[–-]\s*(\d+\.\d+\.\d+))?")
NOT_MEASURED = "not measured yet"
MONEY = re.compile(r"[$€£]\s*\d|\d\s*(?:USD|EUR|GBP)\b|\b(?:dollars?|euros?)\b", re.IGNORECASE)
SITTING_OFFER = (("§Sitting lengths", "the pointer to the one table the figures live in"),
                 ("room left on your plan", "the warning to start with room left on the plan"),
                 ("loses review steps", "why the warning matters - a cut-off run loses review steps"),
                 ("never estimated", "what to say when a phase has no measured run - that, never an estimate"),
                 ("added up", "the batch's sitting, its phases' rows added up"))
SESSION_COST_POINTER = '"${CLAUDE_PLUGIN_ROOT}/tools/session_cost.py"'


def version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def check_sitting_lengths(files: dict[str, Path]) -> None:
    """35. /playbook's offers say how long a sitting is, from one measured table, and warn to start with room left.

    The routing entry point offered /foundation + /contracts + /tickets as a batch because it was legal, and said
    nothing about length: about two hours of agent work on a logged test run. A usage limit that cuts a run off
    mid-review loses review steps - on one logged /build it struck inside the review, and four of the seven review
    angles never ran. So every offer quotes a row and carries the warning, the figures live in one
    section so a release updates one row, each is labelled with the version it was measured on, and no row may
    hold a price or a range invented from one run.
    """
    text = files["playbook"].read_text(encoding="utf-8")
    m = SITTING_SECTION.search(text)
    if not m:
        fail("playbook.md has no `## Sitting lengths` section - an offer that states a sitting has nowhere to "
             "read it from, and figures scattered through the prose drift from each other")
        return
    section = m.group(0)
    rows: dict[str, tuple[str, ...]] = {}
    for row in SITTING_ROW.finditer(section):
        if row.group(1) in rows:
            fail(f"playbook.md §Sitting lengths lists /{row.group(1)} twice - one phase, one row")
        rows[row.group(1)] = tuple(cell.strip() for cell in row.group(2, 3, 4))
    for extra in sorted(set(rows) - set(SITTING_PHASES)):
        fail(f"playbook.md §Sitting lengths has a row for /{extra}, which /playbook never offers as a phase")
    released = released_version()
    for phase in SITTING_PHASES:
        if phase not in rows:
            fail(f"playbook.md §Sitting lengths has no row for /{phase} - its offer would state no sitting, or an "
                 f"invented one; a phase with no measured run gets a `{NOT_MEASURED}` row")
            continue
        figure, measured, runs = rows[phase]
        if figure == NOT_MEASURED:
            if SITTING_VERSIONS.search(measured) or runs not in ("0", "—", "-"):
                fail(f"/{phase} reads `{NOT_MEASURED}` but names a version or a run count - a row is measured or it is not")
            continue
        if not SITTING_FIGURE.search(figure):
            fail(f"/{phase}'s sitting {figure!r} states no minutes or hours - give the measured figure or "
                 f"`{NOT_MEASURED}`")
        label = SITTING_VERSIONS.fullmatch(measured)
        if not label:
            fail(f"/{phase}'s sitting is labelled {measured!r}, not with the playbook version(s) it was measured on - "
                 f"a figure from an older version reads as current")
        else:
            versions = [v for v in label.groups() if v]
            if released and any(version_key(v) > version_key(released) for v in versions):
                fail(f"/{phase}'s sitting is labelled {measured!r}, newer than the released {released} - no run "
                     f"was measured on it")
            if len(versions) == 2 and version_key(versions[0]) >= version_key(versions[1]):
                fail(f"/{phase}'s version range {measured!r} does not run oldest to newest")
        if not runs.isdigit() or int(runs) < 1:
            fail(f"/{phase}'s sitting gives {runs!r} runs - a measured figure names how many runs it rests on")
        elif runs == "1" and SITTING_RANGE.search(figure):
            fail(f"/{phase}'s sitting {figure!r} is a range from one run - one run gives one figure")
    money = MONEY.search(text)
    if money:
        fail(f"playbook.md states a price ({money.group(0)!r}) - what a run costs depends on the user's plan, "
             f"and a subscription meets a usage limit, not a bill")
    stray = SITTING_FIGURE.search(text[:m.start()] + text[m.end():])
    if stray:
        fail(f"playbook.md states a sitting figure outside §Sitting lengths ({stray.group(0)!r}) - the figures "
             f"live in one place, or a release updates one copy and the other goes stale")
    step2 = re.search(r"^## Step 2\b(.*?)^2\. ", text, re.MULTILINE | re.DOTALL)
    offer = " ".join(step2.group(1).split()) if step2 else ""
    for token, what in SITTING_OFFER:
        if token not in offer:
            fail(f"playbook.md Step 2 item 1 (the phase and batch offers) lost {what} (expected {token!r})")
    if SESSION_COST_POINTER not in section or not (ROOT / "tools" / "session_cost.py").is_file():
        fail(f"playbook.md §Sitting lengths does not point at {SESSION_COST_POINTER} - a user cannot measure a run "
             f"of their own against the table")
    check_session_cost_working_time()


def check_session_cost_working_time() -> None:
    """35, behaviour. tools/session_cost.py's agent working time leaves out every wait that ended in the user's
    input - a typed reply, an answered question card or an approved plan - and keeps the agent's own waits, and
    its wall clock ends at the newest row, so the figure a user measures means what §Sitting lengths means."""
    import importlib.util
    import tempfile
    spec = importlib.util.spec_from_file_location("session_cost", ROOT / "tools" / "session_cost.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    at = lambda hhmm: f"2026-01-01T{hhmm}:00.000Z"  # noqa: E731
    rows = [
        {"type": "user", "timestamp": at("10:00"), "message": {"content": "<command-name>/x</command-name>"}},
        {"type": "assistant", "timestamp": at("10:05"), "message": {"id": "m1", "content": [
            {"type": "tool_use", "id": "q1", "name": "AskUserQuestion", "input": {}}]}},
        # the user answers the card 20 minutes later: a wait for the user
        {"type": "user", "timestamp": at("10:25"), "message": {"content": [
            {"type": "tool_result", "tool_use_id": "q1", "content": "answered"}]}},
        {"type": "assistant", "timestamp": at("10:30"), "message": {"id": "m2", "content": [
            {"type": "tool_use", "id": "b1", "name": "Bash", "input": {}}]}},
        {"type": "user", "timestamp": at("10:31"), "message": {"content": [
            {"type": "tool_result", "tool_use_id": "b1", "content": "ok"}]}},
        # a meta row the harness injects is neither the user's input nor the end of a wait
        {"type": "user", "isMeta": True, "timestamp": at("10:33"), "message": {"content": "meta"}},
        # a background job reports 9 minutes later: the agent's own wait, so it is working time
        {"type": "user", "timestamp": at("10:40"), "message": {"content": "<task-notification>done</task-notification>"}},
        {"type": "assistant", "timestamp": at("10:41"), "message": {"id": "m3", "content": [{"type": "text", "text": "x"}]}},
        {"type": "assistant", "timestamp": at("10:35"), "message": {"id": "m3", "content": [{"type": "text", "text": "x"}]}},
        {"type": "user", "isMeta": True, "timestamp": at("10:50"), "message": {"content": "meta"}},
        {"type": "attachment", "timestamp": at("10:55")},
        # the user types 19 minutes after the agent's last message; neither row above shortens that wait
        {"type": "user", "timestamp": at("11:00"), "message": {"content": "ok"}},
        {"type": "assistant", "timestamp": at("11:02"), "message": {"id": "m4", "content": [
            {"type": "tool_use", "id": "p1", "name": "ExitPlanMode", "input": {}}]}},
        # the user approves the plan 8 minutes later: a wait for the user
        {"type": "user", "timestamp": at("11:10"), "message": {"content": [
            {"type": "tool_result", "tool_use_id": "p1", "content": "approved"}]}},
        {"type": "assistant", "timestamp": at("11:12"), "message": {"id": "m5", "content": [{"type": "text", "text": "y"}]}},
        # the file's last row was logged out of time order: the wall clock still ends at 11:12
        {"type": "assistant", "timestamp": at("11:11"), "message": {"id": "m5", "content": [{"type": "text", "text": "y"}]}},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "session.jsonl"
        log.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        got = module.measure(log)
    if (got.get("minutes"), got.get("working"), got.get("questions")) != (72.0, 25.0, 1):
        fail(f"tools/session_cost.py measured wall {got.get('minutes')} / agent working {got.get('working')} / "
             f"questions {got.get('questions')} on the fixture, not 72.0 / 25.0 / 1 - the wall clock ends at the "
             f"newest row, and the working time leaves out waits for the user's reply, card answer or plan "
             f"approval while keeping the agent's own waits")


# Check 36 (#249). The epic layer, the plan file and the lane flow graph.
TICKETS_REFS = ROOT / "commands" / "tickets" / "references"
# Split so that this line is not itself a mention of the file the check looks for.
OLD_PLAN_FILE = "docs/issues/" + "README.md"
PLAN_FILE_NAME = "TICKETS.md"
# History keeps the name a past run used; a line of the migration rule names the file only to say it is gone.
OLD_PLAN_HISTORY = re.compile(r"^(?:CHANGELOG\.md|references/case-files-[a-z-]+\.md)$")
OLD_PLAN_MIGRATION = ("remains", "migrat", "replaces", "an earlier backlog")
EPIC_TICKET_ID = re.compile(r"\bM\d+-(?!SLICE-|TICK-|ADHOC-)[A-Z]{2,}-\d{2}\b")
LEGACY_ID = re.compile(r"\bM(?:\d+|<[a-z]+>)-(?:SLICE|TICK)-")
# The one eval case that is about a backlog published under the old IDs.
LEGACY_ID_EVAL = "tickets-rerun-earlier-backlog"
EPIC_TOKENS = (
    ("milestone → epic → ticket", "tickets exit criteria", "the hierarchy the proposal is confirmed against"),
    ("`TICKETS.md`", "tickets exit criteria", "the root plan file"),
    ("never a status", "tickets exit criteria", "status staying on GitHub, never in the plan"),
    ("one box per lane", "tickets exit criteria", "the flow graph's one box per lane"),
    ("solid arrow = wait for the merge", "tickets exit criteria", "what a solid arrow means"),
    ("dotted = build against the contract", "tickets exit criteria", "what a dotted arrow means"),
    ("day-1 table", "tickets exit criteria", "the day-1 who-starts-what table"),
    ("parent issue", "tickets exit criteria", "each epic published as a parent issue"),
    ("sub-issues", "tickets exit criteria", "the epic's tickets as its sub-issues"),
    ("no duplicate epic or link", "tickets exit criteria", "a re-run creating no second epic or link"),
    ("milestone → epic → ticket", "tickets Step 3A.1", "printing the proposal as the hierarchy"),
    ("`references/tickets-md.md`", "tickets Step 3A.2", "the pointer to the plan file's shape where the plan is written"),
    ("top of `TICKETS.md`", "tickets Step 0", "a stopped run's trace line living in the plan file"),
    ("## §Epics", "slicing.md", "the epic mechanism"),
    ("one feature of one milestone, inside one lane", "slicing.md", "what an epic is"),
    ("## §Waiting or building against", "slicing.md", "the two kinds of dependency"),
    ("**not** a *blocked by* link", "slicing.md", "a Builds against never becoming a link /build would stop on"),
    ("When unsure, it is `Depends On`", "slicing.md", "failing toward the wait"),
    ("never in `TICKETS.md`", "tickets-md.md", "the status ban"),
    ("**one box per lane**", "tickets-md.md", "one box per lane"),
    ("**Solid arrow** `-->` = **wait for the merge**", "tickets-md.md", "the solid arrow's meaning"),
    ("**Dotted arrow** `-.->` = **build against the contract**", "tickets-md.md", "the dotted arrow's meaning"),
    ("A day-1 ticket has no `Depends On`", "tickets-md.md", "the day-1 rule"),
    ("`/build` never writes", "tickets-md.md", "/build never writing the plan"),
    ("## §Epics are parent issues", "publishing.md", "the sub-issue procedure"),
    ("/sub_issues", "publishing.md", "the sub-issue endpoint"),
    ("sub_issue_id", "publishing.md", "the sub-issue's database id"),
    ("never pass `replace_parent`", "publishing.md", "never silently moving a ticket from another epic"),
    ("for each epic returns exactly the tickets", "publishing.md", "the sub-issue read-back"),
    ("creates no second epic and no second link", "publishing.md", "the idempotent re-run"),
    ("raise the limit and fetch again", "publishing.md", "a dedup index that cannot silently truncate"),
    ("A published ID is never renamed", "publishing.md", "old IDs kept, so dedup still matches them"),
    ("is migrated, never kept beside `TICKETS.md`", "publishing.md", "migrating an earlier plan file"),
    ("**Epics are parents, read back.**", "verification.md", "the sub-issue read-back check"),
    ("**`TICKETS.md` is the plan, never the status**", "verification.md", "the plan file check"),
    ("edit `TICKETS.md`", "adhoc-capture.md", "Mode B never editing the plan"),
    ("coordination point in `TICKETS.md`", "build Step 0", "/build reading coordination points from the plan"),
    ("A `Builds against` is not a blocker", "build Step 0", "/build starting a ticket that only builds against a contract"),
    ('title: "[M<milestone>-<EPIC>-<nn>] "', "feature_ticket_template.md", "the epic-scoped title"),
    ("### 🗂️ Epic", "feature_ticket_template.md", "the Epic field"),
    ("### 🧩 Builds Against", "feature_ticket_template.md", "the Builds Against field"),
    ("TICKETS.md here", "feature_ticket_template.md", "TICKETS.md on the never-list of Target Files"),
)
# How the flow graph may be written: GitHub renders Mermaid with a pinned version, so only these shapes are allowed.
GRAPH_NODE = re.compile(r'^lane_(\w+)\["([^"]+)"\]$')
GRAPH_EDGE = re.compile(r'^lane_(\w+) (-->|-\.->)\|"([^"]+)"\| lane_(\w+)$')
STATUS_HEADER = re.compile(r"^(?:status|state|progress|done|todo|in progress|%)$", re.IGNORECASE)
STATUS_MARKS = ("✅", "☑", "✔", "✓", "🟢", "🟡", "🔴")


def md_section(text: str, heading: str) -> str:
    """The body under a `## heading` line, up to the next `## ` heading."""
    m = re.search(rf"^## {re.escape(heading)}[^\n]*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def table_rows(block: str) -> list[list[str]]:
    """Markdown table rows as cells, header first, the |---| separator dropped."""
    rows = []
    for line in block.splitlines():
        s = line.strip()
        if s.startswith("|") and not re.fullmatch(r"\|[\s|:-]+\|", s):
            rows.append([c.strip() for c in s.strip("|").split("|")])
    return rows


def plan_example_faults(example: str) -> list[str]:
    """What is wrong with a TICKETS.md: status in it, a graph that is not one box per lane, an arrow whose kind
    disagrees with its coordination point, or a day-1 ticket that waits for a merge. Empty means it holds."""
    faults: list[str] = []
    for n, line in enumerate(example.splitlines(), 1):
        if re.match(r"^\s*[-*]\s*\[[ xX]\]", line):
            faults.append(f"line {n} is a checkbox - a status the file would have to keep up to date")
        if any(mark in line for mark in STATUS_MARKS):
            faults.append(f"line {n} carries a done mark")
        if line.strip().startswith("|"):
            for cell in (c.strip() for c in line.strip().strip("|").split("|")):
                if STATUS_HEADER.match(cell.strip("*` ")):
                    faults.append(f"line {n} has a {cell!r} column - status lives on GitHub")
    lanes = {r[0] for r in table_rows(md_section(example, "Lanes"))[1:] if r}
    if not lanes:
        faults.append("no Lanes table to draw the graph from")
    graph = re.search(r"```mermaid\n(.*?)```", example, re.DOTALL)
    if not graph:
        return faults + ["no mermaid block"]
    lines = [ln.strip() for ln in graph.group(1).splitlines() if ln.strip()]
    if not lines or lines[0] != "flowchart LR":
        faults.append("the graph does not open with `flowchart LR`")
    nodes: set[str] = set()
    edges: set[tuple[str, str, str]] = set()   # (dependant ticket, blocker ticket, kind)
    arrows: list[tuple[str, str, str, str]] = []  # (from lane, to lane, dependant ticket, blocker ticket)
    for ln in lines[1:]:
        node, edge = GRAPH_NODE.match(ln), GRAPH_EDGE.match(ln)
        if node:
            if not node.group(2).startswith(node.group(1)):
                faults.append(f"box lane_{node.group(1)} is labelled {node.group(2)!r}, not after its lane")
            nodes.add(node.group(1))
        elif edge:
            src, arrow, label, dst = edge.groups()
            kind = "waits for" if arrow == "-->" else "builds against"
            ids = EPIC_TICKET_ID.findall(label)
            if f" {kind} " not in label or len(ids) != 2:
                faults.append(f"arrow {src} {arrow} {dst} is labelled {label!r} - a {'solid' if arrow == '-->' else 'dotted'} "
                              f"arrow reads '<ticket> {kind} <ticket>'")
            else:
                edges.add((ids[0], ids[1], kind))
                arrows.append((src, dst, ids[0], ids[1]))
            for end in (src, dst):
                if end not in lanes:
                    faults.append(f"arrow {src} {arrow} {dst} ends at lane_{end}, which is not a lane")
        else:
            faults.append(f"graph line {ln!r} is not a box or an arrow in the allowed shapes")
    if nodes != lanes:
        faults.append(f"the graph has boxes {sorted(nodes)} for lanes {sorted(lanes)} - one box per lane, no other box")
    points: set[tuple[str, str, str]] = set()
    for line in md_section(example, "Coordination points").splitlines():
        if not line.strip().startswith("-"):
            continue  # prose around the list is not a point
        ids = EPIC_TICKET_ID.findall(line)
        kind = "waits for" if "waits for" in line else "builds against" if "builds against" in line else None
        if len(ids) != 2 or not kind:
            faults.append(f"coordination point {line.strip()!r} names no kind and two tickets")
        else:
            points.add((ids[0], ids[1], kind))
    if points != edges:
        faults.append(f"the arrows {sorted(edges)} differ from the coordination points {sorted(points)} - one arrow "
                      f"per point, solid for waits for, dotted for builds against")
    waiting = {dep for dep, _, kind in edges if kind == "waits for"}
    day1 = table_rows(md_section(example, "Day 1"))
    if not day1 or "Seat" not in day1[0]:
        faults.append("no Day 1 table with a Seat column")
    else:
        seen = set()
        for row in day1[1:]:
            if len(row) > 1:
                seen.add(row[1])
            for tid in EPIC_TICKET_ID.findall(row[2] if len(row) > 2 else ""):
                if tid in waiting:
                    faults.append(f"day 1 starts {tid}, which waits for a merge - it cannot start on day one")
        if seen != lanes:
            faults.append(f"the Day 1 table covers lanes {sorted(seen)}, not every lane {sorted(lanes)}")
    ticket_lane: dict[str, str] = {}
    for milestone in re.findall(r"^## M\d+\b.*?(?=^## |\Z)", example, re.MULTILINE | re.DOTALL):
        for row in table_rows(milestone)[1:]:
            epic = re.search(r"`(M\d+-[A-Z]{2,})`", row[0]) if row else None
            if not epic or len(row) < 4:
                faults.append(f"epic row {row!r} names no epic ID, lane, owner and tickets")
                continue
            if row[1] not in lanes:
                faults.append(f"epic {epic.group(1)} sits in {row[1]!r}, which is not a lane")
            for tid in EPIC_TICKET_ID.findall(row[3]):
                ticket_lane[tid] = row[1]
                if not tid.startswith(epic.group(1) + "-"):
                    faults.append(f"ticket {tid} is listed under epic {epic.group(1)} - a ticket sits in its own epic")
    # An arrow runs from the lane that goes first (the blocker's) to the lane that needs it (the dependant's).
    for src, dst, dependant, blocker in arrows:
        want = (ticket_lane.get(blocker), ticket_lane.get(dependant))
        if (src, dst) != want:
            faults.append(f"the arrow for {dependant} and {blocker} runs lane_{src} -> lane_{dst}, not from the "
                          f"blocker's lane to the dependant's ({want[0]} -> {want[1]})")
    return faults


def check_epic_plan(files: dict[str, Path]) -> None:
    """36. /tickets groups milestone -> epic -> ticket, publishes epics as parent issues read back, and writes the
    plan to a root TICKETS.md with a lane flow graph and a day-1 table - and never a status.

    A backlog sized by behaviour (#247) is too long to read as one list, and the plan it came with sat in a README
    inside docs/issues/ that nothing on GitHub could see (#249). The model: an epic is one feature of one milestone
    in one lane, published as a parent issue with its tickets as sub-issues; TICKETS.md holds the plan and never the
    status, which stays on the issues and the board so the file cannot go stale. A solid arrow is a wait for a merge
    and so a blocked-by link; a dotted arrow builds against a frozen contract and is never a link, because /build
    stops on an open blocker and the day-1 table promises the ticket can start. The rules are read where they must
    appear, and the invented example is read as a TICKETS.md would be: status, boxes per lane, arrows against their
    coordination points, the day-1 rows. Known limit: a line naming the old plan file passes when it also uses a
    migration word (remains, migrate, replaces), because the migration rule has to name the file it removes.
    """
    skill = files["tickets"].read_text(encoding="utf-8")
    step0 = re.search(r"^## Step 0\b(.*?)^## Step 1\b", skill, re.MULTILINE | re.DOTALL)
    step3a1 = re.search(r"^### 3A\.1\b(.*?)^### 3A\.2", skill, re.MULTILINE | re.DOTALL)
    step3a2 = re.search(r"^### 3A\.2\b(.*?)^## Step 3B\b", skill, re.MULTILINE | re.DOTALL)
    build = files["build"].read_text(encoding="utf-8")
    build0 = re.search(r"^## Step 0\b(.*?)^## Step 1\b", build, re.MULTILINE | re.DOTALL)
    template = (ROOT / "templates" / "feature_ticket_template.md").read_text(encoding="utf-8")
    refs = {name: (TICKETS_REFS / f"{name}").read_text(encoding="utf-8") if (TICKETS_REFS / name).exists() else ""
            for name in ("slicing.md", "tickets-md.md", "publishing.md", "verification.md", "adhoc-capture.md")}
    flat = lambda s: " ".join(s.split())  # noqa: E731
    regions = {"tickets exit criteria": flat(" ".join(criteria_of(skill))),
               "tickets Step 0": flat(step0.group(1) if step0 else ""),
               "tickets Step 3A.1": flat(step3a1.group(1) if step3a1 else ""),
               "tickets Step 3A.2": flat(step3a2.group(1) if step3a2 else ""),
               "build Step 0": flat(build0.group(1) if build0 else ""),
               "feature_ticket_template.md": flat(template),
               **{name: flat(text) for name, text in refs.items()}}
    if not refs["tickets-md.md"]:
        fail("commands/tickets/references/tickets-md.md is missing - /tickets has no shape to write TICKETS.md in")
    for token, where, what in EPIC_TOKENS:
        if token not in regions[where]:
            fail(f"{where} lost {what} (expected {token!r})")
    if not EPIC_TICKET_ID.search(regions["tickets exit criteria"]):
        fail("tickets exit criteria give no epic-scoped ID (M<n>-<EPIC>-<nn>) - dedup matches IDs, so their shape is a rule")

    # Everything after the heading: the example is a TICKETS.md, so it carries `## ` headings of its own.
    example = refs["tickets-md.md"].split("\n## §Example", 1)[-1] if "\n## §Example" in refs["tickets-md.md"] else ""
    block = re.search(r"^````markdown\n(.*?)^````", example, re.MULTILINE | re.DOTALL)
    if not block:
        fail("tickets-md.md §Example has no ````markdown TICKETS.md to read - the rules have nothing shown to hold them")
    else:
        for fault in plan_example_faults(block.group(1)):
            fail(f"tickets-md.md §Example TICKETS.md: {fault}")

    # Old IDs only where a backlog published under them is the subject.
    publishing_now = re.sub(r"^## §An earlier backlog\b.*?(?=^## )", "", refs["publishing.md"], flags=re.MULTILINE | re.DOTALL)
    evals = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
    current_cases = json.dumps([c for c in evals.get("evals", []) if c.get("skill") == "tickets"
                                and c.get("id") != LEGACY_ID_EVAL], ensure_ascii=False)
    for where, text in (("commands/tickets/SKILL.md", skill), ("tickets/references/slicing.md", refs["slicing.md"]),
                        ("tickets/references/tickets-md.md", refs["tickets-md.md"]),
                        ("tickets/references/publishing.md outside §An earlier backlog", publishing_now),
                        ("templates/feature_ticket_template.md", template),
                        ("evals/evals.json (tickets cases)", current_cases),
                        ("README.md", (ROOT / "README.md").read_text(encoding="utf-8")),
                        ("docs/how-it-works.md", (ROOT / "docs" / "how-it-works.md").read_text(encoding="utf-8")),
                        ("commands/new-component.md", files["new-component"].read_text(encoding="utf-8"))):
        m = LEGACY_ID.search(text)
        if m:
            fail(f"{where} still gives a ticket ID as {m.group(0)!r}... - IDs are epic-scoped now (M1-PARTY-02); an old "
                 f"ID belongs only where a backlog published under it is the subject")

    for rel in repo_files():
        if OLD_PLAN_HISTORY.match(rel):
            continue
        try:
            text = (ROOT / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if OLD_PLAN_FILE in line and not any(word in line.lower() for word in OLD_PLAN_MIGRATION):
                fail(f"{rel}:{n} still points at {OLD_PLAN_FILE} - the plan lives in {PLAN_FILE_NAME}; a reader of the "
                     f"old file reads a plan no run writes any more")



# Check 37 (#260). The verification companion's two halves.
VERIFY_READ_BACKS = ("Structure mirrored + idempotent.", "Epics are parents, read back.",
                     "Bodies are their files, read back.", "The board reads back set.",
                     "Dependencies are links, read back.")
# Every check verification.md held when #260 split it (16), plus the two #249 added and the two #279 added. A check
# may be reworded only by editing this list in the same change, so a dropped check is a visible diff, never a silent one.
VERIFY_CHECKS = ("§Resolve every symbol first", "Strategy was confirmed", "Lanes are modules.",
                 "Every ticket sits in one epic, in its epic's lane, under an epic-scoped ID.",
                 "`TICKETS.md` is the plan, never the status", "Every path resolves.", "Vertical:", "Vertical:",
                 "Horizontal:", "Every `#Plan` item has a home: a ticket, or a named later phase with its sequence point.",
                 "IDs unique.", "Dedup ran.", "Every ticket file is its issue body.", "Security DoD present",
                 "Independently mergeable.",
                 "No ticket lists a spine file or `TICKETS.md`; every ticket lists its feature doc and tests.",
                 *VERIFY_READ_BACKS)
VERIFY_SPLIT_TOKENS = (
    ("§Before publishing", "tickets Step 3b", "naming the half that runs over the local files"),
    ("§After publishing", "tickets Step 3b", "naming the half that runs once the issues exist"),
    ("a local-only run skips them", "tickets Step 3b", "a run with nothing published skipping the read-backs"),
    ("§Before publishing half", "tickets Step 3A.2", "running only the before-publishing half before anything is sent"),
    ("never read them as a reason to stop before publishing", "verification.md header", "the read-backs never blocking a publish"),
    ("A local-only run", "verification.md header", "the local-only run saying the read-backs did not run"),
)


def check_verification_publish_split(files: dict[str, Path]) -> None:
    """37. verification.md runs its checks over the local files before publishing, and its read-backs after.

    The companion's header and /tickets Step 3b both said every check runs before publishing, while three of them
    read GitHub back and can only run once the issues exist (#260). A logged re-run did them after publishing, as
    publishing.md says; a batch run taking the header literally would stop on three checks it cannot run yet. So the
    file has two halves, the read-backs sit only in the second, and no check left in the move.
    """
    text = (TICKETS_REFS / "verification.md").read_text(encoding="utf-8")
    before, after = text.find("\n## §Before publishing"), text.find("\n## §After publishing")
    if before < 0 or after < 0 or after < before:
        fail("tickets/references/verification.md is not split into `## §Before publishing` then `## §After publishing` - "
             "the read-backs need published issues, and a list read as all-before stops a run that cannot do them yet")
        return
    header, first, second = text[:before], text[before:after], text[after:]
    bullets = lambda s: re.findall(r"^- \*\*(.+?)\*\*", s, re.MULTILINE)  # noqa: E731
    for name in VERIFY_READ_BACKS:
        if name not in bullets(second):
            fail(f"verification.md §After publishing lacks the read-back {name!r}")
        if name in bullets(first):
            fail(f"verification.md lists the read-back {name!r} before publishing - it needs the published issues")
    for name in bullets(second):
        if name not in VERIFY_READ_BACKS:
            fail(f"verification.md §After publishing holds {name!r}, which is not a read-back - a check over the local "
                 f"files that runs after publishing runs too late to stop anything")
    held = bullets(text) + re.findall(r"^### (§Resolve every symbol first)\b", text, re.MULTILINE)
    for name in sorted(set(VERIFY_CHECKS)):
        want, got = VERIFY_CHECKS.count(name), held.count(name)
        if got < want:
            fail(f"verification.md holds {got} check(s) named {name!r}, not {want} - no check is dropped; reword one by "
                 f"editing VERIFY_CHECKS in the same change")
    skill = files["tickets"].read_text(encoding="utf-8")
    step3b = re.search(r"^## Step 3b\b(.*?)^## Step 3c\b", skill, re.MULTILINE | re.DOTALL)
    step3a2 = re.search(r"^### 3A\.2\b(.*?)^## Step 3B\b", skill, re.MULTILINE | re.DOTALL)
    regions = {"tickets Step 3b": " ".join((step3b.group(1) if step3b else "").split()),
               "tickets Step 3A.2": " ".join((step3a2.group(1) if step3a2 else "").split()),
               "verification.md header": " ".join(header.split())}
    for token, where, what in VERIFY_SPLIT_TOKENS:
        if token not in regions[where]:
            fail(f"{where} lost {what} (expected {token!r})")


# Check 38 (#235). A shape-changing /structure re-run syncs the moved paths to GitHub itself.
PATH_SYNC_HEADING = "## §A path rewrite reaches GitHub"
PATH_SYNC_CASE = "The paths that moved in the repo, not on GitHub"
PATH_SYNC_TOKENS = (
    ("`docs/issues/*.md` and `TICKETS.md`", "structure Step 0", "rewriting the moved paths in the plan as well as the tickets"),
    ("then commits it as a `path rewrite` and syncs the open issues", "structure Step 0",
     "the rewrite committed under the marker a later run finds, and synced in the same run"),
    ("§A path rewrite reaches GitHub", "structure Step 0", "the pointer to the sync procedure"),
    ("the close counts the issues synced", "structure Step 0", "the synced count in the close"),
    ("§A path rewrite reaches GitHub", "publishing.md §Provision", "the dedup exception pointing at the sync"),
    ("Every Mode A re-run runs that section's pre-flight before any other edit", "publishing.md §Provision",
     "/tickets finishing a sync the rewrite could not run, before a regroup reads the body as edited"),
    ("over the skipped open tickets whose file has a `path rewrite` commit", "publishing.md §Provision",
     "/tickets finding the rewrite by its commit, whatever the body now holds"),
    ("finishes whatever sync or settle it finds", "publishing.md §Provision", "/tickets finishing a settle as well as a sync"),
    ("normalised as §A path rewrite reaches GitHub normalises", "publishing.md §Provision",
     "the regroup pre-flight normalising a body the way the sync does, ticks included"),
    ("The lines change in the ticket files first, committed, then in each body", "publishing.md §Provision",
     "a regroup committing its lane change to the files, so a regrouped body reads as current later"),
    ("every ticket issue's body still equals its committed file", "publishing.md §Provision",
     "the regroup pre-flight comparing ticket issues only - an epic has no ticket file"),
    ("settled as that section's item 4 settles one", "publishing.md §Provision",
     "a regroup settling a body that differs instead of stopping for good"),
    ("edit only by its exceptions", "tickets Step 2", "the one-line dedup rule admitting the exceptions"),
    ("The run that moved the paths syncs the issues, in the same run", "publishing.md sync", "who runs the sync"),
    ("The rewrite is committed as a `path rewrite`", "publishing.md sync", "a rewrite commit a later run can find"),
    ("in the PR title too, so a squash-merge keeps them", "publishing.md sync", "the marker surviving a squash-merge"),
    ('git log --reverse --grep "path rewrite"', "publishing.md sync", "how a later run finds every rewrite, oldest first"),
    ("finds no such commit stops and says the marker is missing", "publishing.md sync",
     "a forgotten marker reported, never a silent `0 issues synced`"),
    ("each later rewrite starts where the one before it ended", "publishing.md sync",
     "a body several unsynced rewrites behind brought forward through all of them, and only them"),
    ("exactly what those commits changed", "publishing.md sync", "the sync publishing the rewrites and nothing else"),
    ("A diff that changes more than paths is flagged", "publishing.md sync", "a non-path edit riding in with the move shown before the yes"),
    ("Remote guard first", "publishing.md sync", "never syncing without a verified remote"),
    ("before editing any", "publishing.md sync", "the pre-flight covering every body before the first edit"),
    ("by its bracketed ID tag, never by title", "publishing.md sync", "matching a file to its issue by the ID tag"),
    ("`git show <commit>^:<file>` for one of them", "publishing.md sync", "syncing only a body equal to the file before a rewrite"),
    ("trailing whitespace and task-list marks normalised", "publishing.md sync",
     "a ticked box read as progress, never as an edit made on GitHub"),
    ("`[x]` or `[X]` reads as `[ ]`", "publishing.md sync", "both spellings GitHub accepts for a tick normalised"),
    ("the file at `<rewrite>` **or at any later commit**", "publishing.md sync",
     "a body a regroup or a later file edit moved on read as current, not as edited"),
    ("anything else → to settle", "publishing.md sync", "a body that matches no version going to the owner, never synced"),
    ("published in another shape than its file", "publishing.md sync", "a body published in another shape settled, not synced"),
    ("Closed issues keep their paths", "publishing.md sync", "closed issues keeping what they were built against"),
    ("An epic carries no paths", "publishing.md sync", "epics left alone"),
    ("owner's yes", "publishing.md sync", "the owner confirming the list before any edit"),
    ("nothing is edited until every issue on it is answered", "publishing.md sync", "no edit before every listed issue has an answer"),
    ("any ticked line the rewrite did not replace one for one, for the owner to place", "publishing.md sync",
     "a tick the sync cannot carry shown to the owner"),
    ("**the file wins**", "publishing.md sync", "settling an issue by dropping the GitHub change"),
    ("**the GitHub text wins**", "publishing.md sync", "settling an issue by keeping the GitHub change"),
    ("committed — never as a `path rewrite`", "publishing.md sync", "a settled GitHub change never passed off as a path move"),
    ("An issue left unsettled stops the sync", "publishing.md sync", "a body someone wrote on GitHub never overwritten unasked"),
    ("**keeping its ticks**", "publishing.md sync", "a sync never unticking a builder's boxes"),
    ("a line it replaced one for one passes its mark on", "publishing.md sync", "a tick on a moved path carried to the new path"),
    ("A settled issue gets `git show HEAD:<file>`", "publishing.md sync", "a settled issue published from the file, so it reads current"),
    ("Read every edited body back", "publishing.md sync", "the read-back"),
    ("each carries the ticks it was written with", "publishing.md sync", "the read-back checking the ticks"),
    ("The close counts it", "publishing.md sync", "the count in the close"),
    ("asks once more about every issue still to settle", "publishing.md sync",
     "the close naming the run that finishes a stopped sync, settles included"),
    (f"(case file: {PATH_SYNC_CASE})", "publishing.md sync", "the pointer to the war story"),
    ("except a shape-changing `/structure` re-run, which rewrites the paths it moved and nothing else",
     "tickets-md.md", "the one other writer of TICKETS.md"),
)
# The deferral #235 removed: a sync left to a later /tickets run that nothing tells the user to start.
PATH_SYNC_DEFERRAL = re.compile(r"keeps? the old paths until `/tickets`", re.IGNORECASE)


def check_structure_rerun_syncs_issues(files: dict[str, Path]) -> None:
    """38. A shape-changing /structure re-run rewrites the moved paths in the tickets AND TICKETS.md, and syncs the
    open issues in the same run.

    A logged test run (2026-09-13/14): a /structure re-run moved 55 files and rewrote every ticket file, while the
    published issues kept naming the emptied folders. The first fix let a later /tickets re-run sync them, but that
    run only happened because the owner wanted a regroup - /structure's handoff never names /tickets (#235). And
    TICKETS.md (#249) lists hub files by path, while nothing told the re-run to rewrite it. The rules are read where
    they must appear; the deferral is forbidden in /structure Step 0; the case file the procedure cites must exist.
    A review of that sync (#279) replayed a regroup and a ticked box after a synced move: both stopped the next move
    on issues nobody had edited, with no way to clear them - so ticks, later file versions and the settle are held too.
    """
    skill = files["structure"].read_text(encoding="utf-8")
    step0 = re.search(r"^## Step 0\b(.*?)^## Step 1\b", skill, re.MULTILINE | re.DOTALL)
    pub = (TICKETS_REFS / "publishing.md").read_text(encoding="utf-8")
    provision = re.search(r"^## §Provision and pre-flight\b(.*?)^## ", pub, re.MULTILINE | re.DOTALL)
    sync = re.search(rf"^{re.escape(PATH_SYNC_HEADING)}\n(.*?)(?=^## |\Z)", pub, re.MULTILINE | re.DOTALL)
    if not sync:
        fail(f"tickets/references/publishing.md has no {PATH_SYNC_HEADING!r} section - a path moved by a /structure "
             f"re-run stays at its old address on GitHub")
    flat = lambda s: " ".join(s.split())  # noqa: E731
    tickets = files["tickets"].read_text(encoding="utf-8")
    step2 = re.search(r"^## Step 2\b(.*?)^## Step 3A\b", tickets, re.MULTILINE | re.DOTALL)
    regions = {"structure Step 0": flat(step0.group(1) if step0 else ""),
               "tickets Step 2": flat(step2.group(1) if step2 else ""),
               "publishing.md §Provision": flat(provision.group(1) if provision else ""),
               "publishing.md sync": flat(sync.group(1) if sync else ""),
               "tickets-md.md": flat((TICKETS_REFS / "tickets-md.md").read_text(encoding="utf-8"))}
    for token, where, what in PATH_SYNC_TOKENS:
        if token not in regions[where]:
            fail(f"{where} lost {what} (expected {token!r})")
    m = PATH_SYNC_DEFERRAL.search(regions["structure Step 0"])
    if m:
        fail(f"structure Step 0 still defers the issue sync ({m.group(0)!r}...) - no phase after /structure is told "
             f"to run /tickets, so the issues keep the emptied folders")
    cases = (ROOT / "references" / "case-files-tickets.md").read_text(encoding="utf-8")
    if f"\n## {PATH_SYNC_CASE}\n" not in cases.replace("\r\n", "\n"):
        fail(f"references/case-files-tickets.md has no heading {PATH_SYNC_CASE!r}, which publishing.md cites")


# Check 39 (#279). An issue body is its ticket file.
BODY_RULE_HEADING = "## §An issue body is its ticket file"
BODY_RULE_POINTER = "§An issue body is its ticket file"
BODY_RULE_TOKENS = (
    ("--body-file docs/issues/<file>", "publishing.md body rule", "each issue created from its ticket file"),
    ("in both modes", "publishing.md body rule", "an ad-hoc issue published the same way as a planned one"),
    ("never retyped, trimmed, or given a header or footer", "publishing.md body rule",
     "no title line dropped and no footer added on the way to GitHub"),
    ("holds **no front matter**", "publishing.md body rule", "the issue template's header kept out of the ticket file"),
    ("reads as edited from the day it is published", "publishing.md body rule", "why the body must be the file"),
    ("Publish only committed files", "publishing.md body rule", "no body made from a file no later comparison can find"),
    ("declined, the run publishes nothing and says why", "publishing.md body rule", "a declined commit stopping the publish"),
    ("nothing uncommitted before the first `gh issue create`", "verification.md before publishing",
     "the commit checked before anything is published"),
    ("committed version of its ticket file it was written from", "verification.md after publishing",
     "the body read-back against a committed file"),
    (BODY_RULE_POINTER, "slicing.md", "the pointer at the Mode A publish step"),
    (BODY_RULE_POINTER, "adhoc-capture.md", "the pointer at the Mode B publish step"),
    ("write `#N` into the ticket file", "adhoc-capture.md", "the parent reference kept in the file, so the body still equals it"),
    ("Only then commit the file and publish it", "adhoc-capture.md",
     "the ad-hoc file committed after its parent reference is written, and before it is published"),
    ("**Every ticket file is its issue body.**", "verification.md before publishing", "the front-matter check over the local files"),
    ("compare one body with a different ticket's file and watch it fail", "verification.md after publishing",
     "the body read-back seen failing before it is trusted"),
    ("Every ticket issue this run created or edited", "verification.md after publishing",
     "the body read-back over ticket issues only - an epic has no ticket file"),
    ("IS the issue body: it starts at this comment, never copies the front matter", "feature_ticket_template.md",
     "the template saying where a ticket file starts"),
)


def check_issue_body_is_ticket_file() -> None:
    """39. A ticket's GitHub issue body is its file in docs/issues/, unchanged, and the tickets companions say so.

    The regroup pre-flight and the path sync decide "edited on GitHub" by comparing a body with its file, and nothing
    said how the body was made (#279). A logged test run published fifteen bodies with the file's title line dropped
    and a source footer added, so none equalled its file at any commit and the sync as written would have stopped on
    every one; two other runs wrote the issue template's front matter into their ticket files. The rule, its
    pointers at both publish steps, the check before publishing and the read-back after are read where they belong.
    """
    pub = (TICKETS_REFS / "publishing.md").read_text(encoding="utf-8")
    rule = re.search(rf"^{re.escape(BODY_RULE_HEADING)}\n(.*?)(?=^## |\Z)", pub, re.MULTILINE | re.DOTALL)
    if not rule:
        fail(f"tickets/references/publishing.md has no {BODY_RULE_HEADING!r} section - nothing says how an issue body "
             f"is made from its ticket file, so every comparison between them is a guess")
    verify = (TICKETS_REFS / "verification.md").read_text(encoding="utf-8")
    split = verify.find("\n## §After publishing")
    flat = lambda s: " ".join(s.split())  # noqa: E731
    regions = {"publishing.md body rule": flat(rule.group(1) if rule else ""),
               "slicing.md": flat((TICKETS_REFS / "slicing.md").read_text(encoding="utf-8")),
               "adhoc-capture.md": flat((TICKETS_REFS / "adhoc-capture.md").read_text(encoding="utf-8")),
               "verification.md before publishing": flat(verify[:split] if split >= 0 else verify),
               "verification.md after publishing": flat(verify[split:] if split >= 0 else ""),
               "feature_ticket_template.md": flat((ROOT / "templates" / "feature_ticket_template.md").read_text(encoding="utf-8"))}
    for token, where, what in BODY_RULE_TOKENS:
        if token not in regions[where]:
            fail(f"{where} lost {what} (expected {token!r})")


DESIGN_REFS = ROOT / "commands" / "design-system" / "references"
# Known sRGB colours the studio's converter must turn into OKLCH that the audit engine reads back unchanged.
STUDIO_RGB_PROBES = ((255, 136, 0, 1), (10, 125, 90, 1), (0, 0, 0, 1), (255, 255, 255, 1), (18, 52, 86, 0.5))
STUDIO_OKLCH_OUT = re.compile(r"^oklch\(\d\.\d{3} \d\.\d{3} \d{1,3}\.\d( / [\d.]+)?\)$")
STUDIO_DRIVER = """
var bad = [];
PRESETS.forEach(function (p) {
  if (p.length !== 3) { bad.push(p[0] + ' is not [name, light, dark]'); return; }
  [[1, 'light'], [2, 'dark']].forEach(function (x) {
    var v = p[x[0]], fg = fgFor(v), r = ct(fg, v), other = ct(fg === INK ? WHITE : INK, v);
    if (r == null) bad.push(p[0] + ' ' + x[1] + ' is not a colour the studio can read: ' + v);
    else if (r < 4.5) bad.push(p[0] + ' ' + x[1] + ' exports button text at ' + r.toFixed(2) + ':1');
  });
});
for (var L = 0.30; L <= 0.95; L += 0.05) for (var H = 0; H < 360; H += 30) {
  var v = 'oklch(' + L.toFixed(2) + ' 0.12 ' + H + ')', fg = fgFor(v);
  if (ct(fg, v) < ct(fg === INK ? WHITE : INK, v)) bad.push('fgFor picks the lower-contrast text for ' + v);
}
process.stdout.write(JSON.stringify({bad: bad, conv: PROBES.map(function (c) { return okFromRgb(c[0], c[1], c[2], c[3]); })}));
"""


def check_theme_studio_export() -> None:
    """40. The Theme Studio export is all of DESIGN.md §2, every colour OKLCH, with the higher-contrast button text.

    build-loop.md says the export IS §2. It read the light block with only `.dark` removed, so an OS in dark mode
    exported dark values as light; one inline accent beat `.dark`, so both blocks carried the same accent; custom
    picks left as hex; 15 of the §2 keys; and a luminance cut-off gave the Amber preset white text at 2.29:1 (#282).
    Exercised where a browser is not needed: the studio's own maths runs in node against its presets, a lightness
    sweep and known sRGB colours, and the audit engine reads the converted values back. The DOM half (the class set
    for each read, the per-mode accent) is held by the two lines that do it and was proven in headless Chromium.
    """
    import importlib.util
    import shutil
    import subprocess

    studio = (DESIGN_REFS / "theme-studio.md").read_text(encoding="utf-8")
    template = (DESIGN_REFS / "design-md-template.md").read_text(encoding="utf-8")
    s2 = re.search(r"^## 2\. Color & Roles.*?^:root \{\n(.*?)^\}", template, re.MULTILINE | re.DOTALL)
    keys = re.search(r"var KEYS=\[([^\]]*)\]", studio)
    if not s2 or not keys:
        fail("check 40 cannot find the §2 :root block in design-md-template.md or the export KEYS in theme-studio.md")
        return
    missing = sorted(set(re.findall(r"(--[\w-]+)\s*:", s2.group(1))) - set(re.findall(r"'(--[\w-]+)'", keys.group(1))))
    if missing:
        fail(f"theme-studio.md's export leaves out §2 tokens {missing} - build-loop.md pastes the export as all of §2")
    if not re.search(r"function rd\(m\)\{el\.classList\.remove\('dark','light'\);el\.classList\.add\(m\);", studio):
        fail("theme-studio.md's export no longer SETS the mode class before each read - with only .dark removed, "
             "an OS in dark mode exports dark values as the light block")
    if re.search(r"rs\.setProperty\('--(primary|accent|ring)'", studio):
        fail("theme-studio.md writes the accent inline directly - one inline value beats .dark, so both exported "
             "blocks carry the same accent; keep picks per mode and write them through apply()")

    maths = re.search(r"// --- maths.*?\n(.*?)\n\s*// --- /maths ---", studio, re.DOTALL)
    presets = re.search(r"^\s*var PRESETS=\[.*?\];$", studio, re.MULTILINE)
    if not maths or not presets:
        fail("check 40 cannot find the studio's `// --- maths` section or its PRESETS line in theme-studio.md")
        return
    if shutil.which("node") is None:
        fail("check 40 needs node on PATH to run the Theme Studio's contrast and OKLCH maths")
        return
    script = (f"{maths.group(1)}\n{presets.group(0)}\nvar PROBES={json.dumps(STUDIO_RGB_PROBES)};\n{STUDIO_DRIVER}")
    run = subprocess.run(["node", "-"], input=script, capture_output=True, text=True, encoding="utf-8", timeout=60)
    if run.returncode != 0:
        fail(f"check 40: the studio's maths did not run in node: {run.stderr.strip()[:300]}")
        return
    result = json.loads(run.stdout)
    for problem in result["bad"]:
        fail(f"theme-studio.md: {problem}")
    spec = importlib.util.spec_from_file_location("audit_engine", AUDIT_ENGINE)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    for (r, g, b, _a), out in zip(STUDIO_RGB_PROBES, result["conv"]):
        want = engine.luminance_from_hex(f"#{r:02x}{g:02x}{b:02x}")
        got = engine.luminance(out) if STUDIO_OKLCH_OUT.match(out) else None
        if got is None or abs(got - want) > 0.002:
            fail(f"theme-studio.md converts rgb({r} {g} {b}) to {out!r}, which is not OKLCH the audit engine reads "
                 f"back to the same luminance ({want:.4f})")



PLUGIN_ROOT_VAR = "${CLAUDE_PLUGIN_ROOT}"
PLUGIN_PATH_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_./-]+)")
# Longest name first, so MECHANISMS-ON-DEMAND.md is never read as MECHANISMS.md.
RULE_FILE_RE = re.compile(r"(?<![\w/-])(MECHANISMS-ON-DEMAND|MECHANISMS|PRINCIPLES|LESSONS)\.md")
RULES_LINE = "**Rule files — open by path, never search:**"
RULES_FALLBACK = "still starting with `$`"
# What a project install writes in its place: the relative paths start at the project root, not the working folder.
PROJECT_ROOT_NOTE = "paths start at the project root: the nearest folder, from the working directory up"
DEAD_README_POINTER = "see README"
# A skill that starts the spine from the template gives the template's path on the same line.
TEMPLATE_MENTION = "`PRODUCT.md` template"
TEMPLATE_PATH = "`${CLAUDE_PLUGIN_ROOT}/templates/PRODUCT.md`"
# Plugin paths a copy install may leave as they are, because the skill names its own copy-install fallback.
PLUGIN_PATHS_WITH_FALLBACK = {"commands/frontend-audit/audit.py": "/frontend-audit §Which engine runs (#256)"}
# Files the agent opens with Read: Claude Code fills `${CLAUDE_PLUGIN_ROOT}` into skill text only.
READ_COMPANIONS = ("PRINCIPLES.md", "references/mechanisms.md", "references/mechanisms-on-demand.md",
                   "references/lessons.md")
# Each Read companion gives the route paths from its own folder.
COMPANION_ROUTE_TOKENS = (
    ("PRINCIPLES.md", ("`references/mechanisms.md`", "`references/mechanisms-on-demand.md`",
                       "`references/lessons.md`", "`MECHANISMS-ON-DEMAND.md`", "beside this file",
                       "never search")),
    ("references/mechanisms.md", ("`mechanisms-on-demand.md` in the plugin or a clone",
                                  "`MECHANISMS-ON-DEMAND.md` in a copy install")),
    ("references/mechanisms-on-demand.md", ("`tools/session_cost.py` in the folder above this",
                                            "`session_cost.py` beside this file")),
)


def rule_path_for(label: str) -> str:
    """The exact text a skill's rule-files line carries for one rule file it names."""
    path = f"`{PLUGIN_ROOT_VAR}/{POINTER_FILES[label]}`"
    return path if label == "PRINCIPLES.md" else f"{label} = {path}"


def check_rule_file_paths(files: dict[str, Path]) -> None:
    """41. A skill that names a rule file says where it is, and every plugin path it gives exists (#287).

    Every skill header said "see README for its path per install mode"; the README gave none, and in the plugin
    no file is called MECHANISMS.md (it ships as references/mechanisms.md). A logged /vision run on plugin 1.57.0
    grepped for MECHANISMS.md at the plugin root, ran a case-sensitive `find` for MECHANISMS*, found nothing, and
    never opened PRINCIPLES.md or the mechanisms - it ran without the rules it was meant to follow. Claude Code
    fills `${CLAUDE_PLUGIN_ROOT}` into skill text (checked on 2.1.274, flat and SKILL.md skills alike), but not
    into a file the agent opens with Read and not into the shell, so those files give paths from their own folder.
    """
    for name, path in sorted(files.items()):
        text = path.read_text(encoding="utf-8")
        where = path.relative_to(ROOT).as_posix()
        if DEAD_README_POINTER in text:
            fail(f"{where} still says {DEAD_README_POINTER!r} - the README gives no path; name the rule files by path")
        for ln in text.splitlines():
            if TEMPLATE_MENTION in ln and TEMPLATE_PATH not in ln:
                fail(f"{where} names the {TEMPLATE_MENTION} without its path {TEMPLATE_PATH}: {ln.strip()[:80]!r}")
        named = sorted({m.group(1) + ".md" for m in RULE_FILE_RE.finditer(text)})
        if named:
            line = next((ln for ln in text.splitlines() if RULES_LINE in ln), None)
            if line is None:
                fail(f"{where} names {', '.join(named)} but has no {RULES_LINE!r} line - in a plugin install no "
                     f"file is called MECHANISMS.md, so the agent has to search for its rules")
            else:
                for label in named:
                    if rule_path_for(label) not in line:
                        fail(f"{where} names {label}, but its rule-files line does not give "
                             f"{rule_path_for(label)} - the agent cannot open it without searching")
                if RULES_FALLBACK not in line:
                    fail(f"{where}'s rule-files line has no fallback for a path Claude Code did not fill in "
                         f"({RULES_FALLBACK!r})")
        for m in PLUGIN_PATH_RE.finditer(text):
            if not (ROOT / m.group(1)).is_file():
                fail(f"{where} gives {PLUGIN_ROOT_VAR}/{m.group(1)}, which is not a file in the plugin - "
                     f"the path opens nothing")
    read_files = [ROOT / rel for rel in READ_COMPANIONS] + sorted((ROOT / "commands").glob("*/references/*.md"))
    for path in read_files:
        if PLUGIN_ROOT_VAR in path.read_text(encoding="utf-8"):
            fail(f"{path.relative_to(ROOT).as_posix()} uses {PLUGIN_ROOT_VAR} - the agent opens this file with "
                 f"Read, where Claude Code never fills it in; give the path from this file's own folder")
    for rel, tokens in COMPANION_ROUTE_TOKENS:
        unquoted = re.sub(r"^\s*>\s?", "", (ROOT / rel).read_text(encoding="utf-8"), flags=re.MULTILINE)
        flat = " ".join(unquoted.split())
        for token in tokens:
            if token not in flat:
                fail(f"{rel} no longer says {token!r} - the path from that file to the other rule files or "
                     f"tools, per install route")


def bash_for_install() -> str | None:
    """A POSIX bash for install.sh. On Windows, Git's own: System32's bash.exe is WSL, a different machine."""
    import shutil
    if os.name == "nt":
        git = shutil.which("git")
        if git:  # <Git>/cmd/git.exe or <Git>/mingw64/bin/git.exe
            for root in Path(git).parents[1:3]:
                cand = root / "bin" / "bash.exe"
                if cand.is_file():
                    return str(cand)
        return None
    return shutil.which("bash")


def check_copy_install_rule_paths() -> None:
    """41b. A real copy install leaves no rule-file path the agent cannot open (#287).

    install.sh copies the rule files under their installed names (MECHANISMS.md, not references/mechanisms.md)
    and must rewrite every `${CLAUDE_PLUGIN_ROOT}/...` path in what it installed. It is run for real into a
    temporary project: a plugin path left behind, or a rewritten path with no file under it, is a skill that has
    to search.
    """
    import subprocess
    import tempfile

    bash = bash_for_install()
    if bash is None:
        if os.environ.get("CI"):
            fail("check 41: no bash to run install.sh - the copy-install route goes unchecked")
        else:
            print("note: check 41's copy-install run skipped - no Git bash found")
        return
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / ".claude"
        run = subprocess.run([bash, (ROOT / "install.sh").as_posix(), "--project", Path(tmp).as_posix()],
                             cwd=ROOT, capture_output=True)
        if run.returncode != 0:
            fail(f"check 41: install.sh --project failed: {run.stderr.decode('utf-8', 'replace')[-300:]}")
            return
        support = base / "product-playbook"
        installed = sorted((base / "commands").rglob("*.md")) + sorted(support.glob("*.md"))
        if not installed:
            fail("check 41: install.sh --project installed no Markdown files - nothing to check")
        for path in installed:
            text = path.read_text(encoding="utf-8")
            where = path.relative_to(base).as_posix()
            for m in PLUGIN_PATH_RE.finditer(text):
                if m.group(1) not in PLUGIN_PATHS_WITH_FALLBACK:
                    fail(f"copy install: {where} still gives {PLUGIN_ROOT_VAR}/{m.group(1)} - install.sh must "
                         f"rewrite it to the file it installed")
            if RULES_LINE in text:
                given = re.findall(r"`\.claude/product-playbook/([A-Za-z0-9_.-]+)`", text)
                if "PRINCIPLES.md" not in given:
                    fail(f"copy install: {where}'s rule-files line does not point at the installed PRINCIPLES.md")
                if PROJECT_ROOT_NOTE not in text or RULES_FALLBACK in text:
                    fail(f"copy install: {where}'s rule-files line does not say where the project root is - its "
                         f"paths are relative, and Claude Code may start in a subfolder")
                for name in given:
                    if not (support / name).is_file():
                        fail(f"copy install: {where} points at .claude/product-playbook/{name}, which "
                             f"install.sh did not install")
        if not (support / "session_cost.py").is_file():
            fail("copy install: session_cost.py is not installed - a copy-install close could never measure its cost")



# The instruction every skill carries. Both files are read on every run, by their own statement: PRINCIPLES.md
# "is loaded by every skill" (PRINCIPLES.md), and of MECHANISMS.md, "Everything in that file is read by every
# phase, every run" (MECHANISMS-ON-DEMAND.md, which is the file that says it). "the first step" and not "Step 0":
# /drift-check runs Step 0b and 0c before its Step 0, and /new-component has no Step 0 at all.
OPEN_RULES_LINE = "**Open `PRINCIPLES.md` and `MECHANISMS.md` before the first step**"
OPEN_RULES_SITUATIONAL = "a situational companion only when a rule points into it"
# MECHANISMS-ON-DEMAND.md is "the mechanism you open only when its trigger fires" and LESSONS.md is the same:
# opening either on every run is the per-session context cost they were split out to avoid, so no skill may
# order it. Checked as a phrase that would ORDER it, not as a mention - every skill names both files' paths.
ALWAYS_OPEN_SITUATIONAL = re.compile(
    r"(?:\b(?:[Aa]lways|[Uu]nconditionally)\s+(?:open|read|load)\b[^\n]{0,60}?`?(?:MECHANISMS-ON-DEMAND|LESSONS)\.md"
    r"|\b(?:[Oo]pen|[Rr]ead|[Ll]oad)\b[^\n]{0,60}?`?(?:MECHANISMS-ON-DEMAND|LESSONS)\.md`?[^\n]{0,60}?"
    r"\b(?:before the first step|before Step 0|on every run|every run|always|unconditionally|at the start))")


def check_rule_files_are_opened(files: dict[str, Path]) -> None:
    """42. A skill that names its rule files says to OPEN the two that are read every run (#290).

    Every header said "Apply PRINCIPLES.md" and named MECHANISMS.md sections (§Step 3b, §Spine resolution), but
    no line told the agent to open either file, so it was left to judgement. After #287 gave the paths, two
    /vision runs on the same version split: a logged test run opened PRINCIPLES.md and never MECHANISMS.md,
    while a headless run opened MECHANISMS.md and MECHANISMS-ON-DEMAND.md and never PRINCIPLES.md. Both wrote a
    spine section, which §Step 3b and §Step 3c govern. The situational companions stay opt-in: this check fails
    a skill that orders them open on every run, which would restore the context cost they were split out to avoid.

    Known limit: that last guard reads prose, so it catches the phrasings a skill would plausibly use ("always
    open X", "open X on every run", "read X at the start") and not every possible rewording. The load-bearing
    half is the exact instruction above, which is a literal match.
    """
    for name, path in sorted(files.items()):
        text = path.read_text(encoding="utf-8")
        where = path.relative_to(ROOT).as_posix()
        if RULES_LINE not in text:
            continue  # a skill that names no rule file has none to open (/frontend-audit)
        if OPEN_RULES_LINE not in text:
            fail(f"{where} names its rule files but never says to open them - naming a file is not reading it, "
                 f"so whether the run loads the rules is left to chance ({OPEN_RULES_LINE!r})")
        elif OPEN_RULES_SITUATIONAL not in text:
            fail(f"{where} says to open the rule files without holding the situational ones back "
                 f"({OPEN_RULES_SITUATIONAL!r}) - MECHANISMS-ON-DEMAND.md and LESSONS.md are opened on a trigger")
        m = ALWAYS_OPEN_SITUATIONAL.search(" ".join(text.split()))
        if m:
            fail(f"{where} orders a situational companion open every run ({m.group(0)!r}) - that file exists to "
                 f"be opened when its trigger fires; always-open is the context cost it was split out to avoid")


if __name__ == "__main__":
    sys.exit(main())
