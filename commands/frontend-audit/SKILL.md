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
> *decides* the look and writes `DESIGN.md` + the 20 universal laws; **this skill *enforces* the
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
| **7 — contrast (the headline)** | **Computes** WCAG ratio for every shadcn foreground/surface token pair (OKLCH or hex → relative luminance → ratio). `<4.5` body = ERROR, `3–4.5` = large-only WARN. *This is the law `/design-system` could only assert.* |
| 14 — tokens only | raw `#hex` in component code (outside `:root`) = ERROR |
| 12 — motion | `transition: all` / `transition-all` = ERROR |
| 1 — distinctive font | Inter/Roboto/Arial/system-ui as the **primary** `--font-sans/-display` = ERROR |
| 3 — type floor | any `font-size` below 12px = ERROR |
| 13 — states | interactive elements but no `:focus-visible` = WARN |

Markdown is treated as spec: only its colour **tokens** are contrast-checked; code-pattern rules are
skipped (so a `DESIGN.md` "Don't: no `transition: all`" line doesn't false-positive).

## What it does NOT check (still human/judgment — by design)

Archetype fit, visual hierarchy, layout-matches-archetype (Law 11), "looks generic", whether the
sample was confirmed (Law 16). Those stay with `/design-system`'s stop-and-confirm. Some laws are
partial here (table header/cell alignment Law 20, caption tier Law 3) — flagged as v1 follow-ups.

## How to use

1. After `/design-system` emits `DESIGN.md` and you've built screens (via `/new-component`), run the
   audit over the UI dir + `DESIGN.md`.
2. Fix every **ERROR** (the floor is non-negotiable); triage **WARN**.
3. Wire it into CI as a gate (`exit 1` blocks the build) once the project's UI is established.

## Roadmap (v1 → v1.1)

Config file for project-specific token pairs/ignore rules; table header/cell-alignment parsing
(Law 20); caption-tier awareness (Law 3); generalise the existing `frontend_drift_detector.py` /
`frontend_checkpoint_runner.py` patterns (RESPONSIVE/FORMS/SECURITY categories) into this one tool.
