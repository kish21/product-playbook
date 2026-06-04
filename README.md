# product-playbook

**A guided path from idea → shipped that bakes in the discipline most teams learn the hard way.**

## Why this exists

I built a real product. It worked — then I watched it go wrong in the quiet ways products do. None of
these were dumb mistakes; they're the normal entropy of building. **Each scar became a rule** — and
those rules are **[`PRINCIPLES.md`](PRINCIPLES.md): the working rulebook every skill enforces** (and
*verifies with evidence*, not just intends). Don't take the story on faith — here's the scar, and the
exact rule it became:

| The scar (real, on my own build) | The rule it's now → in `PRINCIPLES.md` |
|---|---|
| Features kept creeping in that nobody needed | One core feature + an explicit **OUT-OF-SCOPE** list; `/drift-check` catches creep |
| A config setting silently did **nothing** (overridden upstream) | **Dead config** — prove the value actually *flows* end-to-end |
| Tests were green while the feature was **dead in production** | **Tests passing ≠ it works** — verify the path the product actually runs |
| A doc claimed a security guarantee that **wasn't true** | **Docs must match reality** — reconcile code ↔ docs, or it's a liability |
| We wired the code straight to one vendor's API — swapping it later meant touching half the app | **Wrap every external (LLM, DB, vendor) behind a swap-by-config adapter** |
| One missing filter could let a user see **another customer's data** | **Tenant isolation on every data path** (defense-in-depth, fail-closed) |
| Secrets nearly slipped into source | **No secret in code** — `.env` + secret-scan; tests use fake keys |

`product-playbook` turns those rules into a **guided, step-by-step path** — so you (or a teammate, or
someone who's never shipped) get this discipline *by default*, without collecting the scars first.

**The other file you'll see — `PRODUCT.md` — is the living spine.** One file at the root of *your*
project that every phase reads and appends to, so the product's story and decisions carry from vision
all the way to shipped. Without it the steps would be disconnected one-offs; with it, anyone can read
the whole product top-to-bottom.

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
