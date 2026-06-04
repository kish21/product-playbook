---
name: architect
description: >
  Phase 2 (Development), step 1 of product-builder. Decide the tech stack + tools + key
  architecture decisions, benchmarked to the best current-year open-source options, aligned
  to the product. Use at the start of building, or run /architect "what stack", "tech
  decisions", "how should we build this". Writes the Architecture section of PRODUCT.md.
  Run /structure next.
---

# `/architect` — Phase 2 · Development ① · run as an **architect**

> Part of **product-builder**. Reads + updates the shared spine `PRODUCT.md`.
> Apply `PRINCIPLES.md` (bundled at `~/.claude/product-builder/PRINCIPLES.md`) — load-bearing: **benchmark best-2026-OSS**, **provider/adapter for
> externals**, **typed-contracts intent**, **layered/decoupled**, **no-hardcoding**.

## Contract
- **Purpose:** choose the stack/tools/decisions before any folders exist, aligned to the product.
- **Reads:** `PRODUCT.md#Vision`, `#Scope`, `#Plan`.
- **Writes:** `PRODUCT.md#Architecture` — stack+tools+why · key decisions/ADRs · externals behind adapters.
- **Exit criteria:**
  - [ ] Stack + key tools chosen, each with a one-line **why** (benchmarked to current-year OSS-first).
  - [ ] Every external dependency (LLM, DB, vendor SDK, queue) named with the **adapter interface** it sits behind.
  - [ ] Key decisions recorded as short ADRs (decision · why · rejected alternative).
  - [ ] Decisions trace to the scope/plan (not gold-plating for out-of-scope items).
  - [ ] A **migrations** approach chosen for any datastore (never hand-edited schema).
  - [ ] The **concern areas to design for** named (security, observability, testing, docs, DX, + AI-specific if AI) — what the architecture must accommodate; **no secret in code** (secrets→`.env`).

## Step 0 — Context + prior-gate check
- Read `#Vision/#Scope/#Plan`. If `#Scope`/`#Plan` are empty, warn and offer to run them first (allow override).
- Brownfield: detect the existing stack from the repo and record it as the starting point.

## Step 1 — Apply principles (this phase)
- **Benchmark to the current year, OSS-first:** pick what leading teams use *now*; prefer open source unless told otherwise. Justify each choice in one line.
- **Provider/adapter for every external:** no vendor SDK in business logic — wrap it behind a config-selected interface so it's swappable via `.env`.
- **No-hardcoding & typed contracts:** decisions must keep values in config and payloads typed.

## Step 2 — Guided decisions
1. **What kind of system is it?** (web app · API · CLI · data/ML · agentic). Match the scope, not ambition.
2. **Choose the stack core** (language · framework · datastore · key libs). One-line why each; flag anything paid and its trigger to adopt.
3. **List every external** and the **adapter interface** it will hide behind (e.g. `LLMProvider`, `Storage`). This is what keeps it swappable and testable.
4. **Record 2–4 ADRs** for the load-bearing choices (decision · why · rejected alternative).
- Give **one recommendation** for the stack; get a yes/no.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Architecture`: stack+tools+why · key decisions/ADRs · externals behind adapters.

## Step 3b — Self-verify (completeness gate)
Check the boxes. **If any external lacks an adapter interface, STOP and add it** — a vendor SDK
imported directly into logic is the lock-in/dead-config trap this skill exists to prevent.

## Step 4 — Handoff
"Stack and decisions recorded. Now build the **first concrete thing**: run **`/structure`** to lay
out clean folders and explain what each is for."
