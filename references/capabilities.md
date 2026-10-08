# CAPABILITIES.md — each tool's native way to do what a skill asks

A skill names a capability and points here: *"review the diff (→ `CAPABILITIES.md` §Code review)"*.
Find your tool's column and use that way. Each tool uses its **own strongest** method; the skills are not
cut down to what all four share.

**When your tool's cell says `none` or `UNCONFIRMED`:** use the fallback in the last column, then record it
in the close's *What I skipped or couldn't do* block (→ `MECHANISMS.md` §Plain-language close) — name the
capability, what you did instead, and what the user should check by hand. A fallback nobody hears about
is a silent skip.

Researched 2026-09-24 from each tool's docs; the Codex column and the helper rows from logged /vision runs and
each tool's own self-review (2026-09-30). `UNCONFIRMED` = not in the docs, or the docs disagree; verified on the
first logged test run in that tool, then this file is updated.

## Where the skills are installed

| Claude Code | Cursor | Antigravity | Codex |
|---|---|---|---|
| the plugin, or `.claude/skills/<name>/SKILL.md` | `.agents/skills/<name>/SKILL.md` (also reads `.cursor/skills/`, `.claude/skills/`) | `.agents/skills/<name>/SKILL.md`; user-wide `~/.gemini/config/skills/` | `.agents/skills/<name>/SKILL.md`, started as `$<name>`; user-wide `~/.codex/skills/` (UNCONFIRMED) |

## Paths to the playbook's own files

| Claude Code | Cursor | Antigravity | Codex |
|---|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}/…`, filled in for a plugin | paths relative to `SKILL.md`; no variable | paths relative to `SKILL.md`; no variable | paths relative to the project root; no variable |

**Fallback:** the installer rewrites every `${CLAUDE_PLUGIN_ROOT}/…` path to one that exists, and every
`python <playbook script>` command to the full path of the Python it found (a logged Codex run's PowerShell had no
`python`). A path that still starts with `$` means a copy install that was not rewritten: follow the skill's own
fallback line.

## Project instructions file

| Claude Code | Cursor | Antigravity | Codex |
|---|---|---|---|
| `CLAUDE.md` (reads `AGENTS.md` only when no `CLAUDE.md` exists) | `AGENTS.md`, `.cursor/rules/*.mdc` | `AGENTS.md` or `GEMINI.md` | `AGENTS.md` |

**Fallback:** keep the rules in `AGENTS.md`; `CLAUDE.md` holds one line, `@AGENTS.md`.

## Code review

| Claude Code | Cursor | Antigravity | Codex | Fallback |
|---|---|---|---|---|
| `/code-review` | `/review` (editor 3.7+, billed per use) | no review command: a helper agent (`invoke_subagent` - not offered in a logged 2026-09-29 session, only `browser_subagent`: check your tool list) given `build/references/review-stretch.md` §Helper prompt | `/review` (UNCONFIRMED), or a `spawn_agent` helper the skill explicitly asks for | a subagent given the diff (`git diff <base>...HEAD`) and the ticket's DoD, returning findings rated HIGH / MEDIUM / LOW; a tool with no helper agent at all: the review in this conversation, recorded as `self-review` |

## Security review

| Claude Code | Cursor | Antigravity | Codex | Fallback |
|---|---|---|---|---|
| `/security-review` — reads COMMITTED changes only, so commit first; run it inside a subagent so its report cannot end the run | `/review-security` (editor only) | no review command: the same helper agent (UNCONFIRMED), given the committed diff and `PRINCIPLES.md` §Production safeguards | a `spawn_agent` helper given the committed diff (UNCONFIRMED) | a subagent given the committed diff and `PRINCIPLES.md` §Production safeguards, returning findings rated HIGH / MEDIUM / LOW; with no helper agent: `self-review`, as above |

**A review is recorded by the route that ran** — `helper agent` · `self-review` · `by hand` — never by a command
your tool does not have: on Cursor, Antigravity and Codex `status.py ticket` refuses `/code-review` or `/security-review`
in `--review`, and prints the sentence that tells the user which review ran. A logged Gemini build reviewed its own
diff in its own conversation, recorded "/code-review → R1 clean", and missed two bugs a separate review found.

## Run the app and check the live path

| Claude Code | Cursor | Antigravity | Codex | Fallback |
|---|---|---|---|---|
| `/run`, plus a browser MCP server (Playwright or Chrome) for pages | built-in Browser tool, or the Browser subagent | the Browser subagent (`/browser`); saves screenshots and recordings | none built in (UNCONFIRMED) | start the app with the project's run command and drive the path with `curl` or the test client; for a page with no browser, record it as not checked |

## Subagents and parallel work

| Claude Code | Cursor | Antigravity | Codex |
|---|---|---|---|
| the Agent tool, `run_in_background`; agents in `.claude/agents/` (the plugin's own `agents/`) | Task sub-agents, `run_in_background`; agents in `.cursor/agents/` (reads `.claude/agents/`) | background subagents in `.agents/agents/`; the Agent Manager | `spawn_agent` (more than one at a time) - its own rules forbid spawning unless the user or the skill **explicitly** asks, so a skill that wants one says so in command form; no agent files: give it the brief's path |

All four run a helper in the background while the main conversation keeps going: `/vision` starts its research
helper this way (brief: the playbook's `agents/vision-research.md`, which the installer also puts where each tool
looks for its agents). On the same task, plain Claude's helper ran 18 searches and 7 page reads in its own context
while every playbook run searched 3-6 times in the main conversation (2026-09-30).

**Fallback:** do the work in the main conversation, one item after another - independent searches or
reads in ONE message - and say so in the close.

## Ask the user a question with options

| Claude Code | Cursor | Antigravity | Codex |
|---|---|---|---|
| the AskUserQuestion tool | the ask-question tool (UNCONFIRMED outside Plan mode) | `none` (UNCONFIRMED) | `none` (UNCONFIRMED) |

**Fallback:** write the question and its options as a numbered list, mark the recommended one, and stop
until the user answers. Never pick an option for them.

## Recurring checks

| Claude Code | Cursor | Antigravity | Codex |
|---|---|---|---|
| `/loop` (this machine) or `/schedule` (cloud) | Automations (cloud only) | `/schedule` | `none` (UNCONFIRMED) |

**Fallback:** write the check as a dated line in the user's *What you do next* list.

## Web search

| Claude Code | Cursor | Antigravity | Codex |
|---|---|---|---|
| the web search tool (deferred in some sessions: load it in the first turn) | the web search tool | the web search tool | the web search tool, up to 4 queries per call |

**Fallback:** name the question you could not search, and ask the user for the source.

## Time and cost of a run

| Claude Code | Cursor | Antigravity | Codex |
|---|---|---|---|
| `tools/session_cost.py` reads the session log: time, tokens, dollars | headless `agent -p --output-format json`: time only; tokens on the usage dashboard | `session_cost.py` reads the conversation file: tokens, no time, no dollars; headless `agy -p --output-format json`: time and tokens | the session file in `~/.codex/sessions/`: tokens and time (read by hand; no script yet) |

**Fallback:** report the figures your tool gives and write `not measured` for the rest.
