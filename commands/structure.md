---
name: structure
description: >
  Phase 2 (Development), step 2 of product-playbook — the FIRST thing you build. Set up a clean,
  industry-standard folder structure (backend / frontend / full-stack) and explain what each folder is
  for and why, plus the root scaffolding every project needs (.gitignore, .env.example, .gitleaks.toml,
  pre-commit, Makefile) and a prompts/ YAML folder for AI. Use when starting to code, or run /structure
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
- **Reads:** `PRODUCT.md#Architecture` (stack decides the layout), `#Vision` (AI product?).
- **Writes:** `STRUCTURE.md` (folder→purpose map) + `PRODUCT.md#Structure` (summary).
- **Exit criteria:**
  - [ ] A folder tree matching the chosen shape (**backend / frontend / full-stack**), layered, no god-files.
  - [ ] `STRUCTURE.md` explains **what each folder is for and why**, in plain language.
  - [ ] Root scaffolding present: `README.md` · `.gitignore` · `.env.example` · `.gitleaks.toml` · `.pre-commit-config.yaml` · task runner (`Makefile`/npm scripts) · dependency manifest (dev/prod split) · `SECURITY.md` (responsible-disclosure policy) · `CHANGELOG.md` (Keep a Changelog format, seeded with `[Unreleased]`).
  - [ ] **The config-layering files are actually scaffolded** (not just an empty `config/`): `config/loader.py` (typed) + `config/platform.yaml` (engine knobs) + `config/product.yaml` (product knobs) reading `.env` — the no-hardcoding engine.
  - [ ] `.gitignore` ignores `.env` **and its variants/backups** (`.env.bak`, `*.env.local`); only `.env.example` is committed. **No secret in any code file.**
  - [ ] For AI products: a **`prompts/` YAML folder as a backend sub-package** (`app/prompts/` when there's an `app/` package; root `prompts/` only if there's no backend package) — prompts never inline in code.

## Step 0 — Context + prior-gate check
- Read `#Architecture` (stack) and `#Vision` (AI?). If `#Architecture` is empty, warn and offer `/architect` first (allow override).
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

**Root (every shape):** `README.md` · `.gitignore` · `.env.example` · `CONTRIBUTING.md` ·
`.gitleaks.toml` (secret-scan: `useDefault=true`, allowlist only documented dev fakes + `.env.example`)
· `.pre-commit-config.yaml` (lint + format + secret-scan) · `SECURITY.md` (how to report a vuln —
enables GitHub's "Report a vulnerability"; cheap on day one, annoying to retrofit) · `CHANGELOG.md`
(Keep a Changelog format, start with an `[Unreleased]` section) · `Makefile` (or npm scripts) ·
dependency manifest with **dev/prod split** · `tests/` · `docs/` (will hold PRODUCT.md, STRUCTURE.md,
docs/features/*) · `tools/`|`scripts/`. **When relevant:** `Dockerfile`+`docker-compose.yml`+
`.dockerignore` · CI workflow · `.github/dependabot.yml` (or Renovate) · migrations config ·
observability config · `benchmark/`|`evals/` (AI).

**`Makefile` generic targets** a newcomer can just run: `dev` · `frontend` (full-stack) · `test` ·
`lint` · `check` (lint+test) · and, with a DB, `seed` · `reset`.

## Step 3 — Write back
Write **`STRUCTURE.md`** (one line per folder — *what goes here and why*, plain language). Fill
`PRODUCT.md#Structure` with the summary + the prompts location (AI).

## Step 3b — Self-verify (completeness gate)
Check the boxes. **STOP and fix if:** a folder is unexplained; `.gitignore` doesn't cover `.env*`;
`.gitleaks.toml`/pre-commit secret-scan is missing; a secret sits in a code file; or an AI product has
no `prompts/` folder. An unexplained layout decays into god-files; a leaked `.env` is a real incident.

## Step 4 — Handoff
"Clean structure + root scaffolding in place and explained in `STRUCTURE.md`. Next run **`/foundation`**
to make a walking skeleton that actually runs (config, logging, infra, CI, secret-scan live)."
