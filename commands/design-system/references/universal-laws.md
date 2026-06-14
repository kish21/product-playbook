# Universal UI Laws — the quality floor (always enforced)

> Loaded by `/design-system`. These are **fixed rules — the same for every product, every user,
> every run.** They are the floor of quality: the look (archetype, colour, type) changes per product,
> but these never bend. This is where *"never look AI-generated"* lives — made **concrete and
> checkable**, not a vibe.
>
> They **extend** product-playbook's `PRINCIPLES.md` (see its *Accessibility (UI)* line and the
> 5-step spine) — they do not duplicate it. PRINCIPLES.md owns the engineering bar; this file owns
> the **visual-design** bar. If a derived per-product principle (Step 1) ever conflicts with a law
> here, **the law wins** — say so to the user and adjust the principle.

**These laws don't *design* — a designer does (SKILL.md Steps 1–4). The laws are the *enforcement
floor* that guarantees a non-designer's output can't fall below a professional baseline.** Designer
reasoning *leads*; the laws *catch*. Each law has a one-line **why** (teach-mode) and a **check** (so
`/frontend-audit` can enforce it mechanically).

---

## How to read these — outcome, not tool

A rule only earns the word *law* if it states **an outcome that holds regardless of stack, aesthetic,
or motion level.** Where a rule named a specific tool or a specific look, it was a *means* wearing a
law's costume — the usual source of contradiction (e.g. "use shadcn" can't be obeyed on a canvas game,
a non-React stack, or a standalone preview). The fix: **the outcome is the law; the tool/look is a
recommendation that varies.** Every rule below is tagged with one of:

- **`[FLOOR]`** — a universal outcome. True for *any* product, stack, or aesthetic. `/frontend-audit`
  enforces these mechanically. **Non-negotiable.**
- **`[MEANS]`** — the recommended *way* to achieve a floor on a given stack/archetype (shadcn, OKLCH,
  GSAP…). **Swap it freely** as long as the floor it serves is still met. A `[MEANS]` is advice, not a gate.
- **`[AESTHETIC]`** — a strong anti-"AI-look" default that prescribes one concrete choice. The *outcome*
  is the floor; the named choice is the canonical example, not the only valid answer.
- **`[PROCESS]`** — how the skill must *behave* while producing the design (it governs the run, not the
  artifact). Not something `/frontend-audit` checks on a built page.

### The 22 rules, grouped by category

- **`[FLOOR]` (the mechanical gate):** 1 · 2 · 3 · 4 · 5 (restraint) · 7 · 9 · 10 · 11 · 13 · 14 · 15 (accessible components) · 20 (alignment) · 21 · 22
- **`[MEANS]` (recommendations — swap per stack/archetype):** 8 (OKLCH) · 12 (motion-library ladder) · 15 (shadcn/21st.dev)
- **`[AESTHETIC]` (outcome + canonical example):** 6 (no default/gradient) · 20 (status = dot, not pill)
- **`[PROCESS]` (skill behaviour, not artifact):** 16 · 17 · 18 · 19

> Several rules (12, 15, 20) split across categories: a fixed **floor** + a **means/aesthetic** that
> varies. The numbering 1–22 is kept stable because other files reference laws by number.

---

## A. Type & hierarchy (fixes "fonts too small / no hierarchy")

1. **Distinctive display/identity typeface — never a default as the identity.** · `[FLOOR]`
   *Why:* Inter / Roboto / Arial / `system-ui` / Helvetica as the *whole identity* is the #1 tell of an
   AI-generated page; it reads as "no decision was made."
   *Law:* the **display/identity face is a deliberate, characterful choice** (Geist, Plus Jakarta Sans, General
   Sans, Space Grotesk, Fraunces/Newsreader for editorial, IBM Plex, a serif). A **neutral grotesque (incl.
   Inter/Roboto) is fine as the BODY/UI face when paired with a distinctive display** (e.g. Inter body +
   Playfair display) — it just can't be the *whole* identity. **A near-twin of the body face (e.g. Inter Tight
   over Inter) is NOT a distinctive display — it fails this floor.**
   *Check:* `--font-display` is not a generic default and is not a weight/width variant of `--font-sans`; if `--font-sans` is Inter/Roboto/Arial, a genuinely distinct `--font-display` is present.

2. **A real type scale — no random sizes.** · `[FLOOR]`
   *Why:* arbitrary `text-[15px]` everywhere = visual noise; a ratio creates rhythm.
   *Law:* sizes come from ONE modular scale (a fixed ratio off a base — see `archetypes.md`). Every
   font-size in the app is a step on that scale.
   *Check:* finite set of sizes, each traceable to the scale; no off-scale one-offs.

3. **Body text never below the archetype minimum.** · `[FLOOR]`
   *Why:* the single most common new-user mistake is body copy that's too small to read comfortably.
   *Law:* **app/dashboard body ≥ 16px** (14px floor for genuinely dense data tables, 13px is the
   hard floor for tabular numerals only); **marketing/consumer body ≥ 16–18px**. Never below.
   **Caption tier:** uppercase **labels / overlines / table headers** may be **12px** — the only
   non-numeral exception, and only when uppercase + letter-spaced.
   *Check:* no text token below the archetype's minimum, except 12px uppercase captions and 13px numerals.

4. **Clear hierarchy via weight + size + colour, not size alone.** · `[FLOOR]`
   *Why:* heading and subtitle at the same weight look flat and undesigned.
   *Law:* a heading and the text under it differ by **≥ 200 font-weight** OR a clear size step; use a
   muted foreground token for secondary text. Display headings: tight tracking (≈ `-0.02em`).
   *Check:* heading vs. adjacent body differ in weight or size; secondary text uses `--muted-foreground`.

## B. Colour & contrast (fixes "generic purple-gradient AI look")

5. **One dominant + one accent — never a flat even palette.** · `[FLOOR]` (restraint outcome)
   *Why:* five equally-loud colours read as a template; restraint reads as design.
   *Law:* a neutral base (background/surface/foreground) + **one** brand/accent used sparingly
   for primary action and emphasis. Status colours (success/warning/error/info) are *semantic*, not
   decorative. *(A brand may legitimately run two accents — the floor is **restraint**, not literally "one";
   what fails is a flat rainbow where everything competes.)*
   *Check:* a single dominant accent role; accents are not sprinkled across non-interactive elements.

6. **Brand colour is a deliberate value — never a framework default, no unjustified gradient.** · `[AESTHETIC]` (outcome + example)
   *Why:* the underlying failure is *no colour decision was made*. The canonical signature of that failure is
   the indigo→violet gradient hero and raw tailwind palette names shipped as the brand.
   *Outcome (law):* the brand colour is a chosen token; gradients appear only when the archetype/brand genuinely
   calls for one.
   *Canonical example to avoid:* purple-on-white gradient; `indigo-500`/`blue-600` as the brand.
   *Check:* brand colour is a chosen token, not a framework default; no unjustified gradient.

7. **WCAG AA contrast on every text/background pair.** · `[FLOOR]`
   *Why:* low-contrast grey-on-white is both an accessibility failure and an "undesigned" tell.
   *Law:* body/UI text ≥ **4.5:1**; large text (≥ 24px or 19px bold) and meaningful UI/icons ≥ **3:1**.
   Verify each text-colour-on-its-surface pair — including muted text and text on coloured buttons.
   **Compute the ratio — never eyeball or assert it.** A `/* ~13:1 */` comment is NOT compliance; run the
   contrast engine (`/frontend-audit`). Semantic **status text** is the usual failure (warning-amber
   especially): **darken the label shade** until it passes on its surface; the status **dot/icon may stay
   brighter** (3:1 graphical). Never ship a colour whose contrast you haven't computed.
   *Check:* compute contrast for every `(--x-foreground on --x)` pair, incl. status labels; none below threshold.

8. **Colour tokens scale lightness predictably (accessible shades + real dark mode).** · `[MEANS]` (recommend OKLCH)
   *Why:* if shades are picked ad-hoc, accessible scales and a real dark mode can't be derived reliably.
   *Outcome (law):* colour tokens are built by varying **lightness** along a scale, so AA-correct shades and a
   distinct dark set are derivable — not hand-picked per use.
   *Recommended means:* express tokens in **OKLCH** (the 2026 norm; shadcn ships it — perceptually uniform,
   predictable L). Hex fallback is fine for legacy; the floor is "predictable lightness," not the format.
   *Check:* shades vary by lightness on a scale (OKLCH preferred); no ad-hoc per-component colours.

## C. Depth, spacing & layout (fixes "flat / cramped / cards-in-cards")

9. **Depth via a deliberate elevation system — never flat `shadow-md` everywhere.** · `[FLOOR]`
   *Why:* one flat shadow on everything = no spatial logic; real apps layer.
   *Law:* a small elevation ladder (e.g. base → `--shadow-sm` raised → `--shadow-lg` floating), used
   consistently. **Never nest a bordered+shadowed card inside another** (cards-in-cards).
   *Check:* shadows come from named elevation tokens; no card directly inside a card with both borders.

10. **Spacing on a consistent grid — no arbitrary px.** · `[FLOOR]`
    *Why:* random margins read as sloppy; an 8px (or 4px) rhythm reads as intentional.
    *Law:* all spacing is a multiple of the archetype's base unit (usually 4 or 8px). Generous,
    consistent whitespace; group related things, separate unrelated.
    *Check:* spacing values are grid multiples; no off-grid one-offs.

11. **Layout matches the archetype, not a generic centred column.** · `[FLOOR]`
    *Why:* a dashboard is not a landing page; using one layout for both is the "artsy-but-wrong" failure.
    *Law:* pick the archetype's layout pattern (sidebar+content for dense apps, top-nav for consumer
    apps, single editorial column for content) — see `archetypes.md`. Respect task density.
    *Check:* the sample page uses the archetype's layout pattern.

## D. Motion & interaction

12. **Motion is performant and reduced-motion-safe, and earns its place.** · `[FLOOR]` + `[MEANS]` (library ladder)
    *Why:* animating layout/colour properties janks and re-paints; `transition: all` animates things
    you didn't mean to; un-gated motion harms users who opt out.
    *Floor (law — always true):* transitions target only **`transform`/`opacity`** with a sane duration
    (≈150–250ms) and an ease; **never `transition: all`**; never animate paint/layout props
    (width/height/top/left/margin/box-shadow/background). Any motion beyond simple feedback is wrapped in
    `@media (prefers-reduced-motion: reduce)` with a static fallback. Motion *earns its place*
    (feedback/continuity), never decorates.
    *Check (floor):* no `transition: all`/`transition-all`; transition properties are transform/opacity;
    any Tier ≥ 1 library implies a `prefers-reduced-motion` guard; no duration > ~1000ms outside an
    intentional scroll-driven effect.

    **`[MEANS]` — the 4-tier library ladder (a recommendation that scales with the product's chosen motion
    level; pick the lowest tier that expresses the intent, never exceed the archetype's ceiling in
    `archetypes.md`):**
    - **Tier 0 — CSS transitions/keyframes (default, ~90% of products).** Hover/focus/active feedback,
      overlay enter/exit, scroll-reveal via Intersection Observer. `transform`/`opacity`, 150–300ms.
    - **Tier 1 — Framer Motion (`motion/react`).** Orchestrated/staggered sequences, layout & shared-element
      transitions, gesture/drag feedback in React — when choreography exceeds what CSS expresses cleanly.
    - **Tier 2 — GSAP (+ ScrollTrigger).** Scroll-driven storytelling: pinned/parallax sections, timelines
      where scroll progress *drives* the animation. Marketing / editorial / cinematic pages.
    - **Tier 3 — Three.js / WebGL (React Three Fiber).** A genuine 3D/shader **hero moment** — highest cost
      (bundle, perf, complexity). **Cinematic / Marketing-Splash / Glass archetypes ONLY** — never
      dashboards, data-dense, forms, conversational, or social feeds.

    **Whichever tier you pick, the floor above still holds:** lazy-load the library (keep it out of the
    critical bundle), hold a 60fps / no-main-thread-jank budget, ship the `prefers-reduced-motion` fallback,
    and make the motion serve the vision. The *tier* is the means; the *floor* is fixed.

13. **Every interactive element has hover + focus-visible + active states.** · `[FLOOR]`
    *Why:* missing states (especially `:focus-visible`) is both an a11y failure and an "undesigned" tell.
    *Law:* buttons/links/inputs define hover, **focus-visible** (keyboard), and active/pressed; disabled
    is visually distinct. Keyboard reachable, semantic markup (`PRINCIPLES.md` *Accessibility*).
    *Check:* interactive components define all three states + a visible focus ring.

## E. Tokens & reuse (fixes "raw hex everywhere / hand-rolled components")

14. **Tokens only — no raw hex / raw font strings in components.** · `[FLOOR]`
    *Why:* a hardcoded `#1A2540` can't theme, can't rebrand, and drifts; this is the no-hardcoding law
    applied to UI.
    *Law:* components reference CSS variables (`var(--primary)`, `var(--font-sans)`, `var(--radius)`),
    never literal colours/fonts. Rebrand = change token values, nothing else (shadcn contract).
    *Check:* no raw hex or raw font-family literal inside component code.

15. **Interactive components meet the accessibility floor — don't naively hand-author them.** · `[FLOOR]` + `[MEANS]` (shadcn/21st.dev)
    *Why:* a hand-built modal/menu silently misses focus-trap, ARIA roles, and keyboard nav; the ecosystem
    already solved this. The failure isn't "wrote CSS" — it's *shipping an inaccessible primitive*.
    *Floor (law — always true, any stack):* every interactive primitive (button, input, select, dialog/modal,
    menu, tabs, tooltip, combobox) provides **focus management** (focus-trap + restore for overlays), correct
    **ARIA** roles/states, full **keyboard navigation**, and all of Law 13's states. Don't naively re-author
    these and drop those guarantees.
    *Recommended means:* on a **React stack**, get all of this for free from **shadcn/ui + 21st.dev**,
    re-skinned with the tokens — never re-author what the registry already solved. On a **non-React stack,
    standalone preview, or non-DOM surface (canvas/WebGL/TUI)**, use or vendor an **equally accessible**
    primitive set; the floor is *accessible components*, not *this library*.
    *Check:* interactive primitives provide focus/ARIA/keyboard/states (Law 13); on a React build they are
    sourced from the registry and re-skinned via tokens, not hand-authored.

## F. Process laws (how the skill itself must behave)

16. **Always confirm with a visible sample BEFORE propagating.** · `[PROCESS]`
    *Why:* "decide-for-you" can misread the product; the sample-confirm loop is the safety mechanism.
    *Law:* build ONE real sample screen, **STOP**, and get explicit approval — iterating until liked —
    before emitting `DESIGN.md` system-wide.

17. **Decide FOR the non-designer, with the reason explained.** · `[PROCESS]`
    *Why:* a beginner wants a confident default + to learn *why*, not a jargon matrix.
    *Law:* give ONE recommended default at every choice (font, archetype, scale) with a plain-language
    why; offer the alternative as a yes/no. Never dump options without a recommendation.

18. **Real content, never lorem.** · `[PROCESS]` (content floor)
    *Why:* lorem hides hierarchy and length problems; real strings expose them.
    *Law:* sample pages use plausible real content drawn from the product's actual domain/vision.

19. **Honest boundary — don't oversell.** · `[PROCESS]`
    *Why:* for a simple pretty/marketing splash, Anthropic's `frontend-design` is the better tool; this
    skill's edge is *real apps* (enterprise, dense, existing codebases, disciplined builds). For a **bespoke,
    non-document surface** (canvas/WebGL game, generative art, a pure-CLI/TUI) the token+component machinery
    does **not** apply — say so and decline gracefully rather than force a `DESIGN.md`.
    *Law:* if the product is a simple marketing/brochure page, point the user to `frontend-design`; if it is a
    bespoke/non-document surface, state that this skill doesn't apply and stop.

## G. Data tables (fixes "misaligned columns / badge-on-every-row")

20. **Table columns: header alignment matches cell alignment; status is low-noise.** · `[FLOOR]` (alignment) + `[AESTHETIC]` (status style)
    *Why:* a left-aligned "DUE" header over right-aligned dates reads as broken — one of the most common,
    most visible table mistakes; and a filled pastel badge on every row is a generic/AI tell.
    *Floor (law):* for every column the `<th>` and `<td>` share **one** alignment. **Numbers right-aligned**
    with **tabular figures** (`font-variant-numeric: tabular-nums`); **text and dates left-aligned**;
    IDs/amounts in mono.
    *Outcome (status):* status must **not shout** — don't put a loud filled pill on every row.
    *Canonical example:* a coloured **dot + label**, not a filled pastel pill.
    *Check:* each column's header and cells share an alignment; numeric columns are right + tabular; status is
    low-noise (dot+label preferred; no filled pills on every row).

## H. Responsive & mobile (fixes "looks fine on the laptop, breaks on a phone")

21. **Design the mobile experience first — never ship a shrunk desktop.** · `[FLOOR]`
    *Why (how a designer thinks):* a phone user isn't a small-screen desktop user — they have **one goal,
    one thumb, and no hover.** A senior designer decides *what matters most on a phone* and builds **up**,
    not down. Responsive is a design decision (what to show, hide, reflow), not just a CSS afterthought.
    *Law:* **mobile-first** — base styles target the smallest screen; complexity is added upward. A
    desktop-first sheet with `max-width` overrides shrinking down is the failure this law names.
    - **Content priority / progressive disclosure:** lead with the user's #1 mobile job; demote, hide, or
      tap-to-reveal the rest. Don't cram the desktop in.
    - **Touch ergonomics:** primary actions thumb-reachable; tap targets **≥ 44px**; no hover-only controls.
    - **Adapt the layout to the device** via the archetype's collapse pattern — sidebar → drawer/Sheet,
      data table → stacked cards, detail panel → Sheet/bottom-sheet, KPI grid → reflow (see `archetypes.md`).
    - **Mechanics:** `<meta name="viewport">` present; **container queries** for components, **media queries**
      for page layout; **fluid type** via `clamp()`; **no fixed width > ~360px without a collapse**;
      breakpoints where content breaks (mobile <640 · tablet 640–1024 · desktop ≥1024 — laptop = monitor = desktop).
    *Check:* viewport meta present; base styles target small screen (min-width queries add complexity up); any
    multi-column/grid page has ≥1 breakpoint; no fixed pixel layout width without a responsive fallback;
    **the sample is confirmed at ~375 / 768 / desktop.**

## I. Theming (light, dark & system)

22. **Ship light AND dark, and follow the system preference — by default.** · `[FLOOR]`
    *Why (how a designer thinks):* users expect their OS choice respected; one-mode-only feels dated in 2026, and
    dark is not just inverted light — it needs its **own** AA-checked values.
    *Law:* emit **both** a `:root` (light) and `.dark` token set (shadcn contract) and **switch the token set on
    `prefers-color-scheme`** (a media query that only sets `color-scheme` without swapping the variables does NOT
    satisfy this — system-auto dark must actually apply the dark values), plus an optional manual toggle.
    **Contrast (Law 7) holds in BOTH modes.** A deliberately single-mode product (e.g. a cinematic dark tool)
    states *why* and still provides a usable alternate.
    *Check:* a `.dark` (or equivalent) token block exists AND `prefers-color-scheme: dark` applies it; foreground/surface pairs pass AA in **both** modes.

---

### The contract, in one line
**`/design-system` output = the `[FLOOR]` laws (the guaranteed, mechanically-enforced floor) + the per-product
principles from Step 1 (the specific look), achieved through `[MEANS]` chosen per stack/archetype, produced under
the `[PROCESS]` laws.** The floors make it impossible to ship something generic, inaccessible, broken-on-mobile, or
single-mode-by-accident — regardless of what the user wanted to build; the principles and means make it *this*
product's own. A rule is only a *law* if it holds no matter the stack, aesthetic, or motion level — anything that
names a specific tool or look is a recommendation, and is tagged as such.
