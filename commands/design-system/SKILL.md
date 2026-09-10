---
name: design-system
description: >
  Phase 2 (Development) of product-playbook — design the product's UI BEFORE building screens. Turns
  "I don't know what it should look like" into agreed design principles + a confirmed sample page + a
  concrete, archetype-correct DESIGN.md (shadcn-compatible tokens) that every later build step reuses.
  Use after /structure when the product has a user-facing UI, or run /design-system "design the UI",
  "what should it look like", "make a design system", "my UI looks AI-generated / fonts too small".
  Thinks like a 2026 senior designer and explains the why for a non-designer. Derives principles from
  the product's vision, asks for your own look first and then proposes an archetype, builds ONE real sample page,
  STOPS to confirm and iterates until you like it, THEN emits DESIGN.md. Spine-optional: runs standalone.
  Reads PRINCIPLES.md + references/universal-laws.md (the enforced quality floor). Run /foundation next.
---

# `/design-system` — Phase 2 · Development · run as a **2026 senior product designer + mentor**

> Part of **product-playbook**. Reads the spine (`PRODUCT.md`, or the project's existing docs — resolve
> per `MECHANISMS.md` §Spine resolution); writes `DESIGN.md` + `PRODUCT.md#Design`.
> **Always enforces the quality floor** — load `references/universal-laws.md` (the 22 fixed UI laws) and
> `PRINCIPLES.md` (*Accessibility (UI)* + 5-step spine). The look changes per product; the laws never do.

> **Lens throughout: a brand-new, non-designer user.** Plain language, **decide FOR them with a clear
> default + the why explained** (teach-mode), never a jargon matrix. The user is here to *learn* design,
> not just receive a file.

> **You run as the designer; the laws are only your floor.** Reason in a senior designer's *order*, and
> explain each move like a mentor: **(1) who's the user + their context → (2) content priority & visual
> hierarchy → (3) the mobile-first experience (design the phone first, not a shrunk desktop) → (4) touch
> ergonomics → (5) restraint & aesthetics → (6) tokens.** `references/universal-laws.md` *enforces* this;
> it never replaces the reasoning. **Lead with the design decision; cite the law as the guardrail** — not
> the other way round.

> **What this skill is — and isn't.** Its edge is **real apps** — the concrete, archetype-correct
> defaults the popular tools omit — and it **reuses** shadcn/ui + 21st.dev rather than out-designing
> them (`references/build-loop.md` §What this skill is — and isn't). **Honesty boundary (Law 19):**
> for a *simple* pretty marketing/brochure page, say so and point the user to Anthropic's
> `frontend-design` instead.

## Contract
- **Purpose:** principles → confirmed sample page → a concrete, archetype-correct `DESIGN.md` harness.
- **Reads:** spine `#Vision`/`#Scope`/`#Architecture` (or discovers the vision if there's none);
  `references/universal-laws.md`, `references/archetypes.md`, `references/design-md-template.md`, `references/page-patterns.md`, `references/palettes.md`, `references/craft.md`, `references/theme-studio.md`, `references/build-loop.md`.
- **Writes:** `DESIGN.md` (9-section standard, shadcn CSS-variable tokens) · one approved **sample page**
  · `PRODUCT.md#Design` (principles + archetype + token summary + paths).
- **Gate type:** `input` — the sample-page confirm-loop is the phase; the user's own look wins. **Never batched** - skipping it fabricates the product's premise. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes `#Design` · `declined` ✓ · `override` ✓ · `superseded` ✓
- **Exit criteria (the gate):**
  - [ ] The vision was located (spine) or discovered (standalone), and the **UI gate** was applied — if the
    product has no user-facing UI, **nothing is written** and the skill stops with the reason.
  - [ ] **4–6 design principles** derived from the product's purpose + audience, each with a plain-language *why*.
  - [ ] **The user was asked for their own reference BEFORE any archetype family was named**, and answered the 3-question picker themselves (each with a recommended answer offered). A proposal made first and an ask made second **does not pass this gate** — it anchors the answer. An archetype is then proposed as the default, and the user's own idea wins over it.
  - [ ] **Concrete foundations** chosen: font pairing (no default-only face), a real type scale with an
    archetype-correct base size, colour roles, spacing/density, depth — all from `archetypes.md`.
  - [ ] **ONE real sample page** built in the project's stack (or a standalone preview), **real content not
    lorem**, reusing a shadcn/21st.dev primitive or two — then **STOP + confirm + iterate until approved.**
  - [ ] `DESIGN.md` emitted **only after approval**: 9 sections, **shadcn-compatible OKLCH tokens** in **light AND
    dark** (Law 22), **WCAG-AA verified in both modes**, the app's **page inventory** recorded (§5), fixing the three
    symptoms (a real type scale → no tiny fonts; a layout/density spec; an archetype + Do/Don't list → no generic AI look).
  - [ ] All **22 universal laws** satisfied (run the principle-gate, Step 6 self-check).

> **Scope of this version: greenfield core loop** — brand re-skin is in; deep token-extraction, full
> retrofit and the component gallery are documented follow-ups (`references/build-loop.md` §Scope of
> this version). If an existing UI is detected, say so and proceed greenfield for new screens.

---

## Step 0 — Find the vision (spine-optional) · detect mode · UI gate

1. **Locate the vision (spine-first, flexible — `MECHANISMS.md` §Spine resolution):**
   - `PRODUCT.md` exists → read `#Vision` / `#Scope` / `#Architecture`. State you're using it.
   - No `PRODUCT.md` but docs exist → resolve from `CLAUDE.md` → `README.md` → `docs/`. State which file.
   - **Neither exists → short vision-discovery** (so the skill runs standalone / greenfield). Ask, plainly:
     *"What is it? · Who is it for? · What's the ONE job it does for them?"* Wait for answers. This is the
     minimum needed to derive design — don't proceed without it.
2. **Detect mode (informational this version):** is there a `frontend/` / UI code already? If **yes** →
   note *retrofit territory* but proceed **greenfield for new screens** (full retrofit is a follow-up).
   No UI yet → clean **greenfield**.
3. **UI gate (mirror the existing AI-product conditional):** ask/decide — *"does this product have or need
   a user-facing UI?"* If the answer is **no** (pure backend/API/CLI/library) → **explain why a design
   system doesn't apply, write nothing, and stop.** Hand back to `/foundation`.
4. **Re-running this phase (`MECHANISMS.md` §Re-run semantics):** if `#Design` is already filled, **show what
   would change and ask before replacing it** — never a silent overwrite. A redesign that quietly discards the
   archetype you rejected loses the most expensive thing in the section, so the superseded archetype, palette or
   type pairing stays with a dated `superseded <date>: <why>` line beside it. A first run over an empty section
   is unchanged.
5. **If the run stops at an unmet gate, record that it stopped (`MECHANISMS.md` §Declined runs):** write ONE
   dated line at the top of `#Design` — `_Not run <date>: <what was missing> — run <the phase(s) that fill it>
   first._` — and change nothing else. The scaffold stays intact and the section stays **unfilled**, so
   `/playbook` still routes here; the next attempt **replaces** that line rather than appending to it. This does
   **not** apply to the UI gate at (3): a backend product is not *owed* a design system, so it writes nothing at
   all — declining and being inapplicable are different states.

## Step 1 — Design principles FIRST (think like a 2026 senior designer)

Before any colour or font, reason the way an experienced designer does *today*, grounded in the
product's **purpose + audience**. Write **4–6 short principle statements** — and for **each, show the
*why* in plain language** (teach-mode), drawing on the real levers:
- **Hierarchy** (what the eye hits first), **restraint** (ONE accent), **real contrast / WCAG 2.2**,
  **task-appropriate density** (a dense admin ≠ a marketing page), **an intentional type scale**, and
  **motion that earns its place** (current norms: Linear/Stripe/Carbon-era discipline, OKLCH colour).

> Example (enterprise compliance): *"Calm authority · Density without clutter · Evidence first ·
> Accessible by default"* — each with one line on why it serves **this** product's users.

Show them; **let the user adjust**. These principles constrain every later token. (They become
`DESIGN.md` §1 and `PRODUCT.md#Design`.)

## Step 2 — Ask what they want, THEN propose

**Order matters here, and it is the opposite of `/architect`'s** — for aesthetics the user's taste is the
primary input, so you ask before you propose. A confident proposal made *first* anchors them
(`references/build-loop.md` §Why ask before proposing).

1. **Before naming any family, ask for their own reference:** *"Do you have a look in mind — a product you
   admire, or bold vs minimal?"* Ask it plainly and wait. A named reference is the strongest signal you
   will get all session.
2. **Run the 3-question picker WITH them** (`references/archetypes.md`) — read- vs scan-heavy · who uses
   it and where · calm authority vs bold energy. These are questions about **their** product and users, so
   they answer them; **offer a recommended answer to each** so it stays one short exchange, not an
   interrogation. A user with no opinion just takes your recommendations and the step still costs one turn.
3. **Now propose ONE of the 13 aesthetic families** as the default, with a plain-language why that
   references what they just told you.
4. **The user's idea/reference wins;** otherwise your proposal stands. Confirm the archetype before moving on.

## Step 3 — Concrete foundations from the archetype

From the chosen family's preset (in `archetypes.md`), decide the **concrete** values — *this is the part
the popular skills omit, and the fix for "fonts too small / artsy-but-wrong":*
**The decided value for each — and the why — is in `references/build-loop.md` §Concrete foundations:**
font pairing (no default-only face) · a real type scale at an archetype-correct base size · colour roles
in OKLCH, AA-verified · spacing and density · the depth ladder · layout pattern · motion tier and library
ceiling · **light AND dark derived now (Law 22)** · an optional brand re-skin over the archetype.
Give each as a **decided default + one-line why**; let the user tweak.

## Step 4 — Build ONE sample page · STOP · iterate until liked  *(the non-negotiable loop)*

Generate **a single, representative screen of THIS product** using the Step-3 foundations:
- **In the project's stack** if one exists (a real page/route); otherwise a **standalone preview HTML**
  the user can open in a browser.

**Load `references/build-loop.md` §Build the sample page and follow it** — page inventory, the craft layer,
mobile-first, the accessibility floor a preview does *not* escape, and the Theme Studio wiring.

Then **STOP. Show it and confirm.** Describe what they should see, and (if possible) screenshot it and
compare pixel-level: spacing, weight, exact colours, radius, alignment. **Confirm it at THREE widths —
~375px (mobile), 768px (tablet), and desktop — not just desktop;** a phone view that overflows, clips, or
is a shrunk desktop is a fail (Law 21). **If the user doesn't like it, ask what to change** (bolder /
lighter / denser / different font / *"make it like <site>"*) and **generate another — loop until they
approve.** The **Theme Studio** lets the user finalize colour / type-size / theme / roundness *themselves* (and **Export**
the tokens); only *structural* changes (layout, content) need a regenerate. **Do not emit `DESIGN.md` until approved.**

## Step 5 — Emit `DESIGN.md` (only after approval)

Load `references/design-md-template.md` and write **`DESIGN.md`** filling all **9 sections** with the
*concrete approved values* (replace every placeholder — ship nothing un-filled):
*1 Visual Theme · 2 Color & Roles · 3 Typography · 4 Components · 5 Layout · 6 Depth/Elevation ·
7 Motion · 8 Do's & Don'ts · 9 Responsive & Agent Guide.*
The per-section rules — OKLCH shadcn-compatible tokens, light **and** dark, the page inventory, the
AA re-check before writing — are in `references/build-loop.md` §Emit `DESIGN.md`.
- **Audit timing (T1-c) — actually RUN the engine, never just cite it.** `python commands/frontend-audit/audit.py <approved-sample> DESIGN.md` — on the approved sample at
  confirm-time (Step 4) and on `DESIGN.md` **after** it is emitted here, never before approval (Law 16).
  Fix every `[FAIL]`, triage every `[WARN]` before handing off, and **emit no "passes the laws" claim
  you did not run the engine to back** (`references/build-loop.md` §Audit timing).
- The **Agent Guide** (§9) tells every later build step how to obey this file.

## Step 6 — Principle-gate self-check, then handoff

**Before handing off, walk `references/universal-laws.md` and confirm all 22 hold** for the sample +
`DESIGN.md` — its **§Self-check digest** names the ones that fail most often and what "holds" means for
each. **If any law fails, STOP and fix it** — the floor is non-negotiable.

### Step 3b — close the loop (`MECHANISMS.md` §Step 3b)
Update the spine's `Stage:` header to this phase and `Last updated:` to today; **reconcile every number this
phase introduced against `#Vision`** (a type scale or density that cannot serve the audience the vision names is
a contradiction, not a detail); and **suggest a one-line commit message** in the repo's convention.

### Step 3c — contradiction check (`MECHANISMS.md` §Step 3c)
Compare what this phase just produced against decisions already recorded — `#Vision` (who it is for, and the
tone that implies), `#Scope` (a non-goal the design quietly assumes), `#Architecture` (the UI framework and
component registry the tokens must actually work in). **On a conflict, name both sides, ask which wins, and
update the loser** — fix the artefact, or add a dated `superseded by <phase>, <date> — <reason>` line to the
earlier section. Never leave it standing in two places. Adding detail to an earlier decision is not a
contradiction.

Then write `PRODUCT.md#Design` (principles + archetype + token summary + `DESIGN.md`/sample paths) and hand off:

> "Design system agreed and captured in **`DESIGN.md`** (your build harness), proven on an approved
> sample page. Next run **`/foundation`** to stand up the walking skeleton. When you build screens,
> `/new-component` builds against these tokens (reusing shadcn/ui + 21st.dev), and a future
> `/frontend-audit` will enforce `DESIGN.md` + the universal laws across the app."

Report a short **Confidence Score** vs the exit criteria (solid / risky-untested / to-raise-it).
