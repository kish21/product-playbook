---
name: foundation
description: >
  Phase 2 (Development), step 3 of product-playbook. Build the walking skeleton that actually RUNS —
  dependencies, config loader, structured logging, base infra wiring (DB/LLM/queue), dev tooling
  (lint/format + the commit-hook runner #Architecture chose), secret-scan, and a CI that mirrors the
  prod bootstrap. Use after
  /structure, or run /foundation "set up the skeleton", "get it running", "wire up CI". Writes the
  Foundation section of PRODUCT.md. Run /contracts next.
---

# `/foundation` — Phase 2 · Development ③ · run as an **engineer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per PRINCIPLES.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **no-hardcoding (config/.env)**, **verify config actually
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
  - [ ] **Placeholders are rejected BY NAME at boot, not by length or format** — the loader knows the `CHANGE_ME__<VAR>__CHANGE_ME` values `/structure` wrote to `.env.example` and refuses to start on any of them, naming the variable and how to generate a real one. A length/format check is not this: a 48-char placeholder passes `min(32)` and boots the app on a public signing key. **A test proves it** (copy `.env.example` → `.env` unedited → boot fails), and under production (`NODE_ENV`/`APP_ENV`) there is **no override** — see `PRINCIPLES.md` §Production safeguards.
  - [ ] **An isolated, disposable test datastore is provisioned** — its own variable (`TEST_DATABASE_URL` or the chosen datastore's equivalent) in `.env.example`, created and torn down by the task runner. Per-test transaction rollback is an acceptable alternative; **sharing the development datastore is not.** The test bootstrap **fails closed**: handed the dev or production target, it refuses to run, names both, and exits non-zero — verified by pointing it at the dev one on purpose.
  - [ ] **The test runner loads config the same way the app does** (same loader, same precedence) — not whatever happened to be exported into the shell. A runner with its own config path is dead config on the test side, and it is how a suite ends up pointed at the wrong datastore.
  - [ ] Structured logging (no stray prints); dev tooling wired — lint/format + the **commit-hook runner and secret scanner `#Architecture` chose** (not a tool this skill picks).
  - [ ] **CI is in place and mirrors the prod bootstrap** (builds/migrates/tests from the real schema), green — a must, not optional.
  - [ ] CI runs **both secret-scan AND dependency-vulnerability scan** (e.g. `pip-audit`/`npm audit`), **fail-closed on a known CVE**; CI creates throwaway creds at runtime (no literal secret in the repo).
  - [ ] An **automated dependency-update bot** is wired (`.github/dependabot.yml` or Renovate). Add it **on day one while deps are clean** — a strict CVE gate bolted on late faces a months-deep backlog (the bot patches one-at-a-time so the backlog never forms). **Group tightly-coupled packages** (react+react-dom, eslint+eslint-config-next) so they bump in one PR — bumping them independently drifts versions apart and breaks the build.
  - [ ] Long/first-use work (model download, slow external calls) **does not block the async event loop** (offload/async).

## Step 0 — Context + prior-gate check
- Read `#Architecture/#Structure`. If `#Structure` is empty, warn and offer `/structure` first (allow override).
- Brownfield: detect what already exists (CI, config, logging) and fill only the gaps.

## Step 1 — Apply principles (this phase)
- **No-hardcoding:** every endpoint/secret/threshold from config/`.env`. **Prove it flows** — read a value back at runtime; a setting silently overridden upstream is "dead config" and a real bug.
- **Fail-loud/fail-closed:** a startup guard refuses to boot if a required secret is unset, equals a default constant, **or is still one of `.env.example`'s placeholders**. Match the placeholder **by value, by name** — never infer "looks unset" from length or shape; `make setup` copying the example to `.env` is the normal path, so this guard is the only thing between a fresh clone and a public signing key.
- **CI mirrors prod:** bootstrap the same way prod does (real schema/migrations), least-privilege tokens.

## Step 2 — Build the skeleton
1. **Dependency manifest: this phase owns its CONTENTS AND PROVABILITY** (`PRINCIPLES.md` §Seam) — `/structure` created the file and its dev/prod split; pin the versions, **actually install**, write the tool config files those scripts reference (`biome.json`, `tsconfig.json`, the test-runner config), and get the first real run to pass. Then a runnable entrypoint with a **health/hello path** (the walking skeleton).
2. **Config loader** reading `.env`/config; add a **startup guard** (fail-loud on misconfig, fail-closed on security) that holds the placeholder values as a **known-bad list** and rejects them by name, with a message saying how to generate a real value (`openssl rand -base64 32`). Keep the list next to the loader so adding a secret to `.env.example` and forgetting the guard is visible in one file.
3. **The test datastore + its guard**, alongside the app's own: provision a separate disposable target, wire the runner to the app's config loader, and write the **refuse-to-run guard** before any test exists. Order matters — a suite written first is a suite that has already run once against whatever was configured.
4. **Structured logging** (no prints) **+ a tracing / error-reporter hook** (even a stub behind an adapter) — wire base infra behind the adapters from `/architect` (DB/LLM/queue), even if stubbed.
5. **The auto-layer:** dev tooling lint + format + **the commit-hook runner `#Architecture` recorded** running **secret-scan + dependency-vuln scan**; this is what enforces the deterministic checks on every commit so the later skills don't rely on memory. Wire an **automated dependency-update bot** (`.github/dependabot.yml`/Renovate) here too — adding the CVE gate on day one keeps it green from the start; bolting it on later means inheriting a backlog of CVEs that piled up unscanned.
6. **CI** that installs, bootstraps from the real schema/migrations, runs lint/secret-scan/dep-scan/tests, **builds + runs in the container prod uses**, and **blocks merge on red** — green. CI creates throwaway creds at runtime (no secret in repo).

## Step 3 — Write back to `PRODUCT.md`
Fill `#Foundation`: runs end-to-end? · config-flow verified (how) · guards (**incl. the placeholder rejection and the test-datastore refuse-to-run guard, each with its test**) · isolated test datastore + how the runner loads config · secret-scan + dep-vuln · hook runner + CI (auto-layer) · container · observability hook.

## Step 3b — Principle-gate: verify it RUNS and the guards are real (evidence)
Walk this phase's principles and prove each — don't assume:
- runs end-to-end → actually start it / hit the health path (compose `/run`); evidence.
- config flows / no dead config → read a value back at runtime; evidence.
- **the commit hooks + CI actually run** the deterministic checks (lint/format/secret-scan + dependency-vuln/tests) and **block on red** → show a green run; this is the auto-layer the later skills rely on.
- fail-loud/fail-closed guard → trigger it with a missing secret and confirm it refuses to boot.
- **test-isolation guard → point it at the dev datastore on purpose** and show it refusing to run, naming both targets. Then confirm the suite's teardown cannot reach the dev data. This one is verified by *attempting the destruction*, because the failure mode is silent until the data is gone.
- **placeholder guard → replay the real failure:** copy `.env.example` to `.env` **unedited**, start the app, and show it **refusing to boot** with a readable message. If it starts, the guard is decorative and the product ships a public secret.
**If any is "should" not "shown", STOP and make it real.** Record HOW in `#Foundation`.

**Close the loop (`PRINCIPLES.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and end with a suggested one-line commit message in the repo's convention.

## Step 3c — Contradiction check (before the gate closes)
Per `PRINCIPLES.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Architecture` (adapters · tool choices · CI approach) and `#Structure`'s map — a skeleton wired to a datastore, hook runner or provider other than the recorded one. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Skeleton runs and CI is green. Next run **`/contracts`** to define typed models/schemas/migrations
BEFORE business logic — so the data shape is right from the start."
