---
name: adopt
description: >
  Entry skill of product-playbook (cross-cutting — run ANYTIME). Brings an existing, half-built project
  into the playbook by drafting an INFERRED PRODUCT.md from what the repo actually contains — docs,
  package metadata, entry points, routes, tests, CI — then walking the owner through a confirm-loop
  before writing anything. Use when a project already has code but no spine, or run /adopt "adopt this
  project", "we already started", "set up the playbook on an existing repo", "create a PRODUCT.md from
  what we have". Writes PRODUCT.md with a provenance note. Run the recommended next phase after.
---

# `/adopt` — bring an existing project into the playbook · run as a **careful archaeologist**

> Part of **product-playbook**. This is an **entry** skill, like `/playbook` — not a phase in the
> vision→learn chain. It **creates** the spine that `MECHANISMS.md` §Spine resolution otherwise only
> knows how to *read*.
> Apply `PRINCIPLES.md` — load-bearing: **no assumptions / verify against the real code**, **honesty
> (label what is inferred; never fabricate)**, **docs must match reality**, **plain-language
> communication**, **one clear recommendation + yes/no**.

> **Why this exists.** §Spine resolution tells every skill how to *read* a project that has no
> `PRODUCT.md` — `CLAUDE.md` → `README.md` → `docs/` → `AGENTS.md`, else infer from code and label it
> INFERRED. But **nothing ever created that spine.** A user midway through a build got a fresh
> low-confidence guess on every run and no offer to turn it into a record, and `/playbook`'s brownfield
> branch only said "enter at `/architect` or `/build`". A midway user will not think to run a *guided
> start*; they will understand **"adopt this project"**.

## Contract
- **Purpose:** turn an existing repo into a confirmed `PRODUCT.md`, without inventing anything.
- **Reads:** the repository — `CLAUDE.md` · `README.md` · `docs/` · `AGENTS.md` · `CHANGELOG` · package
  metadata (`package.json`, `pyproject.toml`, …) · entry points · routes · tests · CI config.
- **Writes:** `PRODUCT.md` (only after the owner confirms), header `Stage: adopted <date>` + a one-line
  provenance note naming which files it was drawn from.
- **Exit criteria:**
  - [ ] **Every inferred line is tagged `(inferred — confirm)`** until the owner confirms it. A finished
        `PRODUCT.md` contains **no un-tagged claim that was not confirmed**.
  - [ ] **A section with no evidence stays empty.** Never a guess dressed as a record — an empty section
        correctly means "this phase's exit criteria are not met yet".
  - [ ] The owner walked the **confirm-loop** (keep / correct / drop) before anything was written. This
        skill **stops**; it does not auto-write.
  - [ ] `PRODUCT.md` carries `Stage: adopted <date>` and the provenance note.
  - [ ] **Idempotent:** an existing `PRODUCT.md` is **never overwritten** — offer to fill only its empty
        sections, and leave every filled one alone.
  - [ ] A recommended next skill, chosen from what is still empty and stated in one line.

## Step 0 — Refuse to clobber, then survey
- **If `PRODUCT.md` already exists, stop and say so.** Offer exactly one thing: to fill the sections that
  are still **empty**, leaving every filled section untouched. Re-adopting a project is not a reason to
  overwrite a record someone wrote by hand.
- Otherwise survey what exists, in `MECHANISMS.md` §Spine resolution order, and **say which files you
  found** — the user should know what this reading is based on before they trust any of it.

## Step 1 — Apply principles (this phase)
- **Never fabricate.** Code tells you *what* was built. It cannot tell you *why*, for *whom*, what was
  deliberately **not** built, or what the riskiest assumption is. Those are the owner's to supply.
- **Label the boundary between the two.** Everything drawn from the repo is `(inferred — confirm)`;
  everything the owner states becomes a plain line. The tag is what keeps a guess from hardening into a
  fact three sessions later.
- **Evidence beats inference:** an explicit "not doing" list in a README is a real Non-goal; a feature
  that merely doesn't exist is **not**.

## Step 2 — Draft, from the bundled `PRODUCT.md` template
Fill only what the repo can actually support:

| Section | Draw it from | Leave empty when |
|---|---|---|
| **Vision** | README/CLAUDE.md "what and why", package description | there is no stated purpose — do **not** infer a market or a north star |
| **Scope** | features that demonstrably exist (routes, commands, entry points) | Non-goals unless an explicit "not doing"/"out of scope" list exists |
| **Architecture** | package metadata, lockfiles, imports of external SDKs, CI, containers | no ADR rationale exists — record the *what*, never invent the *why* |
| **Structure** | the real folder tree | — |
| **Foundation / Tests** | CI config, test dirs, what the pipeline actually runs | there is no CI — say "none found", which is a finding |
| **Build log** | features found + **how each can be verified today** | you cannot state a verification — an unverifiable row is noise |

**The north star, the riskiest assumption, the business model and the Non-goals are almost never
inferable.** Leave them empty and say plainly that these are the parts only the owner knows — that is the
honest result, not a gap in the skill.

## Step 3 — Confirm-loop (this is the skill's real work)
Walk the owner through **each drafted section, one at a time**: **keep / correct / drop**. Show the
evidence beside each inferred line ("Scope — 'CSV export' — inferred from `src/routes/export.ts`").
Keep it short and plain; a newcomer should not feel interrogated. **Nothing is written until this
finishes** — and a section the owner cannot speak to stays empty rather than being kept on a shrug.

## Step 3b — Self-verify (before writing)
Check the boxes. **STOP if:** any line in the draft is a claim the repo does not support; any section was
filled from absence rather than evidence; a Non-goal was inferred from a missing feature; or an existing
`PRODUCT.md` would be overwritten. **A fabricated spine is far worse than no spine** — every later phase
gates against it, and `/drift-check` would then measure drift from fiction.

**Close the loop (`MECHANISMS.md` §Step 3b):** set the header (`Stage: adopted <date>`, `Last updated:`),
reconcile any number carried in from the repo against what the owner just confirmed, and end with a
suggested one-line commit message in the repo's convention.

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check the draft against decisions **already recorded** — here: the
project's own docs. Where `README.md` and the code disagree (a documented feature that no longer exists,
a stack the README still names), **name both sides, ask which is true now, and record the answer** —
never silently prefer one. A doc that has drifted from its code is the single most common thing an
adoption finds, and recording *which* was stale is worth more than quietly picking the code.

## Step 4 — Handoff
Write `PRODUCT.md`, then recommend the next skill **from what is still empty** — in one line, with why:
- no Non-goals → **`/scope`** (the anti-creep list is the most valuable thing a half-built project lacks);
- a riskiest assumption that was never tested → **`/validate`**;
- Vision confirmed and the rest empty → **`/playbook`**, which will now orient properly because the spine
  exists.

> "Adopted: `PRODUCT.md` written from <files>, confirmed by you. <N> sections left empty because the repo
> couldn't evidence them — that is accurate, not missing. Next: **`/<skill>`**, because <reason>."
