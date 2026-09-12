# Product Playbook: Build with Discipline in the AI Era

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.40.0-blue.svg)](CHANGELOG.md)
![Claude Code skills](https://img.shields.io/badge/Claude%20Code-22%20skills-8A2BE2.svg)

**AI writes code faster than anyone can reason about it. `product-playbook` puts the gates in between.**

AI is an incredible *execution engine* — it is not a *discipline engine*. Build without guardrails and it does not just build your product: it multiplies the entropy, debt and chaos at 100mph. These five cost me real time on a real project:

| The failure | What it looked like |
|---|---|
| **Features nobody asked for** | Building was so cheap the core purpose got buried under "cool" ideas. |
| **Config that silently did nothing** | The block looked correct in the file; the value never flowed end-to-end. |
| **Green tests over a dead live path** | The suite passed perfectly while the path the product actually runs was broken. |
| **A vendor SDK welded into business logic** | Swapping providers meant refactoring half the codebase. |
| **A leaked secret, a missing tenant filter** | One absent scope check away from a cross-customer data leak. |

Every one of those is an *AI-speed* failure: not "we could not build it", but a working-looking product nobody can account for. AI made building cheap, so **deciding what to build, and proving it worked, are what is now scarce.** That is the whole product — six phases, a gate between each, and one file at your repo root that remembers what you decided.

### Evidence gates

> **No evidence → the gate holds → no progress.**

The teeth are in the *refusal*, not the advance. And it is not a slogan: [`tools/check.py`](tools/check.py) **check 9** fails CI if any phase skill carries a gate's title without a gate's behaviour — the guarantee is enforced in this repo's own build.

The guarantee is deliberately narrow: **a process that cannot silently skip a check.** Not senior judgment, not good outcomes — those stay yours. A gate can always be passed; passing one is *recorded*, with a reason and a date, so a later reader can tell a gate that held from a gate that was waved through.

**Who it is for:** a technical builder shipping with AI coding agents — a solo founder, or an engineer anywhere from first job to staff — with no PM, designer, QA, security engineer or release manager beside them. Claude Code is the runtime; the same gap exists in Cursor or Copilot. ([the full audience note, and who it is *not* for →](VISION.md))

**Requirements:** Claude Code (≥ 2.0.70 for the plugin route). **Nothing else to install** — every phase skill ships here, and the only skills composed from outside are Claude Code's own built-ins (`/code-review`, `/security-review`, `/run`, `/loop`, `/schedule`). If your version or harness names one differently, **any equivalent satisfies it**: `PRINCIPLES.md` requires the same work be done by the best means available — your own reviewer agent, security pass, or a careful hand pass — and the evidence line to **say which**. A gate is never skipped for a missing command, and never silently. Language- and framework-agnostic — it drives your process, not your stack.

## ⚡ Quick start

**Install, then type one command.** It reads your repo, works out where you are, and runs the right phase — you never have to pick.

```
/plugin marketplace add kish21/product-playbook
/plugin install product-playbook@product-playbook
```

Then, in a new Claude Code session:

```
/product-playbook:playbook
```

*Already have a process and want one step of it?* **Every skill also runs on its own** — `/product-playbook:adopt` to draft a spine from code you have already written, `/product-playbook:tickets`, `/product-playbook:ship`, `/product-playbook:drift-check`, any of them, in any order. The guided path is the default, never a requirement.

If the install summary says `Run /reload-plugins to activate.`, run it first. Prefer plain `/vision`-style names (no plugin prefix), a project-local install, or just a few of the skills? See [Installation and Setup](#install).

## 🔀 Before → after

**Without a playbook**

```
idea  -->  "sure, I'll build that"  -->  ~500 files later  -->  ???
```

Four questions nobody can answer — and the section of `PRODUCT.md` that answers each:

| The question | Answered by |
|---|---|
| *Why did we build this?* | **#Vision** — who it is for, the job to be done, the north-star metric |
| *What did we decide, and why?* | **#Architecture** + **#Contracts** — stack, ADRs, typed boundaries |
| *Does this actually work?* | **#Tests** + **#Evaluation** — live-path and adversarial cases, measured |
| *Can we safely ship this?* | **#Ship log** — security review, rollback path, post-deploy signal |

**With it** — three tiers over the six phases, and a gate between each:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/journey-dark.svg">
  <img alt="The playbook journey: three tiers over six phases. Tier 1 Product thinking — /vision, /validate, /scope, /plan — then an evidence gate: a named user and job-to-be-done, a measured experiment, ONE core feature, non-goals. Tier 2 Engineering discipline — /architect, /structure, /design-system (UI only), /foundation, /contracts, /tickets, /build, /dev-check — then an evidence gate: it runs end to end, every feature's definition-of-done met with how it was verified. Tier 3 Shipping and learning — /test, /eval, /ship, /learn — then an evidence gate: measured against a baseline, security-reviewed with a rollback path, metric instrumented." src="docs/diagrams/journey-light.svg">
</picture>

<sub>Diagram source: <a href="docs/diagrams/journey.mmd"><code>docs/diagrams/journey.mmd</code></a> (regenerate with <code>sh tools/render-diagrams.sh</code>). The three tiers are a way to hold the map in your head; the <strong>six phases</strong> are what the skills are numbered by.</sub>

**Security, verification and scope integrity are carried through all three tiers — never a phase of their own.** They live in `/scope`'s non-goals, `/build`'s definition-of-done, `/dev-check`, `/test` and `/ship`'s security review. A stage you pass once would be the opposite of the position this playbook takes.

Three skills sit outside the chain, on purpose: **`/drift-check`** any time (*are we still building the vision?*), **`/adopt`** if you already have code (it drafts the spine from your repo), and — for UI products — **`/new-component`** to build against `DESIGN.md` with **`/frontend-audit`** to enforce it.

### The one file: `PRODUCT.md`

Everything above writes to **one file at your repo root**. `#Vision`, `#Scope`, `#Architecture`, `#Tests`, `#Ship log` are its sections — each phase appends its own and reads the ones before it. An empty section means that phase is not done. It is plain Markdown, it lives in Git beside the code, and it is what makes the next session (or the next person) able to pick up where you stopped. Full description: [How it works](#how-it-works).

## Contents

- [The personal story: the vibe coding trap](#story) — the long version of the five failures above
- [How it works: the files and principles](#how-it-works) — `PRODUCT.md`, `PRINCIPLES.md`, the commands, the templates
- [Why this is not a set of templates](#not-templates) — the executable proof
- [Case study: the playbook auditing its own work](docs/case-study-subscription-tracker.md) — 9 real findings, unsoftened
- [The playbook journey](#journey) — the phase map
- [Skill reference](#skill-reference) — every skill, and what each one writes
- [Installation and setup](#install) — three install routes, updating, uninstalling
- [Contributing](#contributing)

---

<a id="story"></a>
<details>
<summary><strong>📖 The personal story: the vibe coding trap</strong> — click to read why this playbook exists</summary>


In this AI era, everyone is building a product. I did too.

Armed with tools like Claude Code, Cursor, and Copilot, I was coding at 100mph. I felt like a superhero. I was spinning up files, adding features in minutes, and generating entire modules with single prompts. We call it "vibe coding." It feels like magic—until the vibe fades and reality hits.

Suddenly, I found myself staring at a product that was slipping away from me. I was completely lost.

Here is exactly how it happened:
1.  **I let features creep in that nobody needed:** Because the AI made building so easy, I kept adding "cool" ideas. Soon, the core purpose of my app was buried under a mountain of secondary features.
2.  **I trusted config settings that silently did nothing:** The AI generated configuration blocks that were silently overridden upstream. Everything looked correct in the files, but the value never flowed end-to-end.
3.  **I relied on green tests while the app was dead in production:** My test suites were passing perfectly, but the actual critical path the product ran on was completely broken because of decoupled runtime wiring.
4.  **I hardcoded vendor APIs directly into my business logic:** I let the AI wire code straight to a specific vendor's SDK. When I needed to swap providers, I had to touch and refactor half the codebase.
5.  **I accidentally exposed secrets and skipped tenant isolation:** A missing security filter almost let users see another customer's data, and placeholder keys were constantly in danger of being committed.

**The Lesson I Learned:** AI is an incredible *execution engine*, but it is not a *discipline engine*. If you build without guardrails, AI doesn't just build your product—it multiplies the entropy, debt, and chaos at 100mph.

To cut short the time of my next project and stay laser-focused, I needed a playbook. Not just a document, but **executable skills with evidence-based gates and checks** that force both me and the AI to maintain engineering discipline.

> 👉 *This is the long version of the five failures at the top. Short on time? **[Go straight to the one command that starts it ->](#-quick-start)***

`product-playbook` was born from my scars. It turns those lessons into a single, shared rulebook (`PRINCIPLES.md`) and maps them to **22 step-by-step commands (skills)** (18 journey phases + `/adopt` for projects that already have code + the `/frontend-audit` and `/new-component` UI-suite skills). It forces you to move one phase at a time, checking each gate against evidence in the repo before writing code — **a process that cannot silently skip a check.** What it enforces is the process; the judgment stays yours.

</details>

---

<a id="how-it-works"></a>

## ⚙️ How it Works: The Files and Principles

This system relies on three core files to create a structured, sequential, yet standalone development workflow.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/architecture-dark.svg">
  <img alt="How product-playbook works: PRINCIPLES.md and PRODUCT.md feed the playbook skills, which generate your codebase" src="docs/diagrams/architecture-light.svg">
</picture>

<sub>Diagram source: <a href="docs/diagrams/architecture.mmd"><code>docs/diagrams/architecture.mmd</code></a> (regenerate with <code>sh tools/render-diagrams.sh</code>).</sub>

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
mode — live in [`references/mechanisms.md`](references/mechanisms.md), and the harvested war-story rules
live in [`references/lessons.md`](references/lessons.md). Both install as companions and are read on
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
    ([`docs/state-model.md`](docs/state-model.md)): an **input** gate (`/vision`, `/scope`, `/architect`)
    asks you a question whose answer exists nowhere else, so it can never be skipped or batched; a
    **derivation** gate (`/structure`, `/contracts`, `/build`) works from what earlier phases decided and
    can run with its neighbours, ending in one review; a **verification** gate (`/dev-check`, `/test`,
    `/ship`) reports pass or fail against the repo and only stops you on red. Most of the eighteen stops
    are interviews, not signatures.

### 4. The Forms (`templates/`)
Think of a template as a printed form with blank boxes. A skill fills the boxes so every ticket and every pull request looks the same and nothing gets forgotten. All three are ordinary text files in your repo: edit the wording if you like, and no skill will ever overwrite a form you already have.

| Form | File | Who fills it | What its boxes ask |
|---|---|---|---|
| **The product spine** | `templates/PRODUCT.md` | Every phase skill, one section each | Vision, Scope, Plan, Architecture, and so on. An empty section means that phase is not done yet. |
| **The ticket form** | `templates/feature_ticket_template.md` | `/tickets`, one copy per ticket | The goal; how the work was cut (a thin end-to-end slice, a single layer, or a one-off bug); the feature it belongs to (the optional *Lane*); the **exact files it may touch** — the box that keeps a ticket small and lets two people work without colliding; what data it takes in and hands out; which tickets must come first; what a reviewer can *see working* after merge; a short task list; a definition of done with security built in; the one command that proves it works. |
| **The pull request form** | `templates/pull_request_template.md` | GitHub shows it on every PR | Which issue it closes, a summary, the files changed, and a checklist of what was verified using the project's own test command. |

How they fit together: the spine says *what* to build, the ticket form turns that into small bounded pieces, and the pull request form is how each finished piece is checked back in. (When [Lanekeeper](https://github.com/kish21/parallel-agents) is present it supplies its own pull request form, so `/tickets` leaves that one alone — see `MECHANISMS.md` §Lane mode.)

---

<a id="not-templates"></a>

## 🔩 Why this is not a set of templates

A spine document, six phases, milestones and exit criteria are the vocabulary of project management, and it is a fair first guess that this is a folder of AI-written PM templates. Four things a template cannot do:

**1. Two of the skills ship executable code, not prose.**

- [`commands/frontend-audit/audit.py`](commands/frontend-audit/audit.py) — a real OKLCH→WCAG contrast engine. Contrast is **computed** from your `DESIGN.md` tokens in both light and dark mode, never asserted; an ERROR exits non-zero, so it fails a CI build.
- [`tools/check.py`](tools/check.py) — the gate that guards the gates. Check 9 fails this repo's own build if a phase skill carries a `prior-gate check` heading whose body gates on nothing. That check exists because a skill did exactly that for five releases.

**2. The definition-of-done carries engineering, not just process.** Secret-scan clean and placeholders that *fail the boot* rather than pass a length check · fail-closed authorization and tenant isolation on every data path · the OWASP LLM Top 10 for AI products · migrations rather than hand-edited schema · externals behind provider adapters · verification of the path the product **actually runs**, not the function in isolation · a rollback path and a named post-deploy signal before a release is called done.

**3. The rules are single-sourced and referenced, not copy-pasted.** Every skill links [`PRINCIPLES.md`](PRINCIPLES.md) and names the subset that is load-bearing for its phase — see §[Production safeguards](PRINCIPLES.md#production-safeguards) and §[Production-readiness concern areas](PRINCIPLES.md#production-readiness-concern-areas-the-coverage-checklist). A rule that lived in fifteen copies would drift in fifteen directions.

**4. It has been pointed at its own work, and reported faults.** `/drift-check` on a project this playbook
had itself guided returned **9 findings** — an API spec describing three routes that were never built, a
deferred feature that shipped silently and doubled the surface of 11 open contrast defects, a riskiest
assumption still untested three slices after the override that skipped it. Two days earlier the same
project caught a fault in *this repo*: `/eval` carried a gate's heading and no gate, which became #104,
`tools/check.py` check 9, and the rule *a heading is not a behaviour*.
**[The full case study, with the findings unsoftened →](docs/case-study-subscription-tracker.md)**

**5. The claims are checked in CI.** `python tools/check.py` asserts that the skill set is identical across `commands/`, `manifest.json`, `evals/evals.json` and `VISION.md`; that one version is stated everywhere; that every `#Section` a skill reads is one the `PRODUCT.md` template actually defines; and that every phase skill really gates. Docs that drift from reality are the failure this project exists to catch — including its own.

---

<a id="journey"></a>

## 🗺️ The Playbook Journey

The three-tier map is [above](#-before--after). This is the same journey at full resolution — every skill, what it writes, and when to reach for it. The tiers are a way to hold it in your head; the **six phases** are what the skills themselves are numbered by.

| Tier | Phases | What you are doing |
|---|---|---|
| ① Product thinking | 1 · Product | Deciding what is worth building, and cutting what is not |
| ② Engineering discipline | 2 · Development | Building it so it holds — stack, contracts, features, checkpoint |
| ③ Shipping & learning | 3 · Testing · 4 · Evaluation · 5 · Ship · 6 · Learn | Proving it, releasing it safely, finding out if it worked |

**Security, verification and scope integrity span all three.** They are not stages you pass — they are in `/scope`'s non-goals, `/build`'s definition-of-done, `/dev-check`, `/test` and `/ship`'s security review. A phase that "passed security" once would be the opposite of the position this playbook takes.

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
| **Dev** | `/tickets` | Splits each milestone into 2-4 independently mergeable tickets — **vertical** thin end-to-end slices (each demoable on merge) or **horizontal** layer tickets — recommended per milestone and confirmed by you. Exact file paths, typed in/out, security DoD. Given a description instead, logs ONE ad-hoc bug against the owning file | `docs/issues/*` + issue/PR templates | After `/contracts`, before building; or any time you spot a bug |
| **Dev** | `/build` | Implements feature with testable exit criteria and docs | Feature code + `docs/features/*` | Building feature-by-feature |
| **Dev** | `/dev-check` | Verifies exit criteria and security DoD with evidence | `PRODUCT.md` -> **Dev-complete** | Prior to testing |
| **Dev** | `/deploy` | Executes the runtime target `#Architecture` chose: the repo reaches a host, and `docs/deployment.md` says how | `docs/deployment.md` + `PRODUCT.md` -> **Deployment** | A real request answered on the public URL |
| **Testing** | `/test` | Performs unit/integration/regression and adversarial tests | Test suites | Post-development check |
| **Eval** | `/eval` | Measures quality and latencies against baseline | `PRODUCT.md` -> **Evaluation** | Validating performance/accuracy |
| **Ship** | `/ship` | Does security review, doc audit, PR, and rollback plans | Release PR + CHANGELOG | Deploying to production |
| **Learn** | `/learn` | Tracks success metric and decides: iterate or **KILL** | `PRODUCT.md` -> **Learnings** | Post-launch retro |
| **Cross-Cut** | `/drift-check` | Compares current code and docs vs. original scope | Drift Report | Anytime you suspect creep |

> **One repo, no companions.** An earlier sibling repo (`product-toolkit`) held à-la-carte engineering
> skills that some phases composed. Everything the playbook needs now lives **here** — where a phase
> wanted a small part of one of those skills, the check was written into the phase itself rather than
> pulled in whole. **product-playbook is the guided journey across the entire product arc**
> (vision -> learn), and it installs on its own.
>
> **Companion for parallel agents:** [`Lanekeeper`](https://github.com/kish21/parallel-agents) runs several
> coding agents on one repo without collisions. *product-playbook writes the work down; Lanekeeper divides it
> up.* Each `/tickets` ticket's **Target Files** list is the lane Lanekeeper enforces on every PR. When a
> project is in **lane mode** (a `.lanekeeper/` policy or a `.lane` file is present), `/tickets`, `/build`,
> `/dev-check` and `/ship` follow the four rules in `MECHANISMS.md` §Lane mode — ticket = boundary, lanes are
> features not layers, the spine has one writer, the PR carries its lane. The design note behind that seam is
> [`docs/lane-mode.md`](docs/lane-mode.md).
>
> **Single-master rule for the UI suite.** The UI suite — `/design-system`, `/frontend-audit`, and
> `/new-component` — is **mastered here in product-playbook** (they're coupled through `DESIGN.md`, so one
> master = one place to fix bugs). All three are **bundled here**, as is every
> other phase skill — product-playbook installs **fully standalone**. There is no synced copy of any
> skill in any other repo: a mirror with no sync tooling drifts, and the one that existed did (to a
> quarter of its master's size). One master, one copy.

### How `DESIGN.md` is derived (the UI suite)

For UI products, `/design-system` turns your vision into one concrete, reusable design spec — **`DESIGN.md`** — which
the other two UI skills then consume. So the look is *decided once, confirmed by you, and enforced everywhere*:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/design-system-dark.svg">
  <img alt="How DESIGN.md is derived: PRODUCT.md and universal-laws feed /design-system, which emits DESIGN.md, consumed by /new-component and enforced by /frontend-audit" src="docs/diagrams/design-system-light.svg">
</picture>

<sub>Diagram source: <a href="docs/diagrams/design-system.mmd"><code>docs/diagrams/design-system.mmd</code></a> (regenerate with <code>sh tools/render-diagrams.sh</code>).</sub>

`DESIGN.md` is **derived** (not hand-written) through the sample-and-confirm loop, then **consumed**: `/new-component`
builds against its tokens and `/frontend-audit` mechanically enforces them. Skipped entirely for backend/API/CLI products.

---

<a id="install"></a>

## 🚀 Installation and Setup

**Pick one route.** All three run the same skills — they differ in how you *call* a skill, how you *get updates*, and how many skills you take.

| | **A. Plugin** (recommended) | **B. Copy install** | **C. Copy install `--only`** |
|---|---|---|---|
| You get | all 22 skills | all 22 skills | just the skills you name |
| Best for | new to product work — take the whole guided journey | you want everything, without the plugin system | you already have a process and want a few steps of it |
| Call a skill as | `/product-playbook:vision` | `/vision` (the bare names used throughout this README) | `/vision` |
| Updates | Automatic, once you enable it (step 3 below) | Nothing tracks the copy — re-run the installer | Same — re-run with the same `--only` |
| Lives in | Claude Code's plugin cache, per scope | `~/.claude/commands/` (or `<project>/.claude/commands/`) | same as B |
| Needs | Claude Code ≥ 2.0.70 | `bash` — on Windows, run from **Git Bash** | `bash` — on Windows, run from **Git Bash** |

### A. Plugin (recommended)

1. **Add the marketplace, then install** — inside Claude Code:
   ```
   /plugin marketplace add kish21/product-playbook
   /plugin install product-playbook@product-playbook
   ```
   Choose a scope when asked: **User** (all your projects) · **Project** (everyone who clones this repo, via `.claude/settings.json`) · **Local** (you only, this repo). From a shell instead: `claude plugin install product-playbook@product-playbook --scope user`.
2. **Activate** — if the install summary says `Run /reload-plugins to activate.`, run `/reload-plugins`.
3. **Turn on updates** — third-party marketplaces do **not** auto-update by default. `/plugin` → **Marketplaces** → `product-playbook` → **Enable auto-update**. Claude Code then checks after each session start and tells you to `/reload-plugins` when a new version lands.
   To update by hand: `/plugin marketplace update product-playbook`, then from a shell `claude plugin update product-playbook@product-playbook`.

Skills are **namespaced by the plugin**: wherever this README says `/vision`, type `/product-playbook:vision` (same for `/playbook`, `/build`, …).
Context cost, from `claude plugin details`: ~3.5k tokens always-on per session; each skill's full text loads only when you invoke it.

### B. Copy install

| Scope | Command |
|---|---|
| **Global** — one line, no clone | `curl -fsSL https://raw.githubusercontent.com/kish21/product-playbook/master/install.sh \| bash` |
| **Global** — from a clone | `git clone https://github.com/kish21/product-playbook ~/product-playbook && cd ~/product-playbook && ./install.sh` |
| **Project-level** — teammates get it on clone | `./install.sh --project /path/to/project` then commit `<project>/.claude/` |
| **Subset** — only the skills you name | `./install.sh --only build,ship` (remote: `curl -fsSL …/install.sh \| bash -s -- --only build,ship`) |

What it puts where: the 22 skills → `~/.claude/commands/` (or `<project>/.claude/commands/`), plus the companions the skills read (`PRINCIPLES.md`, `MECHANISMS.md`, `LESSONS.md`, `VISION.md`, `PRODUCT.md` template) → `~/.claude/product-playbook/` (or `<project>/.claude/product-playbook/`).

**Updating:** re-run the exact same command. It overwrites in place. There is no version check — if you want to be told about updates, use route A.

#### C. Copy install, subset (`--only`)

`--only` takes a comma-separated list of skill names — `./install.sh --only build,ship,drift-check`. It installs exactly those (flat skills and directory-form ones like `design-system`, with their `references/`) **plus the companions every skill reads** (`PRINCIPLES.md`, `MECHANISMS.md`, `LESSONS.md`, `VISION.md`, the `PRODUCT.md` template), which are never optional. It combines with `--project`. An unknown name installs nothing and prints the valid ones; `./install.sh --list` prints them on demand. Add more skills later by re-running with a new list — nothing already installed is removed.

Skills stay runnable on their own, but a few **call other skills** when they are present — `/build` → `/code-review`, `/ship` → `/security-review`, `/drift-check` → `/doc-audit`. Those live outside this repo; if they are not installed, the composing skill runs without that step rather than failing.

### Did it work?

Open a new Claude Code session and type `/playbook` (route A: `/product-playbook:playbook`). It should be offered as a command and greet you with the journey. Route A users can also run `/plugin list` and expect `product-playbook@product-playbook · Version: 1.40.0 · enabled`.

### Uninstall

- **A:** `/plugin uninstall product-playbook@product-playbook`, then `/plugin marketplace remove product-playbook`.
- **B:** delete the 22 skill files/folders from `~/.claude/commands/` (or the project's) and the `product-playbook/` companions folder beside it.

---

<a id="contributing"></a>

## 🛠️ Contributing

1.  Add or modify a command in `commands/<name>.md` — or directory-form `commands/<name>/SKILL.md` (+ `references/`) for skills that carry references. Keep them concise and single-purpose.
2.  Register it in **all three**: `VISION.md`, `manifest.json`, and `evals/evals.json` (the CI gate checks they stay in sync). Each skill needs **at least two** eval cases, each with a unique `id` plus a non-empty `skill`, `prompt` and `expected_output`; `files`, `expectations` and `expected_artifacts` are optional. CI checks that shape — it does **not** run the cases.
3.  If a rule earned its place from a real incident, keep the skill file to the **bold one-line rule** and put the war story in `references/case-files-<skill>.md`, pointed to as `(case file: <heading>)`. **Rules go in `PRINCIPLES.md`; mechanisms go in `references/mechanisms.md`; harvested lessons go in `references/lessons.md`** — CI fails any of the three over ~15KB, and fails a `§` pointer that names a heading none of them has.
4.  Run `python tools/check.py` (the CI consistency gate: every skill registered + structured + under the 500-line budget), then `./install.sh`, commit, and open a PR (master requires the `check` to pass).
5.  Run `/drift-check` on this repo to verify nothing drifted.
