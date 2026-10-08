---
name: tickets
description: >
  Phase 2 (Development), step 4b of product-playbook — bridges /contracts and /build. Bare /tickets
  turns every milestone in PRODUCT.md#Plan into EPICS of small, independently mergeable tickets — grouped
  into MODULE LANES (one per STRUCTURE.md module, ordered inside, parallel across) with an Owner, sliced
  VERTICALLY (thin end-to-end increments) or HORIZONTALLY (one ticket per layer), proposed and
  confirmed by you — each with exact file paths, typed in/out and a security DoD, filed as parent issues +
  sub-issues on a Delivery Board (Status · Owner · Lane · Seat) so one person or four
  can take the same backlog. /tickets "<description>" logs ONE ad-hoc bug / edge case / tech debt item
  against the file that owns it. Provisions the issue template, verifies the remote, never creates a remote
  repo, skips existing tickets. Writes TICKETS.md (the plan) + docs/issues/*.md.
---

# `/tickets` — Phase 2 · Development ④b · run as a **tech lead / project engineer**

> Part of **product-playbook**. Reads the project spine (`PRODUCT.md`, `STRUCTURE.md`, `#Contracts` — resolve per MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **This skill's OWN reference files are a DIFFERENT folder:** `references/` beside this SKILL.md (`commands/tickets/references/`: `adhoc-capture.md` · `publishing.md` · `slicing.md` · `tickets-md.md` · `verification.md`), never the plugin-root `references/`.
> **`status.py rules tickets` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it). Load-bearing:
> **modular / single-responsibility** (one ticket = one concern), **layered & decoupled** (a ticket respects
> the layer boundaries even when it crosses them), **typed contracts** at every seam a ticket exposes,
> **security in the definition-of-done**, and **no hardcoding** (a ticket never asks for a baked-in
> endpoint, key or model name).
> **The start prints what a step needs from them** (or says to run `status.py rules tickets`); one more `§` a step names: `status.py section <path> "<§>"`.

## Contract
- **Purpose:** turn milestones into granular, independently assignable and independently mergeable tickets — grouped by module lane so the backlog **never assumes one builder** — and capture ad-hoc issues without derailing the backlog.
- **Reads:** `PRODUCT.md#Plan`, `#Contracts`, `#Architecture`, `STRUCTURE.md`, `DESIGN.md` (UI products
  only) — **and the files `#Contracts` names** (schemas, route table, db schema): `#Contracts` is a *record
  that* the types were frozen and *where*; it never contains them, so the start prints the names those files define.
- **Writes:**
  - `docs/issues/*.md` — one file per ticket; root **`TICKETS.md`** — the plan, never status.
  - `.github/ISSUE_TEMPLATE/feature_ticket.md` and `.github/PULL_REQUEST_TEMPLATE.md` (scaffolded from bundled `templates/` if missing).
  - GitHub issues (epics as parents) + milestones + labels + the **Delivery Board** — **ONLY IF** a remote origin is verified and `gh` is authenticated.
- **Checked by `status.py set tickets filled`, not by reading** (the start prints the list; `--dry-run` shows the gaps): exact files, feature doc and tests · a `STRUCTURE.md` lane, an Owner · a security line · `Depends On` exists, no cycle · consumed names in the code or a `(new)` · no two tickets of a milestone writing one file unordered · every milestone ticketed or explained · `TICKETS.md`'s lane boxes, no status, day 1 waits for nothing.
- **Gate type:** `derivation` — computable from `#Plan` + `#Contracts`. Batchable - a `derivation` run may chain with its neighbours and end in ONE review. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes no spine section · `declined` ✓ · `override` ✓ · `superseded` n/a — writes `TICKETS.md` + `docs/issues/*`; a re-run skips tickets that already exist, so there is nothing in the spine to erase
- **Exit criteria:**
  - [ ] **Mode A:** every milestone is decomposed **milestone → epic → ticket** (`references/slicing.md` §Epics), into **as many tickets as it has visible behaviours — no count cap** — under a **stated slice strategy** (vertical or horizontal), recommended with a reason and **confirmed against the proposal SHOWN in full** (every epic and ticket: ID · title · lane · owner; a title with "and" flagged); a set that changes after the yes is shown and confirmed again.
  - [ ] **Lanes are modules** (`references/slicing.md`): every ticket carries `Lane` = a `STRUCTURE.md` module and an `Owner`; ordered inside a lane, parallel across; root `TICKETS.md` (`references/tickets-md.md`) carries the plan — epics, the parallel table, coordination points, hub files, a Mermaid lane flow graph (one box per lane; solid arrow = wait for the merge, dotted = build against the contract) and the day-1 table — and **never a status**; no `docs/issues/README.md` remains.
  - [ ] **Epics are parent issues** (`references/publishing.md` §Epics are parent issues): each epic is published as a GitHub parent issue with its tickets as sub-issues, **read back**; a re-run creates **no duplicate epic or link**.
  - [ ] **Filed on the Delivery Board** (`references/publishing.md`): every ticket issue is a card with **Status, Owner, Lane, Seat** set and **read back**; labels `lane: <name>` + `owner: <role>`; no `project` scope → said in the close with the command that grants it, never half-stamped.
  - [ ] **Every `Depends On` is a GitHub *blocked by* link, read back** (`references/publishing.md` §Mirror the plan structure, *Dependencies*): prose in a body is not a dependency; a re-run adds the links an earlier publish left out; a `Builds against` is never linked.
  - [ ] Every ticket names **exact target file paths** (`src/services/quoteEngine.ts`), never a bare folder.
  - [ ] Every ticket states its **typed inputs and outputs** — the seam it owns — and **every type, route,
    field and event name it uses RESOLVES to a real symbol** in the files `#Contracts` names, checked by
    `set`: a name that does not resolve is a typo or an invention, and both stop the run.
  - [ ] **Every milestone produces tickets or a recorded reason why not** — a milestone whose deliverable is
    *evidence* (a measurement, a session, a decision) gets the ticket that captures it, or one line in
    `TICKETS.md` saying why it was skipped.
  - [ ] Every ticket is **self-contained**: assignable to one developer and mergeable as an isolated PR.
  - [ ] **Vertical only:** every slice states what a reviewer **can see working** after it merges.
  - [ ] **Horizontal only:** no ticket lists files from two layers, and layers absent from `STRUCTURE.md` produce no ticket.
  - [ ] Every ticket carries a **DoD including security** (input validation, no swallowed errors, no secrets in source).
  - [ ] Ticket IDs are **globally unique and epic-scoped** — `[M1-DISC-03]` is milestone · epic · number, its epic `[M1-DISC]` — so dedup is reliable on re-run.
  - [ ] **Mode B:** an ad-hoc issue is filed against the owning file with a reproduction, and **no backlog ticket is created, renumbered or modified**.
  - [ ] **Pre-flight remote verification executed** — no remote repository is ever created.

## Step 0 — Context + prior-gate check
- **First turn, ONE command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase tickets`.** It prints `#Plan`, `#Scope`'s lines, **the real types, routes and tables the `#Contracts` files define** (`references/verification.md` §Resolve every symbol first), the lanes, the remote, the rounds, the ticket shape and what `set` refuses: open none of those files. Show its first line. `#Contracts` empty: warn (tickets would invent their own types), the user may override; naming files that do not exist: **stop** — drift.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words** (the start prints the question), say it will be written down — then record it — `status.py bypass --from tickets --gate <gate> --reason "<the user's own words>"` (`MECHANISMS.md` §Status) — before continuing.
- Brownfield: the start lists `TICKETS.md` and `docs/issues/` — extend the numbering, keep every epic code, migrate an old plan file (`references/publishing.md` §An earlier backlog).
- **Dispatch on the argument — this is the whole mode decision:** no argument or a planning phrase
  (`"break down plan"`, `"sprint backlog"`) → **Mode A** (3A); `"vertical"` / `"horizontal"` → Mode A with the
  strategy chosen; any other free text describing a defect, gap or debt item → **Mode B** (3B). Ambiguous?
  Ask — never regenerate a backlog when the user meant to log one bug.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** `status.py set tickets declined --reason "<what was missing>" --gate <the phase(s) that fill it>` (`MECHANISMS.md` §Status) — and no ticket files are written; the next attempt **replaces** the note.

## Step 1 — Apply principles (this phase)
- **One ticket = one concern; size by behaviour, never by count** (`references/slicing.md` §Size by behaviour).
  Vertically: one behaviour a user can see · one build session · one PR readable in about fifteen minutes —
  a milestone gets as many as it has. A title with "and" is usually two tickets; a layer half is never a
  ticket; never smaller than one visible behaviour. Horizontally: one layer of one milestone.
- **Never assume one builder: milestone → epic → ticket — group by module, slice by visible behaviour, assign
  by role** (§Lanes are modules, §Epics). **The strategy is chosen per milestone** (§Choose the strategy).
- **Every ticket declares the contract it exposes**, so dependent work can start against a stub rather than
  waiting for a merge — a `Builds against`, never a `Depends On` (§Waiting or building against).
- **Security is not a ticket** — a DoD line on *every* ticket; never emit an "add security" ticket.

## Step 2 — Provision templates + pre-flight remote guard (both modes)
**The four guards, one line each — procedure in `references/publishing.md` §Provision and pre-flight:**
1. **Templates — one master per file, never overwritten.** Missing: the start prints the copy commands.
2. **Remote guard — NEVER blindly create a remote repository.** No remote, or `gh` not authenticated → write the local files only and say so. **Do not run `gh repo create`.**
3. **Capability pre-flight — a half-published backlog is worse than none.** Issues, milestones, labels and the board (`project` scope) are separate permissions: the engine checks all four **before publishing anything** (exit 2, nothing written); the user chooses degrade-with-a-warning or publish nothing.
4. **Dedup index + numbering.** The engine fetches the existing issues once, never truncated; matches epics and tickets by **exact ID tag** first, exact title second; skips a match; never closes it, edit only by its exceptions. Next number = `docs/issues/` **and** that list together, so a partial publish cannot reuse an ID.

## Step 3A — Mode A: batch milestone decomposition

### 3A.1 — Round 1 asks, round 2 SHOWS the proposal, then STOP
**Round 1 — the start's numbered questions in ONE message** (who builds: alone or 2-10 seats · the strategy
per milestone, §Choose the strategy · owners · publishing, when a remote exists · each decision a ticket needs
that no section records), each with your recommendation; a decision never asked is never taken.
**Round 2 — ONE message:** derive the lanes from `STRUCTURE.md` (§Lanes are modules) and the epics inside
them (§Epics), then **print the whole proposal** — milestone → epic → ticket, every ticket as `ID · title ·
lane · owner · depends on · builds against`, one behaviour per ticket, **any title containing "and" flagged**
(a warning to split or justify, not a block), with the parallel table and the day-1 rows — and offer two
options: *Looks good - write and save* / *Change something*. A yes is a yes to the list shown: a ticket
added, dropped or merged afterwards is shown and confirmed again. (case file: Confirmed as proposed, never shown)
If the invocation named a strategy, skip the strategy question, not the list.

Record the strategy on every ticket of that milestone.

### 3A.2 — Slice the milestone, fill every ticket, write the plan
After the yes, few calls (several files each): the ticket files `docs/issues/<id>_<slug>.md` in the
template's shape the start printed (**§Vertical slicing** / **§Horizontal slicing** / **§Per-ticket content**
of `references/slicing.md` by `§` when the template leaves a field open), then the root `TICKETS.md` in `references/tickets-md.md`'s shape,
then **`status.py set tickets filled --commit "<one line>"`**: it runs Step 3b's §Before publishing half in
code, every problem in one refusal (`--dry-run` lists them first), and saves only when all pass.

**Local files are the reversible draft; `gh issue create` is the irreversible step** — nothing is
published before that save. (case file: Eleven issues against an invented API)

Then publish the non-duplicates **in the order `references/publishing.md` §Mirror the plan structure onto
GitHub gives** — milestones → labels → **epic parent issues** → tickets → **parent and *blocked by* links** →
**board cards with all four fields** — each read back and created idempotently: a second run adds no duplicate.

**Publish with the engine, never by hand.** Write the CONFIRMED proposal to `<scratch>/plan.json` (format in
the start), then run ONE command:
`python "${CLAUDE_PLUGIN_ROOT}/commands/tickets/publish.py" <scratch>/plan.json` (`--no-board` only when the
user chose issues without the board). It publishes in that order, reads every part back, watches each
read-back go red once, and plans a second run that must create nothing. **Its printed `OK`/`FAIL` lines are
§After publishing's evidence — quote them in the close.** Exit 1 → name the failed line and stop, never
publish again to make it pass; exit 2 → it refused before writing anything, say why.

## Step 3B — Mode B: ad-hoc issue capture
**Fast path — open `references/adhoc-capture.md` and follow it (classify, owning file and lane, parent `#N`,
board card); touch nothing else.** One invocation, one issue. **Never** read `#Plan`, regenerate, renumber,
touch a milestone ticket or epic, or edit `TICKETS.md`.

## Step 3b — Principle-gate: verify the tickets hold (evidence)
**`references/verification.md`, in its two halves.** §Before publishing runs over the LOCAL files: `set
tickets filled` runs its countable checks in code, the symbol check first; the judged ones stay yours, over
the files you wrote — strategy confirmed against the list shown, every ticket independently mergeable,
slice 1 runs end to end, a horizontal ticket one layer. §After publishing holds the read-backs, which the
engine runs once the issues exist (a local-only run skips them and says so).

**Keep the context lean** (`MECHANISMS-ON-DEMAND.md` §Context hygiene): long output to a scratch file; grep the verdict, cite the file.

**Close the loop (`MECHANISMS.md` §Step 3b):** `set tickets filled --commit` records the state (`MECHANISMS.md` §Status) and saves on round 2's yes — no git call of your own (`MECHANISMS.md` §Commit the work; no yes yet: leave `--commit` out and ask *"Save this version of your project? (yes / no)"*) — then prints the rest of the close in order: reconcile against `#Vision` (surface a contradiction, never write over it), Step 3c, **the transition guard** (`MECHANISMS.md` §Step 3b, item 4: a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not). **Close in plain language** (`MECHANISMS.md` §Plain-language close): four blocks in order, each under its bolded name: **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next** (ends with the handoff `set` printed).

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, against decisions **already recorded** — `#Plan` milestones, `#Scope` non-goals, `#Contracts` types (`set` names them). On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or a dated `superseded by` line in the earlier section) — never both standing. Added detail is not a contradiction.

## Step 4 — Handoff
"Backlog grouped into epics and lanes, planned in `TICKETS.md` and on the board — each ticket mergeable on
its own; inside a lane in order, lanes side by side. Alone? Every seat is yours — run **`/build`** on the
first ticket, one ticket per session. With help, give each seat its row of the day-1 table and set its Seat
on the board — a card that reads *Blocked by #n* is not startable until #n closes."
