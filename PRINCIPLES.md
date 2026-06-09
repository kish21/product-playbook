# PRINCIPLES.md — the working rules every skill enforces

> Single source of truth. Every `product-playbook` skill links here and names the
> subset that is load-bearing for its phase. Do not duplicate these rules inside a
> skill — reference them, so they can never drift.

---

## The 5-step spine (run on every non-trivial task)

1. **Architect first** — think how it *should* be built and where it fits, before writing code.
2. **Verify** — confirm assumptions/root cause against the real code + running system. Never act on a stale note or a guess.
3. **No hardcoding** — every value (weights, thresholds, endpoints, model names, prompts, credentials) lives in **config / `.env` / a prompt file**, never baked into source.
4. **Benchmark to the current year** — ask "is this how leading product companies do it *now*?" and prefer the **best open-source tool** (open source over proprietary unless told otherwise).
5. **Self-review** — run the project's review (`/code-review`, `/security-review` on auth/data) and check quality/perf/tests before calling it done.

## Per-feature contract (agree BEFORE building a feature)

- **Exit criteria** — explicit, *testable* definition of done. Not done until every criterion is met **and verified, with evidence**. No vague "done".
- **Module-interaction map** — which modules/services it touches, the **typed contract in/out** of each boundary, dependencies.
- **Independent test plan** — **unit** (isolated via injection/mocks), **integration** (real contracts with neighbours), plus E2E/regression as needed. If a feature can't be tested independently, fix the seams first.

## Architecture & quality bar

- **Modular / single-responsibility** — one module = one concern; no god-files.
- **Layered & decoupled** — API ↔ service/domain ↔ data; dependencies point *inward*; cross-boundary payloads are **typed contracts**, never raw dict/text.
- **Provider/adapter for every external** — wrap each external (LLM, DB, vendor SDK, queue) behind a **config-selected interface**; never import a vendor SDK in business logic.
- **Intention-revealing naming**; **testable by construction** (inject dependencies; prefer pure functions).
- **Change safely** — DB via **migrations** (never hand-edit schema); **version public contracts** (`/v1`, additive-only schema evolution) and keep them backward-compatible; **structured logging, no stray prints**.
- **Robust data paths** — write/ingest paths have an **idempotency / natural key**; **public or expensive endpoints are rate-limited**; every persisted entity carries its **tenant/owner key**.
- **Accessibility (UI)** — keyboard, focus, contrast, semantic markup are part of the definition-of-done for any user-facing feature.

## Production safeguards

- **Security baseline** — no secrets in source (secret-scan clean); check authorization / tenant-isolation on **every** data path; validate inputs; **fail-CLOSED** on security/auth.
- **Secrets never get pushed** — tests/imports use **obviously-fake placeholder keys** (`sk-fake-...`); the secret-scan config allowlists *only those documented fakes by name* (a real key still fails CI); CI generates throwaway creds at runtime; real secrets live only in gitignored `.env` (and its backups — `.env.bak`, `*.env.local` — never `.env.example`).
- **AI-specific security (when the product uses LLMs)** — defend against **prompt injection**, jailbreaks, data exfiltration via outputs, secret/PII leakage, tool/over-agency abuse. Benchmark to the **OWASP LLM Top 10**.
- **Observability & audit** — structured logging; trace every external/LLM/agent step; an audit record for state changes.
- **Fail-safe errors** — graceful fallbacks; never silently swallow errors; retry only *transient* failures.
- **Resilience by design** — for every external: timeouts, retry-transient-only, and a fallback / circuit-breaker. Decide this at architecture time, not after an outage.
- **Perf & cost budgets** — set a latency + cost target where relevant (the stack choice locks it in). Defer paid infra until a real need (record the trigger).
- **AI architecture (AI products)** — decide prompt-versioning, an eval harness, and LLM tracing/observability as first-class architecture decisions, not emergent ones.
- **Rollout safety** — risky/irreversible changes ship behind a **feature flag / staged rollout** with a stated **rollback path** (revert PR, migration-down, flag-off) and a named **post-deploy signal to watch**.
- **Measure for real** — quality is compared to a **recorded baseline** (a regression below threshold fails); the success metric is **actually instrumented** (events/analytics), never guessed; tests are **deterministic** (seeded, no races) with the **critical path covered**.

## Documentation-driven

- Before a big task, create a short design doc. On completion, **reconcile code ↔ doc**; gate the merge on the doc matching reality. Docs that drift are worse than none — a false capability/security claim is a liability.

## Communication

- Explain in **plain, non-technical language**; wait for confirmation before changing things.
- Prefer **one clear recommendation + yes/no** over a jargon matrix.
- **Honesty always** — surface gaps, failures, uncertainty plainly.
- **`.env` / secret files are the user's to edit** — hand the user the exact lines; never script-overwrite a secret file.

## Reviews, vision & confidence

- **Reviews are DEEP, not skims** — read the real code paths; end with a **confidence rating + evidence**.
- **Vision alignment is the top priority** — continually ask *"does this serve the product's vision?"* and surface misalignment instead of drifting.
- On completion, report a **Confidence Score (0–100%)** against the exit criteria: one line each on **solid** (verified), **risky/untested** (gaps), and **to raise it** (next check).
- **Generic, not domain-specific** — prefer the generic mechanism; a domain/special-case branch baked into shared infra is a smell.

---

## Production-readiness concern areas (the coverage checklist)

A serious product consciously covers — or *deliberately defers with a trigger* — each of these.
`/plan` emits this as a now / next / later / N-A checklist; the relevant skills enforce the items:

- **security** — authz/tenant-isolation, secret-scan + dependency-vulnerability scan, fail-closed, cookie-based auth (not localStorage), CORS, data-deletion/GDPR (data products).
- **ai-specific** (AI products) — prompt-injection defence, LLM fallback, scoring-bias, prompt version pinning (OWASP LLM Top 10).
- **observability** — structured logging, dashboards, alerting rules, cost-per-run reporting.
- **developer-experience** — README/CONTRIBUTING, API docs (OpenAPI), CHANGELOG, task runner.
- **testing** — unit + integration + regression + adversarial + a golden/eval dataset.
- **infra** — CI (mirrors prod), migrations (not raw schema), containerization, backup/restore.
- **documentation** — ADRs, architecture, ops runbook, the PRODUCT.md/STRUCTURE.md/feature-docs surface.
- **product** — a sharp vision (named customer + **job-to-be-done**, why-now), a **north-star success metric**, the **riskiest assumption** named, business-model awareness (free/paid/internal), scope discipline, roadmap. A vague vision is the root of later drift.

Not all are P0 — but each should be a conscious choice, never an accident.

## The exit-criteria gate (ONE pattern, used by every skill)

Every skill carries a **contract block** in its header:

```
Purpose:  <one line>
Reads:    <PRODUCT.md sections this phase depends on>
Writes:   <PRODUCT.md section + required fields>
Exit criteria:
  - [ ] <testable item — maps to a PRODUCT.md field or an evals assertion>
  - [ ] ...
```

- **Authoring:** the skill is not "done" until it satisfies its own exit criteria.
- **Runtime self-check (before handoff):** verify every required `PRODUCT.md` field is present, non-empty, and evidenced. **If anything is missing, STOP and report it — do not hand off.**
- **Prior-gate check (Step 0):** confirm the previous phase's exit criteria were met; if not, warn but allow override (standalone/jump-in still works).

## Spine resolution — what "`PRODUCT.md`" means (greenfield · brownfield · code-only)

`PRODUCT.md` is the spine for products *born* in this playbook. Every skill must resolve the
spine **flexibly and `PRODUCT.md`-first**, so a greenfield playbook project is never affected:

1. **`PRODUCT.md` exists** → it *is* the spine. (default — unchanged behaviour)
2. **No `PRODUCT.md`, but the project has docs** → resolve the spine from the project's own
   docs, in order: `CLAUDE.md` → `README.md` → `docs/` → `AGENTS.md`. Map sections *loosely*
   (Vision ≈ the "what/why"; Scope/Non-goals ≈ an out-of-scope / "not doing" list; Build log ≈
   a build-state / `CHANGELOG`). **State which file you resolved as the spine.** Never fabricate
   a section that isn't there.
3. **Code only, no spine doc at all** → infer a **low-confidence** picture from the code +
   package metadata (`package.json`, `pyproject.toml`, manifest, entry points, routes). **Label
   it "INFERRED"** and say plainly what *cannot* be judged without recorded intent (e.g. true
   scope/vision drift). **Never grade against a self-guessed baseline** (no-assumptions /
   honesty). Recommend bootstrapping a real spine — `/vision`+`/scope`, or a minimal
   `PRODUCT.md`/`CLAUDE.md`.

A skill that *writes* a section degrades gracefully when there's no `PRODUCT.md`: prefer
reporting to the user (and offering to create/append a spine) over forcing a `PRODUCT.md` the
project never opted into. A skill that *creates* `PRODUCT.md` by design (e.g. `/vision`) keeps
doing so.

---

## Lessons baked in (generalised from real project struggles)

Phrased generically so they apply to any project:

- **Dead config** — a setting silently overridden upstream, or applied as a no-op. Verify the value actually *flows* end-to-end.
- **Fail-loud on misconfig, fail-closed on security** — refuse to boot on insecure/known-constant defaults; secret-scan source.
- **No swallowed errors** — route failures explicitly (don't `print`+continue); retry only transient errors, never bare `Exception` (a silent failure looks healthy).
- **Measure/reproduce before fixing** — a scary number is often a *display/measurement artifact* (a 0–1 value read on a 0–10 scale; a matcher quirk), not the bug. Don't act on a guessed root cause.
- **Eval/benchmark integrity** — distinguish "blocked/errored/dropped" from "genuinely low quality", or the metrics lie.
- **Units/scale agree across boundaries** — confirm both sides agree on units/scale/shape when a value crosses a boundary.
- **Schema ↔ code consistency** — via migrations; a column the code reads must exist; CI bootstraps from the real schema.
- **Environment/platform gotchas** — cross-platform (stdout encoding, caches cleared between runs, corporate proxy/SSL); don't assume network egress.
- **Defer paid infra/features until a real trigger** — anti-creep at the infra level; record the trigger.
- **Docs must match reality** — reconcile code ↔ docs; no false claims.
- **Fresh-eyes review, but verify findings against the real code** — don't rubber-stamp an audit; some findings are already done or misdiagnosed.
- **Tests passing ≠ it works** — verify the path the product *actually runs*, not just the function in isolation; trace callers / cross-file wiring.
- **Every "done" records HOW it was verified** — evidence, not just "done".
- **Multi-tenant isolation at DB *and* app (defense-in-depth)** — one missing scope filter is a silent cross-tenant leak.
- **Policy-as-code: "parses" ≠ "governs"** — a syntactically-valid but ruleless policy (comments-only / zero statements) silently degrades to the engine's default (deny-all, or worse allow-all); load-validate that it defines ≥1 rule and fail-loud. Build the authz query from **escaped identifiers + structured request/entity objects**, never string-interpolated into policy text — a crafted name (tool/resource/role) is an injection point like SQL. Default-deny; any eval error / no-decision → **deny**.
