# Craft layer — archetype signature moves (the *how*, not just the *what*)

> Loaded by `/design-system` **Step 4** (the sample build), *after* the archetype is confirmed.
> `archetypes.md` says **which motion tier is allowed**; this file says **what the signature gesture
> actually is and how to wire it** so the page reads as *deliberately crafted*, not generic.
>
> **The split that matters:** for **restraint** families the craft *is precision* — the right move is
> the *absence* of decorative motion. For **expressive** families, **wire the real signature move — never
> stub it in a comment.** A cinematic sample with `// GSAP would go here` is a failed sample.
>
> Every Tier ≥ 1 snippet below already carries its **`prefers-reduced-motion` static fallback** and a
> **lazy-load**, per Law 12. **Do not strip them**, and never offer a Tier ≥ 1 move to a Tier-0 family.

## Two rules that govern this whole file

1. **Shared grammar, distinct voice.** The signature *moves* below (line-mask, scrub parallax, count-up,
   spring-stagger, glass/WebGL hero) are the reusable **grammar** of an archetype. The **voice** — typeface
   pairing, palette, texture, radius — is **derived for THIS product in Step 3**, **never lifted from one
   exemplar.** Two Cinematic products must share the motion grammar and still look like **two different
   brands**. *Gut-check:* if the page resembles a specific site you've seen (same fonts + same texture),
   change the voice — that's a clone, not a craft. craft.md owns the *moves*; `archetypes.md` + Step 3 own
   the *look*.
2. **Expressive pages earn at least ONE signature moment.** An expressive family (Bucket B) that ships a
   page with *no* signature gesture is under-built ("safe/flat") — pick at least one within its tier (a
   scroll-reveal, a full-bleed break, a hero gesture). **Restraint families (Bucket A) deliberately ship
   none** — for them, zero decorative motion *is* the signature.

---

## Archetype → bucket index  (the routing table — no family falls through)

| Family | Bucket | Tier cap | Signature recipe |
|---|---|---|---|
| Data-Dense Pro | **A · restraint** | 0 | Precision signature |
| Terminal-Core | **A · restraint** | 0 | Precision signature (mono-structural) |
| Calm Authority | **A · restraint** | 0 | Precision signature (orderly/trust) |
| Conversational / AI-chat | **A · restraint** | 0 | Precision signature (streaming only) |
| E-commerce / Retail | **A · restraint** | 0 | Precision signature (+ product hover-lift) |
| Social / Feed | **B · expressive** | 1 | Optimistic spring micro-feedback |
| Playful Consumer | **B · expressive** | 1 | Spring stagger |
| Editorial Minimalism | **B · expressive** | 2 | Gentle scroll fade-up + light parallax |
| Warm Editorial | **B · expressive** | 2 | Gentle scroll fade-up + light parallax |
| Neo-Brutalist | **B · expressive** | 2 | Hard-edged deliberate scroll |
| Glass / Soft Depth | **B · expressive** | 3 | Glass/backdrop hero (chrome stays ≤ Tier 1) |
| Bold Brand / Marketing Splash | **B · expressive** | 3 | Scroll narrative (line-mask + scrub) |
| Cinematic / Media-Forward | **B · expressive** | 3 | Full signature (line-mask + scrub + count-up) |

**How to use:** find the confirmed family → its bucket → apply that bucket's craft below, composing the
named moves its recipe lists. Never exceed the tier cap (that's the `archetypes.md` ceiling restated).

---

## Bucket A — Restraint archetypes · the craft *is* precision

For enterprise, data, trust, chat and retail UIs, decorative motion **erodes** the product's credibility.
The signature is restraint executed precisely — what a senior designer ships for Linear / Stripe / Mercury.

**Positive craft (do these — this is what reads as "designed"):**
- **Hairline structure:** 1px borders + generous, consistent whitespace carry the layout; separation by
  border/space, not big shadows (one subtle elevation step max).
- **Numeric discipline:** `font-variant-numeric: tabular-nums`, numbers right-aligned, baselines aligned,
  IDs/amounts in mono. Status = a coloured **dot + label**, never a filled pastel pill.
- **Instant feedback only:** hover/focus/active in **≤ 120–160ms**, `transform`/`opacity` only. State
  changes feel immediate, not animated.
- **Hierarchy by type, not effects:** weight + size + a muted foreground do the work; one accent, used
  sparingly for the primary action.

**❌ The trust-breaker list — do NOT, here:**
- No scroll-triggered reveals, parallax, pinned sections, count-up tickers, or blend-mode cursors.
- No film grain, no decorative looping animation, no hero "experience."
- **No Tier ≥ 1 library.** If you reached for GSAP / ScrollTrigger / Three.js in a Bucket-A product,
  stop — it's the wrong instinct here and the audit + Step-6 gate will flag it.

**Per-family precision note:**
- **Data-Dense Pro / Terminal-Core:** density + alignment are the craft; mono used structurally; snappy
  (100–160ms) micro-feedback.
- **Calm Authority:** orderly sectioning, even rhythm, restrained accent — "serious and safe."
- **Conversational:** the only motion is **streaming text** + a gentle message-in (opacity/translate, one-shot).
- **E-commerce:** the one flourish allowed is a **product image hover-lift** (`transform` only) + quick
  add-to-cart feedback; everything else stays calm so price + CTA lead.

---

## Bucket B — Expressive archetypes · wire the real signature, scaled to tier

These families *earn* expressive motion. Build the sample with the **actual** gesture wired. The named
moves below are defined **once**; each family's recipe composes them up to its tier cap.

### Non-motion craft details (half the win — a generic *layout* sinks an expressive page too)
- **Display type that commits:** large display via `clamp(...)`, **`line-height` ~0.9–1.05**, tight
  tracking (~`-0.03em`); pair the grotesque display with an **italic-serif accent face** for emphasis
  words — a strong editorial signal.
- **Deliberate radius:** either soft+rounded (Glass/Playful) or **anti-rounded ~2px** (Editorial/Cinematic/
  Brutalist) — not the default 8px "AI card."
- **Full-bleed structure:** edge-to-edge media/CSS-art breaks, not a centred column of boxed cards.
- **Texture (sparingly):** a faint grain or gradient field adds depth — keep any looping animation subtle
  and short (see the long-duration audit note below).

### The named moves (each ships its guard + lazy-load — copy them intact)

> **Standalone-preview rule:** a no-stack preview CAN and SHOULD load GSAP/Framer from a CDN so the sample
> ships *real* motion. The single guard wrapper below covers every GSAP move. Animate **transform/opacity
> only** (never `top`/`width`/`height`/`margin` — that janks *and* trips `Law12-layout-anim`).

```html
<!-- Tier 2 · GSAP + ScrollTrigger — loaded from CDN for a standalone preview -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
<script>
(function () {
  // Tier >= 1 guardrail (Law 12): no motion if the user asked for none, and degrade gracefully.
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (typeof gsap === 'undefined') return;           // page is fully readable without JS
  if (reduce) { document.querySelectorAll('.reveal').forEach(function (el) { el.style.opacity = 1; }); return; }
  gsap.registerPlugin(ScrollTrigger);

  // MOVE · line-mask reveal — heading slides up from under its own clip (transform only)
  gsap.from('.headline .line > span', { yPercent: 110, duration: 0.9, ease: 'power4.out', stagger: 0.1 });

  // MOVE · scrub parallax — full-bleed art drifts on scroll (yPercent = transform, GPU-friendly)
  gsap.utils.toArray('.bleed__art').forEach(function (art) {
    gsap.fromTo(art, { yPercent: -8 }, {
      yPercent: 8, ease: 'none',
      scrollTrigger: { trigger: art, start: 'top bottom', end: 'bottom top', scrub: true }
    });
  });

  // MOVE · scroll fade-up — sections rise + fade as they enter (transform/opacity)
  gsap.utils.toArray('.reveal').forEach(function (el) {
    gsap.from(el, { opacity: 0, y: 32, duration: 0.7, ease: 'power2.out',
      scrollTrigger: { trigger: el, start: 'top 88%' } });
  });

  // MOVE · count-up stat — number tweens to its target on enter (text content, not layout)
  document.querySelectorAll('[data-count]').forEach(function (el) {
    var target = parseInt(el.getAttribute('data-count'), 10), o = { v: 0 };
    gsap.to(o, { v: target, duration: 0.9, ease: 'power2.out',
      scrollTrigger: { trigger: el, start: 'top 90%' },
      onUpdate: function () { el.textContent = Math.round(o.v); } });
  });
})();
</script>
```
*Markup the moves expect:* a headline as `<h1 class="headline"><span class="line"><span>…</span></span></h1>`
(the inner `<span>` is what transforms; the `.line` gets `overflow:hidden`), full-bleed art as
`.bleed__art`, any section to reveal gets `class="reveal"`, and stat numbers carry `data-count="41"`.

```jsx
// MOVE · spring stagger — Tier 1, Framer Motion (motion/react) for Playful / Social
import { motion, useReducedMotion } from 'motion/react';     // lazy-import in the real build
function Cards({ items }) {
  const reduce = useReducedMotion();                          // Tier >= 1 guardrail
  return items.map((it, i) => (
    <motion.div key={i}
      initial={reduce ? false : { opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: i * 0.05, type: 'spring', stiffness: 320, damping: 26 }}>
      {it}
    </motion.div>
  ));
}
```

**Tier 3 · Glass / Cinematic hero (WebGL note):** a Three.js / React-Three-Fiber shader or video backdrop
mounts in the **hero only**, **lazy-loaded** (`import('three')`), behind the same `prefers-reduced-motion`
check (show a static poster frame instead), with a 60fps budget. The **app chrome stays Tier 0–1** — never
let the 3D layer leak into navigation, forms, or content.

### Signature recipes (thin — compose the moves above)
- **Cinematic / Media-Forward** (cap 3): line-mask reveal + scrub parallax + count-up; optional WebGL/video
  hero. Anti-rounded radius, huge display, italic-serif accent. The *media* is the hero.
- **Marketing Splash** (cap 3): line-mask reveal + a scroll narrative (pinned sections / scrub); WebGL hero
  optional. Dramatic display scale.
- **Editorial / Warm Editorial** (cap 2): gentle scroll fade-up + *light* parallax only — restraint inside
  expression; serif display, generous measure. No count-up theatrics.
- **Neo-Brutalist** (cap 2): the same scroll moves but **hard-edged and deliberate** (snappier ease, offset
  hard shadows, no soft blur).
- **Glass / Soft Depth** (cap 3): glass/backdrop hero (translucency + soft gradient) as the signature; chrome
  motion stays Tier 0–1 (smooth 250ms springy hovers).
- **Playful / Social** (cap 1): spring stagger + optimistic tap feedback (Framer Motion). Lively, never heavy.

---

## Audit & Theme-Studio notes (so the wired sample actually passes)
- **`Law12-reduced-motion`:** every snippet above already includes the `prefers-reduced-motion` guard —
  keep it, or `/frontend-audit` warns.
- **`Law12-layout-anim`:** scroll/parallax must move via **`transform`/`yPercent`**, never `top`/`width`/
  `margin` in a CSS `transition`.
- **`Law12-long-duration`:** a *CSS* `animation`/`transition` over ~1000ms trips a WARN — keep any decorative
  loop (e.g. grain) short, or accept it as an intentional, documented scroll effect. (GSAP JS `duration:` is
  not a CSS property and is not flagged.)
- **Theme Studio:** ScrollTrigger anchors to the real document scroller; the studio's width buttons
  (`@container`) are **not** expected to drive scroll pins — note this so the interactive sample doesn't
  look broken when a width button is pressed.
- **Persist the choice:** record the wired signature + tier in `DESIGN.md` §7 (Step 5) so `/new-component`
  and later build steps inherit the craft — `craft.md` teaches the *sample*; §7 is what *survives*.
