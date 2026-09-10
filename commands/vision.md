---
name: vision
description: >
  Phase 1 (Product) of product-playbook. Define a product's vision — who it's for, the
  problem (why now), the value proposition — and pressure-test it against the CURRENT-YEAR
  market and competitors. Use at the very start of a new product, or run /vision "start a
  product", "what should we build", "is this idea any good". Writes the Vision section of
  PRODUCT.md (the shared spine). Run /scope next.
---

# `/vision` — Phase 1 · Product · run as a **product developer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing here: **vision-alignment**, **verify-don't-assume**,
> **benchmark-to-current-year**, **plain-language communication**.

## Contract
- **Purpose:** turn a rough idea into a sharp, benchmarked product vision.
- **Reads:** nothing required (this is the first phase) — or an existing `PRODUCT.md`/codebase if present.
- **Writes:** `PRODUCT.md#Vision` — fields: who it's for · problem (why now) · value proposition · 2026 market/competitor read.
- **Gate type:** `input` — who it is for, the job, the north star - the answers exist only in the user's head. **Never batched** - skipping it fabricates the product's premise. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes `#Vision` · `declined` ✓ · `override` n/a — `/vision` opens the chain; there is no prior section to bypass · `superseded` ✓
- **Exit criteria:**
  - [ ] A single sentence vision (the world this product creates).
  - [ ] Named target user + the concrete problem they have, and **why now**.
  - [ ] A value proposition stating how this is better/different.
  - [ ] A current-year market/competitor read with at least one sharpening insight.
  - [ ] A **north-star metric with all five parts** — a **target number + date**, **2–3 input metrics**, **1 guardrail**, and an **instrumentation line**. A direction ("more people tracking subscriptions") is a slogan, not a metric, and **fails this gate**: `/eval` would have nothing to measure against.
  - [ ] The **job-to-be-done**, the **riskiest assumption**, and the **business model** (free/paid/internal) captured.
  - [ ] Recorded whether this is an **AI product** (uses LLMs) — flags the AI-security layer downstream.

## Step 0 — Context + prior-gate check
- If `PRODUCT.md` exists, read `#Vision`; you are refining, not overwriting blindly.
- If a codebase exists but no `PRODUCT.md`, skim it to infer what's being built, then confirm with the user.
- If neither, start fresh from the bundled `PRODUCT.md` template (shipped with this toolkit; see README).

- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** if the section is already filled, **show what would change and ask before replacing it** — never a silent overwrite — and leave a reversed decision in place with a dated `superseded <date>: <why>` line. A first run over an empty section is unchanged.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** write ONE dated line at the top of `#Vision` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **Verify, don't assume:** do not invent the user's intent — ask. **Benchmark to the current year:** the idea must be judged against how the market solves this *now*, not 3 years ago.
- Speak in **plain language**; end with **one recommendation**, not a jargon matrix.

## Step 2 — Guided discovery (ask, then sharpen)
Ask these one block at a time; wait for answers. Keep it short — a newcomer should not feel interrogated.
1. **In one line, what is this product and who is it for?**
2. **What painful problem does it solve, and why is now the right time?** (regulation, tech shift, cost, new behaviour)
3. **How do people solve this today, and why is that not good enough?**
4. **How will you know it's working?** — the **north star, in five parts**. Ask for them together; a bare
   direction is the usual answer and is not yet a metric:
   - **Target + date** — "400 accounts with 3+ subscriptions by 2027-03-31", not "growth".
   - **2–3 input metrics** — the weekly-moving numbers that *drive* it. A north star moves too slowly to steer by.
   - **1 guardrail** — what must NOT get worse while chasing it (churn, p95 latency, support load).
   - **Instrumentation** — *how* it gets measured, named now. **If nothing can currently record it, that is a
     finding, not a detail for later** — say so plainly.
5. **What's the riskiest assumption** this depends on? And is it **free, paid, or internal**?
6. **Will it use AI / LLMs?** (yes flags the AI-security layer in later phases)

Then **benchmark to the current year** — and actually check, don't guess (compose a web search and/or `/doc-create`):
- How do leading products solve this *now*? Name 2–3 **real** comparables and the current best-practice approach.
- Frame the problem as a **job-to-be-done** ("when <situation>, I want to <motivation>, so I can <outcome>").
- Surface **one sharpening insight**: a sharper angle, segment, or differentiator the user hadn't stated.
- Give **one clear recommendation** on the crispest framing; get a yes/no. Keep it plain — no jargon.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Vision`: who · problem (why now) · value proposition · verified market/competitor read · north star
(**target+date · input metrics · guardrail · instrumentation**) · job-to-be-done · riskiest assumption ·
business model. Set the header `AI product? <yes/no>`.

## Step 3b — Principle-gate: verify it's sharp, not fuzzy
Walk the exit criteria and confirm each is **concrete with evidence** — the competitor read cites *real*
named products (not from memory), the metric is a measurable number, the JTBD/risk are specific. **If any
field is empty or vague, STOP and fill it with the user** — **a north star missing its target, date, input
metrics, guardrail or instrumentation line is vague by definition** — a fuzzy vision is the root of later drift.

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and end with a suggested one-line commit message in the repo's convention. Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal.

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: any spine that already exists (`README.md`/`CLAUDE.md` purpose, a prior `#Vision`) — a re-run that quietly changes the customer, the north star or the business model rewrites the premise every later phase was built on. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Vision captured in `PRODUCT.md`. Next run **`/validate`** to test the riskiest assumption you just
named with the cheapest real-world experiment — days of evidence before months of code. Then
**`/scope`** locks the ONE core feature and what's explicitly out of scope — your seatbelt against
feature creep."
