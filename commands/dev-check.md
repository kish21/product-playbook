---
name: dev-check
description: >
  Phase 2 (Development), step 6 of product-builder — the checkpoint tester / development-complete gate.
  Verify that every core-scope feature is actually built, runs, and met its exit criteria + security
  definition-of-done, before moving to Testing. Use when you think development is done, or run
  /dev-check "is development complete", "checkpoint", "ready to test". Writes the Dev-complete section
  of PRODUCT.md. Run /test next.
---

# `/dev-check` — Phase 2 · Development ⑥ · run as an **engineer/tester**

> Part of **product-builder**. Reads + updates the shared spine `PRODUCT.md`.
> Apply `PRINCIPLES.md` — load-bearing: **exit-criteria are testable AND verified (not assumed)**,
> **security-in-DoD checked**, **honest gap surfacing**, **scope re-check**, **measure not assume**.

## Contract
- **Purpose:** prove development is actually complete before Testing — a real gate, not a vibe.
- **Reads:** `PRODUCT.md#Scope`, `#Plan`, `#Build log`, `#Foundation`, `#Contracts`.
- **Writes:** `PRODUCT.md#Dev-complete` — the checklist, each item checked **with evidence**.
- **Exit criteria:**
  - [ ] Every **core-scope** feature has a `#Build log` row, **runs**, and met its DoD (incl. security) — verified.
  - [ ] No hardcoding · prompts externalized · contracts typed · schema↔code consistent · builds/CI green.
  - [ ] **Scope re-check:** nothing built that's in OUT-OF-SCOPE (no creep).
  - [ ] Every "done" has **HOW it was verified** recorded (evidence, not "done").

## Step 0 — Context + prior-gate check
- Read `#Scope/#Plan/#Build log`. Cross-check the planned core features against what's actually in the build log.

## Step 1 — Apply principles (this phase)
- **Verify, don't assume:** re-run / re-check; "should pass" is not "passes". **Surface gaps honestly** — a half-done feature listed as done is the "thought it was done" trap.
- **Scope discipline:** anything built that's in OUT-OF-SCOPE is flagged as creep, not quietly accepted.

## Step 2 — Run the checkpoint
1. **Coverage:** every core-scope feature present + runs (spot-run the live paths, compose `/verify`/`/run`).
2. **Quality bar:** no hardcoded values; prompts in `prompts/` YAML; contracts typed; schema↔code consistent; CI green.
3. **Security DoD:** each feature's security checks are actually present (not just promised) — for AI, prompt-injection defence exists.
4. **Scope re-check:** compare built features to OUT-OF-SCOPE; flag any creep.
5. **Evidence:** confirm each `#Build log` row records HOW it was verified.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Dev-complete`: tick each box **only with evidence**; list any failing item explicitly.

## Step 3b — Self-verify (completeness gate)
**If any box can't be ticked with evidence, the gate FAILS — STOP and report exactly what's missing;
do not hand off to Testing.** A failing checkpoint is the point of this skill.

## Step 4 — Handoff
"Development checkpoint passed (evidence recorded). Next run **`/test`** — unit, integration, regression,
and adversarial/security cases on the LIVE path."
