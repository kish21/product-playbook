# Product Playbook

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.44.0-blue.svg)](CHANGELOG.md)
![Claude Code skills](https://img.shields.io/badge/Claude%20Code-22%20skills-8A2BE2.svg)

**Build a product with an AI coding agent without losing the plot.**

Claude Code builds fast. What goes wrong is everything around the building: the idea drifts, features nobody asked for creep in, tests go green over a path that is dead in production, a secret lands in a commit.

Product Playbook wraps your coding agent in a product-development workflow — a **gate between each step** that cannot be skipped silently, and **one file at your repo root that remembers what you decided**.

```
idea → vision → validate → scope → plan → architect → structure → foundation
     → contracts → tickets → build → dev-check → test → eval → ship → learn
```

**Is this for you?** You are a developer — first job to staff, or a solo founder — building a real product with Claude Code, with no product manager, designer, QA or security engineer beside you. The playbook plays those roles at each gate. Any language, any framework, AI product or not. ([Who it is *not* for →](VISION.md#who-it-is-for))

---

## 🚀 Get started

**1. Install** — inside Claude Code:

```
/plugin marketplace add kish21/product-playbook
/plugin install product-playbook@product-playbook
```

If it says `Run /reload-plugins to activate.`, run that.

**2. Start with your idea** — new session, empty folder:

```
/product-playbook:vision I want to build a walk-in waitlist for small restaurants — guests scan a QR code at the door and get a text when their table is ready.
```

One rough sentence is enough. You do not need to know the other skills yet.

**3. What happens next**

- It asks you the few things it cannot answer for you — *who is the host? what does a good night look like?*
- It checks the idea against what is on the market **this year**.
- It writes the `Vision` section of `PRODUCT.md` and **stops**, telling you in plain words what it did and what you do next.
- Lost at any point? `/product-playbook:playbook` reads `PRODUCT.md`, works out where you are, and offers the next step.

> Skills are typed with the plugin prefix — `/product-playbook:vision`, `/product-playbook:scope` … The examples below drop the prefix to stay readable.

---

## 🪄 See it in action

One product — the waitlist app — through every skill: what you type, what it asks or does, what it writes, and the failure it prevents.

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

---

## 🧪 Try your own idea

Paste one into a new session in an empty folder, or write your own — one sentence is enough:

```
/product-playbook:vision I want to build a tool that turns a support inbox into a weekly list of the top five product complaints.
/product-playbook:vision I want to build an app that helps a running club organise who drives to which race.
/product-playbook:vision I want to build a CLI that tells me which of my cloud resources nobody has touched in 90 days.
/product-playbook:vision I want to build a bot that summarises a Slack channel into a daily standup note.
```

An AI product with no UI · a web app · a CLI · an AI product that needs a real deployment. Watch which skills switch on.

---

## 🤔 Why not just Claude Code?

Claude Code is the execution engine. It is not a discipline engine. These five happened to me, on a real project, at AI speed:

| The failure | What it looked like |
|---|---|
| **Features nobody asked for** | Building was so cheap the core purpose got buried under "cool" ideas. |
| **Config that silently did nothing** | The block looked correct in the file; the value never flowed end to end. |
| **Green tests over a dead live path** | The suite passed while the path the product actually runs was broken. |
| **A vendor SDK welded into business logic** | Swapping providers meant refactoring half the codebase. |
| **A leaked secret, a missing tenant filter** | One absent scope check away from a cross-customer data leak. |

The answer is narrow on purpose: **a process that cannot silently skip a check.** Every phase ends at a gate. A gate holds until there is evidence in the repo. Passing one is *recorded*, with a reason and a date, so a later reader can tell a gate that held from one that was waved through. Not a slogan: [`tools/check.py`](tools/check.py) check 9 fails this repo's own CI if a phase skill carries a gate's heading without a gate's behaviour. The process is enforced. The judgment stays yours.

**Everything connects through one file.** `PRODUCT.md` sits at your repo root; `#Vision`, `#Scope`, `#Architecture`, `#Tests`, `#Ship log` are its sections. Each phase reads the ones before it and writes its own. An empty section means that phase is not done. It lives in Git beside the code, so the next session — or the next person — picks up exactly where you stopped.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/journey-dark.svg">
  <img alt="The playbook journey: three tiers over six phases. Tier 1 Product thinking — /vision, /validate, /scope, /plan — then an evidence gate: a named user and job-to-be-done, a measured experiment, ONE core feature, non-goals. Tier 2 Engineering discipline — /architect, /structure, /design-system (UI only), /foundation, /contracts, /tickets, /build, /dev-check — then an evidence gate: it runs end to end, every feature's definition-of-done met with how it was verified. Tier 3 Shipping and learning — /test, /eval, /ship, /learn — then an evidence gate: measured against a baseline, security-reviewed with a rollback path, metric instrumented." src="docs/diagrams/journey-light.svg">
</picture>

<sub>Diagram source: <a href="docs/diagrams/journey.mmd"><code>docs/diagrams/journey.mmd</code></a> (regenerate with <code>sh tools/render-diagrams.sh</code>).</sub>

---

## 📚 Contents

| | |
|---|---|
| [The personal story: the vibe coding trap](#story) | the long version of the five failures above |
| [How it works: the files and principles](docs/how-it-works.md#how-it-works) | `PRODUCT.md`, `PRINCIPLES.md`, the commands, the templates |
| [Why this is not a set of templates](docs/how-it-works.md#not-templates) | the executable proof |
| [Case study: the playbook auditing its own work](docs/case-study-subscription-tracker.md) | 9 real findings, unsoftened |
| [The playbook journey](docs/how-it-works.md#journey) | the phase map |
| [Skill reference](docs/how-it-works.md#skill-reference) | every skill, and what each one writes |
| [Installation and setup](docs/install.md) | plugin, copy install, subset, updating, uninstalling |
| [Contributing](#contributing) | adding or changing a skill |
| [VISION.md](VISION.md) · [PRINCIPLES.md](PRINCIPLES.md) · [CHANGELOG.md](CHANGELOG.md) | the contract, the rulebook, the history |

<a id="story"></a>
<details>
<summary><strong>📖 The personal story: the vibe coding trap</strong> — click to read why this playbook exists</summary>

In this AI era, everyone is building a product. I did too.

Armed with tools like Claude Code, Cursor, and Copilot, I was coding at 100mph. I felt like a superhero. I was spinning up files, adding features in minutes, and generating entire modules with single prompts. We call it "vibe coding." It feels like magic — until the vibe fades and reality hits.

Suddenly, I found myself staring at a product that was slipping away from me. I was completely lost.

Here is exactly how it happened:
1. **I let features creep in that nobody needed:** because the AI made building so easy, I kept adding "cool" ideas. Soon, the core purpose of my app was buried under a mountain of secondary features.
2. **I trusted config settings that silently did nothing:** the AI generated configuration blocks that were silently overridden upstream. Everything looked correct in the files, but the value never flowed end to end.
3. **I relied on green tests while the app was dead in production:** my test suites were passing perfectly, but the critical path the product ran on was broken because of decoupled runtime wiring.
4. **I hardcoded vendor APIs directly into my business logic:** I let the AI wire code straight to a specific vendor's SDK. When I needed to swap providers, I had to refactor half the codebase.
5. **I accidentally exposed secrets and skipped tenant isolation:** a missing security filter almost let users see another customer's data, and placeholder keys were constantly in danger of being committed.

**The lesson:** AI is an incredible *execution engine*, but it is not a *discipline engine*. Build without guardrails and it does not just build your product — it multiplies the entropy, debt and chaos at 100mph.

So I wrote a playbook. Not a document — **executable skills with evidence-based gates** that force both me and the AI to keep engineering discipline, one phase at a time, checking each gate against evidence in the repo before writing code. What it enforces is the process; the judgment stays mine.

</details>

---

## ⭐ Feedback

This is a working tool, and the thing I most want to know is whether the workflow helps. Try it with a real idea, build something, break it, then open an issue and tell me: what was useful, what was confusing, what you would remove, what you would add, and whether it gave you anything Claude Code alone did not.

<a id="contributing"></a>

## 🛠️ Contributing

1. Add or modify a command in `commands/<name>.md` — or directory-form `commands/<name>/SKILL.md` (+ `references/`) for skills that carry references. Keep them concise and single-purpose.
2. Register it in **all three**: `VISION.md`, `manifest.json`, and `evals/evals.json` (the CI gate checks they stay in sync). Each skill needs **at least two** eval cases, each with a unique `id` plus a non-empty `skill`, `prompt` and `expected_output`. CI checks that shape — it does **not** run the cases.
3. If a rule earned its place from a real incident, keep the skill file to the **bold one-line rule** and put the war story in `references/case-files-<skill>.md`, pointed to as `(case file: <heading>)`. **Rules go in `PRINCIPLES.md`; mechanisms go in `references/mechanisms.md`; harvested lessons go in `references/lessons.md`** — CI fails any of the three over ~15KB, and fails a `§` pointer that names a heading none of them has.
4. Run `python tools/check.py` (the CI consistency gate), commit, and open a PR (master requires the `check` to pass).
5. Run `/drift-check` on this repo to verify nothing drifted.
