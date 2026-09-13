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
- **Reads:** `PRODUCT.md#Plan`, `#Contracts`, `#Architecture`, `STRUCTURE.md`, `DESIGN.md` (UI products
  only) — **and the files `#Contracts` names** (`src/schemas/*`, the route table, the db schema).
  `#Contracts` is a *record that* the types were frozen and *where*; it never contains them
  (`MECHANISMS.md` §Follow the pointer).
- **Writes:**
  - `docs/issues/*.md` — one file per ticket.
  - `.github/ISSUE_TEMPLATE/feature_ticket.md` and `.github/PULL_REQUEST_TEMPLATE.md` (scaffolded from bundled `templates/` if missing).
  - GitHub issues — **ONLY IF** a remote origin is verified and `gh` is authenticated.
- **Gate type:** `derivation` — computable from `#Plan` + `#Contracts`. Batchable - a `derivation` run may chain with its neighbours and end in ONE review. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes no spine section · `declined` ✓ · `override` ✓ · `superseded` n/a — writes `docs/issues/*`, not a spine section; a re-run skips tickets that already exist, so there is nothing in the spine to erase
- **Exit criteria:**
  - [ ] **Mode A:** every milestone in `#Plan` is decomposed into 2–4 tickets under a **stated slice strategy** (vertical or horizontal), recommended with a reason and **confirmed by the user** before anything is written.
  - [ ] Every ticket names **exact target file paths** (`src/services/quoteEngine.ts`), never a bare folder.
  - [ ] Every ticket states its **typed inputs and outputs** — the seam it owns — and **every type, route,
    field and event name it uses RESOLVES to a real symbol** in the files `#Contracts` names. Checked by
    grep, not by reading: a name that does not resolve is a typo or an invention, and both stop the run.
  - [ ] **Every milestone produces tickets or a recorded reason why not.** A milestone whose deliverable is
    *evidence* (a measurement, a user session, a decision) is the one that silently produces none — write
    the ticket that captures the evidence, or one line in `docs/issues/README.md` saying which milestone
    was skipped and why. Zero tickets and zero trace is indistinguishable from an oversight.
  - [ ] Every ticket is **self-contained**: assignable to one developer and mergeable as an isolated PR.
  - [ ] **Vertical only:** every slice states what a reviewer **can see working** after it merges.
  - [ ] **Horizontal only:** no ticket lists files from two layers, and layers absent from `STRUCTURE.md` produce no ticket.
  - [ ] Every ticket carries a **DoD including security** (input validation, no swallowed errors, no secrets in source).
  - [ ] Ticket IDs are **globally unique** across milestones (`[M2-SLICE-01]`, `[M2-TICK-01]`), so dedup is reliable on re-run.
  - [ ] **Mode B:** an ad-hoc issue is filed against the owning file with a reproduction, and **no backlog ticket is created, renumbered or modified**.
  - [ ] **Pre-flight remote verification executed** — no remote repository is ever created.
  - [ ] **Lane mode** (MECHANISMS.md §Lane mode — Lanekeeper present): every ticket's Target Files include **everything the build writes** (feature doc + tests) and **never a spine file**; a horizontal strategy carries a **recorded reason**; the playbook's PR template is **not** written (Lanekeeper owns it).

## Step 0 — Context + prior-gate check
- Read `#Plan`, `#Contracts`, `#Architecture` and `STRUCTURE.md`. **Then open the schema files
  `#Contracts` points at and read the real types, routes and enums** — a presence check cannot tell
  *contracts were used* from *contracts were ignored*, and the second is what happens. If `#Contracts` is
  empty, warn (tickets would invent their own types) but allow override; if it names files that do not
  exist, **stop** — that is drift, not a missing section.
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

Write each ticket to `docs/issues/<id>_<slug>.md`. **Then verify — and only then publish.**

**Local files are the reversible draft; `gh issue create` is the irreversible step.** Run Step 3b's
checks over the written files *before* anything leaves the machine: the skill's own rule — *a
half-published backlog is worse than none* — applies harder to a **complete, confident and wrong** one.
A real run published 11 issues against an invented API and corrected them 22 minutes later; on a team
the window is not 22 minutes, it is *until someone reads them*, and **nothing notifies a reader that
every issue they saw was rewritten**.

Then publish the non-duplicates with `gh issue create`. **Publishing mirrors the plan's own structure** —
milestone → lane label → ticket, each created idempotently so a second `/tickets` run adds no duplicate
milestone, label or issue. **A milestone carries its target date from `#Plan` onto the GitHub milestone's
`due_on`** — dropping it lands every milestone undated, which is the one field a milestone view sorts by.
Procedure: `references/publishing.md` §Mirror the plan structure onto GitHub.

## Step 3B — Mode B: ad-hoc issue capture
Triggered mid-build by `/tickets "Bug: Gemini API timeout is unhandled on slow 3G"`. **Fast path —
touch nothing else, and read `references/adhoc-capture.md` before writing anything.** One invocation,
one issue: classify (`bug`·`edge-case`·`tech-debt`·`security`, never downgraded) → locate the owning
file from `STRUCTURE.md` → write one `[ADHOC-<nn>]` ticket into `docs/issues/` → publish it under the
Step 2 dedup + remote guards with a real parent `#N`. **Never** read `#Plan`, regenerate, renumber or
touch a milestone ticket.

## Step 3b — Principle-gate: verify the tickets hold (evidence)
**Load `references/verification.md` and run every check in it — over the LOCAL files, before you publish.**
It starts with the one that matters most: **every type, route, field and event name a ticket uses must
resolve to a real symbol** in the files `#Contracts` points at. The rest proves slicing, paths, IDs,
dedup, the security DoD, independent mergeability and the lane rules. Nothing reaches `gh issue create`
until it is green.

**Keep the context lean (`MECHANISMS-ON-DEMAND.md` §Context hygiene):** a command's output longer than a screen goes to a scratch file; read the tail or grep the verdict, and cite the file in the evidence line.

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and **offer to commit the change** (`MECHANISMS.md` §Commit the work — check the repo exists, name the branch, offer the message, push only if a remote exists and the user says so). Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal. **Close in plain language** (`MECHANISMS.md` §Plain-language close): two or three sentences of *what just happened* with no playbook dialect, then a numbered *what YOU do next* — the user's own actions, dated where they are time-bound, or "Nothing — you're done".

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Plan` milestones, `#Scope` non-goals and `#Contracts` types — a ticket that builds a non-goal, or names a type the contracts don't define. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Backlog decomposed — each ticket assignable to a different developer and mergeable on its own. Vertical
slices go in order (slice 1 is the walking skeleton); horizontal tickets go contract-first (layer 1 → 2 → 3,
tests alongside). Run **`/build`** on the first ticket, one ticket per session. In lane mode, hand the
tickets to Lanekeeper (`lanekeeper start` / `spawn --ticket <n>`) — each ticket's file list is its lane."
