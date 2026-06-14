# Changelog

All notable changes to product-playbook are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project uses [Semantic Versioning](https://semver.org/).

## [1.2.3] — 2026-06-14

`/frontend-audit` made trustworthy — closes three silent false-passes found by running the engine on real
sample pages, and wires `/design-system` to actually RUN it. Backward-compatible.

### Fixed
- **Contrast no longer silently passes when it wasn't checked** (`audit.py`, Law 7). The fg/surface token
  pairs were hard-coded to shadcn names, so a project using `--text`/`--surface`/`--bg` got **zero** contrast
  checks yet a `contrast:ok` roll-up. Now: common non-shadcn aliases are checked too, and if colour tokens
  exist but no pair is checkable, it emits a `Law7-unverified` **WARN** instead of a false "ok".
- **Near-twin display fonts are caught** (Law 1). A `--font-display` that is a width/weight variant of the
  body face (e.g. `Inter Tight` over `Inter`) now WARNs `Law1-near-twin` — it isn't a distinct identity. A
  real pairing (e.g. `Space Grotesk` over `Inter`, or IBM Plex Sans/Serif) is not flagged. Font checks now
  also recognise `--font-body`/`--font-base`, not just `--font-sans`.
- **Manual-toggle-only dark mode is caught** (Law 22). A `.dark` block with no `prefers-color-scheme` rule
  that swaps the token set now WARNs `Law22-system` (system preference ignored) — previously reported
  `theming:ok`.

### Changed
- **`/design-system` now RUNS the audit, not just cites it** (`SKILL.md` Step 5). Concrete
  `python commands/frontend-audit/audit.py <sample> DESIGN.md` invocation at confirm-time and post-emit, with
  an instruction to act on `[FAIL]`/`[WARN]` and to treat `Law7-unverified` as "not checked," never "passed."
- `frontend-audit/SKILL.md` check table updated to document the new checks.

## [1.2.2] — 2026-06-14

`/design-system` laws reframed as **outcomes, not tools** — additive, backward-compatible (numbering 1–22 unchanged).

### Changed
- **Universal laws restructured into Floor / Means / Aesthetic / Process** (`references/universal-laws.md`). A
  rule is only a *law* if it holds regardless of stack, aesthetic, or motion level; rules that named a tool or
  a look are now tagged `[MEANS]` / `[AESTHETIC]` recommendations. Every law tagged, a grouped index added, and
  numbering 1–22 kept stable (other files reference laws by number).
- **Law 15 reframed** — the floor is now *"interactive components meet the accessibility floor
  (focus/ARIA/keyboard/states)"*; **shadcn/ui + 21st.dev is the recommended means on a React stack**. Resolves
  the contradiction where the skill's own standalone-preview output could never satisfy a shadcn-mandating law.
- **Law 8 (OKLCH)** and **Law 12 (Framer/GSAP/Three.js ladder)** demoted to `[MEANS]`; their floors (predictable
  lightness / performant + reduced-motion-safe) stay fixed.
- **Laws 6 & 20** restated as outcome + canonical example (purple gradient / dot-not-pill).
- **Tightened catchable floors:** Law 1 (a body-face near-twin like Inter Tight is not a distinctive display),
  Law 7 (an asserted contrast comment is not compliance — compute it), Law 21 (desktop-first + `max-width` is
  the named failure), Law 22 (the system swap must actually apply dark values).
- **Law 19** now also declines **bespoke / non-document surfaces** (canvas/WebGL games, generative art, TUIs).
- **`SKILL.md`** Step-4 lines fixed so the preview caveat no longer reads as a Law-15 exemption — accessible
  primitives are required even in a vanilla preview.

## [1.2.1] — 2026-06-13

Refinements to `/design-system` from a six-archetype test pass — additive, backward-compatible.

### Changed
- **Theme Studio — Mode toggle syncs to the page's real mode on load** (`references/theme-studio.md`).
  It no longer hard-codes "Light" active; a **dark-default** product (ships `<html class="dark">`) opens on
  **Dark**, a light one on **Light**, a class-less one on **System**. Note added: keep samples token-only so
  the Light switch actually adapts (a stray hardcoded colour ghosts in light mode).
- **Craft layer — "shared grammar, distinct voice"** (`references/craft.md`, `SKILL.md`). The signature
  *moves* are reusable across an archetype, but the *voice* (typeface pairing, palette, texture, radius) must
  be derived per product and never lifted from one exemplar — so two Cinematic products look like two brands,
  not clones. Added an explicit gut-check + a Step-6 self-check clause.
- **Craft layer — expressive pages earn ≥1 signature moment** (`references/craft.md`, `SKILL.md`). An
  expressive (Bucket B) page with no signature gesture is under-built; restraint (Bucket A) families
  deliberately ship none.

## [1.2.0] — 2026-06-13

Motion gets a discipline: which motion an archetype may use, and the concrete craft to wire it well.

### Added
- **Motion tier ladder** (`/design-system` Law 12) — turns the motion law from a pure constraint into a
  gated 4-tier ladder: **Tier 0** CSS transitions · **Tier 1** Framer Motion · **Tier 2** GSAP +
  ScrollTrigger · **Tier 3** Three.js / WebGL. Each archetype declares a **motion ceiling** in
  `archetypes.md`; Tier 3 (3D/WebGL hero) is sanctioned only for Cinematic / Marketing-Splash / Glass.
  Every Tier ≥ 1 effect must sit behind `prefers-reduced-motion` with a static fallback, be lazy-loaded,
  and hold a 60fps budget — the "earn its place" restraint floor is unchanged.
- **Craft layer** (`design-system/references/craft.md`, loaded at Step 4) — the per-archetype *signature
  moves* that make a page read as hand-crafted, split into **restraint** families (the craft is precision;
  an explicit "no scroll theatrics" list) and **expressive** families (real, wired GSAP/Framer signatures —
  line-mask reveal, scrub parallax, count-up, spring-stagger, glass/WebGL hero — never stubbed). Snippets
  ship their reduced-motion guard + lazy-load inline.
- **DESIGN.md §7 motion fields** — motion tier, scroll/hero motion, reduced-motion fallback, and perf budget
  are now recorded so the chosen signature survives into the real build.

### Changed
- `/frontend-audit` (`audit.py`) gains three motion checks (WARN): `Law12-reduced-motion` (heavy-motion lib
  with no reduced-motion guard — accepts the media query *or* an idiomatic `useReducedMotion` hook),
  `Law12-layout-anim` (transition targets a layout/paint property), `Law12-long-duration` (CSS animation
  > 1000ms). They fold into the existing `motion` roll-up; reference docs that *name* the libraries do not
  false-positive.

## [1.1.1] — 2026-06-09

### Added
- **Lesson: policy-as-code "parses" ≠ "governs"** (`PRINCIPLES.md` §Lessons baked in) — a
  syntactically-valid but ruleless authorization policy silently degrades to the engine default
  (deny-all / allow-all); load-validate ≥1 rule and fail-loud, build the authz query from escaped
  identifiers + structured request/entity objects (a crafted tool/role name is an injection point
  like SQL), and default-deny on any eval error / no-decision. Generalised from a Cedar RBAC adapter
  build (GateKeeperAI M1.2).

## [1.1.0] — 2026-06-07

### Added
- **Flexible spine resolution** (`PRINCIPLES.md` §Spine resolution) — skills now work on existing /
  brownfield projects, not just products born in the playbook. When there is no `PRODUCT.md`, skills
  resolve the spine from the project's own docs (`CLAUDE.md` → `README.md` → `docs/` → `AGENTS.md`);
  for **code-only** projects they emit a clearly-labelled **INFERRED** summary and recommend
  bootstrapping a spine instead of fabricating a baseline. `/drift-check` carries the full
  three-tier behaviour (resolve spine · graceful write when no `PRODUCT.md` · honest "no recorded
  intent" verdict for code-only).

### Changed
- All 15 skill headers point at `PRINCIPLES.md` §Spine resolution rather than hard-naming `PRODUCT.md`.

### Unchanged (compatibility)
- **`PRODUCT.md`-first** — when `PRODUCT.md` exists, behaviour is identical to 1.0.0. Greenfield
  playbook projects and the existing `evals/` (all Tier-1) are unaffected.

## [1.0.0] — 2026-06-04

First public release.

### Added
- **15 skills** across the product lifecycle: `/playbook` (guided entry-point); Product — `/vision`,
  `/scope`, `/plan`; Development — `/architect`, `/structure`, `/foundation`, `/contracts`, `/build`,
  `/dev-check`; `/test`; `/eval`; `/ship`; `/learn`; and the cross-cutting `/drift-check`.
- **`PRODUCT.md`** living-spine template — every phase reads + appends; the product's story in one file.
- **`PRINCIPLES.md`** — the single rulebook every skill enforces (and verifies with evidence).
- **`VISION.md`** — the toolkit's own completeness contract (every skill + its exit criteria).
- **Evidence-based principle gates** — each skill verifies its named principles are actually
  implemented (composing `/code-review`, `/security-review`, `/verify`, `/run`, `/doc-audit`) before
  handing off; deterministic checks (secret-scan, lint, tests, dep-vuln) run via pre-commit + CI.
- **Three install modes** — global (`./install.sh`), project-level (`./install.sh --project <path>`),
  and plugin (`.claude-plugin/` → `/plugin install`).
- `manifest.json`, `evals/evals.json` (a behaviour check per skill), and an `install.sh` installer.

[1.2.1]: https://github.com/kish21/product-playbook/releases/tag/v1.2.1
[1.2.0]: https://github.com/kish21/product-playbook/releases/tag/v1.2.0
[1.0.0]: https://github.com/kish21/product-playbook/releases/tag/v1.0.0
