---
name: frontend-audit
description: UI products - check built screens against DESIGN.md.
---

# `/frontend-audit` — the UI quality gate (mechanical floor)

> Part of the **product-playbook UI suite** (mastered here; see `/design-system`). `/design-system`
> *decides* the look and writes `DESIGN.md` + the 26 universal laws; **this skill *enforces* the
> mechanically-checkable subset** so a guaranteed floor holds regardless of who built the screen.
> It does **not** judge taste/archetype fit — it checks what a machine can prove.
> `/new-component` builds a new part to `DESIGN.md` and the laws; run this audit after it.
> **This skill's OWN reference files are a DIFFERENT folder** (`commands/frontend-audit/references/checks.md`, beside
> this file), never the plugin-root `references/`.

## Step 0 — Start
**First turn, ONE command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase frontend-audit`** — it
names the installed engine, `DESIGN.md`, the UI folders and the one audit command. Run it as printed; end
with the start's last line, word for word.
**Must NOT:** change `DESIGN.md` or a design decision, judge taste or archetype fit, or call 0 errors an
accessibility pass.

## What it does

Runs `audit.py` (stdlib-only, ASCII output) over UI files and `DESIGN.md`, and prints a scorecard. **Exits non-zero if any ERROR-level law fails** (CI-friendly).

## Which engine runs — the installed one, never a search

```
python "${CLAUDE_PLUGIN_ROOT}/commands/frontend-audit/audit.py" DESIGN.md <ui-dir> [more...]
```

That path is **the installed version**. **Never search the plugin cache for `audit.py`:** it keeps every old
version, and a logged build ran a `1.9.0` engine missing five checks that way. If
the path above still starts with a `$`, this is a copy install: the engine is
`frontend-audit/audit.py` in the installed skills folder (`.claude/skills/` or `.agents/skills/` in the
project, else your tool's user skills folder, `CAPABILITIES.md` §Where the skills are installed); neither there →
stop and say so. **The scorecard's first line names the engine version — quote it in the evidence line.**

**Hooks and CI run a project copy** (`/foundation` commits it as `<tooling>/frontend-audit/audit.py`,
because a clean clone has no plugin). Every run of the installed engine ends with an `engine copy:`
line — the copy matches, is **OLDER** (refresh it: the line names the file to copy), is newer (update
the plugin), was edited in place, or does not exist (hooks and CI do not run the audit). **Repeat that
line to the user;** an older copy means CI passes on checks this run fails.

## What it checks

The mechanical subset of the 26 laws. Law 7 is the headline: it **Computes** WCAG ratio for every foreground/surface
token pair (OKLCH or hex → relative luminance → ratio), in light and dark. *This is the law `/design-system` could only
assert.* Also status colours, tokens, motion, fonts, the type floor and caption tier, focus, responsive, theming, Laws
23–26 and table alignment; anti-pattern, form and security warnings. One row per check: `references/checks.md`
(beside this file), opened only to explain a finding. A project's `.frontend-audit.json` adds token pairs and skips
named WARN rules, never an ERROR (its §Config).

## What it does NOT check (still human/judgment — by design)

Archetype fit, visual hierarchy, layout-matches-archetype (Law 11), "looks generic", whether the
sample was confirmed (Law 16): `/design-system`'s.

**Accessibility (category J) is a floor, never a pass.** Laws 23–26 are the mechanically decidable
subset. **Not checked, and not checkable from source:** keyboard traps and tab order, focus management
across route changes, real screen-reader output, alt-text *quality*, and meaning carried by colour
alone. `audit.py` prints this list on every run, because a milestone that delegates its accessibility
criterion to *"frontend-audit passes with no errors"* is relying on a check that cannot fail on most of
what it appears to certify — and a check like that stops anyone from looking.

## How to use

1. Run the command the start printed (Step 0).
2. Fix every **ERROR** (the floor is non-negotiable); triage **WARN**. **A "use a token" fix is a fix only
   when the token's class exists in the built CSS** — search the build output for it. A utility class with
   no mapping to the token (Tailwind v4 without an `@theme` entry) emits no CSS, and the element ships
   invisible.
   - **On a change to existing files, add `--baseline <git-ref>`** (`audit.py --baseline <ref> DESIGN.md <ui-dir>`):
     only the findings this change ADDS are listed and counted toward the exit code; the findings already
     present at `<ref>` are printed as one count. A bad ref or no git repository fails the run (exit 2),
     never a silent full pass. The whole-file run stays the gate for a new screen and for `/dev-check`.
3. **Layout at phone, tablet and desktop:** `render_check.py` (beside `audit.py`) draws a page at 375 / 768 / 1280 px -
   a built `.html` page or the running app's URL; the start prints the call. Exit 3 = NOT RUN, reported as such, and the
   user is told as-is: "Start your app, then run /frontend-audit again to check phone, tablet and desktop layout." Never
   start a server in the foreground; the start prints the background start/stop pair when the project names its dev command.
4. It is a gate only where it runs without being remembered: `/foundation` wires the project copy into
   the commit hooks and CI (`exit 1` on an ERROR blocks both; a WARN only reports). A project past
   `/foundation` with no copy (the `engine copy:` line says so) → wire it the same way.

