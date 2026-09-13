# Publishing a backlog to GitHub — provisioning, guards, dedup, mirroring

> Loaded by `/tickets` **Step 2** (both modes) and **Step 3A**, on demand. `SKILL.md` carries the
> guards as one-liners — never create a remote, never overwrite a template, never half-publish; this
> file carries the procedure behind each.

## §Provision and pre-flight

1. **Templates — one master per file.** If `.github/ISSUE_TEMPLATE/feature_ticket.md` is missing, copy it
   from the bundled `templates/feature_ticket_template.md` — the playbook owns the **issue** template
   (Lanekeeper's own `task.yml`/`bug.yml` forms may sit beside it; both carry the file-paths heading
   Lanekeeper reads). If `.github/PULL_REQUEST_TEMPLATE.md` is missing **and the project is not in lane
   mode**, copy `templates/pull_request_template.md`; **in lane mode, do not write a PR template** —
   Lanekeeper owns the PR template and the gate workflow (§Lane mode rule 4). Never overwrite a template
   the project already has.
2. **Remote guard — NEVER blindly create a remote repository.** Run `git remote -v`.
   - **No remote:** write tickets to `docs/issues/` only and say:
     *"Tickets written to `docs/issues/`. No remote is linked — run `git remote add origin <url>`, then `/tickets` again to publish."*
   - **Remote present:** check `gh auth status` and `gh repo view`. If either fails, keep the local files and
     tell the user to run `gh auth login`. **Do not run `gh repo create`.**
3. **Capability pre-flight — a half-published backlog is worse than none.** Creating issues, milestones,
   labels and **project boards** are *separate* permissions (`gh auth status` lists the token scopes; the
   board needs `project`). Check all four **before publishing anything**; if the token can create issues
   but not milestones, labels or the board, either **degrade with a stated warning** (issues without a
   board, plus the one command that grants the scope: `gh auth refresh -s project`) or publish nothing —
   the user chooses. Never discover the gap halfway through the backlog.
4. **Dedup index.** With a verified remote, fetch once:
   `gh issue list --state all --limit 100 --json number,title`
   Match a planned ticket to an existing issue by its **ID tag** (`[M2-SLICE-01]`, `[M2-TICK-01]`, `[ADHOC-07]`)
   first, exact title second. On a match: skip and log `Skipping [M2-TICK-01]: exists as #<num>`. Never edit
   or close an existing issue.
   **The one exception is an owner-confirmed regroup** (new lanes on a backlog already published): change only
   the `lane:`/`owner:` labels and the Lane/Owner lines of the body, and only after a pre-flight shows every
   GitHub body still equals its committed file — a body edited on GitHub stops the run. (case file: Regrouping a backlog already on GitHub)
4. **Numbering.** Derive the next free number from `docs/issues/` **and** the fetched issue list together,
   so a re-run after a partial publish cannot reuse an ID.
5. **Draw `docs/issues/` in the structure map before the first ticket file exists.** A two-way map check
   (`STRUCTURE.md` ↔ tree) fails CI on an undrawn folder; the first `/build` PR owes the same line for
   `docs/features/` — say so in `docs/issues/README.md`. (case file: The folder the map did not draw)

## §Mirror the plan structure onto GitHub
`#Plan` → milestones → lanes → tickets has a native GitHub equivalent at every level, and a flat list uses
none of it: the Milestone column stays empty, tickets cannot be filtered by feature, and ad-hoc bugs never
link back to the feature they belong to. On publish:
- **Milestone** — parse `PRODUCT.md#Plan`, create each **missing** GitHub milestone (titles derived from
  `#Plan`, never invented) and pass it on `gh issue create`. **Carry the target date across:** `#Plan`
  gives each milestone a date, `gh` takes it as `--due-date YYYY-MM-DD` (or `due_on` via the API), and
  dropping it lands every milestone with `due_on: null` — the one field the milestone view sorts and
  warns on, so the plan's own sequencing disappears at exactly the place a team reads it. A milestone
  with **no** date in `#Plan` is created without one, and that is worth saying out loud rather than
  inventing a date to fill the field.
- **Lane + owner labels** — the ticket's `Lane` (a module) becomes a label in the **`lane: <name>`** form
  required by `MECHANISMS.md` §Lane mode rule 4, and its `Owner` becomes **`owner: <role>`** (`owner: senior`).
  Do not invent a second spelling; the gate depends on that one.
- **Feature doc — reference the PATH, not a link.** `/build` writes `docs/features/<feature>.md` *after* the
  ticket exists, so a markdown link would 404 on day one. `/build` may add a live link when it creates the file.
- **Idempotent like the issues already are.** `gh milestone`/`gh label create` error on an existing name, so a
  re-run must **reuse, not fail**. Running `/tickets` twice creates no duplicate milestone, label or issue.

## §The Delivery Board — every ticket is a card with four fields set

Labels and milestones are a list; the board is the **map** — who owns which lane, who is sitting in it
today, and what is moving. It is the surface a solo builder and a team of four read the same way, and
the base a project keeps for its whole life. (case file: The base MarkVid runs on)

1. **Create it once.** Find a project titled `<Product> — Delivery Board` for the repo owner
   (`gh project list --owner <owner>`); create it only if absent (`gh project create --owner <owner>
   --title "..."`). Fields, each a single-select, added only when missing: **Status** (`Todo` · `In Queue`
   · `In Progress` · `Done`) · **Owner** (`Senior` · `Junior`) · **Lane** (one option per lane from
   `slicing.md` §Lanes are modules) · **Seat** (`SR1` by default; the user adds `SR2`, `JR1` … when they
   want a second chair). Link the project to the repository.
   **A new project already has `Status`, with no `In Queue`** — `field-create` cannot extend it; set all four
   options with GraphQL `updateProjectV2Field` (every existing option kept) *before* the first card. (case file: The Status field that was already there)
2. **Add every published issue as a card and set all four fields** — `gh project item-add`, then
   `gh project item-edit --field-id ... --single-select-option-id ...` for Status (`Todo`), Owner (the
   ticket's), Lane (the ticket's) and Seat (`SR1` unless the user named seats). **A card added without its
   fields is invisible on every lane view.**
3. **Read it back, do not assume it.** `gh project item-list <n> --owner <owner> --format json` — its field
   keys come back **lowercase** (`status`, `owner`, `lane`, `seat`); confirm every card reads the way it was
   set, and put the count in the close (`14 cards · 14 with all four fields`). A read-back that reports
   `UNSET` for everything is a malformed query, not an empty board — check one card you know is set.
4. **Idempotent.** A re-run finds the board, the fields, the options and the cards by name and adds none
   twice. Never rename or delete a board, a field or an option the project already has.
5. **No `project` scope** → publish issues, milestones and labels, say in the close that the board was
   **not** created, and give `gh auth refresh -s project` followed by `/tickets` again. Never half-stamp.
