<!--
PRODUCT.md — the living spine of this product.

This single file is the shared memory of the product-playbook skills. Each skill
READS the sections it depends on and APPENDS/UPDATES its own. Read it top-to-bottom
to understand the whole product: what it is, why, what's built, and what's next.

Rules:
- A section that is empty/missing = that phase's exit criteria are not yet met.
- A section whose only content is a dated `_Not run <date>: <what was missing> — run <phase> first._`
  line is STILL empty: that phase was attempted and correctly declined. One line, replaced on the next
  attempt, scaffold untouched (PRINCIPLES.md §Declined runs). An `Override <date>:` line is different —
  it is a deliberate skip, and it DOES count as filled.
- Keep entries short and honest. Record HOW something was verified, not just "done".
- Anything explicitly OUT OF SCOPE stays out until the recorded trigger fires.
- Every skill, when it writes back, UPDATES the header line below — bump `Stage:` to its phase
  and set `Last updated:` to today.
-->

# PRODUCT — <product name>

_Last updated: <date> · Stage: <phase> · AI product? <yes/no>_
_Playbook: <phase order followed — or a dated override line if the canonical order was deliberately departed from>_

## Vision            <!-- /vision -->
- **Who it's for:**
- **Problem (why now):**
- **Value proposition:**
- **2026 market / competitor read (verified, not from memory):**
- **North star — target + date (e.g. "400 accounts with 3+ subscriptions by 2027-03-31"):**
- **North star — 2–3 input metrics (the weekly-moving numbers that drive it):**
- **North star — 1 guardrail (what must NOT get worse while chasing it):**
- **North star — instrumentation (how it gets measured; "nothing records this yet" is a finding):**
- **Job-to-be-done (when <situation>, I want to <motivation>, so I can <outcome>):**
- **Riskiest assumption this depends on:**
- **Business model (free / paid / internal):**

## Validation        <!-- /validate --> (test the riskiest assumption BEFORE code; append a dated entry per run)
- **Assumption under test (falsifiable: <user> will <behaviour> because <reason>):**
- **Experiment (type · who it reaches · time box · due date):**
- **Pass/fail threshold (written BEFORE the result):**
- **Measured result (number / quoted evidence · date · raw notes in docs/validation/):**
- **Verdict (proceed / pivot / kill) + one-line reason:**
- **Override (only if skipped: date · reason · "assumption untested" · checked against #Vision):**
  _An override marks the fields above `— not run (override <date>)`; it never deletes them._

## Scope             <!-- /scope -->
- **THE core feature (the one thing):**
- **In scope (now):**
- **Deferred (out for now + the trigger that would bring it in):**
- **Non-goals (deliberately never building):**
- **Table stakes (each: in-scope now / Deferred + trigger / N-A + reason — none may be blank):**
  - password reset · email verification · account deletion + data export · empty/loading/error states ·
    privacy policy + terms · accessibility baseline · a way to report a problem

## Plan              <!-- /plan -->
- **Phases / milestones (core first):**
- **Timeline:**
- **Exit criteria per milestone:**
- **Four-risks row per milestone (value · usability · feasibility · viability — which this milestone retires and how you'll know; cite evidence for one already retired):**
- **Usability checkpoint before going public (which milestone, and its exit criterion):**
- **Concern-area coverage (security · ai · observability · DX · testing · infra · docs · product → now/next/later/N-A + trigger):**

## Architecture      <!-- /architect -->
- **Stack + tools (and why, 2026 OSS-first):**
- **Data custody (local/self-hosted · managed-serverless · embedded) + why (privacy/cost/portability/lock-in):**
- **Runtime target (container-anywhere · PaaS · VPS · user's machine) — decides what `/structure` scaffolds:**
- **Identity custody (self-hosted auth · vendor auth + RLS) — or N/A:**
  _Mark any of the three "default taken, not user-chosen" if it was decided without the user._
- **Dev tooling (hook runner · secret scanner · task runner · formatter/linter · dependency manifest — `/structure` scaffolds exactly these):**
- **Key decisions / ADRs (patterns applied · anti-patterns avoided):**
- **Externals behind provider/adapter interfaces (+ resilience strategy each):**
- **Resilience · perf/cost budget · migrations approach:**
- **(AI) prompt-versioning · eval harness · tracing:**

## Structure         <!-- /structure --> (see STRUCTURE.md for the full folder map)
- **Folder → purpose map (summary):**
- **Prompts location (AI):** `app/prompts/` (backend sub-package; YAML, never inline)

## Design             <!-- /design-system --> (UI products only; see DESIGN.md for the full system)
- **Has user-facing UI?** <yes/no — if no, this phase is skipped intentionally>
- **Design principles (4–6, derived from vision):**
- **Archetype (aesthetic family + why it fits):**
- **Foundations summary (font pairing · base body size + type scale · one accent + palette · density · depth · motion):**
- **Tokens:** shadcn/ui-compatible CSS variables (OKLCH), WCAG-AA verified — see `DESIGN.md`
- **Approved sample page (path):** · **DESIGN.md (path):**

## Foundation        <!-- /foundation -->
- **Runs end-to-end (walking skeleton):**
- **Config flows verified (no dead config):**
- **Fail-loud/fail-closed guards (placeholder rejection · test-datastore refusal) · secret-scan + dependency-vuln scan · CI mirrors prod:**
- **Isolated test datastore provisioned (variable + teardown) · test runner uses the app's config loader:**
- **Usable end-to-end (a seeded account can log in) · seed is idempotent + prod-refusing · dev credentials location:**
- **Commit hooks + CI auto-run (lint/format/secret-scan/tests) · runs in its container · async-safe:**
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
<!-- Evidence format (the ONE form - docs/state-model.md §2f). Append to any criterion you can re-run:
     - [x] Authentication works - `evidence: pnpm test:e2e -> 18 passed - tests/e2e/auth.spec.ts - 2026-09-10`
     command -> result - artefact - date. A criterion with no evidence line is honest and is reported
     UNVERIFIED by /drift-check; a line that names no command or no date fails CI. Never invent a second
     format. -->
- [ ] Every core-scope feature built & runs
- [ ] Exit criteria + security DoD verified (with **re-runnable** evidence: `command -> result - artefact - date`)
- [ ] No hardcoding · prompts externalized · contracts typed · builds green
- [ ] Scope re-check — nothing crept in

## Tests             <!-- /test -->
- **Isolated test datastore (the target the suite runs against) · bootstrap refuses dev/prod:**
- **Unit / integration / regression coverage (critical path accounted for):**
- **Adversarial/security (prompt-injection, authz) cases:**
- **Real-user-environment (DOM injection · locale/timezone · reduced motion/forced colours/zoom · degraded network):**
- **Live-path verified (not just isolated units):**
- **Golden/eval dataset location · tests deterministic · run in CI (red blocks merge):**

## Evaluation        <!-- /eval -->
- **Is it good? (measured vs a recorded baseline; regression fails):**
- **Metrics + confidence score:**
- **Cost-per-run · (AI) scoring-bias:**
- **Operational failures (separated from quality):**

## Ship log          <!-- /ship -->
| Date | What shipped | Review + /security-review | Skipped phases (none = full chain ran) | Docs reconciled | CHANGELOG | Rollback / flag | PR |
|---|---|---|---|---|---|---|---|

## Learnings         <!-- /learn -->
- **Success metric + result (instrumented, not guessed):**
- **User/usage signal incorporated:**
- **Retro (what worked / what to change):**
- **Decided next — build / iterate / KILL (from evidence):**
- **Observability + cost watch in place:**

## Drift log         <!-- /drift-check (run anytime) -->
| Date | Drift found (scope/vision/plan/docs) | Recommendation (cut / re-scope+trigger / fix) |
|---|---|---|
