# Lane mode — the seam between product-playbook and Lanekeeper

Design note for v1.7.0. Read `PRINCIPLES.md` §Lane mode for the rules; this file records why they
are shaped this way, what the change touches, and what is verified.

## The problem

[Lanekeeper](https://github.com/kish21/parallel-agents) reads product-playbook's tickets, turns each
ticket's file list into a lane, gives one agent a worktree per lane, and fails any PR that leaves its
lane. Its parser already accepted the playbook's `Target Files` heading (verified in Lanekeeper's
`config.py` defaults: `allowed file paths`, `target modules`, `target files`). So the two tools already
talked. Three things broke the moment more than one agent ran:

1. **Both tools provisioned templates.** `/tickets` wrote an issue template *and* a PR template;
   Lanekeeper ships `task.yml`, `bug.yml` and its own PR template. Whoever ran second either
   overwrote or was refused.
2. **The spine is one file.** Every `/build` appended a row to `PRODUCT.md#Build log`; every `/ship`
   wrote `CHANGELOG.md`. Three lanes meant three PRs touching the same file outside every lane, so
   the gate failed them or the merges conflicted.
3. **Horizontal tickets are anti-lanes.** One layer of one feature is a ticket; four of them are four
   lanes for one feature, and every change collides.

## The contract

**Exit criteria (all met in this change):**
- `PRINCIPLES.md` §Lane mode exists, defines detection and the four rules once; skills reference it.
- `/tickets`: Lane field emitted; Target Files include feature doc + tests, never a spine file;
  horizontal in lane mode carries a reason; no PR template written when Lanekeeper is present.
- `/build`: reads `.lane`; a file outside `ALLOW` is flagged, not touched; no `PRODUCT.md` write
  inside a lane; Build-log row lives in the feature doc.
- `/dev-check`: reconciles feature-doc rows into `#Build log`; checks `lanes.yaml` against `#Scope`;
  runs cross-lane seams on the merged base.
- `/ship`: `lanekeeper check` before the PR; `lane:` label; Ship log + CHANGELOG written post-merge on
  the base branch.
- Outside lane mode every skill behaves exactly as in 1.6.1.

**Interaction map:**

| Producer | Artifact | Consumer |
|---|---|---|
| `/tickets` | issue body: `Lane` heading + `Target Files` list | Lanekeeper `divide` / `spawn --ticket` (boundary + lane name) |
| Lanekeeper `spawn` | `.lane` (`TASK`, `ALLOW`, `DENY`) in the worktree | `/build` Step 0 (file-level scope gate), `/ship` step 6 |
| `/build` | `docs/features/<feature>.md` with `## Build log row` | `/dev-check` step 0 (spine reconciliation) |
| Lanekeeper `check --write-workflow` | `lanekeeper-gate.yml` + PR template | `/ship` (label + pre-PR check); `/tickets` (does not write a PR template) |
| Lanekeeper `divide --confirm` | `lanes.yaml` | `/dev-check` step 4 (lane ↔ scope) |

**Decisions worth recording:**
- *One writer for the spine, not a shared zone.* A `shared:` zone with `merge=union` would let every
  lane append to `PRODUCT.md`, but union merges silently interleave rows and the gate would have to
  exempt the spine for every lane. Reconciling in `/dev-check` and `/ship` keeps lane PRs clean and
  keeps the gate honest. The shared-zone route stays available as the user's explicit choice.
- *Playbook owns the issue template, Lanekeeper owns the PR template.* The producer of a document
  owns its template: the playbook produces tickets; Lanekeeper produces the gate the PR must pass.
- *Lane field is optional.* Lanekeeper groups by paths when it is blank, and a wrong lane name is
  worse than none.

## Test plan and what is actually verified

- `tools/check.py` (CI): skill set consistency, phase-template structure, line budget, one version
  across CHANGELOG / manifest / plugin.json / README badge. **Run and green.**
- `evals/evals.json`: two new cases, `tickets-lane-mode` and `build-lane-mode`, stating the expected
  behaviour. **Listed only — the evals are not executed by CI yet** (open item in the repo).
- **Not verified in this change:** a live run of `/tickets` → `lanekeeper start` → `/build` in a
  worktree → `/ship` with the gate. That is the next session's job, against
  `kish21/mini-issue-tracker`, which already has three playbook-written issues.

**Verified against Lanekeeper's real parser** (`lanekeeper.divide.boundary.read` with default
`DivideConfig`, run on a ticket filled from the new template): paths = exactly the three listed files,
lane = `checkout`, the guidance comment lines land in `ignored_lines`. This run found two template
bugs that were fixed before publishing: backticked example paths inside the Target Files comment were
read as real boundary paths (the pre-1.7.0 template had the same defect), and a blank Lane field
returned the HTML comment as the lane name. The template now keeps backticks out of that comment and
puts the Lane guidance above the heading.

## Known gaps on the Lanekeeper side (not fixed here, `kish21/parallel-agents`)

- `templates/pull_request_template.md` still offers layer lanes (interface · service · data ·
  platform), contradicting its "a lane is a feature" rule and this seam.
- `boundary._section` does not strip HTML comments, so any issue form whose comment sits under the
  Lane or Target Files heading leaks the comment into the lane name or the path list. Fixed on the
  playbook side by template layout; the parser should strip `<!-- … -->` regardless.
