---
name: scope
description: >
  Phase 1 (Product) of product-playbook. Lock the ONE core feature that delivers the core
  value, and write an explicit OUT-OF-SCOPE list so the product does not drift. Use after
  /vision, or run /scope "what should the MVP be", "we keep adding features", "cut scope".
  Writes the Scope section of PRODUCT.md. Run /plan next. This is the anti-scope-creep skill.
---

# `/scope` — Phase 1 · Product · run as a **product manager**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per PRINCIPLES.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing here: **scope discipline**, **vision-alignment**,
> **defer until a real trigger**, **plain-language one-recommendation**.

## Contract
- **Purpose:** force a single core feature and an explicit, defended OUT-OF-SCOPE list.
- **Reads:** `PRODUCT.md#Vision`.
- **Writes:** `PRODUCT.md#Scope` — fields: THE core feature · in-scope (now) · Deferred (+trigger) · Non-goals (never).
- **Exit criteria:**
  - [ ] Exactly **one** core feature named (the thing that, alone, delivers the core value).
  - [ ] A short in-scope list, each item tied to the vision's value proposition **and** plausibly moving the north-star metric.
  - [ ] A **non-empty Deferred list**, each item with the **trigger** that would bring it in — **and** a **Non-goals** list (things we deliberately will *never* build).
  - [ ] Each in-scope item traces to a customer outcome, not a feature wish.
  - [ ] **The table-stakes checklist is fully sorted** — every item explicitly **in-scope now**, **Deferred (with trigger)** or **N/A (with reason)**. **No item may be left unsorted**: an unsorted item fails this gate, because these are the things nobody proposes and everybody expects.

## Step 0 — Context + prior-gate check
- Read `PRODUCT.md#Vision`. If it is missing/empty, warn: "`/vision` looks incomplete — scope without
  a vision drifts." Offer to run `/vision` first, but allow override (standalone use).
- Read `PRODUCT.md#Validation`. If it is empty, or holds an **override** (assumption untested), warn:
  "The riskiest assumption has not been tested — scoping locks a core feature around an unproven bet."
  Offer to run `/validate` first (usually days, not weeks), but allow override (standalone use); if the
  user proceeds, carry the untested assumption into the scope discussion so the core feature is chosen
  with that risk visible.

- **Re-running this phase (`PRINCIPLES.md` §Re-run semantics):** if the section is already filled, **show what would change and ask before replacing it** — never a silent overwrite — and leave a reversed decision in place with a dated `superseded <date>: <why>` line. A first run over an empty section is unchanged.
- **If the gate is unmet and the run stops here, record that it stopped (`PRINCIPLES.md` §Declined runs):** write ONE dated line at the top of `#Scope` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **Scope discipline:** the default answer to a new feature is **"not yet — what's the trigger?"**
- **Vision-alignment:** every in-scope item must serve the value proposition; if it doesn't, it's out.
- **Defer until a real trigger** (incl. paid infra): record the condition that would pull it in.

## Step 2 — Guided scoping
Ask, one block at a time:
1. **If you could ship only ONE capability and nothing else, what is it?** → that's the core feature.
   Push back if they name three; help them pick the one that delivers the core value alone.
2. **What's the smallest set around it that makes that core usable?** → the in-scope (now) list. Keep it ruthless.
3. **What are you tempted to add that is NOT needed for the core?** If the user is unsure, prompt with the
   usual creep categories — auth/multi-user, admin dashboard, integrations, mobile, analytics, settings.
   Sort each into **Deferred** (with the **trigger/signal** that would justify it) or **Non-goal** (never).
4. **Walk the table-stakes checklist** — the boring items nobody proposes and everybody expects. They do not
   get deferred, they get *forgotten*, and they resurface at ship time as "we can't launch without this":
   the exact scope shock this skill exists to prevent. Sort **every** one into **in-scope now / Deferred
   (+trigger) / N-A (+reason)**:
   password reset · email verification · account deletion **+ data export** (often a legal duty, not a
   feature) · empty / loading / error states · privacy policy + terms · accessibility baseline · a way for a
   user to report a problem.
   **Adapt the list to the product kind** — an account-less CLI has no password reset (N-A: "no accounts"),
   but it still has error states and a licence. Adapting the list is expected; leaving an item unsorted is not.
5. Tie each in-scope item to **a customer outcome** ("user can X in minutes"), not a feature name — and check it plausibly moves the north-star metric.

Give **one recommendation** on the tightest viable core; get a yes/no.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Scope`: THE core feature · in-scope (now) · Deferred (each with its trigger) · Non-goals (never) ·
**Table stakes** (every item with its in / deferred+trigger / N-A+reason verdict).

## Step 3b — Self-verify (completeness gate)
Check the boxes. **If the Deferred list is empty, or there are no Non-goals, STOP** — an empty
out-of-scope list is how products drift. Push the user to name at least the obvious temptations
(sorted into deferred-with-trigger vs never).

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
   feature that prompted it (e.g. "avatar" reopened during an editor build is a generation feature
   with its own doc, not an editor button). Name it separately so its true size is visible.
If the assistant notices work quietly contradicting a Non-goal without this protocol, that is
drift — surface it (`/drift-check` treats an unrecorded reversal as a finding, not a decision).

**Close the loop (`PRINCIPLES.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and end with a suggested one-line commit message in the repo's convention.

## Step 3c — Contradiction check (before the gate closes)
Per `PRINCIPLES.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Vision` (customer · job-to-be-done · north star) and `#Validation`'s verdict — a core feature that serves nobody in `#Vision`, or scope written as if a failed validation had passed. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Scope locked — one core feature, with an explicit out-of-scope list. `/drift-check` will hold you to
it later. Next run **`/plan`** to sequence the build core-first."
