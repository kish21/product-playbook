---
name: tickets
description: >
  Phase 2 (Development), step 4b of product-playbook — bridges /contracts and /build. Breaks down the
  milestones from PRODUCT.md#Plan, STRUCTURE.md, and /contracts into structured, actionable GitHub
  Issue Tickets with exact target files, modules, implementation tasks, and DoD. Automatically
  provisions .github/ISSUE_TEMPLATE/ in the repository. Verifies remote repository status before
  publishing and never blindly creates remote repositories. Writes docs/issues/*.md and provisions
  .github/ISSUE_TEMPLATE/feature_ticket.md.
---

# `/tickets` — Phase 2 · Development ④b · run as a **tech lead / project engineer**

> Part of **product-playbook**. Reads the project spine (`PRODUCT.md`, `STRUCTURE.md`, `contracts`), generates
> structured issue tickets, provisions `.github/ISSUE_TEMPLATE/`, and syncs with GitHub only after strict pre-flight checks.

## Contract
- **Purpose:** Translate high-level milestones into granular, code-mapped GitHub issue tickets before building.
- **Reads:** `PRODUCT.md#Plan`, `#Contracts`, `STRUCTURE.md`.
- **Writes:**
  - `.github/ISSUE_TEMPLATE/feature_ticket.md` (scaffolded from bundled resources if missing)
  - `.github/PULL_REQUEST_TEMPLATE.md` (scaffolded if missing)
  - `docs/issues/*.md` (local issue tickets for each milestone)
  - Publishes to GitHub **ONLY IF** a remote origin is verified and user is authenticated.
- **Exit criteria:**
  - [ ] Every milestone from `PRODUCT.md#Plan` has a corresponding structured ticket.
  - [ ] Every ticket maps to **exact target file paths and module names** derived from `STRUCTURE.md`.
  - [ ] Every ticket carries a strict **Definition of Done (DoD) including security**.
  - [ ] `.github/ISSUE_TEMPLATE/` is populated in the workspace.
  - [ ] **Pre-flight remote verification executed:** Never blindly create a remote repository. If no remote exists, tickets are saved locally in `docs/issues/` and the user is notified.

---

## Step-by-Step Execution

### Step 1 — Auto-Provision GitHub Templates
1. Check if `.github/ISSUE_TEMPLATE/` exists in the workspace.
2. If missing, copy `resources/feature_ticket_template.md` to `.github/ISSUE_TEMPLATE/feature_ticket.md`.
3. If `.github/PULL_REQUEST_TEMPLATE.md` is missing, copy `resources/pull_request_template.md`.

### Step 2 — Derive File Names & Modules
For each milestone in `PRODUCT.md#Plan`:
1. Read the feature deliverable and user outcome.
2. Map it across the layers defined in `STRUCTURE.md`:
   - **Domain / Contracts:** `src/domain/...`
   - **Data / Providers:** `src/providers/...`
   - **Services / Logic:** `src/services/...`
   - **UI Components:** `src/components/...`
   - **Automated Tests:** `tests/unit/...`
3. Generate the step-by-step task checklist and DoD.
4. Save local markdown ticket files into `docs/issues/` (e.g. `docs/issues/01_issue_crud_and_prompt_synthesis.md`).

### Step 3 — Pre-Flight Remote Verification Guard (NEVER blindly create a remote repo)
1. **Check Git & Remote Origin:** Run `git remote -v`.
   - **Case A: No remote origin exists:** Stop remote sync. Notify the user:  
     *"Tickets have been generated locally in `docs/issues/`. No remote GitHub repository is linked. When you link a repository (`git remote add origin <url>`), run `/tickets` to publish them."*
2. **Check GitHub Auth & Repo Existence:** If remote exists, check `gh auth status` and `gh repo view`.
   - **Case B: Repo exists and authenticated (Deduplication & Ignore Guard):**
     - Fetch all existing repository issues: `gh issue list --state all --limit 100 --json title,number`
     - Compare each planned ticket against existing issue titles (matching by `[FEAT-XX]` tag or exact title).
     - **If a ticket already exists:** IGNORE it (skip creation, log: `Skipping [FEAT-XX]: already exists as Issue #<num>`).
     - **If a ticket does NOT exist:** Publish it using `gh issue create`.
   - **Case C: GitHub CLI not authenticated or repo inaccessible:**
     - Keep local files in `docs/issues/` and inform the user to run `gh auth login`.

---

## Handoff
"Issue tickets generated with concrete file names, module breakdowns, and Definition of Done. Ready to build: run **`/build`** on Ticket 1."
