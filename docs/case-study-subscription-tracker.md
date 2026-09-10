# Case study — the playbook auditing a project it built

**Project:** Subscription Tracker — a private, manual subscription tracker that runs in a browser (Next.js).
**Built with:** `product-playbook`, phases `/vision` → `/validate` → `/scope` → `/plan` → `/architect` → `/structure` → `/design-system` → `/foundation` → `/contracts` → `/tickets` → `/build` → `/dev-check`.
**The run reported here:** `/drift-check`, 2026-09-10, after three vertical slices had shipped.
**Result: 9 drifts.** Every one of them in a project the playbook itself had guided.

---

## Why this is the only evidence in this repo worth having

Every other claim in the README is self-asserted. This one is not, and it has an uncomfortable
property that makes it worth more than a testimonial: **the tooling found faults in work it had
guided**, including one fault in the tooling itself, which became a shipped fix here.

A case study where everything went well proves nothing. Nothing below has been softened.

### On checkability

The project is a personal repository and is not published, so the honest position is stated
plainly: **the artefacts below are excerpted verbatim from that project's own
`PRODUCT.md#Drift log` and the two findings that are cheapest to falsify are traced to file
paths anyone can reason about.** Where a claim rests on the repository rather than on the
excerpt, it is labelled. What you cannot do is `git clone` it — if that matters more than the
findings do, treat this page as unverified and disregard it.

---

## The findings, as recorded

Verbatim from `PRODUCT.md#Drift log`, entry `2026-09-10`. Grouped as the run grouped them.

### Docs drift — the spec described routes that do not exist

> **(1)** `docs/api/openapi.json` specifies `GET/PATCH/DELETE /api/v1/subscriptions/{id}` — no `[id]` route file exists.

The API specification described three endpoints that were never built. Anyone integrating from
the spec — a person, or an agent reading it as ground truth — would have written client code
against three routes that return 404.

Checkable without the repo, from the two facts the finding names: `openapi.json` lists
`/api/v1/subscriptions/{id}`; the route tree contains `src/app/api/v1/subscriptions/route.ts`
and **no `[id]/` directory beneath it**. In Next.js's App Router a dynamic segment *is* a
directory. No directory, no route.

> **(2)** `openapi.json` + `#Contracts` both claim `/api/v1/auth/*`, but Better Auth mounts at `/api/auth/*` (default basePath, no rewrite in `next.config.ts`) — `docs/features/*` written from live verification are correct, the re-typed spec rotted.

The interesting half is the clause at the end. **The documents written by verifying the running
system were right. The document written by typing out the intended shape was wrong.** That is
the whole argument for `/build`'s "verify the LIVE path" rule, arriving as evidence rather than
as advice — and it is the second-order reason `PRINCIPLES.md` insists a doc that drifts is worse
than no doc: this one was confidently, specifically wrong.

> **(3)** README status banner still says active work is M1-SLICE-02 (02 and 03 shipped) and advertises category filter/breakdown as a current capability.

A shipped-features claim for features that had no live path. See (7).

### Scope creep — three items, and only one of them looked like creep

> **(4)** dark mode is LIVE via `@media (prefers-color-scheme: dark)` in `globals.css` — Deferred, trigger "first user request" never fired, and ADHOC-05's 11 contrast failures now span an untested second palette.

This is the finding that justifies the whole mechanism. Dark mode was on the **Deferred** list
with an explicit trigger — *first user request* — which had never fired. It shipped anyway,
invisibly, because a CSS media query is three lines. And it did not arrive alone: **11 known
contrast failures now applied to a second palette nobody had audited.** A deferred item that
ships silently does not merely add scope; it doubles the surface of an open defect.

> **(5)** `status: active|cancelled` in DB + 4 schemas + domain exclusion serves Deferred mark-as-cancelled (dormant — nothing can set it).

Half a deferred feature, built into the schema. Not wrong to have — but until it was named, the
column read to any later reader as evidence that the feature existed.

> **(6)** name `search` (`?search=`, `escapeLikePattern`, security fix ADHOC-04) appears nowhere in `#Scope`.

A feature with its own security hardening, absent from the scope document entirely.

### Table stakes — the two that hurt

> **(7)** edit/delete and category filter/breakdown are in-scope-NOW with no live path (gated by `/dev-check` same day).

In-scope, advertised in the README (3), not actually reachable.

### Vision

> **(8)** `#Validation` is an override — riskiest assumption still untested across 3 shipped slices.

The riskiest assumption — *"people will keep entering subscriptions manually"* — was never
tested. `/validate` was skipped by an explicit, recorded override on 2026-09-07 (*"building
directly for personal use"*). Three slices later, the override was still standing, and
`/drift-check` still surfaced it, because a recorded override is surfaced every time a later
phase orients. **This is the mechanism working exactly as designed**: the skip was allowed, it
was attributable, and it did not become invisible.

### Process

> **(9)** project `CLAUDE.md` carries no build-state/NEXT SESSION PLAN and both it and `AGENTS.md` are untracked.

---

## What it did with them — the part that is not a bug list

`/drift-check` does not only report. Each finding was resolved as **fix** or as a **deliberate
re-scope**, and the split is the point:

| Findings | Verdict |
|---|---|
| (1) (2) (3) (7) (9) | **fix** — delete the three unimplemented paths from `openapi.json`, correct the auth basePath in both places, refresh the README, build the missing slices, write the handoff block |
| (4) | **deliberate re-scope** — keep dark mode, **move it out of Deferred into shipped**, and extend the contrast audit to the dark palette |
| (5) (6) | **deliberate re-scope** — keep both, record `status` as pre-built-dormant, add `search` to `#Scope` so neither reads as evidence a feature exists |
| (8) | **standing** — `/validate` is still cheaper than the next feature |

Nothing was quietly deleted to make the report look clean, and nothing that had shipped was
ripped out to satisfy a document. A reversal is fine; an **unrecorded** reversal is the bug. The
recommendation for (1) is the sharpest of them — *"pin with a parity test that reads the route
tree so the spec cannot rot again"* — a check, not a promise to be careful.

Overall status recorded: **DRIFTING (docs), on-track (code direction).**

---

## The loop closed: a finding here became a fix in the playbook

Two days earlier, on **2026-09-08**, a run on this same project surfaced something worse than a
project defect.

The project was mid-Build: two features in `#Build log`, `#Dev-complete` entirely unchecked,
`#Tests` empty. The user ran `/eval` — three phases early. **The run stopped, correctly. But it
stopped on the agent's own judgement, not because the skill asked.** `/eval` had carried the
heading `## Step 0 — Context + prior-gate check` for five releases while its body gated on
nothing at all. A run that scored the half-built product instead would have violated no
instruction in the file.

Two things had kept it invisible:

1. **The heading answered the question.** Anyone auditing *"does `/eval` gate?"* greps for the
   gate's name, finds it, and stops looking.
2. **An eval case asserted the missing behaviour.** `eval-declined-run-leaves-a-trace` claimed
   `/eval` "finds `#Tests` empty, declines to measure" — a gate the skill body never specified.
   Nothing executes the eval cases, so the assertion sat there agreeing with the heading instead
   of contradicting the body.

That became **#104**, fixed in **v1.25.0**, and it produced two things that outlast it:

- **`tools/check.py` check 9** — a Step 0 titled `prior-gate check` must contain a gate: name a
  prior `#Section` **and** offer an override. Written before the fix, **it went red on three
  skills rather than one** — `/build` named `/contracts` with no override, and `/dev-check` had
  no prior gate at all, so a checkpoint over an empty `#Build log` passed by having nothing to
  fail.
- **A rule** — *a heading is not a behaviour* — now in `LESSONS.md`, with the full story in
  `references/case-files-principles.md`.

The README's central claim is that this repo's guarantees are enforced in its own build rather
than asserted. Check 9 exists because a real run on a real project caught this repo doing the
thing it warns others about.

---

## What this does and does not prove

**It does show**: a system that reports faults in work it guided, that separates *fix* from
*deliberate re-scope* rather than treating every deviation as an error, that surfaced a
three-slice-old recorded override instead of letting it fade, and that turned a finding about
itself into a check which fails CI.

**It does not show** that the playbook prevented these nine issues. It did not — they happened
under it. What it changed is that they were **found, named, and each given a verdict**, rather
than living in a repository nobody could account for. That is the claim this project actually
makes: not that discipline makes you faultless, but that a fault should never be invisible.
