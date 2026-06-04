# product-builder

A phased, principle-driven **product-building skill set** for Claude Code. It walks anyone —
a newcomer (technical or not) *or* an experienced builder dropping into one phase — through the
**full product lifecycle**, with hard-won engineering principles **baked into each phase** so good
results are the default. It is **anti-scope-creep by design**.

> Sibling to [`product-toolkit`](https://github.com/kish21/product-toolkit). `product-toolkit` is a
> grab-bag of individual dev/quality skills; **`product-builder` is the opinionated end-to-end
> *journey*.**

## How it works (three ideas)

1. **One shared file is the memory.** Every skill reads + appends to **`PRODUCT.md`** (the spine) at
   the root of *your* project — so the build step knows the vision, the test step knows the features,
   and a newcomer can read the whole story top-to-bottom. (Not Claude memory: a file is shareable,
   versioned, and travels with the repo.)
2. **Principles are baked in, once.** Every skill references **`PRINCIPLES.md`** (single source) and
   enforces the subset that matters for its phase — so even a non-techie gets senior-level discipline.
3. **Sequential but standalone.** Run the phases in order, or jump into any skill — each one
   bootstraps context from `PRODUCT.md` or the existing codebase. And skills **compose existing
   Claude Code skills** (`/code-review`, `/security-review`, `/verify`, `/run`, `/doc-create`,
   `/doc-audit`, `/loop`, `github-pr-flow`) rather than reinventing them.

Each skill ends by **self-verifying its exit criteria** — it won't hand off a half-done phase.

## The journey

```
1 PRODUCT      /vision  →  /scope  →  /plan
2 DEVELOPMENT  /architect → /structure → /foundation → /contracts → /build → /dev-check
3 TESTING      /test
4 EVALUATION   /eval
5 SHIP         /ship
6 LEARN        /learn
ANYTIME        /drift-check   ← are we still building the vision, or creeping?
```

| Phase | Skill | What it does |
|---|---|---|
| 1 Product | `/vision` | Vision · customer · problem · value — benchmarked to the current-year market |
| 1 Product | `/scope` | Lock the **ONE** core feature + an explicit **OUT-OF-SCOPE** list (anti-creep) |
| 1 Product | `/plan` | Core-first phases + timeline + a **testable exit criterion per milestone** |
| 2 Dev | `/architect` | Decide stack + tools + key decisions (2026 OSS-first); ADRs |
| 2 Dev | `/structure` | Clean folder layout + **what each folder is for**; `prompts/` YAML for AI |
| 2 Dev | `/foundation` | The **walking skeleton that runs**: config · logging · infra · tooling · CI |
| 2 Dev | `/contracts` | **Typed** models/schemas/migrations *before* logic; agree units across boundaries |
| 2 Dev | `/build` | Per-feature loop: **security-in-DoD** · reuse-first · **verify the live path** · feature doc |
| 2 Dev | `/dev-check` | **Checkpoint tester** — verify exit criteria + security DoD before testing |
| 3 Test | `/test` | Unit · integration · regression · **adversarial/security** (injection/authz); live-path |
| 4 Eval | `/eval` | Is it **good**? measure-first · separate failures from quality · confidence score |
| 5 Ship | `/ship` | Deep review + security review + **reconcile docs** + PR + handoff |
| 6 Learn | `/learn` | Success metric · retro · decide next **from evidence** |
| anytime | `/drift-check` | Scope-creep / vision / code↔docs drift check |

## What's baked in (the principles)

The discipline lives in [`PRINCIPLES.md`](PRINCIPLES.md): architect → verify → no-hardcoding →
benchmark-to-the-current-year → self-review; per-feature contracts with **testable, evidenced exit
criteria**; provider/adapter for every external; **security in the build** (fail-closed; OWASP LLM
Top 10 for AI); honest docs that match reality; **measure before fixing**; generic-not-domain-specific.
It also encodes lessons learned the hard way — dead config, swallowed errors, "tests pass but it's
dead in the live path", unit/scale mismatches, multi-tenant leaks, false doc claims.

## Install

```bash
# One-liner
curl -fsSL https://raw.githubusercontent.com/kish21/product-builder/master/install.sh | bash

# Or local clone
git clone https://github.com/kish21/product-builder ~/product-builder
cd ~/product-builder && ./install.sh

# Sync after updates
cd ~/product-builder && git pull && ./install.sh
```

This copies the 14 skills **plus the companion files they read** (`PRINCIPLES.md`, `VISION.md`,
`templates/PRODUCT.md`) into `~/.claude/commands/`.

## Adding / changing a skill

1. Edit (or add) `commands/<name>.md` — keep it single-purpose and well under ~250 lines.
2. Update its row in `VISION.md` (purpose + exit criteria) and `manifest.json`, and add an
   `evals/evals.json` check. `VISION.md` is the completeness contract — *nothing we envisioned is
   missing if every row has a skill and every skill matches its row.*
3. `./install.sh`, then `git add -A && git commit && git push`.
4. Run `/drift-check` on this repo to confirm each skill still matches `VISION.md`.

MIT licensed.
