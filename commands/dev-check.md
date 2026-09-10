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
- **If `#Build log` is empty, this checkpoint is premature** — there is nothing built to check. Warn and
  offer `/build` first (allow override): a checkpoint run over an empty log passes by having nothing to
  fail, which is the opposite of a gate.
- **An override is RECORDED, never a verbal "yes"** (`PRINCIPLES.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then write `Override <date>: <reason> — bypassed <gate>` at the top of `#Dev-complete` before continuing. Advancing on unmet criteria is the more consequential of warn-vs-override, so it is the one that leaves a trace: without it a later reader cannot tell a gate that held from a gate that was waved through.
- **If the gate is unmet and the run stops here, record that it stopped (`PRINCIPLES.md` §Declined runs):** write ONE dated line at the top of `#Dev-complete` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

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

**Close the loop (`PRINCIPLES.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and end with a suggested one-line commit message in the repo's convention.

## Step 3c — Contradiction check (before the gate closes)
Per `PRINCIPLES.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Scope`'s core list against `#Build log` — a feature marked done that scope never asked for, or a scoped feature quietly dropped. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Development checkpoint passed (evidence recorded). Next run **`/test`** — unit, integration, regression,
and adversarial/security cases on the LIVE path."
