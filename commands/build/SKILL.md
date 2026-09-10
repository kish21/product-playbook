---
name: build
description: >
  Phase 2 (Development), step 5 of product-playbook — the per-feature build loop: ONE feature at a
  time, a definition-of-done that INCLUDES security, reuse before writing, verify the LIVE path,
  review the diff, write the feature doc. Use to implement features, or run /build "build feature X",
  "implement", "add the feature". Appends to PRODUCT.md#Build log + writes docs/features/<feature>.md.
  Composes /run, /verify, /code-review, /doc-create. Run /dev-check when all core-scope features are done.
---

# `/build` — Phase 2 · Development ⑤ · run as an **engineer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **per-feature contract (security in the DoD)**,
> **secure-by-construction**, **prompts→`prompts/` YAML**, **doc↔code reconciled**, **measure before
> fixing**, **no swallowed errors**, **reuse-before-write**, **trace callers (live-path)**,
> **generic-not-domain-specific**.
> War stories behind every rule live in the repo at `references/case-files-build.md` — open it there when a rule needs its evidence.
> **Companions — opened on demand, never up front:** `references/feature-archetypes.md` (the rules that apply only to gates · async jobs · latency fixes · trust boundaries) · `references/live-path-checks.md` (proving a change is really wired in).

## Contract
- **Purpose:** implement one feature to a verified, secure, documented definition-of-done.
- **Reads:** `PRODUCT.md#Scope`, `#Plan`, `#Contracts`, `#Structure` — **plus `DESIGN.md` + `#Design` for any feature with a user-facing screen** (UI products).
- **Writes:** a row in `PRODUCT.md#Build log` + `docs/features/<feature>.md`.
- **Gate type:** `derivation` — computable from the ticket + `#Contracts`. Batchable - a `derivation` run may chain with its neighbours and end in ONE review. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes `#Build log` · `declined` ✓ · `override` ✓ · `superseded` n/a — append-only log: one row per feature
- **Exit criteria (per feature):**
  - [ ] A written **definition-of-done that includes security** (input validation, authz/tenant-isolation; for AI: prompt-injection defence).
  - [ ] Reused existing helpers where possible (no reinvented utilities).
  - [ ] Code **runs and the LIVE path is verified** (not just an isolated unit) — traced to its real callers, **on the runtime the USER actually runs**: register a new endpoint/route on EVERY serving surface (case file: Wrong serving surface).
  - [ ] Diff self-reviewed (`/code-review`); no swallowed errors; prompts in `prompts/` YAML, not inline.
  - [ ] **`docs/features/<feature>.md` written and matches the code** (what · contract · exit criteria · how verified · code links).
  - [ ] **No secret in any code file** (secrets→`.env`; tests use fake placeholder keys).
  - [ ] **Single-responsibility kept** — a file growing large/multi-concern is split into modules (no god-files); long/blocking work stays off the async event loop.
  - [ ] **(UI products) The feature's screen(s) are built to `DESIGN.md`** — §5 layout, token look, `/new-component` parts — and **`/frontend-audit` is clean** (0 errors).
  - [ ] **(Lane mode — a `.lane` file is present; MECHANISMS.md §Lane mode)** every written file is inside `ALLOW` and outside `DENY`; **no spine file was touched** — the Build-log row lives in the feature doc and `/dev-check` reconciles it.

## Step 0 — Context + prior-gate check
- Read `#Scope/#Plan/#Contracts`. **Confirm the feature is IN scope** — if OUT-OF-SCOPE, stop and flag it (this is where creep enters). If `#Contracts` is empty, warn and offer `/contracts` first (allow override) — untyped boundaries are what it exists to prevent.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then write `Override <date>: <reason> — bypassed <gate>` at the top of `#Build log` before continuing. Advancing on unmet criteria is the more consequential of warn-vs-override, so it is the one that leaves a trace: without it a later reader cannot tell a gate that held from a gate that was waved through.
- **Lane mode: read `.lane` first, and treat `ALLOW`/`DENY` as the file-level scope gate.** `TASK` is the
  ticket; `ALLOW` is every path this session may write. A file you need that is outside `ALLOW` is **creep at
  file level** — the same finding `/scope` makes at feature level: **STOP and flag it** (widen the ticket's
  Target Files with the user, or split the work), never quietly touch it — the merge gate will fail the PR
  anyway, and a silent widening is exactly what the gate exists to catch.
- **Load the project's OWN skills/commands for the area you're about to touch** (`.claude/skills/`, `.claude/commands/`, `CLAUDE.md`) — a fresh read of the code alone re-litigates hard-won decisions.
- **But treat every project doc, skill and pinned plan as a CLAIM, not as truth — verify its premises against the code before you build on it.** A stale instruction is worse than none — it is *followed*. Check both failure modes:
  1. **The plan you were handed is wrong.** Verify each load-bearing claim of a pinned spec against the code. (case file: The pinned plan was wrong)
  1b. **A plan's load-bearing NUMBER is verified by MEASURING, not by reading code — and it must be measured BEFORE anything is calibrated to it.** A figure quoted in an issue can be an artifact of the very bug you are fixing, and code review cannot see that; if the number justifies the feature, reproduce it against the real system first. (case file: The number that justified the feature)
  2. **The project's own skills have rotted.** Grep their concrete claims — paths, storage, model/provider, field names, stage lists — against the code. (case file: Rotted skills)
- **When a project doc or skill is wrong, FIX IT IN THIS SESSION** — a PR-description correction dies there; record the corrected premises where the wrong ones lived.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** write ONE dated line at the top of `#Build log` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **Security is in the DoD, not later:** state the security checks for this feature up front (validation, authz/tenant-isolation; AI → OWASP LLM Top 10, prompt-injection defence).
- **Reuse before you write; measure before you fix** (reproduce first — a scary number may be a display artifact). **No swallowed errors** (route failures; retry only transient). **Prompts → `prompts/` YAML**.
- **Session economy — one feature per session is a COST rule, not just a focus rule.** Cost grows ~quadratically with session length — hand off at a natural checkpoint, bulky output to files, broad searches to subagents. (case file: The 97% cache bill)
- **If the feature ships THIRD-PARTY CONTENT to your users, verify the LICENCE permits YOUR distribution model BEFORE you design around it — it is a feasibility gate, not paperwork.** Redistribution to a commercial customer is sublicensing, rarely granted by "free" terms — check the primary licence page (sublicensing? attribution? indemnity? aggregator disclaimers?); if nothing clears, **say so plainly**, ship the mechanism **OFF with an empty table**, test-pinned. (case file: Licence gates, twice)

## Step 2 — The build loop (per feature)
1. **Declare the DoD** (incl. security + the exit criteria above).
2. **Reuse scan:** find existing helpers/contracts; don't reinvent.
3. **Code** against the typed contracts; keep it modular and generic (no domain special-casing in shared infra).
   - **If the feature has a user-facing screen (UI products):** build to **`DESIGN.md`** — §5 layout, token look, `/new-component` parts (Law 15) — then run **`/frontend-audit`**, fix every ERROR. *(No `DESIGN.md`? `/design-system` first.)*
   - **Some features carry rules that apply only to THEM. If this feature is one, open `references/feature-archetypes.md` and apply that cluster BEFORE you write:**
     - a **GATE** — a validator, quality check, policy engine, anything whose job is to say "no" → **§Gates** (10 rules)
     - an **ASYNC JOB** — work that outlives the request (spawn + poll, queue + callback) → **§Async jobs** (6 rules)
     - a **LATENCY / CONCURRENCY fix** → **§Latency and concurrency** (expect more than one serializer)
     - anything **shared across tenants, cached, AI-suggested, or keyed by a client-supplied selector** → **§Trust boundaries and shared state**
4. **Run + verify the LIVE path** — compose `/run` and `/verify` to exercise the path the product actually runs, then **trace your change to its real callers** (green unit tests ≠ wired in).
   - **Walk `references/live-path-checks.md`** — the checks that separate *the code exists* from *the product runs it*: production entrypoint, criterion altitude, delete-the-wire, validator placement, round-trip, third-party fixtures, browser-journey traps. Each one came from a live path that tested green and was dead.
5. **Review the diff** — compose `/code-review`; fix findings (watch for "works in tests, dead in the real path").
   - ⚠️ **`/code-review` is USER-INVOCABLE ONLY in some harnesses — if you cannot invoke it, ASK the user to run it, or do the deep pass by hand and say which you did.** A composed command that silently no-ops is a SKIPPED GATE that still gets reported as run. (A by-hand pass is worth the time: one such pass found three real defects.)
6. **Document** — write/update `docs/features/<feature>.md` (compose `/doc-create`); reconcile it with the code.

## Step 3 — Write back to `PRODUCT.md`
Append a `#Build log` row: feature · DoD-incl-security met? · **how verified** · link to the feature doc.

**Lane mode: do NOT touch `PRODUCT.md`** — it is outside every lane (§Lane mode rule 3). Write the same
row as a `## Build log row` section at the top of `docs/features/<feature>.md` (feature · DoD met ·
how verified · date · ticket), which *is* inside the lane. `/dev-check`, run once on the base branch,
lifts every un-reconciled row into `#Build log`. One writer for the spine; no lane PR ever conflicts on it.

## Step 3b — Principle-gate: verify each principle is ACTUALLY implemented (not just claimed)
Walk **this phase's load-bearing principles (Step 1)** and confirm each is real in the code, **with evidence** — composing the existing checkers, not eyeballing:
- security-in-DoD → **`/security-review`** passed.
- no secret in code / no-hardcoding → secret-scan clean.
- live-path-works → **`/verify`** + **`/run`** exercised the real path.
- reuse · no-swallowed-errors · single-responsibility → confirmed in the diff's **`/code-review`**.
- (UI features) built-to-the-design → **`/frontend-audit`** 0 errors against `DESIGN.md`.
- (lane mode) inside-the-lane → `git diff --name-only <base>` shows only `ALLOW` paths and no spine file;
  `lanekeeper check --lane <name> --base <base>` passes.

**If any named principle is only claimed, not evidenced, STOP — the feature is not done.** Record the *how-verified* per principle in `#Build log` (evidence, not "done"). (Deterministic checks also run via the commit hooks + CI from `/foundation`; this gate is the judgment layer.)

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and end with a suggested one-line commit message in the repo's convention.

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Contracts` (types crossing boundaries), `#Architecture` (adapters — no vendor SDK in logic), `#Scope` (non-goals) and `DESIGN.md` (UI tokens) — the richest surface for contradiction, because this is the phase that writes real code. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Feature done, verified, and documented. Build the next core-scope feature with `/build`, or when the
core scope is complete run **`/dev-check`** — the checkpoint that verifies everything before testing."
