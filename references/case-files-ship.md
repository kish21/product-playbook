# Case files — /ship

War stories behind the one-line lessons in `commands/ship.md`. Each heading is pointed to from
the skill file as `(case file: <heading>)`.

## Dry-run live verify

A shipped project added an LLM-judge gate with a bounded auto-rewrite to a content pipeline.
The ship checklist called for a post-deploy live run to see the new log signals fire. The only
production record at the right pipeline stage was the owner's real project, sitting in
`pending_review` with the owner's own variant selection recorded — re-running the stage would
have overwritten the variants the owner had reviewed, and calling the pipeline's advance
endpoint would have *approved the pending human review* and started the next (paid) stage.

The fix: a scratch harness that loaded the real persisted inputs from production, ran the exact
deployed service/runner code (same commit) with real model calls, and simply never called the
persistence layer. The full decision table fired on real data — including a provider failure
mid-rewrite that proved a money-guard branch no test environment had exercised under real
conditions — and the owner's pending decision state was untouched.

Two side benefits observed: (1) a dry run can safely exercise *failure* paths that staging
fixtures rarely produce; (2) the run's evidence (score variance across identical judge calls, a
token-cap truncation) fed straight into already-filed follow-up issues instead of being lost.

## The environment blocker that was my own typo

A ticket on a shipped project changed one LLM-judge rubric dimension. Code review was clean and
the recorded calibration re-ran green, but the pre-push gate failed on a test in a completely
unrelated module: `ModuleNotFoundError: No module named 'supabase'`, in a project whose whole
data layer is Supabase.

The diagnosis was right as far as it went. `python` in that shell resolved to a DIFFERENT
project's virtualenv, which had no `supabase` installed, and the gate script calls bare `python`.
Stashing to a clean tree reproduced the same failure, which proved the diff was innocent.

The attempted workaround was to prepend the project's own venv to `PATH`. It appeared to do
nothing — `command -v python` kept returning the wrong interpreter. Two more attempts, same
result. That was reported to the user as an environment blocker with three options, one of which
was `git push --no-verify`.

It was not an environment blocker. The `PATH` override contained a Windows drive-letter path
(`c:/Users/...`), and because `PATH` is colon-separated, the colon in `c:` split the entry into
two meaningless fragments. The override had never existed. In POSIX form (`/c/Users/...`) it
worked on the first try, the gate went 7/7, and the push went through the hook normally.

The cost was one wasted user round-trip and a near-miss on bypassing a push gate for a problem
that was not real. The tell was available the whole time and never checked: after applying a
workaround, confirm the workaround APPLIED (`command -v python`) before drawing any conclusion
from the fact that the symptom persisted. A workaround that silently no-ops is indistinguishable
from an environment that refuses to cooperate — and the second story is far more flattering,
which is exactly why it gets believed.

## The second review round

**lanekeeper #38, 2026-09-01.** A ~2,000-line step (a new `divide` package, a new CLI
command, a new config section) went through `/code-review` at high effort. It returned
10 findings, every one real and reproduced. They were fixed carefully — deny/shared
zones honoured in the collision check, the draft file no longer clobbered, configured
paths validated — and the whole suite went green.

The second review round on the fixed tree returned **7 more findings**, and at least
four of them existed only because of the first round's fixes:

- The fix for "an existing lane file gets clobbered" added a `--fresh` overwrite switch —
  reusing step 1's flag, whose documented meaning is "ignore the recorded judgement". A
  user re-running `start --fresh` for that meaning would now silently lose an edited file.
- The fix for "deny and shared zones are dropped" suppressed *every* structural overlap
  whenever any zone existed anywhere, so one answered overlap hid all the unanswered ones.
- The fix for "a feature with a directory on one side only is missed" read feature names
  out of filenames by concatenating the surviving words: `useAuth.ts` became `useauth`,
  a word in no project, and the very files the fix cited stayed unmatched.
- A commented-out block the file instructs the user to uncomment emitted a blank list
  item, which loads as the path `"None"` — passing the "does this entry have a boundary"
  check with a boundary that matches nothing.

None of these were in the original code. Each was written while looking at a finding
rather than at the design, and every one passed the suite, because the suite was written
against the design the fixes had just quietly changed.

**The rule:** a review is not done when the findings are fixed. Fixing is editing, and
the edits have had no reviewer. Re-run the review on the fixed tree before the PR.
