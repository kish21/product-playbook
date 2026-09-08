---
name: structure
description: >
  Phase 2 (Development), step 2 of product-playbook — the FIRST thing you build. Set up a clean,
  industry-standard folder structure (backend / frontend / full-stack) and explain what each folder is
  for and why, plus the root scaffolding every project needs (ignore rules, .env.example, a secret-scan
  config, a commit-hook runner, a task runner) using the TOOLS #Architecture chose, and a prompts/ YAML
  folder for AI. Use when starting to code, or run /structure
  "set up the project", "folder structure", "where does this go". Writes STRUCTURE.md + the Structure
  section of PRODUCT.md. Run /foundation next.
---

# `/structure` — Phase 2 · Development ② · run as a **senior engineer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per PRINCIPLES.md §Spine resolution); writes `STRUCTURE.md`.
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing:
> **modular/single-responsibility**, **layered sub-packages**, **intention-revealing naming**,
> **prompts externalized to `prompts/` YAML**, **no-hardcoding (secrets→`.env`, knobs→config)**,
> **no secret in any code file**.

> This skill exists because bad/ad-hoc folder structure is the #1 thing newcomers get wrong (god-files,
> "where does this go?"). The goal is not just to create folders — it is to **teach what each folder is
> for** so the layout stays clean as the product grows. Adapt names to the chosen stack, but always lay
> the same solid base.

## Contract
- **Purpose:** a clean, explained, stack-appropriate layout + the root scaffolding files + (AI) `prompts/`.
- **Reads:** `PRODUCT.md#Architecture` — the **stack** (decides the layout) *and* the **Dev tooling** line (decides which tool fills each scaffolding slot), `#Vision` (AI product?).
- **Writes:** `STRUCTURE.md` (folder→purpose map) + `PRODUCT.md#Structure` (summary).
- **Exit criteria:**
  - [ ] A folder tree matching the chosen shape (**backend / frontend / full-stack**), layered, no god-files.
  - [ ] `STRUCTURE.md` explains **what each folder is for and why**, in plain language.
  - [ ] **`STRUCTURE.md`'s map and the real tree agree BOTH ways:** every folder drawn in the map exists on disk (create it — even with just an `__init__.py`/`.gitkeep`), and every folder on disk is in the map. A drawn-but-missing folder is silent doc↔code drift.
  - [ ] Root scaffolding present — each named as a **capability**, filled by the tool `#Architecture` recorded (the playbook never dictates the tool): `README.md` · ignore rules · `.env.example` · **secret-scan config** · **commit-hook runner** · **task runner** · **dependency manifest** (dev/prod split) · `SECURITY.md` (responsible-disclosure policy) · `CHANGELOG.md` (Keep a Changelog format, seeded with `[Unreleased]`).
  - [ ] **Every scaffolded tool matches `#Architecture`'s Dev tooling line.** Scaffolding `.pre-commit-config.yaml` into a Node repo whose ADR chose lefthook makes the recorded trail describe a tool the repo does not use — and forces a Node contributor to install Python tooling to commit. If `#Architecture` names no tool for a slot, **recommend one that fits the detected stack, say why, and record it back** — never default to the Python one on a Node repo.
  - [ ] **The config-layering files are actually scaffolded** (not just an empty `config/`): a **typed loader** in the project's own language (`config/loader.py` · `config/loader.ts` — follow the stack, not this example) + `config/platform.yaml` (engine knobs) + `config/product.yaml` (product knobs) reading `.env` — the no-hardcoding engine.
  - [ ] Ignore rules cover `.env` **and its variants/backups** (`.env.bak`, `*.env.local`); only `.env.example` is committed. **No secret in any code file.**
  - [ ] **`.env.example` holds only unmistakable placeholders** — `CHANGE_ME__<VAR>__CHANGE_ME`, never a realistic-looking string that happens to be long enough (`replace-me-with-32-plus-random-characters` is 48 chars and **passes** `min(32)`, so a copied `.env` boots the app on a signing key that is public in git). Each placeholder carries a one-line comment on how to generate the real value. `/foundation` then **rejects these by name** at boot — see `PRINCIPLES.md` §Production safeguards.
  - [ ] For AI products: a **`prompts/` YAML folder as a backend sub-package** (`app/prompts/` when there's an `app/` package; root `prompts/` only if there's no backend package) — prompts never inline in code.

## Step 0 — Context + prior-gate check
- Read `#Architecture` and `#Vision` (AI?). Take **two** things from `#Architecture`, not one: the **stack** (which decides the folder shape) and the **Dev tooling** line (hook runner · secret scanner · task runner · formatter/linter · dependency manifest) — **which decides every root scaffolding file you are about to write**. Reading only the stack is how a recorded tool choice gets silently overridden one phase later.
- If `#Architecture` is empty, warn and offer `/architect` first (allow override). Running standalone, detect the stack from the repo and pick tooling that fits it — then record the choice so the next phase inherits it.
- Brownfield: read the existing tree; propose a clean target layout + a migration note — don't blindly move files.

## Step 1 — Apply principles (this phase)
- **One folder = one concern; dependencies point inward** (api → service/domain → data). No god-files.
- **No-hardcoding:** secrets go to `.env`; tunable knobs to layered config; **never a key/secret in a code file**.
- **Prompts are config (AI):** `app/prompts/*.yaml` (backend sub-package), versioned, never inline.
- Reuse `/new-project`'s sub-package conventions where they fit; don't reinvent.

## Step 2 — Lay the structure (pick the shape, then adapt names to the stack)

**Backend** (the proven base — adapt names to the stack):
```
app/
├── api/         # HTTP routes, one file per concern — thin, no business logic
├── domain/      # business/domain logic (the "what")
├── db/          # data access / persistence (repositories, queries)
├── providers/   # adapters for every external (LLM, DB, vendor SDK) — swappable via config
├── infra/       # cross-cutting: logging, audit, rate-limit, cost, circuit-breaker
├── auth/        # authn / authz
├── schemas/     # typed models / DTOs (contracts that cross boundaries)
├── validators/  # input validation
├── config/      # loader + layered config — SEE BELOW — reads .env
├── jobs/        # background / scheduled tasks
└── main.py      # entrypoint
# AI/agentic ONLY (when PRODUCT.md says AI), as app/ sub-packages: agents/ · pipeline/ (orchestration) · app/prompts/ (versioned YAML) · retrieval/
```
**`config/` layered pattern (the no-hardcoding engine) — ACTUALLY CREATE THESE FILES, don't leave
`config/` empty:** `loader.py` (typed loader that reads the YAML + `.env`) + `platform.yaml`
(engine/technical knobs) + `product.yaml` (product/business knobs, change without code) + a root
`.env.example` (secret *names* only). This is *how* you keep secrets and tunables out of code — it is a
deliverable of this skill, not just a description.

**Frontend** (Next.js App Router shown — adapt to the framework):
```
frontend/
├── app/          # routes: one folder per route (+ layouts, pages)
├── components/   # reusable UI, grouped: ui/ (primitives) · features/ · layout/ · auth/
├── lib/          # client utils: api client · hooks · theme · types · constants
├── public/       # static assets / brand
└── middleware.ts # edge middleware (auth, redirects)
```
**Full-stack** = backend `app/` and `frontend/` side by side.

**Root (every shape) — the *capability*, filled by the tool `#Architecture` chose:** `README.md` ·
ignore rules · `.env.example` (unmistakable `CHANGE_ME__<VAR>__CHANGE_ME` placeholders only) ·
`CONTRIBUTING.md` · **secret-scan config** (e.g. `.gitleaks.toml`: `useDefault=true`, allowlist only
documented dev fakes + `.env.example`) · **commit-hook runner** running lint + format + secret-scan
(`.pre-commit-config.yaml` for Python · `lefthook.yml` · `.husky/` for Node — whichever the ADR names)
· `SECURITY.md` (how to report a vuln —
enables GitHub's "Report a vulnerability"; cheap on day one, annoying to retrofit) · `CHANGELOG.md`
(Keep a Changelog format, start with an `[Unreleased]` section) · **task runner** (`Makefile` · npm
scripts · `just` — whichever the ADR names) · dependency manifest with **dev/prod split** · `tests/` · `docs/` (will hold PRODUCT.md, STRUCTURE.md,
docs/features/*) · `tools/`|`scripts/`. **When relevant:** `Dockerfile`+`docker-compose.yml`+
`.dockerignore` · CI workflow · `.github/dependabot.yml` (or Renovate) · migrations config ·
observability config · `benchmark/`|`evals/` (AI).

**`Makefile` generic targets** a newcomer can just run: `dev` · `frontend` (full-stack) · `test` ·
`lint` · `check` (lint+test) · and, with a DB, `seed` · `reset`.

## Step 3 — Write back
Write **`STRUCTURE.md`** (one line per folder — *what goes here and why*, plain language). Fill
`PRODUCT.md#Structure` with the summary + the prompts location (AI).

## Step 3b — Self-verify (completeness gate)
Check the boxes. **STOP and fix if:** a folder is unexplained; **a folder drawn in `STRUCTURE.md`
doesn't exist on disk, or a folder on disk is absent from the map** (the map↔tree must match BOTH
directions — a drawn-but-uncreated folder is silent doc↔code drift); ignore rules don't cover `.env*`;
the secret-scan config or the commit-hook runner is missing; **`.env.example` holds any value that would
survive a plausible validity check** (it must be an unmistakable placeholder — see the criterion above);
a secret sits in a code file; or an AI product has no `prompts/` folder. An unexplained layout decays
into god-files; a leaked `.env` is a real incident.

## Step 3c — Contradiction check (before the gate closes)
Per `PRINCIPLES.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Architecture` — **especially its Dev tooling line**: every scaffolding file you wrote must be the tool recorded there (this check exists because a run scaffolded `.pre-commit-config.yaml` into a Node repo whose ADR chose lefthook, and nothing noticed). On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Clean structure + root scaffolding in place and explained in `STRUCTURE.md`.
- **If this product has a user-facing UI** (there's a `frontend/`): run **`/design-system`** next — agree
  design principles + a confirmed sample page + a concrete `DESIGN.md` (shadcn tokens) *before* building
  screens, so the UI doesn't end up generic/AI-looking. Then `/foundation`.
- **Backend/API/CLI only** (no UI): skip straight to **`/foundation`** to make a walking skeleton that
  actually runs (config, logging, infra, CI, secret-scan live)."
