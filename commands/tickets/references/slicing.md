# Slicing a milestone into tickets — Mode A mechanics

> Loaded by `/tickets` **Step 3A**, on demand. `SKILL.md` owns the mode dispatch and the
> stop-for-confirmation gate; this file owns *how* each strategy actually splits a milestone and what
> goes inside every ticket. Mode B (ad-hoc capture) never loads it.

## §Lanes are modules — group first, slice second

**Never assume one builder.** A backlog written as one chain — every ticket needing the one before it —
gives a second person, or a second agent, nothing to start until the first finishes; and a backlog grouped
by module costs a solo builder nothing, because solo simply means every seat is theirs. So the grouping
is always there, and the user decides per lane who sits in it. (case file: The fifteen-step recipe)

1. **A lane is a module.** Read the module folders `STRUCTURE.md` draws (`events/`, `claims/`, `board/`)
   and make one lane per module, named after the folder. Layered shape (no module folders) → one lane per
   feature, and say so. **A lane is never a technology layer** (`backend`, `ui`).
2. **Every ticket carries `Lane` (its module) and `Owner`** — the role that owns the lane, `Senior` by
   default; the user re-assigns lanes to `Junior` on the board, never in the tickets. Owner follows the
   files, not the difficulty.
3. **Order inside a lane, parallel across lanes.** The tickets of one lane are ordered by `Depends On`;
   two lanes may run side by side. Where a ticket in lane X needs a ticket in lane Y first, write it as a
   **coordination point** in `docs/issues/README.md` — *"claims #8 starts after board #6 merges"* — not
   only inside the ticket.
4. **Hub files.** A file named by tickets in two or more lanes (the route registry, the config loader, the
   dependency manifest) is a **hub file**: list them in `docs/issues/README.md` so `/build` treats a change
   there as a one-line merge. Three or more hub files, or a
   handler/store folder shared by every module, is a structure finding — say so, and point at `/structure`.
5. **The parallel table** goes into `docs/issues/README.md` and into the close: lane · owner · tickets in
   order · which lanes can run at once · hub files. That table is the answer to "can two people work on
   this?", and it must exist before anyone asks.

The live map is the **Delivery Board** (`publishing.md` §The Delivery Board): Lane and Owner are also
board fields, `Seat` is the chair actually working (a person or an agent instance, one by default), and
`Status` moves as work happens.

## §Choose the strategy — the recommendation table

Decide **per milestone**, not once for the repo — and always *inside* the lanes above.

| Recommend | When |
|---|---|
| **Vertical** (default lean) | The milestone has a user-visible surface · one full-stack codebase · early product where "show it working" matters. Each slice stays inside one lane where it can. |
| **Horizontal** | A milestone that is mostly infrastructure with no user-visible surface · contracts already frozen in `#Contracts`, so layers can safely run in parallel. |

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
   (reading the ticket, branch, gate, review, PR) of roughly twenty minutes, so "add the button" and "wire
   the button" as two tickets doubles that cost for nothing a user can see.

How to find the behaviours: walk the feature from the user's side, one verb per ticket, inside its lane —
a **quotes** lane might be *create a quote* · *edit a draft* · *send a quote* · *refuse an expired quote*;
an **auth** lane *sign up* · *log in* · *log out* · *reset password* · *admin invites a member*. Refusals and
empty states that a user meets are behaviours too; security is still a DoD line on every ticket, never its
own ticket.

## §Vertical slicing (thin end-to-end increments)
Split the milestone into **one slice per user-observable behaviour** (§Size by behaviour), each going through
whatever layers it needs. ID: `[M<milestone>-SLICE-<nn>]`.

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
ID: `[M<milestone>-TICK-<nn>]`.

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
Fill the provisioned `feature_ticket.md` template for each ticket:
- **ID + title:** `[M<milestone>-SLICE-<nn>]` or `[M<milestone>-TICK-<nn>]`, then the concern in plain words.
  The `M<milestone>` prefix is what keeps IDs unique across milestones; without it, dedup misfires on re-run.
- **Lane:** the module this ticket lives in (`claims`, `board`) — §Lanes are modules — never a layer.
  Horizontal: all of a milestone's layer tickets share one lane.
- **Owner:** the role that owns the lane — `Senior` unless the board says otherwise.
- **Target files:** exact paths, derived from `STRUCTURE.md` — `src/services/quoteEngine.ts`, not `src/services/`.
  **The list is the boundary**, so it must name **everything `/build` will write**: the code, its tests, *and*
  `docs/features/<feature>.md`. **Never list `PRODUCT.md`, `CHANGELOG.md` or `STRUCTURE.md`** — the spine is
  shared — each phase writes its own rows, and a ticket never lists it.
- **Inputs → outputs:** the typed contract this ticket consumes and the one it exposes, named from `#Contracts`.
- **Depends on:** the ticket IDs whose *contracts* it needs. Contracts land first, so dependants can start
  against a stub rather than waiting for a merge.
- **Demo (vertical):** what a reviewer can see working once this merges. Required on every slice.
- **Implementation tasks:** concrete, ordered, checkable steps — inside this ticket's concern only.
- **DoD (security included):** inputs validated at the boundary · no secrets in source (`.env` only) · no
  swallowed errors, fallbacks fail-closed on auth/security · structured logging, no stray prints ·
  tests written and passing for everything this ticket touches · feature doc updated.
- **Verification command:** the exact command a reviewer runs to see it work.

Write each to `docs/issues/<id>_<slug>.md`, then publish the non-duplicates with `gh issue create`.

