---
name: structure
description: Lay out the folders and what each one is for.
---

# `/structure` — Phase 2 · Development ② · run as a **senior engineer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution); writes `STRUCTURE.md`.
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` · AGENT.md = `${CLAUDE_PLUGIN_ROOT}/references/agent.md`, only when `Agent: yes` (a path still starting with `$`: the variable is the folder two levels above this SKILL.md, holding `commands/` and `PRINCIPLES.md` - never another tool's install). If `python` will not start (not found, or a sandbox refuses it): `python3`, else `py -3`, else the project's `.venv` Python - never a hunt; later commands use the start's `Run this copy as` line.
> **This skill's OWN reference files are a DIFFERENT folder** — they live in `references/` **beside this SKILL.md** (`commands/structure/references/`), not in the plugin-root `references/` named above. Both install routes put them there. Below, `choosing-the-shape.md` · `layered-shapes.md` · `root-scaffolding.md` · `edge-cases.md` each mean that folder: open them by that path, and never look for them next to MECHANISMS.md.
> **`status.py next --phase structure` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it); the rest of the close prints when `set structure filled` passes. Load-bearing here:
> **modular/single-responsibility**, **layered sub-packages**, **intention-revealing naming**,
> **prompts externalized to `prompts/` YAML**, **no-hardcoding (secrets→`.env`, knobs→config)**,
> **no secret in any code file**.

> This skill exists because bad/ad-hoc folder structure is the #1 thing newcomers get wrong (god-files,
> "where does this go?"). The goal is to **teach what each folder is for**, not just create it, so the
> layout stays clean as it grows. Adapt names to the chosen stack, but always lay the same solid base.

## Contract
- **Purpose:** a chosen, explained layout + the root scaffolding files + (AI) `prompts/`.
- **Reads:** `PRODUCT.md#Architecture` — the **stack** *and* the **Dev tooling** line (which decides the
  tool in every scaffolding slot); `#Scope` (the concerns that become modules); the AI and agent flags — as `next` prints them.
- **Writes:** `STRUCTURE.md` (folder→purpose map) + `PRODUCT.md#Structure` (summary); re-run after `/tickets`: moved paths in `docs/issues/`, `TICKETS.md`, open issues.
- **Gate type:** `derivation` — computable from `#Architecture` + the stack. Batchable - a `derivation` run may chain with its neighbours and end in ONE review. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Structure` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Exit criteria:** `set structure filled` refuses each countable one, every gap in one list:
  - [ ] **The project's agent instructions exist** (`CLAUDE.md` / `AGENTS.md` — one may point at the
    other), from `templates/AGENTS.md`: a **pointer** to the spine plus the rules an agent breaks first,
    **never a copy of `PRODUCT.md`**. Five skills read this file and `/drift-check` polices it; nothing
    created it. **Write outside any tool-owned `<!-- BEGIN: -->` block** — those are rewritten every run.
  - [ ] **The SHAPE was chosen, stated and recorded** — domain modules (the default: one folder per thing
    the product does) or layers — with a one-line why in `STRUCTURE.md`. A shape nobody chose is a
    decision nobody can revisit. Dependencies point inward either way; no god-files.
  - [ ] **A module is a complete lane** (`references/choosing-the-shape.md` §A module is a complete lane):
    routes, handlers, store and tests live inside the module folder; the app reaches it through one
    registry line; `platform/` holds only what no module owns; the frontend follows the same rule. **`STRUCTURE.md`
    names the hub files** under `## Hub files`, each verified to exist by `check_structure.py`.
  - [ ] `STRUCTURE.md` explains **what each folder is for and why**, in plain language.
  - [ ] **`STRUCTURE.md`'s map and the real tree agree BOTH ways** — proven by `scripts/check_structure.py`
    (Step 3b), not by eye. A drawn-but-uncreated folder is silent doc↔code drift; an unmapped folder on
    disk is a layout decision nobody recorded.
  - [ ] Root scaffolding present — each a **capability**, filled by the tool `#Architecture` recorded:
    `README.md` · ignore rules · `.env.example` · **secret-scan config**
    · **commit-hook runner** · **task runner** · **dependency manifest** (dev/prod split) · `SECURITY.md` ·
    `CHANGELOG.md` (Keep a Changelog, seeded with `[Unreleased]`).
  - [ ] **Every scaffolded tool matches `#Architecture`'s Dev tooling line** (case file: The tool nobody
    chose). No tool recorded for a slot →
    **recommend one that fits the detected stack, say why, and record it back**.
  - [ ] **The config-layering files are scaffolded**, not an empty `config/`: a **typed loader**
    in the project's own language + `platform.yaml` (engine knobs) + `product.yaml` (product knobs),
    reading `.env` — the no-hardcoding engine. ONE loader, beside the YAML or where `STRUCTURE.md` names it.
  - [ ] Ignore rules cover `.env` **and its variants/backups** (`.env.bak`, `*.env.local`); only `.env.example` is committed. **No secret in any code file.** An existing `.gitignore` is added to, never replaced.
  - [ ] **Folders, config and empty modules only — product logic is `/build`'s.**
  - [ ] **It runs** (`MECHANISMS-ON-DEMAND.md` §Seam): the manifest (dev/prod split) with a **real lockfile**
    the package manager wrote, installed from; **the linter and ONE smoke test pass** (it imports every module; a
    `CHANGE_ME` value fails the boot), their last lines in `#Structure`'s evidence. No network: `lock pending`.
    **Leave no script that cannot run** — it runs now, or it is marked as arriving with `/foundation`.
  - [ ] **`.env.example` declares the isolated test datastore** (`TEST_DATABASE_URL` or equivalent) as its
    own variable, never the development one — `/test` runs against real boundaries, so the two values must
    differ. `/foundation` provisions it and guards it.
  - [ ] **`.env.example` holds only unmistakable placeholders** — `CHANGE_ME__<VAR>__CHANGE_ME`, never a
    realistic-looking string long enough to pass validation (case file: The placeholder that booted). Each
    carries a one-line comment on generating the real value; `/foundation` **rejects them by
    name** at boot (`PRINCIPLES.md` §Production safeguards).
  - [ ] **`Agent: yes`: every AGENT.md §Structure row** has a home in `STRUCTURE.md` (folders created), or N/A.
  - [ ] For AI products: a **`prompts/` YAML folder inside the backend package** (root `prompts/` only
    when there is no backend package) — prompts never inline in code.

## Step 0 — Context + prior-gate check
- **First turn, ONE command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase structure`** — and, in the same message, open `references/choosing-the-shape.md` and `${CLAUDE_PLUGIN_ROOT}/templates/structure.md`. Read nothing else whole: the start prints `#Architecture` whole and the rest this phase derives from. Show its first line; close by its checklist.
- **The Dev tooling line decides every scaffolding file**, and **the recorded runtime target decides what infra is appropriate at all** — **no `docker-compose.yml` for a target that does not use one** (managed-serverless data, a PaaS, an embedded datastore). Open an ADR only when a line of `#Architecture` points into it and you need more; quote it in a `Read:` line.
- `#Architecture` empty (the start says so) → warn and offer `/architect` first (allow override). Running standalone, detect the stack from the repo and pick tooling that fits it — then record the choice so the next phase inherits it.
- Brownfield (the start lists the code): read the existing tree; propose a clean target layout + a migration note — don't blindly move files.
- **Anything unusual — an override, a re-run (a shape change after `/tickets` included), stopping at an unmet gate, a refusal the user says does not apply:** open `references/edge-cases.md` (beside this SKILL.md) for that case; a normal first run never opens it.

## Step 1 — Principles
Printed by the start (the architecture bar, the safeguards that decide a file): apply them.

## Step 2 — Lay the structure (pick the shape, then adapt names to the stack)

### 2a — The shape, in two decisions. **Follow `references/choosing-the-shape.md`.**

1. **The split is classified from the PRODUCT, not asked and not read off the stack.** UI *and*
   server-side logic/data/externals → **full-stack → two folders** (a backend package and `frontend/`).
   The stack names what is *inside* each; a UI-tooling constraint binds the UI only. **Collapsing them
   into one app is the exception, recorded with a reason** — and if `#Architecture`'s stack implies a
   shape that disagrees with this classification, **surface it rather than following the stack**.
2. **Then how folders are organised: by concern (the default) or by layer.** Domain modules — one folder
   per thing the product *does*, owning its own types, persistence, logic, **routes and tests**, reached
   through one registry line (§A module is a complete lane) — unless this is a genuinely single-concern
   service. Dependencies point inward either way. **Say which and why in one line, in `STRUCTURE.md`,
   before drawing anything**: a shape nobody chose is a decision nobody can revisit.

### 2b — Layers, and the root scaffolding

When 2a chose layers, **open `references/layered-shapes.md` and follow it** (backend, frontend and full-stack
trees, the layered `config/` pattern, the AI sub-packages `agents/` · `pipeline/` · `prompts/` · `retrieval/`).
**Root scaffolding (every shape):** the list the start prints from `references/root-scaffolding.md` — each a
**capability**, filled by the tool `#Architecture` named; one folder = one concern; sub-package conventions
the same across the tree.

## Step 3 — Write it, in order (big writes last)
1. **Decide and ask first** — the shape, modules, homes, any question, first; a question goes through your question tool (4 per call: more in several calls in that same message), else numbered options: 2–4 options, ONE (Recommended) with its reason, Other last.
2. Write every folder and starter file in **ONE call**: ONE bundle outside the repo: `STRUCTURE.md` + only
   what the product's decisions shape, then `status.py scaffold
   --from <bundle>`; **it writes the standard files — never type them**. Write **`STRUCTURE.md`** (one line per folder — *what goes here and why*, plain language) with **five
sections, each a table with one backticked path per row** (backtick paths only: `check_structure.py` reads a
backticked name such as `LLMProvider` as a name): `## Modules` (each has its own `tests/`) · `## Inside a module`
(the file convention) · `## Where does a new file go?` · **`## Where decisions live`** (each `#Architecture` row
with an on-disk result → its path, created now: migration tool → `migrations/`, a container the
runtime uses → `Dockerfile`, each vendor → its adapter) · `## Hub files` (files every lane touches by one line). `#Structure` (the fields
the start prints) goes in a scratch file outside the repo: the summary + the prompts location (AI).
3. **Then make it run, in ONE call:** `status.py prove "<lock>" "<install>" "<lint>" "<smoke test>"` (printed
by the start) — it stops at the first failure; paste the evidence lines it prints into `#Structure`; it writes
the `## Checks you run` results.
4. Step 3c's check first (a clash: `status.py open`, below), then ONE call, no save question: `set structure filled
   --section-from <file> --commit "<line>"`; the close shows the
   layout and any Step 3c clash and asks "Change anything?".

**Never run** a type checker, a secret-scan sweep, a separate lint, test or `check_structure.py` run, a second
`prove` after a pass, or a `--dry-run` before the save: `prove` and `set` run every check counted here.

### Step 3c — Contradiction check, BEFORE the save call (`set`, below)
Per `MECHANISMS.md` §Step 3c, check what this phase produced against decisions **already recorded** — here `#Architecture`, **especially its Dev tooling line**: every scaffolding file must be the tool recorded there. On a conflict (this replaces `MECHANISMS.md` §Step 3c items 2-3), **name both sides on a line of their own** in the close, ask nothing, and **never edit an earlier phase's record or
document**: record it as an open item, `status.py open --from structure --what "Clash: <both sides>" --clears "/<that phase> decides"`. Carry any decision still OPEN forward (§Step 3c item 4). Adding detail to an earlier decision is not a contradiction. Record it before `set`, so the save takes it (`git status` clean at the end).

## Step 3b — Close (`MECHANISMS.md` §Step 3b)
1. **`scripts/check_structure.py` is the playbook's copy** (`scaffold` puts it there) — never edit it. It is committed: the commit hook and later sessions re-run it, and `#Structure`'s
   `evidence:` line names the script, its result, `STRUCTURE.md` and today's date.
2. **`status.py set structure filled --section-from <file>`** — it runs the structure check (map vs tree in
   **both** directions) and every countable exit criterion, and names every gap in ONE refusal; fix them all,
   then run it once more (`--commit` saves only a pass). Never check by hand what it checks.
3. It then prints the rest of the close, in order — reconcile, **Step 3c** (done above, before this call), no save question
   (`MECHANISMS.md` §Commit the work; `--commit` saved; a save the user asks for later: ONE call, `status.py save -m
   "<one line>"`), the **transition guard**
   (`MECHANISMS.md` §Step 3b; UNVERIFIED is a normal outcome) on ONE line: `Checked by the save: <what set counted> - judged, not checked: <the
   wording and quality criteria>`, and the close (`MECHANISMS.md` §Plain-language close), 8 lines in this order: the
   guard line · `Saved (commit <hash>).` · one line each, `STRUCTURE.md` linked, never restated: **What
   just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next** · then its
   last two lines word for word: `Change anything? If not:` and the `Open a NEW conversation` line.

## Step 4 — Handoff
"Clean structure + root scaffolding in place and explained in `STRUCTURE.md`.
- **User-facing UI?** Run **`/design-system`** next — principles, a confirmed sample page and a concrete
  `DESIGN.md` *before* any screen is built, so the UI doesn't end up generic. Then `/foundation`.
- **Backend/API/CLI only:** straight to **`/foundation`** for a walking skeleton that actually runs —
  alone, or as a **batch** `/foundation` + `/contracts` + `/tickets` with one review at the end
  (`MECHANISMS-ON-DEMAND.md` §Batch mode); the batch still stops wherever a phase asks you to confirm."
