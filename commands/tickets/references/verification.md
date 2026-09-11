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

## §The rest of the gate

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
