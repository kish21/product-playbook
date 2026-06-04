---
name: scope
description: >
  Phase 1 (Product) of product-builder. Lock the ONE core feature that delivers the core
  value, and write an explicit OUT-OF-SCOPE list so the product does not drift. Use after
  /vision, or run /scope "what should the MVP be", "we keep adding features", "cut scope".
  Writes the Scope section of PRODUCT.md. Run /plan next. This is the anti-scope-creep skill.
---

# `/scope` — Phase 1 · Product · run as a **product manager**

> Part of **product-builder**. Reads + updates the shared spine `PRODUCT.md`.
> Apply `PRINCIPLES.md` (bundled at `~/.claude/product-builder/PRINCIPLES.md`) — load-bearing here: **scope discipline**, **vision-alignment**,
> **defer until a real trigger**, **plain-language one-recommendation**.

## Contract
- **Purpose:** force a single core feature and an explicit, defended OUT-OF-SCOPE list.
- **Reads:** `PRODUCT.md#Vision`.
- **Writes:** `PRODUCT.md#Scope` — fields: THE core feature · in-scope (now) · OUT-OF-SCOPE (+ trigger).
- **Exit criteria:**
  - [ ] Exactly **one** core feature named (the thing that, alone, delivers the core value).
  - [ ] A short in-scope list, each item tied to the vision's value proposition.
  - [ ] A **non-empty OUT-OF-SCOPE list**, each item with the **trigger** that would bring it in later.
  - [ ] Each in-scope item traces to a customer outcome, not a feature wish.

## Step 0 — Context + prior-gate check
- Read `PRODUCT.md#Vision`. If it is missing/empty, warn: "`/vision` looks incomplete — scope without
  a vision drifts." Offer to run `/vision` first, but allow override (standalone use).

## Step 1 — Apply principles (this phase)
- **Scope discipline:** the default answer to a new feature is **"not yet — what's the trigger?"**
- **Vision-alignment:** every in-scope item must serve the value proposition; if it doesn't, it's out.
- **Defer until a real trigger** (incl. paid infra): record the condition that would pull it in.

## Step 2 — Guided scoping
Ask, one block at a time:
1. **If you could ship only ONE capability and nothing else, what is it?** → that's the core feature.
   Push back if they name three; help them pick the one that delivers the core value alone.
2. **What's the smallest set around it that makes that core usable?** → the in-scope (now) list. Keep it ruthless.
3. **What are you tempted to add that is NOT needed for the core?** → seed the OUT-OF-SCOPE list.
   For each, ask **"what real signal would make this worth building?"** and record that as the trigger.
4. Tie each in-scope item to **a customer outcome** ("user can X in minutes"), not a feature name.

Give **one recommendation** on the tightest viable core; get a yes/no.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Scope`: THE core feature · in-scope (now) · OUT-OF-SCOPE list (each with its trigger).

## Step 3b — Self-verify (completeness gate)
Check the boxes. **If the OUT-OF-SCOPE list is empty, STOP** — an empty out-of-scope list is how
products drift. Push the user to name at least the obvious temptations and their triggers.

## Step 4 — Handoff
"Scope locked — one core feature, with an explicit out-of-scope list. `/drift-check` will hold you to
it later. Next run **`/plan`** to sequence the build core-first."
