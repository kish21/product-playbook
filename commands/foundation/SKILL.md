---
name: foundation
description: >
  Phase 2 (Development), step 3 of product-playbook. Build the walking skeleton that actually RUNS —
  dependencies, config loader, structured logging, base infra wiring (DB/LLM/queue), dev tooling
  (lint/format + the commit-hook runner #Architecture chose), secret-scan, and a CI that mirrors the
  prod bootstrap. Use after
  /structure, or run /foundation "set up the skeleton", "get it running", "wire up CI". Writes the
  Foundation section of PRODUCT.md. Run /contracts next.
---

# `/foundation` — Phase 2 · Development ③ · run as an **engineer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **no-hardcoding (config/.env)**, **verify config actually
> flows (no dead config)**, **fail-loud on misconfig / fail-closed on security**, **structured
> logging (no prints)**, **CI mirrors prod**, **fast feedback early**.

## Contract
- **Purpose:** a thin end-to-end skeleton that runs, with config/logging/infra/tooling/CI in place.
- **Reads:** `PRODUCT.md#Architecture`, `#Structure`.
- **Writes:** **`docs/runbook.md`** (how to boot it, what `.env` needs, what each guard does and how to
  verify it) + `PRODUCT.md#Foundation`, which stays a **record**: runs end-to-end? · config-flow verified ·
  guards/secret-scan/CI · the pointer. This section hit **14KB** on a real run — one section at the
  whole-file ceiling the playbook imposes on a skill — because a runbook was wearing a spine section's
  clothes (`PRINCIPLES.md`: a section is a record, not a container).
- **Gate type:** `derivation` — computable from `#Architecture` + `#Structure`. Batchable - a `derivation` run may chain with its neighbours and end in ONE review. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes `#Foundation` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Exit criteria:**
  - [ ] App **runs end-to-end** with nothing in it (a health check / hello path works).
  - [ ] **For a product with auth, the bar is USABLE end-to-end, not merely running** — a login actually
    succeeds. A health path proves the process booted, not that a human can get in; on a real run the app
    booted perfectly and nobody could log in. The **seed produces a working dev account** and the guard is
    *logging in*, not *200 OK*.
  - [ ] **The seed is idempotent and re-runnable** — it is the recovery path after a reset or an isolated-test
    teardown, so running it twice succeeds and duplicates nothing. **A wiped database is recoverable with one
    documented command.**
  - [ ] **The seeder refuses to run against a production target**, and prints its credentials once at the end.
    They are **obviously-fake documented dev values** (`PRINCIPLES.md` §Secrets never get pushed) — this must
    never normalise printing real credentials, and the dev account must not be creatable in prod.
  - [ ] `#Foundation` records **where the dev credentials are**, and the handoff names them — so the next
    session does not go looking.
  - [ ] Config loads from config/`.env`; **the value actually flows** (verify — no dead/overridden config).
  - [ ] **Fail-loud on misconfig, fail-closed on security**: boot refuses on missing/known-constant secrets.
  - [ ] **Placeholders are rejected BY NAME at boot, not by length or format** — the loader knows the `CHANGE_ME__<VAR>__CHANGE_ME` values `/structure` wrote to `.env.example` and refuses to start on any of them, naming the variable and how to generate a real one. A length/format check is not this: a 48-char placeholder passes `min(32)` and boots the app on a public signing key. **A test proves it** (copy `.env.example` → `.env` unedited → boot fails), and under production (`NODE_ENV`/`APP_ENV`) there is **no override** — see `PRINCIPLES.md` §Production safeguards.
  - [ ] **An isolated, disposable test datastore is provisioned** — its own variable (`TEST_DATABASE_URL`
    or the chosen datastore's equivalent) in `.env.example`, created and torn down by the task runner.
    Per-test transaction rollback is an acceptable alternative; **sharing the development datastore is
    not.** The test bootstrap **fails closed**: handed the dev or production target, it refuses to run,
    names both, and exits non-zero — verified by pointing it at the dev one on purpose.
    **How you obtain it depends on the data custody `#Architecture` recorded** — a throwaway instance
    (local/self-hosted), a **database branch or a second project** (managed-serverless), or a temp file
    (embedded). The mechanics are not comparable: near-trivial on a container, real work on a managed
    service, which is why the obvious shortcut is the one thing this forbids. **Open
    `references/test-datastore.md` and follow the recipe for the recorded custody** — including what to
    do when none is achievable today.
  - [ ] **The test runner loads config the same way the app does** (same loader, same precedence) — not whatever happened to be exported into the shell. A runner with its own config path is dead config on the test side, and it is how a suite ends up pointed at the wrong datastore.
  - [ ] Structured logging (no stray prints); dev tooling wired — lint/format + the **commit-hook runner and secret scanner `#Architecture` chose** (not a tool this skill picks).
  - [ ] **CI is in place and mirrors the prod bootstrap** (builds/migrates/tests from the real schema), green — a must, not optional.
  - [ ] CI runs **both secret-scan AND dependency-vulnerability scan** (e.g. `pip-audit`/`npm audit`), **fail-closed on a known CVE**; CI creates throwaway creds at runtime (no literal secret in the repo).
  - [ ] An **automated dependency-update bot** is wired (`.github/dependabot.yml` or Renovate). Add it **on day one while deps are clean** — a strict CVE gate bolted on late faces a months-deep backlog (the bot patches one-at-a-time so the backlog never forms). **Group tightly-coupled packages** (react+react-dom, eslint+eslint-config-next) so they bump in one PR — bumping them independently drifts versions apart and breaks the build.
  - [ ] Long/first-use work (model download, slow external calls) **does not block the async event loop** (offload/async).

## Step 0 — Context + prior-gate check
- Read `#Architecture/#Structure`. If `#Structure` is empty, warn and offer `/structure` first (allow override).
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then write `Override <date>: <reason> — bypassed <gate>` at the top of `#Foundation` before continuing. Advancing on unmet criteria is the more consequential of warn-vs-override, so it is the one that leaves a trace: without it a later reader cannot tell a gate that held from a gate that was waved through.
- Brownfield: detect what already exists (CI, config, logging) and fill only the gaps.
- **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** if the section is already filled, **show what would change and ask before replacing it** — never a silent overwrite — and leave a reversed decision in place with a dated `superseded <date>: <why>` line. A first run over an empty section is unchanged.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** write ONE dated line at the top of `#Foundation` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **No-hardcoding:** every endpoint/secret/threshold from config/`.env`. **Prove it flows** — read a value back at runtime; a setting silently overridden upstream is "dead config" and a real bug.
- **Fail-loud/fail-closed:** a startup guard refuses to boot if a required secret is unset, equals a default constant, **or is still one of `.env.example`'s placeholders**. Match the placeholder **by value, by name** — never infer "looks unset" from length or shape; `make setup` copying the example to `.env` is the normal path, so this guard is the only thing between a fresh clone and a public signing key.
- **CI mirrors prod:** bootstrap the same way prod does (real schema/migrations), least-privilege tokens.

## Step 2 — Build the skeleton
**Open `references/skeleton-steps.md` and work through all eight** — each carries the detail, the
ownership seam and the failure it prevents:

1. **Dependency manifest: contents and provability** (`MECHANISMS.md` §Seam — `/structure` owns its shape)
   — pin, install, write the tool configs, get the first real run green. Then a runnable entrypoint with
   a health path: the walking skeleton.
2. **The dev seed** — idempotent, production-refusing, prints its fake credentials once.
3. **Config loader + startup guard** — fail-loud on misconfig, fail-closed on security, rejecting
   `.env.example`'s placeholders **by name**.
4. **The test datastore + its refuse-to-run guard**, written *before* any test exists
   (`references/test-datastore.md` for the recipe per custody).
5. **Structured logging + a tracing/error-reporter hook**, and base infra behind `/architect`'s adapters.
6. **The auto-layer** — lint, format, the recorded commit-hook runner, secret-scan, dependency-vuln scan,
   and an automated dependency-update bot wired on day one.
7. **The design tokens, if this product has a UI** — the stylesheet `/design-system` emitted is imported
   by the root entry and **resolves at runtime**; prove it by reading a token back.
8. **CI that mirrors the prod bootstrap** — real schema/migrations, blocks on red, throwaway creds.

## Step 3 — Write the runbook, then the record
**`docs/runbook.md` holds the operational detail** — boot sequence, the `.env` variables and how to
generate each, what every guard refuses and how to prove it, how to reset and re-seed, how to run the
suite against the isolated datastore. It is the document someone opens at 2am, so it is written for
someone who was not here. **`#Foundation` keeps the record and the pointer.**

Fill `#Foundation`: runs end-to-end? · config-flow verified (how) · guards (**incl. the placeholder rejection and the test-datastore refuse-to-run guard, each with its test**) · isolated test datastore + how the runner loads config · secret-scan + dep-vuln · hook runner + CI (auto-layer) · container · observability hook.

## Step 3b — Principle-gate: verify it RUNS and the guards are real (evidence)
Walk this phase's principles and prove each — don't assume:
- runs end-to-end → actually start it / hit the health path (compose `/run`); evidence.
- **usable end-to-end (auth products) → actually log in with the seeded account**, and show the seed running
  **twice** without failing or duplicating. "The health check passes" is not this.
- config flows / no dead config → read a value back at runtime; evidence.
- **the commit hooks + CI actually run** the deterministic checks (lint/format/secret-scan + dependency-vuln/tests) and **block on red** → show a green run; this is the auto-layer the later skills rely on.
- fail-loud/fail-closed guard → trigger it with a missing secret and confirm it refuses to boot.
- **test-isolation guard → point it at the dev datastore on purpose** and show it refusing to run, naming both targets. Then confirm the suite's teardown cannot reach the dev data. This one is verified by *attempting the destruction*, because the failure mode is silent until the data is gone.
- **placeholder guard → replay the real failure:** copy `.env.example` to `.env` **unedited**, start the app, and show it **refusing to boot** with a readable message. If it starts, the guard is decorative and the product ships a public secret.
**If any is "should" not "shown", STOP and make it real.** Record HOW in `#Foundation`.

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and **offer to commit the change** (`MECHANISMS.md` §Commit the work — check the repo exists, name the branch, offer the message, push only if a remote exists and the user says so). Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal. **Close in plain language** (`MECHANISMS.md` §Plain-language close): two or three sentences of *what just happened* with no playbook dialect, then a numbered *what YOU do next* — the user's own actions, dated where they are time-bound, or "Nothing — you're done".

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Architecture` (adapters · tool choices · CI approach) and `#Structure`'s map — a skeleton wired to a datastore, hook runner or provider other than the recorded one. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Skeleton runs, a seeded account can log in (credentials: <where>), and CI is green. Next run **`/contracts`** to define typed models/schemas/migrations
BEFORE business logic — so the data shape is right from the start."
