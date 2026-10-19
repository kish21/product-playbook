---
name: design-system
description: UI products - set the visual rules and write DESIGN.md.
---

# `/design-system` — Phase 2 · Development · run as a **2026 senior product designer + mentor**

> Part of **product-playbook**. Reads the spine (`PRODUCT.md`, or the project's existing docs — resolve
> per `MECHANISMS.md` §Spine resolution); writes `DESIGN.md` + `PRODUCT.md#Design`.
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` · STATE-MODEL.md = `${CLAUDE_PLUGIN_ROOT}/docs/state-model.md` (a path still starting with `$`: the variable is the folder two levels above this SKILL.md, holding `commands/` and `PRINCIPLES.md` - never another tool's install). If `python` will not start (not found, or a sandbox refuses it): the project's `.venv` Python, else `python3`, else `py -3` - never a hunt; later commands use the start's `Run this copy as` line.
> **This skill's OWN reference files are a DIFFERENT folder:** `R` = folder of `${CLAUDE_PLUGIN_ROOT}/commands/design-system/references/archetypes.md`, never the plugin-root `references/`. **Each turn's sections come in ONE call the start prints** (`--step foundations|sample|write`).
> **`status.py next --phase design-system` prints this phase's sections of `PRINCIPLES.md` and `MECHANISMS.md`** — apply them; never open the whole files (a situational companion only when a rule points into it); the close rules print at `set design-system filled`.
> **Quality floor, every run:** `references/universal-laws.md` (26 fixed laws), printed by the `--step` calls;
> `PRINCIPLES.md` *Accessibility (UI)* + its 5-step spine come printed. The look changes per product; the laws never do.

> **The user is a non-designer.** Plain language; every choice is **a decided default + a one-line why**,
> never a jargon matrix. Decide in this order: **user + context → content priority → mobile-first → touch
> → restraint → tokens** (`references/craft.md` §Designer order). **Lead with the design decision; cite
> the law as the guardrail.**
> **A simple marketing/brochure page (Law 19):** point the user to Anthropic's `frontend-design`
> (`references/build-loop.md` §What this skill is — and isn't); this skill is for real apps, built on the UI component source `#Architecture` names (shadcn/ui + 21st.dev only when it names them; plain CSS when it names none).

## Contract
- **Purpose:** principles → confirmed sample page → a concrete, archetype-correct `DESIGN.md` harness.
- **Reads:** spine `#Vision`/`#Scope`/`#Architecture` (or discovers the vision if there's none); the
  references above, each at the step that names it.
- **Writes:** `DESIGN.md` (9-section standard, OKLCH CSS-variable tokens in shadcn/ui's names - plain CSS reads them too) · **the token stylesheet the
  app loads** (`src/app/globals.css` or where `STRUCTURE.md` puts it) · one approved **sample page**
  · `PRODUCT.md#Design` (principles + archetype + token summary + paths).
- **Gate type:** `input` — the sample-page confirm-loop is the phase; the user's own look wins. **Never batched** - skipping it fabricates the product's premise. (`STATE-MODEL.md` §2d)
- **State model** (`STATE-MODEL.md` §2c): writes `#Design` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Exit criteria (the gate):**
  - [ ] The vision was located (spine) or discovered (standalone), and the **UI gate** was applied — if the
    product has no user-facing UI, **nothing is written** and the skill stops with the reason.
  - [ ] **4–6 design principles** derived from the product's purpose + audience, each with a plain-language *why*.
  - [ ] **The user was asked for their own reference BEFORE any archetype family was named**, and answered
    the 3-question picker themselves (a recommended answer offered for each). Proposing first and asking
    second **fails this gate**.
  - [ ] **Concrete foundations** chosen: font pairing (no default-only face), a real type scale with an
    archetype-correct base size, colour roles, spacing/density, depth — all from `archetypes.md`.
  - [ ] **ONE real sample page** built in the project's stack (or a standalone preview), **real content not
    lorem**, with its empty, loading and error states and what `#Scope` asks it to show, in the owner's
    language(s), self-hosted fonts, rendered at three widths with screenshots, reusing a
    primitive from the component source `#Architecture` names (never a library it does not name) — then **STOP + confirm + iterate until approved.**
  - [ ] `DESIGN.md` emitted **only after approval**: 9 sections, **OKLCH CSS-variable tokens** in **light AND
    dark** (Law 22), **WCAG-AA verified in both modes**, the app's **page inventory** recorded (§5), fixing the three
    symptoms (a real type scale → no tiny fonts; a layout/density spec; an archetype + Do/Don't list → no generic AI look).
  - [ ] **The tokens EXIST IN THE APP, not only in the spec** — every token `DESIGN.md` defines is written
    into the project's real stylesheet, that stylesheet is imported by the app's root entry, and its path
    is recorded in `DESIGN.md` §2 (case file: The spec that styled nothing).
  - [ ] All **26 universal laws** satisfied (run the principle-gate, Step 6 self-check).

---

## Step 0 — Find the vision (spine-optional) · detect mode · UI gate

**First turn, ONE command: `python ${CLAUDE_PLUGIN_ROOT}/tools/status.py next --phase design-system`** — all
this step needs; never `PRODUCT.md` or a rule file whole. Show its first line. **A script refuses or fails →
its message names the fix:** make it and run the SAME command again; `set design-system filled --section-from <file>
--dry-run` lists every gap the save would refuse. Never open `status.py`, `theme_studio.py`, `render_check.py` or
`audit.py` and never run their `--help` - the start printed every command and flag.

1. **Locate the vision (spine-first — `MECHANISMS.md` §Spine resolution):** say you use the spine
   lines the start prints. **No spine at all → run the
   three-question vision-discovery in `references/build-loop.md` §Standalone vision discovery** and wait
   for the answers.
2. **Detect mode** (the start says): UI code exists → say *retrofit territory*, design new screens greenfield
   (`references/build-loop.md` §Scope of this version); none → greenfield.
3. **UI gate:** the start applies the UI flag; unknown → ask *"does this product have or need a user-facing UI?"* **No** (backend, API, CLI,
   library) → **explain why a design system doesn't apply, write nothing, and stop.** Hand back to `/foundation`.
4. **Re-running — `MECHANISMS.md` §Re-run semantics, in full.** The superseded archetype, palette or type
   pairing keeps its dated `superseded <date>: <why>` line; so does an archetype **you recommended and the
   user reversed inside this run**.
5. **Stopping — `MECHANISMS.md` §Declined runs, in full**, except at the UI gate (3): a product with no UI
   writes nothing at all — not a `declined` record.

**Two rounds, ONE message or form each:** round 1 = Step 1 + Step 2.1–2; round 2 = Step 2.3–4 + Step 3; then
the sample's confirm until approved.

## Step 1 — Design principles FIRST

Write **4–6 short principle statements** from the product's **purpose + audience**, each with its *why*
in plain language — before any colour or font. Levers and a worked example: `references/build-loop.md`
§Design principles. Show them; **let the user adjust**. They become `DESIGN.md` §1 and `PRODUCT.md#Design`.
Under them, name what `#Scope` asks the screen to show; the sample carries each.

## Step 2 — Ask what they want, THEN propose

1. **Before naming any family, ask for their own reference:** *"Do you have a look in mind — a product you
   admire, or bold vs minimal?"* Ask it plainly and wait (case file: The answer we anchored).
2. **Run the 3-question picker WITH them** (`references/archetypes.md` §The 3-question picker, printed by the
   start). They answer; **offer a recommended answer to each**. Same message: **interface language(s)**
   (pre-filled from `#Scope`) and whether they switch; **fonts self-hosted** (decided under EU custody, else asked); and
   *"What is this sample for?"* (the end user's main screen · a demo / presenter view · both - the start marks one Recommended).
3. **Now propose ONE of the 13 aesthetic families** as the default, with a plain-language why that
   references what they just told you. **Say that there are 13 and where they are** (`references/archetypes.md`):
   a shortlist must name the full set ("Other" alone asks a non-designer to invent one).
4. **The user's idea/reference wins;** otherwise your proposal stands. Confirm the archetype before moving on;
   every confirm offers *"Keep as proposed (Recommended)"* first.

## Step 3 — Concrete foundations from the archetype

From the chosen family's preset (`archetypes.md` §<the family> §How Step 3), decide
each value in `references/build-loop.md` §Concrete foundations — type pairing and scale, colour roles in OKLCH, density, depth, layout, motion tier,
**light AND dark now** (Law 22) — as a **decided default + one-line why**; let the user tweak.

## Step 4 — Build ONE sample page · STOP · iterate until liked  *(the non-negotiable loop)*

Build **one representative screen of THIS product** from the Step-3 foundations — in the project's stack,
or a **standalone preview HTML** when there is no stack. Which screen: round 1's *"What is this sample for?"* — the
end user's main screen, or a presenter view of how the product decides. **Follow `references/build-loop.md` §Build the
sample page**.

**The sample proves the LOOK, never the LOGIC.** Label any numbers in the page "illustrative figures — not
the product's rules", say so when you present it, and **do not copy sample logic into the product** — the
real rules arrive with `/contracts` and `/build` (case file: The sample that set a price).

Then ONE turn runs the rendered check and the audit over the sample (the start's commands); fix every
`[FAIL]`; `NOT RUN` is no result (the start says how). **STOP. Show it and confirm** — at **three widths, ~375px ·
768px · desktop**, never desktop alone (Law 21) — in ONE message with two options: *"Looks good
(Recommended)"* · *"Change something"* - a looks-good is the go-ahead to write and save. Not liked → ask what to change, **generate another; loop until they
approve**. **Do not emit `DESIGN.md` until approved** (`references/build-loop.md` §Confirm the sample). The
after-approval commands refuse until you pass the owner's answer word for word (`--approved "<their answer>"`): never
run them before you asked.

## Step 5 — Emit `DESIGN.md` (only after approval)

After approval, ONE message: `status.py next --phase design-system --step write --approved "<their answer>"` and
`theme_studio.py <sample> --remove --approved "<the same answer>"` (the start prints both), then writes: **the tokens TWICE — as the
spec and as the app's stylesheet**, following `references/build-loop.md` §Emit the token stylesheet; **`DESIGN.md`**
from `references/design-md-template.md` §intro §The skeleton — **`## 0. In short` first** (plain words; each principle
with its `#Vision` line), then all **9 sections** with the
*concrete approved values* — replace every placeholder, ship nothing un-filled. Per-section rules:
`references/build-loop.md` §Emit `DESIGN.md`. And the `#Design` file.
- **Audit — RUN the engine, never cite it:** `python "${CLAUDE_PLUGIN_ROOT}/commands/frontend-audit/audit.py"`
  (never search the plugin cache) over the sample at confirm-time; `set` runs it over `DESIGN.md` and writes its
  counts there — never type one (never before approval, Law 16); fix every `[FAIL]`, triage every `[WARN]`.

## Step 6 — Principle-gate self-check, then handoff

**Walk `references/universal-laws.md` and confirm all 26 hold** for the sample + `DESIGN.md` (its
**§Self-check digest** lists the ones that fail most). **A law fails → STOP and fix it.**

### Step 3c — contradiction check, BEFORE the save call (`MECHANISMS.md` §Step 3c)
Before `set` (Step 3b), compare the result with the `#Vision` · `#Scope` · `#Architecture` lines the start printed. **On a conflict** (this replaces
`MECHANISMS.md` §Step 3c items 2-3), **name both sides on a line of their own, ask nothing, never edit an earlier
phase's record or document**: `status.py open --from design-system --what "Clash: <both sides>" --clears "/<that
phase> decides"`. Adding detail to an earlier decision is not a contradiction. The open item is written before `set`, so the save takes it (`git status` clean at the end).

### Step 3b — close the loop (`MECHANISMS.md` §Step 3b)
`status.py set design-system filled --section-from <file> --commit "<one line>"` (`MECHANISMS.md` §Status)
refuses every gap the start lists in one list (fix what it names, never the check), then
records, saves and prints the rest of the close. **Reconcile every number against `#Vision`**. No save question: the record call saves (`--no-commit` only when the user said not to save) - the confirm's
*"Looks good"* was the go-ahead (`MECHANISMS.md` §Commit the work). **The transition guard**
(`MECHANISMS.md` §Step 3b, item 4): `set` re-ran this phase's own `evidence:` line (the rendered check) and the
`/frontend-audit`; a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not.
A Step 3c clash is named in the close too. **Close in plain language** (`MECHANISMS.md` §Plain-language close): four blocks in order, each under its bolded name: **What just happened** · **What I skipped or couldn't do** · **Test this yourself** · **What YOU do next** (ends with the handoff).

Then hand off:

> "Design system agreed and captured in **`DESIGN.md`**, proven on an approved sample page. Next run
> **`/foundation`** — alone, or as a **batch** `/foundation` + `/contracts` + `/tickets` with one review at
> the end (`MECHANISMS-ON-DEMAND.md` §Batch mode). Screens: `/new-component` builds them on these tokens,
> `/frontend-audit` checks them against `DESIGN.md` + the universal laws."

Report a short **Confidence Score** vs the exit criteria (solid / risky-untested / to-raise-it).
