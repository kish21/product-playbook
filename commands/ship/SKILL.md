---
name: ship
description: >
  Phase 5 (Ship) of product-playbook. Ship a piece of work the right way — a deep fresh-eyes review,
  a security review, reconcile docs to reality, a confidence score, open the PR, write the handoff,
  and tell the user to start a fresh session. Use when a feature/subtask is done, or run /ship "ship
  it", "open a PR", "release", "wrap up". Records a release row in STATUS.md (status.py). Composes /code-review,
  /security-review. Run /learn after a release lands.
---

# `/ship` — Phase 5 · Ship · run as a **release reviewer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **`status.py next --phase ship` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it). Load-bearing: **reviews are DEEP not skims**, **fresh-eyes caller/cross-file
> tracing (works-in-tests-dead-in-prod)**, **security/fail-closed on auth/data**, **docs match
> reality**, **one-subtask→PR+handoff**, **confidence score**, **verify findings against real code**.

## Contract
- **Purpose:** release one subtask safely, with review + security + honest docs, and hand off cleanly.
- **Reads:** what `next` prints — the diff, the reviews already run, the gates, `#Project policy`, the release record, `#Deployment`'s rollback.
- **Writes:** a `STATUS.md` release row (`status.py release`) — what shipped · reviews · docs reconciled · PR.
- **Gate type:** `verification` — review, security and doc gates pass or they do not. Batchable, and **stops on red** - a failing check ends the batch there. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes a `STATUS.md` release row · `declined` ✓ · `override` ✓ · `superseded` n/a — append-only log: one entry per release
- **Exit criteria:**
  - [ ] **Deep review** done (`/code-review`, or the equivalent your harness has) — findings traced to real callers/cross-file impact, not a skim. → `STATUS.md Releases: Reviews`
  - [ ] **Security review** on auth/data changes (`/security-review`, or equivalent — and say which); for AI, the OWASP LLM Top 10 checklist (esp. prompt injection). → `STATUS.md Releases: Reviews`
  - [ ] **Docs reconciled to reality** — every **capability and security claim** in `PRODUCT.md`, `docs/features/*` and the README checked against the code that backs it. A claim with no implementation is the finding; delete it or build it. → `STATUS.md Releases: Docs reconciled`
  - [ ] **Confidence score (0–100%)** reported (solid / risky-untested / to-raise-it). → `STATUS.md Releases: What shipped`
  - [ ] PR opened with **`Closes #N`** in the body where a tracked issue exists; a smooth **handoff** written; user told to start a fresh session. → `PR`
  - [ ] **Tracker reconciled after merge:** the linked issue is **Closed** and (if a project board exists) its card moved to **Done** — **if the project keeps a board**; the playbook does not create one, so audit what exists rather than a structure nothing here provisions — *verified against the tracker*, not assumed from "shipped" (Step 7 below). → `PR`
  - [ ] **The release is recorded where this project records releases** — a **CHANGELOG** entry (+ a **semver** bump where versioned), or `n/a — releases recorded in <X>` when the CHANGELOG is retired or absent, or `#Project policy` names another record. An explicit line either way, never silence. → `CHANGELOG`
  - [ ] Security checklist cleared: dependency-vuln scan, CORS prod domain, cookie-based auth (not localStorage), and data-deletion/GDPR for data products. → `STATUS.md Releases: Reviews`
  - [ ] **No placeholder can boot this build** — `.env.example`'s values are still rejected by name at startup (the `/foundation` guard and its test are intact, with no production override). A release that boots on a committed secret is a live incident, not a finding. → `STATUS.md Releases: Reviews`
  - [ ] **Rollout safety:** a stated **rollback path** (revert PR / migration-down / flag-off); risky changes behind a **flag / staged rollout**; the **post-deploy signal to watch** named. → `STATUS.md Releases: Rollback`

## Step 0 — Context + prior-gate check
- **One first command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase ship`** — it prints the diff, the reviews already run, the gates and the rules; never open `PRODUCT.md` whole. Show its first line.
- `#Dev-complete`, `#Tests`, `#Evaluation` (the start prints each): **name each one that is not passed** and
  recommend the specific phase that fills it (`/dev-check` → `/test` → `/eval`). Shipping is still allowed —
  standalone use is first-class — but **an override here is recorded on the release, not implied by an empty
  section**: write the skipped phases into the release row's `--skipped` with the reason.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then record it — `status.py bypass --from ship --gate <gate> --reason "<the user's own words>"` (`MECHANISMS.md` §Status) — before continuing.
- **What this phase must NOT do:** start a new feature, or merge without the user's explicit word.
- **`#Project policy`** (the start prints it; `MECHANISMS-ON-DEMAND.md` §Project policy): a project that wraps `/ship` in its own command declares its rules there once — never merge, no deploy, where releases are recorded, reviews already run in `/build` — and they apply here without the wrapper restating them.
- **The exception is bounded, not vague.** A change may skip `/eval` only when it touches no product
  behaviour — a docs/typo/comment change, or a revert. **Anything that changes what the product does needs
  its tests recorded**; "small" is not a judgement the shipper makes about their own change. (case file: The last gate that never asked about tests)
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** record it — `status.py set ship declined --reason "<what was missing>" --gate <the phase(s) that fill it>` (`MECHANISMS.md` §Status) — and change nothing in `PRODUCT.md`.

## Step 1 — Apply principles (this phase)
- **Reviews are DEEP:** trace the change to its real callers; hunt the "green tests, dead in the live path" bug. **Verify any review/audit finding against the real code** — don't rubber-stamp; some findings are already done or misdiagnosed.
- **Security fail-closed** on auth/data; **docs must match reality** (a false claim is a diligence liability).
- **The most expensive operation in the chain is the one most worth de-duplicating:** read the ticket rows (the start prints them) before composing any review.
- **One subtask per session:** ship this, then hand off — don't roll into the next subtask; a fresh session after the PR is the cost lever (every call re-sends the whole conversation).

## Step 2 — Ship
0. **First, read what has ALREADY been reviewed.** The `STATUS.md` ticket rows record each review with its result,
   scope and date — **a review is evidence with a scope, not a step that always fires.** Compare that
   scope to the diff you are shipping and take one of three paths, explicitly:
   - **unchanged since that review** → say so, **cite the ticket row as the evidence, and skip it**
   - **changed** → re-run, and **name what changed** (new commits, a wider diff, a round of fixes)
   - **no recorded review** → run it
   A deep review is the priciest operation in this chain, `/build`'s diff and this one are often *the
   same diff*, and a reviewer handed an already-fixed diff **re-reports closed findings**.
1. **Deep review:** run **`/code-review`** *if available* — otherwise your default code-reviewer agent / review mode, inspecting the diff against `PRINCIPLES.md`. **NEVER skip the review** on a diff nothing has reviewed. Fix real findings; verify each against the code before acting.
   - **Then review AGAIN — the fixes are new code, and nothing has reviewed them.** A round of fixes edits the same files under time pressure with the finding, not the design, in view; re-running the review is the only thing that looks at what the fixing produced (case file: The second review round). **This round is never the duplicate Step 0 prunes** — its scope is *the fixes*, which by definition no review has seen. Do not let a mechanical reading of Step 0 delete it.
   - **Round 1 is the review Step 0 says must run** — over a diff nothing has reviewed, or over fixes no ticket row records a review of (a `/build` whose round 2 was skipped). **Then show the user what it caught** — how many, and each one that mattered in ONE plain sentence saying what would have gone wrong for a user; that they are fixed and tested.
   - **Round 2 — over THIS run's fixes — is the user's call, never automatic.** Ask ONE question: review again, over **the files round 1's fixes touched, only** (`/security-review` too when they touch an auth/data surface)? Recommend YES when the fixes touched an auth/data surface, when round 1 found a HIGH or MEDIUM, or when the fixes were more than small edits; otherwise NO, and say why. The user chose up front → do not ask; nobody can answer → follow your recommendation and say so. **A skipped round 2 is RECORDED** in the release row's `--reviews` with its reason.
   - **No round 3.** A round-2 fix is covered by the gate below; one that would fail an exit criterion → **STOP and tell the user** the finding and the fix. (case file: The gate that ran for every fix)
   - **Fix with the edit tool, not with a patch script** — a script puts the code in the conversation twice and breaks on quoting.
   - **Tests while fixing: the test files that import a module you changed** (a search for `<module name>` over the test folders), then only the failing tests until they pass — never the full suite per fix.
   - **The full gate runs ONCE, after the last fix** — over the final tree, before the PR; a gate started before a later fix proves nothing about that fix. No fix at all → cite `/build`'s recorded gate: re-run a check when any code, config or test file it reads changed after its evidence was captured; a review fix counts, a doc-only change does not.
   - **Never two test runs at once** — a gate in the background and a test in the foreground share the project's test database and files, and one fails because of the other.
2. **Security:** apply Step 0 to this one too — a ticket row may already record a `/security-review`
   over an unchanged auth/data surface. Otherwise run **`/security-review`** *if available* on auth/data, **inside a subagent** so its report returns as input and cannot end the run — otherwise your default security-audit pass over auth, capability tokens and data paths against `PRINCIPLES.md`'s production safeguards. For AI, run the OWASP LLM Top 10 / prompt-injection checklist. Run the dependency scan the start names; its count goes in `--reviews`.
3. **Reconcile docs:** walk every **capability / security / “supported” claim** in `PRODUCT.md`, `docs/features/*` and the README and find the code that backs it — grep the concrete nouns (paths, flags, model names, field names), don't re-read the prose. Update whichever side is wrong. **Gate the PR on this:** a doc that overstates the product is a false security claim, not a typo.
4. **Rollout safety:** state the **rollback path** — **take it from `docs/deployment.md` §7 if `/deploy`
   has run**, rather than inventing one per release (revert PR / migration-down / flag-off); put risky/irreversible changes behind a **flag or staged rollout**; name the **post-deploy signal to watch** (the bridge to `/learn`); bump **semver** where versioned.
   - **Post-deploy live verification must never mutate a record sitting in a human's review/approval state — dry-run the same code path on the real data with persistence off.** A no-persist harness proves the deployed logic on production inputs while the human's pending decision stays untouched (case file: Dry-run live verify).
   - **A DATA migration (one that rewrites rows rather than schema) usually has no automatic down-path — "migration-down" is not the rollback, a hand-written re-flip is.** Say so in the rollback line instead of implying reversibility, and take the backup BEFORE applying: with no failing test to catch a bad data write, the only evidence you will have afterwards is a before/after diff proving exactly the intended rows moved.
5. **Confidence score:** report 0–100% with solid / risky-untested / to-raise-it.
6. **PR + handoff:** after Step 3b's dry run passes, open the PR — **`Closes #N`** goes in the **body**, not the title (a title keyword closes nothing) + the **release record**; write a short handoff (done / next / how to resume / blockers). No remote (or `gh` signed out): no PR or issue — `--pr "local-only: <branch> @ <sha>"`.
   - **The release record is a CHANGELOG entry — unless the project records releases elsewhere.** Read the CHANGELOG's top lines: retired ("do not add entries"), absent, or another record named in `#Project policy` → write `n/a — releases recorded in <X>` in the release row's `--record`, naming X. Absent with nothing declared → ask the user where releases are recorded and record the answer; never recreate a CHANGELOG the project retired. (case file: The retired changelog)
   - **`merge: never` in `#Project policy`** → open the PR and stop; Step 7's post-merge checks become the commands in the close for the user to run after they merge.
   - **A blocker you hand the user must be a PROVEN blocker — re-run with your workaround in effect and confirm it took, before calling it environmental.** An unverified diagnosis costs a round-trip and is often your own bug wearing the environment's clothes (case file: The environment blocker that was my own typo).
7. **Reconcile the tracker (post-merge):** a merge closes nothing on its own — `gh issue view <N> --json state -q .state` must read `CLOSED`, and a board card only moves if the project's set-Done workflow is on. **Both fail silently**, so the work reads as shipped while the tracker still says open. Close or move by hand where it did not fire (`gh issue close <N> --comment "Shipped in #<PR> (<sha>)."`), then sweep the board for any card whose column disagrees with its issue's state. A "shipped" note is not proof; check the tracker.

## Step 3 — Write back to `PRODUCT.md`
Record a release row — `status.py release --what "<what shipped>" --reviews "<each round's scope and the gate count: R1 (diff) 4 findings · R2 skipped by the user: <reason> · gate ×1 <sha>>" --skipped "<none when the full chain ran; otherwise e.g. /test, /eval — <reason>>" --docs "<reconciled?>" --record "<the CHANGELOG entry, or n/a — releases recorded in <X>>" --rollback "<rollback / flag>" --pr <link> --commit "<one line>"` (`MECHANISMS.md` §Status), after the same call with `--pr pending --dry-run` passed. **A release whose test phase was skipped must say so on the release record** — an
empty `#Tests` section is not a disclosure, it is an absence, and absence reads as "not applicable".

## Step 3b — Self-verify (completeness gate)
**Before the PR: `status.py release ... --pr pending --dry-run`** — every gap in one list, nothing written. **If review/security/docs aren't actually done, or a doc claim doesn't match the
code, STOP — do not open the PR.** Shipping a false claim is the exact failure to avoid. A gap found after the PR opened: fix it on the same branch (the PR updates).

**Close the loop (`MECHANISMS.md` §Step 3b):** the release row is the record (#ship is filled once it exists); `--commit` is the yes to *"Save this version of your project? (yes / no)"* (`MECHANISMS.md` §Commit the work), and the call prints the rest of the close: reconcile any number against `#Vision`; **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not; **close in plain language** (`MECHANISMS.md` §Plain-language close): **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next**, ending with its `Open a NEW conversation` line word for word. **The close is the run's last message** — a composed review's report is input to it, never the close itself.

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: the whole spine against what actually shipped — docs claiming a capability the code lacks, and the version in the release record against every manifest surface. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Shipped: reviewed, security-checked, docs reconciled, PR open, confidence recorded; **after the merge,
the issue closed and the card moved — checked, not assumed** (Step 7). **Start a fresh session** for the next subtask. After it lands, run
**`/learn`** to capture metrics + decide what's next."
