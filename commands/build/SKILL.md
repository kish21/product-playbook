---
name: build
description: >
  Phase 2 (Development), step 5 of product-playbook — the per-feature build loop: ONE feature at a
  time, a definition-of-done that INCLUDES security, reuse before writing, verify the LIVE path,
  review the diff, write the feature doc. Use to implement features, or run /build "build feature X",
  "implement", "add the feature". Appends to PRODUCT.md#Build log + writes docs/features/<feature>.md.
  Composes /run and /code-review. Run /dev-check when all core-scope features are done.
---

# `/build` — Phase 2 · Development ⑤ · run as an **engineer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **per-feature contract (security in the DoD)**,
> **secure-by-construction**, **prompts→`prompts/` YAML**, **doc↔code reconciled**, **measure before
> fixing**, **no swallowed errors**, **reuse-before-write**, **trace callers (live-path)**,
> **generic-not-domain-specific**.
> War stories: `references/case-files-build.md`.
> **Companions — opened on demand, never up front:** `references/feature-archetypes.md` (the rules that apply only to gates · async jobs · latency fixes · trust boundaries) · `references/live-path-checks.md` (proving a change is really wired in).

## Contract
- **Purpose:** implement one feature to a verified, secure, documented definition-of-done.
- **Reads:** `PRODUCT.md#Scope`, `#Plan`, `#Contracts`, `#Structure` — **plus `DESIGN.md` + `#Design` for any feature with a user-facing screen** (UI products).
- **Writes:** a row in `PRODUCT.md#Build log` + `docs/features/<feature>.md`.
- **Gate type:** `derivation` — computable from the ticket + `#Contracts`. Batchable - a `derivation` run may chain with its neighbours and end in ONE review. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes `#Build log` · `declined` ✓ · `override` ✓ · `superseded` n/a — append-only log: one row per feature
- **Exit criteria (per feature):**
  - [ ] A written **definition-of-done that includes security** (input validation, authz/tenant-isolation; for AI: prompt-injection defence).
  - [ ] Reused existing helpers where possible (no reinvented utilities).
  - [ ] Code **runs and the LIVE path is verified** (not just an isolated unit) — traced to its real callers, **on the runtime the USER actually runs**: register a new endpoint/route on EVERY serving surface (case file: Wrong serving surface).
  - [ ] Diff self-reviewed (`/code-review`); no swallowed errors; prompts in `prompts/` YAML, not inline.
  - [ ] **`docs/features/<feature>.md` written and matches the code** (what · contract · exit criteria · how verified · code links).
  - [ ] **No secret in any code file** (secrets→`.env`; tests use fake placeholder keys).
  - [ ] **Single-responsibility kept** — a file growing large/multi-concern is split into modules (no god-files); long/blocking work stays off the async event loop.
  - [ ] **(UI products) The feature's screen(s) are built to `DESIGN.md`** — §5 layout, token look, `/new-component` parts — and **`/frontend-audit` is clean** (0 errors).

## Step 0 — Context + prior-gate check
- Read `#Scope/#Plan/#Contracts`. **Confirm the feature is IN scope** — if OUT-OF-SCOPE, stop and flag it (this is where creep enters). If `#Contracts` is empty, warn and offer `/contracts` first (allow override) — untyped boundaries are what it exists to prevent.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then write `Override <date>: <reason> — bypassed <gate>` at the top of `#Build log` before continuing. Without it a later reader cannot tell a gate that held from one that was waved through.
- **The ticket's lane and owner are a gate, not a label.** Read its `Lane` + `Owner` (board fields or the
  `lane:` / `owner:` labels). If this session sits in a seat (a seat or role the user named)
  and the ticket is not this seat's lane, **STOP and say so**; a fix needing a file in another lane is
  raised, never made. No seat configured → nothing changes. (case file: Working the wrong seat)
- **A blocked ticket is not startable.** Read its *blocked by* links first
  (`gh api repos/<o>/<r>/issues/<n>/dependencies/blocked_by`); an open blocker → **STOP and name it** — it
  is a coordination point in `docs/issues/README.md`. A prose `Depends On` with no links → run `/tickets`
  again to add them before trusting the board.
- **Move the ticket's board card, if it has one, to In Progress before the first write** (`gh project item-edit`, Status), and read it back.
- **Read the ticket's slice, not the repo.** Up front: its Target Files and a grep for each contract name it
  uses. Anything else when a step needs it, a line range rather than a file — never paste whole modules into
  the conversation; every later call re-reads them. (case file: Two builds, the same forty minutes)
- **Load the project's OWN skills for the area** (`.claude/skills/`, `CLAUDE.md`), **but treat every doc, skill and pinned plan as a CLAIM**: verify a spec's load-bearing claims against the code (case file: The pinned plan was wrong), reproduce a load-bearing NUMBER by measuring (case file: The number that justified the feature), grep a skill's concrete claims — paths, fields, providers (case file: Rotted skills).
- **When a project doc or skill is wrong, FIX IT IN THIS SESSION** — a PR-description correction dies there; record the corrected premises where the wrong ones lived.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** write ONE dated line at the top of `#Build log` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **Security is in the DoD, not later:** state the security checks for this feature up front (validation, authz/tenant-isolation; AI → OWASP LLM Top 10, prompt-injection defence).
- **Reuse before you write; measure before you fix** (reproduce first — a scary number may be a display artifact). **No swallowed errors** (route failures; retry only transient). **Prompts → `prompts/` YAML**.
- **Session economy — one feature per session is a COST rule, not just a focus rule.** Cost grows ~quadratically with session length — hand off at a natural checkpoint; bulky output to files, a progress line per step, broad searches to subagents (`MECHANISMS-ON-DEMAND.md` §Context hygiene). (case file: The 97% cache bill)

## Step 2 — The build loop (per feature)
1. **Declare the DoD** (incl. security + the exit criteria above).
2. **Reuse scan:** find existing helpers/contracts; don't reinvent.
3. **Code** against the typed contracts; keep it modular and generic (no domain special-casing in shared infra).
   - **If the feature has a user-facing screen (UI products):** build to **`DESIGN.md`** — §5 layout, token look, `/new-component` parts (Law 15) — then run **`/frontend-audit`** — `python "${CLAUDE_PLUGIN_ROOT}/commands/frontend-audit/audit.py" DESIGN.md <ui-dir>`, the installed engine; **never search the plugin cache** (a `$` left in the path: `/frontend-audit` §Which engine runs) — fix every ERROR, and repeat its `engine copy:` line. *(No `DESIGN.md`? `/design-system` first.)*
   - **Some features carry rules that apply only to THEM. If this feature is one, open `references/feature-archetypes.md` and apply that cluster BEFORE you write:**
     - a **GATE** — a validator, quality check, policy engine, anything whose job is to say "no" → **§Gates** (10 rules)
     - an **ASYNC JOB** — work that outlives the request (spawn + poll, queue + callback) → **§Async jobs** (6 rules)
     - a **LATENCY / CONCURRENCY fix** → **§Latency and concurrency** (expect more than one serializer)
     - anything **shared across tenants, cached, AI-suggested, or keyed by a client-supplied selector** → **§Trust boundaries and shared state**
     - **third-party content shipped to your users** → **§Third-party content** (the licence is a feasibility gate)
4. **Run + verify the LIVE path** — compose `/run` to exercise the path the product actually runs, **then check the observable result yourself** (the response, the row, the rendered page — not the exit code), then **trace your change to its real callers** (green unit tests ≠ wired in).
   - **Walk the checks in `references/live-path-checks.md` whose trigger matches this feature** — the ones that separate *the code exists* from *the product runs it*.
   - **Tests: the affected files while you iterate, the full suite once at the gate.**
   - **A test that fails, then passes with no change, is FLAKY — record it (name · error · N of M runs failed) and file it with `/tickets "<bug>"` in the lane that owns it.** Outside what you changed → carry on and name the issue in the close; inside it and small → fix it with a proof. **Never re-run until green.** (case file: The flake nobody wrote down)
5. **Review the diff** — compose `/code-review`, then `/security-review` on any auth/data surface — **both
   BEFORE the commit and the close**, so their verdicts land in the record; fix findings. **Record each
   review's SCOPE** in the `#Build log` row — `/code-review high → 8 findings, all fixed · <sha> · <date>` —
   so `/ship` can tell whether the diff changed since.
   - **Run `/security-review` inside a subagent** (prompt: *run /security-review on this branch and return
     the findings*) — invoked inline it takes over the turn and ends it on its report. **Its report is
     input: record the verdict, then step 6, Step 3, 3b and the close.** (case file: The review that ended the run again)
   - ⚠️ **If you cannot invoke it, ASK the user to run it, or do the deep pass by hand and say which you did** — see `PRINCIPLES.md`, *Composed skills*.
6. **Document** — write/update `docs/features/<feature>.md`; reconcile it with the code. **Copy every `evidence:` number from the command's captured output, never ahead of it** — a figure pencilled in while CI runs reads exactly like a measured one. (case file: The pencilled bundle size)

## Step 3 — Write back to `PRODUCT.md`
Append a `#Build log` row: feature · DoD-incl-security met? · **how verified** · link to the feature doc.

## Step 3b — Principle-gate: verify each principle is ACTUALLY implemented (not just claimed)
Walk **this phase's load-bearing principles (Step 1)** and confirm each is real, **citing the evidence Step 2 already captured** (command · result · commit) — re-run a check only when its files changed since:
- security-in-DoD → **`/security-review`** (or the equivalent pass) passed — name which.
- no secret in code / no-hardcoding → secret-scan clean.
- live-path-works → **`/run`** exercised the real path **and the observable result was checked** — name the command **and what you saw**. An exit code is not the observable result.
- reuse · no-swallowed-errors · single-responsibility → confirmed in the diff's **`/code-review`**.
- (UI features) built-to-the-design → **`/frontend-audit`** 0 errors against `DESIGN.md`.

**If any named principle is only claimed, not evidenced, STOP — the feature is not done.** Record the *how-verified* per principle in `#Build log` (evidence, not "done"). (Deterministic checks also run via the commit hooks + CI from `/foundation`; this gate is the judgment layer.)

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and **offer to commit the change** (`MECHANISMS.md` §Commit the work — check the repo exists, name the branch, offer the message, push only if a remote exists and the user says so). Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal. **Close in plain language** (`MECHANISMS.md` §Plain-language close): two or three sentences of *what just happened* with no playbook dialect, then a numbered *what YOU do next* — the user's own actions, dated where they are time-bound, or "Nothing — you're done". **The close is the run's last message** — a composed skill's report is input to it, never the close itself. (case file: The report that became the close) After the PR merges, set the card to **Done** and read it back; merged later → the close gives the user that command.

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Contracts` (types crossing boundaries), `#Architecture` (adapters — no vendor SDK in logic), `#Scope` (non-goals) and `DESIGN.md` (UI tokens) — the richest surface for contradiction, because this is the phase that writes real code. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Feature done, verified, and documented. Build the next core-scope feature with `/build`, or when the
core scope is complete run **`/dev-check`** — the checkpoint that verifies everything before testing."
