---
name: tickets
description: >
  Phase 2 (Development), step 4b of product-playbook — bridges /contracts and /build. Bare /tickets
  turns every milestone in PRODUCT.md#Plan into small, independently mergeable tickets — grouped into
  MODULE LANES (one per STRUCTURE.md module, ordered inside, parallel across) with an Owner, sliced
  VERTICALLY (thin end-to-end increments) or HORIZONTALLY (one ticket per layer), proposed and
  confirmed by you — each with exact file paths, typed in/out and a security DoD, filed on a Delivery
  Board (Status · Owner · Lane · Seat) so one person or four can take the same backlog. /tickets
  "<description>" logs ONE ad-hoc bug / edge case / tech debt item against the file that owns it.
  Provisions the issue template, verifies the remote, never creates a remote repo, skips existing
  tickets. Writes docs/issues/*.md.
---

# `/tickets` — Phase 2 · Development ④b · run as a **tech lead / project engineer**

> Part of **product-playbook**. Reads the project spine (`PRODUCT.md`, `STRUCTURE.md`, `#Contracts` — resolve per MECHANISMS.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing:
> **modular / single-responsibility** (one ticket = one concern), **layered & decoupled** (a ticket respects
> the layer boundaries even when it crosses them), **typed contracts** at every seam a ticket exposes,
> **security in the definition-of-done**, and **no hardcoding** (a ticket never asks for a baked-in
> endpoint, key or model name).
> **Companions — opened on demand, never up front:** `references/slicing.md` (lanes, strategies, what every ticket carries) · `references/publishing.md` (provisioning, guards, dedup, GitHub mirroring, the Delivery Board).

## Contract
- **Purpose:** turn milestones into granular, independently assignable and independently mergeable tickets — grouped by module lane so the backlog **never assumes one builder** — and capture ad-hoc issues without derailing the backlog.
- **Reads:** `PRODUCT.md#Plan`, `#Contracts`, `#Architecture`, `STRUCTURE.md`, `DESIGN.md` (UI products
  only) — **and the files `#Contracts` names** (schemas, route table, db schema): `#Contracts` is a *record
  that* the types were frozen and *where*; it never contains them (`MECHANISMS.md` §Follow the pointer).
- **Writes:**
  - `docs/issues/*.md` — one file per ticket.
  - `.github/ISSUE_TEMPLATE/feature_ticket.md` and `.github/PULL_REQUEST_TEMPLATE.md` (scaffolded from bundled `templates/` if missing).
  - GitHub issues + milestones + labels + the **Delivery Board** — **ONLY IF** a remote origin is verified and `gh` is authenticated.
- **Gate type:** `derivation` — computable from `#Plan` + `#Contracts`. Batchable - a `derivation` run may chain with its neighbours and end in ONE review. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes no spine section · `declined` ✓ · `override` ✓ · `superseded` n/a — writes `docs/issues/*`, not a spine section; a re-run skips tickets that already exist, so there is nothing in the spine to erase
- **Exit criteria:**
  - [ ] **Mode A:** every milestone in `#Plan` is decomposed into **as many tickets as it has visible behaviours — no count cap** — under a **stated slice strategy** (vertical or horizontal), recommended with a reason and **confirmed against the proposal SHOWN in full** (every ticket: ID · title · lane · owner; a title with "and" flagged); a set that changes after the yes is shown and confirmed again.
  - [ ] **Lanes are modules** (`references/slicing.md`): every ticket carries `Lane` = a `STRUCTURE.md` module and an `Owner`; ordered inside a lane, parallel across; `docs/issues/README.md` carries the parallel table, coordination points and hub files.
  - [ ] **Filed on the Delivery Board** (`references/publishing.md`): every issue is a card with **Status, Owner, Lane, Seat** set and **read back**; labels `lane: <name>` + `owner: <role>`; no `project` scope → said in the close with the command that grants it, never half-stamped.
  - [ ] **Every `Depends On` is a GitHub *blocked by* link, read back** (`references/publishing.md` §Mirror the plan structure, *Dependencies*): prose in a body is not a dependency; a re-run adds the links an earlier publish left out.
  - [ ] Every ticket names **exact target file paths** (`src/services/quoteEngine.ts`), never a bare folder.
  - [ ] Every ticket states its **typed inputs and outputs** — the seam it owns — and **every type, route,
    field and event name it uses RESOLVES to a real symbol** in the files `#Contracts` names, checked by
    grep: a name that does not resolve is a typo or an invention, and both stop the run.
  - [ ] **Every milestone produces tickets or a recorded reason why not** — a milestone whose deliverable is
    *evidence* (a measurement, a session, a decision) gets the ticket that captures it, or one line in
    `docs/issues/README.md` saying why it was skipped.
  - [ ] Every ticket is **self-contained**: assignable to one developer and mergeable as an isolated PR.
  - [ ] **Vertical only:** every slice states what a reviewer **can see working** after it merges.
  - [ ] **Horizontal only:** no ticket lists files from two layers, and layers absent from `STRUCTURE.md` produce no ticket.
  - [ ] Every ticket carries a **DoD including security** (input validation, no swallowed errors, no secrets in source).
  - [ ] Ticket IDs are **globally unique** across milestones (`[M2-SLICE-01]`, `[M2-TICK-01]`), so dedup is reliable on re-run.
  - [ ] **Mode B:** an ad-hoc issue is filed against the owning file with a reproduction, and **no backlog ticket is created, renumbered or modified**.
  - [ ] **Pre-flight remote verification executed** — no remote repository is ever created.

## Step 0 — Context + prior-gate check
- Read `#Plan`, `#Contracts`, `#Architecture` and `STRUCTURE.md`. **Then open the schema files
  `#Contracts` points at and read the real types, routes and enums** — a presence check cannot tell
  *contracts were used* from *contracts were ignored*, and the second is what happens. If `#Contracts` is
  empty, warn (tickets would invent their own types) but allow override; if it names files that do not
  exist, **stop** — that is drift, not a missing section.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then write `Override <date>: <reason> — bypassed <gate>` at the top of `#Plan` before continuing. Without it a later reader cannot tell a gate that held from a gate that was waved through.
- Brownfield: read the tree and `docs/issues/` first — extend the numbering, never restart it.
- **Dispatch on the argument — this is the whole mode decision:** no argument or a planning phrase
  (`"break down plan"`, `"sprint backlog"`) → **Mode A** (3A); `"vertical"` / `"horizontal"` → Mode A with the
  strategy chosen; any other free text describing a defect, gap or debt item → **Mode B** (3B). Ambiguous?
  Ask — never regenerate a backlog when the user meant to log one bug.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** this phase owns no spine section, so its trace is ONE dated line at the top of `docs/issues/README.md` (create it if absent) — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and no ticket files are written; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **One ticket = one concern; size by behaviour, never by count** (`references/slicing.md` §Size by behaviour).
  Vertically: one behaviour a user can see · one build session · one PR readable in about fifteen minutes —
  a milestone gets as many as it has. A title with "and" is usually two tickets; a layer half is never a
  ticket; never smaller than one visible behaviour. Horizontally: one layer of one milestone.
- **Never assume one builder.** Group by module first (§Lanes are modules), slice second: solo means every
  seat is the user's, and a lane can be handed to a friend or a second agent without re-planning.
- **The strategy is a per-milestone decision, not a house style.** An infrastructure milestone with no
  user-visible surface slices badly vertically; a user-facing milestone slices badly horizontally.
- **Every ticket declares the contract it exposes**, so dependent work can start against a stub rather than
  waiting for a merge.
- **Security is not a ticket** — a DoD line on *every* ticket; never emit an "add security" ticket.

## Step 2 — Provision templates + pre-flight remote guard (both modes)
**The four guards, one line each — procedure in `references/publishing.md` §Provision and pre-flight:**
1. **Templates — one master per file, never overwritten.** Copy the bundled issue and PR templates if the project has none.
2. **Remote guard — NEVER blindly create a remote repository.** No remote, or `gh` not authenticated → write `docs/issues/` only and say so. **Do not run `gh repo create`.**
3. **Capability pre-flight — a half-published backlog is worse than none.** Issues, milestones, labels and the board (`project` scope) are separate permissions: check all four **before publishing anything**, then let the user choose degrade-with-a-warning or publish nothing.
4. **Dedup index + numbering.** Fetch the existing issues once; match by **ID tag** first, exact title second; skip a match, never edit or close it. Next number = `docs/issues/` **and** that list together, so a partial publish cannot reuse an ID.

## Step 3A — Mode A: batch milestone decomposition

### 3A.1 — Group into lanes, choose the strategy, SHOW the proposal, then STOP
**Load `references/slicing.md`.** Derive the lanes from `STRUCTURE.md` (§Lanes are modules), decide the
strategy **per milestone** (§Choose the strategy), then **print the whole proposal** — every ticket as
`ID · title · lane · owner · depends on`, grouped by lane, one behaviour per ticket, **any title containing
"and" flagged** (a warning to split or justify, not a block), with the parallel table — and **wait for the
user's yes**. A yes is a yes to the list shown: a ticket added, dropped or merged afterwards is shown and
confirmed again. (case file: Confirmed as proposed, never shown)
If the invocation named a strategy, skip the strategy question, not the list.

State it like this, then stop:
> *Lanes: events (2) · claims (4) · board (3). M2 touches providers + services + UI — recommending **vertical** (3 slices, each inside one lane). The list above is what gets written. Proceed, or switch to horizontal?*

Record the strategy on every ticket of that milestone.

### 3A.2 — Slice the milestone, then fill every ticket
**`references/slicing.md`** — **§Vertical slicing** or **§Horizontal slicing** for the strategy just confirmed, then **§Per-ticket content**. Write each ticket to `docs/issues/<id>_<slug>.md`. **Then verify — and only then publish.**

**Local files are the reversible draft; `gh issue create` is the irreversible step** — run Step 3b over
the written files before anything leaves the machine. (case file: Eleven issues against an invented API)

Then publish the non-duplicates. **Publishing mirrors the plan's own structure** — milestone (with its
`#Plan` date on `due_on`) → `lane:` + `owner:` labels → ticket → **its `Depends On` as *blocked by*
links** → **a card on the Delivery Board with Status, Owner, Lane and Seat set and read back** — each
created idempotently, so a second run adds no duplicate milestone, label, board field, link or issue.
Procedure: `references/publishing.md` §Mirror the plan structure onto GitHub and §The Delivery Board.

## Step 3B — Mode B: ad-hoc issue capture
Triggered mid-build by `/tickets "Bug: Gemini API timeout is unhandled on slow 3G"`. **Fast path —
touch nothing else; read `references/adhoc-capture.md` first.** One invocation, one issue: classify
(`bug`·`edge-case`·`tech-debt`·`security`, never downgraded) → locate the owning file and its lane from
`STRUCTURE.md` → write one `[ADHOC-<nn>]` ticket → publish it under the Step 2 guards with a real parent
`#N`, its lane and owner, and its board card. **Never** read `#Plan`, regenerate, renumber or touch a
milestone ticket.

## Step 3b — Principle-gate: verify the tickets hold (evidence)
**Load `references/verification.md` and run every check in it — over the LOCAL files, before you publish.**
First the symbol check (**every type, route, field and event name resolves** in the files `#Contracts`
names), then the rest; nothing reaches `gh issue create` until it is green.

**Keep the context lean** (`MECHANISMS-ON-DEMAND.md` §Context hygiene): long output to a scratch file; grep the verdict, cite the file.

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and **offer to commit the change** (`MECHANISMS.md` §Commit the work — check the repo exists, name the branch, offer the message, push only if a remote exists and the user says so). Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal. **Close in plain language** (`MECHANISMS.md` §Plain-language close): two or three sentences of *what just happened* with no playbook dialect, then a numbered *what YOU do next* — the user's own actions, dated where they are time-bound, or "Nothing — you're done".

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Plan` milestones, `#Scope` non-goals and `#Contracts` types — a ticket that builds a non-goal, or names a type the contracts don't define. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Backlog grouped into lanes and on the board — each ticket mergeable on its own, each lane workable by
one person or agent. Inside a lane the tickets go in order (slice 1 is the walking skeleton; horizontal
tickets contract-first); lanes run side by side. Alone? Every seat is yours — run **`/build`** on the
first ticket, one ticket per session. With help, set the board's Seat per lane and hand it over — a card
that reads *Blocked by #n* is not startable until #n closes."
