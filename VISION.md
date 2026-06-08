# VISION.md — what product-playbook is, and the contract every skill must meet

## Why this exists

A guided, end-to-end way to build a product **without drifting out of control** —
encoding hard-won discipline (architect → verify → no-hardcoding → benchmark →
self-review; scope control; security-in-the-build; honest docs) so that **anyone —
a newcomer (techie or not) or an experienced builder dropping into one phase — gets
senior-level results by default.**

It is **sequential but standalone**: a newcomer runs the phases in order; an
experienced builder enters at any skill. Continuity comes from one shared file,
`PRODUCT.md` (the spine). Quality comes from `PRINCIPLES.md` (single-source rules)
baked into every phase. Skills **compose existing Claude Code skills** (`/code-review`,
`/verify`, `/doc-create`, …) rather than reinventing them.

This is distinct from `product-toolkit` (a grab-bag of individual dev/quality skills).
`product-playbook` is the opinionated *journey*.

## The journey (phases → skills)

| Phase | Skill | Purpose | Exit criteria (must all be true to hand off) |
|---|---|---|---|
| start | `/playbook` | Guided entry-point — orchestrates the phases one at a time, pausing at each gate | user always knows where they are + the next phase; **never skips a gate**; routes only (writes nothing itself) |
| 1 Product | `/vision` | Vision, customer, problem, value; benchmark to the 2026 market; metric/JTBD/risk/model | `PRODUCT.md#Vision` has who/problem/value/verified-market-read + north-star metric + job-to-be-done + riskiest assumption + business model, all non-empty |
| 1 Product | `/scope` | The ONE core feature + Deferred(+trigger) + Non-goals (anti-creep) | `#Scope` names a single core feature, a non-empty **Deferred** list with triggers, **and** a **Non-goals** list |
| 1 Product | `/plan` | Phases, milestones, timeline, per-milestone exit criteria + concern-area coverage | `#Plan` has core-first phases + timeline + a testable exit criterion per milestone + a concern-area checklist (security/observability/testing/docs/DX/…) marked now/next/later |
| 2 Dev | `/architect` | Decide stack + tools + key decisions (2026 OSS-first); patterns/anti-patterns; ADRs | `#Architecture` records stack+tools+why, externals behind adapters, the design patterns applied + anti-patterns avoided (current-year), migrations approach |
| 2 Dev | `/structure` | Stack-aware clean layout (backend/frontend/full-stack) + what each folder does + root scaffolding + `prompts/` for AI | `STRUCTURE.md` folder→purpose map; root files (`.gitignore` ignoring `.env*`, `.gitleaks.toml`, pre-commit, `.env.example`, Makefile, dep manifest); no secret in code; `#Structure` filled |
| 2 Dev | `/design-system` | (UI products only) Principles → confirmed sample page → archetype-correct `DESIGN.md` (shadcn tokens); enforces a universal-laws quality floor | UI gate applied (no UI → writes nothing); 4–6 principles with a plain-language why; an archetype proposed + the user asked for their own idea; concrete foundations (font pairing/type scale/OKLCH colour/density/depth/motion); ONE sample page (real content) **approved via a confirm-loop** before any propagation; `DESIGN.md` (9 sections, shadcn OKLCH tokens, WCAG-AA) + `#Design` filled |
| 2 Dev | `/foundation` | Walking skeleton that RUNS: config, logging+tracing, infra, the pre-commit+CI auto-layer | `#Foundation` shows app runs end-to-end (shown); config-flow verified; guards; **pre-commit + CI auto-run** secret-scan + dependency-vuln + tests and block on red; observability hook; async-safe |
| 2 Dev | `/contracts` | Typed models/schemas/migrations BEFORE logic | `#Contracts` lists typed models/migrations (applies); boundary units/scale agreed; **versioning**; **PII + tenant + idempotency keys**; API contracts documented |
| 2 Dev | `/build` | Per-feature loop with security-in-DoD + per-feature doc | each feature in `#Build log` has DoD-met + how-verified + a `docs/features/*` doc; no secret in code; single-responsibility (no god-files) |
| 2 Dev | `/dev-check` | Checkpoint: verify every feature's exit criteria + security DoD | all `#Dev-complete` boxes checked, with evidence; no god-files; scans clean |
| 3 Test | `/test` | Unit/integration/regression + adversarial (injection/authz) + golden dataset | `#Tests` shows coverage incl. live-path + security cases + a golden/eval dataset; fake keys only |
| 4 Eval | `/eval` | Is it good? measure-first; confidence score | `#Evaluation` has measured result + confidence; operational-failures separated; cost-per-run (+ AI bias) |
| 5 Ship | `/ship` | Deep review + security review + reconcile docs + rollout-safety + PR + handoff | `#Ship log` entry with review+security+docs-reconciled+PR + CHANGELOG + security checklist + **rollback/flag + post-deploy signal**; confidence reported |
| 6 Learn | `/learn` | Success metric (instrumented), user signal, decide next/kill from evidence | `#Learnings` has instrumented metric result + a user signal + retro + evidence-based next step (build/iterate/**kill**); observability + cost watch in place |
| anytime | `/drift-check` | Are we still building the vision, or creeping? + concern-area + code↔docs drift | reports scope/vision/plan/doc drift against `PRODUCT.md`; records confirmed drift in `#Drift log` |

## Completeness guarantee

- Every skill's **contract block** exit criteria ⊆ a `PRODUCT.md` field or an `evals/evals.json` assertion.
- A skill won't hand off until its exit criteria are met (runtime self-check); the next skill re-checks the prior phase.
- `evals/evals.json` proves each skill matches this VISION; re-run on change.
- Run `/drift-check` on this repo to confirm each skill still matches its row above.

## Non-negotiables (from PRINCIPLES.md)

No hardcoding (config/`.env`/prompt files) · typed contracts · provider/adapter for externals ·
security-in-the-build (fail-closed; OWASP LLM Top 10 for AI) · honest docs that match reality ·
measure before fixing · evidence-based "done" · generic-not-domain-specific · plain-language
communication · `.env` is user-owned.
