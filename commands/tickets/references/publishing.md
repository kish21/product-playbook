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
3. **Capability pre-flight — a half-published backlog is worse than none.** Creating issues, milestones and
   labels are *separate* permissions. Check all three **before publishing anything**; if the token can create
   issues but not milestones or labels, either **degrade to plain issues with a stated warning** or publish
   nothing — the user chooses. Never discover the gap halfway through the backlog.
4. **Dedup index.** With a verified remote, fetch once:
   `gh issue list --state all --limit 100 --json number,title`
   Match a planned ticket to an existing issue by its **ID tag** (`[M2-SLICE-01]`, `[M2-TICK-01]`, `[ADHOC-07]`)
   first, exact title second. On a match: skip and log `Skipping [M2-TICK-01]: exists as #<num>`. Never edit
   or close an existing issue.
4. **Numbering.** Derive the next free number from `docs/issues/` **and** the fetched issue list together,
   so a re-run after a partial publish cannot reuse an ID.

## §Mirror the plan structure onto GitHub
`#Plan` → milestones → lanes → tickets has a native GitHub equivalent at every level, and a flat list uses
none of it: the Milestone column stays empty, tickets cannot be filtered by feature, and ad-hoc bugs never
link back to the feature they belong to. On publish:
- **Milestone** — parse `PRODUCT.md#Plan`, create each **missing** GitHub milestone (titles derived from
  `#Plan`, never invented) and pass it on `gh issue create`.
- **Lane label** — the ticket's `Lane` field becomes a label in the **`lane: <name>`** form required by
  `MECHANISMS.md` §Lane mode rule 4. Do not invent a second spelling; the gate depends on that one.
- **Feature doc — reference the PATH, not a link.** `/build` writes `docs/features/<feature>.md` *after* the
  ticket exists, so a markdown link would 404 on day one. `/build` may add a live link when it creates the file.
- **Idempotent like the issues already are.** `gh milestone`/`gh label create` error on an existing name, so a
  re-run must **reuse, not fail**. Running `/tickets` twice creates no duplicate milestone, label or issue.
