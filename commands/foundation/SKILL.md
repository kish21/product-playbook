---
name: foundation
description: Build the runnable skeleton - config, logging, tooling, CI.
---

# `/foundation` — Phase 2 · Development ③ · run as an **engineer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` · AGENT.md = `${CLAUDE_PLUGIN_ROOT}/references/agent.md`, only when `Agent: yes` (a path still starting with `$`: the variable is the folder two levels above this SKILL.md, holding `commands/` and `PRINCIPLES.md` - never another tool's install). If `python` will not start (not found, or a sandbox refuses it): the project's `.venv` Python, else `python3`, else `py -3` - never a hunt; later commands use the start's `Run this copy as` line.
> **This skill's OWN reference files are a DIFFERENT folder** (`${CLAUDE_PLUGIN_ROOT}/commands/foundation/references/skeleton-steps.md` · `verify.md` · `test-datastore.md`, never the plugin-root `references/`)**: the start prints them, and its scripts' and templates' paths** — never open them. Its scripts: `devserver.py` (check · start · stop · refuses) · `ci_local.py` (the CI steps, run here) · `env_init.py` (makes `.env`) · `proof.py` (logs a proof).
> **`status.py next --phase foundation` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it). Load-bearing: **no-hardcoding (config/.env)**, **verify config actually
> flows (no dead config)**, **fail-loud on misconfig / fail-closed on security**, **structured
> logging (no prints)**, **CI mirrors prod**, **fast feedback early**.

## Contract
- **Purpose:** a thin end-to-end skeleton that runs, with config/logging/infra/tooling/CI in place.
- **Reads:** `PRODUCT.md#Architecture`, `#Structure`.
- **Writes:** **`docs/runbook.md`** (how to boot it, what `.env` needs, what each guard does and how to
  verify it) + `PRODUCT.md#Foundation`, which stays a **record, not a container** (`PRINCIPLES.md`; case
  file: The runbook in the spine).
- **Gate type:** `derivation` — computable from `#Architecture` + `#Structure`. Batchable - a `derivation` run may chain with its neighbours and end in ONE review. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Foundation` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Checked by `status.py set foundation filled`, not by reading** (every problem in one refusal; the start lists
  each one).
- **Exit criteria:**
  - [ ] App **runs end-to-end** with nothing in it (a health check / hello path works).
  - [ ] **For a product with auth, the bar is USABLE end-to-end, not merely running** — a login actually
    succeeds; the guard is *logging in*, not *200 OK* (case file: The skeleton nobody could log in to). The **seed produces a working dev account**.
  - [ ] **The seed is idempotent and re-runnable** — it is the recovery path after a reset or an isolated-test
    teardown, so running it twice succeeds and duplicates nothing. **A wiped database is recoverable with one
    documented command.**
  - [ ] **The seeder refuses to run against a production target** — by the environment AND by a non-local database host —
    and prints its credentials once at the end. They are **obviously-fake documented dev values** (`PRINCIPLES.md` §Secrets never get pushed) — this must
    never normalise printing real credentials, and the dev account must not be creatable in prod.
  - [ ] **The seed stops at identity:** the login's user table (+ the kill-switch row, `Agent: yes`) — no domain models,
    fixtures or money types; those are `/contracts` (`skeleton-steps.md` §2).
  - [ ] `#Foundation` records **where the dev credentials are**, and the handoff names them — so the next
    session does not go looking.
  - [ ] Config loads from config/`.env`; **the value actually flows** (verify — no dead/overridden config).
  - [ ] **Fail-loud on misconfig, fail-closed on security**: boot refuses on missing/known-constant secrets, and **no secret has a fallback value in code**.
  - [ ] **Placeholders are rejected BY NAME at boot, not by length or format** — the loader knows the `CHANGE_ME__<VAR>__CHANGE_ME` values `/structure` wrote to `.env.example` and refuses to start on any of them, naming the variable and how to generate a real one. **Proven through the real entrypoint** (`.env.example` unedited → the app, started as prod starts it, refuses to boot — `verify.md` §Guards), and under production (`NODE_ENV`/`APP_ENV`) there is **no override** — see `PRINCIPLES.md` §Production safeguards. **It refuses the placeholders in use:** local values always; outside keys with the real provider on or under production — so development on the fake model boots with them still `CHANGE_ME` (`skeleton-steps.md` §3.).
  - [ ] **`.env` is made by the script, not by hand:** `env_init.py` (git-ignores it first, never overwrites, never prints a value) filled the local values, and the close shows its list — filled / needed from you only for real mode. Its committed copy is the runbook's one `.env` command.
  - [ ] **The tests never read the developer's `.env`:** the loader takes an `env_file` argument and a config test passes an empty temp file; `proof.py dotenv -- <test command>` passed with a filled `.env` and without one (`set` refuses otherwise).
  - [ ] **An isolated, disposable test datastore is provisioned** — its own variable (`TEST_DATABASE_URL`
    or the chosen datastore's equivalent) in `.env.example`, created and torn down by the task runner,
    **the same engine `#Architecture` chose**. Per-test transaction rollback is an acceptable alternative; **sharing the development datastore is
    not.** The test bootstrap **fails closed**: handed the dev or production target, it refuses to run,
    names both, and exits non-zero — verified by pointing it at the dev one on purpose.
    **How you obtain it depends on the data custody `#Architecture` recorded** — **follow `test-datastore.md` §The recipes**, including what to do when none is achievable today.
  - [ ] **The test runner loads config the same way the app does** (same loader, same precedence) — not whatever happened to be exported into the shell. A runner with its own config path is dead config on the test side.
  - [ ] Structured logging (no stray prints); dev tooling wired — lint/format + **a type checker for a typed language** (none only with the user's reason recorded) + the **commit-hook runner and secret scanner `#Architecture` chose** (not a tool this skill picks), **installed, with one real commit through it**, and a planted fake secret refused (`set` plants it).
  - [ ] **AI product: the real adapter fits its caller** — on a dead endpoint, in the fake's place, it takes `#Architecture`'s failure path (a hand-off), not an exception.
  - [ ] **`docs/runbook.md` boots a fresh clone with the project's own commands** — `.env` from `.env.example`, the database created and migrated; never a path into the playbook's install or this machine.
  - [ ] **CI is in place and mirrors the prod bootstrap** (builds/migrates/tests from the real schema, installs from the lockfile), **every action version it pins exists, and it ran once** (`ci_local.py` checks both), green — a must, not optional. **No git remote:** its steps pass with `ci_local.py` = *verified locally*, and an open item stays until CI is green on the first push.
  - [ ] **UI product (`DESIGN.md` exists): the frontend audit runs in the commit hooks AND CI** from a committed copy of the installed engine, over `DESIGN.md` + the whole UI tree — an ERROR blocks, a WARN only reports — **proven red at Step 3b**. **A route renders the UI shell** with the tokens (`skeleton-steps.md` §7).
  - [ ] CI runs **both secret-scan AND dependency-vulnerability scan** (e.g. `pip-audit`/`npm audit`), **fail-closed on a known CVE**; CI creates throwaway creds at runtime (no literal secret in the repo).
  - [ ] An **automated dependency-update bot** is wired (`.github/dependabot.yml` or Renovate). Add it **on day one while deps are clean**. **Group tightly-coupled packages** (react+react-dom, eslint+eslint-config-next) so they bump in one PR.
  - [ ] **`Agent: yes`: every AGENT.md §Foundation item** has an `evidence:` line in `#Foundation`.
  - [ ] Long/first-use work (model download, slow external calls) **does not block the async event loop** (offload/async).

## What /foundation must NOT build
The wiring, never the product: no feature routes (health, login, the UI shell only), no domain models (`/contracts`),
no product prompt, pipeline or real golden cases (`/build`) — two logged runs pre-built the agent loop here.
`Agent: yes`: one generic read tool, a scripted fake (one reply wrong); a fake that echoes its input is refused.

## Step 0 — Context + prior-gate check
- **One start command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase foundation`**, run as it is (its output is sized for your tool — never into a file of your own) — this project's facts (git, manifests, hooks, `.env.example`, the datastore, this machine's tools, the script lines), `#Architecture`, `#Structure` (`#Design` for a UI), AGENT.md §Foundation (`Agent: yes`), the eight steps, the proofs, this phase's rules. Show its first line. `STRUCTURE.md`, `DESIGN.md` and code: the parts a step needs.
- If `#Structure` is empty, warn and offer `/structure` first (allow override).
- Brownfield: detect what already exists (CI, config, logging) and fill only the gaps.
- **Anything unusual - the start names it when it is real:** a re-run follows its `RE-RUN` line: **one question listing what would change**, never a silent overwrite; a reversed decision keeps a dated `superseded <date>: <why>` line. **An override is RECORDED, never a verbal "yes"**: the **reason in the user's own words**, then `status.py bypass --from foundation --gate <gate> --reason "<the user's own words>"` before continuing. A stop at an unmet gate: `status.py set foundation declined --reason "<what was missing>" --gate <the phase(s) that fill it>`, and nothing changes in `PRODUCT.md` (`MECHANISMS.md` §Re-run semantics, §Declined runs).

## Step 1 — Apply principles (this phase)
- **No-hardcoding, fail-loud/fail-closed:** as the exit criteria say — the guard in the entrypoint (`skeleton-steps.md` §3.), a value read back at runtime (`verify.md` §Config flows).
- **CI mirrors prod:** bootstrap the same way prod does (real schema/migrations), least-privilege tokens.

## Step 2 — Build the skeleton
**First, when `.env` is missing, run `python ${CLAUDE_PLUGIN_ROOT}/commands/foundation/env_init.py`** (again after a step adds a variable to `.env.example`: it only appends what `.env` lacks) and show the user its list.
**Work through the eight in `skeleton-steps.md`, in order — the start printed them whole** (`§1.` … `§8.`) — each
carries the detail, the ownership seam and the failure it prevents. **Print one line as each step lands**
(`MECHANISMS-ON-DEMAND.md` §Context hygiene).
**Item 1 ends by proving it boots:** hit the health path with `devserver.py check` (one call: start, answer, then
stop whatever you started, port freed) and print one plain-language line — the app runs, and how to see it (the
command, the address). A line, not a pause. No boot → fix it before item 2.
(case file: The skeleton nobody saw boot)

1. **Dependency manifest: contents and provability** — pin, install, **commit the lockfile**, write the tool configs, get the first real run green; a runnable entrypoint with a health path. Missing `.gitattributes` / gitleaks config → copy the templates.
2. **The dev seed** — idempotent, production-refusing (environment AND database host), identity only, prints its fake credentials once.
3. **Config loader + startup guard** — fail-loud on misconfig, fail-closed on security, rejecting
   `.env.example`'s placeholders **by name** (outside keys only in real mode or production), no fallback values for
   secrets, run at boot; the loader takes an `env_file` argument, so tests never read the developer's `.env`.
4. **The test datastore + its refuse-to-run guard**, written *before* any test exists, on the engine `#Architecture` chose.
5. **Structured logging + a tracing/error-reporter hook**, and base infra behind `/architect`'s adapters.
6. **The auto-layer** — lint, format, the recorded commit-hook runner (**installed**), secret-scan, dependency-vuln scan,
   and an automated dependency-update bot wired on day one. **UI product: the frontend audit too** — copy
   `"${CLAUDE_PLUGIN_ROOT}/commands/frontend-audit/audit.py"` (the installed engine; never search the plugin cache)
   into the project; the step's recipe says where and how the hook and CI call it.
7. **The design tokens, if this product has a UI** — imported by the root entry and **read back at runtime**; no own stylesheet → a route renders the shell.
8. **CI that mirrors the prod bootstrap** — real schema/migrations, blocks on red, throwaway creds.

## Step 3 — Write the runbook, then the record
**`docs/runbook.md` holds the operational detail** — boot sequence, the `.env` variables and how to
generate each, what every guard refuses and how to prove it, how to reset and re-seed, how to run the
suite against the isolated datastore. It is the document someone opens at 2am, so it is written for
someone who was not here, every heading numbered (the start prints the five) — so its commands are the project's own (task-runner targets, files in the repo; a clone has
no playbook) and its recipes run as written in PowerShell and bash. **`#Foundation` keeps the record and the pointer.**

Fill `#Foundation`: runs end-to-end? · config-flow verified (how) · guards (**incl. the placeholder rejection and the test-datastore refuse-to-run guard, each with its proof**) · isolated test datastore + how the runner loads config · secret-scan + dep-vuln · hook runner + CI (auto-layer; UI: audit copy path + engine version) · container · observability hook.

## Step 3b — Principle-gate: verify it RUNS and the guards are real (evidence)
**Prove each with `verify.md` (printed by the start), in order, and don't assume:** §Evidence lines · §Runs end to end · §Usable end
to end · §Config flows · §Guards · §Hooks and CI · §Heavy checks in a fresh conversation. **If any is "should" not
"shown", STOP and make it real.** Record HOW in `#Foundation`. **Run every proof through `proof.py -- <command>`**
(`devserver.py`, `ci_local.py` log their own; a plant: `proof.py plant`): `set` matches each `evidence:` line to that
log, and plants a fake secret through the hooks itself.

**Keep the context lean (`MECHANISMS-ON-DEMAND.md` §Context hygiene):** a command's output over 30 lines goes to a scratch file; read the tail or grep the verdict, and cite the file in the evidence line.

**Review this phase's own code before the record:** `status.py secreview foundation` lists only the code this phase wrote and prints ONE helper's prompt; fix every HIGH and MEDIUM; its `security review:` line goes in `#Foundation` (`/dev-check` then skips those files, unless it was a self-review).

**Close the loop (`MECHANISMS.md` §Step 3b):** first Step 3c below, and reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it). Then, no save question: the record call saves (`--no-commit` only when the user said not to save) (`MECHANISMS.md` §Commit the work — this project's repo, name the branch; push only if a remote exists and the user says so): close each open item this phase settled (`status.py close <n> --how "…"`), then record the phase's state — `status.py set foundation filled --section-from <file> --commit "<one line>"` (`MECHANISMS.md` §Status): it refuses every gap at once, commits through the hooks with the items in the save (`verify.md` §Saving) and prints the rest; the close says what runs and what the proofs showed (each block at most 2 lines - the record holds the evidence), what is owed and any clash, and asks *"Change anything?"*. Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run an `evidence:` line only when a file it reads changed after Step 3b captured it (`verify.md` §Runs end to end) and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal. **Close in plain language** (`MECHANISMS.md` §Plain-language close): four blocks in order, each under its bolded name: **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next** (ends with the handoff).

## Step 3c — Contradiction check (BEFORE the save call in Step 3b: what it fixes or records goes in that save)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Architecture` (adapters · tool choices · CI approach · **the datastore and its custody, test datastore included**) and `#Structure`'s map — a skeleton wired to a datastore, hook runner or provider other than the recorded one. On a conflict (this replaces `MECHANISMS.md` §Step 3c items 2-3), **name both sides on a line of its own** in the close and ask nothing; fix this phase's artefact, **never an earlier phase's record or document** — record the clash as an open item: `status.py open --from foundation --what "Clash: <both sides>" --clears "/<that phase> decides"`. A file only an earlier refusal forced is no clash to ask about. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Skeleton runs, a seeded account can log in (credentials: <where>), and CI is green. Next run **`/contracts`** to define typed models/schemas/migrations
BEFORE business logic."
