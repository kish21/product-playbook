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
  - [ ] **CI is in place and mirrors the prod bootstrap** (builds/migrates/tests from the real schema), green — a must, not optional.
  - [ ] CI runs **both secret-scan AND dependency-vulnerability scan**; CI creates throwaway creds at runtime (no literal secret in the repo).
  - [ ] Long/first-use work (model download, slow external calls) **does not block the async event loop** (offload/async).

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
3. **Structured logging** (no prints) **+ a tracing / error-reporter hook** (even a stub behind an adapter) — wire base infra behind the adapters from `/architect` (DB/LLM/queue), even if stubbed.
4. **The auto-layer:** dev tooling lint + format + **pre-commit** running **secret-scan + dependency-vuln scan**; this is what enforces the deterministic checks on every commit so the later skills don't rely on memory.
5. **CI** that installs, bootstraps from the real schema/migrations, runs lint/secret-scan/dep-scan/tests, **builds + runs in the container prod uses**, and **blocks merge on red** — green. CI creates throwaway creds at runtime (no secret in repo).

## Step 3 — Write back to `PRODUCT.md`
Fill `#Foundation`: runs end-to-end? · config-flow verified (how) · guards · secret-scan + dep-vuln · pre-commit + CI (auto-layer) · container · observability hook.

## Step 3b — Principle-gate: verify it RUNS and the guards are real (evidence)
Walk this phase's principles and prove each — don't assume:
- runs end-to-end → actually start it / hit the health path (compose `/run`); evidence.
- config flows / no dead config → read a value back at runtime; evidence.
- **pre-commit + CI actually run** the deterministic checks (lint/format/secret-scan + dependency-vuln/tests) and **block on red** → show a green run; this is the auto-layer the later skills rely on.
- fail-loud/fail-closed guard → trigger it with a missing secret and confirm it refuses to boot.
**If any is "should" not "shown", STOP and make it real.** Record HOW in `#Foundation`.

## Step 4 — Handoff
"Skeleton runs and CI is green. Next run **`/contracts`** to define typed models/schemas/migrations
BEFORE business logic — so the data shape is right from the start."
