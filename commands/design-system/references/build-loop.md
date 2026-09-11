# The build loop — Steps 2–5 mechanics

> Loaded by `/design-system` on demand. `SKILL.md` owns the phase's gates — ask before you propose,
> STOP for confirmation, emit `DESIGN.md` only after approval. This file owns the mechanics behind
> them: what each concrete value should be, how the sample page is actually built, and what goes into
> `DESIGN.md`.

## §Why ask before proposing

**Order matters here, and it is the opposite of `/architect`'s.** For a stack you hold knowledge the user
may not, so one recommendation and a yes/no is right. For **aesthetics the user's taste is the primary
input** — you have no privileged view of what they like, and a design they did not choose is one they will
fight for the rest of the project. A confident proposal made *first* anchors them: they answer "yours is
fine" because they were never handed a blank page.

## §Concrete foundations

From the chosen family's preset (in `archetypes.md`), decide the **concrete** values — *this is the part
the popular skills omit, and the fix for "fonts too small / artsy-but-wrong":*
- **Font pairing** (display / body / mono) — **never a default-only face** (Law 1).
- **A real type scale** with an **archetype-correct base size** (enterprise 14–16px body, 13px tables,
  ~1.2 ratio, 4–8px grid; consumer 16–18px, 1.25–1.333, bolder) — Law 3.
- **Colour roles** (one dominant + one accent; semantic status) in **OKLCH**, **WCAG-AA verified** — Laws 5–8.
- **Spacing / density**, **depth ladder** (`--shadow-sm/-lg`, `--radius`), **layout pattern**, **motion**
  defaults (transform/opacity only) + the archetype's **motion tier/library ceiling** (CSS → Framer → GSAP →
  Three.js; `archetypes.md`) — Laws 9–12.
- **Light + dark by default (Law 22):** derive both token sets now (dark is not inverted light — give it its own
  AA-checked values); the archetype's natural mode is the default, the other is the alternate.
- **Brand input (optional — decide-for-them otherwise):** if the user has a brand — colours, a logo, a marketing
  screenshot, or a *"make it like <site>"* reference — extract its palette + type and **re-skin the tokens to it**.
  The archetype is the strong default; the brand *personalises* it; the laws + AA contrast still hold.

Give each as a **decided default + one-line why**; let the user tweak.

## §Build the sample page

Generate **a single, representative screen of THIS product** using the §Concrete foundations values:
- **In the project's stack** if one exists (a real page/route); otherwise a **standalone preview HTML**
  the user can open in a browser.
- **Interactive primitives must meet the accessibility floor** (Law 15 — focus management, ARIA, keyboard
  nav, all states). On a React stack the recommended means is **reuse a shadcn/ui + 21st.dev primitive or
  two**, re-skinned with the tokens — never re-author what the registry already solved.
- **Real content from the product's domain — never lorem** (Law 18).
- **Apply the craft layer (load `craft.md`).** Route the confirmed archetype through its index:
  **restraint families (Bucket A) get the precision signature and NO decorative motion** — adding scroll
  reveals/parallax/count-ups here breaks trust; **expressive families (Bucket B) WIRE THE REAL signature
  move(s)** for their tier — line-mask reveal, scrub parallax, count-up, spring-stagger, glass/WebGL hero —
  **never stubbed in a comment.** Ship the gesture *with* its `prefers-reduced-motion` fallback + lazy-load
  attached, at/below the family's `archetypes.md` ceiling. The non-motion craft (display type, radius,
  full-bleed structure, italic-serif accent) matters as much as the motion — a generic layout sinks an
  expressive page even with perfect animation. **Shared grammar, distinct voice (craft.md):** the *moves*
  are reusable, but derive the *voice* (fonts/palette/texture) **for this product** — never clone one
  exemplar's identity. Every **expressive** page earns **≥1 signature moment**; **restraint** pages earn none.
- **Note the page inventory first** (which page TYPES this app needs — auth, dashboard, billing, settings, landing…
  from the vision; see `page-patterns.md`), then build the *most representative* one (a dashboard's main
  view, the consumer app's home — not a login). The other pages' patterns get recorded in `DESIGN.md` §5 — we don't build them all now.
- **Build it mobile-first and responsive (Law 21):** design the **phone view first** — lead with the user's
  #1 mobile job (content priority), collapse the archetype's layout (sidebar → drawer, table → stacked cards,
  detail → sheet, KPIs reflow), tap targets ≥44px — *then* scale up to tablet/desktop. Never a fixed desktop
  grid that can't collapse.
- **Preview caveat:** a standalone preview (no stack) **can't import shadcn/21st.dev** (they're React) — say
  so. This does NOT exempt it from Law 15: the **floor is accessible components, not the library**, so any
  interactive primitive in the preview (button/input/dialog/menu) **still ships focus-visible + ARIA +
  keyboard nav** via vanilla — don't hand-roll an inaccessible one and call it "just a preview." Mirror the
  `DESIGN.md` tokens exactly. **For an expressive archetype the preview still ships real motion** — load
  GSAP/Framer from a CDN (the wrapper in `craft.md`), gated behind `prefers-reduced-motion`; do not fall back
  to a comment stub.
- **Confirm on the user's real display:** subtle choices (canvas tint, status-label colour, table alignment)
  render differently across screens — pick **clearly visible** values and verify on the user's monitor, not just code.
- **Ship it as an INTERACTIVE sample (the visualization moat):** inject `theme-studio.md` (the drop-in editor)
  before `</body>`, wrap the page content in `<div id="ts_stage">…</div>`, size readable text in **rem** with
  `html { font-size: var(--font-size-base,16px) }`, and replace the studio's `PRESETS` with 3–5 vetted palettes for the
  archetype (from `palettes.md`). Now the user **tweaks colour / theme / type-size / responsive LIVE, AA-guarded** —
  not "agent regenerates". Dev-only: stripped from the real build; only the finalized tokens persist.
  **For the studio to actually work:** give `#ts_stage` `container-type:inline-size` and write the page's responsive with
  **`@container` queries (not `@media`)** so the width buttons reflow (T5-1); use the `.light`/`.dark` **escape-hatch** dark
  pattern (template §2) so manual mode beats the OS (T5-6); load the font via `<link>` in the preview (T5-7).

## §Design principles

**Trigger:** Step 1 — before any colour or font is chosen.

The levers a 2026 senior designer actually pulls: **hierarchy** (what the eye hits first) · **restraint**
(ONE accent) · **real contrast / WCAG 2.2** · **task-appropriate density** (a dense admin is not a
marketing page) · **an intentional type scale** · **motion that earns its place**. Current norms to
benchmark against: Linear / Stripe / Carbon-era discipline, OKLCH colour.

Worked example, an enterprise compliance product: *"Calm authority · Density without clutter · Evidence
first · Accessible by default"* — each carrying one line on why it serves **this** product's users.

A principle is doing work when it can **decide a later argument**: "evidence first" settles whether the
audit trail or the summary goes above the fold. A principle that cannot lose an argument is decoration.

## §Emit the token stylesheet

**Trigger:** Step 5 — the design is approved and `DESIGN.md` is being written.

**Why this exists.** `DESIGN.md` is a specification. On a real run a component referenced 14 tokens, every
one of them correctly defined *in `DESIGN.md`*, and rendered as an unstyled browser button: no stylesheet
in the app defined them, and no root layout imported one. Typecheck, lint and `/frontend-audit` were all
green, because CSS drops a declaration whose `var()` resolves to nothing — silently. The token layer was
finally written four phases later, during a feature build, where design decisions do not belong (it grew
to 94 tokens against the spec's 16 — most of the design system was invented by `/build`).

1. **Write the real file.** Path from `STRUCTURE.md` — `src/app/globals.css` for Next.js app-router,
   `src/styles/tokens.css` otherwise. Every token in `DESIGN.md` §2/§3, in the project's CSS convention
   (shadcn CSS variables on `:root`), **light and dark both** (Law 22), in the same names the spec uses.
2. **Import it from the app's root entry** — the root layout / app entry / global stylesheet chain — and
   **verify the import resolves**, not that you wrote the line. An unimported stylesheet fails exactly the
   way a missing one does.
3. **Record the path in `DESIGN.md` §2** and in `PRODUCT.md#Design`, so `/new-component`, `/build` and
   `/frontend-audit` can resolve tokens against the app instead of against the spec.
4. **Check both directions before the gate closes.** Every spec token exists in the stylesheet, and every
   stylesheet token exists in the spec. A token in one and not the other is a contradiction
   (`MECHANISMS.md` §Step 3c) — name both sides, do not quietly add it to the loser.
5. **The sample page is not this file.** A preview that defines its own tokens inline demonstrates the
   design twice and ships it zero times. If the sample carries inline `<style>` tokens, say so, and point
   at the stylesheet as the one that counts.

## §Confirm the sample

**Trigger:** the sample page is built and you are about to show it (Step 4).

Describe what they should see, and if you can, screenshot it and compare pixel-level: spacing, weight,
exact colours, radius, alignment. **Three widths — ~375px (mobile), 768px (tablet), desktop.** A phone
view that overflows, clips, or is a shrunk desktop is a fail (Law 21), not a detail to fix later.

If the user doesn't like it, **ask what to change** — bolder / lighter / denser / different font /
*"make it like <site>"* — and generate another. Loop until they approve; the loop is the phase.

The **Theme Studio** lets the user finalize colour, type size, theme and roundness *themselves*, and
**Export** the tokens. Only *structural* changes — layout, content — need a regenerate from you.

## §Standalone vision discovery

**Trigger:** Step 0 found no `PRODUCT.md` — this skill is running on its own.

- **Docs but no `PRODUCT.md`** → resolve the spine from the project's own docs in order: `CLAUDE.md` →
  `README.md` → `docs/`. **State which file you resolved as the spine** (`MECHANISMS-ON-DEMAND.md`
  §Spine resolution (full)).
- **Nothing at all** → ask these three, plainly, and wait: *"What is it? · Who is it for? · What's the ONE
  job it does for them?"* Design cannot be derived from less, so do not proceed on a guess. What they
  answer is what the principles in Step 1 are built from, and it belongs in `PRODUCT.md#Design` verbatim
  enough that the next session can see what the design was aimed at.

## §Emit `DESIGN.md`

**The 9 sections, in order:** *1 Visual Theme · 2 Color & Roles · 3 Typography · 4 Components ·
5 Layout · 6 Depth/Elevation · 7 Motion · 8 Do's & Don'ts · 9 Responsive & Agent Guide.* Every one is
filled with the concrete approved values — a placeholder that ships is a section that was never decided.

- Tokens are **shadcn/ui-compatible CSS variables in OKLCH** (rebrand = change values; plugs into
  shadcn/21st.dev with no theme provider/build step).
- **Emit light AND dark token sets + system switch** (`:root` + `.dark` + `prefers-color-scheme`) — Law 22.
  *(If the user used the Theme Studio **Export**, those tokens — both modes + `--font-size-base` — ARE §2; paste them in.)*
- **Record the page inventory** in §5 (each page type → its layout pattern from `page-patterns.md`).
- **Re-run the WCAG-AA contrast check** on every foreground/surface pair, **in both modes**, before writing (Laws 7 & 22).
- The **Agent Guide** (§9) tells every later build step how to obey this file.

### §Audit timing

- **Audit timing (T1-c) — actually RUN it, don't just cite it:** the floor is mechanically enforced, not
  asserted. Run the engine on the **approved sample** at confirm-time (Step 4) and on **`DESIGN.md` after**
  it's emitted here (never `DESIGN.md` before approval — Law 16):
  ```
  python commands/frontend-audit/audit.py <approved-sample> DESIGN.md
  ```
  **Read the output and act on it:** fix every `[FAIL]` (the floor is non-negotiable) and triage `[WARN]`
  before handing off — a `Law7-unverified` warn means contrast was NOT checked (rename tokens so it can be),
  not that it passed. Do not emit a "passes the laws" claim you didn't run the engine to back.

*(Greenfield: `DESIGN.md` is now the harness for new pages. Retrofit-rewrite of existing pages is the
documented follow-up.)*

## §What this skill is — and isn't

**What this skill is — and isn't.** Its edge is **real apps**: enterprise, dense, data-heavy, existing
codebases, disciplined builds — the unglamorous *concrete, archetype-correct* defaults the popular
tools omit. It does **not** out-design the ecosystem on palettes/components — it **reuses** shadcn/ui +
21st.dev + the open DESIGN.md standard and wires them into the build lifecycle. **Honesty boundary
(Law 19):** for a *simple* pretty marketing/brochure page, say so and point the user to Anthropic's
`frontend-design` instead.

## §Scope of this version

**Scope of this version: greenfield core loop.** Lightweight brand-input (re-skin to given colours/reference)
is in; **deep** image/code token-extraction (the user's `UI_to_Prompt`), full retrofit (rewrite existing pages),
and the component-gallery page are documented follow-ups (`/frontend-audit` is the separate enforcement skill).
If an existing UI is detected, say so and proceed greenfield for new screens.
