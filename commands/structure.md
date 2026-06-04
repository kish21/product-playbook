---
name: structure
description: >
  Phase 2 (Development), step 2 of product-builder — the FIRST thing you build. Set up a clean,
  industry-standard folder structure and explain what each folder is for and why, plus config/.env
  scaffolding and a prompts/ YAML folder for AI products. Use when starting to code, or run
  /structure "set up the project", "folder structure", "where does this go". Writes STRUCTURE.md +
  the Structure section of PRODUCT.md. Run /foundation next.
---

# `/structure` — Phase 2 · Development ② · run as a **senior engineer**

> Part of **product-builder**. Reads + updates the shared spine `PRODUCT.md`; writes `STRUCTURE.md`.
> Apply `PRINCIPLES.md` (bundled at `~/.claude/product-builder/PRINCIPLES.md`) — load-bearing: **modular/single-responsibility**, **layered sub-packages**,
> **intention-revealing naming**, **prompts externalized to `prompts/` YAML**, **no-hardcoding**.

> This skill exists because bad/ad-hoc folder structure is the #1 thing newcomers get wrong
> (god-files, "where does this go?"). The goal is not just to create folders — it is to **teach
> what each folder is for** so the layout stays clean as the product grows.

## Contract
- **Purpose:** a clean, explained folder layout + config/`.env` + (for AI) a `prompts/` YAML folder.
- **Reads:** `PRODUCT.md#Architecture` (stack decides the layout).
- **Writes:** `STRUCTURE.md` (folder→purpose map) + `PRODUCT.md#Structure` (summary).
- **Exit criteria:**
  - [ ] A folder tree exists, matching the chosen stack, with **layered sub-packages** (no god-files).
  - [ ] `STRUCTURE.md` explains **what each folder is for and why** (plain language).
  - [ ] Config lives in config/`.env` (a `.env.example`, never real secrets); **no hardcoded values**.
  - [ ] For AI products: a **`prompts/` YAML folder** exists; prompts are never inline in code.

## Step 0 — Context + prior-gate check
- Read `#Architecture`. If empty, warn and offer `/architect` first (allow override).
- Brownfield: read the existing tree; propose a clean target layout + a migration note, don't blindly move files.

## Step 1 — Apply principles (this phase)
- **One folder = one concern; dependencies point inward** (API → service/domain → data). No god-files.
- **Intention-revealing names** matching the stack's conventions. **Prompts are config:** AI prompts go in `prompts/*.yaml`, versioned, never inline (extends no-hardcoding).
- Reuse `/new-project`'s sub-package conventions where they fit; don't reinvent.

## Step 2 — Build the structure
1. Lay out the standard sub-package structure for the stack (e.g. API / service-domain / data layers,
   `config/`, `tests/`, `docs/`, and for AI `prompts/`). Create the folders + placeholder files.
2. Add config scaffolding: a config loader + a **`.env.example`** (names only, no secrets).
3. Write **`STRUCTURE.md`**: one line per folder — *what goes here and why*, in plain language a newcomer can follow.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Structure`: a short folder→purpose summary + the prompts location (AI). Point to `STRUCTURE.md`.

## Step 3b — Self-verify (completeness gate)
Check the boxes. **If `STRUCTURE.md` doesn't explain every folder, or an AI product has no `prompts/`
folder, STOP and fix it** — an unexplained layout decays into god-files.

## Step 4 — Handoff
"Clean structure in place and explained in `STRUCTURE.md`. Next run **`/foundation`** to make a
walking skeleton that actually runs (config, logging, infra, CI)."
