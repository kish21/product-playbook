---
name: eval
description: >
  Phase 4 (Evaluation) of product-playbook. Judge whether the product is actually GOOD and hits its
  goal — measured against criteria, not assumed. Separates operational failures from genuine quality,
  and ends with an honest confidence score. Use after /test, or run /eval "is it good", "measure
  quality", "evaluate the output", "benchmark". Writes the Evaluation section of PRODUCT.md. For AI
  products, composes /enterprise-ai-audit. Run /ship next.
---

# `/eval` — Phase 4 · Evaluation · run as an **evaluator**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per PRINCIPLES.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **measure-first**, **evidence-based**, **eval/benchmark
> integrity (separate operational-failure from quality)**, **honest confidence score**, **surface gaps**.

## Contract
- **Purpose:** measure whether the product meets its goal, honestly — quality, not just "it runs".
- **Reads:** `PRODUCT.md#Vision`, `#Scope`, `#Plan` (the goal), `#Tests`.
- **Writes:** `PRODUCT.md#Evaluation` — measured result · metrics + confidence · separated failures.
- **Exit criteria:**
  - [ ] A measurable definition of "good" tied to the vision/goal (a metric or a rubric).
  - [ ] **Measured** against real or representative inputs (not asserted from vibes).
  - [ ] **Operational failures (errored/blocked/dropped) are separated** from genuine low quality.
  - [ ] An honest **confidence score (0–100%)** with solid / risky-untested / to-raise-it lines.
  - [ ] **Cost-per-run** captured (token/compute spend) where relevant; for AI, a **scoring-bias** check.
  - [ ] Result compared to a **recorded baseline** — a regression below threshold **fails** (gates as config, not hardcoded).

## Step 0 — Context + prior-gate check
- Read `#Vision/#Scope/#Plan` for the goal and `#Tests` for what's covered. If the goal is fuzzy, sharpen it first.

## Step 1 — Apply principles (this phase)
- **Measure first:** judge against real/representative inputs; a scary or great number alike must be reproduced, not assumed (beware display/measurement artifacts).
- **Eval integrity:** an errored/blocked/dropped run is an *operational* failure — never score it as "low quality" or the metric lies. Count it separately.
- **Honesty:** surface gaps and weak spots plainly; do not round up.

## Step 2 — Evaluate
1. **Define "good":** the metric(s) or rubric that reflect the goal (e.g. accuracy, groundedness, latency, task success). For AI, compose **`/enterprise-ai-audit`**.
2. **Measure** against a representative set; record the numbers + how they were produced (so they're reproducible).
3. **Separate failures:** tag operational failures distinctly; report a clean quality number + a separate failure count.
4. **Interpret honestly:** what's solid, what's weak, what's an artifact vs a real gap.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Evaluation`: the measured result + metrics, operational-failure count (separated), and a
**confidence score** (solid / risky-untested / to-raise-it).

## Step 3b — Principle-gate: measured, not asserted (evidence)
Confirm: the number was **actually measured** against representative inputs (reproducible — show how);
it's compared to a **recorded baseline** and a regression **fails**; operational failures are counted
**separately** from quality. **If the result is asserted rather than measured, or failures are blended
into the quality number, STOP and fix it** — an un-measured or contaminated number is worse than none.

## Step 4 — Handoff
"Quality measured honestly, with a confidence score. Next run **`/ship`** — deep review, security
review, reconcile the docs, open the PR, and hand off."
