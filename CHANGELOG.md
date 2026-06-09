# Changelog

All notable changes to product-playbook are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project uses [Semantic Versioning](https://semver.org/).

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

[1.0.0]: https://github.com/kish21/product-playbook/releases/tag/v1.0.0
