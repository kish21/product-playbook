# Contributing to product-playbook

1. Add or modify a command in `commands/<name>.md` — or directory-form `commands/<name>/SKILL.md` (+ `references/`) for skills that carry references. Keep them concise and single-purpose.
2. Register it in **all three**: `VISION.md`, `manifest.json`, and `evals/evals.json` (the CI gate checks they stay in sync). Each skill needs **at least two** eval cases, each with a unique `id` plus a non-empty `skill`, `prompt` and `expected_output`. CI checks that shape — it does **not** run the cases.
3. If a rule earned its place from a real incident, keep the skill file to the **bold one-line rule** and put the war story in `references/case-files-<skill>.md`, pointed to as `(case file: <heading>)`. **Rules go in `PRINCIPLES.md`; mechanisms go in `references/mechanisms.md`; lessons go in `references/lessons.md`** — CI fails any of the three over ~15KB, and fails a `§` pointer that names a heading none of them has.
4. Run `python tools/check.py` (the CI consistency gate), commit, and open a PR (master requires the `check` to pass).
5. Run `/drift-check` on this repo to verify nothing drifted.

## No project is named

The playbook ships to people building every kind of product, so no real project — a test project, the
maintainer's own tools, a user's repo — is named anywhere in this repo: skills, references, case files, evals,
templates, docs, `tools/`, the CHANGELOG. Write evidence as *"a logged test run"* and keep its dates, counts and
failures; make every example in a rule an invented one. Check 34 in `tools/check.py` enforces it. It reads the
names from `PLAYBOOK_PRIVATE_NAMES` (comma-separated, one entry per spelling) so the list never enters the repo:
CI takes it from the repository secret of that name, and a local run skips the check unless you set it.

## §Lesson format — rule up front, story in the case file

Skills are loaded verbatim into every session that runs them, so their size is a per-session cost
and an attention cost: a checklist of sharp one-liners gets followed; a wall of war stories gets
skimmed. Therefore every lesson is written in two parts:

- **In the skill file:** the **bold one-line rule** plus at most one sentence of mechanism — enough
  to act on, nothing more.
- **In `references/case-files-<skill>.md`:** the full war story, verbatim, under its own heading,
  pointed to from the rule as `(case file: <heading>)`. Opened on demand, never auto-loaded.
- **A rule that applies only SOMETIMES moves into the skill's OWN `commands/<skill>/references/`, never into a case file.** A case file is repo-only evidence — `install.sh` does not ship it — so a rule parked there is gone for every installed user, while a directory-form skill's `references/` installs beside `SKILL.md` and is size-exempt precisely because it is opened on demand. (case file: The prune that would have deleted the rules)

Gardening cadence: roughly every 10 merged lessons, run a prune
pass — condense, merge overlapping rules, retire ones that stopped earning their place. A lesson
that can't be stated as one bold line isn't distilled enough to be a rule yet.
