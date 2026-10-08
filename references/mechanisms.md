# MECHANISMS.md — the how, referenced by name from every skill

> The mechanisms every skill references by name (`§Declined runs`, `§Step 3c`, …). The rule sits inline
> with at most a sentence of mechanism; situational mechanism lives in `MECHANISMS-ON-DEMAND.md`, which
> installs beside it: `mechanisms-on-demand.md` in the plugin or a clone, `MECHANISMS-ON-DEMAND.md` in a
> copy install. `STATE-MODEL.md`, cited below, is `../docs/state-model.md` in the plugin or a clone and
> `STATE-MODEL.md` beside this file in a copy install.

## §Step 3b — closing the loop (every phase that writes)


Each phase runs its own principle gate at Step 3b. Five things belong to *every* one of them, defined here
once. None is optional: three are bookkeeping the user should not have to do, the fourth is the gate itself,
and the fifth is the only part the user reads:

1. **Record the phase's state** — `status.py set <phase> filled` (§Status; a verification phase adds
   `--verdict pass|fail`). `STATUS.md` is what `/playbook` and the next run orient from: a phase that
   completes without recording it sends the next run back here.
2. **Reconcile every number you just introduced against `#Vision`.** Counts, dates, thresholds and budgets
   from a later phase can quietly contradict the north star (a plan dated past the target date; a scope
   that cannot reach the target number). Compare them and **surface the contradiction — never write over
   it.** (A conflict with a *non-numeric* decision is Step 3c's job; this is the arithmetic.)
3. **Offer to commit the change — never just name it.** See §Commit the work below: suggesting a message
   and stopping leaves the phase's output uncommitted, in a repo the skill never checked for.
4. **Run the transition guard — reconcile *intended* against *actual*:** the spine against the repository,
   after item 1 and while the phase can still fix what it finds (a fix re-runs `set`). Order: 1, 2, 3c, 3, 4, 5.
   - **Re-run this phase's own evidence.** Each `evidence:` line this run wrote: run its command, check its
     artefact (`/drift-check`'s Step 0b §Claim-to-evidence pass); a phase whose gate records its runs
     (`/build`'s gate.py) cites that record, re-running only what changed. **No second format**:
     `STATE-MODEL.md` §2f's one line, here as everywhere.
   - **An untracked command or artefact is `UNVERIFIED`, not `PASS`** (`STATE-MODEL.md` §2f). The
     guard runs in the session that wrote the line, where a throwaway script still resolves; commit the
     script, or report the criterion as judged rather than measured.
   - **Classify each with `STATE-MODEL.md` §2g's four verdicts** and say which: `VERIFIED` only when a
     command run in this run tests *that* criterion and agreed (a link is not a command); a criterion you judged, or one about wording or quality (plain, clear, explained), is `UNVERIFIED (judged)`. **`UNVERIFIED` never
     blocks a phase** — no evidence line, or a command that cannot run *here* (absent tooling, credentials,
     a live service), and the phase completes. Never call that CONTRADICTED, which means a
     measurement was taken and disagreed.
   - **Check the transition is legal** against `STATE-MODEL.md` §2b — the state the section was in,
     and the one this run leaves it in.
   - **Report, never silently pass.** Every criterion gets a verdict, the unevidenced ones included.
5. **Close in plain language — see §Plain-language close.** Everything above is bookkeeping the user did
   not ask for; the run is not finished until they have been told what happened and what *they* do next,
   without playbook dialect.

## §Status — the one way to record where the product stands


Where the product stands is `STATUS.md`, written **only** by `status.py` (`STATE-MODEL.md` §2h) — from this
file's folder: `../tools/status.py` in the plugin or a clone, `status.py` beside this file in a copy install.
Run it from the project root: `python <that path> <command>`. **Never edit `STATUS.md` by hand, and never write
a state line (`Stage:`, `Not run`, `Override`, `Running`) into `PRODUCT.md`.** Step 0 runs `status.py next`
and reports what it lists; Step 3b runs `status.py set <phase> filled` (`/dev-check`, `/test`, `/eval` add
`--verdict pass|fail`). **Any other moment: run `status.py how`** — it prints which command records what.
A refusal says what to do instead — never edit the file around it.
**`next` prints first `Playbook <version> · rule files in <folder>`**; rules you opened from another folder →
**stop**: two copies are installed — tell the user to start the skill labelled `[product-playbook <version>]`.

## §Commit the work — a phase that writes offers to commit it


A phase that only *suggests* a commit message leaves its own output uncommitted, and says nothing at all
when there is no repository to commit to. Every phase that writes ends with these four, in order:

1. **Check the repo is THIS project's — not merely that a repo exists.** Run `git rev-parse
   --show-toplevel` and compare it to the project directory. Git resolves *upward*: an accidentally
   `git init`-ed home directory answers for every folder beneath it, and "is there a repo?" then commits
   `PRODUCT.md` into `~` beside dotfiles and credentials.
   - **Root == the project directory** → normal path, proceed.
   - **Root is a PARENT directory** → **STOP. Do not commit.** Name both paths (`this project:
     <dir>` · `git root: <root>`) and offer exactly two ways forward: `git init` here so the project owns
     its own repo, or an explicit instruction from the user to commit into the outer repo. A monorepo is
     the legitimate case and it is **the user's call, recorded once** (a line under `#Project policy`:
     `- **commits into:** <root> — <reason, the user's words> (<date>)`), never re-inferred by the next phase from the fact that
     `git rev-parse` answered.
   - **No repo anywhere** → say so and offer `git init` once.

   **Never create a remote**, and never push to one the user has not named.
2. **Name the branch AND the repository root you are on.** A phase writing straight to `main`/`master`
   says so and offers a branch; the user may decline, and that is their call to make knowingly.
   Naming the root is what lets a human see a commit landing in the wrong repository.
3. **Offer the commit in plain words:** ask *"Save this version of your project? (yes / no)"*; the branch,
   root, files and message (one line, the repo's own convention, built from the run's summary) go under it,
   marked as the details.
   **Offer, then do it on a yes.** Suggest-and-stop is what left three phases behaving three different
   ways and a project with zero commits after two full phases. Commit with `git add <files>`, then
   `git commit -m "<one line>"`: every shell, never a heredoc.
4. **Push only if a remote exists and the user says so.** No remote → state that the work is committed
   locally and stop. Never `git push` unasked, and never `--force` anything. The secrets rule still holds:
   `PRINCIPLES.md` §Secrets never get pushed.

## §Plain-language close — what just happened, and what YOU do next


Four blocks close every phase, in this order, each under its bolded name — **printed first**, before the
transition-guard table and the confidence score (the user meets their own language before the dialect):

- **What just happened** — two or three sentences. No skill names, no `#Section` references, no state
  vocabulary. What the product now has that it did not have an hour ago.
- **What I skipped or couldn't do** — every step of this run that did not happen as the skill says: a
  capability your tool lacks and the fallback used (→ `CAPABILITIES.md`), a check not run, a review
  round declined. One line each: what, why, and what it leaves unchecked. None: write **"Nothing
  skipped."** Each line is also recorded where the next phase reads it, so it is not lost between runs.
- **Test this yourself** — numbered steps the user can do by hand to see the result working (open this
  page, click this, you should see that). A phase that built nothing to click (a plan, a scope) writes
  **"Nothing to test by hand in this phase."**
- **What YOU do next** — the user's own actions, numbered, with dates where the work is time-bound
  (*"run 3 dinners with real bills by 2026-09-24"*). **Real-world homework belongs here and nowhere
  else** — a phase can hand back a two-week experiment, and prose under a confidence score is not a place
  a person can find it again. If there is nothing for them to do, say **"Nothing — you're done; run
  `/<next phase>` when you're ready"**, which is also a complete answer. **It ends with the handoff:** the
  phase's own *next, run `/<phase>`* line and, when `/playbook` runs the phase, its next-phase offer with its
  size and, for a long one, the start-with-room line (`/playbook` Step 2) — never after the close. **The next phase runs in
  a new conversation** (a chosen batch or chain excepted): the record is in git.

The agent's own next steps go in the handoff, never in this list.
**The close is the run's LAST message**, after the save question's answer. A composed skill's report is evidence *for* the close, never the
close; one that ends on its own report (`/security-review`) runs **inside a subagent** so it cannot end
the turn. Keep going until all four blocks are printed.

## §Re-run semantics — a second run must not erase the first


**Trigger:** the section is **not empty** (`next --phase` prints a `RE-RUN` line). Then: **compare the
section against the current rules first, and ask ONE question listing each concrete change** (the gaps
marked Recommended); nothing differs → say so and stop. Never ask *whether* to re-run: the user chose it by
running the phase. **Date a reversal rather than erasing it** — the superseded ADR / scope item / metric stays with
a `superseded <date>: <why>` line, including a recommendation the user reversed *inside* one run.
Log-shaped sections (`#Validation`, `#Learnings`) always append; tickets, releases and drift findings are
`STATUS.md` rows (§Status), appended by `status.py`.
**Before overwriting anything, open `MECHANISMS-ON-DEMAND.md` §Re-run semantics (full)** — the exact
forms, the within-run trigger, and the one case that may replace wholesale.

## §Declined runs — a phase that stops still leaves a trace


**Trigger:** this phase is **stopping without filling its section**. A stop that leaves the repo
byte-identical is indistinguishable from never having run, so it records the stop, and touches nothing in
`PRODUCT.md`:

`status.py set <phase> declined --reason "<what was missing>" --gate <the phase(s) that fill it>`

A *deliberate* skip of THIS phase is `status.py set <phase> overridden …`; proceeding here although an
earlier gate is unmet is `status.py bypass …` (§Status). Each needs gate · the user's own words; the date is
stamped. `filled ──▶ declined` is refused by `status.py`. **Before recording either, open
`MECHANISMS-ON-DEMAND.md` §Declined runs (full)** — which one applies, what it does to `/playbook`'s routing,
and the already-filled case.

## §Follow the pointer — a spine section that names files is an instruction to open them


The spine **records** that a thing was decided and **where it lives**; it does not contain the thing. So
a phase that consumes the thing **opens the files the section names** — `#Contracts`' `src/schemas/*` and
route table, `#Structure`'s map, `#Design`'s token stylesheet. Reading the record instead of the artefact
is how a phase finds a signpost where it needed a definition, and **fills the gap by inventing one**.

- **A presence check is not a usage check.** *"`#Contracts` is empty → warn"* cannot tell *contracts
  exist and were used* from *contracts exist and were ignored* — and the second is the case that happens.
- **Every type, route or field name a phase writes must resolve to a real symbol** in the files it was
  pointed at. This is greppable, so it is a gate, not an intention.
- **It failed exactly this way once:** the phase downstream of `/contracts` read the record, invented ten
  types, a float money field and an event that did not exist, and **published eleven public issues**
  before its own self-check caught it 22 minutes later.
- **Proof is a quotation, not an assertion** — a phase that opens a companion writes one `Read:`
  line per file, quoting a fragment that occurs VERBATIM in it (`MECHANISMS-ON-DEMAND.md §Read receipt`).

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
