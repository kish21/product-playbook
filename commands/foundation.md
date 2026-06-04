---
name: foundation
description: >
  Phase 2 (Development), step 3 of product-builder. Build the walking skeleton that actually RUNS —
  dependencies, config loader, structured logging, base infra wiring (DB/LLM/queue), dev tooling
  (lint/format/pre-commit), secret-scan, and a CI that mirrors the prod bootstrap. Use after
  /structure, or run /foundation "set up the skeleton", "get it running", "wire up CI". Writes the
  Foundation section of PRODUCT.md. Run /contracts next.
---

# `/foundation` — Phase 2 · Development ③ · run as an **engineer**

> Part of **product-builder**. Reads + updates the shared spine `PRODUCT.md`.
> Apply `PRINCIPLES.md` (bundled at `~/.claude/product-builder/PRINCIPLES.md`) — load-bearing: **no-hardcoding (config/.env)**, **verify config actually
> flows (no dead config)**, **fail-loud on misconfig / fail-closed on security**, **structured
> logging (no prints)**, **CI mirrors prod**, **fast feedback early**.

## Contract
- **Purpose:** a thin end-to-end skeleton that runs, with config/logging/infra/tooling/CI in place.
- **Reads:** `PRODUCT.md#Architecture`, `#Structure`.
- **Writes:** `PRODUCT.md#Foundation` — runs end-to-end? · config-flow verified · guards/secret-scan/CI.
- **Exit criteria:**
  - [ ] App **runs end-to-end** with nothing in it (a health check / hello path works).
  - [ ] Config loads from config/`.env`; **the value actually flows** (verify — no dead/overridden config).
  - [ ] **Fail-loud on misconfig, fail-closed on security**: boot refuses on missing/known-constant secrets.
  - [ ] Structured logging (no stray prints); dev tooling (lint/format/pre-commit) + **secret-scan** wired.
  - [ ] **CI mirrors the prod bootstrap** (builds/migrates/tests from the real schema), green.

## Step 0 — Context + prior-gate check
- Read `#Architecture/#Structure`. If `#Structure` is empty, warn and offer `/structure` first (allow override).
- Brownfield: detect what already exists (CI, config, logging) and fill only the gaps.

## Step 1 — Apply principles (this phase)
- **No-hardcoding:** every endpoint/secret/threshold from config/`.env`. **Prove it flows** — read a value back at runtime; a setting silently overridden upstream is "dead config" and a real bug.
- **Fail-loud/fail-closed:** a startup guard refuses to boot if a required secret is unset or equals a default constant (no silent insecure boot).
- **CI mirrors prod:** bootstrap the same way prod does (real schema/migrations), least-privilege tokens.

## Step 2 — Build the skeleton
1. Dependency manifest + a runnable entrypoint with a **health/hello path** (the walking skeleton).
2. **Config loader** reading `.env`/config; add a **startup guard** (fail-loud on misconfig, fail-closed on security).
3. **Structured logging** (no prints); wire base infra behind the adapters from `/architect` (DB/LLM/queue) — even if stubbed.
4. Dev tooling: lint + format + pre-commit; **secret-scan** (e.g. gitleaks). 
5. **CI** that installs, bootstraps from the real schema/migrations, and runs the skeleton + tooling — green.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Foundation`: runs end-to-end? · config-flow verified (note how) · guards + secret-scan + CI status.

## Step 3b — Self-verify (completeness gate)
Check the boxes. **If you didn't actually run it, or didn't verify a config value flows, STOP and do
so** — "should run" is not "runs". Record HOW you verified.

## Step 4 — Handoff
"Skeleton runs and CI is green. Next run **`/contracts`** to define typed models/schemas/migrations
BEFORE business logic — so the data shape is right from the start."
