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
