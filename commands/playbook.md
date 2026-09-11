---
name: playbook
description: >
  The guided entry-point for product-playbook — run this to be walked through building a product
  phase-by-phase instead of remembering each skill. Use when starting fresh and unsure where to begin,
  or run /playbook "start", "guide me", "build a product", "what's next". Reads PRODUCT.md to see how
  far you've got and proposes the next phase; runs ONE phase at a time, pausing at each gate for your
  confirmation. It orchestrates the other skills — it does NOT auto-build or skip gates.
---

# `/playbook` — guided orchestrator · run as a **calm guide**

> Part of **product-playbook**. Reads the project spine (`PRODUCT.md`, or existing project docs — see MECHANISMS.md §Spine resolution); orchestrates the phase skills.
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) —
> load-bearing here: **plain-language communication**, **one recommendation + confirm**, **never
> bypass a gate**.

> **What this is (and isn't):** a single "start here" that runs the phases in order and keeps you
> oriented. It is an **orchestrator, not an autopilot** — every phase still asks you its questions and
> still stops at its exit gate for your confirmation. `/vision` alone does **not** build the product;
> the chain does, one human-checked step at a time.

## Contract
- **Purpose:** walk a (possibly non-technical) user through the lifecycle one phase at a time.
- **Reads:** `PRODUCT.md` (which sections are filled = how far along).
- **Writes:** nothing itself — each phase skill writes its own section. `/playbook` only routes + explains.
- **Exit criteria:** the user always knows **where they are, what the next phase is, and why** — and no
  gate is ever skipped.

## Step 0 — Orient
- If there's no `PRODUCT.md`, this is a fresh start → the next phase is **`/vision`**.
- If `PRODUCT.md` exists, read which sections are filled and find the **first unfilled / incomplete
  phase** in order: Vision → **Validate** → Scope → Plan → Architect → Structure → **Design (if UI)** →
  Foundation → Contracts → Tickets → Build → Dev-check → Test → Eval → Ship → Learn. That's the next phase.
  *(Design = run `/design-system`; it fills `PRODUCT.md#Design`. **Skip it for backend/API/CLI products** —
  the has-UI flag from `/architect`/`/structure` decides. Validate = run `/validate`; it fills
  `PRODUCT.md#Validation`. An **override** line there counts as filled but is surfaced every time you orient.)*
- **A `Not run` line is not a filled section.** A section whose only content is a dated
  `_Not run <date>: … — run <phase> first._` line (`MECHANISMS.md` §Declined runs) counts as **empty**:
  it stays the frontier, and the phase that fills it is still the next phase. But **say that the attempt
  happened** — *"`/eval` was already tried on <date> and declined because `#Tests` was empty; the missing
  phase is still `/test`"* — instead of proposing it blind for a second time. Distinguish it from an
  `Override` line, which *does* count as filled and is surfaced rather than routed to.
- **Surface every recorded override, every time you orient.** Scan the filled sections for
  `Override <date>: <reason> — bypassed <gate>` lines (`MECHANISMS.md` §Declined runs) and list them in one
  block before proposing anything — *"`#Contracts` was written on <date> with `#Foundation` bypassed:
  '<the user's reason>'"*. This is the whole point of recording a bypass: the project advanced on unmet
  criteria, and the next session — human or agent — must be told that without having to go looking. Offer
  the bypassed phase again; never re-ask for a reason that is already written down.
- **Check the order, not just the frontier.** The first-unfilled rule is silent when the chain was walked
  out of order — a project with `#Architecture` filled and `#Scope` empty gets pointed at Scope with no
  hint that stack decisions already exist which may not survive it. Compare the filled sections against
  the canonical order above and, for each **later section filled while an earlier one is empty**:
  - **name the inversion in one line** — "`#Architecture` is filled but `#Scope` is empty: the stack was
    chosen before the scope was locked";
  - **say what is at risk** — decisions taken without the earlier phase's input may not survive it
    (`/architect` traces to scope; a scope change can invalidate the stack);
  - **offer the earlier phase first, and allow an override.** Skills are standalone by design, so
    out-of-order use is legitimate — it should be *visible*, not blocked.
  An **in-order spine produces no extra output at all**; don't manufacture noise. A user who overrides gets
  it recorded on the `Playbook:` line of the `PRODUCT.md` header — **read that first and do not re-ask** on later runs.
- **UI projects only — recommend the enforcement tool, never gate on it.** If the has-UI flag is set and
  `#Build log` already contains UI work, say once that `/frontend-audit` mechanically checks that UI against
  the laws `/design-system` set (real contrast computation, not an opinion). It is a **recommendation, not a
  phase**: it writes no `PRODUCT.md` section, so the first-unfilled frontier must never look for one, and a
  user who ignores it is not behind on anything. For a backend/API/CLI product (has-UI false) say nothing —
  neither UI-suite skill exists for that user.
- **Brownfield (existing code, no `PRODUCT.md`): route to `/adopt`.** It drafts an INFERRED `PRODUCT.md`
  from what the repo actually contains and confirms it with the owner — after which orienting works
  normally. Entering straight at `/architect` or `/build` still works and stays offered, but it leaves the
  project with no spine, so every later phase re-guesses it.

## Step 1 — Explain the map (once, briefly, plain language)
Show the journey in one screen so the user has the mental model:
`vision → validate → scope → plan` (Product) · `architect → structure → design-system* → foundation → contracts → tickets → build → dev-check → deploy**†**` (*UI only —
UI products also get `/new-component` to build one against `DESIGN.md` and `/frontend-audit` to check it; tools, not steps)
(Development; **†** `/deploy` runs when something ahead needs a real URL — it executes the host
`#Architecture` chose) · `test` · `eval` · `ship` · `learn` · `/drift-check` anytime. Note: each step asks a few
questions and ends with a check before moving on — you stay in control.

## Step 2 — Run the next phase (one at a time)
1. Tell the user the next phase in plain language: *what it does and why it matters now.*
2. **Invoke that phase's skill** (e.g. run `/vision`). Let it ask its questions and do its work.
3. When that skill reaches its **exit gate**, surface the result and **pause** — confirm with the user
   that it's right before continuing. **Never advance past an unmet gate.**
4. On confirmation, point to the next phase and repeat. The user can stop anytime and resume later by
   running `/playbook` again (it re-orients from `PRODUCT.md`).

## Step 3 — Anytime
Remind the user they can run **`/drift-check`** whenever they suspect scope creep, and — **on a UI product
only** — **`/frontend-audit`** after building or changing UI, or before shipping. Both are anytime tools, not
phases in the chain: neither fills a `PRODUCT.md` section, so neither can ever be "the next phase". They can
also run any single phase skill directly (e.g. `/test`) without `/playbook`.

## Handoff
"You're set up to be guided. We'll do **one phase at a time**, checking each before moving on — run the
proposed next skill, or just keep running `/playbook` and I'll walk you through."
