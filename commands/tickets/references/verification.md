# Verifying the backlog — the full list, run BEFORE anything is published

> Opened by /tickets at Step 3b. **Every check here runs over `docs/issues/*.md` while they are still
> local files.** Local is the reversible draft; `gh issue create` is the irreversible step, and a
> backlog that is complete, confident and wrong is worse than a half-published one.

## §Resolve every symbol first

**Grep each backticked type, route, field, enum value and event name in every ticket against the files
`#Contracts` names** (`src/schemas/*`, the route table, the db schema). A name that does not resolve is a
typo or an invention; both stop the run. This one check turns eight of the nine defects from the real
failure into a hard red before anything is written to GitHub — including `costUsd: number` where the
frozen field is `costMinor` (an integer), a `status: "draft"` outside the `open | finalized` enum, an
event outside the closed `EVENT_TYPES` tuple, and ten response types that existed nowhere.

**Resolve against the contract files OR a path some ticket's Target Files creates; then plant one invented
name and watch it fail.** A component the backlog itself creates is not an invention — without that list the
check drowns real misses in false positives, and a checker never seen failing proves nothing. (case file: The checker that cried wolf)

## §The rest of the gate

Walk the principles and prove each against the files just written — do not assert it:
- **Strategy was confirmed**, not assumed, and is recorded on every ticket of that milestone — and **the set
  confirmed is the set published**: the proposal shown before the yes listed every ticket (ID · title ·
  lane · owner), and any ticket added, dropped or renamed after that yes was shown again and re-confirmed.
  (case file: Confirmed as proposed, never shown)
- **Lanes are modules.** Every ticket's `Lane` is a module folder `STRUCTURE.md` draws (or a feature, with
  the layered-shape reason recorded) and every ticket carries an `Owner`; `docs/issues/README.md` carries
  the parallel table (lane · owner · tickets in order · lanes that can run at once · hub files) and every
  cross-lane dependency as a coordination point. A backlog whose lanes form one chain across modules, or
  whose hub-file list has three or more entries, is reported as such — never published silently.
- **Every path resolves.** Check each target path against the real tree (or against `STRUCTURE.md` for a
  not-yet-created file). A ticket pointing at a directory, or at a path this project will never have, fails.
- **Every path is writable under the project's import rules.** For each ticket, name the cross-folder imports
  its Target Files imply (a page calling another lane's `api`, an adapter reusing another lane's constants) and
  check them against `STRUCTURE.md` §Dependency rules — or run its lane checker on a stub; a ticket that can only
  be built by breaking a rule is re-pathed before publishing. (case file: The ticket the lane checker refused)
- **Vertical:** every slice names an observable outcome. **A slice whose Demo field says "n/a" is a layer
  wearing a slice's ID — STOP and re-slice, or switch that milestone to horizontal.**
- **Vertical:** slice 1 runs end to end on its own. If it needs slice 2 to do anything, the order is wrong.
- **Horizontal:** no ticket lists files from two layers; no layer-3 ticket exists when `STRUCTURE.md`
  declares no component directory; layer 4 contains no per-layer unit tests.
- **Every `#Plan` item has a home: a ticket, or a named later phase with its sequence point.** Items a phase
  owns (real-environment tests → `/test`, hosting → `/deploy`) get one line in `docs/issues/README.md` saying
  when that phase runs — never a ticket, never silence. (case file: The tests that fell between phases)
- **IDs unique.** Every ID appears exactly once across `docs/issues/` and the fetched GitHub issues.
- **Dedup ran.** Confirm `gh issue list` was fetched before any `gh issue create`, and that no remote
  repository was created.
- **Structure mirrored + idempotent.** Every published ticket carries its milestone, its `lane: <name>` and
  its `owner: <role>` label; a second run created no duplicate milestone, label, board field or issue
  (**re-run it and show that**); no link points at a feature doc that does not exist yet; permissions —
  `project` scope included — were checked **before** the first create.
- **The board reads back set.** Every published issue is a card on the Delivery Board and
  `gh project item-list --format json` shows Status, Owner, Lane and Seat set on each (lowercase keys); the
  close states the count. No board (scope missing) → the close says so and names the command that grants it.
- **Dependencies are links, read back.** For every published issue, `GET …/dependencies/blocked_by`
  returns exactly the issue numbers its `Depends On` names — closed ones included, none extra — and the
  close states the count (`13 issues · 15 links`). Before trusting the read-back, remove one link, watch
  the check go red, and put it back (`DELETE …/blocked_by/<id>`): a read-back never seen failing proves
  nothing. A body that says *Depends On* with an empty `blocked_by` is the failure this check exists for.
  (case file: Written down, never linked)
- **Security DoD present** on every ticket, including the ad-hoc ones.
- **Independently mergeable.** For each ticket ask: could one developer open a PR containing only these
  files and have it reviewed on its own? **If not, the split is wrong — STOP and re-split before publishing.**
- **Lane mode:** no ticket lists a spine file; every ticket lists its feature doc and tests; two tickets that
  name the same file are either **dependants through a contract** (fine — `Depends On` says so) or a
  **collision** (STOP: re-split, or name the shared file so Lanekeeper can declare it a `shared:` zone).
  A horizontal milestone has its reason recorded. No `PULL_REQUEST_TEMPLATE.md` was written.
