# Building the skeleton — the eight steps in full

> Printed whole by `status.py next --phase foundation` (a UI's parts only for a UI product): one call instead of
> one per step. SKILL.md names the eight; this file is what each one actually means, including the ownership
> seams with /structure and the failures behind each rule.

## 1. Dependency manifest — its contents and provability

**This phase owns its CONTENTS AND PROVABILITY** (`MECHANISMS-ON-DEMAND.md` §Seam) — `/structure` created the file and
its dev/prod split; **install into the project's own environment** (`uv sync` → `.venv`, on the version `requires-python` pins; Node: `engines`), and every task-runner line that needs the packages runs through it (`uv run pytest`, never a bare `python -m pytest`, which uses whatever Python the machine finds first - `set foundation filled` checks both); pin the versions, **actually install, and commit the lockfile** (`uv.lock`, `package-lock.json`,
`pnpm-lock.yaml`, `Cargo.lock`, `go.sum` — `set foundation filled` refuses a manifest without one), write the tool
config files those scripts reference (`biome.json`, `tsconfig.json`, the test-runner config), and get the first real
run to pass. A frontend manifest counts too: it lists every package the code imports (a logged run imported React
with no `react` in `package.json` and no bundler, so nothing could build it). Then a runnable entrypoint with a
**health/hello path** (the walking skeleton), and **prove it boots before step 2 below** with one call:
`devserver.py check --cmd "<start command>" --port <port> --health <url>` (beside SKILL.md) — it starts the app,
waits for the answer, stops the whole process tree and proves the port is free. Print its line: the app runs and how
to see it (the command, the address). A line, not a pause. This boot never counts as SKILL.md Step 3b's evidence,
because steps 3–8 below change the boot path.

**Missing root files:** no `.gitattributes` → copy `templates/gitattributes` (LF everywhere; a Windows checkout
otherwise ships CRLF into a Linux image). Secret scanner is gitleaks and it has no config → copy
`templates/gitleaks.toml`. Both are `/structure`'s files; fill the gap, do not redesign them.

## 2. The dev seed

`/structure` named the task-runner target; **this phase makes it real** — the same ownership split as the dependency
manifest (`MECHANISMS-ON-DEMAND.md` §Seam): idempotent, production-refusing, and it prints the fake dev credentials
once when it finishes.
- **Refuse production by the target, not only by a name:** refuse when `APP_ENV`/`NODE_ENV` says production **and**
  when the database host is not a local or declared dev host. A logged run refused only `APP_ENV=production`, so a
  wrong database address would still have been seeded.
- **The scope edge (this phase vs `/contracts`):** the seed creates the **minimum identity** the login needs (one
  user/account table), plus the agent's kill-switch row when `Agent: yes`. **No domain models, fixtures or money
  types** — those are `/contracts`, where their types, units and migrations are decided. A logged run added order,
  refund and audit models with money as a float and no migration; that is two phases of decisions made by accident.

## 3. Config loader + startup guard

Read `.env`/config; add a **startup guard** (fail-loud on misconfig, fail-closed on security) that holds the
placeholder values as a **known-bad list** and rejects them by name, with a message saying how to generate a real value
(`openssl rand -base64 32`). Keep the list next to the loader so adding a secret to `.env.example` and forgetting the
guard is visible in one file. Match by name because `make setup` copying the example to `.env` is the normal path, so this guard is the only thing between a fresh clone and a public signing key.
- **No fallback values for a secret.** `os.getenv("SECRET", "dev-value")` or `process.env.SECRET || "x"` boots without
  the real value in every environment — a logged run's production mode loaded a hardcoded key that way. A variable
  `.env.example` marks `CHANGE_ME` has no default in code; `set foundation filled` refuses one.
- **The guard runs at boot, in the entrypoint** — not only inside a request handler or a dependency that runs later.
  A logged run's app answered `/health` with every placeholder set, because only `/login` ever called the loader.
- **Connection URLs say `127.0.0.1`, never `localhost`** — in `.env.example`, its comments and the runbook: on Windows
  with Docker, `localhost` can resolve to IPv6 `::1` first and hang (a logged run lost a boot to it).

## 4. The test datastore + its guard

Alongside the app's own: provision a separate disposable target **of the same engine `#Architecture` chose** (SQLite
standing in for Postgres tests a different database — `set foundation filled` refuses it unless the user's override is
recorded), wire the runner to the app's config loader, and write the **refuse-to-run guard** before any test exists.
Order matters — a suite written first is a suite that has already run once against whatever was configured. The
guard compares **host, port and database name**, never the whole URL as a string, and **never prints a password**.
Recipe per custody: `references/test-datastore.md`.
**A local container is this project's own:** name it after the project (`<project>-pg`), and never reuse a container
another project owns (`docker ps` names them): two projects on one machine would share, and reset, each other's data.
**So are its databases, on any server:** `<project>_dev` and `<project>_test`, never a generic `app_test`; and the
guard also refuses a test database stamped with a migration this repo does not have, naming it. A logged build found
its test tables replaced by a sibling project's on the same server and spent ~6 calls working round it.

## 5. Logging, tracing, base infra

**Structured logging** (no prints) **+ a tracing / error-reporter hook** (even a stub behind an adapter) — wire base
infra behind the adapters from `/architect` (DB/LLM/queue), even if stubbed.
- **The real AI adapter fits its caller.** The tests pass a fake where the caller takes the provider, so a fake can
  fit a method the real class lacks (a logged loop called `.complete`; its adapter had only `async acomplete`). One
  test builds the REAL adapter on a dead endpoint (`http://127.0.0.1:9`, no network) and passes it where the caller
  takes the fake: it must reach the call, then take the failure path `#Architecture` recorded — a hand-off to a
  person, not an exception (a logged run's connection error escaped and crashed the run). Its `evidence:` line names
  "the real adapter".
- **A fake model answers from a script** — fixed replies, one of them wrong, which the eval harness must score as a
  miss. A fake that returns its input (an echo) makes every golden and behaviour test pass by construction;
  `set foundation filled` refuses one.
- **The skeleton, not the product:** one generic read tool and a generic task prove the wiring. The product prompt,
  the decision pipeline and golden cases from real product cases are `/build`'s (SKILL.md: What /foundation must NOT
  build).

## 6. The auto-layer

Dev tooling lint + format + **a type checker** (Python: pyright or mypy; TypeScript: `tsc --noEmit`; the one
`#Architecture` recorded, else the user's choice from the step-0 card; none only with the user's reason recorded as
`no type checker: <reason>`) + **the commit-hook runner `#Architecture` recorded** running **secret-scan +
dependency-vuln scan**; this is what enforces the deterministic checks on every commit so the later skills don't rely
on memory. **Install the hooks** (`pre-commit install`, `lefthook install`, husky's `prepare`) and make one real commit
through them — a configured runner that is not installed runs on no commit (`set foundation filled` checks the hook
file). **The secret scan reads what git holds**, never the working folder: `gitleaks git` (CI, the history) and
`gitleaks git --staged` (the hook). `gitleaks dir .` also reads the gitignored `.env`, `.venv/` and `node_modules/`,
and two logged runs spent 5–10 calls tuning the config around findings that could never be committed. **The scan
must be able to fail:** `set foundation filled` commits a fresh fake token through the installed hooks in a throwaway
copy and refuses when it goes through — a logged hook ran `python -m detect_secrets.main scan`, which exits 0 doing
nothing, and `|| true` swallows any scanner. The allowlist names the placeholder VALUES, never `.env.example`'s path
(the template does): that is the file people paste keys into. Wire an **automated dependency-update bot** (`.github/dependabot.yml`/Renovate) here too — adding the CVE gate
on day one keeps it green from the start; bolting it on later means inheriting a backlog of CVEs that piled up
unscanned.

**UI product (`DESIGN.md` exists): the frontend audit joins the auto-layer.** Composed by `/build` alone, it runs only
when someone remembers it — and a gate you must remember is not a gate.
- **The copy.** Copy the installed engine — the path SKILL.md Step 2 item 6 names; never search the plugin cache,
  whose text sort picks an old version — to `<tooling>/frontend-audit/audit.py`, where `<tooling>` is the repo-wide
  tooling folder `STRUCTURE.md` names (e.g. `scripts/`), and **add `frontend-audit/` to `STRUCTURE.md`'s tree** in the
  same commit (`check_structure.py --suggest` prints the line; the structure check fails an unmapped folder). **Keep the `frontend-audit/audit.py`
  ending:** the installed engine finds the copy by it and says when it falls behind. **Commit it** — a clean clone has
  no plugin, and a CI step that downloads the script adds a network dependency and a pin someone must bump by hand.
  Record the path and its `--version` in `#Foundation`.
- **One run over the whole UI.** `DESIGN.md` + the token stylesheet + the UI source tree together, never only the
  staged files: Law 14b resolves a component's tokens across files, so a staged-only run reports tokens the
  stylesheet defines as missing.
- **Hook:** a pre-commit command in the recorded runner — `python <tooling>/frontend-audit/audit.py DESIGN.md
  <ui-dir>` — filtered to commits that stage a UI file or `DESIGN.md`. Exit 1 on an ERROR refuses the commit; a WARN
  prints and passes.
- **CI:** the same command as a step of the job every PR runs (step 8).
- **Interpreter:** the engine is stdlib-only Python 3. Use the command the project already runs its scripts with;
  hosted CI runners have it, a container or self-hosted runner needs it set up. A machine without it fails the hook
  loudly — never a silent skip. Say so in `docs/runbook.md`.
- **Refresh:** after a plugin update, the installed engine's `engine copy:` line says when this copy is older; copy
  the engine over it and commit.

## 7. The design tokens, if this product has a UI

(`DESIGN.md` exists): confirm the token stylesheet `/design-system` emitted is **imported by the app's root entry and
resolves at runtime** — load a page and read a token back, the same "prove it flows" bar as config. A spec-only token
layer is dead config with a stylesheet's name: components render unstyled while lint, typecheck and the audit stay
green. Missing entirely → this is `/design-system`'s output, so send it back rather than writing CSS here.
**`DESIGN.md` chose no stylesheet of its own** (a host's components, e.g. an admin's design system): prove instead
that **a route renders the UI shell** (`base.html` or the root layout) and it loads — a logged run wrote the shell
and no route ever served it.

## 8. CI that mirrors the prod bootstrap

CI that installs **from the lockfile**, bootstraps from the real schema/migrations **on the engine `#Architecture`
chose**, runs lint/secret-scan/dep-scan/tests (+ the frontend audit copy for a UI product), **builds + runs in the
container prod uses**, and **blocks merge on red** — green. CI creates throwaway creds at runtime (no secret in repo).
Prove it with `ci_local.py` (beside SKILL.md) — see `references/verify.md` §CI.
