# Product Playbook

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.52.0-blue.svg)](CHANGELOG.md)
![Claude Code skills](https://img.shields.io/badge/Claude%20Code-22%20skills-8A2BE2.svg)

**Build a product with AI without losing the plot.**

## 🧩 The problem

Claude Code can build software incredibly fast.

It is just as fast at building the wrong thing. You start with one idea and end up with something else — extra features nobody asked for, tests that pass while the app is broken, a secret in a commit. Nothing stopped it, because nothing was checking.

## 💡 The solution

Product Playbook adds a product-development workflow around your coding agent.

```
idea → vision → validate → scope → plan → build → test → ship → learn
```

*(The short version. The table below has all 18 steps. The other four of the 22 skills are helpers, not steps: `/playbook` guides you through the steps, `/adopt` brings in a project that already has code, and `/new-component` and `/frontend-audit` help build and check screens.)*

Each step checks the one before it. Each step writes its decision into one file, `PRODUCT.md`, next to your code. No step is skipped silently — a step that can't show its evidence stops and says so.

**For:** developers and founders building a real product with Claude Code, without a product manager, designer, QA or security engineer on hand. The playbook asks the questions those roles would ask, at every step. Any language, any stack, AI product or not.

## 🤔 Why it works

Claude Code is a great builder. It is not a great *decider*. These five happened to me on a real project:

- Features nobody asked for.
- Config that looked right and did nothing.
- Tests green, app dead in production.
- A vendor's SDK welded into the business logic.
- A secret exposed; a missing security filter.

Each one is a decision that was never made, or never checked. So every step of the playbook ends at a gate that asks for evidence in the repo. If you choose to pass a gate anyway, that choice is written down with a date and a reason. The next session — or the next person — reads `PRODUCT.md` and picks up exactly where you stopped.

---

## 🚀 Get started

**1. Install** — inside Claude Code:

```
/plugin marketplace add kish21/product-playbook
/plugin install product-playbook@product-playbook
```

If it says `Run /reload-plugins to activate.`, run that.

**2. Start with your idea** — open Claude Code in an empty folder and type:

```
/product-playbook:vision I want to build a walk-in waitlist for small restaurants.
```

That's it. One rough sentence. The playbook asks you a few questions, writes down the vision, and tells you what to do next.

Not sure where you are? `/product-playbook:playbook` looks at your project and offers the next step.

---

## 🪄 See it in action

Take the waitlist idea. This is what each step gives you. (You type each command with the plugin prefix — `/product-playbook:scope` — shortened here to `/scope`.)

| | Step | You type | You get |
|---|---|---|---|
| 💡 | **Vision** | `/vision I want to build a walk-in waitlist …` | Who it's for, the problem, one number that says it worked — and who already does this. |
| 🔎 | **Validate** | `/validate` | The cheapest real-world test of your riskiest assumption, with a pass mark set *before* you run it. Proceed, pivot or kill. |
| ✂️ | **Scope** | `/scope` | ONE core feature. A list of what you will *not* build. |
| 🗺️ | **Plan** | `/plan` | Milestones, core first, each with a clear "done". |
| 🏗️ | **Architect** | `/architect` | The stack, chosen against *your* budget and constraints, decisions written down. |
| 📁 | **Structure** | `/structure` | The folder layout, and why. "Where does this go?" always has an answer. |
| 🎨 | **Design system** | `/design-system` | *(Apps with a UI.)* One sample page you approve, then the look every screen reuses. |
| 🧱 | **Foundation** | `/foundation` | A skeleton that runs: config, logging, database, CI. Placeholder secrets refuse to boot. |
| 📐 | **Contracts** | `/contracts` | The data models and API agreed before any logic is written. |
| 🎫 | **Tickets** | `/tickets` | Small tickets on a GitHub board, grouped so two people never collide. |
| 🛠️ | **Build** | `/build M1-SLICE-01` | One ticket built, reviewed, verified on the real path, documented. |
| ✅ | **Dev check** | `/dev-check` | Proof that every planned feature is really done. |
| 🌐 | **Deploy** | `/deploy` | *(When you need a real URL.)* The product live, and how it got there written down. |
| 🧪 | **Test** | `/test` | Unit, integration, regression — and the attacks: bad tokens, double bookings, prompt injection. |
| 📊 | **Eval** | `/eval` | Is it actually good? Measured, with an honest confidence score. |
| 🚢 | **Ship** | `/ship` | Code review, security review, docs matched to reality, a rollback plan, the PR. |
| 📈 | **Learn** | `/learn` | Did the number move? What to build next, from evidence. |
| 🛑 | **Drift check** | `/drift-check` | *(Any time.)* "Are we still building what we set out to build?" |

Each step reads what the earlier steps decided.

---

## 🧭 Does it fit what I'm building?

Yes — the playbook adapts to the kind of product. A few examples:

- **You're building an app people will use on their phones** — say, the waitlist above. Before any screen is built, the playbook helps you agree on how it should look, from one sample page. Every screen after that matches it, and a check tells you if the text is too small or too hard to read.
- **You're building something with no screens at all** — a command-line tool, or a service other software talks to. The design steps simply don't run. You go from the plan to the code.
- **Your product uses AI** — it summarises, answers, or decides something. You get extra safety checks: the AI model can be swapped out later without rewriting your code, and the tests try to trick it the way a bad actor would.
- **You already have code**, but it grew without a plan. Start with `/product-playbook:adopt`. It reads what you have, writes down what it thinks you decided, and asks you to confirm each part before it moves on.
- **You're not building alone** — a friend, a colleague, or a second AI agent is helping. The tickets come grouped by area, each with an owner, so two people never end up editing the same thing at the same time.

---

## 📚 Contents — the thinking behind the skills

| Read | What it covers |
|---|---|
| [The personal story](docs/story.md) | why this exists — the five failures in full |
| [The full walkthrough](docs/how-it-works.md#walkthrough) | every skill: what it asks, what it writes, what it prevents |
| [Which skills apply, in detail](docs/how-it-works.md#which-skills) · [Ways to run it, in detail](docs/how-it-works.md#ways-to-run) | batch mode, chain mode, overrides, the skills it calls |
| [How it works](docs/how-it-works.md#how-it-works) | `PRODUCT.md`, the rulebook, the command contract, the templates |
| [The playbook journey](docs/how-it-works.md#journey) | three tiers over six phases, with the gate after each |
| [Why this is not a set of templates](docs/how-it-works.md#not-templates) | the executable proof |
| [Skill reference](docs/how-it-works.md#skill-reference) | every skill and what it writes |
| [Case study](docs/case-study.md) | the playbook auditing its own work: 9 findings, unsoftened |
| [Installation and setup](docs/install.md) | plugin, copy install, subset, updating, uninstalling |
| [VISION.md](VISION.md) · [PRINCIPLES.md](PRINCIPLES.md) · [CHANGELOG.md](CHANGELOG.md) | the contract, the rulebook, the history |

---

## ⭐ Feedback

Try it with a real idea. Build something. Break it. Then open an issue and tell me what was useful, what was confusing, what you'd remove, and what you'd add.

<a id="contributing"></a>

## 🛠️ Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — how skills are added, registered, tested and kept small.
