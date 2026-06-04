---
name: vision
description: >
  Phase 1 (Product) of product-builder. Define a product's vision — who it's for, the
  problem (why now), the value proposition — and pressure-test it against the CURRENT-YEAR
  market and competitors. Use at the very start of a new product, or run /vision "start a
  product", "what should we build", "is this idea any good". Writes the Vision section of
  PRODUCT.md (the shared spine). Run /scope next.
---

# `/vision` — Phase 1 · Product · run as a **product developer**

> Part of **product-builder**. Reads + updates the shared spine `PRODUCT.md`.
> Apply `PRINCIPLES.md` — load-bearing here: **vision-alignment**, **verify-don't-assume**,
> **benchmark-to-current-year**, **plain-language communication**.

## Contract
- **Purpose:** turn a rough idea into a sharp, benchmarked product vision.
- **Reads:** nothing required (this is the first phase) — or an existing `PRODUCT.md`/codebase if present.
- **Writes:** `PRODUCT.md#Vision` — fields: who it's for · problem (why now) · value proposition · 2026 market/competitor read.
- **Exit criteria:**
  - [ ] A single sentence vision (the world this product creates).
  - [ ] Named target user + the concrete problem they have, and **why now**.
  - [ ] A value proposition stating how this is better/different.
  - [ ] A current-year market/competitor read with at least one sharpening insight.
  - [ ] Recorded whether this is an **AI product** (uses LLMs) — flags the AI-security layer downstream.

## Step 0 — Context + prior-gate check
- If `PRODUCT.md` exists, read `#Vision`; you are refining, not overwriting blindly.
- If a codebase exists but no `PRODUCT.md`, skim it to infer what's being built, then confirm with the user.
- If neither, start fresh from `templates/PRODUCT.md`.

## Step 1 — Apply principles (this phase)
- **Verify, don't assume:** do not invent the user's intent — ask. **Benchmark to the current year:** the idea must be judged against how the market solves this *now*, not 3 years ago.
- Speak in **plain language**; end with **one recommendation**, not a jargon matrix.

## Step 2 — Guided discovery (ask, then sharpen)
Ask these one block at a time; wait for answers. Keep it short — a newcomer should not feel interrogated.
1. **In one line, what is this product and who is it for?**
2. **What painful problem does it solve, and why is now the right time?** (regulation, tech shift, cost, new behaviour)
3. **How do people solve this today, and why is that not good enough?**
4. **Will it use AI / LLMs?** (yes flags the AI-security layer in later phases)

Then **benchmark to the current year** — compose `/doc-create` if a deeper artifact is wanted:
- How do leading products solve this *now*? Name 2–3 comparables and the current best-practice approach.
- Surface **one sharpening insight**: a sharper wedge, a segment, or a differentiator the user hadn't stated.
- Give **one clear recommendation** on the crispest framing of the vision; get a yes/no.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Vision`: who it's for · problem (why now) · value proposition · 2026 market/competitor read.
Set the header `AI product? <yes/no>`.

## Step 3b — Self-verify (completeness gate)
Check every Exit-criteria box against what you wrote. **If any field is empty or vague, STOP and
fill it with the user — do not hand off a fuzzy vision** (a fuzzy vision is the root of later drift).

## Step 4 — Handoff
"Vision captured in `PRODUCT.md`. Next run **`/scope`** to lock the ONE core feature and what's
explicitly out of scope — that's your seatbelt against feature creep."
