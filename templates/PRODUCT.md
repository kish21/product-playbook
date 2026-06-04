<!--
PRODUCT.md — the living spine of this product.

This single file is the shared memory of the product-builder skills. Each skill
READS the sections it depends on and APPENDS/UPDATES its own. Read it top-to-bottom
to understand the whole product: what it is, why, what's built, and what's next.

Rules:
- A section that is empty/missing = that phase's exit criteria are not yet met.
- Keep entries short and honest. Record HOW something was verified, not just "done".
- Anything explicitly OUT OF SCOPE stays out until the recorded trigger fires.
-->

# PRODUCT — <product name>

_Last updated: <date> · Stage: <phase> · AI product? <yes/no>_

## Vision            <!-- /vision -->
- **Who it's for:**
- **Problem (why now):**
- **Value proposition:**
- **2026 market / competitor read:**

## Scope             <!-- /scope -->
- **THE core feature (the one thing):**
- **In scope (now):**
- **OUT OF SCOPE (and the trigger that would change that):**

## Plan              <!-- /plan -->
- **Phases / milestones (core first):**
- **Timeline:**
- **Exit criteria per milestone:**

## Architecture      <!-- /architect -->
- **Stack + tools (and why, 2026 OSS-first):**
- **Key decisions / ADRs:**
- **Externals behind provider/adapter interfaces:**

## Structure         <!-- /structure --> (see STRUCTURE.md for the full folder map)
- **Folder → purpose map (summary):**
- **Prompts location (AI):** `prompts/` (YAML, never inline)

## Foundation        <!-- /foundation -->
- **Runs end-to-end (walking skeleton):**
- **Config flows verified (no dead config):**
- **Fail-loud/fail-closed guards · secret-scan · CI mirrors prod:**

## Contracts         <!-- /contracts -->
- **Typed models / schemas / migrations:**
- **Boundary units/scale agreed:**

## Build log         <!-- /build --> (one entry per feature; see docs/features/*)
| Feature | DoD (incl. security) met? | How verified | Doc |
|---|---|---|---|

## Dev-complete      <!-- /dev-check -->
- [ ] Every core-scope feature built & runs
- [ ] Exit criteria + security DoD verified (with evidence)
- [ ] No hardcoding · prompts externalized · contracts typed · builds green
- [ ] Scope re-check — nothing crept in

## Tests             <!-- /test -->
- **Unit / integration / regression coverage:**
- **Adversarial/security (prompt-injection, authz) cases:**
- **Live-path verified (not just isolated units):**

## Evaluation        <!-- /eval -->
- **Is it good? (measured, not assumed):**
- **Metrics + confidence score:**

## Ship log          <!-- /ship -->
| Date | What shipped | Review/security | Docs reconciled | PR |
|---|---|---|---|---|

## Learnings         <!-- /learn -->
- **Success metric + result:**
- **Retro (what worked / what to change):**
- **Decided next (from evidence):**
