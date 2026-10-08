# Root scaffolding — the files every shape needs

> Printed by `next --phase structure`. Each is a **capability**, filled by the tool `#Architecture` recorded:
> a file scaffolded by habit silently overrides a tool decision one phase later.

**The bundle holds ONLY what the product's decisions shape:** `STRUCTURE.md` · the agent instructions (`CLAUDE.md`
or `AGENTS.md`) · `README.md`: what it is, how to install, lint and run the smoke test (an existing one gets that
section with the edit tool) · `.env.example` (every variable, `CHANGE_ME__<VAR>__CHANGE_ME`
placeholders, a how-to comment each) · the **commit-hook runner** running lint + format + secret-scan · the **task
runner** with generic targets a newcomer can just run (`dev` · `frontend` (full-stack) · `test` · `lint` · `check`
(lint+test) · with a DB `seed` · `reset`) · the dependency manifest with a **dev/prod split** (the lockfile is the
package manager's) · `platform.yaml` + `product.yaml` + ONE typed loader refusing a `CHANGE_ME` value · the entry
point · `tests/test_smoke.py` (or the stack's equivalent: imports every module, a placeholder fails the boot).

**`scaffold` writes — never type these:** `CONTRIBUTING.md` · `SECURITY.md` (enables GitHub's "Report a
vulnerability") · `CHANGELOG.md` (`[Unreleased]`) · the standard ignore lines (`.env` and its variants,
`!.env.example`, `.venv/` / `node_modules/`, caches) added to the existing file · every folder `STRUCTURE.md`'s tables
name, with its package file (`__init__.py`) or `README.md` from the table's line, and each module's `tests/` ·
`.gitattributes` (LF) · the gitleaks config · `scripts/check_structure.py`. A file the bundle holds is kept.

**When relevant:** `Dockerfile`+`docker-compose.yml`+`.dockerignore` · CI workflow · `.github/dependabot.yml` ·
migrations config · observability config · `evals/` (AI) · `docs/` · `scripts/`.

**Never:** a placeholder test · a README or `.gitkeep` in a folder that holds a file · empty route/service/schema
stubs (`/build` writes them) · product logic.
