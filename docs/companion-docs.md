# Every spine section gets a companion doc — and a pointer you can prove was opened

> Design note. Follows the `docs/state-model.md` precedent: the problem, the contract, what it
> touches, what is verified. Two problems, one piece of work — the spine overflows *because* eight
> sections have nowhere else to write, and moving detail out is only safe once a pointer is provably
> followed. Shipping the split without the proof would multiply #166 across eight new sections.

---

## 1. The problem

### 1a. Eight sections have nowhere to put detail, so it all lands in the spine

`templates/PRODUCT.md` states the rule already: **"A section is a RECORD, not a container"** — summary,
the decision, the evidence line, and a pointer to where the detail lives. Six sections have a companion
file to point *at*:

| Section | Companion |
|---|---|
| `#Architecture` | `docs/adr/*` |
| `#Structure` | `STRUCTURE.md` |
| `#Design` | `DESIGN.md` |
| `#Foundation` | `docs/runbook.md` |
| `#Build log` | `docs/features/*` |
| `#Deployment` | `docs/deployment.md` |

**Eight do not:** `#Vision`, `#Validation`, `#Scope`, `#Plan`, `#Contracts`, `#Tests`, `#Evaluation`,
`#Learnings`. The rule applies to them and there is no file to apply it to, so the detail has exactly
one place to go and it goes there.

**Measured on a live run (2026-09-12, `potluck_latest`):** `/vision` — the *first* of seventeen sections
— wrote **5,131 bytes into `#Vision` against the ~5,120-byte per-section cap**. It breached the cap on
phase one and nothing said a word. The empty scaffold is already 10,359 bytes of the ~25,000 budget,
leaving ~14,600 bytes for seventeen sections; `/vision` alone spent 4,297 of it. At that rate the file
lands at **73–83KB** — the number #167 was filed about and believed fixed in v1.38.0.

**Why nothing caught it:** the cap lives in a template comment and in `/drift-check` — a skill the user
runs *by choice*. No section-writing phase checks the size of what it just wrote. `tools/check.py:35`
already names this failure mode: *"a rule with no check is a suggestion."*

### 1b. The guard against pointer-blindness is itself unenforced

`MECHANISMS.md` §Follow the pointer exists precisely for this: *"a phase that consumes the thing opens
the files the section names… Reading the record instead of the artefact is how a phase finds a signpost
where it needed a definition, and fills the gap by inventing one."* It cost eleven wrongly-published
public issues once (#166).

Its current reach, verified:

- **named in 2 of 22 skills** — `commands/contracts.md`, `commands/tickets/SKILL.md`
- **enforced by 0 of 18 checks** in `tools/check.py`
- the text claims it *"is greppable, so it is a gate, not an intention"* — **nothing greps it**

So the safeguard for the change in 1a does not currently work. That ordering is the whole design.

---

## 2. The contract

### 2a. Eight new companion docs

Each section below becomes a **record** in the spine (summary · decision · evidence · pointer) with its
detail in a companion file the phase writes:

| Section | Companion | Owner |
|---|---|---|
| `#Vision` | `docs/vision.md` | `/vision` |
| `#Validation` | `docs/validation.md` | `/validate` |
| `#Scope` | `docs/scope.md` | `/scope` |
| `#Plan` | `docs/plan.md` | `/plan` |
| `#Contracts` | `docs/contracts.md` | `/contracts` |
| `#Tests` | `docs/tests.md` | `/test` |
| `#Evaluation` | `docs/evaluation.md` | `/eval` |
| `#Learnings` | `docs/learnings.md` | `/learn` |

The spine keeps what a *later phase* must not miss (the one-sentence vision, the core feature, the
non-goals, the north-star numbers). Reasoning, competitor detail, raw notes and workings move out.

### 2b. A read receipt — a pointer you can prove was opened

A pointer is only safe if following it is **verifiable**. Intent is not verifiable; a quotation is.

**Every phase that consumes a companion file writes a read receipt into its own section:**

```
Read: docs/scope.md (2026-09-12) — "no accounts for the organiser either"
```

The quoted fragment must occur **verbatim in the named file**. That is the anti-cheat: a phase cannot
produce the quotation without opening the file, and the claim is checkable by string match rather than
by trust. This reuses the existing `evidence:` discipline (`command -> result · artefact · date`) rather
than inventing a second format.

### 2c. Three enforcement layers, honestly scoped

Two of these run in this repo's CI. The third runs in the user's project — stated separately because
conflating them is how the size cap ended up unenforced.

| Layer | Where | Enforces | Mechanically checkable? |
|---|---|---|---|
| **L1 — declaration** | `tools/check.py`, this repo | the skill that OWNS a section declares its companion, and the template points at it | **Yes** — static text |
| **L2 — receipt** | the user's project | the receipt exists, and the quoted fragment occurs in the named file | **Yes** — string match |
| **L3 — record** | the user's project | the phase that wrote a section reports its size and applies the record test per field (decision stays, reasoning moves) — **no byte cap** (#200) | **Partly** — size is a byte count; the record test is a judgement |

**L1 is a new check in `check.py`.** L2 and L3 become obligations in the gate-closing region of every
section-writing skill, in the style check 17 already enforces for §Commit the work — so the *obligation*
is verified statically here, and the *act* is verified at runtime there.

---

## 3. What it touches

- `templates/PRODUCT.md` — eight sections gain a `see docs/<name>.md` pointer and a `Read:` line
- eight skills — `vision` `validate` `scope` `plan` `contracts` `test` `eval` `learn`: write the
  companion, emit the receipt, report their own size
- every skill with a `**Reads:**` naming a companion-backed section — receipt obligation
- `references/mechanisms.md` — §Follow the pointer gains the receipt format; a new §Section is a record rule (built in `mechanisms-on-demand.md`; named §Section size until #200)
- `tools/check.py` — L1 check; extend check 17's region test to the receipt + size obligations
- `commands/drift-check.md` — keeps the size check; it is no longer the *only* place it lives

---

## 4. What is verified (exit criteria)

- [ ] Eight companion docs defined in `templates/PRODUCT.md`, each with a pointer + `Read:` line
- [ ] L1 check added and **proven red before green**: removing a companion from a skill's `Reads:` fails
- [ ] Receipt format in `MECHANISMS.md`, with the verbatim-quotation rule stated
- [ ] Receipt + size obligations named in all eight skills' gate-closing regions, enforced like check 17
- [ ] `check.py` green; skill count unchanged at 22; no skill file over 15KB
- [ ] **Re-run `/vision` on a clean folder: `#Vision` holds only decisions/evidence/pointers, its size is reported (not trimmed to), and `docs/vision.md` exists** _(rewritten by #200 — was "lands under 5KB")_

The last one is the only criterion that proves the original defect is gone, and it is a live run, not
a unit test.

---

## 5. Decisions on record

- **The split ships only WITH the receipt.** Moving detail out while pointers stay unenforced is #166 in
  eight new places. Not sequencing — the same piece of work.
- **Proof is a quotation, not an assertion.** "I read it" is not checkable; a fragment that must occur in
  the file is.
- **No remote-repo change.** `MECHANISMS.md` §Commit the work keeps *"never create a remote"* — the
  owner set that aside on 2026-09-12 as out of scope for this work.

---

## 6. Built vs designed — one recorded deviation

**Designed:** L1 would require every *consuming* skill to name the companion in its `**Reads:**` list.

**Built:** L1 checks that the skill which *owns* a section declares its companion and that the template
points at it. Consumers are bound instead by the two rules that already exist — the section they read now
literally contains `Detail: docs/<name>.md`, and `MECHANISMS.md` §Follow the pointer makes a named file an
instruction to open it — with the receipt proving they did.

**Why the change:** a `Reads:` entry declares *intent to open*, which is the weaker of the two claims and
the one already superseded by the receipt (*a verbatim quotation*). Requiring both would edit every skill
in the chain to restate an obligation the receipt already proves, and check 17's history is that a second
way of saying the same thing is how one of them drifts.

**What this leaves open, stated plainly:** a consumer that reads the record, never opens the companion and
writes no `Read:` line is caught by check 21 only at its *own* gate-closing region (the obligation is
declared), not by a check that the receipt was actually produced in the user's project. That verification
is runtime (L2) and belongs to `/drift-check`. **Unfiled and owed.**

---

## 7. Reversal on record — the byte caps are gone (#200, 2026-09-12)

**Designed and built (v1.40.0):** L3 measured `#Section` against ~5KB and `PRODUCT.md` against ~25KB, both
inherited from the #167 fix.

**Measured on the next live run:** `#Vision` landed at 5,101 B after being "trimmed twice to squeeze
under" — 14 required fields at ~360 B each, none bloated, nothing left to move — while `docs/vision.md`
(9.6 KB) was written *in addition*. The cap produced trimming, not relocation. The template's 95 required
fields at a tight 300 B each come to ~40 KB, so the 25 KB total was unreachable by construction, and the
two caps never agreed with each other (17 × 5 KB = 85 KB).

**Owner decision:** *"I never asked it to cap, but to have a separate document and keep PRODUCT.md
reasonable and relevant."* **No byte caps on the spine.** The instrument is the record test — per field,
*decision or reasoning?* — with size reported as a signal for `/drift-check`, never enforced. Check 21
keeps all three assertions; only its prose and the pointer name (`§Section is a record`) changed.
