---
name: test
description: Write and run unit, integration and security tests.
---

# `/test` — Phase 3 · Testing · run as a **tester**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · LESSONS.md = `${CLAUDE_PLUGIN_ROOT}/references/lessons.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the variable is the folder two levels above this SKILL.md, holding `commands/` and `PRINCIPLES.md` - never another tool's install). If `python` will not start (not found, or a sandbox refuses it): the project's `.venv` Python, else `python3`, else `py -3` - never a hunt; later commands use the start's `Run this copy as` line.
> **The start prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`**, `set` the close's — apply them; never open the whole files (a situational companion only when a rule points into it). Load-bearing: **independent test plan**, **unit=isolated/mocked,
> integration=real contracts**, **testable-by-construction**, **tests passing ≠ it works (verify the
> live path)**, **OWASP LLM Top 10 cases for AI**, **multi-tenant isolation tests**.

## Contract
- **Purpose:** independent coverage of what `/build`'s per-ticket tests missed — the live path, the seams between tickets, adversarial inputs — proven on the path the product actually runs.
- **Reads:** what the start prints (Step 0); more by `status.py section`.
- **Writes:** `PRODUCT.md#Tests` — coverage (unit/integration/regression) · security cases · live-path verified.
- **Gate type:** `verification` — pass/fail on repo evidence; no preference involved. Batchable, and **stops on red** - the chain waits; this run still does every check once. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Tests` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Companion:** `docs/tests.md` — the reasoning, workings and raw notes. `PRODUCT.md#Tests` stays a
  RECORD (summary · decision · evidence · pointer) — no byte cap; reasoning moves, answers stay.
- **Exit criteria:**
  - [ ] **Unit** tests for core logic (isolated via injection/mocks). → `Unit / integration / regression coverage`
  - [ ] **Integration** tests across real contracts/boundaries (not all mocked). → `Unit / integration / regression coverage`
  - [ ] **The suite can name its isolated target, and the bootstrap enforces it.** Real boundaries plus a teardown hook is a destructive combination: an integration suite pointed at the development datastore will truncate it. The target is the disposable one `/foundation` provisioned (or per-test transaction rollback), and the bootstrap **refuses to run** against the dev or production target — a suite that cannot name its isolated target **does not pass this gate**. → `Isolated test datastore`
  - [ ] **Live-path check:** the path the product actually runs is exercised end-to-end (not just isolated units). → `Live-path verified`
  - [ ] **Adversarial/security** cases: authz/tenant-isolation; for AI, prompt-injection & jailbreak (OWASP LLM Top 10). → `Adversarial/security`
  - [ ] **Real-user-environment** cases where the start says they apply (a built form/auth screen in a browser UI) — the environments a clean headless run
    never reproduces: **third-party DOM injection** (password managers, autofill, translation and
    accessibility extensions mutating the DOM before/during hydration) · **locale, timezone and date
    formatting** · **reduced motion, forced colours, zoom, small viewports** · **throttled network and a cold
    cache**. At minimum, one executable check that **first interactive paint survives injected DOM on an
    auth/form surface**, run against a profile that is not pristine. → `Real-user-environment`
  - [ ] A regression case for any bug fixed. → `Unit / integration / regression coverage`
  - [ ] A **defect hunt** per built module: the start's probes, generated data hash-pinned, command-line tools faked. → `Unit / integration / regression coverage`
  - [ ] A **golden / eval dataset** for quality-critical or AI behaviour (known inputs → expected outputs), so quality is measurable and regressions are caught. → `Golden/eval dataset location`
  - [ ] Tests use **fake placeholder keys**, never real secrets. → `Isolated test datastore`
  - [ ] `#Tests` is a **RECORD** — every field is a decision, evidence line or pointer; the reasoning is
    in `docs/tests.md`. Size is reported, never trimmed to. → `Detail:`
  - [ ] **Every companion opened is receipted** — one line per file, quoting a fragment that
    occurs verbatim in it. → `Read (file · date · verbatim quote)`

## Step 0 — Context + prior-gate check
- **First turn, ONE command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase test`** — the facts, this phase's rules and what it must NOT do; never the rule files or `PRODUCT.md` whole. Show its first line.
- **The start prints each built ticket's done-list beside its tests, its security surface, the suite's database, browser cases, CI, the eval dataset, the defect probes, and the commands.**
- **The dev checkpoint not passed** (`#Dev-complete`): follow the start's gate line - an unfinished milestone is one line and the run tests what is built; any other gate is ONE options question (Stop - run /dev-check first (Recommended) · Proceed anyway · Other). **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): Proceed runs `status.py bypass --from test --gate <gate> --reason "/<gate> not passed - the user chose to go on"` before continuing - never a typed reason.
- **Unusual cases - the start prints their rule only when the case is real.** A re-run (a filled section) follows the `RE-RUN` line `next` prints: ONE options question listing what would change, never a silent overwrite; a reversed decision keeps a dated `superseded <date>: <why>` line. The user declines the run: `status.py set test declined --reason "<their words>" --gate <the phase that fills it>` - and change nothing in `PRODUCT.md`.

## Step 1 — Apply principles (this phase)
- **Independent test plan:** judge each criterion by the assertions that test it, never by a file name or a coverage number; write only what is missing. Unit = isolated/mocked; integration = real contracts with neighbours. If a unit can't be tested in isolation, the seams are wrong — fix them.
- **Tests passing ≠ it works:** at least one test on the **live path** the product runs (compose `/run`, then assert on the observable result), and trace that the feature is wired in (the "green tests, dead feature" trap).
- **Isolation before coverage:** confirm what the suite points at *before* a destructive hook, through the app's own config loader; **prove the guard each run** on a fake dev-looking target, never real data.
- **A clean headless browser is not a user's browser** — where the start says browser cases apply, test the environment, not just the code.
- **Security is testable:** authz/tenant-isolation cases; for AI, real injection/jailbreak inputs.

## Step 2 — Build the suite (the gaps only)
1. **Unit** tests for each core-feature unit the start shows uncovered (inject deps; mock externals).
2. **Integration** across real boundaries/contracts from `/contracts` — **against the isolated test datastore**, verified by reading back the target the bootstrap resolved, not by trusting the variable's name.
3. **Live-path** test through the real entry point (the start's live-path command), asserting on what the user would see; confirm the feature is reachable in the running product. An automated, re-runnable test, never a one-off script.
4. **Adversarial/security:** the **built security code the start lists**, tested now even before its feature exists; cross-tenant AND **within-tenant** access attempts (one user must not see another user's resources inside the same org — tenant-id/RLS only stops cross-tenant); the per-resource access check on **every resource-returning endpoint individually, including streaming ones** (SSE/WebSocket/`StreamingResponse`); a missing, empty or model-supplied auth value; for AI, prompt-injection/jailbreak prompts that must be refused. **Outside-service reach:** each file the start lists uses the fake or refuses when the app starts as the project runs it.
5. **Real-user-environment** (only where the start says APPLY): injected third-party DOM on the auth/form surfaces, then locale/timezone, reduced motion, forced colours, a small viewport, a throttled cold-cache load. A hydration-mismatch escape hatch is **scoped and justified** — one element, a comment naming why — **never a blanket default**: mismatches also come from real bugs.
6. **Defect hunt:** the start's probes. **Regression:** lock in each fixed bug. **A test that exposes a real bug stays:** mark it an expected failure naming the issue you file; never fix product code here.
7. While writing, only the start's per-edit command; **the gate once**, after the tests and `docs/tests.md` are written, committed or not.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Tests` once: coverage (unit/integration/regression) · security cases · the live-path verification · the isolation proof · CI (a red run blocks merge, or remote enforcement is missing/unverified and the local gate is the evidence) · the eval dataset (executed, with its result, or "structure only, not executed").

## Step 3b — Principle-gate: prove the suite is real (evidence)
Confirm, citing this run's records (the gate counts on the exact files it checked: never re-run a file it covered): the gate green over the final tree; at least one **integration + live-path** test, not only isolated units; **deterministic** tests (seeded, no time/network races); expiring tokens made inside the test; the isolation proof; an AI product's injection/jailbreak cases; the **golden/eval dataset executed by something** — else gate its structure and say so, never describe it as proof (`LESSONS.md` §Lessons baked in). **If only isolated units exist, add them** — that's exactly the gap that ships broken-but-green code.

**The record test on every field** (`MECHANISMS-ON-DEMAND.md §Section is a record`): reasoning moves into `docs/tests.md`, a tight answer stays whatever it weighs, never trim to a number; one `Read:` line per companion you opened, quoting a fragment verbatim (`MECHANISMS-ON-DEMAND.md §Read receipt`). All receipts: one `status.py quote` call.

**Close the loop (`MECHANISMS.md` §Step 3b):** record it in ONE call — `status.py set test filled --verdict pass|fail` `--section-from <file>` (writes `#Tests` from a scratch file — never an edit tool on `PRODUCT.md`) (`MECHANISMS.md` §Status; it refuses a `#Tests` naming no live path, security or regression cases, or a PASS without the gate green on this code — every gap at once; `--dry-run` lists them) — then the rest of the close it prints, in order: reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), Step 3c, **no save question** — the record call saved (`MECHANISMS.md` §Commit the work; never a separate save question; `--no-commit` only if the user said not to save; push only if the user says so), then **the transition guard** (`MECHANISMS.md` §Step 3b, item 4): cite this run's `evidence:` records — never re-run one for its number — and report a verdict for every exit criterion; `UNVERIFIED` is a normal outcome, silence is not. **Close in plain language** (`MECHANISMS.md` §Plain-language close): four blocks in order, each under its bolded name: **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next** (its last line the `Open a NEW conversation` line `set` printed). **The close is the run's last message** — a composed skill's report is input to it, never the close itself.

## Step 3c — Contradiction check (BEFORE the save call in Step 3b: what it fixes or records goes in that save)
Per `MECHANISMS.md` §Step 3c: `#Contracts` and `#Architecture` — a suite that asserts a shape the contracts don't declare, or **points a real-boundary test at the datastore `#Foundation` recorded for development**. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or a dated `superseded by` line in the earlier section).

## Step 4 — Handoff
"Suite covers units, integration, the live path, and adversarial cases. Next run **`/eval`** to judge
whether it's actually *good*, measured — not just whether it runs."
