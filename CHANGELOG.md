# Changelog

All notable changes to product-playbook are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project uses [Semantic Versioning](https://semver.org/).

## [1.16.0] - 2026-09-08

### Added - **decisions the playbook was making silently, and a test class it never had**
Three findings from the 2026-09-08 Phase 2/3 run, each one a thing that was *decided* or *missed* without anyone choosing it.
- **`/architect` now decides data custody, runtime target and identity custody.** It chose a local Docker Postgres and scaffolded a compose file without ever asking **where the data should live or where the product would run** - grep-verified: `deploy`, `hosting`, `managed`, `serverless` appeared **zero times** across `/architect`, `/plan` and `/foundation`. To be precise about the defect: the confirmation gate already existed (*"give one recommendation, get a yes/no"*) - **hosting and custody were simply never on Step 2's agenda**, so the recommendation the user approved could not cover them. That is a scope hole in the decision list, and it is fixed as one. The runtime target decides whether a compose file is even the right artifact and is expensive to reverse once later phases build on it, so **`/structure` now reads it before writing any infra file and will not emit a compose file for a target that does not use one.** PRINCIPLES' *defer paid infra* bias toward local is now a **stated default the user can decline**, and a choice made without user input is recorded as *"default taken, not user-chosen"*.
- **`/foundation`'s bar becomes USABLE end-to-end, not merely running.** Immediately after the test suite wiped the dev database (#86), the app ran perfectly and **nobody could log in**; recovery took a hand-seeded account. A health path proves the process booted, not that a human can get in. For products with auth the guard is now **logging in**, via a seed that is **idempotent** (it is the recovery path after a reset or a test teardown, so twice must work), **refuses to run against production**, and **prints its obviously-fake dev credentials once** - recorded in `#Foundation` and named at handoff, so the next session does not go looking. A wiped database is recoverable with one documented command. Seed ownership follows the same split as the dependency manifest: `/structure` names the target, `/foundation` makes it real.
- **`/test` gains a real-user-environment class.** A password-manager extension injected DOM nodes into the login form before hydration and threw for real users, while every automated test stayed green - the suite ran headless, clean profile, zero extensions. The existing classes all describe *what the code does*; **none described the environment it runs in**, and "the path the product actually runs" had quietly come to mean "the path our runner runs". The new class covers third-party DOM injection, locale/timezone, reduced motion and forced colours and zoom, and degraded network, with at least one executable check that first paint survives injected DOM on an auth surface. **The originally proposed fix was rejected:** blanket `suppressHydrationWarning` on every input would silence genuine mismatches (clock/random values, locale drift, branch divergence) in a toolkit whose principles are *fail-loud* and *no swallowed errors*, and it is framework-specific - the #78 bug. Suppression is **scoped and justified** instead, and the wording names the capability, not a framework.

## [1.15.0] - 2026-09-08

### Added - **three shared rules the skills were each half-inventing**
`PRINCIPLES.md` exists so a rule lives in one place and cannot drift. These three were being re-decided per run, per skill, or not at all.
- **§Step 3b - closing the loop.** Three omissions repeated by *every* phase, each leaving the user bookkeeping the skill could do itself: the `Stage:` header went stale (and `/playbook` orients from it, so a stale header misroutes the next phase); numbers introduced by a later phase were never reconciled against `#Vision`'s north star, so a plan dated past the target date wrote cleanly; and each skill made a substantial doc change then left the user to invent the commit message, discarding the run's own summary - the best possible source for it. All three now happen at every phase's Step 3b, defined once and referenced by all 15.
- **§Re-run semantics.** Only `/validate` said what a second run does (append a dated entry, never overwrite). `/vision`, `/scope`, `/plan`, `/architect` and `/contracts` said nothing - and their write step **rewrites the section in place**, so a re-run silently destroyed earlier ADRs, rejected alternatives and the reasoning behind them, discoverable only from `git diff` if you thought to look. Re-running a phase is not an edge case (a pivot, a changed constraint, a redo), and what got lost was the most expensive thing to reconstruct: *why the other option was rejected*. A run over a non-empty section now shows what would change and **asks**; a reversed decision is **dated, not erased**; log-shaped sections keep appending, and `/validate`'s rule becomes the general case instead of a local exception. **That the most recently written skill invented this rule locally was the signal it had no shared home.**
- **§Seam - who owns the dependency manifest.** `/structure` required one as root scaffolding while `/foundation` existed to install and pin dependencies, and nothing said where the line was - so the outcome depended on how thorough the agent felt. On the test run `/structure` wrote 23 pinned dependencies and 14 scripts pointing at config files that did not exist yet: `make check` failed at the end of a phase that reported green. **`/structure` owns the manifest's existence and shape; `/foundation` owns its contents and provability**, stated in the same words in both skills - and `/structure` may no longer leave a script that cannot run at its own gate. A phase reporting green while `make check` fails has reported a lie.

## [1.14.0] - 2026-09-08

### Added - **Phase 1 gates that produce a steerable product, not a slogan**
Five findings from the 2026-09-07 Phase 1 test run, shipped together because they are one theme: **Phase 1 was collecting answers without checking they were usable by the phases downstream.**
- **`/vision` - a north star needs five parts, not a direction.** The gate asked only for "a measurable number", which produced *"more people tracking subscriptions"*: no target, no date, no leading indicator, no guardrail against gaming it. It now requires a **target + date**, **2-3 input metrics** (a north star moves too slowly to steer by), **1 guardrail** (what must not get worse), and an **instrumentation line** - and *"nothing records this yet"* is a finding, not a detail for later. **`/eval` now takes its measurement baseline from that target and reports the guardrail alongside**: a north star that improved while the guardrail got worse is not a pass.
- **`/validate` - the skip override is pressure-tested against `#Vision`, and no longer deletes the scaffold.** On the test run a user skipped validation with *"personal/project use"* against a Vision recording a public customer, a north star and a business model - a reason that does not defer validation, it contradicts the Vision. It was accepted silently, and writing it **blanked the experiment fields** so the section no longer showed what had been skipped. Now the reason is compared against the recorded customer, business model and north star first; a contradiction is named and routed back to `/vision` (still overridable, but informed), a merely deferring reason records in one step, and either way the fields stay, marked `- not run (override <date>)`.
- **`/scope` - a table-stakes gate.** The Deferred and Non-goals lists only ever covered features somebody *thought of*. The systematic gap is the boring items nobody proposes and everybody expects - password reset, email verification, account deletion + data export, empty/loading/error states, privacy + terms, accessibility, a way to report a problem. They do not get deferred, they get forgotten, and they resurface at ship time as "we can't launch without this": the exact scope shock the skill exists to prevent. Every item must now be sorted **in-scope now / Deferred + trigger / N-A + reason**; the list adapts to the product kind, but **an unsorted item fails the gate**. `/drift-check` reports a table-stakes item marked in-scope and never built.
- **`/plan` - a four-risks row per milestone.** The plan sequenced core-first with a testable exit criterion each, which addresses **feasibility only**; the four product risks are value, usability, feasibility and viability, so the plan had three blind spots. Every milestone now names which risks it retires and how you will know, an already-retired risk **cites its evidence** rather than repeating the work, and a **usability checkpoint before anything goes public** is a milestone exit criterion - usability being the risk discovered after launch, when it is most expensive to fix.
- **`/playbook` - a non-canonical phase order is now visible.** Orienting by "first unfilled section" said nothing when the chain was walked out of order: a project with `#Architecture` filled and `#Scope` empty was pointed at Scope with no hint that stack decisions already existed which may not survive it. The inversion is now named, its risk stated, and the earlier phase offered - **with an override**, because standalone use is first-class. An in-order spine produces no extra output, and a recorded override is not re-asked.
- `templates/PRODUCT.md` carries every new scaffold line (north-star parts, table stakes, four-risks row, usability checkpoint, the playbook-order line). Five eval cases (40 total).

## [1.13.0] - 2026-09-08

### Added - **Law 7b: status colours are checked against both WCAG bars**
Found on the `/design-system` test run. The audit reported the sample dashboard **12 pass, 1 warn, 0 error** - and missed a colour that fails the bar the page itself cites. `--warning-dot` measures **2.27:1** against `--card` in light mode, under the 3:1 minimum for a meaningful graphic (WCAG 1.4.11), while the page's own token comment claimed *"the DOT stays brighter (3:1 graphical is enough)"*. The design asserted a bar it did not meet and the gate had no opinion. The cause: `PAIRS` checked shadcn foreground/surface pairs and a few aliases, and **never checked semantic status colours at all** - neither as text (4.5:1) nor as graphics (3:1). A status colour is the single most common place a palette drifts below AA: the shade is picked for *brightness* so the dot reads as "amber", then reused as a label.
- **Both bars, chosen by the token's role.** Every status token is checked against `--card`/`--background`/`--popover`/`--muted` in **both modes**: **4.5:1** as text, or **3:1** where the name marks it a graphic (`-dot`, `-indicator`, `-fill`, `-bar`, `-chart`). One value can now pass as a dot and fail as a label - the single-bar output could not express that.
- **Miss-by-design beats silence:** below its bar is an ERROR naming the ratio, the bar and the fix. A token that is genuinely never text opts out **explicitly** (`/* decorative */` on its declaration) - never inferred.
- `references/universal-laws.md` Law 7 now states how the gate tells the bars apart, so the law and its enforcement agree.
- Verified by replaying the sample: the `--warning-dot` failure is reported at **2.27:1**, matching the by-hand measurement exactly, while **all 12 originally-passing pairs still pass** (45 pass / 1 warn / 3 error). A project declaring no status tokens gains no findings.

## [1.12.0] - 2026-09-08

### Added - **Law 14b: `/frontend-audit` flags token references nothing defines**
Found while verifying #84, which claimed a component written to a private token vocabulary "can fail the audit `/build` gates on". It does not - and the truth is worse. The same component written twice, shadcn tokens vs private `--color-*` ones, both audited **0 errors**; the private one still passed when `DESIGN.md` was handed to the audit **in the same run**. Every one of its nine tokens was undefined. CSS treats `color: var(--color-success)` with no such token as invalid at computed-value time and **drops the declaration**, so the value silently inherits: the component looks almost right, the colour never arrives, and nothing reports it - not the build, not the audit, not the console. v1.10.1 fixed the cause; this is the net.
- **Cross-file by construction** - `audit.py DESIGN.md frontend/` collects definitions across the whole audited set before resolving references, so a component is checked against the design system it is audited with.
- **ERROR** when the set defines tokens (the reference is provably orphaned), naming each one. **WARN "unverified"** when the set defines none at all - the same anti-false-pass convention Law 7 already uses, so auditing a component without its stylesheet says so instead of quietly passing. `var(--x, fallback)` is exempt: a declared fallback is a deliberate choice.
- **`/new-component`'s verification is now this check** rather than the hand-rolled `grep` v1.10.1 shipped, and it says to pass `DESIGN.md` alongside the component - auditing the component alone cannot verify tokens and now admits it.
- Verified on the real 725-line `/design-system` sample: **12 pass · 1 warn · 0 error**, unchanged - no false positives on a page whose tokens are all defined.

## [1.11.0] - 2026-09-08

### Fixed - **the playbook permitted an integration suite to wipe the developer's database** (it did)
The severest defect found so far, and it destroyed real data on the 2026-09-08 Phase 3 test run: `test:integration` ran against the same datastore URL the dev server used, its teardown hook truncated the tables, and the developer was left stranded at `/login` with no accounts. **This was not a project mistake - the playbook asked for the conditions that caused it.** `/test` required integration tests "across real contracts/boundaries (not all mocked)" and required them deterministic and CI-gating; **nothing anywhere required the test target to be a different datastore.** `/foundation` never provisioned one and `/structure` never scaffolded the variable, so a suite satisfying every one of `/test`'s exit criteria was permitted to point at the developer's database and truncate it. A toolkit that mandates real-boundary integration tests and stays silent on test-data isolation ships a data-destroying default.
- **`PRINCIPLES.md` §Production safeguards** states it once, so every phase inherits it: tests run against an **isolated, disposable datastore** (a separate target, or per-test transaction rollback) - sharing the dev one is not an option - and the isolation is enforced by a **fail-closed bootstrap**, not a convention.
- **`/foundation` provisions it as a deliverable:** its own variable, created and torn down by the task runner, plus the **refuse-to-run guard** written *before any test exists* - a suite written first is one that has already run once against whatever was configured. Step 3b verifies it **by attempting the destruction**: point the bootstrap at the dev target and show it refusing, naming both. The failure mode is silent until the data is gone.
- **The test runner loads config the way the app does** (same loader, same precedence) - a runner with its own config path is dead config on the test side, and it is how a suite ends up aimed at the wrong datastore.
- **`/structure`** declares the test-datastore variable in `.env.example`, distinct from the development one; **`/test`** gains the exit criterion - a suite that cannot name its isolated target does not pass the gate - and proves the target by reading back what the bootstrap resolved rather than trusting the variable's name.
- Wording names no specific database, test runner or package manager (the tool-vs-capability rule from v1.10.0).

## [1.10.1] - 2026-09-08

### Fixed - **`/new-component` spoke a token vocabulary no other skill knew**
The three UI skills disagreed about what a design token is called. `/design-system` emits **shadcn-compatible OKLCH tokens** into `DESIGN.md` (`--primary`, `--muted-foreground`, `--destructive`); `/new-component` hardcoded its own (`--color-success`, `--color-surface-hover`, `--transition`, and the font constants `FONT`/`DISPLAY`/`MONO`) and **never read `DESIGN.md` at all**. It was also the only skill in `commands/` with no contract block, no `PRINCIPLES.md` line and no spine read - 27 lines of styling rules - so nothing had ever flagged it.
- **Step 0 resolves the vocabulary before a line is written:** `DESIGN.md` §Tokens wins verbatim; with no `DESIGN.md` it says so, recommends `/design-system`, and falls back to the **shadcn defaults the ecosystem shares** - never to a private vocabulary. Concrete token names in the skill are now marked as *examples*; the nine styling rules keep their intent and stop dictating the names.
- **Contract block + `PRINCIPLES.md` line added**, and `tools/check.py` now enforces both on the skills a build step depends on (`design-system`, `new-component`) via a new `CONTRACTED` set - phases keep the full template, `frontend-audit` stays exempt because its contract is `audit.py`'s exit code, not prose. Recorded, not left as a note.

### Changed - the verification, because the premise turned out to be wrong
The ticket said a private-vocabulary component "can fail the audit `/build` gates on". **Verified: it does not.** The same component written twice - shadcn tokens vs private tokens - both audit **0 errors**, and the private one still passes when `DESIGN.md` is handed to the audit in the same run. CSS drops a `var()` referencing an undefined token *silently*, so the colour never arrives and nothing reports it. The skill now says that plainly and verifies with a `grep` of every referenced `var(--…)` against `DESIGN.md` - the check that actually catches it - with the audit as the second, explicitly insufficient, gate. **Filed #92** for the real net: `/frontend-audit` should flag orphaned token references.

## [1.10.0] - 2026-09-08

### Added - **Step 3c, the contradiction check** (every phase that writes)
Step 0 checks the *previous* phase's gate; Step 3b checks *this* phase's own criteria. Neither ever asked the question that matters most: **does what I just produced contradict a decision already recorded?** A phase could satisfy every box on its own list and still silently overrule an ADR made one phase earlier - doc<->code drift created *inside* the playbook, left for `/drift-check` to find later, if anyone ran it.
- **`PRINCIPLES.md` §Step 3c** defines it once: compare this phase's output against the decisions already recorded (ADRs, **tool choices**, stack, scope items and non-goals, budgets, contracts, `DESIGN.md` tokens); on a conflict **name both sides**, ask which wins, and **update the loser** - fix the artefact, or add a dated `superseded by` line to the earlier section. A contradiction is never left standing in two places; a reversal is fine, an *unrecorded* reversal is the bug. Adding detail to an earlier decision is explicitly **not** a contradiction, so the check doesn't cry wolf.
- **All 15 phase skills** carry a `## Step 3c` naming their own comparison set - `/plan` against `#Scope`'s non-goals, `/build` against `#Contracts` + adapters + `DESIGN.md`, `/test` against the datastore `#Foundation` recorded, `/learn` against the non-goals a "what we learned" proposal tends to reopen.
- **`tools/check.py`** enforces the token in the phase template (verified by removing it: the check fails on `plan missing 'Step 3c'`). `/drift-check` now treats a conflict carrying no `superseded by` line as evidence a phase skipped its Step 3c.

### Fixed - **`/structure` hardcoded a tool where it meant a capability**
A no-hardcoding toolkit hardcoding a tool name, in the most visible place it has. `/structure`'s exit criteria demanded `.pre-commit-config.yaml` **by name** for every project regardless of stack. On a real run `/architect` had recorded **lefthook**; `/structure` scaffolded the Python framework into a Node/pnpm repo anyway, wired `make hooks` to `pre-commit install`, and listed it in `STRUCTURE.md` - so the recorded ADR trail described a tool the repo did not use, and a Node contributor needed Python tooling to commit. Neither skill noticed.
- Root scaffolding is now named as a **capability** filled by the tool `#Architecture` chose: secret-scan config · commit-hook runner · task runner · dependency manifest. The playbook no longer dictates filenames.
- **The actual hole is fixed in Step 0:** `/structure` reads `#Architecture` for **tool choices**, not just the stack. With no tool recorded it recommends one that fits the *detected* stack, says why, and records it back - never defaulting to the Python one on a Node repo.
- **`/architect` Step 2 gains a Dev tooling decision** (hook runner · secret scanner · task runner · formatter/linter · dependency manifest), and `templates/PRODUCT.md#Architecture` a line to record it - an unnamed slot is one `/structure` fills from habit. Swept the same tool-vs-capability confusion out of `/foundation`, `/build`, the PR template and the README.

### Fixed - **`.env.example` placeholders that pass a length check and boot the app**
Found on the same run, and the more dangerous of the two. `/structure` mandates a committed `.env.example` but never said its placeholders must be **rejected at boot**. The one it produced - `BETTER_AUTH_SECRET=replace-me-with-32-plus-random-characters-abcd` - is 48 characters, so `z.string().min(32)` **passes**; `make setup` copies the example to `.env`; the app starts happily on a session-signing key that is public in git, and anyone who can read the repo can forge a session. Length checks feel like validation and are not.
- **`PRINCIPLES.md` §Production safeguards** carries the rule once, so `/build` and `/ship` inherit it: placeholders are written in an unmistakable form (`CHANGE_ME__<VAR>__CHANGE_ME`) and **rejected by name**, never by length or shape.
- **`/structure`** writes only that form, one comment per placeholder on how to generate the real value; **`/foundation`**'s startup guard holds them as a known-bad list, refuses to boot naming the variable and the command to generate a real one, and has **no override under production**. Step 3b proves it by replaying the failure - copy `.env.example` to `.env` unedited, show the app refusing to start. A guard that is claimed rather than shown is decorative.
- **`/ship`**'s security checklist gains the line: a release that boots on a committed secret is a live incident, not a finding.

Closes #78, #79, #81. Three eval cases added (31 total).

## [1.9.0] - 2026-09-08

### Added - `install.sh --only <skills>` (take just the skills you want)
VISION.md promises "sequential but standalone": any skill runs on its own. That was true at runtime but not at install time - the copy installer shipped all 20 skills or nothing, so someone who already has a process and just wants `/build` and `/ship` had to take the whole journey. The plugin route stays all-or-nothing by design; the copy route no longer is.
- **`install.sh --only build,ship`** - installs exactly the named skills, flat (`commands/<name>.md`) or directory-form (`commands/<name>/` with its `references/`), **always** plus the companions every skill reads (`PRINCIPLES.md`, `VISION.md`, `templates/PRODUCT.md`). Combines with `--project`. Names normalise, so `/build`, `build` and `build.md` all mean the same skill. An unknown name **installs nothing** and prints the valid ones - a partial install is worse than none.
- **`--list`** prints the installable skill names; **`--help`** documents every flag; an unrecognised flag exits non-zero instead of being ignored. Flags now parse in any order (`--project` was previously only honoured as the first argument).
- A subset install closes with the **composition note**: `/build` -> `/code-review`, `/ship` -> `/security-review`, `/drift-check` -> `/doc-audit` live outside this repo; without them the composing skill runs on, minus that step.
- **README Installation** is now three routes - plugin (everything, auto-update) · copy (everything, re-run to update) · copy `--only` (the skills you pick) - with a *Best for* row so a newcomer takes the guided journey and an experienced user takes the steps they lack. Also fixes a stale version in the "Did it work?" check.

## [1.8.0] - 2026-09-07

### Added - `/validate` (Phase 1, between `/vision` and `/scope`)
`/vision` made you *name* the riskiest assumption; nothing in the chain ever *tested* it. A product could pass every later gate and still be the wrong product. `/validate` is the cheapest anti-waste lever the playbook was missing: days of evidence before months of code.
- **`commands/validate.md`** - reads the riskiest assumption, north-star metric and JTBD from `#Vision`; restates the assumption as a **falsifiable behaviour**; recommends ONE experiment from a five-rung ladder (desk check · problem interviews · landing page / fake door · concierge · pre-sale), the lowest rung that can falsify *this* assumption; makes the user write a **numeric pass/fail threshold and a time box BEFORE the result**; records the **measured** result and a **proceed / pivot / kill** verdict. A pivot re-runs `/validate` on the new assumption; a kill is the playbook working. Skipping is allowed only as an **explicit dated override** line, never a silent pass. Long-running experiments compose `/loop` / `/schedule` to re-measure.
- **`templates/PRODUCT.md`** gains a `## Validation` section (append a dated entry per run). `VISION.md` row, `manifest.json` entry, two eval cases.
- **`/vision`** hands off to `/validate`; **`/playbook`** orients through it (an override counts as filled but is surfaced every time); **`/scope` Step 0** warns when `#Validation` is empty or an override, and carries the untested assumption into the scoping discussion (override allowed - standalone use still works).
- `tools/check.py` enforces the phase template on `validate` (20 skills).

## [1.7.0] - 2026-09-06

### Added - lane mode (the Lanekeeper seam)
[Lanekeeper](https://github.com/kish21/parallel-agents) runs several coding agents on one repo and gates every PR to the lane its ticket declares. It reads product-playbook's tickets, so the two already talked; what was missing was the playbook knowing it was being read. **Lane mode** is detected from a `.lanekeeper/` policy, a root `lanes.yaml`, or a `.lane` file in the worktree. Outside lane mode nothing changes.
- **`PRINCIPLES.md` §Lane mode** - the four rules, defined once and referenced by the skills: the ticket's file list IS the lane; a lane is a feature slice, never a technology layer; the spine (`PRODUCT.md`, `CHANGELOG.md`, `STRUCTURE.md`) is a shared file with ONE writer; the PR carries its `lane:` label.
- **`/tickets`** - a **Lane** field on the ticket template (Lanekeeper reads the heading); Target Files must name *everything the build writes* (feature doc + tests) and never a spine file; in lane mode the default strategy is vertical and a horizontal choice carries a recorded reason; two tickets naming one file are a contract dependency or a flagged collision. **Template ownership settled:** the playbook owns the issue template, Lanekeeper owns the PR template + gate workflow - `/tickets` no longer writes `PULL_REQUEST_TEMPLATE.md` when Lanekeeper is present, and neither tool overwrites the other's file.
- **`/build`** - reads `.lane` first; `ALLOW`/`DENY` is the file-level scope gate (a needed file outside it is creep, flagged not touched); **does not write `PRODUCT.md`** from inside a lane - the Build-log row goes in a `## Build log row` section of the feature doc, which is inside the lane.
- **`/dev-check`** - the spine's one writer: lifts every feature-doc Build-log row into `#Build log` on the base branch, checks `lanes.yaml` against `#Scope` (a lane with no in-scope item is creep with a worktree attached), and runs the cross-lane seams - a green lane is not a green product.
- **`/ship`** - runs `lanekeeper check` before opening the PR, labels it `lane: <name>`, and writes the Ship log + CHANGELOG on the base branch after merge, never from the worktree.

### Fixed
- **PR template was npm-hardcoded** (`npm test`, `npm run build`) in a repo whose first principle is no hardcoding. It now asks for the project's own gate command from the Makefile / STRUCTURE.md, adds the no-hardcoding and feature-doc lines, and says why it is not used in lane mode.

### Docs
- `docs/lane-mode.md` - the design note for this change (contract, interaction map, what is and is not verified).

## [1.6.1] - 2026-09-06

### Fixed - installing as a Claude Code plugin
- **Plugin Mode never worked.** `.claude-plugin/marketplace.json` declared `"source": "git"`, a source type the marketplace schema does not have; `claude plugin validate` failed with `plugins.0.source: Invalid input`, so `/plugin install product-playbook@product-playbook` could not succeed. The source is now the documented relative-path form (`"./"` : the marketplace and the plugin are the same repo) and the marketplace carries the `description` the validator asks for. Passes `claude plugin validate --strict`.
- **A plugin install silently dropped two skills.** Claude Code loads `SKILL.md` skills from `skills/`, not `commands/`, so the directory-form `design-system` and `frontend-audit` were missing: a live install reported **17** skills. `plugin.json` now declares `"skills": ["./commands/"]`; a live install reports all **19**.
- **Version surfaces disagreed** (README badge 1.2.1 · `plugin.json` 1.2.3 · `manifest.json` 1.6.0). On the plugin route `plugin.json`'s version is what pins updates, so a stale value there means users never receive one. All aligned, and `tools/check.py` check 5 enforces it against the newest CHANGELOG release from now on.

### Changed - README
- **Installation rewritten as a choice between two verified routes.** Plugin (namespaced `/product-playbook:vision`, auto-update once enabled) vs. copy (bare `/vision`, re-run to update) : with the `curl` one-liner that `install.sh` always supported but the README never showed, the scope choices, the *enable auto-update* step third-party marketplaces need, a "did it work?" check, update and uninstall steps for each route, and the Windows Git Bash note.

### Added - `tools/check.py`
- **Check 6:** every directory-form skill's folder must be listed under `skills` in `plugin.json`, so a plugin install can never silently drop skills again.

## [1.6.0] - 2026-09-01

### Changed - `/tickets`
- **Two slice strategies, chosen per milestone.** A milestone is no longer one monolithic card. It is decomposed either **vertically** - 2-4 thin end-to-end slices, each crossing layers on purpose and each demoable on merge - or **horizontally** - one ticket per architectural layer (storage/provider, domain service, UI component, cross-layer verification). `/tickets` reads `STRUCTURE.md` and the milestone, **recommends one with a reason, and stops for confirmation**; `/tickets "vertical"` or `/tickets "horizontal"` skips the ask. The chosen strategy is recorded on every ticket.
- **Every ticket is a real ticket.** Whichever strategy is used, each one carries a milestone-scoped ID (`[M2-SLICE-01]` / `[M2-TICK-01]`), exact target file paths, typed inputs/outputs, a `Depends on` contract list and a security DoD - assignable to a different developer and mergeable as an isolated PR. Previously a milestone produced one card listing all five layers as checkboxes.
- **Vertical guardrail:** a slice with no observable outcome is rejected as "a layer wearing a slice id" and re-sliced, or the milestone moves to horizontal. Slice 1 must be a walking skeleton that runs end to end on its own.
- **Layer 4 narrowed to cross-layer work only** (integration across the real seam, adversarial/security). Per-layer unit tests stay in each layer ticket's DoD - previously the same work was counted twice, and a standalone QA ticket is the part of the layered model most teams have moved away from.
- **Layers are emitted only if the project has them.** Read from `STRUCTURE.md`, so a backend/API/CLI product gets 3 tickets and no orphan UI card; full-stack gets 4.
- **Dual-mode execution.** Bare `/tickets` (or a planning phrase) runs batch milestone decomposition. `/tickets "<description>"` logs ONE ad-hoc bug / edge case / tech debt item against the file that owns it, classified and labelled, with a DoD requiring a regression test - without reading, regenerating or renumbering the backlog.
- **Canonical structure + enforcement.** `/tickets` now follows the standard phase-skill shape (principles reference, `Step 3b` principle-gate, `Step 4 - Handoff`) and was added to the `TEMPLATE` set in `tools/check.py`, so CI enforces that shape from now on instead of exempting it.

### Fixed
- **Template provisioning was broken.** The skill copied from `resources/`, a directory that does not exist; the bundled templates live in `templates/`. Auto-provisioning would have failed on every run.
- **Ticket IDs could collide across milestones.** `[TICK-01]` repeated per milestone, so the dedup guard would skip real tickets as duplicates on re-run. IDs are now milestone-scoped and derived from `docs/issues/` and the fetched issue list together.
- **`manifest.json` said `1.4.0` while the changelog declared `1.5.0`** (v1.5.0 never bumped it).

### Changed - templates
- `templates/feature_ticket_template.md` rewritten for a single scope-bounded ticket (one concern, one PR) with slice-strategy, layer, contract, dependency, **Demo** and mergeable-alone fields, replacing the old all-layers-in-one-card form.

## [1.5.0] - 2026-09-01

### Added
- **/tickets Skill (Phase 2, Step 4b):** Bridges /contracts and /build. Automatically translates milestones from PRODUCT.md#Plan into structured GitHub Issue Tickets with exact target files, modules, tasks, and security DoD.
- **GitHub Templates Auto-Provisioning:** Bundles and automatically deploys .github/ISSUE_TEMPLATE/feature_ticket.md and .github/PULL_REQUEST_TEMPLATE.md.
- **Pre-Flight Remote & Deduplication Guard:** Verifies remote repository status before publishing, never blindly creates repos, and ignores existing issues to prevent duplicates.

## [1.4.0] — 2026-07-28

The first pruning release. `/build` had grown to 41KB of load-bearing lessons — every byte
re-read at the start of every build session, and the rules increasingly buried in their own
war stories.

### Changed — `/build`
- **Distilled to rule-first form**: every lesson keeps its bold one-line rule (+ ≤1 sentence of
  mechanism); all 26 war stories moved verbatim to `references/case-files-build.md`, pointed to
  as `(case file: <heading>)`. 41KB → 16KB with zero rules dropped.

### Added
- **`/build`: validator-seam parity rule** — a sibling field's check that runs AFTER the
  protected use (a prompt render, a query) protects nothing on that path while reading as
  covered; check WHERE each check runs, not just that it exists (supersedes PR #34).
- **PRINCIPLES §Lesson format** — the standing policy: rule up front, story in the case file;
  prune roughly every 10 merged lessons or when a skill passes ~15KB.

## [1.3.0] — 2026-07-27

Catch-up release: 20 merged PRs of harvested build-loop lessons (PRs #12–#31)
that shipped without CHANGELOG/version bumps. All additive guidance — backward-compatible.
Every lesson below was paid for by a real bug (or a real bill) on a shipped project.

### Added — `/build`
- **Session economy** (#31): one-feature-per-session is a COST rule — session cost grows
  ~quadratically with length; handoff + fresh session at checkpoints, `/compact` after closed
  detours, bulky output to files. Measured: 97% of a ~$2.9K-equivalent month was cache re-reads.
- **Latency/concurrency-fix lessons** (#30): sync-SDK-in-async serializes the process (measure the
  staircase first); the platform's per-container concurrency is a SECOND serializer — re-measure
  deployed. Plus delete-the-wire mechanics: cut wires on a COMMITTED baseline.
- **Suggested-options lessons** (#29, also `/contracts`): AI suggestion vs user confirmation kept
  structurally distinct; service-role reads re-state RLS scoping; client selectors only choose among
  server-approved sets; context switches clear dependent confirmations.
- **Collector + comment lessons** (#28): config-driven collectors drop inputs rendered outside the
  config list — audit them; a code comment's behavioral claim is a spec to verify.
- **Re-run bypasses cache** (#27): an explicit Refresh must skip the cache READ, keep the WRITE;
  cache keys include logic version.
- **Green-suite gates** (#25): criterion-altitude tests (match the VERB); implemented ≠ verified;
  delete-the-wire; wrong-column corollary (a wire can exist and point at the wrong source — verify
  every WRITER); widening what's legal leaves the suite green and the consumers unread; round-trip
  save→reopen→save tests; mechanical checks over remembered rules.
- **Vendor-payload fixtures** (#24): your own fixtures can't falsify what a third party sends —
  capture one real vendor response; read what a vendor flag REMOVES.
- **Licence gate** (#18): third-party content licences are a feasibility gate before design —
  sublicensing, attribution, indemnity; ship the mechanism OFF when no source clears it.
- **Shipped-config spot-checks** (#17): validate generated output at the values production ships,
  not test-convenient ones; derive layout constants from runtime state.
- **Deployed-binary features** (#16): a pinned static binary's feature set is a deploy-only risk —
  smoke the actual feature, not `--version`.
- **Async-job checklist + production entrypoint** (#15): the job handle IS the money (spawner must
  poll); sign handles (HMAC); persist per-poll; terminal-timeout taxonomy; mid-batch merges. Verify
  the production ENTRYPOINT — dependency construction is untested code.
- **Gate/validator DoD + cache keys** (#14): fail CLOSED on your own bugs; unconfigured ≠ degraded;
  auto-fixes re-validated; never trust client "already passed"; facts vs judgements; no fabricated
  scores; cache keys built by EXCLUSION.
- **Browser-E2E traps** (#12, #13): `text=` substring waits; mid-request browser close; assert
  persisted state; verify the actual bound dev-server port; env-gated UI on the instance under test.
- **Live path on the USER'S runtime** (#20): register routes on EVERY serving surface; verifying the
  deployed surface proves nothing about the local shim the user opens.
- **Project docs/skills are CLAIMS** (#22, also `/drift-check`): verify a pinned plan's load-bearing
  claims and a repo skill's concrete facts against the code; fix rotted instructions in-session.

### Added — other skills
- **`/ship`**: one-subtask-per-session named as the cost lever with the measurement (#31).
- **`/scope`**: non-goal reversal protocol — reopen deliberately, record the reversal (#19).
- **`/architect`**: benchmark must ask where approvals/human-in-the-loop attach — the OSS-first
  blind spot (#21).
- **`/drift-check`**: docs must POINT at the source of truth, not re-type it (#23).

### Process
- This release also closes the gap it documents: `/ship`'s own CHANGELOG+semver criterion was
  skipped by every one of these PRs. Stale PR #26 closed as superseded (content landed via #27/#28).

## [1.2.3] — 2026-06-14

`/frontend-audit` made trustworthy — closes three silent false-passes found by running the engine on real
sample pages, and wires `/design-system` to actually RUN it. Backward-compatible.

### Fixed
- **Contrast no longer silently passes when it wasn't checked** (`audit.py`, Law 7). The fg/surface token
  pairs were hard-coded to shadcn names, so a project using `--text`/`--surface`/`--bg` got **zero** contrast
  checks yet a `contrast:ok` roll-up. Now: common non-shadcn aliases are checked too, and if colour tokens
  exist but no pair is checkable, it emits a `Law7-unverified` **WARN** instead of a false "ok".
- **Near-twin display fonts are caught** (Law 1). A `--font-display` that is a width/weight variant of the
  body face (e.g. `Inter Tight` over `Inter`) now WARNs `Law1-near-twin` — it isn't a distinct identity. A
  real pairing (e.g. `Space Grotesk` over `Inter`, or IBM Plex Sans/Serif) is not flagged. Font checks now
  also recognise `--font-body`/`--font-base`, not just `--font-sans`.
- **Manual-toggle-only dark mode is caught** (Law 22). A `.dark` block with no `prefers-color-scheme` rule
  that swaps the token set now WARNs `Law22-system` (system preference ignored) — previously reported
  `theming:ok`.

### Changed
- **`/design-system` now RUNS the audit, not just cites it** (`SKILL.md` Step 5). Concrete
  `python commands/frontend-audit/audit.py <sample> DESIGN.md` invocation at confirm-time and post-emit, with
  an instruction to act on `[FAIL]`/`[WARN]` and to treat `Law7-unverified` as "not checked," never "passed."
- `frontend-audit/SKILL.md` check table updated to document the new checks.

## [1.2.2] — 2026-06-14

`/design-system` laws reframed as **outcomes, not tools** — additive, backward-compatible (numbering 1–22 unchanged).

### Changed
- **Universal laws restructured into Floor / Means / Aesthetic / Process** (`references/universal-laws.md`). A
  rule is only a *law* if it holds regardless of stack, aesthetic, or motion level; rules that named a tool or
  a look are now tagged `[MEANS]` / `[AESTHETIC]` recommendations. Every law tagged, a grouped index added, and
  numbering 1–22 kept stable (other files reference laws by number).
- **Law 15 reframed** — the floor is now *"interactive components meet the accessibility floor
  (focus/ARIA/keyboard/states)"*; **shadcn/ui + 21st.dev is the recommended means on a React stack**. Resolves
  the contradiction where the skill's own standalone-preview output could never satisfy a shadcn-mandating law.
- **Law 8 (OKLCH)** and **Law 12 (Framer/GSAP/Three.js ladder)** demoted to `[MEANS]`; their floors (predictable
  lightness / performant + reduced-motion-safe) stay fixed.
- **Laws 6 & 20** restated as outcome + canonical example (purple gradient / dot-not-pill).
- **Tightened catchable floors:** Law 1 (a body-face near-twin like Inter Tight is not a distinctive display),
  Law 7 (an asserted contrast comment is not compliance — compute it), Law 21 (desktop-first + `max-width` is
  the named failure), Law 22 (the system swap must actually apply dark values).
- **Law 19** now also declines **bespoke / non-document surfaces** (canvas/WebGL games, generative art, TUIs).
- **`SKILL.md`** Step-4 lines fixed so the preview caveat no longer reads as a Law-15 exemption — accessible
  primitives are required even in a vanilla preview.

## [1.2.1] — 2026-06-13

Refinements to `/design-system` from a six-archetype test pass — additive, backward-compatible.

### Changed
- **Theme Studio — Mode toggle syncs to the page's real mode on load** (`references/theme-studio.md`).
  It no longer hard-codes "Light" active; a **dark-default** product (ships `<html class="dark">`) opens on
  **Dark**, a light one on **Light**, a class-less one on **System**. Note added: keep samples token-only so
  the Light switch actually adapts (a stray hardcoded colour ghosts in light mode).
- **Craft layer — "shared grammar, distinct voice"** (`references/craft.md`, `SKILL.md`). The signature
  *moves* are reusable across an archetype, but the *voice* (typeface pairing, palette, texture, radius) must
  be derived per product and never lifted from one exemplar — so two Cinematic products look like two brands,
  not clones. Added an explicit gut-check + a Step-6 self-check clause.
- **Craft layer — expressive pages earn ≥1 signature moment** (`references/craft.md`, `SKILL.md`). An
  expressive (Bucket B) page with no signature gesture is under-built; restraint (Bucket A) families
  deliberately ship none.

## [1.2.0] — 2026-06-13

Motion gets a discipline: which motion an archetype may use, and the concrete craft to wire it well.

### Added
- **Motion tier ladder** (`/design-system` Law 12) — turns the motion law from a pure constraint into a
  gated 4-tier ladder: **Tier 0** CSS transitions · **Tier 1** Framer Motion · **Tier 2** GSAP +
  ScrollTrigger · **Tier 3** Three.js / WebGL. Each archetype declares a **motion ceiling** in
  `archetypes.md`; Tier 3 (3D/WebGL hero) is sanctioned only for Cinematic / Marketing-Splash / Glass.
  Every Tier ≥ 1 effect must sit behind `prefers-reduced-motion` with a static fallback, be lazy-loaded,
  and hold a 60fps budget — the "earn its place" restraint floor is unchanged.
- **Craft layer** (`design-system/references/craft.md`, loaded at Step 4) — the per-archetype *signature
  moves* that make a page read as hand-crafted, split into **restraint** families (the craft is precision;
  an explicit "no scroll theatrics" list) and **expressive** families (real, wired GSAP/Framer signatures —
  line-mask reveal, scrub parallax, count-up, spring-stagger, glass/WebGL hero — never stubbed). Snippets
  ship their reduced-motion guard + lazy-load inline.
- **DESIGN.md §7 motion fields** — motion tier, scroll/hero motion, reduced-motion fallback, and perf budget
  are now recorded so the chosen signature survives into the real build.

### Changed
- `/frontend-audit` (`audit.py`) gains three motion checks (WARN): `Law12-reduced-motion` (heavy-motion lib
  with no reduced-motion guard — accepts the media query *or* an idiomatic `useReducedMotion` hook),
  `Law12-layout-anim` (transition targets a layout/paint property), `Law12-long-duration` (CSS animation
  > 1000ms). They fold into the existing `motion` roll-up; reference docs that *name* the libraries do not
  false-positive.

## [1.1.1] — 2026-06-09

### Added
- **Lesson: policy-as-code "parses" ≠ "governs"** (`PRINCIPLES.md` §Lessons baked in) — a
  syntactically-valid but ruleless authorization policy silently degrades to the engine default
  (deny-all / allow-all); load-validate ≥1 rule and fail-loud, build the authz query from escaped
  identifiers + structured request/entity objects (a crafted tool/role name is an injection point
  like SQL), and default-deny on any eval error / no-decision. Generalised from a Cedar RBAC adapter
  build (GateKeeperAI M1.2).

## [1.1.0] — 2026-06-07

### Added
- **Flexible spine resolution** (`PRINCIPLES.md` §Spine resolution) — skills now work on existing /
  brownfield projects, not just products born in the playbook. When there is no `PRODUCT.md`, skills
  resolve the spine from the project's own docs (`CLAUDE.md` → `README.md` → `docs/` → `AGENTS.md`);
  for **code-only** projects they emit a clearly-labelled **INFERRED** summary and recommend
  bootstrapping a spine instead of fabricating a baseline. `/drift-check` carries the full
  three-tier behaviour (resolve spine · graceful write when no `PRODUCT.md` · honest "no recorded
  intent" verdict for code-only).

### Changed
- All 15 skill headers point at `PRINCIPLES.md` §Spine resolution rather than hard-naming `PRODUCT.md`.

### Unchanged (compatibility)
- **`PRODUCT.md`-first** — when `PRODUCT.md` exists, behaviour is identical to 1.0.0. Greenfield
  playbook projects and the existing `evals/` (all Tier-1) are unaffected.

## [1.0.0] — 2026-06-04

First public release.

### Added
- **15 skills** across the product lifecycle: `/playbook` (guided entry-point); Product — `/vision`,
  `/scope`, `/plan`; Development — `/architect`, `/structure`, `/foundation`, `/contracts`, `/build`,
  `/dev-check`; `/test`; `/eval`; `/ship`; `/learn`; and the cross-cutting `/drift-check`.
- **`PRODUCT.md`** living-spine template — every phase reads + appends; the product's story in one file.
- **`PRINCIPLES.md`** — the single rulebook every skill enforces (and verifies with evidence).
- **`VISION.md`** — the toolkit's own completeness contract (every skill + its exit criteria).
- **Evidence-based principle gates** — each skill verifies its named principles are actually
  implemented (composing `/code-review`, `/security-review`, `/verify`, `/run`, `/doc-audit`) before
  handing off; deterministic checks (secret-scan, lint, tests, dep-vuln) run via pre-commit + CI.
- **Three install modes** — global (`./install.sh`), project-level (`./install.sh --project <path>`),
  and plugin (`.claude-plugin/` → `/plugin install`).
- `manifest.json`, `evals/evals.json` (a behaviour check per skill), and an `install.sh` installer.

[1.2.1]: https://github.com/kish21/product-playbook/releases/tag/v1.2.1
[1.2.0]: https://github.com/kish21/product-playbook/releases/tag/v1.2.0
[1.0.0]: https://github.com/kish21/product-playbook/releases/tag/v1.0.0
