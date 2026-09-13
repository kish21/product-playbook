# Installation and setup

**Pick one route — and only one.** Installing the plugin *and* copy-installing makes every skill appear twice (`/vision` and `/product-playbook:vision`); if you have the plugin, never run `install.sh` on the same machine. All three run the same skills — they differ in how you *call* a skill, how you *get updates*, and how many skills you take.

| | **A. Plugin** (recommended) | **B. Copy install** | **C. Copy install `--only`** |
|---|---|---|---|
| You get | all 22 skills | all 22 skills | just the skills you name |
| Best for | new to product work — take the whole guided journey | you want everything, without the plugin system | you already have a process and want a few steps of it |
| Call a skill as | `/product-playbook:vision` | `/vision` (the bare names used throughout this README) | `/vision` |
| Updates | Automatic, once you enable it (step 3 below) | Nothing tracks the copy — re-run the installer | Same — re-run with the same `--only` |
| Lives in | Claude Code's plugin cache, per scope | `~/.claude/commands/` (or `<project>/.claude/commands/`) | same as B |
| Needs | Claude Code ≥ 2.0.70 | `bash` — on Windows, run from **Git Bash** | `bash` — on Windows, run from **Git Bash** |

### A. Plugin (recommended)

1. **Add the marketplace, then install** — inside Claude Code:
   ```
   /plugin marketplace add kish21/product-playbook
   /plugin install product-playbook@product-playbook
   ```
   Choose a scope when asked: **User** (all your projects) · **Project** (everyone who clones this repo, via `.claude/settings.json`) · **Local** (you only, this repo). From a shell instead: `claude plugin install product-playbook@product-playbook --scope user`.
2. **Activate** — if the install summary says `Run /reload-plugins to activate.`, run `/reload-plugins`.
3. **Turn on updates** — third-party marketplaces do **not** auto-update by default. `/plugin` → **Marketplaces** → `product-playbook` → **Enable auto-update**. Claude Code then checks after each session start and tells you to `/reload-plugins` when a new version lands.
   To update by hand: `/plugin marketplace update product-playbook`, then from a shell `claude plugin update product-playbook@product-playbook`.

Skills are **namespaced by the plugin**: wherever this README says `/vision`, type `/product-playbook:vision` (same for `/playbook`, `/build`, …).
Context cost, from `claude plugin details`: ~3.5k tokens always-on per session; each skill's full text loads only when you invoke it.

### B. Copy install

| Scope | Command |
|---|---|
| **Global** — one line, no clone | `curl -fsSL https://raw.githubusercontent.com/kish21/product-playbook/master/install.sh \| bash` |
| **Global** — from a clone | `git clone https://github.com/kish21/product-playbook ~/product-playbook && cd ~/product-playbook && ./install.sh` |
| **Project-level** — teammates get it on clone | `./install.sh --project /path/to/project` then commit `<project>/.claude/` |
| **Subset** — only the skills you name | `./install.sh --only build,ship` (remote: `curl -fsSL …/install.sh \| bash -s -- --only build,ship`) |

What it puts where: the 22 skills → `~/.claude/commands/` (or `<project>/.claude/commands/`), plus the companions the skills read (`PRINCIPLES.md`, `MECHANISMS.md`, `LESSONS.md`, `VISION.md`, `PRODUCT.md` template) → `~/.claude/product-playbook/` (or `<project>/.claude/product-playbook/`).

**Updating:** re-run the exact same command. It overwrites in place. There is no version check — if you want to be told about updates, use route A.

#### C. Copy install, subset (`--only`)

`--only` takes a comma-separated list of skill names — `./install.sh --only build,ship,drift-check`. It installs exactly those (flat skills and directory-form ones like `design-system`, with their `references/`) **plus the companions every skill reads** (`PRINCIPLES.md`, `MECHANISMS.md`, `LESSONS.md`, `VISION.md`, the `PRODUCT.md` template), which are never optional. It combines with `--project`. An unknown name installs nothing and prints the valid ones; `./install.sh --list` prints them on demand. Add more skills later by re-running with a new list — nothing already installed is removed.

Skills stay runnable on their own, but a few **call other skills** when they are present — `/build` → `/code-review` and `/run`, `/ship` → `/security-review`, `/learn` → `/loop` or `/schedule`, `/eval` → `/enterprise-ai-audit` (AI products, optional). Those live outside this repo; if they are not installed, the composing skill runs without that step rather than failing.

### Did it work?

Open a new Claude Code session and type `/playbook` (route A: `/product-playbook:playbook`). It should be offered as a command and greet you with the journey. Route A users can also run `/plugin list` and expect `product-playbook@product-playbook · Version: <the version on the README badge> · enabled`.

### Uninstall

- **A:** `/plugin uninstall product-playbook@product-playbook`, then `/plugin marketplace remove product-playbook`.
- **B:** delete the 22 skill files/folders from `~/.claude/commands/` (or the project's) and the `product-playbook/` companions folder beside it.

