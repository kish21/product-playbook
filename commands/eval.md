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
  - [ ] A measurable definition of "good" tied to the vision/goal (a metric or a rubric) — **for a product with a north star, that definition IS `#Vision`'s target + date**, not a fresh rubric invented here.
  - [ ] **The guardrail metric is measured too, and reported alongside.** A north-star number that improved while the guardrail got worse is not a pass — say so plainly.
  - [ ] **Measured** against real or representative inputs (not asserted from vibes).
  - [ ] **Operational failures (errored/blocked/dropped) are separated** from genuine low quality.
  - [ ] An honest **confidence score (0–100%)** with solid / risky-untested / to-raise-it lines.
  - [ ] **Cost-per-run** captured (token/compute spend) where relevant; for AI, a **scoring-bias** check.
  - [ ] Result compared to a **recorded baseline** — a regression below threshold **fails** (gates as config, not hardcoded).

## Step 0 — Context + prior-gate check
- Read `#Vision/#Scope/#Plan` for the goal and `#Tests` for what's covered. Take the **target + date**, the
  **input metrics** and the **guardrail** from `#Vision`'s north star — that is the measurement baseline, and
  the **instrumentation line** says how to read it. If the north star is a direction rather than a target,
  the goal is fuzzy: sharpen it with the user (or send them back to `/vision`) before measuring anything.
- **If the gate is unmet and the run stops here, record that it stopped (`PRINCIPLES.md` §Declined runs):** write ONE dated line at the top of `#Evaluation` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **Measure first:** judge against real/representative inputs; a scary or great number alike must be reproduced, not assumed (beware display/measurement artifacts).
- **Eval integrity:** an errored/blocked/dropped run is an *operational* failure — never score it as "low quality" or the metric lies. Count it separately.
- **Honesty:** surface gaps and weak spots plainly; do not round up.

## Step 2 — Evaluate
1. **Define "good":** the metric(s) or rubric that reflect the goal (e.g. accuracy, groundedness, latency, task success). For AI, compose **`/enterprise-ai-audit`**.
2. **Measure** against a representative set; record the numbers + how they were produced (so they're reproducible). **Re-measuring an aspirational overhead/latency budget?** Gate the **isolated** layer's delta — *not* the end-to-end number a noisy carried baseline (an fsync tail, GC, a slow neighbour) swamps; a **negative or wildly variable p95** is the tell you're measuring noise, not the layer (a category error). And **don't certify a single-digit-ms budget on a shared/dev box** — re-measure on a dedicated target (Linux/SSD CI) before quoting a canonical number. (This is the budget-*checking* half of `/architect`'s "set it aspirational + re-measure here".)
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

**Close the loop (`PRINCIPLES.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and end with a suggested one-line commit message in the repo's convention.

## Step 3c — Contradiction check (before the gate closes)
Per `PRINCIPLES.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Vision`'s north star and `#Architecture`'s perf/cost budget — measuring a different metric than the one recorded, or a measured number that silently supersedes an ADR's budget. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Quality measured honestly, with a confidence score. Next run **`/ship`** — deep review, security
review, reconcile the docs, open the PR, and hand off."
