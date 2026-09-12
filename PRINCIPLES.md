# PRINCIPLES.md — the working rules every skill enforces

> Single source of truth for the **rules**. Every `product-playbook` skill links here and names the
> subset that is load-bearing for its phase. Do not duplicate these rules inside a skill — reference
> them, so they can never drift.
>
> **The mechanisms live next door, in `MECHANISMS.md`** (`references/mechanisms.md` in this repo;
> installed beside `PRINCIPLES.md` as a companion) — §Step 3b · §Step 3c · §Re-run semantics ·
> §Declined runs · §Seam · §Spine resolution · §Lane mode. **The harvested lessons live in
> `LESSONS.md`** (`references/lessons.md`) — §Lessons baked in · §Lesson format.
> This file is loaded by every skill, so its size is the per-session attention cost of the whole
> system; a rule that is followed has to be short enough to read. `tools/check.py` fails either file
> over the size threshold, and fails a `§` pointer that resolves to nothing.

---

## The 5-step spine (run on every non-trivial task)

1. **Architect first** — think how it *should* be built and where it fits, before writing code.
2. **Verify** — confirm assumptions/root cause against the real code + running system. Never act on a stale note or a guess.
3. **No hardcoding** — every value (weights, thresholds, endpoints, model names, prompts, credentials) lives in **config / `.env` / a prompt file**, never baked into source.
4. **Benchmark to the current year, then optimise for the project's constraints — not for an ideology** — ask "is this how leading product companies do it *now*?", then judge the candidates on **fit**: reliability, operational burden, team size, cost, compatibility, maturity, and **lock-in — portability and exit cost stay explicit criteria**. Record *why the winner won*. A managed service that saves a two-person team twenty hours a month can beat self-hosting; so can the boring, stable option. "Open source by default" pre-decides a trade-off the project's constraints should decide.
5. **Self-review** — run the project's review (`/code-review`, `/security-review` on auth/data) and check quality/perf/tests before calling it done.

## Per-feature contract (agree BEFORE building a feature)

- **Exit criteria** — explicit, *testable* definition of done. Not done until every criterion is met **and verified**. Where the verification can be re-run, record it in the one settled form (`docs/state-model.md` §2f) — `` `evidence: <command> → <result> · <artefact> · <date>` `` — so a later session, a reviewer or CI can **re-execute it and compare** rather than take the claim on trust. A criterion that was judged rather than measured carries no evidence line and is reported as unverified; that is honest. No vague "done".
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
- **Placeholders must FAIL the boot, never pass a check** — every value in `.env.example` is written in an
  unmistakable form (`CHANGE_ME__<VAR>__CHANGE_ME`) and **rejected by name** at startup, not merely length- or
  format-checked. A 48-character `replace-me-with-32-plus-random-characters` placeholder passes `min(32)` and boots
  the app on a session-signing key that is public in git. The boot failure names the variable and how to generate a
  real value; under production (`NODE_ENV`/`APP_ENV`) there is **no override**.
- **Tests never touch the developer's or production data** — an integration suite runs against an
  **isolated, disposable datastore** (a separate URL, or per-test transaction rollback); sharing the dev
  one is not an option, because "real boundaries" plus a teardown hook is a truncate away from real data.
  The isolation is enforced by a **fail-closed bootstrap**, not a convention: if the target it was handed
  is the dev or production one, the suite **refuses to run**, names both, and exits non-zero. A destructive
  hook must never be one copied `.env` away from the real thing.
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
- **A spine section is a RECORD, not a container.** Summary · the decision · the evidence line · a pointer
  to where the detail lives. **No byte cap on the spine** — the instrument is the record test, per
  field: *decision, or the reasoning behind it?* Reasoning moves into a companion (`STRUCTURE.md`,
  `DESIGN.md`, `docs/adr/*`, `docs/runbook.md`, `docs/features/*`, `docs/<phase>.md`) and the pointer
  stays; a required field answered tightly stays whatever it weighs. Size is *reported*, never
  *enforced*: a cap trims answers instead of relocating reasoning (#200). A spine full of reasoning gets
  grepped instead of read, and a phase that greps is how a standing open decision gets dropped.
- **Then the pointer is binding** (`MECHANISMS.md` §Follow the pointer): every companion added is a new
  place a phase can find a signpost where it needed a definition. Splitting without that rule is worse
  than not splitting.

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

## Composed skills — name the capability, not the command

- **Every skill this playbook composes is a CAPABILITY, not a command name.** `/code-review`,
  `/security-review`, `/run`, `/loop` and `/schedule` are Claude Code built-ins; another harness names
  them differently, or not at all. **If the command is unavailable, do the same work by the best means
  you have** — your default reviewer agent / review mode, your own security-audit pass, running the app
  by hand — and **NEVER skip it**.
- **Then say which one you did, in the evidence line.** A composed command that silently no-ops is a
  **SKIPPED GATE still reported as run** — the one outcome that is never acceptable. Some harnesses make
  a review command **user-invocable only**: then ASK the user to run it, or do the pass by hand and
  record that. **Degrading is fine; degrading invisibly is not.**

---

## Production-readiness concern areas (the coverage checklist)

A serious product consciously covers — or *deliberately defers with a trigger* — each of these.
`/plan` emits this as a now / next / later / N-A checklist; the relevant skills enforce the items:

- **security** — authz/tenant-isolation, secret-scan + dependency-vulnerability scan, fail-closed, cookie-based auth (not localStorage), CORS, data-deletion/GDPR (data products).
- **ai-specific** (AI products) — prompt-injection defence, LLM fallback, scoring-bias, prompt version pinning (OWASP LLM Top 10).
- **observability** — structured logging, dashboards, alerting rules, cost-per-run reporting.
- **developer-experience** — README/CONTRIBUTING, API docs (OpenAPI), CHANGELOG, task runner.
- **testing** — unit + integration + regression + adversarial + a golden/eval dataset + **the real user's
  environment** (browser UI: third-party DOM injection, locale/timezone, reduced motion and forced colours,
  degraded network) — a clean headless run reproduces none of these.
- **infra** — CI (mirrors prod), migrations (not raw schema), containerization, backup/restore.
- **documentation** — ADRs, architecture, ops runbook, the PRODUCT.md/STRUCTURE.md/feature-docs surface.
- **product** — a sharp vision (named customer + **job-to-be-done**, why-now), a **north-star success metric**, the **riskiest assumption** named, business-model awareness (free/paid/internal), scope discipline, roadmap. A vague vision is the root of later drift.

Not all are P0 — but each should be a conscious choice, never an accident.

## The exit-criteria gate (ONE pattern, used by every skill)

**Evidence gates: no evidence → the gate holds → no progress.** The name for what this pattern does;
the teeth are in the refusal, not the advance. Every skill carries a **contract block** in its header:

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
- **Gates are classified by where the answer lives, not by how experienced the user is**
  (`docs/state-model.md` §2d). **input** — the answer exists only in the human, so it can **never** be
  batched or auto-answered; **derivation** — computable from prior sections, so a run may batch and end
  in one review; **verification** — pass/fail on repo evidence, batchable and **stops on red**. Declared
  per skill and enforced by `tools/check.py`; a global auto-mode is rejected, with reasons, in
  `docs/state-model.md` §3. **An input gate is a question, not an approval** — do not call it a
  confirmation.
- **A `PRODUCT.md` section is in one of five declared states** — empty · declined · filled · overridden ·
  superseded (`docs/state-model.md` §2a). Every section-writing skill declares which markers it
  implements, and any exemption carries a reason; an omission and a decision must never look the same.
- **Prior-gate check (Step 0):** confirm the previous phase's exit criteria were met. If they were not,
  **warn, name the missing phase and offer it first** — standalone/jump-in is first-class, so a gate is a
  gate and never a wall. Proceeding anyway is an **override, and an override is recorded, never verbal**:
  it names the gate being bypassed, captures **the reason in the user's own words**, and is written as an
  `Override <date>: <reason> — bypassed <gate>` line in this phase's own section. A *warning* is
  informational and needs no ceremony; an *override* advances the project on unmet criteria — the more
  consequential of the two — so it is the one that must leave a trace. **One rule, one home:** the form and
  the reading of it are defined in §Declined runs; this is the pointer, not a second copy. Enforced by
  `tools/check.py` check 9, which reads the Step 0 body, not its heading.
