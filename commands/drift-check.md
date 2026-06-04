---
name: drift-check
description: >
  Cross-cutting skill of product-builder — run ANYTIME. Checks whether the product is still building
  the vision or has drifted: scope creep (features built that are OUT OF SCOPE), vision misalignment,
  and code↔docs drift. Use when you suspect creep, before a milestone, or run /drift-check "are we
  on track", "did we drift", "scope creep", "is this still the plan". Reports against PRODUCT.md;
  composes /doc-audit. Does not advance the phase chain.
---

# `/drift-check` — Cross-cutting · run as a **skeptical reviewer**

> Part of **product-builder**. Reads the shared spine `PRODUCT.md` and the codebase/docs.
> Apply `PRINCIPLES.md` (bundled at `~/.claude/product-builder/PRINCIPLES.md`) — load-bearing: **vision-alignment (top priority)**, **scope discipline**,
> **no-drift / no-assumptions**, **docs match reality**, **verify against real code**.

> This is the seatbelt against the pain that motivated product-builder: *"I started this product but
> slowly drifted out of control adding features which may not be required."* Run it often.

## Contract
- **Purpose:** detect and surface scope creep, vision drift, and code↔docs drift — early.
- **Reads:** `PRODUCT.md#Vision`, `#Scope` (esp. OUT-OF-SCOPE), `#Plan`, `#Build log`; the codebase + docs.
- **Writes:** a drift report to the user (and optionally a note in `PRODUCT.md#Learnings`); does NOT advance the chain.
- **Exit criteria:**
  - [ ] Built features cross-checked against `#Scope` — any OUT-OF-SCOPE item that got built is flagged as creep.
  - [ ] Current direction cross-checked against `#Vision` — misalignment surfaced.
  - [ ] Code↔docs drift checked (claims that don't match reality), composing `/doc-audit`.
  - [ ] A clear verdict: on-track, or a specific list of drifts + a recommended cut/correction.

## Step 0 — Context
- Read `#Vision/#Scope/#Plan/#Build log`. Build the picture of what was *supposed* to be built.
- **Verify against the real code/docs** — don't assume the spine is current; reconcile it with what's actually there.

## Step 1 — Apply principles
- **Vision-alignment is top priority:** the test for every feature is "does this serve the vision?"
- **Scope discipline:** anything built that's in OUT-OF-SCOPE (without its trigger having fired) is creep.
- **Docs match reality:** a claim in the docs that the code doesn't support is drift too.

## Step 2 — Check for drift
1. **Scope creep:** list features present in the code/build log that are in (or not justified by) `#Scope`; flag OUT-OF-SCOPE items that were built without their trigger.
2. **Vision drift:** is the current direction still serving `#Vision`? Surface any quiet pivot.
3. **Plan drift:** are milestones being skipped or reordered away from core-first?
4. **Doc drift:** compose **`/doc-audit`**; flag claims that don't match the code.

## Step 3 — Report
Give an honest verdict: **on-track**, or a specific list of drifts. For each drift, recommend a cut,
a re-scope (add it to `#Scope` deliberately, with a trigger), or a correction. Optionally note it in
`#Learnings`. (This skill doesn't write phase sections or hand off — it's a check, not a stage.)

## Step 3b — Self-verify
**If you reported "on-track" without actually cross-checking the build against OUT-OF-SCOPE, redo it** —
a rubber-stamp drift check is worse than none.
