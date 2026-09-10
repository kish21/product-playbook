---
name: contracts
description: >
  Phase 2 (Development), step 4 of product-playbook. Define typed data models, schemas, DB migrations,
  and API/agent contracts BEFORE business logic — so boundaries are typed and units/scale agree. Use
  after /foundation, or run /contracts "define the models", "schema", "data types", "api contract".
  Writes the Contracts section of PRODUCT.md. Run /build next.
---

# `/contracts` — Phase 2 · Development ④ · run as an **engineer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **typed contracts not raw dict/text**, **units/scale/shape
> agree across boundaries**, **migrations (never hand-edit schema)**, **schema↔code consistency**,
> **testable-by-construction**.

## Contract
- **Purpose:** lock the typed shapes (models, schemas, migrations, API/agent contracts) before logic.
- **Reads:** `PRODUCT.md#Scope`, `#Architecture`, `#Structure`.
- **Writes:** `PRODUCT.md#Contracts` — typed models/schemas/migrations · boundary units/scale agreed.
- **Exit criteria:**
  - [ ] Core domain entities defined as **typed models** (not raw dicts/free text).
  - [ ] Persistence via a **migration** (never hand-edited schema); **schema matches what code reads/writes**.
  - [ ] Every cross-boundary payload (API in/out, agent in/out) is a typed contract.
  - [ ] **Units/scale/shape agreed on both sides** of each boundary (the classic "0–1 vs 0–10" trap); a unit captured at the source (e.g. currency) is used everywhere, not re-derived.
  - [ ] Public API/agent contracts are documented (e.g. an OpenAPI/schema export), not just in code.

## Step 0 — Context + prior-gate check
- Read `#Scope/#Architecture/#Structure`. If `#Foundation` isn't done, warn (you need a place to run migrations) but allow override.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then write `Override <date>: <reason> — bypassed <gate>` at the top of `#Contracts` before continuing. Advancing on unmet criteria is the more consequential of warn-vs-override, so it is the one that leaves a trace: without it a later reader cannot tell a gate that held from a gate that was waved through.
- Brownfield: read existing models/migrations; extend, don't duplicate.

- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** if the section is already filled, **show what would change and ask before replacing it** — never a silent overwrite — and leave a reversed decision in place with a dated `superseded <date>: <why>` line. A first run over an empty section is unchanged.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** write ONE dated line at the top of `#Contracts` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **Typed contracts everywhere:** model the domain with the stack's type system; no raw dict/text across a boundary.
- **Migrations only:** schema changes via migration files; **verify a column the code reads actually exists** (schema↔code).
- **Agree units/scale/shape** explicitly at each boundary — write the unit into the field name/comment if ambiguous (e.g. `score_0_10`).

## Step 2 — Define the contracts
1. **Domain models** for the core-feature entities (typed; validated at construction).
2. **Persistence schema** + a **migration**; confirm the schema matches the models and the queries.
   - **Seed data that mirrors a code registry must be PINNED to it by a test** (parse the seed migration, assert its rows are in lockstep with the registry constant). A seed is a copy of a code contract frozen in SQL — without the pin, the registry evolves and the DB silently offers keys the code no longer recognises, or misses ones it requires. *(Real instance: per-intent option seeds pinned to the active intent registry by a migration-parsing test — a registry rename now fails the build instead of orphaning seeded rows.)*
3. **API/agent contracts:** request/response (and, for AI, the typed output schema each step returns) — with a **versioning / back-compat** approach (`/v1`, additive-only).
4. **Boundary audit:** for each boundary, state the units/scale/shape both sides expect; reconcile mismatches now. For write/ingest paths define the **idempotency/natural key**.
   - **A document another tool PARSES is a boundary too — verify it by running the consumer's real parser on a filled example, not by reading the spec.** Template comments, placeholders and example paths are input to the parser as much as the fields are. (case file: The template the parser read differently)
5. **Safety on the data:** classify **PII/sensitive** fields (retention/N-A) and give every persisted entity its **tenant/owner key** (the isolation seam).

## Step 3 — Write back to `PRODUCT.md`
Fill `#Contracts`: typed models/schemas/migrations · boundary units/scale · versioning · PII · tenant/idempotency keys.

## Step 3b — Principle-gate: verify the contracts hold (evidence)
Walk this phase's principles and prove each: the migration **actually applies** and a column the code
reads exists (schema↔code — run it); every boundary's **units/scale are stated on both sides**; public
contracts have a **versioning** approach; persisted entities carry a **tenant key**; write paths have an
**idempotency key**; PII is classified. **If schema and code disagree, or a boundary's units are unstated,
STOP and fix it** — a scale mismatch across a boundary is a silent wrong-answer bug that looks healthy.

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and end with a suggested one-line commit message in the repo's convention.

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Architecture` (datastore · migrations approach) and `#Scope` — types for an entity no scoped feature needs, or a schema that bypasses the recorded migration path. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Typed contracts and migrations are in place. Now build features against them: run **`/build`** — one
feature at a time, security in the definition-of-done."
