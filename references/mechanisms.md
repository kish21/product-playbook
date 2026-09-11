# MECHANISMS.md — the how, referenced by name from every skill

> Split out of `PRINCIPLES.md` at v1.29.0, which had grown to 25.8KB against the ~15KB prune rule it
> defines itself while **88% of it was mechanism, not principle**. `PRINCIPLES.md` is loaded by *every*
> skill, so its size is the largest per-session attention cost in the system. **Nothing was deleted** —
> these sections were already separable units the skills referenced by name (`§Declined runs`, `§Step 3c`,
> …), so this was a relocation. `tools/check.py` fails a dangling `§` pointer and fails either file over
> the size threshold. **This file is held to the prune rule it states:** the rule inline, at most a
> sentence of mechanism with it, and situational mechanism in `MECHANISMS-ON-DEMAND.md`, which installs
> beside it.

## §Step 3b — closing the loop (every phase that writes)


Each phase runs its own principle gate at Step 3b. Five things belong to *every* one of them, so they are
defined here rather than repeated (and forgotten) fifteen times. None is optional; the first three are
bookkeeping the skill can do and the user should not have to, the fourth is the gate itself, and the fifth
is the only part the user reads:

1. **Update the `Stage:` header** to the phase just completed, and `Last updated:` to today. A spine whose
   header names an earlier phase than its filled sections is lying about where the product is — and
   `/playbook` orients from it.
2. **Reconcile every number you just introduced against `#Vision`.** Counts, dates, thresholds and budgets
   from a later phase can quietly contradict the north star (a plan dated past the target date; a scope
   that cannot reach the target number). Compare them and **surface the contradiction — never write over
   it.** (A conflict with a *non-numeric* decision is Step 3c's job; this is the arithmetic.)
3. **Offer to commit the change — never just name it.** See §Commit the work below: suggesting a message
   and stopping leaves the phase's output uncommitted, in a repo the skill never checked for.
4. **Run the transition guard — reconcile *intended* against *actual* before the section changes state.**
   The other three compare docs against docs; this compares the spine against the repository, at the last
   moment the phase can still fix what it finds. `/drift-check` stays the deeper sweep — but it is opt-in,
   and **a gate that only runs when you remember it is not a gate.**
   - **Re-run this phase's own evidence.** For each exit criterion this run just wrote with an `evidence:`
     line, execute the command it names and check the artefact it names — `/drift-check`'s Step 0b
     §Claim-to-evidence pass, run at the transition over this phase's own claims. **No second format**:
     `docs/state-model.md` §2f's one line, here as everywhere.
   - **An untracked command or artefact is `UNVERIFIED`, not `PASS`** (`docs/state-model.md` §2f). The
     guard runs in the session that wrote the line, where a throwaway script still resolves; commit the
     script, or report the criterion as judged rather than measured.
   - **Classify each with `docs/state-model.md` §2g's four verdicts** and say which. **`UNVERIFIED` never
     blocks a phase** — no evidence line, or a command that cannot run *here* (absent tooling, credentials,
     a live service), and the phase still completes. Never call that CONTRADICTED, which means a
     measurement was taken and disagreed: the two send people to different places.
   - **Check the transition is legal** against `docs/state-model.md` §2b — the state the section was in,
     and the one this run leaves it in. (The illegal one, `filled ──▶ declined`, comes from a *declining*
     run, which never reaches Step 3b; it is refused where it happens, in §Declined runs.)
   - **Report, never silently pass.** Every criterion gets a verdict, the unevidenced ones included: green
     over something nobody measured spends the user's trust on a box that was never checked.
5. **Close in plain language — see §Plain-language close.** Everything above is bookkeeping the user did
   not ask for; the run is not finished until they have been told what happened and what *they* do next,
   without playbook dialect.

## §Commit the work — a phase that writes offers to commit it


A phase that only *suggests* a commit message leaves its own output uncommitted, and says nothing at all
when there is no repository to commit to. Every phase that writes ends with these four, in order:

1. **Check the repo exists.** No `.git` → say so and offer `git init` once. **Never create a remote**, and
   never push to one the user has not named.
2. **Name the branch you are on.** A phase writing straight to `main`/`master` says so and offers a branch;
   the user may decline, and that is their call to make knowingly.
3. **Offer the commit, message included** — one line, in the repo's existing convention, built from the
   run's own summary (`docs: lock Scope in PRODUCT.md (core feature, deferred + triggers, non-goals)`).
   **Offer, then do it on a yes.** Suggest-and-stop is what left three phases behaving three different
   ways and a project with zero commits after two full phases.
4. **Push only if a remote exists and the user says so.** No remote → state that the work is committed
   locally and stop. Never `git push` unasked, and never `--force` anything. The secrets rule still holds:
   `PRINCIPLES.md` §Secrets never get pushed.

## §Plain-language close — what just happened, and what YOU do next


`PRINCIPLES.md` demands plain, non-technical language and nothing implemented it: runs ended in playbook
dialect — gates, states, verdicts, confidence scores. Two short blocks close every phase, after the
bookkeeping and before the handoff:

- **What just happened** — two or three sentences. No skill names, no `#Section` references, no state
  vocabulary. What the product now has that it did not have an hour ago.
- **What YOU do next** — the user's own actions, numbered, with dates where the work is time-bound
  (*"run 3 dinners with real bills by 2026-09-24"*). **Real-world homework belongs here and nowhere
  else** — a phase can hand back a two-week experiment, and prose under a confidence score is not a place
  a person can find it again. If there is nothing for them to do, say **"Nothing — you're done; run
  `/<next phase>` when you're ready"**, which is also a complete answer.

The agent's own next step is *not* this list. Anything the skill will do itself belongs in the handoff.

## §Re-run semantics — a second run must not erase the first


**Trigger:** the section is **not empty**. Then: **show what is about to change and ask before replacing
it**, and **date a reversal rather than erasing it** — the superseded ADR / scope item / metric stays with
a `superseded <date>: <why>` line, including a recommendation the user reversed *inside* one run.
Log-shaped sections (`#Validation`, `#Build log`, `#Drift log`, `#Ship log`, `#Learnings`) always append.
**Before overwriting anything, open `MECHANISMS-ON-DEMAND.md` §Re-run semantics (full)** — the exact
forms, the within-run trigger, and the one case that may replace wholesale.

## §Declined runs — a phase that stops still leaves a trace


**Trigger:** this phase is **stopping without filling its section**. A stop that leaves the repo
byte-identical is indistinguishable from never having run, so it records one dated line at the top of its
own section, nothing else touched:

`_Not run <date>: <what was missing> — run <the phase(s) that fill it> first._`

A *deliberate* skip or a bypassed gate instead reads `Override <date>: <reason> — bypassed <gate>`, counts
as filled, and needs all three of gate · the user's own words · date. The scaffold always stays intact, and
`filled ──▶ declined` is refused. **Before writing either line, open `MECHANISMS-ON-DEMAND.md`
§Declined runs (full)** — which of the two applies, what it does to `/playbook`'s routing, and the
already-filled case.

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
doc↔code drift *created by the playbook itself*. So before any phase that writes closes its gate:

1. **Compare** the artefacts + spine section this phase just wrote against the decisions already recorded
   in earlier sections — ADRs, **tool choices**, the stack, scope items and non-goals, budgets, contracts,
   `DESIGN.md` tokens. Each skill names its own comparison set in its `## Step 3c`.
2. **On a conflict, name both sides explicitly** — "`#Architecture` records **lefthook**; this phase
   scaffolded `.pre-commit-config.yaml`" — and **ask which one wins**. Never resolve it silently.
3. **Update the loser.** Either fix the artefact, or amend the earlier section with a dated
   `superseded by <phase>, <date> — <reason>` line. A contradiction is **never left standing in two
   places**: a reversal is fine, an *unrecorded* reversal is the bug.
4. **Carry the OPEN decisions forward.** A decision an earlier section records as still open is not a
   contradiction — it is an *absence*, which a collision check cannot see. List every one still open in the
   sections you read, and either resolve it here or restate it in what you write. Carried by hand, it is
   dropped by hand.

**Not a contradiction** (don't cry wolf): a phase that merely *adds detail* to an earlier decision
(`#Architecture` says "Postgres", `/contracts` picks the column types), or fills in something the earlier
section marked N/A. Only a claim that cannot be true at the same time as a recorded one counts. This is a
pre-gate check *inside* each phase — it does not replace `/drift-check`'s cross-cutting sweep.

## §Spine resolution — what "`PRODUCT.md`" means (greenfield · brownfield · code-only)


`PRODUCT.md` is the spine for products *born* in this playbook. Every skill resolves the spine
**`PRODUCT.md`-first**: it exists → it *is* the spine, and that is the whole rule for a greenfield
playbook project.

**No `PRODUCT.md`?** The project is brownfield (resolve the spine from its own docs, and say which file
you resolved) or code-only (infer a **low-confidence, explicitly INFERRED** picture and **never grade
against a self-guessed baseline**). Both cases, and how a *writing* phase degrades gracefully, are in
`MECHANISMS-ON-DEMAND.md` §Spine resolution (full) — **open it before resolving a spine from anything but
`PRODUCT.md`.**

---

## §Lane mode — when several agents build one repo (Lanekeeper)


**Trigger:** the project has `.lanekeeper/config.yaml` or a root `lanes.yaml` (the policy), or the current
worktree has a `.lane` file (this session IS one agent's seat). Either → **lane mode**, and the four rules
in `MECHANISMS-ON-DEMAND.md` §Lane mode (full) apply to every phase — **open it before writing anything in
a lane.** They fix, in one place: the ticket's file list *is* the lane, a lane is a feature slice and never
a technology layer, the spine gets exactly one writer, and the label form is `lane: <name>` with a space,
on both the issue and the PR.

**Outside lane mode nothing above applies** and every skill behaves as before.

---
