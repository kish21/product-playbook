# Archetypes — aesthetic families → concrete presets

> Loaded by `/design-system` (Steps 2–3). Maps the product's **principles** to one of ~9 **aesthetic
> families**, each carrying *concrete* defaults: base font size, type scale, density, spacing grid,
> font pairing, colour-role guidance, **layout pattern**, **motion**, and representative real brands.
>
> **The concrete numbers are the whole point** — the popular skills (incl. Anthropic's `frontend-design`)
> ship NO numbers and NO enterprise/consumer split, which is the root cause of *"fonts too small /
> artsy-but-wrong."* These presets are the unglamorous, decided-for-you part.
>
> Sources reused (don't re-author): the aesthetic-family taxonomy + 3-question picker from the
> awesome-claude-design collections (rohitg00 / VoltAgent), enterprise-dashboard typography numbers
> (Stephanie Walter / dashboard-typography writing), the user's own `UI_guide` pattern taxonomy
> (Typography · ColorHierarchy · SpacingRhythm · Layout · Navigation · Forms · Cards · InteractiveStates
> · Responsive · Accessibility), and shadcn/ui + 21st.dev for the components. **We reuse the families
> and numbers — NOT the generic styling defaults** (Inter / tailwind-blue / grey) those prototypes carry.

---

## The 3-question picker (decide the archetype FOR the user)

Ask the user — plain language, one recommended answer each:

1. **Read-heavy or scan-heavy?** Long-form reading (article, docs) → editorial. Scanning lots of data
   fast (dashboard, tables, admin) → data-dense. A focused task flow (form, checkout) → calm/minimal.
2. **Who uses it, and where?** Expert/internal users many hours a day → density + restraint. First-time
   consumers, mobile, marketing → warmth + bold + bigger type.
3. **Calm authority or bold energy?** Trust/compliance/finance/health → calm. Fun/creator/growth → bold.

Map the answers to a family below, **propose ONE as the default with the why**, then ask: *"Do you
already have a look in mind — a product you admire, or bold vs minimal?"* The user's reference/idea
wins; otherwise the proposal stands.

---

## The families (concrete presets)

> **Type scale ratios:** minor-third 1.2 · major-third 1.25 · perfect-fourth 1.333 · golden 1.618.
> Denser product → smaller ratio (1.2). Marketing → larger ratio (1.25–1.333) for big display jumps.
> **Font pairings avoid Inter/Roboto/Arial as the *primary* (Law 1).** All listed faces are free/OSS
> unless noted. Mono is for data/IDs/code.

### 1. Data-Dense Pro  — *enterprise dashboards, admin, analytics, B2B tools*
- **Use when:** scan-heavy, expert users, many hours/day. (This RFP platform is here.)
- **Base body:** 14px (UI), **16px** primary readable; **13px** tabular numerals only. **Scale 1.2.**
- **Density:** compact. **Grid:** 4px base (8px rhythm for sections). Tight, information-rich.
- **Type pairing:** UI/display — **Geist** or **IBM Plex Sans**; data — **IBM Plex Mono** / **JetBrains Mono**.
- **Colour roles:** near-neutral background, one restrained accent (often a desaturated blue/teal/indigo
  *value you choose*, not tailwind-blue) for primary actions + active nav; status colours semantic.
  Strong reliance on `--muted-foreground` for secondary metadata.
- **Canvas vs surface:** a **clearly visible** light-grey canvas (L≈0.97) behind **white** cards (L=1.0) —
  never a sub-1.5% tint (it only shows on good monitors; confirm it on the user's real display).
- **Status indicators:** coloured **dot + label**, *not* filled pastel pills (filled badges are a generic/AI
  tell); AA-darken the label text (Law 7).
- **Tables:** header alignment matches cells; **numbers right + tabular**, **dates/text left** (Law 20).
- **Layout:** **persistent left sidebar + content area**, dense top bar, data tables, right detail panel.
- **Responsive (mobile-first, Law 21):** sidebar → **drawer/Sheet** (hamburger); data table → **stacked cards**
  (label:value rows, lead with vendor + amount + status); right detail panel → **bottom Sheet**; KPI row → **2-col
  then 1-col reflow**. Phone leads with *overdue / the action*; secondary columns hidden or tap-to-reveal; tap targets ≥44px.
- **Depth:** subtle — hairline borders + `--shadow-sm`; flat-ish, separation by border/space not big shadows.
- **Motion:** minimal, fast (120–180ms), opacity/transform only; no decorative motion.
- **Brands:** Linear, Stripe Dashboard, Carbon (IBM), Vercel dashboard, Datadog.

### 2. Editorial Minimalism  — *marketing sites, docs, premium SaaS landing, content-forward*
- **Use when:** read-heavy or a calm premium brand; lots of whitespace.
- **Base body:** **17–18px**. **Scale 1.25–1.333** (big display jumps).
- **Density:** airy. **Grid:** 8px. Generous line-height (1.6–1.7) for prose.
- **Type pairing:** display — **Fraunces** / **Newsreader** (serif) or **General Sans**; body —
  **General Sans** / **Instrument Sans**; mono — **Geist Mono**.
- **Colour roles:** off-white/warm-neutral base, near-black ink, ONE quiet accent; lots of restraint.
- **Layout:** single centred reading column (≈ 640–720px) or simple top-nav; big hero type, few elements.
- **Depth:** mostly flat; subtle borders; shadow only on true overlays.
- **Motion:** gentle fade/slide on scroll (transform/opacity), 200–300ms.
- **Brands:** Stripe (marketing), Vercel, Notion, Linear (site), Apple editorial.

### 3. Terminal-Core / Developer  — *dev tools, infra, CLIs-with-a-UI, technical products*
- **Use when:** developer audience; code/logs are first-class; "fast & precise" brand.
- **Base body:** 14–15px UI; **mono used structurally**, not just for code. **Scale 1.2.**
- **Density:** compact-to-medium. **Grid:** 4px.
- **Type pairing:** UI — **Geist** / **Space Grotesk**; everywhere data/code — **Geist Mono** /
  **JetBrains Mono** / **Berkeley-likes**.
- **Colour roles:** dark-default surfaces common; high-contrast text; one neon-ish accent (green/cyan/lime)
  used sparingly; semantic status.
- **Layout:** sidebar or command-palette-centric; monospace tables, log panes, keyboard-first.
- **Depth:** flat, crisp borders; minimal shadow.
- **Motion:** snappy (100–150ms), almost utilitarian.
- **Brands:** Vercel, Railway, Warp, Supabase, GitHub dark.

### 4. Warm Editorial / Humanist  — *media, creator, community, lifestyle SaaS*
- **Use when:** content + personality; approachable, not corporate.
- **Base body:** **17–18px**. **Scale 1.25.**
- **Type pairing:** display — **Fraunces** / **Bricolage Grotesque**; body — **Source Serif** or a
  humanist sans (**Instrument Sans**); warm.
- **Colour roles:** warm neutrals (cream/sand), an earthy or saturated-warm accent; tactile.
- **Layout:** editorial grid, generous imagery, top-nav.
- **Depth:** soft; rounded corners (larger `--radius`); gentle shadows.
- **Motion:** friendly ease, 200–300ms.
- **Brands:** Medium, Substack, Ghost, Airbnb-ish warmth.

### 5. Playful Consumer  — *consumer apps, growth/gamified, B2C onboarding*
- **Use when:** first-time consumers, mobile-first, fun > restraint.
- **Base body:** **16–18px**, bolder weights. **Scale 1.25–1.333.**
- **Type pairing:** display — **Plus Jakarta Sans** (heavy) / **Cabinet Grotesk**; body — **Plus Jakarta
  Sans** / **General Sans**.
- **Colour roles:** one vivid brand + a friendly secondary; rounded, energetic; still ONE dominant (Law 5).
- **Layout:** top-nav or bottom-tab (mobile), big touch targets, cards, illustration.
- **Depth:** rounded, soft colourful shadows (accent-tinted), bouncy.
- **Motion:** lively spring/ease, 250–350ms (still transform/opacity).
- **Brands:** Duolingo, Gumroad, Cash App, Headspace.

### 6. Glass / Soft Depth  — *premium consumer, AI products, "Apple-like"*
- **Use when:** a polished, modern, slightly futuristic feel.
- **Base body:** **16–17px**. **Scale 1.25.**
- **Type pairing:** **General Sans** / **Geist**; restrained.
- **Colour roles:** layered translucency (backdrop-blur), soft gradients used *with restraint*, one accent.
- **Layout:** floating panels over a soft background; top-nav or sidebar.
- **Depth:** the star — frosted glass, layered `--shadow-lg`, subtle gradient borders.
- **Motion:** smooth, 250–350ms, springy.
- **Brands:** Arc, Raycast, Apple, Linear (accents).

### 7. Neo-Brutalist / Bold  — *creator tools, bold brands, statement products*
- **Use when:** the brand wants to be loud and memorable (and the user explicitly asks for bold).
- **Base body:** **16–18px**, heavy weights. **Scale 1.333.**
- **Type pairing:** display — **Space Grotesk** / **Cabinet Grotesk** (huge); body — **General Sans**.
- **Colour roles:** high-contrast, flat saturated blocks, hard borders, visible offsets.
- **Layout:** asymmetric blocks, thick borders, hard shadows (offset, not blur).
- **Depth:** intentional flat hard-shadow (`4px 4px 0`), no soft blur.
- **Motion:** snappy, deliberate.
- **Brands:** Gumroad (rebrand), Figma community, indie tools.

### 8. Calm Authority / Trust  — *fintech, healthcare, gov, compliance, insurance*
- **Use when:** trust + clarity + "we are serious and safe" matter most.
- **Base body:** **16px** (15px dense). **Scale 1.2.**
- **Type pairing:** UI — **IBM Plex Sans** / **Geist**; data — **IBM Plex Mono**; steady, even.
- **Colour roles:** deep trustworthy base (navy/slate/forest *value you choose*), restrained accent,
  high legibility; semantic status carefully accessible.
- **Layout:** clean sidebar or top-nav; lots of structure, clear sectioning, evidence/figures foregrounded.
- **Depth:** subtle, orderly; hairline borders + `--shadow-sm`.
- **Motion:** calm, minimal, 150–200ms.
- **Brands:** Mercury, Wise, Ramp, Stripe, healthcare dashboards.

### 9. Bold Brand / Marketing Splash  — *simple promo / landing / brochure*
- **⚠ Honesty boundary (Law 19):** for a *simple* pretty marketing page, this skill is overkill —
  **point the user to Anthropic's `frontend-design`** (277k installs, tuned for exactly this). Use this
  family only when the marketing page must match a real app's design system.
- **Base body:** **18px+**. **Scale 1.333–1.618** (dramatic display).
- **Brands:** product launch pages, campaign microsites.

### 10. Cinematic / Media-Forward  — *video, streaming, creative tools, media review, AI-video*
- **Use when:** the content is **media** (video/image/audio) and should be the hero; premium dark feel.
- **Base body:** 14–15px; larger media, lower density. **Scale 1.2–1.25.**
- **Type pairing:** display — **Space Grotesk** / **Clash Display**; body — **Geist** / **General Sans**; timecodes — **JetBrains Mono**.
- **Colour roles:** **dark-default** near-black surfaces so thumbnails pop; ONE vivid accent (violet / electric-blue)
  with **dark text on the bright accent** for AA (white-on-bright fails); semantic status. (Law 22: still provide a light alternate.)
- **Layout:** sidebar + **media grid** (auto-fill 16:9 thumbnail cards with a duration badge) or a player + timeline review screen.
- **Depth:** flat dark; shadow on hover/overlays; restrained gradient accents.
- **Motion:** smooth 160–250ms, transform/opacity; gentle card lift on hover.
- **Brands:** Frame.io, Vimeo, RunwayML, Mux, Pika.

---

## How Step 3 turns a family into tokens

1. **Base size + scale** → the full type scale (xs … 5xl) as CSS-variable steps. Enforce the body
   minimum (Law 3).
2. **Font pairing** → `--font-display` / `--font-sans` / `--font-mono` (Law 1: no default-only face).
3. **Colour roles** → the shadcn token set in OKLCH (Law 8), one `--primary` (Law 5), semantic status,
   WCAG-AA verified for every foreground/surface pair (Law 7). **A *light/vivid* `--primary` fill takes DARK
   `--primary-foreground`** (white-on-light fails ~1.7:1); for accent **text / active / rings on a light surface use a
   separate *deeper* shade** of the accent — never the light fill as text (T1-b). Start from `references/palettes.md`.
4. **Grid + density** → spacing scale (4 or 8px base) and component padding (Law 10).
5. **Depth ladder** → `--shadow-sm/-md/-lg` + `--radius` for the family (Law 9).
6. **Layout pattern** → the structure of the sample page (Law 11).
7. **Motion** → duration/easing tokens; transform/opacity only (Law 12).
8. **Responsive** → mobile-first; the family's collapse pattern + breakpoints (mobile <640 · tablet 640–1024 ·
   desktop ≥1024); container queries for components, fluid type via `clamp()` (Law 21).

These become the concrete contents of `DESIGN.md` (see `design-md-template.md`).

> **Every family is mobile-first.** The presets above describe the *desktop* expression; each must also state
> how it collapses to tablet and phone (Law 21). For non-dashboard families the collapse is simpler (top-nav →
> hamburger, multi-col → single column, side content → stacked), but it is never optional.
