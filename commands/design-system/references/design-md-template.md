# `DESIGN.md` template — the 9-section standard + shadcn tokens

> Loaded by `/design-system` (Step 5). `DESIGN.md` is the **persistent design harness** every later
> build step reads. Adopt the **9-section open standard** (popularised by Google Stitch + the
> awesome-claude-design `DESIGN.md` systems) — **don't invent a private format.**
>
> Tokens are emitted as **shadcn/ui-compatible CSS variables** so the 2026 contract holds: *rebrand =
> change token values, no theme provider, no build step*, and it plugs straight into shadcn/ui + 21st.dev.
> Emit colours in **OKLCH** (Law 8) and **verify every foreground/surface pair at WCAG AA** (Law 7)
> before writing.
>
> Fill the skeleton with the **concrete** values chosen in Steps 2–3 (archetype presets). Two worked
> examples follow — one **enterprise** (Data-Dense Pro), one **consumer** (Playful) — so the contrast is
> visible. **Replace every `<…>`; ship no placeholders.**

---

## The skeleton (9 sections)

```markdown
# DESIGN.md — <Product> design system
_Archetype: <family> · derived by /design-system on <date> · approved sample: <path>_

## 1. Visual Theme
- **Principles (from Step 1):** <4–6 short statements, e.g. "Calm authority · Density without clutter · Evidence first · Accessible by default">
- **Archetype:** <family> — <one line why it fits the product/audience>
- **Feel in one line:** <e.g. "A calm, dense, trustworthy compliance workspace.">
- **Reference brands:** <2–3 real products this should feel adjacent to>

## 2. Color & Roles  (shadcn CSS-variable tokens, OKLCH, WCAG-AA verified)
- **Brand decision:** <dominant + ONE accent — Law 5>
- **Contrast check:** <every text/surface pair ≥ AA — list the computed ratios>
:root {
  --background: <oklch>;        --foreground: <oklch>;
  --card: <oklch>;              --card-foreground: <oklch>;
  --popover: <oklch>;           --popover-foreground: <oklch>;
  --primary: <oklch>;           --primary-foreground: <oklch>;
  --secondary: <oklch>;         --secondary-foreground: <oklch>;
  --muted: <oklch>;             --muted-foreground: <oklch>;
  --accent: <oklch>;            --accent-foreground: <oklch>;
  --destructive: <oklch>;       --destructive-foreground: <oklch>;
  --success: <oklch>;  --warning: <oklch>;  --info: <oklch>;   /* semantic status */
  --border: <oklch>;   --input: <oklch>;    --ring: <oklch>;
  --radius: <rem>;
}
.dark { /* same keys, dark values — keep AA */ }

## 3. Typography
- **Fonts:** display `--font-display: <face>` · body `--font-sans: <face>` · data `--font-mono: <face>`
  (Law 1 — no Inter/Roboto/Arial-only). How to load: <next/font | @font-face | CDN>.
- **Base body size:** <px — meets archetype minimum, Law 3> · **Scale ratio:** <1.2 | 1.25 | 1.333>
- **Type scale (the steps):**
  | token | size | line-height | weight | use |
  |---|---|---|---|---|
  | display | <px> | <lh> | <800> | hero / page title |
  | h1 | <px> | <lh> | <700> | section title |
  | h2 | <px> | <lh> | <600> | subsection |
  | body | <px> | <1.6> | <400–500> | paragraphs / UI |
  | small | <px> | <lh> | <500> | metadata |
  | mono | <px> | <lh> | <400–500> | IDs / numbers / code |
- **Hierarchy rule:** heading vs body differ by ≥200 weight or a clear size step (Law 4).

## 4. Components  (reuse — never hand-roll, Law 15)
- **Source:** shadcn/ui + 21st.dev primitives, re-skinned with the tokens above.
- **Key components + their look:** Button (variants <primary/secondary/ghost>, radius, padding) ·
  Input · Card · Table/DataGrid · Nav/Sidebar · Dialog · Toast · Badge/Status.
- **Table/DataGrid (Law 20):** header alignment matches cells; **numbers right-aligned + tabular-nums**;
  **dates/text left**; **status = coloured dot + label, not a filled pastel pill.**
- **States (Law 13):** every interactive element defines hover · focus-visible (visible ring) · active · disabled.

## 5. Layout  (archetype pattern, Law 11)
- **Pattern:** <sidebar+content | top-nav app | single editorial column | bottom-tab mobile>
- **Density:** <compact | medium | airy> · **Grid base:** <4px | 8px> · **Container max-width:** <px>
- **Page anatomy:** <sidebar / top bar / content / detail panel — what goes where>

## 6. Depth & Elevation  (Law 9)
- **Ladder:** base (`--background`) → raised `--shadow-sm` → floating `--shadow-lg`.
  --shadow-sm: <…>;  --shadow-md: <…>;  --shadow-lg: <…>;
- **Borders:** `--border` default, strong for emphasis. **No cards-in-cards.**

## 7. Motion  (Law 12)
- **Tokens:** `--transition: <150–250ms> <ease>`; animate **transform/opacity only**; honour
  `prefers-reduced-motion`. **No `transition: all`.**
- **Where motion is allowed:** <hover feedback · overlay enter/exit · scroll reveal> — and where it isn't.

## 8. Do's & Don'ts  (kills the generic AI look)
- **Do:** <5 product-specific do's — e.g. "lead with the evidence table", "use mono for vendor IDs">
- **Don't:** <5 don'ts — e.g. "no purple gradient", "no body text under 14px", "no flat shadow-md on cards",
  "no raw hex in components", "no Inter as the primary face">

## 9. Responsive & Agent Guide  (mobile-first, Law 21)
- **Approach:** mobile-first — design the phone first, scale up. Breakpoints (where content breaks): mobile <640 · tablet 640–1024 · desktop >=1024. Container queries for components, media queries for page layout; fluid type via clamp().
- **Mobile content priority:** <the user's #1 mobile job leads; what is demoted / hidden / tap-to-reveal>. Tap targets >=44px; no hover-only controls.
- **Per-component collapse (fill in):** nav/sidebar <persistent -> drawer/Sheet> · data table <full -> stacked cards> · detail panel <side -> bottom Sheet> · KPI grid <N-col -> 1-col>.
- **Agent guide (how a build step/LLM uses this file):** always reference tokens (never raw hex/font);
  pull components from shadcn/ui + 21st.dev and skin with these tokens; keep body ≥ <min>px; run the
  contrast check on any new colour; obey the universal laws. `/new-component` builds against this;
  `/frontend-audit` enforces it.
```

---

## Worked example A — Enterprise (Data-Dense Pro)

```css
:root {
  --background: oklch(0.99 0.002 250);   /* near-white, faint cool */
  --foreground: oklch(0.22 0.01 250);    /* ink — 12.8:1 on bg ✓AA */
  --card: oklch(1 0 0);                  --card-foreground: oklch(0.22 0.01 250);
  --primary: oklch(0.52 0.13 250);       /* restrained indigo-slate (a chosen value, not tailwind-blue) */
  --primary-foreground: oklch(0.99 0.002 250);  /* 5.1:1 ✓AA */
  --muted: oklch(0.96 0.004 250);        --muted-foreground: oklch(0.46 0.01 250); /* 4.7:1 ✓AA */
  --accent: oklch(0.52 0.13 250);        --accent-foreground: oklch(0.99 0.002 250);
  --success: oklch(0.6 0.13 150);  --warning: oklch(0.7 0.15 80);  --destructive: oklch(0.55 0.2 25);
  --border: oklch(0.92 0.004 250);       --input: oklch(0.92 0.004 250);  --ring: oklch(0.52 0.13 250);
  --radius: 0.5rem;
  --font-display: "Geist", sans-serif;  --font-sans: "Geist", sans-serif;  --font-mono: "IBM Plex Mono", monospace;
  --shadow-sm: 0 1px 2px oklch(0.22 0.01 250 / 0.06);
  --shadow-lg: 0 10px 30px oklch(0.22 0.01 250 / 0.12);
  --transition: 160ms cubic-bezier(0.4,0,0.2,1);
}
```
- **Body 14px UI / 16px readable / 13px table numerals · scale 1.2 · 4px grid.**
- **Layout:** left sidebar + dense top bar + data table + right detail panel.
- **Do:** lead with the evidence table; mono for vendor/run IDs; status chips semantic.
- **Don't:** no purple gradient; no body under 14px; no flat shadow on every card; no Inter.

## Worked example B — Consumer (Playful)

```css
:root {
  --background: oklch(0.99 0.01 95);     /* warm off-white */
  --foreground: oklch(0.25 0.02 60);     /* warm ink — ✓AA */
  --primary: oklch(0.7 0.18 25);         /* vivid coral (one dominant, Law 5) */
  --primary-foreground: oklch(0.99 0.01 95);
  --accent: oklch(0.8 0.13 200);         /* friendly secondary */
  --muted: oklch(0.95 0.01 95);          --muted-foreground: oklch(0.5 0.02 60); /* ✓AA */
  --success: oklch(0.7 0.15 150);  --destructive: oklch(0.6 0.2 25);
  --border: oklch(0.9 0.01 95);    --ring: oklch(0.7 0.18 25);
  --radius: 1rem;                        /* rounded, friendly */
  --font-display: "Plus Jakarta Sans", sans-serif;  --font-sans: "Plus Jakarta Sans", sans-serif;
  --shadow-lg: 0 12px 32px oklch(0.7 0.18 25 / 0.18);   /* accent-tinted */
  --transition: 280ms cubic-bezier(0.34,1.56,0.64,1);   /* springy */
}
```
- **Body 17px · scale 1.333 · 8px grid · bold weights.**
- **Layout:** top-nav (or bottom-tab mobile), big touch targets, cards, illustration.
- **Do:** big confident headings; accent-tinted soft shadows; lively but transform/opacity-only motion.
- **Don't:** no five-equal-colour rainbow; no tiny type; no `transition: all`.

---

### Notes
- **Two layers:** the tokens above are derived per product (the *look*); the **universal laws** in
  `universal-laws.md` are the floor every `DESIGN.md` must also satisfy. Both are non-negotiable.
- **shadcn install:** these variables map 1:1 onto shadcn/ui's `globals.css` `:root`/`.dark` blocks —
  paste them in and the whole component library re-skins. 21st.dev components consume the same tokens.
