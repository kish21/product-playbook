---
name: drift-check
description: >
  Cross-cutting skill of product-playbook — run ANYTIME. Checks whether the product is still building
  the vision or has drifted: scope creep (features built that are OUT OF SCOPE), vision misalignment,
  and code↔docs drift. Use when you suspect creep, before a milestone, or run /drift-check "are we
  on track", "did we drift", "scope creep", "is this still the plan". Reports against the project
  spine (PRODUCT.md, or the project's existing docs / inferred-from-code — see MECHANISMS.md
  §Spine resolution). Does not advance the phase chain.
---

# `/drift-check` — Cross-cutting · run as a **skeptical reviewer**

> Part of **product-playbook**. Reads the project spine — `PRODUCT.md`, or (for existing/brownfield
> projects) the project's own docs, or an inferred-from-code picture — and the codebase/docs.
> Resolve the spine per `MECHANISMS.md` §Spine resolution.
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **vision-alignment (top priority)**, **scope discipline**,
> **no-drift / no-assumptions**, **docs match reality**, **verify against real code**.

> This is the seatbelt against the pain that motivated product-playbook: *"I started this product but
> slowly drifted out of control adding features which may not be required."* Run it often.

## Contract
- **Purpose:** detect and surface scope creep, vision drift, and code↔docs drift — early.
- **Reads:** the resolved spine's Vision, Scope (Deferred + Non-goals), Plan (concern-area checklist), Build log; the codebase + docs. (`PRODUCT.md#…` when it exists; otherwise the equivalent sections of the resolved doc, per MECHANISMS.md §Spine resolution.)
- **Writes:** a drift report to the user + a dated row in `PRODUCT.md#Drift log` on any confirmed drift (its OWN section — never `/learn`'s `#Learnings`); does NOT advance the chain. **If there is no `PRODUCT.md`, do not create one** — report to the user and, if the project keeps a log/CHANGELOG, offer to append the drift note there.
- **State model** (`docs/state-model.md` §2c): writes `#Drift log` · `declined` ✓ · `override` n/a — cross-cutting, it gates on nothing · `superseded` n/a — append-only log: one entry per run
- **Exit criteria:**
  - [ ] Built features cross-checked against `#Scope` — any OUT-OF-SCOPE item that got built is flagged as creep.
  - [ ] Current direction cross-checked against `#Vision` — misalignment surfaced.
  - [ ] Code↔docs drift checked — every stated capability / security control / supported path traced to the code that backs it.
  - [ ] **Claim-to-evidence pass:** every exit criterion recorded as met in the spine is given one of four
    verdicts — `VERIFIED` · `PARTIALLY VERIFIED` · `UNVERIFIED` · `CONTRADICTED` (`docs/state-model.md` §2g).
    A claim with no evidence is **reported, never silently passed**.
  - [ ] A clear verdict: on-track, or a specific list of drifts + a recommended cut/correction.

## Step 0b — Claim-to-evidence pass (re-verify, don't re-read)

> **One pass, two moments.** Every phase now runs this same pass at its own transition, scoped to the
> criteria it just wrote (`MECHANISMS.md` §Step 3b, item 4 — the transition guard). This sweep is the
> cross-cutting one: every claim in the spine, including the ones written before the guard existed.

Every `- [x]` in the spine is a claim. **A checked box and a checked box with fabricated justification are
indistinguishable to any later reader, human or agent** — unless the claim points at something re-runnable.
So for each one:

1. **Find its evidence line** — the single form settled in `docs/state-model.md` §2f:
   `` `evidence: <command> → <result> · <artefact> · <YYYY-MM-DD>` ``. There is exactly one format; **do
   not invent a second one**, and do not "upgrade" prose evidence you find into that shape without
   re-running it — transcribing a claim into evidence-looking text is the failure this pass exists to catch.
2. **Re-run it, don't re-read it.** Execute the command. Check the artefact exists.
3. **Assign one of four verdicts** (`§2g`), and say which:
   - `VERIFIED` — re-ran, result matches.
   - `PARTIALLY VERIFIED` — re-ran and the artefact is there, but the result differs in degree not
     direction, or the evidence covers only part of the claim.
   - `UNVERIFIED` — **no measurement was taken**: no evidence line, or the command cannot run here
     (missing tooling, credentials, a live service). Say *which*, so the reader knows whether to be
     worried or to install something.
   - `CONTRADICTED` — **a measurement was taken and it disagrees**: the command fails, or the named
     artefact does not exist.
4. **Never merge the last two.** `UNVERIFIED` is absence of evidence; `CONTRADICTED` is evidence of
   absence. Reporting a never-attempted check as CONTRADICTED sends someone chasing a phantom regression;
   reporting a failed one as UNVERIFIED hides a real one behind "we could not tell".
5. **Report every unevidenced claim.** A criterion nobody measured is a normal, honest state — plenty of
   things are judged rather than measured — but it is never silently counted as met.

An `UNVERIFIED` claim is a finding about the *record*, not necessarily about the code; a `CONTRADICTED`
one is a finding about both. Rank them accordingly in the report.

## Step 0c — Check the project against its OWN rules

Before comparing code to docs, compare the project to the rules it publishes. **A rule the project does
not apply to itself is the one most likely to be broken** — the author knows the reasoning, so the file
feels exempt (`LESSONS.md`). Read the spine's own stated rules — thresholds, naming requirements, gates,
counts — and ask of each: *does this repository satisfy it?* That list is free, specific to this project,
and nobody else will ever run it.

## Step 0 — Resolve the spine, then build context
- **Resolve the spine first** (MECHANISMS.md §Spine resolution): `PRODUCT.md` if present; else the
  project's own docs (`CLAUDE.md` → `README.md` → `docs/` → `AGENTS.md`); else (code only) an
  **INFERRED** picture from code + package metadata. **Say which you resolved.**
- Read the spine's Vision / Scope / Plan / Build-log equivalents. Build the picture of what was
  *supposed* to be built.
- **Verify against the real code/docs** — don't assume the spine is current; reconcile it with what's actually there.
- **Code-only (Tier 3):** there is no recorded intent, so **true scope/vision drift cannot be
  judged** — do not invent a baseline and grade against it. You may still sanity-check the code's
  internal consistency; then jump to Step 3 and recommend bootstrapping a spine.

## Step 1 — Apply principles
- **Vision-alignment is top priority:** the test for every feature is "does this serve the vision?"
- **Scope discipline:** anything built that's in OUT-OF-SCOPE (without its trigger having fired) is creep.
- **Docs match reality:** a claim in the docs that the code doesn't support is drift too.

## Step 2 — Check for drift
> Each phase now runs its own **Step 3c** contradiction check before its gate closes (`MECHANISMS.md` §Step 3c), so a contradiction *between* two spine sections should be rare and dated. This sweep is what catches the ones that escaped — and a conflict you find here that carries **no `superseded by` line** means a phase skipped its Step 3c: report that as drift in its own right.

1. **Scope creep:** list features in the code/build log not justified by `#Scope`; flag anything built that's a **Non-goal** or a **Deferred** item whose trigger never fired. Also flag the inverse: a deliberate pivot the spine never recorded → recommend updating `#Scope`/`#Vision`, not cutting code.
2. **A stalled `running` gate.** A section in the `running` state (`docs/state-model.md` §2a) **past its
   due date with no result** is a finding nobody was emitting: the experiment was scheduled, the chain
   moved on provisionally, and the result never landed. Report it with the date it was due and what
   downstream work is still marked provisional.
3. **Vision drift:** is the current direction still serving `#Vision` and its north-star metric? Surface any quiet pivot. If `#Validation` is empty or holds an **override** while code exists, that is a **standing finding** — the product is being built on an untested riskiest assumption; recommend `/validate` (still cheaper than the next feature).
4. **Table-stakes drift:** re-read `#Scope`'s table-stakes list. An item marked **in-scope now** that was
   never built is drift of the most expensive kind — it surfaces at ship time as "we can't launch without
   this". An item marked **Deferred** whose **trigger has now fired** is the same finding with a date on it.
5. **Plan / concern-area drift:** milestones skipped or reordered off core-first? Re-read `#Plan`'s concern-area checklist — any "now" still unbuilt, any "next" overdue?
6. **Doc drift:** grep the docs' **concrete** claims — paths, flags, model names, field names, stage lists — against the code, and flag each that no longer holds. Prose re-reading finds nothing; a stale instruction is worse than none because it gets followed. If the `#Build log` itself is stale vs the code, flag that as drift too.
7. **Agent instructions that are ABSENT, before any check for rot.** A filled spine and **no**
   `CLAUDE.md` / `AGENTS.md` at all is the emptiest possible case, and it passed silently: every
   check below reads a file that has to exist. Report it — the next session is then told nothing
   of what every phase decided, which on a solo-with-agents workflow *is* the workflow. A file the
   project's framework generated (a `<!-- BEGIN: -->` block and nothing else) counts as absent.
   `/structure` scaffolds it from `templates/AGENTS.md`.
8. **Agent-instruction drift — the project's OWN skills/commands/`CLAUDE.md`.** These rot exactly like docs, but they are far more dangerous, because they are **executed, not read**: a stale `docs/` page misleads a human who can sanity-check it, while a stale `.claude/skills/*` is picked up and *acted on*. Check each skill's concrete, falsifiable claims against the code — file paths and directory layout, storage/vendor, model + provider, contract field names, stage list and count, and any "always/never do X" rule. Flag three things: claims that are **false**, skills that contradict **each other**, and skills that contradict a **locked decision** in the spine. *(Real instance: a project's three most task-relevant skills were each materially wrong — a stage documented as "no LLM, schema check only" that actually runs a vision judge; a contract listing fields deleted a session earlier plus a storage vendor the project had migrated off; and an "X is blocking" claim that inverted a locked blocking-vs-advisory split. Two also contradicted each other on whether a whole backend technology was permitted. Nobody had noticed, because sessions read the code directly and never opened the skills.)*

   **The structural fix, once you find the drift: make docs POINT, don't RE-TYPE.** Audit the rotted
   set and you'll find nearly every false claim is a constant that already exists in config or a
   schema — a model name, a bucket, a threshold, a field list — copied into prose where nothing can
   ever check it. This is the **no-hardcoding rule aimed at documentation**: a re-typed constant in a
   doc is the same defect as a magic number in source, minus the compiler. So cite the source of
   truth (`see platform.yaml llm.*`, `see schemas/brief.py`) instead of restating its values, and
   where a claim must be stated, pin it with a **parity test** that reads both sides. *(Real
   instance: in a 21-skill audit, 14 were stale and **every** model/storage error was a re-typed
   config value; the only two skills that survived were the two that pointed at a doc rather than
   restating it.)*

## Step 3 — Report + record
Give an honest verdict: **on-track**, or a specific list of drifts. For each, recommend a **cut**, a
**deliberate re-scope** (add to Scope with a trigger), or a **fix**. On any confirmed drift, write a
dated row to `PRODUCT.md#Drift log` (its own section) **when a `PRODUCT.md` exists**; otherwise report
to the user and offer to append to the project's log/CHANGELOG — never silently create a `PRODUCT.md`.
(No phase write, no handoff — it's a check, not a stage.)

**Tier-3 (code-only) verdict:** say plainly *"no spine doc exists, so I can't assess scope/vision
drift — there's no recorded intent to compare against."* Give the INFERRED summary, then recommend
bootstrapping a spine (`/vision`+`/scope`, or a minimal `PRODUCT.md`/`CLAUDE.md`). Do **not** report
"on-track" (there's nothing to be on-track *against*) and do **not** fabricate drift.

## Step 3b — Self-verify
**If you reported "on-track" without actually cross-checking the build against OUT-OF-SCOPE, redo it** —
a rubber-stamp drift check is worse than none.
