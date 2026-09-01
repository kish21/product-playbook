---
name: tickets
description: >
  Phase 2 (Development), step 4b of product-playbook — bridges /contracts and /build. Two modes.
  Bare /tickets decomposes every milestone in PRODUCT.md#Plan into 2–4 granular, single-responsibility
  developer tickets split by architectural layer (data · service · UI · tests), each with exact target
  file paths, typed inputs/outputs and a security DoD, so they can be assigned to different developers
  and merged as isolated PRs. /tickets "<description>" instead logs ONE ad-hoc bug / edge case / tech
  debt item against the file that owns it, without touching the backlog. Provisions
  .github/ISSUE_TEMPLATE/, verifies the remote before publishing, never creates remote repositories,
  and skips tickets that already exist. Writes docs/issues/*.md.
---

# `/tickets` — Phase 2 · Development ④b · run as a **tech lead / project engineer**

> Part of **product-playbook**. Reads the project spine (`PRODUCT.md`, `STRUCTURE.md`, `#Contracts` — resolve per PRINCIPLES.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing:
> **modular / single-responsibility** (one ticket = one concern), **layered & decoupled** (a ticket does not
> straddle layers), **typed contracts** at every seam a ticket exposes, **security in the definition-of-done**,
> and **no hardcoding** (a ticket never asks for a baked-in endpoint, key or model name).

## Contract
- **Purpose:** turn milestones into granular, independently assignable and independently mergeable tickets — and capture ad-hoc issues without derailing the backlog.
- **Reads:** `PRODUCT.md#Plan`, `#Contracts`, `#Architecture`, `STRUCTURE.md`, `DESIGN.md` (UI products only).
- **Writes:**
  - `docs/issues/*.md` — one file per ticket.
  - `.github/ISSUE_TEMPLATE/feature_ticket.md` and `.github/PULL_REQUEST_TEMPLATE.md` (scaffolded from bundled `templates/` if missing).
  - GitHub issues — **ONLY IF** a remote origin is verified and `gh` is authenticated.
- **Exit criteria:**
  - [ ] **Mode A:** every milestone in `#Plan` is decomposed into **one ticket per architectural layer that the project actually has** (2–4 tickets; see the layer split in Step 3A).
  - [ ] Every ticket names **exact target file paths** (`src/services/quoteEngine.ts`), never a bare folder.
  - [ ] Every ticket states its **typed inputs and outputs** — the seam it owns.
  - [ ] Every ticket is **self-contained**: assignable to one developer and mergeable as an isolated PR.
  - [ ] Every ticket carries a **DoD including security** (input validation, no swallowed errors, no secrets in source).
  - [ ] Ticket IDs are **globally unique** across milestones (`[M2-TICK-01]`), so dedup is reliable on re-run.
  - [ ] **Mode B:** an ad-hoc issue is filed against the owning file with a reproduction, and **no backlog ticket is created, renumbered or modified**.
  - [ ] **Pre-flight remote verification executed** — no remote repository is ever created.

## Step 0 — Context + prior-gate check
- Read `#Plan`, `#Contracts`, `#Architecture` and `STRUCTURE.md`. If `#Contracts` is empty, warn (tickets
  would invent their own types) but allow override.
- Brownfield: read the existing tree and `docs/issues/` first — extend the numbering, never restart it.
- **Dispatch on the argument — this is the whole mode decision:**
  - **No argument**, or a planning phrase (`"break down plan"`, `"decompose milestones"`, `"sprint backlog"`) → **Mode A** (Step 3A).
  - **Any other free-text argument** describing a defect, gap or debt item → **Mode B** (Step 3B).
  - Ambiguous? Ask. Do **not** silently regenerate a backlog when the user meant to log one bug.

## Step 1 — Apply principles (this phase)
- **One ticket = one concern.** A ticket that touches two layers is two tickets. If a reviewer would need
  context from another layer to approve the PR, the split is wrong.
- **Vertical slices are for milestones; horizontal slices are for tickets.** The milestone still delivers a
  whole user outcome — it is the *work* that is split by layer, so it can run in parallel.
- **Every ticket declares the contract it exposes**, so the next layer can be built against it before it lands.
- **Security is not a ticket.** It is a DoD line on *every* ticket. Never emit an "add security" ticket.

## Step 2 — Provision templates + pre-flight remote guard (both modes)
1. **Templates.** If `.github/ISSUE_TEMPLATE/feature_ticket.md` is missing, copy it from the bundled
   `templates/feature_ticket_template.md`. If `.github/PULL_REQUEST_TEMPLATE.md` is missing, copy
   `templates/pull_request_template.md`. Never overwrite a template the project already has.
2. **Remote guard — NEVER blindly create a remote repository.** Run `git remote -v`.
   - **No remote:** write tickets to `docs/issues/` only and say:
     *"Tickets written to `docs/issues/`. No remote is linked — run `git remote add origin <url>`, then `/tickets` again to publish."*
   - **Remote present:** check `gh auth status` and `gh repo view`. If either fails, keep the local files and
     tell the user to run `gh auth login`. **Do not run `gh repo create`.**
3. **Dedup index.** With a verified remote, fetch once:
   `gh issue list --state all --limit 100 --json number,title`
   Match a planned ticket to an existing issue by its **ID tag** (`[M2-TICK-01]`, `[ADHOC-07]`) first, exact
   title second. On a match: skip and log `Skipping [M2-TICK-01]: exists as #<num>`. Never edit or close
   an existing issue.
4. **Numbering.** Derive the next free number from `docs/issues/` **and** the fetched issue list together,
   so a re-run after a partial publish cannot reuse an ID.

## Step 3A — Mode A: batch milestone decomposition
For each milestone in `PRODUCT.md#Plan`, emit one ticket per layer **that this project actually has**.

| # | Layer | Home (per `STRUCTURE.md`) | The ticket owns |
|---|---|---|---|
| 1 | 📦 Storage / data provider | `src/providers/…`, `src/domain/…` | Typed schema models, persistence adapter, migration. Vendor SDKs stay behind the adapter interface. |
| 2 | ⚙️ Pure domain service | `src/services/…` | Business logic, state transitions, validation workflow. Depends on layer 1 **only through its typed contract**. |
| 3 | 🎨 UI component | `src/components/features/…` | One isolated component: interactive states, accessibility, `DESIGN.md` tokens. No business logic. |
| 4 | 🧪 Test & verification | `tests/unit/…`, `tests/integration/…` | Unit tests per layer, an integration test across the real seam, and adversarial/security cases. |

**Emit only the layers the project has.** Read the directories `STRUCTURE.md` actually declares:
- Backend / API / CLI product (no `src/components/`) → layers 1, 2, 4 — **three tickets, no UI ticket**.
- Frontend-only product (no `src/providers/`) → layers 2, 3, 4.
- Full-stack → all four.
- Layer 4 is always emitted. A milestone with no verification is not shippable.
- Never invent a directory to justify a ticket. A ticket pointing at a path the project does not have is a bug.

### Per-ticket content
Fill the provisioned `feature_ticket.md` template for each layer ticket:
- **ID + title:** `[M<milestone>-TICK-<nn>] <layer icon> <milestone name> — <layer concern>`.
  The `M<milestone>` prefix is what keeps IDs unique across milestones; without it, dedup misfires on re-run.
- **Target files:** exact paths, derived from `STRUCTURE.md` — `src/services/quoteEngine.ts`, not `src/services/`.
- **Inputs → outputs:** the typed contract this ticket consumes and the one it exposes, named from `#Contracts`.
- **Depends on:** the ticket IDs whose *contracts* it needs. Contracts land first, so layers 2–4 can start
  against a stub rather than waiting for layer 1 to merge.
- **Implementation tasks:** concrete, ordered, checkable steps — inside this layer only.
- **DoD (security included):** inputs validated at the boundary · no secrets in source (`.env` only) · no
  swallowed errors, fallbacks fail-closed on auth/security · structured logging, no stray prints ·
  tests written and passing · feature doc updated.
- **Verification command:** the exact command a reviewer runs to see it work.

Write each to `docs/issues/<id>_<slug>.md`, then publish the non-duplicates with `gh issue create`.

## Step 3B — Mode B: ad-hoc issue capture
Triggered mid-build by `/tickets "Bug: Gemini API timeout is unhandled on slow 3G"`. **Fast path — touch nothing else.**
1. **Classify** the text: `bug` · `edge-case` · `tech-debt` · `security`. Security items are never downgraded.
2. **Locate the owning file** via `STRUCTURE.md` + the architecture: the example above is an LLM provider
   concern → `src/providers/llm/geminiProvider.ts`. Confirm the path exists; if you cannot resolve one
   confidently, say so and record the candidates rather than guessing a path into the ticket.
3. **Write one ticket** `[ADHOC-<nn>]` into `docs/issues/` using the same template, filling: what happened ·
   expected vs actual · reproduction or trigger condition · affected file(s) · suspected cause · a DoD that
   includes a **regression test proving the fix**.
4. **Publish** it as a single issue with the classification as a label, subject to the same dedup and remote
   guards from Step 2.
5. **Do not** read `#Plan`, regenerate, renumber or modify any milestone ticket. One invocation, one issue.

## Step 3b — Principle-gate: verify the tickets hold (evidence)
Walk the principles and prove each against the files just written — do not assert it:
- **Every path resolves.** Check each target path against the real tree (or against `STRUCTURE.md` for a
  not-yet-created file). A ticket pointing at a directory, or at a path this project will never have, fails.
- **Single responsibility.** No ticket lists files from two layers. If one does, split it.
- **No orphan UI tickets.** If `STRUCTURE.md` declares no component directory, no layer-3 ticket exists.
- **IDs unique.** Every ID appears exactly once across `docs/issues/` and the fetched GitHub issues.
- **Dedup ran.** Confirm `gh issue list` was fetched before any `gh issue create`, and that no remote
  repository was created.
- **Security DoD present** on every ticket, including the ad-hoc ones.
- **Independently mergeable.** For each ticket ask: could one developer open a PR containing only these
  files and have it reviewed on its own? **If not, the split is wrong — STOP and re-split before publishing.**

## Step 4 — Handoff
"Backlog decomposed into layer-scoped tickets — each one assignable to a different developer and mergeable
on its own. Build them contract-first (layer 1 → 2 → 3, tests alongside): run **`/build`** on the first ticket,
one ticket per session."
