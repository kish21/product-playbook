# Installation and setup

**Pick one route — and only one.** Installing the plugin *and* copy-installing makes every skill appear twice (`/vision` and `/product-playbook:vision`); if you have the plugin, never run `install.sh` on the same machine. All three run the same skills — they differ in how you *call* a skill, how you *get updates*, and how many skills you take.

| | **A. Plugin** (recommended) | **B. Copy install** | **C. Copy install `--only`** |
|---|---|---|---|
| You get | all 22 skills | all 22 skills | just the skills you name |
| Best for | new to product work — take the whole guided journey | you want everything, without the plugin system | you already have a process and want a few steps of it |
| Call a skill as | `/product-playbook:vision` | `/vision` (the bare names used throughout this README) | `/vision` |
| Updates | Automatic, once you enable it (step 3 below) | Nothing tracks the copy — re-run the installer | Same — re-run with the same `--only` |
| Lives in | Claude Code's plugin cache, per scope | `~/.claude/skills/` (or `<project>/.claude/skills/`) | same as B |
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
Rule files: each skill names them as `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` and `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` (and so on), and Claude Code fills in the installed plugin's folder. The agent opens the installed version's rules directly, and never searches the plugin cache, which keeps every old version.

### B. Copy install

| Scope | Command |
|---|---|
| **Global** — one line, no clone | `curl -fsSL https://raw.githubusercontent.com/kish21/product-playbook/master/install.sh \| bash` |
| **Global** — from a clone | `git clone https://github.com/kish21/product-playbook ~/product-playbook && cd ~/product-playbook && ./install.sh` |
| **Project-level** — one project only, never committed | `./install.sh --project /path/to/project` (each teammate runs it; the playbook's save never commits the install) |
| **Subset** — only the skills you name | `./install.sh --only build,ship` (remote: `curl -fsSL …/install.sh \| bash -s -- --only build,ship`) |

What it puts where: the 22 skills, each a `<name>/SKILL.md` folder → `~/.claude/skills/` (or `<project>/.claude/skills/`), plus the companions the skills read (`PRINCIPLES.md`, `MECHANISMS.md`, `MECHANISMS-ON-DEMAND.md`, `LESSONS.md`, `STATE-MODEL.md`, `CAPABILITIES.md`, `VISION.md`, the templates, the case files, `status.py`, `session_cost.py`) → `~/.claude/product-playbook/` (or `<project>/.claude/product-playbook/`). Each skill names its rule files by path. The installer rewrites those paths to this folder: a full path for a global install, and `.claude/product-playbook/…` for a project install, so the paths work wherever the project sits on disk.

**Updating:** re-run the exact same command. It overwrites in place. There is no version check — if you want to be told about updates, use route A.

#### C. Copy install, subset (`--only`)

`--only` takes a comma-separated list of skill names — `./install.sh --only build,ship,drift-check`. It installs exactly those (each skill's folder, with its `references/` and engines) **plus the companions every skill reads** (`PRINCIPLES.md`, `MECHANISMS.md`, `MECHANISMS-ON-DEMAND.md`, `LESSONS.md`, `VISION.md`, the `PRODUCT.md` template, `session_cost.py`), which are never optional. It combines with `--project`. An unknown name installs nothing and prints the valid ones; `./install.sh --list` prints them on demand. Add more skills later by re-running with a new list — nothing already installed is removed.

Skills stay runnable on their own, but a few **use your tool's own capabilities** — code review, security review, running the app, recurring checks. `CAPABILITIES.md` (installed beside the rules) names each tool's native way and the fallback; a run that uses a fallback says so in its close.

### D. Cursor and Antigravity

Both read skills as `<name>/SKILL.md` folders. The installer puts them where each tool looks and rewrites every path in them — Cursor and Antigravity never fill in Claude's plugin variable.

| Scope | Command | Lands in |
|---|---|---|
| **Project** (both tools at once) | `./install.sh --project /path/to/project --tool cursor` | `<project>/.agents/skills/` + `<project>/.agents/product-playbook/` — commit `.agents/` |
| **Global, Cursor** | `./install.sh --tool cursor` | `~/.cursor/skills/` |
| **Global, Antigravity** | `./install.sh --tool antigravity` | `~/.gemini/config/skills/` |

`--only` works the same way. On Windows run it from **Git Bash**. Call a skill as `/vision`, `/build`, …; each tool's way to review code, check security and run the app is in `CAPABILITIES.md` — and where a tool has no native way, the skill uses the fallback named there and tells you.

### Did it work?

Open a new Claude Code session and type `/playbook` (route A: `/product-playbook:playbook`). It should be offered as a command and greet you with the journey. Route A users can also run `/plugin list` and expect `product-playbook@product-playbook · Version: <the Latest version on the Releases page> · enabled`.

### Uninstall

- **A:** `/plugin uninstall product-playbook@product-playbook`, then `/plugin marketplace remove product-playbook`.
- **B:** delete the 22 skill folders from `~/.claude/skills/` (or the project's) and the `product-playbook/` companions folder beside it. An install made before the skills became folders also left them in `~/.claude/commands/` — re-running the installer removes those.
- **D:** delete the 22 skill folders and the `product-playbook/` folder from the folder the installer named (`.agents/` in a project; `~/.cursor/` or `~/.gemini/config/` globally).

