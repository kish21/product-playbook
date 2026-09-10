---
name: learn
description: >
  Phase 6 (Learn) of product-playbook. After something ships, capture the success metric, run a short
  retro, and decide what to build next FROM EVIDENCE — re-checking against the vision so you don't
  drift. Use after a release lands, or run /learn "retro", "what next", "did it work", "post-launch".
  Writes the Learnings section of PRODUCT.md. Composes /loop or /schedule for recurring metric checks
  and /doc-audit for doc drift. Loops back to /scope or /plan for the next cycle.
---

# `/learn` — Phase 6 · Learn · run as a **product analyst**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **honesty**, **measure-first**, **vision-alignment re-check**,
> **defer until a real trigger**, **decide from evidence**.

## Contract
- **Purpose:** learn whether what shipped worked, and decide the next move from evidence — not gut.
- **Reads:** `PRODUCT.md#Vision`, `#Scope`, `#Evaluation`, `#Ship log`.
- **Writes:** `PRODUCT.md#Learnings` — success metric + result · retro · decided next (from evidence).
- **Gate type:** `input` — the metric is evidence, but iterate-or-kill is the user's call and is the phase's output. **Never batched** - skipping it fabricates the product's premise. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes `#Learnings` · `declined` ✓ · `override` ✓ · `superseded` n/a — append-only log: one entry per cycle
- **Exit criteria:**
  - [ ] A **success metric** named and its actual result captured (measured, not guessed).
  - [ ] A short retro: what worked · what to change.
  - [ ] A **next step decided from evidence**, re-checked against the vision (and against OUT-OF-SCOPE).
  - [ ] Any deferred item carries the **trigger** that would activate it.
  - [ ] The success metric is **actually instrumented** (events/analytics/dashboard), not back-of-envelope.
  - [ ] At least one **real user/usage signal** incorporated (support, interview, usage data).
  - [ ] **Kill/deprecate** is an allowed outcome — if the evidence says a feature isn't working, record the decision + trigger.
  - [ ] Ongoing **observability** (dashboards/alerting) + **cost** monitored — the post-launch watch, not a one-off.
  - [ ] **Reusable learning harvested:** any *generic* pattern, gotcha, or process fix surfaced this cycle is pushed back into the toolkit (a `product-toolkit` skill/scaffold, or a `product-playbook` phase skill) — or explicitly "nothing reusable this cycle". Generic learnings compound across future projects; project-specific ones stay in the project.

## Step 0 — Context + prior-gate check
- Read `#Vision/#Scope/#Evaluation/#Ship log`. If nothing has shipped yet, this is premature — say so.
- **If `#Evaluation` is empty, say so before drawing conclusions:** a retro written with no measured result
  is opinion, and the "decided next" line it produces carries that weight. Continue if the user wants, but
  label the basis honestly.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then write `Override <date>: <reason> — bypassed <gate>` at the top of `#Learnings` before continuing. Advancing on unmet criteria is the more consequential of warn-vs-override, so it is the one that leaves a trace: without it a later reader cannot tell a gate that held from a gate that was waved through.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** write ONE dated line at the top of `#Learnings` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **Measure, then decide:** base the next move on the metric, not enthusiasm. **Re-check the vision:** does the evidence still support the direction? **Defer:** don't pull OUT-OF-SCOPE items in without a real signal.

## Step 2 — Learn
1. **Metric (instrumented, not guessed):** confirm the north-star metric is actually measured (events/analytics/dashboard); report what it did. For ongoing tracking, compose **`/loop`** or **`/schedule`** to re-measure on a cadence.
2. **User signal:** incorporate at least one real user/usage signal (support, interview, usage data) — not just internal opinion.
3. **Retro:** what worked, what to change (process + product). Keep it short and honest.
4. **Doc drift:** compose **`/doc-audit`** to confirm the docs still reflect reality.
5. **Harvest reusable learnings into the toolkit:** ask "did this ticket teach something a *future project* would want?" — a recurring gotcha, a better default, a process gap (e.g. a missed `Closes #N`), a scaffold improvement. If yes, patch the right home and push it: **`product-toolkit`** (cross-project scaffolds/skills like `new-project`, `github-pr-flow`) or **`product-playbook`** (phase skills like this one). Keep project-specific facts in the project; only *generalisable* lessons graduate to the toolkit. This is automatic — don't wait to be asked.
6. **Decide next from evidence:** the highest-value next move — **build / iterate / KILL** (deprecating a feature the evidence says isn't working is a valid, healthy outcome). Re-check against the vision + Non-goals; record the trigger for anything deferred.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Learnings`: metric + result (instrumented) · user signal · retro · decided-next (build/iterate/kill, with evidence + triggers) · observability+cost watch.

## Step 3b — Self-verify (completeness gate)
Check the boxes. **If the next step isn't backed by evidence, or it quietly pulls in an OUT-OF-SCOPE
item without a trigger, STOP and reconsider** — that's how the next cycle starts drifting.

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and end with a suggested one-line commit message in the repo's convention. Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal.

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Vision`'s north star against what you measured, and next-cycle proposals against `#Scope`'s non-goals — 'what we learned we should build' is the most common way a non-goal comes back unrecorded. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Learnings captured and the next move is evidence-based. Start the next cycle: run **`/scope`** (or
**`/plan`**) for the next feature — and **`/drift-check`** anytime you suspect creep."
