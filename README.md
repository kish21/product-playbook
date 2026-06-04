# product-playbook

**A guided path from idea → shipped that bakes in the discipline most teams learn the hard way.**

## Why this exists

I built a real product. It worked — and then I watched it slowly go wrong in the ways products
quietly do:

- features crept in that nobody actually needed;
- a config setting silently did **nothing** (it was overridden upstream — "dead config");
- the tests were green while the feature was **dead in the real path** in production;
- a doc claimed a security guarantee that **wasn't actually true**;
- a number on a 0–1 scale got read as 0–10, and everything looked broken for a day.

None of these were dumb mistakes — they're the normal entropy of building. Each one cost time and
taught a lesson. **`product-playbook` is those lessons turned into a guided, step-by-step path** — so
you (or a teammate, or someone who's never shipped before) gets senior-level discipline *by default*,
and doesn't have to collect the same scars first.

Two ideas make that work, and they're the two files you'll see in this repo:

- **`PRINCIPLES.md` — the rulebook.** Every lesson, written down once. Each skill references it and
  *enforces* the part that matters for its phase, so the discipline can't drift skill-to-skill.
- **`PRODUCT.md` — the living spine.** One file at the root of *your* project that every phase reads
  and appends to. It's how the product's story and decisions stay in one place and carry from vision
  all the way to shipped — without it, the steps would be disconnected one-offs.

It's **guided and step-by-step — not a one-shot generator.** `/vision` does the vision phase only; you
move one phase at a time, each asking a few questions and ending with a check, so nothing drifts.

## Start here

**Run `/playbook`** — the one command to remember. It reads how far you've got, tells you the next
phase in plain language, runs it, and **checks with you before moving on** (it never auto-builds or
skips a gate). Prefer to drive yourself? Run the phases in order — each one tells you the next.

```
START → /playbook   (guides you through ↓, one phase at a time)

1 PRODUCT      /vision → /scope → /plan
2 DEVELOPMENT  /architect → /structure → /foundation → /contracts → /build → /dev-check
3 TESTING      /test
4 EVALUATION   /eval
5 SHIP         /ship
6 LEARN        /learn
ANYTIME        /drift-check
```

## The skills

| Group | Skill | What it does | Output it produces | Use it when |
|---|---|---|---|---|
| **Start** | `/playbook` | Guides you through the phases, one at a time, pausing at each gate | *(routes only — writes nothing itself)* | You're new / unsure what's next |
| **Product** | `/vision` | Sharpen the idea: who · problem · value · metric · risk, vs the market | `PRODUCT.md` → **Vision** | Starting a brand-new product |
| **Product** | `/scope` | Pick the **one** core feature; list Deferred (+triggers) & Non-goals | `PRODUCT.md` → **Scope** | After vision / scope is creeping |
| **Product** | `/plan` | Core-first milestones, each a testable "done" + concern coverage | `PRODUCT.md` → **Plan** | After scope / you need a roadmap |
| **Development** | `/architect` | Choose stack + tools; ADRs (patterns/anti-patterns); resilience; budget | `PRODUCT.md` → **Architecture** | Before writing any code |
| **Development** | `/structure` | Clean folders (explained) + root scaffolding; `app/prompts/` for AI | folder tree + `STRUCTURE.md` + **Structure** | The first thing you build |
| **Development** | `/foundation` | Skeleton that **runs**: config · logging · pre-commit + CI auto-layer | running skeleton + CI + **Foundation** | After structure |
| **Development** | `/contracts` | Typed models/schemas/migrations; versioning · PII · keys | models/migrations + **Contracts** | Before business logic |
| **Development** | `/build` | Build **one** feature: security-in-DoD · reuse · verify live path · doc | code + `docs/features/*` + **Build log** | Implementing each feature |
| **Development** | `/dev-check` | Verify each feature's exit criteria + security DoD, with evidence | `PRODUCT.md` → **Dev-complete** | Before moving to testing |
| **Testing** | `/test` | Unit + integration + regression + adversarial + golden set; live path | tests + `PRODUCT.md` → **Tests** | After dev-check |
| **Evaluation** | `/eval` | Measure quality vs a baseline; cost; honest confidence score | `PRODUCT.md` → **Evaluation** | "Is it actually good?" |
| **Ship** | `/ship` | Review + security + reconcile docs + rollout safety + PR + handoff | PR + `PRODUCT.md` → **Ship log** | A subtask is done |
| **Learn** | `/learn` | Metric (instrumented) · user signal · decide next / **kill** | `PRODUCT.md` → **Learnings** | After a release lands |
| **Anytime** | `/drift-check` | Detect scope / vision / code↔docs drift | report + `PRODUCT.md` → **Drift log** | Whenever you suspect creep |

## What's in this repo (and why each file matters)

| File | Why it exists |
|---|---|
| `PRINCIPLES.md` | The **single rulebook** — the lessons above, written once; every skill enforces the part for its phase (so quality can't drift). |
| `templates/PRODUCT.md` | The template for the **living spine** each project gets. Every phase reads it + appends its section, so the whole product (vision → learnings) lives in one file that travels with the repo. |
| `commands/` | The **15 skills** (the phases) — one `.md` each, with YAML frontmatter. |
| `VISION.md` | The toolkit's own **completeness contract** — what every skill must cover. For maintainers, so nothing is missed. |
| `manifest.json` · `install.sh` · `.claude-plugin/` | Packaging + the three install modes (below). |
| `evals/evals.json` | A behaviour check per skill (catches drift when a skill changes). |

*Produced in **your** project when you run the skills:* `PRODUCT.md` (the spine), `STRUCTURE.md` (what
each folder is for), `docs/features/*` (one doc per feature) — all committed with your code.

## Install — three ways, you choose

| Way | Command | Who gets it | Command names |
|---|---|---|---|
| **Global (per machine)** | `./install.sh` | you, in every project on your machine | `/vision` |
| **Project-level (committed)** | `./install.sh --project /path/to/project` | anyone who clones *that* repo | `/vision` |
| **Plugin (one-command + updates)** | `/plugin marketplace add kish21/product-playbook` → `/plugin install product-playbook@product-playbook` | anyone, via Claude Code | `/product-playbook:vision` (namespaced) |

```bash
# Global (local clone)
git clone https://github.com/kish21/product-playbook ~/product-playbook
cd ~/product-playbook && ./install.sh

# Project-level — commit the project's .claude/ so teammates get it on clone
cd ~/product-playbook && ./install.sh --project /path/to/your/project
```

*Pick:* your own toolkit everywhere → **global**; one project's team on clone → **project-level**;
widest distribution + updates → **plugin**.

## Under the hood (for the curious)

<details>
<summary>How the discipline is actually enforced (not just intended)</summary>

- **Principles live once** in `PRINCIPLES.md`; each skill *names* the subset for its phase and applies
  it — no duplicated rule text to drift.
- **Each skill's gate is small** — it only asks "is this phase's `PRODUCT.md` section complete?" — so
  skills stay lean and newcomer-friendly.
- **The gate verifies, it doesn't rubber-stamp.** At completion a skill walks its named principles and
  confirms each is *actually implemented, with evidence*, by composing existing Claude Code skills
  (`/code-review`, `/security-review`, `/verify`, `/run`, `/doc-audit`). Only claimed → it **stops**.
- **Deterministic checks run automatically** — secret-scan, lint, tests, dependency-vuln are wired into
  **pre-commit + CI** by `/foundation`, so they run on every commit/PR even if you forget. The skill
  gate is the judgment layer on top.
- **Sequential but standalone** — follow the chain, or jump into any single skill on an existing
  project (it bootstraps context from `PRODUCT.md` or the codebase).

What's baked in (from `PRINCIPLES.md`): architect → verify → no-hardcoding → benchmark-to-the-current-
year → self-review; per-feature contracts with testable, evidenced exit criteria; provider/adapter for
every external; security in the build (fail-closed; OWASP LLM Top 10 for AI); resilience + perf/cost
budgets; honest docs; measure before fixing; generic-not-domain-specific.

</details>

## Contributing

1. Edit/add `commands/<name>.md` (single-purpose, well under ~250 lines).
2. Update its row in `VISION.md`, `manifest.json`, and `evals/evals.json`.
3. `./install.sh`, commit + push, then run `/drift-check` on this repo to confirm skills still match `VISION.md`.

MIT licensed.
