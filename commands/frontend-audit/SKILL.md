---
name: frontend-audit
description: >
  Phase 2/3 of product-playbook — the UI enforcement gate. Mechanically checks built UI (and its
  DESIGN.md) against the /design-system universal laws, with a REAL WCAG contrast engine
  (OKLCH/hex → ratio) so contrast is computed, never asserted. Use after building or changing UI,
  before shipping, or in CI — run /frontend-audit "check my UI", "is this accessible", "audit the
  frontend", "did I break the design system". Reports a pass/warn/error scorecard and exits non-zero
  on errors. Pairs with /design-system (which sets the laws + DESIGN.md) and /new-component.
---

# `/frontend-audit` — the UI quality gate (mechanical floor)

> Part of the **product-playbook UI suite** (mastered here; see `/design-system`). `/design-system`
> *decides* the look and writes `DESIGN.md` + the 26 universal laws; **this skill *enforces* the
> mechanically-checkable subset** so a guaranteed floor holds regardless of who built the screen.
> It does **not** judge taste/archetype fit — it checks what a machine can prove.

## What it does

Runs `audit.py` (stdlib-only, portable, ASCII output — no `PYTHONUTF8` needed) over UI files and
`DESIGN.md`, and prints a scorecard. **Exits non-zero if any ERROR-level law fails** (CI-friendly).

```
python commands/frontend-audit/audit.py <file-or-dir> [more...]
# e.g.  python .../audit.py frontend/  ·  python .../audit.py DESIGN.md sample.html
```

## What it checks (the mechanical subset of the 20 laws)

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

Markdown is treated as spec: only its colour **tokens** are contrast-checked; code-pattern rules are
skipped (so a `DESIGN.md` "Don't: no `transition: all`" line doesn't false-positive).

## What it does NOT check (still human/judgment — by design)

Archetype fit, visual hierarchy, layout-matches-archetype (Law 11), "looks generic", whether the
sample was confirmed (Law 16). Those stay with `/design-system`'s stop-and-confirm. Some laws are
partial here (table header/cell alignment Law 20, caption tier Law 3) — flagged as v1 follow-ups.

**Accessibility (category J) is a floor, never a pass.** Laws 23–26 are the mechanically decidable
subset. **Not checked, and not checkable from source:** keyboard traps and tab order, focus management
across route changes, real screen-reader output, alt-text *quality*, and meaning carried by colour
alone. `audit.py` prints this list on every run, because a milestone that delegates its accessibility
criterion to *"frontend-audit passes with no errors"* is relying on a check that cannot fail on most of
what it appears to certify — and a check like that stops anyone from looking.

## How to use

1. After `/design-system` emits `DESIGN.md` and you've built screens (via `/new-component`), run the
   audit over the UI dir + `DESIGN.md`.
2. Fix every **ERROR** (the floor is non-negotiable); triage **WARN**.
3. Wire it into CI as a gate (`exit 1` blocks the build) once the project's UI is established.

## Roadmap (v1 → v1.1)

Config file for project-specific token pairs/ignore rules; table header/cell-alignment parsing
(Law 20); caption-tier awareness (Law 3); generalise the existing `frontend_drift_detector.py` /
`frontend_checkpoint_runner.py` patterns (RESPONSIVE/FORMS/SECURITY categories) into this one tool.
