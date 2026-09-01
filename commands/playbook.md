---
name: playbook
description: >
  The guided entry-point for product-playbook — run this to be walked through building a product
  phase-by-phase instead of remembering each skill. Use when starting fresh and unsure where to begin,
  or run /playbook "start", "guide me", "build a product", "what's next". Reads PRODUCT.md to see how
  far you've got and proposes the next phase; runs ONE phase at a time, pausing at each gate for your
  confirmation. It orchestrates the other skills — it does NOT auto-build or skip gates.
---

# `/playbook` — guided orchestrator · run as a **calm guide**

> Part of **product-playbook**. Reads the project spine (`PRODUCT.md`, or existing project docs — see PRINCIPLES.md §Spine resolution); orchestrates the phase skills.
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) —
> load-bearing here: **plain-language communication**, **one recommendation + confirm**, **never
> bypass a gate**.

> **What this is (and isn't):** a single "start here" that runs the phases in order and keeps you
> oriented. It is an **orchestrator, not an autopilot** — every phase still asks you its questions and
> still stops at its exit gate for your confirmation. `/vision` alone does **not** build the product;
> the chain does, one human-checked step at a time.

## Contract
- **Purpose:** walk a (possibly non-technical) user through the lifecycle one phase at a time.
- **Reads:** `PRODUCT.md` (which sections are filled = how far along).
- **Writes:** nothing itself — each phase skill writes its own section. `/playbook` only routes + explains.
- **Exit criteria:** the user always knows **where they are, what the next phase is, and why** — and no
  gate is ever skipped.

## Step 0 — Orient
- If there's no `PRODUCT.md`, this is a fresh start → the next phase is **`/vision`**.
- If `PRODUCT.md` exists, read which sections are filled and find the **first unfilled / incomplete
  phase** in order: Vision → Scope → Plan → Architect → Structure → **Design (if UI)** → Foundation →
  Contracts → Tickets → Build → Dev-check → Test → Eval → Ship → Learn. That's the next phase.
  *(Design = run `/design-system`; it fills `PRODUCT.md#Design`. **Skip it for backend/API/CLI products** —
  the has-UI flag from `/architect`/`/structure` decides.)*
- Brownfield (existing code, no `PRODUCT.md`): say so, and propose entering at `/architect` or `/build`.

## Step 1 — Explain the map (once, briefly, plain language)
Show the journey in one screen so the user has the mental model:
`vision → scope → plan` (Product) · `architect → structure → design-system* → foundation → contracts → tickets → build → dev-check` (*UI only)
(Development) · `test` · `eval` · `ship` · `learn` · `/drift-check` anytime. Note: each step asks a few
questions and ends with a check before moving on — you stay in control.

## Step 2 — Run the next phase (one at a time)
1. Tell the user the next phase in plain language: *what it does and why it matters now.*
2. **Invoke that phase's skill** (e.g. run `/vision`). Let it ask its questions and do its work.
3. When that skill reaches its **exit gate**, surface the result and **pause** — confirm with the user
   that it's right before continuing. **Never advance past an unmet gate.**
4. On confirmation, point to the next phase and repeat. The user can stop anytime and resume later by
   running `/playbook` again (it re-orients from `PRODUCT.md`).

## Step 3 — Anytime
Remind the user they can run **`/drift-check`** whenever they suspect scope creep, and that they can
also run any single phase skill directly (e.g. `/test`) without `/playbook`.

## Handoff
"You're set up to be guided. We'll do **one phase at a time**, checking each before moving on — run the
proposed next skill, or just keep running `/playbook` and I'll walk you through."
