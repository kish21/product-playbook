# Building the skeleton — the eight steps in full

> Opened by /foundation at Step 2. SKILL.md names the eight; this file is what each one actually
> means, including the ownership seams with /structure and the failures behind each rule.

1. **Dependency manifest: this phase owns its CONTENTS AND PROVABILITY** (`MECHANISMS.md` §Seam) — `/structure` created the file and its dev/prod split; pin the versions, **actually install**, write the tool config files those scripts reference (`biome.json`, `tsconfig.json`, the test-runner config), and get the first real run to pass. Then a runnable entrypoint with a **health/hello path** (the walking skeleton).
2. **The dev seed** (`/structure` named the task-runner target; **this phase makes it real** — the same
   ownership split as the dependency manifest, `MECHANISMS.md` §Seam): idempotent, production-refusing, and
   it prints the fake dev credentials once when it finishes.
3. **Config loader** reading `.env`/config; add a **startup guard** (fail-loud on misconfig, fail-closed on security) that holds the placeholder values as a **known-bad list** and rejects them by name, with a message saying how to generate a real value (`openssl rand -base64 32`). Keep the list next to the loader so adding a secret to `.env.example` and forgetting the guard is visible in one file.
4. **The test datastore + its guard**, alongside the app's own: provision a separate disposable target, wire the runner to the app's config loader, and write the **refuse-to-run guard** before any test exists. Order matters — a suite written first is a suite that has already run once against whatever was configured.
5. **Structured logging** (no prints) **+ a tracing / error-reporter hook** (even a stub behind an adapter) — wire base infra behind the adapters from `/architect` (DB/LLM/queue), even if stubbed.
6. **The auto-layer:** dev tooling lint + format + **the commit-hook runner `#Architecture` recorded** running **secret-scan + dependency-vuln scan**; this is what enforces the deterministic checks on every commit so the later skills don't rely on memory. Wire an **automated dependency-update bot** (`.github/dependabot.yml`/Renovate) here too — adding the CVE gate on day one keeps it green from the start; bolting it on later means inheriting a backlog of CVEs that piled up unscanned.

   **UI product (`DESIGN.md` exists): the frontend audit joins the auto-layer.** Composed by `/build` alone,
   it runs only when someone remembers it — and a gate you must remember is not a gate.
   - **The copy.** Copy the installed engine — the path SKILL.md Step 2 item 6 names; never search the
     plugin cache, whose text sort picks an old version — to `<tooling>/frontend-audit/audit.py`, where
     `<tooling>` is the repo-wide tooling folder `STRUCTURE.md` names (e.g. `scripts/`), and register it
     there. **Keep the `frontend-audit/audit.py` ending:** the installed engine finds the copy by it and
     says when it falls behind. **Commit it** — a clean clone has no plugin, and a CI step that downloads
     the script adds a network dependency and a pin someone must bump by hand. Record the path and its
     `--version` in `#Foundation`.
   - **One run over the whole UI.** `DESIGN.md` + the token stylesheet + the UI source tree together,
     never only the staged files: Law 14b resolves a component's tokens across files, so a staged-only run
     reports tokens the stylesheet defines as missing.
   - **Hook:** a pre-commit command in the recorded runner — `python <tooling>/frontend-audit/audit.py
     DESIGN.md <ui-dir>` — filtered to commits that stage a UI file or `DESIGN.md`. Exit 1 on an ERROR
     refuses the commit; a WARN prints and passes.
   - **CI:** the same command as a step of the job every PR runs (step 8).
   - **Interpreter:** the engine is stdlib-only Python 3. Use the command the project already runs its
     scripts with; hosted CI runners have it, a container or self-hosted runner needs it set up. A machine
     without it fails the hook loudly — never a silent skip. Say so in `docs/runbook.md`.
   - **Refresh:** after a plugin update, the installed engine's `engine copy:` line says when this copy is
     older; copy the engine over it and commit.
7. **The design tokens, if this product has a UI** (`DESIGN.md` exists): confirm the token stylesheet
   `/design-system` emitted is **imported by the app's root entry and resolves at runtime** — load a page
   and read a token back, the same "prove it flows" bar as config. A spec-only token layer is dead config
   with a stylesheet's name: components render unstyled while lint, typecheck and the audit stay green.
   Missing entirely → this is `/design-system`'s output, so send it back rather than writing CSS here.
8. **CI** that installs, bootstraps from the real schema/migrations, runs lint/secret-scan/dep-scan/tests (+ the frontend audit copy for a UI product), **builds + runs in the container prod uses**, and **blocks merge on red** — green. CI creates throwaway creds at runtime (no secret in repo).
