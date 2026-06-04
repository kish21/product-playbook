---
name: learn
description: >
  Phase 6 (Learn) of product-builder. After something ships, capture the success metric, run a short
  retro, and decide what to build next FROM EVIDENCE — re-checking against the vision so you don't
  drift. Use after a release lands, or run /learn "retro", "what next", "did it work", "post-launch".
  Writes the Learnings section of PRODUCT.md. Composes /loop or /schedule for recurring metric checks
  and /doc-audit for doc drift. Loops back to /scope or /plan for the next cycle.
---

# `/learn` — Phase 6 · Learn · run as a **product analyst**

> Part of **product-builder**. Reads + updates the shared spine `PRODUCT.md`.
> Apply `PRINCIPLES.md` (bundled at `~/.claude/product-builder/PRINCIPLES.md`) — load-bearing: **honesty**, **measure-first**, **vision-alignment re-check**,
> **defer until a real trigger**, **decide from evidence**.

## Contract
- **Purpose:** learn whether what shipped worked, and decide the next move from evidence — not gut.
- **Reads:** `PRODUCT.md#Vision`, `#Scope`, `#Eval`, `#Ship log`.
- **Writes:** `PRODUCT.md#Learnings` — success metric + result · retro · decided next (from evidence).
- **Exit criteria:**
  - [ ] A **success metric** named and its actual result captured (measured, not guessed).
  - [ ] A short retro: what worked · what to change.
  - [ ] A **next step decided from evidence**, re-checked against the vision (and against OUT-OF-SCOPE).
  - [ ] Any deferred item carries the **trigger** that would activate it.

## Step 0 — Context + prior-gate check
- Read `#Vision/#Scope/#Eval/#Ship log`. If nothing has shipped yet, this is premature — say so.

## Step 1 — Apply principles (this phase)
- **Measure, then decide:** base the next move on the metric, not enthusiasm. **Re-check the vision:** does the evidence still support the direction? **Defer:** don't pull OUT-OF-SCOPE items in without a real signal.

## Step 2 — Learn
1. **Metric:** what does success look like, and what did it actually do? For ongoing tracking, compose **`/loop`** or **`/schedule`** to re-measure on a cadence.
2. **Retro:** what worked, what to change (process + product). Keep it short and honest.
3. **Doc drift:** compose **`/doc-audit`** to confirm the docs still reflect reality.
4. **Decide next from evidence:** the highest-value next move; re-check it against the vision and the OUT-OF-SCOPE list. Record the trigger for anything deferred.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Learnings`: success metric + result · retro · decided-next (with the evidence and the trigger for deferrals).

## Step 3b — Self-verify (completeness gate)
Check the boxes. **If the next step isn't backed by evidence, or it quietly pulls in an OUT-OF-SCOPE
item without a trigger, STOP and reconsider** — that's how the next cycle starts drifting.

## Step 4 — Handoff
"Learnings captured and the next move is evidence-based. Start the next cycle: run **`/scope`** (or
**`/plan`**) for the next feature — and **`/drift-check`** anytime you suspect creep."
