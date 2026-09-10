# Slicing a milestone into tickets — Mode A mechanics

> Loaded by `/tickets` **Step 3A**, on demand. `SKILL.md` owns the mode dispatch and the
> stop-for-confirmation gate; this file owns *how* each strategy actually splits a milestone and what
> goes inside every ticket. Mode B (ad-hoc capture) never loads it.

## §Choose the strategy — the recommendation table

Decide **per milestone**, not once for the repo.

| Recommend | When |
|---|---|
| **Vertical** (default lean) | Solo or small team · one full-stack codebase · the milestone has a user-visible surface · early product where "show it working" matters more than parallelism. |
| **Horizontal** | Separate frontend/backend trees owned by different people · a milestone that is mostly infrastructure with no user-visible surface · contracts already frozen in `#Contracts`, so layers can safely run in parallel. |

**Lane mode overrides the table:** the default is **vertical**, because a vertical slice *is* a lane
(one feature, top to bottom) and a horizontal ticket turns one feature into N lanes that collide on every
change (§Lane mode rule 2). If the user still wants horizontal, say so plainly, **record the reason on
every ticket of that milestone**, and expect Lanekeeper to report the collisions.

## §Vertical slicing (thin end-to-end increments)
Split the milestone into **2–4 slices, each one user-observable behaviour**, going through whatever layers
it needs. ID: `[M<milestone>-SLICE-<nn>]`.

Split along one of these seams — pick the one that yields the thinnest first slice:
- **By user action** — "create a quote" · "export it" · "email it".
- **By happy path, then edges** — slice 1 is the path that works; slice 2 adds the failure and empty states.
- **By input variant** — one supported format first, the rest after.
- **By surface depth** — read-only view first, then the write path.

Rules that keep a slice honest:
- **Slice 1 is the walking skeleton** — the thinnest path that runs end to end. It may be ugly; it must work.
- **A slice that no one can see is not a slice.** "Build the data model" is a layer, not a slice. If a slice
  has no observable outcome, it belongs in a horizontal split instead.
- A slice crosses layers **by design**, but still respects them: vendor SDKs stay behind adapters, business
  logic stays out of components.
- Each slice's DoD carries the tests for the layers it touched — **there is no separate test slice**.

## §Horizontal slicing (one ticket per architectural layer)
ID: `[M<milestone>-TICK-<nn>]`.

| # | Layer | Home (per `STRUCTURE.md`) | The ticket owns |
|---|---|---|---|
| 1 | 📦 Storage / data provider | `src/providers/…`, `src/domain/…` | Typed schema models, persistence adapter, migration. Vendor SDKs stay behind the adapter interface. |
| 2 | ⚙️ Pure domain service | `src/services/…` | Business logic, state transitions, validation workflow. Depends on layer 1 **only through its typed contract**. |
| 3 | 🎨 UI component | `src/components/features/…` | One isolated component: interactive states, accessibility, `DESIGN.md` tokens. No business logic. |
| 4 | 🧪 Cross-layer verification | `tests/integration/…`, `tests/security/…` | The **integration test across the real seam** and the **adversarial/security cases** — the tests that belong to no single layer. |

**Emit only the layers the project has.** Read the directories `STRUCTURE.md` actually declares:
- Backend / API / CLI product (no `src/components/`) → layers 1, 2, 4 — **three tickets, no UI ticket**.
- Frontend-only product (no `src/providers/`) → layers 2, 3, 4.
- Full-stack → all four.
- Never invent a directory to justify a ticket. A ticket pointing at a path the project does not have is a bug.
- **Unit tests are not layer 4.** Each layer ticket's DoD covers its own unit tests. Layer 4 is only what
  cannot live in one layer — otherwise it becomes a dumping ground and the same work is counted twice.

## §Per-ticket content (both strategies)
Fill the provisioned `feature_ticket.md` template for each ticket:
- **ID + title:** `[M<milestone>-SLICE-<nn>]` or `[M<milestone>-TICK-<nn>]`, then the concern in plain words.
  The `M<milestone>` prefix is what keeps IDs unique across milestones; without it, dedup misfires on re-run.
- **Lane:** the feature name this ticket belongs to (`checkout`, `export`) — never a layer. Vertical: the slice's
  feature. Horizontal: the milestone's feature (all its layer tickets share one lane). Lanekeeper reads it.
- **Target files:** exact paths, derived from `STRUCTURE.md` — `src/services/quoteEngine.ts`, not `src/services/`.
  **The list is the boundary**, so it must name **everything `/build` will write**: the code, its tests, *and*
  `docs/features/<feature>.md`. **Never list `PRODUCT.md`, `CHANGELOG.md` or `STRUCTURE.md`** — the spine is
  shared and is reconciled by `/dev-check` + `/ship`, not written from inside a ticket (§Lane mode rule 3).
- **Inputs → outputs:** the typed contract this ticket consumes and the one it exposes, named from `#Contracts`.
- **Depends on:** the ticket IDs whose *contracts* it needs. Contracts land first, so dependants can start
  against a stub rather than waiting for a merge.
- **Demo (vertical):** what a reviewer can see working once this merges. Required on every slice.
- **Implementation tasks:** concrete, ordered, checkable steps — inside this ticket's concern only.
- **DoD (security included):** inputs validated at the boundary · no secrets in source (`.env` only) · no
  swallowed errors, fallbacks fail-closed on auth/security · structured logging, no stray prints ·
  tests written and passing for everything this ticket touches · feature doc updated.
- **Verification command:** the exact command a reviewer runs to see it work.

Write each to `docs/issues/<id>_<slug>.md`, then publish the non-duplicates with `gh issue create`.

