# /build — the review stretch (Step 5, round 1 and round 2)

Read by the helper agent that reviews with a fresh context, and by the build conversation for §Findings. **The helper
reports; the build conversation fixes, commits and writes `## Review`** — two writers on one branch collide, and a
logged lean build's review helper sat idle four minutes waiting for a reviewer it had started itself.

**Who runs what, both at once:** on Claude Code the build conversation runs `/code-review` directly (it starts its own
reviewer) while ONE helper runs the security review; on a tool without `/code-review` (`CAPABILITIES.md` §Code review)
the helper runs both. Neither waits for the other.

## Helper prompt

Fill in the `<…>` and give the helper exactly this (it has no other context):

> Review ticket `<ticket id>` of the project at `<absolute path>`, branch `<branch>`, committed range
> `<base>...HEAD` (`git diff <base>...HEAD`) — the `<security review | code and security review>`. Its definition of
> done: `<the DoD lines>`. Rules: `<absolute path of this file>` §In the helper — open it first. Change no file.
> Return ONLY the findings table (severity · file:line · what would go wrong for a user) and one line per changed
> code file saying what you checked there — or CLEAN and those lines — plus anything you could not do.

## In the helper

- **Every check that guards access (an owner's email, a token, a tenant, a limit) is read for the value MISSING, EMPTY and SUPPLIED BY THE MODEL**, not only for a wrong one — a logged build checked the email only when one was given, so no email meant any order's tracking, and let an email the model supplied replace the session's. A check that runs only when its input is present fails open.
- **Round 1.** The review runs **BEFORE the push, the PR and the close**, so its verdict lands in the record. **Report, never fix** — the build conversation fixes every finding inside the ticket's files, each with its proof, and **commits the fixes locally** before any round 2.
- **The code review runs directly** (`CAPABILITIES.md` §Code review) — it starts its own reviewer; wrapping it in another helper reads the diff twice (`run_report` flags it).
- **Run `/security-review` inside a subagent — this helper IS that subagent**, so run it as your own work: invoked in the build conversation it takes over the turn and ends it on its report; here, its report is your answer. Never start another agent for it and wait. (case file: The review that ended the run again)
- **The base, with or without a remote:** `git merge-base HEAD <default branch>`. When the security review command cannot find its base, review `git diff <base>...HEAD` against `PRINCIPLES.md` §Production safeguards by hand and say in the table which ran — and why, from what `git remote -v` printed NOW (the build start prints it), never from an older note.
- **A tool without an independent reviewer** (no helper agents): the security review goes to **another tool** — the build conversation asks the user the exact question `status.py ticket` prints; its review is recorded as `another tool: <name>`. Never recommend approving your own security review.
- ⚠️ **If you cannot invoke it, ASK the user to run it, or do the deep pass by hand and say which you did** — see `PRINCIPLES.md`, *Composed skills*.
- **Is it wired?** Name where the path the ticket's demo runs calls the new code (file:line), or say it is not wired yet and which ticket wires it — a logged build shipped a service nothing calls, and its demo could never happen. `status.py ticket` refuses a branch whose additions nothing outside their module uses, unless `--not-wired "<why>"`.
- **Record the route that ran** on the table's first line: `helper agent` · `self-review` · `by hand` — never a review command your tool does not have (`CAPABILITIES.md` §Code review).

## Findings

For the build conversation, with both reviews' findings in hand:

- **Findings that are not this ticket's.** **A finding that leaves a DoD line unmet is never "outside"** — whichever file its fix lives in, fix it now or STOP and ask the user; it is never deferred. **Any other finding outside the ticket's files is filed IN THIS RUN**, never handed to the user as a list to file — **MEDIUM or above: one issue each** (`/tickets "<finding>"`); **LOW and unrated: ONE issue for the run**, every finding on its own line with its file and what goes wrong (a board of one-line tickets buries the ones that matter; grouped, none is lost) — **and named in the close, never fixed here** (Step 4's flake rule, applied to reviews). **A security finding on a PUBLIC repo is never filed publicly** — never into an issue or a committed file (the spine of a public repo is public too): put it to the user in the close. (case file: The findings handed back)
- **Fixes through `gate.py` checks, with whole-file writes or one message of edits per file** — the same rules as Step 2 item 3.
- **Write the feature doc's `## Review` section once:** both reviews' findings in one table and one line per changed code file saying what was checked there. `status.py ticket` refuses a row whose `## Review` does not name every changed code file, or whose count disagrees with the table.

## The findings table

| Severity | File:line | What would go wrong for a user | Fixed by (sha) or filed as |
|---|---|---|---|

Severity may sit in any column. No findings: the word **CLEAN**, then the per-file lines — a review that names no file it read is not a review.
