---
name: ship
description: >
  Phase 5 (Ship) of product-playbook. Ship a piece of work the right way — a deep fresh-eyes review,
  a security review, reconcile docs to reality, a confidence score, open the PR, write the handoff,
  and tell the user to start a fresh session. Use when a feature/subtask is done, or run /ship "ship
  it", "open a PR", "release", "wrap up". Writes the Ship log of PRODUCT.md. Composes /code-review,
  /security-review, /doc-audit, github-pr-flow. Run /learn after a release lands.
---

# `/ship` — Phase 5 · Ship · run as a **release reviewer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per PRINCIPLES.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **reviews are DEEP not skims**, **fresh-eyes caller/cross-file
> tracing (works-in-tests-dead-in-prod)**, **security/fail-closed on auth/data**, **docs match
> reality**, **one-subtask→PR+handoff**, **confidence score**, **verify findings against real code**.

## Contract
- **Purpose:** release one subtask safely, with review + security + honest docs, and hand off cleanly.
- **Reads:** `PRODUCT.md` (all relevant sections), the diff.
- **Writes:** `PRODUCT.md#Ship log` — what shipped · review/security · docs reconciled · PR.
- **Exit criteria:**
  - [ ] **Deep review** done (`/code-review`) — findings traced to real callers/cross-file impact, not a skim.
  - [ ] **Security review** on auth/data changes (`/security-review`); for AI, the OWASP LLM Top 10 checklist (esp. prompt injection).
  - [ ] **Docs reconciled to reality** (`/doc-audit`) — no false capability/security claims.
  - [ ] **Confidence score (0–100%)** reported (solid / risky-untested / to-raise-it).
  - [ ] PR opened (`github-pr-flow`) with **`Closes #N`** in the body where a tracked issue exists; a smooth **handoff** written; user told to start a fresh session.
  - [ ] **Tracker reconciled after merge:** the linked issue is **Closed** and (if a project board exists) its card moved to **Done** — *verified against the tracker*, not assumed from "shipped". See `github-pr-flow` Step 7.
  - [ ] A **CHANGELOG / release note** entry (+ a **semver** bump where versioned).
  - [ ] Security checklist cleared: dependency-vuln scan, CORS prod domain, cookie-based auth (not localStorage), and data-deletion/GDPR for data products.
  - [ ] **Rollout safety:** a stated **rollback path** (revert PR / migration-down / flag-off); risky changes behind a **flag / staged rollout**; the **post-deploy signal to watch** named.

## Step 0 — Context + prior-gate check
- Read `#Eval` and the diff. If quality wasn't evaluated, warn and offer `/eval` first (allow override for small changes).

## Step 1 — Apply principles (this phase)
- **Reviews are DEEP:** trace the change to its real callers; hunt the "green tests, dead in the live path" bug. **Verify any review/audit finding against the real code** — don't rubber-stamp; some findings are already done or misdiagnosed.
- **Security fail-closed** on auth/data; **docs must match reality** (a false claim is a diligence liability).
- **One subtask per session:** ship this, then hand off — don't roll into the next subtask.

## Step 2 — Ship
1. **Deep review:** compose **`/code-review`**; fix real findings; verify each against the code before acting.
2. **Security:** compose **`/security-review`** on auth/data; for AI, run the OWASP LLM Top 10 / prompt-injection checklist.
3. **Reconcile docs:** compose **`/doc-audit`**; update `PRODUCT.md`, `docs/features/*`, README so they match reality (no false claims). Gate the PR on this.
4. **Rollout safety:** state the **rollback path** (revert PR / migration-down / flag-off); put risky/irreversible changes behind a **flag or staged rollout**; name the **post-deploy signal to watch** (the bridge to `/learn`); bump **semver** where versioned.
5. **Confidence score:** report 0–100% with solid / risky-untested / to-raise-it.
6. **PR + handoff:** compose **`github-pr-flow`** to open the PR (with **`Closes #N`** in the body for any tracked issue) + a **CHANGELOG** entry; write a short handoff (done / next / how to resume / blockers).
7. **Reconcile the tracker (post-merge):** verify the linked issue actually **Closed** and the project-board card moved to **Done** (`github-pr-flow` Step 7) — close/move manually if the keyword or board workflow was missing. A "shipped" note is not proof; check the tracker.

## Step 3 — Write back to `PRODUCT.md`
Append a `#Ship log` row: date · what shipped · review+security · docs reconciled? · CHANGELOG · rollback/flag · PR link.

## Step 3b — Self-verify (completeness gate)
Check the boxes. **If review/security/docs aren't actually done, or a doc claim doesn't match the
code, STOP — do not open the PR.** Shipping a false claim is the exact failure to avoid.

## Step 4 — Handoff
"Shipped: reviewed, security-checked, docs reconciled, PR open, confidence recorded, **issue closed +
board card moved to Done**. **Start a fresh session** for the next subtask. After it lands, run
**`/learn`** to capture metrics + decide what's next."
