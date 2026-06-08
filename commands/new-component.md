---
name: new-component
description: Create a new React frontend component. Use when building any UI component — buttons, cards, forms, modals, tables, or page sections. Enforces CSS variable rules, interactive states, and typography constraints to keep components consistent with the design system.
---

# New Frontend Component

Create a new React component for your project's frontend.

$ARGUMENTS

## Rules — apply before writing a single line

1. **File location**: Place in your project's component directory (e.g. `components/<ComponentName>.tsx` or a page-level route folder). Ask if unsure.
2. **No raw hex** — all colours via `var(--color-*)`
3. **No raw fonts** — use your project's font constants (e.g. `FONT`, `DISPLAY`, `MONO`) or CSS font variables. Never write `'Inter'`, `system-ui`, or any literal font string.
4. **Theme context** — use your project's theme hook if `isDark` or theme state is needed. Do not import theme from unrelated modules.
5. **Border rule** — never mix `border` shorthand with `borderTop` / `borderLeft` / `borderRight` / `borderBottom` in the same element's inline styles — React will warn and the style breaks on re-render. Use all four sides explicitly, or use the shorthand alone.
6. **Interactive states** — every clickable element needs hover + focus-visible + active states. Use `var(--color-surface-hover)` for hover backgrounds. Never suppress focus outlines without a visible replacement.
7. **No `transition: all`** — animate only `transform` and `opacity`. Use your project's transition duration variable (e.g. `var(--transition)`) for consistency.
8. **Status colours** — always semantic: `var(--color-success)` / `var(--color-warning)` / `var(--color-error)` / `var(--color-info)`. Never raw colour for state.
9. **Depth** — use the layering system: base (`var(--color-background)`) → elevated (`var(--color-surface)` + `var(--shadow-sm)`) → floating (`var(--shadow-lg)` + border). Never everything on the same z-plane.

## Output format
- Full TypeScript component with correct prop types
- Export at bottom (`export default` or named export)
- No comments unless the WHY is non-obvious
