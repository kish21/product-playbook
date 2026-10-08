# Proving the skeleton — Step 3b in full

> Printed whole by `status.py next --phase foundation`, for Step 3b. Each proof
> ends in an `evidence:` line in `#Foundation`. **If any is "should" not "shown", STOP and make it real.**

## Evidence lines

`evidence: <command> → <result> · <artefact> · <date>` (`STATE-MODEL.md` §2f). **Everything a line cites must
exist**: `set foundation filled` refuses a cited file that is not in the project and a cited `file::test_name` the
file does not define (a logged run cited ten tests that were never written). A file planted only to prove a gate goes
red, then removed, is written `planted <what> in <path>`. Cite the command you ran, never the one you meant to run.
**Run each proof through `proof.py -- <command>`** (beside SKILL.md; `devserver.py` and `ci_local.py` log their own
runs): it prints the run's last lines and logs them. `set foundation filled` matches every `evidence:` line to that log
— a command it never saw, or an exit, a count or a quoted message the run did not print, is refused (a logged record
cited a plant that never happened and results a re-run did not give). A browser check is written `browser → ...` and
is judged, never a command's proof.

## Runs end to end

Start it and hit the health path — `devserver.py check --cmd "<start>" --port <port> --health <url>` (one call:
start, answer, stop, port freed; compose `/run` where it is a capability); evidence. Or cite an earlier boot (this
line only), as `/build` does: **re-run a check when any code, config or test file it reads changed after its
evidence was captured; a review fix counts, a doc-only change does not.** Uncommitted and scripted edits count. A
file a check reads is never doc-only for that check, and **when unsure whether anything changed or whether a change is
doc-only, re-run.** **The item-1 boot never qualifies** — Step 2's items 3–8 change the boot path; a CI health check
on the final tree can.

## Usable end to end

**Auth products: actually log in with the seeded account**, and show the seed running **twice** without failing or
duplicating. "The health check passes" is not this. Then point the seed at a non-local database host with
production unset: it refuses.

## Config flows

Read a value back at runtime; evidence.

## Guards

- **Fail-loud/fail-closed:** trigger it with a missing secret and confirm it refuses to boot.
- **Placeholder guard → replay the real failure through the real entrypoint:** never copy `.env.example` to `.env`
  **unedited** over the user's own `.env` - pass it as the env file and start the app the way prod does, in one
  call: `devserver.py refuses --cmd "<the real start command>" ... --env-file .env.example` (exit 0 only when the
  app stopped before answering and named a variable), or the image with `--env-file .env.example`. It must
  **refuse to boot** with a message naming the variable; record that command - `set foundation filled` looks for it. A unit test of the validator alone is not this proof: a logged run's validator passed its test while
  the app booted and answered `/health` on every placeholder. If it starts, the guard is decorative and the product
  ships a public secret.
- **Test-isolation guard → point it at the dev datastore on purpose** and show it refusing to run, naming both
  targets: `proof.py --env TEST_DATABASE_URL=@DATABASE_URL -- <the test command>` takes the value from `.env`, in
  PowerShell and bash alike. The runbook's recipe is the one you ran: a logged PowerShell recipe read
  `$env:DATABASE_URL`, empty in a fresh shell because the value lives in `.env`, and ran the suite green. Then confirm the suite's teardown cannot reach the dev data. This one is verified by *attempting the
  destruction*, because the failure mode is silent until the data is gone.

## Hooks and CI

- **Hooks:** the commit hooks actually run the deterministic checks (lint/format/secret-scan + dependency-vuln/tests)
  and **block on red** → a real commit went through them; show one refusal.
- **The secret scan is real** → `set foundation filled` proves it itself (a fresh fake token committed through the
  installed hooks in a throwaway copy); nothing to plant by hand.
- **UI product: the audit gate is real** → plant a raw hex colour in a component with `proof.py plant --file <a UI
  file> --text "<raw hex>" --also "<the CI audit command>"`: in a throwaway copy of the folder, the hook must refuse the commit and the CI step exit non-zero;
  your folder is never touched. A WARN alone passes.
- **CI:** commit first, then `ci_local.py` (beside SKILL.md) runs the workflow's own `run:` steps on this machine,
  one line each, **in a clean checkout of HEAD** (as a CI runner does; nothing lands in your folder) and refuses a
  step that would get the database in your `.env`; with no git remote this is the proof. Passing counts as **verified locally — never "green on CI"** — and record
  `status.py open --from foundation --what "CI has not run on a remote" --clears "CI is green on the first push"`
  (`set foundation filled` refuses a workflow that never ran without it). A step that needs a service this machine
    `--skip`ped and named under *What I skipped*. **One replay:** a step that fails for a reason of this machine (a
  TLS-inspecting proxy's `UnknownIssuer`, no network) is skipped and UNVERIFIED, never replayed again; after a fix,
  re-run that step alone with `--only`.

## Heavy checks in a fresh conversation

The image build, the image boot and the full CI replay are the longest outputs of the phase, and every later call
re-sends the conversation. **Your tool can start a helper conversation** (CAPABILITIES.md: a sub-agent / task) →
hand it the exact commands (`ci_local.py`, `devserver.py check`, `docker build …`) and take back only the verdict
lines; it starts small instead of at this conversation's size. No such capability → run them here, output to a
scratch file, read the tail.
- **It pays for many calls late in a phase**, not for two or three: a helper starts at its own baseline (~50k
  tokens on one tool), so a short job costs more there than here.
- **It returns evidence, not a summary:** each command it ran, word for word, and its result line — these become
  the `evidence:` lines, and `set foundation filled` checks what they cite. "All tests pass" with no command is
  not a result; ask again or run it here.

## Saving

- **`set foundation filled --commit "<one line>"` is the save** - no git call of your own. It commits through the
  commit hooks (a formatter's rewrite is added and committed once more) and says so: that commit is the "one real
  commit through the hooks".
- **The phase's own files only.** A playbook update (`.agents/`, `.claude/`) that arrived during the phase is its
  own commit, `chore: playbook <version>` — `set --commit` makes it first, never inside the phase's commit, where a
  reviewer reads it as project work.
- **Close settled items BEFORE the save** (`status.py close <n> --how "pre-commit installed; the /foundation commit
  ran through it"`): the save then carries `STATUS.md` with them. An item closed after it changes `STATUS.md` after
  the commit → `status.py save -m "status: …"` at once; `next` warns about an uncommitted `STATUS.md`.
