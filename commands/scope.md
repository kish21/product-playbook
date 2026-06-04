---
name: scope
description: >
  Phase 1 (Product) of product-playbook. Lock the ONE core feature that delivers the core
  value, and write an explicit OUT-OF-SCOPE list so the product does not drift. Use after
  /vision, or run /scope "what should the MVP be", "we keep adding features", "cut scope".
  Writes the Scope section of PRODUCT.md. Run /plan next. This is the anti-scope-creep skill.
---

# `/scope` — Phase 1 · Product · run as a **product manager**

> Part of **product-playbook**. Reads + updates the shared spine `PRODUCT.md`.
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing here: **scope discipline**, **vision-alignment**,
> **defer until a real trigger**, **plain-language one-recommendation**.

## Contract
- **Purpose:** force a single core feature and an explicit, defended OUT-OF-SCOPE list.
- **Reads:** `PRODUCT.md#Vision`.
- **Writes:** `PRODUCT.md#Scope` — fields: THE core feature · in-scope (now) · Deferred (+trigger) · Non-goals (never).
- **Exit criteria:**
  - [ ] Exactly **one** core feature named (the thing that, alone, delivers the core value).
  - [ ] A short in-scope list, each item tied to the vision's value proposition **and** plausibly moving the north-star metric.
  - [ ] A **non-empty Deferred list**, each item with the **trigger** that would bring it in — **and** a **Non-goals** list (things we deliberately will *never* build).
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
3. **What are you tempted to add that is NOT needed for the core?** If the user is unsure, prompt with the
   usual creep categories — auth/multi-user, admin dashboard, integrations, mobile, analytics, settings.
   Sort each into **Deferred** (with the **trigger/signal** that would justify it) or **Non-goal** (never).
4. Tie each in-scope item to **a customer outcome** ("user can X in minutes"), not a feature name — and check it plausibly moves the north-star metric.

Give **one recommendation** on the tightest viable core; get a yes/no.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Scope`: THE core feature · in-scope (now) · Deferred (each with its trigger) · Non-goals (never).

## Step 3b — Self-verify (completeness gate)
Check the boxes. **If the Deferred list is empty, or there are no Non-goals, STOP** — an empty
out-of-scope list is how products drift. Push the user to name at least the obvious temptations
(sorted into deferred-with-trigger vs never).

## Step 4 — Handoff
"Scope locked — one core feature, with an explicit out-of-scope list. `/drift-check` will hold you to
it later. Next run **`/plan`** to sequence the build core-first."
