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
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **`status.py next --phase plan` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it); the close's sections print when `set plan filled` passes. Load-bearing here: **per-feature contract (testable "done")**,
> **defer until a real trigger**, **docs-driven**.

## Contract
- **Purpose:** sequence the work core-first, each milestone with a testable exit criterion.
- **Reads:** `PRODUCT.md#Vision`, `#Scope`, `#Validation` — as `next` prints them.
- **Writes:** `PRODUCT.md#Plan` — every field `next` prints · `docs/plan.md` (the user's answers word for word + the reasoning).
- **Gate type:** `input` — the timeline and the ordering are the user's constraints. **Never batched** - skipping it fabricates the product's premise. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Plan` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Companion:** `docs/plan.md` — the reasoning, workings and raw notes. `PRODUCT.md#Plan` stays a
  RECORD (summary · decision · evidence · pointer) — no byte cap; reasoning moves, answers stay.
- **Exit criteria:**
  - [ ] Milestones ordered **core-first** (the core feature ships before nice-to-haves). → `Phases / milestones (core first)`
  - [ ] A rough timeline (relative is fine: M1, M2… or weeks) built on the user's capacity and start date. → `Timeline`
  - [ ] **Every milestone has a testable exit criterion** (a definition of done you could verify) that is
    also **reachable** — every prerequisite it implies (a deployed URL, credentials, seeded or real data,
    a device, another person) is delivered by a milestone in this plan, or the criterion is weakened. → `Exit criteria per milestone`
  - [ ] **Every milestone carries a four-risks row** — which of **value · usability · feasibility · viability** it retires, and how you will know. → `Four-risks row per milestone`
  - [ ] **At least one pre-public milestone has a usability exit criterion** — even five people attempting the core task unaided. Usability is the risk discovered *after* launch, when it is most expensive to fix. → `Usability checkpoint before going public`
  - [ ] A risk already retired **cites its evidence** (a `#Validation` result, a prior milestone) instead of repeating the work; `#Validation` empty → a milestone retires value. → `Four-risks row per milestone`
  - [ ] Out-of-scope items remain out (referenced, not scheduled). → `Phases / milestones (core first)`
  - [ ] A **concern-area coverage checklist** (security · ai-specific · observability · developer-experience · testing · infra · documentation · product) — each marked **now / next / later / N-A** with a trigger. → `Concern-area coverage`
  - [ ] **Every number is the user's or marked** — from the answers or the spine, else `(proposed)` or `(derived: <sum>)`. → `Exit criteria per milestone` · `Timeline`
  - [ ] `#Plan` is a **RECORD** — every field is a decision, evidence line or pointer; the reasoning and the user's answers word for word are
    in `docs/plan.md`. Size is reported, never trimmed to. → `Detail:`
  - [ ] **Every companion opened is receipted** — one line per file, quoting a fragment that
    occurs verbatim in it; only `PRODUCT.md` read → `Read: none - only PRODUCT.md sections`. → `Read (file · date · verbatim quote)`

## Step 0 — Context + prior-gate check
- **One first command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase plan`** — it prints the spine facts, the `#Plan` fields and the rules; never open those files or `PRODUCT.md` whole. Show its first line.
- `#Scope` missing/empty → warn and offer `/scope` first (allow
  override). **A `running` gate upstream is advisory here** (`STATE-MODEL.md` §2a) — plan
  provisionally, mark the milestones that depend on the pending result, and note that it blocks from
  `/architect` on.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then record it — `status.py bypass --from plan --gate <gate> --reason "<the user's own words>"` (`MECHANISMS.md` §Status) — before continuing.
- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** a filled section → follow the `RE-RUN` line `next` prints: **one question listing what would change**, never a silent overwrite; a reversed decision keeps a dated `superseded <date>: <why>` line.
- **The gate is unmet and the run stops here (`MECHANISMS.md` §Declined runs):** `status.py set plan declined --reason "<what was missing>" --gate <the phase(s) that fill it>` (`MECHANISMS.md` §Status) — and change nothing in `PRODUCT.md`.

## Step 1 — Apply principles (this phase)
- **Core-first:** the first milestone delivers the one core feature end-to-end (a thin vertical slice),
  not horizontal layers. **Testable "done":** no milestone is "build X" — it's "X works such that <observable>".
- **Defer:** anything in OUT-OF-SCOPE stays unscheduled until its trigger.
- **The user's words:** who builds it, the dates, the order and the north star stay as the user gave them; a number you suggest is `(proposed)` until the user gives their own.

## Step 2 — Guided planning
**Two rounds, each ONE message or form** (`CAPABILITIES.md` §Ask the user a question with options). **Round 1: these three together; draft no milestone or date before the answers**, each with 2–4 ready choices · **1.** who builds it, and how many hours a week · **2.** the start date (a running experiment: after its due date) · **3.** what follows the core, in order (propose one, marked yours). **Round 2: the draft** (steps 1–7) with **4.** if the plan ends after the north-star date `next` printed — keep it and flag it, move it, or lower the interim bar; any clash with `#Scope` (Step 3c: name both sides, ask which wins); and *"Anything to change? If not: Save this version of your project? (yes / no)"* - either answer records it; never a turn of its own.
1. **Slice the core feature into a thin end-to-end milestone** (M1): the smallest thing a user can actually do.
2. **Sequence the rest core-first:** what must exist for M1; what builds on it (M2, M3…). Keep it short. An **agent** (`Agent: yes`) launches in stages: approval first, then unchecked, with a stop switch before anything goes public.
3. For **each milestone**, write a one-line **exit criterion** — an observable, testable "done" — and
   then check it is **REACHABLE**, which is a different question. Testable asks *could you verify it*;
   reachable asks *does anything in this plan produce what verifying it requires*. Write
   `Needs: <prerequisite> (<the milestone or person that delivers it>)` for each one the criterion implies — **a deployed URL, credentials, seeded or real data, a physical
   artefact, a second device, another person**. **A public
   URL is delivered by `/deploy`**, so a milestone that needs one schedules that phase rather than
   assuming it. Nothing
   delivers it → **schedule it, or weaken the criterion.** (case file: The URL nobody scheduled)
4. **Add the four-risks row to each milestone.** The four product risks are **value** (do they want it),
   **usability** (can they use it), **feasibility** (can we build it) and **viability** (can the business
   sustain it) — a plan that sequences only feasibility has three blind spots. For each milestone, name which
   risks it retires and the observable that proves it. Where a risk is **already retired**, point at the
   evidence — a passing `#Validation` result retires value; don't re-run it. `#Vision` is a claim, never evidence; `#Validation` empty (it is optional) → value is untested, so a milestone retires it. **Put a usability checkpoint
   before anything goes public**, written as a milestone exit criterion, not a nice-to-have.
5. Add a **rough timeline** from answers 1 and 2; a duration you work out is `(derived: <hours> ÷ <hours a week>)`. Ends after the north-star date → a `North star:` line with answer 4. Flag any milestone that needs paid infra and record the trigger.
6. **Concern-area coverage:** walk the production-readiness areas `next` printed (security, ai-specific, observability, DX, testing, infra, documentation, product) and mark each now / next / later / N-A with a trigger.
   Each constraint `#Vision` names (a law such as GDPR, a language) gets its own line too: in a milestone now, or `later - when <trigger>`.
7. Show the draft (round 2); the user confirms or changes every `(proposed)` number — their own number goes into `## Owner's answers`.
- A fuller `ROADMAP.md` is optional; keep `PRODUCT.md#Plan` as the summary and the single source.

## Step 3 — Write back to `PRODUCT.md`
After the answer, **ONE message, both writes**: `docs/plan.md` (`## Owner's answers` word for word, then the reasoning) and every `#Plan` field `next` printed, labels as written, each milestone's line starting M1, M2…, in a scratch file outside the repo; then `status.py set plan filled --section-from <file> --commit "<one line>"` (no `--commit` on a no).

## Step 3b — Self-verify (completeness gate)
`set plan filled` refuses what a file shows, every problem in one list: fix what it names, never the check. **STOP and fix it with the user** when a milestone lacks a testable exit criterion, or a `Needs:` line names
nothing that delivers it — an unreachable criterion reads later as the milestone having failed rather than the plan.

**Receipts and size** (`MECHANISMS-ON-DEMAND.md §Section is a record`, `MECHANISMS-ON-DEMAND.md §Read receipt`): `set` writes both lines; an input file you opened yourself gets a quote, never `docs/plan.md`. Reasoning moves into the companion, never trim to a number.

**Close the loop (`MECHANISMS.md` §Step 3b):** the checklist `set plan filled` prints: the save was the yes (`MECHANISMS.md` §Commit the work); **run the transition guard** (§Step 3b, item 4): a verdict per exit criterion, `UNVERIFIED` is normal, silence is not; **close in plain language** (`MECHANISMS.md` §Plain-language close): **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next**, ending with its `Open a NEW conversation` line word for word.

## Step 3c — Contradiction check (in round 2, before the yes; the close's step 3 confirms it)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Scope` — every milestone traces to the core feature, and **no milestone delivers a recorded non-goal**. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Plan set, core-first, each milestone with a testable done. Development starts next: run **`/architect`**
to choose the stack + tools before you lay out folders."
