# Structure — <product name>

> **Status:** `draft | approved by <owner> on <YYYY-MM-DD>` · written `<YYYY-MM-DD>` from `docs/architecture.md` ·
> last checked against the disk `<YYYY-MM-DD>`. **Owner:** read In short, the tree and Not here yet. **Developers and
> coding agents:** all of it; before adding a file, read Where does a new file go? and Dependency rules. A change to the
> layout updates this file in the same commit and adds a line under Changes.

<!-- HOW TO FILL THIS TEMPLATE (delete every comment when you write the file)
1. Every `##` section below is ALWAYS present, in this order, with this heading. A section that does not apply holds
   `Not applicable: <reason>`; a single row that does not apply says the same in its first cell. The checker reads
   `## Modules`, `## Inside a module`, `## Where does a new file go?`, `## Where decisions live`, `## Hub files` and
   `## Changes` by name. Keep every table's header row and its `|---|` separator row exactly as given: never rename,
   drop or reorder a column.
2. Size: at most 14,000 bytes, no minimum - a small product gets a short file. Never pad; never repeat a row from one
   table in another (a path appears in the tree, then in ONE table that explains it).
3. Names: use the block names of the architecture's `## Building blocks` as the module names. A block may live in more
   than one path (a backend folder and a UI folder); list every path. A folder the architecture does not name (shared
   setup, prompts, evals, scripts) gets one row under `## Where does a new file go?` saying why it exists.
4. Paths: as on disk, in backticks, from the repository root; a folder ends in `/`. A path in `## Modules`,
   `## Entry points`, `## Where decisions live` and `## Hub files` exists today; a planned one goes ONLY under
   `## Not here yet`. Create a folder only for a module or a home the architecture names - no empty folders for later.
5. Plain words in full sentences: no slash-joined word lists, no open-ended lists. An unknown is written as
   `Not decided: <what decides it>`.
6. Shape by product kind (from the architecture's summary): a web app keeps server-rendered templates in the module that
   renders them; a separate browser app has its own top-level folder and build; an API keeps its specification in one
   named place; a scheduled job or pipeline has its steps (read, transform, write) as modules and its schedule as an
   entry point; a mobile app keeps generated platform folders (`ios/`, `android/`) listed as generated; a library puts
   its public API in one module; a CLI puts its commands in one module.
7. Results are never claimed: a check's result is the last line its command printed in this session, with the date.
-->

## In short

<!-- 3-5 plain sentences: the shape (domain modules, layers, or steps), one deployable or several, why this shape fits the
team and the product, and the one rule a newcomer must not break. Then the tree: folders only, no files; every folder on
disk down to each module's direct sub-folders, deeper only where a later file has its home there; leave out installed
dependencies, caches and build output. One short note per folder after `#`. -->

<3-5 sentences.>

```
<the tree>
```

## Modules

<!-- One row per code unit of the architecture: a domain module, a layer, a package or a UI feature folder. -->

| Path | What it is for | Others may call only | Owns (data it changes) | Depends on | Tests at |
|---|---|---|---|---|---|
| `<path>/` | <one plain sentence> | `<path>/service.py: <function or class>` | <tables, files, or `-`> | `<path>/`, or `-`, or `injected: <path>` | `<path>/tests/` |

## Entry points

<!-- Every way the product starts: the web process, a worker, a scheduled job, a CLI command, the migration runner. -->

| Process | Entry file | Start command | Runs where (from Running it in the architecture) | Schedule or trigger |
|---|---|---|---|---|
| <web app> | `<path>` | `<command>` | <host> | <requests> |

## Dependency rules

<!-- `A → B` means "code in A may import B". Line 1: the order inside a module. Line 2: the rule between modules - exactly
one of "a module imports another only through its `Others may call only` entry" or "modules never import each other;
`<composition root>` wires them". Events and network calls between parts are listed as rows, not arrows. -->

```
inside a module: <outer part> → <inner part>
between modules: <the one rule>
```

| Rule | Why (architecture D# or R#) | Enforced by (the file or command that fails today when it is broken) |
|---|---|---|
| <e.g. Only `<path>/adapters/` imports the model vendor's SDK.> | <R4> | <`tests/test_imports.py`, or `Not enforced yet: added by <phase>`> |

## Inside a module

<!-- Row 1: one ordinary module, its real files as `file - purpose; file - purpose`. Then one row per module that adds or
omits files, naming only the difference. Never list a file a module does not have. -->

| Path | Convention |
|---|---|
| `<path>/` | <`service.py` - the entry other modules call; `store.py` - its tables; `tests/` - its tests> |

## Where does a new file go?

<!-- One row per kind of thing a developer or agent adds - never one row per module. Include each kind this product has:
a screen, a domain rule, an outside-service adapter, a test, a cross-module test, a fixture, an eval or golden case, a
migration, a prompt, a product setting, an engine setting, a secret, a script, a generated file. As many rows as kinds.
Each When cell starts "If you are adding ..." and names the hub line it also needs. -->

| Path | When |
|---|---|
| `<path>/` | <If you are adding a ..., it goes here because ...; also add one line to `<hub file>`> |

**Adding a feature, in order:** <1. module files · 2. its tests · 3. a migration if a table changes · 4. the hub lines ·
5. a golden or eval case if the AI is involved · 6. update this file if a folder is new>.

## Tests and fixtures

| Level | Lives in | Naming and markers | May call an outside service? | Command |
|---|---|---|---|---|
| Module tests | `<path>/tests/` | `test_<thing>.py` | no - stand-ins only | `<command>` |
| Cross-module tests | `tests/` | <marker> | <no / only behind a flag> | `<command>` |
| Golden or eval cases | `<path>/` | <one file per case> | <only behind a flag> | `<command>` |

**Fixtures:** <where inputs live, where expected answers live - kept apart so a test cannot read the answer as input -
and what is never committed: real or personal data, model transcripts, secrets>.

## Root files

<!-- Each file in the repository root, what it is for and which decision chose it. Tooling lives here, not under
`## Where decisions live`. -->

| File | Purpose | Chosen in |
|---|---|---|
| `<manifest>` | <dependency manifest and tool settings> | <D#> |
| `<lockfile>` | <exact versions; changed only by the package manager> | <D#> |
| `.env.example` | <the secrets and environment values the app reads, with placeholders> | <D#> |

## Where decisions live

<!-- One row per architecture decision whose result is a code home: an adapter, prompts, migrations, the settings files,
the stop switch. Start each Decision cell with its D# or R#. The path exists today. -->

| Path | Decision (from docs/architecture.md) |
|---|---|
| `<path>` | <D#: the decision in 3-10 words> |

## Hub files

<!-- Files that two or more modules each change when they add a feature (a registry, the settings loader, the manifest).
Name the smallest complete change, so two people rarely edit the same lines. -->

| Path | What a new feature adds here |
|---|---|
| `<path>` | <one `register_<module>(app)` line> |

## Naming and placement rules

<!-- 3-8 rules, each with what enforces it. Include where generated and vendored files live (their source, the command
that makes them, whether they are committed, "never edit by hand"), and the naming of versioned files (prompts,
migrations, settings keys). -->

| Rule | Enforced by |
|---|---|
| <e.g. No `utils/`, `common/` or `shared/` folder; a helper lives with the module that owns it.> | <review checklist> |

## Checks you run

<!-- The commands that prove the layout is right and the project runs. Result = the last line the command printed in this
session and the date; never "passes" for a command not run here. For a job, the check is one run on the sample input. -->

| Check | Command | Last result |
|---|---|---|
| Install from the lockfile | `<command>` | <YYYY-MM-DD: printed line, or "lock pending: <why>"> |
| Structure check | `<command>` | <YYYY-MM-DD: printed line> |
| Lint | `<command>` | <YYYY-MM-DD: printed line> |
| Smoke test, or one sample run for a job | `<command>` | <YYYY-MM-DD: printed line> |

## Not here yet

<!-- What the architecture needs but does not exist on disk yet, and which phase or milestone adds it. -->

| What | Added by |
|---|---|
| <e.g. `Dockerfile`, the CI workflow, the first migration> | <the foundation phase · milestone M1> |

## Changes

<!-- Every later addition, removal, rename or move of a module or home: one dated line with the old and new path, the
reason and the decision. The tables above always show only the current layout. -->

- <YYYY-MM-DD - what changed, old path → new path, why, D#>
