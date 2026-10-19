---
name: scope
description: Pick the one core feature; list what is in, later and never.
---

# `/scope` — Phase 1 · Product · run as a **product manager**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the variable is the folder two levels above this SKILL.md, holding `commands/` and `PRINCIPLES.md` - never another tool's install). If `python` will not start (not found, or a sandbox refuses it): the project's `.venv` Python, else `python3`, else `py -3` - never a hunt; later commands use the start's `Run this copy as` line.
> **This skill's OWN reference files are a DIFFERENT folder:** `references/` beside this SKILL.md, not the plugin-root one.
> **`status.py next --phase scope` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it); the rest of the close prints when `set scope filled` passes. Load-bearing here: **scope discipline**, **vision-alignment**,
> **defer until a real trigger**, **plain-language options with one Recommended**.

## Contract
- **Purpose:** force a single core feature and an explicit, defended OUT-OF-SCOPE list.
- **Reads:** `PRODUCT.md#Vision` and `#Validation`'s state, as `next` prints them.
- **Writes:** ONE fields file; `set scope filled --from-fields` renders `PRODUCT.md#Scope` (THE core feature · Capacity · in-scope (now) · Deferred (+trigger) · Non-goals (never) · Table stakes) and `docs/scope.md` from it.
- **Gate type:** `input` — what gets cut is a preference no prior section encodes. **Never batched** - skipping it fabricates the product's premise. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Scope` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Companion:** `docs/scope.md` — the story for people, rendered from the same fields as `PRODUCT.md#Scope`:
  each fact is typed once.
- **Exit criteria:**
  - [ ] Exactly **one** core feature named (the thing that, alone, delivers the core value). → `THE core feature`
  - [ ] A short in-scope list, each item tied to the vision's value proposition **and** naming the north-star input it moves. → `In scope (now)`
  - [ ] A **non-empty Deferred list**, each item with the **trigger** that would bring it in — **and** a **Non-goals** list (things we deliberately will *never* build). → `Deferred (out for now` · `Non-goals`
  - [ ] Each in-scope item traces to a customer outcome, not a feature wish. → `In scope (now)`
  - [ ] **The table-stakes checklist is fully sorted** — every item explicitly **in-scope now**, **Deferred (with trigger)** or **N/A (with reason)**. **No item may be left unsorted.** → `Table stakes`
  - [ ] **Every number is the owner's or marked** — `(proposed)`, `(owner)`, or carried from `#Vision` with where it came from. → `Deferred (out for now` · `In scope (now)`
  - [ ] **Capacity** asked in round 1, and the in-scope list fits it; each in-scope item has a **Done when**. → `Capacity` · `In scope (now)`
  - [ ] `#Scope` is a **RECORD** — every field is a decision, evidence line or pointer; the reasoning is
    in `docs/scope.md`. Size is reported, never trimmed to. → `Detail:`
  - [ ] **Every companion opened is receipted** — one line per file, quoting a fragment that
    occurs verbatim in it. → `Read (file · date · verbatim quote)`

## Step 0 — Context + prior-gate check
- **First turn, ONE command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase scope`** — it prints the start and this phase's rules; never the rule files or `PRODUCT.md` whole. Show its first line; close by its checklist.
- `#Validation` **empty** is normal (`/validate` is optional) — no warning, no override. Carry `#Vision`'s
  riskiest assumption in, marked **untested**, so the core feature is chosen with
  that risk visible. A `#Validation` result (a verdict, or an override) shapes the scope as recorded.
- **Anything unusual** (`#Vision` empty, `#Validation` running, a re-run of a filled `#Scope`, an override, a run that stops with the gate unmet): `next` prints the rule and the command for it only when it is true - follow it as printed.
  An override is recorded, never a verbal yes (`MECHANISMS.md` §Declined runs): the reason as options (Other = the user's own words), then `status.py bypass --from scope --gate <gate> --reason "<the picked option's words>"`. A running `#Validation` is advisory here (mark the scope decisions that depend on it `provisional`) and blocks from `/architect` on.

## Step 1 — Apply principles (this phase)
- **Scope discipline:** the default answer to a new feature is **"not yet — what's the trigger?"**
- **Vision-alignment:** every in-scope item must serve the value proposition; if it doesn't, it's out.
- **Defer until a real trigger** (incl. paid infra): record the condition that would pull it in.

## Step 2 — Guided scoping
Two rounds, then the save. **Each round is ONE message or form** (`CAPABILITIES.md` §Ask the user a question with options): **every question 2–4 options built from `#Vision` and the answers, Recommended first, plus Other.** **Every option is a complete answer** (never "specify your hours"); alternatives are one pick. **Never decide the core feature, the items or the triggers** — propose them as options; only what the user picks goes in (`picked: <option>` under `## Owner's answers`). **A number you suggest is marked `(proposed)`**; one the user gave is `(owner)`; one carried from `#Vision` says where it came from: `(from vision: owner's answer, not yet worked out)`.
**Round 1 — questions 1–4 together:**
1. **If you could ship only ONE capability and nothing else, what is it?** → that's the core feature.
   Push back on three; help them pick the one that delivers the core value alone.
2. **What's the smallest set around it that makes that core usable?** → the in-scope (now) list. Keep it ruthless.
3. **Which of these should stay OUT of the first version? You decide later or never for each next.** Options: the
   usual creep categories — auth/multi-user, admin dashboard, integrations, mobile, analytics, settings — and what `#Vision` invites.
4. **Who builds the first version, and how long do you have?** → `Capacity` (people × hours
   a week · weeks) as concrete options ("1 person, 8 h/week x 5 weeks (Recommended)" · another size · Other); `/plan` only confirms it.

**Round 2 — in ONE message, only what round 1 left open** (never capacity again, never an item round 1 did not keep out):
- **Each temptation from question 3 is its own question:** only the ones round 1 kept out — later, when `<proposed trigger>` · never — Recommended marked; the user decides each one.
- **Walk the table-stakes checklist** — the boring items nobody proposes and everybody expects.
   `next` prints the list for this product: the base list, the rules that apply and the languages, plus the
   AI items for an AI product and the agent items for an agent, and the engineering must-haves. Propose a verdict for each in one block; the
   user confirms or changes it. Sort **every** one into **in-scope now / Deferred
   (+trigger) / N-A (+reason)**, one `table stakes` row each: `| <item> | in now |` · `| <item> | deferred - when <trigger> |` · `| <item> | N/A - <reason> |`.
   **Adapt the list to the product kind** — an account-less CLI has no password reset (N-A: "no accounts"),
   but it still has error states and a licence.
- Tie each in-scope item to **a customer outcome** (what the user can now do), its **Done when** (a check anyone can run), and the north-star input it moves.
- **Does it fit** in <time> for <team>? When not, offer the cut as options.

Round 2 ends with **one recommendation** on the tightest viable core, any clash with `#Vision` or `#Validation` (Step 3c: name both sides, ask which wins, as options). No save question: the answers are the go-ahead to write and save; the close asks *"Change anything?"*.

## Step 3 — Write ONE fields file; the script renders both documents
After the answers, **ONE call: the fields `next` printed — `### <field>` and its text — in a scratch file outside the
repo** (never `docs/scope.md` or `PRODUCT.md` yourself, never a template): the core feature in one clear sentence,
one concrete example and the core-loop diagram, one row per in-scope item with its Done when, the week-by-week shape,
a trigger per later item, a reason per never, a row per table stake, the user's answers word for word. **The core
sentence is the first in-scope row**; no deferred or never row takes it back. No `[n]` marks here. Then
`status.py set scope filled --from-fields <file> --commit "<one line>"` (`--no-commit` only when the user said not to save) renders
`docs/scope.md` and `#Scope`, checks and saves. A refusal lists every gap at once.

## Step 3b — Self-verify (completeness gate)
`set scope filled` refuses the countable gaps `next` listed, every problem in one list: fix what it names, never
the check. **If the Deferred list is empty, or there are no Non-goals, STOP** — an empty
out-of-scope list is how products drift. Push the user to name at least the obvious temptations
(sorted into deferred-with-trigger vs never).

**Receipts and size** (`MECHANISMS-ON-DEMAND.md §Section is a record`, `MECHANISMS-ON-DEMAND.md §Read receipt`): `set` writes the `Read:` line and the size line; only an input file you opened yourself gets a quote, in the `read` field. Never trim to a number; a warning after a passing `set` (a plain-words estimate) needs no re-run.

**Close the loop (`MECHANISMS.md` §Step 3b):** the checklist `set scope filled` prints: the save was the yes (`MECHANISMS.md` §Commit the work); **run the transition guard** (§Step 3b, item 4) in one line: what the save checked, what is judged (`UNVERIFIED` is normal, silence is not); **close in plain language** (`MECHANISMS.md` §Plain-language close), 7 lines in all, as `set` prints them: the guard line, then `Saved (commit ...).`, then the four blocks, one line each under its bolded name: **What just happened** and **What I skipped or couldn't do** (the document linked, never restated), **Test this yourself**: `Nothing to test by hand in this phase.`, **What YOU do next**: `Change anything? If not:` - and last the `Open a NEW conversation` line, copied whole to its last word.

## Step 3c — Contradiction check (in round 2, before the yes; the close's step 3 confirms it)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Vision` (customer · job-to-be-done · north star) and `#Validation`'s verdict. The `vision check` field has **one row per vision promise** (the vision line, who it's for, the job, each step of the worked example, the north star, the AI line): `kept` · `deferred - <reason>` · `changed - <how, and who picked it>` — never a bare "agrees" — a core feature that serves nobody in `#Vision`, or scope written as if a failed validation had passed. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or a dated `superseded by` line in the earlier section) — never both standing. Adding detail to an earlier decision is not a contradiction.

## Reopening a Non-goal later
A reversed Non-goal is an explicit recorded reversal, never silent drift: follow `references/reopen-non-goal.md`.

## Step 4 — Handoff
"Scope locked — one core feature and an explicit out-of-scope list (`/drift-check` holds you to it).
Next run **`/plan`** to sequence the build core-first."
