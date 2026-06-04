---
name: test
description: >
  Phase 3 (Testing) of product-playbook. Write the test suite — unit (isolated/mocked), integration
  (real contracts), regression, and adversarial/security cases (prompt-injection & jailbreak for AI,
  authz/tenant-isolation) — and verify the path the product ACTUALLY runs, not just functions in
  isolation. Use after /dev-check, or run /test "write tests", "test this", "does it actually work".
  Writes the Tests section of PRODUCT.md. Composes /verify and /run. Run /eval next.
---

# `/test` — Phase 3 · Testing · run as a **tester**

> Part of **product-playbook**. Reads + updates the shared spine `PRODUCT.md`.
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **independent test plan**, **unit=isolated/mocked,
> integration=real contracts**, **testable-by-construction**, **tests passing ≠ it works (verify the
> live path)**, **OWASP LLM Top 10 cases for AI**, **multi-tenant isolation tests**.

## Contract
- **Purpose:** prove the product works on the path it actually runs, including adversarial inputs.
- **Reads:** `PRODUCT.md#Scope`, `#Contracts`, `#Build log`, `#Dev-complete`.
- **Writes:** `PRODUCT.md#Tests` — coverage (unit/integration/regression) · security cases · live-path verified.
- **Exit criteria:**
  - [ ] **Unit** tests for core logic (isolated via injection/mocks).
  - [ ] **Integration** tests across real contracts/boundaries (not all mocked).
  - [ ] **Live-path check:** the path the product actually runs is exercised end-to-end (not just isolated units).
  - [ ] **Adversarial/security** cases: authz/tenant-isolation; for AI, prompt-injection & jailbreak (OWASP LLM Top 10).
  - [ ] A regression case for any bug fixed.
  - [ ] A **golden / eval dataset** for quality-critical or AI behaviour (known inputs → expected outputs), so quality is measurable and regressions are caught.
  - [ ] Tests use **fake placeholder keys**, never real secrets.

## Step 0 — Context + prior-gate check
- Read `#Dev-complete`. If the dev checkpoint hasn't passed, warn ("development isn't verified complete")
  but allow override (you can still add tests for an existing product).

## Step 1 — Apply principles (this phase)
- **Independent test plan:** unit = isolated/mocked; integration = real contracts with neighbours. If a unit can't be tested in isolation, the seams are wrong — fix them.
- **Tests passing ≠ it works:** add at least one test on the **live path** the product runs (compose `/run`+`/verify`), and trace that the feature is actually wired in (the "green tests, dead feature" trap).
- **Security is testable:** add authz/tenant-isolation cases; for AI, real injection/jailbreak inputs.

## Step 2 — Build the suite
1. **Unit** tests for each core-feature unit (inject deps; mock externals).
2. **Integration** tests across real boundaries/contracts from `/contracts`.
3. **Live-path** test: exercise the real end-to-end path (`/run`+`/verify`); confirm the feature is reachable in the running product.
4. **Adversarial/security:** cross-tenant access attempts; for AI, prompt-injection/jailbreak prompts that must be refused/neutralised.
5. **Regression:** lock in any fixed bug with a test.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Tests`: coverage (unit/integration/regression) · security cases · note the live-path verification.

## Step 3b — Principle-gate: prove the suite is real (evidence)
Confirm with evidence: the suite **runs in CI and a red run blocks merge** (not just locally); there's at
least one **integration + live-path** test (compose `/verify`+`/run`), not only isolated units; tests are
**deterministic** (seeded, no time/network races); an AI product has injection/jailbreak cases; a
**golden/eval dataset** exists. **If only isolated units exist, or the suite isn't a CI gate, STOP and
add them** — that's exactly the gap that ships broken-but-green code.

## Step 4 — Handoff
"Suite covers units, integration, the live path, and adversarial cases. Next run **`/eval`** to judge
whether it's actually *good*, measured — not just whether it runs."
