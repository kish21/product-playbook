# Defining the contracts — the five steps in full

> Printed whole by `status.py next --phase contracts`; one step alone: `status.py section <this file> "<n>."`. SKILL.md names the five; this file is what each one means and the failure behind each rule.

## 1. Domain models

**Domain models** for the core-feature entities (typed; validated at construction) — the stack's own type system
(Pydantic, zod, a dataclass that checks its fields), never a raw dict or free text. Model only what a `#Scope` feature
needs: types for an entity no scoped feature needs are a Step 3c conflict. Brownfield: extend the models that exist.

## 2. Persistence schema and a migration

**Persistence schema** + a **migration**, on the migrations approach `#Architecture` recorded; confirm the schema
matches the models and the queries (`verify.md` §Schema matches code).
- **Migrations only:** the schema is built by migration files, never by app code at boot (`metadata.create_all`,
  `synchronize: true`, `db push`) — `set contracts filled` refuses a project with no migration file, or with app code
  that builds the schema. Generate the migration from the models when the tool can (then the models and the history
  are one thing and a schema check means something), read it, adjust it. **Never edit a migration that has run**;
  add a new one. The identity tables `/foundation` seeded stay; extend them by a new migration.
- **Money is never a float** — integer minor units (`amount_cents`, `*_micros`) or a fixed decimal, the currency
  stored beside it. Binary floating point cannot hold 6.75 exactly, and a sum over thousands of rows drifts.
  `set contracts filled` refuses a money-named column or field (pay, salary and tax words, a currency in the name)
  typed float or Any, converted from a float, or given a float value in code or config (`spend_eur: 0.10` →
  `spend_micro_eur: 100000`), unless a line of `#Contracts` names it with why it stays one (a vendor reports a rate
  as a float, converted at the adapter). A rate is not money: `rate_bp` (integer basis points, 1250 = 12.50%); a
  float `*_rate` or percentage is a warning at the close, not a refusal.
- **Seed data that mirrors a code registry must be PINNED to it by a test** (parse the seed migration, assert its rows are in lockstep with the registry constant). A seed is a copy of a code contract frozen in SQL — without the pin, the registry evolves and the DB silently offers keys the code no longer recognises, or misses ones it requires. *(Real instance: per-intent option seeds pinned to the active intent registry by a migration-parsing test — a registry rename now fails the build instead of orphaning seeded rows.)*

## 3. API and agent contracts

**API/agent contracts:** request/response (and, for AI, the typed output schema each step returns) — with a
**versioning / back-compat** approach (`/v1`, additive-only: a new optional field is allowed; removing or renaming a
field, narrowing a type or **changing a unit** is a `/v2`).
- **Exported to a committed file** — OpenAPI, JSON Schema, GraphQL SDL or `.proto`, written by a script from the code
  so the file and the app cannot disagree (a `--check` mode in the commit hook or CI). `#Contracts` names the file.
  Nothing outside the app calls it (no public API, no webhook, no client in another repo): the versioning field says
  `N/A — <reason>` instead.
- **Routes declared now return 501** until `/build` fills them: a declared route that returns 200 and nothing is a
  wrong answer wearing a success code.
- **`Agent: yes`:** open AGENT.md §Contracts and record every row.

## 4. Boundary audit

**Boundary audit:** for each boundary, state the units/scale/shape both sides expect; reconcile mismatches now. For
write/ingest paths define the **idempotency/natural key**.
- Write the unit into the name when it could be read two ways (`score_0_10`, `amount_cents`, `timeout_ms`); time is
  timezone-aware UTC at every layer; an unknown value is `null`, never `0`.
- A unit captured at the source (the shop's currency) is carried, never re-derived downstream.
- **A document another tool PARSES is a boundary too — verify it by running the consumer's real parser on a filled example, not by reading the spec.** Template comments, placeholders and example paths are input to the parser as much as the fields are. (case file: The template the parser read differently)

## 5. Safety on the data

**Safety on the data:** classify **PII/sensitive** fields (retention/N-A) and give every persisted entity its
**tenant/owner key** (the isolation seam).
- **Name the key in backticks** in `#Contracts`' PII · tenant field, on the sentence that says tenant (e.g.
  Tenant key: `shop_id`) - an idempotency key in the same field is not a tenant key. `set contracts filled` checks
  every table the migrations create carries it. A table that does not — the tenant table itself, a global switch —
  is named on a line of `#Contracts` with why (`kill_switch has no tenant key: one switch for the whole service`).
  A single-user product writes `N/A — <reason>` in that field.
- PII: each sensitive field, why it is kept, how long, and how it is deleted; a field nobody needs is not stored.
