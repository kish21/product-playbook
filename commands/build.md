---
name: build
description: >
  Phase 2 (Development), step 5 of product-playbook — the per-feature build loop. Build ONE feature at
  a time: declare a definition-of-done that INCLUDES security, reuse before writing, code it, run and
  verify the LIVE path, review the diff, and write the feature doc. Use to implement features, or run
  /build "build feature X", "implement", "add the feature". Appends to PRODUCT.md#Build log + writes
  docs/features/<feature>.md. Composes /run, /verify, /code-review, /doc-create. Run /dev-check when
  all core-scope features are done.
---

# `/build` — Phase 2 · Development ⑤ · run as an **engineer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per PRINCIPLES.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **per-feature contract (security in the DoD)**,
> **secure-by-construction**, **prompts→`prompts/` YAML**, **doc↔code reconciled**, **measure before
> fixing**, **no swallowed errors**, **reuse-before-write**, **trace callers (live-path)**,
> **generic-not-domain-specific**.

## Contract
- **Purpose:** implement one feature to a verified, secure, documented definition-of-done.
- **Reads:** `PRODUCT.md#Scope`, `#Plan`, `#Contracts`, `#Structure` — **plus `DESIGN.md` + `#Design` for any feature with a user-facing screen** (UI products).
- **Writes:** a row in `PRODUCT.md#Build log` + `docs/features/<feature>.md`.
- **Exit criteria (per feature):**
  - [ ] A written **definition-of-done that includes security** (input validation, authz/tenant-isolation; for AI: prompt-injection defence).
  - [ ] Reused existing helpers where possible (no reinvented utilities).
  - [ ] Code **runs and the LIVE path is verified** (not just an isolated unit) — traced to its real callers.
  - [ ] Diff self-reviewed (`/code-review`); no swallowed errors; prompts in `prompts/` YAML, not inline.
  - [ ] **`docs/features/<feature>.md` written and matches the code** (what · contract · exit criteria · how verified · code links).
  - [ ] **No secret in any code file** (secrets→`.env`; tests use fake placeholder keys).
  - [ ] **Single-responsibility kept** — a file growing large/multi-concern is split into modules (don't let god-files form); long/blocking work stays off the async event loop.
  - [ ] **(UI products) The feature's screen(s) are built to `DESIGN.md`** — layout from its page inventory (§5), look from its tokens, parts via `/new-component` — and **`/frontend-audit` is clean** (0 errors) before done.

## Step 0 — Context + prior-gate check
- Read `#Scope/#Plan/#Contracts`. **Confirm the feature is IN scope** — if it's in OUT-OF-SCOPE, stop and
  flag it (this is where creep enters). If `#Contracts` is empty, warn and offer `/contracts` first.

## Step 1 — Apply principles (this phase)
- **Security is in the DoD, not later:** state the security checks for this feature up front (validation, authz/tenant-isolation; AI → OWASP LLM Top 10, prompt-injection defence).
- **Reuse before you write; measure before you fix** (reproduce a bug before patching — a scary number may be a display artifact). **No swallowed errors** (route failures; retry only transient). **Prompts → `prompts/` YAML**.

## Step 2 — The build loop (per feature)
1. **Declare the DoD** (incl. security + the exit criteria above). 
2. **Reuse scan:** find existing helpers/contracts to use; don't reinvent.
3. **Code** against the typed contracts; keep it modular and generic (no domain special-casing in shared infra).
   - **If the feature has a user-facing screen (UI products):** build it to **`DESIGN.md`** — take the layout from its **page inventory (§5)** and the look from its **tokens**, and **reuse `/new-component`** for buttons/inputs/cards/etc. (never hand-roll, Law 15). Then run **`/frontend-audit`** and fix every ERROR. *(No `DESIGN.md` yet? the product has UI but skipped `/design-system` — run that first.)*
4. **Run + verify the LIVE path** — compose `/run` and `/verify` to exercise the path the product actually runs, then **trace your change to its real callers** (green unit tests ≠ wired in).
   - **If the live path is a browser journey (Playwright/E2E), avoid the classic false-pass/false-fail traps** (each cost a real debugging round on a shipped project): anchor waits on a **unique interactive element** (`getByRole('button', {name: …})`), never `text=` — Playwright `text=` is a case-insensitive substring match and will fire on incidental copy (a heading wait matched a sidebar step label); **keep the browser open until every in-flight request resolves** — closing the page mid-request cancels the local server's HTTP handler and can strand server-side state mid-write; and when the app has long (>1 min) backend calls, assert on the **persisted state after completion** (DB row/API read-back), not just what's painted, so the pass is evidence not theater. **Also verify the server you're actually hitting**: dev servers silently bind a FALLBACK port when the default is taken (Vite 5173→5175 when another instance runs) — read the bound port from the server's own startup output and align the test BASE URL *and* any CORS allowlist to it; and when an **env-gated UI element** (a button behind a feature-flag env var) comes back "missing", first confirm the instance under test was launched with those env vars — the element being absent on a *different* running instance is the classic false-fail.
5. **Review the diff** — compose `/code-review`; fix findings (watch for "works in tests, dead in the real path").
6. **Document** — write/update `docs/features/<feature>.md` (compose `/doc-create`); reconcile it with the code.

## Step 3 — Write back to `PRODUCT.md`
Append a `#Build log` row: feature · DoD-incl-security met? · **how verified** · link to the feature doc.

## Step 3b — Principle-gate: verify each principle is ACTUALLY implemented (not just claimed)
This is where principles and the gate coordinate. Walk **this phase's load-bearing principles
(Step 1)** and confirm each is real in the code, **with evidence** — composing the existing checkers,
not eyeballing:
- security-in-DoD → compose **`/security-review`** on the feature; evidence = it passed.
- no secret in code / no-hardcoding → secret-scan clean; evidence.
- live-path-works → **`/verify`** + **`/run`** exercised the real path; evidence (green unit tests ≠ wired in).
- reuse · no-swallowed-errors · single-responsibility → confirmed in the **`/code-review`** of the diff.
- (UI features) built-to-the-design → **`/frontend-audit`** clean against `DESIGN.md`; evidence = scorecard with 0 errors.

**If any named principle is only claimed, not evidenced, STOP — the feature is not done.** Record the
*how-verified* per principle in `#Build log` (evidence, not "done"). (Deterministic checks —
secret-scan, lint, tests — also run automatically via pre-commit + CI from `/foundation`; this gate is
the judgment layer on top.)

## Step 4 — Handoff
"Feature done, verified, and documented. Build the next core-scope feature with `/build`, or when the
core scope is complete run **`/dev-check`** — the checkpoint that verifies everything before testing."
