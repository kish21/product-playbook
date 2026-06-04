---
name: build
description: >
  Phase 2 (Development), step 5 of product-builder — the per-feature build loop. Build ONE feature at
  a time: declare a definition-of-done that INCLUDES security, reuse before writing, code it, run and
  verify the LIVE path, review the diff, and write the feature doc. Use to implement features, or run
  /build "build feature X", "implement", "add the feature". Appends to PRODUCT.md#Build log + writes
  docs/features/<feature>.md. Composes /run, /verify, /code-review, /doc-create. Run /dev-check when
  all core-scope features are done.
---

# `/build` — Phase 2 · Development ⑤ · run as an **engineer**

> Part of **product-builder**. Reads + updates the shared spine `PRODUCT.md`.
> Apply `PRINCIPLES.md` — load-bearing: **per-feature contract (security in the DoD)**,
> **secure-by-construction**, **prompts→`prompts/` YAML**, **doc↔code reconciled**, **measure before
> fixing**, **no swallowed errors**, **reuse-before-write**, **trace callers (live-path)**,
> **generic-not-domain-specific**.

## Contract
- **Purpose:** implement one feature to a verified, secure, documented definition-of-done.
- **Reads:** `PRODUCT.md#Scope`, `#Plan`, `#Contracts`, `#Structure`.
- **Writes:** a row in `PRODUCT.md#Build log` + `docs/features/<feature>.md`.
- **Exit criteria (per feature):**
  - [ ] A written **definition-of-done that includes security** (input validation, authz/tenant-isolation; for AI: prompt-injection defence).
  - [ ] Reused existing helpers where possible (no reinvented utilities).
  - [ ] Code **runs and the LIVE path is verified** (not just an isolated unit) — traced to its real callers.
  - [ ] Diff self-reviewed (`/code-review`); no swallowed errors; prompts in `prompts/` YAML, not inline.
  - [ ] **`docs/features/<feature>.md` written and matches the code** (what · contract · exit criteria · how verified · code links).

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
4. **Run + verify the LIVE path** — compose `/run` and `/verify` to exercise the path the product actually runs, then **trace your change to its real callers** (green unit tests ≠ wired in).
5. **Review the diff** — compose `/code-review`; fix findings (watch for "works in tests, dead in the real path").
6. **Document** — write/update `docs/features/<feature>.md` (compose `/doc-create`); reconcile it with the code.

## Step 3 — Write back to `PRODUCT.md`
Append a `#Build log` row: feature · DoD-incl-security met? · **how verified** · link to the feature doc.

## Step 3b — Self-verify (completeness gate)
Check the per-feature boxes. **If you didn't verify the live path, or the feature doc doesn't match
the code, STOP** — don't log it as done. Record HOW it was verified (evidence, not "done").

## Step 4 — Handoff
"Feature done, verified, and documented. Build the next core-scope feature with `/build`, or when the
core scope is complete run **`/dev-check`** — the checkpoint that verifies everything before testing."
