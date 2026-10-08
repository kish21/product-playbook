---
name: contracts
description: >
  Phase 2 (Development), step 4 of product-playbook. Define typed data models, schemas, DB migrations,
  and API/agent contracts BEFORE business logic — so boundaries are typed and units/scale agree. Use
  after /foundation, or run /contracts "define the models", "schema", "data types", "api contract".
  Writes the Contracts section of PRODUCT.md. Run /tickets next, then /build.
---

# `/contracts` — Phase 2 · Development ④ · run as an **engineer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **This skill's OWN reference files are a DIFFERENT folder** (`commands/contracts/references/`: `contract-steps.md`, `verify.md`), never the plugin-root `references/`.
> **`status.py next --phase contracts` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it) — with both reference files and AGENT.md §Contracts (`Agent: yes`) whole. Load-bearing: **typed contracts not raw dict/text**, **units/scale/shape agree across boundaries**, **migrations (never hand-edit schema)**, **schema↔code consistency**, **testable-by-construction**.

## Contract
- **Purpose:** lock the typed shapes (models, schemas, migrations, API/agent contracts) before logic.
- **Reads:** `PRODUCT.md#Scope`, `#Architecture`, `#Structure`.
- **Writes:** the schemas **in code** (`src/schemas/*`, the migrations, the route table / API spec) and
  `PRODUCT.md#Contracts` as a **record**: what was frozen, the boundary units and scale, the evidence
  line, and **the paths**. The section never restates the types — it points at them, and
  `MECHANISMS.md` §Follow the pointer makes that pointer binding on every phase that reads it.
- **Gate type:** `derivation` — computable from `#Scope` + `#Architecture`. Batchable - a `derivation` run may chain with its neighbours and end in ONE review. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Contracts` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Companion:** `docs/contracts.md` — the reasoning, workings and raw notes, after the reader's part (an overview with ONE diagram, the units, the PII table). `PRODUCT.md#Contracts` stays a
  RECORD (summary · decision · evidence · pointer) — no byte cap; reasoning moves, answers stay.
- **Must NOT:** write product logic (a declared route returns 501 until `/build`), edit a migration that has run, change a decision `#Architecture` recorded (a clash is Step 3c), or commit before the close.
- **Checked by `status.py set contracts filled`, not by reading** — every countable gap in ONE refusal, an earlier phase's failing check included; `--dry-run` lists them, writes nothing.
- **Exit criteria:**
  - [ ] Core domain entities defined as **typed models** (not raw dicts/free text). → `Typed models / schemas / migrations`
  - [ ] Persistence via a **migration** (never hand-edited schema); **schema matches what code reads/writes**. → `Typed models / schemas / migrations`
  - [ ] Every cross-boundary payload (API in/out, agent in/out) is a typed contract. → `Typed models / schemas / migrations`
  - [ ] **Units/scale/shape agreed on both sides** of each boundary (the classic "0–1 vs 0–10" trap); a unit captured at the source (e.g. currency) is used everywhere, not re-derived. → `Boundary units/scale agreed`
  - [ ] Public API/agent contracts are documented (e.g. an OpenAPI/schema export), not just in code. → `Typed models / schemas / migrations`
  - [ ] **`Agent: yes`: every AGENT.md §Contracts row** is recorded, or `N/A — <reason>`. → `(Agent)`
  - [ ] `#Contracts` is a **RECORD** — every field is a decision, evidence line or pointer; the reasoning is
    in `docs/contracts.md`. Size is reported, never trimmed to. → `Detail:`
  - [ ] **Every companion opened is receipted** — one line per file, quoting a fragment that
    occurs verbatim in it. → `Read (file · date · verbatim quote)`

## Step 0 — Context + prior-gate check
- **One first command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase contracts`** — the spine lines the contracts are built from, round 1, the five steps and their proofs, the record's shape, what `set` refuses, the rules. Show its first line; open no rule, reference or spine file whole after it.
- If `#Foundation` isn't done, warn (you need a place to run migrations) but allow override.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then record it — `status.py bypass --from contracts --gate <gate> --reason "<the user's own words>"` (`MECHANISMS.md` §Status) — before continuing.
- Brownfield: read existing models/migrations; extend, don't duplicate.
- **Ask the open decisions NOW, in one card, before any file is written** — round 1 as `next` prints it, ONE message (outside callers · the tenant key · how long personal data is kept · the currency · what earlier sections left open); the answers word for word into `docs/contracts.md`; then run unattended and say so.
- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** a filled section → follow the `RE-RUN` line `next` prints: **one question listing what would change**, never a silent overwrite; a reversed decision keeps a dated `superseded <date>: <why>` line.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** record it — `status.py set contracts declined --reason "<what was missing>" --gate <the phase(s) that fill it>` (`MECHANISMS.md` §Status) — and change nothing in `PRODUCT.md`.

## Step 1 — Apply principles (this phase)
- **Typed contracts everywhere:** model the domain with the stack's type system; no raw dict/text across a boundary.
- **Migrations only:** schema changes via migration files; **verify a column the code reads actually exists** (schema↔code).
- **Agree units/scale/shape** explicitly at each boundary — write the unit into the field name/comment if ambiguous (e.g. `score_0_10`).

## Step 2 — Define the contracts
**Work through the five in `contract-steps.md`, printing each step's § as you reach it**.
Print one line as each numbered step lands (`MECHANISMS-ON-DEMAND.md` §Context hygiene).
1. **Domain models** for the core-feature entities (typed; validated at construction).
2. **Persistence schema** + a **migration**; confirm the schema matches the models and the queries. **Seed data that mirrors a code registry is pinned to it by a test.**
3. **API/agent contracts:** request/response (and, for AI, the typed output schema each step returns) — with a **versioning / back-compat** approach (`/v1`, additive-only), exported to a committed file. `Agent: yes`: AGENT.md §Contracts.
4. **Boundary audit:** for each boundary, state the units/scale/shape both sides expect; reconcile mismatches now. For write/ingest paths define the **idempotency/natural key**. **A document another tool PARSES is a boundary too.**
5. **Safety on the data:** classify **PII/sensitive** fields (retention/N-A) and give every persisted entity its **tenant/owner key** (the isolation seam).
A folder this phase adds goes into STRUCTURE.md's map in the same message.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Contracts`: typed models/schemas/migrations · boundary units/scale · versioning · PII · tenant/idempotency keys · (Agent) rows — a scratch file outside the repo; `docs/contracts.md` comes last (Step 3b).

## Step 3b — Principle-gate: verify the contracts hold (evidence)
**Prove each with `verify.md`, § by §:** §Evidence lines · §Migration applies · §Schema matches code ·
§Boundaries · §Keys and PII · §Documented contract · §Agent. **If schema and code disagree, or a boundary's units are
unstated, STOP and fix it** — a scale mismatch across a boundary is a silent wrong-answer bug that looks healthy.

**Measure what you wrote and receipt what you read** (`MECHANISMS-ON-DEMAND.md §Section is a record`, `MECHANISMS-ON-DEMAND.md §Read receipt`): `set` reports the section and file size in one line; apply the record test to every field — reasoning moves into the companion, a tight answer stays whatever it weighs, never trim to a number; write one `Read:` line per companion opened, each quoting a fragment that occurs verbatim in that file.

**Keep the context lean (`MECHANISMS-ON-DEMAND.md` §Context hygiene):** a command's output over 30 lines goes to a scratch file; read the tail or grep the verdict, and cite the file in the evidence line.

**Close the loop (`MECHANISMS.md` §Step 3b):** `set contracts filled --section-from <file> --dry-run`; fix every gap. **Round 2, ONE message:** a table of what was frozen (table · tenant key · units · how long personal data is kept · contract file), any Step 3c clash, one question - *"Anything to change? If not: Save this version of your project? (yes / no)"* as "Looks good - save (Recommended)" · "Looks good - don't save yet" · "Change something". Then ONE message: `docs/contracts.md` (its shape: the dry-run) and, after it, `set contracts filled --section-from <file> --commit "<one line>"` (no `--commit` on "don't save yet"; `MECHANISMS.md` §Commit the work) records, saves and prints the rest of the close, in order. Its transition guard (`MECHANISMS.md` §Step 3b, item 4) cites the evidence lines this run ran (a line whose files changed since: run it again); `UNVERIFIED` is a normal outcome, silence is not; the close in plain language (`MECHANISMS.md` §Plain-language close) ends with its `Open a NEW conversation` line word for word.

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Architecture` (datastore · migrations approach) and `#Scope` — types for an entity no scoped feature needs, or a schema that bypasses the recorded migration path. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Typed contracts and migrations are in place. Next run **`/tickets`** — it cuts each milestone into small,
independently mergeable tickets whose types and routes resolve to these contracts. Then **`/build`**, one
ticket at a time, security in the definition-of-done. Ship when a milestone's exit criterion holds —
`/ship` is per release, not per project."
