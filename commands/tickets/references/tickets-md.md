# `TICKETS.md` — the backlog's plan, at the project root

> Opened by `/tickets` **Step 3A.2**, after the ticket files are written and before verification. `slicing.md`
> decides the epics, lanes and dependencies; this file decides how the plan is written down. Mode B never
> opens it: an ad-hoc bug is not part of the plan.

## §What it holds — the plan, never the status

`TICKETS.md` is what a second person reads to start work without asking anyone: the epics, the lanes, how
the lanes wait on each other, and who starts what on day one. It replaces `docs/issues/README.md`.

- **Status lives on GitHub** — the issues and the Delivery Board — **and never in `TICKETS.md`**: no status
  column, no checkbox, no done mark, no progress count, no issue state. A plan that tracks status goes stale
  the day a ticket merges and nobody edits it; one that never tracks it cannot. `/build` never writes
  `TICKETS.md`, and no ticket lists it in its Target Files.
- **Written by `/tickets` alone** — rendered by `set tickets filled --from-fields` from the fields file, never typed.
  A re-run renders it again from the fields; nothing else edits it —
  except a shape-changing `/structure` re-run, which rewrites the paths it moved and nothing else.
- **One file for the whole backlog**, every milestone in it, in `#Plan` order.
- **A stopped run** (`MECHANISMS.md` §Declined runs) is recorded by `status.py` (`MECHANISMS.md` §Status), never as a line at the top of
  this file, and the next attempt replaces that line.

## §The sections, in order

1. **A one-line header** saying the file is the plan and naming where status lives (the board's title).
2. **One section per milestone**, named from `#Plan`: a table of its epics — epic ID and name · lane · owner ·
   tickets in build order (ID and title). A milestone with no tickets gets one line saying why (`slicing.md`).
3. **Lanes** — the parallel table (`slicing.md` §Lanes are modules): lane · owner · seat · epics · which lanes
   run at the same time. **Seat** works that lane (§Seats) and is stamped on its cards.
4. **Seat load** — each seat's operator, ticket count and lanes; the PRs a person reviews for agent seats; the
   longest chain of waits (the tickets that merge one after another however many seats there are). An idle seat,
   or one seat carrying twice another's tickets, is a warning in `set`'s output.
5. **Coordination points** — every cross-lane dependency, one line each, in its kind: *waits for … to merge*
   (that ticket's `Depends On`) or *builds against …* (its `Builds against`).
6. **Hub files** — each with the lanes that touch it.
7. **The flow graph** (§The flow graph).
8. **Day 1 — who starts what** (§Day 1).
9. **Handed to later phases** — each `#Plan` item a later phase owns, with the point it runs at.

## §The flow graph

A Mermaid `flowchart LR` with **one box per lane** — every lane in the parallel table, no box that is not a
lane — and one arrow per coordination point, from the lane that goes first to the lane that needs it:
- **Solid arrow** `-->` = **wait for the merge** — the label reads *"<ticket> waits for <ticket>"*.
- **Dotted arrow** `-.->` = **build against the contract**, a stub is enough to start — the label reads
  *"<ticket> builds against <ticket>"*.

Write it in the shapes shown below and no others: a box is `lane_<name>["<name> · <owner>"]` (the `lane_`
prefix keeps a module called `end` from breaking the parser), an arrow is `lane_a -->|"label"| lane_b` or
`lane_a -.->|"label"| lane_b`, one per line. GitHub renders Mermaid with a pinned version that has rejected
newer syntax, and a graph that does not render is a code block nobody reads. Say the legend in one line under it.

## §Seats — one per person or agent the user named

The seats come from the number round 1's answer gave, never a default list: *"2 developers"* → `SR1`, `SR2`;
*"3 seniors and 2 juniors"* → `SR1`–`SR3`, `JR1`–`JR2`; alone → `SR1`. Every lane gets exactly one seat in the
Lanes table (a seat may work several lanes; split the lanes so the seats carry about the same number of
tickets), and the publish engine reads that table: `"seats"` lists them all and each epic carries its lane's
`"seat"` (`publishing.md` §The Delivery Board). **What each seat is** - its type (`SR` senior, `JR` junior) and its
operator (a person, an agent, or an agent a person operates) - is round 1's answer, written once in the fields file
(`{"id": "JR1", "operator": "agent+person"}`); the script renders it into the Lanes table's **Seat type** and
**Operator** columns, and publishing puts it in the board's Seat option description.

## §Day 1 — who starts what

**One row per seat** the user named — no seatless *"next free seat"* row: the **Seat**, its lane, its day-one
ticket and why it does not wait. **A day-1 ticket has no `Depends On`** (it may build against a contract) and
is in the current milestone. Under the table, one line: **when a seat frees up, it takes the next startable
ticket on the board**, its own lanes first. With agent seats, one more line: each agent seat works in its own
`git worktree` folder and branch, so two seats never share a working copy.

## §Example

An invented waitlist app with three module lanes, two developers named in round 1 (`SR1`, `SR2`):

````markdown
# Tickets — Waitlist

> The plan: epics, lanes, and who starts what. Status lives on GitHub, on the *Waitlist — Delivery Board*,
> and never in this file.

## M1 — Parties wait for a table

| Epic | Lane | Owner | Tickets in build order |
|---|---|---|---|
| `M1-PARTY` Parties join the list | parties | Senior | `M1-PARTY-01` guest adds their party · `M1-PARTY-02` guest sees their place · `M1-PARTY-03` guest leaves the list |
| `M1-HOST` Host runs the queue | queue | Senior | `M1-HOST-01` host sees the queue · `M1-HOST-02` host seats a party · `M1-HOST-03` host marks a no-show |
| `M1-TEXT` Guests get a text | notify | Senior | `M1-TEXT-01` guest gets a text when their table is ready · `M1-TEXT-02` host sees a text that failed |

## Lanes

| Lane | Owner | Seat | Seat type | Operator | Epics | Runs alongside |
|---|---|---|---|---|---|---|
| parties | Senior | SR1 | senior | person | `M1-PARTY` | queue, notify |
| queue | Senior | SR2 | senior | agent, a person reviews its PRs | `M1-HOST` | parties |
| notify | Senior | SR2 | senior | agent, a person reviews its PRs | `M1-TEXT` | parties |

## Coordination points

- `M1-HOST-01` (queue) builds against `M1-PARTY-01` (parties) — the `Party` type is frozen; a stub list is enough.
- `M1-TEXT-01` (notify) waits for `M1-HOST-02` (queue) to merge — the text is sent when a host seats a party.

## Hub files

- `src/app/routes.ts` — parties, queue and notify each add one line.

## Flow graph

```mermaid
flowchart LR
  lane_parties["parties · Senior"]
  lane_queue["queue · Senior"]
  lane_notify["notify · Senior"]
  lane_parties -.->|"M1-HOST-01 builds against M1-PARTY-01"| lane_queue
  lane_queue -->|"M1-TEXT-01 waits for M1-HOST-02"| lane_notify
```

Solid arrow: wait for the merge. Dotted arrow: build against the contract — a stub is enough to start.

## Day 1 — who starts what

| Seat | Lane | Starts | Why it does not wait |
|---|---|---|---|
| SR1 | parties | `M1-PARTY-01` guest adds their party | depends on nothing |
| SR2 | queue | `M1-HOST-01` host sees the queue | builds against `M1-PARTY-01` with a stub |

When a seat frees up, it takes the next startable ticket on the board — `M1-TEXT-01` (notify, SR2's lane)
once `M1-HOST-02` merges.

## Handed to later phases

- Phone-width and slow-network checks → `/test`, once `/dev-check` closes M1.
````
