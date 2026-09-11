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
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing this phase:
> **benchmark 2026 then optimise for constraints (incl. lock-in)**, **patterns & anti-patterns**, **provider/adapter for externals**,
> **resilience strategy**, **perf/cost budget**, **migrations (not raw schema)**, **no-hardcoding /
> no secret in code**, **typed-contracts intent**, **layered/decoupled**. (Depth lives in Step 2 +
> PRINCIPLES; the gate below just confirms it's recorded and real.)

## Contract
- **Purpose:** choose the stack/tools/decisions before any folders exist, aligned to the product.
- **Reads:** `PRODUCT.md#Vision`, `#Scope`, `#Plan`.
- **Writes:** `PRODUCT.md#Architecture` — stack+tools+why · **dev tooling** · ADRs · externals behind adapters · resilience · perf/cost budget · (AI) prompt-versioning/eval.
- **Gate type:** `input` — since #129 the choice is made against the project's constraints - team size, operational appetite, budget, tolerable lock-in - and those live in the human. **Never batched** - skipping it fabricates the product's premise. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes `#Architecture` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Exit criteria (the gate — small: is the section complete?):**
  - [ ] `#Architecture` is complete and **traces to scope/plan** (no gold-plating): stack+tools+why **with
    a provenance flag on every row** and **the constraint set each choice was optimised against**
    (reliability · operational burden · team size · cost · compatibility · maturity · lock-in/exit cost);
    every external behind an adapter; key ADRs (patterns applied / anti-patterns avoided); the migrations
    approach; a **custody + runtime target** line (data custody · runtime target · identity custody, each
    an ADR or an explicit N/A); a **Dev tooling** line naming hook runner · secret scanner · task runner ·
    formatter/linter · dependency manifest (leave one unnamed and `/structure` picks it blind); and the
    **decisions for the concern areas this product needs** — resilience · perf/cost budget ·
    security/no-secret-in-code · observability **+ (AI) prompt-versioning · eval · tracing · model runtime
    config** — each recorded or marked **N/A**.

## Step 0 — Context + prior-gate check
- Read `#Vision/#Scope/#Plan`. If `#Scope`/`#Plan` are empty, warn and offer to run them first (allow
  override). **A `running` upstream gate BLOCKS from here on** (`docs/state-model.md` §2a): it was
  advisory for `/scope` and `/plan`, which produce documents — from here the product is being built, so a
  pending result needs the result, or a recorded override.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then write `Override <date>: <reason> — bypassed <gate>` at the top of `#Architecture` before continuing. Advancing on unmet criteria is the more consequential of warn-vs-override, so it is the one that leaves a trace: without it a later reader cannot tell a gate that held from a gate that was waved through.
- Brownfield: detect the existing stack from the repo and record it as the starting point.

- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** if the section is already filled, **show what would change and ask before replacing it** — never a silent overwrite — and leave a reversed decision in place with a dated `superseded <date>: <why>` line. A first run over an empty section is unchanged.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** write ONE dated line at the top of `#Architecture` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **Benchmark to the current year, then choose on constraints:** find what leading teams use *now* — that half is load-bearing and stops the AI reaching for a stale default. Then pick on **fit, not ideology**: reliability, operational burden, **the size of the team that has to run it**, cost, compatibility, maturity, and **lock-in (portability + exit cost)**. Open source often wins on the last one; it does not win automatically, and self-hosting infrastructure whose operating cost dwarfs the licence saving is a real failure mode for a solo builder. **Record the constraint set you optimised against** and why the winner won — one line each, in `#Architecture`, so the decision is auditable when a constraint changes.
- **Check where approvals attach (the self-host blind spot):** where an integration is gated by a third
  party's approval, ask *"does it attach to the app/account, or to the software?"* If it attaches to the
  app, **self-hosting OSS does not bypass it** — OSS saves code, not compliance
  (`references/decisions.md` §Where approvals attach).
- **Patterns & anti-patterns awareness:** know the established design patterns for this kind of system *and* its common anti-patterns (e.g. god-objects, tight coupling to a vendor, dead config, N+1 / blocking the event loop, distributed-monolith). Apply the right patterns; consciously avoid the anti-patterns — adapted to *this* project, not cargo-culted.
- **Provider/adapter for every external:** no vendor SDK in business logic — wrap it behind a config-selected interface so it's swappable via `.env`.
- **No-hardcoding & typed contracts:** decisions must keep values in config and payloads typed.

## Step 2 — Guided decisions
1. **What kind of system is it?** (web app · API · CLI · data/ML · agentic). Match the scope, not ambition.
   Note whether it has a **user-facing UI** — this flags whether `/design-system` runs after `/structure`
   (UI products) or is skipped (backend/API/CLI only).
   Then name the **2–3 design patterns** that fit it and the **2–3 anti-patterns** to avoid (current-year), and how this design honours/avoids them — record the notable ones as ADRs.
2. **Choose the stack core** (language · framework · datastore · key libs). One-line why each; flag
   anything paid and its trigger to adopt. **Two rules on how the rows are recorded:**
   - **Every row carries its provenance** — `user-chosen` or `default taken, not user-chosen`. That flag
     covered only custody · runtime · identity, so the *language* was picked silently and the owner found
     out at the output. A default is fine; an **unvoiced** default is what nobody can decline.
   - **A UI-tooling constraint binds the UI only.** React/shadcn decides what `frontend/` is written in and
     says **nothing** about the server language. Letting it imply one is how a full-stack product became a
     single TypeScript app that no later phase could question — `/structure` derives shape from this row,
     so a collapsed row collapses the tree.
3. **Custody + runtime target — three questions that are NOT stack trivia.** *Where does the data live?*
   (local/self-hosted · managed-serverless · embedded) · *Where does this run?* (container-anywhere · a
   PaaS · a VPS · the user's machine) · *Who holds identity?* (self-hosted auth vs the vendor's auth +
   RLS). They are expensive to reverse once `/structure` and `/foundation` have built on them, the
   runtime target is what **`/deploy` later executes**, and the custody answer selects `/foundation`'s
   test-datastore recipe. **Open `references/decisions.md` §Custody, runtime and identity** for the
   trade-offs and the recorded-default rule: a default is fine, an **unvoiced** default is not.
4. **List every external** and the **adapter interface** it hides behind (`LLMProvider`, `Storage`) — *and*
   its **failure/resilience strategy** (timeouts · retry-transient-only · fallback/circuit-breaker). That
   is what keeps it swappable, testable and resilient.
5. **Set a rough perf/cost budget** where it matters (latency + cost-per-operation) — the stack choice
   locks it in — or mark **N/A**. **Derive it from the dominant cost, don't guess:** name the single most
   expensive step (a durable fsync, an LLM call, a network hop) and budget from a quick probe of *that*;
   if you cannot probe now, write the budget as **explicitly aspirational** and commit to re-measuring in
   `/eval`. A number pulled from a hunch misses by ~2× and erodes trust when `/eval` measures the truth.
6. **Name the dev tooling** — hook runner (pre-commit · lefthook · husky) · secret scanner · task runner
   (`make` · npm scripts · just) · formatter/linter · dependency manifest. These look like trivia and are
   not: `/structure` scaffolds these files next, and an **unrecorded slot is one it fills from habit**
   rather than from the stack (a Python hook runner landing in a Node repo). Pick them from the stack you
   just chose, one line of why each.
7. **If it's an AI product:** decide **prompt-versioning**, an **eval harness**, **LLM tracing** and the
   **model runtime config** as ADRs — don't let them emerge. The runtime config is the one that was
   missing and the one the budget depends on (thinking effort, `max_tokens`, timeout, streaming, retry
   and refusal fallback, caching): frontier models run adaptive thinking **by default** and thinking
   bills as output, so a budget written without it is unachievable by construction. **Tie the Step-5
   budget to the recorded config** — `references/decisions.md` §AI runtime config.
8. **Record 2–4 ADRs** for the load-bearing choices (decision · why · rejected alternative).
- Give **one recommendation** for the stack; get a yes/no. Keep it plain — explain *why* for a newcomer.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Architecture`: stack+tools+why **with a provenance flag on every row** · **data custody · runtime target · identity custody** · (AI) **model runtime config** · **dev tooling** (hook runner · secret scanner · task runner · formatter/linter · dependency manifest) · ADRs (patterns/anti-patterns) · externals behind adapters + resilience · perf/cost budget · migrations approach · (AI) prompt-versioning/eval/tracing.

## Step 3b — Principle-gate: verify the decisions are real, not vague
Walk this phase's load-bearing principles (Step 1) and confirm each is **concretely decided**, not hand-waved:
- every external actually has an adapter interface **and** a resilience strategy (no raw vendor SDK in logic);
- patterns/anti-patterns are *addressed by the design*, not just listed;
- secrets go to `.env` (none in code); a migrations approach exists for any datastore;
- **every dev-tooling slot is named and stack-appropriate** — `/structure` treats this line as the instruction for which files to write.
**If any is vague or missing, STOP and decide it.** (No code yet, so the evidence is concrete, consistent
decisions in `#Architecture`; `/build` later re-verifies them in code via `/code-review`.)

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and **offer to commit the change** (`MECHANISMS.md` §Commit the work — check the repo exists, name the branch, offer the message, push only if a remote exists and the user says so). Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal. **Close in plain language** (`MECHANISMS.md` §Plain-language close): two or three sentences of *what just happened* with no playbook dialect, then a numbered *what YOU do next* — the user's own actions, dated where they are time-bound, or "Nothing — you're done".

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Scope` and `#Plan` — a stack sized for work that is explicitly out of scope is gold-plating, and a perf/cost budget must not contradict `#Vision`'s business model (paid infra against a free product). On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Stack and decisions recorded. Now build the **first concrete thing**: run **`/structure`** to lay
out clean folders and explain what each is for."
