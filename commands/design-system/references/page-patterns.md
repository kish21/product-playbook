# Page patterns — common SaaS page types → layout (2026, curated)

> Loaded by `/design-system`. **ONE design system (tokens + the 26 laws) drives MANY pages — but each
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
**Charts and KPIs (B2B, admin):** a KPI tile = the number, its unit, the period and the change against a named
baseline ("+4% vs last month"), never a bare number. One chart answers one question, written as its title. Lines for a
trend over time, bars for comparing 2–12 categories, a table when the reader needs exact values; no pie with more than
5 slices, no 3D, no dual axes. A threshold the product decides by (a confidence of 0.80) is drawn on the chart as a
labelled line. Colour encodes one thing; the same series keeps the same colour on every chart.
**Keyboard (expert tools used many hours a day):** `j`/`k` or arrow keys move through a list, `Enter` opens, `Esc`
closes, `/` focuses search; each shortcut shows in its button's tooltip and in one `?` overlay; no shortcut is the
only way to do something.

### Forms — create/edit · settings · checkout · onboarding wizard
Grouped sections with clear labels; one column on mobile, optionally two on desktop. Settings = sectioned form
(account / team / billing / notifications) with a clear save affordance. Checkout/onboarding = a stepped wizard
with progress; validate per step.
**Errors and required fields:** the error shows under its field, says what to do ("Enter a date after 1 March"),
keeps what the user typed, and is linked by `aria-describedby`; validate on leaving a field and on submit, never on
each key press. Mark the optional fields "(optional)" when most are required, else mark the required ones; never a
lone `*` with no legend. On submit with errors: a summary at the top lists each one as a link to its field, and focus
moves to it. The submit button stays enabled and names the action ("Save changes").

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
**Feedback after an action:** a success that changes what is on screen shows there (the row updates, the saved
label); a toast is for what happens off screen, says what happened in the past tense ("Reply approved"), stays
at least 5 s, is announced (`role="status"`), and carries the undo when one exists. An error toast never replaces
an inline error. A notification the user did not ask for needs a setting that turns it off.

### Presenter / explainer view — a demo of how the product decides
For a sample shown to a jury, investors or colleagues (round 1's "What is this sample for?" → a demo). One wide
screen tells the core idea: **when the product acts, holds back or stays silent, and why**. Anatomy, left to right on desktop: (1) the input over time — a timeline or a day slider of the signals
it reads; (2) the decision — what it concluded, its confidence drawn against the threshold, the evidence items
(E1, E2 …) with their weights; (3) **the end user's view embedded in a device frame** (`data-view="end-user"`) —
what the person actually receives, with every action #Scope gives them; (4) a decision log — each case with its
outcome (ACT · HELD · SILENT) and the one-line reason. On a phone the four stack in that order. Same checklist as
any sample (states, languages, fonts, 3 widths); #Scope's must-shows sit inside the device frame.

### Flows across screens
The sample is one screen; the core task spans 2 or more. Record in `DESIGN.md` §5 the core task as a flow, one line:
`<screen> → <action> → <screen> → …` with the state the user sees at each step (where they land after the main
action, after an error, after undo). A screen the flow needs that is not in the page inventory is added to it.

## Microcopy rules (fixed ids — each one checkable by reading the page)
- **W1** A button says Verb + Noun ("Approve reply", "Save changes"); never "OK", "Submit", "Yes".
- **W2** A destructive action names what it destroys and has a confirm or an undo ("Delete 3 drafts").
- **W3** Loading text says what is loading and ends with "…" ("Reading the payslips…").
- **W4** An error says what happened and what to do next; never a code alone, never blame.
- **W5** An empty state says why it is empty and offers the next action.
- **W6** One name per thing, the same word on every screen.
- **W7** Every action #Scope gives the user keeps its own control: approve · ignore · "not relevant" are three
  buttons, never merged into one ("hide" that does both).
- **W8** Sentence case; numbers as digits; dates and amounts in the interface language's format.

## Out of scope
Only build the pages the product actually needs. A small tool may need just auth + dashboard + settings — don't
invent pages the vision doesn't call for.
