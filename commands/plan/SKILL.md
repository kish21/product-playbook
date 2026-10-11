---
name: plan
description: Order the work into milestones with dates and testable exit criteria.
---

# `/plan` — Phase 1 · Product · run as a **product planner**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **`status.py next --phase plan` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it); the close's sections print when `set plan filled` passes. Load-bearing here: **per-feature contract (testable "done")**,
> **defer until a real trigger**, **docs-driven**.

## Contract
- **Purpose:** sequence the work core-first, each milestone with a testable exit criterion.
- **Reads:** `PRODUCT.md#Vision`, `#Scope`, `#Validation` — as `next` prints them.
- **Writes:** ONE fields file; `set plan filled --from-fields` renders `PRODUCT.md#Plan` (the summary every later phase reads) and `docs/plan.md` (the whole plan, for a person) from it.
- **Gate type:** `input` — the timeline and the ordering are the user's constraints. **Never batched** - skipping it fabricates the product's premise. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Plan` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Companion:** `docs/plan.md` — the whole plan a person reads, rendered from the same fields as
  `PRODUCT.md#Plan`: each fact is typed once.
- **Exit criteria:**
  - [ ] Milestones ordered **core-first** (the core feature ships before nice-to-haves). → `Phases / milestones (core first)`
  - [ ] A rough timeline (relative is fine: weeks) built on the user's capacity and start date. → `Timeline`
  - [ ] **Every milestone has a testable exit criterion** (a definition of done you could verify) that is
    also **reachable** — every prerequisite it implies (a deployed URL, credentials, seeded or real data,
    a device, another person) is delivered by a milestone in this plan, or the criterion is weakened. → `Exit criteria per milestone`
  - [ ] **Every milestone carries a four-risks row** — which of **value · usability · feasibility · viability** it retires, and how you will know. → `Four-risks row per milestone`
  - [ ] **At least one pre-public milestone has a usability exit criterion** — even five people attempting the core task unaided. → `Usability checkpoint before going public`
  - [ ] A risk already retired **cites its evidence** (a `#Validation` result, a prior milestone) instead of repeating the work. → `Four-risks row per milestone`
  - [ ] Out-of-scope items remain out (referenced, not scheduled). → `Phases / milestones (core first)`
  - [ ] A **concern-area coverage checklist** (security · ai-specific · observability · developer-experience · testing · infra · documentation · product) — each marked **now / next / later / N-A** with a trigger. → `Concern-area coverage`
  - [ ] **Every number is the user's or marked** — from the answers or the spine, else in `Open items` or `(derived: <sum>)`. → `Exit criteria per milestone` · `Open items`
  - [ ] Every `#Scope` "in now" item sits in a milestone; schedule risks and a buffer are named. → `Exit criteria per milestone` · `Schedule risks`
  - [ ] `#Plan` is a **RECORD** — every field is a decision, evidence line or pointer; the reasoning and the user's answers word for word are
    in `docs/plan.md`. Size is reported, never trimmed to. → `Detail:`
  - [ ] **Every companion opened is receipted** — one line per file, quoting a fragment that
    occurs verbatim in it; only `PRODUCT.md` read → no `read` field (`none` is written). → `Read (file · date · verbatim quote)`

## Step 0 — Context + prior-gate check
- **One first command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase plan`** — it prints the spine facts, the plan's fields and the rules; never open those files or `PRODUCT.md` whole. Show its first line.
- **Anything unusual** (`#Scope` empty, a `running` gate upstream, a re-run of a filled `#Plan`, an override, a run that stops with the gate unmet): `next` prints the rule and the command for it only when it is true - follow it as printed.
  An override is recorded, never a verbal yes (`MECHANISMS.md` §Declined runs): the reason as options (Other = the user's own words), then `status.py bypass --from plan --gate <gate> --reason "<the picked option's words>"`. A running gate upstream is advisory here (`STATE-MODEL.md` §2a): mark the milestones that depend on it `provisional`; it blocks from `/architect` on.

## Step 1 — Apply principles (this phase)
- **Core-first:** M1 delivers the one core feature end-to-end (a thin vertical slice), not layers. **Testable "done":** no milestone is "build X" — it's "X works such that <observable>".
- **Defer:** anything in OUT-OF-SCOPE stays unscheduled until its trigger.
- **Never decide for the user:** capacity, dates, order and the north star are the user's answers or picked options; a number nobody gave goes to Open items.

## Step 2 — Guided planning
**One round, ONE message or form** (`CAPABILITIES.md` §Ask the user a question with options): every question 2–4 options + Recommended + Other. **Round 1: these together; draft no milestone or date before the answers** · **1.** capacity: `#Scope`'s `Capacity` to confirm (Recommended: as recorded); none recorded → ONE concrete question, people × hours a week (solo is an option) · **2.** the start date (a running experiment: after its due date) · **3.** what follows the core, in order · **4.** every number or list the plan needs that nobody gave (how many testers, which of `#Vision`'s moments, the demo date), each with `I don't know yet - keep it open`. **A second round only for a question an answer raised:** the plan ends after the north-star date `next` printed (keep and flag it, move it, or lower the interim bar), or a `#Scope` clash (Step 3c). No save question, never a save inside an option: the answers are the go-ahead to write and save; the close asks *"Change anything?"*.
1. **Slice the core feature into a thin end-to-end milestone** (M1): the smallest thing a user can actually do.
2. **Sequence the rest core-first:** what must exist for M1; what builds on it (M2, M3…). An **agent** (`Agent: yes`) launches in stages: approval first, then unchecked, with a stop switch before anything goes public.
3. For **each milestone**, write a one-line **exit criterion** — an observable, testable "done" — and
   then check it is **REACHABLE**: does anything in this plan produce what verifying it requires? Write
   `Needs: <prerequisite> (<the milestone or person that delivers it>)` for each one the criterion implies — **a deployed URL, credentials, seeded or real data, a physical
   artefact, a second device, another person**. **A public
   URL is delivered by `/deploy`**: schedule that phase. Nothing
   delivers it → **schedule it, or weaken the criterion.** (case file: The URL nobody scheduled)
4. **Add the four-risks row to each milestone.** The four product risks are **value** (do they want it),
   **usability** (can they use it), **feasibility** (can we build it) and **viability** (can the business
   sustain it). For each milestone, name which
   risks it retires and the observable that proves it. Where a risk is **already retired**, point at the
   evidence — a passing `#Validation` result retires value; don't re-run it. `#Vision` is a claim, never evidence; `#Validation` empty (it is optional) → value is untested, so a milestone retires it. **Put a usability checkpoint
   before anything goes public**, as an exit criterion.
5. Add a **rough timeline** from answers 1 and 2; a duration you work out is `(derived: <hours> ÷ <hours a week>)`. Ends after the north-star date → a `North star:` line. **Schedule risks + buffer:** what could slip, and the slack kept. **The AI model and its cost are chosen at `/architect`** (free local or paid API): never schedule a paid API or a key; a `#Vision` cost cap stays a cap. Other paid infra: flag it with its trigger.
6. **Concern-area coverage:** mark each area `next` printed now / next / later / N-A with a trigger.
   Each constraint `#Vision` names (a law such as GDPR, a language) gets its own line too: in a milestone now, or `later - when <trigger>`.
7. **Both directions:** every milestone traces to `#Scope`, and every `#Scope` "in now" item (core feature, in-scope items, table stakes in now) sits in an exit criterion. A `#Vision` list (moments, first users, targets) is copied exactly or the change named with its reason; kept in part → name what is in and out.
8. **Open items:** every number or point nobody decided, one line each with the recommended value — never a `(proposed)` scattered in the text.

## Step 3 — Write ONE fields file; the script renders both documents
After the answers, **ONE call: the fields `next` printed — `### <field>` and its text — in a scratch file outside the
repo** (never `docs/plan.md` or `PRODUCT.md` yourself, never a template): one `milestones` row per milestone, M1
first (M1's Delivers in 3–5 `;`-separated parts, later milestones 1–2 sentences), a `coverage` row per `#Scope` "in
now" item, the user's answers word for word. Then `status.py set plan filled --from-fields <file> --commit "<one line>"`
(`--no-commit` only when the user said not to save) renders `docs/plan.md` and `#Plan` from the same rows, checks and saves.

## Step 3b — Self-verify (completeness gate)
`set plan filled` refuses what a file shows, every problem in one list: fix what it names, never the check. **STOP and fix it with the user** when a milestone lacks a testable exit criterion, or a `Needs:` line names
nothing that delivers it.

**Receipts and size** (`MECHANISMS-ON-DEMAND.md §Section is a record`, `MECHANISMS-ON-DEMAND.md §Read receipt`): `set` writes both lines; an input file you opened yourself gets a quote in the `read` field, never `docs/plan.md`; never trim to a number; a warning after a passing `set` (a plain-words estimate) needs no re-run.

**Close the loop (`MECHANISMS.md` §Step 3b):** the checklist `set plan filled` prints: the save was the yes (`MECHANISMS.md` §Commit the work); **run the transition guard** (§Step 3b, item 4) in one line: what the save checked, what is judged (`UNVERIFIED` is normal, silence is not); **close in plain language** (`MECHANISMS.md` §Plain-language close), 6 lines in all, as `set` prints them: the guard line, then `Saved (commit ...).`, **What just happened** and **What I skipped or couldn't do** (one line each, the document linked, never restated), and **What YOU do next** as the last two lines word for word; **Test this yourself** is left out (nothing to test by hand here).

## Step 3c — Contradiction check (in round 2, before the yes; the close's step 3 confirms it)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Scope` — every milestone traces to the core feature, and **no milestone delivers a recorded non-goal**. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Plan set, core-first, each milestone with a testable done. Development starts next: run **`/architect`**
to choose the stack + tools before you lay out folders."
