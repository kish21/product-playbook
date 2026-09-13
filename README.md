# Product Playbook

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.44.0-blue.svg)](CHANGELOG.md)
![Claude Code skills](https://img.shields.io/badge/Claude%20Code-22%20skills-8A2BE2.svg)

**Build a product with an AI coding agent without losing the plot.**

Claude Code builds fast. The problem is what happens around the building: the idea drifts, features nobody asked for creep in, tests go green over a path that is dead in production, a secret lands in a commit. Product Playbook wraps your coding agent in a product-development workflow with a **gate between each step** — a gate that cannot be skipped silently — and **one file at your repo root that remembers what you decided**.

```
idea → /vision → /validate → /scope → /plan → /architect → /structure → /foundation
     → /contracts → /tickets → /build → /dev-check → /test → /eval → /ship → /learn
```

**Is this for you?** You are a developer (first job to staff, or a solo founder) building a real product with Claude Code, and there is no product manager, designer, QA or security engineer beside you. If that is you, the playbook plays those roles at each gate. It works for any language or framework, and for AI and non-AI products alike. ([Who it is not for →](VISION.md#who-it-is-for))

## 🚀 Get started in two minutes

**1. Install** — inside Claude Code:

```
/plugin marketplace add kish21/product-playbook
/plugin install product-playbook@product-playbook
```

If it says `Run /reload-plugins to activate.`, run that. (Other install routes, updates, uninstall: [docs/install.md](docs/install.md).)

**2. Start with your idea** — in a new session, in an empty folder:

```
/product-playbook:vision I want to build a walk-in waitlist for small restaurants — guests scan a QR code at the door and get a text when their table is ready.
```

One rough sentence is enough. You do not need to know the other skills yet.

**3. What happens next.** The skill asks you a few questions it cannot answer for you (who is the host? what does a good night look like?), checks the idea against what exists on the market *this year*, writes the `Vision` section of `PRODUCT.md`, and **stops**. It tells you in plain words what it did and what you do next. When you are ready, run the next skill. Lost? Type `/product-playbook:playbook` — it reads `PRODUCT.md`, works out where you are, and offers the next step.

> Every skill below is typed with the plugin prefix: `/product-playbook:vision`, `/product-playbook:scope`, and so on. The examples drop the prefix to stay readable.

## 🪄 See it in action

One product, the waitlist app, walked through every phase. Each step shows what you type, what the skill asks, what it writes, and the failure it exists to prevent.

### Phase 1 — Product: decide what is worth building

**💡 `/vision`** — *you type:* `/vision I want to build a walk-in waitlist …`
It asks: who exactly is the user, what job are they hiring this for, what is the one number that says it worked? It searches the current market and tells you who already does this. It writes: a one-sentence vision, the target user (*the host at a 40-seat restaurant on a Friday night*), the north star (*80 % of walk-ins seated without the host chasing anyone, by March*), and the **riskiest assumption** (*guests will scan a code instead of giving their name at the door*).
*Why it matters:* without a named user and a number, every later "should we add X?" has no answer.

**🔎 `/validate`** — *you type:* `/validate`
It takes the riskiest assumption and designs the **cheapest real-world test before any code**: a paper QR code on the door linking to a form, one Friday night, pass mark 60 % of walk-ins scan. You set the threshold *before* the result. The verdict is **proceed, pivot or kill**. If the test takes weeks, the next phases run *provisionally* and the section says so.
*Why it matters:* this is the phase that saves you from building something nobody wanted.

**✂️ `/scope`** — *you type:* `/scope`
It locks **ONE core feature** — *a guest joins the queue and gets told when their table is ready* — lists what is deferred (with the trigger that would bring it back: *host-side editing, once two real nights show the host needs it*) and writes the **non-goals**: reservations, payments, menus, accounts. Reopening a non-goal later is allowed, but it is recorded with a date and a reason.
*Why it matters:* this is the anti-scope-creep gate. Every later skill checks against this list.

**🗺️ `/plan`** — *you type:* `/plan`
It sequences the scope into milestones, core first, each with a **testable exit criterion**: M1 *a guest joins and gets a text on a laptop demo*, M2 *the host sees and seats the queue*, M3 *one real Friday night with a real restaurant*.
*Why it matters:* a milestone with no exit criterion is a wish. This is what `/dev-check` and `/ship` measure against later.

### Phase 2 — Development: build it so it holds

**🏗️ `/architect`** — *you type:* `/architect`
It asks the constraints only you know (budget, where it will run, who maintains it), benchmarks the **current-year** options for each open decision, and records the stack and the key decisions as ADRs — including the runtime target, the commit-hook tool, and that every external service (the SMS provider) sits behind an adapter. It offers to **chain straight into `/structure`** in the same session.
*Why it matters:* a vendor SDK welded into business logic is the single most expensive thing to undo.

**📁 `/structure`** — *you type:* `/structure`
It draws the folder shape — **one module per thing the product does** (`queue/`, `notify/`, `host/`), each holding its own routes, store and tests — plus the root scaffolding: agent instructions, `.env.example`, secret-scan, commit hooks, a task runner, and a `prompts/` folder if the product uses an LLM. Writes `STRUCTURE.md`, so "where does this go?" always has an answer.

**🎨 `/design-system`** — *UI products only.* *you type:* `/design-system`
It asks what look *you* want, proposes an archetype, builds **one real sample page**, stops until you like it, then writes `DESIGN.md` with the tokens every later screen reuses. Kills the generic AI look and the too-small fonts. Skipped for a backend, API or CLI product.

**🧱 `/foundation`** — *you type:* `/foundation` (or accept the **batch** offer, below)
The walking skeleton that actually runs: dependencies, config loader, structured logging, the database wired, lint and hooks, and a CI that mirrors the production boot. A placeholder secret left in `.env` **refuses to boot by name**, so it can never ship.
*Why it matters:* "config that silently did nothing" is a foundation failure.

**📐 `/contracts`** — *you type:* `/contracts`
Typed models, schemas, migrations and the API contract **before** business logic — so the front and the back agree on what a `QueueEntry` is before either is written.

**🎫 `/tickets`** — *you type:* `/tickets`
It turns each milestone into small, independently mergeable tickets, **grouped into lanes by module** (`queue`, `notify`, `host`), shows you the proposal, and after you confirm files them as GitHub issues on a **Delivery Board** with Status · Owner · Lane · Seat. Each ticket names its exact files, typed inputs and outputs, and a definition of done that includes security. Works the same whether one person builds it or four.
*Mid-build, one bug:* `/tickets "Bug: the SMS send is not retried on a 5xx"` files **one** issue against the file that owns it and touches nothing else.

**🛠️ `/build`** — *you type:* `/build M1-SLICE-01`
One ticket at a time. Reuse before writing, verify the **live path** (the request the product actually serves, not a function in isolation), run `/code-review` on the diff, write the feature doc, commit. Its last message is always the plain close: what was built, how it was verified, what you do next.
*Why it matters:* green tests over a dead live path is the failure this step is built around.

**✅ `/dev-check`** — *you type:* `/dev-check`
The checkpoint: is every core-scope feature built, does it run, did each meet its exit criteria and security definition of done — **with evidence you can re-run**, not a claim.

**🌐 `/deploy`** — *when the product needs a real URL.* *you type:* `/deploy`
Executes the runtime target `/architect` already chose (it never reopens it). Done when someone who is not you loads the page.

### Phases 3–6 — Test, evaluate, ship, learn

**🧪 `/test`** — unit (mocked), integration (real seams), regression, and **adversarial**: the wrong host token, a double claim on the last table, prompt injection if there is an LLM.

**📊 `/eval`** — is it actually *good*, measured against the criteria set in `/plan`, with operational failures separated from quality, and an honest confidence score. AI products can add `/enterprise-ai-audit`.

**🚢 `/ship`** — fresh-eyes `/code-review`, `/security-review`, docs reconciled to what was really built, a rollback path, the PR, a handoff note, and *"start a new session"*.

**📈 `/learn`** — after the real Friday night: did the north star move? A short retro, then the next cycle from evidence — back to `/scope` or `/plan`. Sets up `/loop` or `/schedule` to re-measure on a cadence.

**🛑 `/drift-check`** — *any time.* *"Are we still building the vision?"* Finds features built that were non-goals, docs that no longer match the code, an API spec describing routes that were never built. Reports; never advances the chain.

## 🧭 Which skills apply to your product?

Every product runs the spine (`/vision` → `/learn`). A few skills switch on or off depending on what you are building — the playbook works this out from `PRODUCT.md`, and this is why:

| Your product | Extra skills that run | Skipped | Why |
|---|---|---|---|
| **Has a user interface** (web app, mobile web) | `/design-system` before any screen · `/new-component` for each component · `/frontend-audit` after UI changes and in CI | — | Screens built without agreed tokens come out looking AI-generated and inaccessible. `/frontend-audit` *computes* contrast (OKLCH → WCAG) instead of asserting it. |
| **Backend, API or CLI only** | — | `/design-system`, `/new-component`, `/frontend-audit` | Nothing to design. `/structure` and `/contracts` carry the weight instead. |
| **Uses an LLM** (chat, extraction, agents) | `/structure` adds a `prompts/` folder · `/architect` puts the provider behind an adapter · `/test` adds prompt-injection and jailbreak cases · `/eval` can add `/enterprise-ai-audit` | — | Swapping the model must not touch business logic; the OWASP LLM Top 10 is part of `/ship`'s security review. |
| **No LLM** | — | the AI-specific checks above | They are skipped, not faked: the definition of done never lists a check that did not run. |
| **Needs a public URL** (real users, a second device, a milestone criterion) | `/deploy` after `/dev-check` | — | Deciding a host in `/architect` and never executing it is a real failure this playbook once had. |
| **Runs on your laptop only** (internal tool, experiment) | — | `/deploy` | A URL nobody needs is work nobody needs. |
| **Already has code** but no `PRODUCT.md` | `/adopt` first | `/vision` from scratch | It drafts the spine *from the repo* (docs, package metadata, routes, tests, CI), tags every inferred line, and confirms each section with you before writing. |
| **Built by more than one person or agent** | `/tickets` lanes + the Delivery Board | — | A lane per module, an owner and a seat per card, so two people never edit the same folder at once. Solo builders get the same board; every seat is you. |

## ⚙️ Ways to run it

| You want | Type | What happens |
|---|---|---|
| **Be guided** (default) | `/product-playbook:playbook` | Reads `PRODUCT.md`, names where you are, offers the next phase. One phase, then it stops for you. |
| **One phase per session** | `/product-playbook:scope` | Any skill runs on its own, in any order. Out-of-order use is allowed and *visible*: it names what is at risk and lets you override with a recorded reason. |
| **Batch the derivation phases** | say **yes** when `/playbook` or `/structure` offers `/foundation` + `/contracts` + `/tickets` as one batch | Nothing inside a phase changes; one commit per phase; it still stops wherever a phase asks you to confirm, and on the first red; one review at the end. Never the default. |
| **Chain `/architect` → `/structure`** | say **yes** when `/architect` offers it at its first step | The stack decision and the folder shape in one session, every question kept. |
| **Log one bug mid-build** | `/product-playbook:tickets "Bug: …"` | One issue, against the file that owns it, on the board. The backlog is untouched. |
| **Bring in an existing repo** | `/product-playbook:adopt` | Inferred `PRODUCT.md`, confirmed section by section. |
| **Check for drift, any time** | `/product-playbook:drift-check` | A report, and a dated row in `#Drift log` if anything is confirmed. |
| **Re-measure after launch** | `/learn` sets it up | Composes Claude Code's `/loop` or `/schedule` to re-check the metric on a cadence. |

**Skills it calls that ship with Claude Code:** `/code-review` (in `/build` and `/ship`), `/security-review` (in `/ship`, and on any auth or data change), `/run` (to drive the app in `/build` and `/test`), `/loop` and `/schedule` (in `/learn`). If your harness names one differently, any equivalent satisfies the gate — the record says which was used. A gate is never skipped for a missing command, and never silently.

## 🤔 Why not just Claude Code?

Claude Code is the execution engine. It is not a discipline engine. These five happened to me on a real project, at AI speed:

| The failure | What it looked like |
|---|---|
| **Features nobody asked for** | Building was so cheap the core purpose got buried under "cool" ideas. |
| **Config that silently did nothing** | The block looked correct in the file; the value never flowed end to end. |
| **Green tests over a dead live path** | The suite passed while the path the product actually runs was broken. |
| **A vendor SDK welded into business logic** | Swapping providers meant refactoring half the codebase. |
| **A leaked secret, a missing tenant filter** | One absent scope check away from a cross-customer data leak. |

The playbook's answer is narrow on purpose: **a process that cannot silently skip a check.** Every phase ends at a gate; a gate holds until there is evidence in the repo; passing one is *recorded* with a reason and a date, so a later reader can tell a gate that held from one that was waved through. It is not a slogan — [`tools/check.py`](tools/check.py) check 9 fails this repo's own CI if any phase skill carries a gate's heading without a gate's behaviour. What it enforces is the process. The judgment stays yours.

**Everything connects through one file.** `PRODUCT.md` sits at your repo root. `#Vision`, `#Scope`, `#Architecture`, `#Tests`, `#Ship log` are its sections; each phase reads the ones before it and writes its own. An empty section means that phase is not done. It lives in Git beside the code, so the next session — or the next person — can pick up exactly where you stopped.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/journey-dark.svg">
  <img alt="The playbook journey: three tiers over six phases. Tier 1 Product thinking — /vision, /validate, /scope, /plan — then an evidence gate: a named user and job-to-be-done, a measured experiment, ONE core feature, non-goals. Tier 2 Engineering discipline — /architect, /structure, /design-system (UI only), /foundation, /contracts, /tickets, /build, /dev-check — then an evidence gate: it runs end to end, every feature's definition-of-done met with how it was verified. Tier 3 Shipping and learning — /test, /eval, /ship, /learn — then an evidence gate: measured against a baseline, security-reviewed with a rollback path, metric instrumented." src="docs/diagrams/journey-light.svg">
</picture>

<sub>Diagram source: <a href="docs/diagrams/journey.mmd"><code>docs/diagrams/journey.mmd</code></a> (regenerate with <code>sh tools/render-diagrams.sh</code>).</sub>

## 🧪 Try your own idea

After installing, paste one of these into a new session in an empty folder, or write your own — one sentence is enough:

```
/product-playbook:vision I want to build a tool that turns a support inbox into a weekly list of the top five product complaints.
/product-playbook:vision I want to build an app that helps a running club organise who drives to which race.
/product-playbook:vision I want to build a CLI that tells me which of my cloud resources nobody has touched in 90 days.
/product-playbook:vision I want to build a bot that summarises a Slack channel into a daily standup note.
```

The first is an AI product with no UI, the second a web app, the third a CLI, the fourth an AI product that needs a real deployment. Watch which skills switch on.

## 📚 Go deeper

- [How it works](docs/how-it-works.md) — `PRODUCT.md`, the rulebook, the command contract, the forms, why this is not a set of templates, the full skill reference, the UI suite.
- [Installation and setup](docs/install.md) — plugin, copy install, subset install, updating, uninstalling.
- [Case study](docs/case-study-subscription-tracker.md) — the playbook pointed at its own work: 9 findings, unsoftened.
- [VISION.md](VISION.md) · [PRINCIPLES.md](PRINCIPLES.md) · [CHANGELOG.md](CHANGELOG.md)

## ⭐ Feedback

This is a working tool, and the thing I most want to know is whether the workflow helps. Try it with a real idea, build something, break it, then open an issue and tell me: what was useful, what was confusing, what you would remove, what you would add, and whether it gave you anything Claude Code alone did not.

<a id="contributing"></a>

## 🛠️ Contributing

1. Add or modify a command in `commands/<name>.md` — or directory-form `commands/<name>/SKILL.md` (+ `references/`) for skills that carry references. Keep them concise and single-purpose.
2. Register it in **all three**: `VISION.md`, `manifest.json`, and `evals/evals.json` (the CI gate checks they stay in sync). Each skill needs **at least two** eval cases, each with a unique `id` plus a non-empty `skill`, `prompt` and `expected_output`. CI checks that shape — it does **not** run the cases.
3. If a rule earned its place from a real incident, keep the skill file to the **bold one-line rule** and put the war story in `references/case-files-<skill>.md`, pointed to as `(case file: <heading>)`. **Rules go in `PRINCIPLES.md`; mechanisms go in `references/mechanisms.md`; harvested lessons go in `references/lessons.md`** — CI fails any of the three over ~15KB, and fails a `§` pointer that names a heading none of them has.
4. Run `python tools/check.py` (the CI consistency gate), commit, and open a PR (master requires the `check` to pass).
5. Run `/drift-check` on this repo to verify nothing drifted.
