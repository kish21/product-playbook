---
name: learn
description: >
  Phase 6 (Learn) of product-playbook. After something ships, capture the success metric, run a short
  retro, and decide what to build next FROM EVIDENCE — re-checking against the vision so you don't
  drift. Use after a release lands, or run /learn "retro", "what next", "did it work", "post-launch".
  Writes the Learnings section of PRODUCT.md. Composes /loop or /schedule for recurring metric checks.
  Loops back to /scope or /plan for the next cycle.
---

# `/learn` — Phase 6 · Learn · run as a **product analyst**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **`status.py next --phase learn` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it); the close's sections print at `set learn filled`. Load-bearing: **honesty**, **measure-first**, **vision-alignment re-check**,
> **defer until a real trigger**, **decide from evidence**.

## Contract
- **Purpose:** learn whether what shipped worked, and decide the next move from evidence — not gut.
- **Reads:** `PRODUCT.md#Vision`, `#Scope`, `#Evaluation`; the `STATUS.md` release rows — as `next` prints them.
- **Writes:** `PRODUCT.md#Learnings` — success metric + result · retro · decided next (from evidence).
- **Gate type:** `input` — the metric is evidence, but iterate-or-kill is the user's call and is the phase's output. **Never batched** - skipping it fabricates the product's premise. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Learnings` · `declined` ✓ · `override` ✓ · `superseded` n/a — append-only log: one entry per cycle
- **Companion:** `docs/learnings.md` — the reasoning, workings and raw notes; `#Learnings` stays a RECORD.
- **Exit criteria:**
  - [ ] A **success metric** named and its actual result captured (measured, not guessed). → `Success metric + result`
  - [ ] A short retro: what worked · what to change. → `Retro (what worked / what to change)`
  - [ ] A **next step decided from evidence**, re-checked against the vision (and against OUT-OF-SCOPE). → `Decided next`
  - [ ] Any deferred item carries the **trigger** that would activate it. → `Decided next`
  - [ ] The success metric is **instrumented** (events/analytics/dashboard), not back-of-envelope. → `Success metric + result`
  - [ ] At least one **real user/usage signal** incorporated (support, interview, usage data). → `User/usage signal incorporated`
  - [ ] **Kill/deprecate** is an allowed outcome — if the evidence says a feature isn't working, record the decision + trigger. → `Decided next`
  - [ ] Ongoing **observability** (dashboards/alerting) + **cost** monitored — the post-launch watch, not a one-off. → `Observability + cost watch in place`
  - [ ] `#Learnings` is a **RECORD** — every field is a decision, evidence line or pointer; the reasoning is
    in `docs/learnings.md`. Size is reported, never trimmed to. → `Detail:`
  - [ ] **Every companion opened is receipted** — one line per file, quoting a fragment that
    occurs verbatim in it. → `Read (file · date · verbatim quote)`

## Step 0 — Context + prior-gate check
- **One first command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase learn`** — it prints the spine lines, the release rows, the `#Learnings` fields and the rules; never open `PRODUCT.md` whole. Show its first line. Nothing shipped yet: premature — say so.
- **If `#Evaluation` is empty, say so before drawing conclusions:** a retro written with no measured result
  is opinion, and the "decided next" line it produces carries that weight. Continue if the user wants, but
  label the basis honestly.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then record it — `status.py bypass --from learn --gate <gate> --reason "<the user's own words>"` (`MECHANISMS.md` §Status) — before continuing.
- **The gate is unmet and the run stops here (`MECHANISMS.md` §Declined runs):** `status.py set learn declined --reason "<what was missing>" --gate <the phase(s) that fill it>` — and change nothing in `PRODUCT.md`.
- **What this phase must NOT do:** build or change code — it decides; the next cycle builds, from `/scope`.

## Step 1 — Apply principles (this phase)
- **Measure, then decide:** base the next move on the metric, not enthusiasm. **Re-check the vision:** does the evidence still support the direction? **Defer:** don't pull OUT-OF-SCOPE items in without a real signal.

## Step 2 — Learn
1. **Metric (instrumented, not guessed):** confirm the north-star metric is actually measured (events/analytics/dashboard); report what it did. For ongoing tracking, compose **`/loop`** or **`/schedule`** to re-measure on a cadence (other tools: the start's fallback).
2. **User signal:** incorporate at least one real user/usage signal (support, interview, usage data) — not internal opinion.
3. **Retro:** what worked, what to change (process + product). Keep it short and honest. A lesson worth keeping goes into this project's `docs/learnings.md`, where the next cycle reads it.
4. **Doc drift:** confirm the docs still reflect reality — trace each capability claim to the code, not to the last release note.
5. **Decide next from evidence:** the highest-value next move — **build / iterate / KILL** (deprecating a feature the evidence says isn't working is a valid, healthy outcome). Re-check against the vision + Non-goals; record the trigger for anything deferred.

**Two rounds, each ONE message.** **Round 1, before drafting:** the start's numbered questions (the metric's number and source · the user signal · what the owner already wants next). **Round 2:** the retro, the evidence and the proposed decision marked (proposed), any Step 3c clash, and *"Anything to change? If not: Save this version of your project? (yes / no)"* as "Keep as proposed - save (Recommended)" · "Change something" — the decision is the owner's.

## Step 3 — Write back to `PRODUCT.md`
After round 2, **ONE message, both writes**: `docs/learnings.md` (an earlier cycle under `## Cycle <date>`, word for word) and `#Learnings` — metric + result (instrumented) · user signal · retro · decided-next (build/iterate/kill, with evidence + triggers) · observability+cost watch — in a scratch file; then `status.py set learn filled --section-from <file> --commit "<one line>"` (no `--commit` on a no).

## Step 3b — Self-verify (completeness gate)
**If the next step isn't backed by evidence, or it quietly pulls in an OUT-OF-SCOPE
item without a trigger, STOP and reconsider** — that's how the next cycle starts drifting.

`set learn filled` refuses what a file shows, every problem in one list (`--dry-run` lists them): fix what it names. **Receipts and size** (`MECHANISMS-ON-DEMAND.md §Section is a record`, `MECHANISMS-ON-DEMAND.md §Read receipt`): `set` writes both lines; a file you opened yourself gets a quote. Reasoning moves into the companion, never trim to a number.

**Close the loop (`MECHANISMS.md` §Step 3b):** the checklist `set learn filled` prints: reconcile any number against `#Vision` (surface a contradiction, never write over it); the save was round 2's yes (`MECHANISMS.md` §Commit the work); **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not; **close in plain language** (`MECHANISMS.md` §Plain-language close): **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next**, ending with its `Open a NEW conversation` line word for word.

## Step 3c — Contradiction check (in round 2, before the yes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Vision`'s north star against what you measured, and next-cycle proposals against `#Scope`'s non-goals — 'what we learned we should build' is the most common way a non-goal comes back unrecorded. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Learnings captured and the next move is evidence-based. Start the next cycle: run **`/scope`** (or
**`/plan`**) for the next feature — and **`/drift-check`** anytime you suspect creep."
