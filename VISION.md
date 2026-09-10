# VISION.md — what product-playbook is, and the contract every skill must meet

## Why this exists

AI made building cheap. It did not make **deciding what to build** or **proving it worked**
cheap — those are what is now scarce. An AI coding agent writes code faster than anyone can
reason about it, so the failure mode is no longer *"we couldn't build it"*: it is a
working-looking product nobody can account for. The five that cost the author real time:
features nobody asked for, config that silently did nothing, green tests over a dead live
path, a vendor SDK welded into the business logic, a missing tenant filter.

**AI is an execution engine, not a discipline engine.** Without gates it does not just build
the product — it multiplies the entropy at the same speed. `product-playbook` puts the gates
in between. Each phase writes its decision into one file (`PRODUCT.md`); the next phase reads
it and checks it against the repository before it advances.

### The guarantee (deliberately narrow)

**A process that cannot silently skip a check.** Not senior judgment, not good outcomes —
those depend on the builder. What is guaranteed is the enforced sequence: every advance is
checked against evidence in the repo, and a bypass is *recorded* with a reason and a date
rather than waved through.

That claim is checkable, which is why it is the one being made. `tools/check.py` **check 9**
fails CI if any phase skill carries a gate's title without a gate's behaviour — the enforcement
is in the build, not in this paragraph.

### Evidence gates — the idea, named once

> **No evidence → the gate holds → no progress.**

The teeth are in the *refusal*, not in the advance, so the name is the negative one. Used where
it is load-bearing — the skills' `## Contract` exit criteria, §Completeness guarantee below,
`PRINCIPLES.md` — and nowhere as decoration.

## Who it is for

**Primary — a technical builder shipping with AI coding agents, without the team that normally
catches this.** A solo founder, or an engineer anywhere from first job to staff, with no PM,
designer, QA, staff engineer, security engineer or release manager beside them. Claude Code is
the runtime; the same gap exists in Cursor or Copilot.

**The job to be done:** *"I can build incredibly fast, and make expensive mistakes just as fast.
Give me the discipline of the roles I do not have, without a bureaucracy."*

**Secondary — recorded, and deliberately deferred.** Small engineering teams adopting AI agents ·
tech leads · consultancies and agencies · developers inheriting an AI-generated codebase. Nothing
is designed for these until the primary reader is served; they are listed so a later decision to
serve one is deliberate rather than drift.

**Retired claim — "a newcomer, techie or not".** This file previously promised value to anyone,
technical or not. That is who *can* open it, not who it is *for*, and it is exactly the answer
`/vision` would reject from a user. Phase 1 (`/vision` → `/plan`) stays readable without code,
but from `/architect` onward this drives an engineering process — **you need a developer from
there.**

It is **sequential but standalone**: a first-timer runs the phases in order; an experienced
builder enters at any skill. Continuity comes from one shared file, `PRODUCT.md` (the spine).
Quality comes from `PRINCIPLES.md` (single-source rules) baked into every phase. Skills
**compose existing Claude Code skills** (`/code-review`, `/verify`, `/doc-create`, …) rather
than reinventing them.

This is distinct from `product-toolkit` (a grab-bag of individual dev/quality skills).
`product-playbook` is the opinionated *journey*.

## The journey (phases → skills)

| Phase | Skill | Purpose | Exit criteria (must all be true to hand off) |
|---|---|---|---|
| start | `/playbook` | Guided entry-point — orchestrates the phases one at a time, pausing at each gate | user always knows where they are + the next phase; **never skips a gate**; routes only (writes nothing itself) |
| start | `/adopt` | Entry for a project that already has code — drafts an **INFERRED** `PRODUCT.md` from the repo, confirmed section-by-section by the owner | every inferred line tagged `(inferred — confirm)`; a section with no evidence stays **empty**, never guessed; nothing written before the confirm-loop; never overwrites an existing `PRODUCT.md`; recommends the next skill from what is still empty |
| 1 Product | `/vision` | Vision, customer, problem, value; benchmark to the 2026 market; metric/JTBD/risk/model | `PRODUCT.md#Vision` has who/problem/value/verified-market-read + north-star metric + job-to-be-done + riskiest assumption + business model, all non-empty |
| 1 Product | `/validate` | Test the riskiest assumption with the cheapest experiment BEFORE code; threshold set in advance; proceed / pivot / kill | `#Validation` has a falsifiable assumption + one experiment with a time box + a pass/fail threshold recorded **before** the result + a measured result + a verdict — or an explicit dated **override**; never hands off on a feeling |
| 1 Product | `/scope` | The ONE core feature + Deferred(+trigger) + Non-goals (anti-creep) | `#Scope` names a single core feature, a non-empty **Deferred** list with triggers, **and** a **Non-goals** list |
| 1 Product | `/plan` | Phases, milestones, timeline, per-milestone exit criteria + concern-area coverage | `#Plan` has core-first phases + timeline + a testable exit criterion per milestone + a concern-area checklist (security/observability/testing/docs/DX/…) marked now/next/later |
| 2 Dev | `/architect` | Decide stack + tools + key decisions (2026 OSS-first); patterns/anti-patterns; ADRs | `#Architecture` records stack+tools+why, externals behind adapters, the design patterns applied + anti-patterns avoided (current-year), migrations approach |
| 2 Dev | `/structure` | Stack-aware clean layout (backend/frontend/full-stack) + what each folder does + root scaffolding + `prompts/` for AI | `STRUCTURE.md` folder→purpose map; root files (`.gitignore` ignoring `.env*`, `.gitleaks.toml`, pre-commit, `.env.example`, Makefile, dep manifest); no secret in code; `#Structure` filled |
| 2 Dev | `/design-system` | (UI products only) Principles → confirmed sample page → archetype-correct `DESIGN.md` (shadcn tokens); enforces a universal-laws quality floor | UI gate applied (no UI → writes nothing); 4–6 principles with a plain-language why; the user asked for their own look **before any archetype is named** + the 3-question picker answered by them, then an archetype proposed as the default (their idea wins); concrete foundations (font pairing/type scale/OKLCH colour/density/depth/motion); ONE sample page (real content) **approved via a confirm-loop** before any propagation; `DESIGN.md` (9 sections, shadcn OKLCH tokens, WCAG-AA) + `#Design` filled |
| 2 Dev | `/frontend-audit` | (UI products only) Mechanical enforcement of the design-system laws — real OKLCH→WCAG contrast engine + token/motion/font/responsive checks; CI-friendly | runs `audit.py` over UI + `DESIGN.md`; computes the WCAG ratio per token pair in **both** modes; any ERROR exits non-zero (CI gate); prints a per-law pass/warn/error scorecard |
| UI suite | `/new-component` | (bundled UI-suite support) Build/skin ONE React component against `DESIGN.md` tokens | CSS-vars (no raw hex); interactive states (hover/focus-visible/active/disabled); typography + a11y constraints; reuses shadcn/ui + 21st.dev primitives |
| 2 Dev | `/foundation` | Walking skeleton that RUNS: config, logging+tracing, infra, the pre-commit+CI auto-layer | `#Foundation` shows app runs end-to-end (shown); config-flow verified; guards; **pre-commit + CI auto-run** secret-scan + dependency-vuln + tests and block on red; observability hook; async-safe |
| 2 Dev | `/contracts` | Typed models/schemas/migrations BEFORE logic | #Contracts lists typed models/migrations (applies); boundary units/scale agreed; **versioning**; **PII + tenant + idempotency keys**; API contracts documented |
| 2 Dev | `/tickets` | Breaks down milestones into structured GitHub issue tickets with target file paths, modules, tasks, and DoD | docs/issues/*.md, .github/ISSUE_TEMPLATE/ |
| 2 Dev | `/build` | Per-feature loop with security-in-DoD + per-feature doc | each feature in `#Build log` has DoD-met + how-verified + a `docs/features/*` doc; no secret in code; single-responsibility (no god-files); **lane mode:** writes only inside `ALLOW`, Build-log row goes in the feature doc, spine untouched |
| 2 Dev | `/dev-check` | Checkpoint: verify every feature's exit criteria + security DoD | all `#Dev-complete` boxes checked, with evidence; no god-files; scans clean; **lane mode:** feature-doc Build-log rows reconciled into the spine (one writer), cross-lane seams tested on the merged base |
| 3 Test | `/test` | Unit/integration/regression + adversarial (injection/authz) + golden dataset | `#Tests` shows coverage incl. live-path + security cases + a golden/eval dataset; fake keys only |
| 4 Eval | `/eval` | Is it good? measure-first; confidence score | `#Evaluation` has measured result + confidence; operational-failures separated; cost-per-run (+ AI bias) |
| 5 Ship | `/ship` | Deep review + security review + reconcile docs + rollout-safety + PR + handoff | `#Ship log` entry with review+security+docs-reconciled+PR + CHANGELOG + security checklist + **rollback/flag + post-deploy signal**; confidence reported; **lane mode:** `lanekeeper check` passed, `lane:` label on the PR, Ship log + CHANGELOG written on the base branch after merge |
| 6 Learn | `/learn` | Success metric (instrumented), user signal, decide next/kill from evidence | `#Learnings` has instrumented metric result + a user signal + retro + evidence-based next step (build/iterate/**kill**); observability + cost watch in place |
| anytime | `/drift-check` | Are we still building the vision, or creeping? + concern-area + code↔docs drift | reports scope/vision/plan/doc drift against `PRODUCT.md`; records confirmed drift in `#Drift log` |

## Git-native by design — and the non-goal that protects it

The product's memory lives in **Git, beside the product**, not in a dashboard. That is an
architectural choice, not a convenience, and every property below is a consequence of it:

- **Reviewable** — a decision arrives as a diff in a PR, and can be argued with there.
- **Versioned and blameable** — `git log PRODUCT.md` is the decision history, with dates and authors.
- **Revertable** — a bad scope call is reverted the same way a bad commit is.
- **Branchable** — a spike carries its own spine on its own branch.
- **Agent-inspectable** — any agent, in any harness, reads a text file in the repo it is already in.
- **Forkable** — a team forks the process along with the code.
- **No external dependency** — nothing to sign up for, no service to be down, no account to lose.
- **It travels with the repo** — clone the project and the reasoning arrives with it.

**Non-goal: no hosted service.** No accounts, no cloud database, no hosted `PRODUCT.md`, no web UI,
no analytics dashboard, no team management. Not "not yet" — the reason is above: a hosted copy of
the spine would be the one part of the product that is *not* reviewable, versionable or forkable,
and it would trade the whole list for a nicer view of it. The proof this product needs is
`git clone → install → /playbook → a real project → a result someone can check`, and none of that
needs a server.

**Reopen trigger** (per `/scope`'s Deferred+trigger convention, applied to this repo): a
requirement that genuinely cannot be met by a text file in a repo — e.g. several people needing
to edit one spine concurrently with conflict resolution, or an org needing cross-repo rollups —
reported by real users, not anticipated. Until then, tickets that add machine-readable state
(state model, evidence records, status output) are built **against** this non-goal: none of them
may assume a service.

## Completeness guarantee

Evidence gates, stated as a contract rather than a slogan:

- Every skill's **contract block** exit criteria ⊆ a `PRODUCT.md` field or an `evals/evals.json` assertion.
- A skill won't hand off until its exit criteria are met (runtime self-check); the next skill re-checks the prior phase.
- `evals/evals.json` states, per skill, the behaviour this VISION requires — at least two cases each.
  **CI gates the file's structure, not its verdicts:** `tools/check.py` fails on a missing or drifted
  field, a duplicate id or a skill below two cases. **Executing the cases is still manual** — re-run
  them on change; until that is automated, a green build means the assertions are well-formed, not met.
- **A phase skill's `Step 0` gate is read from its body, not its heading** — `tools/check.py` check 9
  fails the build if a `prior-gate check` names no prior `#Section` or offers no override. This is the
  enforcement the guarantee above cites, and it may not be weakened or exempted for a new skill.
- Run `/drift-check` on this repo to confirm each skill still matches its row above.

## Non-negotiables (from PRINCIPLES.md)

No hardcoding (config/`.env`/prompt files) · typed contracts · provider/adapter for externals ·
security-in-the-build (fail-closed; OWASP LLM Top 10 for AI) · honest docs that match reality ·
measure before fixing · evidence-based "done" · generic-not-domain-specific · plain-language
communication · `.env` is user-owned.

<!-- skills: `/adopt` `/architect` `/build` `/contracts` `/design-system` `/dev-check` `/drift-check` `/eval` `/foundation` `/frontend-audit` `/learn` `/new-component` `/plan` `/playbook` `/scope` `/ship` `/structure` `/test` `/tickets` `/validate` `/vision` -->
