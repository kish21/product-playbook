---
name: plan
description: >
  Phase 1 (Product) of product-playbook. Turn the locked scope into a core-first phased plan —
  milestones, a rough timeline, and a testable exit criterion per milestone. Use after /scope,
  or run /plan "make a roadmap", "how do we sequence this", "milestones". Writes the Plan
  section of PRODUCT.md. Run /architect next (start of Development).
---

# `/plan` — Phase 1 · Product · run as a **product planner**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing here: **per-feature contract (testable "done")**,
> **defer until a real trigger**, **docs-driven**.

## Contract
- **Purpose:** sequence the work core-first, each milestone with a testable exit criterion.
- **Reads:** `PRODUCT.md#Vision`, `#Scope`.
- **Writes:** `PRODUCT.md#Plan` — fields: phases/milestones (core first) · timeline · exit criteria per milestone.
- **Gate type:** `input` — the timeline and the ordering are the user's constraints. **Never batched** - skipping it fabricates the product's premise. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes `#Plan` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Exit criteria:**
  - [ ] Milestones ordered **core-first** (the core feature ships before nice-to-haves).
  - [ ] A rough timeline (relative is fine: M1, M2… or weeks).
  - [ ] **Every milestone has a testable exit criterion** (a definition of done you could verify).
  - [ ] **Every milestone carries a four-risks row** — which of **value · usability · feasibility · viability** it retires, and how you will know. A plan that sequences only "can we build it" ships something buildable that nobody wants, nobody can use, or the business cannot sustain.
  - [ ] **At least one pre-public milestone has a usability exit criterion** — even five people attempting the core task unaided. Usability is the risk discovered *after* launch, when it is most expensive to fix.
  - [ ] A risk already retired **cites its evidence** (a `#Validation` entry, a prior milestone) instead of repeating the work.
  - [ ] Out-of-scope items remain out (referenced, not scheduled).
  - [ ] A **concern-area coverage checklist** (security · ai-specific · observability · developer-experience · testing · infra · documentation · product) — each marked **now / next / later / N-A** with a trigger.

## Step 0 — Context + prior-gate check
- Read `#Vision` and `#Scope`. If `#Scope` is missing/empty, warn and offer `/scope` first (allow override).
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then write `Override <date>: <reason> — bypassed <gate>` at the top of `#Plan` before continuing. Advancing on unmet criteria is the more consequential of warn-vs-override, so it is the one that leaves a trace: without it a later reader cannot tell a gate that held from a gate that was waved through.

- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** if the section is already filled, **show what would change and ask before replacing it** — never a silent overwrite — and leave a reversed decision in place with a dated `superseded <date>: <why>` line. A first run over an empty section is unchanged.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** write ONE dated line at the top of `#Plan` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **Core-first:** the first milestone delivers the one core feature end-to-end (a thin vertical slice),
  not horizontal layers. **Testable "done":** no milestone is "build X" — it's "X works such that <observable>".
- **Defer:** anything in OUT-OF-SCOPE stays unscheduled until its trigger.

## Step 2 — Guided planning
1. **Slice the core feature into a thin end-to-end milestone** (M1): the smallest thing a user can actually do.
2. **Sequence the rest core-first:** what must exist for M1; what builds on it (M2, M3…). Keep it short.
3. For **each milestone**, write a one-line **exit criterion** — an observable, testable "done".
4. **Add the four-risks row to each milestone.** The four product risks are **value** (do they want it),
   **usability** (can they use it), **feasibility** (can we build it) and **viability** (can the business
   sustain it) — a plan that sequences only feasibility has three blind spots. For each milestone, name which
   risks it retires and the observable that proves it. Where a risk is **already retired**, point at the
   evidence — a passing `#Validation` entry retires value; don't re-run it. **Put a usability checkpoint
   before anything goes public**, written as a milestone exit criterion, not a nice-to-have.
5. Add a **rough timeline** (relative is fine). Flag any milestone that needs paid infra and record the trigger.
6. **Concern-area coverage:** walk the production-readiness areas in `PRINCIPLES.md` (security, ai-specific, observability, DX, testing, infra, documentation, product) and mark each now / next / later / N-A with a trigger — so nothing is missed by accident (a product-grade, interview-worthy artifact).
- Optionally compose `/doc-create` to scaffold a fuller `ROADMAP.md`; keep `PRODUCT.md#Plan` as the summary.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Plan`: phases/milestones (core-first) · timeline · exit criteria per milestone · **the four-risks row
per milestone** (value/usability/feasibility/viability + how you'll know, or the evidence that retired it).

## Step 3b — Self-verify (completeness gate)
Check the boxes. **If any milestone lacks a testable exit criterion, STOP and add one** — a milestone
without a verifiable "done" is where "is it finished?" arguments come from.

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and end with a suggested one-line commit message in the repo's convention. Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal.

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Scope` — every milestone traces to the core feature, and **no milestone delivers a recorded non-goal**. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Plan set, core-first, each milestone with a testable done. Development starts next: run **`/architect`**
to choose the stack + tools before you lay out folders."
