---
name: validate
description: >
  Phase 1 (Product) of product-playbook. Test the RISKIEST ASSUMPTION from /vision with the
  cheapest real-world experiment BEFORE any code is written — landing page, interviews, a manual
  concierge run, a pre-sale — with a pass/fail threshold set in advance, a measured result, and a
  proceed / pivot / kill verdict. Use after /vision, or run /validate "is anyone going to want
  this", "test the idea", "validate before building", "riskiest assumption". Writes the Validation
  section of PRODUCT.md. Run /scope next.
---

# `/validate` — Phase 1 · Product · run as a **sceptical founder**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per PRINCIPLES.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing here: **verify-don't-assume**,
> **measure before fixing**, **evidence-based "done"**, **plain-language one-recommendation**.

> **Why this phase exists:** `/vision` makes you *name* the riskiest assumption; nothing else in the
> chain ever *tests* it. A product can pass every later gate and still be the wrong product. This is
> the cheapest anti-waste lever in the playbook: a few days of evidence before months of code.

## Contract
- **Purpose:** falsify (or survive) the riskiest assumption with the cheapest experiment that can, and decide from the measured result.
- **Reads:** `PRODUCT.md#Vision` — riskiest assumption · north-star metric · job-to-be-done · target user · business model.
- **Writes:** `PRODUCT.md#Validation` — fields: assumption under test · experiment (type, who, time box) · pass/fail threshold (set before) · measured result · verdict (proceed / pivot / kill) · override (if any).
- **Exit criteria:**
  - [ ] The assumption under test is stated as a **falsifiable sentence** ("<user> will <behaviour> because <reason>"), copied from `#Vision` or sharpened with the user.
  - [ ] **One experiment** chosen, the cheapest that can falsify it — with the real people it reaches and a **time box** (days, not months).
  - [ ] A **pass/fail threshold written down BEFORE the experiment runs** (a number, e.g. "≥ 3 of 10 interviewees describe doing this manually today" / "≥ 5% of visitors leave an email").
  - [ ] A **measured result** — an actual number or quoted evidence, never "people seemed interested".
  - [ ] A **verdict**: proceed / pivot / kill, with one sentence of reasoning tied to the threshold.
  - [ ] If the user skips the experiment, an **explicit override** line (date + reason) is recorded instead — never a silent pass.
  - [ ] **The override reason is pressure-tested against `#Vision` before it is recorded.** A reason implying a *different product* than the Vision describes ("personal use", "internal tool", "just for me" — against a Vision with a public customer, a north star and a business model) is a **contradiction, not a deferral**: name the `#Vision` line it contradicts and offer `/vision` first. The override stays allowed, but as an informed choice.
  - [ ] **The override follows `PRINCIPLES.md` §Declined runs** — the *deliberate-skip* shape of that rule: one dated line, the experiment fields kept and each marked `— not run (override <date>)`, never a blanked section. (Unlike a `Not run` note, an override **does** count as filled — the phase is not still owed — and every later phase surfaces it.)

## Step 0 — Context + prior-gate check
- Read `PRODUCT.md#Vision`. If the **riskiest assumption** is missing or vague ("people will like it"),
  warn: "`/vision` looks incomplete — there is nothing testable to validate." Offer to run `/vision`
  first, but allow override (standalone use): ask the user to state the assumption now.
- If `#Validation` already has a result, you are **re-validating** (a pivot, or a stale result) — read
  it, and do not overwrite the earlier record; append a new dated entry.

- **Re-running this phase (`PRINCIPLES.md` §Re-run semantics):** if the section is already filled, **show what would change and ask before replacing it** — never a silent overwrite — and leave a reversed decision in place with a dated `superseded <date>: <why>` line. A first run over an empty section is unchanged.
- **If the gate is unmet and the run stops here, record that it stopped (`PRINCIPLES.md` §Declined runs):** write ONE dated line at the top of `#Validation` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **Verify, don't assume:** the user's confidence is not evidence. Neither is yours. Only people
  outside the building count.
- **Measure before fixing:** the threshold comes *before* the result, or the result gets rationalised.
- **Evidence-based "done":** a verdict without a number is a wish. Say so.
- Speak in **plain language**; end with **one recommendation**, not a menu of research methods.

## Step 2 — Design the experiment (ask, then sharpen)
Ask one block at a time; wait for answers.
1. **Restate the assumption as a bet.** "If we're wrong about *this*, nothing else matters — agree?"
   Make it falsifiable: *who* does *what* observable thing. Push back on "people want X" until it
   names a behaviour ("ops leads at 20-200-person firms will hand us a spreadsheet they maintain by
   hand today").
2. **What is the cheapest thing that could prove this wrong?** Recommend ONE from the ladder below —
   the lowest rung that can actually falsify *this* assumption — and say why in a sentence:
   | Rung | Experiment | Falsifies | Cost |
   |---|---|---|---|
   | 1 | **Desk check** — do people already pay for / hack around this? (compose a web search or `/deep-research` if available) | "nobody has this problem" | hours |
   | 2 | **5–10 problem interviews** with the named user (not friends) | "the problem is not painful enough to act on" | days |
   | 3 | **Landing page / fake door** — the promise, one call-to-action, measure conversion | "nobody will show intent" | days |
   | 4 | **Concierge / Wizard-of-Oz** — deliver the outcome by hand for 3–5 real users | "the outcome is not valuable" | 1–2 weeks |
   | 5 | **Pre-sale / LOI / deposit** | "nobody will pay" | 1–2 weeks |
   For **internal** products: rung 2 with the actual internal users, or rung 4 (do the job by hand for
   one team). For **AI products**: rung 4 with a human behind the curtain — it tests the *outcome*
   before any model, prompt or eval exists.
3. **Set the bar before you look.** Ask: "What result would make you *not* build this?" Turn the
   answer into a number + a time box. Write both down now. If the user cannot name a failing result,
   the experiment is theatre — say so and keep asking.
4. **Who exactly, and how do you reach them this week?** Names, channels, a date. An experiment
   with no reachable participants is a plan, not a test.

Give **one recommendation** (experiment + threshold + time box); get a yes/no.

## Step 3 — Run it, then record the measured result
- **Run or schedule it.** Small desk checks run now. Interviews / landing pages / concierge runs take
  days: write the plan into `#Validation` as **"running — due <date>"**, and offer to re-measure
  later (compose `/loop` or `/schedule` for a landing-page or sign-up count that changes over time).
- When the result is in, **record what was measured** — the number, the quotes, the count — and the
  date. Keep the raw evidence somewhere the repo can point to (`docs/validation/<date>-<experiment>.md`
  for interview notes / screenshots), not only in chat.
- **Apply the threshold mechanically**, then interpret:
  - **Proceed** — met the bar. Note any sharpening the evidence gave the vision (a narrower segment, a
    different JTBD wording) and update `#Vision` *deliberately*, with a one-line "changed because".
  - **Pivot** — missed the bar but the evidence points somewhere adjacent. Say what changed, rewrite
    the riskiest assumption, and **run `/validate` again** on the new one. Do not proceed to `/scope`
    on the old assumption.
  - **Kill** — missed the bar and nothing adjacent showed up. Record it plainly. A kill here is the
    playbook working: it cost days, not a codebase.

## Step 3b — Self-verify (the evidence gate)
Walk the exit criteria. **STOP and do not hand off if:**
- the threshold was written *after* the result (or is missing) — it is not a test;
- the "result" is a feeling, a friend's opinion, or the user's own conviction;
- the verdict contradicts the threshold without a recorded reason.
If the user wants to skip the experiment entirely: allowed, but **only with an explicit override**
line in `#Validation` — `Override <date>: <reason> — assumption untested.`

**First, pressure-test the reason against `#Vision`** — one comparison, not an interrogation: does it fit the
recorded **customer**, **business model** and **north star**? A reason that merely *defers* ("no budget this
month", "pre-sold to a design partner") records cleanly in one step. A reason that describes a **different
product** does not — quote the `#Vision` line it contradicts, say plainly that recording it would leave two
incompatible statements standing in the spine, and offer `/vision` first. If the user proceeds anyway, record it.

**Keep the scaffold** (`PRINCIPLES.md` §Declined runs — the deliberate-skip shape). Writing the override
must not blank the experiment fields: leave each present and marked `— not run (override <date>)`. Both
`/scope` and `/drift-check` read it — `/scope` surfaces it, and `/drift-check` treats an untested
assumption as a standing finding until it is closed.

**Close the loop (`PRINCIPLES.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and end with a suggested one-line commit message in the repo's convention.

## Step 3c — Contradiction check (before the gate closes)
Per `PRINCIPLES.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Vision` — the assumption you tested must be the **riskiest** one recorded there, and a skip override whose reason implies a different user or business model contradicts `#Vision` itself. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
- **Proceed:** "Assumption tested and recorded in `PRODUCT.md#Validation` (result vs threshold).
  Next run **`/scope`** to lock the ONE core feature — now with evidence about what the user actually does."
- **Pivot:** "Recorded. The riskiest assumption changed — re-run **`/validate`** on the new one before scoping."
- **Kill:** "Recorded as killed with the evidence. Nothing further to build; if a new idea emerges,
  start again at **`/vision`**."
- **Override:** "Recorded as untested, by your decision. `/scope` and `/drift-check` will keep
  flagging it until an experiment closes it. Next run **`/scope`**."
