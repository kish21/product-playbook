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
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **`status.py next --phase adopt` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it). Load-bearing: **no assumptions / verify against the real code**, **honesty
> (label what is inferred; never fabricate)**, **docs must match reality**, **plain-language
> communication**, **one clear recommendation + yes/no**.

## Contract
- **Purpose:** turn an existing repo into a confirmed `PRODUCT.md`, without inventing anything.
- **Reads:** the repository — `CLAUDE.md` · `README.md` · `docs/` · `AGENTS.md` · `CHANGELOG` · package
  metadata (`package.json`, `pyproject.toml`, …) · entry points · routes · tests · CI config.
- **Writes:** `PRODUCT.md` (only after the owner confirms) with a one-line provenance note naming which
  files it was drawn from, and `STATUS.md` through `status.py` (`MECHANISMS.md` §Status).
- **Must NOT:** write code, change the repo's files, guess a north star, assumption, business model or Non-goal, or write before the owner's yes.
- **Gate type:** `input` — every inferred line is confirmed by the owner section by section. **Never batched** - skipping it fabricates the product's premise. (`STATE-MODEL.md` §2d)
- **Exit criteria:**
  - [ ] **Every inferred line is tagged `(inferred — confirm)`** until the owner confirms it. A finished
        `PRODUCT.md` contains **no un-tagged claim that was not confirmed**.
  - [ ] **A section with no evidence stays empty.** Never a guess dressed as a record — an empty section
        correctly means "this phase's exit criteria are not met yet".
  - [ ] The owner walked the **confirm-loop** (keep / correct / drop) before anything was written. This
        skill **stops**; it does not auto-write.
  - [ ] `PRODUCT.md` carries the provenance note, and `STATUS.md` records each confirmed section `filled` as "adopted <date>" (the record call).
  - [ ] **Idempotent:** an existing `PRODUCT.md` is **never overwritten** — offer to fill only its empty
        sections, and leave every filled one alone.
  - [ ] A recommended next skill, chosen from what is still empty and stated in one line.

## Step 0 — Refuse to clobber, then survey
- **First turn, ONE command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase adopt`** — it surveys the repo (docs, package metadata, entry points, routes, tests, CI), says whether `PRODUCT.md` exists, and prints the rules; never the rule files whole. Show its first line.
- **If `PRODUCT.md` already exists, stop and say so.** Offer exactly one thing: to fill the sections that
  are still **empty**, leaving every filled section untouched. Re-adopting a project is not a reason to
  overwrite a record someone wrote by hand.
- Otherwise **say which files the start found** (`MECHANISMS.md` §Spine resolution order) — the user should
  know what this reading is based on before they trust any of it; open only those.

## Step 1 — Apply principles (this phase)
- **Never fabricate.** Code tells you *what* was built. It cannot tell you *why*, for *whom*, what was
  deliberately **not** built, or what the riskiest assumption is. Those are the owner's to supply.
- **Label the boundary between the two.** Everything drawn from the repo is `(inferred — confirm)`;
  everything the owner states becomes a plain line. The tag is what keeps a guess from hardening into a
  fact three sessions later.
- **Evidence beats inference:** an explicit "not doing" list in a README is a real Non-goal; a feature
  that merely doesn't exist is **not**.

## Step 2 — Draft, from the bundled `PRODUCT.md` template (`${CLAUDE_PLUGIN_ROOT}/templates/PRODUCT.md`)
Fill only what the repo can actually support:

| Section | Draw it from | Leave empty when |
|---|---|---|
| **Vision** | README/CLAUDE.md "what and why", package description | there is no stated purpose — do **not** infer a market or a north star |
| **Scope** | features that demonstrably exist (routes, commands, entry points) | Non-goals unless an explicit "not doing"/"out of scope" list exists |
| **Architecture** | package metadata, lockfiles, imports of external SDKs, CI, containers | no ADR rationale exists — record the *what*, never invent the *why* |
| **Structure** | the real folder tree | — |
| **Foundation / Tests** | CI config, test dirs, what the pipeline actually runs | there is no CI — say "none found", which is a finding |
| **Tickets** (`status.py ticket`) | features found + **how each can be verified today** | you cannot state a verification — an unverifiable row is noise |

**The north star, the riskiest assumption, the business model and the Non-goals are almost never
inferable.** Leave them empty and say plainly that these are the parts only the owner knows — that is the
honest result, not a gap in the skill.

## Step 3 — Confirm-loop (this is the skill's real work)
**Two rounds, each ONE message:** round 1 — the whole draft, **keep / correct / drop** per line, with the
evidence beside each inferred line ("Scope — 'CSV export' — inferred from `src/routes/export.ts`"), plus the
owner-only questions (who and why, north star, riskiest assumption, business model, never-build list; "don't
know" leaves it empty); round 2 — the corrected draft, any Step 3c clash, and *"Looks good - save
(Recommended)"* / *"Change something"* (no drawn options: *"Save this version of your project? (yes / no)"*).
Keep it short and plain; a newcomer should not feel interrogated. **Nothing is written until this
finishes** — and a section the owner cannot speak to stays empty rather than being kept on a shrug.

## Step 3b — Self-verify (before writing)
Check the boxes. **STOP if:** any line in the draft is a claim the repo does not support; any section was
filled from absence rather than evidence; a Non-goal was inferred from a missing feature; or an existing
`PRODUCT.md` would be overwritten. **A fabricated spine is far worse than no spine** — every later phase
gates against it, and `/drift-check` would then measure drift from fiction.

**Close the loop (`MECHANISMS.md` §Step 3b):** ONE call records it — `status.py set adopt filled --section-from <draft> --product "<name>" --commit "<one line>"` (`--dry-run` writes nothing; no `--commit` on a no: `MECHANISMS.md` §Commit the work); a verification phase stays empty; it refuses what the start lists —
reconcile any number carried in from the repo against what the owner just confirmed. Then **run the transition guard** (`MECHANISMS.md`
§Step 3b, item 4): re-run any `evidence:` line this draft carried in and report a verdict for every
criterion — an inferred spine is *full* of claims nobody has re-measured, so `UNVERIFIED` will be the
common answer here, and saying so is the point — and check the transition is legal. **Close in plain language** (`MECHANISMS.md` §Plain-language close): four blocks in order, each under its bolded name: **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next**, ending with the `Open a NEW conversation` line the record call printed, word for word.

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check the draft against decisions **already recorded** — here: the
project's own docs. Where `README.md` and the code disagree (a documented feature that no longer exists,
a stack the README still names), **name both sides, ask which is true now, and record the answer** —
never silently prefer one. A doc that has drifted from its code is the single most common thing an
adoption finds, and recording *which* was stale is worth more than quietly picking the code.

## Step 4 — Handoff
The record call's last line names **the earliest phase in the chain that is not done**, by these rules;
say why in one line. **Never recommend a phase whose own Step 0 would reject the project**: read the target skill's
`Reads:` line first; if what it reads is empty, recommend the phase that fills it instead.
(case file: Sent to a gate that sends you back)
- `#Vision` has no vision sentence, audience or value proposition → **`/vision`** (code shows *what* was
  built, never *why* or *for whom* — an empty Vision is the normal result of adopting);
- Vision confirmed, no core feature or no Non-goals → **`/scope`** (the anti-creep list is the most
  valuable thing a half-built project lacks);
- otherwise → **`/playbook`**, which will now orient properly because the spine exists.

> "Adopted: `PRODUCT.md` written from <files>, confirmed by you. <N> sections left empty because the repo
> couldn't evidence them — that is accurate, not missing. Next: **`/<skill>`**, because <reason>."
