---
name: ship
description: >
  Phase 5 (Ship) of product-playbook. Ship a piece of work the right way — a deep fresh-eyes review,
  a security review, reconcile docs to reality, a confidence score, open the PR, write the handoff,
  and tell the user to start a fresh session. Use when a feature/subtask is done, or run /ship "ship
  it", "open a PR", "release", "wrap up". Writes the Ship log of PRODUCT.md. Composes /code-review,
  /security-review. Run /learn after a release lands.
---

# `/ship` — Phase 5 · Ship · run as a **release reviewer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per MECHANISMS.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **reviews are DEEP not skims**, **fresh-eyes caller/cross-file
> tracing (works-in-tests-dead-in-prod)**, **security/fail-closed on auth/data**, **docs match
> reality**, **one-subtask→PR+handoff**, **confidence score**, **verify findings against real code**.

## Contract
- **Purpose:** release one subtask safely, with review + security + honest docs, and hand off cleanly.
- **Reads:** `PRODUCT.md` (all relevant sections), the diff.
- **Writes:** `PRODUCT.md#Ship log` — what shipped · review/security · docs reconciled · PR.
- **Gate type:** `verification` — review, security and doc gates pass or they do not. Batchable, and **stops on red** - a failing check ends the batch there. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes `#Ship log` · `declined` ✓ · `override` ✓ · `superseded` n/a — append-only log: one entry per release
- **Exit criteria:**
  - [ ] **Deep review** done (`/code-review`, or the equivalent your harness has) — findings traced to real callers/cross-file impact, not a skim.
  - [ ] **Security review** on auth/data changes (`/security-review`, or equivalent — and say which); for AI, the OWASP LLM Top 10 checklist (esp. prompt injection).
  - [ ] **Docs reconciled to reality** — every **capability and security claim** in `PRODUCT.md`, `docs/features/*` and the README checked against the code that backs it. A claim with no implementation is the finding; delete it or build it.
  - [ ] **Confidence score (0–100%)** reported (solid / risky-untested / to-raise-it).
  - [ ] PR opened with **`Closes #N`** in the body where a tracked issue exists; a smooth **handoff** written; user told to start a fresh session.
  - [ ] **Tracker reconciled after merge:** the linked issue is **Closed** and (if a project board exists) its card moved to **Done** — **if the project keeps a board**; the playbook does not create one, so audit what exists rather than a structure nothing here provisions — *verified against the tracker*, not assumed from "shipped" (Step 7 below).
  - [ ] A **CHANGELOG / release note** entry (+ a **semver** bump where versioned).
  - [ ] Security checklist cleared: dependency-vuln scan, CORS prod domain, cookie-based auth (not localStorage), and data-deletion/GDPR for data products.
  - [ ] **No placeholder can boot this build** — `.env.example`'s values are still rejected by name at startup (the `/foundation` guard and its test are intact, with no production override). A release that boots on a committed secret is a live incident, not a finding.
  - [ ] **Rollout safety:** a stated **rollback path** (revert PR / migration-down / flag-off); risky changes behind a **flag / staged rollout**; the **post-deploy signal to watch** named.
  - [ ] **(Lane mode — MECHANISMS.md §Lane mode)** `lanekeeper check` passed before the PR was opened; the PR carries exactly one `lane: <name>` label; the `#Ship log` + CHANGELOG entries were written **on the base branch after merge**, never from inside the lane.

## Step 0 — Context + prior-gate check
- Read `#Dev-complete`, `#Tests`, `#Evaluation` and the diff. **Name every one of them that is empty** and
  recommend the specific phase that fills it (`/dev-check` → `/test` → `/eval`). Shipping is still allowed —
  standalone use is first-class — but **an override here is recorded on the release, not implied by an empty
  section**: write the skipped phases into the Ship log's *Skipped* column with the reason.
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate being bypassed, ask for the **reason in the user's own words**, say it will be written down — then write `Override <date>: <reason> — bypassed <gate>` at the top of `#Ship log` before continuing. Advancing on unmet criteria is the more consequential of warn-vs-override, so it is the one that leaves a trace: without it a later reader cannot tell a gate that held from a gate that was waved through.
- **The exception is bounded, not vague.** A change may skip `/eval` only when it touches no product
  behaviour — a docs/typo/comment change, or a revert. **Anything that changes what the product does needs
  its tests recorded**; "small" is not a judgement the shipper makes about their own change.
- *(On a real run this gate read the evaluation section alone and shipped a product whose `#Dev-complete`, `#Tests` and
  `#Evaluation` were all empty — the last gate before release never asked whether anything was tested.)*
- **If the gate is unmet and the run stops here, record that it stopped (`MECHANISMS.md` §Declined runs):** write ONE dated line at the top of `#Ship log` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so `/playbook` still routes to the missing phase; the next attempt **replaces** that line rather than appending to it.

## Step 1 — Apply principles (this phase)
- **Reviews are DEEP:** trace the change to its real callers; hunt the "green tests, dead in the live path" bug. **Verify any review/audit finding against the real code** — don't rubber-stamp; some findings are already done or misdiagnosed.
- **Security fail-closed** on auth/data; **docs must match reality** (a false claim is a diligence liability).
- **One subtask per session:** ship this, then hand off — don't roll into the next subtask. This is also the **cost lever**: agent-session cost grows ~quadratically with length (every API call re-reads the full history), so a fresh session after the PR is materially cheaper than continuing — measured on a shipped project (97% of a month's token spend was cache re-reads from overlong sessions), not a vibe.

## Step 2 — Ship
1. **Deep review:** run **`/code-review`** *if available* — otherwise your default code-reviewer agent / review mode, inspecting the diff against `PRINCIPLES.md`. **NEVER skip the review.** Fix real findings; verify each against the code before acting.
   - **Then review AGAIN — the fixes are new code, and nothing has reviewed them.** A round of fixes edits the same files under time pressure with the finding, not the design, in view; re-running the review is the only thing that looks at what the fixing produced (case file: The second review round).
2. **Security:** run **`/security-review`** *if available* on auth/data — otherwise your default security-audit pass over auth, capability tokens and data paths against `PRINCIPLES.md`'s production safeguards. For AI, run the OWASP LLM Top 10 / prompt-injection checklist.
3. **Reconcile docs:** walk every **capability / security / “supported” claim** in `PRODUCT.md`, `docs/features/*` and the README and find the code that backs it — grep the concrete nouns (paths, flags, model names, field names), don't re-read the prose. Update whichever side is wrong. **Gate the PR on this:** a doc that overstates the product is a false security claim, not a typo.
4. **Rollout safety:** state the **rollback path** — **take it from `docs/deployment.md` §6 if `/deploy`
   has run**, rather than inventing one per release (revert PR / migration-down / flag-off); put risky/irreversible changes behind a **flag or staged rollout**; name the **post-deploy signal to watch** (the bridge to `/learn`); bump **semver** where versioned.
   - **Post-deploy live verification must never mutate a record sitting in a human's review/approval state — dry-run the same code path on the real data with persistence off.** A no-persist harness proves the deployed logic on production inputs while the human's pending decision stays untouched (case file: Dry-run live verify).
   - **A DATA migration (one that rewrites rows rather than schema) usually has no automatic down-path — "migration-down" is not the rollback, a hand-written re-flip is.** Say so in the rollback line instead of implying reversibility, and take the backup BEFORE applying: with no failing test to catch a bad data write, the only evidence you will have afterwards is a before/after diff proving exactly the intended rows moved.
5. **Confidence score:** report 0–100% with solid / risky-untested / to-raise-it.
6. **PR + handoff:** open the PR — **`Closes #N`** goes in the **body**, not the title (a title keyword closes nothing) + a **CHANGELOG** entry; write a short handoff (done / next / how to resume / blockers).
   - **Lane mode (a `.lane` file is present):** before opening, run `lanekeeper check --lane <LANE> --base origin/<base>` and fix every file it names — a stray file is creep, not a label problem. Open the PR with the label **`lane: <LANE>`** (the gate fails closed without exactly one). Use Lanekeeper's PR template as-is. **Do not write the CHANGELOG or `#Ship log` from the worktree** — both are spine files outside the lane; note the entry in the PR body, and write it on the base branch once the PR merges (step 7).
   - **A blocker you hand the user must be a PROVEN blocker — re-run with your workaround actually in effect and confirm it took, before calling it environmental.** An unverified diagnosis costs a round-trip and is often your own bug wearing the environment's clothes (case file: The environment blocker that was my own typo).
7. **Reconcile the tracker (post-merge):** a merge closes nothing on its own — `gh issue view <N> --json state -q .state` must read `CLOSED`, and a board card only moves if the project's set-Done workflow is on. **Both fail silently**, so the work reads as shipped while the tracker still says open. Close or move by hand where it did not fire (`gh issue close <N> --comment "Shipped in #<PR> (<sha>)."`), then sweep the board for any card whose column disagrees with its issue's state. A "shipped" note is not proof; check the tracker. **Lane mode:** now, on the base branch, write the `#Ship log` row + CHANGELOG entry the lane PR could not carry (one writer for the spine), and if a Lanekeeper board exists confirm the card's Lane/Seat fields still match `lanes.yaml`.

## Step 3 — Write back to `PRODUCT.md`
Append a `#Ship log` row: date · what shipped · review+security · **skipped phases** (write `none` when the
full chain ran; otherwise name them, e.g. `/test, /eval — <reason>`) · docs reconciled? · CHANGELOG ·
rollback/flag · PR link. **A release whose test phase was skipped must say so on the release record** — an
empty `#Tests` section is not a disclosure, it is an absence, and absence reads as "not applicable".

## Step 3b — Self-verify (completeness gate)
Check the boxes. **If review/security/docs aren't actually done, or a doc claim doesn't match the
code, STOP — do not open the PR.** Shipping a false claim is the exact failure to avoid.

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and **offer to commit the change** (`MECHANISMS.md` §Commit the work — check the repo exists, name the branch, offer the message, push only if a remote exists and the user says so). Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal. **Close in plain language** (`MECHANISMS.md` §Plain-language close): two or three sentences of *what just happened* with no playbook dialect, then a numbered *what YOU do next* — the user's own actions, dated where they are time-bound, or "Nothing — you're done".

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase just produced against decisions **already recorded** — here: the whole spine against what actually shipped — docs claiming a capability the code lacks, and the version in the CHANGELOG against every manifest surface. On a conflict, **name both sides, ask which wins, and update the loser** (fix the artefact, or add a dated `superseded by` line to the earlier section) — never leave it standing in two places. Adding detail to an earlier decision is not a contradiction.

## Step 4 — Handoff
"Shipped: reviewed, security-checked, docs reconciled, PR open, confidence recorded, **issue closed +
board card moved to Done**. **Start a fresh session** for the next subtask. After it lands, run
**`/learn`** to capture metrics + decide what's next."
