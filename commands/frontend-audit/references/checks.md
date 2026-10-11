# What `audit.py` checks — the full table

> Opened by `/frontend-audit` only to explain a finding (the scorecard names its rule id). The mechanical subset of
> the 26 universal laws, plus anti-pattern, form and security warnings. Responsive layout at real widths is
> `render_check.py`'s (375 / 768 / 1280 px).

| Law | Check |
|---|---|
| **7 — contrast (the headline)** | **Computes** WCAG ratio for every foreground/surface token pair — shadcn names **plus common aliases** (`--text`/`--surface`/`--bg`/`--text-muted`…) — (OKLCH or hex → relative luminance → ratio). `<4.5` body = ERROR, `3–4.5` = large-only WARN. **Anti-false-pass:** if colour tokens exist but no pair was checkable, it **WARNs "unverified"** rather than silently reporting ok. *This is the law `/design-system` could only assert.* |
| **7b — status colours, two bars** | Every status token (`--success`/`--warning`/`--destructive`/`--info` and friends) against `--card`/`--background`/`--popover`/`--muted`, in **both modes**. Held to **4.5:1** as text, or **3:1** when the token's *name* marks it a graphic (`-dot`, `-indicator`, `-fill`, `-bar`, `-chart`) - so one value can pass as a dot and fail as a label. Below its bar = ERROR, with the fix named. Opt out only by declaring the token `/* decorative */`. *This is where palettes actually drift: the shade is chosen for brightness so the dot reads as "amber", then reused as a label.* |
| 14 — tokens only | raw `#hex` in component code (outside `:root`) = ERROR |
| **14b — tokens exist** | a `var(--token)` **nothing defines** = ERROR (cross-file: `audit.py DESIGN.md frontend/` resolves components against the design system in the same run). CSS drops such a declaration *silently* - the colour never arrives and nothing else reports it, so this is the one class the rest of the audit was blind to. `var(--x, fallback)` is exempt (a declared fallback is a choice). **Anti-false-pass:** references but no definitions anywhere in the set = WARN "unverified", never a pass. |
| 12 — motion | `transition: all` / `transition-all` = ERROR; transition on a layout/paint prop = WARN; heavy-motion lib without a `prefers-reduced-motion` guard = WARN |
| 1 — distinctive font | Inter/Roboto/Arial/system-ui as the **display** `--font-display` = ERROR; as the body face = WARN; **a display that is a width/weight variant of the body face (e.g. `Inter Tight` over `Inter`) = WARN** (near-twin, not a distinct identity) |
| 3 — type floor | any `font-size` below 12px (px **and** rem/em) = ERROR |
| 13 — states | interactive elements but no `:focus-visible` = WARN |
| **21 — responsive** | missing `<meta viewport>` (html) = ERROR; multi-column/grid layout with **no** `@media`/`@container`/`auto-fit`/`minmax` = ERROR (desktop-only) |
| **22 — theming** | computes contrast in **both** `:root` (light) and `.dark`; `:root` colour tokens but no `.dark` block = WARN (single-mode); **a `.dark` block but no `prefers-color-scheme` rule that swaps tokens = WARN** (system preference ignored — manual-toggle-only) |

| **23 — live regions** | a value that looks computed/updated (`total`, `count`, `balance`, `status`…) with no `aria-live` and no `role="status"` = WARN. Heuristic by nature — a regex cannot know what re-renders — so it warns rather than errors, and it is the check that would have caught a live "You owe ₹253" that was **silent to every screen reader** on a page scoring 86 pass / 0 errors |
| **24 — semantics** | `<div onClick>` with no `role` = ERROR (not focusable, not announced, not keyboard-operable) |
| **25 — accessible names** | icon-only `<button>`/`<a>` with no `aria-label` or visually-hidden text = ERROR; link text that names nothing ("click here", "read more") = WARN |
| **26 — heading order** | first heading below `<h1>` (html) = WARN; a skipped level (`h2 → h4`) = WARN |
| **20 — table alignment** | per `<table>`: a column of numbers not right-aligned (own `text-right`/`text-align: right`, or a class a stylesheet in the run aligns right) = WARN; a header aligned unlike its column's cells = WARN |
| **3 — caption tier** | a CSS rule setting 12–13px on body text (not an uppercase caption, overline, label, table header or numeral) = WARN |
| **Anti-patterns (AP1–AP9)** | WARN each: an emoji as an icon · an untinted pure-black surface · a purple-blue gradient · a bounce/elastic easing · a ≥3px coloured stripe down one side of a card · a text column wider than 80ch · a card inside a card · muted grey text on a coloured fill · an untinted grey token (no hue) |
| **Forms** | an `<input>`/`<select>`/`<textarea>` no `<label for>`, wrapping `<label>` or `aria-label` names = WARN (a placeholder is not a label) |
| **Security** | `target="_blank"` with no `rel="noopener noreferrer"` · a `javascript:` link · raw HTML put into the page (`dangerouslySetInnerHTML`, `v-html`, `{@html}`, `.innerHTML =`, a `safe` filter) = WARN each |

Markdown is treated as spec: only its colour **tokens** are contrast-checked; code-pattern rules are
skipped (so a `DESIGN.md` "Don't: no `transition: all`" line doesn't false-positive).

## Config — `.frontend-audit.json`

A project may put one file at its root (the audit looks from the folder it runs in up to the git root):

```json
{"pairs": [["--ink", "--paper"]], "ignore": ["AP9", "Law23-live-region:src/legacy/*"]}
```

- `pairs` adds foreground/surface token pairs to the contrast check (Law 7) — tokens named outside shadcn's convention
  get a real check instead of "unverified".
- `ignore` skips WARN findings by rule id or its prefix, optionally only for files matching a glob after a `:`.
  **An ERROR is never skipped.** The scorecard prints how many warnings the file skipped, so nothing goes quiet.
- A file that is not this shape stops the run (exit 2) — never a silent default.
