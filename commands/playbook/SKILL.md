---
name: playbook
description: >
  The guided entry-point for product-playbook — run this to be walked through building a product
  phase-by-phase instead of remembering each skill. Use when starting fresh and unsure where to begin,
  or run /playbook "start", "guide me", "build a product", "what's next". Reads where the project stands
  (STATUS.md, or the folder itself on a first visit) and proposes the next phase; runs ONE phase per
  conversation, pausing at each gate for your confirmation. It orchestrates the other skills — it does NOT
  auto-build or skip gates.
---

# `/playbook` — guided orchestrator · run as a **calm guide**

> Part of **product-playbook**. Reads where the project stands; orchestrates the phase skills.
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **`status.py route` (Step 0) prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them;
> never open the whole files (a situational companion only when a rule points into it) — load-bearing here:
> **plain-language communication**, **one recommendation + confirm**, **never bypass a gate**.

> **What this is (and isn't):** a single "start here" that runs the phases in order and keeps you
> oriented. It is an **orchestrator, not an autopilot** — every phase still asks you its questions and
> still stops at its exit gate for your confirmation. `/vision` alone does **not** build the product;
> the chain does, one human-checked step at a time.

## Contract
- **Purpose:** walk a fresher or a working engineer through the lifecycle one phase at a time.
- **Reads:** `STATUS.md` through `status.py route` (which phases are filled = how far along).
- **Writes:** no `PRODUCT.md` section — each phase skill writes its own. `STATUS.md` only through `status.py`
  (`migrate --write`, `bypass`, `flag --order-override`), each on the user's yes.
- **Exit criteria:** the user always knows **where they are, what the next phase is, and why** — and no
  gate is ever skipped.
- **Must NOT:** write a `PRODUCT.md` section, answer a phase's questions for the user, start a phase without
  the user's yes, or start the next phase in the same conversation.

## Step 0 — Orient
- **Run `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py route` first — one call, nothing before it** (no `ls`, no
  file reads: it looks at the folder itself). It prints the rules above, every skill in order, then `Where:`,
  `Next:`, `Size:`, `Batch:` (only when legal), `Map:` and every note. It finds the **first unfilled / incomplete phase** in order: Vision → Validate (optional) → Scope → Plan → Architect → Structure → **Design (if UI)** →
  Foundation → Contracts → Tickets → Build → Dev-check → Test → Eval → Ship → Learn. That's the next phase.
  *(Design = run `/design-system`, skipped when `STATUS.md` says `UI: no`; Validate = `/validate`, only when the user asks — never the next phase by itself. Build stays
  the next phase while a milestone in `TICKETS.md` has unrecorded tickets; Dev-check, Test and Eval stay it until
  their verdict is `pass`. `/deploy` is never the next phase by itself: it runs when a milestone needs a real URL,
  else `/test` follows `/dev-check`.)*
- **No `STATUS.md`:** `route` names the start — a fresh folder → **`/vision`**; existing code or a `PRODUCT.md`
  with no `STATUS.md` → **`/adopt`**, which drafts or confirms the spine with the owner (entering straight at
  `/architect` or `/build` still works and stays offered, but every later phase then re-guesses the spine); the
  old `_Last updated: … Stage:` header → `status.py migrate` (a dry run; `--write` only on the user's yes).
- **Report what `route` lists, before proposing anything** — one line each, in plain words:
  - **a declined next phase** — *"`/eval` was already tried on <date> and declined because `#Tests` was empty;
    the missing phase is still `/test`"* — never propose it blind a second time;
  - **every override and bypass** — *"`#Contracts` was written on <date> with `/foundation` bypassed:
    '<the user's reason>'"*. The project advanced on unmet criteria, and the next session must be told that
    without having to go looking. Offer the bypassed phase again; **never re-ask for a reason already recorded**;
  - **every running gate** with its due date (an overdue one is a stalled gate), and **every open item**;
  - **every inversion** (`out of order: #X is filled but #Y is empty`): **say what is at risk** — decisions
    taken without the earlier phase's input may not survive it (`/architect` traces to scope; a scope change
    can invalidate the stack) — and **offer the earlier phase first, allowing an override**
    (`status.py bypass`). Skills are standalone by design, so out-of-order use is legitimate — it should be
    *visible*, not blocked. A user who chose to leave the order is recorded once
    (`status.py flag --order-override "<the user's reason>"`); `route` prints it — **do not re-ask**.
  An **in-order project produces no extra output at all**; don't manufacture noise.
- **UI projects only — recommend the enforcement tool, never gate on it.** `UI: yes` and ticket rows with UI
  work → say once that `/frontend-audit` mechanically checks that UI against the laws `/design-system` set (real
  contrast computation, not an opinion). A **recommendation, not a phase**: it writes no `PRODUCT.md` section,
  and a user who ignores it is not behind. `UI: no` → say nothing about the UI suite.

## Step 1 — Explain the map (only when `route` prints `Map: show it`)
Show `route`'s `Skills, in order` lines as printed (one source: never re-type the list) so the user has the
mental model, and add: each step asks you questions and ends with a check before moving on — you stay in
control. `Map: skip it` → no map; the list still routes a goal the user names (Step 2).

## Step 2 — Offer the next phase, then run it (one phase per conversation)
1. **One message, ending in one question.** Lead with three plain lines — what's done (`Done:`), what's next,
   why — then what `route` reported (Step 0), the map when Step 1 says so, the next phase in plain language —
   *what it does and why it matters now* — and its size from `route`'s `Size:`
   line: *"`/<phase>` is a short one: questions and one section of your product document"*, or for a long one
   *"`/<phase>` is a long one: it writes and checks project files. Start it with room left on your plan: a run a
   usage limit cuts off mid-review loses review steps."* Never a number of minutes, never a price — what a run
   costs depends on the user's plan. Last line: *"Start `/<phase>` now? (yes / later)"*.
   - **Offer a batch only when `route` prints `Batch: legal`** (`MECHANISMS-ON-DEMAND.md` §Batch mode): *"Run
     `/foundation` alone, or `/foundation` + `/contracts` + `/tickets` as one batch? The batch still stops where
     a phase asks you to confirm; one commit per phase, one review at the end."* A batch is long. The user's
     choice is a choice, not a default.
   - **The user already named a goal** (`/playbook <text>`, or the reply): route it, no extra question — a new
     idea → `/vision` with their words as its input; a bug → `/tickets "<the bug>"`; changing scope → `/scope`
     (a re-run); "something feels off" → `/drift-check`; "continue" → the next phase.
2. **Invoke that phase's skill only on the user's yes** (e.g. run `/vision`), in this conversation. *Later* → say
   *"Run `/playbook` again when you're ready"* and stop.
3. The phase asks its questions and does its work. When it reaches its **exit gate**, surface the result and
   **pause** — confirm with the user that it's right before continuing. **Never advance past an unmet gate.**
4. **After the phase's close, this conversation is done.** No second `route` call:
   the offer is the last item of its *What YOU do next* (`MECHANISMS.md` §Plain-language close) — the `Open a NEW
   conversation and type: /<next>` line the phase's close printed, word for word — or *"open a new conversation
   and run `/playbook`"*, whose `route` gives the next phase's size. **Never invoke the next phase in this conversation** — every call would re-send the finished phase — except a
   batch the user chose. The user can stop anytime and resume later by running `/playbook` again.

## Step 3 — Anytime
Remind the user they can run **`/drift-check`** whenever they suspect scope creep, and — **on a UI product
only** — **`/frontend-audit`** after building or changing UI, or before shipping. Both are anytime tools, not
phases in the chain: neither fills a `PRODUCT.md` section, so neither can ever be "the next phase". They can
also run any single phase skill directly (e.g. `/test`) without `/playbook`.

## Handoff
"You're set up to be guided. We'll do **one phase at a time**, checking each before moving on — run the
proposed next skill, or just keep running `/playbook` in a new conversation and I'll walk you through."
