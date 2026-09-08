---
name: new-component
description: Create a new React frontend component in the token vocabulary DESIGN.md records. Use when building any UI component — buttons, cards, forms, modals, tables, or page sections. Reads DESIGN.md (falling back to shadcn defaults) so the component's tokens actually exist in the project, and enforces interactive states, motion and typography rules.
---

# `/new-component` — build one component against the recorded design system

Create a new React component for your project's frontend.

$ARGUMENTS

> Part of **product-playbook**. Reads `DESIGN.md` (+ `PRODUCT.md#Design`) — resolve per
> `PRINCIPLES.md` §Spine resolution; writes one component file.
> Apply `PRINCIPLES.md` — load-bearing: **no-hardcoding (tokens/fonts come from `DESIGN.md`, never
> baked into the component)**, **accessibility (keyboard · focus · contrast · semantic markup) is part
> of the definition-of-done**, **intention-revealing naming**, **docs match reality**.

## Contract
- **Purpose:** one React component, written in **the token vocabulary this project actually uses**.
- **Reads:** `DESIGN.md` (tokens · type scale · motion · depth ladder) and `PRODUCT.md#Design`; `STRUCTURE.md` for where components live.
- **Writes:** one component file (path confirmed with the user).
- **Exit criteria:**
  - [ ] **Every `var(--token)` the component references is defined in `DESIGN.md`** — checked mechanically (see the verification step). An undefined token does **not** fail `/frontend-audit`: CSS drops the declaration silently, so the colour simply never arrives. Nothing else catches this.
  - [ ] No raw hex, no literal font string, no invented token name. A token this component needs but `DESIGN.md` lacks is a **gap to raise**, not one to improvise.
  - [ ] Every interactive element has **hover · focus-visible · active**; focus is never suppressed without a visible replacement.
  - [ ] Motion animates `transform`/`opacity` only — never `transition: all`, never a layout/paint property.
  - [ ] Typed props; no `font-size` below the floor `DESIGN.md` sets (12px absolute minimum).
  - [ ] **`/frontend-audit` reports 0 errors** on the file — the gate `/build` runs. Necessary, not sufficient: it checks the tokens that *are* defined, not the ones you referenced.

## Step 0 — Resolve the token vocabulary (do this BEFORE writing a line)
The names below are **examples, not the contract**. Where `DESIGN.md` records a name, **that name wins**.

1. **`DESIGN.md` exists** → read §Tokens and use those names verbatim. `/design-system` emits
   **shadcn-compatible OKLCH tokens**, so expect `--background` · `--foreground` · `--card` ·
   `--card-foreground` · `--primary` · `--primary-foreground` · `--muted` · `--muted-foreground` ·
   `--destructive` · `--success` · `--warning` · `--border` · `--input` · `--ring` · `--radius` ·
   `--shadow-sm` · `--shadow-lg`. Take the **type scale**, **motion durations** and the **depth
   ladder** from there too.
2. **No `DESIGN.md`** → say so plainly, recommend **`/design-system`**, and fall back to the **shadcn
   defaults above** — the vocabulary `/design-system` emits and the ecosystem shares. **Never invent a
   private one.** A component written to token names the project never defines does not error: CSS
   treats `color: var(--color-success)` with no such token as invalid at computed-value time and drops
   the declaration, so the status colour silently inherits and the component looks *almost* right. The
   audit reports 0 errors on it (verified). Nothing catches it — which is exactly why Step 0 exists.
3. **A brownfield project with its own tokens** → use the project's names and record where you found them.

## Rules — the intent is fixed, the token names come from Step 0
1. **File location** — put it where `STRUCTURE.md` says components live (e.g. `components/<Name>.tsx`). Ask if unsure; never invent a new components root.
2. **No raw hex** — every colour is a token from Step 0.
3. **No raw fonts** — use the project's font variables/constants from `DESIGN.md`. Never write `'Inter'`, `system-ui`, or any literal font string.
4. **Theme context** — use the project's own theme hook if `isDark`/theme state is needed. Don't import theme from an unrelated module.
5. **Border rule** — never mix the `border` shorthand with `borderTop`/`borderLeft`/`borderRight`/`borderBottom` in one element's inline styles: React warns and the style breaks on re-render. All four sides explicitly, or the shorthand alone.
6. **Interactive states** — hover + focus-visible + active on everything clickable, at a target ≥44px. Use the hover surface `DESIGN.md` names (shadcn default: `--muted` or `--accent`). Never suppress a focus outline without a visible replacement.
7. **No `transition: all`** — animate `transform` and `opacity` only, at the duration `DESIGN.md` records, and honour `prefers-reduced-motion`.
8. **Status colours are semantic** — the success/warning/destructive tokens from Step 0 (shadcn default: `--success` · `--warning` · `--destructive`). Never a raw colour for state.
9. **Depth** — follow `DESIGN.md`'s layering ladder: base (`--background`) → raised (`--card` + `--shadow-sm`) → floating (`--shadow-lg` + border). Never everything on one z-plane.

10. **Third-party DOM injection** — form and auth surfaces receive attributes and nodes from password
    managers, autofill and accessibility extensions before the framework hydrates. Where your framework
    offers a hydration-mismatch escape hatch, apply it **to the specific element that receives them, with a
    comment naming why** — **never as a default across every input**. A blanket suppression silences genuine
    mismatches (clock/random values, locale drift, branch divergence) that are real bugs. `/test`'s
    real-user-environment class is what proves the surface actually survives it.

## Output format
- Full TypeScript component with correct prop types
- Export at bottom (`export default` or named export)
- No comments unless the WHY is non-obvious

## Before you hand it back — verify, don't assert
**Both in one run** — pass `DESIGN.md` alongside the component, or the token check cannot run:

1. **Every token the component references is defined.** Audit the component **together with `DESIGN.md`**
   so the two resolve against each other — Law 14b errors on any `var(--token)` nothing defines:
   ```
   python commands/frontend-audit/audit.py DESIGN.md <the new component>
   ```
   Auditing the component **alone** cannot check this and will say so (`tokens-defined: warn`,
   "unverified"). Passing `DESIGN.md` is what makes it a real check.
2. **0 errors overall** on that same run.

A token this component genuinely needs but `DESIGN.md` doesn't define is a **contradiction between the
component and the recorded design system**: name both sides and take it back to `/design-system` to be
added there — never invent it here (`PRINCIPLES.md` §Step 3c).
