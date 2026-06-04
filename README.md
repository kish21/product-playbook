# product-playbook

A phased, principle-driven **product-building skill set** for Claude Code. It walks anyone —
a newcomer (technical or not) *or* an experienced builder dropping into one phase — through the
**full product lifecycle**, with hard-won engineering principles **baked into each phase** so good
results are the default. It is **anti-scope-creep by design**.

> Sibling to [`product-toolkit`](https://github.com/kish21/product-toolkit). `product-toolkit` is a
> grab-bag of individual dev/quality skills; **`product-playbook` is the opinionated end-to-end
> *journey*.**

## How you actually use it (read this first)

**It is a guided, step-by-step process — not a one-shot generator.** Running `/vision` does the
*vision* phase only; it does **not** build your whole app. You move through the phases one at a time,
and each one asks you a few questions and ends with a quick check before moving on — so you stay in
control and nothing drifts.

Two ways to drive it:

- **Be guided (easiest):** run **`/playbook`**. It looks at how far you've got, explains the next
  phase, runs it, pauses at the gate for your OK, then moves on. One command, one phase at a time.
- **Drive it yourself:** run the phases in order, following each skill's *"next: run /X"* handoff:
  `/vision → /scope → /plan → /architect → /structure → /foundation → /contracts → /build →
  /dev-check → /test → /eval → /ship → /learn`. Run **`/drift-check`** anytime.

Either way: everything accumulates in a single **`PRODUCT.md`** at your project root (the shared spine),
and you can **jump into any single skill** on an existing project (e.g. just `/structure` or `/test`).

## How it works (three ideas)

1. **One shared file is the memory.** Every skill reads + appends to **`PRODUCT.md`** — so the build
   step knows the vision, the test step knows the features, and a newcomer can read the whole story
   top-to-bottom. (A file, not Claude memory: shareable, versioned, travels with the repo.)
2. **Principles are baked in, once.** Every skill references **`PRINCIPLES.md`** (single source) and
   enforces the subset that matters for its phase — so even a non-techie gets senior-level discipline.
3. **Sequential but standalone.** Run the phases in order, or jump into any skill — each bootstraps
   from `PRODUCT.md` or the existing codebase. Skills **compose existing Claude Code skills**
   (`/code-review`, `/security-review`, `/verify`, `/run`, `/doc-create`, `/doc-audit`, `/loop`,
   `github-pr-flow`) rather than reinventing them.

Each skill ends by **self-verifying its exit criteria** — it won't hand off a half-done phase.

## Start here: `/playbook`

**New or unsure? Run `/playbook` — it's the only command you need to remember.** It reads how far
you've got, tells you the next phase in plain language, runs it, and **checks with you before moving
on**. It doesn't build anything itself — it *drives* the skills in the table below, one at a time, and
never skips a gate. (Prefer to drive yourself? Run the skills in order instead — each one tells you the
next.)

```
START → /playbook  (guides you through ↓, one phase at a time)

1 PRODUCT      /vision → /scope → /plan
2 DEVELOPMENT  /architect → /structure → /foundation → /contracts → /build → /dev-check
3 TESTING      /test
4 EVALUATION   /eval
5 SHIP         /ship
6 LEARN        /learn
ANYTIME        /drift-check
```

## The skills — what each does, what it produces, when to use it

| Skill | What it does | Output it produces | Use it when |
|---|---|---|---|
| `/playbook` | Guides you through the phases, one at a time, pausing at each gate | *(routes only — runs the next skill; writes nothing itself)* | You're new / unsure what's next |
| `/vision` | Sharpen the idea: who · problem · value · metric · risk, vs the market | `PRODUCT.md` → **Vision** | Starting a brand-new product |
| `/scope` | Pick the **one** core feature; list Deferred (+triggers) & Non-goals | `PRODUCT.md` → **Scope** | After vision / scope is creeping |
| `/plan` | Core-first milestones, each a testable "done" + concern coverage | `PRODUCT.md` → **Plan** | After scope / you need a roadmap |
| `/architect` | Choose stack + tools; ADRs (patterns/anti-patterns); resilience; budget | `PRODUCT.md` → **Architecture** | Before writing any code |
| `/structure` | Clean folders (explained) + root scaffolding; `app/prompts/` for AI | folder tree + `STRUCTURE.md` + **Structure** | The first thing you build |
| `/foundation` | Skeleton that **runs**: config · logging · pre-commit + CI auto-layer | running skeleton + CI + **Foundation** | After structure |
| `/contracts` | Typed models/schemas/migrations; versioning · PII · keys | models/migrations + **Contracts** | Before business logic |
| `/build` | Build **one** feature: security-in-DoD · reuse · verify live path · doc | code + `docs/features/*` + **Build log** | Implementing each feature |
| `/dev-check` | Verify each feature's exit criteria + security DoD, with evidence | `PRODUCT.md` → **Dev-complete** | Before moving to testing |
| `/test` | Unit + integration + regression + adversarial + golden set; live path | tests + `PRODUCT.md` → **Tests** | After dev-check |
| `/eval` | Measure quality vs a baseline; cost; honest confidence score | `PRODUCT.md` → **Evaluation** | "Is it actually good?" |
| `/ship` | Review + security + reconcile docs + rollout safety + PR + handoff | PR + `PRODUCT.md` → **Ship log** | A subtask is done |
| `/learn` | Metric (instrumented) · user signal · decide next / **kill** | `PRODUCT.md` → **Learnings** | After a release lands |
| `/drift-check` | Detect scope / vision / code↔docs drift | report + `PRODUCT.md` → **Drift log** | Whenever you suspect creep |

Everything a skill produces lands in **your project** — `PRODUCT.md` (the spine), `STRUCTURE.md`, the
scaffolded code, `docs/features/*` — so the output becomes part of your repo and gets committed.

## Three ways to include it — you choose

| Way | Command | Who gets it | Command names |
|---|---|---|---|
| **Global (per machine)** | `./install.sh` | you, in every project on your machine | `/vision` |
| **Project-level (committed)** | `./install.sh --project /path/to/project` | anyone who clones *that* repo | `/vision` |
| **Plugin (one-command + updates)** | `/plugin marketplace add kish21/product-playbook` then `/plugin install product-playbook@product-playbook` | anyone, via Claude Code | `/product-playbook:vision` (namespaced) |

```bash
# Global (one-liner)
curl -fsSL https://raw.githubusercontent.com/kish21/product-playbook/master/install.sh | bash

# Global (local clone)
git clone https://github.com/kish21/product-playbook ~/product-playbook
cd ~/product-playbook && ./install.sh

# Project-level (commit .claude/ so your team gets it on clone)
cd ~/product-playbook && ./install.sh --project /path/to/your/project

# Plugin (inside Claude Code)
/plugin marketplace add kish21/product-playbook
/plugin install product-playbook@product-playbook
```

- **Global** copies the skills to `~/.claude/commands/` + companions to `~/.claude/product-playbook/`.
- **Project-level** puts them in `<project>/.claude/commands/` + `<project>/.claude/product-playbook/` — commit that folder and teammates get the skills with nothing installed globally.
- **Plugin** auto-discovers `commands/` from the repo; note commands are **namespaced** (`/product-playbook:vision`), and the bundled `PRINCIPLES.md`/`PRODUCT.md` resolve under the plugin root.

*Which to pick:* your own toolkit everywhere → **global**; give one project's team the skills on clone → **project-level**; widest distribution + updates → **plugin**.

## What's baked in (the principles)

The discipline lives in [`PRINCIPLES.md`](PRINCIPLES.md): architect → verify → no-hardcoding →
benchmark-to-the-current-year → self-review; per-feature contracts with **testable, evidenced exit
criteria**; provider/adapter for every external; **security in the build** (fail-closed; OWASP LLM
Top 10 for AI); resilience + perf/cost budgets; honest docs that match reality; **measure before
fixing**; generic-not-domain-specific. It also encodes lessons learned the hard way — dead config,
swallowed errors, "tests pass but it's dead in the live path", unit/scale mismatches, multi-tenant
leaks, false doc claims.

## How the principle-gate works (the hybrid)

Quality isn't a checklist bolted on at the end — it's **coordinated** so the principles are actually
*verified*, not just intended:

1. **Principles are inherent** — they live once in `PRINCIPLES.md`. Each skill *names* the subset for
   its phase and *applies* it in its guided steps. (No duplicated rule text.)
2. **Each skill's gate is small** — "is this phase's `PRODUCT.md` section complete?" — never a giant
   engineering checklist (keeps skills lean and newcomer-friendly).
3. **The gate verifies, it doesn't rubber-stamp** — at completion, a skill walks its named principles
   and **confirms each is actually implemented, with evidence**, by composing the existing checkers
   (`/security-review`, `/code-review`, `/verify`, `/run`, `/doc-audit`). Only claimed → **STOP**.
4. **Deterministic checks run automatically** — secret-scan, lint, tests, dependency-vuln are wired
   into **pre-commit + CI** by `/foundation`, so they run on every commit/PR *even if you forget*.
5. **On demand** — `/dev-check` verifies the phase before Testing; `/drift-check` checks drift anytime.

Two kinds of "definition of done", kept distinct: the **feature's** DoD (what `/build` and `/plan`
make *you* define for your product) vs the **skill's** gate (is this phase's output complete).

## Adding / changing a skill

1. Edit (or add) `commands/<name>.md` — single-purpose, well under ~250 lines.
2. Update its row in `VISION.md` (purpose + exit criteria), `manifest.json`, and `evals/evals.json`.
   `VISION.md` is the completeness contract — *nothing is missing if every row has a skill and every
   skill matches its row.*
3. `./install.sh`, then commit + push. Run `/drift-check` on this repo to confirm skills match `VISION.md`.

MIT licensed.
