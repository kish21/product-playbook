---
name: contracts
description: >
  Phase 2 (Development), step 4 of product-playbook. Define typed data models, schemas, DB migrations,
  and API/agent contracts BEFORE business logic — so boundaries are typed and units/scale agree. Use
  after /foundation, or run /contracts "define the models", "schema", "data types", "api contract".
  Writes the Contracts section of PRODUCT.md. Run /build next.
---

# `/contracts` — Phase 2 · Development ④ · run as an **engineer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per PRINCIPLES.md §Spine resolution).
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
- Brownfield: read existing models/migrations; extend, don't duplicate.

## Step 1 — Apply principles (this phase)
- **Typed contracts everywhere:** model the domain with the stack's type system; no raw dict/text across a boundary.
- **Migrations only:** schema changes via migration files; **verify a column the code reads actually exists** (schema↔code).
- **Agree units/scale/shape** explicitly at each boundary — write the unit into the field name/comment if ambiguous (e.g. `score_0_10`).

## Step 2 — Define the contracts
1. **Domain models** for the core-feature entities (typed; validated at construction).
2. **Persistence schema** + a **migration**; confirm the schema matches the models and the queries.
3. **API/agent contracts:** request/response (and, for AI, the typed output schema each step returns) — with a **versioning / back-compat** approach (`/v1`, additive-only).
4. **Boundary audit:** for each boundary, state the units/scale/shape both sides expect; reconcile mismatches now. For write/ingest paths define the **idempotency/natural key**.
5. **Safety on the data:** classify **PII/sensitive** fields (retention/N-A) and give every persisted entity its **tenant/owner key** (the isolation seam).

## Step 3 — Write back to `PRODUCT.md`
Fill `#Contracts`: typed models/schemas/migrations · boundary units/scale · versioning · PII · tenant/idempotency keys.

## Step 3b — Principle-gate: verify the contracts hold (evidence)
Walk this phase's principles and prove each: the migration **actually applies** and a column the code
reads exists (schema↔code — run it); every boundary's **units/scale are stated on both sides**; public
contracts have a **versioning** approach; persisted entities carry a **tenant key**; write paths have an
**idempotency key**; PII is classified. **If schema and code disagree, or a boundary's units are unstated,
STOP and fix it** — a scale mismatch across a boundary is a silent wrong-answer bug that looks healthy.

## Step 4 — Handoff
"Typed contracts and migrations are in place. Now build features against them: run **`/build`** — one
feature at a time, security in the definition-of-done."
