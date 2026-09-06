---
name: dev-check
description: >
  Phase 2 (Development), step 6 of product-playbook — the checkpoint tester / development-complete gate.
  Verify that every core-scope feature is actually built, runs, and met its exit criteria + security
  definition-of-done, before moving to Testing. Use when you think development is done, or run
  /dev-check "is development complete", "checkpoint", "ready to test". Writes the Dev-complete section
  of PRODUCT.md. Run /test next.
---

# `/dev-check` — Phase 2 · Development ⑥ · run as an **engineer/tester**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per PRINCIPLES.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **exit-criteria are testable AND verified (not assumed)**,
> **security-in-DoD checked**, **honest gap surfacing**, **scope re-check**, **measure not assume**.

## Contract
- **Purpose:** prove development is actually complete before Testing — a real gate, not a vibe.
- **Reads:** `PRODUCT.md#Scope`, `#Plan`, `#Build log`, `#Foundation`, `#Contracts`.
- **Writes:** `PRODUCT.md#Dev-complete` — the checklist, each item checked **with evidence**.
- **Exit criteria:**
  - [ ] Every **core-scope** feature has a `#Build log` row, **runs**, and met its DoD (incl. security) — verified.
  - [ ] No hardcoding · prompts externalized · contracts typed · schema↔code consistent · builds/CI green.
  - [ ] No oversized god-files (single-responsibility held); secret-scan + dependency-vuln scan clean.
  - [ ] **Scope re-check:** nothing built that's in OUT-OF-SCOPE (no creep).
  - [ ] Every "done" has **HOW it was verified** recorded (evidence, not "done").
  - [ ] **(Lane mode — PRINCIPLES.md §Lane mode)** every `## Build log row` in `docs/features/*.md` is **reconciled into `#Build log`** (this is the spine's one writer), and the **cross-lane seams** — files two lanes both depend on through a contract — have an integration test that ran on the merged base.

## Step 0 — Context + prior-gate check
- Read `#Scope/#Plan/#Build log`. Cross-check the planned core features against what's actually in the build log.

## Step 1 — Apply principles (this phase)
- **Verify, don't assume:** re-run / re-check; "should pass" is not "passes". **Surface gaps honestly** — a half-done feature listed as done is the "thought it was done" trap.
- **Scope discipline:** anything built that's in OUT-OF-SCOPE is flagged as creep, not quietly accepted.

## Step 2 — Run the checkpoint
0. **Lane mode first — reconcile the spine.** Run this on the **base branch after the lane PRs merged**, not
   inside a worktree. For every `docs/features/*.md` whose `## Build log row` is not yet in `#Build log`,
   append it verbatim (feature · DoD met · how verified · date · ticket). `/build` could not write it from
   inside a lane; this is the single writer that keeps every lane PR clean of the spine.
1. **Coverage:** every core-scope feature present + runs (spot-run the live paths, compose `/verify`/`/run`).
2. **Quality bar:** no hardcoded values; prompts in `prompts/` YAML; contracts typed; schema↔code consistent; CI green.
3. **Security DoD:** each feature's security checks are actually present (not just promised) — for AI, prompt-injection defence exists.
4. **Scope re-check:** compare built features to OUT-OF-SCOPE; flag any creep. **Lane mode:** also compare
   `lanes.yaml` to `#Scope` — a lane that traces to no in-scope item is creep with a worktree attached.
5. **Evidence:** confirm each `#Build log` row records HOW it was verified.
6. **Lane mode — the seams:** each lane was verified alone by `/build`; nothing has yet run the paths that
   *cross* lanes (a `shared:` zone, a contract two lanes consume). Run the cross-layer verification ticket's
   integration tests on the merged base; a green lane is not a green product.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Dev-complete`: tick each box **only with evidence**; list any failing item explicitly.

## Step 3b — Principle-gate: phase-level verification (evidence)
Beyond ticking the per-feature boxes, do a phase-level check: compose a holistic **`/security-review`**
across the auth/data surface and confirm CI (the auto-layer) is green. Then **report a phase Confidence
Score (0–100%)** with one line each on solid / risky-untested / to-raise-it (per `PRINCIPLES.md`).
**If any box can't be ticked with evidence, the gate FAILS — STOP and report exactly what's missing;
do not hand off to Testing.** A failing checkpoint is the point of this skill.

## Step 4 — Handoff
"Development checkpoint passed (evidence recorded). Next run **`/test`** — unit, integration, regression,
and adversarial/security cases on the LIVE path."
