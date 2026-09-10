# Changelog

All notable changes to product-playbook are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project uses [Semantic Versioning](https://semver.org/).

## [1.26.0] - 2026-09-10

### Changed — **the playbook now names its own target user** (#132)
`/vision`'s exit criteria require every product to name a target user and a job-to-be-done.
This repo had never done it: `VISION.md` said "anyone — a newcomer (techie or not)", which is who
*can* use it, not who it is *for* — the exact answer `/vision` would reject. `VISION.md` now names a
primary reader (a technical builder shipping with AI coding agents, with no PM/QA/security/release
role beside them) and the job to be done, lists the secondary audiences as explicitly deferred, and
**retires the "techie or not" claim** rather than leaving two audience statements standing. Third
instance of the same self-exemption pattern, after #127 and #128.

### Changed — **positioning states the pain, not the shape** (#118, #124)
"A guided path from idea → shipped" was equally true of Scrum or a whiteboard checklist. The thesis
was already written and hidden at line 60 inside a collapsed `<details>`, with a skip-link routing
readers around it. `README.md` now leads with the AI-speed-vs-reasoning gap, carries the
execution-engine / discipline-engine argument and the five failure modes above the fold, and the
story CTA routes to the entry command instead of past the positioning. AI coding is the accelerant;
**Claude Code is the runtime, never the villain**. `VISION.md` §Why this exists moves with it — a
sharpened README against an unchanged VISION would be the doc-drift this repo exists to catch.

The guarantee is calibrated in the same edit: **"senior-level results by default" is gone.** Results
depend on judgment no gate can supply. Both spine files now make one claim — *a process that cannot
silently skip a check* — which is stronger because it is checkable.

### Added — **"evidence gates", the philosophy named once** (#120)
Both words appeared 30+ times across the spine; the idea had no name, so every use re-explained it.
Named once in `README.md`, `VISION.md` and `PRINCIPLES.md` §The exit-criteria gate, and used only
where it is load-bearing. **Third word decided deliberately:** the audit proposed *Evidence → Gate →
Progress*; shipped instead as **no evidence → the gate holds → no progress**, because the enforced
behaviour is the refusal, not the advance — a happy-path slogan would describe the half of the
mechanism that has no teeth. `README.md` cites `tools/check.py` check 9 as the mechanical proof,
which makes check 9 load-bearing for the claim: it may not be weakened or exempted.

### Added — **why this is not a set of templates** (#122)
A single four-word bullet separated this from "AI-generated PM templates". A README body section now
makes the case with verifiable specifics — `audit.py` (contrast computed, never asserted),
`tools/check.py` (CI fails on a gateless gate), the engineering definition-of-done, and one-click
links into `PRINCIPLES.md` §Production safeguards and §Production-readiness concern areas. The
audit's suggested label "AI-native development operating system" was **rejected**: hype register
undermines a product whose thesis is discipline over vibes.

### Added — **before → after, and three tiers over six phases** (#119, #123)
The journey diagram was ~140 lines down and showed no gates — a flat list of command names that read
as "18 things to memorise". It moves above the fold, gains `✓ evidence` between the tiers, and gains
a "without the playbook" contrast whose four unanswerable questions are each **wired to the
`PRODUCT.md` section that answers them**. The six phases group into three tiers for **display only**
— all 15 skill frontmatters keep their phase numbers, since those strings are what Claude Code shows
in the skill picker. Security, verification and scope integrity are drawn as spanning all three
tiers, never as a stage you pass. Net visual count above the fold is unchanged: the new panel
replaces the old journey block rather than joining it.

### Changed — **the reveal order: one door, then the rooms** (#116)
"21 skills" was announced five times in the first 66 lines, including as the opening sentence's
subject and as the destination of the skip-link for the most time-pressed reader. The count is now a
capability claim, not a first instruction; the quick start is one command; and the standalone-skill
guarantee stays on the quick-start screen — **the fix is ordering, not removal**, since every skill
running on its own is why an experienced builder picks this over a rigid wizard.

### Added — **Git-native stated as a choice, hosted state recorded as a non-goal** (#133)
`PRODUCT.md` living in Git was mentioned once, as a convenience. `VISION.md` now states it as the
architectural property it is, with its consequences listed concretely (reviewable · versioned ·
revertable · branchable · agent-inspectable · forkable · no external dependency), and records **no
SaaS / no hosted spine / no web UI / no accounts** as an explicit non-goal with its reasoning and a
**reopen trigger**, per `/scope`'s own Deferred+trigger convention. Every open ticket that adds
machine-readable state is now built against a written guard rail rather than an assumption.

### Added — `check.py` check 10: one skill count, everywhere (#130)
The GitHub repo description said "18 commands" while the README said 21 in five places — a stale
storefront on a project whose thesis is docs-match-reality. The description is updated to the new
positioning, and the number now has exactly one source: check 10 fails the build when any
`N skills` / `N commands` claim in `README.md` (badge and prose) or the `VISION.md` skills comment
disagrees with `commands/`. **Proven to fail first** — `all 21 skills` → `18` went red at
`README.md:313`, and dropping `/adopt` from the VISION comment went red before either was restored.

## [1.25.0] - 2026-09-10

### Fixed — **a heading is not a behaviour: `/eval` had the gate's title and no gate**
`/eval` Step 0 has read `## Step 0 — Context + prior-gate check` since the phase template landed,
while its body only *read* `#Tests` — it never asked whether `#Tests` or `#Dev-complete` were empty.
A user running `/eval` three phases early (found on a real mid-Build project) got none of the
"run `/dev-check` then `/test` first" orientation the other fourteen phase skills give. `/eval` now
carries the standard gate — name the missing phase, recommend it, allow an override — with the
v1.14.0 north-star baseline check left intact as a separate second gate.

### Added — `check.py` check 9: phase gates are read from the body, not the heading
Every phase skill except `/vision` must name a prior `#Section` in Step 0 **and** offer an override.
Written before the fix, it went red on three skills rather than one: `/build` named `/contracts` with
no override, and `/dev-check` had no prior-gate at all — a checkpoint over an empty `#Build log`
passed by having nothing to fail. Both now carry the same wording, so the chain is uniform.
Generalised into `PRINCIPLES.md` §Lessons baked in as **a heading is not a behaviour**
(case file: The gate that was only a heading), plus an eval case for the gate.

## [1.24.0] - 2026-09-10

### Added - **a correct no-op must still leave a trace**
The v1.23.0 fix, generalised out of the playbook and into `PRINCIPLES.md` §Lessons baked in so it
applies to the products built with it, not only to the playbook's own phases. A guard that declines,
a check that finds nothing, a scheduled job with no work to do: if it writes nothing, *"ran and found
nothing"* is indistinguishable from *"never ran"*, and whatever orients from the output keeps
proposing the same thing. One dated line, replaced rather than appended.

## [1.23.0] - 2026-09-10

### Added - **a phase that declines to run leaves a trace**
A skill that correctly stops at an unmet prior gate left the repo byte-identical, so from the repo
alone *"I ran `/eval` and it correctly declined"* was indistinguishable from *"I never ran `/eval`"*.
The user could not tell, the next session could not tell, and `/playbook` — which orients purely by
which sections are filled — kept proposing the same phase with no memory that it had already been
attempted and declined for a good reason.
- **`PRINCIPLES.md` §Declined runs is new.** A phase that declines to run records that it declined:
  ONE dated line at the top of its own section — `_Not run <date>: <what was missing> — run <phase>
  first._` — scaffold untouched, section still visibly **unfilled**, replaced (never appended to) on
  the next attempt. §Re-run semantics governed a phase *rewriting* its section; nothing governed a
  phase *declining to write one*.
- **All 15 phase skills reference it from Step 0.** `/tickets`, which owns no spine section, writes
  its trace to `docs/issues/README.md` instead.
- **`/playbook` now reads the note.** A section holding only a `Not run` line still counts as empty —
  it stays the frontier and the missing phase is still next — but the earlier attempt is *named*
  rather than proposed blind, and it is distinguished from an `Override` line, which does count as
  filled.
- **`/validate`'s override is reconciled, not duplicated** — it is now stated as the *deliberate-skip*
  shape of the general rule (dated, one line, scaffold kept), differing only in that the phase is no
  longer owed. The same generalisation v1.15.0 made of its append rule.
- Three eval cases; `templates/PRODUCT.md` states the empty-vs-`Not run`-vs-`Override` distinction in
  its own rules block.

## [1.22.0] - 2026-09-10

### Added - **a guarantee that nothing executes decays silently**
The v1.21.0 incident is now a rule instead of a memory. `PRINCIPLES.md` §Lessons baked in gains
**"a guarantee that nothing executes decays silently"** — an assertion file no runner reads drifts
freely (a second schema, a required field missing) because the only thing ever compared is a name,
so gate its structure in CI or scope the claim to what is actually checked. Overclaiming a guarantee
is worse than not having one: it stops anyone going to look.
- **`references/case-files-principles.md` is new** — the first case file for `PRINCIPLES.md` itself,
  carrying the full war story (*The 53 assertions nothing read*) so the rule in the skill-facing file
  stays one line, per §Lesson format.
- **`/test` Step 3b now asks the question at the gate.** Its evidence check already required that a
  golden/eval dataset *exist*; it now requires that **something actually executes it** — and if
  nothing does, that the suite's structure be gated and the claim be worded to match, never described
  as proof.

## [1.21.0] - 2026-09-10

### Fixed - **the eval file that proves the skills was itself unproven**
`VISION.md` claimed *"`evals/evals.json` proves each skill matches this VISION"*. Nothing read it. CI
parsed the file for JSON validity and compared the **set of skill names** against `commands/` — and
never once looked at a `prompt` or an `expected_output`. Fifty-three assertions, green forever, and
this is failure mode #3 from this repo's own README (*"green tests while the app was dead in
production"*) sitting inside the repo that preaches against it.
- **What the blind spot was already hiding: two schemas in one file.** Six cases — the five `/tickets`
  cases and `build-lane-mode` — had drifted to `assertions` + `expected_artifacts` and carried **no
  `expected_output` at all**, the one field skill-creator's schema requires. They had been merged,
  released and cached in three plugin versions without anything noticing, because the only field CI
  ever compared was the skill's name. All six are migrated: `assertions` is `expectations` (the
  upstream name, so an executor can one day read them), and each gained the `expected_output` it
  never had.
- **`tools/check.py` gains check 8**, a structural gate on every case: the required fields exist and
  are non-empty, ids are unique, list fields are lists, **no field name has drifted** (the allow-list
  is what caught `assertions`), and **every skill carries at least two cases** — which the file's own
  note had promised all along while `contracts`, `dev-check` and `eval` each shipped exactly one. All
  three now have the second case, covering the behaviour a single happy-path case never reached: the
  boundary units/scale trap and the refusal to accept a hand-edited schema, the dev-complete gate
  **failing** on a "done" recorded without evidence, and `#Vision`'s north star being the definition
  of good rather than a rubric invented at eval time.
- **The claim is now scoped to what is true.** `VISION.md` says CI gates the file's *structure*, not
  its verdicts, and that executing the cases is still manual — so a green build means the assertions
  are **well-formed, not met**. `docs/lane-mode.md` keeps the open item for the half that stands.
  Overclaiming a guarantee is worse than not having it: it stops anyone from going to look.

## [1.20.0] - 2026-09-08

### Fixed - **the last gate before release never asked whether anything was tested**
Found reviewing a **complete** `/vision`->`/learn` run on a real project. The spine came out with Vision, Validation, Scope, Plan, Architecture, Structure, Design, Foundation, Contracts, Build log, Ship log, Learnings and Drift log all filled - and **`#Dev-complete`, `#Tests` and `#Evaluation` all empty.** Three consecutive phases were skipped, `/ship` shipped anyway, `/learn` wrote a retro on top of it, and **nothing warned.**
- The cause: `/ship` Step 0 read **`#Eval` only** and never looked at `#Tests` or `#Dev-complete`. Every other phase gates on its predecessor; the one place it matters most gated on the least. It now reads **`#Dev-complete`, `#Tests` and `#Evaluation`**, names each empty one and recommends the phase that fills it.
- **Shipping is still allowed** - standalone use is first-class - but **an override is now recorded on the release, not implied by an empty section.** The Ship log gains a **Skipped phases** column: `none` when the full chain ran, otherwise the phases and the reason. *An empty `#Tests` is not a disclosure; it is an absence, and absence reads as "not applicable".*
- **"Allow override for small changes" is now bounded**, because an undefined escape hatch is always taken: `/eval` may be skipped only for a change that touches no product behaviour (docs, typo, revert). Whether a change is "small" is not a judgement the shipper makes about their own work.
- `/learn` now says so plainly when `#Evaluation` is empty - a retro with no measured result is opinion, and the "decided next" line inherits that weight.

### Fixed - **two skills read a section the template has never defined**
`/ship` and `/learn` were told to read **`#Eval`**; `templates/PRODUCT.md` defines **`## Evaluation`**. It worked only because the match is loose - and it is exactly the doc<->code drift this toolkit exists to prevent, sitting inside the toolkit. (A third instance was wording added earlier the same day: `/playbook` pointed at a `#Playbook` section that is a header *line*, not a section.)
- **`tools/check.py` now verifies every `#Section` a skill references against the template's real headings**, so the class cannot recur. Only `#Capitalised` references of 3+ characters count, so a CSS `#hex` or an issue `#N` is not mistaken for a section name.

## [1.19.0] - 2026-09-08

### Fixed - **`/design-system` proposed the look before asking what the user wanted**
Reported from a real `/design-system` run. The cause was not an ordering nit - **three statements described three behaviours**: `references/archetypes.md` headed its picker *"decide the archetype **FOR** the user"* and then, **one line later**, said *"**Ask the user** - plain language, one recommended answer each"*; `SKILL.md` Step 2 followed the heading (*"map the principles to one of the 13 families"*), so the agent answered all three questions on the user's behalf and the user was never asked them.
- **The ordering compounded it.** Step 2 read *"propose ONE as the default ... **then** ask the user 'do you already have a look in mind?'"*, and the exit criterion required both the proposal and the ask but **said nothing about their order** - so anchoring was compliant. A user handed a confident, well-argued recommendation says "yours is fine", not because they have no taste but because they were never given a blank page to answer from.
- **Step 2 is now ask-first:** the user's own reference is requested **before any family is named**, they answer the 3-question picker themselves (each with a recommended answer offered, so it stays one short exchange), and only then is one of the 13 families proposed - with a why that references what they just said. Their idea still wins. **A user with no opinion still gets a confident default in one turn**; the change adds no steps for them.
- **The exit criterion now states the order**, so proposal-then-ask no longer passes the gate, and `archetypes.md` stops contradicting its own next line.
- **Why this differs from `/architect`'s "one recommendation, get a yes/no":** for a stack the skill holds knowledge the user may lack, so leading with a recommendation is right. For **aesthetics the user's taste is the primary input** - the skill has no privileged view of what they like, and a design the user did not choose is one they will fight for the rest of the project.

## [1.18.0] - 2026-09-08

### Added - **`/adopt` - bring an existing, half-built project into the playbook**
`PRINCIPLES.md` §Spine resolution told every skill how to *read* a project with no `PRODUCT.md` - `CLAUDE.md` -> `README.md` -> `docs/` -> `AGENTS.md`, else infer from code and label it INFERRED. **Nothing ever created that spine.** A user midway through a build got a fresh low-confidence guess on every run and no offer to turn it into a record, and `/playbook`'s brownfield branch only said "enter at `/architect` or `/build`" - which leaves the project spineless, so every later phase re-guesses it. A midway user will not think to run a *guided start*; they will understand **"adopt this project"**.
- **Reads the repo, drafts, then stops.** Surveys docs, package metadata, entry points, routes, tests and CI, names the files it read, and drafts `PRODUCT.md` filling **only what the repo can evidence**. **Every inferred line is tagged `(inferred - confirm)`**; the owner then walks each section keep / correct / drop, and **nothing is written until that finishes**.
- **What it refuses to guess.** The north star, the riskiest assumption, the business model and the Non-goals are almost never inferable - code says *what* was built, never *why*, for *whom*, or what was deliberately **not** built. Those sections stay **empty**, which correctly means "this phase's exit criteria are not met yet". **An explicit "not doing" list is a real Non-goal; a feature that merely does not exist is not.** A fabricated spine is far worse than none: every later phase gates against it, and `/drift-check` would measure drift from fiction.
- **Idempotent and non-destructive** - an existing `PRODUCT.md` is never overwritten; it offers only to fill still-empty sections. Where the project's docs and its code disagree (the most common thing an adoption finds), Step 3c names both sides and records **which was stale**, rather than quietly preferring the code.
- Registered across every surface: `manifest.json`, `VISION.md` journey row, README table + the skill count (**20 -> 21**), the architecture diagram, and 2 eval cases (50 total). `/playbook`'s brownfield branch now routes here, and §Spine resolution case 3 recommends it as the direct route.

## [1.17.0] - 2026-09-08

### Added - **the playbook already knew the answer; now it uses it**
Both changes take structure the playbook had already written down and stopped making the user retype it.
- **`/new-component` discovers what is pending.** Bare, it expected the user to supply the component name, props and target path by hand - so the guided, core-first promise broke exactly where the playbook should be carrying the user. But `/tickets` requires each ticket's Target files to be **exact paths derived from `STRUCTURE.md`**, so every UI file a milestone needs is already recorded machine-readably before this skill runs. It now resolves the active milestone, takes those paths (**reusing the reading `/build` already does for its ALLOW list** - not a second parser), diffs against disk, and offers a built-vs-pending menu. Three constraints keep it honest: **discovery is a fallback, never a dependency** (with no `docs/issues/` it says so and continues from a description - the playbook is *sequential but standalone*); **one component per invocation**, because a batch generator in a leaf skill routes around `/build`'s definition-of-done gate and emits files nothing reviewed; and **directories come from `STRUCTURE.md`**, never a hardcoded `src/components/ui/`. A malformed ticket **fails loudly** - a silently empty menu reads as "nothing pending", the worst possible answer (a parsed document is a boundary).
- **`/tickets` mirrors the plan onto GitHub.** It published a flat, disconnected list: the Milestone column empty, no way to filter by feature, and ad-hoc bugs never linking back to the feature they belong to - while `#Plan` -> milestones -> lanes -> tickets has a native GitHub equivalent at every level. Now milestones are created from `#Plan` (titles derived, never invented) and assigned on create, the `Lane` field becomes a label, and Mode B resolves the parent's **real issue number** from the dedup index already in hand so GitHub renders the timeline link - degrading to the plain ID with a stated reason rather than **guessing a number that would link the bug to an unrelated issue**. **The label form is `lane: <name>`, with the space** - the spelling PRINCIPLES §Lane mode rule 4 already requires on PRs, because Lanekeeper's gate fails closed without exactly one label and therefore cannot move; a second spelling would split filtering in half. Milestones and labels get the **idempotency the issues already had**, and permissions for all three are checked **before** the first create: **a half-published backlog is worse than none**.
- **Resolved an inconsistency this exposed:** `/ship` required a project-board card "moved to Done" - auditing a board structure **nothing in the playbook creates**. Its criterion now applies only *if the project keeps a board*. Boards, assignees and estimates stay out of scope.

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
