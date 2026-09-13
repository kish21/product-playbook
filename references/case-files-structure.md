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
