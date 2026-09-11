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
 18. Every STATE docs/state-model.md defines is implemented by at least one skill. The `running` state
     was improvised in two live runs before it existed in the model; the mirror failure is a state
     defined in the model that no skill writes, which reads as a rule the product does not have.
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
# Standalone use is first-class in this toolkit, so every gate must offer a way through.
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
# ~15KB is the prune threshold MECHANISMS.md §Lesson format sets for everyone; it is enforced on the
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


def check_file_sizes(files: dict[str, Path]) -> None:
    """11. The ~15KB prune rule applies to the file that wrote it.

    PRINCIPLES.md set the threshold and exempted itself, reaching 25.8KB - and unlike any single skill it
    is loaded by EVERY skill, so its size is the per-session attention cost of the whole system. A rule
    with no check is how it got there.
    """
    for rel in ("PRINCIPLES.md", "references/mechanisms.md", "references/mechanisms-on-demand.md",
                "references/lessons.md"):
        size = (ROOT / rel).stat().st_size
        if size > SIZE_LIMIT:
            fail(f"{rel} is {size / 1024:.1f}KB (> {SIZE_LIMIT // 1024}KB) - the prune rule it defines "
                 f"applies to it first: move mechanism into references/, or condense")
    for name, path in sorted(files.items()):
        size = path.stat().st_size
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
        block = text.split("**Exit criteria:**", 1)[1].split("\n## ", 1)[0]
        for line in block.splitlines():
            s = line.strip()
            if not s.startswith("- [ ]"):
                continue
            crit = s[5:].strip()
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
CRITERIA_CITED = {"vision"}


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


if __name__ == "__main__":
    sys.exit(main())
