---
name: vision
description: >
  Phase 1 (Product) of product-playbook. Define a product's vision — who it's for, the
  problem (why now), the value proposition — and pressure-test it against the CURRENT-YEAR
  market and competitors. Use at the start of a new product, or run /vision "start a
  product", "what should we build", "is this idea any good". Writes the Vision section of
  PRODUCT.md (the shared spine). Run /scope next.
---

# `/vision` — Phase 1 · Product · run as a **product developer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **`status.py next --phase vision` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it); the rest of the close prints when `set vision filled` passes. Load-bearing here: **vision-alignment**, **verify-don't-assume**,
> **benchmark-to-current-year**, **plain-language communication**.

## Contract
- **Purpose:** turn a rough idea into a sharp, benchmarked product vision.
- **Reads:** nothing required (this is the first phase) — or an existing `PRODUCT.md`/codebase if present.
- **Writes:** `PRODUCT.md#Vision` — every field `next` prints · `docs/vision.md` · `STATUS.md` with the AI flags.
- **Gate type:** `input` — who it is for, the job, the north star - the answers exist only in the user's head. **Never batched** - skipping it fabricates the product's premise. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Vision` · `declined` ✓ · `override` n/a — `/vision` opens the chain; there is no prior section to bypass · `superseded` ✓
- **Companion:** `docs/vision.md` — **the document a founder reads** (Step 3). `PRODUCT.md#Vision` stays a
  RECORD (summary · decision · evidence · pointer) — no byte cap; reasoning moves, answers stay.
- **Exit criteria:**
  - [ ] A single sentence vision (the world this product creates). → `Vision (ONE sentence`
  - [ ] **In plain words** (2–3 sentences) and one **worked example** with names and numbers — a newcomer understands the product from these alone. → `In plain words` · `Worked example`
  - [ ] Named target user + the concrete problem they have, and **why now** — backed by a recorded search, or marked `the owner's claim, not verified`. → `Who it's for` · `Problem (why now)`
  - [ ] Who it's for, who asks and the business model are the owner's words (`## Owner's answers`). → `Who it's for` · `Business model`
  - [ ] A value proposition stating how this is better/different. → `Value proposition`
  - [ ] A current-year market/competitor read with at least one sharpening insight. → `Current-year market`
  - [ ] **Every search the market read ran is recorded in `docs/vision.md`** — one line each, query · what it settled — and every comparable named without a search has its own line saying so. → `Current-year market`
  - [ ] Every search line carries its source link, and the list has a `local ·` line (the named market, first), a `same job ·` line (this exact job, anywhere) and a `rules ·` line (data protection, AI law, the sector's law). → `Current-year market`
  - [ ] The **constraints**: the rules that apply, the users' languages, where the data comes from. → `Constraints`
  - [ ] A **north-star metric with all five parts** — a **target number + date**, **2–3 input metrics**, **1 guardrail**, and an **instrumentation line**. A direction ("more restaurants using the waitlist") is a slogan, not a metric, and **fails this gate**: `/eval` would have nothing to measure against. **Every term in the target and the inputs has a number** ("active" = "≥1 chore in 14 days"). → `North star`
  - [ ] Every number says where it came from — owner · searched · derived · proposed. → `North star`
  - [ ] The **job-to-be-done**, the **riskiest assumption**, and the **business model** (free/paid/internal) captured. → `Job-to-be-done` · `Riskiest assumption` · `Business model`
  - [ ] How the **first 10 users** find it and why they switch. → `First users`
  - [ ] Recorded whether this is an **AI product** (uses LLMs) and an **agent** (acts on its own) — flags the AI-security layer downstream. → `STATUS.md header: AI product` · `STATUS.md header: Agent`
  - [ ] An AI product: what the AI does and what a person decides, the accuracy bar, the cost per use. → `AI (what it does`
  - [ ] `#Vision` is a **RECORD** — every field is a decision, evidence line or pointer; the reasoning is
    in `docs/vision.md`. Size is reported, never trimmed to. → `Detail:`

## Step 0 — Context + prior-gate check
- **First turn, ONE command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase vision`** — it prints the start and this phase's rules; never the rule files, the template or `PRODUCT.md` whole. Show its first line; close by its checklist. Load your web-search tool in the same turn. `next` says **fresh start** → ask question 1; nothing to probe.
- `PRODUCT.md` exists → read `#Vision`; you are refining it. Already filled → **re-run** (`MECHANISMS.md` §Re-run semantics): **show what would change and ask before replacing it**; a reversed decision keeps a dated `superseded <date>: <why>` line.
- Code exists, no `PRODUCT.md` → offer `/adopt` first (it drafts the whole spine from the code); the user wants
  only the vision → skim it, say what you infer is being built, and confirm it with the user.
- Neither → start from the template `${CLAUDE_PLUGIN_ROOT}/templates/PRODUCT.md`: `set vision filled --section-from` makes `PRODUCT.md` from it and `--product` makes `STATUS.md` — never read or copy it yourself.
- **The run stops with the gate unmet** (`MECHANISMS.md` §Declined runs) → `status.py set vision declined --reason "<what was missing>" --gate <the phase(s) that fill it>` (`MECHANISMS.md` §Status); change nothing in `PRODUCT.md`.

## Step 1 — Apply principles (this phase)
- **Verify, don't assume:** the user's intent comes from the user — ask. **Benchmark to the current year:** judge the idea against how the market solves this *now*.
- **Plain language**; every choice put to the user is **one recommendation** with a yes/no.

## Step 2 — Guided discovery (ask, then sharpen)
Open by telling the user what to expect: two rounds of questions (the first verdict opens round 2), then one
message of drafts to confirm. **Ask each round in ONE message** — numbered, each question with one example, so a
newcomer does not feel interrogated — and wait for the answers (owner's choice, 2026-10-01: 7 single-question
turns re-sent the whole conversation each time). Where the answers are few (question 5's free /
paid / internal, question 6's AI level), offer them as 2–4 ready choices, the recommended one first
(`CAPABILITIES.md` §Ask the user a question with options). Keep each answer word for word in the conversation:
`docs/vision.md` is written **once, in one call, at Step 3** — never edited after each answer.
**Draft only to sharpen an answer the user gave** (the vision sentence, the term definitions, the job-to-be-done,
the plain words and the worked example), and the user confirms or changes each draft;
**never draft who it's for, the problem, why now, the riskiest assumption or the business model** —
those come from the user, and so do the first users and the AI's accuracy bar and cost. **Who it's for, who asks
and the business model stay as the owner said them** — never narrow or widen them.

**Round 1 — quick: questions 1–3, then a first verdict.**
**In your first reply, with round 1, start the research helper in the background** (Claude: the Agent tool · Cursor: a Task sub-agent ·
   Antigravity: `invoke_subagent` if listed · Codex: `spawn_agent` after round 1, then ONE `wait_agent` in that turn — this skill explicitly asks you to spawn it), brief
   `${CLAUDE_PLUGIN_ROOT}/agents/vision-research.md` (Claude: the `vision-research` agent type - the brief is
   already its instructions: send no path - a logged helper had no read tool and could not open it), given the
   requirement word for word (it names no product or
   user: start it after round 1, with the answers). **It is the only research pass:** never search yourself or
   open its files; when round 1's answers are in, wait for its report. A tool with no helper runs the brief's
   searches itself after round 1, all in one message.
1. **In one line, what is this product and who is it for?** It becomes the **one-sentence vision — the world
   this creates once it works**, not what the product is ("nobody stands at the door guessing the wait", not
   "an app for a waitlist"), drafted in the last message; who it's for stays in the owner's words.
2. **What painful problem does it solve, and why is now the right time?** (regulation, tech shift, cost, new behaviour)
   **Why now is backed by a search** — its line on the search list starts `why now ·`; with no search behind
   it, the record says `why now: the owner's claim, not verified`.
3. **How do people solve this today, and what fails about that?**

Then **benchmark to the current year** with a web search, never from memory: (the helper's findings)
- Name 2–3 **real** comparables and how the market solves this *now*. **The owner's market first:** its players
  and newcomers, searched in its language(s) too (`local ·`), then anywhere (`same job ·`); a product doing
  another task the same way is evidence for the riskiest assumption (`nearby ·`).
- Include **the rules that apply** (data protection, AI law, the sector's law), the users' languages and the
  data source: the `Constraints` field; a rule read from commentary says so.
- **Record every search in `docs/vision.md`, one line each: query · what it settled** · its source link — the
  comparables it verified, the insight it gave, or `nothing found`. The topic starts the line: `why now ·`,
  `local ·`, `same job ·`, `nearby ·`, `rules ·`. **No count on searches:** a search for what users complain about is where a sharpening
  insight comes from. A comparable named without a search gets its own line:
  `<name> · no search — <where the name came from>`. (case file: The search list nobody could check)
  The links are the market read's evidence — never an `evidence:` line that greps a file for the names.
- Surface **one sharpening insight** the user had not stated: an angle, segment or differentiator.
- **First verdict:** what the searches found, the insight, and one call — **go** or **reconsider**, with one
  reason — **at the top of the round 2 message**, never a turn of its own: *"Reply stop to end here, or
  answer 4–7."* Stop → the run stops: record it as `next` says.

**Round 2 — deeper: questions 4–7, in ONE message, under the first verdict** (the helper's findings feed them: a rule it found → ask what it means here).
4. **How will you know it's working?** — the **north star: ask for all five parts in one block** (a bare direction is the usual first answer and is not yet a metric).
   The owner's numbers first; **propose only a part the owner left out**, marked `(proposed)`, and the owner
   confirms or changes it:
   - **Target + date** — "40 restaurants seating 100+ walk-ins a week by 2027-03-31", not "growth".
   - **2–3 input metrics** — numbers that move between events/releases and drive the target. Cadence follows
     the product: weekly for a SaaS, per event for a tool used monthly.
   - **1 guardrail** — what must NOT get worse while chasing it (churn, p95 latency, support load).
   - **Instrumentation** — how it is measured. **Nothing can record it yet → say so plainly: it is a finding.**
   - **Every term in the target and the inputs gets a number** — "active member" = "completed ≥1 chore in the
     last 14 days", "weekly" = "Monday to Sunday" — one row each in the `## North-star terms` table of
     `docs/vision.md` (`| Term | Number | From |`, From = owner · searched · derived · proposed). A definition is
     not a target: a metric the owner set no bar for reads `bar: not set`, or ask once — never invent one.
5. **What's the riskiest assumption** this depends on? And is it **free, paid, or internal**?
6. **Will it use AI?** no · an AI feature (writes text a person uses) · an **agent** (acts on its own: looks up, changes, sends, pays)
   Any AI → one block: what the AI does and what a person decides · how accurate it must be before people
   trust it · what one use may cost.
7. **How will your first 10 users find it, and why would they switch from today's way?**

Then **ONE message of drafts** the user confirms or changes in one reply — the vision sentence, any part or term
marked `(proposed)`, and:
- Frame the **job-to-be-done**: "when <situation>, I want to <motivation>, so I can <outcome>". The situation and who asks as the owner said them.
- Draft **In plain words** and one **worked example** from the user's answers. A number
  in the example that is not the owner's is marked `(illustrative)`.
- Give **one recommendation** on the framing, any clash (Step 3c: README purpose, an earlier record; numbers
  against each other), and *"Anything to change? If not: Save this version of your project? (yes / no)"* - either answer records it; never a turn of its own.

## Step 3 — Write `docs/vision.md` once, then `PRODUCT.md`
**`docs/vision.md` in one call:** plain `##` sections a founder reads in order — vision and plain words · who ·
problem (+ a "How it happens" paragraph, linked) · why now · today · how we will know · riskiest assumption
(+ evidence for and against, linked) · business model · AI · rules, languages, data
· competitors (table: product · market · does · does not · same job / nearby; owner's market first) ·
boundaries · sources; then `## Appendix`: `### Owner's answers` (word for word) · `### Search list` ·
`### North-star terms`.

Fill every `#Vision` field `next` printed, each one line `- **<label>:** <value>`, in a scratch file outside the repo, **in the same message as `docs/vision.md`**. Leave `UI` alone: `/architect` decides it. Then ONE call: `set vision filled --section-from <file> --ai yes|no --agent yes|no --commit "<one line>"` (+ `--product "<name>"` on a new project; no `--commit` on a no) writes `PRODUCT.md`, records the AI flag, fills the `Read:` line from `README.md` and saves.

## Step 3b — Principle-gate: verify it's sharp, not fuzzy
Walk the exit criteria. Check every named comparable **against the search list in `docs/vision.md`**: a search
settled it, or it has its own no-search line; a name on neither → search it, or record where it came from.
`set vision filled` refuses the countable ones below, every problem in one list: fix what it names, never
the check. **STOP and fill it with the user** when a field is empty, or when:
- the north star lacks its target, date, input metrics, guardrail or instrumentation line, or a row of the north-star terms table has no number;
- a terms row has no `From`, a search line has no link, or the list has no `local ·`, `same job ·` or `rules ·` line;
- the search list has no line starting `why now ·` and `Problem (why now)` does not say `the owner's claim, not verified`;
- who it's for, who asks or the business model differ from `## Owner's answers`;
- the vision sentence describes the product instead of the world it creates, or promises more than the target;
- the first verdict denies a same-job product a later search found;
- the job-to-be-done or the riskiest assumption names no user, situation or behaviour of this product.

**Receipts and size** (`MECHANISMS-ON-DEMAND.md §Section is a record`, `MECHANISMS-ON-DEMAND.md §Read receipt`): `set` prints the size and writes the `README.md` line; another companion you opened gets a quote. Reasoning moves into the companion, never trim to a number; a warning after a passing `set` needs no re-run.

**Close the loop (`MECHANISMS.md` §Step 3b):** the checklist `set vision filled` prints: the save was the yes (`MECHANISMS.md` §Commit the work); **run the transition guard** (§Step 3b, item 4): a verdict per exit criterion, `UNVERIFIED` is normal, silence is not; **close in plain language** (`MECHANISMS.md` §Plain-language close): **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next**, ending with its `Open a NEW conversation` line word for word.

## Step 3c — Contradiction check (in the drafts message, before the yes; the close's step 3 confirms it)
Per `MECHANISMS.md` §Step 3c, compare against what is **already recorded**: the `README.md`/`CLAUDE.md` purpose and any prior `#Vision` (`set` prints the README's). A change to the customer, the north star or the business model is a conflict → **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line). Added detail is not a contradiction.

## Step 4 — Handoff
"Vision captured in `PRODUCT.md`. Next run **`/scope`** to lock the ONE core feature and what stays out.
Want real-world evidence for the riskiest assumption first? **`/validate`** is optional: the cheapest
experiment — days of evidence before months of code."
