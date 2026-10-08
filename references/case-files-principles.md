# Case files — `PRINCIPLES.md`

War stories behind the one-line lessons in `PRINCIPLES.md` §Lessons baked in. Each heading is
pointed to from the rule as `(case file: <heading>)`. Opened on demand, never auto-loaded.

## The 53 assertions nothing read

This repo's own `VISION.md` claimed *"`evals/evals.json` proves each skill matches this VISION;
re-run on change."* Nothing read it. CI parsed the file for JSON validity and compared the **set of
skill names** against `commands/` — and never once looked at a `prompt` or an `expected_output`.
Fifty-three assertions, green forever. This is failure mode #3 from the repo's own README (*"I
relied on green tests while the app was dead in production"*), sitting inside the repo that
preaches against it.

The file did not merely go stale. It grew a **second schema**: six cases — the five `/tickets` cases
and `build-lane-mode` — had drifted to `assertions` + `expected_artifacts` and carried **no
`expected_output` at all**, the one field skill-creator's schema (`references/schemas.md`)
requires. They were merged, released and cached in three plugin versions without anything noticing,
**because the only field anything compared was a name.** Separately, `evals.json`'s own note
promised *"2-3 trigger/behaviour checks per skill"* while `contracts`, `dev-check` and `eval` each
shipped exactly one.

The overclaim was the active harm: it stopped anyone from going to look. A file described as a
guarantee is a file nobody audits.

The fix had two halves, and only one of them was cheap. **Structure** got a real gate —
`tools/check.py` check 8, run in CI on every case: required fields present and non-empty, unique
ids, list fields are lists, **no field name has drifted** (an allow-list, which is what caught
`assertions`), and at least two cases per skill. The gate was written first and run **red on all 15
pre-existing violations** before any data was touched, then mutation-tested per violation class
(duplicate id, blank required field, list field given a string, drifted field name, a skill dropped
to one case — each red with a distinct message). **Execution** was not fixed: running the cases
needs `claude plugin eval`, an API budget and tolerance for non-determinism across 56 LLM-judged
cases. So the *claim* was scoped instead — `VISION.md` now says CI gates the file's **structure**,
not its verdicts, and that a green build means the assertions are **well-formed, not met**, with
the execution half left standing as an open item in `docs/lane-mode.md`.

That is the shape of the lesson: when you cannot afford to run the thing, you can still gate its
structure, and you must shrink the sentence that describes it down to what is actually checked.

**The same shape elsewhere:** *the absence of a record reads as "fine"* — a phase that declines to
run leaves no trace, and a skipped step is indistinguishable from a step that passed.

## The gate that was only a heading

`/eval` shipped with `## Step 0 — Context + prior-gate check` from the day the phase template landed.
Fourteen sibling skills carried the same heading and, under it, an actual gate: *"if `#Scope` is
missing/empty, warn and offer `/scope` first (allow override)"*. `/eval` carried the heading and,
under it, a read: *"Read `#Vision/#Scope/#Plan` for the goal and `#Tests` for what's covered."*
Reading a section is not gating on it.

It surfaced on a logged test run (2026-09-08). The project was mid-Build:
two features in `#Build log`, `#Dev-complete` entirely unchecked, `#Tests` entirely empty. The user ran
`/eval` — three phases early. The run stopped, correctly. But it stopped on the agent's own judgement,
not because the skill asked; a run that scored the half-built product instead would have violated no
instruction in the file. The orientation the playbook exists to give — *"you are early, run `/dev-check`
then `/test` first"* — was never in the text.

Two things made it invisible for five releases:

1. **The heading answered the question.** Anyone auditing "does `/eval` gate?" greps for the gate's
   name, finds it, and stops. The title is the most convincing possible evidence that the behaviour
   exists, and it costs nothing to keep after the behaviour never arrived.
2. **An eval case asserted the missing behaviour.** `eval-declined-run-leaves-a-trace` states that
   `/eval` "finds `#Tests` (and `#Dev-complete`) empty, declines to measure" — a gate the skill body
   never specified. Nothing executes the eval cases, so the assertion sat there agreeing with the
   heading rather than contradicting the body.

The fix was one bullet in `/eval` and a CI check that reads the body, not the title: every phase skill
except `/vision` (which opens the chain) must name a prior `#Section` in Step 0 **and** offer an
override. Written before the fix, it went red on three skills, not one — `/build` named `/contracts`
with no override, and `/dev-check` had no prior-gate at all, so a checkpoint run over an empty
`#Build log` passed by having nothing to fail. The bug the ticket described was real; it was also
one instance of a class, and only a check that ignored headings could see the other two.

## The prune that would have deleted the rules

**product-playbook #138, 2026-09-10.** Three skills sat over the ~15KB prune threshold and were
exempted by name in `check.py`: `build` (24.5KB), `tickets` (21.3KB), `design-system` (19.6KB). The
ticket's instruction was the standing one from §Lesson format — run a prune pass, war story verbatim
into `references/case-files-<skill>.md`.

Reading `build.md` before moving anything showed the premise was wrong twice over. First, the bulk was
not war stories: ~7KB of it was *rules* — ten for building a gate, six for an async job, two for a
latency fix, seven for trust boundaries — each already distilled to one bold line. There was nothing
left to condense. Second, and worse: `install.sh` copies only `PRINCIPLES.md`, `MECHANISMS.md`,
`LESSONS.md`, `VISION.md` and the `PRODUCT.md` template into `~/.claude/product-playbook/`. Nothing
under `references/case-files-*.md` is installed at all. Following the instruction literally would have
moved 7KB of load-bearing rules into a file no installed user has — and `check.py` would have gone
green on it, because it measures the skill file, not what the skill still knows.

The fix was the structure the repo already used for `design-system`: convert `build` and `tickets` to
directory form, so their `references/` folder installs beside `SKILL.md`. Conditional rules moved
there; the triggers stayed in the skill. `SIZE_EXEMPT` is now empty. The size check was proved to
still fire by lowering the threshold and watching three skills go red.

The generalisation is the distinction the original rule never drew: **a case file holds evidence, a
reference holds rules.** Only one of the two ships.

## The state model's history — moved out of STATE-MODEL.md on 2026-09-24, unchanged

STATE-MODEL.md now holds only the rules a run follows. What follows is the design note it grew from
(v1.31.0, #126/#121, and the later #131/#145 decisions), kept verbatim so the reasoning is never lost.

### Why the state model exists (was §1)

### 1a. The state vocabulary was never written down

`PRODUCT.md` is described as the spine's *memory*. It is more than that already, and has been for
several releases — the state vocabulary accreted one fix at a time:

| Shipped | What it added |
|---|---|
| v1.23.0 | `_Not run <date>: … — run X first._` — a phase that declines leaves a trace |
| §Declined runs | `Override <date>: <reason>` — a deliberate skip *counts as filled* |
| v1.28.0 (#128) | `Override <date>: <reason> — bypassed <gate>` — a bypassed gate, ditto |
| §Re-run semantics | `superseded <date>: <why>` — a reversed decision is dated, not erased |
| `/playbook` Step 0 | the *frontier* — the first unfilled section — plus out-of-order inversion warnings |

Those **are** states and transitions. Nobody had written the set down, and an undeclared vocabulary
grown ad hoc has holes nobody can see. Measured across all 16 phase skills before this change:

| Marker | Coverage |
|---|---|
| `Not run` (declined) | 15/16 — `/design-system` had none |
| Step 3b (close the loop) | 15/16 — `/design-system` had none |
| Step 3c (contradiction check) | 15/16 — `/design-system` had none |
| §Re-run semantics (superseded) | **6/16** |

Two consequences, and the second is the real defect:

1. **`/design-system` was outside the state model entirely** — zero of four — while still writing
   `PRODUCT.md#Design`.
2. **Re-run semantics covered 6 of 16, and some of those omissions are correct.** `/build`, `/ship`
   and `/learn` append rather than overwrite, so "a second run must not erase the first" may be free
   for them. **But it was impossible to tell.** With no declared rule for which skills need it, an
   intentional omission and a hole are indistinguishable. *That ambiguity is the bug*, not the
   omission.

### 1b. Every stop was called "confirmation", and most of them are not

`/vision` Step 2 says *"Ask these one block at a time; wait for answers."* `/scope` says *"Ask, one
block at a time."* Those pause because **the answer exists only in the user's head** — who it is for,
the north-star target, what gets cut. Describing them as *"stops and waits for your confirmation"*
makes an **interview** sound like a **signature**, and a reader budgets eighteen approval clicks
before they have run anything. That framing is ours, and it is the largest single source of the
"bureaucratic" reading.

### Where the claim-to-evidence pass lives (was §2h)

Three options were on the table: extend `/drift-check` · a `/prove` engine other skills compose · a 22nd
top-level skill. **Chosen: extend `/drift-check`**, and the ticket's instruction not to pick the third by
default is honoured.

- `/drift-check` **already owns claim-vs-reality** — its exit criteria already include *"code↔docs drift
  checked (claims that don't match reality)"*. This generalises that from scope/vision/doc drift to
  *every claim in the spine*, which is a widening of an existing remit rather than a new capability.
- It is **already the "run anytime" skill**, which is exactly when a re-verification pass is wanted.
- A 22nd top-level skill would directly contradict #116 and #123, which are about the surface already
  being intimidating. That cost is real and buys nothing here.

**This also supplied the transition guard §4 deferred.** Once evidence is re-runnable, reconciling
*intended* against *actual* at a transition is a small addition to Step 3b rather than a new subsystem.
That is exactly how it shipped in #145 — see §4.

### Rejected: /playbook --auto (was §3, full text)

Recorded here so a future session finds it before re-proposing it cold.

1. **It would let the AI author the product premise.** Phase 1 gates have no derivable answer.
   Autopiloting `/vision` → `/scope` does not skip a confirmation; it has the agent invent what the
   product is and build on it — the exact failure this repo was founded on (*"I let features creep in
   that nobody needed"*). That places the vibe-coding trap inside the tool built to prevent it.
2. **It deletes the cost mechanism, not just the safety one.** A vision→ship run in one session is a
   single 600–900-call session; agent-session cost grows roughly quadratically with session length,
   because every call re-reads the whole history. The per-phase stops **are** the session boundaries.
3. **The escape hatch already exists.** Every skill runs standalone (`commands/playbook.md`), so an
   experienced builder types `/contracts` directly and never touches the orchestrator. The residual
   complaint is `/playbook` **verbosity** — a narration fix, not a new mode.

Batching within `derivation` and `verification` runs delivers most of what was asked for, and grants
no authority to invent product decisions. **If `--auto` is ever reopened it must be a deliberate
reversal with the reasoning recorded** — not a silent re-introduction.

### The transition guard (was §4)

The audit's model makes **evidence reconciliation a transition guard**: every advance compares
*intended* state against *actual* repository state. Nothing did that automatically — `/drift-check`
does intended-vs-actual but is opt-in, and Step 3c compares recorded decisions against *other recorded
decisions* (docs vs docs, not docs vs repo). **A gate that only runs when you remember it is not a gate.**

**It shipped as a fourth item in `MECHANISMS.md` §Step 3b**, not a new subsystem and not a new skill —
§2h had already made and recorded that surface-cost decision. At every transition the phase re-runs its
own `evidence:` lines through `/drift-check`'s Step 0b pass, classifies each with §2g's four verdicts,
and checks the transition against §2b's table. `UNVERIFIED` — no measurement possible here — stays a
normal outcome and never blocks a phase, or the guard would punish exactly the environments that
legitimately cannot measure.

**The one illegal transition is refused where it is produced.** `filled ──▶ declined` comes from a
*declining* run, which stops early and never reaches Step 3b — so the refusal lives in
`MECHANISMS.md` §Declined runs (only an unfilled section may take the Not-run line), not in a gate that
path never executes. A guard placed where the failure cannot occur is a heading, not a behaviour.

**The deferral, kept rather than erased** (§Re-run semantics: date the reversal, do not erase it). It was
deferred as the largest behavioural change in the area, and blocked on #131, which had to land a
re-runnable evidence record before a guard had anything to check. **Reopen trigger, met 2026-09-10:**
#131 shipped §2f, so the guard became a small addition to Step 3b rather than a new subsystem, and #145
picked it up at its own gate. Nothing about the original reasoning was wrong; the condition it named
came true.

### What the state model did NOT do (was §5)

**No engine.** A YAML state file with a transition engine would be heavier than the thing it guards,
and these skills are prompt files, not code. The value is in **declaring the set and enforcing
participation**, exactly as check 9 enforces prior gates.

**No service.** Per `VISION.md`'s recorded non-goal, machine-readable state is added *against* that
guard rail: everything here is a line of Markdown in a file in the repo.

**No second override format.** `Override <date>: <reason> — bypassed <gate>` is #128's, reused.

*Superseded 2026-09-24 for status only: see STATE-MODEL.md §2h.*

### What was verified (was §6)

`tools/check.py`:

- **check 12** — every phase skill declares a **Gate type** of `input` · `derivation` ·
  `verification`, and an `input` gate declares that it is **never batched**.
- **check 13** — every skill that writes a spine section declares its **State model**: the section it
  writes, and `declined` / `override` / `superseded` each either implemented or marked `n/a` **with a
  reason**. A missing declaration fails; so does an exemption with no reason.
- **check 16** — every skill that writes a spine section actually **runs the transition guard** in the
  region where it closes its gate (Step 3b through Step 3c), points at `MECHANISMS.md` §Step 3b where the
  guard is defined once, and says there that `UNVERIFIED` is a normal outcome. Reading the region rather
  than the file is deliberate: a skill that *mentions* the guard elsewhere and never runs it would
  otherwise pass, which is check 9's lesson (a heading is not a behaviour) applied to the clause that
  names one. `/drift-check` is the single exemption: it *owns* the claim-to-evidence pass the guard
  re-uses, so a pointer back to itself would say nothing. `/adopt` participates too — it drafts the whole
  spine from repo evidence, so reconciling intended against actual is its subject matter, and an inferred
  spine is precisely where unmeasured claims collect.

All three were proven to fail before they passed.
