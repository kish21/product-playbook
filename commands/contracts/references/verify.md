# Proving the contracts — Step 3b in full

> Printed whole by `status.py next --phase contracts`; one proof alone: `status.py section <this file> "<name>"`. Each proof
> ends in an `evidence:` line in `#Contracts`. **If any is "should" not "shown", STOP and make it real.**

## Evidence lines

`evidence: <command> → <result> · <artefact> · <date>` (`STATE-MODEL.md` §2f). **Everything a line cites must
exist**: `set contracts filled` refuses a cited file that is not in the project and a cited `file::test_name` the file
does not define. Cite the command you ran, never the one you meant to run. A long output goes to a scratch file; cite
the verdict line.

## Migration applies

Run the migrations **from empty on the isolated test datastore** `/foundation` provisioned (its own variable, e.g.
`TEST_DATABASE_URL`), never the development one: `alembic upgrade head` · `prisma migrate deploy` · `drizzle-kit
migrate` · the tool `#Architecture` recorded. Where the tool can go down, go down one step and up again. The evidence
line names the migration command (`set contracts filled` refuses a `#Contracts` with no evidence line that ran one).

## Schema matches code

Prove the models and the migrated schema agree with the tool's own check: `alembic check` ("No new upgrade
operations") · `prisma migrate diff --from-migrations <dir> --to-schema-datamodel <schema> --exit-code` ·
`drizzle-kit check`. No such check: a test that reads, from the migrated database, every column the code reads. Put
the check in CI, so it is run on every change, not asserted once.

## Boundaries

One test per boundary asserts its unit on both sides — e.g. money round-trips exactly (6.75 in, 6.75 out), a float
amount is refused, a naive datetime is refused, a score outside its range is refused. A unit written in a table only is
UNVERIFIED.

## Keys and PII

A test proves every persisted table carries the tenant key (the named exceptions only), and that each write path's
idempotency/natural key is unique in the schema (a second insert with the same key fails or is ignored, never
duplicated). PII: the classification is in `docs/contracts.md`; a field marked delete-after has a deletion path named.

## Documented contract

Run the export script, then its `--check` (the committed file equals what the app serves): exit 0. A document another
tool parses: run that tool's real parser on a filled example and show what it read.

## Agent

`Agent: yes`: each AGENT.md §Contracts row has its path and one evidence line — a tool call with a wrong argument is
refused by its schema, an unknown policy key stops the boot, a malformed model reply is refused, one trace record and
one hand-off payload validate against their schemas, the golden cases load against the eval-case schema.
