---
name: plan
description: >
  Phase 1 (Product) of product-playbook. Turn the locked scope into a core-first phased plan —
  milestones, a rough timeline, and a testable exit criterion per milestone. Use after /scope,
  or run /plan "make a roadmap", "how do we sequence this", "milestones". Writes the Plan
  section of PRODUCT.md. Run /architect next (start of Development).
---

# `/plan` — Phase 1 · Product · run as a **product planner**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per PRINCIPLES.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing here: **per-feature contract (testable "done")**,
> **defer until a real trigger**, **docs-driven**.

## Contract
- **Purpose:** sequence the work core-first, each milestone with a testable exit criterion.
- **Reads:** `PRODUCT.md#Vision`, `#Scope`.
- **Writes:** `PRODUCT.md#Plan` — fields: phases/milestones (core first) · timeline · exit criteria per milestone.
- **Exit criteria:**
  - [ ] Milestones ordered **core-first** (the core feature ships before nice-to-haves).
  - [ ] A rough timeline (relative is fine: M1, M2… or weeks).
  - [ ] **Every milestone has a testable exit criterion** (a definition of done you could verify).
  - [ ] Out-of-scope items remain out (referenced, not scheduled).
  - [ ] A **concern-area coverage checklist** (security · ai-specific · observability · developer-experience · testing · infra · documentation · product) — each marked **now / next / later / N-A** with a trigger.

## Step 0 — Context + prior-gate check
- Read `#Vision` and `#Scope`. If `#Scope` is missing/empty, warn and offer `/scope` first (allow override).

## Step 1 — Apply principles (this phase)
- **Core-first:** the first milestone delivers the one core feature end-to-end (a thin vertical slice),
  not horizontal layers. **Testable "done":** no milestone is "build X" — it's "X works such that <observable>".
- **Defer:** anything in OUT-OF-SCOPE stays unscheduled until its trigger.

## Step 2 — Guided planning
1. **Slice the core feature into a thin end-to-end milestone** (M1): the smallest thing a user can actually do.
2. **Sequence the rest core-first:** what must exist for M1; what builds on it (M2, M3…). Keep it short.
3. For **each milestone**, write a one-line **exit criterion** — an observable, testable "done".
4. Add a **rough timeline** (relative is fine). Flag any milestone that needs paid infra and record the trigger.
5. **Concern-area coverage:** walk the production-readiness areas in `PRINCIPLES.md` (security, ai-specific, observability, DX, testing, infra, documentation, product) and mark each now / next / later / N-A with a trigger — so nothing is missed by accident (a product-grade, interview-worthy artifact).
- Optionally compose `/doc-create` to scaffold a fuller `ROADMAP.md`; keep `PRODUCT.md#Plan` as the summary.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Plan`: phases/milestones (core-first) · timeline · exit criteria per milestone.

## Step 3b — Self-verify (completeness gate)
Check the boxes. **If any milestone lacks a testable exit criterion, STOP and add one** — a milestone
without a verifiable "done" is where "is it finished?" arguments come from.

## Step 4 — Handoff
"Plan set, core-first, each milestone with a testable done. Development starts next: run **`/architect`**
to choose the stack + tools before you lay out folders."
