---
name: architect
description: Choose the stack, hosting, data and AI approach, with recorded decisions.
---

# `/architect` — Phase 2 · Development ① · run as an **architect**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` · AGENT.md = `${CLAUDE_PLUGIN_ROOT}/references/agent.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **This skill's OWN reference files are a DIFFERENT folder** — they live in `references/` **beside this SKILL.md** (`commands/architect/references/`), not in the plugin-root `references/` named above. Both install routes put them there. Below, `decisions.md` · `edge-cases.md` each mean that folder: open them by that path, and never look for them next to MECHANISMS.md.
> **`status.py next --phase architect` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** (and AGENT.md §Architect when `Agent: yes`) — apply them; never open the whole files (a situational companion only when a rule points into it); the close's sections print when `set architect filled` passes. Load-bearing this phase: Step 1, and **resilience strategy**, **perf/cost budget**, **migrations (not raw schema)**, **layered/decoupled**.

## Contract
- **Purpose:** choose the stack/tools/decisions before any folders exist, aligned to the product.
- **Reads:** `PRODUCT.md#Vision`, `#Scope`, `#Plan` — as `next` prints them.
- **Writes:** ONE fields file (outside the repo); `set architect filled --from-fields <file>` renders from it `PRODUCT.md#Architecture` (the AI's summary: stack+tools+why · **dev tooling** · key decisions · externals behind adapters · resilience · perf/cost budget · (AI) prompt-versioning/eval) and `docs/architecture.md` (the human story, numbered headings, the workings in the appendix). Each fact is written once. **No ADR file on a first run:** `docs/adr/NNNN-<slug>.md` only when a recorded decision changes later.
- **Gate type:** `input` — the choice is made against the project's constraints - team size, operational appetite, budget, tolerable lock-in - and those live in the human. **Never batched** - skipping it fabricates the product's premise. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Architecture` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Exit criteria (the gate — small: is the section complete?):** `set architect filled` checks every countable one and names each gap in one refusal; what reads words is a warning.
  - [ ] `#Architecture` is complete and **traces to scope/plan** (no gold-plating; every #Plan milestone has a row in Mapping to the plan, every #Scope "in now" item a home): stack+tools+why **with
    a provenance flag on every row** and **the constraint set each choice was optimised against** (Step 1);
    every external behind an adapter; the key decisions (patterns applied / anti-patterns avoided); the migrations
    approach; a **custody + runtime target** line (data custody · **a runtime target for each deployable
    unit** · identity custody, each a decision or an explicit N/A); a **Dev tooling** line naming hook runner ·
    secret scanner · task runner · formatter/linter · dependency manifest; and the
    **decisions for the concern areas this product needs** — resilience · perf/cost budget ·
    security/no-secret-in-code · observability **+ (AI) prompt-versioning · eval · tracing · model runtime
    config** — each recorded or marked **N/A**; **`Agent: yes`: every AGENT.md §Architect row** in the (Agent) field, recorded or `N/A — <reason>`.

## Step 0 — Context + prior-gate check
- **One first command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase architect`** — it prints the `#Vision`, `#Scope` and `#Plan` lines the stack is chosen against, what `set` refuses and the rules; never open those files or `PRODUCT.md` whole. Show its first line. No research helper on your tool: load your web-search tools in the same call. After it, never re-open this SKILL.md or a start file; a `flag` or `quote` rides with the next real step, never a call of its own.
- `#Scope`/`#Plan` empty → warn and offer to run them first (allow
  override).
- Brownfield: detect the existing stack from the repo and record it as the starting point.
- **Anything unusual — an upstream gate still `running`, an override, a narrow run for another phase, the chain, a re-run, stopping at an unmet gate, a refusal the user says does not apply:** open `references/edge-cases.md` (beside this SKILL.md) for that case; a normal first run never opens it.

## Step 1 — Apply principles (this phase)
- **Benchmark to the current year, then choose on constraints:** find what leading teams use *now*. Then pick on **fit, not ideology**: reliability, operational burden, **the size of the team that has to run it**, cost, compatibility, maturity, and **lock-in (portability + exit cost)**. (Open source vs self-hosting: decisions.md §Custody.) **Record the constraint set you optimised against** and why the winner won — the `constraints` field and one `why` per decision.
- **Search discipline — a helper, two turns, bounded:** after round 1, ONE call starts the research helper `next` names (brief `${CLAUDE_PLUGIN_ROOT}/agents/architect-research.md`; its own context keeps the pages out of this conversation), waited for, with `status.py fields architect` in the same message; its search lines go into the `searches` field. A tool with no helper runs the two turns itself. **Turn A:** **one search per open decision row** (AI product: the model row gets two - a free local model and a paid API - so the table prices both), all in one turn after round 1, naming the need, never a vendor or framework. **Turn B:** one page open per fact the record needs (the registry page for a version, the pricing page, the model page), all in one turn, at most 12. Cite the page opened, one quoted line per fact, never a search hit. No third turn. **The search list goes in `docs/architecture.md`** (the `searches` field: query · what it settled). A search that settled nothing is not benchmark evidence. The bound never lowers a verdict — a row still open says so. Current facts (model names and release dates, prices, free tiers, versions) come from this run's pages, never from memory.
- **Check where approvals attach (the self-host blind spot):** where an integration is gated by a third
  party's approval, ask *"does it attach to the app/account, or to the software?"* If it attaches to the
  app, **self-hosting OSS does not bypass it** — OSS saves code, not compliance
  (`references/decisions.md` §Where approvals attach).
- **Patterns & anti-patterns awareness:** the established patterns for this kind of system *and* its anti-patterns (god-objects, vendor coupling, dead config, N+1 / a blocked event loop, a distributed monolith).
- **Provider/adapter for every external:** no vendor SDK in business logic — wrap it behind a config-selected interface so it's swappable via `.env`.
- **No-hardcoding & typed contracts:** decisions must keep values in config and payloads typed.

## Step 2 — Guided decisions, in two rounds
**Round 1: all questions in ONE turn**, through your question tool (4 questions per call, so several calls in that same message), else numbered options in one message. **Every question: 2–4 options, ONE marked (Recommended) with its reason in one line, plus Other.** The Recommended option is the one a spine line points to (that line is the reason); with no spine line: 3 → managed only · 4 → portable only · 5 → EU only · 6 → don't know · 1, 2, 7 → *I don't know yet - work it out in /architect* · 8 → only write text. Never a stack technology, host, model, version or price as an option here (question 6's login providers are fine) — those come after the searches (round 2). Numbered as written: **1.** who builds and runs it (people, hours a week, languages they know) · **2.** money a month for hosting and AI at the start · **3.** infrastructure they will run (managed only · some · self-host) · **4.** lock-in they accept (any vendor · portable only) · **5.** where the data must be processed, including what is sent to the AI model (EU only · anywhere while the data is fake) · **6.** which login people use (Entra ID · Google · Okta · don't know · none: its own accounts) · **7.** anything already chosen (a host, a language, a tool) · **8.** only with **`Agent: unknown` on an AI product** (`next` says so): *"Does the AI act on its own - look records up, change them, send messages, move money - or only write text a person sends?"* → `status.py flag --agent yes|no`. An answer `next` printed from the spine is the Recommended option to confirm, never asked blank. Answers 1-7 go word for word into the `constraints` field. Money (answer 2) is a budget, never a model choice: "€0 to start" does not by itself pick a free model.
Then decide, with Step 1's two research turns:
1. **What kind of system is it?** (web app · API · CLI · data/ML · agentic). Match the scope, not ambition.
   Note whether it has a **user-facing UI** and record it — `status.py flag --ui yes|no` (`MECHANISMS.md`
   §Status) — it decides whether `/design-system` runs.
   Then name the **2–3 design patterns** that fit it and the **2–3 anti-patterns** to avoid (current-year), and how this design honours/avoids them — the notable ones are decisions.
2. **Choose the stack core** (language · framework · datastore · key libs). One-line why each; flag
   anything paid and its trigger to adopt. **Two rules on how the rows are recorded:**
   - **Every row carries its provenance** — `user-chosen` or `default taken, not user-chosen`, no third value ("go with your recommendation" is `default taken`).
   - **A UI-tooling constraint binds the UI only.** React/shadcn decides what `frontend/` is written in and
     says **nothing** about the server language. (case file: One app by accident)
3. **Custody + runtime target, from answers 5 and 6 - never asked again** (`references/decisions.md` §Custody, runtime and identity holds the trade-offs): *Where does the data live?*
   (local/self-hosted · managed-serverless · embedded), the model call inside answer 5 · *Where does each part run?* — **list the
   deployable units first** (the site, the API, a worker, a forwarder) and record a runtime target for EACH
   (container-anywhere · a PaaS · a VPS · the user's machine · a static site / CDN) · *Who holds identity?*
   (answer 6's login - a stable user id, a role, fail closed - else self-hosted vs vendor auth + RLS; N/A only when nobody logs in). Explain in one plain line
   what running it somewhere means for this product.
   **A host the user already chose still gets its facts** — cost, free-tier limits and what happens AT each, 2–3 alternatives (decisions.md §Custody). (case file: "Is it free?")
4. **List every external** and the **adapter interface** it hides behind (LLMProvider, Storage: plain names, backticks only around a path) — *and*
   its **failure/resilience strategy** (timeouts · retry-transient-only · fallback/circuit-breaker).
5. **Set a rough perf/cost budget** (latency + cost-per-operation) or mark **N/A**. **Derive it from the dominant cost, don't guess:** the single most
   expensive step (an LLM call, a network hop), budgeted from a quick probe of *that*, or written as **explicitly aspirational**, re-measured in `/eval`.
6. **Name the dev tooling** — hook runner (pre-commit · lefthook · husky) · secret scanner · task runner
   (`make` · npm scripts · just) · formatter/linter · dependency manifest · type checker (Python or TypeScript: always one; a compiled language: its compiler). `/structure` scaffolds exactly these. Pick them from the stack you
   just chose, one line of why each.
7. **If it's an AI product:** decide **prompt-versioning**, an **eval harness**, **LLM tracing** and the
   **model runtime config** as decisions. **Free or paid model is the user's choice** - round 2 asks it (below). The model row names the model and its **release date** from its search; older than 12 months needs a stated reason. **Tie the Step-5 budget to the recorded runtime config** (thinking effort, `max_tokens`, timeout, streaming, retry and refusal fallback, caching — `references/decisions.md` §AI runtime config); the `cost per use` field holds the numbers (tokens, prices per 1M from this run's page) and the script works the cost out and checks it against `#Vision`'s cap. **`Agent: yes`:** decide AGENT.md §Architect's ten rows (`next` prints them); the framework row gets its search like any stack row.
8. **The decisions, written once:** 4–10 blocks in the `decisions` field, the most consequential first, each clear on its own: the decision · the problem it solves · the options considered · why this one · what it costs or rules out · when to revisit · its provenance. They render into `docs/architecture.md` §Decisions and one line each in `#Architecture`. **No ADR file on a first run.** A spine with inline legacy ADRs: `references/decisions.md` §Legacy ADRs.
- **Round 2, ONE message:** **one recommendation** for the stack — a table of the rows, each with its why, the host's facts (item 3) and (`Agent: yes`) the framework table AGENT.md row 1 asks for — any clash with `#Scope` or `#Plan` that no answer this run decided (Step 3c), then the question form: **(AI product) the model, as its own question:** *a free local model* (runs on the machine, €0, weaker) · *a paid API* (this run's price × the product's scale = its monthly cost, against `#Vision`'s cap), each saying where the data is processed (answer 5), one (Recommended) with its reason - the answer replaces the table's model row; then *"Keep this stack (Recommended)"* (the other rows) · *"Change a row"* · *"Other"* - a keep is the go-ahead to write and save; no separate save question. Keep it plain — explain *why* for a newcomer. A row the user picks is `user-chosen`; a yes to your recommendation is `default taken, not user-chosen`.

## Step 3 — Write back to `PRODUCT.md`
**The section is a RECORD, not a container** (`PRINCIPLES.md`): `#Architecture` is rendered — one line per decision and the pointer to `docs/architecture.md`. On the yes, ONE message: the fields file (the shape `status.py fields architect` printed), `status.py flag --ui yes|no` if unknown, then `status.py set architect filled --from-fields <file>` — it renders both files, writes each `plan notes` line as a dated note on its `#Plan` line and each `open items` line into STATUS.md, works out the cost per use, checks, and saves (`--no-commit` only when the user said not to save). Refused: fix the fields file, run the same command. Never an edit tool on `PRODUCT.md` or `docs/architecture.md`, never a template opened, never an ADR by hand.

## Step 3b — Principle-gate and close
Walk this phase's load-bearing principles (Step 1) and confirm each is **concretely decided**, not hand-waved — `set` refuses a missing field, an external row with no adapter interface or no resilience cell, a decision missing a part; you judge the rest: patterns/anti-patterns are *addressed by the design*, not just listed; secrets go to `.env` (none in code); each tooling slot fits the stack. **If any is vague or missing, STOP and decide it.**

**Close the loop (`MECHANISMS.md` §Step 3b):** the checklist `set architect filled` prints (refused: fix every named gap, run it again): the save was the yes (`MECHANISMS.md` §Commit the work); **the transition guard** (`MECHANISMS.md` §Step 3b, item 4) on ONE line: `Checked by the save: <what set counted> - judged, not checked: <the exit criteria about wording and quality>`; never 100%, and UNVERIFIED (judged, not checked) is a normal outcome; **Close in plain language** (`MECHANISMS.md` §Plain-language close), 8 lines in this order: the guard line · `Saved (commit <hash>).` when `set` saved · one line each (`docs/architecture.md` linked, never restated): **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next** · then its last two lines, word for word: `Change anything? If not:` and the `Open a NEW conversation` line. The save took every file: `git status` is clean at the end.

## Step 3c — Contradiction check (in round 2, before the yes; the close's step 3 confirms it)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Scope` and `#Plan` — a stack sized for work that is explicitly out of scope is gold-plating, and a perf/cost budget must not contradict `#Vision`'s business model (paid infra against a free product). **The user's answer this run wins:** an answer that changes `#Plan` or `#Scope` (a laptop instead of a web address, a paid model instead of a free one) is never a "which side wins?" question — write it as a `plan notes` line (the save adds the dated `superseded` note to that line) and tell the user in one line. A conflict no answer this run decided: **name both sides on a line of their own, ask nothing, never edit `#Scope` or `#Plan`** — write it in the fields file as an `open items` line `- Clash: <both sides> | /<that phase> decides`. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Stack and decisions recorded. Next, **`/structure`** lays out the folders — or, when the user asked for the chain, it starts now."
