# How product-playbook works — the files, the principles, the proof

> Moved here from the README so the front page can stay a getting-started guide. Nothing below is required reading before your first `/vision`; it is where to come when you want to know *why* a phase behaves the way it does.

<a id="how-it-works"></a>

## ⚙️ How it Works: The Files and Principles

This system relies on three core files to create a structured, sequential, yet standalone development workflow.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="diagrams/architecture-dark.svg">
  <img alt="How product-playbook works: PRINCIPLES.md and PRODUCT.md feed the playbook skills, which generate your codebase" src="diagrams/architecture-light.svg">
</picture>

<sub>Diagram source: <a href="diagrams/architecture.mmd"><code>diagrams/architecture.mmd</code></a> (regenerate with <code>sh tools/render-diagrams.sh</code>).</sub>

### 1. The Living Spine (`PRODUCT.md`)
Every project gets a single file at its root called `PRODUCT.md` (instantiated from `templates/PRODUCT.md`). This file is the **shared memory** of the product.
*   Every phase reads the prior section for context and appends/updates its own section.
*   If a section is empty, that phase is incomplete.
*   It travels with your Git repo, ensuring anyone (or any new LLM session) can read it top-to-bottom to understand the product's vision, decisions, contracts, and learnings.

### 2. The Rulebook (`PRINCIPLES.md`, with `MECHANISMS.md` and `LESSONS.md` beside it)
The single source of truth for your quality bar — and deliberately **short**, because it is loaded by
every skill in every session. It details:
*   **The 5-Step Spine:** Architect first → Verify assumptions → No hardcoding → Benchmark to the current year → Self-review.
*   **Per-Feature Contracts:** Explicit exit criteria, interaction maps, and independent test plans.
*   **Production Safeguards:** Zero-secrets, fail-closed security, observability, and rollback paths.

The *mechanisms* those rules run on — how a phase closes its loop, what a re-run must not erase, how a
declined run and a recorded override leave a trace, how the spine is resolved in a brownfield repo, lane
mode — live in [`../references/mechanisms.md`](../references/mechanisms.md), and the harvested war-story rules
live in [`../references/lessons.md`](../references/lessons.md). Both install as companions and are read on
demand, by name (`MECHANISMS.md §Declined runs`). `tools/check.py` fails a pointer that resolves to
nothing, and fails any governing file **or skill** over the ~15KB threshold `LESSONS.md` §Lesson
format sets — a skill goes under it by moving conditional mechanism into its own installed
`references/`, not by widening the rule.

### 3. The Commands (`commands/*.md`)
These are plain **Markdown commands** (skills) that you install into Claude Code. Each command (e.g., `/vision`, `/scope`, `/architect`, `/dev-check`) has a strict contract:

```markdown
---
name: vision
description: Phase 1 (Product) of product-playbook.
---
# `/vision` — Phase 1, Product

## Contract
- **Purpose:** turn a rough idea into a sharp, benchmarked product vision.
- **Reads:** nothing / existing codebase.
- **Writes:** PRODUCT.md#Vision
- **Exit criteria:**
  - [ ] A single sentence vision.
  - [ ] Named target user + job-to-be-done.
  - [ ] North-star success metric.
  - [ ] Verified current-year market read.
```
*(Abridged — the real skill also captures the value proposition, riskiest assumption, business model, and whether it's an AI product.)*

When you run `/playbook` or an individual command, the AI is instructed to:
1.  Verify the prior gate's exit criteria.
2.  Follow the guided checklist.
3.  Perform research/evaluations (e.g., web searches for competitors, security reviews).
4.  Write results back to `PRODUCT.md`.
5.  **Stop at the gate.** What the stop *is* depends on the gate — and they are not all approvals
    ([`docs/state-model.md`](state-model.md)): an **input** gate (`/vision`, `/scope`, `/architect`)
    asks you a question whose answer exists nowhere else, so it can never be skipped or batched; a
    **derivation** gate (`/structure`, `/contracts`, `/build`) works from what earlier phases decided and
    can run with its neighbours, ending in one review; a **verification** gate (`/dev-check`, `/test`,
    `/ship`) reports pass or fail against the repo and only stops you on red. Most of the eighteen stops
    are interviews, not signatures.
    **Two ways to run the development phases.** One phase per session is the default. Where two or more
    `derivation` phases follow each other with no `input` phase between (`/foundation` → `/contracts` →
    `/tickets`), `/playbook` and the handoffs offer a **batch**: the phases run in full, one commit each,
    stopping wherever a phase asks you to confirm and on the first red, with one review at the end.

### 4. The Forms (`templates/`)
Think of a template as a printed form with blank boxes. A skill fills the boxes so every ticket and every pull request looks the same and nothing gets forgotten. All three are ordinary text files in your repo: edit the wording if you like, and no skill will ever overwrite a form you already have.

| Form | File | Who fills it | What its boxes ask |
|---|---|---|---|
| **The product spine** | `templates/PRODUCT.md` | Every phase skill, one section each | Vision, Scope, Plan, Architecture, and so on. An empty section means that phase is not done yet. |
| **The ticket form** | `templates/feature_ticket_template.md` | `/tickets`, one copy per ticket | The goal; how the work was cut (a thin end-to-end slice, a single layer, or a one-off bug); the feature it belongs to (the optional *Lane*); the **exact files it may touch** — the box that keeps a ticket small and lets two people work without colliding; what data it takes in and hands out; which tickets must come first; what a reviewer can *see working* after merge; a short task list; a definition of done with security built in; the one command that proves it works. |
| **The pull request form** | `templates/pull_request_template.md` | GitHub shows it on every PR | Which issue it closes, a summary, the files changed, and a checklist of what was verified using the project's own test command. |

How they fit together: the spine says *what* to build, the ticket form turns that into small bounded pieces, and the pull request form is how each finished piece is checked back in.

---

<a id="not-templates"></a>

<a id="not-templates"></a>

## 🔩 Why this is not a set of templates

A spine document, six phases, milestones and exit criteria are the vocabulary of project management, and it is a fair first guess that this is a folder of AI-written PM templates. Four things a template cannot do:

**1. Two of the skills ship executable code, not prose.**

- [`commands/frontend-audit/audit.py`](../commands/frontend-audit/audit.py) — a real OKLCH→WCAG contrast engine. Contrast is **computed** from your `DESIGN.md` tokens in both light and dark mode, never asserted; an ERROR exits non-zero, so it fails a CI build.
- [`../tools/session_cost.py`](../tools/session_cost.py) — what a phase run cost, read from the session log (calls, minutes, tokens, ≈ $), so a close never estimates.
- [`../tools/check.py`](../tools/check.py) — the gate that guards the gates. Check 9 fails this repo's own build if a phase skill carries a `prior-gate check` heading whose body gates on nothing. That check exists because a skill did exactly that for five releases.

**2. The definition-of-done carries engineering, not just process.** Secret-scan clean and placeholders that *fail the boot* rather than pass a length check · fail-closed authorization and tenant isolation on every data path · the OWASP LLM Top 10 for AI products · migrations rather than hand-edited schema · externals behind provider adapters · verification of the path the product **actually runs**, not the function in isolation · a rollback path and a named post-deploy signal before a release is called done.

**3. The rules are single-sourced and referenced, not copy-pasted.** Every skill links [`PRINCIPLES.md`](../PRINCIPLES.md) and names the subset that is load-bearing for its phase — see §[Production safeguards](../PRINCIPLES.md#production-safeguards) and §[Production-readiness concern areas](../PRINCIPLES.md#production-readiness-concern-areas-the-coverage-checklist). A rule that lived in fifteen copies would drift in fifteen directions.

**4. It has been pointed at its own work, and reported faults.** `/drift-check` on a project this playbook
had itself guided returned **9 findings** — an API spec describing three routes that were never built, a
deferred feature that shipped silently and doubled the surface of 11 open contrast defects, a riskiest
assumption still untested three slices after the override that skipped it. Two days earlier the same
project caught a fault in *this repo*: `/eval` carried a gate's heading and no gate, which became #104,
`tools/check.py` check 9, and the rule *a heading is not a behaviour*.
**[The full case study, with the findings unsoftened →](case-study-subscription-tracker.md)**

**5. The claims are checked in CI.** `python tools/check.py` asserts that the skill set is identical across `commands/`, `manifest.json`, `evals/evals.json` and `VISION.md`; that one version is stated everywhere; that every `#Section` a skill reads is one the `PRODUCT.md` template actually defines; and that every phase skill really gates. Docs that drift from reality are the failure this project exists to catch — including its own.

---

<a id="journey"></a>

<a id="journey"></a>

## 🗺️ The Playbook Journey

This is the journey at full resolution — every skill, what it writes, and when to reach for it. The tiers are a way to hold it in your head; the **six phases** are what the skills themselves are numbered by.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="diagrams/journey-dark.svg">
  <img alt="The playbook journey: three tiers over six phases. Tier 1 Product thinking — /vision, /validate, /scope, /plan — then an evidence gate: a named user and job-to-be-done, a measured experiment, ONE core feature, non-goals. Tier 2 Engineering discipline — /architect, /structure, /design-system (UI only), /foundation, /contracts, /tickets, /build, /dev-check — then an evidence gate: it runs end to end, every feature's definition-of-done met with how it was verified. Tier 3 Shipping and learning — /test, /eval, /ship, /learn — then an evidence gate: measured against a baseline, security-reviewed with a rollback path, metric instrumented." src="diagrams/journey-light.svg">
</picture>

<sub>Diagram source: <a href="diagrams/journey.mmd"><code>docs/diagrams/journey.mmd</code></a> (regenerate with <code>sh tools/render-diagrams.sh</code>).</sub>

| Tier | Phases | What you are doing |
|---|---|---|
| ① Product thinking | 1 · Product | Deciding what is worth building, and cutting what is not |
| ② Engineering discipline | 2 · Development | Building it so it holds — stack, contracts, features, checkpoint |
| ③ Shipping & learning | 3 · Testing · 4 · Evaluation · 5 · Ship · 6 · Learn | Proving it, releasing it safely, finding out if it worked |

**Security, verification and scope integrity span all three.** They are not stages you pass — they are in `/scope`'s non-goals, `/build`'s definition-of-done, `/dev-check`, `/test` and `/ship`'s security review. A phase that "passed security" once would be the opposite of the position this playbook takes.

<a id="skill-reference"></a>

### Skill Reference

| Group | Skill | What it does | Output produced | Use it when |
|---|---|---|---|---|
| **Start** | `/playbook` | Guided entry-point that orchestrates phases | Routes only | You are starting fresh or unsure of the next step |
| **Product** | `/vision` | Sharpens who it's for, the problem, and the job they need done — vs the market | `PRODUCT.md` -> **Vision** | Starting a brand-new project |
| **Start** | `/adopt` | Brings an **existing, half-built** project in: drafts an INFERRED `PRODUCT.md` from the repo (docs, package metadata, routes, tests, CI), tags every inferred line, and confirms it with you section by section before writing | `PRODUCT.md` (`Stage: adopted`) | You already have code but no spine |
| **Product** | `/validate` | Tests the riskiest assumption with the cheapest real-world experiment BEFORE code — threshold set in advance, measured result, proceed / pivot / **kill** | `PRODUCT.md` -> **Validation** | Right after `/vision`, before any scoping or code |
| **Product** | `/scope` | Locks down **one** core feature; lists Deferred and Non-goals | `PRODUCT.md` -> **Scope** | Defining MVP / fighting feature creep |
| **Product** | `/plan` | Core-first milestones + concern-area checklists | `PRODUCT.md` -> **Plan** | Creating the roadmap |
| **Dev** | `/architect` | Chooses stack, records ADRs, wraps externals in adapters | `PRODUCT.md` -> **Architecture** | Before writing any code |
| **Dev** | `/structure` | Scaffolds directory layout + root scaffolding; `app/prompts/` for AI | File tree + `STRUCTURE.md` | The first coding step |
| **Dev** | `/design-system` | (UI products) Derives design principles -> confirmed sample page -> archetype-correct `DESIGN.md` (shadcn tokens). Kills the generic AI look; fixes too-small fonts | `DESIGN.md` + sample page + `PRODUCT.md` -> **Design** | Before building any screens |
| **Dev / UI** | `/frontend-audit` | (UI products) Mechanically enforces the design-system laws — a real OKLCH->WCAG contrast engine + token/motion/font/responsive checks; CI-friendly | Pass/warn/error scorecard (exits non-zero on error) | After building or changing UI, or in CI |
| **UI suite** | `/new-component` | (bundled support skill) Builds/skins ONE React component against the `DESIGN.md` tokens — CSS-vars, interactive states, a11y; reuses shadcn/ui + 21st.dev | Component file | Building any UI component |
| **Dev** | `/foundation` | Builds walking skeleton with logging, config, commit hooks and CI | Running app + CI workflows | Bootstrapping the codebase |
| **Dev** | `/contracts` | Writes typed schemas/migrations BEFORE business logic | Schema files + migrations | Writing data layers |
| **Dev** | `/tickets` | Splits each milestone into 2-4 independently mergeable tickets, **grouped into module lanes** (one per `STRUCTURE.md` module, ordered inside, parallel across) with an Owner — **vertical** thin slices or **horizontal** layer tickets, proposed and confirmed by you — and files them on a **Delivery Board** (Status · Owner · Lane · Seat) so one person or four can take the same backlog. Exact file paths, typed in/out, security DoD. Given a description instead, logs ONE ad-hoc bug against the owning file | `docs/issues/*` + issue/PR templates | After `/contracts`, before building; or any time you spot a bug |
| **Dev** | `/build` | Implements feature with testable exit criteria and docs | Feature code + `docs/features/*` | Building feature-by-feature |
| **Dev** | `/dev-check` | Verifies exit criteria and security DoD with evidence | `PRODUCT.md` -> **Dev-complete** | Prior to testing |
| **Dev** | `/deploy` | Executes the runtime target `#Architecture` chose: the repo reaches a host, and `docs/deployment.md` says how | `docs/deployment.md` + `PRODUCT.md` -> **Deployment** | A real request answered on the public URL |
| **Testing** | `/test` | Performs unit/integration/regression and adversarial tests | Test suites | Post-development check |
| **Eval** | `/eval` | Measures quality and latencies against baseline | `PRODUCT.md` -> **Evaluation** | Validating performance/accuracy |
| **Ship** | `/ship` | Does security review, doc audit, PR, and rollback plans | Release PR + CHANGELOG | Deploying to production |
| **Learn** | `/learn` | Tracks success metric and decides: iterate or **KILL** | `PRODUCT.md` -> **Learnings** | Post-launch retro |
| **Cross-Cut** | `/drift-check` | Compares current code and docs vs. original scope | Drift Report | Anytime you suspect creep |

> **Everything installs from this one repo.** Every phase skill and the UI suite (`/design-system`, `/frontend-audit`, `/new-component`, coupled through `DESIGN.md`) are mastered and bundled here; there is no synced copy anywhere else, because a mirror with no sync tooling drifts.

### How `DESIGN.md` is derived (the UI suite)

For UI products, `/design-system` turns your vision into one concrete, reusable design spec — **`DESIGN.md`** — which
the other two UI skills then consume. So the look is *decided once, confirmed by you, and enforced everywhere*:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="diagrams/design-system-dark.svg">
  <img alt="How DESIGN.md is derived: PRODUCT.md and universal-laws feed /design-system, which emits DESIGN.md, consumed by /new-component and enforced by /frontend-audit" src="diagrams/design-system-light.svg">
</picture>

<sub>Diagram source: <a href="diagrams/design-system.mmd"><code>diagrams/design-system.mmd</code></a> (regenerate with <code>sh tools/render-diagrams.sh</code>).</sub>

`DESIGN.md` is **derived** (not hand-written) through the sample-and-confirm loop, then **consumed**: `/new-component`
builds against its tokens and `/frontend-audit` mechanically enforces them. Skipped entirely for backend/API/CLI products.

---

<a id="walkthrough"></a>

## 🪄 One product through every skill — the full walkthrough

The waitlist app from the README, skill by skill: what you type, what it asks or does, what it writes, and the failure it prevents.

**Phase 1 · Product — decide what is worth building**

| Skill | You type | It asks / does | It writes | It prevents |
|---|---|---|---|---|
| 💡 `/vision` | `/vision I want to build a walk-in waitlist for small restaurants …` | Who exactly is the user? What job are they hiring this for? Which one number says it worked? Checks the current-year market. | One-sentence vision · the user (*host of a 40-seat restaurant on a Friday night*) · north star (*80 % of walk-ins seated without chasing, by March*) · the **riskiest assumption** (*guests scan a code instead of giving a name*) | Every later "should we add X?" having no answer |
| 🔎 `/validate` | `/validate` | What is the cheapest real-world test, and what counts as a pass — *set before running it*? | The experiment (*paper QR on the door, one Friday, pass mark 60 % scan*) · the measured result · **proceed / pivot / kill**. Slow result → later phases run *provisionally* | Building something nobody wanted |
| ✂️ `/scope` | `/scope` | Which single behaviour delivers the value? | **THE core feature** (*guest joins the queue, is told when the table is ready*) · deferred items, each with its trigger · **non-goals**: reservations, payments, menus, accounts | Scope creep — every later skill checks this list; reopening a non-goal is recorded with a date and reason |
| 🗺️ `/plan` | `/plan` | Sequences the scope, core first | Milestones with a testable exit each — M1 *guest gets a text, laptop demo* · M2 *host seats the queue* · M3 *one real Friday night* | Milestones that are wishes |

**Phase 2 · Development — build it so it holds**

| Skill | You type | It asks / does | It writes | It prevents |
|---|---|---|---|---|
| 🏗️ `/architect` | `/architect` | Budget? Where will it run? Who maintains it? Benchmarks current-year options. Offers to **chain into `/structure`** | The stack and key decisions as ADRs — runtime target, commit-hook tool, every external (the SMS provider) behind an adapter | A vendor SDK welded into business logic |
| 📁 `/structure` | `/structure` | Draws the folder shape | One module per thing the product does (`queue/`, `notify/`, `host/`), each with its routes, store and tests · root scaffolding (agent instructions, `.env.example`, secret-scan, hooks, task runner) · `prompts/` if there is an LLM · `STRUCTURE.md` | "Where does this go?" having no answer |
| 🎨 `/design-system` *(UI only)* | `/design-system` | What look do *you* want? Proposes an archetype, builds **one real sample page**, stops until you like it | `DESIGN.md` — the tokens every later screen reuses | The generic AI look, too-small fonts |
| 🧱 `/foundation` | `/foundation` | Builds the walking skeleton | Dependencies · config loader · structured logging · DB wired · lint and hooks · CI that mirrors the production boot. A placeholder secret **refuses to boot, by name** | Config that silently does nothing |
| 📐 `/contracts` | `/contracts` | Types before logic | Typed models, schemas, migrations, the API contract — front and back agree on what a `QueueEntry` is | Two halves disagreeing about one field |
| 🎫 `/tickets` | `/tickets` | **Shows the proposal**, waits for your confirm, then files it | Tickets in **lanes by module** (`queue`, `notify`, `host`) as GitHub issues on a **Delivery Board** — Status · Owner · Lane · Seat — each with exact files, typed in/out, a security DoD | One backlog blocking a second builder (solo: every seat is you) |
| 🎫 `/tickets "…"` | `/tickets "Bug: the SMS send is not retried on a 5xx"` | Files **one** issue against the owning file | One `[ADHOC-nn]` ticket, on the board | Derailing the backlog for one bug |
| 🛠️ `/build` | `/build M1-SLICE-01` | Reuse before writing · verifies the **live path** · `/code-review` on the diff · commits | Feature code + `docs/features/<name>.md`; ends with the plain close — built, verified how, what you do next | Green tests over a dead live path |
| ✅ `/dev-check` | `/dev-check` | Is every core feature built, running, at its exit criteria and security DoD? | `#Dev-complete` with **evidence you can re-run** | A claim standing in for proof |
| 🌐 `/deploy` *(needs a URL)* | `/deploy` | Executes the runtime target `/architect` chose; never reopens it | `docs/deployment.md` + `#Deployment`; done when someone who is not you loads the page | A host decided and never executed |

**Phases 3–6 · Test, evaluate, ship, learn**

| Skill | You type | It asks / does | It writes | It prevents |
|---|---|---|---|---|
| 🧪 `/test` | `/test` | Unit (mocked) · integration (real seams) · regression · **adversarial** (wrong host token, double claim on the last table, prompt injection if there is an LLM) | The suite + `#Tests` | Functions that pass while the product fails |
| 📊 `/eval` | `/eval` | Is it actually *good*, measured against `/plan`'s criteria? Operational failures separated from quality | `#Evaluation` with an honest confidence score (AI products: `/enterprise-ai-audit` optional) | "It works" without a number |
| 🚢 `/ship` | `/ship` | Fresh-eyes `/code-review` · `/security-review` · docs reconciled to reality · rollback path | The PR · `#Ship log` · a handoff note · *"start a new session"* | Shipping what the docs no longer describe |
| 📈 `/learn` | `/learn` | Did the north star move after the real Friday night? Short retro | `#Learnings` · the next cycle, back to `/scope` or `/plan` · `/loop` or `/schedule` to re-measure | Deciding what is next from feeling, not evidence |
| 🛑 `/drift-check` *(any time)* | `/drift-check` | Are we still building the vision? Features that were non-goals, docs that no longer match code | A report · a dated `#Drift log` row on confirmed drift; never advances the chain | Drift nobody noticed |

---

<a id="which-skills"></a>

## 🧭 Which skills apply to *your* product?

Every product runs the spine above. A few skills switch on or off depending on what you are building — the playbook works it out from `PRODUCT.md`. Here is why each one matters:

- **Has a user interface** → `/design-system` before any screen, `/new-component` per component, `/frontend-audit` after UI changes and in CI.
  *Why:* screens built without agreed tokens come out AI-generated and inaccessible. `/frontend-audit` **computes** contrast (OKLCH → WCAG) rather than asserting it.
- **Backend, API or CLI only** → the three UI skills are skipped. `/structure` and `/contracts` carry the weight.
- **Uses an LLM** → `/structure` adds `prompts/`, `/architect` puts the provider behind an adapter, `/test` adds prompt-injection and jailbreak cases, `/eval` can add `/enterprise-ai-audit`.
  *Why:* swapping the model must not touch business logic; the OWASP LLM Top 10 is part of `/ship`'s security review.
- **No LLM** → those checks are skipped, not faked: a definition of done never lists a check that did not run.
- **Needs a public URL** (real users, a second device, a milestone criterion) → `/deploy` after `/dev-check`.
  *Why:* deciding a host and never executing it is a real failure this playbook once had.
- **Runs on your laptop only** → `/deploy` is skipped.
- **Already has code** but no `PRODUCT.md` → `/adopt` first. It drafts the spine *from the repo* (docs, package metadata, routes, tests, CI), tags every inferred line, and confirms each section with you before writing.
- **More than one person or agent building** → the `/tickets` lanes and Delivery Board are already the map: a lane per module, an owner and a seat per card, so two people never edit the same folder at once.

---

<a id="ways-to-run"></a>

## ⚙️ Ways to run it

| You want to… | Type | What happens |
|---|---|---|
| **Be guided** (default) | `/product-playbook:playbook` | Reads `PRODUCT.md`, names where you are, offers the next phase. One phase, then it stops. |
| **Run one phase** | `/product-playbook:scope` | Any skill, on its own, in any order. Out of order is allowed and *visible*: it names what is at risk and lets you override with a recorded reason. |
| **Batch the derivation phases** | say **yes** when `/playbook` or `/structure` offers `foundation + contracts + tickets` | Nothing inside a phase changes. One commit per phase. Still stops wherever a phase asks you to confirm, and on the first red. One review at the end. Never the default. |
| **Chain architect → structure** | say **yes** when `/architect` offers it at its first step | The stack and the folder shape in one session, every question kept. |
| **Log one bug mid-build** | `/product-playbook:tickets "Bug: …"` | One issue against the file that owns it, on the board. Backlog untouched. |
| **Bring in an existing repo** | `/product-playbook:adopt` | Inferred `PRODUCT.md`, confirmed section by section. |
| **Check for drift** | `/product-playbook:drift-check` | A report; a dated row in `#Drift log` if anything is confirmed. |
| **Re-measure after launch** | `/learn` sets it up | Uses Claude Code's `/loop` or `/schedule` to re-check the metric on a cadence. |

**Claude Code skills it calls:** `/code-review` (in `/build` and `/ship`) · `/security-review` (in `/ship`, and on any auth or data change) · `/run` (to drive the app in `/build` and `/test`) · `/loop` and `/schedule` (in `/learn`). If your harness names one differently, any equivalent satisfies the gate and the record says which was used. A gate is never skipped for a missing command, and never silently.

