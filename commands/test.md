---
name: test
description: >
  Phase 3 (Testing) of product-playbook. Write the test suite — unit (isolated/mocked), integration
  (real contracts), regression, and adversarial/security cases (prompt-injection & jailbreak for AI,
  authz/tenant-isolation) — and verify the path the product ACTUALLY runs, not just functions in
  isolation. Use after /dev-check, or run /test "write tests", "test this", "does it actually work".
  Writes the Tests section of PRODUCT.md. Composes /run. Run /eval next.
---

# `/test` — Phase 3 · Testing · run as a **tester**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **independent test plan**, **unit=isolated/mocked,
> integration=real contracts**, **testable-by-construction**, **tests passing ≠ it works (verify the
> live path)**, **OWASP LLM Top 10 cases for AI**, **multi-tenant isolation tests**.

## Contract
- **Purpose:** prove the product works on the path it actually runs, including adversarial inputs.
- **Reads:** `PRODUCT.md#Scope`, `#Contracts`, `#Build log`, `#Dev-complete`.
- **Writes:** `PRODUCT.md#Tests` — coverage (unit/integration/regression) · security cases · live-path verified.
- **Gate type:** `verification` — pass/fail on repo evidence; no preference involved. Batchable, and **stops on red** - a failing check ends the batch there. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes `#Tests` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Exit criteria:**
  - [ ] **Unit** tests for core logic (isolated via injection/mocks). → `Unit / integration / regression coverage`
  - [ ] **Integration** tests across real contracts/boundaries (not all mocked). → `Unit / integration / regression coverage`
  - [ ] **The suite can name its isolated target, and the bootstrap enforces it.** Real boundaries plus a teardown hook is a destructive combination: an integration suite pointed at the development datastore will truncate it. The target is the disposable one `/foundation` provisioned (or per-test transaction rollback), and the bootstrap **refuses to run** against the dev or production target — a suite that cannot name its isolated target **does not pass this gate**. → `Isolated test datastore`
  - [ ] **Live-path check:** the path the product actually runs is exercised end-to-end (not just isolated units). → `Live-path verified`
  - [ ] **Adversarial/security** cases: authz/tenant-isolation; for AI, prompt-injection & jailbreak (OWASP LLM Top 10). → `Adversarial/security`
  - [ ] **Real-user-environment** cases (products with a browser UI) — the environments a clean headless run
    never reproduces: **third-party DOM injection** (password managers, autofill, translation and
    accessibility extensions mutating the DOM before/during hydration) · **locale, timezone and date
    formatting** · **reduced motion, forced colours, zoom, small viewports** · **throttled network and a cold
    cache**. At minimum, one executable check that **first interactive paint survives injected DOM on an
    auth/form surface**, run against a profile that is not pristine. → `Real-user-environment`
  - [ ] A regression case for any bug fixed. → `Unit / integration / regression coverage`
  - [ ] A **golden / eval dataset** for quality-critical or AI behaviour (known inputs → expected outputs), so quality is measurable and regressions are caught. → `Golden/eval dataset location`
  - [ ] Tests use **fake placeholder keys**, never real secrets. → `Isolated test datastore`

## Step 0 — Context + prior-gate check
- Read `#Dev-complete`. If the dev checkpoint hasn't passed, warn ("development isn't verified complete")
  but allow override (you can still add tests for an existing product).
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then write `Override <date>: <reason> — bypassed <gate>` at the top of `#Tests` before continuing. Advancing on unmet criteria is the more consequential of warn-vs-override, so it is the one that leaves a trace: without it a later reader cannot tell a gate that held from a gate that was waved through.
- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** if the section is already filled, **show what would change and ask before replacing it** — never a silent overwrite — and leave a reversed decision in place with a dated `superseded <date>: <why>` line. A first run over an empty section is unchanged.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** write ONE dated line at the top of `#Tests` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **Independent test plan:** unit = isolated/mocked; integration = real contracts with neighbours. If a unit can't be tested in isolation, the seams are wrong — fix them.
- **Tests passing ≠ it works:** add at least one test on the **live path** the product runs (compose `/run`, then assert on the observable result), and trace that the feature is actually wired in (the "green tests, dead feature" trap).
- **Isolation before coverage:** confirm what the suite is pointed at *before* writing a destructive hook, and confirm the runner loads config through the app's own loader. This is not tidiness — on a real run, an `afterAll` truncate against a shared URL left the developer stranded at `/login` with no accounts.
- **A clean headless browser is not a user's browser.** "The path the product actually runs" has quietly
  meant "the path our runner runs". On a real run every test was green while the login page threw for real
  users: a password-manager extension injected DOM nodes into the form before the framework hydrated. The
  suite ran headless, clean profile, zero extensions — it could not have seen it. **Test the environment, not
  just the code.**
- **Security is testable:** add authz/tenant-isolation cases; for AI, real injection/jailbreak inputs.

## Step 2 — Build the suite
1. **Unit** tests for each core-feature unit (inject deps; mock externals).
2. **Integration** tests across real boundaries/contracts from `/contracts` — **against the isolated test datastore**, verified by reading back the target the bootstrap resolved, not by trusting the variable's name.
3. **Live-path** test: exercise the real end-to-end path (`/run`), asserting on what the user would actually see; confirm the feature is reachable in the running product.
4. **Adversarial/security:** cross-tenant AND **within-tenant** access attempts (one user must not see another user's resources inside the same org — tenant-id/RLS only stops cross-tenant). Assert the per-resource access check on **every resource-returning endpoint individually, including streaming ones** (SSE/WebSocket/`StreamingResponse` handlers routinely skip the guard their REST siblings call). For AI, prompt-injection/jailbreak prompts that must be refused/neutralised.
5. **Real-user-environment** (browser UI): drive the auth/form surfaces with **injected third-party DOM** and
   assert first interactive paint survives; then vary locale/timezone, reduced motion and forced colours, a
   small viewport, and a throttled cold-cache load.
   **On absorbing third-party injection:** where a framework offers a hydration-mismatch escape hatch, it is
   **scoped and justified** — applied to the specific element known to receive third-party attributes, with a
   comment naming why. **Never a blanket default across a component library:** mismatches also come from real
   bugs (clock/random values, locale drift, server-client branch divergence), and suppressing them wholesale
   silences a correctness signal in a toolkit whose principles are *fail-loud* and *no swallowed errors*. The
   capability wanted is **"third-party DOM injection must not break first paint"**; how a given framework
   absorbs that is the framework's business.
6. **Regression:** lock in any fixed bug with a test.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Tests`: coverage (unit/integration/regression) · security cases · note the live-path verification.

## Step 3b — Principle-gate: prove the suite is real (evidence)
Confirm with evidence: the suite **runs in CI and a red run blocks merge** (not just locally); there's at
least one **integration + live-path** test (compose `/run`), not only isolated units; tests are
**deterministic** (seeded, no time/network races); **the suite is provably pointed at the isolated datastore** (print the resolved target; point it at the dev one and show it refusing to run); an AI product has injection/jailbreak cases; a
**golden/eval dataset** exists **and something actually executes it** — if nothing runs it, gate its
structure and say so, never describe it as proof (`LESSONS.md` §Lessons baked in). **If only isolated units exist, or the suite isn't a CI gate, STOP and
add them** — that's exactly the gap that ships broken-but-green code.

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and **offer to commit the change** (`MECHANISMS.md` §Commit the work — check the repo exists, name the branch, offer the message, push only if a remote exists and the user says so). Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal. **Close in plain language** (`MECHANISMS.md` §Plain-language close): two or three sentences of *what just happened* with no playbook dialect, then a numbered *what YOU do next* — the user's own actions, dated where they are time-bound, or "Nothing — you're done".

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Contracts` and `#Architecture` — a suite that asserts a shape the contracts don't declare, or **points a real-boundary test at the datastore `#Foundation` recorded for development**. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Suite covers units, integration, the live path, and adversarial cases. Next run **`/eval`** to judge
whether it's actually *good*, measured — not just whether it runs."
