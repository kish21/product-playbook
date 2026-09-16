# Publishing a backlog to GitHub — provisioning, guards, dedup, mirroring

> Loaded by `/tickets` **Step 2** (both modes) and **Step 3A**, and by a shape-changing `/structure` re-run
> (§A path rewrite reaches GitHub), on demand. `SKILL.md` carries the
> guards as one-liners — never create a remote, never overwrite a template, never half-publish; this
> file carries the procedure behind each.

## §Provision and pre-flight

1. **Templates — one master per file.** If `.github/ISSUE_TEMPLATE/feature_ticket.md` is missing, copy it
   from the bundled `templates/feature_ticket_template.md`. If `.github/PULL_REQUEST_TEMPLATE.md` is missing,
   copy `templates/pull_request_template.md`. Never overwrite a template the project already has.
2. **Remote guard — NEVER blindly create a remote repository.** Run `git remote -v`.
   - **No remote:** write the local files only — the tickets to `docs/issues/` and, in Mode A only, the plan to
     `TICKETS.md` (Mode B never writes it) — publish nothing, and say *"Tickets written to `docs/issues/`."*, in
     Mode A *"The plan is in `TICKETS.md`."*, then *"No remote is linked — run `git remote add origin <url>`, then `/tickets` again to publish."*
   - **Remote present:** check `gh auth status` and `gh repo view`. If either fails, keep the local files and
     tell the user to run `gh auth login`. **Do not run `gh repo create`.**
3. **Capability pre-flight — a half-published backlog is worse than none.** Creating issues, milestones,
   labels and **project boards** are *separate* permissions (`gh auth status` lists the token scopes; the
   board needs `project`). Check all four **before publishing anything**; if the token can create issues
   but not milestones, labels or the board, either **degrade with a stated warning** (issues without a
   board, plus the one command that grants the scope: `gh auth refresh -s project`) or publish nothing —
   the user chooses. Never discover the gap halfway through the backlog.
4. **Dedup index.** With a verified remote, fetch once:
   `gh issue list --state all --limit 1000 --json number,title`
   **If the list comes back exactly as long as the limit, raise the limit and fetch again** — a truncated
   index silently drops the oldest issues, and a re-run then publishes them a second time.
   Match a planned epic or ticket to an existing issue by its **exact bracketed ID tag** (`[M2-PARTY]`,
   `[M2-PARTY-01]`, `[ADHOC-07]` — `[M2-PARTY]` never matches `[M2-PARTY-01]`) first, exact title second. On a
   match: skip and log `Skipping [M2-PARTY-01]: exists as #<num>`. Never edit or close an existing issue.
   **The one exception is an owner-confirmed regroup** (new lanes on a backlog already published): change only
   the `lane:`/`owner:` labels and the Lane/Owner lines of the body, and only after a pre-flight shows every
   GitHub body still equals its committed file, compared as §A path rewrite reaches GitHub compares — a body that
   does not is settled as that section's item 4 settles one, and an unsettled body stops the run. (case file: Regrouping a backlog already on GitHub)
   **A committed path rewrite (a shape-changing `/structure` re-run) is the same exception** — paths only, by
   §A path rewrite reaches GitHub. **Every Mode A re-run runs that section's pre-flight before any other edit**,
   over the skipped open tickets whose file has a `path rewrite` commit, and finishes whatever sync or settle it
   finds — a move whose sync could not run is otherwise left behind for good.
   **A link is not an edit.** A skipped (already published) ticket still gets its missing *blocked by* links
   and its missing parent link in §Mirror the plan structure — both are relationships on the issue, not its
   body, so the rule above is untouched and a re-run completes a backlog that was published without them.
5. **Numbering.** Derive each epic's next free number from `docs/issues/` **and** the fetched issue list
   together, so a re-run after a partial publish cannot reuse an ID; an existing epic keeps its code
   (`slicing.md` §Epics).
6. **Draw `docs/issues/` in the structure map before the first ticket file exists.** A two-way map check
   (`STRUCTURE.md` ↔ tree) fails CI on an undrawn folder; the first `/build` PR owes the same line for
   `docs/features/` — say so in `TICKETS.md`. (case file: The folder the map did not draw)

## §An earlier backlog — old IDs and `docs/issues/README.md`

A project published before epics carries `[M<n>-SLICE-<nn>]` / `[M<n>-TICK-<nn>]` IDs and the old plan file.
A re-run brings it forward without duplicating anything:
- **A published ID is never renamed.** Dedup matches the old tag, the old ticket files stay, and `TICKETS.md`
  lists those tickets under their old IDs. Only a new ticket takes an epic-scoped ID.
- **The epics are proposed over the existing tickets**, shown in full with the rest of the proposal and
  confirmed. Attaching a published ticket to its epic is a parent link — a relationship, like *blocked by* —
  so it needs no regroup exception.
- **`docs/issues/README.md` is migrated, never kept beside `TICKETS.md`:** its plan content moves into
  `TICKETS.md`, anything in it that is status is dropped (the board holds status), the README is deleted in
  the same commit, and the close says so. Two plan files disagree the first time one of them is edited.

## §An issue body is its ticket file

**A ticket's issue body is its file in `docs/issues/`, unchanged:** `gh issue create --title "[<ID>] <title>"
--body-file docs/issues/<file>`, in both modes — never retyped, trimmed, or given a header or footer. So a ticket
file holds **no front matter**: `name:`, `about:`, `title:` and `labels:` belong to the issue template in
`.github/ISSUE_TEMPLATE/`, and the title, labels and milestone go on the command's flags. The regroup pre-flight
and §A path rewrite reaches GitHub both decide whether someone edited an issue by comparing its body with its
file, so a body made any other way reads as edited from the day it is published. (case file: The paths that moved in the repo, not on GitHub)

## §A path rewrite reaches GitHub

A shape-changing `/structure` re-run rewrites the paths in `docs/issues/*.md` and `TICKETS.md`, but the issues
a team reads still name the old folders. **The run that moved the paths syncs the issues, in the same run** —
leaving it to a later `/tickets` re-run means leaving it to a phase nothing tells the user to run. (case file: The paths that moved in the repo, not on GitHub)

1. **The rewrite is committed as a `path rewrite`** — those words in the commit message and, when it reaches the
   default branch through a pull request, in the PR title too, so a squash-merge keeps them. A file's rewrites are
   `git log --reverse --grep "path rewrite" --format=%H -- <file>`, oldest first; `<rewrite>` is the newest.
   **A run that rewrote paths and finds no such commit stops and says the marker is missing** — never reports
   `0 issues synced`. What a sync publishes is exactly what those commits changed; anything else reaches an issue
   only through item 4's settle. Remote guard first (§Provision item 2): no remote → nothing was published, nothing to sync.
2. **Pre-flight every open ticket issue whose file has a `path rewrite` commit, before editing any.** Fetch the
   open bodies once to a scratch file (`gh issue list --state open --limit 1000 --json number,title,body`;
   §Provision item 4's limit rule applies) and match each file to its issue **by its bracketed ID tag, never by
   title** — a file with no issue was never published. **Compare a body with a version of its file with line
   endings, trailing whitespace and task-list marks normalised** — `[x]` reads as `[ ]`, because a ticked box is
   progress, not an edit. Walk the file's `path rewrite` commits oldest first:
   - the body equals the file at `<rewrite>` **or at any later commit** (`git log --format=%H <rewrite>..HEAD --
     <file>`) → **current**, skip — a regroup or a later edit of the file moved it on, not a person;
   - the body equals `git show <commit>^:<file>` for one of them, and each later rewrite starts where the one
     before it ended (its `^` version equals the earlier commit's version) → **to sync**;
   - **anything else → to settle** (item 4): it was edited on GitHub, published in another shape than its file
     (§An issue body is its ticket file), or its file changed some other way between two rewrites.
3. **Closed issues keep their paths** — they name what they were built against. **An epic carries no paths**
   (§Epics are parent issues), so nothing on it is synced.
4. **Show the list and ask once; nothing is edited until every issue on it is answered.** An issue to sync shows
   its ticket ID, the diff from the body's version to `<rewrite>`'s (`git diff <commit>^ <rewrite> -- <file>`),
   and any ticked line the rewrite did not replace one for one, for the owner to place.
   **A diff that changes more than paths is flagged**: a squash can carry another edit in with the move, and the
   owner's yes covers only what the list shows. **An issue to settle** shows its body against the file at `HEAD`,
   and the owner picks **the file wins** (the difference is dropped) or **the GitHub text wins** (it is written
   into the ticket file, the moved paths in their new form, and committed — never as a `path rewrite`); one answer
   may cover several. **An issue left unsettled stops the sync**, and nothing is edited: a body someone wrote on
   GitHub is theirs, and a backlog half on old paths and half on new is read as all current.
5. **Write each body from a scratch file** with `gh issue edit <n> --body-file`, **keeping its ticks**; the body
   changes, nothing else does. A synced issue gets `git show <rewrite>:<file>`: a line the rewrite left alone keeps
   its mark, a line it replaced one for one passes its mark on, and any other tick goes where the owner placed it.
   A settled issue gets `git show HEAD:<file>`, each tick kept on a line still there, so every later run reads it
   as current.
6. **Read every edited body back**, compared the same way: a synced one equals `<rewrite>`'s version, a settled
   one `HEAD`'s, and each carries the ticks it was written with. A mismatch is reported.
7. **The close counts it** — `9 issues synced · 1 settled · 2 closed kept their paths`. A sync that could not run
   (`gh` not signed in, the rewrite not yet committed, an issue left unsettled) is named with its issues, what
   clears it — sign in, commit, or settle — and the step after: run `/tickets` once it is cleared, and its Mode A
   re-run finishes the sync (§Provision item 4).

## §Mirror the plan structure onto GitHub
`#Plan` → milestones → epics → lanes → tickets has a native GitHub equivalent at every level, and a flat list
uses none of it: the Milestone column stays empty, tickets cannot be filtered by feature, and ad-hoc bugs never
link back to the feature they belong to. On publish, in this order:
- **Milestone** — parse `PRODUCT.md#Plan`, create each **missing** GitHub milestone (titles derived from
  `#Plan`, never invented) and pass it on `gh issue create`. **Carry the target date across:** `#Plan`
  gives each milestone a date, `gh` takes it as `--due-date YYYY-MM-DD` (or `due_on` via the API), and
  dropping it lands every milestone with `due_on: null` — the one field the milestone view sorts and
  warns on, so the plan's own sequencing disappears at exactly the place a team reads it. A milestone
  with **no** date in `#Plan` is created without one, and that is worth saying out loud rather than
  inventing a date to fill the field.
- **Lane + owner labels** — the ticket's `Lane` (a module) becomes a label in the **`lane: <name>`** form
  (with the space), and its `Owner` becomes **`owner: <role>`** (`owner: senior`). Do not invent a second
  spelling: a board or label filter on one spelling silently misses the other.
- **Epics, then tickets, then the parent links** — §Epics are parent issues.
- **Dependencies — LINK them, do not only write them.** `Depends On` in a body is prose GitHub cannot
  read; the native relationship is *blocked by*. After **every** issue of the backlog exists (new or
  skipped), for each ticket and each ID in its `Depends On`: resolve the ID to its issue number from the
  dedup index, then
  `gh api -X POST repos/<o>/<r>/issues/<n>/dependencies/blocked_by -F issue_id=<blocker database id>`
  where the id is `gh api repos/<o>/<r>/issues/<blocker n> -q .id` — the numeric database id, **not** the
  issue number and not the node id. Link a **closed** blocker too (GitHub shows it as cleared; skipping it
  makes the link set differ from the body). Every *waits for* coordination point in `TICKETS.md` must also be
  a `Depends On` on the dependant ticket, and so a link — a point with no matching link is a gap in the
  ticket, fixed there. A *builds against* point is that ticket's `Builds against` and is **never** linked: a
  *blocked by* link would make `/build` stop a ticket that is free to start (`slicing.md` §Waiting or
  building against). Read back first (`GET …/dependencies/blocked_by`) and add only what is
  missing: a duplicate is `422 Target issue has already been taken`, and a pull-request number is
  `422 … may only be an issue`. The issue then shows *Blocked by #8* in its sidebar and #8 shows *Blocking
  #9* — a second builder opening a card sees whether it is startable without reading `TICKETS.md`.
  (case file: Written down, never linked)
- **Feature doc — reference the PATH, not a link.** `/build` writes `docs/features/<feature>.md` *after* the
  ticket exists, so a markdown link would 404 on day one. `/build` may add a live link when it creates the file.
- **Idempotent like the issues already are.** `gh milestone`/`gh label create` error on an existing name, so a
  re-run must **reuse, not fail**. Running `/tickets` twice creates no duplicate milestone, label, epic,
  issue, parent link or *blocked by* link.

## §Epics are parent issues — tickets are their sub-issues

An epic is a GitHub issue whose sub-issues are its tickets, so the repository shows the hierarchy itself: the
epic lists its tickets with a progress bar, each ticket names its parent, and the board can group cards by
GitHub's *Parent issue* field. `gh` has no sub-issue command, so this is the REST API.
1. **Create each missing epic issue** before its tickets, deduplicated like any issue (§Provision item 4):
   title `[M<n>-<EPIC>] <epic name>`; the milestone; the `lane:` and `owner:` labels of its lane; a body
   naming the milestone, the lane, the owner and `TICKETS.md` — **never a ticket list or a status**: the
   sub-issues are the list, GitHub computes the progress, and a body that lists tickets goes stale on the
   first re-run that adds one.
2. **Attach the tickets, after every epic and ticket issue exists** (new or skipped). For each epic, read
   back first — `gh api "repos/<o>/<r>/issues/<epic n>/sub_issues?per_page=100" -q '.[].number'` — then, for
   each of its tickets in build order that is not listed:
   - `gh api repos/<o>/<r>/issues/<n>/parent` — a 404 (*No parent issue found*) means free; a parent that is
     another issue means the ticket already sits under a different epic: **report it and leave it** — moving a
     ticket between epics is an owner-confirmed regroup, so **never pass `replace_parent`**.
   - `gh api -X POST repos/<o>/<r>/issues/<epic n>/sub_issues -F sub_issue_id=<ticket database id>`, where the
     id is `gh api repos/<o>/<r>/issues/<n> -q .id` — the numeric database id, **not** the issue number and
     not the node id (the same id a *blocked by* link takes).
3. **Read it back, do not assume it.** `GET …/sub_issues` for each epic returns exactly the tickets
   `TICKETS.md` lists under it — none extra, and none missing except a ticket reported in step 2 as under a
   different parent, which the close names — and the close states the count
   (`3 epics · 8 sub-issues`). Before trusting the read-back, remove one
   (`gh api -X DELETE repos/<o>/<r>/issues/<epic n>/sub_issue -F sub_issue_id=<id>`), watch the check go red,
   and attach it again: a read-back never seen failing proves nothing.
4. **Idempotent.** A re-run finds each epic by its tag, reads its sub-issues back and adds only what is
   missing, so it creates no second epic and no second link.
5. **An epic is not a board card.** Its tickets are cards (§The Delivery Board); the epic's progress is
   GitHub's own count of its closed sub-issues, so nothing writes a status onto the epic.

## §The Delivery Board — every ticket is a card with four fields set

Labels and milestones are a list; the board is the **map** — who owns which lane, who is sitting in it
today, and what is moving. It is the surface a solo builder and a team of four read the same way, and
the base a project keeps for its whole life. (case file: The base a real product runs on)

1. **Create it once.** Find a project titled `<Product> — Delivery Board` for the repo owner
   (`gh project list --owner <owner>`); create it only if absent (`gh project create --owner <owner>
   --title "..."`). Fields, each a single-select, added only when missing: **Status** (`Todo` · `In Queue`
   · `In Progress` · `Done`) · **Owner** (`Senior` · `Junior`) · **Lane** (one option per lane from
   `slicing.md` §Lanes are modules) · **Seat** (`SR1` by default; the user adds `SR2`, `JR1` … when they
   want a second chair). Link the project to the repository.
   **A new project already has `Status`, with no `In Queue`** — `field-create` cannot extend it; set all four
   options with GraphQL `updateProjectV2Field` (every existing option kept) *before* the first card. (case file: The Status field that was already there)
2. **Add every published ticket issue as a card and set all four fields** (an epic is a parent, not a
   card — §Epics are parent issues) — `gh project item-add`, then
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
