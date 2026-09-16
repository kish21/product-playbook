# Verifying the backlog — before publishing, then the read-backs after

> Opened by /tickets at Step 3b. **Two halves, run in order, every check in both.**
> **§Before publishing** runs over `docs/issues/*.md` and `TICKETS.md` while they are still local files. Local is the
> reversible draft; `gh issue create` is the irreversible step, and a backlog that is complete, confident and
> wrong is worse than a half-published one. Nothing is published until every check in this half is green.
> **§After publishing** holds the read-backs. They check what GitHub now holds, so they can only run
> once the issues exist — never read them as a reason to stop before publishing. A local-only run (no remote,
> or `gh` not authenticated) publishes nothing: it skips this half and says in the close that the read-backs
> did not run and why.

## §Before publishing — over the local files

### §Resolve every symbol first

**Read the real schema files before writing a ticket, not only this check after.** A presence check cannot
tell *contracts were used* from *contracts were ignored*, and the second is what happens.

**Grep each backticked type, route, field, enum value and event name in every ticket against the files
`#Contracts` names** (`src/schemas/*`, the route table, the db schema). A name that does not resolve is a
typo or an invention; both stop the run. This one check turns eight of the nine defects from the real
failure into a hard red before anything is written to GitHub — including `costUsd: number` where the
frozen field is `costMinor` (an integer), a `status: "draft"` outside the `open | finalized` enum, an
event outside the closed `EVENT_TYPES` tuple, and ten response types that existed nowhere.

**Resolve against the contract files OR a path some ticket's Target Files creates; then plant one invented
name and watch it fail.** A component the backlog itself creates is not an invention — without that list the
check drowns real misses in false positives, and a checker never seen failing proves nothing. (case file: The checker that cried wolf)

### §The rest of the gate

Walk the principles and prove each against the files just written — do not assert it:
- **Strategy was confirmed**, not assumed, and is recorded on every ticket of that milestone — and **the set
  confirmed is the set published**: the proposal shown before the yes listed every epic and every ticket
  (ID · title · lane · owner), and any ticket added, dropped or renamed after that yes was shown again and re-confirmed.
  (case file: Confirmed as proposed, never shown)
- **Lanes are modules.** Every ticket's `Lane` is a module folder `STRUCTURE.md` draws (or a feature, with
  the layered-shape reason recorded) and every ticket carries an `Owner`; `TICKETS.md` carries
  the parallel table (lane · owner · tickets in order · lanes that can run at once · hub files) and every
  cross-lane dependency as a coordination point. A backlog whose lanes form one chain across modules, or
  whose hub-file list has three or more entries, is reported as such — never published silently.
- **Every ticket sits in one epic, in its epic's lane, under an epic-scoped ID.** Each epic is one feature of
  one milestone in one lane; every new ID reads `M<n>-<EPIC>-<nn>` with a code unique inside its milestone
  and not `SLICE`, `TICK` or `ADHOC`; a published old-style ID was kept, never renamed (`slicing.md` §Epics).
- **`TICKETS.md` is the plan, never the status** (`tickets-md.md`). It holds every epic, the parallel table,
  every coordination point, the hub files, the flow graph and the day-1 table, and **no** status column,
  checkbox, done mark or progress count. Every *waits for* point is its ticket's `Depends On`; every *builds
  against* point is its ticket's `Builds against`. The graph has one box per lane and no other boxes, a solid
  arrow for each *waits for* and a dotted one for each *builds against*, in the shapes `tickets-md.md` shows.
  No day-1 ticket has a `Depends On`. No `docs/issues/README.md` remains beside it.
- **Every path resolves.** Check each target path against the real tree (or against `STRUCTURE.md` for a
  not-yet-created file). A ticket pointing at a directory, or at a path this project will never have, fails.
- **Vertical:** every slice names an observable outcome. **A slice whose Demo field says "n/a" is a layer
  wearing a slice's ID — STOP and re-slice, or switch that milestone to horizontal.**
- **Vertical:** slice 1 runs end to end on its own. If it needs slice 2 to do anything, the order is wrong.
- **Horizontal:** no ticket lists files from two layers; no layer-3 ticket exists when `STRUCTURE.md`
  declares no component directory; layer 4 contains no per-layer unit tests.
- **Every `#Plan` item has a home: a ticket, or a named later phase with its sequence point.** Items a phase
  owns (real-environment tests → `/test`, hosting → `/deploy`) get one line in `TICKETS.md` saying
  when that phase runs — never a ticket, never silence. (case file: The tests that fell between phases)
- **IDs unique.** Every epic and ticket ID appears exactly once across `docs/issues/`, `TICKETS.md`'s epics
  and the fetched GitHub issues.
- **Dedup ran.** Confirm `gh issue list` was fetched before any `gh issue create`, and that no remote
  repository was created.
- **Every ticket file is its issue body.** No file in `docs/issues/` opens with front matter, and each is
  published with `--body-file` as it stands (`publishing.md` §An issue body is its ticket file) — a body made any
  other way reads as edited on GitHub to every later regroup and path sync.
- **Security DoD present** on every ticket, including the ad-hoc ones.
- **Independently mergeable.** For each ticket ask: could one developer open a PR containing only these
  files and have it reviewed on its own? **If not, the split is wrong — STOP and re-split before publishing.**
- **No ticket lists a spine file or `TICKETS.md`; every ticket lists its feature doc and tests.** Two
  tickets that name the same file are either **dependants through a merge** (fine — `Depends On` orders them)
  or a **collision** — a `Builds against` pair runs side by side, so a file both write is a collision too
  (STOP: re-split, or list the file as a hub file).

## §After publishing — the read-backs

Run once `/tickets` has published; each one reads GitHub back rather than trusting what was sent.
- **Structure mirrored + idempotent.** Every published ticket carries its milestone, its `lane: <name>` and
  its `owner: <role>` label; a second run created no duplicate milestone, label, epic, board field or issue
  (**re-run it and show that**); no link points at a feature doc that does not exist yet; permissions —
  `project` scope included — were checked **before** the first create.
- **Epics are parents, read back.** Every epic in `TICKETS.md` is one issue, and
  `GET …/issues/<epic n>/sub_issues` returns exactly the tickets listed under it — none extra, and none missing
  except a ticket this run found under a different parent and left there, which the close names for the owner
  to regroup — and the close states the count (`3 epics · 8 sub-issues`). The re-run
  above added no second epic and no second parent link. Before trusting the read-back, remove one sub-issue,
  watch the check go red, and attach it again (`DELETE …/sub_issue`): a read-back never seen failing proves
  nothing. (`publishing.md` §Epics are parent issues)
- **Bodies are their files, read back.** Every ticket issue this run created or edited returns, as its body, the
  version of its ticket file it was written from (`gh issue view <n> --json body`) — an epic has no ticket file
  and is read back by *Epics are parents* — compared as `publishing.md` §A path rewrite reaches GitHub compares;
  the close states the count (`13 bodies · 13 equal`). Before trusting it, compare one body with a different
  ticket's file and watch it fail: a read-back never seen failing proves nothing.
- **The board reads back set.** Every published ticket issue is a card on the Delivery Board and
  `gh project item-list --format json` shows Status, Owner, Lane and Seat set on each (lowercase keys); the
  close states the count. No board (scope missing) → the close says so and names the command that grants it.
- **Dependencies are links, read back.** For every published issue, `GET …/dependencies/blocked_by`
  returns exactly the issue numbers its `Depends On` names — closed ones included, none extra — and the
  close states the count (`13 issues · 15 links`). Before trusting the read-back, remove one link, watch
  the check go red, and put it back (`DELETE …/blocked_by/<id>`): a read-back never seen failing proves
  nothing. A body that says *Depends On* with an empty `blocked_by` is the failure this check exists for.
  (case file: Written down, never linked)
