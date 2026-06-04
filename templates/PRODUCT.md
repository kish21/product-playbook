<!--
PRODUCT.md — the living spine of this product.

This single file is the shared memory of the product-builder skills. Each skill
READS the sections it depends on and APPENDS/UPDATES its own. Read it top-to-bottom
to understand the whole product: what it is, why, what's built, and what's next.

Rules:
- A section that is empty/missing = that phase's exit criteria are not yet met.
- Keep entries short and honest. Record HOW something was verified, not just "done".
- Anything explicitly OUT OF SCOPE stays out until the recorded trigger fires.
- Every skill, when it writes back, UPDATES the header line below — bump `Stage:` to its phase
  and set `Last updated:` to today.
-->

# PRODUCT — <product name>

_Last updated: <date> · Stage: <phase> · AI product? <yes/no>_

## Vision            <!-- /vision -->
- **Who it's for:**
- **Problem (why now):**
- **Value proposition:**
- **2026 market / competitor read (verified, not from memory):**
- **North-star success metric (how we'll know it works):**
- **Job-to-be-done (when <situation>, I want to <motivation>, so I can <outcome>):**
- **Riskiest assumption this depends on:**
- **Business model (free / paid / internal):**

## Scope             <!-- /scope -->
- **THE core feature (the one thing):**
- **In scope (now):**
- **Deferred (out for now + the trigger that would bring it in):**
- **Non-goals (deliberately never building):**

## Plan              <!-- /plan -->
- **Phases / milestones (core first):**
- **Timeline:**
- **Exit criteria per milestone:**
- **Concern-area coverage (security · ai · observability · DX · testing · infra · docs · product → now/next/later/N-A + trigger):**

## Architecture      <!-- /architect -->
- **Stack + tools (and why, 2026 OSS-first):**
- **Key decisions / ADRs (patterns applied · anti-patterns avoided):**
- **Externals behind provider/adapter interfaces (+ resilience strategy each):**
- **Resilience · perf/cost budget · migrations approach:**
- **(AI) prompt-versioning · eval harness · tracing:**

## Structure         <!-- /structure --> (see STRUCTURE.md for the full folder map)
- **Folder → purpose map (summary):**
- **Prompts location (AI):** `app/prompts/` (backend sub-package; YAML, never inline)

## Foundation        <!-- /foundation -->
- **Runs end-to-end (walking skeleton):**
- **Config flows verified (no dead config):**
- **Fail-loud/fail-closed guards · secret-scan + dependency-vuln scan · CI mirrors prod:**
- **pre-commit + CI auto-run (lint/format/secret-scan/tests) · runs in its container · async-safe:**
- **Observability wired (tracing / error-reporter, even a stub):**

## Contracts         <!-- /contracts -->
- **Typed models / schemas / migrations:**
- **Boundary units/scale agreed:**
- **Contract versioning / back-compat approach:**
- **PII/sensitive fields classified · tenant-owner key · idempotency/natural key:**

## Build log         <!-- /build --> (one entry per feature; see docs/features/*)
| Feature | DoD (incl. security) met? | How verified | Doc |
|---|---|---|---|

## Dev-complete      <!-- /dev-check -->
- [ ] Every core-scope feature built & runs
- [ ] Exit criteria + security DoD verified (with evidence)
- [ ] No hardcoding · prompts externalized · contracts typed · builds green
- [ ] Scope re-check — nothing crept in

## Tests             <!-- /test -->
- **Unit / integration / regression coverage (critical path accounted for):**
- **Adversarial/security (prompt-injection, authz) cases:**
- **Live-path verified (not just isolated units):**
- **Golden/eval dataset location · tests deterministic · run in CI (red blocks merge):**

## Evaluation        <!-- /eval -->
- **Is it good? (measured vs a recorded baseline; regression fails):**
- **Metrics + confidence score:**
- **Cost-per-run · (AI) scoring-bias:**
- **Operational failures (separated from quality):**

## Ship log          <!-- /ship -->
| Date | What shipped | Review + /security-review | Docs reconciled | CHANGELOG | Rollback / flag | PR |
|---|---|---|---|---|---|---|

## Learnings         <!-- /learn -->
- **Success metric + result (instrumented, not guessed):**
- **User/usage signal incorporated:**
- **Retro (what worked / what to change):**
- **Decided next — build / iterate / KILL (from evidence):**
- **Observability + cost watch in place:**

## Drift log         <!-- /drift-check (run anytime) -->
| Date | Drift found (scope/vision/plan/docs) | Recommendation (cut / re-scope+trigger / fix) |
|---|---|---|
