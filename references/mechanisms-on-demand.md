# MECHANISMS-ON-DEMAND.md — the mechanism you open only when its trigger fires

> Companion to `MECHANISMS.md`. Everything in that file is read by **every** phase, every run, so its
> size is the per-session attention cost of the whole system. The mechanism below is **situational** —
> each section states the condition that makes it apply, and outside that condition it is dead weight in
> the context window. `MECHANISMS.md` keeps the trigger and the default inline and points here for the
> rest; this file installs alongside it, so the pointer resolves for an installed user too.

## §Spine resolution (full) — brownfield and code-only projects


**Trigger:** the project has **no `PRODUCT.md`**. With one, it *is* the spine and nothing here applies —
that default is stated inline in `MECHANISMS.md` §Spine resolution.

**2. No `PRODUCT.md`, but the project has docs** → resolve the spine from the project's own docs, in
order: `CLAUDE.md` → `README.md` → `docs/` → `AGENTS.md`. Map sections *loosely* (Vision ≈ the "what/why";
Scope/Non-goals ≈ an out-of-scope / "not doing" list; Build log ≈ a build-state / `CHANGELOG`). **State
which file you resolved as the spine.** Never fabricate a section that isn't there.

**3. Code only, no spine doc at all** → infer a **low-confidence** picture from the code + package
metadata (`package.json`, `pyproject.toml`, manifest, entry points, routes). **Label it "INFERRED"** and
say plainly what *cannot* be judged without recorded intent (e.g. true scope/vision drift). **Never grade
against a self-guessed baseline** (no-assumptions / honesty). Recommend bootstrapping a real spine —
**`/adopt`** is the direct route (it drafts the spine from this same evidence and has the owner confirm
it); `/vision`+`/scope` suits a project that is really starting over.

**Writing a section without a `PRODUCT.md`:** a skill that *writes* degrades gracefully — prefer reporting
to the user (and offering to create/append a spine) over forcing a `PRODUCT.md` the project never opted
into. A skill that *creates* `PRODUCT.md` by design (e.g. `/vision`) keeps doing so.

## §Lane mode (full) — the four rules


**Trigger:** the project has `.lanekeeper/config.yaml` or a root `lanes.yaml` (the policy), or the current
worktree has a `.lane` file (this session IS one agent's seat). Outside lane mode **nothing here applies**
and every skill behaves as before. The companion tool is
[Lanekeeper](https://github.com/kish21/parallel-agents): *product-playbook writes the work down;
Lanekeeper divides it up and gates every PR to its lane.*

1. **The ticket's file list IS the lane.** Lanekeeper reads the `Target Files` / `Allowed File Paths`
   section of the issue as the boundary, and a `Lane` heading as the feature name. A ticket with no files
   has no safety guarantee; a ticket that lists a *folder* has a boundary too wide to protect anyone.
   Exact paths, always — and the paths a ticket names must include **everything the build will write**,
   feature doc included.
2. **A lane is a feature slice, never a technology layer.** Vertical tickets are lanes by construction. A
   horizontal (per-layer) ticket turns one feature into N lanes and makes every change a collision — in
   lane mode the default is vertical, and horizontal needs a recorded reason.
3. **The spine is a shared file — it gets ONE writer.** `PRODUCT.md`, `CHANGELOG.md`, `STRUCTURE.md` and
   the policy files sit outside every lane; a lane PR that touches them fails the gate (or merge-conflicts
   with every other lane). Inside a lane, a skill writes only lane-owned files
   (`docs/features/<feature>.md`); the spine rows are **reconciled by the integrating session** on the
   base branch (`/dev-check` for the Build log, `/ship` for the Ship log + CHANGELOG). The alternative — a
   declared `shared:` zone for the spine with `merge=union` — is the user's explicit choice, never a
   default.
4. **The PR carries its lane — and so does the issue.** The label form is **`lane: <name>`, with a
   space**, on **both** the issue (`/tickets` applies it at publish) and the PR. One spelling, stated
   here, because Lanekeeper's gate fails closed without exactly one label: a second spelling (`lane:auth`)
   would split filtering in half. Every lane PR is labelled `lane: <name>` and passes `lanekeeper check`
   before it is opened. Lanekeeper owns the **PR template** and the gate workflow; product-playbook owns
   the **issue template**. Neither overwrites the other's file.

## §Re-run semantics (full) — a second run must not erase the first


**Trigger:** the section this phase writes is **not empty** — a pivot, a changed constraint, a redo.

Re-running a phase is not an edge case: a pivot, a changed constraint, or simply a redo. What gets lost is
the most expensive thing in the section to reconstruct — **why the other option was rejected.**

- **A run over a *non-empty* section shows what is about to change and asks before replacing it.** Never a
  silent overwrite. A first run over an empty section is unchanged — no extra prompting.
- **A reversed decision is dated, not erased.** The superseded ADR / scope item / metric stays, with a
  `superseded <date>: <why>` line beside it — the same record Step 3c writes, and what makes a reversal
  auditable instead of invisible.
- **A recommendation reversed *inside* one run is recorded too.** Where a skill recommends an option and
  the user picks another — the cheap trigger is *the answer is not the option marked (Recommended)* — the
  run writes one line into the section it is filling: `chose <X> over the recommended <Y> (<date>): <the
  user's reason>`. A confirm-and-iterate phase reverses within a run as its normal mode, and an argument
  made once in chat is gone by the next session.
- **Log-shaped sections keep appending** — `#Validation`, `#Build log`, `#Drift log`, `#Ship log`,
  `#Learnings`. `/validate`'s "append a new dated entry, never overwrite" is the general case.
- **A true restart may replace wholesale** — but only as an explicit, recorded choice.

## §Declined runs (full) — a phase that stops still leaves a trace


**Trigger:** this phase is **stopping without filling its section** — an unmet prior gate, or a
deliberate skip / bypass.

§Re-run semantics governs a phase *rewriting* its section. This governs a phase **declining to write
one**. A skill that correctly stops at an unmet prior gate leaves the repo byte-identical — so *"I ran
`/eval` and it correctly declined"* is indistinguishable from *"I never ran `/eval`"*, and `/playbook`,
which orients purely by which sections are filled, keeps proposing the phase with no memory of the stop.

**A phase that declines to run records that it declined.** One dated line at the top of its own
section, in this form, with nothing else in the section touched:

`_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._`

- **The scaffold stays intact and visibly unfilled.** Blanking or half-filling the fields is the
  §Re-run failure wearing new clothes: the note is orientation, not content.
- **It does not count as the section being filled.** `/playbook`, `/drift-check` and the next session
  still route to the missing phase — the note only lets them say *"attempted <date>, declined because X"*
  instead of proposing it blind.
- **One line, replaced on the next attempt — never appended.** An append-only log of every early
  invocation is noise, and noise trains people to skip the line that mattered.
- **Only a *declined* run writes it.** A phase that runs to completion writes its section normally; a
  phase nobody invoked writes nothing. This line means exactly *"attempted, and stopped for a reason"*.
- **Only an *unfilled* section can take it — `filled ──▶ declined` is refused** (`docs/state-model.md`
  §2b: a phase that ran does not un-run). A stop over an **already filled** section leaves it exactly as
  it is and says so; a filled section that needs redoing goes `filled ──▶ filled` through §Re-run
  semantics. The Not-run line over real content would destroy the phase's output *and* route `/playbook`
  back to a phase that is not owed.

**A deliberate skip is the same rule's other shape.** Where a phase is not merely *early* but is
**skipped on purpose** — `/validate`'s untested assumption, `/ship`'s skipped phases — or where a prior
gate is **bypassed on unmet criteria**, the line reads `Override <date>: <reason> — bypassed <gate>`, it
*does* count as filled, and later phases surface it every time they orient. Three things are required and
none is optional: **which gate** was bypassed, **a reason in the user's own words** (not the agent's
paraphrase, and not "user said continue"), and **the date**. A verbal "yes, continue" that reaches no file
turns a gated workflow into an advisory one. Both lines are dated, both are one line, both keep the
scaffold; they differ only in whether the phase is still owed.

## §Read receipt — proving a pointer was followed


**Trigger:** the section you are reading has a **`Detail:` companion file**. With no companion there is
nothing to follow and nothing to prove.

`MECHANISMS.md` §Follow the pointer makes opening the file an obligation. An obligation nobody can check
is a suggestion — it was named in 2 of 22 skills and enforced by no check, while the failure it exists to
prevent (a phase reading the record, inventing what the artefact would have said, and publishing eleven
wrong issues) had already happened once.

**So the proof is a quotation, not an assertion.** A phase that consumes a companion writes, into its own
section's `Read` field, one line per file opened:

```
Read: docs/scope.md (2026-09-12) — "no accounts for the organiser either"
```

- **The quoted fragment must occur VERBATIM in the named file.** That is the whole mechanism: the
  quotation cannot be produced without opening the file, and it is verifiable by string match rather
  than by trust. *"I read it"* is not checkable; a fragment is.
- **Quote something you actually used** — the line that decided what you wrote, not the first heading.
  A receipt quoting the title proves the file was opened and not that it was read.
- **One line per companion**, in the order read. A phase reading three companions writes three.
- **The file is missing or empty** → say so and write `Read: <file> — MISSING`, then treat the gap as a
  finding. Never infer the content; inventing it is the exact failure this prevents.

## §Section is a record — the phase that writes a section reports its size and applies the record test

**Trigger:** a phase has just written a spine section.

**There is no byte cap on `PRODUCT.md` or on any section.** A cap produces trimming, not relocation: on a
live run `#Vision` was "trimmed twice to squeeze under" a number, landed at 14 required fields of ~360
bytes each with nothing left to move, and the reasoning was written to the companion *in addition* — the
spine shrank by 30 bytes. The template's own 95 required fields make its old 25KB total unreachable by
construction (#200). The instrument is the **record test**, not a number.

**After writing, before closing the gate:**

1. **Measure and report** the section and the file in one line (`#Vision 5.1KB · PRODUCT.md 12.4KB`).
   Silence reads as unmeasured, and unmeasured is how it reached 73KB once. The number is a *signal* for
   `/drift-check`, never a verdict.
2. **Apply the record test to every field, invented fields included** — *is this the decision, or the
   reasoning behind it?* A decision, an evidence line or a pointer **stays, however many bytes it is**.
   Reasoning, workings, alternatives considered and raw notes **move to the `Detail:` companion**, and the
   field keeps the one-line conclusion plus the pointer.
3. **Never trim to a number.** Shortening a required answer to fit is the failure this replaces: the
   field loses information and the companion gains nothing. If a threshold is ever wanted, derive it from
   the template's field count — never hardcode one.
4. A field that is *only* reasoning with no decision in it is not a record yet: write the decision, then
   move the reasoning.

## §Context hygiene — bulky output to files, a progress line per step, measured close metrics

**Trigger:** a phase that runs commands for most of a session (`/foundation`, `/contracts`, `/tickets`,
`/build`). Any phase may apply it.

**Why this exists.** Session cost grows with everything already in the context, because every call
re-reads all of it. On one live run `/foundation` (385 calls) and `/contracts` (326 calls) each cost
~$70–75, about 60 % of it cache re-reads — and what had grown the context was **tool output**: full test
logs, whole files read back, long shell output. `/build` had carried "bulky output to files" as one
sentence since #31; a rule in one skill's Step 1 bound nobody. **Nothing here changes what a phase checks,
writes or verifies — reporting and context only.** (case file: The seventy-dollar skeleton)

1. **Bulky output goes to a file.** A command whose output would exceed a screen is redirected to the
   scratchpad (`> <scratch>/ci.log 2>&1`); the phase reads the tail or greps for the verdict line, and the
   `evidence:` line cites the file. Same command, same verdict. Read a file in full only when you are
   about to edit it; otherwise the range you need.
2. **One progress line per named step**, the moment it lands (*"3/8 — config loader + guards: boots,
   refuses the placeholder"*). A 50-minute phase with one question at the end is indistinguishable from a
   hung one; the owner should never have to ask "why is it taking so long".
3. **Blocking decisions up front.** A decision an earlier section left open for this phase is asked at
   Step 0, in one card, before any file is written; then the phase runs unattended and says so. A card
   asked six minutes in stalled everything behind it for 37 minutes.
4. **Close metrics are measured or absent.** If the close reports time, tokens or cost, the numbers come
   from the session log — call count, wall-clock first→last timestamp, output tokens, cache read/write —
   or the line reads *"not measured"*. Never an estimate: live closes guessed "$1.50–2.50" for a $20 run
   and "not visible" for a $75 one.

