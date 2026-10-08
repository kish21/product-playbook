# The clarity standard — how a skill is written so any model, in any tool, follows it the same way

**Who this is for:** anyone writing or changing a skill, a rule file or a template. It is not read by a run.

**Why it exists.** A rule only a strong model follows is not a rule. Measured on logged test runs: a rule
that said "affected tests" with no method was broken on the strongest model (7 full-suite runs where the
skill asked for 2); a rule that lived only in a file no step opened was never read; companions with no
trigger were skipped. Each failure was a rule's *shape*, not the model's effort.

**Applies to** every file a run is told to follow: `commands/**`, `PRINCIPLES.md`,
`references/mechanisms*.md`, `references/capabilities.md`, `docs/state-model.md`, `templates/*.md`.
Case files and `LESSONS.md` are history: bound by C4 (their titles are pointer targets), not by C2.

**Enforced by** `tools/clarity.py`, run by `tools/check.py` (checks 49–52), against
`tools/clarity-baseline.json`. The baseline is today's debt, per file. A count above it fails (the change
added a finding); a count below it fails until the baseline is lowered (the clean-up is locked in).
`python tools/clarity.py --report <file>` lists every finding with its line.

## C1 — Rule shape: WHEN + WHAT + CHECK

- **WHEN** — something the run can observe: a step number, a file that exists, a field's value, a
  command's exit code or output.
- **WHAT** — an exact action: a command, a file and heading to write, a question to ask.
- **CHECK** — what someone can see afterwards: a count in the log row, a trace line in the feature doc,
  a file that exists, a command's result.

*Checked by:* the review table for each piece of the rework — one row per rule. No script judges this.

## C2 — No judgement word without a method

Banned unless the **same sentence** carries its method — a `code span` (a command or path), a number, or
a pointer (`§` or `→`) to where the word is defined:

affected · relevant · appropriate · if in doubt · as / if / when needed · where / if possible · enough ·
obvious · trivial · non-trivial · significant · substantial · reasonable · sensible · meaningful ·
consider · carefully · properly · thoroughly · just in case · small · large · big · minor · major ·
a few · several.

**"If unsure" / "when unsure"** is allowed only with its default: *"if unsure → ask"* or *"→ the stricter
option: X"*.

*Checked by:* check 49. *Known limit:* a sentence that carries an unrelated code span passes; the review
reads every sentence of a piece it rewrites.

## C3 — One home per rule

A rule's text lives in one file, under one heading. Everywhere else: `→ <FILE>.md §<heading>`, never a
paraphrase — two copies drift, and a run follows whichever it read last.

*Checked by:* the review (duplicates are listed as findings). A duplicate-sentence check is added once a
piece has been de-duplicated, so it has a clean baseline to hold.

## C4 — Every pointer resolves

Each `<FILE>.md §<name>` names a heading (or its number, `§2a`) or a **bold term** that exists in that
file today; each `case file: <title>` names a case-file heading.

*Checked by:* check 50.

## C5 — Companions open on a trigger, and the opening leaves a trace

"At Step N, when <observable>, open <file>" — never "see also", "if useful", or a file ordered open on
every run that is not a core rule file. The run writes one line naming what it opened and what matched
(the archetype-trace pattern).

*Checked by:* check 42 (rule files) today; companion triggers are checked per skill as its review lands.

## C6 — Script before sentence

For every rule the review asks first: can a script do this, or a check verify it? Each rule is marked
**script**, **check**, or **sentence-only (reason)**. A script-able rule becomes one line: "run X".

*Checked by:* the review table's column.

## C7 — Tool-neutral

A skill names the capability and points to `CAPABILITIES.md`: *"review the diff (→ `CAPABILITIES.md`
§Code review)"*. One tool's command — `/code-review`, `/security-review`, `/run`, `/loop`, `/schedule`,
`/deep-research`, `/compact`, `AskUserQuestion`, "Claude Code" — appears only inside `CAPABILITIES.md`.
`${CLAUDE_PLUGIN_ROOT}` stays: it is the plugin route's path, and a copy install rewrites it (check 41).
When one tool does something better, `CAPABILITIES.md` brings it to the others, or says plainly it can't.

*Checked by:* check 51.

## C8 — Size without loss

Before a skill is cut, a script lists every rule, exit criterion and check in it, each with an ID. After
the cut the same script must find every ID, in the skill or behind a pointer the skill opens at a named
step. The *why* and the history move to case files; repeated rules get one home (C3); script-able rules
become "run X" (C6). Each skill has a **character** budget (the 500-line budget never binds: one skill is
123 lines and 24k characters); budgets only go down, set per skill after its review.

*Checked by:* check 52 (budgets, starting at today's sizes) and check 55 (`tools/rule_inventory.py`): a cut
skill has `tools/rules/<skill>.json` — the commit before the cut, each rule's old and new wording (or the
file it moved to), and each dropped sentence with its reason. Every word of a changed old line must be
accounted for, beyond 3 joining words.

## C9 — The honest close

Every run ends with four plain-words blocks: **What just happened** · **What I skipped or couldn't do**
(each fallback from `CAPABILITIES.md`, each check not run, each round declined — what, why, what it leaves
unchecked) · **Test this yourself** (numbered steps by hand, and what you should see) · **What YOU do
next**. The rule's one home is `MECHANISMS.md` §Plain-language close.

*Checked by:* check 17 (every writing skill's close names that section). Skipped items move into the
status file when it exists (the spine piece of the rework).

## How a change under this standard is proven

1. `python tools/check.py` green; every new check shown RED first by breaking what it guards.
2. The rule inventory before = after (C8), and no exit criterion or check removed.
3. A real run with the same verdicts as before (Claude first), then merged into the public playbook.
