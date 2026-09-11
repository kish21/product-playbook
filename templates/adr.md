# ADR-NNNN — <the decision, as a statement>

- **Status:** `accepted` <!-- proposed | accepted | superseded by ADR-NNNN (<date>) | reversed (<date>) -->
- **Date:** `<YYYY-MM-DD>`
- **Phase:** `<the skill that recorded it — usually /architect>`
- **Provenance:** `<user-chosen | default taken, not user-chosen>`

## Decision

One or two sentences. State it as a rule someone can obey or break, not as a topic:
*"The share link IS the authorization model — high-entropy ids, no enumeration, `noindex`"*, not
*"we discussed authorization"*.

## Why

The constraint set this was optimised against — reliability · operational burden · team size · cost ·
compatibility · maturity · lock-in — and which of them decided it. Name the one that would have to change
for this decision to change.

## What was rejected, and why it lost

The expensive thing to reconstruct in a year is not what was chosen, it is **why the other option lost**.
One line per rejected alternative.

## Consequences

What this makes easy, what it makes hard, and **what breaks if someone ignores it**. This is the part an
agent reads before editing the code — a rule whose consequence is stated survives a refactor; a bare
instruction does not.

## Superseding

A reversal does not delete this file. Set `status: superseded by ADR-NNNN` here, with the date, and state
the reason in the new ADR. Being individually supersedable is the whole point of one file per decision —
it is what a paragraph buried in a 73KB spine could never do.
