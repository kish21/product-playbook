# Page patterns — common SaaS page types → layout (2026, curated)

> Loaded by `/design-system`. **ONE design system (tokens + the 22 laws) drives MANY pages — but each
> page TYPE has its own layout.** We don't build every page; we (a) infer which pages the app needs from
> the vision/existing app, (b) build ONE representative sample, (c) record each needed page's pattern in
> `DESIGN.md` §5 so every later build stays consistent (same tokens/fonts/laws, different layout).
>
> Curated to what real 2026 **consumer + enterprise** SaaS actually ship. Reuses the page taxonomy from
> the user's `UI_guide` repo (Authentication · Navigation · Landing · Data Display · Forms · Interactive).

## How to use
1. From the vision/scope (or an existing app's routes), **list the page types this product needs**.
2. Pick the archetype + tokens once (the design system).
3. For each page type, apply its pattern below — same tokens, different layout. Record the list in `DESIGN.md` §5.

## The patterns

### Auth — login · signup · reset · verify
Centered single card (~400px) on the page background; brand mark on top; ONE primary action. Often a split
(brand panel + form) on desktop that collapses to the card alone on mobile. Inputs have labels (`htmlFor`),
inline validation, errors `role="alert"`. Minimal nav.

### Dashboard / overview — the home of most SaaS
Sidebar (nav) + top bar + content. Lead with KPIs / the user's top job, then the primary list/table. Archetype
drives density (Data-Dense Pro = tight table; Cinematic = media grid). Mobile: sidebar → drawer, KPIs reflow,
table → cards (Laws 20/21). **Content aligns with the top-bar header and uses consistent padding (~24–32px) — no
large left gutter / off-centre indent (T3-C).** *(Contrast: editorial/reading layouts ARE a centered narrow column
with wide margins — that's correct there, not a gutter.)*

### Data display — lists · tables · detail
Table/DataGrid (header align = cell align; numbers right + tabular; status = dot + label — Law 20) OR a card grid.
Filters/search on top; pagination or infinite scroll; a detail panel/route/sheet for one record. **Empty state is
designed** (icon + one line + a primary action) — never a blank screen.

### Forms — create/edit · settings · checkout · onboarding wizard
Grouped sections with clear labels; one column on mobile, optionally two on desktop. Settings = sectioned form
(account / team / billing / notifications) with a clear save affordance. Checkout/onboarding = a stepped wizard
with progress; validate per step.

### Billing / pricing / plans
Pricing = 2–4 plan cards, one highlighted (recommended), monthly/annual toggle, a clear CTA per card. Billing
settings = current plan + usage + an invoice table (dates; amounts right + tabular; status; download). Trust cues
(secure, cancel anytime); amounts in mono/tabular.

### Landing / marketing — often a different surface
Hero (one big value line + ONE primary CTA) → proof/features → social proof → CTA → footer. Bigger type/scale than
the app (Editorial / Bold archetypes). Honesty boundary (Law 19): a *pure* marketing splash may be better served by
Anthropic's `frontend-design`; here it must still match the app's design system.

### Nav & chrome — shared across pages
Sidebar / top-nav, breadcrumbs, tabs, command palette. Active + focus-visible states, keyboard reachable. Mobile = a
drawer/Sheet (Law 21) that **actually opens** (no dead hamburger).

### Interactive / overlays — modals · dialogs · toasts · dropdowns · tooltips
Reuse shadcn/ui + 21st.dev (focus-trap, ARIA, keyboard) — never hand-roll (Law 15). Skin with tokens.

## Out of scope
Only build the pages the product actually needs. A small tool may need just auth + dashboard + settings — don't
invent pages the vision doesn't call for.
