# Product Playbook

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.44.0-blue.svg)](CHANGELOG.md)
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

*(The short version. The full 18 steps are in the table below.)*

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

## 🧭 Does it fit my product?

- **Has screens** → the design steps run: `/design-system` for the look, `/new-component` for each piece of UI, `/frontend-audit` to check it. **API or CLI only** → they're skipped.
- **Uses an LLM** → extra checks for AI: the model can be swapped without touching your logic, prompts live in files, and the tests try to trick it. **No LLM** → those checks are skipped, not faked.
- **Needs a public URL** → `/deploy` runs. **Laptop only** → it doesn't.
- **Already have code?** → start with `/product-playbook:adopt`. It reads your repo and drafts the decisions for you to confirm.
- **More than one builder?** → the ticket board already has a lane and an owner per module.

---

## ⚙️ Ways to run it

- **Guided** — `/product-playbook:playbook`. It knows where you are and offers the next step.
- **One step at a time** — run any skill on its own, in any order.
- **A few steps in one go** — when offered, say yes to run foundation → contracts → tickets together, or architect → structure. Every question is still asked; you get one review at the end.
- **Log a bug mid-build** — `/product-playbook:tickets "Bug: …"` files one issue and touches nothing else.

Under the hood it uses Claude Code's own `/code-review`, `/security-review`, `/run`, `/loop` and `/schedule`.

---

## 🧪 Try your own idea

```
/product-playbook:vision I want to build a tool that turns a support inbox into a weekly list of the top five complaints.
/product-playbook:vision I want to build an app that helps a running club organise who drives to which race.
/product-playbook:vision I want to build a CLI that finds cloud resources nobody has touched in 90 days.
```

One sentence is enough.

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
| [Case study](docs/case-study-subscription-tracker.md) | the playbook auditing its own work: 9 findings, unsoftened |
| [Installation and setup](docs/install.md) | plugin, copy install, subset, updating, uninstalling |
| [VISION.md](VISION.md) · [PRINCIPLES.md](PRINCIPLES.md) · [CHANGELOG.md](CHANGELOG.md) | the contract, the rulebook, the history |

---

## ⭐ Feedback

Try it with a real idea. Build something. Break it. Then open an issue and tell me what was useful, what was confusing, what you'd remove, and what you'd add.

<a id="contributing"></a>

## 🛠️ Contributing

1. Add or modify a command in `commands/<name>.md` — or directory-form `commands/<name>/SKILL.md` (+ `references/`) for skills that carry references. Keep them concise and single-purpose.
2. Register it in **all three**: `VISION.md`, `manifest.json`, and `evals/evals.json` (the CI gate checks they stay in sync). Each skill needs **at least two** eval cases, each with a unique `id` plus a non-empty `skill`, `prompt` and `expected_output`. CI checks that shape — it does **not** run the cases.
3. If a rule earned its place from a real incident, keep the skill file to the **bold one-line rule** and put the war story in `references/case-files-<skill>.md`, pointed to as `(case file: <heading>)`. **Rules go in `PRINCIPLES.md`; mechanisms go in `references/mechanisms.md`; harvested lessons go in `references/lessons.md`** — CI fails any of the three over ~15KB, and fails a `§` pointer that names a heading none of them has.
4. Run `python tools/check.py` (the CI consistency gate), commit, and open a PR (master requires the `check` to pass).
5. Run `/drift-check` on this repo to verify nothing drifted.
