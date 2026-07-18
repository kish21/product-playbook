---
name: drift-check
description: >
  Cross-cutting skill of product-playbook — run ANYTIME. Checks whether the product is still building
  the vision or has drifted: scope creep (features built that are OUT OF SCOPE), vision misalignment,
  and code↔docs drift. Use when you suspect creep, before a milestone, or run /drift-check "are we
  on track", "did we drift", "scope creep", "is this still the plan". Reports against the project
  spine (PRODUCT.md, or the project's existing docs / inferred-from-code — see PRINCIPLES.md
  §Spine resolution); composes /doc-audit. Does not advance the phase chain.
---

# `/drift-check` — Cross-cutting · run as a **skeptical reviewer**

> Part of **product-playbook**. Reads the project spine — `PRODUCT.md`, or (for existing/brownfield
> projects) the project's own docs, or an inferred-from-code picture — and the codebase/docs.
> Resolve the spine per `PRINCIPLES.md` §Spine resolution.
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **vision-alignment (top priority)**, **scope discipline**,
> **no-drift / no-assumptions**, **docs match reality**, **verify against real code**.

> This is the seatbelt against the pain that motivated product-playbook: *"I started this product but
> slowly drifted out of control adding features which may not be required."* Run it often.

## Contract
- **Purpose:** detect and surface scope creep, vision drift, and code↔docs drift — early.
- **Reads:** the resolved spine's Vision, Scope (Deferred + Non-goals), Plan (concern-area checklist), Build log; the codebase + docs. (`PRODUCT.md#…` when it exists; otherwise the equivalent sections of the resolved doc, per PRINCIPLES.md §Spine resolution.)
- **Writes:** a drift report to the user + a dated row in `PRODUCT.md#Drift log` on any confirmed drift (its OWN section — never `/learn`'s `#Learnings`); does NOT advance the chain. **If there is no `PRODUCT.md`, do not create one** — report to the user and, if the project keeps a log/CHANGELOG, offer to append the drift note there.
- **Exit criteria:**
  - [ ] Built features cross-checked against `#Scope` — any OUT-OF-SCOPE item that got built is flagged as creep.
  - [ ] Current direction cross-checked against `#Vision` — misalignment surfaced.
  - [ ] Code↔docs drift checked (claims that don't match reality), composing `/doc-audit`.
  - [ ] A clear verdict: on-track, or a specific list of drifts + a recommended cut/correction.

## Step 0 — Resolve the spine, then build context
- **Resolve the spine first** (PRINCIPLES.md §Spine resolution): `PRODUCT.md` if present; else the
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
1. **Scope creep:** list features in the code/build log not justified by `#Scope`; flag anything built that's a **Non-goal** or a **Deferred** item whose trigger never fired. Also flag the inverse: a deliberate pivot the spine never recorded → recommend updating `#Scope`/`#Vision`, not cutting code.
2. **Vision drift:** is the current direction still serving `#Vision` and its north-star metric? Surface any quiet pivot.
3. **Plan / concern-area drift:** milestones skipped or reordered off core-first? Re-read `#Plan`'s concern-area checklist — any "now" still unbuilt, any "next" overdue?
4. **Doc drift:** compose **`/doc-audit`**; flag claims that don't match the code. If the `#Build log` itself is stale vs the code, flag that as drift too.
5. **Agent-instruction drift — the project's OWN skills/commands/`CLAUDE.md`.** These rot exactly like docs, but they are far more dangerous, because they are **executed, not read**: a stale `docs/` page misleads a human who can sanity-check it, while a stale `.claude/skills/*` is picked up and *acted on*. Check each skill's concrete, falsifiable claims against the code — file paths and directory layout, storage/vendor, model + provider, contract field names, stage list and count, and any "always/never do X" rule. Flag three things: claims that are **false**, skills that contradict **each other**, and skills that contradict a **locked decision** in the spine. *(Real instance: a project's three most task-relevant skills were each materially wrong — a stage documented as "no LLM, schema check only" that actually runs a vision judge; a contract listing fields deleted a session earlier plus a storage vendor the project had migrated off; and an "X is blocking" claim that inverted a locked blocking-vs-advisory split. Two also contradicted each other on whether a whole backend technology was permitted. Nobody had noticed, because sessions read the code directly and never opened the skills.)*

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
