# Palettes — curated light+dark OKLCH starter palettes

> Loaded by `/design-system` (Step 3 colour) + the Theme Studio "Starter looks". A **palette = one NEUTRAL base
> (background/surface/text) + one ACCENT** (`--primary`). Pick a base + an accent for the archetype, then **re-run
> `/frontend-audit` (contrast is computed, not trusted)**. Reused/adapted from the user's UI_guide theme picker —
> **converted hex→OKLCH, AA-vetted both modes, generic ones (iOS/Tailwind default blue) dropped.**
>
> **Auto-readable text rule (T1-b):** a *light/vivid* accent fill takes **dark** `--primary-foreground`; a *deep* accent
> takes **white**. Never white-on-a-light-fill. Each accent below states the foreground that passes AA.

## Neutral bases (choose one)

```css
/* COOL NEUTRAL — Data-Dense Pro · Terminal · Calm Authority (default) */
:root{ --background:oklch(0.985 0.003 250); --foreground:oklch(0.24 0.02 250); --card:oklch(1 0 0);
  --card-foreground:oklch(0.24 0.02 250); --muted:oklch(0.96 0.004 250); --muted-foreground:oklch(0.45 0.015 250);
  --border:oklch(0.91 0.004 250); --input:oklch(0.91 0.004 250); }
.dark{ --background:oklch(0.20 0.02 260); --foreground:oklch(0.96 0.01 260); --card:oklch(0.25 0.02 260);
  --card-foreground:oklch(0.96 0.01 260); --muted:oklch(0.30 0.02 260); --muted-foreground:oklch(0.74 0.02 260);
  --border:oklch(0.32 0.02 260); --input:oklch(0.32 0.02 260); }

/* WARM NEUTRAL — Warm Editorial · creator · lifestyle (cream paper) */
:root{ --background:oklch(0.985 0.01 85); --foreground:oklch(0.26 0.02 60); --card:oklch(1 0 0);
  --muted-foreground:oklch(0.48 0.02 60); --border:oklch(0.90 0.01 80); }
.dark{ --background:oklch(0.22 0.015 60); --foreground:oklch(0.95 0.01 80); --card:oklch(0.26 0.015 60);
  --muted-foreground:oklch(0.74 0.015 70); --border:oklch(0.33 0.015 60); }

/* INK / DARK-DEFAULT — Cinematic · Terminal (dark is primary, light is the alternate) */
:root.dark, :root[data-default=dark]{ --background:oklch(0.17 0.012 280); --foreground:oklch(0.96 0.004 280);
  --card:oklch(0.21 0.014 280); --card-foreground:oklch(0.96 0.004 280); --muted-foreground:oklch(0.70 0.012 280);
  --border:oklch(0.29 0.012 280); }
```

## Accents (`--primary` = `--accent` = `--ring`; pick ONE — Law 5)

| Name | Feel · archetype | `--primary` light | `--primary` dark | `--primary-foreground` |
|---|---|---|---|---|
| **Teal-Slate** | calm, trustworthy · Calm Authority, Data-Dense | `oklch(0.48 0.09 230)` | `oklch(0.66 0.10 220)` | white(L) / ink(D) |
| **Slate-Indigo** | restrained pro · Data-Dense, dashboards | `oklch(0.50 0.13 265)` | `oklch(0.68 0.14 265)` | white(L) / ink(D) |
| **Forest** | growth, finance, eco · Sustainable, fintech | `oklch(0.50 0.12 155)` | `oklch(0.68 0.13 155)` | white(L) / ink(D) |
| **Violet** | modern, AI, media · Cinematic, Glass | `oklch(0.55 0.20 290)` | `oklch(0.68 0.18 290)` | white(L) / ink(D) |
| **Indigo** | friendly-pro · Playful, consumer SaaS | `oklch(0.52 0.17 265)` | `oklch(0.68 0.16 265)` | white(L) / ink(D) |
| **Coral** | energetic, warm · Playful consumer | `oklch(0.58 0.18 28)` | `oklch(0.70 0.17 28)` | white(L) / ink(D) |
| **Terracotta** | editorial warmth · Warm Editorial | `oklch(0.55 0.13 40)` | `oklch(0.68 0.13 45)` | white(L) / ink(D) |
| **Amber** | bright accent (use as fill sparingly) | `oklch(0.74 0.15 75)` | `oklch(0.80 0.14 80)` | **ink both** (bright) |

- **white** = `oklch(0.99 0.005 250)`, **ink** = `oklch(0.20 0.02 260)`. The studio/Step-3 auto-picks per the rule above; verify with the audit.
- **Semantic status (shared):** success `oklch(0.55 0.13 155)` · warning `oklch(0.65 0.13 75)` · destructive `oklch(0.55 0.20 27)` · info `oklch(0.55 0.14 250)` — **AA-darken the *label* text** on light surfaces (T1-b).

## How the Theme Studio uses this
The studio's `PRESETS` array is 3–5 accents from the row above that fit the archetype (e.g. Calm Authority → Teal-Slate,
Slate-Indigo, Forest). The user flips between them live; the live AA badge confirms each.
