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
  - [ ] `#Architecture` is complete and **traces to scope/plan** (no gold-plating): stack+tools+why **and the constraint set each choice was optimised against** (reliability · operational burden · team size · cost · compatibility · maturity · lock-in/exit cost), every external behind an adapter, key ADRs (incl. patterns applied / anti-patterns avoided), migrations approach, a **custody + runtime target** line (data custody · runtime target · identity custody — each an ADR or an explicit N/A, and a default taken without user input says so), a **Dev tooling** line naming the hook runner · secret scanner · task runner · formatter/linter · dependency manifest (the tools `/structure` will scaffold — leave one unnamed and `/structure` picks it blind), and the **decisions for the concern areas this product needs** — resilience · perf/cost budget · security/no-secret-in-code · observability, **+ (AI) prompt-versioning/eval/tracing** — each recorded or marked **N/A**.

## Step 0 — Context + prior-gate check
- Read `#Vision/#Scope/#Plan`. If `#Scope`/`#Plan` are empty, warn and offer to run them first (allow override).
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then write `Override <date>: <reason> — bypassed <gate>` at the top of `#Architecture` before continuing. Advancing on unmet criteria is the more consequential of warn-vs-override, so it is the one that leaves a trace: without it a later reader cannot tell a gate that held from a gate that was waved through.
- Brownfield: detect the existing stack from the repo and record it as the starting point.

- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** if the section is already filled, **show what would change and ask before replacing it** — never a silent overwrite — and leave a reversed decision in place with a dated `superseded <date>: <why>` line. A first run over an empty section is unchanged.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** write ONE dated line at the top of `#Architecture` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **Benchmark to the current year, then choose on constraints:** find what leading teams use *now* — that half is load-bearing and stops the AI reaching for a stale default. Then pick on **fit, not ideology**: reliability, operational burden, **the size of the team that has to run it**, cost, compatibility, maturity, and **lock-in (portability + exit cost)**. Open source often wins on the last one; it does not win automatically, and self-hosting infrastructure whose operating cost dwarfs the licence saving is a real failure mode for a solo builder. **Record the constraint set you optimised against** and why the winner won — one line each, in `#Architecture`, so the decision is auditable when a constraint changes.
- **Check where approvals attach (the self-host blind spot):** for any integration gated by a third party's approval — social/platform publishing APIs, app-store distribution, payment-processor onboarding, healthcare/finance API access — ask *"does the approval attach to the developer app/account, or to the software?"* If it attaches to the app, **self-hosting OSS does not bypass it** (you still register + pass every review yourself — OSS saves code, not compliance), and vendors who rent out their approvals (aggregators) may legitimately beat both OSS and direct builds. Benchmark all three routes with time-to-first-working-result including review/audit wait, not just code effort. (Learned on a shipped video product's distribution stage: IG/TikTok/YouTube app-review wall — unapproved apps fail *silently*, e.g. YouTube force-privates uploads.)
- **Patterns & anti-patterns awareness:** know the established design patterns for this kind of system *and* its common anti-patterns (e.g. god-objects, tight coupling to a vendor, dead config, N+1 / blocking the event loop, distributed-monolith). Apply the right patterns; consciously avoid the anti-patterns — adapted to *this* project, not cargo-culted.
- **Provider/adapter for every external:** no vendor SDK in business logic — wrap it behind a config-selected interface so it's swappable via `.env`.
- **No-hardcoding & typed contracts:** decisions must keep values in config and payloads typed.

## Step 2 — Guided decisions
1. **What kind of system is it?** (web app · API · CLI · data/ML · agentic). Match the scope, not ambition.
   Note whether it has a **user-facing UI** — this flags whether `/design-system` runs after `/structure`
   (UI products) or is skipped (backend/API/CLI only).
   Then name the **2–3 design patterns** that fit it and the **2–3 anti-patterns** to avoid (current-year), and how this design honours/avoids them — record the notable ones as ADRs.
2. **Choose the stack core** (language · framework · datastore · key libs). One-line why each; flag anything paid and its trigger to adopt.
3. **Custody + runtime target — three questions that are NOT stack trivia.** The deployment target decides
   whether a compose file is even the right artifact, whether connection strings or a local service get
   scaffolded, and it is expensive to reverse once `/structure` and `/foundation` have built on it:
   - **Where does the data live?** Local/self-hosted · managed-serverless · embedded. One line of trade-off
     each, and name the **vision-driven** consideration (privacy · cost · portability · lock-in).
   - **Where does this run?** Container-anywhere · a specific PaaS · a VPS · the user's own machine.
     **This is what tells `/structure` and `/foundation` what to scaffold.**
   - **Who holds identity?** Self-hosted auth vs the datastore vendor's auth + row-level security. If the
     user already pays for a platform, the "free" self-hosted option may not be the cheaper one.
   PRINCIPLES' *defer paid infra until a real need* biases all three toward local — a sensible default, but
   **it must be a stated default the user can decline, not an unvoiced one.** If the user has no opinion,
   recommend one with a reason and **record it as "default taken, not user-chosen"**. Get the same yes/no
   the rest of the stack recommendation gets.
4. **List every external** and the **adapter interface** it will hide behind (e.g. `LLMProvider`, `Storage`) — *and* its **failure/resilience strategy** (timeouts · retry-transient-only · fallback/circuit-breaker). This is what keeps it swappable, testable, and resilient.
5. **Set a rough perf/cost budget** where it matters (latency + cost-per-operation), since the stack choice locks it in — or mark **N/A**. **Derive the number from the dominant cost, don't guess it:** name the single most expensive step (a durable fsync, an LLM call, a network hop) and budget from a quick probe of *that* — or, if you can't probe now, write the budget as **explicitly aspirational** and commit to **re-measuring it in `/eval`**. A hard ADR number pulled from a hunch tends to miss by ~2× and erodes trust when `/eval` measures the truth.
6. **Name the dev tooling** — hook runner (pre-commit · lefthook · husky) · secret scanner · task runner (`make` · npm scripts · just) · formatter/linter · dependency manifest. These look like trivia and are not: `/structure` scaffolds these files next, and an *unrecorded* slot is one it fills from habit rather than from the stack (a Python hook runner landing in a Node repo). Pick them **from the stack you just chose**, one line of why each.
7. **If it's an AI product:** decide **prompt-versioning**, an **eval harness**, and **LLM tracing/observability** as ADRs (don't let them emerge).
8. **Record 2–4 ADRs** for the load-bearing choices (decision · why · rejected alternative).
- Give **one recommendation** for the stack; get a yes/no. Keep it plain — explain *why* for a newcomer.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Architecture`: stack+tools+why · **data custody · runtime target · identity custody** · **dev tooling** (hook runner · secret scanner · task runner · formatter/linter · dependency manifest) · ADRs (patterns/anti-patterns) · externals behind adapters + resilience · perf/cost budget · migrations approach · (AI) prompt-versioning/eval/tracing.

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
