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

## A. Type & hierarchy (fixes "fonts too small / no hierarchy")

1. **Distinctive display/identity typeface — never a default as the identity.**
   *Why:* Inter / Roboto / Arial / `system-ui` / Helvetica as the *whole identity* is the #1 tell of an
   AI-generated page; it reads as "no decision was made."
   *Law:* the **display/identity face is a deliberate, characterful choice** (Geist, Plus Jakarta Sans, General
   Sans, Space Grotesk, Fraunces/Newsreader for editorial, IBM Plex, a serif). A **neutral grotesque (incl.
   Inter/Roboto) is fine as the BODY/UI face when paired with a distinctive display** (e.g. Inter body +
   Playfair display) — it just can't be the *whole* identity.
   *Check:* `--font-display` is not a generic default; if `--font-sans` is Inter/Roboto/Arial, a distinctive `--font-display` is present.

2. **A real type scale — no random sizes.**
   *Why:* arbitrary `text-[15px]` everywhere = visual noise; a ratio creates rhythm.
   *Law:* sizes come from ONE modular scale (a fixed ratio off a base — see `archetypes.md`). Every
   font-size in the app is a step on that scale.
   *Check:* finite set of sizes, each traceable to the scale; no off-scale one-offs.

3. **Body text never below the archetype minimum.**
   *Why:* the single most common new-user mistake is body copy that's too small to read comfortably.
   *Law:* **app/dashboard body ≥ 16px** (14px floor for genuinely dense data tables, 13px is the
   hard floor for tabular numerals only); **marketing/consumer body ≥ 16–18px**. Never below.
   **Caption tier:** uppercase **labels / overlines / table headers** may be **12px** — the only
   non-numeral exception, and only when uppercase + letter-spaced.
   *Check:* no text token below the archetype's minimum, except 12px uppercase captions and 13px numerals.

4. **Clear hierarchy via weight + size + colour, not size alone.**
   *Why:* heading and subtitle at the same weight look flat and undesigned.
   *Law:* a heading and the text under it differ by **≥ 200 font-weight** OR a clear size step; use a
   muted foreground token for secondary text. Display headings: tight tracking (≈ `-0.02em`).
   *Check:* heading vs. adjacent body differ in weight or size; secondary text uses `--muted-foreground`.

## B. Colour & contrast (fixes "generic purple-gradient AI look")

5. **One dominant + one accent — never a flat even palette.**
   *Why:* five equally-loud colours read as a template; restraint reads as design.
   *Law:* a neutral base (background/surface/foreground) + **exactly one** brand/accent used sparingly
   for primary action and emphasis. Status colours (success/warning/error/info) are *semantic*, not
   decorative.
   *Check:* one `--primary`; accents are not sprinkled across non-interactive elements.

6. **No purple-on-white gradient default; no even rainbow.**
   *Why:* the indigo→violet gradient hero is the canonical "AI made this" signature.
   *Law:* don't ship the default-tailwind palette names (`indigo-500`, `blue-600`) as the brand, and
   don't default to a purple gradient unless the archetype/brand genuinely calls for it.
   *Check:* brand colour is a chosen value in tokens, not a tailwind default; no unjustified purple gradient.

7. **WCAG AA contrast on every text/background pair.**
   *Why:* low-contrast grey-on-white is both an accessibility failure and an "undesigned" tell.
   *Law:* body/UI text ≥ **4.5:1**; large text (≥ 24px or 19px bold) and meaningful UI/icons ≥ **3:1**.
   Verify each text-colour-on-its-surface pair — including muted text and text on coloured buttons.
   **Compute the ratio — never eyeball or assert it.** Semantic **status text** is the usual failure
   (warning-amber especially): **darken the label shade** until it passes on its surface; the status
   **dot/icon may stay brighter** (3:1 graphical). Never ship a colour whose contrast you haven't computed.
   *Check:* compute contrast for every `(--x-foreground on --x)` pair, incl. status labels; none below threshold.

8. **Prefer OKLCH for colour tokens.**
   *Why:* OKLCH is the 2026 norm (shadcn ships it) — perceptually uniform, predictable lightness for
   accessible scales and dark mode.
   *Law:* emit colour tokens in OKLCH (hex fallback fine for legacy). Build shades by varying L, not ad-hoc.
   *Check:* tokens are OKLCH (or a documented reason not to).

## C. Depth, spacing & layout (fixes "flat / cramped / cards-in-cards")

9. **Depth via a deliberate elevation system — never flat `shadow-md` everywhere.**
   *Why:* one flat shadow on everything = no spatial logic; real apps layer.
   *Law:* a small elevation ladder (e.g. base → `--shadow-sm` raised → `--shadow-lg` floating), used
   consistently. **Never nest a bordered+shadowed card inside another** (cards-in-cards).
   *Check:* shadows come from named elevation tokens; no card directly inside a card with both borders.

10. **Spacing on a consistent grid — no arbitrary px.**
    *Why:* random margins read as sloppy; an 8px (or 4px) rhythm reads as intentional.
    *Law:* all spacing is a multiple of the archetype's base unit (usually 4 or 8px). Generous,
    consistent whitespace; group related things, separate unrelated.
    *Check:* spacing values are grid multiples; no off-grid one-offs.

11. **Layout matches the archetype, not a generic centred column.**
    *Why:* a dashboard is not a landing page; using one layout for both is the "artsy-but-wrong" failure.
    *Law:* pick the archetype's layout pattern (sidebar+content for dense apps, top-nav for consumer
    apps, single editorial column for content) — see `archetypes.md`. Respect task density.
    *Check:* the sample page uses the archetype's layout pattern.

## D. Motion & interaction

12. **Animate only `transform` and `opacity`; never `transition: all`.**
    *Why:* animating layout/colour properties janks and re-paints; `transition: all` animates things
    you didn't mean to.
    *Law:* transitions are scoped to `transform`/`opacity` with a sane duration token (≈150–250ms) and
    an ease. Respect `prefers-reduced-motion`. Motion must *earn its place* (feedback/continuity), not decorate.
    *Check:* no `transition: all` / `transition-all`; transition properties are transform/opacity.

13. **Every interactive element has hover + focus-visible + active states.**
    *Why:* missing states (especially `:focus-visible`) is both an a11y failure and an "undesigned" tell.
    *Law:* buttons/links/inputs define hover, **focus-visible** (keyboard), and active/pressed; disabled
    is visually distinct. Keyboard reachable, semantic markup (`PRINCIPLES.md` *Accessibility*).
    *Check:* interactive components define all three states + a visible focus ring.

## E. Tokens & reuse (fixes "raw hex everywhere / hand-rolled components")

14. **Tokens only — no raw hex / raw font strings in components.**
    *Why:* a hardcoded `#1A2540` can't theme, can't rebrand, and drifts; this is the no-hardcoding law
    applied to UI.
    *Law:* components reference CSS variables (`var(--primary)`, `var(--font-sans)`, `var(--radius)`),
    never literal colours/fonts. Rebrand = change token values, nothing else (shadcn contract).
    *Check:* no raw hex or raw font-family literal inside component code.

15. **Reuse accessible, animated primitives — never hand-roll buttons/inputs/modals.**
    *Why:* a hand-built modal/menu will miss focus-trap, ARIA, keyboard nav; the ecosystem already
    solved this. Hand-rolling is the "competing trap" — compose, don't author.
    *Law:* pull primitives from **shadcn/ui + 21st.dev** (and re-skin with the tokens). New users get
    production-grade, accessible, animated components for free.
    *Check:* interactive primitives come from the registry, re-skinned via tokens.

## F. Process laws (how the skill itself must behave)

16. **Always confirm with a visible sample BEFORE propagating.**
    *Why:* "decide-for-you" can misread the product; the sample-confirm loop is the safety mechanism.
    *Law:* build ONE real sample screen, **STOP**, and get explicit approval — iterating until liked —
    before emitting `DESIGN.md` system-wide.

17. **Decide FOR the non-designer, with the reason explained.**
    *Why:* a beginner wants a confident default + to learn *why*, not a jargon matrix.
    *Law:* give ONE recommended default at every choice (font, archetype, scale) with a plain-language
    why; offer the alternative as a yes/no. Never dump options without a recommendation.

18. **Real content, never lorem.**
    *Why:* lorem hides hierarchy and length problems; real strings expose them.
    *Law:* sample pages use plausible real content drawn from the product's actual domain/vision.

19. **Honest boundary — don't oversell.**
    *Why:* for a simple pretty/marketing splash, Anthropic's `frontend-design` is the better tool; this
    skill's edge is *real apps* (enterprise, dense, existing codebases, disciplined builds).
    *Law:* if the product is a simple marketing/brochure page, say so and point the user to `frontend-design`.

## G. Data tables (fixes "misaligned columns / badge-on-every-row")

20. **A data table's header alignment matches its cell alignment, per column.**
    *Why:* a left-aligned "DUE" header sitting over right-aligned dates (or vice-versa) reads as broken —
    one of the most common, most visible table mistakes.
    *Law:* for every column the `<th>` and `<td>` share **one** alignment. **Numbers right-aligned** with
    **tabular figures** (`font-variant-numeric: tabular-nums`); **text and dates left-aligned**; IDs/amounts in mono.
    **Status cells = a coloured dot + label, NOT a filled pastel pill** (the filled-badge default is a generic/AI tell).
    *Check:* each column's header and cells share an alignment; numeric columns are right + tabular; no filled status pills.

## H. Responsive & mobile (fixes "looks fine on the laptop, breaks on a phone")

21. **Design the mobile experience first — never ship a shrunk desktop.**
    *Why (how a designer thinks):* a phone user isn't a small-screen desktop user — they have **one goal,
    one thumb, and no hover.** A senior designer decides *what matters most on a phone* and builds **up**,
    not down. Responsive is a design decision (what to show, hide, reflow), not just a CSS afterthought.
    *Law:* **mobile-first** — base styles target the smallest screen; complexity is added upward.
    - **Content priority / progressive disclosure:** lead with the user's #1 mobile job; demote, hide, or
      tap-to-reveal the rest. Don't cram the desktop in.
    - **Touch ergonomics:** primary actions thumb-reachable; tap targets **≥ 44px**; no hover-only controls.
    - **Adapt the layout to the device** via the archetype's collapse pattern — sidebar → drawer/Sheet,
      data table → stacked cards, detail panel → Sheet/bottom-sheet, KPI grid → reflow (see `archetypes.md`).
    - **Mechanics:** `<meta name="viewport">` present; **container queries** for components, **media queries**
      for page layout; **fluid type** via `clamp()`; **no fixed width > ~360px without a collapse**;
      breakpoints where content breaks (mobile <640 · tablet 640–1024 · desktop ≥1024 — laptop = monitor = desktop).
    *Check:* viewport meta present; any multi-column/grid page has ≥1 `@media`/`@container` breakpoint; no fixed
    pixel layout width without a responsive fallback; **the sample is confirmed at ~375 / 768 / desktop.**

## I. Theming (light, dark & system)

22. **Ship light AND dark, and follow the system preference — by default.**
    *Why (how a designer thinks):* users expect their OS choice respected; one-mode-only feels dated in 2026, and
    dark is not just inverted light — it needs its **own** AA-checked values.
    *Law:* emit **both** a `:root` (light) and `.dark` token set (shadcn contract) and switch on
    `prefers-color-scheme` (+ an optional manual toggle). **Contrast (Law 7) holds in BOTH modes.** A deliberately
    single-mode product (e.g. a cinematic dark tool) states *why* and still provides a usable alternate.
    *Check:* a `.dark` (or equivalent) token block exists; foreground/surface pairs pass AA in **both** modes.

---

### The contract, in one line
**`/design-system` output = these 22 universal laws (the guaranteed floor) + the per-product principles
derived in Step 1 (the specific look).** The laws make it impossible to ship something generic, inaccessible,
broken-on-mobile, or single-mode-by-accident; the principles make it *this* product's own.
