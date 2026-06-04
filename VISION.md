# VISION.md — what product-builder is, and the contract every skill must meet

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
`product-builder` is the opinionated *journey*.

## The journey (phases → skills)

| Phase | Skill | Purpose | Exit criteria (must all be true to hand off) |
|---|---|---|---|
| 1 Product | `/vision` | Vision, customer, problem, value; benchmark to the 2026 market | `PRODUCT.md#Vision` has who/problem/value/market read, all non-empty |
| 1 Product | `/scope` | The ONE core feature + explicit OUT-OF-SCOPE (anti-creep) | `#Scope` names a single core feature **and** a non-empty OUT-OF-SCOPE list with triggers |
| 1 Product | `/plan` | Phases, milestones, timeline, per-milestone exit criteria | `#Plan` has core-first phases + timeline + a testable exit criterion per milestone |
| 2 Dev | `/architect` | Decide stack + tools + key decisions (2026 OSS-first); ADRs | `#Architecture` records stack+tools+why, key decisions, externals behind adapters |
| 2 Dev | `/structure` | Clean folder layout + what each folder does; `prompts/` for AI | `STRUCTURE.md` exists with a folder→purpose map; `#Structure` summary filled |
| 2 Dev | `/foundation` | Walking skeleton that RUNS: config, logging, infra, tooling, CI | `#Foundation` shows app runs end-to-end; config-flow verified; guards + secret-scan + CI present |
| 2 Dev | `/contracts` | Typed models/schemas/migrations BEFORE logic | `#Contracts` lists typed models/migrations; boundary units/scale agreed |
| 2 Dev | `/build` | Per-feature loop with security-in-DoD + per-feature doc | each feature in `#Build log` has DoD-met + how-verified + a `docs/features/*` doc |
| 2 Dev | `/dev-check` | Checkpoint: verify every feature's exit criteria + security DoD | all `#Dev-complete` boxes checked, with evidence |
| 3 Test | `/test` | Unit/integration/regression + adversarial (injection/authz) | `#Tests` shows coverage incl. live-path + security cases |
| 4 Eval | `/eval` | Is it good? measure-first; confidence score | `#Evaluation` has measured result + confidence; operational-failures separated |
| 5 Ship | `/ship` | Deep review + security review + reconcile docs + PR + handoff | `#Ship log` entry with review+security+docs-reconciled+PR; confidence reported |
| 6 Learn | `/learn` | Success metric, retro, decide next from evidence | `#Learnings` has metric result + retro + evidence-based next step |
| anytime | `/drift-check` | Are we still building the vision, or creeping? + code↔docs drift | reports scope/vision/doc drift against `PRODUCT.md` |

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
