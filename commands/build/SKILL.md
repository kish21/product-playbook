---
name: build
description: >
  Phase 2 (Development), step 5 of product-playbook — the per-feature build loop: ONE feature at a
  time, a definition-of-done that INCLUDES security, reuse before writing, verify the LIVE path,
  review the diff, write the feature doc. Use to implement features, or run /build "build feature X",
  "implement", "add the feature". Records a ticket row in STATUS.md (status.py) + writes docs/features/<feature>.md.
  Composes /run and /code-review. Run /dev-check when all core-scope features are done.
---

# `/build` — Phase 2 · Development ⑤ · run as an **engineer**

**Mode:** the user's words `full` · `thorough` · `high` → add `--mode full` to the start command; `lean` · `quick` · `fast` → `--mode lean`; none → the tool decides. Follow the path the start prints.

## Lean path — the start prints `Mode: lean`: this section is the whole run
1. **One call:** `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase build --ticket <id>` — the ticket, its files, the contract rules, the gate and live-path commands, whether a security review is required. Open no rule file.
2. On the ticket branch (the start names it), **implement the ticket and its tests**; the ticket's DoD is the DoD. A new file in one write; every edit to a file in one message.
3. **Before the reviews: only the ticket's tests and lint on the changed files** — the full project check runs ONCE, at step 5. Commit locally.
4. **Reviews, both at once:** the code review and the security review (`CAPABILITIES.md` §Code review) over the ticket's commits — and ask: what REAL thing could this code touch by mistake (a real shop, account, inbox, payment, user)? Fix every real finding, commit. Then ONE question: review again, over the fixes' files only (recommended after a HIGH/MEDIUM)? No skips it; no round 3.
5. **`docs/features/<feature>.md` in ONE write:** what it does · how it was verified · `## Review` with the findings table (severity · file:line · what goes wrong · fixed by) or CLEAN · `Real-world reach: <what> - guarded by test_<name>` · why each changed file the ticket did not list changed. **Every new setting in the runbook/README too**, and any `STRUCTURE.md` line — then **`gate.py --ticket <id> --close` once**, over it all; commit.
6. **Record:** `status.py ticket <id> --dod yes|partial --verified "<command> → <result>" --doc docs/features/<feature>.md --review "code + security review R1 <n> findings · R2 (<n> files) <n> findings"` (or `· R2 skipped by the user: <reason>`) — say every line it prints. Then the close `next` printed.
7. **Everything below is the full path (`Mode: full`).**

> Part of **product-playbook**. **Reads the ticket; never writes the spine** (`PRODUCT.md`, or the project's docs — MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **This skill's OWN reference files are a DIFFERENT folder:** `references/` beside this SKILL.md (`commands/build/references/`: `feature-archetypes.md` · `live-path-checks.md` · `review-stretch.md`), never the plugin-root `references/`.
> **The start command (Step 0) prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it). Load-bearing: **per-feature contract (security in the DoD)**,
> **secure-by-construction**, **prompts→`prompts/` YAML**, **doc↔code reconciled**, **measure before
> fixing**, **no swallowed errors**, **reuse-before-write**, **trace callers (live-path)**,
> **generic-not-domain-specific**.
> War stories: `${CLAUDE_PLUGIN_ROOT}/references/case-files-build.md`.
> **Terms:** *ticket's base* = `git merge-base HEAD <default branch>` · *close gate* = `gate.py --ticket <id> --close` over the final committed code · *seat* = the lane or role the user gave this session · *observable result* = what a user or caller sees (the response, the row, the page), never an exit code.
> **Companions:** `references/feature-archetypes.md` (the rules that apply only to gates · async jobs · latency fixes · trust boundaries) · `references/live-path-checks.md` (proving a change is wired in) · `references/review-stretch.md` (Step 5's helper) — read one by the `§` a step names: `status.py section <path> "<§>"`.

## Contract
- **Purpose:** implement one feature to a verified, secure, documented definition-of-done.
- **Reads:** the ticket, its files and what the start prints (`#Contracts`' rules among them); `#Structure` only for a file the ticket does not name; **`DESIGN.md` + `#Design` for a feature with a screen** (UI products).
- **Writes:** a ticket row in `STATUS.md` (`status.py ticket`) + `docs/features/<feature>.md` — or, in its place, the one per-ticket record `#Project policy` names. Never `PRODUCT.md` (`status.py ticket` refuses it).
- **Gate type:** `derivation` — computable from the ticket + `#Contracts`. Batchable - a `derivation` run may chain with its neighbours and end in ONE review. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes a `STATUS.md` ticket row · `declined` ✓ · `override` ✓ · `superseded` n/a — append-only log: one row per feature
- **Exit criteria (per feature):**
  - [ ] A written **definition-of-done that includes security** (input validation, authz/tenant-isolation; for AI: prompt-injection defence).
  - [ ] Reused existing helpers where possible (no reinvented utilities).
  - [ ] Code **runs and the LIVE path is verified** (not just an isolated unit) — traced to its real callers, **on the runtime the USER actually runs**: register a new endpoint/route on EVERY serving surface (case file: Wrong serving surface).
  - [ ] Diff self-reviewed (`/code-review`); no swallowed errors; prompts in `prompts/` YAML, not inline.
  - [ ] **`docs/features/<feature>.md` (or the per-ticket record `#Project policy` names) written and matches the code** (what · contract · exit criteria · how verified · code links).
  - [ ] **No secret in any code file** (secrets→`.env`; tests use fake placeholder keys).
  - [ ] **Single-responsibility kept** — a file growing large/multi-concern is split into modules (no god-files); long/blocking work stays off the async event loop.
  - [ ] **(UI products) The feature's screen(s) are built to `DESIGN.md`** — §5 layout, token look, `/new-component` parts — and **`/frontend-audit` is clean** — 0 errors; on existing files, 0 NEW errors against the ticket's base, the pre-existing count quoted.

## Step 0 — Context + prior-gate check
- **First turn, ONE command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase build` with `--ticket <the ticket id>`** — it prints the gate, the ticket, its files, `#Project policy`, the commands and the coding rules; **read nothing else up front** (each line read is re-sent on every call). Show its first line.
- **The first message says what to expect:** ~15–25 min; one mid-run question (round 2), none with `one round`; a note per step.
- **Nobody to answer** (headless, a batch): take the recommended option only where this skill offers one (round 2); **STOP and report** on a scope doubt, an override, a contradiction or a finding that fails the DoD.
- **A tool a step names is missing:** `CAPABILITIES.md` names its equivalent; none → that check is recorded UNVERIFIED with why, never as passed.
- **The ticket is the accepted brief:** build it; revisit a plan decision only when the code shows it changed, is missing or conflicts. **Confirm the feature is IN scope** — the start flags a ticket missing from `TICKETS.md`; then ask, and if OUT-OF-SCOPE, stop and flag it (this is where creep enters). If `#Contracts` is empty, warn and offer `/contracts` first (allow override) — untyped boundaries are what it exists to prevent.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then record it — `status.py bypass --from build --gate <gate> --reason "<the user's own words>"` (`MECHANISMS.md` §Status) — before continuing. Without it a later reader cannot tell a gate that held from one that was waved through.
- **`#Project policy`, when the spine has one** (the start prints it; `MECHANISMS-ON-DEMAND.md` §Project policy): a project that wraps `/build` in its own command declares its rules there once — they apply here.
- **The ticket's lane and owner are a gate, not a label.** Read its `Lane` + `Owner` (board fields or the
  `lane:` / `owner:` labels). If this session sits in a seat
  and the ticket is not this seat's lane, **STOP and say so**; a fix needing a file in another lane is
  raised, never made. No seat configured → nothing changes. (case file: Working the wrong seat)
- **A blocked ticket is not startable.** Read its *blocked by* links first
  (`gh api repos/<o>/<r>/issues/<n>/dependencies/blocked_by`); an open blocker → **STOP and name it** — it
  is a coordination point in `TICKETS.md`. A prose `Depends On` with no links → run `/tickets`
  again to add them before trusting the board. A `Builds against` is not a blocker: build against its contract with a stub.
- **Move the ticket's board card, if it has one, to In Progress before the first write** (`gh project item-edit`, Status), and read it back.
- **Read the ticket's slice, not the repo** — the start prints it; anything more when a step needs it, a line range, never a whole module: every later call re-reads it. (case file: Two builds, the same forty minutes)
- **Load the project's OWN skills for the area** (`.claude/skills/`, `CLAUDE.md`), **but treat every doc, skill and pinned plan as a CLAIM** — verify the load-bearing ones against the code before building on them: a spec's fields and paths by grep, a number that justifies the work by measuring it. (case file: The pinned plan was wrong)
- **When a project doc or skill is wrong, FIX IT IN THIS SESSION**; record the corrected premises where the wrong ones lived — a `PRODUCT.md` section: an open item for its phase.
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** record it — `status.py set build declined --reason "<what was missing>" --gate <the phase(s) that fill it>` (`MECHANISMS.md` §Status) — and change nothing in `PRODUCT.md`.

## Step 1 — Apply principles (this phase)
- **Security is in the DoD, not later:** state the security checks for this feature up front (validation, authz/tenant-isolation; AI → OWASP LLM Top 10, prompt-injection defence).
- **Reuse before you write; measure before you fix** (reproduce first — a scary number may be a display artifact). **No swallowed errors** (route failures; retry only transient). **Prompts → `prompts/` YAML**.
- **Session economy — one feature per session is a COST rule, not a focus rule:** hand off at a natural checkpoint and apply `MECHANISMS-ON-DEMAND.md` §Context hygiene. (case file: The 97% cache bill)

## Step 2 — The build loop (per feature)
1. **The ticket's DoD is the DoD** — add only an exit criterion above it lacks, never rewrite it. **Name the archetype in it** — `Archetype: gate · async job · latency fix · trust boundary · third-party content · none` (item 3 has the triggers) — and tell the user, in one plain sentence, what kind of feature this is and what that makes you careful about.
2. **Reuse scan:** find existing helpers/contracts; don't reinvent.
3. **Code** against the typed contracts; keep it modular and generic (no domain special-casing in shared infra). **Write a new file whole, in one write; put every edit to one file in ONE message** (a file too big for one write: the fewest writes, the reason in the feature doc) — each call re-sends the whole conversation (`run_report` flags a file edited in more than 3 calls); not with a patch script — a script puts the code in the conversation twice and breaks on quoting.
   - **Checks: `gate.py`, all in ONE call** — `python "${CLAUDE_PLUGIN_ROOT}/commands/build/gate.py" --ticket <id>` (it runs the project's check recipe and the ticket's Verification Command; commands named after it are added, `--only` replaces); **wire cuts: `wirecut.py <cuts.json>`** (or `--cut "<file>::<text>::<replacement>::<test>"`), all in one call, each file restored.
   - **A missing table or column before any test runs:** first check the test database's migrations (one command); not migrated → migrate it; migrated → likely another checkout: ask the user once to point `.env` at `<project>_test`; never wrap every command.
   - **Tests while coding: the test files that import a module you changed** — a search for `<module name>` in test folders — then only the failing tests until they pass (`pytest --lf`, `vitest --changed`, or the test ids; keep the runner's cache on, it is what remembers the failures). **The full suite runs at the gate and at the close, nowhere else** (the close reuses it if code is unchanged) — never after a single fix, never after round 1's fixes (the close gate covers them); a gate that fails is fixed with its failing tests, then run once more. **Count the full-suite runs and pass the count as `--runs` on the ticket row** (`--runs 2`). (case file: The suite that ran for every edit)
   - **If the feature has a user-facing screen (UI products):** build to **`DESIGN.md`** — §5 layout, token look, `/new-component` parts (Law 15) — then run **`/frontend-audit`** — `python "${CLAUDE_PLUGIN_ROOT}/commands/frontend-audit/audit.py" DESIGN.md <ui-dir>`, the installed engine; **never search the plugin cache** (a `$` left in the path: `/frontend-audit` §Which engine runs) — fix every ERROR, and repeat its `engine copy:` line. *(No `DESIGN.md`? `/design-system` first.)*
   - **On a ticket that edits EXISTING UI files, add `--baseline <the ticket's base commit>`** (`git merge-base HEAD <default branch>`): it reports only the errors this change ADDS and prints the pre-existing count on its own line. Fix every new error; quote the pre-existing count, and if no open issue tracks those errors, file ONE issue for them — never fixed here, never dropped. A new file or a first screen: the plain run, 0 errors. (case file: Eighty-seven errors, none of them new)
   - **A "use a token" fix counts only when the token's class exists in the built CSS** — search the build output for it: a utility class with no mapping to the token (Tailwind v4 without an `@theme` entry) emits nothing, and the element ships invisible. (case file: The token class that compiled to nothing)
   - **Some features carry rules that apply only to THEM. If this feature is one, open `references/feature-archetypes.md` and apply that cluster BEFORE you write:**
     - a **GATE** — a validator, quality check, policy engine, anything whose job is to say "no" → **§Gates** (10 rules)
     - an **ASYNC JOB** — work that outlives the request (spawn + poll, queue + callback) → **§Async jobs** (7 rules)
     - a **LATENCY / CONCURRENCY fix** → **§Latency and concurrency** (expect more than one serializer)
     - anything **shared across tenants, cached, AI-suggested, or keyed by a client-supplied selector** → **§Trust boundaries and shared state**
     - **third-party content shipped to your users** → **§Third-party content** (the licence is a feasibility gate)
     - The feature doc carries the line — `Archetype: <kind> → §<cluster> opened`, or `Archetype: none`. A cluster applied from memory is a cluster not applied. (case file: The companions nobody opened)
4. **Run + verify the LIVE path** — compose `/run` to exercise the path the product actually runs, **then check the observable result yourself** (the response, the row, the rendered page — not the exit code), then **trace your change to its real callers** (green unit tests ≠ wired in). **Fewest calls:** a test through the Demo's entry point (its route or `python -m` command) and ONE `devserver.py check` call, printed ready to run by the start, — never one started and stopped by hand.
   - **Walk the checks in `references/live-path-checks.md` whose trigger matches this feature** — the ones that separate *the code exists* from *the product runs it*. **The start prints every check's trigger** (the *[always]* ones whole) — a trigger you have not read cannot match; read a matching one by section, and list the ones that matched, by name, in the feature doc: `Live-path checks walked: …`.
   - **Tests: item 3's rule while you iterate, the full suite once at the gate.**
   - **A test that fails, then passes with no change, is FLAKY — record it (name · error · N of M runs failed) and file it with `/tickets "<bug>"` in the lane that owns it.** Outside what you changed → carry on and name the issue in the close; inside it and small → fix it with a proof. **Never re-run until green.** **Attribution is one traceback, not an investigation** — it is **uncertain** until ONE run of the failing test with your change stashed: fails the same → OUTSIDE; passes → yours. Never re-run the suite to characterise it. (case file: The flake nobody wrote down)
5. **Review the diff — one round, then the user decides.**
   - **Commit the ticket's work LOCALLY before round 1** — on the ticket branch (on the default branch, create one first), after `MECHANISMS.md` §Commit the work's repo check; never pushed, no PR — and tell the user in one line, with the undo (`git reset --soft HEAD~1`). **`/security-review` reads only COMMITTED changes:** on an uncommitted tree its files, commits and diff come back empty, and the review falls back to a pass by hand. (case file: The review that read an empty diff)
   - **Round 1, both at once:** run the code review directly here (`CAPABILITIES.md` §Code review) AND, when the start marks security REQUIRED, ONE helper with `references/review-stretch.md` §Helper prompt runs it (no code review tool: it does both). Neither waits; the helper reports; you fix what both found, commit, write `## Review` (§Findings there). Round 2: same, its files only. **A tool with no helper agent** (`CAPABILITIES.md`): §In the helper here, recorded as `self-review`.
   - **Changing another ticket's file** (its issue body, its code) **needs the user's yes first** — name the file and why.
   - **Then show the user what the reviews caught** — before anything else runs: how many, and the ones that mattered most, each in ONE plain sentence saying what would have gone wrong for a user (*"a second shop could have read this shop's photos"*, never *"missing tenant filter"*); that they are fixed and tested; and the time and cost so far, measured (`MECHANISMS-ON-DEMAND.md` §Context hygiene, item 4) or "not measured". Say it again in the close. (case file: The review nobody saw)
   - **Round 2 is the user's call, never automatic.** **The reviews are checks too** — a review fix is code no review has seen — so ask ONE question: review again, over **the files round 1's fixes touched, only** (`/security-review` too when they touch an auth/data surface)? Give your recommendation AND its reason: **recommend YES when the fixes touched an auth/data surface**, when round 1 found a HIGH or MEDIUM, or when the fixes were more than small edits; otherwise recommend NO. The user chose up front (*"one round"*, *"two rounds"*) → do not ask; nobody can answer (headless, a batch) → follow your own recommendation and say so. **A skipped round 2 is RECORDED** in the ticket row's `--review` with its reason — never silent.
   - **No round 3.** A round-2 fix is covered by the deterministic gate at the close (tests · lint · audit · secret-scan · live path, once over the final tree); if round 2 found anything that would fail the DoD, **STOP and tell the user** — the finding and the fix — never a silent third round. (case file: The audit the review fix outran)
   - **Record each round's SCOPE** in the ticket row's `--review` — `/code-review → R1 8 findings · R2 (3 files) 1 finding · <sha> · <date>`, or `· R2 skipped by the user: <reason>` — so `/ship` can tell whether the diff changed since.
   - **A review that never returns has found nothing** — killed, rate-limited or timed out, its findings are never guessed: re-run it once, same scope; if it dies again, STOP and tell the user. (case file: The reviewer that never came back)
6. **Document** — once, at the close's step 3 (Step 3) — write/update `docs/features/<feature>.md` in ONE write; reconcile it with the code; name each changed file the ticket did not list, with why. **`#Project policy` names a per-ticket record** → write that content THERE, once, and nothing into `docs/features/`; the `status.py ticket` row stays, the one-line index `/ship` and `/dev-check` read. **Copy every `evidence:` number from the command's captured output, never ahead of it** — a figure pencilled in while CI runs reads exactly like a measured one. (case file: The pencilled bundle size)

## Step 3 — Record the ticket
**The close, in this order, each once:** (1) the close gate — it prints the close's rules; (2) Step 3c; (3) the feature doc, ONE write (item 6: the review table, the gate's numbers, Step 3c's result); (4) commit it; (5) the ticket row, below; (6) Step 3b's close the loop — the save question there commits only the record (the code was committed before round 1).

Record ONE ticket row — `status.py ticket <id> --dod yes|no|partial --verified "<command> → <result>" --doc docs/features/<feature>.md --runs <full-suite runs> --review "<Step 5's round scopes>"` (`MECHANISMS.md` §Status). **The row is a record, and `status.py` refuses a field past its limit** — findings, defects, round detail and **Step 3c's result go in the feature doc**, never in the row (`MECHANISMS-ON-DEMAND.md` §Section is a record). A stop or an override is recorded by `status.py` too, never as a paragraph. (case file: The log every build read)
**Say every line `ticket` prints to the user;** a refusal names its fix (`--no-cuts` / `--not-wired "<why>"`).

## Step 3b — Principle-gate: verify each principle is ACTUALLY implemented (not just claimed)
Walk **this phase's load-bearing principles (Step 1)** and confirm each is real, **citing the evidence Step 2 already captured** (command · result · commit).
- **Cite, or re-run?** **re-run a check when any code, config or test file it reads changed after its evidence was captured; a review fix counts, a doc-only change does not.** Uncommitted and scripted edits count. A file a check reads is never doc-only for that check (`DESIGN.md` for `/frontend-audit`), and, outside the gate, **when unsure whether anything changed or whether a change is doc-only, re-run** — a stale citation passes a broken feature. **The gate is never re-run to be safe:** `ticket --dry-run` names each file changed since it; re-run only for those.
- **Scope by what a check reads** — a backend-only fix does not re-run the UI audit — but **when you cannot name the files a check reads, re-run it**, and **the whole gate runs once more at the close**, whatever the scoping said: scoping removes repetition inside the loop, never coverage of the committed tree.
- **This gate runs ONCE, after Step 5's last round** — never after each round, and it never re-opens the reviews: Step 5 bounds them. **These re-run rules are Step 3b's alone** — while coding, Step 2 item 3's test rule decides what runs.

**Evidence, per principle:** security-in-DoD → the security review that ran, named (or the start's "not required") · no secret in code → secret-scan clean · live-path-works → `/run` on the real path **and the observable result seen**, named · reuse · no-swallowed-errors · single-responsibility → the code review · (UI) built-to-the-design → `/frontend-audit` 0 errors against `DESIGN.md`, or 0 new with `--baseline`, the old count quoted.

**If any named principle is only claimed, not evidenced, STOP — the feature is not done.** Record the *how-verified* per principle in the feature doc, and the one-line result in the ticket row's `--verified` (evidence, not "done").

**Close the loop (`MECHANISMS.md` §Step 3b):** record the phase's state — `status.py set build filled` (`MECHANISMS.md` §Status) — reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and **ask the save question** *"Save this version of your project? (yes / no)"* (`MECHANISMS.md` §Commit the work). Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): cite the close gate's record (`status.py ticket` checked it) and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal. **Close in plain language** (`MECHANISMS.md` §Plain-language close): four blocks in order, each under its bolded name: **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next** (ends with the handoff). **The close is the run's last message** — a composed skill's report is input to it, never the close itself. (case file: The report that became the close) After the PR merges, set the card to **Done** and read it back; merged later → the close gives the user that command.

## Step 3c — Contradiction check (the close's step 2)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: `#Contracts` (types crossing boundaries), `#Architecture` (adapters — no vendor SDK in logic), `#Scope` (non-goals) and `DESIGN.md` (UI tokens). On a conflict, **name both sides, ask which wins, and update the loser** — the code: fix it; a recorded decision: an open item for the phase that owns it (`status.py open`, naming the section and the change), never a `PRODUCT.md` edit here. Adding detail to an earlier decision is not a contradiction. **Step 3c's result goes in the feature doc** — never a paragraph in the ticket row, which `status.py` limits to a record.

## Step 4 — Handoff
"Feature done, verified, and documented. Build the next core-scope feature with `/build`, or when the
core scope is complete run **`/dev-check`** — the checkpoint that verifies everything before testing."
