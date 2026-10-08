---
name: scope
description: >
  Phase 1 (Product) of product-playbook. Lock the ONE core feature that delivers the core
  value, and write an explicit OUT-OF-SCOPE list so the product does not drift. Use after
  /vision, or run /scope "what should the MVP be", "we keep adding features", "cut scope".
  Writes the Scope section of PRODUCT.md. Run /plan next. This is the anti-scope-creep skill.
---

# `/scope` — Phase 1 · Product · run as a **product manager**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **`status.py next --phase scope` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it); the rest of the close prints when `set scope filled` passes. Load-bearing here: **scope discipline**, **vision-alignment**,
> **defer until a real trigger**, **plain-language one-recommendation**.

## Contract
- **Purpose:** force a single core feature and an explicit, defended OUT-OF-SCOPE list.
- **Reads:** `PRODUCT.md#Vision` and `#Validation`'s state, as `next` prints them.
- **Writes:** `PRODUCT.md#Scope` — fields: THE core feature · in-scope (now) · Deferred (+trigger) · Non-goals (never) · Table stakes · `docs/scope.md`.
- **Gate type:** `input` — what gets cut is a preference no prior section encodes. **Never batched** - skipping it fabricates the product's premise. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Scope` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Companion:** `docs/scope.md` — the reasoning, workings and raw notes. `PRODUCT.md#Scope` stays a
  RECORD (summary · decision · evidence · pointer) — no byte cap; reasoning moves, answers stay.
- **Exit criteria:**
  - [ ] Exactly **one** core feature named (the thing that, alone, delivers the core value). → `THE core feature`
  - [ ] A short in-scope list, each item tied to the vision's value proposition **and** naming the north-star input it moves. → `In scope (now)`
  - [ ] A **non-empty Deferred list**, each item with the **trigger** that would bring it in — **and** a **Non-goals** list (things we deliberately will *never* build). → `Deferred (out for now` · `Non-goals`
  - [ ] Each in-scope item traces to a customer outcome, not a feature wish. → `In scope (now)`
  - [ ] **The table-stakes checklist is fully sorted** — every item explicitly **in-scope now**, **Deferred (with trigger)** or **N/A (with reason)**. **No item may be left unsorted**: an unsorted item fails this gate, because these are the things nobody proposes and everybody expects. → `Table stakes`
  - [ ] **Every number is the owner's or marked** — a number `#Vision` does not hold says `(proposed)` or `(owner)`. → `Deferred (out for now` · `In scope (now)`
  - [ ] `#Scope` is a **RECORD** — every field is a decision, evidence line or pointer; the reasoning is
    in `docs/scope.md`. Size is reported, never trimmed to. → `Detail:`
  - [ ] **Every companion opened is receipted** — one line per file, quoting a fragment that
    occurs verbatim in it. → `Read (file · date · verbatim quote)`

## Step 0 — Context + prior-gate check
- **First turn, ONE command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase scope`** — it prints the start and this phase's rules; never the rule files or `PRODUCT.md` whole: the start prints what `/scope` needs from them. Show its first line; close by its checklist.
- `#Vision` empty (the start says so) → warn: "`/vision` looks incomplete — scope without
  a vision drifts." Offer to run `/vision` first, but allow override (standalone use).
- `#Validation` **running** → **advisory, not blocking**: proceed **provisionally**, mark every scope decision that depends on the pending result `provisional`, and say the mark
  clears when the result lands. It **blocks from `/architect`
  onward**, where the cost of being wrong is real.
- `#Validation` **empty** is normal (`/validate` is optional) — no warning, no override. Carry `#Vision`'s
  riskiest assumption into the scope discussion, marked **untested**, so the core feature is chosen with
  that risk visible. A `#Validation` result (a verdict, or an override) shapes the scope as recorded.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then record it — `status.py bypass --from scope --gate <gate> --reason "<the user's own words>"` (`MECHANISMS.md` §Status) — before continuing.
- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** a filled section → follow the `RE-RUN` line `next` prints: **one question listing what would change**, never a silent overwrite; a reversed decision keeps a dated `superseded <date>: <why>` line.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** record it — `status.py set scope declined --reason "<what was missing>" --gate <the phase(s) that fill it>` (`MECHANISMS.md` §Status) — and change nothing in `PRODUCT.md`.

## Step 1 — Apply principles (this phase)
- **Scope discipline:** the default answer to a new feature is **"not yet — what's the trigger?"**
- **Vision-alignment:** every in-scope item must serve the value proposition; if it doesn't, it's out.
- **Defer until a real trigger** (incl. paid infra): record the condition that would pull it in.

## Step 2 — Guided scoping
Tell the user what to expect: two rounds, then one recommendation. **Each round is ONE message or form** (`CAPABILITIES.md` §Ask the user a question with options): **round 1, questions 1–3; round 2, question 4's proposed verdicts, question 5, the recommendation and the drafts.** Few possible answers: offer 2–4 choices. **Write the user's words** — the core feature, the items and the triggers as they said them, never wider or narrower. **A number you suggest is marked `(proposed)`**; one the user gave is `(owner)`.
1. **If you could ship only ONE capability and nothing else, what is it?** → that's the core feature.
   Push back if they name three; help them pick the one that delivers the core value alone.
2. **What's the smallest set around it that makes that core usable?** → the in-scope (now) list. Keep it ruthless.
3. **What are you tempted to add that is NOT needed for the core?** If the user is unsure, prompt with the
   usual creep categories — auth/multi-user, admin dashboard, integrations, mobile, analytics, settings.
   Sort each into **Deferred** (with the **trigger/signal** that would justify it) or **Non-goal** (never).
4. **Walk the table-stakes checklist** — the boring items nobody proposes and everybody expects.
   `next` prints the list for this product: the base list, the rules that apply and the languages, plus the
   AI items for an AI product and the agent items for an agent. Propose a verdict for each in one block; the
   user confirms or changes it. Sort **every** one into **in-scope now / Deferred
   (+trigger) / N-A (+reason)**, one line each: `<item>: in now` · `<item>: deferred - when <trigger>` · `<item>: N/A - <reason>`.
   **Adapt the list to the product kind** — an account-less CLI has no password reset (N-A: "no accounts"),
   but it still has error states and a licence. Adapting the list is expected; leaving an item unsorted is not.
5. Tie each in-scope item to **a customer outcome** (what the user can now do), not a feature name — and name the north-star input it moves.

Round 2 ends with **one recommendation** on the tightest viable core, any clash with `#Vision` or `#Validation` (Step 3c: name both sides, ask which wins), and *"Anything to change? If not: Save this version of your project? (yes / no)"* - either answer records it; never a turn of its own.

## Step 3 — Write back to `PRODUCT.md`
After the answer, **ONE message, both writes**: `docs/scope.md` (reasoning; the user's answers word for word under `## Owner's answers`) and, in a scratch file outside the repo, the fields `next` printed: THE core feature (one line) · in-scope (now) · Deferred (+ trigger) · Non-goals (never) · **Table stakes** (each in / deferred+trigger / N-A+reason); then `status.py set scope filled --section-from <file> --commit "<one line>"` (no `--commit` on a no).

## Step 3b — Self-verify (completeness gate)
`set scope filled` refuses the countable gaps `next` listed, every problem in one list: fix what it names, never
the check. **If the Deferred list is empty, or there are no Non-goals, STOP** — an empty
out-of-scope list is how products drift. Push the user to name at least the obvious temptations
(sorted into deferred-with-trigger vs never).

**Receipts and size** (`MECHANISMS-ON-DEMAND.md §Section is a record`, `MECHANISMS-ON-DEMAND.md §Read receipt`): `set` writes the `Read:` line and the size line; only an input file you opened yourself gets a quote. Reasoning moves into the companion, never trim to a number.

**Close the loop (`MECHANISMS.md` §Step 3b):** the checklist `set scope filled` prints: the save was the yes (`MECHANISMS.md` §Commit the work); **run the transition guard** (§Step 3b, item 4): a verdict per exit criterion, `UNVERIFIED` is normal, silence is not; **close in plain language** (`MECHANISMS.md` §Plain-language close): **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next**, ending with its `Open a NEW conversation` line word for word.

## Step 3c — Contradiction check (in round 2, before the yes; the close's step 3 confirms it)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Vision` (customer · job-to-be-done · north star) and `#Validation`'s verdict — a core feature that serves nobody in `#Vision`, or scope written as if a failed validation had passed. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Reopening a Non-goal later (the reversal protocol)
A Non-goal is "never *for this product's vision*", not "never discussable." The owner may reverse
one when the world changes (a competitor makes it table stakes, the buyer demands it). When that
happens, the move is an **explicit recorded reversal, never silent drift**:
1. **Record the decision** — date, who decided, and the *reason the world changed* — in the spine
   (`PRODUCT.md`: strike the Non-goal line with a pointer, add it to Deferred or scope) and in the
   feature's design doc header.
2. **Re-sort, don't just delete** — a reversed Non-goal usually lands in **Deferred with a trigger**
   (e.g. "design doc + benchmark done"), not straight into scope.
3. **Check the blast radius** — a reversal is often a *new capability track*, not a sub-item of the
   feature that prompted it. Name it separately so its true size is visible.
If the assistant notices work quietly contradicting a Non-goal without this protocol, that is
drift — surface it (`/drift-check` treats an unrecorded reversal as a finding, not a decision).

## Step 4 — Handoff
"Scope locked — one core feature, with an explicit out-of-scope list. `/drift-check` will hold you to
it later. Next run **`/plan`** to sequence the build core-first."
