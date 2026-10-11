# Slicing a milestone into tickets — Mode A mechanics

> Loaded by `/tickets` **Step 3A**, on demand. `SKILL.md` owns the mode dispatch and the
> stop-for-confirmation gate; this file owns *how* each strategy actually splits a milestone and what
> goes inside every ticket. Mode B (ad-hoc capture) never loads it.

## §Lanes are modules — group first, slice second

**Never assume one builder.** A backlog written as one chain gives a second person, or a second agent, nothing
to start until the first finishes; a backlog grouped by module costs a solo builder nothing (every seat is
theirs), and a lane can be handed to a friend or a second agent without re-planning. (case file: The
fifteen-step recipe)

1. **A lane is a module.** One lane per module folder `STRUCTURE.md` draws (`queue/`, `parties/`), named after
   the folder. Layered shape (no module folders) → one lane per feature, and say so. **A lane is never a
   technology layer** (`backend`, `ui`).
2. **Every ticket carries `Lane` (its module) and `Owner`** — the role that owns the lane, `Senior` unless round 1
   named a Junior lane. Owner follows the files, not the difficulty.
3. **Order inside a lane, parallel across lanes.** A lane's tickets are ordered by `Depends On`; lanes run side
   by side. A ticket that needs another lane's ticket is a **coordination point** in `TICKETS.md`, of one of two
   kinds (§Waiting or building against) - the script writes them from each ticket's depends and builds.
4. **Hub files.** A file named by tickets in two or more lanes (the route registry, the config loader, the
   dependency manifest) is a **hub file**: list it under hubs, so `/build` treats a change there as a one-line
   merge. A one-line registry `STRUCTURE.md` names under `## Hub files` is normal, however many there are. A hub
   file is a **structure finding** — say so, and point at `/structure` — only when a ticket needs more than a
   one-line change there, or `STRUCTURE.md`'s `## Hub files` does not name it (`set` warns), or a handler/store
   folder is shared by every module.
5. **The parallel table** (lane · owner · seat · epics · which lanes run at once) is in `TICKETS.md` and the
   close: the answer to "can two people work on this?", before anyone asks.

The plan lives in `TICKETS.md` (`tickets-md.md`); the live map is the **Delivery Board** (`publishing.md` §The
Delivery Board), where `Status` moves — never in `TICKETS.md`.

## §Epics — milestone → epic → ticket

The tickets of a milestone are grouped the way a product team writes them: **group by module, slice by visible
behaviour, assign by role.** **Every milestone is ticketed in one run** (owner, 2026-10-08): the full lane and
seat plan for the whole product is the point; ticketing only the next milestone was proposed and declined.

1. **An epic is one feature of one milestone, inside one lane**, so its owner is the lane's owner. A feature
   that needs two modules is two epics joined by a coordination point — never one epic in two lanes. A
   milestone may hold several epics in one lane.
2. **Epic-scoped IDs.** An epic gets a short uppercase code (`PARTY` for *Parties join the list*), unique in
   its milestone: the epic is `[M<milestone>-<EPIC>]`, its tickets `[M<milestone>-<EPIC>-<nn>]` from `01` in
   build order. The pair keeps every ID unique, which is what dedup matches on. `SLICE`, `TICK` (a backlog
   published before epics, `publishing.md` §An earlier backlog) and `ADHOC` (Mode B) are never an epic code.
3. **A re-run keeps every code**: an epic in `TICKETS.md` or on GitHub keeps its code and numbering; a new
   ticket takes the next free `nn` across `docs/issues/` and the fetched issues (a second code for one epic
   publishes a duplicate epic).
4. **An epic is a GitHub parent issue, its tickets its sub-issues** (`publishing.md` §Epics are parent issues);
   past GitHub's 100 sub-issues, split the epic.
5. **The close shows the hierarchy:** milestone, each epic (ID · name · lane · owner), its tickets in order;
   every epic of a milestone uses that milestone's strategy.

## §Waiting or building against — the two kinds of dependency

A ticket needs another ticket in one of two ways, and the difference decides who can start on day one:
- **`Depends On` — wait for the merge.** The ticket needs the other's code merged: it calls a function or
  route that exists only after that merge, edits a file the other creates, or its Demo shows the other's
  behaviour running. It becomes a GitHub *blocked by* link, `/build` will not start it while the blocker is
  open, and `TICKETS.md` draws it as a **solid arrow**.
- **`Builds against` — the contract only.** Every name it uses from the other ticket already resolves in the
  files `#Contracts` names, so a stub typed from those contracts is enough to build, test and demo it. It is
  written on the ticket and in `TICKETS.md`, drawn as a **dotted arrow**, and is **not** a *blocked by* link:
  a link would make `/build` stop a ticket that is free to start. The two run side by side, so the stub lives
  in the ticket's own Target Files, and a file both tickets write makes it a `Depends On` or a hub file.
- **When unsure, it is `Depends On`.** A needless wait only delays a start; a wrong "build against" costs a
  rewrite when the real code lands.

## §Choose the strategy — the recommendation table

Decide **per milestone**, not once for the repo — and always *inside* the lanes above. It is not a house
style: an infrastructure milestone with no user-visible surface slices badly vertically, and a user-facing
milestone slices badly horizontally.

| Recommend | When |
|---|---|
| **Vertical** (default lean) | The milestone has a user-visible surface · one full-stack codebase · early product where "show it working" matters. Each slice stays inside one lane where it can. |
| **Horizontal** | A milestone that is mostly infrastructure with no user-visible surface · contracts already frozen in `#Contracts`, so layers can safely run in parallel. |

Under the printed proposal, state the recommendation in one line, then stop:
> *Lanes: parties (1 epic) · queue (1) · notify (1). M1 touches providers + services + UI — recommending
> **vertical** (8 slices, each inside its epic's lane). The list above is what gets written. Proceed, or
> switch to horizontal?*

## §Size by behaviour — the count follows, it is never a cap

A fixed number of tickets per milestone forces bundling: a real milestone with seven behaviours squeezed
into four tickets produces "admin edits a project and archives it and removes a member" — three reviews in
one PR, and a longer dependency chain for everyone waiting on it. So size each ticket, and let the count
fall out:

1. **No count limit.** A milestone gets as many tickets as it has behaviours — two or twelve.
2. **One ticket = one behaviour a user can see · one build session · one PR readable in about fifteen
   minutes.** Fail any one and the ticket is too big.
3. **The "and" test.** A title with "and" in it is usually two tickets — "create a quote and email it" is
   *create a quote* · *email a quote*. Split it, or keep it and say in one line why the two cannot ship
   apart (a delete that is meaningless without its confirm dialog). The proposal flags every such title.
4. **No layer halves.** Split by behaviour, never by layer: "quote API" + "quote screen" is one behaviour
   cut in two, neither half demoable. (Horizontal milestones keep their own one-layer rule, §Horizontal.)
5. **The floor.** Never smaller than one visible behaviour — every `/build` session pays a fixed overhead
   (reading the ticket, branch, gate, review, PR) of roughly twenty minutes, so a helper, a config key or a copy
   tweak as its own ticket pays that cost for nothing a user can see. Fold it into the behaviour that needs it.

How to find the behaviours: walk the feature from the user's side, one verb per ticket, inside its lane —
a **quotes** lane might be *create a quote* · *edit a draft* · *send a quote* · *refuse an expired quote*;
an **auth** lane *sign up* · *log in* · *log out* · *reset password* · *admin invites a member*. Refusals and
empty states that a user meets are behaviours too; security is still a DoD line on every ticket, never its
own ticket.

## §Vertical slicing (thin end-to-end increments)
Split the milestone into **one slice per user-observable behaviour** (§Size by behaviour), each going through
whatever layers it needs. ID: epic-scoped, `[M<milestone>-<EPIC>-<nn>]` (§Epics).

Split along one of these seams — pick the one that yields the thinnest first slice:
- **By user action** — "create a quote" · "export it" · "email it".
- **By happy path, then edges** — slice 1 is the path that works; slice 2 adds the failure and empty states.
- **By input variant** — one supported format first, the rest after.
- **By surface depth** — read-only view first, then the write path.

Rules that keep a slice honest:
- **Slice 1 is the walking skeleton** — the thinnest path that runs end to end. It may be ugly; it must work.
- **A slice that no one can see is not a slice.** "Build the data model" is a layer, not a slice. If a slice
  has no observable outcome, it belongs in a horizontal split instead.
- A slice crosses layers **by design**, but still respects them: vendor SDKs stay behind adapters, business
  logic stays out of components.
- Each slice's DoD carries the tests for the layers it touched — **there is no separate test slice**.

## §Horizontal slicing (one ticket per architectural layer)
ID: epic-scoped, `[M<milestone>-<EPIC>-<nn>]` (§Epics) — the layer tickets of one milestone form one epic in one lane.

| # | Layer | Home (per `STRUCTURE.md`) | The ticket owns |
|---|---|---|---|
| 1 | 📦 Storage / data provider | `src/providers/…`, `src/domain/…` | Typed schema models, persistence adapter, migration. Vendor SDKs stay behind the adapter interface. |
| 2 | ⚙️ Pure domain service | `src/services/…` | Business logic, state transitions, validation workflow. Depends on layer 1 **only through its typed contract**. |
| 3 | 🎨 UI component | `src/components/features/…` | One isolated component: interactive states, accessibility, `DESIGN.md` tokens. No business logic. |
| 4 | 🧪 Cross-layer verification | `tests/integration/…`, `tests/security/…` | The **integration test across the real seam** and the **adversarial/security cases** — the tests that belong to no single layer. |

**Emit only the layers the project has.** Read the directories `STRUCTURE.md` actually declares:
- Backend / API / CLI product (no `src/components/`) → layers 1, 2, 4 — **three tickets, no UI ticket**.
- Frontend-only product (no `src/providers/`) → layers 2, 3, 4.
- Full-stack → all four.
- Never invent a directory to justify a ticket. A ticket pointing at a path the project does not have is a bug.
- **Unit tests are not layer 4.** Each layer ticket's DoD covers its own unit tests. Layer 4 is only what
  cannot live in one layer — otherwise it becomes a dumping ground and the same work is counted twice.

## §Per-ticket content (both strategies)
What each ticket's entry in the fields file carries — `set tickets filled --from-fields` renders it into the
`feature_ticket.md` template's shape:
- **ID + title:** `[M<milestone>-<EPIC>-<nn>]` (§Epics), then the concern in plain words.
  The `M<milestone>-<EPIC>` prefix is what keeps IDs unique across milestones; without it, dedup misfires on re-run.
- **Epic:** `[M<milestone>-<EPIC>] <epic name>` — published as this ticket's parent issue.
- **Lane:** the module this ticket lives in (`parties`, `notify`) — §Lanes are modules — never a layer.
  Every ticket of an epic shares its lane; horizontal: all of a milestone's layer tickets share one lane.
- **Owner:** the role that owns the lane — `Senior` unless the board says otherwise.
- **Target files:** exact paths, derived from `STRUCTURE.md` — `src/services/quoteEngine.ts`, not `src/services/`.
  **The list is the boundary**, so it must name **everything `/build` will write**: the code, its tests, *and*
  `docs/features/<feature>.md`. **Never list `PRODUCT.md`, `CHANGELOG.md`, `STRUCTURE.md` or `TICKETS.md`** —
  the spine and the plan are shared — each phase writes its own rows, and a ticket never lists them.
- **Exit criterion:** the `#Plan` exit criterion it serves, by the number the start prints (`M1.2`).
- **Inputs → outputs:** the typed contract this ticket consumes and the one it exposes, named from `#Contracts`.
- **Depends on:** the ticket IDs whose *merge* it waits for (§Waiting or building against) — each becomes a
  *blocked by* link. `None` is a valid answer.
- **Builds against:** the ticket IDs whose *contract* it uses before they merge — a stub is enough to start,
  so this is not a link. `#Contracts` is frozen before `/tickets` runs, so a need on another ticket's types
  alone belongs here. `None` is a valid answer.
- **Demo (vertical):** what a reviewer can see working once this merges. Required on every slice.
- **Implementation tasks:** concrete, ordered, checkable steps — inside this ticket's concern only.
- **DoD (security included):** inputs validated at the boundary · no secrets in source (`.env` only) · no
  swallowed errors, fallbacks fail-closed on auth/security · structured logging, no stray prints ·
  tests written and passing for everything this ticket touches · feature doc updated.
- **Verification command:** the exact command a reviewer runs to see it work.

`set` writes each to `docs/issues/<id>_<slug>.md`, then the plan to `TICKETS.md` (`tickets-md.md`), verifies, and only
then the engine publishes the non-duplicates with `gh issue create`, each ticket file as its body, unchanged (`publishing.md`
§An issue body is its ticket file).

