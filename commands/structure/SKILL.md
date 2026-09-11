---
name: structure
description: >
  Phase 2 (Development), step 2 of product-playbook — the FIRST thing you build. Choose the project's
  SHAPE (domain modules by default, or layers) and explain what each folder is for and why, plus the
  root scaffolding every project needs — agent instructions, ignore rules, .env.example, secret-scan,
  commit hooks, a task runner — using the TOOLS #Architecture chose, and a prompts/ YAML folder for AI.
  Use when starting to code, or run /structure "set up the project", "folder structure", "where does
  this go". Writes STRUCTURE.md + the Structure section of PRODUCT.md. Run /foundation next.
---

# `/structure` — Phase 2 · Development ② · run as a **senior engineer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution); writes `STRUCTURE.md`.
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing:
> **modular/single-responsibility**, **layered sub-packages**, **intention-revealing naming**,
> **prompts externalized to `prompts/` YAML**, **no-hardcoding (secrets→`.env`, knobs→config)**,
> **no secret in any code file**.

> This skill exists because bad/ad-hoc folder structure is the #1 thing newcomers get wrong (god-files,
> "where does this go?"). The goal is not just to create folders — it is to **teach what each folder is
> for** so the layout stays clean as the product grows. Adapt names to the chosen stack, but always lay
> the same solid base.

## Contract
- **Purpose:** a chosen, explained layout + the root scaffolding files + (AI) `prompts/`.
- **Reads:** `PRODUCT.md#Architecture` — the **stack** *and* the **Dev tooling** line (which decides the
  tool in every scaffolding slot); `#Scope` (the concerns that become modules); `#Vision` (AI product?).
- **Writes:** `STRUCTURE.md` (folder→purpose map) + `PRODUCT.md#Structure` (summary).
- **Gate type:** `derivation` — computable from `#Architecture` + the stack. Batchable - a `derivation` run may chain with its neighbours and end in ONE review. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes `#Structure` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Exit criteria:**
  - [ ] **The project's agent instructions exist** (`CLAUDE.md` / `AGENTS.md` — one may point at the
    other), from `templates/AGENTS.md`: a **pointer** to the spine plus the rules an agent breaks first,
    **never a copy of `PRODUCT.md`**. Five skills read this file and `/drift-check` polices it; nothing
    created it. **Write outside any tool-owned `<!-- BEGIN: -->` block** — those are rewritten every run.
  - [ ] **The SHAPE was chosen, stated and recorded** — domain modules (the default: one folder per thing
    the product does) or layers — with a one-line why in `STRUCTURE.md`. A shape nobody chose is a
    decision nobody can revisit. Dependencies point inward either way; no god-files.
  - [ ] `STRUCTURE.md` explains **what each folder is for and why**, in plain language.
  - [ ] **`STRUCTURE.md`'s map and the real tree agree BOTH ways** — proven by `scripts/check_structure.py`
    (Step 3b), not by eye. A drawn-but-uncreated folder is silent doc↔code drift; an unmapped folder on
    disk is a layout decision nobody recorded.
  - [ ] Root scaffolding present — each a **capability**, filled by the tool `#Architecture` recorded (the
    playbook never dictates the tool): `README.md` · ignore rules · `.env.example` · **secret-scan config**
    · **commit-hook runner** · **task runner** · **dependency manifest** (dev/prod split) · `SECURITY.md` ·
    `CHANGELOG.md` (Keep a Changelog, seeded with `[Unreleased]`).
  - [ ] **Every scaffolded tool matches `#Architecture`'s Dev tooling line.** `.pre-commit-config.yaml` in
    a Node repo whose ADR chose lefthook makes the recorded trail describe a tool the repo does not use,
    and forces a Node contributor to install Python tooling to commit. No tool recorded for a slot →
    **recommend one that fits the detected stack, say why, and record it back**.
  - [ ] **The config-layering files are actually scaffolded**, not an empty `config/`: a **typed loader**
    in the project's own language + `platform.yaml` (engine knobs) + `product.yaml` (product knobs),
    reading `.env` — the no-hardcoding engine.
  - [ ] Ignore rules cover `.env` **and its variants/backups** (`.env.bak`, `*.env.local`); only `.env.example` is committed. **No secret in any code file.**
  - [ ] **Dependency manifest: this phase owns its EXISTENCE AND SHAPE** — the file, the dev/prod split,
    project metadata (`MECHANISMS.md` §Seam); versions, the install and tool configs belong to
    `/foundation`. **Leave no script that cannot run** — it runs now, or it is marked as arriving with
    `/foundation`. Green while `make check` fails is a lie.
  - [ ] **`.env.example` declares the isolated test datastore** (`TEST_DATABASE_URL` or equivalent) as its
    own variable, never the development one — `/test` runs against real boundaries, so the two values must
    differ. `/foundation` provisions it and guards it.
  - [ ] **`.env.example` holds only unmistakable placeholders** — `CHANGE_ME__<VAR>__CHANGE_ME`, never a
    realistic-looking string long enough to pass validation (`replace-me-with-32-plus-random-characters`
    is 48 chars and **passes** `min(32)`, so a copied `.env` boots the app on a signing key that is public
    in git). Each carries a one-line comment on generating the real value; `/foundation` **rejects them by
    name** at boot (`PRINCIPLES.md` §Production safeguards).
  - [ ] For AI products: a **`prompts/` YAML folder inside the backend package** (root `prompts/` only
    when there is no backend package) — prompts never inline in code.

## Step 0 — Context + prior-gate check
- Read `#Architecture` and `#Vision` (AI?). Take **two** things from `#Architecture`: the **stack**, and
  the **Dev tooling** line (hook runner · secret scanner · task runner · linter · dependency manifest),
  **which decides every scaffolding file you are about to write**. Reading only the stack is how a
  recorded tool choice gets silently overridden one phase later.
- **Read the recorded runtime target before writing any infra file** — `#Architecture`'s custody + runtime
  line decides what is appropriate at all: **no `docker-compose.yml` for a target that does not use one**
  (managed-serverless data, a PaaS, an embedded datastore). A compose file written by habit is an artifact
  the project must later delete, and implies a custody decision nobody made.
- If `#Architecture` is empty, warn and offer `/architect` first (allow override). Running standalone, detect the stack from the repo and pick tooling that fits it — then record the choice so the next phase inherits it.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate, ask for the **reason in the user's own words**, and write `Override <date>: <reason> — bypassed <gate>` at the top of `#Structure` before continuing. Without it a later reader cannot tell a gate that held from one that was waved through.
- Brownfield: read the existing tree; propose a clean target layout + a migration note — don't blindly move files.
- **Re-running — `MECHANISMS.md` §Re-run semantics, in full.** The section is already filled → show what would change and ask first; a reversed decision keeps its dated `superseded` line.
- **Stopping at an unmet gate — `MECHANISMS.md` §Declined runs, in full.** One dated `_Not run_` line at the top of `#Structure`, nothing else touched; the section stays unfilled so `/playbook` still routes here.

## Step 1 — Apply principles (this phase)
- **One folder = one concern; dependencies point inward** (api → service/domain → data). No god-files.
- **No-hardcoding:** secrets go to `.env`; tunable knobs to layered config; **never a key/secret in a code file**.
- **Prompts are config (AI):** `app/prompts/*.yaml` (backend sub-package), versioned, never inline.
- Keep sub-package conventions consistent across the tree; don't reinvent per folder.

## Step 2 — Lay the structure (pick the shape, then adapt names to the stack)

### 2a — Choose the SHAPE: by concern, or by layer. State the choice.

**One rule holds in both shapes and is not the question here:** dependencies point inward — routes may
call domain logic; domain logic never imports a route or a vendor SDK.

The question is **where a feature lives**. Take a real one — "how a bill is split" — and see how many
folders it lands in. `PRINCIPLES.md` says *one module = one concern*, and in product terms a concern is
`split`, `ocr`, `bills`. **`schemas/` is not a concern, it is a file type** — a tree of file types
satisfies the letter of that rule while inverting it: the thing a developer actually changes is the one
thing that is not modular.

- **Domain modules — the default.** Take it when the product has **two or more concerns with their own
  rules**, which is most products. One folder per thing the product *does*, each holding everything that
  concern needs (its types, its persistence, its logic) and declaring what it may depend on.
- **Layers** — take it for a genuinely single-concern service (one CRUD resource, a thin gateway, a
  library), or where the team already works that way. Then the layer folders below are the shape.

**Say which you chose and why, in one line, before you draw anything** — and record it in `STRUCTURE.md`.
This was a silent default for every project the playbook scaffolded; a shape nobody chose is a decision
nobody can revisit. It also sets this phase's own cost: `STRUCTURE.md` writes one rationale per folder,
so four modules is a shorter document than thirteen layers, with no loss.

```
src/
├── split/        # per-person totals: items + assignments + charges -> transfers. Pure. Depends on: nothing
├── bills/        # persistence, share-slug identity, image lifecycle.        Depends on: db, storage
├── ocr/          # image bytes -> typed ParsedBill, behind a config-selected interface. Depends on: LLM provider
├── app/          # screens and routes — thin.                                Depends on: all of the above
├── config/       # loader + layered config (see below)
└── shared/       # only what two or more modules genuinely share — never a dumping ground
```

**Each module owns its own boundary types** — the typed contract in and out lives with the module, not in
a global `schemas/`. A module's dependency line is part of its definition: write it down, and a module
that depends on everything is a module that has not been decided yet.

### 2b — The layered shapes (when 2a chose layers)

Three trees — backend, frontend, and full-stack (backend `app/` and `frontend/` side by side) — plus the
**layered `config/` pattern** that keeps secrets and tunables out of code. **Open
`references/layered-shapes.md` and follow it**; it also carries the AI/agentic sub-packages
(`agents/` · `pipeline/` · `prompts/` · `retrieval/`), which attach to whichever shape you chose.

**Root scaffolding (every shape):** README · **agent instructions** (`CLAUDE.md`/`AGENTS.md`) ·
ignore rules · `.env.example` · `CONTRIBUTING.md` ·
secret-scan config · commit-hook runner · `SECURITY.md` · `CHANGELOG.md` · task runner ·
dependency manifest with a dev/prod split · `tests/` · `docs/` · `tools/`. Each is a **capability**,
filled by the tool `#Architecture` named — **open `references/root-scaffolding.md`** for the exact
list, the per-tool choices, the conditional files (containers, CI, migrations, evals) and the task
runner's generic targets.

## Step 3 — Write back
Write **`STRUCTURE.md`** (one line per folder — *what goes here and why*, plain language). Fill
`PRODUCT.md#Structure` with the summary + the prompts location (AI).

## Step 3b — Self-verify (completeness gate)
**Copy `templates/check_structure.py` into the project** (`scripts/`, or wherever `STRUCTURE.md` puts
tooling), **commit it, and run it** — it compares the map against the tree in **both** directions and
exits non-zero on either mismatch, which is faster and stricter than reading 25 folders by eye. It is
committed rather than scratch because the transition guard re-runs `evidence:` lines in later sessions:
the line it produces names the script, its result, `STRUCTURE.md` and today's date.

Check the boxes. **STOP and fix if:** a folder is unexplained; **the map and the tree disagree either
way** (the script says which); ignore rules don't cover `.env*`;
the secret-scan config or the commit-hook runner is missing; **`.env.example` holds any value that would
survive a plausible validity check** (it must be an unmistakable placeholder — see the criterion above);
a secret sits in a code file; or an AI product has no `prompts/` folder. An unexplained layout decays
into god-files; a leaked `.env` is a real incident.

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and **offer to commit the change** (`MECHANISMS.md` §Commit the work — check the repo exists, name the branch, offer the message, push only if a remote exists and the user says so). Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal. **Close in plain language** (`MECHANISMS.md` §Plain-language close): two or three sentences of *what just happened* with no playbook dialect, then a numbered *what YOU do next* — the user's own actions, dated where they are time-bound, or "Nothing — you're done".

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase produced against decisions **already recorded** — here `#Architecture`, **especially its Dev tooling line**: every scaffolding file must be the tool recorded there (a run once scaffolded `.pre-commit-config.yaml` into a Node repo whose ADR chose lefthook, and nothing noticed). On a conflict **name both sides, ask which wins, update the loser**. Carry any decision still OPEN forward (§Step 3c item 4). Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Clean structure + root scaffolding in place and explained in `STRUCTURE.md`.
- **User-facing UI?** Run **`/design-system`** next — principles, a confirmed sample page and a concrete
  `DESIGN.md` *before* any screen is built, so the UI doesn't end up generic. Then `/foundation`.
- **Backend/API/CLI only:** straight to **`/foundation`** for a walking skeleton that actually runs."
