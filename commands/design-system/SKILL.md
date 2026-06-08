---
name: design-system
description: >
  Phase 2 (Development) of product-playbook — design the product's UI BEFORE building screens. Turns
  "I don't know what it should look like" into agreed design principles + a confirmed sample page + a
  concrete, archetype-correct DESIGN.md (shadcn-compatible tokens) that every later build step reuses.
  Use after /structure when the product has a user-facing UI, or run /design-system "design the UI",
  "what should it look like", "make a design system", "my UI looks AI-generated / fonts too small".
  Thinks like a 2026 senior designer and explains the why for a non-designer. Derives principles from
  the product's vision, proposes an archetype (asks for your own idea too), builds ONE real sample page,
  STOPS to confirm and iterates until you like it, THEN emits DESIGN.md. Spine-optional: runs standalone.
  Reads PRINCIPLES.md + references/universal-laws.md (the enforced quality floor). Run /foundation next.
---

# `/design-system` — Phase 2 · Development · run as a **2026 senior product designer + mentor**

> Part of **product-playbook**. Reads the spine (`PRODUCT.md`, or the project's existing docs — resolve
> per `PRINCIPLES.md` §Spine resolution); writes `DESIGN.md` + `PRODUCT.md#Design`.
> **Always enforces the quality floor** — load `references/universal-laws.md` (the 21 fixed UI laws) and
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

> **What this skill is — and isn't.** Its edge is **real apps**: enterprise, dense, data-heavy, existing
> codebases, disciplined builds — the unglamorous *concrete, archetype-correct* defaults the popular
> tools omit. It does **not** out-design the ecosystem on palettes/components — it **reuses** shadcn/ui +
> 21st.dev + the open DESIGN.md standard and wires them into the build lifecycle. **Honesty boundary
> (Law 19):** for a *simple* pretty marketing/brochure page, say so and point the user to Anthropic's
> `frontend-design` instead.

## Contract
- **Purpose:** principles → confirmed sample page → a concrete, archetype-correct `DESIGN.md` harness.
- **Reads:** spine `#Vision`/`#Scope`/`#Architecture` (or discovers the vision if there's none);
  `references/universal-laws.md`, `references/archetypes.md`, `references/design-md-template.md`, `references/page-patterns.md`.
- **Writes:** `DESIGN.md` (9-section standard, shadcn CSS-variable tokens) · one approved **sample page**
  · `PRODUCT.md#Design` (principles + archetype + token summary + paths).
- **Exit criteria (the gate):**
  - [ ] The vision was located (spine) or discovered (standalone), and the **UI gate** was applied — if the
    product has no user-facing UI, **nothing is written** and the skill stops with the reason.
  - [ ] **4–6 design principles** derived from the product's purpose + audience, each with a plain-language *why*.
  - [ ] An **archetype proposed as a default** AND the user explicitly asked for their own idea/reference.
  - [ ] **Concrete foundations** chosen: font pairing (no default-only face), a real type scale with an
    archetype-correct base size, colour roles, spacing/density, depth — all from `archetypes.md`.
  - [ ] **ONE real sample page** built in the project's stack (or a standalone preview), **real content not
    lorem**, reusing a shadcn/21st.dev primitive or two — then **STOP + confirm + iterate until approved.**
  - [ ] `DESIGN.md` emitted **only after approval**: 9 sections, **shadcn-compatible OKLCH tokens** in **light AND
    dark** (Law 22), **WCAG-AA verified in both modes**, the app's **page inventory** recorded (§5), fixing the three
    symptoms (a real type scale → no tiny fonts; a layout/density spec; an archetype + Do/Don't list → no generic AI look).
  - [ ] All **22 universal laws** satisfied (run the principle-gate, Step 6 self-check).

> **Scope of this version: greenfield core loop.** Lightweight brand-input (re-skin to given colours/reference)
> is in; **deep** image/code token-extraction (the user's `UI_to_Prompt`), full retrofit (rewrite existing pages),
> and the component-gallery page are documented follow-ups (`/frontend-audit` is the separate enforcement skill).
> If an existing UI is detected, say so and proceed greenfield for new screens.

---

## Step 0 — Find the vision (spine-optional) · detect mode · UI gate

1. **Locate the vision (spine-first, flexible — `PRINCIPLES.md` §Spine resolution):**
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

## Step 2 — Propose an archetype, stay flexible

Load `references/archetypes.md`. Map the principles to one of the **~9 aesthetic families** using the
**3-question picker** (read- vs scan-heavy · user type · calm vs bold). **Propose ONE as the default
with a plain-language why** — then **ask the user**: *"Do you already have a look in mind — a product you
admire, or bold vs minimal?"* **The user's idea/reference wins;** otherwise your proposal stands. Confirm
the archetype before moving on.

## Step 3 — Concrete foundations from the archetype

From the chosen family's preset (in `archetypes.md`), decide the **concrete** values — *this is the part
the popular skills omit, and the fix for "fonts too small / artsy-but-wrong":*
- **Font pairing** (display / body / mono) — **never a default-only face** (Law 1).
- **A real type scale** with an **archetype-correct base size** (enterprise 14–16px body, 13px tables,
  ~1.2 ratio, 4–8px grid; consumer 16–18px, 1.25–1.333, bolder) — Law 3.
- **Colour roles** (one dominant + one accent; semantic status) in **OKLCH**, **WCAG-AA verified** — Laws 5–8.
- **Spacing / density**, **depth ladder** (`--shadow-sm/-lg`, `--radius`), **layout pattern**, **motion**
  defaults (transform/opacity only) — Laws 9–12.
- **Light + dark by default (Law 22):** derive both token sets now (dark is not inverted light — give it its own
  AA-checked values); the archetype's natural mode is the default, the other is the alternate.
- **Brand input (optional — decide-for-them otherwise):** if the user has a brand — colours, a logo, a marketing
  screenshot, or a *"make it like <site>"* reference — extract its palette + type and **re-skin the tokens to it**.
  The archetype is the strong default; the brand *personalises* it; the laws + AA contrast still hold.
Give each as a **decided default + one-line why**; let the user tweak.

## Step 4 — Build ONE sample page · STOP · iterate until liked  *(the non-negotiable loop)*

Generate **a single, representative screen of THIS product** using the Step-3 foundations:
- **In the project's stack** if one exists (a real page/route); otherwise a **standalone preview HTML**
  the user can open in a browser.
- **Reuse a shadcn/ui + 21st.dev primitive or two** (Law 15 — never hand-roll buttons/inputs/modals),
  re-skinned with the tokens.
- **Real content from the product's domain — never lorem** (Law 18).
- **Note the page inventory first** (which page TYPES this app needs — auth, dashboard, billing, settings, landing…
  from the vision; see `references/page-patterns.md`), then build the *most representative* one (a dashboard's main
  view, the consumer app's home — not a login). The other pages' patterns get recorded in `DESIGN.md` §5 — we don't build them all now.
- **Build it mobile-first and responsive (Law 21):** design the **phone view first** — lead with the user's
  #1 mobile job (content priority), collapse the archetype's layout (sidebar → drawer, table → stacked cards,
  detail → sheet, KPIs reflow), tap targets ≥44px — *then* scale up to tablet/desktop. Never a fixed desktop
  grid that can't collapse.
- **Preview caveat:** a standalone preview (no stack) **can't import shadcn/21st.dev** — say so; Law 15 governs
  the real build. Still mirror the `DESIGN.md` tokens exactly.
- **Confirm on the user's real display:** subtle choices (canvas tint, status-label colour, table alignment)
  render differently across screens — pick **clearly visible** values and verify on the user's monitor, not just code.

Then **STOP. Show it and confirm.** Describe what they should see, and (if possible) screenshot it and
compare pixel-level: spacing, weight, exact colours, radius, alignment. **Confirm it at THREE widths —
~375px (mobile), 768px (tablet), and desktop — not just desktop;** a phone view that overflows, clips, or
is a shrunk desktop is a fail (Law 21). **If the user doesn't like it, ask what to change** (bolder /
lighter / denser / different font / *"make it like <site>"*) and **generate another — loop until they
approve.** **Do not emit `DESIGN.md` until the sample is approved.**

## Step 5 — Emit `DESIGN.md` (only after approval)

Load `references/design-md-template.md` and write **`DESIGN.md`** filling all **9 sections** with the
*concrete approved values* (replace every placeholder — ship nothing un-filled):
*1 Visual Theme · 2 Color & Roles · 3 Typography · 4 Components · 5 Layout · 6 Depth/Elevation ·
7 Motion · 8 Do's & Don'ts · 9 Responsive & Agent Guide.*
- Tokens are **shadcn/ui-compatible CSS variables in OKLCH** (rebrand = change values; plugs into
  shadcn/21st.dev with no theme provider/build step).
- **Emit light AND dark token sets + system switch** (`:root` + `.dark` + `prefers-color-scheme`) — Law 22.
- **Record the page inventory** in §5 (each page type → its layout pattern from `page-patterns.md`).
- **Re-run the WCAG-AA contrast check** on every foreground/surface pair, **in both modes**, before writing (Laws 7 & 22).
- The **Agent Guide** (§9) tells every later build step how to obey this file.
*(Greenfield: `DESIGN.md` is now the harness for new pages. Retrofit-rewrite of existing pages is the
documented follow-up.)*

## Step 6 — Principle-gate self-check, then handoff

**Before handing off, walk `references/universal-laws.md` and confirm all 22 hold** for the sample +
`DESIGN.md` — especially: distinctive font (1), body ≥ min (3), one accent (5), AA contrast *computed* (7),
elevation ladder not flat shadows (9), grid spacing (10), archetype layout (11), no `transition: all` (12), all
interactive states (13), tokens-not-hex (14), reused primitives (15), confirmed via sample (16), real
content (18), table header/cell alignment + dot-not-pill status (20), mobile-first responsive at 3 widths (21),
light+dark+system shipped (22). **If any law fails, STOP and fix it** — the floor is non-negotiable.

Then write `PRODUCT.md#Design` (principles + archetype + token summary + `DESIGN.md`/sample paths) and hand off:

> "Design system agreed and captured in **`DESIGN.md`** (your build harness), proven on an approved
> sample page. Next run **`/foundation`** to stand up the walking skeleton. When you build screens,
> `/new-component` builds against these tokens (reusing shadcn/ui + 21st.dev), and a future
> `/frontend-audit` will enforce `DESIGN.md` + the universal laws across the app."

Report a short **Confidence Score** vs the exit criteria (solid / risky-untested / to-raise-it).
