# STATE-MODEL.md — the states a phase can be in, the moves between them, and where they are recorded

**Read by** every skill that records a phase's state (§2c) and by `/playbook` when it orients. The rules are
below; the reasoning and history behind them are in `references/case-files-principles.md`
§The state model's history.

### 2a. The state set

Each phase is in exactly one of these, recorded in `STATUS.md` (§2h). Nothing else is a state.

| State | Written as | Counts as filled? | Frontier logic treats it as |
|---|---|---|---|
| **empty** | the phase has not run (`status.py init` writes every phase empty) | no | **empty** — this is the frontier |
| **declined** | `status.py set <phase> declined --reason <what was missing> --gate <phase to run first>` | no | **empty**, but names the earlier attempt instead of proposing blind |
| **filled** | `status.py set <phase> filled` — after the phase's required fields in `PRODUCT.md` are non-empty and evidenced | yes | done |
| **running** | `status.py set <phase> running --due <date> --reason <what is being measured>` + the section's fields filled in `PRODUCT.md`, `PENDING` where the result goes | **no** — the gate is open | **not the frontier, and not done**: the work started and finishes later |
| **overridden** | `status.py set <phase> overridden --reason <the user's words> --gate <the gate bypassed>` | **yes** — the phase is not still owed | done, **and surfaced every time a later phase orients** |
| **superseded** | `superseded <date>: <why>` beside the old entry | n/a — a property of an *entry*, not a section | unchanged |

**`/validate` is optional** (owner, 2026-09-30): an `empty` `#Validation` is normal — it never blocks, is never
the next phase by itself, and no later phase warns about it. Only an experiment the user started (`running`)
gates the phases after it, as below.

**`running` is for work that has genuinely started and cannot finish today** — a two-week
Wizard-of-Oz experiment, a pre-sale, a measurement that needs real users. It is **full of text with its
gate still open**, the one case the four-state model could not express: a later reader saw content and
had no way to tell whether to wave it through. It was improvised, well and identically, in two separate
runs before it was defined here.

**What a downstream phase does with a `running` section — the third option.** The honest menu used to be
*wait a fortnight* or *override forever*, and the experiment ladder itself prices the serious rungs at
1–2 weeks, so the override wins every time: **a gate whose honest path is unusable gets routed around**,
which is the silent skip this playbook exists to prevent. So:

- **Phase 1 document phases (`/scope`, `/plan`) treat a `running` gate as ADVISORY.** Proceed
  **provisionally**, mark what depends on the pending result, and say so. They produce documents, not
  code — blocking them buys little.
- **From `/architect` onward it BLOCKS**, like any unmet gate, and needs a real override to pass.
  **One override carries** to every later phase until that gate is filled or its due date passes:
  the owner answers once, and `status.py next` shows it on every run (`proceeding under the override`).
  Blocking `/build` on an untested behavioural assumption buys a great deal.
- **Proceeding provisionally is not an override.** It expects a result, it is due-dated, and the mark
  **clears when the result lands** rather than only by a new experiment. If the experiment fails, the
  provisional work is revisited — `/validate`'s pivot/kill path already says how.
- **An overdue `running` section is a drift finding** (`/drift-check`): past its due date with no result
  is a stalled gate, and nothing was emitting it.

**A verification gate is passed only by a `pass` verdict.** `/dev-check`, `/test` and `/eval` set their phase
filled with `--verdict pass` or `--verdict fail`; a filled phase whose verdict is `fail` (or was never recorded)
stays the next phase — a written section is not a passed gate. **`#build` is done only when every ticket of the
current milestone in `TICKETS.md` has a row** (`status.py ticket`); until then `status.py next` names the
tickets not yet recorded. *(Added 2026-09-24: a logged test run's spine read FAIL at #Dev-complete with 5 of 19
tickets unbuilt, and the section-is-written rule still routed it to `/test`.)*

**No state is terminal.** Every one can be re-entered by a re-run; that is the point of §Re-run
semantics. `superseded` is deliberately not a section state — a section holding a superseded ADR is
still `filled`, and treating it otherwise would make every reversal look like regression.

### 2b. The legal transitions

`status.py set` refuses every move not listed here, and says why (§2h).

```
empty ──▶ filled          a normal run
empty ──▶ running         the work started and finishes later (a timeboxed experiment, a measurement)
running ──▶ filled        the result landed; PENDING fields are replaced and the gate closes
running ──▶ running       a re-run that extends or re-scopes the experiment, dated
running ──▶ overridden    the user chose to proceed without waiting for the result
empty ──▶ declined        the prior gate was unmet and the run stopped (§Declined runs)
empty ──▶ overridden      the prior gate was unmet and the user chose to proceed (#128)
declined ──▶ declined     a later attempt also stopped; the Not-run note is REPLACED with the new one
declined ──▶ filled       the missing phase ran; the Not-run line is REPLACED, never appended to
declined ──▶ overridden   the user chose to proceed without it
filled ──▶ filled         a re-run: show what changes, ask first, date what it reverses
overridden ──▶ filled     the skipped phase was run after all
```

**`running ──▶ filled` needs the result.** `status.py` refuses it without `--note` (the measured result
against the bar), and refuses it while the phase's `PRODUCT.md` section still reads `PENDING`. A phase that
writes its fields and reaches Step 3b while its experiment runs leaves the state `running`; marking it
`filled` there would erase the due date and the provisional mark with no result behind it.

**`filled ──▶ running` is illegal**, for the same reason as the line below: a closed gate does not
re-open into "still measuring". A new experiment over a filled section is `filled ──▶ filled` through
§Re-run semantics, which keeps the first result rather than replacing it with a pending one.

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
| `/build` | a `STATUS.md` ticket row | exempt | append-only: one row per ticket |
| `/ship` | a `STATUS.md` release row | exempt | append-only: one row per release |
| `/learn` | `#Learnings` | exempt | append-only: one entry per cycle |
| `/tickets` | writes `TICKETS.md` + `docs/issues/*`, not a spine section | exempt | a re-run skips tickets that already exist; nothing in the spine to erase |
| `/drift-check` | a `STATUS.md` drift row | exempt | append-only: one row per finding |

**`/design-system` is resolved as a full participant**, not an exemption. It writes `#Design`, that
section can be redone, and a redone design system that silently discards the rejected archetype loses
the most expensive thing in it. It gains `Not run`, Step 3b, Step 3c and §Re-run semantics.

### 2d. Gate types — classified by where the answer lives

Not by the user's experience level. By whether the answer is **derivable**:

| Type | The answer lives in | Skills | Batchable? |
|---|---|---|---|
| **input** | the human, and nowhere else | `/vision` `/validate` `/scope` `/plan` `/architect` `/design-system` `/learn` `/adopt` | **Never** |
| **derivation** | prior `PRODUCT.md` sections + the repo | `/structure` `/foundation` `/contracts` `/tickets` `/build` `/new-component` | Yes — one review at the end of the batch |
| **verification** | repo evidence; no preference involved | `/dev-check` `/test` `/eval` `/ship` (`/frontend-audit`\*) | Yes, and **stops on red** |

**Where the batch offer lives (record test):** `MECHANISMS-ON-DEMAND.md` §Batch mode is the mechanism;
`/playbook` Step 2 and the `/structure` + `/design-system` handoffs make the offer; check 27 holds all four
to it. Until 2026-09-13 this table was the only place batching existed (#204). **Chain** is defined in the
same section: an `input` phase followed by its derivation phase (`/architect` → `/structure`) in one
session with every input question kept — offered at `/architect` Step 0, never the default (#205).

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

### 2f. Evidence — ONE representation, settled here (#131)

An exit criterion may carry **re-runnable** evidence. There is exactly one format, and it is a single
line appended to the criterion itself:

```
- [x] Authentication works — `evidence: pnpm test:e2e → 18 passed · tests/e2e/auth.spec.ts · 2026-09-10`
```

`evidence: <command> → <result> · <artefact> · <YYYY-MM-DD>` — four fields, one line, all required. Spelled exactly
so: an arrow `→` (or `->`) after the command, a middle dot `·` between the other fields.

**Why a line and not a block.** `README.md` promises `PRODUCT.md` reads top-to-bottom. A four-line
structured block per criterion taxes that promise on every page, and the spine is read far more often
than it is parsed. A line stays prose to a human and is trivially machine-readable behind a fixed
`evidence:` prefix. It also honours `VISION.md`'s no-service non-goal by construction: this is Markdown
in the repo, and re-verification is running the command it names.

**Evidence is derived, not declared.** The command and the artefact path are things the phase *did*;
they are transcribed, never invented. A criterion whose evidence cannot be stated as a command someone
else can run is not evidenced — it is asserted, and should be marked so honestly.

**The command must SURVIVE the session that wrote it.** Evidence that names a throwaway script is a
claim with a receipt that no longer exists: on a real run a phase reported *"PASS — mechanically verified
— `verify_map.py`"*, and that file was in neither the tree nor git history. The claim happened to be
true; the proof was gone, and the transition guard could not tell, because it runs **inside the session
that created the temp file**, where the path still resolves. So: **a command or artefact that is not
committed is `UNVERIFIED`, never `PASS`** — and a verification script worth citing is worth committing
(`scripts/`), which costs one `git add` and makes every later re-run possible.

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

### 2h. Where status lives — `STATUS.md`, written only by `status.py`

A project's status — each phase's state (§2a), the open items, the ticket, release and drift rows — is written
**only by `status.py`**; a run never edits it by hand. **`STATUS.md`** at the project root holds the flags and the
phase table. **Each open item, ticket, release and drift row is one small file under `status/`** (`status/open/`,
`status/tickets/`, `status/releases/`, `status/drift/`), so 2–10 workers on separate branches add separate files
and never edit the same line, and a lock makes runs in one folder take turns. Nothing that changes on every
command is stored (the date, the stage, the next phase); `/build` and `/ship` count as filled once a ticket or
release file exists. **`status.py show` prints all of it on one screen.** Open items have short ids (`o7k2`) that
two branches cannot both pick; a project's older STATUS.md moves its rows into these files on its first write.
`PRODUCT.md` holds the product's content: the sections, their fields, their `evidence:` lines (§2f), and an
override of ONE criterion inside a section (it is part of that section's record; `status.py` tracks it as an
open item).

**Which command records what:** `status.py how` prints it — the tool is the one home for its
commands (`MECHANISMS.md` §Status). Every command is also in `status.py`'s own `--help`.

**Each phase row records the rules it was written under** (the `Rules` column: the playbook version at `set
filled`). `status.py` holds a short table of rule changes that alter what a filled phase would have produced;
`next` names each change newer than a row's version (or every one, for a row with no version) and the phase
to re-run, or how to keep it (`set <phase> filled --note "kept: <reason>"`). A project that updates the
playbook mid-way is told, instead of never knowing an earlier phase skipped a question that now exists.

**A row is a record.** Each field has a length limit; a longer value is refused with the file to put the detail
in (the feature doc, the release notes). **Nothing is lost by `migrate`**: every line it removes from
`PRODUCT.md` goes verbatim to `docs/status-archive.md`, and it refuses to write if a line would go missing.

**Superseded 2026-09-24:** *"No engine. A YAML state file with a transition engine would be heavier than the
thing it guards"* (v1.31.0). Reversed for status only, on measurement from a logged test run: runs searched
`PRODUCT.md` 5–30 times each to find their place; the `Stage:` header grew into a 700-character paragraph;
`#Build log` grew to 35% of the file although its rule said one row per feature; and nothing but the model's
memory refused an illegal move. A script refuses; prose cannot. Still no service: a Python file and a Markdown
file in the repo, readable without the script.

## 3. Rejected: `/playbook --auto`

An auto mode would let the AI author the product premise (input gates have no derivable answer), would turn
the per-phase stops that bound a session's cost into one long session, and the escape hatch already exists
(every skill runs standalone). **Reopening it must be a deliberate reversal with the reasoning recorded.**
Full reasoning: `references/case-files-principles.md` §The state model's history.
