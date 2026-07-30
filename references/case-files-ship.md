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
