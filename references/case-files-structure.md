# Case files — `/structure`

War stories behind the rules in `commands/structure/references/*.md`. Each heading is pointed to from its rule.

## The drawers everyone reached into

**Potluck live run, 2026-09-12 → 13.** `/structure` chose domain modules and drew them: `events/`,
`claims/`, `board/`, `activity/`, `retention/`. It also drew `http/` for *every* module's handlers,
`platform/` for *every* module's stores, and one `index.ts` that wired the lot; the frontend was
`pages/ components/ api/ lib/` — by tool throughout. Every gate passed: the map matched the tree both ways.
One phase later, `/tickets` named `backend/src/index.ts` in seven of fifteen tickets, `GuestBoardPage.tsx`
in five, `route.ts` and the config loader in four each. The owner asked whether two people could take
the backlog. Whichever way the tickets were grouped, the answer was no — because the folders each
person would change were the shared ones. A module that keeps its rules but sends its routes, its
store and its tests to communal folders is by-role in name and by-tool where it matters: in the files
two people edit at once. The fix is not in `/tickets`; it is one registry line per module and everything
else inside the module's own folder.

## The move that came a phase late

**Potluck live run, 2026-09-13.** The finding above was recorded by `/tickets` "for a later `/structure`
session", with the owner's condition: worth doing only if a second builder joins, and then before the
next ticket. The same day, `/structure` was re-run on the filled section. It showed three options with
their costs — restructure now, keep the shape and record the deviation with a `## Hub files` section, or
backend only — and the owner chose the full move: 55 files, every module now holding its handlers, store
and tests, one `module.ts` call per lane in a `compose.ts` composition root, the frontend regrouped the
same way. Behaviour and the API contract did not change (the OpenAPI document and the generated types
were byte-identical; 214 tests passed before and after).

Three things the skill did not say had to be discovered on the way. **First**, thirteen open tickets
named exact paths — including files they *planned* to create (`http/claim-handlers.ts`,
`components/ClaimForm.tsx`) — and every one now pointed at a folder the move had emptied; had the next
`/build` session followed its ticket, it would have put the claim handlers back in `http/` and the
by-tool layout would have returned one file at a time. The re-run therefore owns the ticket paths: a
mapping of old to new for existing *and* planned files, applied to `docs/issues/*.md`, plus the one
ticket whose single handler file split across two lanes (host edit/delete → `events/`, remove-claim-as-
host → `claims/`), and the finding itself marked acted on. **Second**, moving `http/event-handlers.ts`
into `events/` silently turned two legal imports (`board/assemble`, `board/wire`) into a lane-to-lane
arrow, and `http/host-handlers.ts` moving into `board/` turned its `eventLinks` import into the arrow
back — a two-way dependency between lanes on the first commit of the layout whose rule was "one arrow,
one way". `check_structure.py` compares folders and could not see it; the code review did. The fix was
to move the URL helper to `http/` (owned by no lane), hand the board projection to the events lane as a
function from the composition root, and add an import-graph check (`scripts/check-lanes.mjs`) to the same
`pnpm run structure` gate, so the dependency rule is a test rather than three sentences. **Third**, the
new `## Hub files` check read *every* backticked string under the heading as a path, so the first draft's
prose (`/tickets`, `shared:`) failed the gate — the template now reads only the first backticked token of
each table row or list item.
