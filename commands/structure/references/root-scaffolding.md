# Root scaffolding — the files every shape needs

> Opened by /structure at Step 2, after the shape is chosen. Each entry is a **capability**; the tool
> that fills it is whichever one `#Architecture` recorded. Scaffolding a file by habit, rather than
> from the recorded choice, is how a tool decision gets silently overridden one phase later.

**Root (every shape) — the *capability*, filled by the tool `#Architecture` chose:** `README.md` ·
ignore rules · `.env.example` (unmistakable `CHANGE_ME__<VAR>__CHANGE_ME` placeholders only) ·
`CONTRIBUTING.md` · **secret-scan config** (e.g. `.gitleaks.toml`: `useDefault=true`, allowlist only
documented dev fakes + `.env.example`) · **commit-hook runner** running lint + format + secret-scan
(`.pre-commit-config.yaml` for Python · `lefthook.yml` · `.husky/` for Node — whichever the ADR names)
· `SECURITY.md` (how to report a vuln —
enables GitHub's "Report a vulnerability"; cheap on day one, annoying to retrofit) · `CHANGELOG.md`
(Keep a Changelog format, start with an `[Unreleased]` section) · **task runner** (`Makefile` · npm
scripts · `just` — whichever the ADR names) · dependency manifest with **dev/prod split** · `tests/` · `docs/` (will hold PRODUCT.md, STRUCTURE.md,
docs/features/*) · `tools/`|`scripts/`. **When relevant:** `Dockerfile`+`docker-compose.yml`+
`.dockerignore` · CI workflow · `.github/dependabot.yml` (or Renovate) · migrations config ·
observability config · `benchmark/`|`evals/` (AI).

**`Makefile` generic targets** a newcomer can just run: `dev` · `frontend` (full-stack) · `test` ·
`lint` · `check` (lint+test) · and, with a DB, `seed` · `reset`.
