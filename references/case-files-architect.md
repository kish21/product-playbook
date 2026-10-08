# Case files — /architect

War stories behind the one-line lessons in `commands/architect/SKILL.md`. Each heading is pointed
to from the skill file as `(case file: <heading>)`.

## Two closes in one run

A logged `/deploy` run found no runtime target for the site and sent the run to `/architect` for that one
decision. All of `/architect` fired inside `/deploy`: its full exit criteria (provenance on every row, the
dev-tooling line), the chain offer into `/structure`, its commit offer and its plain-language close. The
user got two closes in one run, for a question that needed one row. A narrow run decides the row, with its
benchmark and provenance, and hands back.

## "Is it free?"

The host was chosen by the owner, so the run skipped the benchmark, and with it everything about the host.
The owner's first three questions were "is it free?", "alternatives?" and "when would I be charged?".
Later they asked what each usage counter on the host's dashboard meant and when it reset. A user's choice
removes the need to pick. It does not remove the need to know.

## One app by accident

The UI tooling was recorded as React with shadcn, and the run let that decide the server language too. A
full-stack product became a single TypeScript app that no later phase could question, because `/structure`
derives the tree from this row. Earlier the provenance flag covered only custody, runtime and identity, so
the language was picked silently and the owner found out at the output.

## ADRs with no files

A real spine cited `ADR-1…ADR-5` 18 times across four sections with no `docs/adr/` anywhere: the vocabulary
without the mechanism. The playbook has a `superseded` state and nothing per decision to attach it to.

## Other lessons behind one-line rules

- **Search bound:** seventeen searches on one live run were the phase's largest cost after its own output.
- **Budget from the dominant cost:** a number pulled from a hunch missed by about 2x when `/eval` measured it.
- **Dev tooling:** an unrecorded hook-runner slot was filled with a Python runner in a Node repo.
