# `PRODUCT.md` as a declared state machine — and gates classified by where the answer lives

> Design note, v1.31.0. Follows the `docs/lane-mode.md` precedent: the problem, the contract, what it
> touches, what is verified. Closes #126 and #121, which are one piece of work — both declare something
> the repo already does implicitly, and both enforce the declaration in `tools/check.py` in the style of
> check 9. They share one syntax on purpose; two declaration formats in one skill file would be worse
> than none.

---

## 1. The problem

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

---

## 2. The contract

### 2a. The state set

A `PRODUCT.md` section is in exactly one of these. Nothing else is a state.

| State | Written as | Counts as filled? | Frontier logic treats it as |
|---|---|---|---|
| **empty** | the scaffold, unfilled | no | **empty** — this is the frontier |
| **declined** | `_Not run <date>: <what was missing> — run <phase> first._` | no | **empty**, but names the earlier attempt instead of proposing blind |
| **filled** | the phase's required fields, non-empty and evidenced | yes | done |
| **overridden** | `Override <date>: <reason> — bypassed <gate>` | **yes** — the phase is not still owed | done, **and surfaced every time a later phase orients** |
| **superseded** | `superseded <date>: <why>` beside the old entry | n/a — a property of an *entry*, not a section | unchanged |

**No state is terminal.** Every one can be re-entered by a re-run; that is the point of §Re-run
semantics. `superseded` is deliberately not a section state — a section holding a superseded ADR is
still `filled`, and treating it otherwise would make every reversal look like regression.

### 2b. The legal transitions

```
empty ──▶ filled          a normal run
empty ──▶ declined        the prior gate was unmet and the run stopped (§Declined runs)
empty ──▶ overridden      the prior gate was unmet and the user chose to proceed (#128)
declined ──▶ filled       the missing phase ran; the Not-run line is REPLACED, never appended to
declined ──▶ overridden   the user chose to proceed without it
filled ──▶ filled         a re-run: show what changes, ask first, date what it reverses
overridden ──▶ filled     the skipped phase was run after all
```

**`filled ──▶ declined` is illegal.** A phase that ran does not un-run; a section that needs redoing
goes `filled ──▶ filled` through §Re-run semantics, which keeps the reason the other option lost.

### 2c. Which skills must implement which marker — and the exemptions, with reasons

Declared per skill, so an omission can never again be mistaken for a decision.

- **`declined`** — required of **every** skill that writes a section. No exemptions. A phase that
  stops silently is indistinguishable from a phase nobody ran.
- **`override`** — required of every skill that offers a prior gate. `/vision` opens the chain and has
  no prior gate, so it has none.
- **`superseded`** — required of skills whose section is **replaced** on a re-run. **Exempt where the
  section is log-shaped and append-only**, because a second run there cannot erase the first: the
  §Re-run rule is satisfied by construction, not skipped.

| Skill | Section | superseded | Reason if exempt |
|---|---|---|---|
| `/vision` `/scope` `/plan` `/architect` `/structure` `/design-system` `/foundation` `/contracts` `/dev-check` `/test` `/eval` | `#Vision` … `#Evaluation` | **required** | the section is rewritten in place |
| `/validate` | `#Validation` | exempt | append-only: "append a new dated entry, never overwrite" |
| `/build` | `#Build log` | exempt | append-only: one row per feature |
| `/ship` | `#Ship log` | exempt | append-only: one entry per release |
| `/learn` | `#Learnings` | exempt | append-only: one entry per cycle |
| `/tickets` | writes `docs/issues/*`, not a spine section | exempt | a re-run skips tickets that already exist; nothing in the spine to erase |
| `/drift-check` | `#Drift log` | exempt | append-only: one entry per run |

**`/design-system` is resolved as a full participant**, not an exemption. It writes `#Design`, that
section can be redone, and a redone design system that silently discards the rejected archetype loses
the most expensive thing in it. It gains `Not run`, Step 3b, Step 3c and §Re-run semantics.

### 2f. Evidence — ONE representation, settled here (#131)

An exit criterion may carry **re-runnable** evidence. There is exactly one format, and it is a single
line appended to the criterion itself:

```
- [x] Authentication works — `evidence: pnpm test:e2e → 18 passed · tests/e2e/auth.spec.ts · 2026-09-10`
```

`evidence: <command> → <result> · <artefact> · <YYYY-MM-DD>` — four fields, one line, all required.

**Why a line and not a block.** `README.md` promises `PRODUCT.md` reads top-to-bottom. A four-line
structured block per criterion taxes that promise on every page, and the spine is read far more often
than it is parsed. A line stays prose to a human and is trivially machine-readable behind a fixed
`evidence:` prefix. It also honours `VISION.md`'s no-service non-goal by construction: this is Markdown
in the repo, and re-verification is running the command it names.

**Evidence is derived, not declared.** The command and the artefact path are things the phase *did*;
they are transcribed, never invented. A criterion whose evidence cannot be stated as a command someone
else can run is not evidenced — it is asserted, and should be marked so honestly.

**Evidence is optional; a MALFORMED evidence line is not.** A criterion with no evidence line is
reported as `UNVERIFIED` and is a normal state — plenty of things are judged rather than measured. A
line that *looks* like evidence but names no command or no date is worse than none, because it stops
anyone going to look. `tools/check.py` check 15 fails it.

### 2g. The four-state verdict

Produced by `/drift-check`'s claim-to-evidence pass, per criterion:

| Verdict | Means | Separator |
|---|---|---|
| **VERIFIED** | the command was re-run and the result matches what was recorded | a measurement agrees |
| **PARTIALLY VERIFIED** | re-ran and the artefact exists, but the result differs in degree not direction, or the evidence covers only part of the claim | a measurement agrees in part |
| **UNVERIFIED** | **no measurement was taken** — no evidence line, or the command cannot run here (absent tooling, credentials, a live service) | *absence of evidence* |
| **CONTRADICTED** | **a measurement was taken and it disagrees** — the command fails, or the named artefact does not exist | *evidence of absence* |

**What separates `UNVERIFIED` from `CONTRADICTED` is whether a measurement was actually taken.** They
are routinely conflated, and conflating them is expensive in both directions: reporting a
never-attempted check as CONTRADICTED sends people chasing a phantom regression, and reporting a failed
check as UNVERIFIED hides a real one behind "we could not tell". A claim with no evidence is **always
reported**, never silently passed.

### 2h. Where this lives — the surface-cost decision (#131)

Three options were on the table: extend `/drift-check` · a `/prove` engine other skills compose · a 22nd
top-level skill. **Chosen: extend `/drift-check`**, and the ticket's instruction not to pick the third by
default is honoured.

- `/drift-check` **already owns claim-vs-reality** — its exit criteria already include *"code↔docs drift
  checked (claims that don't match reality)"*. This generalises that from scope/vision/doc drift to
  *every claim in the spine*, which is a widening of an existing remit rather than a new capability.
- It is **already the "run anytime" skill**, which is exactly when a re-verification pass is wanted.
- A 22nd top-level skill would directly contradict #116 and #123, which are about the surface already
  being intimidating. That cost is real and buys nothing here.

**This also supplies the transition guard §4 deferred.** Once evidence is re-runnable, reconciling
*intended* against *actual* at a transition is a small addition to Step 3b rather than a new subsystem —
still deferred, but no longer blocked.

### 2d. Gate types — classified by where the answer lives

Not by the user's experience level. By whether the answer is **derivable**:

| Type | The answer lives in | Skills | Batchable? |
|---|---|---|---|
| **input** | the human, and nowhere else | `/vision` `/validate` `/scope` `/plan` `/architect` `/design-system` `/learn` `/adopt` | **Never** |
| **derivation** | prior `PRODUCT.md` sections + the repo | `/structure` `/foundation` `/contracts` `/tickets` `/build` `/new-component` | Yes — one review at the end of the batch |
| **verification** | repo evidence; no preference involved | `/dev-check` `/test` `/eval` `/ship` (`/frontend-audit`\*) | Yes, and **stops on red** |

Two assignments deserve their reasoning, because they are not the audit's:

- **`/architect` is `input`, not `derivation`.** The stack looks derivable from `#Scope` and a
  current-year benchmark — but since #129 the choice is made against *the project's constraints*
  (team size, operational appetite, budget, tolerable lock-in), and those live in the human. A
  derivation-mode `/architect` would invent them.
- **`/learn` is `input`.** The metric is evidence, but *iterate or kill* is the human's call and is
  the whole output of the phase.

\* `/frontend-audit` is a verification gate by nature but carries **no `## Contract` block by design** —
its contract is `audit.py`'s exit code, not prose (this is why `check.py` check 3 exempts it). It is
therefore listed here and excluded from check 12: a declaration in a file that declares nothing else
would be the only prose contract it has, which is precisely the arrangement the exemption avoids.

**Why this is enforceable and `--auto` is not.** Gate type is a property of the gate, so it is
declared once per skill and checked in CI. A global `--auto` flag is unenforceable by construction:
it is a mode that merely *hopes* each skill behaves.

### 2e. Naming — an interview is not an approval

Stop calling input gates "confirmation". An input step **asks a question**; a verification step
**reports a result and asks whether to proceed**. Most of the felt friction is removed by describing
them honestly, at zero cost to the guarantee.

---

## 3. Considered and REJECTED: `/playbook --auto`

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

---

## 4. The transition guard — DEFERRED, with reasons

The audit's model makes **evidence reconciliation a transition guard**: every advance compares
*intended* state against *actual* repository state. Today nothing does that automatically —
`/drift-check` does intended-vs-actual but is opt-in, and Step 3c compares recorded decisions against
*other recorded decisions* (docs vs docs, not docs vs repo).

**Deferred, not rejected.** It is the largest behavioural change in the area and it is the subject of
#131, which needs a re-runnable evidence record before a guard has anything to check. Declaring the
state set and enforcing participation is worth shipping on its own and does not block it.

**Reopen trigger — now met:** #131 landed the re-runnable evidence record in §2f. The guard is now a
small addition to Step 3b rather than a new subsystem, and is the next thing to pick up here. It stays
deferred in this release only because it changes when every phase does work, and that deserves its own
run at its own gate.

---

## 5. What this does NOT do

**No engine.** A YAML state file with a transition engine would be heavier than the thing it guards,
and these skills are prompt files, not code. The value is in **declaring the set and enforcing
participation**, exactly as check 9 enforces prior gates.

**No service.** Per `VISION.md`'s recorded non-goal, machine-readable state is added *against* that
guard rail: everything here is a line of Markdown in a file in the repo.

**No second override format.** `Override <date>: <reason> — bypassed <gate>` is #128's, reused.

---

## 6. What is verified

`tools/check.py`:

- **check 12** — every phase skill declares a **Gate type** of `input` · `derivation` ·
  `verification`, and an `input` gate declares that it is **never batched**.
- **check 13** — every skill that writes a spine section declares its **State model**: the section it
  writes, and `declined` / `override` / `superseded` each either implemented or marked `n/a` **with a
  reason**. A missing declaration fails; so does an exemption with no reason.

Both were proven to fail before they passed.
