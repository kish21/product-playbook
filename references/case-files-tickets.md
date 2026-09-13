# Case files — `/tickets`

War stories behind the rules in `commands/tickets/references/*.md`. Each heading is pointed to from its rule.

## The folder the map did not draw

**Potluck live run, 2026-09-13.** `/tickets` was about to write `docs/issues/` in a repo whose
`scripts/check_structure.py` compares `STRUCTURE.md`'s drawn tree with the real folders **in both
directions** and runs in the commit hook and CI. The skill says nothing about the map, and its own rule
("never list `STRUCTURE.md` in a ticket") reads as "never touch it". Writing the backlog as instructed
would have turned CI red with a docs-only change. The run drew `docs/issues/` itself, since the phase
creating a folder is the one that should draw it. The same trap is waiting for the first `/build`: the
feature docs go in `docs/features/`, which cannot be drawn in advance because a drawn-but-absent folder
also fails. So the backlog README names that one map line as an expected exception in the first build PR.

## The checker that cried wolf

**Potluck live run, 2026-09-13.** The symbol check was run as a script over 15 tickets, grepping every
backticked span against `backend/src/**`, config, migrations and the generated frontend types. The first
pass raised about 70 failures. None was a frozen contract name. They were React components the tickets
themselves create (`ClaimForm`, `Notice`, `EventForm`), in-concern short paths (`claims/store.ts`), and
commands in backticks. A reviewer facing 70 reds either stops trusting the check or starts hand-waving,
and the one real invention would hide in the pile. After the resolver learned "or a basename from any
ticket's Target Files", the run passed. Then `ClaimsStore.claimDish`, `costUsd` and
`POST /api/v1/claims` were planted in one ticket: three reds, reverted, green. Only after that did
anything reach `gh issue create`.

## The tests that fell between phases

**Potluck live run, 2026-09-13.** `#Plan`'s testing row put the real-environment checks (phone width, slow
network, reduced motion, forced colours, Playwright from M3) inside milestones M3/M4. Vertical slicing
produced tickets for every user-visible behaviour in those milestones, and the checks matched none of them:
they are not a feature, and `/test` owns them in the chain. The backlog was complete by every existing gate
and still dropped a planned item without a trace. It was caught only by rereading `#Plan` against the ticket
list after publishing. The fix was one README line placing `/dev-check` → `/test` between M3-SLICE-03 and
M3-SLICE-04.

## The fifteen-step recipe

**Potluck live run, 2026-09-13.** `/tickets` cut the plan into 15 vertical slices and published them with
15 lanes — one per ticket. Every slice depended on the one before it: 01 → 02 → 03 → M2-01 → M2-02 → M2-04
→ M3-03 → M5-02. The run's README said why: *"one person builds this."* The owner then asked whether two
or three people could take the backlog and work on it at the same time. They could not: only three pairs
of tickets could run together without editing the same file, and `backend/src/index.ts` was named by
seven of the fifteen. The skill had optimised for "show it working after every merge" and never
considered that the same work, grouped by the modules `STRUCTURE.md` already drew, would have let a
solo builder hand any module to a friend on the day they wanted to — at no cost to the solo case.

## The base MarkVid runs on

**MarkVid, 2026-09 (60+ cards).** Every ticket is a card on one board with four single-select fields:
**Lane** (the code area — `Images`, `Auth`, `Assembly`), **Owner** (`Senior` or `Junior`, "follows the
files, not the difficulty", mirrored as an `owner:` label on the issue), **Seat** (`SR1 SR2 JR1 JR2` —
the chair actually working, a person or an agent instance) and **Status**. One lane = one owner; never
two branches open in the same lane; cross-lane dependencies written as coordination points ("junior's
#559 starts after senior's #211 merges"); the `/jr-ticket` command refuses a ticket whose `owner:` label
is not its own. Two developers push from one account, so assignees carry nothing — the board does. The
same board also carries the gotcha recorded in `case-files-build.md` §The read-back that always said
unset: a card added with `gh project item-add` and no fields set is invisible on every lane view, and
`item-list --format json` returns lowercase keys.

## Confirmed as proposed, never shown

**Potluck live run, 2026-09-13 (#210).** Step 3A.1 asked one question — *"proceed as proposed (17
tickets)?"* — and no proposal had been printed before it. The owner said yes to a list they had not seen.
The run then published 15: two had been merged into neighbours after the yes, and nobody was asked again.
Nothing was wrong with the 15; what was wrong was that "confirmed" described a number, not a list. A
confirmation is of the thing shown, and a set that changes after it is a new proposal.

## Eleven issues against an invented API

**An earlier live run.** The backlog was published straight from the draft and corrected 22 minutes later:
eleven issues had been written against response types that existed nowhere in the frozen contracts. On a
team the window is not 22 minutes, it is *until someone reads them* — and GitHub tells nobody that every
issue they saw yesterday has been rewritten. Verification runs over the local files; publishing is the
irreversible step.
