---
name: architect
description: >
  Phase 2 (Development), step 1 of product-playbook. Decide the tech stack + tools + key
  architecture decisions, benchmarked to current-year options and chosen against the project's
  own constraints. Use at the start of building, or run /architect "what stack", "tech
  decisions", "how should we build this". Writes the Architecture section of PRODUCT.md.
  Run /structure next.
---

# `/architect` — Phase 2 · Development ① · run as an **architect**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` · AGENT.md = `${CLAUDE_PLUGIN_ROOT}/references/agent.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **This skill's OWN reference files are a DIFFERENT folder** — they live in `references/` **beside this SKILL.md** (`commands/architect/references/`), not in the plugin-root `references/` named above. Both install routes put them there. Below, `decisions.md` each mean that folder: open them by that path, and never look for them next to MECHANISMS.md.
> **`status.py next --phase architect` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** (and AGENT.md §Architect when `Agent: yes`) — apply them; never open the whole files (a situational companion only when a rule points into it); the close's sections print when `set architect filled` passes. Load-bearing this phase: Step 1, and **resilience strategy**, **perf/cost budget**, **migrations (not raw schema)**, **layered/decoupled**.

## Contract
- **Purpose:** choose the stack/tools/decisions before any folders exist, aligned to the product.
- **Reads:** `PRODUCT.md#Vision`, `#Scope`, `#Plan` — as `next` prints them.
- **Writes:** `PRODUCT.md#Architecture` — stack+tools+why · **dev tooling** · ADRs · externals behind adapters · resilience · perf/cost budget · (AI) prompt-versioning/eval · `docs/architecture.md` (an overview with ONE diagram, the decisions, then the workings: the user's answers word for word, the search list, the framework table) · `docs/adr/*`.
- **Gate type:** `input` — the choice is made against the project's constraints - team size, operational appetite, budget, tolerable lock-in - and those live in the human. **Never batched** - skipping it fabricates the product's premise. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Architecture` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Exit criteria (the gate — small: is the section complete?):** `set architect filled` checks every countable one and names each gap in one refusal.
  - [ ] `#Architecture` is complete and **traces to scope/plan** (no gold-plating): stack+tools+why **with
    a provenance flag on every row** and **the constraint set each choice was optimised against** (Step 1);
    every external behind an adapter; key ADRs (patterns applied / anti-patterns avoided); the migrations
    approach; a **custody + runtime target** line (data custody · **a runtime target for each deployable
    unit** · identity custody, each an ADR or an explicit N/A); a **Dev tooling** line naming hook runner ·
    secret scanner · task runner · formatter/linter · dependency manifest; and the
    **decisions for the concern areas this product needs** — resilience · perf/cost budget ·
    security/no-secret-in-code · observability **+ (AI) prompt-versioning · eval · tracing · model runtime
    config** — each recorded or marked **N/A**; **`Agent: yes`: every AGENT.md §Architect row** in the (Agent) field, recorded or `N/A — <reason>`.

## Step 0 — Context + prior-gate check
- **One first command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase architect`** — it prints the `#Vision`, `#Scope` and `#Plan` lines the stack is chosen against, the `#Architecture` fields, what `set` refuses and the rules; never open those files or `PRODUCT.md` whole. Show its first line. Load your web-search tools in the same call. After it, never re-open this SKILL.md or a start file; a `flag` or `quote` rides with the next real step, never a call of its own.
- `#Scope`/`#Plan` empty → warn and offer to run them first (allow
  override). **A `running` upstream gate BLOCKS from here on** (`STATE-MODEL.md` §2a): a
  pending result needs the result, or a recorded override.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then record it — `status.py bypass --from architect --gate <gate> --reason "<the user's own words>"` (`MECHANISMS.md` §Status) — before continuing.
- Brownfield: detect the existing stack from the repo and record it as the starting point.
- **A NARROW run — one decision, called from another phase** (`/deploy` finds a unit with no runtime
  target): decide that row only — its search, its provenance, one line in `#Architecture` (an ADR
  if load-bearing) — then hand back: no chain or commit offer, no close, no state recorded, no full-section exit criterion; the calling phase's close reports it. (case file: Two closes in one run)
- **Offer the chain, never default to it** (`MECHANISMS-ON-DEMAND.md` §Batch mode, *chain*), as the last question of round 1: *"Stop after
  the architecture (default), or continue straight into `/structure` in this session — every question
  still asked, two records, two commits, one close at the end?"* A red gate here never reaches `/structure`.
- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** a filled section → follow the `RE-RUN` line `next` prints: **one question listing what would change**, never a silent overwrite; a reversed decision keeps a dated `superseded <date>: <why>` line.
- **The gate is unmet and the run stops here (`MECHANISMS.md` §Declined runs):** `status.py set architect declined --reason "<what was missing>" --gate <the phase(s) that fill it>` (`MECHANISMS.md` §Status) — and change nothing in `PRODUCT.md`.

## Step 1 — Apply principles (this phase)
- **Benchmark to the current year, then choose on constraints:** find what leading teams use *now*. Then pick on **fit, not ideology**: reliability, operational burden, **the size of the team that has to run it**, cost, compatibility, maturity, and **lock-in (portability + exit cost)**. (Open source vs self-hosting: decisions.md §Custody.) **Record the constraint set you optimised against** and why the winner won — one line each, in `#Architecture`.
- **Search discipline — two turns, bounded:** **Turn A:** **one search per open decision row**, all in one turn after round 1, naming the need, never a vendor or framework. **Turn B:** one page open per fact the record needs (the registry page for a version, the pricing page, the model page), all in one turn, at most 12. Cite the page you opened, one quoted line per fact, never a search hit. No third turn. **The search list goes in `docs/architecture.md`** (query · what it settled). A search that settled nothing is not benchmark evidence. The bound never lowers a verdict — a row still open says so. Current facts (model names and release dates, prices, free tiers, versions) come from this run's pages, never from memory.
- **Check where approvals attach (the self-host blind spot):** where an integration is gated by a third
  party's approval, ask *"does it attach to the app/account, or to the software?"* If it attaches to the
  app, **self-hosting OSS does not bypass it** — OSS saves code, not compliance
  (`references/decisions.md` §Where approvals attach).
- **Patterns & anti-patterns awareness:** the established patterns for this kind of system *and* its anti-patterns (god-objects, vendor coupling, dead config, N+1 / a blocked event loop, a distributed monolith).
- **Provider/adapter for every external:** no vendor SDK in business logic — wrap it behind a config-selected interface so it's swappable via `.env`.
- **No-hardcoding & typed contracts:** decisions must keep values in config and payloads typed.

## Step 2 — Guided decisions, in two rounds
**Round 1: ask these in ONE message, numbered as written, and recommend nothing before the answers** - every row is chosen against them: **1.** who builds and runs it (people, hours a week, languages they know) · **2.** money a month for hosting and AI at the start · **3.** infrastructure they will run (managed only · some · self-host) · **4.** lock-in they accept (any vendor · portable only) · **5.** where the data must be processed, including what is sent to the AI model (EU only · anywhere while the data is fake) · **6.** which login people use (Entra ID · Google · Okta · don't know · none: its own accounts) · **7.** anything already chosen (a host, a language, a tool) · **8.** only with **`Agent: unknown` on an AI product** (`next` says so): *"Does the AI act on its own - look records up, change them, send messages, move money - or only write text a person sends?"* → `status.py flag --agent yes|no` · **last:** the chain offer (Step 0). Record 1-4 as the constraint set; 5 and 6 decide item 3. An answer `next` printed from the spine is shown as the answer to confirm, never asked blank. Each question has 2–4 ready choices and room for their own words.
Then decide, with Step 1's two research turns:
1. **What kind of system is it?** (web app · API · CLI · data/ML · agentic). Match the scope, not ambition.
   Note whether it has a **user-facing UI** and record it — `status.py flag --ui yes|no` (`MECHANISMS.md`
   §Status) — it decides whether `/design-system` runs.
   Then name the **2–3 design patterns** that fit it and the **2–3 anti-patterns** to avoid (current-year), and how this design honours/avoids them — record the notable ones as ADRs.
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
   (`make` · npm scripts · just) · formatter/linter · dependency manifest. `/structure` scaffolds exactly these. Pick them from the stack you
   just chose, one line of why each.
7. **If it's an AI product:** decide **prompt-versioning**, an **eval harness**, **LLM tracing** and the
   **model runtime config** as ADRs. The model row names the model and its **release date** from its search; older than 12 months needs a stated reason. **Tie the Step-5 budget to the recorded runtime config** (thinking effort, `max_tokens`, timeout, streaming, retry and refusal fallback, caching — `references/decisions.md` §AI runtime config); the cost per use shows its working (tokens × price per 1M, from this run's page). **`Agent: yes`:** decide AGENT.md §Architect's ten rows (`next` prints them); the framework row gets its search like any stack row.
8. **Record 2–4 ADRs** for the load-bearing choices — **as FILES, one per decision:
   `docs/adr/NNNN-<slug>.md` with a `status:` line** (`accepted` / `superseded by ADR-N`), in
   the ADR shape the dry-run prints. `#Architecture` then carries the **one-line summary and the pointer**, not the
   paragraphs. (case file: ADRs with no files) A spine with inline legacy ADRs: `references/decisions.md` §Legacy ADRs.
- **Round 2, ONE message:** give **one recommendation** for the stack — a table of the rows, each with its why, the host's facts (item 3), the model's cost per use against `#Vision`'s cap, and (`Agent: yes`) the framework table AGENT.md row 1 asks for, shown before the question — any clash with `#Scope` or `#Plan` (Step 3c), then one question: *"Anything to change? If not: Save this version of your project? (yes / no)"* - either answer records it; never a turn of its own. Keep it plain — explain *why* for a newcomer; the table as approved becomes the `## Decisions` blocks of `docs/architecture.md`. A row the user picks is `user-chosen`; a yes to your recommendation is `default taken, not user-chosen`.

## Step 3 — Write back to `PRODUCT.md`
**The section is a RECORD, not a container** (`PRINCIPLES.md`): one line per decision plus the pointer
to `docs/adr/*`, every field the exit criteria name, in the shape `next` printed. After the answer, ONE message: the section (a scratch file outside the repo), `flag --ui` riding along, `set architect filled --section-from <file> --dry-run` and the one read of `templates/architecture.md`; fix every gap it names. Then ONE message - the long documents last: the ADR files, `docs/architecture.md` (the template filled: every section in its order, as the dry-run prints) and, after them, `status.py set architect filled --section-from <file> --commit "<one line>"` (no `--commit` on a no).

## Step 3b — Principle-gate and close
Walk this phase's load-bearing principles (Step 1) and confirm each is **concretely decided**, not hand-waved — `set` refuses a missing adapter, resilience strategy, migrations approach or dev-tooling slot; you judge the rest: patterns/anti-patterns are *addressed by the design*, not just listed; secrets go to `.env` (none in code); each tooling slot fits the stack. **If any is vague or missing, STOP and decide it.**

**Close the loop (`MECHANISMS.md` §Step 3b):** the checklist `set architect filled` prints (refused: fix every named gap, run it again): the save was the yes (`MECHANISMS.md` §Commit the work); **the transition guard** (`MECHANISMS.md` §Step 3b, item 4): a verdict for every exit criterion — `VERIFIED` only for what a command checked, `UNVERIFIED` is a normal outcome, silence is not; never 100%; **Close in plain language** (`MECHANISMS.md` §Plain-language close), first line `Saved: commit <hash>` when `set` saved: **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next**, ending with its `Open a NEW conversation` line word for word.

## Step 3c — Contradiction check (in round 2, before the yes; the close's step 3 confirms it)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Scope` and `#Plan` — a stack sized for work that is explicitly out of scope is gold-plating, and a perf/cost budget must not contradict `#Vision`'s business model (paid infra against a free product). On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Stack and decisions recorded. Next, **`/structure`** lays out the folders — or, with the chain chosen at Step 0, it starts now."
