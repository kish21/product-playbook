# MECHANISMS.md — the how, referenced by name from every skill

> Split out of `PRINCIPLES.md` at v1.29.0. `PRINCIPLES.md` had grown to 25.8KB against the ~15KB
> prune rule it defines itself, and **88% of it was mechanism, not principle** — the 5-step spine
> everyone quotes was 7 lines out of 310. `PRINCIPLES.md` is loaded by *every* skill, so its size is
> the largest per-session attention cost in the system, and the stated rationale ("a checklist of
> sharp one-liners gets followed; a wall of war stories gets skimmed") applies harder to it than to
> anything it governs.
>
> **Nothing was deleted.** These sections were already pre-declared separable units — the skills have
> always referenced them by name (`§Declined runs`, `§Step 3c`, …) — so this is a relocation, and every
> pointer now names this file. `tools/check.py` fails a dangling `§` pointer and fails either file over
> the size threshold.

## §Step 3b — closing the loop (every phase that writes)


Each phase runs its own principle gate at Step 3b. Four things belong to *every* one of them, so they
are defined here rather than repeated (and forgotten) fifteen times. None is optional; the first three are
bookkeeping the skill can do and the user should not have to, and the fourth is the gate itself:

1. **Update the `Stage:` header** to the phase just completed, and `Last updated:` to today. A spine whose
   header names an earlier phase than its filled sections is lying about where the product is — and
   `/playbook` orients from it.
2. **Reconcile every number you just introduced against `#Vision`.** Counts, dates, thresholds and budgets
   introduced by a later phase can quietly contradict the north star (a plan dated past the target date; a
   scope that cannot reach the target number). Compare them and **surface the contradiction — never write
   over it.** (A conflict with a *non-numeric* decision is Step 3c's job; this is the arithmetic.)
3. **Suggest a one-line commit message**, in the repo's existing convention, for the change you just made
   — e.g. `docs: lock Scope in PRODUCT.md (core feature, deferred + triggers, non-goals)`. The run's own
   summary is the best source for it; leaving the user to invent one wastes the context you already have.
4. **Run the transition guard — reconcile *intended* against *actual* before the section changes state.**
   The other three compare docs against docs; this compares the spine against the repository, at the last
   moment the phase can still fix what it finds. `/drift-check` stays the deeper sweep — but it is opt-in,
   and **a gate that only runs when you remember it is not a gate.**
   - **Re-run this phase's own evidence.** For each exit criterion this run just wrote with an `evidence:`
     line, execute the command it names and check the artefact it names — `/drift-check`'s Step 0b
     §Claim-to-evidence pass, not duplicated, just run at the transition over this phase's own claims.
     **No second format**: `docs/state-model.md` §2f's one line, here as everywhere.
   - **Classify each with `docs/state-model.md` §2g's four verdicts** and say which. **`UNVERIFIED` never blocks a phase** — no
     evidence line, or a command that cannot run *here* (absent tooling, credentials, a live service), and
     the phase still completes. Never call that CONTRADICTED, which means a measurement was taken and
     disagreed: absence of evidence is not evidence of absence, and the two send people to different places.
   - **Check the transition is legal** against `docs/state-model.md` §2b — the state the section was in, and the one this run
     leaves it in. (The illegal one, `filled ──▶ declined`, comes from a *declining* run, which never
     reaches Step 3b; it is refused where it happens, in §Declined runs.)
   - **Report, never silently pass.** Every criterion gets a verdict, the unevidenced ones included: green
     over something nobody measured spends the user's trust on a box that was never checked.

## §Re-run semantics — a second run must not erase the first


Re-running a phase is not an edge case: a pivot, a changed constraint, or simply a redo. What gets lost is
the most expensive thing in the section to reconstruct — **why the other option was rejected.**

- **A run over a *non-empty* section shows what is about to change and asks before replacing it.** Never a
  silent overwrite. A first run over an empty section is unchanged — no extra prompting.
- **A reversed decision is dated, not erased.** The superseded ADR / scope item / metric stays, with a
  `superseded <date>: <why>` line beside it. This is the same record Step 3c writes when it resolves a
  contradiction, and it is what makes a reversal auditable instead of invisible.
- **Log-shaped sections keep appending** — `#Validation`, `#Build log`, `#Drift log`, `#Ship log`,
  `#Learnings`. `/validate`'s "append a new dated entry, never overwrite" is the general case, not a local
  exception.
- **A true restart may replace wholesale** — but only as an explicit, recorded choice.

## §Declined runs — a phase that stops still leaves a trace


§Re-run semantics governs a phase *rewriting* its section. This governs a phase **declining to write
one**. A skill that correctly stops at an unmet prior gate leaves the repo byte-identical — so from the
repo alone, *"I ran `/eval` and it correctly declined"* is indistinguishable from *"I never ran
`/eval`"*. The user cannot tell, the next session cannot tell, and `/playbook` — which orients purely
by which sections are filled — keeps proposing the same phase with no memory that it was already
attempted and declined for a good reason.

**A phase that declines to run records that it declined.** One dated line at the top of its own
section, in this form, with nothing else in the section touched:

`_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._`

- **The scaffold stays intact and visibly unfilled.** Blanking or half-filling the fields is the
  §Re-run failure wearing new clothes: the note is orientation, not content.
- **It does not count as the section being filled.** `/playbook`, `/drift-check` and the next session
  still route to the missing phase — the note only tells them the detour was already noticed, so they
  can say *"attempted <date>, declined because X"* instead of proposing it blind.
- **One line, replaced on the next attempt — never appended.** An append-only log of every early
  invocation is noise, and noise trains people to skip the line that mattered.
- **Only a *declined* run writes it.** A phase that runs to completion writes its section normally; a
  phase nobody invoked writes nothing. This line means exactly *"attempted, and stopped for a reason"*.
- **Only an *unfilled* section can take it — `filled ──▶ declined` is refused** (`docs/state-model.md` §2b:
  a phase that ran does not un-run). A stop over an **already filled** section leaves it exactly as it is and
  says so; a filled section that needs redoing goes `filled ──▶ filled` through §Re-run semantics. The
  Not-run line over real content would destroy the phase's output *and* route `/playbook` back to a phase
  that is not owed.

**A deliberate skip is the same rule's other shape.** Where a phase is not merely *early* but is being
**skipped on purpose** — `/validate`'s untested assumption, `/ship`'s skipped phases — or where a prior
gate is **bypassed on unmet criteria**, the line reads `Override <date>: <reason> — bypassed <gate>`, it
*does* count as filled, and later phases surface it every time they orient. Three things are required and
none is optional: **which gate** was bypassed, **a reason in the user's own words** (not the agent's
paraphrase, and not "user said continue"), and **the date**. A verbal "yes, continue" that reaches no
file turns a gated workflow into an advisory one — the bypass is the strictly more consequential event and
was, until v1.28.0, the only one of the two that left nothing behind. Both are dated, both are one line, both keep the scaffold; they differ only in whether the
phase is still owed. `/validate`'s override rule is this rule's specific case, not a separate one.

## §Seam — who owns the dependency manifest


Two phases can both plausibly claim it, so the split is fixed here and stated identically in both skills:

- **`/structure` owns its existence and shape** — the file itself, the dev/prod split, project metadata. The
  dependency lists may be empty or minimal.
- **`/foundation` owns its contents and provability** — pinned versions, the actual install, the tool config
  files those scripts reference, and the first run that genuinely passes.
- **`/structure` may not leave a script that cannot run at the end of its own phase** without marking it as
  arriving with `/foundation`. A phase that reports green while `make check` fails has reported a lie.

## §Step 3c — the contradiction check (every phase that writes)


Step 0 checks the *previous* phase's gate; Step 3b checks *this* phase's own criteria. Neither asks the
question that matters most: **does what I just produced contradict a decision that is already recorded?**
A phase can satisfy every box on its own list and still silently overrule an ADR made one phase earlier —
that is doc↔code drift *created by the playbook itself*, and creating it is worse than missing it. So
before any phase that writes closes its gate:

1. **Compare** the artefacts + spine section this phase just wrote against the decisions already recorded
   in earlier sections — ADRs, **tool choices**, the stack, scope items and non-goals, budgets, contracts,
   `DESIGN.md` tokens. Each skill names its own comparison set in its `## Step 3c`.
2. **On a conflict, name both sides explicitly** — "`#Architecture` records **lefthook**; this phase
   scaffolded `.pre-commit-config.yaml`" — and **ask which one wins**. Never resolve it silently.
3. **Update the loser.** Either fix the artefact, or amend the earlier section with a dated
   `superseded by <phase>, <date> — <reason>` line. A contradiction is **never left standing in two
   places**: a reversal is fine, an *unrecorded* reversal is the bug.

**Not a contradiction** (don't cry wolf): a phase that merely *adds detail* to an earlier decision
(`#Architecture` says "Postgres", `/contracts` picks the column types), or fills in something the earlier
section marked N/A. Only a claim that cannot be true at the same time as a recorded one counts. This is a
pre-gate check *inside* each phase — it does not replace `/drift-check`'s cross-cutting sweep.

## §Spine resolution — what "`PRODUCT.md`" means (greenfield · brownfield · code-only)


`PRODUCT.md` is the spine for products *born* in this playbook. Every skill must resolve the
spine **flexibly and `PRODUCT.md`-first**, so a greenfield playbook project is never affected:

1. **`PRODUCT.md` exists** → it *is* the spine. (default — unchanged behaviour)
2. **No `PRODUCT.md`, but the project has docs** → resolve the spine from the project's own
   docs, in order: `CLAUDE.md` → `README.md` → `docs/` → `AGENTS.md`. Map sections *loosely*
   (Vision ≈ the "what/why"; Scope/Non-goals ≈ an out-of-scope / "not doing" list; Build log ≈
   a build-state / `CHANGELOG`). **State which file you resolved as the spine.** Never fabricate
   a section that isn't there.
3. **Code only, no spine doc at all** → infer a **low-confidence** picture from the code +
   package metadata (`package.json`, `pyproject.toml`, manifest, entry points, routes). **Label
   it "INFERRED"** and say plainly what *cannot* be judged without recorded intent (e.g. true
   scope/vision drift). **Never grade against a self-guessed baseline** (no-assumptions /
   honesty). Recommend bootstrapping a real spine — **`/adopt`** is the direct route (it drafts the spine from
   this same evidence and has the owner confirm it); `/vision`+`/scope` suits a project that is really
   starting over.

A skill that *writes* a section degrades gracefully when there's no `PRODUCT.md`: prefer
reporting to the user (and offering to create/append a spine) over forcing a `PRODUCT.md` the
project never opted into. A skill that *creates* `PRODUCT.md` by design (e.g. `/vision`) keeps
doing so.

---

## §Lane mode — when several agents build one repo (Lanekeeper)


**Detection:** the project has `.lanekeeper/config.yaml` or a root `lanes.yaml` (the policy), or
the current worktree has a `.lane` file (this session IS one agent's seat). Either → **lane mode**.
The companion tool is [Lanekeeper](https://github.com/kish21/parallel-agents): *product-playbook
writes the work down; Lanekeeper divides it up and gates every PR to its lane.* Four rules that
every phase skill honours in lane mode — defined once here, referenced by the skills:

1. **The ticket's file list IS the lane.** Lanekeeper reads the `Target Files` / `Allowed File
   Paths` section of the issue as the boundary, and a `Lane` heading as the feature name. A ticket
   with no files has no safety guarantee; a ticket that lists a *folder* has a boundary too wide to
   protect anyone. Exact paths, always — and the paths a ticket names must include **everything the
   build will write**, feature doc included.
2. **A lane is a feature slice, never a technology layer.** Vertical tickets are lanes by
   construction. A horizontal (per-layer) ticket turns one feature into N lanes and makes every
   change a collision — in lane mode the default is vertical, and horizontal needs a recorded reason.
3. **The spine is a shared file — it gets ONE writer.** `PRODUCT.md`, `CHANGELOG.md`, `STRUCTURE.md`
   and the policy files sit outside every lane; a lane PR that touches them fails the gate (or
   merge-conflicts with every other lane). Inside a lane, a skill writes only lane-owned files
   (`docs/features/<feature>.md`); the spine rows are **reconciled by the integrating session** on the
   base branch (`/dev-check` for the Build log, `/ship` for the Ship log + CHANGELOG). The alternative —
   a declared `shared:` zone for the spine with `merge=union` — is the user's explicit choice, never a
   default.
4. **The PR carries its lane — and so does the issue.** The label form is **`lane: <name>`, with a space**,
   on **both** the issue (`/tickets` applies it at publish) and the PR. One spelling, stated here, because
   Lanekeeper's gate fails closed without exactly one label and therefore cannot move: a second spelling
   (`lane:auth`) would split filtering in half and risk the gate not seeing what issues carry.
   Every lane PR is labelled `lane: <name>` and passes `lanekeeper check`
   before it is opened; the gate fails closed without exactly one label. Lanekeeper owns the
   **PR template** and the gate workflow; product-playbook owns the **issue template**. Neither
   overwrites the other's file.

Outside lane mode nothing above applies and every skill behaves as before.

---

