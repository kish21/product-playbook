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
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **`status.py next --phase eval` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it); the close's sections print when `set eval filled` passes. Load-bearing here: **measure-first**, **evidence-based**, **eval/benchmark
> integrity (separate operational-failure from quality)**, **honest confidence score**, **surface gaps**.

## Contract
- **Purpose:** measure whether the product meets its goal, honestly — quality, not just "it runs".
- **Reads:** `PRODUCT.md#Vision`, `#Scope`, `#Plan` (the goal), `#Tests`, `#Architecture`'s budget — as `next` prints them.
- **Writes:** `PRODUCT.md#Evaluation` — measured result · metrics + confidence · separated failures.
- **Gate type:** `verification` — measured against a recorded baseline. Batchable, and **stops on red** - a failing check ends the batch there. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Evaluation` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Companion:** `docs/evaluation.md` — the reasoning, workings and raw notes; `#Evaluation` stays a RECORD.
- **Exit criteria:**
  - [ ] A measurable definition of "good" tied to the vision/goal (a metric or a rubric) — **for a product with a north star, that definition IS `#Vision`'s target + date**, not a fresh rubric invented here; a target readable only after launch is recorded `not readable until <date>` and the input metrics are measured now. → `Is it good?`
  - [ ] **The guardrail metric is measured too, and reported alongside.** A north-star number that improved while the guardrail got worse is not a pass — say so plainly. → `Metrics + confidence score`
  - [ ] **Measured** against real or representative inputs (not asserted from vibes). → `Is it good?`
  - [ ] **Operational failures (errored/blocked/dropped) are separated** from genuine low quality. → `Operational failures`
  - [ ] An honest **confidence score (0–100%)** with solid / risky-untested / to-raise-it lines. → `Metrics + confidence score`
  - [ ] **Cost-per-run** captured (token/compute spend) where relevant; for AI, a **scoring-bias** check. → `Cost-per-run`
  - [ ] Result compared to a **recorded baseline** — a regression below threshold **fails** (gates as config, not hardcoded). → `Is it good?`
  - [ ] `#Evaluation` is a **RECORD** — every field is a decision, evidence line or pointer; the reasoning is
    in `docs/evaluation.md`. Size is reported, never trimmed to. → `Detail:`
  - [ ] **Every companion opened is receipted** — one line per file, quoting a fragment that
    occurs verbatim in it. → `Read (file · date · verbatim quote)`

## Step 0 — Context + prior-gate check
- **One first command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase eval`** — it prints the spine lines, the gates, the dataset, the `#Evaluation` fields and the rules; never open `PRODUCT.md` whole. Show its first line.
- **Gate on the phases that come before this one** (the start prints both). `#Tests` or `#Dev-complete` not
  passed → **say which one is missing and offer the phase that fills it first** — `/dev-check`
  then `/test` — but allow override (standalone use). A product mid-Build has nothing to evaluate, and
  a score measured over an untested build reads as a quality verdict on work that was never claimed
  finished.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then record it — `status.py bypass --from eval --gate <gate> --reason "<the user's own words>"` (`MECHANISMS.md` §Status) — before continuing.
- The **target + date**, the **input metrics** and the **guardrail** from `#Vision`'s north star are the measurement baseline, and the **instrumentation line** says how to read it (the start prints them). A direction rather than a target: the goal is fuzzy — sharpen it with the user (or send them back to `/vision`) before measuring anything.
- **What this phase must NOT do:** change product code, config or tests — a gap found is a finding for a ticket.
- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** follow the `RE-RUN` line `next` prints — **one question listing what would change**, never a silent overwrite.
- **The gate is unmet and the run stops here (`MECHANISMS.md` §Declined runs):** `status.py set eval declined --reason "<what was missing>" --gate <the phase(s) that fill it>` — and change nothing in `PRODUCT.md`.

## Step 1 — Apply principles (this phase)
- **Measure first:** judge against real/representative inputs; a scary or great number alike must be reproduced, not assumed (beware display/measurement artifacts).
- **Eval integrity:** an errored/blocked/dropped run is an *operational* failure — never score it as "low quality" or the metric lies. Count it separately.
- **Honesty:** surface gaps and weak spots plainly; do not round up.

## Step 2 — Evaluate
1. **Define "good":** the metric(s) or rubric that reflect the goal (e.g. accuracy, groundedness, latency, task success). For AI, compose **`/enterprise-ai-audit`** *if installed*, **report only** — its audit and its report, never its fix step (it writes a Dockerfile, CI and code files unasked) — otherwise audit the same ground yourself and **say which you did** in the evidence line.
2. **Measure** against a representative set; record the numbers + how they were produced (so they're reproducible). **Re-measuring an aspirational overhead/latency budget?** Gate the **isolated** layer's delta — *not* the end-to-end number a noisy carried baseline (an fsync tail, GC, a slow neighbour) swamps; a **negative or wildly variable p95** is the tell you're measuring noise, not the layer (a category error). And **don't certify a single-digit-ms budget on a shared/dev box** — re-measure on a dedicated target (Linux/SSD CI) before quoting a canonical number.
3. **Separate failures:** tag operational failures distinctly; report a clean quality number + a separate failure count.
4. **Interpret honestly:** what's solid, what's weak, what's an artifact vs a real gap.

**Two rounds, each ONE message.** **Round 1, before measuring:** the start's numbered questions (inputs · baseline · a north star readable only after launch · a gate not passed). **Round 2, after measuring:** the result, the confidence, any Step 3c clash, and *"Anything to change? If not: Save this version of your project? (yes / no)"* as "Looks good - save (Recommended)" · "Change something".

## Step 3 — Write back to `PRODUCT.md`
After round 2, **ONE message, both writes**: `docs/evaluation.md` (the reasoning, the raw numbers, how to reproduce them) and every `#Evaluation` field `next` printed — the measured result + metrics, operational-failure count (separated), and a
**confidence score** (solid / risky-untested / to-raise-it) — in a scratch file; then `status.py set eval filled --verdict pass|fail --section-from <file> --commit "<one line>"` (no `--commit` on a no).

## Step 3b — Principle-gate: measured, not asserted (evidence)
**If the result is asserted rather than measured (reproducible — show how), not compared to a recorded baseline, or failures are blended
into the quality number, STOP and fix it** — an un-measured or contaminated number is worse than none.

`set eval filled` refuses what a file shows, every problem in one list (`--dry-run` lists them): fix what it names, never the check.

**Receipts and size** (`MECHANISMS-ON-DEMAND.md §Section is a record`, `MECHANISMS-ON-DEMAND.md §Read receipt`): `set` writes the size line and the `Read:` line; an input file you opened yourself gets a quote (`status.py quote <file> "<words>"`). Apply the record test to every field — reasoning moves into the companion, never trim to a number.

**Close the loop (`MECHANISMS.md` §Step 3b):** the checklist `set eval filled` prints, in order: reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it); the save was round 2's yes (`MECHANISMS.md` §Commit the work); **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not; **close in plain language** (`MECHANISMS.md` §Plain-language close): **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next**, ending with its `Open a NEW conversation` line word for word. **The close is the run's last message** — a composed skill's report is input to it, never the close itself.

## Step 3c — Contradiction check (in round 2, before the yes; the close's step 3 confirms it)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Vision`'s north star and `#Architecture`'s perf/cost budget — measuring a different metric than the one recorded, or a measured number that silently supersedes an ADR's budget. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Quality measured honestly, with a confidence score. Next run **`/ship`** — deep review, security
review, reconcile the docs, open the PR, and hand off."
