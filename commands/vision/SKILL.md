---
name: vision
description: Define who it is for, the problem, why now and how success is measured.
---

# `/vision` — Phase 1 · Product · run as a **product developer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the variable is the folder two levels above this SKILL.md, holding `commands/` and `PRINCIPLES.md` - never another tool's install). If `python` will not start (not found, or a sandbox refuses it): the project's `.venv` Python, else `python3`, else `py -3` - never a hunt; later commands use the start's `Run this copy as` line.
> **`status.py next --phase vision` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it); the rest of the close prints when `set vision filled` passes. Load-bearing here: **vision-alignment**, **verify-don't-assume**,
> **benchmark-to-current-year**, **plain-language communication**.

## Contract
- **Purpose:** turn a rough idea into a sharp, benchmarked product vision.
- **Reads:** nothing required (this is the first phase) — or an existing `PRODUCT.md`/codebase if present.
- **Writes:** ONE fields file; `set vision filled --from-fields` renders `PRODUCT.md#Vision` (the summary every later phase reads) and `docs/vision.md` (the story for people) from it · `STATUS.md` with the AI flags.
- **Gate type:** `input` — who it is for, the job, the north star - the answers exist only in the user's head. **Never batched** - skipping it fabricates the product's premise. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Vision` · `declined` ✓ · `override` n/a — `/vision` opens the chain; there is no prior section to bypass · `superseded` ✓
- **Companion:** `docs/vision.md` — **the document a founder reads**, rendered from the same fields as
  `PRODUCT.md#Vision` (Step 3): each fact is typed once.
- **Exit criteria:**
  - [ ] A single sentence vision (the world this product creates). → `Vision (ONE sentence`
  - [ ] **In plain words** (2–3 sentences) and one **worked example** with names and numbers — a newcomer understands the product from these alone. → `In plain words` · `Worked example`
  - [ ] Named target user + the concrete problem they have, and **why now** — backed by a recorded search, or marked `the owner's claim, not verified`. → `Who it's for` · `Problem (why now)`
  - [ ] Who it's for, who asks and the business model are the owner's words or picked options (`## Owner's answers`). → `Who it's for` · `Business model`
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
- **First turn, ONE command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase vision`** — it prints the start and this phase's rules; never the rule files, the template or `PRODUCT.md` whole. Show its first line; close by its checklist. Load your web-search tool in the same turn. `next` says **fresh start** → ask question 1.
- `PRODUCT.md` exists → `next` prints `#Vision`; you are refining it.
- Code exists, no `PRODUCT.md` → offer `/adopt` first (it drafts the spine from the code); the user wants
  only the vision → skim it, say what you infer is being built, and confirm it with the user.
- Neither → `set vision filled --from-fields` makes `PRODUCT.md` (its title, the project policy and `#Vision`) and `--product` makes `STATUS.md` — never read or copy a template yourself.
- **Anything unusual** (a re-run of a filled `#Vision`, a run that stops with the gate unmet): `next` prints the rule and the command for it only when it is true - follow it as printed.

## Step 1 — Apply principles (this phase)
- **Verify, don't assume:** the user's intent comes from the user — ask. **Benchmark to the current year:** judge the idea against the market *now*.
- **Plain language.** **Every question: 2–4 options + Recommended (first, one-line reason) + Other** (`CAPABILITIES.md` §Ask the user a question with options), built from the brief, the answers and the research. The one open question: "what's your idea?" when the user gave nothing.

## Step 2 — Guided discovery (ask, then sharpen)
Tell the user what to expect: two rounds of questions (the first verdict opens round 2; the drafts are options
inside round 2), then the save - three owner turns. **Ask each round in ONE message or form** and wait. Keep each answer word for word in the conversation:
the fields file is written **once, in one call, at Step 3** — never edited after each answer.
**A brief (the idea is longer than one sentence: a challenge, a pasted doc): for each round-1 question, if the input
contains an answer, quote it under `From your brief:` instead of asking**; ask only the gaps. **Never ask for a
researchable fact** (how it is solved today, competitors, prices, rules): the market check finds it.
**Never decide who it's for, the problem, why now, the riskiest assumption or the business model** — **propose**
additions and alternatives as options (extra segments, the business's own users, the scale, root
causes, other risks), built from the brief, the answers and the research; only what the user picks goes in, and a
picked option is recorded under `## Owner's answers` as `picked: <option text>`. Nothing changes silently.
**Every option is a complete answer:** a number as concrete values, plus `I don't know yet - work it out in <phase>`;
never "specify your X"; alternatives are one pick.

**Round 1 — quick: questions 1–2, then a first verdict.**
**Your first tool call, before you write round 1, starts the research helper in the background** (Claude: the Agent tool · Cursor: a Task sub-agent ·
   Antigravity: `invoke_subagent` if listed · Codex: `spawn_agent` after round 1, then ONE `wait_agent` in that turn — this skill explicitly asks you to spawn it), brief
   `${CLAUDE_PLUGIN_ROOT}/agents/vision-research.md` (Claude: the `vision-research` agent type - the brief is
   already its instructions: send no path), given the
   idea or brief word for word (the user gave no idea: start it with round 1's answers). **It is the only research pass:** never search yourself or
   open its files; when round 1's answers are in, wait for its report. A tool with no helper runs the whole
   brief itself after round 1 - its searches, then its page opens, each set in one message.
1. **Who is it for, and what does it make possible?** It becomes the **one-sentence vision — the world
   this creates once it works**, not what the product is ("nobody stands at the door guessing the wait", not
   "an app for a waitlist"), offered as options in round 2.
2. **What painful problem does it solve, and why is now the right time?** (regulation, tech shift, cost, new behaviour)
   **Why now is backed by a search** — its line on the search list starts `why now ·`; with no search behind
   it, the record says `why now: the owner's claim, not verified`.

Then **benchmark to the current year** with a web search, never from memory: (the helper's findings)
- Name 2–3 **real** comparables and how the market solves this *now*. **The owner's market first:** its players
  and newcomers, searched in its language(s) too (`local ·`), then anywhere (`same job ·`); a product doing
  another task the same way is evidence for the riskiest assumption (`nearby ·`).
- Include **the rules that apply** (data protection, AI law, the sector's law), the users' languages and the
  data source: the `Constraints` field; a rule read from commentary says so.
- **Record every search in the `searches` field of the fields file, one line each: query · what it settled** · its source link — the
  comparables it verified, the insight it gave, or `nothing found`. The topic starts the line: `why now ·`,
  `local ·`, `same job ·`, `nearby ·`, `rules ·`. **No count on searches:** a search for what users complain about is where a sharpening
  insight comes from. A comparable named without a search gets its own line, no link needed:
  `<name> · no search — <where the name came from>` (or `Not searched · <gap>`). (case file: The search list nobody could check)
  The links are the market read's evidence, never an `evidence:` line grepping a file.
- Surface **one sharpening insight** the user had not stated: an angle, segment or differentiator.
- **First verdict:** what the searches found, the insight, and one call — **go** or **reconsider**, with one
  reason — **at the top of the round 2 message**, never a turn of its own: *"Reply stop to end here, or
  answer 3–6."* Stop → the run stops: record it as `next` says. Then **How it is solved today** as a table from
  the findings (approach · who · where it falls short), the user picking from them, never typing them.

**Round 2 — deeper: questions 3–6 and the drafts, in ONE message, under the first verdict** (the helper's findings feed them: a rule it found → ask what it means here; why-now points and root causes it found → options).
3. **How will you know it's working?** — the **north star: ask for all five parts in one block** (a bare direction is the usual first answer and is not yet a metric).
   The owner's numbers first; **offer only a part the owner left out**, as options marked `(proposed)`:
   - **Target + date** — "40 restaurants seating 100+ walk-ins a week by 2027-03-31", not "growth".
   - **2–3 input metrics** — numbers that move between events/releases and drive the target. Cadence follows
     the product: weekly for a SaaS, per event for a tool used monthly.
   - **1 guardrail** — what must NOT get worse while chasing it (churn, p95 latency, support load).
   - **Instrumentation** — how it is measured. **Nothing can record it yet → say so plainly: it is a finding.**
   - **Every term in the target and the inputs gets a number** — "active member" = "completed ≥1 chore in the
     last 14 days", "weekly" = "Monday to Sunday" — one row each in the `terms` field
     (`| Term | Number | From |`, From = owner · searched · derived · proposed). A definition is
     not a target: a metric the owner set no bar for reads `bar: not set`, or ask once — never invent one.
4. **What's the riskiest assumption** this depends on? And is it **free, paid, or internal**?
5. **Will it use AI?** no · an AI feature (writes text a person uses) · an **agent** (acts on its own: looks up, changes, sends, pays)
   Any AI → one block: what the AI does and what a person decides · how accurate it must be before people
   trust it · what one use may cost.
6. **How will your first 10 users find it, and why would they switch from today's way?**

**The drafts are options inside round 2** (never a message of their own), answered with letters (`1b 2a`) or
clicks (a question form that takes 4 at a time: one form per 4 questions, all in the same reply): **every drafted
choice shows 3 options, the Recommended one first, + Other** — the vision sentence (3 genuinely different angles), the name, the
**job-to-be-done** ("when <situation>, I want to <motivation>, so I can <outcome>"), any target or term marked
`(proposed)`. Also **In plain words** and one **worked example** from the answers (a number that is not the
owner's is `(illustrative)`), and any clash (Step 3c: README purpose, an earlier record; numbers against each other)
as options. No save question: round 2's answers are the go-ahead to write and save; the close asks *"Change anything?"*.

## Step 3 — Write ONE fields file; the script renders both documents
**Write the fields `next` printed — `### <field>` and its text — in ONE call, in a scratch file outside the repo**
(never `docs/vision.md` or `PRODUCT.md` yourself, never a template). `[n]` only on a sourced claim, never on the
owner's answers or an invented example (`(illustrative)`). A field's first line is its plain takeaway; the
script lays out `docs/vision.md` and `PRODUCT.md#Vision` from the same fields. Leave `UI` alone: `/architect` decides it. Then ONE call: `set vision filled --from-fields <file> --ai yes|no --agent yes|no --commit "<one line>"` (+ `--product "<name>"` on a new project; `--no-commit` only when the user said not to save) renders both, records the AI flag, fills the `Read:` line from `README.md` and saves. A refusal lists every missing field at once.

## Step 3b — Principle-gate: verify it's sharp, not fuzzy
Walk the exit criteria. Check every named comparable **against your `searches` field**: a search
settled it, or it has its own no-search line; a name on neither → search it, or record where it came from.
`set vision filled` refuses the countable ones below, every problem in one list: fix what it names, never
the check. **STOP and fill it with the user** when a field is empty, or when:
- the north star lacks its target, date, input metrics, guardrail or instrumentation line, or a row of the north-star terms table has no number;
- a terms row has no `From`, a search line has no link, or the list has no `local ·`, `same job ·` or `rules ·` line;
- the search list has no line starting `why now ·` and `Problem (why now)` does not say `the owner's claim, not verified`;
- who it's for, the problem, why now, the riskiest assumption or the business model contains anything the user did not give or pick (`## Owner's answers`);
- the vision sentence describes the product instead of the world it creates, or promises more than the target;
- the first verdict denies a same-job product a later search found;
- the job-to-be-done or the riskiest assumption names no user, situation or behaviour of this product.

**Receipts and size** (`MECHANISMS-ON-DEMAND.md §Section is a record`, `MECHANISMS-ON-DEMAND.md §Read receipt`): `set` prints the size and writes the `README.md` line; another companion you opened gets a quote in the `read` field; never trim to a number; a warning after a passing `set` (a plain-words estimate) needs no re-run.

**Close the loop (`MECHANISMS.md` §Step 3b):** the checklist `set vision filled` prints: the save was the yes (`MECHANISMS.md` §Commit the work); **run the transition guard** (§Step 3b, item 4) in one line: what the save checked, what is judged (`UNVERIFIED` is normal, silence is not); **close in plain language** (`MECHANISMS.md` §Plain-language close), 7 lines in all, as `set` prints them: the guard line, then `Saved (commit ...).`, then the four blocks, one line each under its bolded name: **What just happened** and **What I skipped or couldn't do** (the document linked, never restated), **Test this yourself**: `Nothing to test by hand in this phase.`, **What YOU do next**: `Change anything? If not:` - and last the `Open a NEW conversation` line, copied whole to its last word.

## Step 3c — Contradiction check (in round 2 with the drafts, before the yes; the close's step 3 confirms it)
Per `MECHANISMS.md` §Step 3c, compare against what is **already recorded**: the `README.md`/`CLAUDE.md` purpose and any prior `#Vision` (`set` prints the README's). A change to the customer, the north star or the business model is a conflict → **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line). Added detail is not a contradiction.

## Step 4 — Handoff
"Vision saved. Next run **`/scope`** to lock the ONE core feature and what stays out.
Untested riskiest assumption? **`/validate`** (optional) tests it cheaply first."
