# Changelog

All notable changes to product-playbook are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project uses [Semantic Versioning](https://semver.org/).

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
