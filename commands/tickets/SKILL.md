---
name: tickets
description: >
  Phase 2 (Development), step 4b of product-playbook — bridges /contracts and /build. Two modes.
  Bare /tickets decomposes every milestone in PRODUCT.md#Plan into granular, single-responsibility
  developer tickets — sliced VERTICALLY (thin end-to-end increments, each demoable on merge) or
  HORIZONTALLY (one ticket per architectural layer: data · service · UI · tests), proposed per
  milestone and confirmed by you — each with exact target file paths, typed inputs/outputs and a
  security DoD, so they can be assigned to different developers and merged as isolated PRs.
  /tickets "<description>" instead logs ONE ad-hoc bug / edge case / tech debt item against the file
  that owns it, without touching the backlog. Provisions .github/ISSUE_TEMPLATE/, verifies the remote
  before publishing, never creates remote repositories, and skips tickets that already exist.
  Writes docs/issues/*.md.
---

# `/tickets` — Phase 2 · Development ④b · run as a **tech lead / project engineer**

> Part of **product-playbook**. Reads the project spine (`PRODUCT.md`, `STRUCTURE.md`, `#Contracts` — resolve per MECHANISMS.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing:
> **modular / single-responsibility** (one ticket = one concern), **layered & decoupled** (a ticket respects
> the layer boundaries even when it crosses them), **typed contracts** at every seam a ticket exposes,
> **security in the definition-of-done**, and **no hardcoding** (a ticket never asks for a baked-in
> endpoint, key or model name).
> **Companions — opened on demand, never up front:** `references/slicing.md` (Mode A: how each strategy splits a milestone, and what every ticket carries) · `references/publishing.md` (provisioning, the remote and capability guards, dedup, mirroring the plan onto GitHub).

## Contract
- **Purpose:** turn milestones into granular, independently assignable and independently mergeable tickets — sliced the way this milestone and this team actually need — and capture ad-hoc issues without derailing the backlog.
- **Reads:** `PRODUCT.md#Plan`, `#Contracts`, `#Architecture`, `STRUCTURE.md`, `DESIGN.md` (UI products only).
- **Writes:**
  - `docs/issues/*.md` — one file per ticket.
  - `.github/ISSUE_TEMPLATE/feature_ticket.md` and `.github/PULL_REQUEST_TEMPLATE.md` (scaffolded from bundled `templates/` if missing).
  - GitHub issues — **ONLY IF** a remote origin is verified and `gh` is authenticated.
- **Gate type:** `derivation` — computable from `#Plan` + `#Contracts`. Batchable - a `derivation` run may chain with its neighbours and end in ONE review. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes no spine section · `declined` ✓ · `override` ✓ · `superseded` n/a — writes `docs/issues/*`, not a spine section; a re-run skips tickets that already exist, so there is nothing in the spine to erase
- **Exit criteria:**
  - [ ] **Mode A:** every milestone in `#Plan` is decomposed into 2–4 tickets under a **stated slice strategy** (vertical or horizontal), recommended with a reason and **confirmed by the user** before anything is written.
  - [ ] Every ticket names **exact target file paths** (`src/services/quoteEngine.ts`), never a bare folder.
  - [ ] Every ticket states its **typed inputs and outputs** — the seam it owns.
  - [ ] Every ticket is **self-contained**: assignable to one developer and mergeable as an isolated PR.
  - [ ] **Vertical only:** every slice states what a reviewer **can see working** after it merges.
  - [ ] **Horizontal only:** no ticket lists files from two layers, and layers absent from `STRUCTURE.md` produce no ticket.
  - [ ] Every ticket carries a **DoD including security** (input validation, no swallowed errors, no secrets in source).
  - [ ] Ticket IDs are **globally unique** across milestones (`[M2-SLICE-01]`, `[M2-TICK-01]`), so dedup is reliable on re-run.
  - [ ] **Mode B:** an ad-hoc issue is filed against the owning file with a reproduction, and **no backlog ticket is created, renumbered or modified**.
  - [ ] **Pre-flight remote verification executed** — no remote repository is ever created.
  - [ ] **Lane mode** (MECHANISMS.md §Lane mode — Lanekeeper present): every ticket's Target Files include **everything the build writes** (feature doc + tests) and **never a spine file**; a horizontal strategy carries a **recorded reason**; the playbook's PR template is **not** written (Lanekeeper owns it).

## Step 0 — Context + prior-gate check
- Read `#Plan`, `#Contracts`, `#Architecture` and `STRUCTURE.md`. If `#Contracts` is empty, warn (tickets
  would invent their own types) but allow override.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then write `Override <date>: <reason> — bypassed <gate>` at the top of `#Plan` before continuing. Advancing on unmet criteria is the more consequential of warn-vs-override, so it is the one that leaves a trace: without it a later reader cannot tell a gate that held from a gate that was waved through.
- Brownfield: read the existing tree and `docs/issues/` first — extend the numbering, never restart it.
- **Dispatch on the argument — this is the whole mode decision:**
  - **No argument**, or a planning phrase (`"break down plan"`, `"decompose milestones"`, `"sprint backlog"`) → **Mode A** (Step 3A).
  - **`"vertical"` / `"horizontal"`** (alone or with a planning phrase) → **Mode A** with the strategy already chosen; skip the proposal.
  - **Any other free-text argument** describing a defect, gap or debt item → **Mode B** (Step 3B).
  - Ambiguous? Ask. Do **not** silently regenerate a backlog when the user meant to log one bug.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** this phase owns no spine section, so its trace is ONE dated line at the top of `docs/issues/README.md` (create it if absent) — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and no ticket files are written. A backlog that does not exist must still be distinguishable from one nobody ever attempted; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **One ticket = one concern.** Concern is *not* a synonym for layer. Vertically, the concern is one thin
  user-observable behaviour; horizontally, it is one layer of one milestone. Either way, if a reviewer would
  need to understand a second concern to approve the PR, the split is wrong.
- **The strategy is a per-milestone decision, not a house style.** An infrastructure milestone with no
  user-visible surface slices badly vertically; a user-facing milestone slices badly horizontally.
- **Every ticket declares the contract it exposes**, so dependent work can start against a stub rather than
  waiting for a merge. This is what makes either strategy parallelisable.
- **Security is not a ticket.** It is a DoD line on *every* ticket. Never emit an "add security" ticket.

## Step 2 — Provision templates + pre-flight remote guard (both modes)
**The four guards, one line each — the procedure behind all four is in `references/publishing.md` §Provision and pre-flight:**
1. **Templates — one master per file, never overwritten.** Copy the bundled issue template if the project has none; **in lane mode do not write a PR template** — Lanekeeper owns it (§Lane mode rule 4).
2. **Remote guard — NEVER blindly create a remote repository.** No remote, or `gh` not authenticated → write `docs/issues/` only and say so. **Do not run `gh repo create`.**
3. **Capability pre-flight — a half-published backlog is worse than none.** Issues, milestones and labels are separate permissions: check all three **before publishing anything**, then let the user choose degrade-with-a-warning or publish nothing.
4. **Dedup index + numbering.** Fetch the existing issues once and match by **ID tag** first, exact title second; skip a match and never edit or close it. Derive the next number from `docs/issues/` **and** that list together, so a re-run after a partial publish cannot reuse an ID.

## Step 3A — Mode A: batch milestone decomposition

### 3A.1 — Choose the slice strategy (propose, then STOP for confirmation)
Decide **per milestone**, not once for the repo. Read `STRUCTURE.md` and the milestone's deliverable, then
recommend one with a one-line reason and **wait for the user's yes**. If the invocation already named a
strategy, skip the proposal and go straight to 3A.2.

**The recommendation table and the lane-mode override are in `references/slicing.md` §Choose the strategy.**

State it like this, then stop:
> *Milestone 2 "Quote export" touches providers + services + UI. Recommending **vertical** (3 slices) — solo build, each slice demoable on merge. Proceed, or switch to horizontal?*

Record the chosen strategy in every ticket generated for that milestone, so a later reader knows why the backlog is shaped the way it is.

### 3A.2 — Slice the milestone, then fill every ticket
**Load `references/slicing.md`** — **§Vertical slicing** or **§Horizontal slicing** for the strategy just confirmed, then **§Per-ticket content** for what every ticket must carry.

Write each ticket to `docs/issues/<id>_<slug>.md`, then publish the non-duplicates with `gh issue create`.

**Publishing mirrors the plan's own structure** — milestone → lane label → ticket, each created idempotently so a second `/tickets` run adds no duplicate milestone, label or issue. Procedure: `references/publishing.md` §Mirror the plan structure onto GitHub.

## Step 3B — Mode B: ad-hoc issue capture
Triggered mid-build by `/tickets "Bug: Gemini API timeout is unhandled on slow 3G"`. **Fast path — touch nothing else.**
1. **Classify** the text: `bug` · `edge-case` · `tech-debt` · `security`. Security items are never downgraded.
2. **Locate the owning file** via `STRUCTURE.md` + the architecture: the example above is an LLM provider
   concern → `src/providers/llm/geminiProvider.ts`. Confirm the path exists; if you cannot resolve one
   confidently, say so and record the candidates rather than guessing a path into the ticket.
3. **Write one ticket** `[ADHOC-<nn>]` into `docs/issues/` using the same template, filling: what happened ·
   expected vs actual · reproduction or trigger condition · affected file(s) · suspected cause · a DoD that
   includes a **regression test proving the fix**.
4. **Publish** it as a single issue with the classification as a label, subject to the same dedup and remote
   guards from Step 2, **plus a real parent reference**: resolve the parent ticket's *issue number* from the
   dedup index already fetched in Step 2 and write `#N`, so GitHub renders the bidirectional timeline link.
   **A parent with no published issue degrades to the plain ID with the reason stated — never a guessed
   number**, which would link the bug to an unrelated issue.
5. **Do not** read `#Plan`, regenerate, renumber or modify any milestone ticket. One invocation, one issue.

## Step 3b — Principle-gate: verify the tickets hold (evidence)
Walk the principles and prove each against the files just written — do not assert it:
- **Strategy was confirmed**, not assumed, and is recorded on every ticket of that milestone.
- **Every path resolves.** Check each target path against the real tree (or against `STRUCTURE.md` for a
  not-yet-created file). A ticket pointing at a directory, or at a path this project will never have, fails.
- **Vertical:** every slice names an observable outcome. **A slice whose Demo field says "n/a" is a layer
  wearing a slice's ID — STOP and re-slice, or switch that milestone to horizontal.**
- **Vertical:** slice 1 runs end to end on its own. If it needs slice 2 to do anything, the order is wrong.
- **Horizontal:** no ticket lists files from two layers; no layer-3 ticket exists when `STRUCTURE.md`
  declares no component directory; layer 4 contains no per-layer unit tests.
- **IDs unique.** Every ID appears exactly once across `docs/issues/` and the fetched GitHub issues.
- **Dedup ran.** Confirm `gh issue list` was fetched before any `gh issue create`, and that no remote
  repository was created.
- **Structure mirrored + idempotent.** Every published ticket carries its milestone and its `lane: <name>`
  label; a second run created no duplicate milestone, label or issue (**re-run it and show that**); no link
  points at a feature doc that does not exist yet; permissions were checked **before** the first create.
- **Security DoD present** on every ticket, including the ad-hoc ones.
- **Independently mergeable.** For each ticket ask: could one developer open a PR containing only these
  files and have it reviewed on its own? **If not, the split is wrong — STOP and re-split before publishing.**
- **Lane mode:** no ticket lists a spine file; every ticket lists its feature doc and tests; two tickets that
  name the same file are either **dependants through a contract** (fine — `Depends On` says so) or a
  **collision** (STOP: re-split, or name the shared file so Lanekeeper can declare it a `shared:` zone).
  A horizontal milestone has its reason recorded. No `PULL_REQUEST_TEMPLATE.md` was written.

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and end with a suggested one-line commit message in the repo's convention. Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal.

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Plan` milestones, `#Scope` non-goals and `#Contracts` types — a ticket that builds a non-goal, or names a type the contracts don't define. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Backlog decomposed — each ticket assignable to a different developer and mergeable on its own. Vertical
slices go in order (slice 1 is the walking skeleton); horizontal tickets go contract-first (layer 1 → 2 → 3,
tests alongside). Run **`/build`** on the first ticket, one ticket per session. In lane mode, hand the
tickets to Lanekeeper (`lanekeeper start` / `spawn --ticket <n>`) — each ticket's file list is its lane."
