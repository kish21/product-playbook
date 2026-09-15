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
     manifest.json, .claude-plugin/plugin.json and the README badge must all match it.
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
     25.8KB against its own ~15KB prune rule, because a rule with no check is a suggestion.
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
 23. The long derivation phases (foundation, contracts, tickets, build) carry the CONTEXT-HYGIENE rule -
     bulky command output goes to a file, one progress line per named step, close metrics measured or
     "not measured". Four phases in a row ignored /build's "bulky output to files" sentence and cost
     $70-75 each, ~60% of it re-reading tool output; a rule in one skill's prose bound nobody.
"""
from __future__ import annotations
import json
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
    # 30. /build's loop carries its overhead rules: read limit, triggered checks, flaky capture, board status
    check_build_loop_overhead(files)
    # 31. the audit runs the INSTALLED engine, and /foundation wires a project copy into hooks + CI
    check_audit_engine_resolution(files)
    check_audit_engine_behaviour()

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
# ~15KB is the prune threshold CONTRIBUTING.md §Lesson format sets for everyone; it is enforced on the
# governing files every session loads AND on every skill file. The exemption set is EMPTY (#138): build,
# tickets and design-system were the three holdouts, and each was pruned by moving on-demand mechanism
# into its own `references/` companion rather than by widening the rule. A directory-form skill's
# references/ is deliberately NOT size-checked - that is the whole point of moving mechanism there: it
# ships with the skill but is opened only when the situation calls for it.
SIZE_LIMIT = 15 * 1024
SIZE_EXEMPT: dict[str, str] = {}
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
    extra = {ROOT / "README.md", ROOT / "VISION.md", ROOT / "PRINCIPLES.md",
             ROOT / "references" / "mechanisms.md",
             ROOT / "references" / "mechanisms-on-demand.md"}
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
    for name, path in sorted(files.items()):
        size = content_size(path)
        if size > SIZE_LIMIT and name not in SIZE_EXEMPT:
            fail(f"{name} is {size / 1024:.1f}KB (> {SIZE_LIMIT // 1024}KB) - run a prune pass, or add "
                 f"a named exemption with a reason to SIZE_EXEMPT")


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

    /contracts closed with "run /build" while /playbook's order is contracts -> tickets -> build. On the
    Potluck live run (2026-09-13) the owner did what the skill said, /tickets never ran, and M1 reached
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

    /build has said "bulky output to files, broad searches to subagents" since #31, and on the Potluck
    run /foundation (385 calls) and /contracts (326 calls) each cost ~$70-75 with ~60% of it cache
    re-reads of tool output - full test logs, whole files read back, long shell output. A sentence in one
    skill's Step 1 bound nobody; the rule now lives once in MECHANISMS-ON-DEMAND.md and each phase that
    runs commands for most of a session must point at it. Reporting and context only - the rule changes
    nothing a phase checks, writes or verifies.
    """
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

    On the Potluck live run (2026-09-13) /tickets wrote 15 vertical slices as one dependency chain with
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
CLOSE_LAST = "The close is the run's last message"


def check_close_is_last(files: dict[str, Path]) -> None:
    """25. A skill that composes a reviewer says the plain close is the run's LAST message.

    Potluck M1-SLICE-01 (2026-09-13): /build committed, then ran /security-review, and the review's
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
    # Potluck /build #8 (2026-09-14): the sentence above was present and the run still ended on the
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


# The obligations that make a module folder a complete lane (#215). Each token names a rule the shape
# reference must carry, and the exit criterion that binds /structure to it.
LANE_SHAPE_TOKENS = ("complete lane", "registry line", "routes", "tests", "platform/", "frontend", "Hub files")
BUILD_SEAT_TOKENS = ("Owner", "seat", "STOP")


def check_module_is_a_lane(files: dict[str, Path]) -> None:
    """26. /structure makes a module a complete lane and names the hub files; /build gates on the seat.

    Potluck (2026-09-12/13): /structure chose domain modules and drew them, then put every module's
    handlers in one http/ folder, every store in one platform/ folder and all the wiring in index.ts;
    the frontend was by tool throughout. /tickets then named index.ts in seven of fifteen tickets, and
    the backlog could not be split between two people however it was grouped - the folders each person
    would change were the shared ones. The rule is one registry line per module and everything else
    inside the module; the hub files are named in STRUCTURE.md so /tickets can treat
    them as shared, and check_structure.py verifies each exists. On the /build side, MarkVid's
    /jr-ticket refuses a ticket whose owner label is not its own - lane ownership is a gate.
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

    On the Potluck run (2026-09-12) /architect ran 17 web searches; each result page entered the context
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
    ("Read the ticket's slice", "a read limit in Step 0 - both Potluck builds pasted whole modules into the "
     "conversation in the first two minutes, and every later call re-read them"),
    ("whose trigger matches", "a triggered live-path walk - 17 untagged checks were weighed on every ticket"),
    ("the full suite once at the gate", "targeted test runs while iterating"),
    ("FLAKY", "the flaky-test rule - build #8 re-investigated the flake build #7 never wrote down"),
    ("Never re-run until green", "the ban on re-running a flaky test until it passes"),
    ("In Progress", "moving the board card when work starts - #7's card read Todo after it merged"),
    ("**Done**", "moving the board card when the PR merges"),
    ("citing the evidence Step 2 already captured", "Step 3b citing Step 2's evidence instead of re-running it"),
)


def check_build_loop_overhead(files: dict[str, Path]) -> None:
    """30. /build carries the rules that cut its fixed overhead, and every live-path check has a trigger.

    Potluck /build #7 and #8 (2026-09-14): #8 needed half the code of #7 and took nearly the same working
    time (35 vs 42 min). The logs showed the overhead, not the ticket: whole modules pasted into the
    conversation up front, a flaky test re-investigated because the previous build never recorded it,
    full suites on every iteration, 17 live-path checks with no triggers, Step 3b asking for evidence
    Step 2 had already produced - and a board card still at Todo after the ticket merged.
    """
    text = " ".join(files["build"].read_text(encoding="utf-8").split())
    for token, what in BUILD_OVERHEAD_TOKENS:
        if token not in text:
            fail(f"build lost {what} (expected {token!r})")
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

    Potluck build M2-SLICE-02 (2026-09-14, plugin 1.46.0 installed) looked for the script with
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
    with tempfile.TemporaryDirectory() as tmp:
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

        cases = (
            (older, "\n# an older engine\n", f"is {older}, OLDER than this engine {current}"),
            ("999.0.0", "\n# a newer engine\n", "NEWER than this engine"),
            (current, "\n# edited in place\n", "edited in place"),
            ("0.0.1", "", "has the same checks as this engine"),
        )
        for version, extra, expected in cases:
            put_copy(version, extra)
            r = run(AUDIT_ENGINE, "ui")
            if expected not in r.stdout:
                fail(f"audit engine: a project copy at {version!r} should report {expected!r} - it did not")

        copy = put_copy(current, "")
        r = run(copy, "ui")
        if r.returncode == 0 or "engine copy:" in r.stdout:
            fail("audit engine: the project copy (as a hook/CI runs it) must fail on the planted ERROR "
                 "and must not report on itself")


if __name__ == "__main__":
    sys.exit(main())
