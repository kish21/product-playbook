---
name: eval
description: >
  Phase 4 (Evaluation) of product-playbook. Judge whether the product is actually GOOD and hits its
  goal — measured against criteria, not assumed. Separates operational failures from genuine quality,
  and ends with an honest confidence score. Use after /test, or run /eval "is it good", "measure
  quality", "evaluate the output", "benchmark". Writes the Evaluation section of PRODUCT.md. For AI
  products, optionally composes /enterprise-ai-audit if installed. Run /ship next.
---

# `/eval` — Phase 4 · Evaluation · run as an **evaluator**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **measure-first**, **evidence-based**, **eval/benchmark
> integrity (separate operational-failure from quality)**, **honest confidence score**, **surface gaps**.

## Contract
- **Purpose:** measure whether the product meets its goal, honestly — quality, not just "it runs".
- **Reads:** `PRODUCT.md#Vision`, `#Scope`, `#Plan` (the goal), `#Tests`.
- **Writes:** `PRODUCT.md#Evaluation` — measured result · metrics + confidence · separated failures.
- **Gate type:** `verification` — measured against a recorded baseline. Batchable, and **stops on red** - a failing check ends the batch there. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes `#Evaluation` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Companion:** `docs/evaluation.md` — the reasoning, workings and raw notes. `PRODUCT.md#Evaluation` stays a
  RECORD (summary · decision · evidence · pointer), capped at ~5KB.
- **Exit criteria:**
  - [ ] A measurable definition of "good" tied to the vision/goal (a metric or a rubric) — **for a product with a north star, that definition IS `#Vision`'s target + date**, not a fresh rubric invented here. → `Is it good?`
  - [ ] **The guardrail metric is measured too, and reported alongside.** A north-star number that improved while the guardrail got worse is not a pass — say so plainly. → `Metrics + confidence score`
  - [ ] **Measured** against real or representative inputs (not asserted from vibes). → `Is it good?`
  - [ ] **Operational failures (errored/blocked/dropped) are separated** from genuine low quality. → `Operational failures`
  - [ ] An honest **confidence score (0–100%)** with solid / risky-untested / to-raise-it lines. → `Metrics + confidence score`
  - [ ] **Cost-per-run** captured (token/compute spend) where relevant; for AI, a **scoring-bias** check. → `Cost-per-run`
  - [ ] Result compared to a **recorded baseline** — a regression below threshold **fails** (gates as config, not hardcoded). → `Is it good?`
  - [ ] `#Evaluation` is a **RECORD**: the reasoning lives in `docs/evaluation.md`, and the section measures
    **under ~5KB**, measured after writing rather than assumed. → `Detail:`
  - [ ] **Every companion opened is receipted** — one line per file, quoting a fragment that
    occurs verbatim in it. → `Read (file · date · verbatim quote)`

## Step 0 — Context + prior-gate check
- Read `#Vision/#Scope/#Plan` for the goal and `#Tests` for what's covered.
- **Gate on the phases that come before this one.** If `#Tests` is empty or `#Dev-complete` still has
  unchecked boxes, **say which one is missing and offer the phase that fills it first** — `/dev-check`
  then `/test` — but allow override (standalone use). A product mid-Build has nothing to evaluate, and
  a score measured over an untested build reads as a quality verdict on work that was never claimed
  finished. *(A real run stopped here correctly — on judgement, because the skill never asked.)*
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then write `Override <date>: <reason> — bypassed <gate>` at the top of `#Evaluation` before continuing. Advancing on unmet criteria is the more consequential of warn-vs-override, so it is the one that leaves a trace: without it a later reader cannot tell a gate that held from a gate that was waved through.
- Take the **target + date**, the
  **input metrics** and the **guardrail** from `#Vision`'s north star — that is the measurement baseline, and
  the **instrumentation line** says how to read it. If the north star is a direction rather than a target,
  the goal is fuzzy: sharpen it with the user (or send them back to `/vision`) before measuring anything.
- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** if the section is already filled, **show what would change and ask before replacing it** — never a silent overwrite — and leave a reversed decision in place with a dated `superseded <date>: <why>` line. A first run over an empty section is unchanged.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** write ONE dated line at the top of `#Evaluation` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **Measure first:** judge against real/representative inputs; a scary or great number alike must be reproduced, not assumed (beware display/measurement artifacts).
- **Eval integrity:** an errored/blocked/dropped run is an *operational* failure — never score it as "low quality" or the metric lies. Count it separately.
- **Honesty:** surface gaps and weak spots plainly; do not round up.

## Step 2 — Evaluate
1. **Define "good":** the metric(s) or rubric that reflect the goal (e.g. accuracy, groundedness, latency, task success). For AI, compose **`/enterprise-ai-audit`** *if installed* — otherwise audit the same ground yourself and **say which you did** in the evidence line.
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

**Measure what you wrote and receipt what you read** (`MECHANISMS-ON-DEMAND.md §Section size`, `MECHANISMS-ON-DEMAND.md §Read receipt`): report the section and file size in one line, and move reasoning into the companion if the section is over ~5KB; write one `Read:` line per companion opened, each quoting a fragment that occurs verbatim in that file. A pointer nobody can prove was followed is how a phase invents what the artefact would have said.

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and **offer to commit the change** (`MECHANISMS.md` §Commit the work — check the repo exists, name the branch, offer the message, push only if a remote exists and the user says so). Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal. **Close in plain language** (`MECHANISMS.md` §Plain-language close): two or three sentences of *what just happened* with no playbook dialect, then a numbered *what YOU do next* — the user's own actions, dated where they are time-bound, or "Nothing — you're done".

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Vision`'s north star and `#Architecture`'s perf/cost budget — measuring a different metric than the one recorded, or a measured number that silently supersedes an ADR's budget. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Quality measured honestly, with a confidence score. Next run **`/ship`** — deep review, security
review, reconcile the docs, open the PR, and hand off."
