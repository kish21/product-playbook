"""status.py - the ONE writer of a project's STATUS.md: where the product stands, in one short page.

A skill never edits STATUS.md by hand. It runs a command here, and this script refuses what the state model
forbids (an illegal transition, a missing due date, a row too long to be a record). Plain Python 3.9+, no
dependencies, so every tool that can run a command can use it (CAPABILITIES.md).

    status.py show                          print STATUS.md
    status.py route                         /playbook's start: where you are, the next phase, its size, a batch
    status.py next [--phase PHASE]          the next phase, and everything a run must be told first;
                                            --phase: the phase this run is (its agent rules, a re-run)
    status.py init --product NAME [--ai yes|no]   (UI is decided later: `flag --ui`)
    status.py set PHASE STATE [--reason R] [--gate PHASE] [--due YYYY-MM-DD] [--note N]
    status.py flag [--ui yes|no] [--ai yes|no] [--agent yes|no] [--order-override REASON]
    status.py ticket ID --dod yes|no|partial --verified "CMD -> RESULT" --doc PATH [--runs N] [--review R]
    status.py release --what W --reviews R --skipped S --docs D --record C --rollback B --pr P
    status.py drift --found F --rec R
    status.py open --from PHASE --what W --clears C
    status.py bypass --from PHASE --gate PHASE --reason R   (proceed here although an earlier gate is unmet)
    status.py close N --how H
    status.py check [--product PRODUCT.md]
    status.py migrate [--product PRODUCT.md] [--write]

Global: --file PATH (default ./STATUS.md) · --today YYYY-MM-DD (tests). Exit 0 ok, 1 refused/failed, 2 usage.
The state set and legal transitions are STATE-MODEL.md §2a and §2b; tools/test_status.py holds this file to them.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

CHAIN = ["vision", "validate", "scope", "plan", "architect", "structure", "design-system", "foundation",
         "contracts", "tickets", "build", "dev-check", "deploy", "test", "eval", "ship", "learn"]
OPTIONAL = {"design-system": "runs for UI products only", "deploy": "runs when the product must be reachable",
            # owner, 2026-09-30: a required experiment was a speed bump for new users, and /vision now gives a first
            # verdict and the riskiest assumption; /validate runs only when the user asks for it
            "validate": "runs only when the user asks to test the riskiest assumption first"}
STATES = ["empty", "declined", "filled", "running", "overridden"]
# STATE-MODEL.md §2b. Anything not listed is refused.
LEGAL = {("empty", "filled"), ("empty", "running"), ("running", "filled"), ("running", "running"),
         ("running", "overridden"), ("empty", "declined"), ("empty", "overridden"), ("declined", "declined"),
         ("declined", "filled"), ("declined", "overridden"), ("filled", "filled"), ("overridden", "filled")}
# Phase 1 document phases treat a running gate as advisory; from /architect on it blocks (STATE-MODEL.md §2a).
ADVISORY_RUNNING = {"scope", "plan"}
# Verification phases record a verdict; only `pass` lets the chain move past them (STATE-MODEL.md §2a).
VERIFY = {"dev-check", "test", "eval"}
# A row is a record: the fact and a pointer. The detail lives in the file the row points to.
CAP = {"note": 160, "reason": 160, "verified": 240, "review": 160, "what": 200, "clears": 160, "how": 160,
       "found": 240, "rec": 200, "cell": 200}

SECTIONS = ["Phases", "Open items", "Tickets", "Releases", "Drift"]
COLUMNS = {
    "Phases": ["Phase", "State", "Since", "Due", "Verdict", "Note", "Rules"],
    "Open items": ["#", "Since", "From", "What", "Clears when", "Closed"],
    "Tickets": ["Ticket", "Date", "DoD met", "How verified", "Full-suite runs", "Review", "Doc"],
    "Releases": ["Date", "What shipped", "Reviews", "Skipped phases", "Docs reconciled", "Release record",
                 "Rollback", "PR"],
    "Drift": ["Date", "Drift found", "Recommendation"],
}
HEADER_KEYS = ["Updated", "Stage", "UI", "AI product", "Agent", "Order", "Next"]
# The one home of "which command, when" - `status.py how` prints it; MECHANISMS.md §Status points here.
HOW = [
    ("/playbook's first call", "route  (where you are, the next phase, its size, a legal batch, the map or not)"),
    ("Step 0, before anything else", "next --phase <this phase>  (report every override, bypass, running gate, "
                                     "inversion, rule change, open item)"),
    ("Step 0 of a phase whose `next` names it", "rules <phase>  (its sections of PRINCIPLES.md + MECHANISMS.md)"),
    ("Step 0, the skill's own reference files", "refs <phase>  (small ones whole, a big one's headings)"),
    ("reading part of a Markdown file", 'section <file> "<heading>" ...  (word for word; intro = above the '
                                        'first heading; --own "<heading>" = without its sub-sections; --headings)'),
    ("writing a Read: receipt", 'quote <file> "<a few words from the line you used>"  (prints the line to paste)'),
    ("a new product: no STATUS.md, no PRODUCT.md", 'init --product "<name>"'),
    ("an older PRODUCT.md with a Stage: header", "migrate  (dry run) -> show the user -> migrate --write on their yes"),
    ("this phase completes (Step 3b)", "set <phase> filled   (dev-check / test / eval add --verdict pass|fail)"),
    ("this phase stops at an unmet prior gate", 'set <phase> declined --reason "<what was missing>" --gate <phase>'),
    ("the user skips THIS phase on purpose", 'set <phase> overridden --reason "<the user\'s own words>" --gate <phase>'),
    ("proceeding here although an earlier gate is unmet",
     'bypass --from <phase> --gate <earlier phase> --reason "<the user\'s own words>"'),
    ("work started that finishes on a later date",
     'set <phase> running --due <YYYY-MM-DD> --reason "<what is measured> · pass: <the bar, plain words>"'),
    ("that work's result is in and recorded (no PENDING left)", 'set <phase> filled --note "<measured result vs bar>"'),
    ("a ticket is built (/build)", 'ticket <id> --dod yes|no|partial --verified "<command> -> <result>" '
                                    '--doc <feature doc> --runs <full-suite runs> --review "<round scopes>"'),
    ("a release ships (/ship)", "release --what --reviews --skipped --docs --record --rollback --pr"),
    ("drift is found (/drift-check)", 'drift --found "<drift>" --rec "<cut / re-scope+trigger / fix>"'),
    ("skipped, unverified or owed (the close)", 'open --from <phase> --what "<what>" --clears "<when settled>"'),
    ("an open item is settled", 'close <n> --how "<how>"'),
    ("the has-UI / AI / agent answer is known", "flag --ui yes|no  ·  flag --ai yes|no  ·  flag --agent yes|no"),
    ("the user leaves the chain order on purpose", 'flag --order-override "<the user\'s reason>"'),
    ("before the close", "check --product PRODUCT.md"),
    ("/structure writes its folders and starter files", "scaffold --from <bundle>  (one call; the start prints the "
                                                        "bundle format)"),
    ("/structure makes the project run", 'prove "<lock>" "<install>" "<lint>" "<smoke test>"  (prints the evidence '
                                         'lines)'),
]
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MUTATING = {"set", "flag", "ticket", "release", "drift", "open", "bypass", "close"}


class Refused(Exception):
    """A command the state model forbids. The message says what to do instead."""


class DryRun(Refused):
    """`set <phase> filled --dry-run`: every check ran, nothing was written (PRODUCT.md is put back like a refusal)."""


# ---- the file ----------------------------------------------------------------------------------------------
def esc(v: str) -> str:
    return str(v).replace("|", "\\|")


def split_row(line: str) -> list[str]:
    cells, buf, i, s = [], "", 0, line.strip()
    s = s[1:] if s.startswith("|") else s
    s = s[:-1] if s.endswith("|") and not s.endswith("\\|") else s
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            buf += "|"
            i += 2
            continue
        if s[i] == "|":
            cells.append(buf.strip())
            buf = ""
        else:
            buf += s[i]
        i += 1
    cells.append(buf.strip())
    return cells


# Team-safe (format 2): each ticket, open item, release and drift finding is one small file under status/, so two
# workers on two branches add two files and never touch the same line; STATUS.md keeps only what changes in order
# (the flags and the phase table). Measured on format 1: two branches that each recorded a ticket and an open item
# conflicted in 4 places and both numbered their item "1"; 8 runs at once in one folder kept 5 of 8 items.
FORMAT = "2"
FRAG_DIR = "status"
FRAG = {"Open items": "open", "Tickets": "tickets", "Releases": "releases", "Drift": "drift"}
DERIVED = {"build": ("Tickets", "first ticket built"), "ship": ("Releases", "first release")}
LOCK = ".status.lock"


def slug(text: str, n: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:n].strip("-") or "item"


def atomic_write(path: Path, text: str) -> None:
    """Write beside, then swap: a reader never sees half a file, and a crash never leaves one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    for i in range(50):  # Windows refuses a swap while another process has the file open for a moment
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.02 * (i + 1))
    os.replace(tmp, path)


class Lock:
    """One status.py command at a time per project folder: parallel agents wait a moment instead of each reading
    the file, adding a row and writing over the other's row."""
    def __init__(self, base: Path, wait: float | None = None) -> None:
        # STATUS_LOCK_WAIT: a test (or a slow CI box) running many status.py at once waits longer; 30 s otherwise
        self.path, self.wait = base / LOCK, wait if wait is not None else float(os.environ.get("STATUS_LOCK_WAIT", 30))

    def __enter__(self) -> "Lock":
        end = time.monotonic() + self.wait
        while True:
            try:
                os.close(os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > 120:  # a run that crashed holding it
                        self.path.unlink()
                        continue
                except FileNotFoundError:
                    continue
                if time.monotonic() > end:
                    raise Refused(f"{self.path.name} has been held for {self.wait:.0f}s by another status.py run; if "
                                  f"none is running, delete {self.path}")
                time.sleep(0.02 + random.random() * 0.05)

    def __exit__(self, *exc) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


class Status:
    def __init__(self) -> None:
        self.product = ""
        self.header = {"Updated": "", "Stage": "", "UI": "unknown", "AI product": "unknown", "Agent": "unknown",
                       "Order": "chain order", "Next": ""}
        self.rows: dict[str, list[list[str]]] = {s: [] for s in SECTIONS}
        self.archive = ""
        self.base = Path(".")
        self.today = dt.date.today().isoformat()
        self.files: dict[int, str] = {}  # id(row) -> its file under status/<kind>/
        self.derived: dict[str, tuple[list[str], list[str]]] = {}  # phase -> (row as stored, row as derived)

    @classmethod
    def load(cls, path: Path) -> "Status":
        """STATUS.md plus its one-file-per-item rows. Build and ship count as filled once a ticket or release file
        exists - derived, never written, so the first ticket on two branches does not edit the same phase row."""
        st = cls.parse(path.read_text(encoding="utf-8")) if path.is_file() else cls()
        st.base = path.resolve().parent
        folder = st.base / FRAG_DIR
        for sec, sub in FRAG.items():
            for f in sorted((folder / sub).glob("*.md")) if (folder / sub).is_dir() else []:
                row = parse_fragment(f.read_text(encoding="utf-8"), sec)
                st.rows[sec].append(row)
                st.files[id(row)] = f.name
            date_col = COLUMNS[sec].index("Date") if "Date" in COLUMNS[sec] else 1
            st.rows[sec].sort(key=lambda r: (r[date_col] if len(r) > date_col else "", st.files.get(id(r), "")))
        for phase, (sec, note) in DERIVED.items():
            r = next((x for x in st.rows["Phases"] if x[0] == phase), None)
            if r is not None and r[1] in ("empty", "declined") and st.rows[sec]:
                date_col = COLUMNS[sec].index("Date")
                stored = list(r)
                r[1:6] = ["filled", min(x[date_col] for x in st.rows[sec]), "", "", note]
                st.derived[phase] = (stored, list(r))
        return st

    def save(self, path: Path) -> list[str]:
        """Write STATUS.md and every item file whose content changed; returns the item files written."""
        folder = path.resolve().parent / FRAG_DIR
        written = []
        for sec, sub in FRAG.items():
            for r in self.rows[sec]:
                name = self.files.get(id(r)) or new_fragment_name(folder / sub, sec, r)
                self.files[id(r)] = name
                f = folder / sub / name
                text = fragment_text(sec, r)
                if not f.is_file() or f.read_text(encoding="utf-8") != text:
                    atomic_write(f, text)
                    written.append(f"{FRAG_DIR}/{sub}/{name}")
        atomic_write(path, self.render())
        return written

    # -- read ----------------------------------------------------------------------------------------------
    @classmethod
    def parse(cls, text: str) -> "Status":
        st, section = cls(), None
        for line in text.splitlines():
            if line.startswith("# STATUS"):
                st.product = line.split("—", 1)[-1].strip()
            elif line.startswith("## "):
                section = line[3:].strip()
            elif section is None and " · " in line and line.startswith(("Updated:", "Format:")):
                for part in line.split(" · "):
                    k, _, v = part.partition(":")
                    if k.strip() in st.header:
                        st.header[k.strip()] = v.strip()
            elif line.startswith("Order:"):
                st.header["Order"] = line.partition(":")[2].strip()
            elif line.startswith("Next:"):
                st.header["Next"] = line.partition(":")[2].strip()
            elif line.startswith("Archive:"):
                st.archive = line.partition(":")[2].strip()
            elif section in SECTIONS and line.startswith("|") and not line.startswith("|---"):
                cells = split_row(line)
                if cells == COLUMNS[section] or (section == "Phases" and cells == COLUMNS[section][:-1]):
                    continue
                if section == "Phases" and len(cells) == len(COLUMNS["Phases"]) - 1:
                    cells.append("")  # written before the Rules column: filled under an unrecorded version
                st.rows[section].append(cells)
        return st

    def phase(self, name: str) -> list[str]:
        for r in self.rows["Phases"]:
            if r[0] == name:
                return r
        raise Refused(f"unknown phase {name!r}; the phases are: {', '.join(CHAIN)}")

    def state(self, name: str) -> str:
        return self.phase(name)[1]

    # -- write ---------------------------------------------------------------------------------------------
    def render(self) -> str:
        """STATUS.md as committed: flags, order and the phase table only. Nothing that changes on every command
        (the date, the stage, the next phase) is stored - `next` and `show` compute it."""
        h = self.header
        out = [f"# STATUS — {self.product}", "",
               "<!-- Written by status.py. Never edit by hand: run `status.py <command>` (STATE-MODEL.md §2h). "
               "Tickets, open items, releases and drift are one file each under status/; `status.py show` prints "
               "everything, with the next phase. -->",
               "",
               f"Format: {FORMAT} · UI: {h['UI']} · AI product: {h['AI product']} · Agent: {h['Agent']}",
               "",  # a blank line between: a Markdown viewer joins consecutive lines into one paragraph
               f"Order: {h['Order']}"]
        if self.archive:
            out += ["", f"Archive: {self.archive}"]
        out += ["", "## Phases", "", "| " + " | ".join(COLUMNS["Phases"]) + " |", "|" + "---|" * len(COLUMNS["Phases"])]
        for r in self.rows["Phases"]:
            stored, derived = self.derived.get(r[0], (None, None))
            out.append("| " + " | ".join(esc(c) for c in (stored if r == derived else r)) + " |")
        return "\n".join(out) + "\n"

    def render_all(self) -> str:
        """`status.py show`: one screen with everything - STATUS.md plus every item file, and the next phase."""
        out = [self.render().rstrip("\n"), "", f"Next: {next_phase(self)['line']}"]
        for s in SECTIONS[1:]:
            out += ["", f"## {s}  (status/{FRAG[s]}/)", "", "| " + " | ".join(COLUMNS[s]) + " |",
                    "|" + "---|" * len(COLUMNS[s])]
            out += ["| " + " | ".join(esc(c) for c in r) + " |" for r in self.rows[s]]
        return "\n".join(out) + "\n"

    @classmethod
    def new(cls, product: str, today: str) -> "Status":
        st = cls()
        st.product = product
        st.header["Updated"] = today
        st.rows["Phases"] = [[p, "empty", "", "", "", "", ""] for p in CHAIN]
        return st


def fragment_text(sec: str, row: list[str]) -> str:
    kind = {"Open items": "open item", "Tickets": "ticket", "Releases": "release", "Drift": "drift finding"}[sec]
    lines = [f"<!-- One {kind}, written by status.py. Never edit by hand. -->"]
    lines += [f"{col}: {val}" for col, val in zip(COLUMNS[sec], row)]
    return "\n".join(lines) + "\n"


def parse_fragment(text: str, sec: str) -> list[str]:
    vals = {}
    for line in text.splitlines():
        k, sep, v = line.partition(": ")
        if not sep and line.endswith(":"):
            k, v = line[:-1], ""
        if k in COLUMNS[sec] and k not in vals:
            vals[k] = v.strip()
    return [vals.get(c, "") for c in COLUMNS[sec]]


def new_fragment_name(folder: Path, sec: str, row: list[str]) -> str:
    """Open items by their id; the rest by date and what they are, never colliding with a file already there."""
    stem = {"Open items": lambda r: r[0], "Tickets": lambda r: f"{r[1]}-{slug(r[0])}",
            "Releases": lambda r: f"{r[0]}-{slug(r[1])}", "Drift": lambda r: f"{r[0]}-{slug(r[1])}"}[sec](row)
    name, n = f"{stem}.md", 2
    while (folder / name).exists():
        name, n = f"{stem}-{n}.md", n + 1
    return name


def new_open_id(st: Status) -> str:
    """A short id no other worker's branch will pick (a count from 1 gave two branches the same "1")."""
    taken = {r[0] for r in st.rows["Open items"]}
    folder = st.base / FRAG_DIR / FRAG["Open items"]
    while True:
        n = "o" + "".join(random.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(3))
        if n not in taken and not (folder / f"{n}.md").exists():
            return n


# Git Bash on Windows rewrites an argument that starts with "/" into a Windows path before the script sees it:
# "/architect records both" arrives as "C:/Program Files/Git/architect records both" (a logged run hit it).
# A phase name after the Git folder is always this rewrite, never a real path a status row would hold.
MSYS_REWRITE = re.compile(r"[A-Za-z]:/(?:[^/|`\n]+/)*?Git/(?=(?:" + "|".join(map(re.escape, sorted(CHAIN, key=len,
                          reverse=True))) + r")\b)")


def playbook_version() -> str:
    """The version of the playbook this script ships with: VERSION beside it (a copy install writes it), else the
    plugin manifest one folder up (the plugin and a clone)."""
    here = Path(__file__).resolve().parent
    beside = here / "VERSION"
    if beside.is_file():
        return beside.read_text(encoding="utf-8").strip()
    manifest = here.parent / ".claude-plugin" / "plugin.json"
    if manifest.is_file():
        m = re.search(r'"version"\s*:\s*"([^"]+)"', manifest.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    return "unknown"


def playbook_line() -> str:
    """Printed first by `next`. A tool that shows two installed copies of a skill can run one copy's skill with
    the other copy's rules; this line names the copy this script belongs to (MECHANISMS.md §Status)."""
    here = Path(__file__).resolve().parent
    rules = here if (here / "PRINCIPLES.md").is_file() else here.parent  # a copy install : the plugin or a clone
    return f"Playbook {playbook_version()} · rule files in {rules.as_posix()}"


def skill_command(phase: str) -> str:
    """How the user starts a phase in this tool: a copy install lists each skill by its own name (/contracts); a
    Claude Code plugin prefixes the plugin's name (/product-playbook:contracts)."""
    here = Path(__file__).resolve().parent
    manifest = here.parent / ".claude-plugin" / "plugin.json"
    if (here / "PRINCIPLES.md").is_file() or not manifest.is_file():
        return f"/{phase}"
    m = re.search(r'"name"\s*:\s*"([^"]+)"', manifest.read_text(encoding="utf-8"))
    return f"/{m.group(1)}:{phase}" if m else f"/{phase}"


def session_costs():
    """session_cost.py, shipped beside this script on every route; None when it cannot be loaded."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import session_cost
        return session_cost
    except Exception:  # a cost line is a report, never a reason to fail a status command
        return None


def last_conversation(base: Path) -> str | None:
    """A7: the cost of the newest finished Claude Code conversation in this project, from the total Claude Code
    writes when a conversation ends - a list-price sum overstated a logged run by 70% ($20.05 against $11.86)."""
    sc = session_costs()
    if sc is None:
        return None
    try:
        found = sc.last_finished(base)
    except Exception:
        return None
    if not found:
        return None
    log, own, m = found
    phase = re.search(r"next\s+--phase\s+([\w-]+)", log.read_text(encoding="utf-8", errors="replace"))
    return (f"the last finished conversation{f' (/{phase.group(1)})' if phase else ''} cost ${own['total']:.2f} "
            f"(Claude Code's own total) · {m['calls']} calls · {m['working']} min working · {log.name}")


def agent_rules() -> str:
    """Where the agent track's rules are on this install route: AGENT.md beside a copy install, else the plugin's."""
    here = Path(__file__).resolve().parent
    return (here / "AGENT.md" if (here / "PRINCIPLES.md").is_file() else here.parent / "references" / "agent.md").as_posix()


# The lean path (owner, 2026-09-28): on Claude Code the full procedure cost 1.1-2.5x plain Claude's tokens for a
# marginal gain (a logged /dev-check: 6.4M tokens vs plain's 2.5M; /build 1.1x). Lean keeps the steps and the cheap
# code checks that caught what plain missed; every other tool keeps the full procedure. PLAYBOOK_MODE overrides.
LEAN_PHASES = {"build", "dev-check"}
LEAN_CLOSE = (
    "Mode: lean (Claude Code) - follow SKILL.md §Lean path only; PLAYBOOK_MODE=full runs the full procedure.",
    "The close: the one record command §Lean path names · ask \"Save this version of your project? (yes / no)\" and "
    "commit on a yes · then three short blocks: What just happened · What I did not check · What YOU do next.")


# The question-led phases close with one `set --section-from`, which prints the rest of the close itself: their start
# carries only the habits (the full list above is ~3 KB, re-sent on each of a run's 15-25 calls - measured on a
# logged HR /vision, next.55/56)
QUESTION_PHASES = ("vision", "scope", "plan")
QUESTION_CLOSE = (
    "This phase closes with ONE call - `status.py set <phase> filled --section-from <file> --commit \"<one line>\"`, "
    "the section in a scratch file outside the repo (never an edit tool on PRODUCT.md): it checks the record, names "
    "every problem at once, saves the project when the user's yes to the drafts included saving (leave `--commit` out "
    "on a no) - no git call of your own - and prints the rest of the close.",
    "Commands work in PowerShell and in bash: one command per call - no &&, tail, grep or export; never `cd <path> &&`. "
    "The same command fails 3 times: stop and tell the user what fails.",
    "An input gate: ask the skill's numbered questions, grouped as the skill groups them, before drafting anything "
    "that depends on the answers - never answer one for the user.",
    "The playbook's scripts are tools, not reading: run them; their output and refusals say what to do - never open "
    "their source. Plain symbols (≤ →), never LaTeX.",
    "Nothing opened beyond what `next` printed: leave the `Read:` line out - `set` writes it. Only an input file you "
    "opened yourself gets a quote: `status.py quote <file> \"<words>\"` prints the line to paste.",
)


def mode_mark(base: Path | None) -> Path | None:
    d = git_dir(base) if base is not None else None
    return d / "playbook-mode.json" if d else None


def playbook_mode(phase: str | None = None, base: Path | None = None) -> str:
    """lean or full for a phase: what the user asked for (`next --mode`, remembered in .git for this checkout), else
    PLAYBOOK_MODE, else lean on Claude Code for LEAN_PHASES and full everywhere else."""
    if phase is not None and phase.lstrip("/") not in LEAN_PHASES:
        return "full"
    f = mode_mark(base)
    if f is not None and phase and f.is_file():
        chosen = json.loads(f.read_text(encoding="utf-8")).get(phase.lstrip("/"))
        if chosen in ("lean", "full"):
            return chosen
    m = os.environ.get("PLAYBOOK_MODE", "").strip().lower()
    return m if m in ("lean", "full") else ("lean" if playbook_tool() == "claude" else "full")


def remember_mode(base: Path, phase: str, mode: str | None) -> None:
    """The user's choice (`/build <id> full`) holds for the whole run - the start and the ticket check agree. No
    choice clears an earlier one, so the default decides again."""
    f = mode_mark(base)
    if f is None:
        return
    data = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
    data.pop(phase, None)
    if mode:
        data[phase] = mode
    f.write_text(json.dumps(data), encoding="utf-8")


# Printed by `next` under the version line: the close every phase that writes runs (MECHANISMS.md §Step 3b,
# §Step 3c, §Commit the work, §Plain-language close). A run that never opens MECHANISMS.md still sees it here.
CLOSE_CHECKLIST = (
    "This phase closes with, in order (MECHANISMS.md §Step 3b):",
    "  1. status.py set <phase> filled --section-from <file> (a timeboxed experiment: set <phase> running --due"
    " <date>): write the section's body to a scratch file outside the repo - never an edit tool on PRODUCT.md (one"
    " edit of the spine put ~90 KB into a logged run's conversation); one call writes it, checks the Read quotes and"
    " prints the size line - no grep or wc of your own; refused, PRODUCT.md is put back",
    "  2. reconcile every number it introduced against #Vision; name a contradiction, never write over it",
    "  3. check it against decisions already recorded (§Step 3c): name both sides, ask which wins",
    '  4. ask "Save this version of your project? (yes / no)"; commit on a yes',
    "  5. a verdict for every exit criterion: VERIFIED only when a command you ran in this run tests THAT criterion"
    " (a count or grep of its field) and agreed; a link, a command that checks something else, or a criterion"
    " about wording or quality (plain, clear, explained) is UNVERIFIED (judged). Never 100%; no criterion"
    " VERIFIED: confidence at most 80%. A passing gate over the final files is that command: cite the gate for every"
    " test file it ran (its record holds the exact files) - never re-run a file it covered to get a number",
    "  6. four blocks, in order: What just happened · What I skipped or couldn't do · Test this yourself · "
    "What YOU do next (ending with the line `set <phase> filled` printed: open a NEW conversation and type the "
    "command it names - the record is in PRODUCT.md, STATUS.md and git; this conversation would be re-sent on "
    "every call of the next phase)",
    "Read: lines quote a line from each input file this phase opened, never one already in PRODUCT.md or a file it"
    " wrote - `set <phase> filled` refuses a copied quote; `status.py quote <file> \"<words>\" [<file> \"<words>\""
    " ...]` prints every line to paste in ONE call. Plain symbols (≤ →), never LaTeX.",
    "An `evidence:` line: <command> → <result> · <a file in THIS repo that the command checks, never a playbook "
    "script> · <date> - `set` refuses anything else. The gate counts as the command (`python gate.py \"just check\"`).",
    "The same command fails 3 times: stop. Tell the user what fails, what you tried and what you need - never a "
    "4th try of the same fix.",
    "Commands you run work in PowerShell and in bash: one command per call - no &&, tail, grep or export (use "
    "status.py section, the tool's own filters, or a file).",
    "An input gate (vision · validate · scope · plan · architect): ask the skill's numbered questions, one per "
    "message, before drafting anything that depends on the answers.",
    "Read PRODUCT.md, STRUCTURE.md, DESIGN.md and any file over 8 KB by section, never whole - `status.py section "
    "<file> --headings`, then `status.py section <file> \"<heading>\"`; the skill's small references come whole "
    "from `status.py refs <phase>`, once (it says when there are none). Every call re-sends the whole conversation, so reads and commands that do "
    "not depend on each other go in ONE turn (several tool calls in one message), never one per turn.",
    "The playbook's scripts (status.py, devserver.py, ci_local.py, audit.py ...) are tools, not reading: run "
    "them; their output and refusals say what to do. Never open their source.",
)


# Rules that change what an already-filled phase would have produced. `set <phase> filled` records the playbook
# version in the Rules column; `next` names every change newer than it, so a project that updates the playbook
# mid-way is told which phase to re-run (a logged agent test: /architect was filled before the framework table
# existed, and nothing said so). (version it shipped in, phase, applies when, what changed)
RULE_CHANGES = (
    ("1.73.0-next.15", "architect", "agent", "AGENT.md §Architect row 1: the agent framework is chosen from a 3-4 "
                                            "option table shown to the user"),
    ("1.73.0-next.15", "structure", "agent", "AGENT.md §Structure: a home for every agent part"),
    ("1.73.0-next.16", "structure", "agent", "the agent folders are created, not only named"),
    ("1.73.0-next.17", "structure", "agent", "AGENT.md §Structure names each home (guards/ is a folder) and adds "
                                            "memory, tracing, the fake model, agent tests"),
    ("1.73.0-next.18", "architect", "agent", "AGENT.md §Architect row 1: the framework search is open (no names in "
                                            "the query), finds one option beyond the examples, cites each row"),
    ("1.73.0-next.19", "structure", "all", "STRUCTURE.md needs ## Modules, ## Inside a module, ## Where decisions "
                                          "live; check_structure.py now fails on a module without tests/, a "
                                          "decision with no home, a placeholder test or a print-only task"),
    ("1.73.0-next.23", "design-system", "all", "set design-system filled refuses an audit that checked 0 things "
                                               "without a recorded override, and a token stylesheet no app file "
                                               "imports without an open item for /foundation"),
    ("1.73.0-next.27", "tickets", "all", "set tickets filled checks every ticket names exact files, a STRUCTURE.md "
                                        "lane, a security line in its DoD, dependencies that exist, consumed names "
                                        "the code or another ticket has, every milestone ticketed or explained, "
                                        "and TICKETS.md's lane graph"),
    ("1.73.0-next.26", "contracts", "all", "a money field typed Any, or converted from a float (int(x * 100), "
                                          "float(x)), is refused like a float"),
    ("1.73.0-next.26", "foundation", "all", "the project runs in its own environment (.venv / a manager lock) on "
                                           "the Python requires-python pins (Node: engines), and every task-runner "
                                           "line that needs the packages runs through it (uv run ..., never a bare "
                                           "python -m pytest)"),
    ("1.73.0-next.24", "foundation", "all", "evidence lines must cite files and tests that exist; the hooks "
                                           "installed, a lockfile per manifest, no fallback for a CHANGE_ME "
                                           "variable, tests on #Architecture's database engine, CI run or an "
                                           "open item; the seed refuses by database host and stops at identity"),
    ("1.73.0-next.25", "design-system", "ui", "every type-scale step is a token (--text-xs ... --text-display) "
                                              "declared in the token stylesheet; components never use a raw size"),
    ("1.73.0-next.25", "contracts", "all", "set contracts filled checks the record's paths exist, a migration ran, "
                                          "no app code builds the schema, no float money, the tenant key on every "
                                          "table, an exported contract or N/A; Agent: yes adds AGENT.md §Contracts"),
    ("1.73.0-next.25", "structure", "all", "the agent-instructions file (CLAUDE.md / AGENTS.md) reads PRODUCT.md, "
                                          "STRUCTURE.md and DESIGN.md by section, never whole"),
    ("1.73.0-next.28", "foundation", "all", "the databases are named for the project (<project>_dev, "
                                           "<project>_test), never a generic app_test another project on the same "
                                           "server also uses, and the test guard refuses a database stamped with a "
                                           "migration this repo does not have"),
)


# A5: the third choice beside re-run and keep. A logged agent test re-ran /architect 3 times and /structure 4 times
# as whole phases, each for one changed decision.
UPDATE_ONE = ("update one decision: edit that entry (and its ADR or companion) with a dated `superseded <date>: <why>` "
              "line, then status.py set {p} filled --note \"updated: <which decision>\" (runs only this phase's check)")


# Rule Q: provenance has exactly two values. "default taken, <anything else>" claims a choice (a logged run wrote
# "default taken, confirmed by user" 35 times); a bare "default taken" inside a superseded note is a quotation.
THIRD_PROVENANCE = re.compile(r"default taken, (?!not user-chosen)[a-z][a-z -]{2,30}[a-z]")


# Rule S: the model row names the model and its release date from a search. A logged run kept 2024 models through
# two re-runs because the rule was a sentence; these two tests make it a refusal. A line recording a superseded
# choice may quote an old id.
MODEL_STAMP = re.compile(r"\b([a-z][a-z0-9.]*(?:-[a-z0-9.]+)*-(20\d{2})(\d{2})(\d{2}))\b")
RELEASED = re.compile(r"released (20\d{2}-\d{2}-\d{2})")


def model_age_problems(body: str, today: str) -> list[str]:
    out, year_ago = [], f"{int(today[:4]) - 1}{today[4:]}"
    live = "\n".join(l for l in body.splitlines() if "superseded" not in l.lower())
    for full, y, m, d in sorted(set(MODEL_STAMP.findall(live))):
        if f"{y}-{m}-{d}" < year_ago:
            out.append(f"model {full!r} is stamped {y}-{m}-{d}, over a year old: search for the current model and "
                       f"record it as 'released <date>' (rule S)")
    if not RELEASED.search(live):
        out.append("no model release date: the model row says 'released YYYY-MM-DD' from a search this run (rule S)")
    return out


# R1 + R2: a phase's own checks, run by this script - never left to the model. A logged review found a model can
# write "passes" without running a check; `set <phase> filled` runs it, and `next` re-runs it for every filled phase.
# The check installed with this script is the one run, so a project's older copy cannot hide a newer rule.
# ONE skip list for every walk of the project (a second, three-name assignment further down won, and every
# walk entered .git, .venv and the installed playbook - its own check_structure.py was taken as the project's).
SKIP_DIRS = {".git", ".agents", ".claude", ".cursor", ".codex", ".gemini", "node_modules", ".venv", "venv",
             "__pycache__", "dist", "build", "site-packages", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
             ".nox", ".next"}
# The playbook's own install inside a project (install.sh --project; each tool's agents folder). The save never
# stages it: a logged Codex /structure replaced .gitignore and its save committed 88 install files (2026-10-03).
INSTALL_PATHS = (".agents", ".claude/skills", ".claude/product-playbook", ".claude/agents", ".cursor/agents", ".codex",
                 ".gemini")


def install_root(rel: str) -> str | None:
    """The INSTALL_PATHS entry a project-relative path sits in, or None."""
    rel = rel.strip().strip('"').replace("\\", "/")
    return next((p for p in INSTALL_PATHS if rel == p or rel.startswith(p + "/")), None)


def tool_file(*parts: str) -> Path | None:
    """A file shipped with the playbook: beside this script on a copy install, else in the plugin or clone."""
    here = Path(__file__).resolve().parent
    for base in (here, here.parent, here.parent / "skills", here.parent / "commands"):
        f = base.joinpath(*parts)
        if f.is_file():
            return f
    return None


# The checkers status.py runs are fingerprinted when the playbook is built; a checker that no longer matches was
# edited after install. A logged Gemini run added `status` and `open` to the installed check_structure.py's IGNORE list
# to get past a failure, and the gate went quiet: a check the run can edit is not a check.
ENGINES = ("check_structure.py", "audit.py")


def file_hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()  # git may check files out with CRLF


def code_hash(p: Path) -> str:
    """A .py file's hash as parsed code: a project's formatter (ruff format, black) rewrites a committed copy on its
    first commit, and a byte hash then names the copy as different forever. Docstrings are compared dedented."""
    import ast
    try:
        tree = ast.parse(p.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, ValueError):
        return file_hash(p)
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) \
                and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            body[0].value.value = "\n".join(x.strip() for x in body[0].value.value.strip().splitlines())
    return hashlib.sha256(ast.dump(tree).encode()).hexdigest()


def engine_hashes() -> dict[str, str]:
    here = Path(__file__).resolve().parent
    f = next((x for x in (here / "ENGINE.sha256", here / "engine.sha256") if x.is_file()), None)
    if f is None:
        return {}
    return {name: sha for sha, name in (l.split() for l in f.read_text(encoding="utf-8").splitlines() if l.strip())}


def engine_changed(p: Path) -> str | None:
    want = engine_hashes().get(p.name)
    if want and file_hash(p) != want:
        return (f"the playbook's own check {p.as_posix()} was changed after install - it no longer matches the "
                f"playbook it came with. Restore it (reinstall the playbook); never edit a playbook check to make it "
                f"pass: fix what it reports, or record the user's override")
    return None


def engine_hash_text() -> str:
    """`status.py engine`: the fingerprint list, written to tools/engine.sha256 when the playbook is built."""
    return "".join(f"{file_hash(tool_file(*parts))}  {parts[-1]}\n" for parts in
                   (("templates", "check_structure.py"), ("frontend-audit", "audit.py")) if tool_file(*parts))


# Step 0 in fewer calls: a skill's own reference files, whole when small. A logged /contracts run read two 3-5 KB
# step files one section per call - each call re-sent ~180k tokens of conversation to save ~1k.
SMALL_REF = 8 * 1024


def phase_refs_text(phase: str) -> str | None:
    here = Path(__file__).resolve().parent
    folder = next((d for d in (here.parent / "commands" / phase / "references", here.parent / "skills" / phase /
                               "references") if d.is_dir()), None)
    if folder is None:
        return None
    parts = [f"The reference files of /{phase}, word for word (small ones whole; a big one by its headings - read "
             f"it by section: status.py section <path> \"<heading>\"):"]
    for f in sorted(folder.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        if len(text.encode("utf-8")) <= SMALL_REF:
            parts.append(f"===== {f.as_posix()} =====\n{text.rstrip()}")
        else:
            heads = [l for l in text.splitlines() if re.match(r"#{1,3} ", l)]
            parts.append(f"===== {f.as_posix()} ({len(text.encode('utf-8')) // 1024} KB: headings only) =====\n"
                         + "\n".join(heads))
    return "\n\n".join(parts)


def find_in_project(base: Path, name: str) -> Path | None:
    for dirpath, dirnames, files in os.walk(base):
        dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS]
        if name in files:
            return Path(dirpath) / name
    return None


def run_check(cmd: list[str], cwd: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, *cmd], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    out = (r.stdout + r.stderr).strip().splitlines()
    fails = [l.strip() for l in out if "[FAIL]" in l]
    return r.returncode, "; ".join(fails[:4]) or (out[-1] if out else f"exit {r.returncode}")


def phase_check(phase: str, base: Path) -> str | None:
    """None when the phase's own check passes (or it has none); else what failed, in one line."""
    if phase == "structure":
        if not (base / "STRUCTURE.md").is_file():
            return "no STRUCTURE.md - /structure writes it"
        if find_in_project(base, "check_structure.py") is None:
            return ("no committed check_structure.py in the project - copy templates/check_structure.py into it "
                    "(the commit hook and CI run that copy)")
        engine = tool_file("templates", "check_structure.py")
        if engine is None:
            return None
        if engine_changed(engine):
            return engine_changed(engine)
        code, out = run_check([str(engine), "STRUCTURE.md", "."], base)
        return None if code == 0 else f"check_structure.py: {out}"
    if phase == "design-system":
        if not (base / "DESIGN.md").is_file():
            return "no DESIGN.md - /design-system writes it after the sample page is approved"
        engine = tool_file("frontend-audit", "audit.py")
        if engine is None:
            return None
        if engine_changed(engine):
            return engine_changed(engine)
        r = subprocess.run([sys.executable, str(engine), "DESIGN.md"], cwd=base, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0:
            fails = [l.strip() for l in (r.stdout + r.stderr).splitlines() if "[FAIL]" in l]
            return f"frontend-audit (audit.py DESIGN.md): {'; '.join(fails[:4]) or f'exit {r.returncode}'}"
        return design_gaps(base, r.stdout)
    if phase == "foundation":
        gaps = foundation_gaps(base)
        return "; ".join(gaps) if gaps else None
    if phase == "contracts":
        gaps = contracts_gaps(base)
        return "; ".join(gaps) if gaps else None
    if phase == "tickets":
        gaps = tickets_gaps(base)
        return "; ".join(gaps) if gaps else None
    return None


# /foundation's claims that a file tree can prove, checked the same way for every model (a logged Gemini run was
# marked done with no hooks installed, no lockfile, fallback secrets in the loader and SQLite under a Postgres design).
HOOK_CONFIGS = (".pre-commit-config.yaml", "lefthook.yml", ".lefthook.yml", "lefthook.yaml", ".husky")
LOCKS = {"pyproject.toml": ("uv.lock", "poetry.lock", "pdm.lock", "requirements.lock", "requirements.txt"),
         "package.json": ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "bun.lock"),
         "Cargo.toml": ("Cargo.lock",), "go.mod": ("go.sum",), "Gemfile": ("Gemfile.lock",),
         "composer.json": ("composer.lock",)}
SOURCE = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}
CI_FILES = (".github/workflows", ".gitlab-ci.yml", ".circleci", "azure-pipelines.yml", "bitbucket-pipelines.yml")
SERVER_DBS = re.compile(r"(?i)\b(postgres(?:ql)?|mysql|mariadb|sql server|mssql|oracle|cockroach(?:db)?)\b")


def project_files(base: Path, suffixes: set[str] | None = None) -> list[Path]:
    out = []
    for dirpath, dirnames, files in os.walk(base):
        dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS]
        out += [Path(dirpath) / f for f in files if suffixes is None or Path(f).suffix.lower() in suffixes]
    return out


def git(base: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=base, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip() if r.returncode == 0 else ""


# The tree /foundation's checks read. Not project_files(): the module rebinds SKIP_DIRS to three names further down,
# so that walk enters .venv, .git and the installed playbook - slow on every later `next`, and the playbook's own
# package.json / test files read as the project's (a logged `next` crashed on a too-long .venv path).
FOUNDATION_SKIP = {".git", ".agents", ".claude", ".cursor", ".codex", ".gemini", "node_modules", ".venv", "venv",
                   "__pycache__", "dist", "build", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".next"}


def foundation_files(base: Path, suffixes: set[str] | None = None) -> list[Path]:
    out = []
    for dirpath, dirnames, files in os.walk(base):
        dirnames[:] = [x for x in dirnames if x not in FOUNDATION_SKIP]
        out += [Path(dirpath) / f for f in files if suffixes is None or Path(f).suffix.lower() in suffixes]
    return out


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def foundation_gaps(base: Path) -> list[str]:
    gaps = []
    # E6: a hook runner that is configured but not installed runs on no commit
    if any((base / c).exists() for c in HOOK_CONFIGS):
        hooks = git(base, "rev-parse", "--git-path", "hooks")  # honours core.hooksPath and worktrees (.git is a file)
        hook_dir = (base / hooks) if hooks else base / ".git" / "hooks"
        if (base / ".git").exists() and not (hook_dir / "pre-commit").is_file():
            gaps.append(f"the commit hooks are configured but not installed ({hooks or '.git/hooks'}/"
                        f"pre-commit is missing): install them (e.g. `pre-commit install`) and commit through them")
    else:
        gaps.append(f"no commit-hook runner is configured (none of {', '.join(HOOK_CONFIGS)}): wire the one "
                    f"#Architecture recorded")
    # E10: a manifest without its lockfile installs different versions on every machine
    for f in foundation_files(base):
        if f.name in LOCKS and not any((d / lock).is_file() for lock in LOCKS[f.name] for d in (f.parent, base)):
            gaps.append(f"{f.relative_to(base).as_posix()} has no lockfile ({' / '.join(LOCKS[f.name])}): pin and "
                        f"install so every machine and CI get the same versions")
    # E3: a secret with a fallback default boots without its real value, in every environment
    env_example = base / ".env.example"
    keys = re.findall(r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*\S*CHANGE_ME", env_example.read_text(encoding="utf-8"),
                      re.M) if env_example.is_file() else []
    if keys:
        alt = "|".join(map(re.escape, keys))
        fallback = re.compile(rf"(?:getenv|environ\.get|env\.get)\(\s*[\"']({alt})[\"']\s*,\s*[\"'][^\"']+[\"']"
                              rf"|process\.env\.({alt})\s*(?:\|\||\?\?)\s*[\"'`][^\"'`]+")
        for f in foundation_files(base, SOURCE):
            rel = f.relative_to(base).as_posix()
            if "/tests/" in f"/{rel}" or f.name.startswith("test_") or ".test." in f.name or ".spec." in f.name:
                continue
            hit = sorted({a or b for a, b in fallback.findall(read_text(f))})
            if hit:
                gaps.append(f"{rel} gives {', '.join(hit)} a fallback value although .env.example marks "
                            f"{'it' if len(hit) == 1 else 'them'} CHANGE_ME: a missing value must stop the boot, "
                            f"never be replaced (PRINCIPLES.md §Production safeguards)")
    # E4: the test datastore is the engine #Architecture chose, not a lighter stand-in
    mismatch = test_engine_mismatch(base)
    if mismatch and not mismatch[2]:
        gaps.append(f"#Architecture chose {mismatch[0]} but the tests use SQLite ({', '.join(mismatch[1])}):"
                    f" test on the same engine (references/test-datastore.md), or record the user's override in "
                    f"#Foundation")
    # E5: CI proven on a remote, or run locally and still owed (the owner's rule, 2026-09-26)
    if not any((base / c).exists() for c in CI_FILES):
        gaps.append("no CI workflow: write the one that mirrors the prod boot")
    elif not git(base, "remote"):
        status = base / "STATUS.md"
        rows = Status.load(status).rows["Open items"] if status.is_file() else []
        if not any(re.search(r"\bCI\b", r[3]) and not r[5] for r in rows):
            gaps.append("no git remote, so CI has never run: run its steps locally (ci_local.py) and record `status.py "
                        "open --from foundation --what \"CI has not run on a remote\" --clears \"CI is green on the "
                        "first push\"`")
    return gaps + env_gaps(base)


# E13: the project runs in its own environment, on the version it pins. A logged Gemini run had no .venv and a
# Makefile calling bare `python -m pytest`: the tests ran on whatever Python Windows found first, with packages in
# the machine's shared install - green there, a different result on a teammate's machine or a runner.
NEEDS_PACKAGES = re.compile(r"(?<![\w./-])(?:python3?\s+-m\s+)?(pytest|uvicorn|alembic|ruff|mypy|gunicorn|celery|"
                            r"procrastinate|django-admin)\b|(?<![\w./-])python3?\s+manage\.py\b")
THROUGH_ENV = re.compile(r"\b(?:uv|poetry|pdm|hatch|pipenv|rye)\s+run\b|\.venv[/\\]|\$\(?\{?\w*(?:PY|PYTHON|VENV)\w*")
ENV_MANAGER_LOCKS = ("uv.lock", "poetry.lock", "pdm.lock", "Pipfile.lock")
VERSION_SPEC = re.compile(r"(>=|<=|==|~=|!=|>|<|\^|~)?v?(\d+(?:\.\d+)*)((?:\.[x*])?)")


def version_ok(have: tuple, spec: str) -> bool:
    """`have` meets a pin: Python '>=3.12,<3.14', '~=3.12', '==3.13.*'; Node '>=20', '^20.1', '~20.1', '20.x', '20',
    and 'a || b'. A clause this reader does not know is never a refusal."""
    if "||" in spec:
        return any(version_ok(have, alt) for alt in spec.split("||"))
    pad = lambda v: tuple(v) + (0,) * (3 - len(v))  # noqa: E731
    for clause in re.split(r"[,\s]+", spec.strip()):
        m = VERSION_SPEC.fullmatch(clause)
        if not m:
            continue
        op, want, star = m.group(1), tuple(map(int, m.group(2).split("."))), m.group(3)
        if star or not op or (op == "==" and len(want) < 3):  # 20.x · 20 · ==3.13.* · ==3.13: a prefix
            if have[:len(want)] != want:
                return False
            continue
        if op in ("^", "~", "~="):  # at least `want`, and the leading part fixed
            # ^20.1 fixes the major; ~=3.12 (Python) all but the last part; ~20.1 (npm) up to the minor
            keep = {"^": 1, "~=": max(len(want) - 1, 1), "~": min(len(want), 2)}[op]
            if pad(have) < pad(want) or have[:keep] != want[:keep]:
                return False
            continue
        h, w = pad(have), pad(want)
        if not {">=": h >= w, "<=": h <= w, "==": h == w, "!=": h != w, ">": h > w, "<": h < w}[op]:
            return False
    return True


def env_python(folder: Path) -> tuple | None:
    """The Python version of the project's .venv, from its pyvenv.cfg (no interpreter is started)."""
    cfg = folder / ".venv" / "pyvenv.cfg"
    if not cfg.is_file():
        return None
    m = re.search(r"^version(?:_info)?\s*=\s*(\d+(?:\.\d+)*)", cfg.read_text(encoding="utf-8", errors="replace"), re.M)
    return tuple(map(int, m.group(1).split("."))) if m else None


def env_gaps(base: Path) -> list[str]:
    gaps = []
    for py in (f for f in foundation_files(base) if f.name == "pyproject.toml"):
        d, rel = py.parent, py.relative_to(base).as_posix()
        pin = re.search(r"^requires-python\s*=\s*[\"']([^\"']+)[\"']", py.read_text(encoding="utf-8", errors="replace"),
                        re.M)
        have = env_python(d) or env_python(base)
        if have is None and not any((x / lock).is_file() for lock in ENV_MANAGER_LOCKS for x in (d, base)):
            gaps.append(f"{rel} has no project environment (no .venv, no {' / '.join(ENV_MANAGER_LOCKS)}): create it "
                        f"with the manager #Architecture recorded (e.g. `uv sync`), so no command uses the machine's "
                        f"shared Python")
        elif have and pin and not version_ok(have, pin.group(1)):
            gaps.append(f"the project environment runs Python {'.'.join(map(str, have))}, but {rel} pins "
                        f"requires-python {pin.group(1)}: recreate it on a pinned version (e.g. `uv python pin`, "
                        f"then `uv sync`)")
    for name in ("Makefile", "justfile", "Justfile"):
        f = base / name
        if not f.is_file():
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            m = NEEDS_PACKAGES.search(line)
            if line[:1].isspace() and m and not THROUGH_ENV.search(line[:m.start()]):
                gaps.append(f"{name}:{n} runs `{line.strip()[:60]}` on whatever Python the machine finds first: run it "
                            f"through the project environment (`uv run ...`, `poetry run ...`, or .venv's python)")
    pkg = base / "package.json"
    if pkg.is_file():
        try:
            want = (json.loads(pkg.read_text(encoding="utf-8")).get("engines") or {}).get("node")
        except ValueError:
            want = None
        node = shutil.which("node")
        if want and node:
            out = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip().lstrip("v")
            have = tuple(int(x) for x in re.findall(r"\d+", out)[:3])
            if have and not version_ok(have, want):
                gaps.append(f"node here is {out}, but package.json's engines.node is {want}: install the pinned "
                            f"version (e.g. with .nvmrc / fnm / volta) so every machine runs the same one")
    return gaps


# /contracts' claims that a file tree can prove, the same way for every model: the record's pointers resolve, the
# schema is built by migrations, money is never a float, every table carries the tenant key, the contract is exported.
SQL_DBS = re.compile(r"(?i)\b(postgres(?:ql)?|mysql|mariadb|sql server|mssql|oracle|cockroach(?:db)?|sqlite)\b")
MIGRATION_DIRS = {"migrations", "versions", "migrate", "drizzle"}
NOT_MIGRATION = {"env.py", "__init__.py", "readme.md"}
MIGRATION_EXT = {".py", ".sql", ".ts", ".js", ".rb"}
SCHEMA_AT_BOOT = re.compile(r"\.create_all\(|synchronize\s*:\s*true|\bdb push\b")
MONEY_WORDS = {"amount", "price", "cost", "balance", "refund", "fee", "fees", "money", "subtotal", "payout"}
# at its own close only (a project filled under older rules is never blocked later): the pay words of a payroll product
# (`net_pay: float` passed) and a currency in the name (`spend_eur: 0.10`); a rate or a share is not money
PAY_WORDS = {"pay", "salary", "salaries", "wage", "wages", "gross", "tax", "taxes", "withholding", "bonus", "deduction",
             "deductions", "allowance", "payment", "spend", "eur", "euro", "euros", "usd", "gbp", "dollar", "dollars", "cents"}
NOT_MONEY = {"rate", "rates", "ratio", "percent", "pct", "percentage", "factor", "fraction", "share", "weight", "score"}
# the project's own files only: a library in the project environment is never its code (`amount: float` in a vendored
# SDK under .venv refused /contracts while SKIP_DIRS was re-bound to three names)
CONTRACT_SKIP = SKIP_DIRS
# a float VALUE handed to a money name - `spend_cap=state.get("spend_cap", 0.10)` (a logged run's graph.py, after its
# first refusal), `spend_eur: 0.10` in config - checked in code, YAML/TOML and config JSON
FLOAT_VALUE = re.compile(r"""["']?\b([A-Za-z_]\w*)["']?\s*(?:=(?!=)|:(?!:)|,)\s*-?\d+\.\d+(?![\w.])""")
VALUE_FILES = {".py", ".yaml", ".yml", ".toml", ".json"}
CONTRACTS_DOC = "docs/contracts.md"
FLOAT_DECL = {  # (a name, a float type) per file kind
    ".py": re.compile(r"[\"'](\w+)[\"']\s*,\s*(?:sa\.|sqlalchemy\.|postgresql\.)?(?:Float|REAL|DOUBLE(?:_PRECISION)?)\b"
                      r"|\b(\w+)\s*:\s*(?:Mapped\[\s*)?(?:Optional\[\s*)?float\b"
                      r"|\b(\w+)\s*(?::[^=\n]*)?=\s*(?:sa\.)?(?:Column|mapped_column)\(\s*(?:sa\.)?(?:Float|Double)\b"
                      # the back door a logged run left after its first refusal: `refund_cap: Any` then
                      # `int(refund_cap * 100)` - still a float at the boundary, only no longer typed as one
                      r"|\b(\w+)\s*:\s*(?:Optional\[\s*)?Any\b|\bint\(\s*(\w+)\s*\*\s*100\b|\bfloat\(\s*(\w+)\s*\)"),
    ".sql": re.compile(r"(?i)^\s*[\"`]?(\w+)[\"`]?\s+(?:float\d*|real|double(?: precision)?)\b", re.M),
    ".prisma": re.compile(r"^\s*(\w+)\s+Float\b", re.M),
    ".ts": re.compile(r"\b(\w+)\s*:\s*(?:real|doublePrecision|float)\("),
}
FLOAT_DECL[".js"] = FLOAT_DECL[".ts"]
TABLE_START = re.compile(r"""op\.create_table\(\s*["'](\w+)["']|CREATE TABLE (?:IF NOT EXISTS )?["`]?(\w+)"""
                         r"""|^model (\w+) \{|(?-i:\b(?:pg|sqlite|mysql)Table)\(\s*["'](\w+)["']""", re.I | re.M)
SPEC_FILE = re.compile(r"(?i)(openapi[\w.-]*\.(?:json|ya?ml)|asyncapi[\w.-]*\.(?:json|ya?ml)|[\w.-]+\.schema\.json"
                       r"|[\w.-]+\.graphql|[\w.-]+\.proto)\b")
POINTER = re.compile(r"`((?:[\w.-]+/)+[\w.-]+)`")
AGENT_CONTRACT_ROWS = ("tool schemas", "action policy", "model output", "trace", "hand-off", "eval case")


def field(body: str, label: str) -> str:
    """The text of one `- **<label>...:**` field of a section, up to the next field."""
    m = re.search(rf"^- \*\*{re.escape(label)}[^\n]*?:\*\*(.*?)(?=^- \*\*|\Z)", body, re.M | re.S)
    return m.group(1) if m else ""


def is_test(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return ("/tests/" in f"/{rel}" or name.startswith("test_") or name == "conftest.py" or ".test." in name
            or ".spec." in name)


def is_money(name: str, pay: bool = False) -> bool:
    """amount_cents, refundAmount, unit_price: a word of the name is a money word (feedback and total_tokens are not);
    with `pay`, net_pay and spend_eur too - and never withholding_tax_rate (a rate is not money)."""
    words = {w.lower() for w in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", name)}
    return bool(words & (MONEY_WORDS | PAY_WORDS if pay else MONEY_WORDS)) and not (pay and words & NOT_MONEY)


def contract_files(base: Path) -> list[Path]:
    out = []
    for dirpath, dirnames, files in os.walk(base):
        dirnames[:] = [x for x in dirnames if x not in CONTRACT_SKIP]  # site-packages: a venv of any name
        out += [Path(dirpath) / f for f in files]
    return out


def tenant_keys(field_text: str, close: bool) -> list[str]:
    """The tenant key(s) the PII · tenant field names. The field also holds the idempotency keys (`run_id`): at the
    close, a sentence that says tenant/owner decides, so a table keyed only by `run_id` is not read as tenant-keyed."""
    keys = lambda t: [k for k in re.findall(r"`(\w+)`", t) if k.endswith(("_id", "_key", "_domain"))]  # noqa: E731
    if close:
        said = [s for s in re.split(r"(?<=[.;])\s+|\n", field_text)
                if re.search(r"(?i)tenant|owner", s) and not re.search(r"(?i)\bno tenant", s)]
        if keys(" ".join(said)):
            return keys(" ".join(said))
    return keys(field_text)


def contracts_doc_gaps(base: Path, body: str) -> list[str]:
    """docs/contracts.md, the reader's part first: an overview with ONE diagram, then the PII table and the owner's
    answers (a contract that lists only workings produces exactly that - 0 of 4 logged architecture docs had a
    diagram until the contract asked for it first)."""
    doc = base / CONTRACTS_DOC
    if not doc.is_file():
        return [] if CONTRACTS_DOC in body else [f"no {CONTRACTS_DOC}: write it (the shape `next` printed)"]
    text = doc.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    h2 = [(t, "\n".join(lines[a:b])) for lvl, t, a, b in md_sections(text) if lvl == 2]
    gaps = []
    if not h2 or not h2[0][0].lower().startswith("overview") or "```mermaid" not in h2[0][1]:
        gaps.append(f"{CONTRACTS_DOC} does not start with `## Overview` holding 3-5 plain sentences and ONE ```mermaid "
                    f"erDiagram (the tables and the tenant key) - the reader's part first, the workings after it")
    if not any("pii" in t.lower() and "|" in s for t, s in h2):
        gaps.append(f"{CONTRACTS_DOC} has no `## PII` table (field · why kept · how long · deletion path)")
    if not any(re.search(r"(?i)owner'?s?['’]?s? answers", t) for t, _ in h2):
        gaps.append(f"{CONTRACTS_DOC} has no `## Owner's answers` (round 1's answers, word for word)")
    return gaps


RATE_WORDS = {"rate", "rates", "percent", "pct", "percentage"}


def contracts_warnings(base: Path) -> list[str]:
    """A rate or percentage kept as a float (`withholding_rate: float`, `vat_rate: 0.21`): a WARNING at the close - the
    recommended form is integer basis points (1250 = 12.50%), exact like money; never a refusal (owner)."""
    found: dict[str, set[str]] = {}
    for p in contract_files(base):
        rel, suffix = p.relative_to(base).as_posix(), p.suffix.lower()
        decl = FLOAT_DECL.get(suffix)
        value = suffix in VALUE_FILES and (suffix in (".py", ".toml") or re.search(
            r"(?i)(^|/)(config|settings)/|config|settings|policy", rel))
        if is_test(rel) or not (decl or value):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        names = {n for m in decl.finditer(text) for n in m.groups() if n} if decl else set()
        if value:
            names |= {m.group(1) for line in text.splitlines()
                      for m in FLOAT_VALUE.finditer(line if suffix == ".json" else re.sub(r"(^|\s)#.*$", "", line))}
        rates = {n for n in names if {w.lower() for w in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", n)} & RATE_WORDS}
        if rates:
            found[rel] = rates
    return [f"{rel} keeps a rate as a float ({', '.join(sorted(n)[:4])}) - integer basis points (1250 = 12.50%) are "
            f"exact; a float rate times money drifts" for rel, n in sorted(found.items())]


def contracts_gaps(base: Path, close: bool = False, doc_pending: bool = False) -> list[str]:
    """What a file tree proves about /contracts. `close`: also the checks added for its own close (pay words, a float
    value, the tenant sentence, docs/contracts.md's shape) - never in phase_check, so a project filled under older
    rules is not blocked by a later phase. `doc_pending`: a --dry-run before docs/contracts.md is written (P46: the
    long document is the last write, after round 2's yes) - its checks wait for the save."""
    gaps = []
    product = base / "PRODUCT.md"
    secs = product_sections(product.read_text(encoding="utf-8")) if product.is_file() else {}
    body, arch = secs.get("Contracts", ""), secs.get("Architecture", "")
    # C1: the record points at code; a pointer to nothing is how a later phase invents what the file would say
    files = [(p, p.relative_to(base).as_posix()) for p in contract_files(base)]
    live = "\n".join(l for l in body.splitlines() if "evidence:" not in l and "superseded" not in l.lower())
    for path in sorted(set(POINTER.findall(live))):
        if re.search(r"[<>*{}]", path) or (base / path).exists() or playbook_file(path) is not None                 or (doc_pending and path == CONTRACTS_DOC):
            continue
        if not any(r.endswith("/" + path) for _, r in files):  # a path inside a sub-project (backend/...) counts
            gaps.append(f"#Contracts points at {path}, which does not exist - write it, or point at the file that does")
    # C2: migrations only - a schema app code builds at boot has no history and cannot be checked against the models
    migrations = [(p, r) for p, r in files if p.name == "migration.sql" or (
        p.parent.name.lower() in MIGRATION_DIRS and p.name.lower() not in NOT_MIGRATION
        and p.suffix.lower() in MIGRATION_EXT)]
    if SQL_DBS.search(arch) and not migrations:
        gaps.append("no migration file (in a migrations/ or versions/ folder): the schema is built by migrations on "
                    "the approach #Architecture recorded (contract-steps.md §2.)")
    for p, rel in files:
        if p.suffix.lower() in SOURCE and not is_test(rel) and (p, rel) not in migrations:
            m = SCHEMA_AT_BOOT.search(p.read_text(encoding="utf-8", errors="replace"))
            if m:
                gaps.append(f"{rel} builds the schema itself ({m.group(0).strip()}): only migrations change it, "
                            f"or the models and the database drift apart unseen")
    # C3: an evidence line ran the migration - the section says it applies, the line shows it did
    if migrations and not re.search(r"(?i)evidence:[^\n]*(?:migrat|upgrade)", body):
        gaps.append("no evidence line in #Contracts ran a migration: run it from empty on the test datastore and "
                    "record the command (verify.md §Migration applies)")
    # C4: money is never a float - 6.75 has no exact binary form, and a sum over many rows drifts
    for p, rel in files:
        suffix = p.suffix.lower()
        decl = FLOAT_DECL.get(suffix)
        # a float value: code anywhere, data files only as config (a fixture or an eval case is input, not a contract)
        value = close and suffix in VALUE_FILES and (suffix in (".py", ".toml") or re.search(
            r"(?i)(^|/)(config|settings)/|config|settings|policy", rel))
        if (decl or value) and not is_test(rel):
            text = p.read_text(encoding="utf-8", errors="replace")
            found = {n for m in decl.finditer(text) for n in m.groups() if n} if decl else set()
            if value:
                found |= {m.group(1) for line in text.splitlines()
                          for m in FLOAT_VALUE.finditer(line if suffix == ".json" else re.sub(r"(^|\s)#.*$", "", line))}
            names = sorted({n for n in found if is_money(n, close)
                            and not re.search(rf"(?im)^.*\b{n}\b.*\bfloat\b", body)})  # named there, with why
            if names:
                gaps.append(f"{rel} keeps money as a float, typed Any or converted from one"
                            f"{', or given a float value' if value else ''} ({', '.join(names[:4])}): "
                            f"store integer minor units or "
                            f"a fixed decimal, with the currency, or name the field on a line of #Contracts with why "
                            f"it is a float (contract-steps.md §2.)")
    # C5: every table carries the tenant key, or #Contracts names it with why
    tenant = field(body, "PII/sensitive fields classified")
    if migrations and "N/A" not in tenant:
        keys = tenant_keys(tenant, close)
        if not keys:
            gaps.append("#Contracts names no tenant key: put it in backticks in the PII · tenant field (e.g. "
                        "`shop_id`), or write N/A - <reason> there for a single-user product")
        else:
            for p, rel in migrations:
                text = p.read_text(encoding="utf-8", errors="replace")
                starts = list(TABLE_START.finditer(text))
                for i, m in enumerate(starts):
                    table = next(g for g in m.groups() if g)
                    block = text[m.start(): starts[i + 1].start() if i + 1 < len(starts) else len(text)]
                    if not any(re.search(rf"\b{k}\b", block) for k in keys) and not re.search(
                            rf"(?im)^.*\b{re.escape(table)}\b.*\b(?:tenant|untenanted|global|N/A)\b", body):
                        gaps.append(f"table {table} ({rel}) has no {' / '.join(keys)}: add it, or name {table} on a "
                                    f"line of #Contracts with why it has no tenant key")
    # C6: the contract is documented outside the code, or nothing outside the app calls it
    named = {Path(s).name for s in SPEC_FILE.findall(body)}
    if not any(find_in_project(base, n) for n in named) and "N/A" not in field(body, "Contract versioning"):
        gaps.append("no exported contract file: #Contracts names none that exists (openapi.json, *.schema.json, "
                    "*.graphql, *.proto), and the versioning field does not say N/A - <reason> (contract-steps.md §3.)")
    # C7: the agent's shapes, every row by name
    status = base / "STATUS.md"
    if status.is_file() and Status.load(status).header.get("Agent") == "yes":
        agent = field(body, "(Agent)").lower()
        missing = [r for r in AGENT_CONTRACT_ROWS if r not in agent]
        if missing:
            gaps.append(f"Agent: yes - #Contracts' (Agent) field lacks {', '.join(missing)}: each AGENT.md "
                        f"§Contracts row by name, with its path or N/A - <reason>")
    return gaps + (contracts_doc_gaps(base, body) if close and not doc_pending else [])


def earlier_gate_gaps(st: "Status", phase: str, base: Path) -> list[str]:
    """Every earlier filled phase whose check fails now, worded as cmd_set's refusal - for a phase that names all its
    gaps in ONE refusal (and in --dry-run), instead of a second refusal round after the first is fixed."""
    out = []
    for p in CHAIN[:CHAIN.index(phase)]:
        if st.state(p) != "filled" or earlier_override(st, p):
            continue
        failed = phase_check(p, base)
        if failed:
            out.append(f"#{p}'s check fails now, so this phase cannot close on it - {failed}. Fix it, or record the "
                       f"user's reason: status.py open --from {phase} --what \"Override: #{p}'s check fails - <the "
                       f"user's own words>\" --clears \"#{p}'s check passes\"")
    return out


# /tickets' claims a backlog's files can prove, the same way for every model. A ticket file is the issue body built
# from templates/feature_ticket_template.md; its id is in the file name (one model wrote no `# [ID]` heading).
TICKET_FILE = re.compile(r"^(M\d+-[A-Z0-9]+-\d+)[_.]")
TICKET_SECTION = re.compile(r"^#{2,3} [^\n]*?(Lane|Target Files|Contract|Inputs|Depends On|Definition of Done)[^\n]*$",
                            re.M | re.I)
SECTION_KEY = {"lane": "Lane", "target files": "Target Files", "contract": "Contract", "inputs": "Contract",
               "depends on": "Depends On", "definition of done": "Definition of Done"}
TARGET = re.compile(r"`([^`\s]+)`")
SECURITY_WORDS = re.compile(r"(?i)secret|validat|auth|tenant|inject|escap|permission|scope")
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
SYMBOL_SOURCES = SOURCE | {".yaml", ".yml", ".json", ".sql", ".toml", ".prisma", ".graphql", ".proto"}


DOC_TARGET = re.compile(r"(?i)\.(?:md|mdx|markdown|rst|adoc|txt)$")


def ticket_sections(text: str) -> dict[str, str]:
    heads = list(TICKET_SECTION.finditer(text))
    out = {}
    for i, m in enumerate(heads):
        nxt = re.search(r"^#{2,3} ", text[m.end():], re.M)
        out.setdefault(SECTION_KEY[m.group(1).lower()], text[m.end(): m.end() + nxt.start() if nxt else len(text)])
    return out


def tickets_gaps(base: Path) -> list[str]:
    gaps: list[str] = []
    folder = base / "docs" / "issues"
    files = sorted(folder.glob("*.md")) if folder.is_dir() else []
    tickets = {m.group(1): f for f in files if (m := TICKET_FILE.match(f.name))}
    if not tickets:
        return ["no ticket files: docs/issues/<ID>_<slug>.md, one per ticket (references/slicing.md §Per-ticket content)"]
    structure = (base / "STRUCTURE.md").read_text(encoding="utf-8") if (base / "STRUCTURE.md").is_file() else ""
    mods = re.search(r"^## Modules\s*$(.*?)(?=^## |\Z)", structure, re.M | re.S)
    lanes = set()
    for m in re.finditer(r"^\|\s*`([^`]+)`", mods.group(1) if mods else "", re.M):
        lanes |= {m.group(1).strip("/"), m.group(1).strip("/").rsplit("/", 1)[-1]}
    source = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in ticket_sources(base)
                       if "docs/issues" not in p.as_posix())
    words = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", source))
    for f in tickets.values():  # a name another ticket creates or exposes exists once that ticket merges
        text = f.read_text(encoding="utf-8", errors="replace")
        exposes = re.search(r"(?is)\*\*(?:Exposes|Produces|Outputs?):?\*\*:?(.*?)(?=\n- \*\*|\n#|\Z)", text)
        lines = [l for l in text.splitlines() if re.search(r"(?i)\(new\b", l)]
        lines += exposes.group(1).splitlines() if exposes else []
        for line in lines:
            words |= {part for name in TARGET.findall(line) for part in name.split(".")}
            words |= set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", line.split("(new", 1)[-1].split(":", 1)[0]))
    bad: dict[str, list[str]] = {}
    for tid, f in tickets.items():
        secs = ticket_sections(f.read_text(encoding="utf-8", errors="replace"))
        # T1 exact target files, never a bare folder
        paths = TARGET.findall(secs.get("Target Files", ""))
        if not paths or any(p.endswith("/") for p in paths) or not any("." in p.rsplit("/", 1)[-1] for p in paths):
            bad.setdefault("names no exact target file (a file with its extension, never a folder)", []).append(tid)
        # T2 the lane is a STRUCTURE.md module
        lane = next((l.strip().strip("`").strip() for l in secs.get("Lane", "").splitlines() if l.strip()), "")
        if lanes and lane.strip("/") not in lanes:
            bad.setdefault(f"has a lane that is no STRUCTURE.md module ({', '.join(sorted(lanes)[:8])})", []).append(
                f"{tid}={lane or 'none'}")
        # T3 security in the definition of done
        if not SECURITY_WORDS.search(secs.get("Definition of Done", "")):
            bad.setdefault("has no security line in its Definition of Done", []).append(tid)
        # T4 every Depends On is a ticket that exists
        for dep in re.findall(r"\bM\d+-[A-Z0-9]+-\d+\b", secs.get("Depends On", "")):
            if dep not in tickets:
                bad.setdefault("depends on a ticket that does not exist", []).append(f"{tid}->{dep}")
        # T5 every name it CONSUMES exists in the code (a name the ticket creates is marked "(new)")
        consumes = re.search(r"(?is)\*\*Consumes:?\*\*:?(.*?)(?=\n- \*\*|\Z)", secs.get("Contract", ""))
        for line in (consumes.group(1) if consumes else "").splitlines():
            if re.search(r"(?i)\(new\b", line):
                continue
            for name in TARGET.findall(line):
                if IDENT.match(name) and not all(part in words for part in name.split(".")):
                    bad.setdefault("consumes a name the code does not have (mark a name the ticket creates \"(new)\")",
                                   []).append(f"{tid}:{name}")
    plan_md = (base / "TICKETS.md").read_text(encoding="utf-8") if (base / "TICKETS.md").is_file() else ""
    ticket_shape_gaps(base, files, tickets, plan_md, bad)
    for what, where in bad.items():
        gaps.append(f"{len(where)} ticket(s) {what}: {', '.join(where[:6])}{' ...' if len(where) > 6 else ''}")
    # T6 every #Plan milestone has tickets, or TICKETS.md says why not
    product = base / "PRODUCT.md"
    plan = product_sections(product.read_text(encoding="utf-8")).get("Plan", "") if product.is_file() else ""
    for ms in sorted(set(re.findall(r"\b(M\d+)\b", plan)), key=lambda x: int(x[1:])):
        # the reason may sit on the milestone's own line or in the few lines under its heading in TICKETS.md
        near = "\n".join(m.group(0) for m in re.finditer(rf"(?im)^.*\b{ms}\b.*$(?:\n(?!#).*){{0,4}}", plan_md))
        if not any(t.startswith(ms + "-") for t in tickets) and not re.search(
                r"(?i)\b(no tickets?|skipped|not ticketed|why)\b", near):
            gaps.append(f"#Plan milestone {ms} has no ticket and TICKETS.md gives no reason (one line: '{ms}: no "
                        f"tickets - <why>')")
    # T7 the plan file carries its lane flow graph
    if not plan_md:
        gaps.append("no TICKETS.md (references/tickets-md.md)")
    elif "```mermaid" not in plan_md:
        gaps.append("TICKETS.md has no Mermaid lane flow graph (references/tickets-md.md)")
    else:  # T18 one box per lane, no box that is no lane
        boxes = set(re.findall(r"\blane_([A-Za-z0-9_-]+)\s*\[", plan_md))
        used = {next((l.strip().strip("`").strip().strip("/").rsplit("/", 1)[-1] for l in
                      ticket_sections(f.read_text(encoding="utf-8", errors="replace")).get("Lane", "").splitlines()
                      if l.strip()), "") for f in tickets.values()} - {""}
        if used - boxes:
            gaps.append(f"TICKETS.md's flow graph has no `lane_<name>[\"<name> · <owner>\"]` box for lane(s) "
                        f"{', '.join(sorted(used - boxes))} (one box per lane, references/tickets-md.md §The flow graph)")
        if boxes and boxes - used:
            gaps.append(f"TICKETS.md's flow graph has box(es) that are no ticket's lane: {', '.join(sorted(boxes - used))}")
    if plan_md:  # T19 the plan, never the status
        marks = re.findall(r"(?im)^\s*(?:[-*]\s*\[[ xX]\]|\|[^\n]*\|\s*status\s*\|)|✅", plan_md)
        if marks:
            gaps.append(f"TICKETS.md carries {len(marks)} status mark(s) (a checkbox, a Status column, a done mark): "
                        f"status lives on the board, never in the plan (references/tickets-md.md)")
    if (folder / "README.md").is_file():  # T20
        gaps.append("docs/issues/README.md remains: its plan moves into TICKETS.md and the file goes "
                    "(publishing.md §An earlier backlog)")
    return gaps


ADHOC_FILE = re.compile(r"^ADHOC-\d+[_.]")


def ticket_shape_gaps(base: Path, files: list[Path], tickets: dict[str, Path], plan_md: str,
                      bad: dict[str, list[str]]) -> None:
    """T8-T17: what makes a backlog safe for 1 or 2-10 builders side by side, read from the files. Calibrated on
    three logged backlogs (two clean; a logged Gemini backlog had 11 same-milestone pairs writing one file with no
    order between them - two builders would both open one service file on day one)."""
    ids = [m.group(1) for f in files if (m := TICKET_FILE.match(f.name))]
    for name in [f.name for f in files if not TICKET_FILE.match(f.name) and not ADHOC_FILE.match(f.name)
                 and f.name != "README.md"]:  # T8 a file no check reads is a ticket nobody checked
        bad.setdefault("is a file not named <ID>_<slug>.md (M<n>-<EPIC>-<nn>, or ADHOC-<nn> for Mode B)",
                       []).append(name)
    for tid in sorted({t for t in ids if ids.count(t) > 1}):  # T9
        bad.setdefault("ID is used by two files (dedup matches the ID)", []).append(tid)
    texts = {t: f.read_text(encoding="utf-8", errors="replace") for t, f in tickets.items()}
    deps = {t: set(re.findall(r"\bM\d+-[A-Z0-9]+-\d+\b", ticket_sections(x).get("Depends On", ""))) & set(tickets)
            for t, x in texts.items()}

    def before(t: str) -> set[str]:
        seen, todo = set(), list(deps.get(t, ()))
        while todo:
            d = todo.pop()
            if d not in seen:
                seen.add(d)
                todo += deps.get(d, ())
        return seen

    hubs = set(re.findall(r"`([^`\s]+)`", re.search(r"(?ims)^#{2,3} [^\n]*hub files[^\n]*$(.*?)(?=^#{1,3} |\Z)",
                                                     plan_md).group(1))) if re.search(r"(?im)^#{2,3} [^\n]*hub files",
                                                                                     plan_md) else set()
    writers: dict[str, list[str]] = {}
    for tid, x in texts.items():
        secs = ticket_sections(x)
        body = lambda word: re.sub(r"<!--.*?-->", "", (re.search(  # noqa: E731
            rf"(?ims)^#{{2,3}} [^\n]*{word}[^\n]*$(.*?)(?=^#{{2,3}} |\Z)", x) or [None, ""])[1], flags=re.S).strip()
        targets = TARGET.findall(secs.get("Target Files", ""))
        for p in dict.fromkeys(targets):
            writers.setdefault(p, []).append(tid)
        if x.lstrip().startswith("---"):  # T10 the body is published as it stands
            bad.setdefault("opens with front matter (the file is the issue body, published as it stands)", []).append(tid)
        ticked = re.findall(r"(?im)^\s*- \[[xX]\][^\n]*(vertical|horizontal|ad-hoc)", body("Slice Strategy"))
        if len(ticked) != 1:  # T11
            bad.setdefault("does not tick exactly one Slice Strategy", []).append(f"{tid}={len(ticked)}")
        if any(TICKET_SPINE.fullmatch(f"`{p}`") for p in targets):  # T12
            bad.setdefault("lists a spine file or TICKETS.md in Target Files (each phase writes its own rows)",
                           []).append(tid)
        if targets and not any(p.startswith("docs/features/") and p.endswith(".md") for p in targets):  # T13
            bad.setdefault("lists no docs/features/<feature>.md in Target Files", []).append(tid)
        if targets and not all(DOC_TARGET.search(p) for p in targets) and not any(re.search(r"(?i)test|spec", p)
                                                                                 for p in targets):
            bad.setdefault("lists no test file in Target Files (a ticket whose target files are all docs needs none)",
                           []).append(tid)
        if not body("Owner"):  # T14
            bad.setdefault("has no Owner", []).append(tid)
        demo = body("Demo")
        if ticked and ticked[0].lower() == "vertical" and (not demo or re.match(r"(?i)(n/?a|none|nothing)\b", demo)):
            bad.setdefault("is a vertical slice with no Demo (a slice no one can see is a layer)", []).append(tid)  # T15
        if tid in before(tid):  # T16
            bad.setdefault("sits in a Depends On cycle (no builder can start it)", []).append(tid)
    for p, ts in writers.items():  # T17 two builders side by side never write one file unordered
        if len(ts) < 2 or p in hubs or p.startswith("docs/features/"):
            continue
        for i, a in enumerate(ts):
            for b in ts[i + 1:]:
                if a.split("-")[0] == b.split("-")[0] and a not in before(b) and b not in before(a):
                    bad.setdefault("write the same file as another ticket of their milestone with no Depends On "
                                   "between them (order them, or list the file under TICKETS.md ## Hub files)",
                                   []).append(f"{a}+{b}:{p}")
    day1 = re.search(r"(?ims)^#{2,3} [^\n]*day 1[^\n]*$(.*?)(?=^#{1,3} |\Z)", plan_md)
    for row in (day1.group(1).splitlines() if day1 else []):  # T21 a day-1 ticket waits for nothing
        cells = row.split("|")
        start = re.findall(r"\bM\d+-[A-Z0-9]+-\d+\b", cells[3]) if len(cells) > 4 else []
        if start and deps.get(start[0]):
            bad.setdefault("start on day 1 in TICKETS.md but have a Depends On", []).append(start[0])


# D2: files that can import a stylesheet. A sample page under docs/ proves the look, not that the app loads it.
IMPORTERS = {".html", ".htm", ".jinja", ".j2", ".jsx", ".tsx", ".js", ".ts", ".mjs", ".css", ".scss", ".py", ".vue",
             ".svelte", ".astro"}


def design_gaps(base: Path, audit_out: str) -> str | None:
    """V2 + D2, after the audit passed. V2: an audit that checked nothing passes any DESIGN.md (a logged run defined
    no tokens and 0 checks read as green), so 0 checks needs the user's override recorded. D2: a token stylesheet
    nothing imports styles nothing (a logged run wrote tokens.css with no app entry yet), so it needs an importer or
    an open item that hands the import to /foundation."""
    design = (base / "DESIGN.md").read_text(encoding="utf-8")
    m = re.search(r"(\d+) pass \| (\d+) warn \| (\d+) error", audit_out)
    if m and sum(map(int, m.groups())) == 0:
        product = base / "PRODUCT.md"
        sec = product_sections(product.read_text(encoding="utf-8")).get("Design", "") if product.is_file() else ""
        if not any("override" in l.lower() for l in (sec + "\n" + design).splitlines()):
            return ("the audit checked 0 things - DESIGN.md defines no tokens it can read. Define them (light and dark), "
                    "or record the user's override with their reason in #Design (a line with the word 'override')")
    sheets = {Path(s).name for s in re.findall(r"[\w./-]+\.css\b", design)}
    sheets = {s: find_in_project(base, s) for s in sheets}
    sheets = {s: p for s, p in sheets.items() if p is not None}
    if not sheets:
        return None
    importers = []
    for dirpath, dirnames, files in os.walk(base):
        dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS and not (Path(dirpath) == base and x == "docs")]
        importers += [Path(dirpath) / f for f in files if Path(f).suffix.lower() in IMPORTERS]
    status = base / "STATUS.md"
    open_rows = Status.load(status).rows["Open items"] if status.is_file() else []
    for name, path in sheets.items():
        if any(f.resolve() != path.resolve() and name in f.read_text(encoding="utf-8", errors="replace")
               for f in importers):
            continue
        if any(name in r[3] and not r[5] for r in open_rows):
            continue
        return (f"{path.relative_to(base).as_posix()} is imported by no app file (a sample under docs/ does not count). "
                f"Import it from the app's root entry, or, when the entry does not exist yet: status.py open --from "
                f"design-system --what \"the root entry imports {name}\" --clears \"/foundation creates the entry and "
                f"imports it\"")
    return None


def vkey(v: str) -> tuple:
    """1.73.0-next.15 < 1.73.0-next.16 < 1.73.0 < 1.74.0 (a pre-release sorts before its release)."""
    m = re.match(r"(\d+)\.(\d+)\.(\d+)(?:-[a-z]+\.(\d+))?", v)
    if not m:
        return (0,)
    a, b, c, pre = m.groups()
    return (int(a), int(b), int(c), 0 if pre else 1, int(pre or 0))


def rule_changes(st: Status, phase: str) -> list[str]:
    """What changed in the rules since this phase was filled, for the flags this product has."""
    r = next((x for x in st.rows["Phases"] if x[0] == phase), None)
    if r is None or r[1] != "filled":
        return []
    on = {"all", *(k for k, h in (("agent", "Agent"), ("ai", "AI product"), ("ui", "UI")) if st.header.get(h) == "yes")}
    got = vkey(r[6]) if len(r) > 6 and r[6] else None
    return [w for v, p, when, w in RULE_CHANGES if p == phase and when in on and (got is None or got < vkey(v))]


def undo_msys_path(value: str) -> str:
    return MSYS_REWRITE.sub("/", value)


# A note is read by a person first: plain words, not operators. "at least 3 of 8", "up to €30", "28 Sep to 11 Oct".
NOT_PLAIN = re.compile(r">=|<=|=>|!=|(?<=\d)\.\.(?=\d)")
PLAIN_FIELDS = {"note", "reason", "what", "clears"}


def capped(field: str, value: str, where: str = "") -> str:
    value = " ".join(str(value).split())
    bad = NOT_PLAIN.search(value)
    if field in PLAIN_FIELDS and bad:
        raise Refused(f"{field} uses {bad.group(0)!r}; write it in plain words - 'at least 3 of 8', 'up to 30', "
                      f"'2026-09-28 to 2026-10-11'. A person reads this row first.")
    limit = CAP.get(field, CAP["cell"])
    if len(value) > limit:
        raise Refused(f"{field} is {len(value)} characters; the limit is {limit}. A status row is a record: keep "
                      f"the fact here and put the detail in {where or 'the file this row points to'}.")
    return value


def need_date(v: str, what: str) -> str:
    if not DATE.match(v or ""):
        raise Refused(f"{what} must be a date as YYYY-MM-DD, got {v!r}")
    return v


# ---- the next phase ---------------------------------------------------------------------------------------
TICKET_ID = re.compile(r"`([A-Z][A-Z0-9]*-[A-Z0-9]+-\d+)`")


def milestone_plan(base: Path) -> dict[str, list[str]] | None:
    """TICKETS.md's tickets per milestone, in order. None: no TICKETS.md."""
    f = base / "TICKETS.md"
    if not f.exists():
        return None
    milestone, plan = None, {}
    for line in f.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## (M\d+)\b", line)
        if m:
            milestone = m.group(1)
            plan.setdefault(milestone, [])
        elif line.startswith("## "):
            milestone = None
        elif milestone and line.startswith("|"):
            for t in TICKET_ID.findall(line):
                if t not in plan[milestone]:
                    plan[milestone].append(t)
    return plan


def ticket_progress(st: Status) -> dict | None:
    """The first milestone in TICKETS.md with a ticket that has no row in ## Tickets. None: no TICKETS.md."""
    plan = milestone_plan(st.base)
    if plan is None:
        return None
    done_ids = {r[0] for r in st.rows["Tickets"]}
    for ms, ids in plan.items():
        missing = [t for t in ids if t not in done_ids]
        if missing:
            return {"milestone": ms, "total": len(ids), "done": len(ids) - len(missing), "missing": missing}
    return {"milestone": None, "total": 0, "done": 0, "missing": []}


def in_checkout(base: Path, row: list[str]) -> bool:
    """A ticket's work is in HEAD: a commit its row names (the review's fix commit) is an ancestor of HEAD; a row that
    names none counts when its record file is committed in HEAD. A logged checkpoint's two tickets each passed on their
    own branch and failed 12 tests once merged - a check on the branch that has neither proves nothing."""
    shas = [s for s in re.findall(r"\b[0-9a-f]{7,40}\b", " ".join(row)) if git(base, "rev-parse", "--verify", "--quiet",
                                                                              f"{s}^{{commit}}")]
    if shas:
        return any(git(base, "merge-base", s, "HEAD") == git(base, "rev-parse", s) for s in shas)
    tracked = git(base, "ls-tree", "-r", "--name-only", "HEAD", FRAG_DIR + "/tickets").lower()
    return row[0].lower() in tracked


def dev_check_state(st: Status) -> dict | None:
    """The milestone a checkpoint checks - the first with a ticket not recorded, not done, or not in this checkout,
    else the last - and each of its tickets' state. None: no TICKETS.md."""
    plan = milestone_plan(st.base)
    if not plan:
        return None
    rows = {r[0]: r for r in st.rows["Tickets"]}
    for ms, ids in plan.items():
        state = [(t, "not recorded" if t not in rows else f"DoD {rows[t][2]}" if rows[t][2] != "yes"
                  else "done" if in_checkout(st.base, rows[t]) else "not in this checkout") for t in ids]
        if any(s != "done" for _, s in state) or ms == list(plan)[-1]:
            return {"milestone": ms, "tickets": state}
    return None


def dev_check_gaps(st: Status) -> list[str]:
    """What a PASS needs the repo to show, the same way for every model: every ticket of the milestone recorded, done
    and merged into this checkout, and the project's full check recipe passing on this exact code. A FAIL verdict
    always records - a failing checkpoint is the point of the skill."""
    base, gaps = st.base, []
    s = dev_check_state(st)
    if s is None:
        return ["no TICKETS.md: nothing says which tickets make the milestone - run /tickets"]
    for want in ("not recorded", "DoD", "not in this checkout"):
        ids = [t for t, v in s["tickets"] if v.startswith(want)]
        if ids:
            gaps.append(f"{len(ids)} of {len(s['tickets'])} {s['milestone']} tickets {want}: "
                        f"{', '.join(ids[:8])}{' ...' if len(ids) > 8 else ''}")
    d = git_dir(base)
    branch = git(base, "rev-parse", "--abbrev-ref", "HEAD")
    gate_gap = final_gate_gap(base, d, branch)[0] if d else "not a git checkout"
    if gate_gap:
        gaps.append(gate_gap.replace("commit the last code change, then run the gate once more",
                                     "run the start's gate command on this checkout"))
    return gaps


# F1: what #Dev-complete must show, pass or fail. A logged checkpoint stopped at the red suite and left security,
# scope and the live run "UNVERIFIED: stopped on red"; plain Claude, same code, ran all of them and found more.
DEV_CHECKS = {"the gate (the project's full checks on this code)": r"just check|make check|npm (?:run )?test|pytest|gate",
              "the live path (/run, the observable result)": r"live|/run|devserver|route|endpoint|/healthz",
              "security (each built ticket's DoD)": r"security",
              "scope creep (against #Scope)": r"scope|creep"}
SKIPPED_ON_RED = re.compile(r"(?i)(stopp?(?:ed|s)?|halt\w*|skipp?\w*)\b[^\n]{0,40}\b(on|at|after)\s+(the\s+)?"
                            r"(first\s+)?(red|fail\w*)")


def dev_complete_gaps(sec: str) -> list[str]:
    """F1: every check named in #Dev-complete with its result, none skipped because an earlier one was red."""
    body = re.sub(r"<!--.*?-->", "", sec, flags=re.S)
    gaps = [f"no line for {what}" for what, rx in DEV_CHECKS.items() if not re.search(rf"(?i){rx}", body)]
    if SKIPPED_ON_RED.search(body):
        gaps.append(f"a check was skipped because an earlier one failed ({SKIPPED_ON_RED.search(body).group(0)!r})")
    return gaps


CHECK_NOT_RUN = re.compile(r"(?i)\bunverified\b|\bnot (?:run|checked|tested|probed)\b")


def skipped_checks(body: str, checks: dict[str, str]) -> list[str]:
    """Q40 (a saving made of a skipped check): the checks whose EVERY line in the record says UNVERIFIED or not run.
    Every line, not any: another line may name the same command beside its own UNVERIFIED (a logged #Dev-complete's
    "No hardcoding ... UNVERIFIED: `just check` did not reach green"), and that is no skip of the gate."""
    lines = re.sub(r"<!--.*?-->", "", body, flags=re.S).splitlines()
    out = []
    for what, rx in checks.items():
        hits = [ln for ln in lines if re.search(rf"(?i){rx}", ln)]
        if hits and all(CHECK_NOT_RUN.search(ln) for ln in hits):
            out.append(f"--verdict pass with {what} not run (every line for it says UNVERIFIED or not run) - a PASS "
                       f"needs it run; record --verdict fail, or run it")
    return out


def dev_check_fail_handoff(st: Status) -> str | None:
    """Owner 2026-10-06: after a checkpoint FAIL, the handoff names the work, not the checkpoint again - the first
    ticket still to build, or (nothing left to build) fixing what the FAIL named. None: no FAIL recorded."""
    r = st.phase("dev-check")
    s = dev_check_state(st) if getattr(st, "base", None) is not None else None
    if r[1] != "filled" or r[4] != "fail" or s is None:
        return None
    todo = [t for t, v in s["tickets"] if v == "not recorded" or v.startswith("DoD")]
    if todo:
        return (f"Open a NEW conversation and type: {skill_command('build')} {todo[0]} - the checkpoint failed with "
                f"{len(todo)} ticket(s) of {s['milestone']} still to build ({', '.join(todo[:6])}"
                f"{' ...' if len(todo) > 6 else ''}); one ticket per conversation, then {skill_command('dev-check')} "
                f"again. Nothing is lost: it is all in PRODUCT.md, STATUS.md and git.")
    return (f"Fix what the FAIL named in #Dev-complete (an unmerged ticket branch, the red gate on the merged code), "
            f"then open a NEW conversation and type: {skill_command('dev-check')} - nothing is lost: it is all in "
            f"PRODUCT.md, STATUS.md and git.")


def dev_check_close_gaps(st: Status, verdict: str) -> list[str]:
    """P20: the checkpoint record's problems in ONE list - #Dev-complete's missing checks and, for a PASS, what the repo
    does not show. They were two refusals in turn, and neither honoured --dry-run."""
    prod = st.base / "PRODUCT.md"
    gaps = [f"#Dev-complete: {g} - every check runs once, pass or fail: a red one decides the verdict, never how "
            f"much is checked" for g in dev_complete_gaps(product_sections(prod.read_text(encoding="utf-8"))
                                                          .get("Dev-complete", ""))] if prod.exists() else []
    if verdict == "pass":
        gaps += [f"--verdict pass needs it (record --verdict fail and name it in #Dev-complete, or fix it first): {g}"
                 for g in dev_check_gaps(st)]
        if prod.exists():
            gaps += skipped_checks(product_sections(prod.read_text(encoding="utf-8")).get("Dev-complete", ""),
                                   DEV_CHECKS)
    return gaps


# what #Tests must show, pass or fail (the lean path's proof that the suite covers what plain Claude's covered)
def seed_recipe(base: Path) -> str | None:
    """The project's own seed command (a just/make recipe or an npm script named seed*): a logged live check hit a 401
    because the dev database was never seeded."""
    for name, rx, fmt in (("justfile", r"(?m)^(seed[\w-]*)(?:\s+[^:\n=]*)?:(?!=)", "just {}"),
                          ("Justfile", r"(?m)^(seed[\w-]*)(?:\s+[^:\n=]*)?:(?!=)", "just {}"),
                          ("Makefile", r"(?m)^(seed[\w-]*)\s*:", "make {}")):
        f = base / name
        if f.is_file():
            m = re.search(rx, f.read_text(encoding="utf-8", errors="replace"))
            if m:
                return fmt.format(m.group(1))
    pkg = base / "package.json"
    if pkg.is_file():
        try:
            names = [k for k in (json.loads(pkg.read_text(encoding="utf-8")).get("scripts") or {}) if k.startswith("seed")]
        except ValueError:
            names = []
        if names:
            return f"npm run {names[0]}"
    return None


def outside_files(base: Path) -> list[str]:
    """Non-test code that calls an outside service (HTTP client, vendor SDK, mail): each is a way the product can
    reach the real world when it starts as the project runs it."""
    out = []
    for f in project_files(base, {".py", ".ts", ".js"}):
        rel = f.relative_to(base).as_posix()
        if not is_test(rel) and OUTSIDE_CALL.search(f.read_text(encoding="utf-8", errors="replace")):
            out.append(rel)
    return out


# P4 for /vision: its Step 3b stops were sentences, and a logged Gemini /vision stated why now as fact with no search,
# defined one north-star term of five, and passed its own gate. `set vision filled` runs these instead - on its own
# close only, never as an earlier phase's re-check (a project filled under older rules is not blocked later), and
# never for /adopt's inferred record. Whether a sentence is sharp stays a judgement; these are the countable parts.
VISION_FIELDS = (("the vision sentence", r"^vision\b"), ("who it's for", r"^who\b"), ("the problem", r"^problem"),
                 ("the value proposition", r"value prop"), ("the market read", r"market|competitor"),
                 ("the north-star target", r"target"), ("the input metrics", r"input"),
                 ("the guardrail", r"guardrail"), ("the instrumentation line", r"instrument"),
                 ("the job-to-be-done", r"^job"), ("the riskiest assumption", r"riskiest"),
                 ("the business model", r"business model"), ("the plain-words summary", r"plain words"),
                 ("the worked example", r"worked example"), ("the first users", r"first users"),
                 ("the constraints line", r"^constraints"))
# An AI product also answers what the AI does and what a person decides, the accuracy bar and the cost per use:
# /eval's threshold and /architect's cost input start here (a review, 2026-09-30)
AI_LINE = r"^ai\b"
# the bullet is optional (P8): a logged Cursor and a logged Codex /vision wrote `**Label:** value` with no "- ",
# and every field read as empty - 6 and 8 calls lost to a refusal that named no cause
FIELD_LINE = re.compile(r"^(?:[-*]\s+)?\*\*(.+?)\*\*:?\s*(.*)$")
EMPTY_VALUE = re.compile(r"(?i)^(?:|-|—|tbd|todo|pending|n/?a|<[^>]*>)$")
NORTH_STAR_HEADING = re.compile(r"(?i)^#{1,6}\s.*north[- ]?star")
LATEX = re.compile(r"\$\\[a-zA-Z]+|\\\(|\\\[")
URL = re.compile(r"https?://\S+")
REDIRECT = re.compile(r"(?i)grounding-api-redirect|google\.[a-z.]+/url\?|bing\.com/ck/|duckduckgo\.com/l/")
HOMEPAGE = re.compile(r"(?i)https?://[^/\s)]+/?(?:[a-z]{2}(?:[-_][a-z]{2})?/?)?[)\].,;]*$")  # a site, maybe its /nl/
FACT_LINE = re.compile(r"(?i)^\W*(?:rules|why[- ]now|complaints|languages)\b")
# a search that found nothing says so; a comparable pointing at the search that found it ("Netto · search 2") has
# its link on that search's line
NOTHING_FOUND = re.compile(r"(?i)\bnothing\b|\bno (?:results?|hits?|sources?|pages?)\b|·\s*searche?s?\s+\d")
# the search-list heading, not any heading that mentions searches: a logged Antigravity /vision wrote "## Problem (Then
# How It Happens, From the Searches)" and its bullets were refused as search lines without links (2026-10-01)
SEARCH_HEADING = re.compile(r"(?i)^#{1,6}\s(?![^\n]*(?:\(|from the search))[^\n]*\bsearch")
OWNER_ANSWERS = re.compile(r"(?i)^#{1,6}\s.*owner'?s?['’]?s? (?:answers|inputs|words)")
NUMBER_FROM = re.compile(r"(?i)\b(owner|proposed|searched|derived)\b")
# the two searches every logged /vision skipped and plain Claude's research helper ran (2026-09-30): products doing
# this exact job anywhere, and the rules that apply. Prefixes as `why now ·`; a line naming the topic also counts (P8)
# The market the owner named comes first (2026-10-01: a logged Cursor /vision searched one country's market only
# in English, for its big names, and missed the local same-job product plain found with a local-language query)
SEARCH_KINDS = (("local", r"(?i)^\W*local\b|no market named",
                 "the market the owner named first, in its own language(s): what its players and newcomers offer "
                 "for this job (no market named: `local · no market named`)"),
                ("same job", r"(?i)^\W*same[- ]job\b|exact[- ]job|same job|comparables?\b|competitors?\b",
                 "products that already do this exact job, anywhere in the world"),
                ("rules", r"(?i)^\W*rules\b|regulat|\blaws?\b|legal|gdpr|compliance|privacy|data protection|ai act",
                 "the rules that apply: data protection, AI law, the sector's own law"))


def vision_labels() -> list[str]:
    """The template's #Vision labels, so a refusal names the exact line to write."""
    tpl = tool_file("templates", "PRODUCT.md")
    body = product_sections(tpl.read_text(encoding="utf-8")).get("Vision", "") if tpl else ""
    return [m.group(1).strip().rstrip(":") for m in map(FIELD_LINE.match, body.splitlines()) if m]


def search_list_lines(lines: list[str]) -> list[str] | None:
    """The lines under the companion's search-list heading(s), to the next heading; None when there is none."""
    out, inside, found = [], False, False
    for l in lines:
        if l.startswith("#"):
            inside = bool(SEARCH_HEADING.match(l))
            found |= inside
        elif inside:
            out.append(l)
    return out if found else None


def section_fields(body: str) -> dict[str, str]:
    """`- **Label:** value` bullets of a section, each with the sub-bullets under it (a long line split by reflow)."""
    out: dict[str, str] = {}
    label = None
    for line in body.splitlines():
        m = FIELD_LINE.match(line.strip()) if not line.startswith((" ", "\t")) else None
        if m:
            label = m.group(1).strip().rstrip(":")
            out[label] = m.group(2).strip()
        elif label and line.startswith((" ", "\t")) and line.strip():
            out[label] = (out[label] + " " + line.strip()).strip()
        elif not line.strip():
            continue
        else:
            label = None
    return out


def vision_gaps(base: Path, header: dict[str, str]) -> list[str]:
    """What `set vision filled` needs, every problem named once in one list (P20)."""
    prod, comp = base / "PRODUCT.md", base / OWN_COMPANION["Vision"]
    body = re.sub(r"<!--.*?-->", "", product_sections(prod.read_text(encoding="utf-8")).get("Vision", "")
                  if prod.is_file() else "", flags=re.S)
    fields = section_fields(body)
    gaps = []
    labels = vision_labels()
    if not fields:  # one cause, named once - never fifteen "empty" lines for a shape the parser missed (P20)
        gaps.append("#Vision: no fields found - each field is one line `- **<label>:** <value>`, the labels as "
                    "`next --phase vision` printed them")
    for what, rx in VISION_FIELDS if fields else ():
        hit = [v for k, v in fields.items() if re.search(rx, k, re.I)]
        if not hit or all(EMPTY_VALUE.match(re.sub(r"[*_`\s]+", " ", v).strip()) for v in hit):
            label = next((l for l in labels if re.search(rx, l, re.I)), "")
            gaps.append(f"#Vision field empty: {what}" + (f" - the line `- **{label}:** <value>`" if label else ""))
    target = " ".join(v for k, v in fields.items() if re.search("target", k, re.I))
    undated = re.sub(r"\b20\d\d(?:-\d\d){0,2}\b|\b[QH][1-4]\b", "", target)  # a date or a quarter is not the number
    if target.strip() and not (re.search(r"\b20\d\d\b", target) and re.search(r"\d", undated)):
        gaps.append("#Vision: the north-star target needs a number and a date (\"40 restaurants ... by 2027-03-31\"), "
                    "not a direction")
    ai = " ".join(v for k, v in fields.items() if re.search(AI_LINE, k, re.I)).strip()
    if header.get("AI product") == "yes" and (EMPTY_VALUE.match(ai.lower()) or ai.lower() in ("n/a", "none", "no")):
        gaps.append("#Vision field empty: the AI line (an AI product: what the AI does · what a person decides · "
                    "the accuracy bar · the cost per use)")
    example = " ".join(v for k, v in fields.items() if re.search("worked example", k, re.I))
    if example.strip() and not re.search(r"\d", example):
        gaps.append("#Vision: the worked example has no numbers - one real-looking case with its names and numbers")
    doc = comp.read_text(encoding="utf-8") if comp.is_file() else ""
    if not doc:
        gaps.append(f"no {OWN_COMPANION['Vision']} - it holds the search list and the north-star terms table")
    else:
        lines = doc.splitlines()
        # the search list is the lines under a heading naming searches; with none, any line of the search shape
        listed = search_list_lines(lines)
        # any honest line shape (P8): `·` as the skill writes it, or a line saying what the search settled
        searches = [l for l in (listed if listed is not None else lines)
                    if (re.match(r"(?:[-*]|\d+[.)])\s", l) if listed is not None
                        else "·" in l or re.search(r"(?i)\bsettled\b", l))
                    and not l.lstrip().startswith(("|", "#")) and "no search" not in l.lower()]
        if not searches:
            gaps.append(f"{OWN_COMPANION['Vision']} lists no search - one line each: query · what it settled · "
                        f"<source link>")
        # every search has a source a reader can open (four reviews, 2026-09-30: no links, so no claim could be
        # checked); a search that found nothing says so
        gaps += [f"{OWN_COMPANION['Vision']} search line has no source link (https://...): {l.strip()[:70]!r}"
                 for l in searches if not URL.search(l) and not NOTHING_FOUND.search(l)]
        # a search engine's redirect is not a source: nobody can read it back (a logged Antigravity /vision's links
        # were all grounding-api-redirect addresses or homepages, and it opened no page - 2026-10-01)
        gaps += [f"{OWN_COMPANION['Vision']} search line links a search redirect, not a page: open the page and cite "
                 f"its own address: {l.strip()[:70]!r}" for l in searches
                 if URL.search(l) and all(REDIRECT.search(u) for u in URL.findall(l))]
        # a fact (a rule, a date, a complaint, a language) needs the page that says it, not the site: a logged
        # Antigravity /vision linked eur-lex.europa.eu and socialsecurity.be bare, and opened no page (2026-10-01).
        # A product's own homepage stays fine on a local / same job / nearby line.
        gaps += [f"{OWN_COMPANION['Vision']} search line cites a site's homepage for a fact: link the page that says "
                 f"it: {l.strip()[:70]!r}" for l in searches
                 if FACT_LINE.search(l) and URL.search(l) and all(HOMEPAGE.match(u) for u in URL.findall(l))]
        for kind, rx, what in SEARCH_KINDS:
            if searches and not any(re.search(rx, l) for l in searches):
                gaps.append(f"{OWN_COMPANION['Vision']} has no `{kind} ·` search line - {what}")
        if not any(OWNER_ANSWERS.match(l) for l in lines):
            gaps.append(f"{OWN_COMPANION['Vision']} has no `## Owner's answers` - each answer in the owner's own "
                        f"words, one per question, so who it's for and the business model can be checked against them")
        problem = " ".join(v for k, v in fields.items() if re.search("problem", k, re.I)).lower().replace("’", "'")
        if not any(re.search(r"(?i)why[- ]now", l) for l in searches) and "owner's claim" not in problem:
            gaps.append(f"why now has no search line in {OWN_COMPANION['Vision']} (`why now · <query> · what it "
                        f"settled`) and #Vision's problem is not marked `why now: the owner's claim, not verified`")
        rows, i = [], 0
        while i < len(lines):
            if NORTH_STAR_HEADING.match(lines[i]):
                j = i + 1
                while j < len(lines) and not lines[j].startswith("#"):
                    cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                    if lines[j].lstrip().startswith("|") and len(cells) >= 2 and not re.fullmatch(r"[-: ]*", "".join(cells)):
                        rows.append(cells)
                    j += 1
                i = j
            else:
                i += 1
        if len(rows) < 2:  # the header row and at least one term
            gaps.append(f"{OWN_COMPANION['Vision']} has no north-star terms table: a `## North-star terms` heading, "
                        f"then `| Term | Number | From |` with one row per term in the target and the inputs")
        # a definition, not a digit: "Monday to Sunday" and "zero changes" are exact (P8); only a blank row fails.
        # "bar: not set" is an honest number - the owner gave none (never invent one to fill the cell)
        gaps += [f"{OWN_COMPANION['Vision']} north-star term {r[0][:40]!r} has no definition - give it an exact "
                 f"one (\"active\" = \"1+ chore in 14 days\"), or `bar: not set`" for r in rows[1:]
                 if EMPTY_VALUE.match(r[1].strip("*_` ").lower()) or r[1].strip() == "?"]
        # where each number came from (four reviews: 40%, 95%, "≥10 questions" were the model's, unmarked)
        if len(rows) >= 2 and (len(rows[0]) < 3 or not re.search(r"(?i)from|source", rows[0][2])):
            gaps.append(f"{OWN_COMPANION['Vision']} north-star terms table has no `From` column - `| Term | Number | "
                        f"From |`, From = owner · proposed · searched · derived")
        elif len(rows) >= 2:
            gaps += [f"{OWN_COMPANION['Vision']} north-star term {r[0][:40]!r}: From is {r[2][:20]!r} - one of owner "
                     f"· proposed · searched · derived" for r in rows[1:]
                     if len(r) < 3 or not NUMBER_FROM.search(r[2])]
    if header.get("AI product") not in ("yes", "no") or (header.get("AI product") == "yes"
                                                         and header.get("Agent") not in ("yes", "no")):
        gaps.append("the AI answer (question 6) is not recorded: add `--ai yes|no --agent yes|no` to this `set`")
    for name, text in (("#Vision", body), (OWN_COMPANION["Vision"], doc)):
        if LATEX.search(text):
            gaps.append(f"{name} has LaTeX ({LATEX.search(text).group(0)}...) - plain symbols (≥ ≤ →)")
    return gaps


TEST_CHECKS = {"the live path (the running app, the observable result)": r"live|/run|devserver|route|endpoint|/healthz",
               "security / adversarial cases": r"security|adversarial|tenant|isolation|injection|authz|forged",
               "regression tests for fixed or found bugs": r"regression|xfail|issue\s*#\d+|#\d+"}


def tests_gaps(st: Status, verdict: str) -> list[str]:
    """What `set test filled` needs: #Tests names each kind of case with its result, and a PASS has the project's full
    checks passing on this exact code (a suite someone wrote but never ran green is not a gate)."""
    prod = st.base / "PRODUCT.md"
    sec = product_sections(prod.read_text(encoding="utf-8")).get("Tests", "") if prod.is_file() else ""
    body = re.sub(r"<!--.*?-->", "", sec, flags=re.S)
    gaps = [f"#Tests has no line for {what}" for what, rx in TEST_CHECKS.items() if not re.search(rf"(?i){rx}", body)]
    if outside_files(st.base) and not re.search(r"(?im)^\W*outside-service reach\b", body):
        gaps.append("#Tests has no `Outside-service reach:` line - name the tests proving each outside-service file uses "
                    "the fake or refuses when the app starts as the project runs it (or the bug they exposed)")
    if verdict == "pass":
        gaps += skipped_checks(sec, TEST_CHECKS)
        d = git_dir(st.base)
        gate_gap = final_gate_gap(st.base, d, git(st.base, "rev-parse", "--abbrev-ref", "HEAD"),
                                  own="Tests")[0] if d else "no git"
        if gate_gap:  # uncommitted is fine: the gate records the exact files it checked
            gaps.append(gate_gap.replace("commit the last code change, then run the gate once more",
                                         "run the start's gate command once over the final files (tests and "
                                         "docs/tests.md written; committing first is not needed)"))
    return gaps


# security code a /test must attack even before its feature exists: guards, sanitisers, policies, validators
GUARD_CODE = re.compile(r"(?i)(^|/)(guards?|sanitiz\w*|escap\w*|redact\w*|polic(y|ies)|permissions?|authz|"
                        r"injection|firewall|validators?)(/|\.|_)")


def test_start_text(st: Status) -> str:
    """/test's start: the built tickets and the files they changed, where the suite points, each ticket's security
    surface, and the gate + live-path commands - what a plain run spends its first calls discovering."""
    base = st.base
    rows = [r for r in st.rows["Tickets"] if in_checkout(base, r)]
    parts = [f"===== tests: {git(base, 'rev-parse', '--abbrev-ref', 'HEAD')} @ {git(base, 'rev-parse', '--short', 'HEAD')}"
             f" ====="]
    pre = env_precheck(base)
    if pre:
        parts.append(pre)
    dc, tt = st.phase("dev-check"), st.phase("test")
    parts.append(f"Dev check: {dc[1]}{' - not verified: warn, and record an override (status.py bypass)' if dc[1] != 'filled' else ''}"
                 f" · #Tests: {tt[1]}{' - a RE-RUN: see the RE-RUN line above' if tt[1] == 'filled' else ''}")
    if not rows:
        parts.append("! no built ticket in this checkout - nothing to test yet: run /build first (or say what to test)")
    for r in rows:
        tf = find_ticket(base, r[0])
        spec = tf.read_text(encoding="utf-8", errors="replace") if tf else ""
        secs = ticket_sections(spec) if spec else {}
        files = TARGET.findall(secs.get("Target Files", ""))
        touches = sorted({w.lower() for w in SECURITY_TICKET.findall(spec)})
        # the criteria next to the tests that exist: the run judges the gaps, it does not rediscover the ticket
        dod = [re.sub(r"^\s*-\s*\[.\]\s*", "", ln).strip() for ln in secs.get("Definition of Done", "").splitlines()
               if re.match(r"^\s*-\s*\[.\]", ln)]
        tests = [n for f in files if is_test(f) and (base / f).is_file()
                 for n in re.findall(r"^\s*(?:async\s+)?def (test_\w+)|^\s*(?:it|test)\(['\"]([^'\"]+)",
                                     (base / f).read_text(encoding="utf-8", errors="replace"), re.M) for n in [n[0] or n[1]]]
        parts.append(f"{r[0]} (doc {r[-1]}): files {', '.join(files[:8]) or 'see its ticket'}"
                     + (f"\n  security surface: {', '.join(touches)}" if touches else "")
                     + (f"\n  definition of done: " + " · ".join(d[:70] for d in dod[:10]) if dod else "")
                     + (f"\n  its tests ({len(tests)}): " + ", ".join(tests[:25]) if tests else "\n  its tests: none found"))
    tests_text = "\n".join((base / q).read_text(encoding="utf-8", errors="replace")
                           for q in (x.relative_to(base).as_posix() for x in project_files(base, {".py", ".ts", ".js"}))
                           if is_test(q))
    guards = []
    for g in project_files(base, {".py", ".ts", ".js"}):
        rel = g.relative_to(base)
        if is_test(rel.as_posix()) or rel.stem == "__init__" or not GUARD_CODE.search(rel.as_posix()):
            continue
        named = len(re.findall(rf"\b{re.escape(rel.parent.name)}[./]{re.escape(rel.stem)}\b|from\s+[\w.]*\b"
                               rf"{re.escape(rel.parent.name)}\s+import\s+[^\n]*\b{re.escape(rel.stem)}\b", tests_text))
        guards.append(f"{rel.as_posix()} (named in tests: {named})")
    reach = outside_files(base)
    if reach:  # both a playbook run and plain Claude missed: the dev app called real Shopify; a seeder reached a real store
        parts.append("Outside-service reach - these files call an outside service: " + ", ".join(reach[:12])
                     + ". For each, a test starts the code the way the project really runs it (the dev entry point, a "
                       "script's own main(), the development config - nothing faked by the test itself) and proves it "
                       "uses the fake or refuses; one that reaches the real service is a real bug: xfail + file it. "
                       "#Tests carries `Outside-service reach:` naming those tests.")
    if guards:  # a logged /test called injection "weak - the agent isn't built", and missed a broken built guard
        parts.append("Security code already built - test each one adversarially NOW, even when the feature that calls "
                     "it isn't built yet (variants: case, spacing, encoding, look-alikes - write them as "
                     "chr(0x043E) or \\N{CYRILLIC SMALL LETTER O}, never the raw character (linters reject it) "
                     "and never \\u in an edit tool (its input decodes it to the raw character)): " + ", ".join(guards[:10]))
    env = base / ".env"
    target = next((ln.split("=", 1)[1].strip() for ln in (env.read_text(encoding="utf-8", errors="replace").splitlines()
                                                          if env.is_file() else []) if ln.startswith("TEST_DATABASE_URL=")), "")
    if target:  # the database name only, never the credentials
        parts.append(f"The suite's database: {re.sub(r'^.*@', '', target)} - every destructive test runs there, never "
                     f"on the development one")
    recipe = check_recipe(base)
    gate = tool_file("build", "gate.py")
    if gate:
        parts.append(f"Gate - the full checks, once, after the tests and docs/tests.md are written (a pass counts on "
                     f"those exact files, committed or not; it is reused, never re-run, while they are unchanged): "
                     f"python \"{gate.as_posix()}\" \"{recipe[0] if recipe else '<the project check command>'}\"")
    prod = base / "PRODUCT.md"
    spine = product_sections(prod.read_text(encoding="utf-8", errors="replace")) if prod.is_file() else {}
    dev, port, health = dev_server(base, spine.get("Foundation", ""))
    server = tool_file("foundation", "devserver.py")
    if server and dev and port:
        url = health if (health or "").startswith("http") else f"http://127.0.0.1:{port}{health or '/'}"
        run_ = f"python \"{server.as_posix()}\""
        seed = seed_recipe(base)
        parts.append(f"Live path - an automated, re-runnable test that starts the real entry point against the test "
                     f"database and asserts on what a user sees (a one-off script is not evidence; its evidence line "
                     f"cites that test file, never devserver.py; it starts a process, so run it when you write it and "
                     f"then only in the gate - not after every change: a logged run spent 4.3 min on 8 runs of it)"
                     + (f"; the dev database needs `{seed}` first" if seed else "")
                     + "".join(f"; docs/runbook.md: {r}" for r in runbook_start_rules(base, dev))
                     + f"; to look first: {run_} start --cmd \"{dev}\" --port {port} --health {url} · hit the built "
                       f"routes · {run_} stop --port {port}")
    # applicability, so no run writes browser cases for a service with no screen, or calls a dataset "proof"
    ui = st.header.get("UI", "unknown")
    # the injected-DOM risk lives on a form/auth surface a browser hydrates, not on a layout shell
    screens = [p for p in project_files(base, (".html", ".tsx", ".jsx", ".vue", ".svelte", ".jinja", ".j2"))
               if re.search(r"(?i)<form\b|type=[\"']password|<input\b", p.read_text(encoding="utf-8", errors="replace"))]
    parts.append("Browser / real-user-environment cases: " + (
        f"APPLY - {len(screens)} form/auth screen(s), e.g. {screens[0].relative_to(base).as_posix()}"
        if ui == "yes" and screens else "not applicable yet - no built form or auth screen (say so in #Tests, write none)"))
    ci = sorted(p.name for p in (base / ".github" / "workflows").glob("*.y*ml")) if (base / ".github").is_dir() else []
    parts.append(f"CI: {', '.join(ci) + ' - check that a red run blocks merge; ' if ci else 'none - '}the local gate is the "
                 f"evidence here; say plainly that remote enforcement is {'unverified' if ci else 'missing'}")
    evals = [p for p in (base / "evals").rglob("*") if p.is_file()] if (base / "evals").is_dir() else []
    runner = check_recipe(base)
    if evals:
        parts.append(f"Golden/eval dataset: {len(evals)} file(s) under evals/ - count it as proof only if a command "
                     f"here executes it and you ran it; otherwise record 'structure only, not executed'")
    parts.append("The files above: read the ones you need in ONE call (several tool calls in one message), and a "
                 "typed input's definition before building one in a test (a logged run built 71 invalid ToolCalls).")
    parts.append("A test that exposes a real bug: keep it, mark it an expected failure naming the issue you file "
                 "(pytest: @pytest.mark.xfail(strict=True, reason=\"#<n>\")), never fix product code here.")
    parts.append("The suite's isolation: prove it each run, safely - point the guard at a FAKE dev-looking target and "
                 "show it refuses (a logged checkpoint found the guard fooled by localhost vs 127.0.0.1); never at real data.")
    parts.append("The record in the fewest calls: every receipt at once - status.py quote <file> \"<words>\" [<file> "
                 "\"<words>\" ...]; write #Tests' body to a scratch file outside the repo, then ONE call writes it "
                 "and closes the phase - status.py set test filled --verdict pass|fail --section-from <file> (refused: "
                 "PRODUCT.md is put back, every gap named at once; --dry-run lists them and writes nothing; it SAVES the "
                 "project - never ask \"Save this version?\", --no-commit only when the user said not to save; `set` "
                 "prints the rest of the close). Never edit PRODUCT.md with an edit tool. Every line "
                 f"under {LONG_LINE} characters (a longer bullet is split for you), #Tests under 8 KB: the "
                 "reasoning goes in docs/tests.md, the section keeps each result, evidence line and pointer.")
    parts.append(remote_line(base))
    return "\n\n".join(parts)


def dev_check_start_text(st: Status) -> str:
    """The checkpoint's start: the milestone's tickets and their state, the gate to run on THIS checkout, and the scope
    lines to check creep against - instead of reading every rule file and the whole spine."""
    s = dev_check_state(st)
    if s is None:
        return "===== checkpoint =====\n! no TICKETS.md - nothing says which tickets make the milestone: run /tickets"
    parts = [f"===== checkpoint: {s['milestone']} on {git(st.base, 'rev-parse', '--abbrev-ref', 'HEAD')} "
             f"@ {git(st.base, 'rev-parse', '--short', 'HEAD')} ====="]
    pre = env_precheck(st.base)
    if pre:
        parts.append(pre)
    parts.append("Tickets (a PASS needs every one done AND in this checkout; anything else is a FAIL with this list):\n"
                 + "\n".join(f"  {t}: {v}" for t, v in s["tickets"]))
    # work on a branch nobody merged: a logged plain run found two ticket branches the checkpoint's list never showed
    ids = [t.lower() for t, _ in s["tickets"]]
    loose = [b.strip() for b in git(st.base, "branch", "-a", "--no-merged", "HEAD", "--format=%(refname:short)")
             .splitlines() if any(t in b.lower() for t in ids)]
    if loose:
        parts.append("Ticket branches NOT merged into this checkout (their work is not checked here - name them in "
                     "the FAIL):\n" + "\n".join(f"  {b}" for b in loose[:12]))
    parts.append("Every check runs once, whatever an earlier one found - a red one decides the verdict, never how "
                 "much is checked: the gate, the live path (/run, the observable result), each built ticket's "
                 "security DoD, and scope creep against the list below. #Dev-complete names each with its result.")
    recipe = check_recipe(st.base)
    gate = tool_file("build", "gate.py")
    if gate:
        parts.append(f"Gate - the project's full checks on THIS code, once (each ticket's own run was on its own branch; "
                     f"merged code is new code): python \"{gate.as_posix()}\" \"{recipe[0] if recipe else '<the '
                     f'project check command>'}\"")
    prod = st.base / "PRODUCT.md"
    spine = product_sections(prod.read_text(encoding="utf-8", errors="replace")) if prod.is_file() else {}
    # the live path in one call: a logged checkpoint spent ~15 calls finding how to start the app and freeing its port
    dev, port, health = dev_server(st.base, spine.get("Foundation", ""))
    server = tool_file("foundation", "devserver.py")
    if server and dev and port:
        url = health if (health or "").startswith("http") else f"http://127.0.0.1:{port}{health or '/'}"
        run_ = f"python \"{server.as_posix()}\""
        parts.append(f"Live path - one call to start, one to stop, never by hand: {run_} start --cmd \"{dev}\" --port "
                     f"{port} --health {url} · then hit the routes the built tickets add · {run_} stop --port {port}")
    plan_lines = [ln for ln in spine.get("Plan", "").splitlines() if re.search(rf"\b{s['milestone']}\b", ln)]
    if plan_lines:
        parts.append(f"#Plan lines for {s['milestone']} (its exit criteria):\n" + "\n".join(plan_lines[:12]))
    scope = spine.get("Scope", "")
    out = re.search(r"(?im)^.*\b(?:deferred|non-goals?|out[- ]of[- ]scope)\b.*$", scope)
    if out:  # the template's "Deferred" + "Non-goals" lists, to the end of the section
        parts.append("#Scope - what must NOT be built (check the code against it):\n" + scope[out.start():].strip()[:2500])
    parts.append(remote_line(st.base))
    return "\n\n".join(parts)


def next_phase(st: Status, run: str | None = None) -> dict:
    """STATE-MODEL.md §2a frontier logic, computed once, so no run re-derives it from prose."""
    notes, ui = [], st.header.get("UI", "unknown")
    states = {r[0]: r for r in st.rows["Phases"]}
    frontier, blocked_by = None, None
    progress = ticket_progress(st)
    for p in CHAIN:
        if p == "deploy":
            continue  # a bridge phase: it runs when the product must be reachable, never the frontier
        if p == "design-system" and ui == "no":
            continue
        r = states.get(p)
        if r is None:
            continue
        if p == "validate" and r[1] in ("empty", "declined"):
            continue  # optional: never the frontier, but an experiment the user started still holds (below)
        if r[1] == "running":
            if blocked_by is None:
                blocked_by = r
            continue
        if r[1] in ("empty", "declined"):
            frontier = r
            break
        if p == "build" and progress and progress["missing"]:
            frontier = r  # a milestone still has unrecorded tickets: build is not done
            break
        if p in VERIFY and r[1] == "filled" and r[4] != "pass":
            frontier = r  # a gate that failed, or whose verdict was never recorded, is not passed
            break
    for r in st.rows["Phases"]:
        if r[1] == "overridden":
            notes.append(f"override: #{r[0]} {r[5]} (since {r[2]})")
        if r[1] == "running":
            late = r[3] and r[3] < st.today
            notes.append(f"running: #{r[0]} due {r[3]}{' - OVERDUE' if late else ''}: {r[5]}")
    if frontier is None:
        line = "none - every phase in the chain is filled or overridden"
    else:
        line = f"/{frontier[0]}"
        if frontier[1] == "declined":
            line += f" (already tried {frontier[2]}: {frontier[5]})"
        elif frontier[0] == "build" and progress and progress["missing"]:
            line += (f" - {progress['milestone']}: {progress['done']} of {progress['total']} tickets recorded; not yet: "
                     f"{', '.join(progress['missing'])} (pick by TICKETS.md: its Day 1 table and coordination points)")
        elif frontier[0] in VERIFY and frontier[1] == "filled":
            if frontier[4] == "fail":
                line += f" - last verdict FAIL ({frontier[2]}): fix what it found, then re-run /{frontier[0]}"
            else:
                line += (f" - verdict not recorded: re-run /{frontier[0]}, or record its last result with "
                         f"`status.py set {frontier[0]} filled --verdict pass|fail`")
        carried = carried_bypass(st, blocked_by[0]) if blocked_by else None
        if carried and frontier[0] not in ADVISORY_RUNNING and CHAIN.index(frontier[0]) > CHAIN.index("plan"):
            line += (f" - proceeding under the override recorded at /{carried[2]} on {carried[1]} (open item "
                     f"{carried[0]}); #{blocked_by[0]} is still running, due {blocked_by[3]}. No new override needed")
        elif blocked_by and frontier[0] not in ADVISORY_RUNNING and CHAIN.index(frontier[0]) > CHAIN.index("plan"):
            line += (f" - BLOCKED: #{blocked_by[0]} is still running, due {blocked_by[3]}. To proceed, ask the user "
                     f"for a reason in their own words, then run: status.py bypass --from {frontier[0]} --gate "
                     f"{blocked_by[0]} --reason \"<their words>\"")
        elif blocked_by:
            line += f" - provisional: #{blocked_by[0]} is still running, due {blocked_by[3]}"
    if ui == "unknown" and frontier and CHAIN.index(frontier[0]) > CHAIN.index("structure"):
        notes.append("UI flag unknown: run `status.py flag --ui yes|no` so design-system is routed or skipped")
    if (st.header.get("AI product") != "no" and st.header.get("Agent", "unknown") == "unknown" and frontier
            and CHAIN.index(frontier[0]) >= CHAIN.index("architect")):
        notes.append("Agent flag unknown: ask whether the AI takes actions (orders, refunds, messages), then "
                     f"`status.py flag --agent yes|no`; yes opens {agent_rules()}")
    elif st.header.get("Agent") == "yes" and frontier:
        rules = Path(agent_rules())
        secs = [m.group(1).lower() for m in re.finditer(r"^## §([\w-]+)", rules.read_text(encoding="utf-8"), re.M)
                ] if rules.is_file() else []
        if run and run in secs:  # an order, not a condition: a logged Gemini run skipped the conditional line
            notes.append(f"Agent: yes - open now: {rules.as_posix()} §{run.capitalize()}, and apply every row of it")
        elif run:
            notes.append(f"Agent: yes - {rules.as_posix()} has no section for /{run}: nothing agent-specific to apply")
        else:
            # The phase run may not be the frontier (a re-run of an earlier phase), so name every section there is.
            notes.append(f"Agent: yes - {rules.as_posix()} has a section for " + ", ".join(f"/{s}" for s in secs)
                         + "; running one of those phases, open its section and apply it; any other phase has none")
    for p in CHAIN:
        changed = rule_changes(st, p)
        if changed:
            when = states[p][6] if len(states[p]) > 6 and states[p][6] else ""
            notes.append(f"rules changed since #{p} was filled{f' under {when}' if when else ' (version not recorded)'}"
                         f": {'; '.join(changed)}. Three choices: {UPDATE_ONE.format(p=p)}; re-run /{p} whole; or "
                         f"keep it as it is: status.py set {p} filled --note \"kept: <the user's reason>\"")
    base = getattr(st, "base", None)
    for name in (AGENT_FILES if base is not None else ()):
        f = Path(base) / name
        if f.is_file() and OLD_READ_ALL in f.read_text(encoding="utf-8", errors="replace"):
            kb = sum((Path(base) / s).stat().st_size for s in ("PRODUCT.md", "STRUCTURE.md", "DESIGN.md")
                     if (Path(base) / s).is_file()) // 1024
            notes.append(f"{name} tells every conversation to read PRODUCT.md, STRUCTURE.md and DESIGN.md whole "
                         f"({kb} KB here, re-sent on every later call): replace its \"{OLD_READ_ALL[3:]}\" block with "
                         f"\"## Read what the task needs\" from the playbook's templates/AGENTS.md")
    if base is not None and (Path(base) / ".git").exists() and git(Path(base), "status", "--porcelain", "STATUS.md", FRAG_DIR):
        # E7: an item closed after the phase's commit (it cites that commit) is left out of it
        notes.append("STATUS.md or status/ has changes that are not committed - commit them, one command each: git "
                     "add STATUS.md status, then git commit -m \"status: record what the last phase closed\"")
    if base is not None and (Path(base) / "PRODUCT.md").exists():
        for p in ("structure", "design-system", "foundation", "contracts"):
            if states.get(p, [p, "empty"])[1] == "filled" and not earlier_override(st, p):
                failed = phase_check(p, Path(base))
                if failed:
                    notes.insert(0, f"#{p}'s check fails now: {failed}. Fix it first (or re-run /{p}) - `set <this "
                                    f"phase> filled` refuses while it fails, unless the user's reason is recorded")
        # the project's committed copy is what the commit hook and CI run: a copy that differs checks something else
        copy, engine = find_in_project(Path(base), "check_structure.py"), tool_file("templates", "check_structure.py")
        if copy and engine and not engine_changed(engine) and code_hash(copy) != code_hash(engine):
            notes.append(f"{copy.relative_to(Path(base)).as_posix()} differs from the playbook's check (the commit hook "
                         f"and CI run it): copy {engine.as_posix()} over it and commit - never edit it to make it pass; "
                         f"if the formatter hook rewrites it, git add it again and commit (a formatted copy is the same "
                         f"check)")
    if run and states.get(run, [run, "empty"])[1] in ("filled", "overridden"):
        changed = rule_changes(st, run)
        notes.insert(0, f"RE-RUN: #{run} is already {states[run][1]}. The user chose this re-run by running /{run}: "
                        f"never ask whether to re-run. First compare the WHOLE section against the current rules and the "
                        f"skill's exit criteria, not only a flagged change"
                        f"{' (changed since: ' + '; '.join(changed) + ')' if changed else ''}; then ask ONE question "
                        f"listing each concrete change, the gaps marked (Recommended). Nothing differs: say so and stop. "
                        f"One decision changes: {UPDATE_ONE.format(p=run)} - not the whole phase again")
    filled = [p for p in CHAIN if states.get(p, [p, "empty"])[1] in ("filled", "overridden", "running")]
    for i, p in enumerate(CHAIN):
        if p in OPTIONAL or states.get(p, [p, "empty"])[1] not in ("empty", "declined"):
            continue
        if p == "design-system" and ui != "yes":
            continue
        later = [q for q in CHAIN[i + 1:] if q in filled and q not in OPTIONAL]
        if later:
            notes.append(f"out of order: #{later[0]} is filled but #{p} is empty")
    for r in st.rows["Open items"]:
        if not r[5]:
            notes.append(f"open item {r[0]} (from /{r[2]}, {r[1]}): {r[3]} - clears when {r[4]}")
    if st.header.get("Order", "chain order") != "chain order":
        notes.append(f"order: {st.header['Order']}")
    return {"phase": frontier[0] if frontier else None, "line": line, "notes": notes}


# ---- /playbook's start: `status.py route` ------------------------------------------------------------------
# One call answers what /playbook used to work out from prose: where the project is, the next phase, how long a
# sitting it is, whether a batch is legal, whether to show the map. Seven logged /playbook runs all started in a
# folder with no STATUS.md, where `next` printed a phase-close checklist and then refused; every run fell back to
# `ls`, and one read PRINCIPLES.md + MECHANISMS.md whole (31 KB) to route one phase.
# Size, not minutes: minutes measured on 1.36-1.47 went stale as the skills were rewritten. A phase is short when it
# asks questions and writes one PRODUCT.md section, long when it also writes, runs or reviews project files.
PHASE_SIZE = {"adopt": "short", "vision": "short", "validate": "short", "scope": "short", "plan": "short",
              "architect": "short", "learn": "short", "structure": "long", "design-system": "long",
              "foundation": "long", "contracts": "long", "tickets": "long", "build": "long", "dev-check": "long",
              "deploy": "long", "test": "long", "eval": "long", "ship": "long"}
SIZE_TEXT = {"short": "short - questions and one PRODUCT.md section",
             "long": "long - it also writes, runs or reviews project files: say to start it with room left on the "
                     "plan (a run a usage limit cuts off mid-review loses review steps)"}
# STATE-MODEL.md §2d derivation phases that MECHANISMS-ON-DEMAND.md §Batch mode may run as one session.
BATCHABLE = ("structure", "foundation", "contracts", "tickets")
# A folder holding only these is a fresh start, not a codebase for /adopt.
NOT_CODE = re.compile(r"^(?:readme|license|licence|changelog|contributing|code_of_conduct)(?:\.\w+)?$"
                      r"|^\.(?:gitignore|gitattributes|gitkeep|editorconfig)$", re.IGNORECASE)
# the playbook's own Communication rules and the sections /playbook cites, word for word
ROUTER_RULES = {"PRINCIPLES.md": ["Communication"], "MECHANISMS.md": ["Status", "Plain-language close"]}
# /playbook's map: every skill in the 2.0 order, one source - route prints it, the skill shows it, never re-types it
SKILL_MAP = (
    ("Start", "/playbook (guides you, one phase at a time) · /adopt (a project that already has code)"),
    ("Product", "/vision -> /validate (optional: only when you ask) -> /scope -> /plan"),
    ("Development", "/architect -> /structure -> /design-system (UI only) -> /foundation -> /contracts -> /tickets -> "
                    "/build -> /dev-check -> /deploy (when something ahead needs a real URL)"),
    ("Testing to learning", "/test -> /eval -> /ship -> /learn"),
    ("Anytime, not steps", "/drift-check (are we still building the vision?) · UI only: /new-component (one "
                           "component against DESIGN.md) · /frontend-audit (checks the built UI)"),
)


def skill_map_text() -> str:
    return "Skills, in order (the map):\n" + "\n".join(f"  {k}: {v}" for k, v in SKILL_MAP)


def code_files(base: Path, limit: int = 5) -> list[str]:
    """Up to `limit` files that make `base` an existing codebase (hidden folders and dependency folders skipped)."""
    found: list[str] = []
    for root, dirs, names in os.walk(base):
        dirs[:] = sorted(x for x in dirs if not x.startswith(".") and x not in SKIP_DIRS)
        for n in sorted(names):
            if n in ("PRODUCT.md", "STATUS.md") or NOT_CODE.match(n):
                continue
            found.append((Path(root) / n).relative_to(base).as_posix())
            if len(found) >= limit:
                return found
    return found


def batch_from(phase: str | None, st: "Status | None") -> list[str]:
    """The legal batch starting at `phase`: consecutive empty derivation phases, design-system (input) splits it."""
    if phase not in BATCHABLE or st is None:
        return []
    ui = st.header.get("UI", "unknown")
    run: list[str] = []
    for p in CHAIN[CHAIN.index(phase):]:
        if p == "design-system" and ui == "no":
            continue
        if p not in BATCHABLE or st.state(p) not in ("empty", "declined"):
            break
        run.append(p)
    return run if len(run) > 1 else []


def route_text(path: Path, today: str) -> str:
    base = path.resolve().parent
    out: list[str] = []
    size = lambda p: SIZE_TEXT[PHASE_SIZE[p]]  # noqa: E731
    if not path.is_file():
        prod = base / "PRODUCT.md"
        head = prod.read_text(encoding="utf-8", errors="replace")[:4000] if prod.is_file() else ""
        if any(HEADER.match(ln) for ln in head.splitlines()):
            out += ["Where: PRODUCT.md holds the old `_Last updated: ... Stage:` header and there is no STATUS.md",
                    "Next: status.py migrate (a dry run) -> show the user what it would record -> "
                    "status.py migrate --write only on their yes; then run this route again"]
        elif prod.is_file():
            out += ["Where: PRODUCT.md exists, STATUS.md does not - nothing records which sections are done",
                    f"Next: /adopt - it confirms each section with the user and records it (size: {size('adopt')})"]
        else:
            code = code_files(base)
            if code:
                out += [f"Where: existing code, no PRODUCT.md ({', '.join(code)})",
                        f"Next: /adopt - drafts PRODUCT.md from the repo and confirms it with the user "
                        f"(size: {size('adopt')}); entering at /architect or /build also works, with no spine",
                        "Map: show it - a first visit"]
            else:
                out += ["Where: a fresh start - no STATUS.md, no PRODUCT.md, no code",
                        "Next: /vision", f"Size: {size('vision')}", "Map: show it - a first visit"]
        return route_out(out)
    st = Status.load(path)
    st.today = today
    n = next_phase(st)
    done = [r[0] for r in st.rows["Phases"] if r[1] in ("filled", "overridden")]
    out.append(f"Done: {', '.join('/' + p for p in done) if done else 'nothing yet'}")
    out.append(f"Next: {n['line']}")
    if n["phase"]:
        per = " per ticket" if n["phase"] == "build" else ""
        kind = PHASE_SIZE[n["phase"]]
        if st.header.get("Agent") == "yes" and n["phase"] in agent_phases():
            kind, per = "long", per + " (the agent track adds its own section)"
        out.append(f"Size: {SIZE_TEXT[kind].replace(' - ', per + ' - ', 1)}")
    batch = batch_from(n["phase"], st)
    if batch:
        out.append(f"Batch: legal - {' + '.join('/' + p for p in batch)}: offer it beside the single phase "
                   f"(MECHANISMS-ON-DEMAND.md §Batch mode); size: long, one session for all of them")
    out.append("Map: skip it - STATUS.md exists; show it only if the user asks")
    out += [f"  - {x}" for x in n["notes"]]
    return route_out(out)


def route_out(facts: list[str]) -> str:
    """The facts come LAST: Antigravity shows only the last ~4 KB of an output, and the rules are ~4 KB - a route
    that printed Where/Next first lost exactly the lines the offer is made of."""
    return "\n".join([playbook_line(), "Rules - apply them; these ARE the rule files for /playbook:\n"
                      + router_rules_text(), "", skill_map_text(), "", *facts])


def agent_phases() -> set[str]:
    """The phases references/agent.md has a section for: an agent product runs longer there."""
    f = Path(agent_rules())
    return {m.group(1).lower() for m in re.finditer(r"^## §([\w-]+)", f.read_text(encoding="utf-8"), re.M)
            } if f.is_file() else set()


def router_rules_text() -> str:
    return "\n\n".join(f"===== {name} =====\n" + print_sections(rule_file(name), secs)
                       for name, secs in ROUTER_RULES.items())


# ---- commands ----------------------------------------------------------------------------------------------
def earlier_override(st: Status, phase: str) -> bool:
    """An open item that records the user's reason to go on while #phase's check fails."""
    return any(not o[5] and o[3].startswith(f"Override: #{phase}'s check fails") for o in st.rows["Open items"])


def replace_section(text: str, name: str, body: str) -> str:
    """`## <name>` keeps its heading line; everything up to the next `## ` becomes `body`."""
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.replace("\r\n", "\n").split("\n")
    at = next((i for i, ln in enumerate(lines) if re.match(rf"^## {re.escape(name)}\b", ln)), None)
    if at is None:
        raise Refused(f"PRODUCT.md has no `## {name}` heading to write into")
    end = next((i for i in range(at + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    new = body.replace("\r\n", "\n").strip("\n").split("\n")
    if new and re.match(rf"^## {re.escape(name)}\b", new[0]):
        new = new[1:]
    tail = [""] if end < len(lines) else []
    return eol.join(lines[:at + 1] + new + tail + lines[end:])


def split_top(text: str, marks: str) -> list[str]:
    """`text` cut after each of `marks` that is followed by a space and sits outside `code` and brackets."""
    cuts, depth, code = [], 0, False
    for i, ch in enumerate(text):
        if ch == "`":
            code = not code
        elif not code and ch in "([{":
            depth += 1
        elif not code and ch in ")]}":
            depth = max(depth - 1, 0)
        elif not code and depth == 0 and re.fullmatch(marks, ch) and text[i + 1:i + 2] == " ":
            cuts.append(i + 1)
    return [t for t in (text[i:j].strip() for i, j in zip([0] + cuts, cuts + [len(text)])) if t]


def reflow(body: str) -> tuple[str, int]:
    """A bullet over LONG_LINE wrapped into indented continuation lines at its sentence ends (outside `code`),
    every word and the label kept - the script formats, not the model: every logged /test wrote 1-2 long lines,
    and one rewrite after the warning lost a label a check needs. Evidence lines, tables and receipts stay whole."""
    out, split = [], 0
    for line in body.splitlines():
        m = re.match(r"^(\s*)- (.*)$", line)
        s_ = line.strip()
        if not m or len(s_) <= LONG_LINE or "evidence:" in s_ or s_.startswith(("|", "<!--", "- **Read")) \
                or TABLE_ROW.match(s_):
            out.append(line)
            continue
        ind, text = m.groups()
        merged: list[str] = []
        for piece in (x for x in split_top(text, "[.;]") for x in (split_top(x, "[,·]") if len(x) > LONG_LINE - 8 else [x])):
            if merged and len(merged[-1]) + 1 + len(piece) <= LONG_LINE - len(ind) - 6:
                merged[-1] += " " + piece
            else:
                merged.append(piece)
        if len(merged) < 2:
            out.append(line)
            continue
        split += 1
        # continuation lines, not sub-bullets: the field still reads as ONE paragraph (2026-10-01: the owner found
        # a logged #Vision "broken sentences" - each split sentence rendered as its own bullet)
        out += [f"{ind}- {merged[0]}"] + [f"{ind}  {x}" for x in merged[1:]]
    return "\n".join(out) + ("\n" if body.endswith("\n") else ""), split


def normalise_section(body: str, sec: str) -> str:
    """The script formats (P19): a heading naming the section is dropped (a logged Codex /vision wrote `# Vision`
    into its section file and PRODUCT.md got a nested heading); a bare `**Label:** value` line gets its "- "."""
    out = []
    for line in body.splitlines():
        h = re.match(r"^(#{1,2})\s+(.*)$", line)
        if h and heading_key(h.group(2)).startswith(sec.lower()):
            continue
        if h:
            raise Refused(f"the section file has the heading {line.strip()[:60]!r}: a `#` or `##` heading starts a new "
                          f"PRODUCT.md section - drop it, or make it `###`")
        out.append("- " + line if re.match(r"^\*\*[^*\n]+\*\*", line) else line)
    return "\n".join(out) + ("\n" if body.endswith("\n") else "")


READ_LINE = re.compile(r"(?m)^- \*\*Read \(file · date · verbatim quote\):\*\*[ \t]*(?:none\b[^\n]*)?$", re.I)


def readme_purpose(base: Path) -> str | None:
    """The README's first line of prose (its heading when it has nothing else), for the Read receipt and Step 3c."""
    f = base / "README.md"
    if not f.is_file():
        return None
    lines = [" ".join(l.split()).lstrip("-*#> ").strip() for l in f.read_text(encoding="utf-8",
                                                                             errors="replace").splitlines()]
    prose = [l for l in lines if len(l) >= 8 and '"' not in l]
    return next((l for l, raw in zip(lines, f.read_text(encoding="utf-8", errors="replace").splitlines())
                 if l in prose and not raw.lstrip().startswith("#")), prose[0] if prose else None)


def vision_bookkeeping(base: Path, body: str, today: str) -> tuple[str, str | None]:
    """/vision's close in the one call (a logged Claude /vision spent 6 calls on init, flag, git root, git status
    and reading the README, and its receipt said `none` because the README was read after `set`)."""
    purpose = readme_purpose(base)
    if purpose and READ_LINE.search(body):
        body = READ_LINE.sub(lambda m: m.group(0).split(":**")[0] + f":** README.md · {today} · \"{purpose}\"",
                             body, count=1)
    return body, purpose


def repo_facts(base: Path, purpose: str | None, readme: bool = True, saved: bool = False) -> str:
    """What the save question (and /vision's Step 3c) need, so the run opens no git or README call of its own."""
    root = git(base, "rev-parse", "--show-toplevel")
    here = base.resolve().as_posix().lower()
    if not root:
        where = "no git repository here: offer `git init` once"
    elif Path(root).resolve().as_posix().lower() == here:
        where = f"git root = this project · branch {git(base, 'branch', '--show-current') or '(none)'}"
    else:
        where = f"git root is a PARENT folder ({root}): do not commit - offer `git init` here (MECHANISMS.md §Commit)"
    # git() strips the output, so the first line may have lost its leading status column: cut by pattern, not by index
    changed = [re.sub(r"^\s*\S{1,2}\s+", "", l) for l in git(base, "status", "--porcelain",
                                                            "--untracked-files=all").splitlines()] if root else []
    changed = [c for c in changed if c != LOCK and not install_root(c)]
    save = f"  - for the save question: {where}"
    if saved:
        save = ""
    elif changed:
        # a logged Cursor /vision ran status, diff, log and a glob before committing anyway: ~600K tokens (2026-10-01).
        # One save path only: a logged /structure close also printed "git add <8 files>" here, and literal obedience
        # would have committed 8 of 53 files (2026-10-04)
        save += (f" · {len(changed)} changed file(s): {', '.join(changed[:8])}{' ...' if len(changed) > 8 else ''} · "
                 f"the save is step 4's one call - it takes every change except the playbook's install; these facts "
                 f"replace git status, diff and log: run none of them")
    if not readme:
        return save
    return save + ("\n" if save else "") + (f"  - for Step 3c: README.md says {purpose!r}" if purpose else
                   "  - for Step 3c: no README.md purpose to compare")


READ_NONE = "none - only PRODUCT.md sections, as `next` printed them"


def read_line_default(body: str) -> str:
    """/scope and /plan read PRODUCT.md through `next`, so the script writes their `Read:` line: a logged /scope close
    made 7 quote attempts (~290K tokens) hunting for a line not already in PRODUCT.md - by construction, there was
    none. A receipt the run wrote itself is kept and checked as before."""
    if READ_LINE.search(body):
        return READ_LINE.sub(lambda m: m.group(0).split(":**")[0] + f":** {READ_NONE}", body, count=1)
    if re.search(r"(?mi)^\W*\**Read \(file", body):
        return body
    return body.rstrip("\n") + f"\n- **Read (file · date · verbatim quote):** {READ_NONE}\n"


def save_commit(base: Path, message: str) -> str:
    """`set <phase> filled --commit "<line>"`: the save in the same call - a logged run spent 6-9 calls on git per
    phase (status, add, commit, a `.git/index.lock` retry), each re-sending the whole conversation."""
    root = git(base, "rev-parse", "--show-toplevel")
    if not root:
        return "not saved: no git repository here - offer `git init` once, then save"
    if Path(root).resolve().as_posix().lower() != base.resolve().as_posix().lower():
        return f"not saved: the git root is a PARENT folder ({root}) - offer `git init` here (MECHANISMS.md §Commit)"
    # never the playbook's own install (INSTALL_PATHS), even when .gitignore lost its line. An exclude that names an
    # IGNORED path makes git 2.46 exit 1 ("paths are ignored ... use -f") although nothing was forced - a live save
    # failed on every project with `.agents/` in .gitignore - so only paths git does not already ignore are excluded.
    excludes = [p for p in (LOCK, *INSTALL_PATHS) if (base / p).exists()
                and subprocess.run(["git", "check-ignore", "-q", p], cwd=base).returncode != 0]
    add = subprocess.run(["git", "add", "-A", "--", ".", *(f":(exclude){p}" for p in excludes)], cwd=base,
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    if add.returncode != 0:
        return f"not saved: git add failed - {(add.stderr or add.stdout).strip()[:200]}"
    staged = git(base, "diff", "--cached", "--name-only").splitlines()
    if not staged:
        return "nothing to save: no file changed"
    c = commit_through_hooks(base, message, staged)
    if c.returncode != 0:
        return (f"not saved: git commit failed - {hook_failure(c)} - the record is written: fix what failed, then run "
                f"this same `set ... --commit` again (no git call of your own)")
    left = sorted({r for r in (install_root(re.sub(r"^\s*\S{1,2}\s+", "", l))
                               for l in git(base, "status", "--porcelain", "--untracked-files=all").splitlines()) if r})
    return (f"saved: commit {git(base, 'rev-parse', '--short', 'HEAD')} \"{message}\" ({len(staged)} file(s): "
            f"{', '.join(staged[:8])}{' ...' if len(staged) > 8 else ''}) - no git call of your own"
            + (" - the commit hooks ran on it" if hooks_state(base)[1] else "")
            + (f"; left out the playbook's install ({', '.join(p + '/' for p in left)}) - not the project's code"
               if left else ""))


# The folders a project-level playbook install writes (install.sh --project): a logged /foundation commit carried a
# playbook upgrade under .agents/ beside the phase's work, where a reviewer reads it as project work (E12).
PLAYBOOK_PATHS = (".claude/skills/", ".claude/product-playbook/", ".agents/", ".cursor/agents/", ".codex/skills/")


def playbook_commit(base: Path, staged: list[str]) -> str:
    """Commit the staged playbook files alone, before the phase's; '' when there are none or nothing else."""
    pb = [f for f in staged if f.startswith(PLAYBOOK_PATHS)]
    if not pb or len(pb) == len(staged):
        return ""
    msg = f"chore: playbook {playbook_version()}"
    c = subprocess.run(["git", "commit", "-q", "-m", msg, "--", *pb], cwd=base, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if c.returncode != 0:  # never mixed in: leave it for its own commit
        subprocess.run(["git", "reset", "-q", "--", *pb], cwd=base, capture_output=True)
        return (f"the playbook update ({len(pb)} file(s) under {pb[0].split('/')[0]}/) is NOT in this save - its own "
                f"commit failed ({hook_failure(c)}); commit it alone: git add {pb[0].split('/')[0]}, then git commit "
                f"-m \"{msg}\"")
    return f"saved the playbook update first, on its own: commit {git(base, 'rev-parse', '--short', 'HEAD')} \"{msg}\""


def commit_through_hooks(base: Path, message: str, staged: list[str]) -> subprocess.CompletedProcess:
    """git commit; when a hook (a formatter) rewrote staged files and refused, add them and commit once more -
    the same two calls a person makes, done here so the run does not spend them."""
    run = lambda: subprocess.run(["git", "commit", "-q", "-m", message], cwd=base, capture_output=True,  # noqa: E731
                                 text=True, encoding="utf-8", errors="replace")
    c = run()
    rewritten = [f for f in git(base, "diff", "--name-only").splitlines() if f in staged]
    if c.returncode != 0 and rewritten:
        subprocess.run(["git", "add", "--", *rewritten], cwd=base, capture_output=True)
        c = run()
    return c


def hook_failure(c: subprocess.CompletedProcess) -> str:
    """The lines that say what failed (pre-commit's `Failed`, an error), not the first 200 characters of a banner."""
    lines = [l.strip() for l in (c.stdout + "\n" + c.stderr).splitlines() if l.strip()]
    keep = [l for l in lines if re.search(r"(?i)\bfailed\b|error|refus|\[FAIL\]|exit code", l)]
    return " | ".join((keep or lines)[:6])[:600]


def set_with_section(st: Status, a, today: str, prod: Path) -> str:
    """One call writes the phase's own PRODUCT.md section and records the phase - no edit tool on the spine (a
    logged Antigravity /test's two small PRODUCT.md edits each put ~90 KB into its conversation)."""
    sec = PHASE_SECTION.get(a.phase)
    src = Path(a.section_from)
    if not sec:
        raise Refused(f"--section-from: #{a.phase} writes no PRODUCT.md section")
    # the first phase starts the spine from the template here: a logged /vision spent two calls and 6 KB reading the
    # template and scripting a copy of it
    template = tool_file("templates", "PRODUCT.md")
    created = a.phase == CHAIN[0] and not prod.is_file() and template is not None
    if not (prod.is_file() or created) or not src.is_file():
        raise Refused(f"--section-from needs {prod.name} and {src} to exist")
    old = template.read_text(encoding="utf-8") if created else prod.read_text(encoding="utf-8")
    body = normalise_section(src.read_text(encoding="utf-8"), sec)
    if a.phase == "vision":
        body, a.purpose = vision_bookkeeping(prod.parent, body, today)
    elif a.phase in ("scope", "plan", "design-system") or a.phase in RELEASEOPS_GAPS:
        body = read_line_default(body)
    body, split = reflow(body)
    prod.write_text(replace_section(old, sec, body), encoding="utf-8", newline="")
    try:
        return cmd_set(st, a, today) + f"\nwrote #{sec} from {src.name}" + (
            f" into a new {prod.name} made from the playbook's template" if created else "") + (
            f" (wrapped {split} long line(s) at sentence ends, every word kept - nothing to do)" if split else "")
    except Refused:
        if created:
            prod.unlink()
        else:
            prod.write_text(old, encoding="utf-8", newline="")
        raise


def apply_flags(st: Status, ai: str | None, agent: str | None) -> None:
    if ai:
        st.header["AI product"] = ai
    if agent:
        if agent == "yes" and st.header["AI product"] == "no":
            raise Refused("an agent is an AI product: --ai yes --agent yes")
        st.header["Agent"] = agent
        if agent == "yes":
            st.header["AI product"] = "yes"


def cmd_set(st: Status, a, today: str) -> str:
    r = st.phase(a.phase)
    old, new = r[1], a.state
    if new not in STATES:
        raise Refused(f"unknown state {new!r}; the states are: {', '.join(STATES)}")
    if (old, new) not in LEGAL:
        why = {("filled", "declined"): "a phase that ran does not un-run; re-run it (filled -> filled)",
               ("filled", "running"): "a closed gate does not reopen into 'still measuring'; a new experiment "
                                      "over a filled section is a re-run (filled -> filled)"}.get((old, new), "")
        raise Refused(f"#{a.phase}: {old} -> {new} is not a legal transition (STATE-MODEL.md §2b). {why}".strip())
    due, note, verdict = "", "", ""
    if a.verdict and not (a.phase in VERIFY and new == "filled"):
        raise Refused(f"--verdict belongs to a filled verification phase ({', '.join(sorted(VERIFY))}) only")
    if a.phase in VERIFY and new == "filled":
        if a.verdict not in ("pass", "fail"):
            raise Refused(f"#{a.phase} is a verification gate: filled needs --verdict pass or --verdict fail - "
                          f"a written section is not a passed gate")
        verdict = a.verdict
        if a.phase == "dev-check" and getattr(st, "base", None) is not None:
            gaps = dev_check_close_gaps(st, verdict)
            if gaps and getattr(a, "dry_run", False):
                raise DryRun(f"{len(gaps)} gap(s) the record call would refuse:\n  - " + "\n  - ".join(gaps))
            if gaps:
                raise Refused(f"dev-check: {len(gaps)} problem(s), every one at once - fix them all, then run this "
                              f"`set` again:\n  - " + "\n  - ".join(gaps))
        prod_ = getattr(st, "base", Path(".")) / "PRODUCT.md"
        if a.phase == "test" and getattr(st, "base", None) is not None:  # every tool: the same record test
            gaps = tests_gaps(st, verdict)
            if gaps and prod_.exists():  # with the section's own problems, so one refusal names them all
                text_ = prod_.read_text(encoding="utf-8")
                gaps += receipt_problems(text_, prod_.resolve().parent, "Tests") + \
                    evidence_problems(text_, prod_.resolve().parent, "Tests")
            if gaps and getattr(a, "dry_run", False):
                raise DryRun(f"{len(dict.fromkeys(gaps))} gap(s) the record call would refuse:\n  - "
                             + "\n  - ".join(dict.fromkeys(gaps)))
            if gaps:
                raise Refused("test not recorded:\n  - " + "\n  - ".join(dict.fromkeys(gaps)))
    if new == "declined":
        if not (a.reason and a.gate):
            raise Refused("declined needs --reason (what was missing) and --gate (the phase to run first)")
        note = f"Not run: {capped('reason', a.reason)} — run /{a.gate.lstrip('/')} first"
    elif new == "overridden":
        if not (a.reason and a.gate):
            raise Refused("overridden needs --reason (the user's words) and --gate (the gate bypassed)")
        note = f"Override: {capped('reason', a.reason)} — bypassed /{a.gate.lstrip('/')}"
    elif new == "running":
        if not (a.due and a.reason):
            raise Refused("running needs --due YYYY-MM-DD and --reason (what is being measured)")
        due = need_date(a.due, "--due")
        note = capped("reason", a.reason)
    elif a.note:
        note = capped("note", a.note)
    if old == "running" and new == "filled":
        # A running experiment closes on its measured result, never on a phase that wrote its fields and moved on.
        if not a.note:
            raise Refused(f"#{a.phase}: running -> filled needs --note (the measured result against the bar); "
                          f"while the result is still to come, the state stays running")
        prod = getattr(st, "base", Path(".")) / "PRODUCT.md"
        sec = PHASE_SECTION.get(a.phase)
        if sec and prod.exists() and "PENDING" in product_sections(prod.read_text(encoding="utf-8")).get(sec, ""):
            raise Refused(f"#{a.phase}: PRODUCT.md#{sec} still reads PENDING - record the measured result and "
                          f"verdict there first; until then the state stays running")
    prod = getattr(st, "base", Path(".")) / "PRODUCT.md"
    sec = PHASE_SECTION.get(a.phase)
    if new in ("filled", "running") and sec and prod.exists():
        bad = receipt_problems(prod.read_text(encoding="utf-8"), prod.resolve().parent, sec)
        if new == "filled":
            bad += evidence_problems(prod.read_text(encoding="utf-8"), prod.resolve().parent, sec)
        if a.phase == "architect":
            body = product_sections(prod.read_text(encoding="utf-8")).get(sec, "")
            bad += [f"provenance {m!r} is not one of the two values (user-chosen · default taken, not "
                    f"user-chosen): a default the user did not pick is never 'confirmed'"
                    for m in sorted(set(THIRD_PROVENANCE.findall(body)))]
            if st.header.get("AI product") == "yes":
                bad += model_age_problems(body, today)
            if new == "filled" and not (a.note or "").lower().startswith(("adopted", "kept:")):
                pending = getattr(a, "dry_run", False) and not (prod.resolve().parent / ARCH_DOC).is_file()
                bad += architect_gaps(prod.resolve().parent, st, doc_pending=pending)
                a.dry_note = arch_docs_pending(st.header.get("Agent") == "yes") if pending else ""
        if a.phase == "vision" and new == "filled" and not (a.note or "").lower().startswith("adopted"):
            bad += vision_gaps(prod.resolve().parent, st.header)
        if a.phase == "scope" and new == "filled" and not (a.note or "").lower().startswith("adopted"):
            bad += scope_gaps(prod.resolve().parent, st)
        if a.phase == "validate" and getattr(a, "section_from", None) and not (a.note or "").lower().startswith(
                "adopted"):
            bad += validate_gaps(prod.resolve().parent, st, new)
        if a.phase == "plan" and new == "filled" and not (a.note or "").lower().startswith("adopted"):
            bad += plan_gaps(prod.resolve().parent, st)
        if a.phase == "structure" and new == "filled" and not (a.note or "").lower().startswith("adopted"):
            bad += structure_gaps(prod.resolve().parent, st)
        if a.phase == "design-system" and new == "filled" and not (a.note or "").lower().startswith("adopted"):
            bad += design_record_gaps(prod.resolve().parent, st, not getattr(a, "dry_run", False), today)
            a.checked = {"design-system"}  # its phase_check ran inside: the audit once, not twice (~3 s each)
        if a.phase == "foundation" and new == "filled" and not (a.note or "").lower().startswith(("adopted", "kept:")):
            bad += earlier_check_gaps(st, a.phase, prod.resolve().parent)  # every problem in ONE list (P20)
            bad += foundation_close_gaps(prod.resolve().parent, st)
            a.checked = set(CHAIN[:CHAIN.index(a.phase) + 1])
        if a.phase == "contracts" and new == "filled" and not (a.note or "").lower().startswith(("adopted", "kept:")):
            # one refusal: an earlier gate and the record's own gaps together (they were three rounds)
            pending = getattr(a, "dry_run", False) and not (prod.resolve().parent / CONTRACTS_DOC).is_file()
            bad += earlier_gate_gaps(st, "contracts", prod.resolve().parent) + contracts_gaps(
                prod.resolve().parent, close=True, doc_pending=pending)
            a.dry_note = CONTRACTS_DOC_PENDING if pending else ""
        if a.phase in RELEASEOPS_GAPS and new == "filled" and not (a.note or "").lower().startswith(("adopted",
                                                                                                    "kept:")):
            bad += RELEASEOPS_GAPS[a.phase](prod.resolve().parent, st, a)
        if bad and getattr(a, "dry_run", False):
            raise DryRun(f"{len(dict.fromkeys(bad))} gap(s) the record call would refuse:\n"
                         + "\n".join(f"  - {g}" for g in dict.fromkeys(bad)) + getattr(a, "dry_note", ""))
        if bad:
            raise Refused(f"#{a.phase}: " + "; ".join(dict.fromkeys(bad)))
    if a.phase == "validate" and new == "overridden" and prod.exists() and getattr(a, "section_from", None):
        bad = validate_gaps(prod.resolve().parent, st, new)  # an override keeps every field (§Declined runs)
        if bad and getattr(a, "dry_run", False):
            raise DryRun(f"{len(bad)} gap(s) the record call would refuse:\n" + "\n".join(f"  - {g}" for g in bad))
        if bad:
            raise Refused("#validate: " + "; ".join(bad))
    if a.phase == "tickets" and new == "filled" and prod.exists():
        # /tickets writes no spine section: its record is docs/issues/*.md + TICKETS.md, checked here so --dry-run
        # lists it and the refusal puts every problem on its own line (phase_check joined them into one)
        bad = tickets_gaps(prod.resolve().parent)
        if bad and getattr(a, "dry_run", False):
            raise DryRun(f"{len(bad)} gap(s) the record call would refuse:\n" + "\n".join(f"  - {g}" for g in bad))
        if bad:
            raise Refused(f"#tickets: {len(bad)} problem(s), every one at once - fix them all, then run this `set` "
                          f"again:\n  - " + "\n  - ".join(bad))
    if new == "filled" and prod.exists():
        # An earlier gate that fails now is not waved through by a later phase closing: a logged Gemini run was told
        # "#foundation's check fails now ... fix it before this phase" by `next`, and filled /contracts anyway.
        base = prod.resolve().parent
        for p in CHAIN[:CHAIN.index(a.phase)]:
            if st.state(p) != "filled" or earlier_override(st, p) or p in getattr(a, "checked", ()):
                continue
            failed = phase_check(p, base)
            if failed:
                raise Refused(f"#{a.phase}: #{p}'s check fails now, so this phase cannot close on it - {failed}. Fix "
                              f"it, or record the user's reason: status.py open --from {a.phase} --what \"Override: "
                              f"#{p}'s check fails - <the user's own words>\" --clears \"#{p}'s check passes\"")
        failed = None if a.phase in getattr(a, "checked", ()) else phase_check(a.phase, base)
        if failed:
            raise Refused(f"#{a.phase}: its own check fails, so it is not done - {failed}")
    if getattr(a, "dry_run", False):
        raise DryRun(f"no gap: `set {a.phase} {new}` without --dry-run records it" + getattr(a, "dry_note", ""))
    r[1:6] = [new, today, due, verdict, note]
    if new in ("filled", "running"):
        r[6] = playbook_version()  # the rules this section was written under (RULE_CHANGES)
    closed = 0
    if new in ("filled", "overridden"):  # a bypassed gate that is now met or deliberately skipped is settled
        for o in st.rows["Open items"]:
            if not o[5] and o[4] == bypass_clears(a.phase):
                o[5] = f"{today}: /{a.phase} {new}"
                closed += 1
    msg = f"#{a.phase}: {old} -> {new}" + (f"; closed {closed} bypass item(s)" if closed else "")
    prod = getattr(st, "base", Path(".")) / "PRODUCT.md"
    sec = PHASE_SECTION.get(a.phase)
    if new in ("filled", "running") and sec and prod.exists():
        text = prod.read_text(encoding="utf-8")
        msg += "\n  " + record_sizes(text, prod.resolve().parent, sec)
        warns = long_lines(text, sec) + big_sections(text, sec)
        if new == "filled" and a.phase == "architect":
            warns += architect_warnings(prod.resolve().parent, st)
        if new == "filled" and a.phase == "contracts":
            warns += contracts_warnings(prod.resolve().parent)
        if new == "filled" and a.phase in RELEASEOPS_WARN:
            warns += RELEASEOPS_WARN[a.phase](prod.resolve().parent)
        msg += "".join(f"\n  ! {w}" for w in warns)
        if warns:  # a logged Codex /vision edited and re-ran `set` 4 times to clear one (293K tokens)
            msg += ("\n  (a warning, not a refusal: the record is saved as written - never re-run `set` for it; "
                    "mention it in the close)")
    return msg


def handoff_card(st: Status, after: str | None = None) -> str:
    """A1: the last lines of every phase close, word for word in the tool's own command spelling (a logged run told
    an Antigravity user to type /product-playbook:contracts, which that tool does not have)."""
    n = next_phase(st)
    if n["phase"] is None and after == "learn":  # the chain is done: the next cycle starts at /scope (#284)
        n["phase"] = "scope"
    lines = []
    still = [o for o in st.rows["Open items"] if not o[5]]
    if still:  # a logged run spent 3 calls finding the close syntax, then retried it
        lines.append("Open items - close each one this phase settled, one command each (plain words, up to "
                     f"{CAP['how']} characters): status.py close <n> --how \"<how it was settled>\"")
        lines += [f"  {o[0]}: {o[3][:110]} - clears when {o[4][:80]}" for o in still]
    fail_next = dev_check_fail_handoff(st) if n["phase"] in ("dev-check", "build") else None
    if fail_next:
        lines.append(fail_next)
    elif n["phase"]:
        lines.append(f"Open a NEW conversation and type: {skill_command(n['phase'])} - nothing is lost: it is all in "
                     f"PRODUCT.md, STATUS.md and git, and this conversation would be re-sent on every call of the "
                     f"next phase.")
    sc = session_costs()
    if sc is not None and st.base is not None and sc.project_log_dir(Path(st.base)).is_dir():
        lines.append("Cost: Claude Code writes this conversation's own total when it ends; `next` in the new "
                     "conversation prints it.")
    return "\n".join(lines)


# A6: a warning, never a refusal (a byte cap trims answers instead of moving reasoning, #200). A logged agent test's
# PRODUCT.md reached 61 KB with #Architecture at 13 KB, and every phase that reads a section pays for all of it.
SECTION_KB = 8


def big_sections(text: str, only: str | None = None) -> list[str]:
    out = []
    for sec, body in product_sections(text).items():
        kb = len(body.encode("utf-8")) / 1024
        if (only and sec != only) or sec in LOG_SECTIONS or kb <= SECTION_KB:
            continue
        m = DETAIL.search(body)
        home = f"`{m.group(1)}`" if m else "its companion file (docs/, docs/adr/, STRUCTURE.md, DESIGN.md)"
        # the signal names no number: "over 8 KB" read as a cap beside the template's "no byte cap - never trim to a
        # number" (a logged self-review, 2026-10-04); SECTION_KB only decides when the signal prints
        out.append(f"PRODUCT.md#{sec} is {kb:.1f} KB - a size signal, not a cap (never trim a decision "
                   f"to a number): move the reasoning to {home} and keep each decision, evidence line and pointer here "
                   f"(MECHANISMS-ON-DEMAND.md §Section is a record)")
    return out


DETAIL = re.compile(r"\*\*Detail:\*\*\s*`([^`]+\.md)`")


def record_sizes(text: str, base: Path, sec: str) -> str:
    """The one line MECHANISMS-ON-DEMAND.md §Section is a record asks a phase to report, measured here so no run
    measures by hand: the section, PRODUCT.md, the companion, and how many Read quotes were checked."""
    kb = lambda s: f"{len(s.encode('utf-8')) / 1024:.1f}KB"  # noqa: E731
    body = product_sections(text).get(sec, "")
    parts = [f"#{sec} {kb(body)}", f"PRODUCT.md {kb(text)}"]
    m = DETAIL.search(body)
    if m and (base / m.group(1)).is_file():
        parts.append(f"{m.group(1)} {kb((base / m.group(1)).read_text(encoding='utf-8'))}")
    quotes = sum(len(RECEIPT.findall(f.group(1))) for f in READ_FIELD.finditer(body + "\n"))
    return "size: " + " · ".join(parts) + f" · Read quotes checked: {quotes}, all found once"


def bypass_clears(gate: str) -> str:
    return f"/{gate} is filled"


def carried_bypass(st: Status, gate: str) -> list[str] | None:
    """An open override of a RUNNING gate carries to every later phase until the gate is filled or its due date
    passes (STATE-MODEL.md §2a): the owner answers once, and `next` still shows it on every run."""
    r = next((p for p in st.rows["Phases"] if p[0] == gate), None)
    if r is None or r[1] != "running" or (r[3] and r[3] < st.today):
        return None
    return next((o for o in st.rows["Open items"]
                 if not o[5] and o[3].startswith(f"Override: bypassed /{gate} ")), None)


def cmd_bypass(st: Status, a, today: str) -> str:
    """Proceeding in THIS phase while an earlier gate is unmet (STATE-MODEL.md §2h). The earlier phase stays
    owed and `next` keeps routing to it; the bypass is surfaced on every run until that phase is filled."""
    frm, gate = a.frm.lstrip("/"), a.gate.lstrip("/")
    st.phase(frm)
    if st.state(gate) in ("filled", "overridden"):
        raise Refused(f"#{gate} is {st.state(gate)} - its gate is met, there is nothing to bypass")
    carried = carried_bypass(st, gate)
    if carried:
        return (f"already covered: open item {carried[0]} (the override recorded at /{carried[2]} on {carried[1]}) "
                f"carries until #{gate} is filled or its due date passes - nothing new recorded")
    n = new_open_id(st)
    st.rows["Open items"].append([n, today, frm, f"Override: bypassed /{gate} — {capped('reason', a.reason)}",
                                  bypass_clears(gate), ""])
    return f"open item {n}: /{frm} proceeds with /{gate} bypassed"


RULES_MARK = "playbook-rules"
REVIEW_HEADING = re.compile(r"^#{2,3} [^\n]*\breview", re.I | re.M)
REVIEWED_SOURCE = SOURCE | {".html", ".sql", ".vue", ".svelte", ".go", ".rs", ".rb", ".java", ".kt"}


def git_dir(base: Path) -> Path | None:
    d = git(base, "rev-parse", "--git-dir")
    return (base / d) if d else None


def mark_rules_read(base: Path, phase: str, today: str) -> None:
    """`rules <phase>` leaves a dated mark inside .git (never committed): a logged Gemini build never ran it."""
    d = git_dir(base)
    if d:
        (d / RULES_MARK).mkdir(exist_ok=True)
        (d / RULES_MARK / phase).write_text(today, encoding="utf-8")


CLAUDE_ONLY_REVIEW = re.compile(r"/(?:code|security)-review\b")
REVIEW_ROUTES = ("helper agent", "another tool", "self-review", "by hand")
# fix 1: the question a self-review needs is written HERE, never by the model. A logged Gemini build wrote its own
# "(Recommended) Approve self-review" question, recorded its option text as the user's words, and shipped the
# same 3 HIGH holes as the round before. The safe choice is the recommended one.
SELF_REVIEW_QUESTION = (
    "Only I reviewed my own security work on {tid}; an independent review catches what a self-review misses. "
    "(1) Run an independent security review first (Recommended): open a different AI coding tool you have (a "
    "different model catches more) on branch "
    "{branch} and run its security review over `git merge-base HEAD main`..HEAD. "
    "(2) Accept my self-review anyway: type why, in your own words.")
OPTION_LABEL = re.compile(r"(?i)\(recommended\)|approve self-review|^\s*(?:approve|approved|yes|ok|option\s*\d|\(?\d\)?)\b")
NEW_PUBLIC = re.compile(r"^\+(?:async\s+def|def|class)\s+([A-Za-z]\w*)"
                        r"|^\+([A-Za-z]\w*)\s*=\s*[A-Za-z_][\w.]*\("
                        r"|^\+export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const)\s+([A-Za-z]\w*)", re.M)


def playbook_tool() -> str:
    """The tool a copy install serves (install.sh writes TOOL beside this script); the plugin route is Claude Code."""
    f = Path(__file__).resolve().parent / "TOOL"
    return f.read_text(encoding="utf-8").strip().lower() if f.is_file() else "claude"


def test_engine_mismatch(base: Path) -> tuple[str, list[str], bool] | None:
    """E4 / DB1: #Architecture's server database against SQLite in the test setup - (engine, files, the user's
    override recorded in #Foundation), or None. A logged Gemini build's tests passed on SQLite with a timestamp
    Postgres rejects."""
    product = base / "PRODUCT.md"
    secs = product_sections(product.read_text(encoding="utf-8")) if product.is_file() else {}
    arch, found = secs.get("Architecture", ""), secs.get("Foundation", "")
    # the chosen engine, not one named as a rejected alternative or a superseded choice
    arch = "\n".join(l for l in arch.splitlines()
                     if not re.search(r"(?i)superseded|rejected|instead of|not chosen|alternative|ruled out", l))
    engine = SERVER_DBS.search(arch)
    if not engine:
        return None
    places = [base / ".env.example"] + [p for p in project_files(base) if p.name in (
        "conftest.py", "pytest.ini", "vitest.config.ts", "jest.config.js") or ".github/workflows" in p.as_posix()]
    lite = [p.relative_to(base).as_posix() for p in places if p.is_file()
            and re.search(r"(?i)sqlite", p.read_text(encoding="utf-8", errors="replace"))]
    return (engine.group(1), lite, bool(ENGINE_OVERRIDE.search(found))) if lite else None


# The user's override of E4 is a line about the test engine. Not any "override": every honest #Foundation says "no
# override in any environment" about the placeholder guard (the exit criterion asks for it), and two logged records
# that did would have switched E4 off.
ENGINE_OVERRIDE = re.compile(r"(?im)^(?!.*\bno override\b)(?=.*\boverride\b).*\b(?:sqlite|test (?:engine|datastore|"
                             r"database))\b")


def unwired(base: Path, mb: str, code: list[str]) -> list[str]:
    """LP1: the new public names this branch adds (top-level def/class/assignment, JS exports), when NOT ONE of
    them is used outside its own module and tests - a logged Gemini build shipped an audit service nothing calls,
    and its ticket's demo could never happen. Empty when one is used, or when the branch adds none."""
    names: dict[str, str] = {}
    for f in code:
        for m in NEW_PUBLIC.finditer(git(base, "diff", "-U0", f"{mb}...HEAD", "--", f)):
            names.setdefault(next(g for g in m.groups() if g), f)
    if not names:
        return []
    others = [p for p in project_files(base, SOURCE) if not is_test(p.relative_to(base).as_posix())]
    for name, f in names.items():
        parts = Path(f).parts
        home = Path(*parts[:2]) if len(parts) > 2 else Path(f).parent
        for p in others:
            rel = p.relative_to(base)
            if rel.parts[:len(home.parts)] == home.parts and home.parts:
                continue
            if re.search(rf"\b{re.escape(name)}\b", p.read_text(encoding="utf-8", errors="replace")):
                return []
    return sorted(names)


# doc-only = cannot change a check's result: only the run's own records - the feature doc, the status record, the
# changelog. Any other file, Markdown too, may be a check's input (check_structure.py reads STRUCTURE.md, the UI
# audit DESIGN.md, a project's `just check` diffed docs/contracts/openapi.json): unknown means re-run
DOC_ONLY = re.compile(r"(?i)^docs/features/[^/]+\.md$|^STATUS\.md$|^status/|^CHANGELOG|^\.status\.lock$")  # the lock: status.py's own
# a finding row: severity as a whole cell in ANY column (a logged lean build's reviewer put it second, and a real
# review was refused as "no findings table")
SEVERITY_ROW = re.compile(r"^\|(?:[^|\n]*\|)*?[ \t]*\**(?:HIGH|MEDIUM|LOW|CRITICAL|INFO|NIT|UNRATED)\**[ \t]*\|", re.I | re.M)
REVIEW_COUNT = re.compile(r"(?i)\bR1\b[^·|]*?\b(\d+)\s+findings?\b|\bR1\b[^·|]*?\b(clean)\b")
DEMO_ENTRY = re.compile(r"(?:GET|POST|PUT|PATCH|DELETE)\s+(/[\w/{}:.-]+)|`(/(?:api|v\d)[\w/{}:.-]*)`"
                        r"|python\s+-m\s+([\w.]+)")
SECURITY_TICKET = re.compile(r"(?i)\b(auth\w*|session token|tenant|permission|refund|payment|money|secret|"
                             r"encrypt\w*|password|oauth|access token|offline token|pii|personal data|"
                             r"webhook|upload|credential\w*|signature|csrf|cors)\b")
VERIFICATION = re.compile(r"(?im)^#{2,3} .*verification command.*$\s*```[^\n]*\n(.*?)```", re.S)


def ticket_verification(spec: str) -> list[str]:
    """The ticket file's own Verification Command lines (what proves THIS ticket, not the project)."""
    m = VERIFICATION.search(spec)
    return [l.strip() for l in m.group(1).splitlines() if l.strip() and not l.strip().startswith("#")] if m else []


def check_recipe(base: Path) -> tuple[str, re.Pattern] | None:
    """The project's own full check command, when it has one: the DoD says it is green (R3-5)."""
    for name in ("justfile", "Justfile", ".justfile"):
        f = base / name
        if f.is_file() and re.search(r"^check(?:\s+[^:\n=]*)?:(?!=)", f.read_text(encoding="utf-8", errors="replace"), re.M):
            return "just check", re.compile(r"\bjust\s+check\b")
    f = base / "Makefile"
    if f.is_file() and re.search(r"^check\s*:", f.read_text(encoding="utf-8", errors="replace"), re.M):
        return "make check", re.compile(r"\bmake\s+check\b")
    f = base / "package.json"
    if f.is_file():
        try:
            if "check" in (json.loads(f.read_text(encoding="utf-8")).get("scripts") or {}):
                return "npm run check", re.compile(r"\b(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?check\b")
        except ValueError:
            pass
    return None


def worktree_tree(base: Path, d: Path) -> str:
    """The working tree as a git tree id (tracked + untracked, ignored left out), built in a scratch index inside
    .git - the same id gate.py records for the files it checked. "" when git can't."""
    idx = d / "playbook-gate" / "tree.index"
    try:
        idx.parent.mkdir(parents=True, exist_ok=True)
        if (d / "index").is_file():
            shutil.copyfile(d / "index", idx)
        elif idx.exists():
            idx.unlink()
    except OSError:
        return ""
    env = {**os.environ, "GIT_INDEX_FILE": str(idx.resolve())}
    if subprocess.run(["git", "add", "-A"], cwd=base, env=env, capture_output=True).returncode:
        return ""
    r = subprocess.run(["git", "write-tree"], cwd=base, env=env, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def only_section_changed(base: Path, tree: str, name: str) -> bool:
    """PRODUCT.md differs from the gated tree in its `## <name>` section alone - the phase's own record, which the
    phase writes after its gate (`set <phase> filled --section-from`); any other section may be a check's input."""
    f = base / "PRODUCT.md"
    if not f.is_file():
        return False
    then = git(base, "show", f"{tree}:PRODUCT.md").replace("\r\n", "\n")
    now = f.read_text(encoding="utf-8").replace("\r\n", "\n").strip()

    def rest(t: str) -> tuple[str, dict]:
        head = t.split("\n## ", 1)[0].strip()
        secs = {k: v.strip() for k, v in product_sections(t).items() if k != name}
        return head, secs
    return bool(then) and rest(then) == rest(now)


# the phase's own companion doc (tools/check.py COMPANION, keyed by its #section): its record like its own section,
# written after the gate - a logged /test edited docs/tests.md after it and its pass was voided
OWN_COMPANION = {"Vision": "docs/vision.md", "Validation": "docs/validation.md", "Scope": "docs/scope.md",
                 "Plan": "docs/plan.md", "Contracts": "docs/contracts.md", "Tests": "docs/tests.md",
                 "Evaluation": "docs/evaluation.md", "Learnings": "docs/learnings.md"}


def final_gate_gap(base: Path, d: Path, branch: str, own: str | None = None) -> tuple[str | None, list[dict]]:
    """R3-5 + the close gate as code: a passing gate.py run on this branch over the final files - the exact files
    it recorded (committed since or not) differ from these in docs/status only; an older record without them needs
    its commit, clean - with the project's check recipe when it has one. `own`: the phase's own PRODUCT.md section,
    which it writes after the gate."""
    f = d / "playbook-gate" / "results.jsonl"
    runs = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()] if f.is_file() else []
    recipe = check_recipe(base)
    cur: list[str] = []
    mine = OWN_COMPANION.get(own or "")

    def stale(r: dict) -> list[str] | None:
        """The files changed since run r that a check could read; None when r cannot be compared."""
        if r.get("tree"):
            if not cur:
                cur.append(worktree_tree(base, d))
            if not cur[0]:
                return None
            bad = [n for n in git(base, "diff", "--name-only", r["tree"], cur[0]).splitlines()
                   if n and not DOC_ONLY.search(n) and n != mine]
            if own and "PRODUCT.md" in bad and only_section_changed(base, r["tree"], own):
                bad.remove("PRODUCT.md")
            return bad
        if not git(base, "rev-parse", "--verify", "--quiet", r["head"]):
            return None
        changed = git(base, "diff", "--name-only", r["head"], "HEAD").splitlines()
        return sorted({n for n in [*r.get("dirty", []), *changed] if n and not DOC_ONLY.search(n) and n != mine})

    def final(r: dict) -> bool:
        return bool(r.get("passed") and r.get("branch") == branch and r.get("head")) and stale(r) == []
    good = [r for r in runs if final(r) and (not recipe or any(recipe[1].search(c) for c in r.get("commands", [])))]
    if good:
        return None, good
    what = f" that includes the project's check recipe (`{recipe[0]}`)" if recipe else ""
    # name what changed since the latest pass: a logged /test, told nothing, guessed "the gate missed untracked files"
    # (false - the tree holds them) and re-ran the full gate
    last = next((r for r in reversed(runs) if r.get("passed") and r.get("branch") == branch and r.get("head")), None)
    moved = stale(last) if last else None
    since = (f"; changed since the latest passing gate: {', '.join(moved[:12])}{' ...' if len(moved) > 12 else ''}"
             if moved else "")
    keep = f", {mine}" if mine else ""
    return (f"no passing gate.py run on {branch} over the final code{what}{since} - commit the last code change, then "
            f"run the gate once more (docs/features/, STATUS.md{keep} and this phase's own section may change after "
            f"it; any other file may not)"), []


def review_count_gap(doc: str, review_text: str, claim: str) -> str | None:
    """R3-4: the row's finding count is the Review table's. A logged Gemini build recorded "R1 0 findings" while its
    feature doc listed 2."""
    m = REVIEW_COUNT.search(claim)
    rows = len(SEVERITY_ROW.findall(review_text))
    if not rows and not re.search(r"\bCLEAN\b", review_text):
        return (f"{doc} §Review has no findings table and no CLEAN: a review that returned nothing did not run - run "
                f"it again (a review that dies twice: STOP and tell the user)")
    if m:
        said = 0 if m.group(2) else int(m.group(1))
        if said != rows:
            return (f"--review says R1 found {said}, the {doc} §Review table has {rows} finding row(s) - the record "
                    f"and the table must agree")
    return None


def build_ticket_gaps(base: Path, a, today: str, st: "Status | None" = None) -> tuple[list[str], list[str]]:
    """What a ticket row needs the repo to show, for every model (a logged Gemini build recorded "R1 pass 0
    findings" after one `git diff`, never ran `rules build`, and merged its branch into main itself). Returns the
    refusals and the notes the run repeats to the user."""
    doc = a.doc
    d = git_dir(base)
    if d is None:
        return [], []
    gaps, notes = [], []
    tool = playbook_tool()
    review = a.review or ""
    if tool != "claude":  # RV3 + RV4: the record and the user hear which review really ran on this tool
        claimed = CLAUDE_ONLY_REVIEW.search(review)
        if claimed:
            gaps.append(f"--review names {claimed.group(0)}, a Claude Code command {tool} does not have: name the "
                        f"route that ran - {' · '.join(REVIEW_ROUTES)} (CAPABILITIES.md §Code review)")
        elif not any(r in review.lower() for r in REVIEW_ROUTES):
            gaps.append(f"--review does not say which review ran on {tool}: {' · '.join(REVIEW_ROUTES)} "
                        f"(CAPABILITIES.md §Code review)")
        notes.append(f"Tell the user in the close, under What I skipped or couldn't do, in plain words which review "
                     f"ran on {tool} - e.g. 'this tool has no review command, so a second agent reviewed the code' or "
                     f"'no second agent was available, so I reviewed my own code; a separate review would be "
                     f"stronger'. Never name a Claude Code command.")
    mark = d / RULES_MARK / "build"
    if not mark.is_file() or mark.read_text(encoding="utf-8").strip() != today:
        gaps.append("the start (`status.py next --phase build --ticket <id>`, or `status.py rules build`) has not run "
                    "today in this checkout - run it and apply its rules; "
                    "the ticket is recorded after them, never instead")
    branch = git(base, "rev-parse", "--abbrev-ref", "HEAD")
    default = next((b for b in ("main", "master") if git(base, "rev-parse", "--verify", "--quiet", b)), "")
    if branch in ("main", "master", "HEAD"):
        gaps.append(f"HEAD is on {branch}: record the ticket on its ticket branch, before any merge - /build never "
                    "merges; /ship does, after its own review")
        return gaps, notes
    changed, mb = [], ""
    if default:
        mb = git(base, "merge-base", "HEAD", default)
        names = git(base, "diff", "--name-only", f"{mb}...HEAD") if mb else ""
        changed = [n for n in names.splitlines() if Path(n).suffix in REVIEWED_SOURCE and not is_test(n)]
        # /build never writes the spine: every parallel branch that edits PRODUCT.md collides at merge, a section
        # belongs to the phase that owns it, and a logged Gemini build wrote its own override into #Foundation
        spine = set((names + "\n" + git(base, "diff", "--name-only", mb)).splitlines()) if mb else set()
        if "PRODUCT.md" in spine:
            gaps.append(f"this branch changed PRODUCT.md - /build never writes the spine: put it back "
                        f"(git checkout {mb[:9]} -- PRODUCT.md) and record what should change as an open item for the "
                        f"phase that owns it: status.py open --from build --what \"#<Section>: <the change> - update "
                        f"with /<phase>\" --clears \"/<phase> updated\"")
    # LP1: the wires were cut and every cut went red, on this branch - or the row says why there is none to cut
    runs = d / "playbook-wirecut" / "results.jsonl"
    cut = [json.loads(l) for l in runs.read_text(encoding="utf-8").splitlines() if l.strip()] if runs.is_file() else []
    lean = playbook_mode("build", base) == "lean"  # the lean path: no cuts, no wiring proof, no per-file review list
    if not any(r.get("branch") == branch and r.get("total", 0) >= 1 and r.get("red") == r.get("total") for r in cut) \
            and not a.no_cuts and not lean:
        gaps.append(f"no wirecut.py run on {branch} with every cut RED - cut the wires this ticket connects "
                    f"(commands/build/wirecut.py <cuts.json>), or --no-cuts \"<why there is no wire to cut>\"")
    loose = unwired(base, mb, [n for n in changed if Path(n).suffix in SOURCE]) if mb else []
    if loose and not a.not_wired and not lean:
        gaps.append(f"nothing outside its own module uses what this branch adds ({', '.join(loose[:5])}): wire it "
                    f"into the path the ticket's demo runs, or --not-wired \"<why, and which ticket wires it>\"")
    # DB1: the suite ran on the engine #Architecture chose, or the user chose otherwise and hears the risk
    mismatch = test_engine_mismatch(base)
    if mismatch:
        engine, files, overridden = mismatch
        # R3-1: an override the build wrote for itself does not count - a logged Gemini build added "(Override: ...)"
        # to #Foundation on its ticket branch, asked nobody, and the refusal became a note
        items = st.rows["Open items"] if st else []
        asked = any(not o[5] and o[3].startswith("Override:") and re.search(r"(?i)sqlite", o[3]) for o in items)
        before = product_sections(git(base, "show", f"{mb}:PRODUCT.md")).get("Foundation", "") if mb else ""
        if overridden and mb and "override" not in before.lower() and not asked:
            gaps.append("the SQLite override in #Foundation was added on this branch - an override the build writes "
                        "for itself does not count: ask the user, and record their words with `status.py open --from "
                        "build --what \"Override: tests on SQLite - <their words>\" --clears \"tests run on "
                        f"{engine}\"`")
        elif not overridden and not asked:
            gaps.append(f"#Architecture chose {engine} but the tests run on SQLite ({', '.join(files)}): run them on "
                        f"{engine}, or ask the user and record their words with `status.py open --from build --what "
                        f"\"Override: tests on SQLite - <their words>\" --clears \"tests run on {engine}\"`")
        else:
            notes.append(f"Tell the user: the tests ran on SQLite, production is {engine} - a bug only {engine} "
                         f"shows (types, timezones, locking) passes here.")
    text = (base / doc).read_text(encoding="utf-8", errors="replace") if (base / doc).is_file() else ""
    m = REVIEW_HEADING.search(text)
    if not m:
        gaps.append(f"{doc} has no Review section: the reviews' findings table (severity · file:line · what goes "
                    "wrong · fixed by) and one line per changed code file saying what the review checked in it")
        # the gate's staleness still: `ticket --dry-run` is how /build learns whether to re-run the gate (owner 10-06)
        return gaps + [g for g in (final_gate_gap(base, d, branch)[0],) if g], notes
    level = len(m.group(0)) - len(m.group(0).lstrip("#"))  # RV5: sub-headings stay inside the section
    nxt = re.search(rf"^#{{1,{level}}} ", text[m.end():], re.M)
    review = text[m.end(): m.end() + nxt.start()] if nxt else text[m.end():]
    missing = [n for n in changed if n not in review and Path(n).name not in review]
    if missing and not lean:
        gaps.append(f"{doc} §Review does not name {len(missing)} changed code file(s): {', '.join(missing[:6])} - a "
                    "review names every file it read, with what it checked there")
    gate_gap, good = final_gate_gap(base, d, branch)
    gaps += [g for g in (review_count_gap(doc, review, a.review or ""), gate_gap) if g]
    tf = find_ticket(base, a.id)
    spec = tf.read_text(encoding="utf-8", errors="replace") if tf else ""
    # finding 2: a complete verdict needs the ticket's OWN verification in the close gate - the project recipe can
    # pass without exercising this ticket at all
    mine = ticket_verification(spec)
    # a gate run counts for THIS ticket only: its ticket is this one (a run naming none is no one's - audit 6) and the
    # commands it ran include this ticket's own Verification Command lines - never another ticket's run
    if tf and a.dod == "yes" and good and not any(
            r.get("ticket") == a.id and mine and all(v in r.get("commands", []) for v in mine)
            for r in good):
        gaps.append(f"--dod yes needs the ticket's own Verification Command passing in the close gate ("
                    f"{' · '.join(mine) if mine else tf.name + ' names none'}) - run `gate.py --ticket {a.id} --close`, "
                    f"or record --dod partial and say why")
    secs = ticket_sections(spec) if spec else {}
    # the security surface is the ticket's words OR the code the branch added: a sensitive path the ticket never named
    # (a token, a password, personal data) still needs its security review (audit 6)
    diff = git(base, "diff", "-U0", f"{mb}...HEAD", "--", *changed) if mb and changed else ""
    added = "\n".join(ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++"))
    in_code = sorted({w.lower() for w in SECURITY_TICKET.findall(added)})
    sensitive = bool(SECURITY_TICKET.search(spec)) or bool(in_code)
    # R3-2: the demo's entry point (a route, a `python -m` command) is called by a test - a logged Gemini build was
    # "wired" to a module whose only way in answered 501; nothing outside the tests could reach it
    demo = demo_section(spec)
    entries = [next(g for g in m.groups() if g) for m in DEMO_ENTRY.finditer(demo)]
    if entries and not a.not_wired:
        tests = [p.read_text(encoding="utf-8", errors="replace") for p in project_files(base, SOURCE)
                 if is_test(p.relative_to(base).as_posix())]
        keys = {e: re.sub(r"\{[^}]*\}.*$", "", e).rstrip("/") for e in entries}
        unreached = [e for e, k in keys.items() if k and not any(k in t for t in tests)]
        if unreached:
            gaps.append(f"no test calls the demo's entry point {', '.join(unreached[:3])} - add one that goes through "
                        f"it (the real app, the real command), or --not-wired \"<why, and which ticket wires it>\"")
    # DP1: every Demo claim is proven by a RED cut tagged D<n>; DP2: every changed file that calls an outside service
    # has a RED cut of its own; both, or the user hears why not (--uncut). A logged Gemini build never sent the
    # status its Demo named, and its fake accepted any request - every test passed, the orders were wrong.
    red = [c for r in cut if r.get("branch") == branch for c in r.get("cuts", []) if c.get("result") == "RED"]
    uncut = {m.group(1).strip(): m.group(2).strip() for u in (getattr(a, "uncut", None) or [])
             if (m := re.match(r"\s*([^:]+?)\s*:\s*(\S.*)", u))}
    claims = [] if lean else demo_claims(spec)
    proven = {c.get("claim") for c in red}
    open_claims = [(f"D{i}", c) for i, c in enumerate(claims, 1) if f"D{i}" not in proven and f"D{i}" not in uncut]
    if open_claims:
        gaps.append(f"{len(open_claims)} Demo claim(s) with no RED cut: "
                    + "; ".join(f"{k} \"{c[:60]}\"" for k, c in open_claims[:6])
                    + " - break the code that does it and watch a test fail: --cut \"D<n>=<file>::<text>::<replacement>"
                      "::<test>\", or --uncut \"D<n>: <why no test can prove it>\" (said to the user)")
    red_files = {Path(c.get("file", "")).as_posix().lstrip("./") for c in red}
    calls_out = [n for n in changed if (base / n).is_file()
                 and OUTSIDE_CALL.search((base / n).read_text(encoding="utf-8", errors="replace"))]
    no_cut = [n for n in calls_out if not any(f == n or f.endswith("/" + n) for f in red_files) and n not in uncut]
    if no_cut and not lean:
        gaps.append(f"{', '.join(no_cut[:4])} call(s) an outside service and no RED cut breaks what they send - cut a "
                    f"field of the request (a fake that accepts any request passes every test), or --uncut "
                    f"\"<file>: <why>\"")
    for k, why in uncut.items():
        notes.append(f"Tell the user, under What I skipped or couldn't do: {k} is not proven by a test - {why}")
    # DP3: code that reaches a real outside thing names what it could touch by mistake, and the test that refuses it
    # (only one of three builds of a logged ticket asked; the other two would have seeded a real merchant's shop)
    if calls_out or sensitive:
        reach = REACH_LINE.search(text)
        named = re.findall(r"`([^`]+)`|\b(test_\w+)", reach.group(1)) if reach else []
        tests = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in project_files(base, SOURCE)
                          if is_test(p.relative_to(base).as_posix())) if reach else ""
        guarded = any((x or y) and (x or y) in tests for x, y in named)
        if not reach:
            gaps.append(f"{doc} has no `Real-world reach:` line - name the real thing this code could touch by mistake "
                        f"(a real shop, account, inbox, payment, user) and the test that proves it refuses: "
                        f"`Real-world reach: <what> - guarded by test_<name>`, or `- not guarded: <why>`")
        elif not guarded and "not guarded" not in reach.group(1).lower():
            gaps.append(f"{doc}'s `Real-world reach:` line names no test that exists - `guarded by test_<name>`, "
                        f"or `not guarded: <why>`")
        elif not guarded:
            notes.append(f"Tell the user, under What I skipped or couldn't do: {reach.group(1).strip()[:200]}")
    # the files a ticket did not name are explained where the next reader looks (a logged build edited a shared hub
    # file past its one-line rule and no record said so)
    targets = set(TARGET.findall(secs.get("Target Files", "")))
    extra = [n for n in changed if n not in targets and n not in text and Path(n).name not in text]
    if targets and extra:
        gaps.append(f"{len(extra)} changed file(s) the ticket does not name, and {doc} does not explain: "
                    f"{', '.join(extra[:6])} - say in the feature doc why each changed, or undo it")
    # a ticket the start marked "security review: REQUIRED" records that one ran (the helper, or its equivalent)
    if sensitive and not re.search(r"(?i)security", a.review or ""):
        where = ("the ticket touches auth / tenant / money / secrets / personal data" if SECURITY_TICKET.search(spec)
                 else f"the code this branch added touches {', '.join(in_code[:5])} (the ticket did not say so)")
        gaps.append(f"{where}, and --review names no security review - run it (round 1's helper) and name it in "
                    f"--review")
    # R3-3: a review of your own code cannot sign off security work - a logged self-review found 0 of 3 HIGH
    independent = re.search(r"(?i)helper agent|another tool", a.review or "")
    if tool != "claude" and "self-review" in (a.review or "").lower() and sensitive \
            and not independent:
        question = SELF_REVIEW_QUESTION.format(tid=a.id, branch=branch)
        if not a.self_review_ok:
            gaps.append("this ticket touches auth / tenant / money / secrets and only a self-review ran. Ask the user "
                        f"EXACTLY this, word for word - add nothing, recommend nothing else: \"{question}\" "
                        "Option 1: record the other tool's review as --review \"another tool: <name> ...\". Option 2: "
                        "their typed reason goes in --self-review-ok")
        elif OPTION_LABEL.search(a.self_review_ok) or len(a.self_review_ok.split()) < 4:
            gaps.append(f"--self-review-ok {a.self_review_ok!r} is an option label or too short, not the user's reason - "
                        f"ask EXACTLY: \"{question}\" and record the reason they type")
    return gaps, notes


def cmd_ticket(st: Status, a, today: str) -> str:
    if a.dod not in ("yes", "no", "partial"):
        raise Refused("--dod is yes, no or partial")
    gaps, notes = build_ticket_gaps(st.base, a, today, st)
    if getattr(a, "dry_run", False):  # every gap the row would be refused for, nothing written (P20)
        raise DryRun(f"{len(gaps)} gap(s) the ticket row would be refused for:\n  - " + "\n  - ".join(gaps) if gaps
                     else f"no gap: `ticket {a.id}` without --dry-run records it")
    if gaps:
        raise Refused("ticket not recorded:\n  - " + "\n  - ".join(gaps))
    verified = a.verified + "".join(f" · {k}: {v}" for k, v in (("no cuts", a.no_cuts), ("not wired", a.not_wired),
                                                                ("self-review ok", a.self_review_ok),
                                                                ("uncut", "; ".join(a.uncut or []))) if v)
    row = [capped("cell", a.id), today, a.dod, capped("verified", verified, a.doc),
           str(a.runs) if a.runs is not None else "not counted", capped("review", a.review or "none recorded", a.doc),
           capped("cell", a.doc)]
    st.rows["Tickets"].append(row)  # #build counts as filled once a ticket file exists (DERIVED), never written here
    return f"ticket {a.id} recorded" + "".join(f"\n  {n}" for n in notes)


def cmd_release(st: Status, a, today: str) -> str:
    cells = [today] + [capped("cell", v) for v in (a.what, a.reviews, a.skipped, a.docs, a.record, a.rollback, a.pr)]
    gaps = ship_release_gaps(st, a, st.base) if st.base is not None else []  # /ship's close, in code (P20)
    if gaps and getattr(a, "dry_run", False):
        raise DryRun(f"{len(gaps)} gap(s) the release call would refuse - fix them before the PR opens:\n"
                     + "\n".join(f"  - {g}" for g in gaps))
    if gaps:
        raise Refused(f"release: {len(gaps)} problem(s), every one at once - fix them all, then run it again:\n  - "
                      + "\n  - ".join(gaps))
    if getattr(a, "dry_run", False):
        raise DryRun("no gap: open the PR, then run this `release` with --pr <link> and --commit \"<one line>\"")
    st.rows["Releases"].append(cells)
    return "release recorded"  # #ship counts as filled once a release file exists (DERIVED)


def cmd_open(st: Status, a, today: str) -> str:
    st.phase(a.frm.lstrip("/"))
    n = new_open_id(st)
    st.rows["Open items"].append([n, today, a.frm.lstrip("/"), capped("what", a.what), capped("clears", a.clears), ""])
    return f"open item {n} recorded"


def cmd_close(st: Status, a, today: str) -> str:
    for r in st.rows["Open items"]:
        if r[0] == str(a.n):
            if r[5]:
                raise Refused(f"open item {a.n} is already closed: {r[5]}")
            r[5] = f"{today}: {capped('how', a.how)}"
            return f"open item {a.n} closed"
    raise Refused(f"no open item {a.n}")


def problems(st: Status, today: str, product: Path | None) -> tuple[list[str], list[str]]:
    errs, warns = [], []
    if not st.product:
        errs.append("no '# STATUS — <product>' title")
    names = [r[0] for r in st.rows["Phases"]]
    for p in CHAIN:
        if names.count(p) != 1:
            errs.append(f"phase {p} appears {names.count(p)} times in ## Phases (want 1)")
    for r in st.rows["Phases"]:
        if len(r) != len(COLUMNS["Phases"]):
            errs.append(f"phase row has {len(r)} cells: {r}")
            continue
        if r[0] not in CHAIN:
            errs.append(f"unknown phase {r[0]!r}")
        if r[1] not in STATES:
            errs.append(f"#{r[0]} has unknown state {r[1]!r}")
        if r[1] != "empty" and not DATE.match(r[2]):
            errs.append(f"#{r[0]} is {r[1]} with no Since date")
        if r[1] == "running" and not DATE.match(r[3]):
            errs.append(f"#{r[0]} is running with no due date")
        if r[1] == "running" and DATE.match(r[3]) and r[3] < today:
            warns.append(f"#{r[0]} was due {r[3]} and is still running - a stalled gate (a drift finding)")
        if r[0] in VERIFY and r[1] == "filled" and r[4] not in ("pass", "fail", "unknown"):
            errs.append(f"#{r[0]} is filled with no verdict (pass / fail / unknown)")
        if r[1] in ("declined", "overridden") and not r[5]:
            errs.append(f"#{r[0]} is {r[1]} with no note saying why")
    for s in SECTIONS[1:]:
        for r in st.rows[s]:
            if len(r) != len(COLUMNS[s]):
                errs.append(f"## {s} row has {len(r)} cells, want {len(COLUMNS[s])}: {r[:2]}")
    ids = [r[0] for r in st.rows["Open items"]]
    if len(ids) != len(set(ids)):
        errs.append("## Open items has a repeated id")
    if product is not None:
        if not product.exists():
            errs.append(f"{product} does not exist")
        else:
            text = product.read_text(encoding="utf-8")
            for pat, what in STATUS_IN_PRODUCT:
                m = re.search(pat, text, re.M)
                if m:
                    errs.append(f"{product.name} still holds status ({what}: {m.group(0)[:60]!r}) - status lives in "
                                f"STATUS.md; run `status.py migrate`")
            secs = product_sections(text)
            for r in st.rows["Phases"]:
                sec = PHASE_SECTION.get(r[0])
                if r[1] == "filled" and sec and not has_content(secs.get(sec, "")):
                    errs.append(f"#{r[0]} is filled in STATUS.md but PRODUCT.md#{sec} has no content")
            warns += long_lines(text) + big_sections(text)
            errs += receipt_problems(text, product.resolve().parent)
            for doc in [product] + sorted((product.resolve().parent / "docs").glob("*.md")):
                m = LATEX.search(doc.read_text(encoding="utf-8"))
                if m:
                    warns.append(f"{doc.name} uses LaTeX math ({m.group(0)[:30]!r}); write plain symbols or words "
                                 f"(≤, →, 'up to') - a Markdown viewer shows the raw code")
    return errs, warns


# A `Read` receipt proves a companion was opened (MECHANISMS-ON-DEMAND.md §Read receipt): the quote must be in the
# file it names, and only once in PRODUCT.md - a quote that also sits in an earlier receipt was copied, not read.
READ_FIELD = re.compile(r"^- \*\*Read \(file · date · verbatim quote\):\*\*(.*?)(?=^- \*\*|^## |\Z)", re.M | re.S)
RECEIPT = re.compile(r"((?:[\w.-]+/)*[\w.-]+\.md)\b[^\"“\n]*?[\"“](.+?)[\"”]")
LATEX = re.compile(r"\$[^$\n]{0,40}?(\\[a-zA-Z]+|[<>]=?\s?\d)[^$\n]{0,40}?\$")


# E1: an evidence line is a claim a later reader re-runs, so what it cites must exist. A logged run cited ten tests
# that were never written, and every gate passed because the words were right.
EVIDENCE = re.compile(r"evidence:\s*(.+?)(?:`|$)", re.M)
NODE = re.compile(r"((?:[\w.-]+/)*[\w.-]+\.(?:py|ts|tsx|js|jsx|mjs|go|rs|rb|java|kt))::([A-Za-z_][\w]*)")
EV_FILE = re.compile(r"(?<![\w/.:@$%~\\-])((?:[\w.-]+/)*[\w-][\w.-]*\.(?:py|ts|tsx|js|jsx|mjs|go|rs|rb|java|kt|toml|ya?ml|"
                     r"json|cfg|ini|sql|html|css|sh|ps1|md|lock))(?![\w/-])")


PLAYBOOK_COMMANDS = {"gate.py", "devserver.py", "ci_local.py", "proof.py"}  # the command of a line, never its artefact


def evidence_problems(text: str, base: Path, only: str) -> list[str]:
    errs = []
    # a template's example line inside <!-- --> is not evidence: a logged checkpoint was refused over the scaffold's
    # commented example and edited the template to pass
    for m in EVIDENCE.finditer(re.sub(r"<!--.*?-->", "", product_sections(text).get(only, ""), flags=re.S)):
        line = re.sub(r"https?://\S+", "", m.group(1))
        for path, name in NODE.findall(line):
            f = base / path
            if not f.is_file():
                errs.append(f"evidence cites {path}::{name}, but {path} does not exist")
            elif not re.search(rf"\b{re.escape(name)}\b", f.read_text(encoding="utf-8", errors="replace")):
                errs.append(f"evidence cites the test {name}, which {path} does not define - write the test, or "
                            f"cite the one that ran")
        for path in EV_FILE.findall(NODE.sub("", line)):
            if re.search(rf"\bplanted\b.{{0,60}}{re.escape(path)}", line):
                continue  # a file planted to prove a gate goes red, then removed: "planted <what> in <path>"
            if path in PLAYBOOK_COMMANDS:
                continue  # the playbook's gate: its record proves the files it ran, and the close says cite it;
                # /foundation's start prints its proofs as `devserver.py refuses ...` / `ci_local.py` to record
            if "/" in path:
                if not (base / path).exists():
                    errs.append(f"evidence cites {path}, which does not exist in the project")
            elif find_in_project(base, path) is None and playbook_file(path) is None:
                errs.append(f"evidence cites {path}, which is not a file in the project")
    return errs


def playbook_file(name: str) -> Path | None:
    """RR1: a Read receipt may quote a playbook file a phase opened (references/agent.md, a skill's own reference).
    Found by its path under the plugin or copy install, else by its file name in a references/ folder there (a copy
    install renames references/agent.md to AGENT.md beside this script)."""
    here = Path(__file__).resolve().parent
    roots = [here, here.parent]
    for r in roots:
        if (r / name).is_file():
            return r / name
    base = Path(name).name
    found: list[Path] = []
    for r in roots:
        found += [r / "references" / base, r / base, r / base.upper()]
        for sub in ("commands", "skills"):
            found += sorted((r / sub).glob(f"*/references/{base}")) if (r / sub).is_dir() else []
    found = [f for f in found if f.is_file()]
    exact = [f for f in found if f.as_posix().endswith(name)]
    return (exact or found or [None])[0]


def quote_line(name: str, words: str, today: str, base: Path) -> str:
    """A3: the Read receipt line to paste, built from the file itself, so a quote is never typed from memory (a
    receipt that misquotes its file is refused at `set <phase> filled`). Prints; never writes PRODUCT.md."""
    f = base / name if (base / name).is_file() else playbook_file(name)
    if f is None:
        raise Refused(f"{name} is not a file here or in the playbook")
    want = " ".join(words.split())
    if len(want) < 12:
        raise Refused("give at least a few words (12 characters) from the line you used")
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        flat = " ".join(line.split()).lstrip("-*#> ").strip()
        at = flat.lower().find(want.lower())
        if at < 0:
            continue
        q = flat if len(flat) <= 160 and '"' not in flat else flat[at:at + len(want)]
        if '"' in q:
            raise Refused("the words hold a double quote, which ends a receipt's quote: pick words without one")
        product = base / "PRODUCT.md"
        if product.is_file() and q in " ".join(product.read_text(encoding="utf-8").split()):
            raise Refused(f"PRODUCT.md already holds {q[:60]!r} - a quote found twice is read as copied; pick other "
                          f"words from {name}")
        return f"  - {name} · {today} · \"{q}\""
    raise Refused(f"{name} has no line with {want[:60]!r} - open the part you used and copy words from it")


def receipt_problems(text: str, base: Path, only: str | None = None) -> list[str]:
    errs, flat = [], " ".join(text.split())
    for field in READ_FIELD.finditer(product_sections(text).get(only, "") + "\n" if only else text):
        for m in RECEIPT.finditer(field.group(1)):
            name, quote = m.group(1), " ".join(m.group(2).split())
            path = base / name
            if not path.is_file():
                path = playbook_file(name)
            if path is None:
                errs.append(f"Read receipt names {name}, which is not a file here or in the playbook")
                continue
            if quote not in " ".join(path.read_text(encoding="utf-8").split()):
                errs.append(f"Read receipt quote is not in {name}: {quote[:60]!r} - open the file and quote a line from it")
            n = flat.count(quote)
            if n > 1:
                errs.append(f"Read receipt quote appears {n} times in PRODUCT.md: {quote[:60]!r} - it was copied from "
                            f"an earlier receipt; open {name} and quote the line this phase used")
    return errs


# PRINCIPLES.md "Readable documents": a PRODUCT.md line longer than this is a paragraph wearing a bullet.
LONG_LINE = 300


TABLE_ROW = re.compile(r"^(?:[-*>]\s+|\d+[.)]\s+)*\|")


def long_lines(text: str, only: str | None = None) -> list[str]:
    """Every PRODUCT.md line over LONG_LINE characters, section by section, except the lines kept verbatim by
    rule: table rows, `Read:` receipts and HTML comments (the template's own notes)."""
    out = []
    for sec, body in product_sections(text).items():
        if only and sec != only:
            continue
        for line in body.splitlines():
            s = line.strip()
            if len(s) <= LONG_LINE or s.startswith(("|", "<!--", "- **Read")) or TABLE_ROW.match(s):
                continue  # a table row - also behind "- " or "> ": reflow keeps it whole, so no warning
            label = re.match(r"-\s+\*\*(.+?)\*\*", s)
            where = f"PRODUCT.md#{sec}" + (f" · {label.group(1).rstrip(':')[:40]}" if label else "")
            out.append(f"{where}: a line of {len(s)} characters - split it into sub-bullets or a table "
                       f"(PRINCIPLES.md: Readable documents)")
    return out


# ---- PRODUCT.md: reading the old status out of it ---------------------------------------------------------
PHASE_SECTION = {"vision": "Vision", "validate": "Validation", "scope": "Scope", "plan": "Plan",
                 "architect": "Architecture", "structure": "Structure", "design-system": "Design",
                 "foundation": "Foundation", "contracts": "Contracts", "dev-check": "Dev-complete",
                 "deploy": "Deployment", "test": "Tests", "eval": "Evaluation", "learn": "Learnings"}
LOG_SECTIONS = {"Build log": ("Tickets", "build"), "Ship log": ("Releases", "ship"), "Drift log": ("Drift", None)}
DAY = r"(\d{4}-\d{2}-\d{2})"
# Real files wrap these in bold and italics, add "(1 of 2)", drop the colon. Matched after unwrap().
NOT_RUN = re.compile(r"^Not run " + DAY + r"\b[\s:—-]*(.*)$")
OVERRIDE = re.compile(r"^Override " + DAY + r"\b[\s:—-]*(.*)$")
OVERRIDE_FIELD = re.compile(r"^Override \(only if skipped[^)]*\):\s*.*?Override " + DAY + r"\b[\s:—-]*(.*)$")
RUNNING = re.compile(r"^Running " + DAY + r", due " + DAY + r"[\s:—-]*(.*)$")
CRITERION = re.compile(r"criterion|\(\d of \d\)", re.I)
HEADER = re.compile(r"^_Last updated:.*_\s*$")
PLAYBOOK_LINE = re.compile(r"^_Playbook:\s*(.*?)_\s*$")
STATUS_IN_PRODUCT = [(r"^_Last updated:", "the Last updated / Stage header"),
                     (r"^[_*\s]*Not run \d{4}-\d{2}-\d{2}", "a Not run line"),
                     (r"^[_*\s]*Running \d{4}-\d{2}-\d{2}, due", "a Running line"),
                     (r"^## (Build log|Ship log|Drift log)\b", "a log section")]


def unwrap(line: str) -> str:
    s = re.sub(r"^[\s\-*_]+", "", line)
    s = re.sub(r"[\s*_]+$", "", s)
    return s.replace("**", "")


def short(text: str, archive_path: str, limit: int = 150) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else f"{text[:limit].rstrip()}… (full text: {archive_path})"


def product_sections(text: str) -> dict[str, str]:
    out, name, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^## (\S+(?: log)?)", line)
        if m:
            if name:
                out[name] = "\n".join(buf)
            name, buf = m.group(1), []
        elif name:
            buf.append(line)
    if name:
        out[name] = "\n".join(buf)
    return out


def heading_key(title: str) -> str:
    """A heading as a name to ask for: no §, backticks, list number or trailing HTML comment; lower case."""
    t = re.sub(r"<!--.*?-->", "", title).replace("`", "").strip().lstrip("#§ ").strip()  # "# Vision" too
    return " ".join(re.sub(r"^\d+\.\s+", "", t).split()).lower()


def md_sections(text: str) -> list[tuple[int, str, int, int]]:
    """(level, title, first line, end line) of every heading outside a code fence; a section runs to the next
    heading of the same or a higher level, so it carries its sub-sections."""
    lines, heads, fence = text.splitlines(), [], False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        m = None if fence else re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            heads.append((len(m.group(1)), m.group(2).strip(), i))
    out = []
    for n, (lvl, title, i) in enumerate(heads):
        end = next((j for l2, _, j in heads[n + 1:] if l2 <= lvl), len(lines))
        out.append((lvl, title, i, end))
    return out


def print_sections(path: Path, names: list[str], own: list[str] = (), headings: bool = False) -> str:
    """The named sections of a Markdown file, word for word (L1). `intro` = the text above the first `##`. A name
    matches a heading that starts with it, ignoring case, §, backticks and a list number; an unknown name is
    refused with the list, so a run never falls back to guessing. `own` names print a section without its
    sub-sections; `headings` prints every heading line (a list to choose from, e.g. the 13 families)."""
    if not path.is_file():
        raise Refused(f"{path.as_posix()} not found")
    text = path.read_text(encoding="utf-8")
    lines, secs = text.splitlines(), md_sections(text)
    if headings:
        return "\n".join(lines[i] for _, _, i, _ in secs)
    if not names and not own:
        raise Refused("name at least one section, or --headings for the list")
    out = []
    for name, whole in [(n, True) for n in names] + [(n, False) for n in own]:
        key = heading_key(name)
        if key == "intro":
            first = next((i for lvl, _, i, _ in secs if lvl >= 2), len(lines))
            out.append("\n".join(lines[:first]).rstrip())
            continue
        num = re.fullmatch(r"§?\s*(\d+)\.?", name.strip())
        if num:  # a step by its number ("6."), as the step files say to ask for it - the key drops the number
            hits = [s for s in secs if re.match(rf"§?\s*{num.group(1)}\.\s", s[1].strip())]
        else:
            hits = [s for s in secs if heading_key(s[1]).startswith(key)]
        if not hits:
            listed = "; ".join(f"{'#' * lvl} {heading_key(t)}" for lvl, t, _, _ in secs)
            raise Refused(f"no section {name!r} in {path.as_posix()}. Its sections: intro; {listed}")
        lvl, _, i, end = hits[0]
        if not whole:
            end = next((j for _, _, j, _ in secs if i < j < end), end)
        out.append("\n".join(lines[i:end]).rstrip())
    return "\n\n".join(out)


def rule_file(name: str) -> Path:
    """PRINCIPLES.md / MECHANISMS.md on this install route: beside a copy install, else the plugin's."""
    here = Path(__file__).resolve().parent
    if (here / "PRINCIPLES.md").is_file():
        return here / name
    return here.parent / (name if name == "PRINCIPLES.md" else f"references/{name.lower()}")


# L3 + P1: the rule sections a phase needs, printed by `next --phase`, so the skill opens no whole rule file (a
# logged Gemini run never opened PRINCIPLES.md or MECHANISMS.md; a Claude run carried both, 31k characters, on every
# call). A phase listed here says so in its Step 0; test_status.py fails when its skill cites a § not listed.
PHASE_RULES = {
    "vision": {  # the close's sections print when `set vision filled` passes (PHASE_CLOSE_RULES)
        "PRINCIPLES.md": ["The 5-step spine", "Documentation-driven", "Communication", "Reviews, vision & confidence"],
        "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status"],
    },
    "design-system": {
        "PRINCIPLES.md": ["The 5-step spine", "Architecture & quality bar", "Documentation-driven", "Communication",
                          "Reviews, vision & confidence", "The exit-criteria gate"],
        "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status", "Step 3b",
                          "Commit the work", "Plain-language close", "Step 3c", "Follow the pointer"],
    },
    "tickets": {
        "PRINCIPLES.md": ["The 5-step spine", "Per-feature contract", "Architecture & quality bar",
                          "Production safeguards", "Documentation-driven", "Communication",
                          "Reviews, vision & confidence", "The exit-criteria gate"],
        "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status", "Step 3b",
                          "Commit the work", "Plain-language close", "Step 3c", "Follow the pointer"],
    },
    "foundation": {
        "PRINCIPLES.md": ["The 5-step spine", "Per-feature contract", "Architecture & quality bar",
                          "Production safeguards", "Documentation-driven", "Communication",
                          "Reviews, vision & confidence", "Composed skills", "The exit-criteria gate"],
        "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status", "Step 3b",
                          "Commit the work", "Plain-language close", "Step 3c", "Follow the pointer"],
    },
    "build": {
        "PRINCIPLES.md": ["The 5-step spine", "Per-feature contract", "Architecture & quality bar",
                          "Production safeguards", "Documentation-driven", "Communication",
                          "Reviews, vision & confidence", "Composed skills", "The exit-criteria gate"],
        "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status", "Step 3b",
                          "Commit the work", "Plain-language close", "Step 3c", "Follow the pointer"],
    },
    # what writing the suite needs, printed by the start (the close's sections: PHASE_CLOSE_RULES, at `set`)
    "test": {
        "PRINCIPLES.md": ["Architecture & quality bar", "Production safeguards", "Composed skills"],
        "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status"],
    },
    # what the checks themselves need, printed by the start (the close's sections: PHASE_CLOSE_RULES, at `set`). All
    # 18 sections were 27 KB re-sent on each of a logged full checkpoint's 67 calls.
    "dev-check": {
        "PRINCIPLES.md": ["Architecture & quality bar", "Production safeguards", "Composed skills"],
        "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status"],
    },
}


# The agent-instructions block templates/AGENTS.md shipped before next.25: every conversation read ~100 KB of spine,
# structure and design whole, a small coding task included.
AGENT_FILES = ("CLAUDE.md", "AGENTS.md", "GEMINI.md")
OLD_READ_ALL = "## Read before you touch anything"


# Phases that run commands for most of a session: `next --phase` prints MECHANISMS-ON-DEMAND.md §Context hygiene
# (bulky output to files, slices not whole files, the edit tool) - three of every four tokens a long run pays are
# the conversation re-sent, and what a command printed is re-sent on every later call.
HYGIENE_PHASES = ("foundation", "contracts", "tickets", "build", "dev-check", "deploy", "test")


# P2 for a question-led phase: /vision is mostly a conversation with the user, and every turn re-sends what the start
# printed. The close's rules (all after `set <phase> filled` in the close order) arrive with that command, once.
PHASE_CLOSE_RULES = {
    "vision": {"PRINCIPLES.md": ["The exit-criteria gate"],
               "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"]},
}


def phase_close_text(phase: str) -> str:
    return rules_text(PHASE_CLOSE_RULES[phase], f"Rules for the rest of /{phase}'s close (steps 2-6 above), word for "
                                                f"word from the rule files - do not open them:")


# Per phase: (what step 2 reconciles, what Step 3c compares with, what `set` itself counted for step 5)
CLOSE_STEPS = {
    "vision": ("every number against the other fields: an input bar against the AI accuracy bar, the target against "
               "the worked example",
               "the README purpose below and any earlier record - who it's for, the north star, the business model",
               "the fields, the search links and the terms table"),
    "scope": ("every number against #Vision: a scope that cannot reach the north-star target, a proposed number the "
              "owner never confirmed",
              "#Vision (customer · job-to-be-done · north star) and #Validation's verdict - a core feature that serves "
              "nobody there, scope written as if a failed validation had passed",
              "the core feature, the triggers, every table stake and the unmarked numbers"),
    "plan": ("every number against #Vision: a timeline ending after the north-star date, a milestone bar above the target",
             "#Scope - every milestone traces to the core feature, no milestone delivers a recorded non-goal",
             "the fields, the milestones' exit criteria, the four-risks rows and the unmarked numbers"),
}


def close_steps_text(phase: str, saved: str | None = None) -> str:
    """What `set <phase> filled` prints: the rest of the close as a checklist. Three reviewers said ~2/3 of the
    ~3.5K tokens of rules it printed went unused, and a re-run of `set` printed them again."""
    sha = re.search(r"commit (\w+)", saved or "")
    reconcile, compare, counted = CLOSE_STEPS.get(phase, ("every number this phase introduced against #Vision",
                                                          "the decisions already recorded", "its fields"))
    return "\n".join([
        f"The rest of the close, in order (the rules word for word, only if a step is unclear: status.py rules "
        f"{phase} --close):",
        # a logged Cursor /vision re-read PRODUCT.md, README.md and its companion 7 times after a passing set, and
        # measured its own line lengths first: ~900K tokens in one turn (2026-10-01)
        "  This `set` checked the record: never re-read PRODUCT.md, STATUS.md, README.md or the companion to check "
        "it, and never measure line lengths (`set` wraps them). Steps 2-3 use what you wrote - it is in this "
        "conversation - and the facts printed below.",
        f"  2. reconcile {reconcile}; name a clash to the user, never write over it",
        f"  3. Step 3c: compare with {compare}; a conflict: name both sides, ask which wins; a fix -> run this `set` "
        f"again",
        (f"  4. {saved} - the user's yes to the drafts was the save: never ask it again" if saved else
         '  4. ask "Save this version of your project? (yes / no)" with the details below under it; it waits for the '
         "reply - on a yes: `status.py save -m \"<one line>\"`, the only save (no git call of your own). End the "
         "message at the question: steps 5-6 come after the answer, their first line saying what the save did "
         "(Saved, with the commit hash - or Not saved). The user's own request already said to commit: that is the yes - save and say so, no question"),
        f"  5. the transition guard: a verdict per exit criterion - VERIFIED only for what a command you ran checked "
        f"(this `set` counted {counted}); wording and quality are UNVERIFIED (judged); never 100%",
        # A6: after a clean --commit save the owner still typed "commit" (3 calls): the close says it first
        (f"  6. its first line: `Saved: commit {sha.group(1)}` - nothing left to commit; then four blocks" if sha
         else "  6. four blocks")
        + ", in order: What just happened · What I skipped or couldn't do · Test this yourself · What YOU do next - "
        "its last line is the `Open a NEW conversation` line below, copied word for word"])


# ---- /dev-check (P1, P2, P20, P44) ------------------------------------------------------------------------------
# The checkpoint's start prints the facts and the rules its checks use; the close is ONE checked call whose refusal
# names every gap, and `set` prints the rest of the close. Before: a second `rules` call (27 KB), the generic 3 KB
# checklist re-sent on every call, and two refusals in turn that --dry-run never reached.
# owner 2026-10-06: a checkpoint or suite record is saved without a question (a separate "Save this version?" turn
# cost ~680K tokens across 4 tools); `--no-commit` only when the user said not to save
AUTO_SAVE = ("dev-check", "test")
PHASE_CLOSE_RULES["dev-check"] = {"PRINCIPLES.md": ["The exit-criteria gate", "Reviews, vision & confidence"],
                                  "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"]}
CLOSE_STEPS["dev-check"] = (
    "every number this checkpoint states against #Vision and #Plan's milestone criteria",
    "#Scope's core list against the STATUS.md ticket rows - a feature marked done that scope never asked for, or a "
    "scoped feature quietly dropped",
    "each milestone ticket's state, the gate on this checkout, and a line for the gate, the live path, security and "
    "scope")
DEV_CHECK_HEAD = (
    "This phase closes with ONE call - `status.py set dev-check filled --verdict pass|fail --section-from <file>`, "
    "#Dev-complete's body in a scratch file outside the repo (never an edit tool on PRODUCT.md): it checks the "
    "record, names every problem at once (refused: PRODUCT.md is put back; `--dry-run` lists them, writes nothing), "
    "SAVES the project - never ask \"Save this version?\" (`--no-commit` only when the user said not to save) - and "
    "prints the rest of the close. A FAIL is a normal record - only the owner declines this phase.",
    "This phase must NOT: edit or fix code, tests or docs · merge a branch · re-run a check to get its number again "
    "(cite the run: a gate pass counts on the exact files it checked) · run a check it was not asked for (an extra type "
    "checker, a second scan) - it checks, records and files.",
    "A playbook command fails twice: stop, show the user the exact error and ask - never open or edit the playbook's "
    "scripts (a logged run spent 11.4M tokens editing them).")


# ---- /test: the same alignment (P1, P2, P20, P44). Its start already names the one close call (test_start_text).
PHASE_CLOSE_RULES["test"] = PHASE_CLOSE_RULES["dev-check"]
CLOSE_STEPS["test"] = (
    "every number this phase states (counts, the eval dataset's result) against #Vision and #Plan",
    "#Contracts and #Architecture - a suite that asserts a shape the contracts don't declare, or points a "
    "real-boundary test at the datastore #Foundation recorded for development",
    "a line each for the live path, security and regression cases, outside-service reach, and the gate over the "
    "final files")
TEST_HEAD = (
    "This phase must NOT: change product code (a test that exposes a bug stays, marked an expected failure naming the "
    "issue filed) · write a one-off script where a re-runnable test belongs · re-run a test file the gate covered to "
    "get its number (cite the gate: it counts on the exact files it checked) · run a check it was not asked for (an "
    "extra type checker, a second scan).",
    DEV_CHECK_HEAD[2])

# ---- release ops: /eval /learn /ship /deploy (v2 alignment, P1 P2 P20 P37 P41-P45) ------------------------------
# Each read PRINCIPLES.md, MECHANISMS.md and PRODUCT.md whole in its first message and closed on prose alone. The
# start is now one call (the spine lines the phase measures against, what to write, what the close refuses, the
# rules); the close is one call that refuses the countable gaps, every problem in one list, on the phase's own close
# only (never in phase_check: a record filled under older rules is never blocked later).
RELEASEOPS_CLOSE = ("Commands work in PowerShell and in bash: one command per call - no &&, tail, grep or export; never "
                    "`cd <path> &&`. An output over 30 lines goes to a file. The same command fails 3 times: stop and "
                    "tell the user what fails. Plain symbols (≤ →), never LaTeX.",
                    # P48: a logged Antigravity run spent 60 calls and 11.4M tokens (69%) working around one harness
                    # error, rewording the command each time so the 3-times rule never fired; Cursor edited status.py
                    "a playbook command fails twice, worded any way: stop, show the user its exact error and ask - "
                    "never open or edit the playbook's scripts to get past it.",
                    "The playbook's scripts are tools, not reading: run them; their output and refusals say what to "
                    "do - never open their source. `--dry-run` runs the same checks and writes nothing.")
RELEASEOPS_HEAD = {p: (f"This phase closes with ONE call - `status.py set {p} filled"
                       f"{' --verdict pass|fail' if p in VERIFY else ''} --section-from <file> --commit "
                       f"\"<one line>\"`, the section in a scratch file outside the "
                       f"repo (never an edit tool on PRODUCT.md): it checks the record, names every problem at once, "
                       f"saves (leave `--commit` out when the user said not to save - no git call of your own) and "
                       f"prints the rest of the close.",) + RELEASEOPS_CLOSE for p in ("eval", "learn", "deploy")}
EVAL_FIELDS = (("Is it good?", r"^is it good"), ("Metrics + confidence score", r"^metrics"),
               ("Cost-per-run", r"^cost"), ("Operational failures", r"^operational"), ("Detail", r"^detail"))
# "Confidence 70%" and "70% confidence" both (format refusals were the biggest refusal family on logged rounds)
EVAL_CONFIDENCE = re.compile(r"(?i)confidence(?: score)?\W{0,4}(?:is |of |at )?(\d{1,3}(?:\.\d+)?)\s*%|"
                             r"(\d{1,3}(?:\.\d+)?)\s*%\s*confiden")
OWNER_ANSWERS = re.compile(r"(?im)^#{2,3}\s.*owner'?s?['’]?s? answers")
EVAL_SCORED = re.compile(r"(?i)bias|scor(?:ed|ing|er)|grade|judge|rubric|exact match|human review")
NOT_READABLE = re.compile(r"(?i)\bnot (?:yet )?readable\b")
# what /eval may change: its record and its measurements - an audit's "fix" step is not measuring (#284 §6)
EVAL_OWN = re.compile(r"^(?:PRODUCT\.md|STATUS\.md|status/|docs/|evals?/|\.status\.lock)")
PHASE_RULES["eval"] = {  # §Production safeguards holds "Measure for real" (baseline, instrumented, deterministic)
    "PRINCIPLES.md": ["Production safeguards", "Reviews, vision & confidence", "Communication"],
    "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status"],
}
PHASE_CLOSE_RULES["eval"] = {
    "PRINCIPLES.md": ["The exit-criteria gate"],
    "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"],
    "MECHANISMS-ON-DEMAND.md": ["Section is a record", "Read receipt"],
}
CLOSE_STEPS["eval"] = (
    "every number against #Vision: a result that contradicts the north-star target, a guardrail the result made worse",
    "#Vision's north star (the metric measured is the one recorded) and #Architecture's performance and cost budget (a "
    "measured number never silently replaces it)",
    "the #Evaluation fields, the baseline, the confidence number and the evidence lines")


# Every call re-sends the start, and the rule sections were 8.4-9.4 KB of each 14-17 KB start: §Production
# safeguards (3.1 KB) was printed whole for the 2-5 bullets a phase applies, §Re-run semantics on a first run,
# §Declined runs with every gate met. The start prints the bullets word for word and those sections only when they
# apply; `status.py rules <phase>` still prints every section whole.
RELEASEOPS_SAFEGUARDS = {
    "eval": ("Measure for real", "Perf & cost budgets"),
    "learn": ("Measure for real", "Observability & audit"),
    "ship": ("Security baseline", "Secrets never get pushed", "Placeholders must FAIL the boot",
             "AI-specific security", "Rollout safety"),
    "deploy": ("Security baseline", "Secrets never get pushed", "Placeholders must FAIL the boot",
               "Rollout safety", "Perf & cost budgets"),
}


def safeguard_bullets(keys: tuple) -> str:
    """The named top-level bullets of PRINCIPLES.md §Production safeguards, word for word (with their continuation
    lines)."""
    lines = print_sections(rule_file("PRINCIPLES.md"), ["Production safeguards"]).splitlines()
    out, keep = [], False
    for ln in lines[1:]:
        if ln.startswith("- **"):
            keep = any(ln.startswith(f"- **{k}") for k in keys)
        elif ln.startswith("#"):
            keep = False
        if keep:
            out.append(ln)
    return "\n".join(out)


def releaseops_rules_text(st: "Status", phase: str, gate_unmet: bool) -> str:
    want = {k: list(v) for k, v in PHASE_RULES[phase].items()}
    want["PRINCIPLES.md"] = [s for s in want["PRINCIPLES.md"] if s != "Production safeguards"]
    if st.phase(phase)[1] not in ("filled", "overridden"):
        want["MECHANISMS.md"] = [s for s in want["MECHANISMS.md"] if s != "Re-run semantics"]
    if not gate_unmet:
        want["MECHANISMS.md"] = [s for s in want["MECHANISMS.md"] if s != "Declined runs"]
    return (rules_text(want, f"Rules for /{phase}, word for word from the rule files (these ARE the rule files for "
                             f"this phase - do not open them; every section whole: status.py rules {phase}):")
            + "\n\n===== PRINCIPLES.md §Production safeguards - the bullets this phase applies =====\n"
            + safeguard_bullets(RELEASEOPS_SAFEGUARDS[phase]))


def releaseops_field(fields: dict[str, str], rx: str) -> str | None:
    return next((v for k, v in fields.items() if re.search(rx, k, re.I)), None)


def releaseops_empty(fields: dict[str, str], want: tuple, sec: str) -> list[str]:
    """One gap per field that is missing or holds only a placeholder (a bare `n/a` needs its reason)."""
    out = []
    for label, rx in want:
        v = releaseops_field(fields, rx)
        if v is None or EMPTY_VALUE.match(v.strip()):
            out.append(f"#{sec} `{label}` is empty - write the answer (one that does not apply: `n/a - <why>`)")
    return out


def releaseops_owner_gaps(base: Path, companion: str) -> list[str]:
    """The owner's round-1 answers kept word for word in the companion (a logged run saved an answer as "a" and a
    later phase read it as a date; the blind review's deciding factor was "owner decisions kept")."""
    if OWNER_ANSWERS.search(read_text(base / companion)):
        return []
    return [f"{companion} has no `## Owner's answers` - round 1's answers word for word, numbered as asked"]


def releaseops_spine(base: Path) -> dict[str, str]:
    prod = base / "PRODUCT.md"
    return {k: re.sub(r"<!--.*?-->", "", v, flags=re.S)
            for k, v in (product_sections(prod.read_text(encoding="utf-8")) if prod.is_file() else {}).items()}


def eval_gaps(base: Path, st: "Status", verdict: str) -> list[str]:
    """What `set eval filled` refuses: every field answered, a baseline (or a north star honestly not readable yet),
    a confidence number that is never 100%, the guardrail beside the result, failures counted apart, and a pass that
    stands on at least one command's result."""
    secs = releaseops_spine(base)
    body = secs.get("Evaluation", "")
    f = section_fields(body)
    gaps = releaseops_empty(f, EVAL_FIELDS, "Evaluation")
    good, metrics = releaseops_field(f, r"^is it good") or "", releaseops_field(f, r"^metrics") or ""
    ops, cost = releaseops_field(f, r"^operational") or "", releaseops_field(f, r"^cost") or ""
    if good and NOT_READABLE.search(good):
        if not re.search(r"\d{4}-\d{2}-\d{2}|\bafter\b", good):
            gaps.append("#Evaluation `Is it good?` says the north star is not readable yet but not when it will be "
                        "(a date, or `after <the event>`)")
    elif good and not (re.search(r"(?i)baseline", good) and re.search(r"\d", good)):
        gaps.append("#Evaluation `Is it good?` has no measured number against a named baseline - write `<result> vs "
                    "baseline <number> (<where it is recorded>)`; no baseline yet: `first run - this result is the "
                    "baseline`; a target readable only after launch: `north star not readable until <date>`")
    conf = EVAL_CONFIDENCE.search(body)
    if metrics and not conf:
        gaps.append("#Evaluation `Metrics + confidence score` has no confidence percentage (`Confidence 70%: solid "
                    "- ...; risky - ...; to raise it - ...`)")
    elif conf and float(conf.group(1) or conf.group(2)) >= 100:
        gaps.append("#Evaluation confidence is 100% - never 100%: name what is still risky or untested")
    guard = releaseops_field(section_fields(re.sub(r"(?m)^\*\*", "- **", secs.get("Vision", ""))), r"guardrail")
    if guard and not EMPTY_VALUE.match(guard.strip()) and not re.search(r"(?i)guardrail", body):
        gaps.append(f"#Vision names a guardrail ({guard[:80]}) and #Evaluation does not report it - measure it beside "
                    f"the result: a north star that improved while the guardrail got worse is not a pass")
    if ops and not re.search(r"\d|(?i:\bnone\b)", ops):
        gaps.append("#Evaluation `Operational failures` has no count - errored, blocked and dropped runs as a number "
                    "(`0 of 40`), apart from the quality result")
    if st.header.get("AI product") == "yes" and cost and not (re.search(r"\d", cost) and EVAL_SCORED.search(cost)):
        gaps.append("#Evaluation `Cost-per-run` needs, for an AI product, the cost of one run as a number and the "
                    "scoring-bias check (who or what scored it, and how a bias in that scoring was checked)")
    gaps += releaseops_owner_gaps(base, "docs/evaluation.md")
    if verdict == "pass" and not EVIDENCE.search(body):
        gaps.append("--verdict pass with no `evidence:` line in #Evaluation - a pass stands on a command you ran "
                    "(`evidence: <command> → <result> · <file it checks> · <date>`); nothing measurable yet: "
                    "--verdict fail and say what is missing")
    return gaps


def eval_warnings(base: Path) -> list[str]:
    """/eval measures; it never changes the product (P44). An audit it composed may have run its own fix step."""
    # git() strips the output, so the first line may have lost its leading status column: cut 2, then strip
    changed = [ln[2:].strip().strip('"') for ln in git(base, "status", "--porcelain").splitlines() if len(ln) > 3]
    other = [p for p in changed if not EVAL_OWN.match(p)]
    if not other:
        return []
    return [f"files outside /eval's record changed in the working tree: {', '.join(other[:8])} - /eval measures and "
            f"changes no product file; if this run or an audit it ran changed them, put them back (git restore / "
            f"delete) - a product change goes through a ticket. The user's own edits: leave them and say so"]


def eval_start_text(st: "Status") -> str:
    """`next --phase eval`: the goal to measure against, the gates before it, the budget, the dataset, the fields and
    what the close refuses - one call instead of three rule files and PRODUCT.md read whole."""
    base = st.base or Path(".")
    secs = releaseops_spine(base)
    vision = section_fields(re.sub(r"(?m)^\*\*", "- **", secs.get("Vision", "")))
    pick = [f"      {k}: {v[:220]}" for k, v in vision.items()
            if re.search(r"north star|target|guardrail|input metric|instrument", k, re.I) and v.strip()]
    gates = []
    for p, sec in (("dev-check", "Dev-complete"), ("test", "Tests")):
        r = st.phase(p)
        gates.append((p, sec, r[1], r[4]))
    unmet = [g for g in gates if not (g[2] == "filled" and g[3] == "pass")]
    budget = [ln.strip()[:200] for ln in secs.get("Architecture", "").splitlines()
              if re.search(r"(?i)budget|latency|p9[59]|per run|cost per|throughput", ln)][:6]
    earlier = releaseops_field(section_fields(secs.get("Evaluation", "")), r"^is it good")
    evals = sorted(p.relative_to(base).as_posix() for p in (base / "evals").rglob("*") if p.is_file()) \
        if (base / "evals").is_dir() else []
    ai = st.header.get("AI product", "unknown")
    tpl = tool_file("templates", "PRODUCT.md")
    fields = product_sections(tpl.read_text(encoding="utf-8")).get("Evaluation", "") if tpl else ""
    fields = "\n".join("      " + l for l in fields.splitlines() if l.startswith("- **"))
    out = ["/eval start - measure against these; read nothing else whole:",
           "  - #Vision (the goal - the measurement baseline):\n" + ("\n".join(pick) or "      (no north star - "
           "sharpen it with the user or send them back to /vision before measuring anything)"),
           "  - Gates before /eval: " + " · ".join(f"#{s} ({p}): {state}{' ' + v if v else ''}"
                                                   for p, s, state, v in gates)
           + (f" - NOT PASSED: {', '.join('/' + g[0] for g in unmet)}. Say which, offer them first (/dev-check, then "
              f"/test); to go on, record the user's own reason: status.py bypass --from eval --gate <phase> --reason "
              f"\"<their words>\"" if unmet else " - both passed"),
           "  - #Architecture's budget lines (a measured number never silently replaces one - Step 3c):\n"
           + ("\n".join("      " + b for b in budget) or "      (none recorded)"),
           "  - Baseline: " + ("the recorded one - #Evaluation now says: " + earlier[:200] if earlier and earlier.strip()
                               else "none recorded - this first result becomes the baseline (ask in round 1)"),
           "  - Dataset: " + (", ".join(evals[:10]) + (" ..." if len(evals) > 10 else "") + " - count it only if a "
                              "command here runs it and you ran it" if evals else
                              "no evals/ folder - the representative inputs are round 1 question 1"),
           f"  - AI product: {ai}" + (" - compose /enterprise-ai-audit if it is installed, REPORT ONLY: run its audit "
                                      "and read the report, never its fix step (it writes a Dockerfile, CI and code "
                                      "files); not installed: audit the same ground yourself; say which in the "
                                      "evidence line. Cost-per-run and the scoring-bias check are required"
                                      if ai == "yes" else ""),
           "  - /eval measures; it never changes product code, config or tests (a gap found is a finding for a "
           "ticket). `set` names any file outside docs/, evals/ and the record that changed.",
           # waste audit W62: a skill loaded into the main conversation re-sent its whole body (~0.6M a run)
           "  - A composed audit (/enterprise-ai-audit) runs inside a subagent and returns only its score card; "
           "its report is input to the record, never the run's last message.",
           # waste audit W7 + unrequested checks (~0.6-1M each on logged runs)
           "  - Run only: the measurement over the representative set, once, and the commands its evidence lines "
           "cite - no test suite, lint, type check or scan of your own. Re-run a measurement only when a file it "
           "reads changed; the transition guard cites this run's lines.",
           "  - #Evaluation is these fields, labels as written, in a scratch file outside the repo; the reasoning and "
           "raw numbers go in docs/evaluation.md:\n" + fields,
           "  - `set eval filled --verdict pass|fail` refuses, every problem in one list: an empty field (a bare "
           "`n/a` too) · `Is it good?` without a number against a named baseline (no baseline yet: `first run - "
           "this result is the baseline`; a target readable only after launch: `north star not readable until "
           "<date>`, and the input metrics measured now) · no confidence percentage, or 100% · a #Vision guardrail "
           "not reported · operational failures without a count · an AI product's cost without a number or the "
           "scoring-bias check · a pass with no `evidence:` line · a cited file that does not exist · LaTeX.",
           "  - Two rounds, each ONE message (numbered lines to answer by typing, or your ask tool's form). Round 1 - "
           "only what the lines above leave open: 1. the representative inputs (the owner's real samples, evals/, or "
           "both) · 2. no baseline recorded: this result becomes it (Recommended), or the owner names one · 3. a north "
           "star readable only after launch: record it not readable until <date> and measure the input metrics now "
           "(Recommended), or stop · 4. a gate not passed: run it first (Recommended), or go on with the owner's "
           "reason. Round 2, after measuring: the result, the confidence, any Step 3c clash, and \"Anything to "
           "change? If not: Save this version of your project? (yes / no)\" as \"Looks good - save (Recommended)\" · "
           "\"Change something\".",
           "  - The forms `set` accepts: `Confidence 70%: solid - ...; risky - ...; to raise it - ...` · failures as "
           "`0 of 40` · `Is it good?` names the input kind (real · owner samples · synthetic) - the close copies every "
           "number and data claim from this record, never from memory.",
           "  - docs/evaluation.md ends with `## Owner's answers`: round 1's answers word for word, numbered as asked.",
           "  - Then ONE message: docs/evaluation.md and the section file, then `set eval filled --verdict pass|fail "
           "--section-from <file> --commit \"<one line>\"` (no `--commit` on a no) records, saves and prints the rest "
           "of the close. Stopping at an unmet gate: `status.py set eval declined --reason \"<what was missing>\" "
           "--gate <phase>`."]
    return "\n".join(out) + "\n\n" + releaseops_rules_text(st, "eval", bool(unmet))


# /learn: an input gate - the metric is evidence, build / iterate / KILL is the owner's call. #Learnings is
# append-only (one entry per cycle): the section holds the latest cycle, an earlier one moves to docs/learnings.md.
LEARN_FIELDS = (("Success metric + result", r"^success metric"), ("User/usage signal incorporated", r"^user"),
                ("Retro (what worked / what to change)", r"^retro"), ("Decided next", r"^decided next"),
                ("Observability + cost watch in place", r"^observability"), ("Detail", r"^detail"))
LEARN_SIGNAL = re.compile(r"(?i)support|ticket|interview|call|survey|usage|analytics|e-?mail|feedback|session|review log|"
                    r"chat|complain|request|churn|log\b|users?\b|customers?\b|pilot|consultants?\b|said|told|asked")
LEARN_SOURCE = re.compile(r"(?i)dashboard|analytics|event|\blog\b|query|export|report|database|table|sql|instrument|tracked|"
                    r"from the|evidence:")
LEARN_DECISION = re.compile(r"(?i)\b(build|iterate|kill|deprecate|stop|continue|keep|drop|pause|pivot|remove)\b")
LEARN_DEFERRED = re.compile(r"(?i)\bdefer\w*|\blater\b|\bparked\b|\bnot now\b|\bnext cycle\b")
LEARN_TRIGGER = re.compile(r"(?i)\btrigger|\bwhen\b|\bonce\b|\bif\b|\buntil\b|\bafter\b")
PHASE_RULES["learn"] = {
    "PRINCIPLES.md": ["Production safeguards", "Reviews, vision & confidence", "Communication"],
    "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status"],
}
PHASE_CLOSE_RULES["learn"] = {
    "PRINCIPLES.md": ["The exit-criteria gate"],
    "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"],
    "MECHANISMS-ON-DEMAND.md": ["Section is a record", "Read receipt"],
}
CLOSE_STEPS["learn"] = (
    "every number against #Vision: a measured result read against the north-star target and date it serves",
    "#Vision's north star and #Scope's non-goals - 'what we learned we should build' is how a non-goal comes back "
    "unrecorded",
    "the #Learnings fields, the decision word, a trigger per deferred item and the earlier cycle kept")


def learn_gaps(base: Path, st: "Status") -> list[str]:
    """What `set learn filled` refuses: every field answered, a measured result read from somewhere (or honestly not
    readable yet), a real user signal (or none yet with an open item), a retro with both halves, one decision word,
    a trigger per deferred item, and the earlier cycle's decision kept in docs/learnings.md (append-only)."""
    secs = releaseops_spine(base)
    f = section_fields(secs.get("Learnings", ""))
    gaps = releaseops_empty(f, LEARN_FIELDS, "Learnings")
    metric, signal = releaseops_field(f, r"^success metric") or "", releaseops_field(f, r"^user") or ""
    retro, decided = releaseops_field(f, r"^retro") or "", releaseops_field(f, r"^decided next") or ""
    watch = releaseops_field(f, r"^observability") or ""
    if metric and NOT_READABLE.search(metric):
        if not re.search(r"\d{4}-\d{2}-\d{2}|\bafter\b", metric):
            gaps.append("#Learnings `Success metric + result` says not readable yet but not when (a date, or `after "
                        "<the event>`)")
    elif metric and not (re.search(r"\d", metric) and LEARN_SOURCE.search(metric)):
        gaps.append("#Learnings `Success metric + result` needs the measured number and where it was read (the "
                    "dashboard, the log, the query) - instrumented, never guessed; not readable yet: `not readable "
                    "until <date>`")
    if signal and re.search(r"(?i)\bnone\b", signal):
        if not any(o[2] == "learn" and not o[5] for o in st.rows["Open items"]):
            gaps.append("#Learnings has no real user signal yet - say so and open an item for it: status.py open "
                        "--from learn --what \"no user signal yet: <why>\" --clears \"<the first signal is in>\"")
    elif signal and not LEARN_SIGNAL.search(signal):
        gaps.append("#Learnings `User/usage signal` names no real source (support, an interview, usage data, the "
                    "review log) - internal opinion is not a user signal")
    if retro and not (re.search(r"(?i)worked|went well|kept", retro)
                      and re.search(r"(?i)chang|differently|improve|\bstop\b|\bstart\b|fix", retro)):
        gaps.append("#Learnings `Retro` needs both halves: what worked · what to change")
    if decided and not LEARN_DECISION.search(decided):
        gaps.append("#Learnings `Decided next` names no decision - build, iterate or KILL (the owner's call)")
    if decided and LEARN_DEFERRED.search(decided) and not LEARN_TRIGGER.search(decided):
        gaps.append("#Learnings `Decided next` defers something without the trigger that would bring it back "
                    "(`later - when <trigger>`)")
    if st.header.get("AI product") == "yes" and watch and not re.search(r"(?i)cost|spend|€|\$|budget", watch):
        gaps.append("#Learnings `Observability + cost watch` names no cost watch - an AI product's spend per use is "
                    "watched after launch, not once")
    gaps += releaseops_owner_gaps(base, "docs/learnings.md")
    # append-only: the cycle this run replaces keeps its decision in the companion
    prev = section_fields(product_sections(git(base, "show", "HEAD:PRODUCT.md")).get("Learnings", "")) \
        if git_dir(base) else {}
    old = (releaseops_field(prev, r"^decided next") or "").strip()
    comp = read_text(base / "docs" / "learnings.md") if (base / "docs" / "learnings.md").is_file() else ""
    if old and not EMPTY_VALUE.match(old) and " ".join(old.split()) != " ".join(decided.split()) and \
            " ".join(old.split())[:60] not in " ".join(comp.split()):
        gaps.append(f"#Learnings is append-only - the earlier cycle's decision ({old[:70]}) is in neither the section "
                    f"nor docs/learnings.md: move the earlier entry under `## Cycle <its date>` there, word for word")
    return gaps


def learn_start_text(st: "Status") -> str:
    """`next --phase learn`: the goal, what shipped, what was measured, the non-goals and the earlier decision - one
    call instead of three rule files and PRODUCT.md read whole."""
    base = st.base or Path(".")
    secs = releaseops_spine(base)
    vision = section_fields(re.sub(r"(?m)^\*\*", "- **", secs.get("Vision", "")))
    pick = [f"      {k}: {v[:220]}" for k, v in vision.items()
            if re.search(r"north star|guardrail|instrument", k, re.I) and v.strip()]
    scope = [ln.strip()[:220] for ln in secs.get("Scope", "").splitlines()
             if re.search(r"(?i)non-goal|out of scope|deferred|later|trigger", ln)][:8]
    ev = st.phase("eval")
    evf = section_fields(secs.get("Evaluation", ""))
    good = releaseops_field(evf, r"^is it good") or ""
    rel = st.rows["Releases"][-5:]
    dep = section_fields(secs.get("Deployment", ""))
    url = releaseops_field(dep, r"^live url") or ""
    prev = releaseops_field(section_fields(secs.get("Learnings", "")), r"^decided next") or ""
    tpl = tool_file("templates", "PRODUCT.md")
    fields = product_sections(tpl.read_text(encoding="utf-8")).get("Learnings", "") if tpl else ""
    fields = "\n".join("      " + l for l in fields.splitlines() if l.startswith("- **"))
    cadence = ("compose /loop or /schedule to re-measure on a cadence" if playbook_tool() == "claude" else
               "no /loop or /schedule on this tool: name the cadence and who re-reads the metric (a calendar "
               "reminder the owner sets)")
    out = ["/learn start - decide from these; read nothing else whole:",
           "  - #Vision (the goal the next move answers to):\n" + ("\n".join(pick) or "      (no north star)"),
           "  - Shipped: " + ("; ".join(f"{r[0]} {r[1][:90]} ({r[7][:60]})" for r in rel) if rel else
                              "NOTHING - no release row: /learn is premature. Say so; go on only with the owner's "
                              "reason: status.py bypass --from learn --gate ship --reason \"<their words>\""),
           f"  - Live: {url[:160] if url.strip() else '(no #Deployment URL)'}",
           f"  - #Evaluation: {ev[1]}{' ' + ev[4] if ev[4] else ''}" + (f" - {good[:220]}" if good.strip() else
           " - EMPTY: say so before drawing conclusions; a retro with no measured result is opinion - label the "
           "basis honestly in the record"),
           "  - #Scope's non-goals and deferred items (a next move that brings one back needs its trigger - Step 3c):\n"
           + ("\n".join("      " + s for s in scope) or "      (none recorded)"),
           # whole, so the move needs no read of PRODUCT.md or the companion (waste audit W26/P19)
           ("  - The earlier cycle, whole - #Learnings is append-only: put it in docs/learnings.md under `## Cycle "
            "<its date>`, word for word, in the same write as this cycle's notes:\n"
            + "\n".join("      " + ln for ln in secs.get("Learnings", "").strip().splitlines())
            if prev.strip() else "  - First cycle: no earlier #Learnings entry"),
           f"  - Cadence: {cadence}.",
           "  - /learn decides; it builds nothing and changes no code - the next cycle does, starting at /scope.",
           "  - Run only: the query or export that reads the metric (once) - no test suite, lint or scan. "
           "docs/learnings.md is written, never read whole: the earlier cycle is printed above.",
           "  - #Learnings is these fields, labels as written, in a scratch file outside the repo; the retro's detail "
           "and lessons go in docs/learnings.md:\n" + fields,
           "  - `set learn filled` refuses, every problem in one list: an empty field (a bare `n/a` too) · a result "
           "without its number and where it was read (not readable yet: `not readable until <date>`) · a user signal "
           "with no real source (none yet: say so and `status.py open --from learn ...`) · a retro without what "
           "worked and what to change · no build / iterate / KILL · a deferred item without its trigger · an AI "
           "product's watch without cost · the earlier cycle's decision lost (append-only) · LaTeX.",
           "  - Two rounds, each ONE message (numbered lines to answer by typing, or your ask tool's form). Round 1, "
           "before drafting: 1. the success metric's number now and where it is read (or when it becomes readable) "
           "· 2. the real user signal: which source and what it said · 3. anything the owner already wants next (an "
           "idea, a complaint, a feature to kill) - recorded as theirs. Round 2: the retro, the evidence and the "
           "proposed build / iterate / KILL with a trigger per deferred item, marked (proposed), any Step 3c clash, "
           "and \"Anything to change? If not: Save this version of your project? (yes / no)\" as \"Keep as proposed "
           "- save (Recommended)\" · \"Change something\" - the decision is the owner's: never record it unseen.",
           "  - docs/learnings.md holds `## Owner's answers` for this cycle: round 1's answers word for word, numbered "
           "as asked. Decision words `set` accepts: build · iterate · continue · KILL · drop · pause.",
           "  - Then ONE message: docs/learnings.md and the section file, then `set learn filled --section-from "
           "<file> --commit \"<one line>\"` (no `--commit` on a no) records, saves and prints the rest of the close "
           "and the next cycle's first command. Stopping at an unmet gate: `status.py set learn declined --reason "
           "\"<what was missing>\" --gate <phase>`."]
    return "\n".join(out) + "\n\n" + releaseops_rules_text(
        st, "learn", not rel or not (ev[1] == "filled" and ev[4] == "pass"))


# /ship: the record is the release row (`status.py release`; #ship is filled once one exists - DERIVED). The check
# runs as `release --dry-run` BEFORE the PR opens, so "stop, do not open the PR" can still fire (#284 ship.md:86);
# the record call after the PR saves and prints the close. A logged /ship spent its first calls on git and the ticket
# rows; the start prints them.
SHIP_CITED = re.compile(r"(?i)\b(?:cited|unchanged since)\b|\b[A-Z][A-Z0-9]*-[A-Z0-9]+-\d+\b")
SHIP_GATE = re.compile(r"(?i)\bgate\s*[×x]\s*1\b|\bgate\b[^·]{0,30}\b(?:cited|unchanged)\b")
SHIP_RETIRED = re.compile(r"(?i)do not add|no longer (?:kept|updated|maintained)|retired|frozen")
PHASE_RULES["ship"] = {
    "PRINCIPLES.md": ["Production safeguards", "Reviews, vision & confidence", "Composed skills", "Communication"],
    "MECHANISMS.md": ["Re-run semantics", "Declined runs", "Status"],
}
PHASE_CLOSE_RULES["ship"] = {
    "PRINCIPLES.md": ["The exit-criteria gate"],
    "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"],
}
CLOSE_STEPS["ship"] = (
    "the version in the release record against every manifest surface (package version, CHANGELOG heading, tag)",
    "the whole spine against what shipped - a doc claiming a capability the code lacks is the finding",
    "the release row's reviews, gate count, skipped phases, record, rollback and PR")


def ship_diff(base: Path) -> tuple[str, list[str], list[str], list[str]]:
    """The merge base, the files changed since it (committed or not), the commits, and the security words in them."""
    default = next((b for b in ("main", "master") if git(base, "rev-parse", "--verify", "--quiet", b)), "main")
    mb = git(base, "merge-base", "HEAD", default)
    if not mb or mb == git(base, "rev-parse", "HEAD"):  # on the default branch: since the last release tag, else all
        mb = git(base, "describe", "--tags", "--abbrev=0") or ""
    changed = git(base, "diff", "--name-only", mb).splitlines() if mb else git(base, "ls-files").splitlines()
    commits = git(base, "log", "--oneline", f"{mb}..HEAD").splitlines() if mb else []
    text = " ".join(changed) + (git(base, "diff", mb)[:200_000] if mb else "")
    return mb, changed, commits, sorted({w.lower() for w in SECURITY_TICKET.findall(text)})


def ship_release_gaps(st: "Status", a, base: Path) -> list[str]:
    """What `status.py release` refuses: round 1 named with its count (or the ticket row it cites), round 2 run or
    its skip recorded, the gate run once, security on an auth/data diff, the dependency scan, every unpassed phase in
    --skipped, a release record that exists, the rollback /deploy wrote, the docs named, and a PR or local-only."""
    gaps, rv = [], a.reviews
    r1 = REVIEW_COUNT.search(rv)
    if not r1 and not SHIP_CITED.search(rv):
        gaps.append("--reviews names no round 1 - `R1 (diff) 4 findings` / `R1 (diff) clean`, or the ticket row whose "
                    "review covers this unchanged diff (`cited M1-A-01`)")
    if r1 and r1.group(1) and int(r1.group(1)) > 0 and not re.search(r"\bR2\b", rv):
        gaps.append("--reviews: round 1 found something and round 2 is not recorded - `R2 (files R1's fixes touched) "
                    "clean`, or `R2 skipped by the user: <reason>`")
    if not SHIP_GATE.search(rv):
        gaps.append("--reviews has no gate count - `gate ×1 <sha>` (the full gate once, after the last fix), or `gate "
                    "cited <ticket>` when nothing changed since /build's")
    sec = ship_diff(base)[3] if git_dir(base) else []
    if sec and not re.search(r"(?i)\bsec(?:urity)?\b", rv):
        gaps.append(f"--reviews has no security review and the diff touches {', '.join(sec[:5])} - `sec R1 clean` "
                    f"(/security-review or the equivalent pass), or the ticket row that already ran it")
    if not re.search(r"(?i)\bdeps?\b|\baudit\b|\bvuln", rv):
        gaps.append("--reviews has no dependency scan - `deps: <scanner> <count>` (the start names the command), or "
                    "`deps: not run - <why>`")
    if re.match(r"(?i)\s*none\b", a.skipped):
        for p in ("dev-check", "test", "eval"):
            r = st.phase(p)
            if not (r[1] == "filled" and r[4] == "pass"):
                gaps.append(f"--skipped says none, but #{p} is {r[1]}{' ' + r[4] if r[4] else ''} - name /{p} in "
                            f"--skipped with the reason (a docs-only change or a revert may skip /eval, nothing else)")
    rec, ch = a.record.strip(), base / "CHANGELOG.md"
    if re.match(r"(?i)n/?a\b", rec):
        if not re.search(r"(?i)recorded in\s+\S", rec):
            gaps.append("--record says n/a without where releases are recorded - `n/a — releases recorded in <X>`")
    elif ch.is_file() and SHIP_RETIRED.search("\n".join(read_text(ch).splitlines()[:8])):
        gaps.append("CHANGELOG.md is retired (its top lines say so) - never add to it: `n/a — releases recorded in "
                    "<X>`, X from #Project policy or the user")
    elif re.search(r"(?i)changelog", rec) and not ch.is_file():
        gaps.append("--record names a CHANGELOG entry and there is no CHANGELOG.md - write the entry, or record where "
                    "this project records releases (`n/a — releases recorded in <X>`)")
    if st.phase("deploy")[1] == "filled" and "deployment.md" not in a.rollback:
        gaps.append("--rollback does not cite docs/deployment.md - /deploy recorded the rollback path there (§7 "
                    "Rollback): take it from there, never a new one per release")
    if not re.search(r"(?i)readme|product\.md|docs/|claims?|features?|spine", a.docs):
        gaps.append("--docs does not say what was reconciled - the README, PRODUCT.md and docs/features/* claims, "
                    "each checked against the code")
    if not git(base, "remote", "get-url", "origin"):
        if not re.search(r"(?i)local", a.pr):
            gaps.append("--pr: no git remote - a local-only release records `local-only: <branch> @ <sha>` (no PR, "
                        "no issue to close)")
    elif not (re.search(r"https?://|#\d+", a.pr) or (getattr(a, "dry_run", False) and
                                                       re.match(r"(?i)\s*(pending|-)\s*$", a.pr))):
        gaps.append("--pr has no link - the PR's URL or #number (`--pr pending` only with --dry-run, before it opens)")
    return gaps


def ship_close_text(path: Path, today: str, commit: str | None) -> str:
    """After the release row is written: the save, the rest of the close, the handoff - from a re-read STATUS.md,
    where #ship is now filled (DERIVED), so the handoff names /learn and not /ship again."""
    st = Status.load(path)
    st.today = today
    saved = save_commit(st.base, commit) if commit else None
    return "\n".join(x for x in (saved, close_steps_text("ship", saved), handoff_card(st, "ship")) if x)


def ship_start_text(st: "Status") -> str:
    """`next --phase ship`: the diff, what /build already reviewed, the gates, the project's policy, the release
    record's home, the rollback /deploy wrote, the remote, and the commands - one call instead of three rule files,
    PRODUCT.md whole and a round of git calls."""
    base = st.base or Path(".")
    secs = releaseops_spine(base)
    mb, changed, commits, sec = ship_diff(base) if git_dir(base) else ("", [], [], [])
    rows = st.rows["Tickets"][-8:]
    gates = [(p, *st.phase(p)[1:2], st.phase(p)[4]) for p in ("dev-check", "test", "eval")]
    unmet = [g for g in gates if not (g[1] == "filled" and g[2] == "pass")]
    # product_sections keys a heading by its first word: "## Project policy" is "Project"
    policy = [ln.strip() for ln in secs.get("Project", "").splitlines()
              if re.match(r"\s*- \*\*", ln) and not re.search(r":\*\*\s*(<.*>)?\s*$", ln)]
    ch = base / "CHANGELOG.md"
    top = " / ".join(l.strip() for l in read_text(ch).splitlines()[:4] if l.strip())[:220] if ch.is_file() else ""
    rollback = releaseops_field(section_fields(secs.get("Deployment", "")), r"^rollback") or ""
    guards = [p.relative_to(base).as_posix() for p in project_files(base, {".py", ".ts", ".js"})
              if is_test(p.relative_to(base).as_posix()) and re.search(r"(?i)placeholder|change-?me|boot guard",
                                                                        read_text(p))][:3]
    deps = ("uv run pip-audit" if (base / "uv.lock").is_file() else "pip-audit" if (base / "pyproject.toml").is_file()
            or (base / "requirements.txt").is_file() else "npm audit --omit=dev" if (base / "package.json").is_file()
            else "")
    gate, recipe = tool_file("build", "gate.py"), check_recipe(base)
    out = [f"/ship start - {git(base, 'rev-parse', '--abbrev-ref', 'HEAD')} @ {git(base, 'rev-parse', '--short', 'HEAD')}"
           f"; read nothing else whole:",
           f"  - The diff since {mb[:9] or 'the first commit'}: {len(changed)} file(s), {len(commits)} commit(s): "
           + (", ".join(changed[:15]) + (" ..." if len(changed) > 15 else "") or "nothing changed - nothing to ship"),
           "  - What was already reviewed (Step 0's three paths - unchanged since that review: cite the row and skip; "
           "changed: re-run and name what changed; none: run it):\n"
           + ("\n".join(f"      {r[0]} {r[1]}: review {r[5][:120] or '(none recorded)'}" for r in rows)
              or "      no ticket row - no recorded review: round 1 runs"),
           "  - Security surface in the diff: " + (", ".join(sec[:8]) + " - /security-review inside a subagent (or the "
                                                   "equivalent pass), unless a ticket row already ran it on this "
                                                   "unchanged surface" if sec else "none named"),
           "  - Gates: " + " · ".join(f"#{p}: {s}{' ' + v if v else ''}" for p, s, v in gates)
           + (f" - not passed: {', '.join('/' + g[0] for g in unmet)}. Name each, recommend it; shipping anyway puts it "
              f"in --skipped with the reason (a change to what the product does needs its tests)" if unmet else
              " - all passed"),
           "  - #Project policy: " + ("; ".join(policy) if policy else "none declared - the defaults (the user merges "
                                                                           "when they say so; CHANGELOG.md)"),
           "  - Release record: " + (f"CHANGELOG.md - its top: {top}" + (" - RETIRED: record `n/a — releases recorded "
                                                                         "in <X>`" if SHIP_RETIRED.search(top) else "")
                                     if ch.is_file() else "no CHANGELOG.md - #Project policy names the record, else "
                                     "ask the user where releases are recorded"),
           f"  - Rollback: {'from docs/deployment.md §7 (/deploy ran): ' + rollback[:160] if rollback.strip() else 'no /deploy record - state it: revert PR · migration-down · flag-off (a data migration has no automatic down)'}",
           "  - No placeholder can boot this build: " + (f"the guard tests {', '.join(guards)} run in the gate - a red "
                                                         f"one stops the release" if guards else
                                                         "no guard test found - say so in the close (UNVERIFIED)"),
           f"  - Dependency scan: {deps or 'name the scanner for this stack'} - its count goes in --reviews as `deps: "
           f"<scanner> <count>` (not run: `deps: not run - <why>`)",
           (f"  - Gate - the full checks ONCE, after the last fix: python \"{gate.as_posix()}\" "
            f"\"{recipe[0] if recipe else '<the project check command>'}\"" if gate else
            "  - Gate - the project's full checks ONCE, after the last fix"),
           "  " + remote_line(base).replace("\n", " "),
           "  - /ship reviews, fixes what the reviews find, reconciles docs and releases; it starts no new feature and "
           "never merges without the user's explicit word (merging is deploying when the host builds on merge).",
           # unrequested checks on logged runs: mypy, a 4.8-min secret scan, a third prove (~0.6M each)
           "  - Run only: the reviews, the gate ONCE after the last fix, the dependency scan named above, and the test "
           "files that import a module you changed while fixing - no other linter, type checker or scan of your own.",
           # waste audit W56: a confirmation in a turn of its own cost ~680K across 4 tools
           "  - Owner turns: round 1's result message also asks round 2 (yes/no, Recommended per Step 2) - and the "
           "save goes in the same message as the dry run's result: \"Open the PR and save (Recommended)\" · \"Open the "
           "PR, don't save yet\" · \"Change something\".",
           "  - The order: reviews (round 1; round 2 is the user's call; no round 3) → security → docs → rollback → "
           "confidence → `status.py release ... --pr pending --dry-run` (fix every gap it names; a gap here means do "
           "not open the PR) → open the PR (`Closes #N` in the body) → `status.py release ... --pr <link> --commit "
           "\"<one line>\"` records, saves and prints the rest of the close. No remote: no PR - `--pr \"local-only: "
           "<branch> @ <sha>\"`. Stopping at an unmet gate: `status.py set ship declined --reason \"<what was "
           "missing>\" --gate <phase>`.",
           "  - `status.py release` refuses, every problem in one list: no round 1 (count or cited ticket) · round 1 "
           "found something and round 2 not recorded · no `gate ×1` · an auth/data diff with no security review · no "
           "dependency scan · --skipped none while a gate is not passed · n/a without where releases are recorded · a "
           "retired or missing CHANGELOG named · a rollback not from docs/deployment.md when /deploy ran · --docs "
           "naming nothing · no PR link (or local-only without a remote) · a cell over 200 characters."]
    return "\n".join(out) + "\n\n" + releaseops_rules_text(st, "ship", bool(unmet))


# /deploy: executes the runtime target #Architecture recorded. It had never had a live run; the logged deploys it was
# built from (case-files-deploy.md) each failed on something a file can show: an env list retyped by hand that had
# drifted to half, a build-time value unset in the built site, two passwords in the built bundle, previews on
# production data. The start generates the env list from the code; the close checks the record and the files.
DEPLOY_FIELDS = (("Host", r"^host"), ("Live URL · why now", r"^live url"), ("Env vars set on the host", r"^env vars"),
                 ("Migrations on deploy", r"^migrations"), ("Who can get in", r"^who can get in"),
                 ("Proof it answers", r"^proof"), ("Rollback path", r"^rollback"), ("Known gaps", r"^known gaps"))
DEPLOY_DOC_SECTIONS = (("1. Build and start", r"build and start"), ("2. Environment variables", r"environment var"),
                       ("3. Migrations on deploy", r"migrations"), ("4. First deploy", r"first deploy"),
                       ("5. Who can get in", r"who can get in"), ("6. Proof it works", r"proof"),
                       ("7. Rollback", r"rollback"), ("8. Known gaps", r"known gaps"))
ENV_READ = re.compile(r"""os\.environ(?:\.get)?\s*[\[(]\s*["']([A-Z][A-Z0-9_]+)["']|os\.getenv\(\s*["']([A-Z][A-Z0-9_]+)"""
                      r"""["']|process\.env\.([A-Z][A-Z0-9_]+)|process\.env\[\s*["']([A-Z][A-Z0-9_]+)["']|"""
                      r"""import\.meta\.env\.([A-Z][A-Z0-9_]+)|Deno\.env\.get\(\s*["']([A-Z][A-Z0-9_]+)""")
ENV_BUILD = re.compile(r"^(?:VITE_|NEXT_PUBLIC_|PUBLIC_|REACT_APP_|NUXT_PUBLIC_|EXPO_PUBLIC_)")
ENV_PLATFORM = {"NODE_ENV", "PORT", "HOME", "PATH", "PWD", "CI", "DEV", "PROD", "MODE", "SSR", "BASE_URL"}
SECRET_VALUE = re.compile(r"(?i)\bsk-[a-z0-9_-]{16,}|\bAKIA[0-9A-Z]{16}\b|\bghp_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE "
                          r"KEY|\bxox[bap]-[A-Za-z0-9-]{10,}|(?:password|passwd|secret|api_?key|token)[\"']?\s*[:=]\s*"
                          r"[\"'][^\"'\s<>{}$]{8,}[\"']")
BUILT_DIRS = ("dist", "build", "out", ".next", ".output")
PHASE_RULES["deploy"] = {  # §Production safeguards: secrets never pushed, fail-closed, no hardcoding
    "PRINCIPLES.md": ["Production safeguards", "Communication"],
    "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status"],
}
PHASE_CLOSE_RULES["deploy"] = {
    "PRINCIPLES.md": ["The exit-criteria gate"],
    "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"],
}
CLOSE_STEPS["deploy"] = (
    "every number against #Vision and #Architecture: a free-tier limit or cost the north-star volume would break",
    "#Architecture's runtime target, data custody and migrations approach (a different host, or a Dockerfile where it "
    "decided none, is a contradiction) and STRUCTURE.md's tree",
    "the #Deployment fields, docs/deployment.md's eight sections, the env list against the code's reads, the proof "
    "line and the built output")


def deploy_env(base: Path) -> tuple[dict[str, str], list[str]]:
    """Every variable the code reads (name -> `build` or `boot`, `test only` when only tests read it), and the names
    .env.example lists - so the env list is generated, never retyped (case file: The env list that had drifted to
    half)."""
    reads: dict[str, set[str]] = {}
    for p in project_files(base, {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte"}):
        rel = p.relative_to(base).as_posix()
        if rel.split("/")[0] in BUILT_DIRS:
            continue
        for m in ENV_READ.finditer(read_text(p)):
            name = next(g for g in m.groups() if g)
            if name not in ENV_PLATFORM:
                reads.setdefault(name, set()).add("test" if is_test(rel) else
                                                  "build" if m.group(5) or ENV_BUILD.match(name) else "boot")
    kinds = {n: ("test only" if k == {"test"} else "build" if "build" in k else "boot") for n, k in reads.items()}
    ex = base / ".env.example"
    listed = [m.group(1) for m in re.finditer(r"(?m)^\s*(?:export\s+)?([A-Z][A-Z0-9_]+)\s*=", read_text(ex))] \
        if ex.is_file() else []
    return kinds, listed


def deploy_gaps(base: Path, st: "Status") -> list[str]:
    """What `set deploy filled` refuses: every field answered, the host carried with its provenance, docs/deployment.md
    as the template's eight sections, every variable the code reads in it, no secret value written, a proof line
    that hit the URL (a static site: two; the owner's machine: a local one), previews and - with #Dev-complete empty -
    spend in `Who can get in`, a migration failure path, and no credential in the built output."""
    secs = releaseops_spine(base)
    f = section_fields(secs.get("Deployment", ""))
    gaps = releaseops_empty(f, DEPLOY_FIELDS, "Deployment")
    host, url = releaseops_field(f, r"^host") or "", releaseops_field(f, r"^live url") or ""
    who, proof = releaseops_field(f, r"^who can get in") or "", releaseops_field(f, r"^proof") or ""
    mig = releaseops_field(f, r"^migrations") or ""
    if not re.search(r"(?i)runtime target|\bhost\b|deploy", secs.get("Architecture", "")):
        gaps.append("#Architecture records no runtime target - run a narrow /architect for it first, or record the "
                    "user's reason: status.py bypass --from deploy --gate architect --reason \"<their words>\"")
    # #Architecture marks a host only when it was "default taken" (templates/PRODUCT.md): an unmarked host is the
    # user's, and a word-for-word copy of it carries no mark - refusing that was a false refusal (waste audit W53)
    if host and re.search(r"(?i)default taken", secs.get("Architecture", "")) and \
            not re.search(r"(?i)default taken", host):
        gaps.append("#Deployment `Host` has no provenance - #Architecture marks it `default taken, not user-chosen`: "
                    "copy the host with that mark, word for word")
    doc_p = base / "docs" / "deployment.md"
    doc = read_text(doc_p) if doc_p.is_file() else ""
    if not doc:
        gaps.append("no docs/deployment.md - fill templates/deployment.md (all eight sections) there")
    else:
        gaps += doc_order_gaps(doc, DEPLOY_DOC_SECTIONS, "docs/deployment.md", "templates/deployment.md")
        gaps += releaseops_owner_gaps(base, "docs/deployment.md")
        left = sorted(set(re.findall(r"`<(?:unit|command|url|VAR|step|runtime target|YYYY-MM-DD)>`", doc)))
        if left:
            gaps.append(f"docs/deployment.md still holds template placeholders: {', '.join(left)} - fill each")
    kinds, _ = deploy_env(base)
    written = doc + "\n" + (releaseops_field(f, r"^env vars") or "")
    missing = [n for n, k in sorted(kinds.items()) if k != "test only" and not re.search(rf"\b{n}\b", written)]
    if missing:
        gaps.append(f"the code reads {', '.join(missing[:10])}{' ...' if len(missing) > 10 else ''} and docs/deployment.md "
                    f"§2 does not list it - the list is generated from what the code reads (the start printed it)")
    for name, text in (("docs/deployment.md", doc), ("#Deployment", secs.get("Deployment", ""))):
        if SECRET_VALUE.search(text):
            gaps.append(f"{name} holds what looks like a secret value - name the variable and how to generate it; the "
                        f"user pastes the value into the host, never into a file")
    own = re.search(r"(?i)own machine|localhost|not public", url)
    if proof and not EVIDENCE.search(proof) and "owner-verified" not in proof:
        gaps.append("#Deployment `Proof it answers` has no `evidence:` line - the request you sent and what came back "
                    "(`evidence: curl -s https://<url>/health → 200 ok · docs/deployment.md · <date>`)")
    elif proof and not own and not re.search(r"https://(?!localhost|127\.)", proof):
        gaps.append("#Deployment `Proof it answers` hit no public https URL - the user's own machine: say `own machine "
                    "- not public, reachable by <who>` in `Live URL` and prove it locally")
    if proof and re.search(r"(?i)static", host) and len(re.findall(r"https?://", proof)) < 2:
        gaps.append("a static site's proof needs the root AND a deep link answering 200 (a single-page app without the "
                    "fallback to index.html 404s every deep link)")
    if who and not re.search(r"(?i)preview", who):
        gaps.append("#Deployment `Who can get in` does not say what happens to preview deployments - off, or on "
                    "against their own backend and data")
    dc = st.phase("dev-check")
    if who and dc[1] != "filled" and not re.search(r"(?i)spend|cost|sign-?up|paid", who):
        gaps.append("#Dev-complete is empty and `Who can get in` does not record what a stranger can reach and spend - "
                    "ask the user before the URL is public, and record the answer")
    if mig and not re.search(r"(?i)fail|abort|none|no database|not applicable", mig):
        gaps.append("#Deployment `Migrations on deploy` does not say what happens when the migration fails")
    for d in BUILT_DIRS:
        for p in ((base / d).rglob("*") if (base / d).is_dir() else []):
            if p.suffix in (".js", ".html", ".map", ".json", ".css") and SECRET_VALUE.search(read_text(p)):
                gaps.append(f"the built output carries a credential-like value in {p.relative_to(base).as_posix()} - "
                            f"remove it from the source, rebuild, and rotate it (it shipped to every visitor)")
                break
    return gaps


def deploy_start_text(st: "Status") -> str:
    """`next --phase deploy`: the recorded host per unit, the milestone that needs the URL, the env list generated
    from the code with .env.example's differences, the host files, the pins, the questions and what the close
    refuses - one call instead of three rule files and PRODUCT.md read whole."""
    base = st.base or Path(".")
    secs = releaseops_spine(base)
    arch = [ln.strip()[:220] for ln in secs.get("Architecture", "").splitlines()
            if re.search(r"(?i)runtime target|\bhost|deploy|data custody|migration|region|free tier|cost", ln)][:10]
    found = [ln.strip()[:200] for ln in secs.get("Foundation", "").splitlines()
             if re.search(r"(?i)guard|placeholder|health|config|start|entry", ln)][:6]
    plan = [ln.strip()[:200] for ln in secs.get("Plan", "").splitlines()
            if re.search(r"(?i)/deploy|public url|deployed url|reachable|go live|live via", ln)][:4]
    kinds, listed = deploy_env(base)
    boot = sorted(n for n, k in kinds.items() if k == "boot")
    build = sorted(n for n, k in kinds.items() if k == "build")
    test = sorted(n for n, k in kinds.items() if k == "test only")
    lacks = sorted(n for n in kinds if kinds[n] != "test only" and n not in listed)
    unread = sorted(n for n in listed if n not in kinds)
    hostfiles = [n for n in ("Dockerfile", "docker-compose.yml", "compose.yaml", "Procfile", "render.yaml", "fly.toml",
                             "vercel.json", "netlify.toml", "railway.json", "app.yaml", "wrangler.toml")
                 if (base / n).is_file()]
    pins = []
    pkg = base / "package.json"
    if pkg.is_file():
        try:
            j = json.loads(read_text(pkg))
            pins += [f"engines {j['engines']}"] if j.get("engines") else []
            pins += [f"packageManager {j['packageManager']}"] if j.get("packageManager") else []
        except ValueError:
            pass
    for n in (".python-version", ".nvmrc", ".node-version"):
        if (base / n).is_file():
            pins.append(f"{n} {read_text(base / n).strip()[:20]}")
    dc = st.phase("dev-check")
    tpl = tool_file("templates", "deployment.md")
    fields = product_sections(read_text(tool_file("templates", "PRODUCT.md"))).get("Deployment", "") \
        if tool_file("templates", "PRODUCT.md") else ""
    fields = "\n".join("      " + l for l in fields.splitlines() if l.startswith("- **"))
    out = ["/deploy start - execute these; read nothing else whole:",
           "  - #Architecture (the host per unit is COPIED from here, never re-decided):\n"
           + ("\n".join("      " + a for a in arch) or "      NO runtime target recorded - offer a narrow /architect "
                                                       "for it first (allow override, recorded)"),
           "  - #Foundation (the boot guard - an unset boot variable is refused by name, by design):\n"
           + ("\n".join("      " + x for x in found) or "      (nothing about the guard recorded)"),
           "  - Why now - #Plan lines that need a URL: " + (" | ".join(plan) if plan else "none - ask the user's reason"),
           f"  - #Dev-complete: {dc[1]}{' ' + dc[4] if dc[4] else ''}" + ("" if dc[1] == "filled" else
           " - EMPTY: deploying an unfinished product is legitimate but a choice; ask what a stranger can reach and "
           "spend once the URL is public, and record the answer"),
           "  - The env list, GENERATED from what the code reads (copy it into docs/deployment.md §2; mark each secret "
           "or not, committed or pasted):\n"
           f"      read at boot: {', '.join(boot) or 'none found'}\n"
           f"      read at build (ships to every visitor - committed, never a secret; check each in the built output): "
           f"{', '.join(build) or 'none found'}\n"
           f"      test only (not the host's - leave out): {', '.join(test) or 'none'}\n"
           f"      .env.example lacks: {', '.join(lacks) or 'none'} · lists but nothing reads: {', '.join(unread) or 'none'}",
           f"  - Host files in the repo: {', '.join(hostfiles) or 'none'} · runtime pins: {'; '.join(pins) or 'none found'}"
           " - check the host's build image against the pins",
           f"  - Template: fill {tpl.as_posix() if tpl else 'templates/deployment.md'} into docs/deployment.md - all "
           f"eight `##` sections in order; one that does not apply holds `Not applicable: <reason>`",
           "  - /deploy executes the recorded host: it never re-decides it, never writes or asks for a secret (the "
           "user pastes values into the host), never merges without the user's explicit word (merging is deploying "
           "when the host builds on merge), and never writes a DNS route into committed config.",
           # waste audit W31/W33/W64: research in the main conversation 2-3.7x; a raw-JSON fetch of 124K chars
           "  - The host's current product and limits: load your web tool in your first reply; at most 1 search and 2 "
           "documentation pages (never a raw JSON or API page); write down product · link · date checked · limits.",
           # waste audit W3: one slow write checked 9 times on Codex (~1.2M); Antigravity 14.8% of tokens polling
           "  - The host is building or DNS is spreading: ONE long wait (the tool's longest), then one request - "
           "never repeated status checks or curl loops; still not up: the `running` state with the user's date.",
           "  - Run only: the host's build (it is the build), one request per proof line, the migrations the way "
           "docs/deployment.md says - no test suite, lint or scan of your own.",
           "  - #Deployment is these fields, labels as written, in a scratch file outside the repo:\n" + fields,
           "  - `set deploy filled` refuses, every problem in one list: an empty field · a host #Architecture marks "
           "`(default taken, not user-chosen)` copied without that mark (an unmarked host is the user's: copy it as "
           "it is) · no docs/deployment.md, a template section missing or out of order, a placeholder left · a "
           "variable the code reads missing from it · a secret value written anywhere · no `evidence:` proof line, "
           "or none hitting a public https URL (own machine: `own machine - not public` in Live URL) · a static site "
           "without root AND deep link · previews not addressed · with #Dev-complete empty, spend not recorded · no "
           "migration failure path · a credential-like value in the built output. Blocked by a quota, DNS or a paid "
           "tier: `status.py set deploy running --due <the date the USER gives> --reason \"<what blocks>\"`.",
           "  - Two rounds, each ONE message (numbered lines to answer by typing, or your ask tool's form), after the "
           "one-line build/deploy explanation. Round 1, before the first deploy: 1. why the URL is needed now (the "
           "#Plan milestone, or the user's reason) · 2. with #Dev-complete empty: who can sign up and what each action "
           "spends · 3. preview deployments: off (Recommended), or on against their own backend · 4. a custom domain "
           "(the user's step at the dashboard) or the host's URL · 5. what a visitor can see (vendor names, account "
           "names in the built site and its calls) - fine, or hidden behind our domain · 6. a proxy, CDN or "
           "forwarder in front of the backend: does the backend key anything on the caller's IP, origin or host? "
           "(one round, not later turns: each extra turn re-sends the whole conversation). Round 2, after the "
           "deploy and the proof: what runs, the "
           "proof, any Step 3c clash, and \"Anything to change? If not: Save this version of your project? (yes / "
           "no)\" as \"Looks good - save (Recommended)\" · \"Change something\".",
           "  - docs/deployment.md ends with `## Owner's answers`: round 1's answers word for word, numbered as asked. "
           "A long command output goes to a scratch file; cite its last lines in the evidence line.",
           "  - Then ONE call: `set deploy filled --section-from <file> --commit \"<one line>\"` (no `--commit` on a "
           "no) records, saves and prints the rest of the close. Stopping at an unmet gate: `status.py set deploy "
           "declined --reason \"<what was missing>\" --gate <phase>`.",
           "  - Order (each call re-sends all before it): reads and round 1 before any deploy command; "
           "docs/deployment.md and the section file are the last writes, in ONE call after the proof; `set` in the "
           "call after the round-2 yes - no check of your own between (`set` checks the template, variables, secrets)."]
    # §Context hygiene (2.1 KB) is no longer printed whole: its first items repeat RELEASEOPS_CLOSE and run_habits,
    # re-sent on every call (cost review: a start cut by half saved 118-171K a run); its one new rule is above
    return "\n".join(out) + "\n\n" + releaseops_rules_text(st, "deploy", not arch)


RELEASEOPS_START = {"eval": eval_start_text, "learn": learn_start_text, "ship": ship_start_text,
                    "deploy": deploy_start_text}
RELEASEOPS_GAPS = {"eval": lambda base, st, a: eval_gaps(base, st, a.verdict),
                   "learn": lambda base, st, a: learn_gaps(base, st),
                   "deploy": lambda base, st, a: deploy_gaps(base, st)}
RELEASEOPS_WARN = {"eval": eval_warnings}
# what the Antigravity start file holds (fit_start's START_HOLDS is defined further down; the start copies it in)
RELEASEOPS_HOLDS = {"eval": "the #Vision lines /eval measures against, the gates, the\n    #Evaluation fields, the "
                            "two rounds, this phase's rules",
                    "learn": "the goal, what shipped, #Evaluation, the non-goals, the\n    #Learnings fields, the two "
                             "rounds, this phase's rules",
                    "ship": "the diff, the reviews already run, the gates, the policy,\n    the release record, the "
                            "order, what `release` refuses, this phase's rules",
                    "deploy": "the recorded host, the env list from the code, the\n    #Deployment fields, the two "
                              "rounds, this phase's rules"}
RELEASEOPS_HEAD["ship"] =("This phase records ONE release row - `status.py release ... --dry-run` BEFORE the PR opens "
                           "(every gap at once, nothing written), then `status.py release ... --commit \"<one line>\"` "
                           "after it: it saves and prints the rest of the close (no git call of your own).",
                           ) + RELEASEOPS_CLOSE


# ---- /plan (P1, P2, P4, P8, P20) -------------------------------------------------------------------------------
# A logged Claude /plan read PRINCIPLES.md, MECHANISMS.md, PRODUCT.md and three companions whole (~74 KB) before its
# first question and re-sent them on 13 calls (1.12M tokens); a logged Gemini /plan asked nothing, invented the
# timeline, cited #Vision as evidence and receipted its own docs/plan.md. The start prints the rules the questions
# need and the spine facts the plan is built from; the close's rules print at `set plan filled`, which refuses
# what a file can show - every problem in one list, on /plan's own close only (never phase_check: a plan filled
# under older rules is never blocked later).
PHASE_RULES["plan"] = {
    "PRINCIPLES.md": ["Per-feature contract", "Production-readiness concern areas", "Documentation-driven",
                      "Communication"],
    "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status"],
}
PHASE_CLOSE_RULES["plan"] = {
    "PRINCIPLES.md": ["The exit-criteria gate"],
    "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"],
    "MECHANISMS-ON-DEMAND.md": ["Section is a record", "Read receipt"],
}
PLAN_FIELDS = (("the milestones", r"^phases|milestones"), ("the timeline", r"^timeline"),
               ("the exit criteria", r"^exit criteria"), ("the four-risks rows", r"four[- ]risks"),
               ("the usability checkpoint", r"^usability"), ("the concern-area coverage", r"^concern"))
PLAN_AREAS = {"security": r"security", "ai-specific": r"ai(?:-specific)?", "observability": r"observability",
              "developer-experience": r"developer[- ]experience|dx", "testing": r"testing",
              "infra": r"infra(?:structure)?", "documentation": r"documentation|docs", "product": r"product"}
PLAN_MARK = r"(?i)^\W*(M\d+)\b"  # a line that starts with a milestone id: "- **M1:**", "| M1 ⧗ |", "M2 Pilot"
PLAN_NEEDS = r"(?i)\b(?:needs?|requires?|reachable|delivered by|prerequisites?|depends on)\b"
PLAN_MARKED = r"(?i)\b(?:proposed|derived)\b"  # `(proposed)`, `(derived: 6 wk × 20 h)`, "derived from"
PLAN_ANSWERS = re.compile(r"(?im)^#{1,6}\s.*\banswer")
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


def plan_field_lines(body: str) -> dict[str, list[str]]:
    """Each #Plan field's lines (its first line without the label), `**Label:**` with or without the `- ` (P8: two
    logged tools wrote it bare and every /vision field read as empty)."""
    out: dict[str, list[str]] = {}
    label = None
    for line in body.splitlines():
        m = re.match(r"^(?:[-*]\s+)?\*\*(.+?)\*\*:?\s*(.*)$", line) if not line.startswith((" ", "\t")) else None
        if m:
            label = m.group(1).strip().rstrip(":")
            out[label] = [m.group(2)] if m.group(2).strip() else []
        elif label and line.strip():
            out[label].append(line)
    return out


def plan_segments(lines: list[str]) -> dict[str, str]:
    """Milestone id -> its text: the line that starts with the id and the lines under it, up to the next id."""
    out: dict[str, str] = {}
    cur = None
    for line in lines:
        m = re.match(PLAN_MARK, line)
        if m:
            cur = m.group(1).upper()
            out[cur] = out.get(cur, "") + "\n" + line
        elif cur:
            out[cur] += "\n" + line
    return out


def plan_dates(text: str) -> list[str]:
    """Every date in the text as YYYY-MM-DD, in order; a bare `11-22` after a dated one takes its year (rolling over
    at a new year), as a timeline writes `2026-10-12 → 11-22`."""
    out, year, last = [], None, ""
    for m in re.finditer(r"\b(20\d\d)-(\d\d)(?:-(\d\d))?\b|(?<![\d-])(\d\d)-(\d\d)\b(?!-)", text):
        if m.group(1):
            year = int(m.group(1))
            d = f"{year}-{m.group(2)}-{m.group(3) or '28'}"
        elif year and 1 <= int(m.group(4)) <= 12:
            d = f"{year}-{m.group(4)}-{m.group(5)}"
            if d < last:
                year += 1
                d = f"{year}-{m.group(4)}-{m.group(5)}"
        else:
            continue
        out.append(d)
        last = d
    return out


def north_star_date(vision: str) -> str | None:
    """The #Vision target's date: a full date, `<month> <year>`, or a bare year (its last day)."""
    target = " ".join(v for k, v in section_fields(re.sub(r"(?m)^\*\*", "- **", vision)).items()
                      if re.search(r"target", k, re.I))
    full = plan_dates(target)
    if full:
        return full[-1]
    m = re.search(r"(?i)\b(" + "|".join(MONTHS) + r")[a-z]*\.?\s+(20\d\d)\b", target)
    if m:
        return f"{m.group(2)}-{MONTHS.index(m.group(1).lower()[:3]) + 1:02d}-28"
    m = re.search(r"\b(20\d\d)\b", target)
    return f"{m.group(1)}-12-31" if m else None


def plan_numbers(line: str) -> list[str]:
    """The numbers a plan line states, without ids, dates, paths and references (M1, #3, 2026-10-12, `docs/x.md`)."""
    s = re.sub(r"`[^`]*`|\]\([^)]*\)|https?://\S+", " ", line)
    s = re.sub(r"\b20\d\d-\d\d(?:-\d\d)?\b|(?<![\d-])\d\d-\d\d\b|\bM\d+\b|#\d+|\b[QH][1-4]\b|§\s*\d+(?:\.\d+)*"
               r"|\b(?:run|step|question|item|round|phase)\s+\d+", " ", s, flags=re.I)
    return re.findall(r"\d+(?:[.,]\d+)?", s)


# #Vision's Constraints field (next.55) names the rules that apply, the languages and the data source. Every
# playbook run of a logged HR product missed them, and no plan scheduled them (the /plan session's review, 2026-09-30):
# each named constraint gets a line in #Plan - a milestone that handles it, or `later - when <trigger>`.
CONSTRAINT_SKIP = {"AI", "EU", "The", "And", "For", "Only", "None", "Not", "Our", "Its", "All", "Any"}


def split_outside_brackets(text: str, sep: str) -> list[str]:
    """Split at `sep` only outside ( ) and [ ] - "GDPR (payslips, contracts)" is one item (a logged plan was
    refused for a bracket's second half)."""
    out, start, depth = [], 0, 0
    for m in re.finditer(rf"[()\[\]]|{sep}", text):
        tok = m.group(0)
        if tok in "([":
            depth += 1
        elif tok in ")]":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(text[start:m.start()])
            start = m.end()
    return out + [text[start:]]


def vision_constraints(vision: str) -> list[tuple[str, list[str]]]:
    """(constraint as written, the names that identify it) - a part with no proper name is left to judgement."""
    text = " ".join(v for k, v in section_fields(vision).items() if re.match(r"(?i)constraints?\b", k))
    out = []
    for part in (x.strip(" .") for x in split_outside_brackets(text, r"\s·\s|;|,|\n") if x.strip(" .")):
        keys = [w for w in re.findall(r"\b[A-Z][\w-]{2,}\b", part) if w not in CONSTRAINT_SKIP]
        if keys and not EMPTY_VALUE.match(part.lower()):
            out.append((part, keys))
    return out


def plan_gaps(base: Path, st: Status) -> list[str]:
    """What `set plan filled` needs, every problem named once in one list (P20)."""
    prod, comp = base / "PRODUCT.md", base / OWN_COMPANION["Plan"]
    secs = product_sections(prod.read_text(encoding="utf-8")) if prod.is_file() else {}
    clean = {k: re.sub(r"<!--.*?-->", "", v, flags=re.S) for k, v in secs.items()}
    fields = plan_field_lines(clean.get("Plan", ""))
    gaps: list[str] = []

    def field(rx: str) -> list[str]:
        return [l for k, v in fields.items() if re.search(rx, k, re.I) for l in v]

    for what, rx in PLAN_FIELDS:
        if not any(not EMPTY_VALUE.match(re.sub(r"[*_`\s]+", " ", l).strip().lower()) for l in field(rx)):
            gaps.append(f"#Plan field empty: {what}")
    phases = field(PLAN_FIELDS[0][1])
    ids = list(dict.fromkeys(m.group(1).upper() for l in phases for m in [re.match(PLAN_MARK, l)] if m)) or \
        list(dict.fromkeys(re.findall(r"\bM\d+\b", "\n".join(phases))))
    if phases and not ids:
        gaps.append("#Plan's milestones have no ids - start each milestone's line with M1, M2, ...")
    exits, risks = plan_segments(field(r"^exit criteria")), plan_segments(field(r"four[- ]risks"))
    for ms in ids:
        if ms not in exits:
            gaps.append(f"{ms} has no exit criterion (a line starting `{ms}:` under Exit criteria per milestone)")
        elif not re.search(PLAN_NEEDS, exits[ms]):
            gaps.append(f"{ms}'s exit criterion names no prerequisite - add `Needs: <what> (<the milestone or person "
                        f"that delivers it>)`, or `Needs: nothing outside this milestone`")
        if ms not in risks:
            gaps.append(f"{ms} has no four-risks row (a line starting `{ms}:` naming value, usability, feasibility "
                        f"or viability)")
        elif not re.search(r"(?i)value|usability|feasibility|viability", risks[ms]):
            gaps.append(f"{ms}'s four-risks row names none of value · usability · feasibility · viability")
    usab = " ".join(field(r"^usability"))
    if usab.strip() and ids and not set(re.findall(r"\bM\d+\b", usab)) & set(ids):
        gaps.append(f"the usability checkpoint names none of the plan's milestones ({', '.join(ids)})")
    cover = "\n".join(field(r"^concern"))
    if cover.strip():
        for area, rx in PLAN_AREAS.items():
            if not re.search(rf"(?i)\b(?:{rx})\b[^\n]{{0,80}}?\b(?:now|next|later|n/?-?a)\b", cover):
                gaps.append(f"concern-area coverage: {area} is not marked now / next / later / N-A")
    timeline = "\n".join(field(r"^timeline"))
    if timeline.strip():
        if not re.search(r"(?i)\d\s*(?:h|hrs?|hours?)\b\s*(?:/|a|per|each)?\s*(?:w|wk|week)\b|full[- ]time|"
                         r"part[- ]time", timeline):
            gaps.append("the Timeline has no capacity - who builds it and hours a week, from the user's answer 1 "
                        "(\"solo, ~20 h/week\")")
        if not plan_dates(timeline) and not re.search(r"(?i)\b(" + "|".join(MONTHS) + r")[a-z]*\.?\s+20\d\d\b",
                                                      timeline):
            gaps.append("the Timeline has no start date - the user's answer 2 (\"from 2026-10-12\")")
    plan_text = clean.get("Plan", "")
    dates = plan_dates(timeline)
    ns = north_star_date(clean.get("Vision", ""))
    if ns and dates and max(dates) > ns and not re.search(r"(?i)north[- ]?star", plan_text):
        gaps.append(f"the plan ends {max(dates)}, after the north-star date {ns} in #Vision, and #Plan says nothing "
                    f"about it - ask question 4 (keep it and flag it · move it · lower the interim bar) and write "
                    f"a `North star:` line under Timeline")
    v = st.phase("validate") if getattr(st, "rows", None) else ["validate", "empty", "", ""]
    if v[1] == "running" and v[3] and dates and min(dates) < v[3] and not re.search(r"(?i)provisional", plan_text):
        gaps.append(f"the timeline starts {min(dates)}, before the running experiment's due date {v[3]}, and #Plan "
                    f"is not marked provisional")
    four = "\n".join(field(r"four[- ]risks"))
    if re.search(r"#Vision\b", four):
        gaps.append("the four-risks rows cite #Vision - a vision is a claim, not evidence: cite a #Validation result "
                    "or the milestone that tests it")
    validation = [l for l in clean.get("Validation", "").splitlines() if l.strip()]
    validation_empty = v[1] not in ("running", "filled") and all(
        re.match(r"^\s*[-*]?\s*\*\*[^*]+\*\*:?\s*$", l) or l.lstrip().startswith("_") for l in validation)
    if validation_empty:
        if re.search(r"(?i)#?validation\b", four):
            gaps.append("the four-risks rows cite #Validation, which is empty (/validate did not run)")
        if not any(re.search(r"(?i)\bvalue\b", seg) for seg in risks.values()):
            gaps.append("#Validation is empty, so value (do they want it) is untested - a milestone's four-risks "
                        "row retires value, with the observable that proves it")
    if re.search(r"docs/plan\.md", " ".join(field(r"^read"))):
        gaps.append("the Read receipt quotes docs/plan.md, which this phase wrote - quote the input files it opened, "
                    "or write `Read: none - only PRODUCT.md sections`")
    doc = comp.read_text(encoding="utf-8") if comp.is_file() else ""
    answers = ""
    if not doc:
        gaps.append(f"no {OWN_COMPANION['Plan']} - it holds the user's answers word for word and the reasoning")
    else:
        m = PLAN_ANSWERS.search(doc)
        if m:
            nxt = re.search(r"(?m)^#{1,6}\s", doc[m.end():])
            answers = doc[m.end():m.end() + nxt.start()] if nxt else doc[m.end():]
        if not answers.strip():
            gaps.append(f"{OWN_COMPANION['Plan']} has no `## Owner's answers` block - the user's answers to the "
                        f"questions, word for word")
    known = set()
    for text in (answers, clean.get("Vision", ""), clean.get("Scope", ""), clean.get("Validation", "")):
        known |= {n.replace(",", "") for n in re.findall(r"\d+(?:[.,]\d+)?", text)}
    loose = []
    for rx in (r"^timeline", r"^exit criteria", r"four[- ]risks", r"^usability", r"^concern"):
        for l in field(rx):
            # a zero bar ("0 wrong refunds") is the absence of a failure, not an invented target
            new = [n for n in plan_numbers(l) if n.replace(",", "") not in known and float(n.replace(",", ".")) != 0]
            if new and not re.search(PLAN_MARKED, l):
                loose.append(f"{', '.join(dict.fromkeys(new))} in {l.strip()[:70]!r}")
    if loose:
        gaps.append(f"{len(loose)} #Plan line(s) state numbers that are not in the user's answers, #Vision, #Scope "
                    f"or #Validation, unmarked - end each such line `(proposed)` (a number you suggested; the user "
                    f"confirms it) or `(derived: <the sum>)`: " + " · ".join(loose[:6])
                    + (f" · and {len(loose) - 6} more" if len(loose) > 6 else ""))
    for part, keys in vision_constraints(clean.get("Vision", "")):
        if not any(re.search(rf"(?i)\b{re.escape(k)}\b", plan_text) for k in keys):
            gaps.append(f"#Vision's constraint {part[:60]!r} has no line in #Plan - a milestone that handles it, or "
                        f"`{keys[0]}: later - when <trigger>` under Concern-area coverage")
    for name, text in (("#Plan", plan_text), (OWN_COMPANION["Plan"], doc)):
        if LATEX.search(text):
            gaps.append(f"{name} has LaTeX ({LATEX.search(text).group(0)}...) - plain symbols (≥ ≤ →)")
    return gaps


def plan_start_text(st: Status) -> str:
    """`next --phase plan`: the spine facts the plan is built from, the fields, what the close refuses, and the rules
    the questions need - one call, instead of three rule files and PRODUCT.md read whole."""
    base = getattr(st, "base", None) or Path(".")
    prod = base / "PRODUCT.md"
    secs = product_sections(prod.read_text(encoding="utf-8")) if prod.is_file() else {}
    vision = section_fields(re.sub(r"(?m)^\*\*", "- **", re.sub(r"<!--.*?-->", "", secs.get("Vision", ""), flags=re.S)))
    pick = [f"      {k}: {v}" for k, v in vision.items()
            if re.search(r"^who|north star|riskiest|business|^ai\b|^constraint", k, re.I) and v.strip()]
    v = st.phase("validate")
    val = {"running": f"RUNNING, due {v[3]} - plan provisionally; the timeline starts after that date or #Plan says "
                      f"provisional",
           "filled": "filled - a passing result retires value: cite it, never re-run it"}.get(
        v[1], "empty (/validate is optional and did not run) - value is UNTESTED: a milestone must retire it")
    tpl = tool_file("templates", "PRODUCT.md")
    fields = product_sections(tpl.read_text(encoding="utf-8")).get("Plan", "") if tpl else ""
    fields = "\n".join("      " + l for l in fields.splitlines() if l.startswith("- **"))
    scope = re.sub(r"<!--.*?-->", "", secs.get("Scope", ""), flags=re.S).strip()
    out = ("/plan start - build the plan from these; read nothing else whole:\n"
           "  - #Vision (the fields the plan answers to):\n" + ("\n".join(pick) or "      (empty)") + "\n"
           f"  - #Validation: {val}\n"
           f"  - Flags: AI product {st.header.get('AI product', 'unknown')} · Agent {st.header.get('Agent', 'unknown')}"
           + (" - an agent launches in stages: approval first, then unchecked, with a stop switch before public"
              if st.header.get("Agent") == "yes" else "") + "\n"
           "  - #Scope, whole:\n" + ("\n".join("      " + l for l in scope.splitlines()) or "      (empty - offer "
                                     "/scope first)") + "\n"
           "  - Earlier companions (docs/vision.md, docs/scope.md ...) are reasoning, not decisions: open one by "
           "section only when a decision above points into it, and receipt it.\n"
           "  - #Plan is these fields, labels as written, in a scratch file outside the repo; `set plan filled "
           "--section-from <file>` writes it:\n" + fields + "\n"
           "  - `set plan filled` refuses, every problem in one list: an empty field · a milestone without an id "
           "(M1, M2 ...), an exit criterion, a `Needs:` prerequisite or a four-risks row · a usability checkpoint "
           "naming no milestone · a concern area not marked now/next/later/N-A · a Timeline without capacity or "
           "start date · a plan ending after the north-star date with no `North star:` line · a timeline before a "
           "running experiment's due date, not marked provisional · four-risks citing #Vision, or an empty "
           "#Validation · value untested while #Validation is empty · a receipt of docs/plan.md · no `## Owner's "
           "answers` block in docs/plan.md · a number not in the answers or the spine without `(proposed)` or "
           "`(derived: <sum>)` · a #Vision constraint (a law, a language) with no line in #Plan · LaTeX.\n"
           "  - Two rounds, each ONE message or form: questions 1-3, then the draft with question 4, any #Scope clash "
           "and \"Anything to change? If not: Save this version of your project? (yes / no)\" (either answer "
           "records it). After it, docs/plan.md and the section file in ONE message, then "
           "`set plan filled --section-from <file> --commit \"<one line>\"` (no `--commit` on a no) records, saves "
           "and prints the rest of the close.\n"
           "  - Order (each call re-sends all before it): every read before question 1, nothing opened after the "
           "draft; docs/plan.md and the section file are the last writes; `set` in that call or the next, no check "
           "of your own between (`set` checks both).\n\n")
    return out + phase_rules_text("plan")


# ---- /design-system (P1, P2, P4, P20, P23, P37) --------------------------------------------------------------------
# The one saved Claude /design-system run read for 8 calls before its first question (rule files, PRODUCT.md and all 8
# references whole: context 49K -> 149K, re-sent on 37 more calls - 45 calls, 7.9M tokens), asked in 7 owner turns and
# measured its sample by hand for 9 calls; a logged Gemini run designed a Shopify admin app without one search of
# Shopify's design rules and recorded none of the owner's answers. The start is one call: the spine lines the design
# comes from, both question rounds, the 13 families, what to write and what `set` refuses. The close's rules print at
# `set design-system filled`, which refuses the record's countable gaps in one list - on its own close only, never in
# phase_check (a design filled under older rules is never blocked later).
QUESTION_PHASES += ("design-system",)
PHASE_RULES["design-system"] = {
    "PRINCIPLES.md": ["The 5-step spine", "Architecture & quality bar", "Communication"],
    "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status"],
}
PHASE_CLOSE_RULES["design-system"] = {
    "PRINCIPLES.md": ["Documentation-driven", "Reviews, vision & confidence", "The exit-criteria gate"],
    "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"],
}
CLOSE_STEPS["design-system"] = (
    "every number this phase introduced against #Vision: a base type size or density that cannot serve the audience "
    "it names (an older user, a phone in one hand)",
    "#Vision (who it is for, the tone that implies), #Scope (a non-goal the design assumes) and #Architecture (the UI "
    "framework and component registry the tokens must work in)",
    "the #Design fields, the owner's answers, the sample and its rendered check, DESIGN.md's sections and the host's "
    "design links")
DESIGN_HOLDS = "the spine lines the design comes from, the two\n    rounds, the 13 families, what to write, this phase's rules"
# D3: an app drawn inside another product's UI follows that host's current design rules. (name, what in #Architecture
# says the UI lives there, the domains of the host's own design docs). Native mobile counts: its platform is the host.
DESIGN_HOSTS = (
    ("Shopify (an admin app)", r"\bshopify admin\b(?! ?api)|\bembedded\b.{0,40}\bshopify\b|\bshopify\b.{0,40}\bembedded"
     r"\b|\bpolaris\b|\bapp bridge\b", ("shopify.dev", "polaris.shopify.com", "polaris-react.shopify.com")),
    ("Slack", r"\bslack (?:app|bot)\b|\bblock kit\b", ("api.slack.com", "docs.slack.dev")),
    ("Microsoft Teams", r"\bteams (?:app|tab|bot)\b", ("learn.microsoft.com",)),
    ("a Microsoft Office add-in", r"\b(?:outlook|excel|word|office) add-?in\b", ("learn.microsoft.com",)),
    ("Salesforce", r"\blightning web component|\bsalesforce (?:app|org|lightning)\b",
     ("lightningdesignsystem.com", "developer.salesforce.com")),
    ("Zendesk", r"\bzendesk (?:app|sidebar)\b", ("developer.zendesk.com", "garden.zendesk.com")),
    ("HubSpot", r"\bhubspot (?:app|ui extension|card)", ("developers.hubspot.com",)),
    ("Atlassian (Jira / Confluence)", r"\b(?:jira|confluence|atlassian|forge) (?:app|plugin|add-?on)\b",
     ("developer.atlassian.com", "atlassian.design")),
    ("a browser extension", r"\b(?:chrome|browser|firefox) extension\b", ("developer.chrome.com", "developer.mozilla.org")),
    ("Figma", r"\bfigma (?:plugin|widget)\b", ("figma.com", "developers.figma.com")),
    ("Google Workspace", r"\b(?:google workspace|gmail|google sheets|google docs) add-?on\b", ("developers.google.com",)),
    ("WordPress", r"\bwordpress (?:plugin|block|theme)\b|\bgutenberg\b", ("developer.wordpress.org", "wordpress.github.io")),
    ("iOS (Apple's Human Interface Guidelines)", r"\b(?:ios|iphone|ipad) app\b|\bswiftui\b", ("developer.apple.com",)),
    ("Android (Material 3)", r"\bandroid app\b|\bjetpack compose\b", ("developer.android.com", "m3.material.io")),
)
DESIGN_UI_LINE = re.compile(r"(?i)\b(?:ui|ux|web|front-?end|pages?|screens?|templates?|jinja|htmx|react|vue|svelte|"
                            r"next\.?js|nuxt|astro|tailwind|shadcn|components?|css|mobile|widget|dashboard|browser|"
                            r"polaris|app bridge|design system)\b")
DESIGN_UI_FILES = {".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".htm", ".jinja", ".j2", ".css", ".scss"}
# its own list: SKIP_DIRS is redefined further up without .git and .agents (the installed playbook's own files)
DESIGN_SKIP = {"node_modules", "venv", "__pycache__", "dist", "build", "docs", "status"}
# the sample's path, in backticks or not (a logged run was refused once for a plain path: 417K tokens)
DESIGN_SAMPLE = re.compile(r"(?<![\w/.\\-])`?([\w./\\-]+\.(?:html?|tsx|jsx|vue|svelte|astro|jinja|j2))\b`?")
# a template placeholder `<oklch>`; never a comparison the template writes out (`mobile <640 · ... desktop >=1024`)
DESIGN_HOLDER = re.compile(r"<[^<>\n]{1,60}>(?!=)")
RENDER_EVIDENCE = re.compile(r"render_check\.py[`\"']?\s+[`\"']?([^\s`\"']+)[`\"']?\s+--main\s+[\"“'](.+?)[\"”']")
# An app is judged on its states, not its happy path: the sample shows the main screen empty, loading and with an error
DESIGN_STATES = ("empty", "loading", "error")
# Labels in these run longer than English (Dutch/French ~30%, German more); a sample shown only in English hides it
DESIGN_LANGS = {"Dutch": "nl", "French": "fr", "German": "de", "Spanish": "es", "Italian": "it", "Portuguese": "pt",
                "Polish": "pl", "Swedish": "sv", "Danish": "da", "Norwegian": "no|nb|nn", "Finnish": "fi", "Czech": "cs",
                "Greek": "el", "Turkish": "tr", "Russian": "ru", "Ukrainian": "uk", "Romanian": "ro",
                "Hungarian": "hu", "Arabic": "ar", "Hebrew": "he", "Persian": "fa", "Urdu": "ur", "Hindi": "hi",
                "Japanese": "ja", "Chinese": "zh", "Korean": "ko"}
DESIGN_RTL = {"Arabic", "Hebrew", "Persian", "Urdu"}
# next.68 - what a logged 4-tool round missed on every playbook sample. #Scope's must-show items, by the words #Scope
# uses: (the id the sample marks with data-must="<id>", what the screen shows, the words). Only 2 of 4 samples showed
# the unexplained amount and 0 of 4 the signed-in user; the best sample of the round (no playbook) showed all five.
DESIGN_MUST = (
    ("unsure", "what the screen shows when the AI is unsure or an amount is unexplained - never a guess",
     r"\b(?:unsure|not sure|uncertain(?:ty)?|unexplained|cannot explain|abstain\w*|low confidence)\b"),
    ("fake-data", "a label, always in view, that the data is fake",
     r"\b(?:fake|synthetic|fictional|fictitious|dummy)\b[^.;]{0,40}\bdata\b|\bdata\b[^.;]{0,20}\b(?:fake|synthetic)\b"),
    ("signed-in-user", "the signed-in user (the company login)",
     r"\bcompany (?:login|sign-?in|identity|account)|\bSSO\b|single sign-on|\bOIDC\b|\bentra id\b|\bokta\b"),
    # a NON-GOAL or a "never": "the app sends reminders automatically" in scope is a feature, not a must-show
    ("not-sent", "that approving sends nothing - a person sends",
     r"(?:NON-GOAL|\bnever\b|\bnot\b).*\bsend\w*\b[^.;]{0,60}\bautomatic|\bsend\w*\b[^.;]{0,60}\bautomatic\w*\W{0,4}"
     r"(?:never|not)\b|\bauto-?sen[dt]|\bnever sen[dt]"),
    ("ai-label", "the label that the text is AI-made",
     r"\bAI[- ](?:drafted|generated|made|written)\b|\bart(?:icle)?\.? ?50\b|\bAI\b[^.;]{0,40}\btransparen|"
     r"\btransparen\w*[^.;]{0,40}\bAI\b"),
)
# EU-only custody: the fonts make no request to a third party (all 4 logged playbook samples loaded Google Fonts on an
# EU-only, GDPR product; the best sample of the round asked and self-hosted them)
DESIGN_EU = re.compile(r"(?i)\bEU\b|\beurope\w*|\bGDPR\b|data residency|no third[- ]part|sovereign")
FONT_URL = re.compile(r"(?i)https?://(?:fonts\.googleapis\.com|fonts\.gstatic\.com|use\.typekit\.net|p\.typekit\.net|"
                      r"fonts\.bunny\.net|api\.fontshare\.com|fonts\.cdnfonts\.com|rsms\.me|fast\.fonts\.net|"
                      r"[^\s\"')]*(?:/fonts?/|fontsource|\.woff2?\b|\.ttf\b|\.otf\b))[^\s\"')]*")
STUDIO_MARK = "<!-- ===== THEME STUDIO"
LANG_CODES = {**DESIGN_LANGS, "English": "en"}
AUDIT_LINE = "- **Audit (written by `status.py set`"
HTML_TAGS = {"html", "head", "body", "div", "span", "p", "a", "button", "input", "form", "nav", "main", "section",
             "header", "footer", "aside", "table", "tr", "td", "th", "ul", "ol", "li", "h1", "h2", "h3", "img", "label",
             "select", "option", "textarea", "dialog", "svg", "link", "script", "style", "br", "hr", "em", "strong"}


def design_hosts(arch: str) -> list[tuple[str, str, tuple[str, ...]]]:
    """The host platforms #Architecture puts the UI inside: (name, the line that says so, its design docs' domains)."""
    out = []
    for name, rx, domains in DESIGN_HOSTS:
        line = next((l.strip() for l in arch.splitlines() if re.search(rx, l, re.I)), None)
        if line:
            out.append((name, line, domains))
    return out


def design_ui_files(base: Path, limit: int = 5) -> list[str]:
    """UI code already in the project (a sample under docs/ is not the app)."""
    found: list[str] = []
    for root, dirs, names in os.walk(base):
        dirs[:] = sorted(x for x in dirs if x not in DESIGN_SKIP and not x.startswith("."))
        for n in sorted(names):
            if Path(n).suffix.lower() in DESIGN_UI_FILES:
                found.append((Path(root) / n).relative_to(base).as_posix())
                if len(found) >= limit:
                    return found
    return found


def design_languages(vision: str) -> list[str]:
    """The non-English languages #Vision names (case-sensitive: "polish the UI" is not Polish)."""
    return [n for n in DESIGN_LANGS if re.search(rf"\b{n}\b", vision)]


def design_scope_languages(scope: str, vision: str) -> tuple[list[str], str]:
    """The languages the users need NOW: #Scope's language line, a deferred one left out ("with German deferred");
    #Vision's older line only when #Scope names none (a logged sample came out in German from a #Vision line that
    #Scope had narrowed to Dutch and French)."""
    for line in scope.splitlines():
        if re.search(r"(?i)\blanguages?\b", line) and design_languages(line):
            now = [s for s in re.split(r"[,;(]|\bwith\b|\bbut\b|\bplus\b", line)
                   if not re.search(r"(?i)\bdeferred\b|\blater\b|\bnot now\b|\buntil\b", s)]
            if design_languages(" ".join(now)):
                return design_languages(" ".join(now)), "#Scope: \"" + line.strip(" -*")[:160] + "\""
    langs = design_languages(vision)
    return langs, ("#Vision (#Scope names none)" if langs else "")


def design_must(scope: str) -> list[tuple[str, str, str]]:
    """#Scope's must-show items: (id, what the screen shows, the #Scope line that asks for it) - deferred lines left
    out."""
    lines, keep, goal = [], True, False
    for l in scope.splitlines():
        if re.match(r"\s*-\s*\*\*", l):  # a field: only the Deferred field is left out (the table stakes name it too)
            keep = not re.match(r"(?i)\s*-\s*\*\*\s*deferred", l)
            goal = bool(re.match(r"(?i)\s*-\s*\*\*\s*non[- ]goals?", l))
        if keep and not re.search(r"(?i):\s*deferred\b", l):
            lines.append(("NON-GOAL " if goal else "") + l)
    out = []
    for mid, what, rx in DESIGN_MUST:
        hit = next((m for l in lines for m in [re.search(rx, l, re.I)] if m), None)
        if hit:
            out.append((mid, what, design_around(hit).replace("NON-GOAL ", "")))
    return out


def design_around(m: re.Match) -> str:
    """The words around a match - a long record line holds it anywhere."""
    s, a, b = m.string, max(0, m.start() - 60), m.end() + 60
    return ("…" if a else "") + s[a:b].strip(" -*") + ("…" if b < len(s) else "")


def design_font_reason(arch: str, vision: str) -> str:
    """The #Architecture (or #Vision) words that make a third-party font request a data-custody question."""
    return next((design_around(m) for l in (arch + "\n" + vision).splitlines() for m in [DESIGN_EU.search(l)] if m),
                "")


def design_ref(name: str) -> Path | None:
    return tool_file("design-system", "references", name)


def design_families() -> list[str]:
    """The 13 aesthetic families, as archetypes.md names them ("Calm Authority / Trust")."""
    f = design_ref("archetypes.md")
    return re.findall(r"(?m)^### \d+\.\s+(.+?)\s+—", f.read_text(encoding="utf-8")) if f else []


def design_start_text(st: "Status") -> str:
    """`next --phase design-system`: the spine lines the design comes from, both question rounds, the 13 families,
    what to write and what `set design-system filled` refuses - one call (P1, P25, P37)."""
    START_HOLDS.setdefault("design-system", DESIGN_HOLDS)  # Antigravity: fit_start names what its file holds
    base = st.base if st.base is not None else Path(".")
    prod = base / "PRODUCT.md"
    secs = product_sections(prod.read_text(encoding="utf-8")) if prod.is_file() else {}
    vision, scope, arch = (re.sub(r"<!--.*?-->", "", secs.get(s, ""), flags=re.S).strip()
                           for s in ("Vision", "Scope", "Architecture"))
    ui = st.header.get("UI", "unknown")
    arc = design_ref("archetypes.md")
    R = arc.parent.as_posix() if arc else "commands/design-system/references"
    tool = {n: (tool_file(*p).as_posix() if tool_file(*p) else n) for n, p in
            (("theme_studio.py", ("design-system", "theme_studio.py")),
             ("render_check.py", ("frontend-audit", "render_check.py")), ("audit.py", ("frontend-audit", "audit.py")))}
    out = ["/design-system start (never read PRODUCT.md, PRINCIPLES.md, MECHANISMS.md or a reference whole - what this "
           "phase starts from is here; a reference is read by the section a line below names, in that step's turn):",
           f"  - Flags: UI {ui} · AI product {st.header.get('AI product', 'unknown')} · Agent "
           f"{st.header.get('Agent', 'unknown')}",
           f"  - This skill's references: {R} (the `--step` calls below print what each turn needs from them)"]
    if ui == "no":
        out.append("  - UI gate: UI no - say in one message why a design system does not apply, write NOTHING (no "
                   "#Design, no DESIGN.md, no declined record) and stop: /foundation is next")
        return "\n".join(out)
    out.append("  - UI gate: " + ("passed (UI yes)" if ui == "yes" else
                                  "unknown - round 1 asks first \"Does this product have or need a user-facing UI?\" "
                                  "(`status.py flag --ui yes|no` records it); no -> say why a design system does not "
                                  "apply, write nothing, stop"))
    if not vision:
        out.append(f"  - No #Vision: run the three-question vision discovery first (`status.py section {R}/build-loop.md "
                   f"\"Standalone vision discovery\"`) and wait for the answers")
    else:
        vis = scope_fields(vision)
        want = ("who it's for", "value proposition", "north-star target", "AI", "constraints")
        shown = dict((what, " ".join(v)) for what, rx in SCOPE_VISION if what in want
                     for k, v in vis.items() if re.search(rx, k, re.I))
        out.append("  - #Vision, what the principles come from (purpose + audience):")
        out += [f"      {w}: {t[:400]}{'…' if len(t) > 400 else ''}" for w, t in shown.items()]
    core = [(k, " ".join(v)) for k, v in scope_fields(scope).items()
            if re.search(r"(?i)core feature|^in[- ]scope|non[- ]goal", k)]
    if core:
        out.append("  - #Scope: the sample is the core feature's main screen; DESIGN.md §5's page inventory is the "
                   "in-scope list; a non-goal the design assumes is a Step 3c clash:")
        out += [f"      {k}: {v[:500]}{'…' if len(v) > 500 else ''}" for k, v in core]
    lines = [l.strip() for l in arch.splitlines() if DESIGN_UI_LINE.search(l)][:10]
    if lines:
        out.append("  - #Architecture, the lines the UI is built in - the tokens must work there:")
        out += [f"      {l[:300]}" for l in lines]
    elif not arch:
        out.append("  - #Architecture is empty: the UI framework is undecided - say so; the sample is a standalone "
                   "preview HTML")
    for name, line, domains in design_hosts(arch):
        out.append(f"  - Host: the UI lives inside {name} (#Architecture: \"{line[:160]}\"). Its CURRENT design rules "
                   f"decide the look: search them in round 2's turn ({' · '.join(domains)}); DESIGN.md links the page "
                   f"each rule comes from (a deep link, not a homepage). Not inside it after all: a #Design line "
                   f"`Host platform: none - <why>`")
    ui_files = design_ui_files(base)
    out.append("  - Mode: " + (f"UI code exists ({', '.join(ui_files)}) - say *retrofit territory*; new screens are "
                               f"designed greenfield (`status.py section {R}/build-loop.md \"Scope of this version\"`)"
                               if ui_files else "no UI code yet - greenfield"))
    langs, lsrc = design_scope_languages(scope, vision)
    rtl = [n for n in langs if n in DESIGN_RTL]
    must = design_must(scope)
    custody = design_font_reason(arch, vision)
    me = Path(__file__).resolve().as_posix()
    smap = base / "STRUCTURE.md"
    rows = [l.strip() for l in (smap.read_text(encoding="utf-8").splitlines() if smap.is_file() else [])
            if not l.lstrip().startswith("#") and re.search(r"(?i)\.css\b|\bstatic/|\bstyles?/|\btemplates/|\bui/|"
                                                              r"front-?end/|\bcomponents/|\bdocs/", l)][:10]
    if rows:
        out.append("  - STRUCTURE.md, where the look lives: the stylesheet goes where it says; the sample goes in a "
                   "folder it maps (a new folder needs its row, or the structure check fails at `set`):")
        out += [f"      {r[:200]}" for r in rows]
    if st.state("design-system") == "filled":
        out.append(f"  - #Design is filled ({st.phase('design-system')[2]}): a RE-RUN (§Re-run semantics below) - a "
                   f"replaced archetype, palette or type pairing keeps a dated `superseded <date>: <why>` line; so does "
                   f"a family you proposed that the user reversed in this run")
    tpl = tool_file("templates", "PRODUCT.md")
    fields = product_sections(tpl.read_text(encoding="utf-8")).get("Design", "") if tpl else ""
    pre = (f"pre-filled: {', '.join(langs)}, from {lsrc}" + (", with a switch (Recommended)" if len(langs) > 1 else "")
           if langs else "pre-filled: English")
    out += [
        "  - Round 1 - ONE message or form, before any family is named (proposing first fails the gate):",
        "      a. 4-6 design principles from #Vision's purpose + audience, each with a one-line why (the levers: "
        "§Design principles below) - the user adjusts them",
        "      b. \"Do you have a look in mind — a product you admire, or bold vs minimal?\"",
        "      c. the 3-question picker below, a recommended answer to each - the user answers, never you",
        "      d. \"Which language(s) is the interface in, and does the user switch between them in the app?\" - "
        + pre + (f"; {', '.join(rtl)} read right to left: `dir=\"rtl\"`, the layout mirrored" if rtl else ""),
        "      e. Fonts: self-hosted - the font files and their licence in the project, loaded by @font-face, no "
        "request to Google Fonts or any other host" + (
            f" - DECIDED, say why: \"{custody}\"" if custody else
            " (Recommended) - or a font service (Google Fonts): the owner chooses"),
        *(["      f. say what the sample will show because #Scope asks for it (the owner may add or drop one):"]
          + [f"         - {w} (data-must=\"{i}\") - #Scope: \"{l}\"" for i, w, l in must] if must else []),
        f"  - Then ONE call: `python {me} next --phase design-system --step foundations --family <N>` prints the "
        f"family's preset, the foundations, the palettes and the type, colour, depth, motion and token laws (no "
        f"`section` call per file, no `--help`); the host's searches beside it",
        "  - Round 2 - ONE message: ONE of the 13 families below as the default, its why citing their answers; say "
        "there are 13 and where (archetypes.md); their own reference wins. Under it the foundations, each a decided "
        "default + a one-line why: type pairing + a real scale (the archetype's base size), colour roles in OKLCH "
        "light AND dark (the accent's hue chosen for THIS product, with its why - a palettes row is a start, not "
        "the answer), density, depth, layout, motion tier. Options, first: \"Keep as proposed (Recommended)\" · "
        "\"Change something\"",
        f"  - The sample, in one turn: `python {me} next --phase design-system --step sample` prints how; ONE screen "
        f"of THIS product (the core feature, real content), its states marked `data-state=\"empty\"` · "
        f"`\"loading\"` · `\"error\"`" + (", each #Scope item above marked `data-must=\"<id>\"`" if must else "")
        + (", every interface language in it (`lang=\"<code>\"`) with a working switch when there are 2+" if
           len(langs) > 1 else "") + f", self-hosted fonts, buttons in Verb + Noun (a destructive one confirmed or "
        f"undoable); numbers read \"illustrative figures — not the product's rules\"; then `python {tool['theme_studio.py']} <page.html> --preset \"Name|oklch(L C H)|oklch(L C H)\"` "
        f"× 3-5 (adds the Theme Studio). Next turn, both at once: `python {tool['render_check.py']} <sample> --main "
        f"\"<the main action's text>\" --shots <the sample's folder>/shots` (saves 3 screenshots) and `python "
        f"{tool['audit.py']} <sample>`; fix every [FAIL]. NOT RUN: `python -m pip install playwright` (it uses an "
        f"installed Chrome or Edge; no browser at all: `python -m playwright install chromium`), run it again; "
        f"cannot install: your tool's own browser at 375, 768 and 1440 px, the 3 screenshots saved in that folder",
        "  - The confirm - ONE message or form: the sample at ~375 px · 768 px · desktop (never desktop alone), what "
        "both checks found, and two options: \"Looks good - save (Recommended)\" · \"Change something\" (the save "
        "question rides on the first). Change -> regenerate, the same message again. No DESIGN.md before approval",
        f"  - After the approval, ONE message: `python {tool['theme_studio.py']} <sample> --remove` (no Theme "
        f"Studio in the approved sample); `python {me} next --phase design-system --step write` for DESIGN.md, the "
        f"stylesheet the app loads + its import and the #Design file; then `set design-system filled --section-from "
        f"<file> --commit \"<one line>\"` in the foreground (~1 min: it re-renders the sample; no `--commit` on a "
        f"no) records, runs the audit, writes its counts into DESIGN.md, saves and prints the rest of the close",
        "  - Order (each call re-sends all before it): reads and round 1 first; the sample written whole in ONE "
        "call, fixed by edits, never rewritten; DESIGN.md, the stylesheet and the #Design file are the last "
        "writes, `set` in that call or the next - no audit or render call of your own after them (`set` runs both)",
        "  - #Design is these fields, labels as written, in a scratch file outside the repo, plus `Own reference: "
        "\"<their words>\"`, `Picker answers (the owner's): <a> · <b> · <c>`, `Interface languages: <names> · "
        "switch: yes|no`, `Font delivery: self-hosted (<files>)` (or `<service> - owner chose: \"<their words>\"`) "
        "and `evidence: python <...>/render_check.py <sample> --main \"<text>\" --shots <folder> → <its last line> · "
        "<date>` (or `evidence: screenshots <folder> (<tool>'s browser) · <date>`):",
        *("      " + l for l in fields.splitlines() if l.startswith("- **")),
        "  - `set design-system filled` refuses, every problem in one list: an empty field · UI no (no UI writes "
        "nothing) · not 4-6 principles · an archetype naming none of the 13 (or `Other: <their reference>`) · no "
        "`Own reference`, `Picker answers`, `Interface languages` or `Font delivery` line · a sample that does not "
        "exist, still holds the Theme Studio, shows numbers with no \"illustrative\" label, has no empty, loading or "
        "error state (or an `App states: <which> not shown - <why>` line), leaves a #Scope item above unmarked (or "
        "`Must-show: <id> not shown - <why>`) or is not in the interface language(s) · a font from a third-party "
        "host the owner did not choose, or a self-hosted font file missing · no render_check line, NOT RUN, fewer "
        "than 3 screenshots, or a sample failing it (`set` runs it again) · a Host above with no link on its docs · "
        "DESIGN.md without its `## In short` (before §1: plain words, each principle with the #Vision or #Scope "
        "line it comes from) or one of its 9 numbered sections, with a template placeholder left, Reference brands "
        "the owner never named, an audit count typed by hand, no page inventory in §5 or no stylesheet path in §2 · "
        "LaTeX · the audit failing a law, checking 0 things or a stylesheet no app file imports. A recorded "
        "override (a #Design line with the word `override` and the user's reason) answers a render failure or NOT "
        "RUN, no tokens and no stylesheet."]
    rules = dict(PHASE_RULES["design-system"])
    rules["MECHANISMS.md"] = [s for s in rules["MECHANISMS.md"]
                              if (s != "Spine resolution" or not vision)
                              and (s != "Re-run semantics" or st.state("design-system") == "filled")]
    picker = print_sections(arc, ["The 3-question picker"]) if arc else ""
    loop = design_ref("build-loop.md")
    return "\n".join(out) + "\n\n" + "\n\n".join(x for x in [
        picker,
        "The 13 families (archetypes.md; read the chosen one by its heading):\n" + "\n".join(
            f"  {i}. {n}" for i, n in enumerate(design_families(), 1)),
        print_sections(loop, ["§Design principles"]) if loop else "",
        rules_text(rules, "Rules for /design-system, word for word from the rule files (these ARE the rule files "
                          "for this phase - do not open them; the close's print at `set`):")] if x)


# One call per turn (next.68): a logged Cursor run made 25 `section` calls (up to 1.46M tokens), a Claude run 7 and an
# Antigravity run 9, each re-sent with the whole conversation; Cursor's first ones failed on a literal `R/` path.
DESIGN_STEPS = {
    "foundations": "the family's preset, the foundations, the palettes, and the laws the foundations decide",
    "sample": "how to build and confirm the sample, its craft, the Theme Studio notes and the page laws",
    "write": "the DESIGN.md skeleton and how to write it and the stylesheet",
}


def design_step_text(phase: str, step: str, family: str | None) -> str:
    """`next --phase design-system --step <step> [--family <N>]`: every reference section one turn needs, word for
    word, in one call (P1, P25)."""
    if phase.lstrip("/") != "design-system" or step not in DESIGN_STEPS:
        raise Refused(f"--step goes with --phase design-system and is one of: {', '.join(DESIGN_STEPS)}")
    ref = {n: design_ref(n) for n in ("archetypes.md", "build-loop.md", "palettes.md", "universal-laws.md", "craft.md",
                                       "theme-studio.md", "design-md-template.md")}
    if any(v is None for v in ref.values()):
        raise Refused("this install has no design-system references folder - reinstall the playbook")
    names = design_families()
    fam = None
    if family:
        k = family.strip().rstrip(".")
        fam = (names[int(k) - 1] if k.isdigit() and 0 < int(k) <= len(names) else
               next((n for n in names if n.lower().startswith(k.lower()) or k.lower() in n.lower()), None))
        if fam is None:
            raise Refused(f"no family {family!r} - one of: " + " · ".join(f"{i}. {n}" for i, n in enumerate(names, 1)))
    if step == "foundations" and fam is None:
        raise Refused("--step foundations needs --family <N> (the family round 2 proposes): "
                      + " · ".join(f"{i}. {n}" for i, n in enumerate(names, 1)))
    parts: list[str] = []
    if step == "foundations":
        parts = [print_sections(ref["archetypes.md"], [str(names.index(fam) + 1), "How Step 3"]),
                 print_sections(ref["build-loop.md"], ["Concrete foundations"]),
                 ref["palettes.md"].read_text(encoding="utf-8").strip(),
                 print_sections(ref["universal-laws.md"], ["intro", "The 26 rules", "A. Type", "B. Colour", "C. Depth",
                                                           "D. Motion", "E. Tokens", "I. Theming"])]
    elif step == "sample":
        index = print_sections(ref["craft.md"], ["Archetype → bucket"])
        row = next((l for l in index.splitlines() if fam and l.startswith("|")
                    and fam.split(" / ")[0].split()[0].lower() in l.lower()), "")
        bucket = "Bucket B" if "B ·" in row else "Bucket A" if row else None
        parts = [print_sections(ref["build-loop.md"], ["Build the sample page", "Confirm the sample"]),
                 print_sections(ref["craft.md"], ["Two rules", "Archetype → bucket"]
                                + ([bucket] if bucket else ["Bucket A"]) + ["Audit & Theme-Studio"]),
                 print_sections(ref["theme-studio.md"], ["Notes"]),
                 print_sections(ref["universal-laws.md"], ["F. Process", "G. Data", "H. Responsive",
                                                           "J. Accessibility"])]
    else:  # Step 6's self-check walks the laws over the sample AND DESIGN.md: it belongs to the write turn
        parts = [print_sections(ref["design-md-template.md"], ["intro", "The skeleton"]),
                 print_sections(ref["build-loop.md"], ["Emit the token stylesheet", "Emit `DESIGN.md`"]),
                 print_sections(ref["universal-laws.md"], ["Self-check digest"])]
    full = (f"/design-system --step {step}" + (f" ({fam})" if fam else "") + f": {DESIGN_STEPS[step]} - word for "
            f"word from {ref['archetypes.md'].parent.as_posix()}; the whole of what this turn reads (no `section` "
            f"call, no reference opened):\n\n" + "\n\n".join(p for p in parts if p))
    if playbook_tool() != "antigravity":
        return full
    f = Path(__file__).resolve().parent / f"design-system-{step}.md"
    f.write_text(full + "\n", encoding="utf-8")
    return (f"Your tool shows only the end of a long output, so this turn's reading is in a file: open "
            f"`{f.as_posix()}` ONCE with view_file - {DESIGN_STEPS[step]}. Never open a reference or status.py.")


def design_record_gaps(base: Path, st: "Status", write: bool = False, today: str = "") -> list[str]:
    """`set design-system filled`: what the record, DESIGN.md and the sample can show, every problem in one list (P4,
    P20). Run on /design-system's own close only."""
    prod = base / "PRODUCT.md"
    secs = product_sections(prod.read_text(encoding="utf-8")) if prod.is_file() else {}
    body = re.sub(r"<!--.*?-->", "", secs.get("Design", ""), flags=re.S)
    f = scope_fields(body)

    def field(rx: str) -> list[str] | None:
        return next((v for k, v in f.items() if re.search(rx, k, re.I)), None)

    design_p = base / "DESIGN.md"
    design = design_p.read_text(encoding="utf-8") if design_p.is_file() else ""
    # the user's override is a #Design line: a DESIGN.md sentence ("a manual toggle overrides the OS") waved three
    # logged NOT RUN / no-screenshot records through
    override = any(re.search(r"(?i)\boverride\b", l) for l in body.splitlines())
    gaps: list[str] = []
    for label, rx in (("Has user-facing UI?", r"user-facing ui"), ("Design principles", r"principles"),
                      ("Archetype", r"archetype"), ("Foundations summary", r"foundations"), ("Tokens", r"^tokens"),
                      ("Approved sample page (path)", r"sample page")):
        if not " ".join(field(rx) or []).strip():
            gaps.append(f"#Design's `{label}` is empty")
    ui = " ".join(field(r"user-facing ui") or [])
    if re.match(r"\W*no\b", ui, re.I):
        gaps.append("#Design says the product has no UI: a product with no UI writes nothing - no #Design, no "
                    "DESIGN.md (`status.py flag --ui no`, then stop)")
    pr = field(r"principles") or []
    items = [l for l in pr[1:] if re.match(r"(?:\d+[.)]|[-*+])\s+\S", l)] or \
        [p for p in re.split(r"\s*(?:·|;|\b\d+[.)]\s)\s*", pr[0] if pr else "") if p.strip()]
    if pr and not 4 <= len(items) <= 6:
        gaps.append(f"Design principles: {len(items)} found, 4-6 wanted - one per line, `1. <principle> - <why>`")
    arche = next((l for l in field(r"archetype") or [] if l.strip()), "")  # its own line: not the answers under it
    names = design_families()
    if arche and names and not any(n.lower() in arche.lower() or n.split(" / ")[0].lower() in arche.lower()
                                   for n in names) and not re.search(r"(?i)\bother\b", arche):
        gaps.append("the Archetype names none of the 13 families in archetypes.md - name one, or write `Other: <the "
                    "owner's own reference>`")
    if not re.search(r"(?i)own (?:reference|look)", body):
        gaps.append("the owner's own reference is not recorded - a #Design line `Own reference: \"<their words>\"` "
                    "(asked before any family was named)")
    if not re.search(r"(?i)picker", body):
        gaps.append("the picker answers are not recorded - a #Design line `Picker answers (the owner's): <read or "
                    "scan> · <who, where> · <calm or bold>`")
    m = DESIGN_SAMPLE.search(" ".join(field(r"sample page") or []))
    sample = base / m.group(1) if m else None
    page = ""
    if " ".join(field(r"sample page") or []).strip() and sample is None:
        gaps.append("the Approved sample page field names no page file (`docs/design/sample.html`)")
    elif sample is not None and not sample.is_file():
        gaps.append(f"the sample page {m.group(1)} does not exist")
    elif sample is not None:
        page = sample.read_text(encoding="utf-8", errors="replace")
        shown = re.sub(r"(?is)<(script|style)\b.*?</\1>|<[^>]+>", " ", page)
        if re.search(r"\d", shown) and "illustrative" not in page.lower():
            gaps.append(f"{m.group(1)} shows numbers with no \"illustrative figures — not the product's rules\" label "
                        f"(the sample proves the look, never the logic)")
        shown_states = set(re.findall(r"data-state\s*=\s*[\"']?(empty|loading|error)\b", page))
        missing = [s_ for s_ in DESIGN_STATES if s_ not in shown_states]
        if missing and not re.search(r"(?im)^\W*app states:.{10,}", body):
            gaps.append(f"{m.group(1)} has no {', '.join(missing[:-1]) + ' or ' if len(missing) > 1 else ''}"
                        f"{missing[-1]} state - the main screen also shows itself empty, loading and with an error "
                        f"(an inline form error counts), each marked data-state=\"empty|loading|error\". A screen "
                        f"that has none of one: a #Design line `App states: <which> not shown - <why>`")
        if STUDIO_MARK in page:
            gaps.append(f"{m.group(1)} still holds the Theme Studio - the approved sample is the page as the user sees "
                        f"it: `python <...>/theme_studio.py {m.group(1)} --remove`")
        scope = re.sub(r"<!--.*?-->", "", secs.get("Scope", ""), flags=re.S)
        unmarked = [(i, w) for i, w, _ in design_must(scope)
                    if not re.search(rf"data-must\s*=\s*[\"']?{i}\b", page)
                    and not re.search(rf"(?im)must-show:\s*`?{i}\b.*\bnot shown\b.{{6,}}", body)]
        if unmarked:
            gaps.append(f"{m.group(1)} does not mark what #Scope asks it to show: "
                        + "; ".join(f"{w} (data-must=\"{i}\")" for i, w in unmarked)
                        + " - show each, marked with its data-must, or a #Design line `Must-show: <id> not shown - "
                          "<why>`")
    gaps += design_language_gaps(body, page, m.group(1) if m else "")
    gaps += design_font_gaps(base, body, design, sample if page else None)
    gaps += design_render_gaps(base, body, override)
    links = re.findall(r"https?://([^/\s)>\]`\"']+)(/[^\s)>\]`\"']*)?", body + "\n" + design)
    if not re.search(r"(?im)host platform:\s*none\b.{6,}", body):
        for name, line, domains in design_hosts(re.sub(r"<!--.*?-->", "", secs.get("Architecture", ""), flags=re.S)):
            if not any((h.lower() == d or h.lower().endswith("." + d)) and len(p or "") > 1
                       for h, p in links for d in domains):
                gaps.append(f"#Architecture puts the UI inside {name}, and neither DESIGN.md nor #Design links its "
                            f"design docs ({' · '.join(domains)}, a page, not the homepage) - search its current "
                            f"rules and link each page used. Not inside it: a #Design line `Host platform: none - "
                            f"<why>`")
    if design:
        found = set(re.findall(r"(?m)^##\s+(\d)\.", design))
        miss = [str(i) for i in range(1, 10) if str(i) not in found]
        if miss:
            gaps.append(f"DESIGN.md has no section {', '.join(miss)} (`## <n>. <title>`, the 9 of the template)")
        skel = design_ref("design-md-template.md")
        holders = set(DESIGN_HOLDER.findall(print_sections(skel, ["The skeleton"]))) if skel else set()
        left = sorted(h for h in set(DESIGN_HOLDER.findall(design)) & holders
                      if h.strip("<>/").split()[0].lower() not in HTML_TAGS)
        if left:
            gaps.append(f"DESIGN.md still holds template placeholders: {' '.join(left[:6])}")
        sec5 = re.search(r"(?ms)^##\s+5\..*?(?=^##\s|\Z)", design)
        if sec5 and not re.search(r"(?i)inventory|pages? (?:this|the) app|pages? it needs", sec5.group(0)):
            gaps.append("DESIGN.md §5 has no page inventory - the pages this app needs, from #Scope")
        sec2 = re.search(r"(?ms)^##\s+2\..*?(?=^##\s|\Z)", design)
        if sec2 and not override and not re.search(r"[\w./-]+\.s?css\b", sec2.group(0)):
            gaps.append("DESIGN.md §2 names no stylesheet path - the file the app loads the tokens from")
        gaps += design_doc_gaps(design, body)
    if LATEX.search(body) or LATEX.search(design):
        gaps.append("LaTeX in #Design or DESIGN.md - plain symbols (≤ →), never $...$")
    failed = phase_check("design-system", base)
    if failed:
        gaps.append(failed)
    if not gaps and write and design:
        design_write_audit(base, design_p, design, m.group(1) if m and page else None, today)
    return gaps


def design_language_gaps(body: str, page: str, name: str) -> list[str]:
    """The interface language(s) the owner chose in round 1, against the sample: a logged sample came out in German
    for a Dutch + French product, and 0 of 4 built a working switch."""
    il = next((l for l in body.splitlines() if re.search(r"(?i)interface languages?\s*:", l)), None)
    if il is None:
        return ["the interface language(s) are not recorded - a #Design line `Interface languages: <names> · switch: "
                "yes|no` (round 1 asks it, pre-filled from #Scope)"]
    names = [n for n in LANG_CODES if re.search(rf"\b{n}\b", il)]
    sw = re.search(r"(?i)switch\w*\s*[:=]?\s*\**\s*(yes|no)\b", il)
    gaps = []
    if not names:
        gaps.append("the `Interface languages` line names no language (e.g. `Interface languages: Dutch, French · "
                    "switch: yes`)")
    if len(names) > 1 and sw is None:
        gaps.append("the `Interface languages` line does not say whether the user switches between them (`switch: "
                    "yes|no`)")
    if not page or not names:
        return gaps
    codes = {c.lower() for c in re.findall(r"(?:\blang|\bdata-lang|\bhreflang)\s*=\s*[\"'{]*([a-z]{2})\b", page, re.I)}
    has = {n for n in names if any(re.fullmatch(LANG_CODES[n], c) for c in codes)}
    top = re.search(r"<html\b[^>]*?\blang\s*=\s*[\"']?([a-z]{2})", page, re.I)
    if top and not any(re.fullmatch(LANG_CODES[n], top.group(1).lower()) for n in names):
        gaps.append(f"{name} is in `{top.group(1)}` (`<html lang>`), not an interface language ({', '.join(names)})")
    elif not has:
        gaps.append(f"{name} is in none of the interface languages ({', '.join(names)}) - `lang=\"<code>\"`")
    if len(names) > 1 and sw and sw.group(1).lower() == "yes" and has != set(names):
        gaps.append(f"{name} has no {', '.join(n for n in names if n not in has)} - the user switches, so the sample "
                    f"carries every interface language (each text in an element with `lang=\"<code>\"`) and a "
                    f"working switch")
    return gaps


def design_walk(base: Path):
    """The project's files, never a dot folder (.git, .agents - the installed playbook) or a dependency folder."""
    for root, dirs, names in os.walk(base):
        dirs[:] = [x for x in dirs if not x.startswith(".") and x not in {"node_modules", "venv", "__pycache__", "dist",
                                                                             "build"}]
        for n in names:
            yield Path(root) / n


def design_font_gaps(base: Path, body: str, design: str, sample: Path | None) -> list[str]:
    """Fonts: self-hosted unless the owner chose a font service. All 4 logged playbook samples (and one real base
    template) loaded Google Fonts on an EU-only product; the reference told the run to `<link>` the face."""
    fd = next((l for l in body.splitlines() if re.search(r"(?i)font delivery\s*:", l)), None)
    gaps = [] if fd else ["how the fonts load is not recorded - a #Design line `Font delivery: self-hosted (<the font "
                          "files>)`, or `<service> - owner chose: \"<their words>\"`"]
    sheets = {Path(s).name for s in re.findall(r"[\w./-]+\.s?css\b", design + "\n" + body)}
    files = [sample] if sample else []
    for f in design_walk(base):
        if f.name in sheets and f.suffix in (".css", ".scss"):
            files.append(f)
        elif f.suffix.lower() in {".html", ".htm", ".jinja", ".j2", ".tsx", ".jsx", ".vue", ".svelte", ".astro"} \
                and f != sample and any(s in f.read_text(encoding="utf-8", errors="replace") for s in sheets):
            files.append(f)  # a template that loads the stylesheet loads its fonts too
    chose = bool(fd and re.search(r"(?i)\bowner\b[^\"“]{0,30}[\"“][^\"”]{3,}[\"”]", fd))
    third, missing, have = [], [], {p.name for p in design_walk(base)}
    for f in dict.fromkeys(files):
        text = f.read_text(encoding="utf-8", errors="replace")
        rel = f.relative_to(base).as_posix()
        third += [(rel, u) for u in dict.fromkeys(FONT_URL.findall(text))]
        for face in re.findall(r"(?is)@font-face\s*\{(.*?)\}", text):
            for u in re.findall(r"url\(\s*[\"']?([^\"')]+)", face):
                if not re.match(r"(?i)(?:https?:|data:)", u) and Path(u).name not in have:
                    missing.append(f"{rel}: {u}")
    if third and not chose:
        hosts = dict.fromkeys(f"{r} → {re.match(r'(?i)https?://([^/]+)', u).group(1)}" for r, u in third)
        gaps.append("fonts load from a third-party host the owner did not choose: " + "; ".join(hosts)
                    + " - self-host them (the font files + their licence in the project, @font-face), or record "
                      "the owner's choice `Font delivery: <service> - owner chose: \"<their words>\"`")
    if missing:
        gaps.append("a self-hosted font file is not in the project: " + "; ".join(missing[:3]))
    return gaps


def design_render_gaps(base: Path, body: str, override: bool) -> list[str]:
    """The rendered 3-width check really ran: render_check (re-run here) or the tool's own browser, with the
    screenshots saved. 2 of 4 logged runs recorded NOT RUN and one of them shipped a phone screen that scrolled
    sideways."""
    evs = [e for e in EVIDENCE.findall(body) if re.search(r"(?i)render_check|screenshot", e)]
    ev = next((e for e in evs if "render_check" in e), None)
    shot_ev = next((e for e in evs if "render_check" not in e), None)
    if ev is None and shot_ev is None:
        return ["no rendered check recorded - run `python <...>/render_check.py <sample> --main \"<the main action's "
                "text>\" --shots <folder>` and add `evidence: <that command> → <its last line> · <date>` (it cannot "
                "run: your tool's own browser at 375, 768 and 1440 px, `evidence: screenshots <folder> · <date>`)"]
    gaps = []
    if ev and re.search(r"(?i)\bNOT RUN\b|\bunverified\b", ev) and not override:
        gaps.append("the rendered check is recorded as NOT RUN - a check that did not run is not a check: `python -m "
                    "pip install playwright` and run it again, or use your tool's own browser at 375, 768 and 1440 px "
                    "and save the screenshots (only the owner's override, with their reason, answers it)")
    sm = re.search(r"--shots\s+[`\"']?([^\s`\"']+)", ev or "") or \
        re.search(r"(?i)screenshots?\s*(?:in|at|:)?\s+[`\"']?([\w./\\-]+)", shot_ev or "")
    folder = base / sm.group(1) if sm else None
    shots = [p for p in folder.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}] \
        if folder and folder.is_dir() else []
    if len(shots) < 3 and not override:
        gaps.append(f"fewer than 3 screenshots of the sample ({len(shots)} in "
                    f"{sm.group(1) if sm else 'no folder named'}) - `render_check.py ... --shots <folder>` saves one "
                    f"per width; name the folder in the evidence line")
    rm = RENDER_EVIDENCE.search(ev or "")
    if ev and rm is None:
        gaps.append("the render_check evidence line needs the sample's path and --main \"<the main action's text>\"")
    elif rm is not None and not gaps:
        code, text = render_recheck(base, rm.group(1), rm.group(2))
        if code == 1 and not override:
            fails = [l.strip() for l in text.splitlines() if "[FAIL]" in l or "REFUSED" in l]
            gaps.append(f"render_check fails on {rm.group(1)} now (`set` ran it): {'; '.join(fails[:4]) or text[:200]}"
                        f" - fix the sample, or record the user's override with their reason in #Design")
    return gaps


def design_doc_gaps(design: str, body: str) -> list[str]:
    """DESIGN.md reads like a document for a person (owner rule: readable like the best plain doc), states no count
    it did not measure, and names no brand the owner did not name."""
    gaps = []
    head = re.split(r"(?m)^##\s+1\.", design, maxsplit=1)[0]
    traced = [l for l in head.splitlines() if re.search(r"#(?:Vision|Scope)\b", l)]
    if not re.search(r"(?m)^##\s+\D", head) or len(traced) < 4:
        gaps.append("DESIGN.md does not open for a reader - before `## 1.`, a `## In short` section: what this "
                    f"design is for in plain words, then each principle with the #Vision or #Scope line it comes "
                    f"from ({len(traced)} traced, 4-6 wanted)")
    own = next((l for l in body.splitlines() if re.search(r"(?i)own (?:reference|look)", l)), "")
    brands = re.search(r"(?im)^.*\breference brands?\b\**\s*:?\**\s*(\S.*)$", design)
    if brands and re.search(r"(?i)\bno\b[^.]{0,30}\b(?:product|brand|reference)|\bnone\b|\bno preference", own):
        gaps.append(f"DESIGN.md lists Reference brands ({brands.group(1)[:60]}) the owner never named (their own "
                    f"reference: {own.split(':', 1)[-1].strip()[:80]}) - delete the line")
    typed = [m.group(0) for l in design.splitlines() if not l.startswith(AUDIT_LINE)
             for m in [re.search(r"(?i)\b\d+\s+(?:checks?\s+)?pass(?:ed|es)?\b(?:\s+checks)?", l)] if m]
    if typed:
        gaps.append(f"DESIGN.md states an audit count by hand (\"{typed[0]}\") - delete it: `set` writes the audit's "
                    f"own counts")
    return gaps


def design_write_audit(base: Path, path: Path, design: str, sample: str | None, today: str) -> None:
    """The audit's own counts, written by the script (3 of 4 logged DESIGN.md files stated a count the close
    contradicted: 50 against 150)."""
    engine = tool_file("frontend-audit", "audit.py")
    if engine is None:
        return
    targets = ["DESIGN.md"] + ([sample] if sample else [])
    r = subprocess.run([sys.executable, str(engine), *targets], cwd=base, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")  # one run: ~3 s each
    c = re.search(r"(\d+) pass \| (\d+) warn \| (\d+) error", r.stdout)
    if not c:
        return
    line = (f"{AUDIT_LINE}, {today}):** `audit.py {' '.join(targets)}`: {c.group(1)} pass · {c.group(2)} warn · "
            f"{c.group(3)} fail")
    lines = design.splitlines()
    at = next((i for i, l in enumerate(lines) if l.startswith(AUDIT_LINE)), None)
    if at is not None:
        lines[at] = line
    else:
        h2 = next((i for i, l in enumerate(lines) if re.match(r"##\s+2\.", l)), None)
        lines.insert(h2 + 1 if h2 is not None else len(lines), line)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def render_recheck(base: Path, sample: str, main: str) -> tuple[int, str]:
    """render_check.py over the recorded sample, as the evidence line names it: 0 pass, 1 fail, 3 not run here."""
    engine = tool_file("frontend-audit", "render_check.py")
    if engine is None or not (base / sample).is_file():
        return 3, ""
    try:
        r = subprocess.run([sys.executable, str(engine), sample, "--main", main], cwd=base, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=180)
    except subprocess.TimeoutExpired:
        return 3, ""
    return r.returncode, r.stdout + r.stderr


def run_habits() -> list[str]:
    """The call habits every `next` prints, with or without a STATUS.md."""
    out = ["  - fewest calls (each re-sends the whole conversation): independent reads and commands in ONE call; "
           "a big file once, early, or by section; never open a playbook script. Conversation summarised "
           "mid-run? run this same `next` again - it reprints where you are; never re-read files to rebuild it",
           # a logged /test ran six python scripts that rewrote test files (27-61 s each, +19% time vs plain); the
           # 169 mined sessions: edit-by-script = 9.3% of all tokens
           "  - write and change code, tests and docs with the edit tool (several edits to one file in one "
           "call) - never a python/sed script that rewrites files: each is slower, breaks on quoting, and puts "
           "the code in the conversation twice"]
    if playbook_tool() == "codex":  # a logged Codex /architect checked a 2-minute file write 9 times: 1.2M tokens
        out.append("  - Codex: a command or file write still running - wait for it with ONE long wait (yield_time_ms "
                   "120000), never repeated short checks: each check re-sends the whole conversation.")
    if playbook_tool() == "antigravity":  # a logged Antigravity /test spent 89 of its 183 calls polling
        out.append("  - Antigravity: give every command WaitMsBeforeAsync 10000 (the longest it takes); a command "
                   "that still goes to the background (the gate and a suite take 1-2 min) gets ONE schedule timer "
                   "tied to it - TimerCondition = its task id, DurationSeconds 300 - and nothing else until it "
                   "fires: never manage_task status checks or 10 s timers (each re-sends the whole conversation). "
                   "Never open a task's log whole - the gate prints the result lines.")
        out.append("  - Antigravity: ask questions as numbered lines to answer by typing, or with your ask tool's "
                   "form - never draw ○ circles in the text: they look clickable and are not.")
    return out


# The research helper per tool (CAPABILITIES.md §Subagents). Plain Claude started one at once on the same HR task:
# 18 searches and 7 page reads in its own context, while the main conversation asked; every playbook run searched
# 3-6 times in its own and missed the rules that apply and the products doing the exact job (2026-09-30).
HELPER_ROUTE = {
    "claude": "the Agent tool with run_in_background: the helper agent whose name ends `vision-research` (a "
              "general-purpose one told to read and follow the brief, when that name is not listed)",
    "cursor": "a Task sub-agent with run_in_background: `vision-research` from .cursor/agents/ (or one told to read "
              "and follow the brief)",
    # Antigravity's subagent tool is behind a feature switch (`enable-teamwork-subagent`), off on a logged install:
    # the run spent 2 steps looking for it (2026-10-01). Name the tool and the fallback in one line.
    "antigravity": "`invoke_subagent` - ONLY if it is in your tool list: the subagent `vision-research` from "
                   ".agents/agents/ (or one told to read and follow the brief). Not in your list: there is no helper - "
                   "after round 1's answers run the brief's searches yourself, ALL in one step (several search_web "
                   "calls in "
                   "one turn), then open the key pages",
    "codex": "spawn_agent - this skill explicitly asks you to spawn it: one agent told to read and follow the brief",
}
# How each tool hands the report back. A logged Cursor /vision read the helper's transcript twice while it ran, and the
# user had to send "continue" and "ok" to keep it moving - each a full turn (2026-10-01).
HELPER_WAIT = {
    "claude": "end your turn - the helper's result arrives as a notification on its own",
    "cursor": "end your turn - Cursor sends a message when the sub-agent completes",
    "antigravity": "wait for the subagent to finish - never poll its files or log",
    "codex": "wait for it with ONE `wait_agent` call (it returns when the report is in)",
}


VISION_LAST = "Last (some tools cut long output - this is the step most often missed):"


def vision_last() -> str:
    """The start's closing block: the version line and the helper step again. A logged Antigravity run's output was
    cut at ~4 KB from the top, and it spent 2 steps re-running `next` for the first line (2026-10-01). Only that
    tool cuts this way, so only its start carries the repeat."""
    if playbook_tool() != "antigravity":
        return ""
    return f"{VISION_LAST}\n{playbook_line()}\n{vision_helper_line()}"


START_FILE = "vision-start.md"
# what each phase's start file holds, named in the short start so the run knows it needs nothing else
START_HOLDS = {
    "vision": "the #Vision field labels, the docs/vision.md layout,\n    the close",
    "scope": "the #Vision lines /scope builds on, the questions, the #Scope\n    labels and items, this phase's rules, "
             "the close",
    "plan": "#Scope whole, the questions, the #Plan labels, this phase's\n    rules, the close",
    "structure": "#Architecture whole, the Dev tooling files, the decision homes,\n    the #Structure labels, this "
                 "phase's rules",
    "dev-check": "the milestone's tickets, the gate and live-path commands,\n    #Plan's and #Scope's lines, this "
                 "phase's rules",
    "test": "the built tickets beside their tests, the surfaces, the database,\n    the commands, the record format, "
            "this phase's rules",
    "build": "the ticket, its files, the contract rules, the commands, what it\n    must NOT do, the coding rules",
}


def fit_start(full: str, phase: str = "vision") -> str:
    """A phase's start, as this tool can read it. Antigravity shows ~4 KB of a command's output and cuts the top:
    a logged /vision run lost the #Vision field labels that way, then read status.py 18 times, a slice at a time, to
    rebuild them (3.05M tokens against plain's 0.59M, 2026-10-01; the file start: 1.12M). /scope's start is ~12 KB
    and /plan's ~14 KB, so they go the same way. There the full start goes to a file it opens once with view_file
    (46 KB per read), and the output stays short. Every other tool gets the full text, unchanged."""
    if playbook_tool() != "antigravity":
        return full
    f = Path(__file__).resolve().parent / (START_FILE if phase == "vision" else f"{phase}-start.md")
    last = vision_last() if phase == "vision" else ""
    f.write_text(full + "\n\n" + last + "\n", encoding="utf-8")
    return "\n".join([
        "Your tool shows only the end of a long output, so this phase's start is in a file:",
        f"  - FIRST: open `{f.as_posix()}` ONCE with view_file - {START_HOLDS[phase]}. Everything you need is there: "
        "never open status.py, the template or `set --help`.",
        *([last] if last else [])])


def vision_helper_line() -> str:
    """The research-helper instruction - printed in the start AND as its last line: a logged Antigravity /vision got
    the start with its first 23 lines cut ("<truncated 23 lines>"), never saw this line, and searched 4 times itself
    in English (2026-10-01)."""
    brief = tool_file("agents", "vision-research.md")
    brief = brief.as_posix() if brief else "agents/vision-research.md"
    route = HELPER_ROUTE.get(playbook_tool())
    # two rounds of questions (owner, 2026-10-01): the helper starts in the FIRST reply, beside round 1, so it
    # researches while the owner answers
    helper = (f"  - Research helper: in your first reply, beside round 1's questions, start {route}, brief `{brief}`, "
              f"given the owner's requirement word for word (it names no product or user: start it after round 1, "
              f"with the answers). It is the only research pass: never search yourself meanwhile, never open its "
              f"files or log. Its report not in when round 1's answers arrive: say in one line that the market check "
              f"is still running and the user need not reply, then {HELPER_WAIT.get(playbook_tool(), 'wait for it')}; "
              f"then give the first verdict" if route else
              f"  - Research: no helper on this tool - after round 1's answers, run the searches of `{brief}` "
              f"yourself, ALL in one message")
    if playbook_tool() == "codex":
        # the Codex app drops a sub-agent's result that arrives after its parent turn ended ("dropping turn-scoped
        # item for unknown turn id ... subagent-completed") and then holds the user's messages in a queue that never
        # sends - a logged run was stuck after round 1 (2026-10-01). So: spawn and wait in ONE turn.
        helper = (f"  - Research helper (Codex): NOT in your first reply. When round 1's answers arrive, in that same "
                  f"turn: {route}, brief `{brief}`, given the requirement and round 1's answers word for word; tell "
                  f"the user in one line the market check takes about 2 minutes; then ONE `wait_agent` call; then the "
                  f"first verdict. Never end a turn while it runs: Codex loses the user's next message. It is the only "
                  f"research pass: never search yourself, never open its files or log")
    return helper


def vision_start_text(new: bool = False) -> str:
    """`next --phase vision`: what to write and what `set vision filled` refuses, so a run meets it the first time."""
    tpl = tool_file("templates", "PRODUCT.md")
    fields = product_sections(tpl.read_text(encoding="utf-8")).get("Vision", "") if tpl else ""
    fields = "\n".join(l for l in fields.splitlines() if l.startswith("- **") and "**Read" not in l)
    helper = vision_helper_line()
    return ("/vision start:\n"
            + ("  - Fresh start: no STATUS.md, no PRODUCT.md, no code - nothing to read or probe; ask round 1.\n"
               if new else "")
            + "  - In your first reply: load your web-search tool now (a deferred tool costs a turn later). "
            "Commands run in the project folder already: never `cd <path> &&`.\n"
            + helper + "\n"
            "  - #Vision is these fields, labels as written, each one line `- **<label>:** <value>`, in a scratch file "
            "outside the repo:\n"
            + "\n".join("      " + l for l in fields.splitlines()) + "\n"
            "  - Keep the owner's answers in the conversation; write docs/vision.md ONCE, in one call, after round 2: "
            "a founder's document in plain paragraphs (order in the skill's Step 3), then `## Appendix` with "
            "`### Owner's answers` (each answer word for word, one per question) · `### Search list` (one line each: "
            "`- why now · <query> · what it settled · <link>`; a `local ·` line - the market the owner named, in its "
            "language(s), first - a `same job ·` line - this exact job anywhere - `nearby ·` lines, and a `rules ·` "
            "line) · `### North-star terms` (`| Term | Number | From |`, From = owner · proposed · searched · derived; "
            "the owner gave no bar: `bar: not set`)\n"
            "  - Close (never measure line lengths or re-read files to check: `set` wraps and checks): "
            "`set vision filled --section-from <file>` + (no STATUS.md yet) `--product \"<name>\"` + "
            "`--ai yes|no --agent yes|no` + `--commit \"<one line>\"` (the drafts message asked "
            "\"Anything to change? If not: Save this version of your project? (yes / no)\"; leave it out on a no): "
            "one call writes PRODUCT.md (from the template when there is none), makes "
            "STATUS.md, records the AI answer, fills the `Read:` line from README.md (nothing else to quote unless "
            "you opened another input file) and saves - then prints the rest of the close. The first verdict opens "
            "round 2's message, never a turn of its own. It refuses, every problem in one list: an empty field · a "
            "target without a number and a date · "
            "a search line without a link or with only a search redirect, no `why now ·` line (or the problem not "
            "marked `why now: the owner's claim, "
            "not verified`), no `local ·`, `same job ·` or `rules ·` line · no Owner's answers · a terms row with no number or "
            "no From · the AI answer not recorded · an AI product's empty AI line · LaTeX.\n"
            "  - Who it's for, who asks and the business model stay in the owner's words: never narrow or widen them.\n"
            "  - The user stops after the first verdict: `status.py set vision declined --reason \"stopped after the "
            "first verdict: <their words>\" --gate vision` (no STATUS.md yet: add `--product \"<name>\"`) - never a "
            "filled record without round 2.")



# A new project has no record to re-run, resolve or decline over (the declined command is in the start itself):
# a logged Antigravity /vision said the start's rules were the bulk of every turn it re-sent
NEW_PROJECT_SKIP = {"vision": {"Spine resolution", "Re-run semantics", "Declined runs"}}


def phase_rules_text(phase: str, new: bool = False) -> str | None:
    want = PHASE_RULES.get(phase)
    if not want:
        return None
    if new and phase in NEW_PROJECT_SKIP:
        want = {k: [x for x in v if x not in NEW_PROJECT_SKIP[phase]] for k, v in want.items()}
    parts = [f"Rules for /{phase}, word for word from the rule files (these ARE the rule files for this phase - do "
             f"not open them):"]
    for name, secs in want.items():
        parts.append(f"===== {name} =====\n" + print_sections(rule_file(name), secs))
    return "\n\n".join(parts)


# ---- /scope: P1 + P2 + P4 for the anti-creep phase ----------------------------------------------------------------
# Its start read ~48 KB whole (PRINCIPLES.md + MECHANISMS.md + all of PRODUCT.md) and re-sent it on every question
# turn; every stop (one core feature, a trigger per deferred item, every table-stakes item sorted) was a sentence. The
# start now prints the #Vision fields scope decides against and the table stakes for THIS product kind; `set scope
# filled` refuses the countable gaps, every problem once, on its own close only (never in phase_check: a project
# filled under older rules is not blocked later, and /adopt's inferred record is not refused).
PHASE_RULES["scope"] = {
    "PRINCIPLES.md": ["Communication", "Reviews, vision & confidence"],
    "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status"],
}
PHASE_CLOSE_RULES["scope"] = {"PRINCIPLES.md": ["The exit-criteria gate"],
                              "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"]}
SCOPE_FIELDS = (("THE core feature", r"core feature"), ("In scope (now)", r"^in[- ]scope"),
                ("Deferred", r"^deferred"), ("Non-goals", r"non[- ]goal"), ("Table stakes", r"table[- ]stakes"))
# (what the start prints, the words that find its line in the record). The generic list was a consumer app's; on a
# logged internal AI product plain Claude raised data-protection law, AI law and languages, and no playbook run did.
SCOPE_STAKES = (
    ("password reset", r"password"), ("email verification", r"verif"),
    ("account deletion + data export (often a legal duty)", r"delet|export"),
    ("empty / loading / error states", r"error|empty|loading"), ("privacy policy + terms", r"privacy|terms"),
    ("accessibility baseline", r"accessib|a11y|wcag"), ("a way for a user to report a problem", r"report|feedback"),
    ("the rules that apply - name each: data protection, AI law, sector law (or why none)",
     r"rules? that apply|regulat|gdpr|data protection|\blaw\b|legal|complian"),
    ("the languages its users need", r"language|locali[sz]|translat|i18n"))
SCOPE_AI_STAKES = (
    ("known-answer test cases the AI must pass before release (#Vision's accuracy bar)",
     r"test cases|known[- ]answer|\bevals?\b|golden|accuracy"),
    ("prompt injection: text from users or data that tries to steer the AI", r"inject"),
    ("the cost cap per use (#Vision's cost per use)", r"\bcost|spend|budget"),
    ("what happens when the AI is wrong or unsure", r"wrong|unsure|fallback|escalat|hand[- ]?off"))
SCOPE_AGENT_STAKES = (
    ("what the agent may do on its own, as a list", r"may do|allowed|permission|read[- ]only|on its own"),
    ("a stop switch that halts it", r"\bstop|kill|pause|disable|switch"),
    ("a log of every action it takes", r"\blog|audit|trail"))
SCOPE_VISION = (("who it's for", r"^who\b"), ("value proposition", r"value prop"), ("north-star target", r"target"),
                ("input metrics", r"input"), ("riskiest assumption", r"riskiest"),
                ("business model", r"business model"), ("AI", r"^ai\b"),
                ("constraints", r"constraint|regulat|rules|language"))
HIDDEN_STAKE = {"email verification": r"e-?mail verif|verif\w* (?:of )?(?:the |an |their )?e-?mail",
                "a log of every action it takes": r"\blog(?!in)|audit|trail"}
SCOPE_VERDICT = re.compile(r"(?i)(?:^|[:—–|→(]|\s-|\*\*)\s*\**\s*(in[- ]scope(?: now)?|in \(?now\)?|now|in|"
                           r"deferred|defer|later|n/?-?a|not applicable|out)\b")
SCOPE_TRIGGER = re.compile(r"(?i)\b(when|once|if|after|until|unless|trigger(?:ed)?|as soon as|before)\b|→|->")
SCOPE_REASON = re.compile(r"(?i)(?:n/?-?a|not applicable)\**\s*[)\]:—–,(-]*\s*\w{2,}|\bbecause\b|\bno\s|\bnot\s|"
                          r"\bsince\b|\bonly\b|\bnone\b")
SCOPE_NUMBER = re.compile(r"(?<![\w.§/-])[€$£]?\d+(?:[.,]\d+)*")
SCOPE_NUMBER_OK = re.compile(r"(?i)\b(?:wcag|art\.?|article|iso|section|§|level)\s*$")
SCOPE_FIELD = re.compile(r"^(?:[-*]\s+)?\*\*(.+?)\*\*:?\s*(.*)$")  # `**Label:** value` with or without "- " (P8)


def scope_fields(body: str) -> dict[str, list[str]]:
    """#Scope's fields: label -> its lines (the inline value, then every line to the next field: sub-bullets,
    table rows, reflowed text). Accepts `**Label:**` with or without a leading "- " (P8)."""
    out: dict[str, list[str]] = {}
    label, item_ind, group = None, -1, None
    for line in body.splitlines():
        m = SCOPE_FIELD.match(line) if not line.startswith((" ", "\t")) else None
        ind = len(line) - len(line.lstrip())
        if m:
            label, item_ind, group = m.group(1).strip().rstrip(":"), 0, None
            out[label] = [m.group(2).strip()] if m.group(2).strip() else []
        elif line.startswith("#"):
            label = None
        elif label and line.strip():
            s_ = line.strip()
            # reflow()'s continuation line: deeper than the item above it, no list marker or table pipe
            if out[label] and ind > item_ind and not re.match(r"[-*+|]\s|\d+[.)]\s|\|", s_):
                out[label][-1] += " " + s_
                continue
            # a group heading ("- the rules that apply:") with its verdicts on the deeper items under it: each child
            # is read as "<heading> <child>" (a logged Cursor /scope wrote that shape and was refused for it, P8)
            if ind > item_ind and out[label] and out[label][-1].rstrip().endswith(":"):
                group = (re.sub(r"^[-*+]\s+", "", out[label].pop()).rstrip(), item_ind)
            elif group and ind <= group[1]:
                group = None
            out[label].append(f"{group[0]} {re.sub(r'^[-*+]\s+', '', s_)}" if group and ind > group[1] else s_)
            item_ind = ind
    return out


def scope_items(lines: list[str], whole=None, named=None) -> list[str]:
    """One entry per item: a line, a table row's cells joined, or a ` · `/`;` part outside brackets. With `whole`
    (the test an item must pass): a line that passes it is split only if every part passes it too - a `;` inside one
    sorted line is a sentence, not more items (all four tools were refused on a logged /scope close) - unless
    a part without its own verdict names a required item (`named`) that the line's first part does not."""
    items = []
    rule = re.compile(r"^\|?[-: |]+\|?$")
    for n, line in enumerate(lines):
        s = re.sub(r"^[-*+]\s+|^\d+[.)]\s+", "", line.strip()).strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            # a separator row, or the header row above one (any words: "Why / trigger")
            if rule.match(s) or (n + 1 < len(lines) and rule.match(lines[n + 1].strip())):
                continue
            items.append(" | ".join(cells))
            continue
        parts, part, depth = [], "", 0
        for i, ch in enumerate(s):
            depth += 1 if ch in "([" else -1 if ch in ")]" else 0
            if depth <= 0 and (ch == ";" or (ch == "·" and s[i - 1:i] == " ")):
                parts.append(part.strip())
                part = ""
            else:
                part += ch
        parts = [x for x in parts + [part.strip()] if re.search(r"\w", x)]
        keep = whole and len(parts) > 1 and whole(s) and not all(whole(x) for x in parts)
        if keep and named:
            own = set(named(parts[0]))
            keep = not any(set(named(x)) - own for x in parts[1:] if not whole(x))
        items += [s] if keep else parts
    return [i for i in items if re.search(r"\w", i)]


def scope_stakes(header: dict[str, str]) -> list[tuple[str, str]]:
    """The table stakes this product sorts: the base list, plus the AI list and the agent list by its flags."""
    return list(SCOPE_STAKES) + (list(SCOPE_AI_STAKES) if header.get("AI product") == "yes" else []) \
        + (list(SCOPE_AGENT_STAKES) if header.get("Agent") == "yes" else [])


def scope_gaps(base: Path, st: "Status") -> list[str]:
    """What `set scope filled` needs, every problem named once in one list (P20)."""
    prod = base / "PRODUCT.md"
    secs = product_sections(prod.read_text(encoding="utf-8")) if prod.is_file() else {}
    body = re.sub(r"<!--.*?-->", "", secs.get("Scope", ""), flags=re.S)
    fields = scope_fields(body)
    got = {what: next((v for k, v in fields.items() if re.search(rx, k, re.I)), None) for what, rx in SCOPE_FIELDS}
    gaps = []
    for what, lines in got.items():
        if lines is None or not scope_items(lines) or all(EMPTY_VALUE.match(re.sub(r"[*_`\s]+", " ", i).strip().lower())
                                                          for i in scope_items(lines)):
            gaps.append(f"#Scope field empty: {what}")
    core = " ".join(got["THE core feature"] or [])
    # one sentence may hold a ";" - only a `·` list or a numbered list is several things
    if len([i for i in re.split(r"\s·\s", core) if i.strip()]) > 1 or re.search(r"(?:^|\s)1[.)]\s.*\s2[.)]\s", core):
        gaps.append("#Scope: THE core feature names more than one thing (a `·` or numbered list) - one capability "
                    "on one line; the others go to In scope, Deferred or Non-goals")
    for item in scope_items(got["Deferred"] or [], SCOPE_TRIGGER.search):
        if not SCOPE_TRIGGER.search(item) and not EMPTY_VALUE.match(item.lower()):
            gaps.append(f"#Scope Deferred item with no trigger: {item[:80]!r} - add what brings it in (`when <signal>`)")
    # a hidden required item is named by its own words; the presence patterns are looser on purpose ("login" is not
    # a log, "anything requiring verification" is not email verification - a replay of logged runs, 2026-10-03)
    required = [(w, HIDDEN_STAKE.get(w, rx)) for w, rx in scope_stakes(st.header)]
    stakes = scope_items(got["Table stakes"] or [], SCOPE_VERDICT.search,
                         lambda x: [w for w, rx in required if re.search(rx, x, re.I)])
    for item in stakes:
        m = SCOPE_VERDICT.search(item)
        if not m:
            gaps.append(f"#Scope table-stakes line not sorted: {item[:80]!r} - `<item>: in now` · `<item>: deferred - "
                        f"when <trigger>` · `<item>: N/A - <reason>`")
        elif re.match(r"(?i)defer|later|out", m.group(1)) and not SCOPE_TRIGGER.search(item):
            gaps.append(f"#Scope table-stakes item deferred with no trigger: {item[:80]!r}")
        elif re.match(r"(?i)n/?-?a|not applicable", m.group(1)) and not SCOPE_REASON.search(item):
            gaps.append(f"#Scope table-stakes item N/A with no reason: {item[:80]!r}")
    if got["Table stakes"] is not None:
        gaps += [f"#Scope table stakes: no line for {what.split(' - ')[0].split(' (')[0]!r} - sort it (in now / "
                 f"deferred + trigger / N/A + reason)" for what, rx in scope_stakes(st.header)
                 if not any(re.search(rx, i, re.I) for i in stakes)]
    vision = {m.group(0).replace(",", "") for m in SCOPE_NUMBER.finditer(secs.get("Vision", ""))}  # whole numbers
    for label, lines in fields.items():
        if re.match(r"(?i)read|detail", label):
            continue
        for item in scope_items(lines):
            if re.search(r"(?i)propos|owner|user said|vision", item):
                continue
            bad = [n for m in SCOPE_NUMBER.finditer(re.sub(r"\b20\d\d(?:-\d\d){0,2}\b|`[^`]*`", "", item))
                   if not SCOPE_NUMBER_OK.search(item[:m.start()]) and (n := m.group(0).replace(",", "")) not in vision]
            if bad:
                gaps.append(f"#Scope number {bad[0]!r} is not in #Vision and not marked - `(proposed)` when you "
                            f"suggested it, `(owner)` when the user said it: {item[:70]!r}")
    if st.state("validate") == "running" and not re.search(r"(?i)provisional", body):
        gaps.append("#Validation is running and #Scope marks nothing `provisional` - mark each decision that depends "
                    "on the pending result")
    comp = base / OWN_COMPANION["Scope"]
    if not comp.is_file():
        gaps.append(f"no {OWN_COMPANION['Scope']} - it holds the reasoning, the answers and the sorting's why")
    elif not any(OWNER_ANSWERS.match(l) for l in comp.read_text(encoding="utf-8").splitlines()):
        # as /vision and /plan: the core feature and the items are checked against the owner's own words
        gaps.append(f"{OWN_COMPANION['Scope']} has no `## Owner's answers` - each answer word for word, one per "
                    f"question")
    return gaps


def scope_start_text(st: "Status") -> str:
    """`next --phase scope`: what #Vision decided, what to write and what `set scope filled` refuses (P1, P4)."""
    base = st.base if st.base is not None else Path(".")
    prod = base / "PRODUCT.md"
    secs = product_sections(prod.read_text(encoding="utf-8")) if prod.is_file() else {}
    vis = scope_fields(re.sub(r"<!--.*?-->", "", secs.get("Vision", ""), flags=re.S))
    out = ["/scope start (never read PRODUCT.md or the rule files whole - what /scope decides against is here):"]
    shown = [(what, " ".join(v)) for what, rx in SCOPE_VISION for k, v in vis.items() if re.search(rx, k, re.I)]
    if shown:
        out.append("  - #Vision, the parts scope is decided against:")
        out += [f"      {what}: {val[:500]}{'…' if len(val) > 500 else ''}" for what, val in dict(shown).items()]
    else:
        out.append("  - #Vision is empty: say \"/vision looks incomplete - scope without a vision drifts\", offer "
                   "/vision first; the user goes on anyway -> record the override (Step 0)")
    val = st.state("validate")
    out.append("  - #Validation " + {"empty": "is empty (optional): #Vision's riskiest assumption is UNTESTED - say so "
                                              "when the core feature is chosen",
                                     "running": "is running: proceed provisionally - mark every decision that depends "
                                                "on the pending result `provisional`",
                                     }.get(val, f"is {val}: its verdict shapes the scope as recorded"))
    doc = base / OWN_COMPANION["Vision"]
    lines = doc.read_text(encoding="utf-8").splitlines() if doc.is_file() else []
    listed = search_list_lines(lines)  # the search list, not the owner's answers (they hold `·` too since next.55)
    found = [l.strip()[:200] for l in (listed if listed is not None else lines)
             if "·" in l and not l.lstrip().startswith(("|", "#")) and "no search" not in l.lower()][:8]
    if found:
        out.append("  - What /vision's searches found (docs/vision.md) - what every comparable ships is a "
                   "table-stakes candidate; no new search is needed:")
        out += [f"      {l}" for l in found]
    tpl = tool_file("templates", "PRODUCT.md")
    fields = product_sections(tpl.read_text(encoding="utf-8")).get("Scope", "") if tpl else ""
    out.append("  - #Scope is these fields, labels as written, in a scratch file outside the repo; `set scope filled "
               "--section-from <file>` writes it:")
    out += ["      " + l for l in fields.splitlines() if l.startswith("- **")]
    out.append("  - Table stakes for THIS product, one line each - `<item>: in now` · `<item>: deferred - when "
               "<trigger>` · `<item>: N/A - <reason>` (a table works too):")
    out += [f"      {what}" for what, _ in scope_stakes(st.header)]
    out += ["  - THE core feature and each item: in the user's words, each answer word for word under `## Owner's "
            "answers` in docs/scope.md. A number #Vision does not hold is marked `(proposed)` when you suggest it, "
            "`(owner)` when the user said it.",
            "  - `set scope filled` refuses, every problem in one list: an empty field · more than one core feature (a "
            "`·` or numbered list) · a Deferred item with no trigger (when / once / if / after / until) · a table "
            "stake above with no line, no verdict, deferred with no trigger or N/A with no reason · a number not in "
            "#Vision and not marked · #Validation running and nothing marked `provisional` · no docs/scope.md or no "
            "`## Owner's answers` in it.",
            "  - Two rounds, each ONE message or form: questions 1-3, then the table-stakes verdicts, question 5, "
            "the recommendation, any #Vision clash and \"Anything to change? If not: Save this version of your "
            "project? (yes / no)\" (either answer records it). After it, docs/scope.md and "
            "the section file in ONE message, then `set scope filled --section-from <file> --commit \"<one line>\"` "
            "(no `--commit` on a no) records, saves and prints the rest of the close."]
    return "\n".join(out)


# ---- /validate (2.0 alignment): one start, two rounds, the record checked in code (P1, P2, P20, P41) -------------
# Its Step 0 read PRINCIPLES.md, MECHANISMS.md and PRODUCT.md whole and asked "one block at a time". Two logged runs
# showed what no rule held: a bet about what owners DO tested by asking them (Gemini, finding G), and a bar whose
# counts could not be tied to a person (finding E). The start prints what the experiment tests; `set validate
# filled|running|overridden --section-from` refuses the countable gaps, every problem once, on its own close only.
PHASE_RULES["validate"] = {
    "PRINCIPLES.md": ["Communication", "Reviews, vision & confidence"],
    "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status"],
}
PHASE_CLOSE_RULES["validate"] = {"PRINCIPLES.md": ["The exit-criteria gate"],
                                 "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"]}
CLOSE_STEPS["validate"] = (
    "every number against #Vision: a bar that cannot falsify the riskiest assumption, a time box past the north-star "
    "date",
    "#Vision's riskiest assumption - the bet tested must be that one; an override reason that implies another "
    "customer or business model contradicts #Vision itself",
    "the fields, the bar's number and date, the result's date and the verdict word")
QUESTION_PHASES = QUESTION_PHASES + ("validate",)
START_HOLDS["validate"] = "the #Vision lines the bet comes from, the two rounds, the\n    #Validation labels, this " \
                          "phase's rules, the close"
VALIDATE_FIELDS = (("the assumption under test", r"^assumption"), ("the experiment", r"^experiment"),
                   ("the pass/fail threshold", r"^pass"), ("the measured result", r"^measured"),
                   ("the verdict", r"^verdict"))
VALIDATE_VISION = (("the riskiest assumption", r"riskiest"), ("who it's for", r"^who\b"),
                   ("the job to be done", r"job"), ("the north-star target", r"target|north"),
                   ("the business model", r"business"))
# finding G: a bet about what people DO needs a test that watches them do it (rung 3-5); asking is rung 2
VALIDATE_DOES = re.compile(r"(?i)\bwill\s+(?:\w+\s+){0,3}?(?:pay|allow|let|use|switch|buy|sign|subscribe|deposit|"
                           r"pre-?order|hand|send|return|adopt|install|share|replace|book|join|upload)\w*\b")
VALIDATE_ASKS = re.compile(r"(?i)\binterview|\bsurvey|\bquestionnaire|\bpoll\b|\bask(?:s|ing)?\b")
VALIDATE_WATCHES = re.compile(r"(?i)landing|fake[- ]door|concierge|wizard|pre-?sale|deposit|\bLOI\b|letter of intent|"
                              r"trial|pilot|hand-?run|by hand|manual|pre-?order|sign-?ups?|smoke test|switch|"
                              r"observ|watch")
# finding E: the bar says how each count is recorded and what ties it to the person or unit it counts
VALIDATE_COUNTED = re.compile(r"(?i)record|logg|tall(?:y|ied)|counted|tied|per (?:person|user|owner|shop|merchant|"
                              r"household|member|team|firm|visitor|customer|account)|sheet|form\b|signed|by name|"
                              r"e-?mail|analytics|dated|column|row|"
                              # P23: a desk check counts products or pages found, each with its link
                              r"\blinks?\b|listed|\bpages?\b|\bsources?\b|\burls?\b")
VALIDATE_VERDICT = re.compile(r"(?i)^\W*(proceed|pivot|kill)\b")


def validate_previous(base: Path) -> str:
    """#Validation as last saved (git HEAD): a re-run appends a dated entry and keeps every earlier line."""
    r = subprocess.run(["git", "show", "HEAD:PRODUCT.md"], cwd=base, capture_output=True, encoding="utf-8",
                       errors="replace")
    return product_sections(r.stdout).get("Validation", "") if r.returncode == 0 else ""


def validate_gaps(base: Path, st: "Status", new: str) -> list[str]:
    """What `set validate filled|running|overridden --section-from` needs, every problem named once (P20)."""
    prod = base / "PRODUCT.md"
    body = re.sub(r"<!--.*?-->", "", product_sections(prod.read_text(encoding="utf-8")).get("Validation", "")
                  if prod.is_file() else "", flags=re.S)
    gaps = []
    before = validate_previous(base) if st.state("validate") in ("filled", "overridden") else ""
    if before:  # a re-validation: the earlier entry stays word for word, in order; what follows it is checked
        lines, at, lost = body.splitlines(), 0, []
        for l in before.splitlines():
            if not l.strip() or l.lstrip().startswith(("- **Read", "- **Detail")):
                continue
            hit = next((i for i in range(at, len(lines)) if " ".join(lines[i].split()) == " ".join(l.split())), None)
            if hit is None:
                lost.append(l.strip())
            else:
                at = hit + 1
        if lost:
            gaps.append(f"#Validation is append-only: {len(lost)} line(s) of the earlier entry are gone, first "
                        f"{lost[0][:80]!r} - keep it word for word and add a new dated entry under it")
        body = "\n".join(lines[at:])
    fields = scope_fields(body)
    got = {what: " ".join(next((v for k, v in fields.items() if re.search(rx, k, re.I)), [""]) or [""]).strip()
           if any(re.search(rx, k, re.I) for k in fields) else None for what, rx in VALIDATE_FIELDS}
    empty = lambda v: v is None or bool(EMPTY_VALUE.match(re.sub(r"[*_`\s]+", " ", v).strip().lower()))  # noqa: E731
    if new == "overridden":
        for what, v in got.items():
            if v is None:
                gaps.append(f"#Validation: the {what} field is gone - an override keeps every field")
            elif empty(v):
                gaps.append(f"#Validation: {what} is blank - mark it `— not run (override <date>)`, never blank it")
        over = next((" ".join(v) for k, v in fields.items() if re.search(r"(?i)overrode|override", k)), "")
        over = re.sub(r"^\(the state itself:.*?\)\s*:?", "", over.strip())  # the template's label tail
        if empty(over):
            gaps.append("#Validation: the override field is empty - what stays untested, checked against #Vision")
        return gaps
    need = VALIDATE_FIELDS if new == "filled" else VALIDATE_FIELDS[:3]
    for what, _ in need:
        if empty(got[what]) or (new == "filled" and "PENDING" in (got[what] or "")):
            gaps.append(f"#Validation field empty: {what}" + (" (still PENDING: while the result is to come, record "
                                                                "`set validate running`)" if "PENDING" in
                                                               (got[what] or "") else ""))
    bet, test, bar = got["the assumption under test"] or "", got["the experiment"] or "", got["the pass/fail threshold"] or ""
    if bet and not re.search(r"(?i)\bwill\b", bet):
        gaps.append("#Validation: the assumption is not falsifiable - write it as `<who> will <behaviour> because "
                    "<reason>`")
    if bet and test and VALIDATE_DOES.search(bet) and VALIDATE_ASKS.search(test) and not VALIDATE_WATCHES.search(test):
        gaps.append(f"#Validation: the bet is about what people do ({VALIDATE_DOES.search(bet).group(0)!r}) and the "
                    f"experiment only asks them - a test that watches the action is rung 3, 4 or 5 (landing page, "
                    f"hand-run trial, pre-sale)")
    plain = re.sub(r"\b20\d\d-\d\d-\d\d\b", "", bar)
    if bar and not re.search(r"\d", plain):
        gaps.append("#Validation: the pass/fail threshold has no number - e.g. `at least 3 of 8 owners ...`")
    if bar and not VALIDATE_COUNTED.search(bar):
        gaps.append("#Validation: the threshold does not say how each count is recorded and what ties it to the "
                    "person or unit it counts (a dated row per owner, a signed-in form, a per-person link)")
    set_on = re.findall(r"\b(20\d\d-\d\d-\d\d)\b", bar)
    if bar and not set_on:
        gaps.append("#Validation: the threshold has no date - write the day it was set (`set 2026-10-06`): a bar "
                    "written after the result is not a test")
    if new == "filled":
        result, verdict = got["the measured result"] or "", got["the verdict"] or ""
        measured = re.findall(r"\b(20\d\d-\d\d-\d\d)\b", result)
        if result and "PENDING" not in result and not measured:
            gaps.append("#Validation: the measured result has no date")
        elif set_on and measured and min(set_on) > max(measured):
            gaps.append(f"#Validation: the threshold was set {min(set_on)}, after the result ({max(measured)}) - a "
                        f"bar set after the result is not a test")
        for path in re.findall(r"`?(docs/validation/[^\s`)]+)`?", result):
            if not (base / path.rstrip(".,;")).exists():
                gaps.append(f"#Validation: the raw notes {path!r} do not exist")
        if verdict and not VALIDATE_VERDICT.search(verdict):
            gaps.append("#Validation: the verdict does not start with proceed, pivot or kill")
    comp = base / OWN_COMPANION["Validation"]
    if not comp.is_file():
        gaps.append(f"no {OWN_COMPANION['Validation']} - it holds the reasoning and the owner's answers")
    elif not any(OWNER_ANSWERS.match(l) for l in comp.read_text(encoding="utf-8").splitlines()):
        gaps.append(f"{OWN_COMPANION['Validation']} has no `## Owner's answers` - each answer word for word")
    return gaps


def validate_start_text(st: "Status") -> str:
    """`next --phase validate`: what the experiment tests, the two rounds, the record and what `set` refuses."""
    base = st.base if st.base is not None else Path(".")
    prod = base / "PRODUCT.md"
    secs = product_sections(prod.read_text(encoding="utf-8")) if prod.is_file() else {}
    vis = scope_fields(re.sub(r"<!--.*?-->", "", secs.get("Vision", ""), flags=re.S))
    out = ["/validate start (never read PRODUCT.md or the rule files whole - what /validate tests is here):"]
    shown = {what: " ".join(v) for what, rx in VALIDATE_VISION for k, v in vis.items() if re.search(rx, k, re.I)}
    if shown.get("the riskiest assumption", "").strip():
        out.append("  - #Vision, what the experiment tests:")
        out += [f"      {what}: {val[:400]}" for what, val in shown.items() if val.strip()]
    else:
        out.append("  - #Vision has no riskiest assumption: say \"/vision looks incomplete - there is nothing testable "
                   "to validate\", offer /vision first; the user goes on -> ask them to state the assumption now")
    val = st.state("validate")
    row = st.phase("validate")
    out.append("  - #Validation " + {
        "empty": "is empty: a first run",
        "running": f"is running (due {row[3]}): the result is in -> fill the result and verdict, keep the rest, "
                   f"`set validate filled ... --note \"<result vs bar>\"`; not in -> the state stays running",
        "declined": "was declined before: a first run",
    }.get(val, f"is {val}: a re-validation - keep the earlier entry word for word and add a new dated entry under it "
                f"(`set` refuses a dropped line)"))
    tpl = tool_file("templates", "PRODUCT.md")
    fields = product_sections(tpl.read_text(encoding="utf-8")).get("Validation", "") if tpl else ""
    out.append("  - #Validation is these fields, labels as written, in a scratch file outside the repo:")
    out += ["      " + l for l in fields.splitlines() if l.startswith("- **") and "**Read" not in l]
    out += [
        "  - Two rounds, each ONE message: round 1 = Step 2's questions 1-4 (the bet, the cheapest test that can "
        "falsify it, the failing result, who and how they are reached); round 2 = ONE recommendation (experiment + "
        "bar + how each count is recorded + time box + due date), any #Vision clash, and two options: "
        "\"Looks good - save (Recommended)\" / \"Change something\".",
        "  - Then ONE message: docs/validation.md (reasoning; the owner's answers word for word under `## Owner's "
        "answers`) and the section file, then ONE record call:",
        "      result in now (a desk check): `set validate filled --section-from <file> --note \"<result vs bar>\" "
        "--commit \"<one line>\"`",
        "      result takes days: result and verdict `PENDING`; `set validate running --due <YYYY-MM-DD> --reason "
        "\"<what is measured> · pass: <the bar>\" --section-from <file> --commit \"<one line>\"` - the gate is NOT "
        "closed; offer the three ways forward (wait · proceed provisionally · override)",
        "      the user skips the test: `set validate overridden --reason \"<their words>\" --gate validate "
        "--section-from <file>` - every field kept, each marked `— not run (override <date>)`",
        "      (`--dry-run` lists every gap and writes nothing; leave `--commit` out on a no)",
        "  - `set` refuses, every problem in one list: an empty field (filled: a PENDING one) · a bet without "
        "`will` · a bet about what people do tested only by asking · a bar with no number, no date, or not saying "
        "how each count is recorded and tied to the person or unit · a result with no date or dated before the bar "
        "· raw notes named that do not exist · a verdict not proceed / pivot / kill · no docs/validation.md or no "
        "`## Owner's answers` · a re-run that drops a line of the earlier entry · an override that blanks a field.",
        "  - Must NOT: write #Scope or any later section, write code, or record a result nobody measured."]
    return "\n".join(out)


# ---- the support skills' starts (2.0): skills outside the chain, run with or without STATUS.md -------------------
# /drift-check, /adopt, /frontend-audit and /new-component each told the run to read PRINCIPLES.md, MECHANISMS.md and
# PRODUCT.md whole (or to find the audit engine itself). Each now has ONE start: `next --phase <skill>` prints the
# facts its first step needs, measured by the script (L3), and the rules it applies. SUPPORT_STARTS is filled below.
SUPPORT_STARTS: dict = {}
SPINE_DOCS = ("CLAUDE.md", "README.md", "docs", "AGENTS.md")


def support_status(path: Path) -> "Status | None":
    if not path.is_file():
        return None
    st = Status.load(path)
    st.base = path.resolve().parent
    return st


def support_close(st: "Status | None", skill: str) -> str:
    """The script-printed last line: with no STATUS.md there is no chain to point at. Printed at the start, so
    it says it comes last: a logged Cursor run said its handoff before the owner's yes."""
    card = handoff_card(st) if st is not None else ""
    return ("Close - after the report, never before; its last line, word for word:\n" + card) \
        if "Open a NEW conversation" in card else (
        f"Close - after the report, never before; its last line: \"Run /{skill} again whenever you want this "
        f"check; /playbook says what comes next.\"")


# P48 (2026-10-06): a playbook save failing on a new git cost one run 11.4M tokens editing the playbook's own script
SUPPORT_HABIT = ("  - Commands run in PowerShell and bash: one command per call - no &&, tail, grep or export. A playbook "
                 "command fails twice: stop, show the user the exact error and ask - never open or edit the "
                 "playbook's scripts (what they need is printed here, or a `--dry-run` lists it).")
# W32 / W66: the design round spent 449K on --help probes and ~1M reading the checkers' source
AUDIT_ARGS = ("  - audit.py takes: <files or folders> [--baseline <git-ref>] (only findings NEW since <ref>); it prints "
              "a scorecard, its first line the engine version; exit 0 = no ERROR, 1 = an ERROR, 2 = git cannot answer "
              "the --baseline. Never run --help or open audit.py.")


PHASE_RULES["drift-check"] = {
    "PRINCIPLES.md": ["Documentation-driven", "Communication", "Reviews, vision & confidence"],
    "MECHANISMS.md": ["Spine resolution", "Status", "Step 3b", "Step 3c"],
}


def drift_start_text(path: Path, today: str) -> str:
    """`next --phase drift-check`: which spine, what drift is judged against, and what the script measured."""
    base, st = path.resolve().parent, support_status(path)
    prod = base / "PRODUCT.md"
    out = ["/drift-check start (never read PRODUCT.md or the rule files whole - what the check compares is here):"]
    if prod.is_file():
        text = prod.read_text(encoding="utf-8", errors="replace")
        secs = {k: re.sub(r"<!--.*?-->", "", v, flags=re.S) for k, v in product_sections(text).items()}
        out.append("  - Spine: Tier 1 - PRODUCT.md (say so in the report)")
        vis, scope = scope_fields(secs.get("Vision", "")), scope_fields(secs.get("Scope", ""))
        for what, fields, rx in (("vision", vis, r"^vision\b"), ("north-star target", vis, r"target"),
                                 ("riskiest assumption", vis, r"riskiest"), ("core feature", scope, r"core feature"),
                                 ("Deferred (+ trigger)", scope, r"^deferred"), ("Non-goals", scope, r"non[- ]goal"),
                                 ("Table stakes", scope, r"table[- ]stakes")):
            val = next((v for k, v in fields.items() if re.search(rx, k, re.I)), None)
            if val:
                out.append(f"  - #{'Vision' if fields is vis else 'Scope'} {what}:")
                out += [f"      {l[:220]}" for l in val[:14]]
        sizes = sorted(((len(v.encode("utf-8")), k) for k, v in secs.items() if v.strip()), reverse=True)
        out.append(f"  - Size: PRODUCT.md {len(text.encode('utf-8')) / 1024:.1f} KB; largest sections: "
                   + ", ".join(f"#{k} {n / 1024:.1f} KB" for n, k in sizes[:3]) + " - apply the record test to these "
                   "only (Step 2 item 2)")
        claims = len(re.findall(r"(?m)^\s*-\s*\[x\]", text))
        ev = [(k, m.group(1).strip()) for k, v in secs.items() for m in EVIDENCE.finditer(v)]
        out.append(f"  - Claims: {claims} checked box(es); {len(ev)} `evidence:` line(s) - re-run each command "
                   f"(Step 0b), in one message:")
        out += [f"      #{k}: {line[:200]}" for k, line in ev[:25]]
        missing = [f"#{k}: {p}" for k in secs for p in evidence_problems(text, base, k)]
        out += [f"  - CONTRADICTED before any run (the script checked the artefact): {m}" for m in missing[:15]]
        if not secs.get("Validation", "").strip() and code_files(base, 1):
            out.append("  - #Validation is empty and code exists: name the riskiest assumption once as an untested "
                       "risk, not a finding (Step 2 item 4)")
    else:
        found = [n for n in SPINE_DOCS if (base / n).exists()]
        if found:
            out.append(f"  - Spine: Tier 2 - no PRODUCT.md; the project's own docs: {', '.join(found)} (open only "
                       f"these, in this order). Never create a PRODUCT.md; drift goes to the user and, if the project "
                       f"keeps a log/CHANGELOG, an offer to append it there")
        else:
            out.append("  - Spine: Tier 3 - code only, no recorded intent: say scope/vision drift cannot be judged, "
                       "give the INFERRED summary, recommend bootstrapping a spine (/adopt); never 'on-track', never "
                       "invented drift")
    if st is not None:
        late = [r for r in st.rows["Phases"] if r[1] == "running" and r[3] and r[3] < today]
        out += [f"  - STALLED gate: #{r[0]} running, due {r[3]}, no result - a finding (Step 2 item 3): {r[5][:120]}"
                for r in late]
        out.append(f"  - STATUS.md: {len(st.rows['Tickets'])} ticket row(s), {len(st.rows['Drift'])} earlier drift "
                   f"row(s) - compare the ticket rows with the code (Step 2 item 7)")
    agents = [n for n in AGENT_FILES if (base / n).is_file()]
    real = [n for n in agents if re.sub(r"(?s)<!--\s*BEGIN:.*?END:[^>]*-->", "",
                                        (base / n).read_text(encoding="utf-8", errors="replace")).strip()]
    if (prod.is_file() or (base / "STATUS.md").is_file()) and not real:
        out.append(f"  - NO agent instructions: {'only a generated block in ' + ', '.join(agents) if agents else 'no CLAUDE.md, AGENTS.md or GEMINI.md'} "
                   f"- a finding (Step 2 item 8)")
    out += ["  - The report: on-track, or each drift with a cut / re-scope (+ trigger) / fix. One message ends it: "
            "\"Record these drifts? Looks good - record (Recommended) / Change something\"; on a yes, one "
            "`status.py drift --found \"<drift>\" --rec \"<cut / re-scope+trigger / fix>\"` per drift, all in that one "
            "message (Tier 1 only).",
            "  - Must NOT: change code, cut a feature, edit PRODUCT.md, create a PRODUCT.md, or call a claim met "
            "without re-running its evidence.",
            support_close(st, "drift-check")]
    return "\n".join(out)


SUPPORT_STARTS["drift-check"] = drift_start_text


# /adopt: the survey is the script's (L3), the draft is confirmed in two rounds, and ONE call writes PRODUCT.md,
# STATUS.md and each confirmed section's row - it was `init` + one `set` per section, every one re-sending the
# conversation, with "nothing un-tagged left" and "never overwrite" as sentences nothing checked.
PHASE_RULES["adopt"] = {
    "PRINCIPLES.md": ["Documentation-driven", "Communication"],
    "MECHANISMS.md": ["Spine resolution", "Status", "Step 3c"],
}
PHASE_CLOSE_RULES["adopt"] = {"PRINCIPLES.md": ["The exit-criteria gate"],
                              "MECHANISMS.md": ["Step 3b", "Commit the work", "Plain-language close"]}
CLOSE_STEPS["adopt"] = ("every number carried in from the repo against what the owner just confirmed",
                        "the project's own docs: a README feature the code no longer has, a stack the README still names",
                        "the tags, the provenance line and which sections were already filled")
ADOPT_TAG =re.compile(r"\(inferred\s*[—–-]+\s*confirm\)", re.I)
ADOPT_PROVENANCE = re.compile(r"(?im)^_?adopted (20\d\d-\d\d-\d\d) from:?\s*(.+?)_?\s*$")
ADOPT_META = ("package.json", "pyproject.toml", "setup.py", "setup.cfg", "Cargo.toml", "go.mod", "Gemfile",
              "composer.json", "pom.xml", "build.gradle", "requirements.txt")
ADOPT_ENTRY = re.compile(r"^(?:main|app|server|index|manage|wsgi|asgi|cli|__main__)\.(?:py|js|ts|mjs|go|rb)$")
ADOPT_ROUTE = re.compile(r"@(?:app|router|bp|blueprint|api)\.(?:get|post|put|patch|delete|route)\(\s*[\"']([^\"']+)|"
                         r"\b(?:app|router)\.(?:get|post|put|patch|delete)\(\s*[\"'`]([^\"'`]+)")
ADOPT_SKIP_PHASES = VERIFY  # a verdict needs the verification phase itself: adopt leaves those rows empty


def adopt_start_text(path: Path, today: str) -> str:
    base, st = path.resolve().parent, support_status(path)
    prod = base / "PRODUCT.md"
    out = ["/adopt start (never read the rule files whole; the repo survey below is the script's - open only the "
           "files it names):"]
    if prod.is_file():
        secs = product_sections(prod.read_text(encoding="utf-8", errors="replace"))
        empty = [k for k, v in secs.items() if not has_content(v)]
        out.append(f"  - STOP: PRODUCT.md exists - never overwrite it. Offer exactly one thing: fill only its empty "
                   f"sections ({', '.join('#' + k for k in empty) or 'none'}); every filled one stays as written")
    found = [n for n in ("CLAUDE.md", "README.md", "AGENTS.md") if (base / n).is_file()]
    docs = sorted(p.relative_to(base).as_posix() for p in (base / "docs").rglob("*.md"))[:10] \
        if (base / "docs").is_dir() else []
    meta = [n for n in ADOPT_META if (base / n).is_file()]
    files = project_files(base)
    entries = [p.relative_to(base).as_posix() for p in files if ADOPT_ENTRY.match(p.name)][:8]
    tests = sorted({p.relative_to(base).parts[0] for p in files if is_test(p.relative_to(base).as_posix())})[:5]
    ci = [c for c in CI_FILES if (base / c).exists()]
    routes = []
    for p in files:
        if p.suffix in SOURCE and len(routes) < 30:
            routes += [f"{m.group(1) or m.group(2)} ({p.relative_to(base).as_posix()})"
                       for m in ADOPT_ROUTE.finditer(read_text(p))][:30 - len(routes)]
    purpose = readme_purpose(base)
    out += ["  - What the repo holds (MECHANISMS.md §Spine resolution order) - say these to the user before any draft:",
            f"      docs: {', '.join(found + docs) or 'none'}" + (f" · README says: {purpose[:200]}" if purpose else ""),
            f"      package metadata: {', '.join(meta) or 'none'} · entry points: {', '.join(entries) or 'none found'}",
            f"      routes: {'; '.join(routes[:12]) or 'none found'}{' ...' if len(routes) > 12 else ''}",
            f"      tests: {', '.join(tests) or 'none found'} · CI: {', '.join(ci) or 'none found - a finding'}"]
    tpl = tool_file("templates", "PRODUCT.md")
    out += [f"  - The draft is the template ({tpl.as_posix() if tpl else 'templates/PRODUCT.md'}) filled from these "
            "files ONLY, in a scratch file outside the repo; its first line the provenance: `_Adopted <YYYY-MM-DD> "
            "from: <file>, <file>_`. Every inferred line ends `(inferred — confirm)` with its file. North star, "
            "riskiest assumption, business model and Non-goals stay empty unless a file states them.",
            "  - Two rounds, each ONE message: round 1 = the whole draft, every inferred line with its file, keep / "
            "correct / drop per line, plus the owner-only questions (who it's for and why, the north star, the "
            "riskiest assumption, the business model, what you will never build) - \"don't know\" leaves it empty; "
            "round 2 = the corrected draft, any README-vs-code clash (Step 3c), and two options: \"Looks good - save "
            "(Recommended)\" / \"Change something\".",
            "  - Then ONE call: `status.py set adopt filled --section-from <draft> --product \"<name>\" --commit "
            "\"<one line>\"` (`--dry-run` lists every gap, writes nothing; no `--commit` on a no). It writes PRODUCT.md "
            "(or only its empty sections), makes STATUS.md, records each confirmed section `filled` with \"adopted "
            "<date>\" (a verification phase stays empty: its verdict is its own run), and refuses, every problem in "
            "one list: a line still tagged `(inferred — confirm)` · no provenance line, or one naming a file that does "
            "not exist · a filled section of an existing PRODUCT.md changed.",
            "  - Must NOT: write code, change the repo's files, guess a north star, an assumption, a business model "
            "or a Non-goal, or write anything before round 2's yes."]
    out.append(support_close(st, "adopt") if st is not None else
               "Close - after the report, never before; its last line is the `Open a NEW conversation` line the "
               "record call prints, word for word.")
    return "\n".join(out)


def adopt_record(path: Path, a, today: str) -> str:
    """`set adopt filled --section-from <draft>`: PRODUCT.md (or its empty sections), STATUS.md, one row per
    confirmed section - one call, every problem in one refusal (P20, P25)."""
    base = path.resolve().parent
    prod, src = base / "PRODUCT.md", Path(a.section_from or "")
    if a.state != "filled" or not src.is_file():
        raise Refused("/adopt records with `set adopt filled --section-from <draft>` (the draft file must exist)")
    draft = src.read_text(encoding="utf-8")
    gaps = []
    tagged = [l.strip()[:90] for l in draft.splitlines() if ADOPT_TAG.search(l)]
    if tagged:
        gaps.append(f"{len(tagged)} line(s) still tagged `(inferred — confirm)` - the owner keeps (drop the tag), "
                    f"corrects or drops each, first: {tagged[0]!r}")
    prov = ADOPT_PROVENANCE.search(draft)
    if not prov:
        gaps.append("no provenance line - `_Adopted <YYYY-MM-DD> from: <file>, <file>_` names what the draft was drawn "
                    "from")
    else:
        named = [n.strip(" `_").rstrip(".") for n in re.split(r",|·|;", prov.group(2)) if n.strip(" `_.")]
        gaps += [f"the provenance names {n}, which is not in the repo" for n in named if not (base / n).exists()]
    new = product_sections(draft)
    if prod.is_file():
        old = product_sections(prod.read_text(encoding="utf-8"))
        gaps += [f"#{k} is already filled in PRODUCT.md - adopt fills empty sections only; leave it as written"
                 for k, v in old.items() if has_content(v) and k in new and
                 " ".join(new[k].split()) != " ".join(v.split())]
    if not prod.is_file() and not (a.product or path.is_file()):
        gaps.append("no STATUS.md yet: add --product \"<name>\"")
    if gaps and getattr(a, "dry_run", False):
        raise DryRun(f"{len(gaps)} gap(s) the record call would refuse:\n" + "\n".join(f"  - {g}" for g in gaps))
    if gaps:
        raise Refused(f"#adopt: {len(gaps)} problem(s), every one at once:\n  - " + "\n  - ".join(gaps))
    filled = [ph for ph, sec in PHASE_SECTION.items() if has_content(new.get(sec, "")) and ph not in ADOPT_SKIP_PHASES]
    if getattr(a, "dry_run", False):
        raise DryRun(f"no gap: the record call writes PRODUCT.md and records {', '.join('#' + p for p in filled)}")
    with Lock(base):
        if prod.is_file():
            text = prod.read_text(encoding="utf-8")
            old = product_sections(text)
            for k, v in new.items():
                if k in old and not has_content(old[k]) and has_content(v):
                    text = replace_section(text, k, v)
        else:
            text = draft
        prod.write_text(text, encoding="utf-8", newline="")
        st = Status.load(path) if path.is_file() else Status.new(a.product, today)
        st.base, st.today = base, today
        done = []
        for ph in filled:
            r = st.phase(ph)
            if r[1] in ("empty", "declined"):
                r[1:6] = ["filled", today, "", "", f"adopted {today}"]
                r[6] = playbook_version()
                done.append(ph)
        errs, _ = problems(st, today, None)
        if errs:
            raise Refused("the result would be invalid: " + "; ".join(errs))
        st.save(path)
    msg = [f"adopted: PRODUCT.md written; recorded {', '.join('#' + p for p in done) or 'nothing new'} filled "
           f"(adopted {today})"]
    saved = save_commit(base, a.commit) if a.commit else None
    msg += [saved] if saved else []
    nxt, why = adopt_next(product_sections(text))
    card = "\n".join(l for l in handoff_card(st).splitlines() if not l.startswith(("Open a NEW", "Cost:")))
    msg += [close_steps_text("adopt", saved), *([card] if card.strip() else []),
            f"Open a NEW conversation and type: {skill_command(nxt)} - {why}; nothing is lost: it is all in "
            f"PRODUCT.md, STATUS.md and git."]
    return "\n".join(msg)


def adopt_next(secs: dict[str, str]) -> tuple[str, str]:
    """/adopt Step 4's routing, one source: the earliest phase whose own start would not send the user back (case
    file: Sent to a gate that sends you back) - an adopted #Vision rarely holds the why, a repo rarely its Non-goals."""
    vis, scope = scope_fields(secs.get("Vision", "")), scope_fields(secs.get("Scope", ""))
    has = lambda fields, rx: any(re.search(rx, k, re.I) and " ".join(v).strip() for k, v in fields.items())  # noqa
    if not all(has(vis, rx) for rx in (r"^vision\b", r"^who\b", r"value prop")):
        return "vision", "#Vision has no vision sentence, audience or value proposition: code shows what was built, never why or for whom"
    if not (has(scope, r"core feature") and has(scope, r"non[- ]goal")):
        return "scope", "#Scope has no core feature or no Non-goals: the anti-creep list a half-built project lacks"
    return "playbook", "the spine exists: /playbook now orients properly"


SUPPORT_STARTS["adopt"] = adopt_start_text


# /frontend-audit and /new-component: the engine path, the token stylesheet and what to audit are resolved here, so a
# run never searches the plugin cache (a logged build ran a 1.9.0 engine that way) or reads the stylesheet whole.
UI_SUFFIXES = {".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".htm", ".jinja", ".j2", ".css", ".scss"}
CSS_PATH = re.compile(r"`?((?:[\w.-]+/)*[\w.-]+\.(?:css|scss))`?")
CSS_TOKEN = re.compile(r"(?m)^\s*(--[\w-]+)\s*:")


def audit_engine() -> str:
    f = tool_file("commands", "frontend-audit", "audit.py") or tool_file("frontend-audit", "audit.py")
    return f.as_posix() if f else "(not found beside this status.py - stop and say so; never search for it)"


def token_sheets(base: Path) -> list[str]:
    """The stylesheets DESIGN.md names that exist: the app's tokens live there, not in the spec."""
    design = base / "DESIGN.md"
    text = design.read_text(encoding="utf-8", errors="replace") if design.is_file() else ""
    return list(dict.fromkeys(p for p in CSS_PATH.findall(text) if (base / p).is_file()))


def ui_changed(base: Path) -> list[str]:
    """UI files changed against HEAD (tracked or new): a change audits with --baseline HEAD."""
    names = git(base, "diff", "--name-only", "HEAD").splitlines() + \
        git(base, "ls-files", "--others", "--exclude-standard").splitlines()
    return [n for n in dict.fromkeys(names) if Path(n).suffix.lower() in UI_SUFFIXES and (base / n).is_file()]


def frontend_audit_start_text(path: Path, today: str) -> str:
    base, st = path.resolve().parent, support_status(path)
    ui = design_ui_files(base, 40)
    dirs = sorted({u.split("/")[0] if "/" in u else u for u in ui})
    design = "DESIGN.md" if (base / "DESIGN.md").is_file() else None
    changed = ui_changed(base) if git(base, "rev-parse", "HEAD") else []
    out = ["/frontend-audit start (the engine and what to audit are resolved here - never search for audit.py):",
           f"  - Engine (the installed one): {audit_engine()}",
           f"  - DESIGN.md: {'found - pass it in the same run, so the tokens resolve' if design else 'none - say so; contrast is checked from the stylesheets alone; recommend /design-system'}",
           f"  - UI in the project: {', '.join(dirs) or 'none found - nothing to audit; say so and stop'}"]
    targets = " ".join(([design] if design else []) + dirs)
    if changed:
        out.append(f"  - {len(changed)} UI file(s) changed against HEAD ({', '.join(changed[:6])}): a change to "
                   f"existing files - only what it ADDS counts: add `--baseline HEAD`")
    out += [f"  - Run, one call: python \"{audit_engine()}\" {'--baseline HEAD ' if changed else ''}{targets}",
            AUDIT_ARGS,
            "  - Repeat its first line (the engine version) and its `engine copy:` line to the user; an OLDER copy "
            "means hooks and CI pass on checks this run fails.",
            "  - Report: every ERROR (the floor - fix or name it), the WARNs triaged, and the list the audit prints "
            "of what it cannot check (keyboard, focus, screen reader): a floor, never an accessibility pass.",
            "  - Must NOT: change DESIGN.md or a design decision, judge taste or archetype fit, or call 0 errors an "
            "accessibility pass.",
            support_close(st, "frontend-audit")]
    return "\n".join(out)


def new_component_start_text(path: Path, today: str) -> str:
    base, st = path.resolve().parent, support_status(path)
    out = ["/new-component start (the token vocabulary and the pending components are resolved here):"]
    sheets = token_sheets(base)
    if not (base / "DESIGN.md").is_file():
        out.append("  - No DESIGN.md: say so, recommend /design-system, and use the shadcn default names (Step 0b) - "
                   "never a private vocabulary")
    elif not sheets:
        out.append("  - DESIGN.md names no stylesheet that exists: the tokens were never emitted - say so and stop "
                   "(that is /design-system's output, not something to improvise here)")
    for s in sheets[:2]:
        names = list(dict.fromkeys(CSS_TOKEN.findall(read_text(base / s))))
        out.append(f"  - Tokens defined in {s} ({len(names)}) - use these names, never one outside the list: "
                   + " ".join(names[:80]) + (" ..." if len(names) > 80 else ""))
    struct = base / "STRUCTURE.md"
    homes = [l.strip()[:160] for l in read_text(struct).splitlines() if re.search(r"(?i)component", l)][:4] \
        if struct.is_file() else []
    out.append("  - Where components live (STRUCTURE.md): " + (" | ".join(homes) if homes else
                                                               "STRUCTURE.md names no place - ask the user"))
    issues = sorted((base / "docs" / "issues").glob("*.md")) if (base / "docs" / "issues").is_dir() else []
    menu, broken = [], []
    for f in issues:
        tgt = ticket_sections(read_text(f)).get("Target Files")
        if tgt is None:
            broken.append(f.name)
            continue
        for p in TARGET.findall(tgt):
            if Path(p).suffix.lower() in {".tsx", ".jsx", ".vue", ".svelte"}:
                menu.append((f.stem.split("_")[0], p, (base / p).is_file()))
    if broken:
        out.append(f"  - Tickets with no `Target Files` section (say so - never an empty menu): {', '.join(broken[:5])}")
    pending = [m for m in menu if not m[2]]
    if pending:
        first = re.match(r"M\d+", pending[0][0])
        ms = first.group(0) if first else ""
        out.append(f"  - Components for {ms or 'the tickets'} (invoked bare: offer these, ONE is built per run):")
        out += [f"      [{'x' if done else ' '}] {p} ({tid}){'' if done else ' - pending'}"
                for tid, p, done in menu if not ms or tid.startswith(ms)][:15]
    elif not issues:
        out.append("  - No docs/issues/: say so in one line and build from the user's description")
    out += [f"  - Prove it, one call, the stylesheet beside the component: python \"{audit_engine()}\" "
            f"{sheets[0] if sheets else '<the token stylesheet>'} <the new component> - 0 errors, and no "
            f"`tokens-defined` error",
            AUDIT_ARGS,
            "  - Must NOT: build more than one component, invent a token or a components folder, edit DESIGN.md or "
            "the stylesheet, or suppress hydration warnings across every input.",
            support_close(st, "new-component")]
    return "\n".join(out)


PHASE_RULES["new-component"] = {
    "PRINCIPLES.md": ["Architecture & quality bar", "Communication"],
    "MECHANISMS.md": ["Spine resolution", "Step 3c"],
}
SUPPORT_STARTS["frontend-audit"] = frontend_audit_start_text
SUPPORT_STARTS["new-component"] = new_component_start_text
START_HOLDS["frontend-audit"] = "the engine, what to audit, the one command, the close"
START_HOLDS["new-component"] = "the tokens, where components live, the pending components,\n    the proof, the close"
START_HOLDS["adopt"] = "the repo survey, the draft's shape, the two rounds, the\n    record call, the rules"
START_HOLDS["drift-check"] = "the spine tier, the lines drift is judged against, the\n    evidence lines, the rules, the close"


# ---- /architect: P1 + P2 + P4 + P20 + P37 -----------------------------------------------------------------------
# Its Step 0 read PRINCIPLES.md, MECHANISMS.md and PRODUCT.md whole (~55 KB on a logged test run's filled project, then
# AGENT.md §Architect and decisions.md) and re-sent them on every call, and asked its questions one per message.
# Every exit criterion was a sentence: a logged Gemini run invented a provenance value, priced 2024 models with no
# search, called links VERIFIED at 100%, copied a receipt and wrote LaTeX. The start prints what the stack is chosen
# against and the record's shape; `set architect filled` refuses the countable gaps, every problem once, on its own
# close only (never phase_check: a project filled under older rules is not blocked later).
QUESTION_PHASES = QUESTION_PHASES + ("architect",)  # its start carries the habits, not the 3 KB close checklist
PHASE_RULES["architect"] = {
    "PRINCIPLES.md": ["Architecture & quality bar", "Communication"],
    "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status"],
}
PHASE_CLOSE_RULES["architect"] = {
    "PRINCIPLES.md": ["The exit-criteria gate"],
    "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"],
}
CLOSE_STEPS["architect"] = (
    "every number against #Vision and the owner's answers: a cost per use above #Vision's cap, a monthly total above "
    "answer 2's money",
    "#Scope and #Plan - a part built for a Deferred item or a non-goal (gold-plating), paid hosting before #Plan's "
    "paid-infra trigger, a budget against #Vision's business model",
    "the fields, every row's provenance, the dev-tooling slots, the runtime targets, the adapters, the concern areas, "
    "the model's release date, the ADR files and docs/architecture.md")
START_HOLDS["architect"] = ("the #Vision, #Scope and #Plan lines the stack is chosen\n    against, the #Architecture "
                            "labels, this phase's rules, the close")
# PRINCIPLES.md §Production safeguards, the bullets this phase decides, word for word (placeholders, test data,
# measuring and rollout are /foundation's, /test's and /ship's): ~1.5 KB of the section's 3.2 KB
ARCH_SAFEGUARDS = ("Security baseline", "AI-specific security", "Observability & audit", "Fail-safe errors",
                   "Resilience by design", "Perf & cost budgets", "AI architecture")
ARCH_DOC = "docs/architecture.md"
# templates/architecture.md (owner 2026-10-05): one standard document for every agent and product kind - these `##`
# sections, in this order. 4 agents filled it with the same 17 headings; 0 of the 9 earlier documents shared a shape.
ARCH_DOC_SECTIONS = (
    ("Overview", r"overview"), ("What drives the design", r"what drives the design"),
    ("Rules the code must keep", r"rules the code must keep"), ("How it works, step by step", r"how it works"),
    ("Building blocks", r"building blocks"), ("Data", r"data\b"), ("Conventions and terms", r"conventions"),
    ("Decisions", r"decisions"), ("Security and privacy", r"security"), ("AI part", r"ai part"),
    ("Running it", r"running it"), ("Mapping to the plan", r"mapping to the plan"),
    ("Risks and open questions", r"risks"), ("Appendix A — Owner's answers", r"appendix a\b"),
    ("Appendix B — Search list", r"appendix b\b"), ("Appendix C — Options considered", r"appendix c\b"),
    ("Appendix D — Sources and what is not verified", r"appendix d\b"))
# Shorthand: a slash-joined list of 3+ words ("edit/reject/approve") outside code, links and the appendix. A logged
# fill that met the size target this way had 144; the readable fills and the 9 earlier documents had 0-5.
ARCH_SHORTHAND = re.compile(r"(?<![\w/.])[A-Za-z][\w-]*(?:/[A-Za-z][\w-]*){2,}(?![\w/])")
ARCH_SHORTHAND_MAX = 10
# P46: the long document is the run's last write, saved in the same call. A logged Claude run read the 27K-char template
# at call 6 and wrote the 15K-token document at call 8 of 14 - both re-sent on every later call, and the save's refusal
# (a model date, two rows) came after the document, costing 4 more calls with it in context. The dry-run now runs
# before the document; these are the document's checks, printed at that moment (they left the start).
def arch_docs_pending(agent: bool) -> str:
    """What `set architect filled --dry-run` prints while the ADR files and docs/architecture.md are unwritten: how to
    write them and what the save checks in them (they left the start: printed at the moment they are needed)."""
    return "\n".join([
        f"\n  The ADR files and {ARCH_DOC} are not written yet, so their checks wait for the save. Next, ONE message: "
        f"write them, then - in that same message, after them - `set architect filled --section-from <file> --commit "
        f"\"<one line>\"` (no `--commit` on a no). Never re-read what you wrote: `set` checks it.",
        "  - ADR files: `docs/adr/NNNN-<slug>.md`, one per load-bearing choice"
        + ("; the framework, the action tiers and staged autonomy + kill switch each get one" if agent else "")
        + ". The shape (the template - do not open it): `# ADR-NNNN — <the decision, as a rule>` · `- **Status:** "
        "accepted` · `- **Date:**` · `- **Provenance:**` · `## Decision` (1-2 sentences) · `## Why` (the constraint "
        "that decided it) · `## What was rejected, and why it lost` (one line each) · `## Consequences` (what breaks "
        "if it is ignored) · `## Superseding` (a reversal sets Status: superseded by ADR-NNNN; never delete the file).",
        f"  - {ARCH_DOC}: the template you read, filled - every `##` section in its order, each `<...>` filled, every "
        f"comment deleted (the comments are its rules: what each section holds, its size, which kind of product adds "
        f"which lines). Round 2's table as approved becomes the `### D<n>.` blocks of `## Decisions`; round 1's "
        f"answers go word for word in Appendix A, the searches in Appendix B"
        + (", the framework table under `### Framework options` in Appendix C" if agent else "")
        + ". Full sentences, no slash-joined word lists.",
        "  - The save refuses: fewer than 2 ADR files or one with no Status"
        + (" · no ADR for the framework, the tiers or the autonomy" if agent else "")
        + " · a template section missing or out of order · no ```mermaid diagram in Overview or How it works, step "
        f"by step · no R# rule with MUST or NEVER · a comment or `<...>` left · more than {ARCH_SHORTHAND_MAX} "
        "slash-joined word lists · no Owner's answers (Appendix A) · no Search list (Appendix B: one line per search, "
        "the page you opened - never a homepage)"
        + (" · a framework table under 3 options, none beyond AGENT.md's examples, or no registry link" if agent
           else "") + "."])


# templates/structure.md (owner 2026-10-05): the checker's six sections plus the parts the plain runs did best.
STRUCT_DOC_SECTIONS = (
    ("In short", r"in short"), ("Modules", r"modules$"), ("Entry points", r"entry points"),
    ("Dependency rules", r"dependency rules"), ("Inside a module", r"inside a module"),
    ("Where does a new file go?", r"where does a new file go"), ("Tests and fixtures", r"tests and fixtures"),
    ("Root files", r"root files"), ("Where decisions live", r"where decisions live"), ("Hub files", r"hub files"),
    ("Naming and placement rules", r"naming and placement"), ("Checks you run", r"checks you run"),
    ("Not here yet", r"not here yet"), ("Changes", r"changes"))


def doc_sections(doc: str, sections: tuple) -> dict[str, re.Match]:
    """Each template section's `##` heading in a document, the first match (a numbered heading counts)."""
    heads = list(re.finditer(r"(?m)^##\s+(?:\d+[.)]\s*)?(.+?)\s*$", doc))
    out: dict[str, re.Match] = {}
    for name, rx in sections:
        for h in heads:
            if re.match(rx, h.group(1), re.I):
                out[name] = h
                break
    return out


def doc_order_gaps(doc: str, sections: tuple, path: str, template: str) -> list[str]:
    """Missing and out-of-order template sections, template comments left, and shorthand - one message each."""
    gaps: list[str] = []
    found = doc_sections(doc, sections)
    missing = [n for n, _ in sections if n not in found]
    if missing:
        gaps.append(f"{path} is missing section(s) of the template: {', '.join(missing)} - every `##` section of "
                    f"{template}, in its order; one that does not apply holds `Not applicable: <reason>`")
    order = [n for n, _ in sections if n in found]
    late = [f"{a} after {b}" for a, b in zip(order[1:], order) if found[a].start() < found[b].start()]
    if late:
        gaps.append(f"{path} sections out of the template's order: {'; '.join(late[:3])}")
    if "<!--" in doc or re.search(r"<3-5 sentences\.>|<product name>|<the tree>", doc):
        gaps.append(f"{path} still holds template comments or placeholders - delete every `<!-- -->` comment and "
                    f"fill each `<...>`")
    reader = re.sub(r"(?s)```.*?```", "", doc)
    reader = re.sub(r"https?://\S+|`[^`\n]*`|\]\([^)]*\)", "", reader)
    short = ARCH_SHORTHAND.findall(reader)
    if len(short) > ARCH_SHORTHAND_MAX:
        gaps.append(f"{path} is written in shorthand: {len(short)} slash-joined word lists (at most "
                    f"{ARCH_SHORTHAND_MAX}), e.g. {', '.join(short[:4])} - full sentences a newcomer can read aloud")
    return gaps


def struct_template_path() -> str:
    f = tool_file("templates", "structure.md")
    return f"`{f.as_posix()}`" if f else "the playbook's `templates/structure.md`"


def arch_doc_sections(doc: str) -> dict[str, re.Match]:
    """Each template section's `##` heading in the document, the first match (a numbered heading counts)."""
    heads = list(re.finditer(r"(?m)^##\s+(?:\d+[.)]\s*)?(.+?)\s*$", doc))
    out: dict[str, re.Match] = {}
    for name, rx in ARCH_DOC_SECTIONS:
        for h in heads:
            if re.match(rx, h.group(1), re.I):
                out[name] = h
                break
    return out


def arch_doc_body(doc: str, name: str) -> str:
    """The text under one template section, to the next `##` heading."""
    h = arch_doc_sections(doc).get(name)
    if not h:
        return ""
    nxt = re.search(r"(?m)^##\s", doc[h.end():])
    return doc[h.end():h.end() + nxt.start()] if nxt else doc[h.end():]


def arch_doc_shape_gaps(doc: str) -> list[str]:
    """docs/architecture.md against templates/architecture.md: every section in order, the two diagrams, the rules,
    no template comment left, no shorthand. Separate from architect_gaps so a logged document replays on its own."""
    gaps: list[str] = []
    found = arch_doc_sections(doc)
    missing = [n for n, _ in ARCH_DOC_SECTIONS if n not in found]
    if missing:
        gaps.append(f"{ARCH_DOC} is missing section(s) of the template: {', '.join(missing)} - every `##` section of "
                    f"templates/architecture.md, in its order; one that does not apply holds `Not applicable: <reason>`")
    order = [n for n, _ in ARCH_DOC_SECTIONS if n in found]
    late = [f"{a} after {b}" for a, b in zip(order[1:], order) if found[a].start() < found[b].start()]
    if late:
        gaps.append(f"{ARCH_DOC} sections out of the template's order: {'; '.join(late[:3])} - the reader's part "
                    f"(Overview to Risks and open questions) first, then the appendices A-D")
    for name, what in (("Overview", "the context diagram"), ("How it works, step by step", "the step-by-step flow")):
        part = arch_doc_body(doc, name)
        if name in found and not re.search(r"(?m)^\s*```\s*mermaid", part) and "not applicable" not in part.lower():
            gaps.append(f"{ARCH_DOC} `## {name}` has no ```mermaid diagram - {what}")
    rules = arch_doc_body(doc, "Rules the code must keep")
    if "Rules the code must keep" in found and "not applicable" not in rules.lower() and not re.search(
            r"(?m)\bR\d+\b.*\b(?:MUST|NEVER)\b", rules):
        gaps.append(f"{ARCH_DOC} `## Rules the code must keep` has no R# rule written with MUST or NEVER")
    if "<!--" in doc or re.search(r"<3-5 sentences\.>|<product name>|\| <n> \|", doc):
        gaps.append(f"{ARCH_DOC} still holds template comments or placeholders - delete every `<!-- -->` comment and "
                    f"fill each `<...>`")
    reader = doc[:found["Appendix A — Owner's answers"].start()] if "Appendix A — Owner's answers" in found else doc
    reader = re.sub(r"(?s)```.*?```", "", reader)
    reader = re.sub(r"https?://\S+|`[^`\n]*`|\]\([^)]*\)", "", reader)
    short = ARCH_SHORTHAND.findall(reader)
    if len(short) > ARCH_SHORTHAND_MAX:
        gaps.append(f"{ARCH_DOC} is written in shorthand: {len(short)} slash-joined word lists (at most "
                    f"{ARCH_SHORTHAND_MAX}), e.g. {', '.join(short[:4])} - full sentences a newcomer can read aloud")
    return gaps
ARCH_FIELDS = (("Stack + tools", r"^stack"), ("Data custody", r"^data custody"),
               ("Runtime target per deployable unit", r"^runtime"), ("Identity custody", r"^identity"),
               ("Dev tooling", r"^dev tooling"), ("Key decisions / ADRs", r"^key decisions|^adrs?\b"),
               ("Externals behind adapters", r"^externals"),
               ("Resilience · perf/cost budget · migrations", r"^resilience"))
ARCH_AI = ("(AI) prompt-versioning · eval harness · tracing", r"^\(ai\)")
ARCH_AGENT = ("(Agent) the ten AGENT.md rows", r"^\(agent\)")
ARCH_PROVENANCE_FIELDS = (r"^stack", r"^data custody", r"^runtime", r"^identity")
ARCH_ROW = re.compile(r"^(?:[-*+]|\d+[.)])\s+")
ARCH_RULE_ROW = re.compile(r"^\|?[-: |]+\|?$")
MONEY = r"(?:[€$£]\s?\d[\d,.]*|\d[\d,.]*\s?(?:€|eur(?:os?)?\b|usd\b|dollars?\b|£))"
ARCH_CONSTRAINTS = (
    ("who builds and runs it, hours a week (answer 1)", r"\d+\s*(?:h|hrs?|hours?)\b|full[- ]time|part[- ]time"),
    ("money a month for hosting and AI (answer 2)",
     MONEY + r"[^\n]{0,40}?(?:/\s?mo(?:nth)?\b|\ba month\b|\bper month\b|\bmonthly\b)|free tiers? only|no budget"),
    ("the infrastructure they will run - managed only · some · self-host (answer 3)",
     r"managed|self[- ]?host|own servers?|serverless"),
    ("the lock-in they accept (answer 4)", r"lock[- ]?in|portab|any vendor|exit cost"))
ARCH_TOOLING = (("hook runner", r"pre-commit|lefthook|husky|\bhooks?\b"),
                ("secret scanner", r"gitleaks|trufflehog|detect-secrets|ggshield|secret"),
                ("task runner", r"\bjust(?:file)?\b|\bmake(?:file)?\b|npm scripts|\bpnpm\b|\bnox\b|\bpoe\b|"
                                r"\binvoke\b|\bmise\b|taskfile|task runner"),
                ("formatter/linter", r"ruff|black|flake8|eslint|biome|prettier|rubocop|gofmt|golangci|clippy|"
                                     r"rustfmt|format|lint"),
                ("dependency manifest", r"pyproject|package\.json|requirements|cargo\.toml|go\.mod|gemfile|pom\.xml|"
                                        r"build\.gradle|composer\.json|manifest"))
# what a runtime target is: a category /deploy can execute, not only a brand (decisions.md §Custody)
ARCH_RUNTIME = re.compile(r"(?i)container|docker|paas|\bvps\b|virtual (?:private )?server|\bvm\b|machine|on[- ]prem|"
                          r"desktop|static|\bcdn\b|serverless|functions?\b|edge|kubernetes|\bk8s\b|\bci\b|cron")
# an interface name, plain or backticked: OrderSource, and acronym-led LLMProvider / AIClient (a logged run was
# refused for a plain LLMProvider, while /structure refuses backticks around a name that is not a path)
ARCH_INTERFACE = re.compile(r"`[A-Za-z_]\w*`|\b[A-Z]+[a-z0-9]*(?:[A-Z][a-z0-9]+)+\b|(?i:adapter|interface|\bport\b)")
ARCH_RESILIENCE = re.compile(r"(?i)timeout|retr(?:y|ies)|fallback|circuit|breaker|fails? ?(?:closed|safe|open)|"
                             r"degrad|backoff")
ARCH_AREAS = (("resilience", r"resilien|timeout|retr(?:y|ies)|fallback|circuit"),
              ("the perf/cost budget", r"budget|latency|per (?:answer|request|call|use|run|operation)"),
              ("security / no secret in code", r"secret|\.env\b"),
              ("observability", r"observab|logging|\blogs?\b|tracing|metrics"))
ARCH_AI_AREAS = (("prompt-versioning", r"prompt[- ]?version|versioned prompt|prompts?\b[^\n]{0,40}\bversion"),
                 ("the eval harness", r"\bevals?\b|evaluation"), ("LLM tracing", r"\btrac(?:e|es|ing)\b"))
ARCH_RUNTIME_CONFIG = (("max_tokens", r"max[_ ]?(?:output[_ ])?tokens|output (?:cap|limit)"), ("a timeout", r"timeout"),
                       ("thinking / reasoning effort", r"thinking|reasoning|effort"),
                       ("retry and refusal fallback", r"retr(?:y|ies)|fallback"), ("prompt caching", r"cach"))
# N5: the cost per use shows its working - a token count and a price per million tokens (two logged runs saved
# "≈ €0.01 per answer" with neither)
ARCH_TOKENS = re.compile(r"(?i)\d[\d,.]*\s*[km]?\s*(?:input |output |in |out |prompt |completion )?tok(?:en)?s?\b")
ARCH_PRICE = re.compile(r"(?i)" + MONEY + r"\s*(?:/|per)\s*(?:1\s?m\b|m\b|mtok|million|1,000,000|1\s?k\b|1,000\b|"
                        r"thousand)")
ARCH_PER_USE = re.compile(r"(?i)" + MONEY + r"[^\n]{0,60}?(?:\bper\s+|/\s?)(?:answer|use|call|run|request|draft|"
                          r"question|conversation|operation|reply|message|scan|query|task|ticket|document|item)\b")
# AGENT.md §Architect's ten rows, found by loose words (a model may rename a row, not drop it)
ARCH_AGENT_ROWS = (("1 framework", r"framework|tool loop|\bsdk\b"), ("2 action tiers", r"\btiers?\b"),
                   ("3 caps per conversation", r"\bcaps?\b|max(?:imum)? steps"),
                   ("4 untrusted input and tool scope", r"untrusted|injection"),
                   ("5 hand-off to a person", r"hand[- ]?off|to a person|human"),
                   ("6 staged autonomy and kill switch", r"autonom|kill[- ]switch|stop switch|shadow"),
                   ("7 action audit log", r"\baudit"), ("8 memory", r"memory|persist"),
                   ("9 agent evals", r"\bevals?\b|golden|known-answer"), ("10 AI disclosure", r"disclos|ai[- ]drafted"))
ARCH_AGENT_ADRS = (("the framework (row 1)", r"framework|tool loop"), ("the action tiers (row 2)", r"\btiers?\b"),
                   ("staged autonomy and the kill switch (row 6)", r"autonom|kill[- ]switch|stop switch"))
# AGENT.md §Architect row 1's example frameworks (test_status checks each is still named there): the table needs one
# the open search found beyond them (F1: two logged runs only re-listed these)
AGENT_EXAMPLES = ("langgraph", "microsoft agent framework", "crewai", "openai agents sdk", "claude agent sdk",
                  "google adk", "strands", "pydantic ai", "mastra", "vercel ai sdk", "llamaindex")
# A1: a person logs in with the company's login (#Scope) - identity custody is a design, never N/A (a logged run
# identified the user by a header the frontend set to a constant)
LOGIN = re.compile(r"(?i)company(?:'s)? (?:login|account|identity)|single sign[- ]on|\bsso\b|\boidc\b|\bsaml\b|"
                   r"\bentra\b|\bokta\b|corporate login|(?:log|sign)[- ]?in with")
REGISTRY = re.compile(r"(?i)pypi\.org|npmjs\.com|crates\.io|pkg\.go\.dev|rubygems\.org|nuget\.org|packagist\.org")


def principle_bullets(section: str, labels: tuple[str, ...]) -> str:
    """The `- **Label**` bullets of a PRINCIPLES.md section named in `labels`, word for word, continuation lines kept."""
    out, keep = [], False
    for line in print_sections(rule_file("PRINCIPLES.md"), [section]).splitlines()[1:]:
        m = re.match(r"^- \*\*(.+?)\*\*", line)
        if m:
            keep = m.group(1).startswith(labels)
        elif not line.startswith((" ", "\t")):
            keep = False
        if keep:
            out.append(line)
    return "\n".join(out)


def arch_rows(lines: list[str]) -> list[str]:
    """A field's decision rows: each sub-bullet with its continuation lines, or each table row (its header and |---|
    rows skipped, P8). The inline value is a row only when nothing is listed under it - otherwise it is a summary."""
    rows: list[str] = []
    inline = ""
    for n, line in enumerate(lines):
        s = line.strip()
        if not s or s.startswith(("_", "<!--")):
            continue
        if s.startswith("|"):
            nxt = next((x.strip() for x in lines[n + 1:] if x.strip()), "")
            if not (ARCH_RULE_ROW.match(s) or ARCH_RULE_ROW.match(nxt)):
                rows.append(s)
        elif ARCH_ROW.match(s):
            rows.append(ARCH_ROW.sub("", s))
        elif rows:
            rows[-1] += " " + s
        else:
            inline = (inline + " " + s).strip()
    return rows or ([inline] if inline else [])


def arch_framework_rows(lines: list[str]) -> list[str]:
    """The first cell of each data row of the table(s) under a heading naming the framework (docs/architecture.md)."""
    out, inside = [], False
    for n, line in enumerate(lines):
        if line.startswith("#"):
            inside = bool(re.search(r"(?i)framework", line))
        elif inside and line.strip().startswith("|"):
            nxt = lines[n + 1].strip() if n + 1 < len(lines) else ""
            if not (ARCH_RULE_ROW.match(line.strip()) or ARCH_RULE_ROW.match(nxt)):
                cell = re.sub(r"[*_`\[\]]|\(http\S*\)", "", line.strip().strip("|").split("|")[0])
                out.append(" ".join(cell.replace("-", " ").lower().split()))  # "Pydantic-AI" = "pydantic ai"
    return out


def architect_warnings(base: Path, st: "Status") -> list[str]:
    """N5, a WARNING (owner 2026-10-04): a cost per use with no working - a token count and a price per 1M. And the
    document's body size against the template's 20,000-32,000 bytes (a warning: a small product may be shorter)."""
    prod, doc_p = base / "PRODUCT.md", base / ARCH_DOC
    warns: list[str] = []
    doc = doc_p.read_text(encoding="utf-8") if doc_p.is_file() else ""
    found = arch_doc_sections(doc)
    if "Overview" in found and "Appendix A — Owner's answers" in found:
        size = len(doc[found["Overview"].start():found["Appendix A — Owner's answers"].start()].encode("utf-8"))
        if size > 36000:
            warns.append(f"{ARCH_DOC} body is {size:,} bytes (template: 20,000-32,000) - merge failure rows with the "
                         f"same handling and cut repetition, never rules, Rejected lines or shorthand")
    return warns + architect_cost_warnings(base, st)


def architect_cost_warnings(base: Path, st: "Status") -> list[str]:
    """N5: the cost per use with no working."""
    prod, doc_p = base / "PRODUCT.md", base / ARCH_DOC
    if st.header.get("AI product") != "yes" or not prod.is_file():
        return []
    fields = plan_field_lines(re.sub(r"<!--.*?-->", "", product_sections(prod.read_text(encoding="utf-8")).get(
        "Architecture", ""), flags=re.S))
    body = "\n".join(l for v in fields.values() for l in v)
    work = body + "\n" + (doc_p.read_text(encoding="utf-8") if doc_p.is_file() else "")
    if ARCH_PER_USE.search(body) and not (ARCH_TOKENS.search(work) and ARCH_PRICE.search(work)):
        return ["the cost per use shows no working - `(<input tokens> × <price per 1M> + <output tokens> × <price per "
                "1M>) / 1,000,000 ≈ <amount> per <use>`, the prices from this run's pricing page (N5)"]
    return []


def architect_gaps(base: Path, st: "Status", doc_pending: bool = False) -> list[str]:
    """What `set architect filled` needs, every problem named once in one list (P20). `doc_pending`: a --dry-run
    before docs/architecture.md is written (P46: the long document is the last write) - its checks wait for the save."""
    prod, doc_p = base / "PRODUCT.md", base / ARCH_DOC
    secs = product_sections(prod.read_text(encoding="utf-8")) if prod.is_file() else {}
    clean = {k: re.sub(r"<!--.*?-->", "", v, flags=re.S) for k, v in secs.items()}
    fields = plan_field_lines(clean.get("Architecture", ""))
    body = "\n".join(l for v in fields.values() for l in v)  # the values only: every label names its own area
    ai, agent = st.header.get("AI product") == "yes", st.header.get("Agent") == "yes"
    gaps: list[str] = []

    def lines_of(rx: str) -> list[str]:
        return [l for k, v in fields.items() if re.search(rx, k, re.I) for l in v]

    def listed(rows: list[str], n: int = 4) -> str:
        return " · ".join(repr(r[:60]) for r in rows[:n]) + (f" · and {len(rows) - n} more" if len(rows) > n else "")

    for what, rx in ARCH_FIELDS + ((ARCH_AI,) if ai else ()) + ((ARCH_AGENT,) if agent else ()):
        if not any(not EMPTY_VALUE.match(re.sub(r"[*_`\s]+", " ", l).strip().lower()) for l in lines_of(rx)):
            gaps.append(f"#Architecture field empty: {what}")
    if st.header.get("UI", "unknown") == "unknown":
        gaps.append("the UI answer is not recorded - `status.py flag --ui yes|no` (does a person use a screen of it?)")
    if st.header.get("AI product") != "no" and st.header.get("Agent", "unknown") == "unknown":
        gaps.append("the Agent answer is not recorded - ask round 1's agent question, then `status.py flag --agent "
                    "yes|no`")
    rows = {rx: arch_rows(lines_of(rx)) for rx in ARCH_PROVENANCE_FIELDS + ((ARCH_AGENT[1],) if agent else ())}
    bare = [r for rs in rows.values() for r in rs if not re.search(r"(?i)\buser-chosen\b", r)
            and not THIRD_PROVENANCE.search(r)  # refused above as a third value: each problem once (P20)
            and not re.match(r"(?i)\W*constraint", r) and "superseded" not in r.lower()]
    if bare:
        gaps.append(f"{len(bare)} row(s) with no provenance - end each with `user-chosen` (the user picked it) or "
                    f"`default taken, not user-chosen` (you recommended it; \"go with your recommendation\" "
                    f"included): {listed(bare)}")
    every_row = [r for k in fields for r in arch_rows(fields[k])]
    cons = " ".join(r for r in every_row if re.search(r"(?i)constraint", r)) + " ".join(
        " ".join(v) for k, v in fields.items() if re.search(r"(?i)^constraint", k))
    if not cons.strip():
        gaps.append("no `Constraint set:` row - the first row under Stack + tools: the owner's answers 1-4 in short "
                    "(team and hours · money a month · infrastructure they run · lock-in they accept)")
    else:
        miss = [what for what, rx in ARCH_CONSTRAINTS if not re.search(rx, cons, re.I)]
        if miss:
            gaps.append("the constraint set has no " + " · no ".join(miss))
    said = next((l.strip().lstrip("-* ") for l in clean.get("Scope", "").splitlines() if LOGIN.search(l)), "")
    ids = rows[r"^identity"]
    if said and ids and all(re.match(r"(?i)\W*(?:identity custody\W*)?n/?a\b", r) for r in ids):
        gaps.append(f"Identity custody is N/A, but #Scope says {said[:80]!r} - a person logs in: record the login "
                    f"(the company's identity provider, answer 6), how the app checks it (a stable user id, a role) "
                    f"and that it fails closed")
    tooling = " ".join(lines_of(r"^dev tooling"))
    if tooling.strip():
        miss = [what for what, rx in ARCH_TOOLING if not re.search(rx, tooling, re.I)]
        if miss:
            gaps.append(f"the Dev tooling line names no {', no '.join(miss)} - /structure scaffolds exactly these five")
        if re.search(r"(?i)\b(?:tbd|todo|to be decided|undecided)\b", tooling):
            gaps.append("the Dev tooling line leaves a slot undecided (TBD) - name one tool for each slot")
    runtime = rows[r"^runtime"]
    # a row that only says when the same unit moves ("From M4, <host>: ...") keeps the category a row above it gave
    # (a logged run was refused for one; P42)
    later = re.compile(r"(?i)\W*(?:from|until|after|before|once|later|then)\b")
    brand = [r for n, r in enumerate(runtime) if not ARCH_RUNTIME.search(r) and not re.search(r"(?i)\bn/?a\b", r)
             and not (later.match(r) and any(ARCH_RUNTIME.search(x) for x in runtime[:n]))]
    if brand:
        gaps.append(f"runtime target row(s) with no category - container-anywhere · PaaS · VPS · user's machine · static "
                    f"site / CDN (what /deploy executes), not only a brand: {listed(brand)}")
    if runtime and not re.search(r"(?i)" + MONEY + r"|\bfree\b", " ".join(runtime)):
        gaps.append("the runtime target names no cost - what it costs, the free-tier limits and what happens at each "
                    "(throttled, blocked or billed)")
    # "<label>: N/A - <reason>" is no external (a logged run was refused for one; P42)
    ext = [r for r in arch_rows(lines_of(r"^externals"))
           if not re.match(r"(?i)\W*(?:[^:—–\n]{0,60}(?::|\s[—–-])\s*)?(?:none|n/?a)\b", r)]
    noadapter = [r for r in ext if not ARCH_INTERFACE.search(r)]
    if noadapter:
        gaps.append(f"external(s) with no adapter interface (an interface name such as LLMProvider or Storage, plain; "
                    f"backticks only around a path): {listed(noadapter)}")
    nores = [r for r in ext if not ARCH_RESILIENCE.search(r)]
    if nores:
        gaps.append(f"external(s) with no resilience strategy (timeout · retry transient only · fallback or circuit "
                    f"breaker): {listed(nores)}")
    areas = ARCH_AREAS + (ARCH_AI_AREAS if ai else ())
    miss = [what for what, rx in areas if not re.search(rx, body, re.I)]
    if SQL_DBS.search(body) and not re.search(r"(?i)migration", body):
        miss.append("the migrations approach")
    if miss:
        gaps.append(f"concern area(s) neither recorded nor marked N/A: {', '.join(miss)}")
    if ai:
        miss = [what for what, rx in ARCH_RUNTIME_CONFIG if not re.search(rx, body, re.I)]
        if miss:
            gaps.append(f"the model runtime config sets no {', '.join(miss)} - the cost per use depends on them")
        if not ARCH_PER_USE.search(body):
            cap = next((v for k, v in section_fields(re.sub(r"(?m)^\*\*", "- **", clean.get("Vision", ""))).items()
                        if re.search(AI_LINE, k, re.I)), "")
            m = re.search(r"(?i)" + MONEY + r"[^\n·]{0,40}", cap)
            gaps.append("no cost per use - the dominant cost (the model call: tokens × price) worked out from the "
                        "recorded model and config" + (f", against #Vision's {m.group(0).strip()!r}" if m else ""))
    if agent:
        text = " ".join(lines_of(ARCH_AGENT[1]))
        miss = [what for what, rx in ARCH_AGENT_ROWS if not re.search(rx, text, re.I)]
        if text.strip() and miss:
            gaps.append(f"the (Agent) field has no row for AGENT.md §Architect {', '.join(miss)} - each recorded or "
                        f"`N/A — <reason>`")
    for l in body.splitlines():
        if re.search(r"\bVERIFIED\b", l) and "evidence:" not in l:
            gaps.append(f"#Architecture says VERIFIED with no `evidence:` command: {l.strip()[:70]!r} - a decision is "
                        f"not verified by a link or a judgement")
    if re.search(r"docs/architecture\.md", " ".join(lines_of(r"^read"))):
        gaps.append(f"the Read receipt quotes {ARCH_DOC}, which this phase wrote - quote only an input file you opened")
    doc = doc_p.read_text(encoding="utf-8") if doc_p.is_file() else ""
    if not doc and doc_pending:
        pass  # checked at the save; the dry-run's note says what the save checks (arch_docs_pending)
    elif not doc:
        gaps.append(f"no {ARCH_DOC} - fill templates/architecture.md: every section in its order, the owner's "
                    f"answers word for word and the search list in the appendix" + (" with the framework table" if agent
                                                                                   else ""))
    else:
        lines = doc.splitlines()
        # A5/P42: the reader's part first - 0 of 4 logged playbook docs had a diagram (3 of 4 plain ones did), and
        # the round-2 table the owner approved was saved nowhere
        gaps += arch_doc_shape_gaps(doc)
        dec = arch_doc_sections(doc).get("Decisions")
        if dec and not re.search(r"(?m)^\s*(?:###\s+D\d|\||[-*]\s|\d+[.)]\s)", arch_doc_body(doc, "Decisions")):
            gaps.append(f"{ARCH_DOC} `## Decisions` is empty - one `### D<n>.` block per decision: Why · Trade-off we "
                        f"accept · Rejected · Revisit when · Rule · ADR · Provenance")
        m = PLAN_ANSWERS.search(doc)
        nxt = re.search(r"(?m)^#{1,6}\s", doc[m.end():]) if m else None
        if not m or not (doc[m.end():m.end() + nxt.start()] if nxt else doc[m.end():]).strip():
            gaps.append(f"{ARCH_DOC} has no `## Owner's answers` block - each answer word for word, numbered as asked")
        found = [l for l in (search_list_lines(lines) or []) if l.strip() and not l.lstrip().startswith(("|", "#"))]
        if not found:
            gaps.append(f"{ARCH_DOC} has no `## Search list` - one line per search: `- <decision> · <query> · what it "
                        f"settled · <link to the page that says it>`")
        nolink = [l.strip() for l in found if not URL.search(l) and not NOTHING_FOUND.search(l)]
        home = [l.strip() for l in found if URL.search(l)
                and all(HOMEPAGE.match(u) or REDIRECT.search(u) for u in URL.findall(l))]
        if nolink:
            gaps.append(f"{ARCH_DOC} search line(s) with no link: {listed(nolink)}")
        if home:
            gaps.append(f"{ARCH_DOC} search line(s) citing only a homepage or a search redirect - link the page that "
                        f"says the fact (the pricing page, the model list): {listed(home)}")
        if agent:
            options = arch_framework_rows(lines)
            if len(options) < 3:
                gaps.append(f"{ARCH_DOC} has no framework table of 3-4 options under a heading naming the framework - "
                            f"the table shown to the user before the question (AGENT.md §Architect row 1)")
            elif not re.search(r"(?i)none beyond", doc) and all(
                    any(x in o for x in AGENT_EXAMPLES) or re.search(r"no framework|plain|vendor sdk|^none", o)
                    for o in options):
                gaps.append("every framework option is one of AGENT.md's examples - add one the open search found, or "
                            "the line `the search found none beyond AGENT.md's examples`")
            if not REGISTRY.search(doc):
                gaps.append("no framework version from a package registry page (pypi.org · npmjs.com · crates.io) - "
                            "read each version and its date there, this run")
    adr_dir = base / "docs" / "adr"
    adrs = sorted(p for p in adr_dir.glob("*.md") if re.match(r"\d{4}-", p.name)) if adr_dir.is_dir() else []
    adrs = [] if doc_pending else adrs  # written with the document, after the dry-run (P46)
    texts = {p.name: p.read_text(encoding="utf-8", errors="replace") for p in adrs}
    if len(adrs) < 2 and not doc_pending:
        gaps.append(f"{len(adrs)} ADR file(s) - the load-bearing choices go in 2-4 files, `docs/adr/NNNN-<slug>.md` "
                    f"in the ADR shape the dry-run printed")
    nostatus = [n for n, t in texts.items() if not re.search(r"(?im)^\W*status\b", t)]
    if nostatus:
        gaps.append(f"ADR file(s) with no `Status:` line: {', '.join(nostatus)}")
    if agent and adrs:
        # an ADR naming an option of the framework table is the framework's ADR (a logged run's "Use Pydantic AI behind
        # a provider-neutral agent boundary" was refused until renamed; P42)
        names = [o.split("(")[0].strip() for o in arch_framework_rows(doc.splitlines())]
        heads = [" ".join((f + " " + t.split("\n", 1)[0]).replace("-", " ").lower().split()) for f, t in texts.items()]
        named = any(len(n) > 2 and n in h for n in names for h in heads)  # in its title or file name
        miss = [what for what, rx in ARCH_AGENT_ADRS if not any(re.search(rx, t, re.I) for t in texts.values())
                and not (named and what.startswith("the framework"))]
        if miss:
            gaps.append(f"no ADR file for {', '.join(miss)} - AGENT.md §Architect gives rows 1, 2 and 6 one each")
    for name, text in (("#Architecture", body), (ARCH_DOC, doc), *texts.items()):
        if re.search(r"(?i)confiden\w*[^\n]{0,30}?\b100\s?%", text):
            gaps.append(f"{name} states 100% confidence - never 100%; with no criterion VERIFIED by a command, at most 80%")
        if LATEX.search(text):
            gaps.append(f"{name} has LaTeX ({LATEX.search(text).group(0)}...) - plain symbols (≤ ≥ →)")
    return gaps


def arch_template_path() -> str:
    """Where the installed playbook keeps templates/architecture.md, for the start to name."""
    f = tool_file("templates", "architecture.md")
    return f"`{f.as_posix()}`" if f else "the playbook's `templates/architecture.md`"


def architect_rules_text(st: "Status") -> str:
    """The rule sections the questions need. Spine resolution only without a PRODUCT.md; §Declined runs only while an
    earlier gate is unmet (the run's one reason to stop, as /structure does); §Re-run semantics by name - on a re-run
    the RE-RUN line carries its short form (P47: the realistic re-run start was 27K, over the 25K target)."""
    base = st.base if st.base is not None else Path(".")
    skip = {"Spine resolution", "Re-run semantics"} if (base / "PRODUCT.md").is_file() else {"Re-run semantics"}
    if all(st.state(p) in ("filled", "overridden") for p in ("vision", "scope", "plan")):
        skip.add("Declined runs")
    named = [w for s, w in (("Declined runs", "§Declined runs (before stopping or skipping this phase)"),
                            ("Re-run semantics", "§Re-run semantics (before changing the filled section)"))
             if s in skip and (s != "Re-run semantics" or st.state("architect") in ("filled", "overridden"))]
    want = {k: [s for s in v if s not in skip] for k, v in PHASE_RULES["architect"].items()}
    return (rules_text(want, "Rules for /architect, word for word from the rule files (these ARE the rule files for "
                             "this phase - do not open them; `status.py rules architect` prints them again"
                       + (", with " + " and ".join(named) + " - run it then" if named else "")
                       + "):")
            + "\n\n===== PRINCIPLES.md §Production safeguards - the bullets /architect decides =====\n"
            + principle_bullets("Production safeguards", ARCH_SAFEGUARDS))


def architect_start_text(st: "Status") -> str:
    """`next --phase architect`: the spine facts the stack is chosen against, the record's shape and what `set
    architect filled` refuses (P1, P4) - one call, instead of PRODUCT.md and three rule files read whole."""
    base = st.base if st.base is not None else Path(".")
    prod = base / "PRODUCT.md"
    secs = product_sections(prod.read_text(encoding="utf-8")) if prod.is_file() else {}
    clean = {k: re.sub(r"<!--.*?-->", "", v, flags=re.S) for k, v in secs.items()}

    def cut(s: str, n: int = 220) -> str:
        s = s.strip()
        return s if len(s) <= n else s[:n] + "…"

    out = ["/architect start - choose against these; never read PRODUCT.md, PRINCIPLES.md, MECHANISMS.md or AGENT.md "
           "whole (what this phase needs from them is here):"]
    vis = section_fields(re.sub(r"(?m)^\*\*", "- **", clean.get("Vision", "")))
    pick = [(k.split(" (")[0], v) for k, v in vis.items()
            if v.strip() and re.search(r"^who|^business|^constraint|^ai\b|^north star\W+target", k, re.I)]
    out += (["  - #Vision:"] + [f"      {k}: {cut(v, 400)}" for k, v in pick] if pick else
            ["  - #Vision is empty: offer /vision first (Step 0)"])
    scope = scope_fields(clean.get("Scope", ""))
    shown = [(what, [l for k, v in scope.items() if re.search(rx, k, re.I) for l in v])
             for what, rx in (("THE core feature", r"core feature"), ("In scope (now)", r"^in[- ]scope"),
                              ("Deferred", r"^deferred"), ("Non-goals", r"non[- ]goal"),
                              ("Table stakes", r"table[- ]stakes"))]
    if any(v for _, v in shown):
        out.append("  - #Scope (a part built for a Deferred item or a non-goal is gold-plating):")
        for what, ls in shown:
            out += [f"      {what}:"] + [f"        {cut(l)}" for l in ls]
    else:
        out.append("  - #Scope is empty: warn and offer /scope first (Step 0)")
    plan = plan_field_lines(clean.get("Plan", ""))
    timeline = [l for k, v in plan.items() if re.search(r"^timeline", k, re.I) for l in v]
    marks = [l for k, v in plan.items() if re.search(r"^phases|milestones", k, re.I) for l in v
             if re.match(PLAN_MARK, l.strip().lstrip("-* "))]
    cover = [l for k, v in plan.items() if re.search(r"^concern", k, re.I) for l in v]
    if timeline or marks:
        out.append("  - #Plan (the milestones, the Timeline's capacity and paid-infra lines, the concern areas):")
        out += [f"      {cut(l.strip().lstrip('-* '), 160)}" for l in marks]
        out += [f"      Timeline: {cut(l.strip().lstrip('-* '))}" for l in timeline
                if re.search(r"(?i)capacity|paid|hosting|infra|budget|\bh(?:ours)?\s*(?:/|a|per)\s*w", l)]
        out += (["      Concern areas:"] + [f"        {cut(l.strip().lstrip('-* '), 160)}" for l in cover]) if cover else []
    else:
        out.append("  - #Plan is empty: warn and offer /plan first (Step 0)")
    known = [cut(l.strip().lstrip("-* "), 160) for l in timeline
             if re.search(r"(?i)capacity|\bh(?:ours)?\s*(?:/|a|per)\s*w", l)][:1]
    ai_line = next((v for k, v in vis.items() if re.search(AI_LINE, k, re.I)), "")
    cap = re.search(r"(?i)" + MONEY + r"[^\n·]{0,40}", ai_line)
    login = [cut(l.strip().lstrip("-* "), 160) for ls in (v for _, v in shown) for l in ls if LOGIN.search(l)][:1]
    out.append("  - Round 1, already in the spine - show it as the answer to confirm, never ask it blank: "
               + (f"answer 1 (team): {known[0]!r} - ask only the languages they know" if known else
                  "nothing for answer 1")
               + (f" · answer 6 (login): #Scope says {login[0]!r} - ask only which one" if login else "")
               + (f" · #Vision's cost cap per use: {cap.group(0).strip()!r} - the model and its config are priced "
                  f"against it" if cap else ""))
    ui, ai, agent = (st.header.get(k, "unknown") for k in ("UI", "AI product", "Agent"))
    out.append(f"  - Flags: UI {ui} · AI product {ai} · Agent {agent}"
               + (" - UI unknown: decide it from #Scope (does a person use a screen of it?) and run `status.py flag "
                  "--ui yes|no` in the call that writes the section file, never in a call of its own" if ui == "unknown" else "")
               + (" - Agent unknown: round 1 asks the agent question" if ai != "no" and agent == "unknown" else ""))
    tpl = tool_file("templates", "PRODUCT.md")
    labels = product_sections(tpl.read_text(encoding="utf-8")).get("Architecture", "") if tpl else ""
    out += ["  - #Architecture is these fields, labels as written, in a scratch file outside the repo; `set architect "
            "filled --section-from <file>` writes it:"]
    out += ["      " + l for l in labels.splitlines() if l.startswith("- **")]
    out += ["  - One decision per row (a sub-bullet or a table row) under Stack + tools, Data custody, Runtime target, "
            "Identity custody" + (" and (Agent)" if agent == "yes" else "") + "; each row ends with its provenance: "
            "`user-chosen` (the user picked it) or `default taken, not user-chosen` (you recommended it; \"go with "
            "your recommendation\" included) - no other words. The first row under Stack + tools: `Constraint set: "
            "<answers 1-4 in short>`. Data custody and Identity custody follow answers 5 and 6: identity is N/A only "
            "when no person logs in. Each external names its interface plain (LLMProvider, Storage); backticks "
            "only around a real path."
            + (" The cost per use shows its working: `(<input tokens> × <price per 1M> + <output tokens> × <price per "
               "1M>) / 1,000,000 ≈ <amount> per <use>`." if ai == "yes" else ""),
            "  - The model row says `released YYYY-MM-DD`, from the model's page this run. A fact you could "
            "not verify is written `UNVERIFIED` with an open item - record the phase `filled` on the owner's yes, "
            "never `declined` (only the owner declines a phase).",
            "  - A package version and its release date come from the package's normal web page "
            "(`pypi.org/project/<name>/`, `npmjs.com/package/<name>`) - never its `/json` data.",
            # P46: a logged run read the template at call 6 and wrote the document at call 8 of 14 - both rode on
            # every later call, and the save's refusal came after them (4 more calls)
            f"  - The order - each call re-sends everything before it, so small things first and the long documents "
            f"last: round 1 → the searches → round 2 → on the yes, ONE message: the section file, `status.py flag --ui "
            f"yes|no` if unknown, `set architect filled --section-from <file> --dry-run` and the one read of "
            f"{arch_template_path()} (whole, in one read - never earlier). Fix every gap the dry-run names while the "
            f"documents are unwritten; it then prints how to write the ADR files and {ARCH_DOC}. Then ONE message: "
            f"the ADR files, {ARCH_DOC} and, after them in that same message, `set architect filled --section-from "
            f"<file> --commit \"<one line>\"` (no `--commit` on a no).",
            "  - `set architect filled` refuses, every problem in one list - beyond the provenance, the "
            "`Constraint set:` row (team + hours, money a month, infrastructure, lock-in), identity and the model's "
            "date above: an empty field · a Dev tooling line missing one of its five slots or saying TBD · a runtime row with no category, or no "
            "cost · an external with no adapter interface or no resilience strategy · a concern area unrecorded "
            "(resilience, budget, secrets, observability, migrations for a SQL database"
            + ("; prompt-versioning, evals, tracing; the runtime config's max_tokens, timeout, thinking effort, retry "
               "and caching; no cost per use (one with no working - a token count and a price per 1M tokens - is a "
               "warning); a model id over a year old" if ai == "yes" else "") + ")"
            + (" · an (Agent) row missing" if agent == "yes" else "")
            + " · the UI or Agent flag unknown · VERIFIED with no `evidence:` · 100% confidence · LaTeX · the ADR "
            "files and the document (the dry-run prints their checks).",
            "  - `set architect filled` prints the rest of the close and the git facts for the save question."]
    maybe = ai != "no" and agent == "unknown"  # round 1 asks; a yes must not cost a second start call
    if agent == "yes" or maybe:
        rules = Path(agent_rules())
        if rules.is_file():
            out += ["", f"===== AGENT.md §Architect ({rules.as_posix()}) - "
                        + ("applies only if round 1's agent answer is yes; " if maybe else "")
                        + "apply every row; do not open the file =====", print_sections(rules, ["Architect"])]
    return "\n".join(out)


# ---- /structure (P1, P2, P4, P19, P20, P25) -----------------------------------------------------------------------
# A logged Claude /structure read PRINCIPLES.md, MECHANISMS.md and PRODUCT.md whole (~69 KB on the agent project)
# before writing anything and re-sent them on each of its 26 calls (158k context at the end). A logged Gemini run left
# five lanes without tests/, an assertTrue(True) test, print-only make targets, `make lint` running the structure
# check, and Alembic and a container recorded with no migrations/ and no Dockerfile. The start prints #Architecture
# (what decides every scaffolding file), the files the Dev tooling line asks for, the decisions that need a home and
# this phase's rules; `set structure filled` runs the structure check and refuses every countable gap in one list, on
# /structure's own close only (never phase_check: a project filled under older rules is not blocked later).
PHASE_RULES["structure"] = {
    "PRINCIPLES.md": ["Architecture & quality bar", "Production safeguards"],
    "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status"],
}
PHASE_CLOSE_RULES["structure"] = {"PRINCIPLES.md": ["The exit-criteria gate"],
                                  "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"]}
CLOSE_STEPS["structure"] = (
    "every number this phase introduced (a port, a cap, a version) against #Vision and #Architecture",
    "#Architecture, its Dev tooling line above all - every scaffolding file is the tool recorded there - and its "
    "runtime line: no docker-compose.yml for a target that does not use one",
    "the map against the tree both ways, the five sections, a tests/ per module, every decision's home, the root "
    "files, the tools against the Dev tooling line, .gitignore, .env.example, the config files, prompts/ and the agent "
    "folders")
# The start's head: the close prints at `set structure filled`, so the start carries only the habits (the generic
# close checklist is ~3 KB, re-sent on every call of the run).
STRUCTURE_HEAD = (
    "This phase closes with ONE call - `status.py set structure filled --section-from <file>`, #Structure in a "
    "scratch file outside the repo (never an edit tool on PRODUCT.md): it runs check_structure.py itself, names every "
    "gap at once, and prints the rest of the close. To see the gaps first, add `--dry-run`: the same checks, nothing "
    "written. Every rule they apply is printed below - the scripts' source says nothing more (P45).",
    "Commands work in PowerShell and in bash: one command per call - no &&, tail, grep or export; never `cd <path> &&`. "
    "The same command fails 3 times: stop and tell the user what fails. Plain symbols (≤ →), never LaTeX.",
    "No commit during the run - not even a STATUS.md the last phase left: the one save at the close takes every "
    "change, and leaves the playbook's install (.agents/, .claude/skills/ ...) out.",
    "A `Read:` line quotes each input file you opened beyond what `next` printed (an ADR, an existing file): "
    "`status.py quote <file> \"<words>\"` prints the line to paste.",
)
# Dev tooling slot -> {tool words: the root files that configure that tool}. A tool the table does not know is never
# refused: only what can be counted is.
STRUCTURE_SLOTS = {
    "hook runner": {r"pre-commit": (".pre-commit-config.yaml",),
                    r"lefthook": ("lefthook.yml", "lefthook.yaml", ".lefthook.yml", ".lefthook.yaml"),
                    r"husky": (".husky",)},
    "secret scanner": {r"gitleaks": (".gitleaks.toml", "gitleaks.toml"), r"detect-secrets": (".secrets.baseline",)},
    "task runner": {r"\bjust(?:file)?\b": ("justfile", "Justfile", ".justfile"),
                    r"\bmake(?:file)?\b": ("Makefile", "makefile", "GNUmakefile"),
                    r"\btaskfile\b|go-task": ("Taskfile.yml", "Taskfile.yaml"),
                    r"\b(?:npm|pnpm|yarn|bun)\b": ("package.json",)},
    "dependency manifest": {r"pyproject|\buv\b|poetry|hatch|\bpdm\b": ("pyproject.toml",),
                            r"package\.json|\bnpm\b|\bpnpm\b|\byarn\b|\bbun\b": ("package.json",),
                            r"\bcargo\b": ("Cargo.toml",), r"go\.mod|go modules": ("go.mod",),
                            r"gemfile|bundler": ("Gemfile",)},
}
STRUCTURE_SLOT_NAMES = {"hook runner": "commit-hook config", "secret scanner": "secret-scan config",
                        "task runner": "task runner", "dependency manifest": "dependency manifest"}
# (what it is, the words in #Architecture's values that record it, what proves its home on disk)
STRUCTURE_HOMES = (
    ("migrations", r"(?i)\b(?:alembic|prisma|drizzle|flyway|liquibase|knex|sequelize|typeorm|goose|migrations?)\b",
     "migrations/ folder (or alembic/, prisma/, drizzle/)"),
    ("container", r"(?i)\bdocker(?:file)?\b|\bcontainers?\b", "Dockerfile"),
    ("background worker", r"(?i)\bworker\b|\bcelery\b|procrastinate|dramatiq|\brq\b|bullmq|sidekiq|\btemporal\b",
     "a worker or queue row under ## Where decisions live"),
)
# backticked or not: /architect's check accepts an interface name without backticks (2026-10-04)
STRUCTURE_PORT = re.compile(r"(?<![\w/.])([A-Z][A-Za-z0-9]*(?:Provider|Port|Client|Gateway|Adapter|Inbound|Outbound|"
                            r"Tracer|Store|Repository|Sender|Queue))(?![\w/.])")
SECRET_NAME = re.compile(r"(?i)key|secret|token|password|passwd|credential|private|salt|signing")
DATASTORE = re.compile(r"(?i)postgres|mysql|mariadb|sqlite|mongo|database|\bneon\b|supabase|dynamo|firestore")
AGENT_DIRS = ("tools", "guards", "adapters", "tests")


def structure_fields(body: str) -> dict[str, str]:
    """A section's `**Label:**` fields (with or without the `- `), each value with its continuation lines."""
    return {k: "\n".join(v) for k, v in plan_field_lines(re.sub(r"<!--.*?-->", "", body, flags=re.S)).items()}


def structure_tools(dev: str) -> dict[str, tuple[str, tuple[str, ...]] | None]:
    """For each slot the tool the Dev tooling line names and its files; None = a tool this table does not know (never
    refused), missing = the line names nothing for the slot."""
    out: dict[str, tuple[str, tuple[str, ...]] | None] = {}
    for slot, tools in STRUCTURE_SLOTS.items():
        seg = re.search(rf"(?i){slot}\s*(?:\([^)]*\))?\s*[:=—–|-]\s*([^·;|\n]+)", dev)
        text = seg.group(1) if seg else re.sub(r"(?i)" + "|".join(STRUCTURE_SLOTS), " ", dev)
        hit = [(re.search(rf"(?i){rx}", text), files) for rx, files in tools.items() if re.search(rf"(?i){rx}", text)]
        if hit:
            out[slot] = (hit[0][0].group(0), hit[0][1])
        elif seg:
            out[slot] = None
    return out


def ignored(patterns: list[str], name: str) -> bool:
    """Whether a root file `name` is ignored by these .gitignore lines (last match wins, `!` re-includes)."""
    import fnmatch
    hit = False
    for p in patterns:
        neg, pat = p.startswith("!"), p.lstrip("!").strip().lstrip("/")
        pat = pat[3:] if pat.startswith("**/") else pat
        if pat and fnmatch.fnmatchcase(name, pat):
            hit = not neg
    return hit


def engine_lines(engine: Path, base: Path) -> tuple[int, list[str]]:
    """The playbook's check_structure.py run in this process (a new interpreter took ~5 s per run on a logged Windows
    machine): its exit code and its output lines."""
    import contextlib
    import importlib.util
    import io
    spec = importlib.util.spec_from_file_location("check_structure_engine", engine)
    mod = importlib.util.module_from_spec(spec)
    keep, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # install.sh copies templates/: no __pycache__
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = keep
    out, cwd = io.StringIO(), os.getcwd()
    try:
        os.chdir(base)
        with contextlib.redirect_stdout(out):
            code = mod.main(["STRUCTURE.md", "."])
    finally:
        os.chdir(cwd)
    return code, out.getvalue().splitlines()


def env_comment(lines: list[str], i: int) -> bool:
    """A variable's how-to comment: on its line, or above its block (one comment may cover a key and its secret)."""
    if "#" in lines[i].split("=", 1)[1]:
        return True
    for line in reversed(lines[:i]):
        if line.lstrip().startswith("#"):
            return True
        if not line.strip():
            return False
    return False


def project_dirs(base: Path) -> list[Path]:
    out = []
    for dirpath, dirnames, _ in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        out += [Path(dirpath) / d for d in dirnames]
    return out


YAML_LIB = re.compile(r"(?im)^\s*(?:import\s+\S*yaml|from\s+\S*yaml\S*\s+import)|require\(\s*['\"][^'\"]*yaml|"
                      r"from\s+['\"][^'\"]*yaml[^'\"]*['\"]|^\s*\"[^\"\n]*yaml[^\"\n]*\"\s*$|serde_yaml|snakeyaml")


def structure_loaders(base: Path) -> list[Path]:
    """Code files (tests left out) that name platform.yaml AND import a YAML library or also name product.yaml: the
    config loaders. An entry point that only passes one path along is not one."""
    out = []
    for dirpath, dirnames, files in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".") and d not in TEST_DIR_NAMES]
        for n in files:
            f = Path(dirpath) / n
            if f.suffix not in CODE_EXT or re.match(r"(?i)test_|.*[._]test\.|.*\.spec\.|conftest", n):
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            # a docstring or comment naming the files is not a loader: a logged run's app/config/__init__.py docstring
            # named platform.yaml and was refused as a second loader (2 calls, ~258K tokens, 2026-10-06)
            text = re.sub(r"(?m)^\s*(?:#|//).*$", "", re.sub(r'(?s)""".*?"""|\'\'\'.*?\'\'\'|/\*.*?\*/', "", text))
            if re.search(r"platform\.ya?ml", text) and (YAML_LIB.search(text) or re.search(r"product\.ya?ml", text)):
                out.append(f)
    return sorted(out)


TEST_DIR_NAMES = {"tests", "test", "__tests__", "spec", "evals"}


STRUCTURE_CODE_LINES = 40  # the logged runs' module files: 1-13 lines; the run that wrote product logic: 47 and 56


def structure_product_code(base: Path, text: str) -> list[tuple[str, int]]:
    """Code files inside the modules STRUCTURE.md lists (tests and the config loader left out) longer than
    STRUCTURE_CODE_LINES non-blank, non-comment lines."""
    mods = re.search(r"(?ms)^##\s+Modules\s*$(.*?)(?=^##\s|\Z)", text)
    roots = [base / m for m in re.findall(r"(?m)^\s*\|\s*`([^`\n]+)`", mods.group(1) if mods else "")]
    loaders = set(structure_loaders(base))
    out = []
    for root in (r for r in roots if r.is_dir()):
        for dirpath, dirnames, files in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and d not in TEST_DIR_NAMES]
            for n in files:
                f = Path(dirpath) / n
                if f.suffix not in CODE_EXT or f in loaders or re.match(r"(?i)test_|.*[._]test\.|.*\.spec\.|conftest|fakes?\.", n):
                    continue
                lines = [l for l in f.read_text(encoding="utf-8", errors="replace").splitlines()
                         if l.strip() and not re.match(r"\s*(?:#|//|/?\*)", l)]
                if len(lines) > STRUCTURE_CODE_LINES:
                    out.append((f.relative_to(base).as_posix(), len(lines)))
    return sorted(set(out))




def structure_gaps(base: Path, st: "Status") -> list[str]:
    """What `set structure filled` needs, every problem named once in one list (P20): the structure check's every
    failure, then the countable exit criteria the check does not see."""
    gaps: list[str] = []
    smd = base / "STRUCTURE.md"
    text = smd.read_text(encoding="utf-8") if smd.is_file() else ""
    if not text:
        gaps.append("no STRUCTURE.md - the folder map, its five sections and the shape's why")
    # the project's copy, never the installed playbook's own (.agents/, .claude/ ...: hidden folders are skipped)
    copy = next((d / "check_structure.py" for d in [base, *project_dirs(base)] if (d / "check_structure.py").is_file()),
                None)
    engine = tool_file("templates", "check_structure.py")
    if copy is None:
        gaps.append("no check_structure.py in the project - copy the playbook's (the path is in the start) into "
                    "scripts/; the commit hook and later phases run that copy")
    elif engine is not None and copy.read_bytes().replace(b"\r\n", b"\n") != engine.read_bytes().replace(b"\r\n", b"\n"):
        gaps.append(f"{copy.relative_to(base).as_posix()} differs from the playbook's check - copy it over again, "
                    f"never edit the copy")
    if text and engine is not None:
        code, lines = engine_lines(engine, base)  # every failure, not phase_check's first four
        gaps += [f"check_structure: {l.strip()[7:].strip()}" for l in lines if "[FAIL]" in l]
        if code and not any("[FAIL]" in l for l in lines):
            gaps.append(f"check_structure: {lines[-1] if lines else f'exit {code}'}")
    if text and not re.search(r"(?i)\bdomain modules?\b|\bby concern\b|\blayer(?:s|ed)\b|\bsteps\b", text):
        gaps.append("STRUCTURE.md names no shape - one line: domain modules, layers or steps, and why")
    if text:
        gaps += doc_order_gaps(text, STRUCT_DOC_SECTIONS, "STRUCTURE.md", "templates/structure.md")
        if len(text.encode("utf-8")) > 20000:
            gaps.append(f"STRUCTURE.md is {len(text.encode('utf-8')):,} bytes (template: at most 14,000) - a path "
                        f"appears in the tree, then in ONE table")
    prod = base / "PRODUCT.md"
    secs = product_sections(prod.read_text(encoding="utf-8")) if prod.is_file() else {}
    arch = structure_fields(secs.get("Architecture", ""))
    values = "\n".join(arch.values())
    dev = next((v for k, v in arch.items() if re.match(r"(?i)dev tooling", k)), None)
    # the root files every shape needs
    for names in (("README.md",), (".gitignore",), (".env.example",), ("CONTRIBUTING.md",), ("SECURITY.md",),
                  ("CHANGELOG.md",), (".gitattributes",), AGENT_FILES):
        if not any((base / n).exists() for n in names):
            gaps.append(f"no {' or '.join(names)} at the project root"
                        + (" - copy the playbook's templates/gitattributes (LF for text files)" if
                           names == (".gitattributes",) else ""))
    if (base / "CHANGELOG.md").is_file() and "unreleased" not in (base / "CHANGELOG.md").read_text(
            encoding="utf-8", errors="replace").lower():
        gaps.append("CHANGELOG.md has no `[Unreleased]` section (Keep a Changelog)")
    for n in AGENT_FILES:
        f = base / n
        if f.is_file():
            body = f.read_text(encoding="utf-8", errors="replace")
            copied = [h for h in ("Vision", "Scope", "Plan", "Architecture") if re.search(rf"(?m)^##\s+{h}\b", body)]
            if copied:
                gaps.append(f"{n} copies PRODUCT.md's #{copied[0]} - it is a pointer to the spine plus the rules an "
                            f"agent breaks first, never a copy")
    # the tools against the Dev tooling line
    if dev is None:
        gaps.append("#Architecture has no Dev tooling line - recommend a hook runner, secret scanner, task runner and "
                    "manifest that fit the stack, say why, and record them in #Architecture first")
    tools = structure_tools(dev or "")
    for slot, kinds in STRUCTURE_SLOTS.items():
        named = tools.get(slot, "missing")
        if named is None:
            continue  # a tool this check does not know: never refused
        present = {files: [f for f in files if (base / f).exists()] for files in kinds.values()}
        if named == "missing":
            if not any(present.values()):
                gaps.append(f"no {STRUCTURE_SLOT_NAMES[slot]} - and the Dev tooling line names none: recommend one "
                            f"that fits the stack and record it")
            continue
        tool, files = named
        if not present[files]:
            gaps.append(f"the Dev tooling line names {tool} ({slot}) - no {files[0]} at the root")
        if slot in ("hook runner", "task runner"):  # package.json is a manifest too: never "a tool nobody chose"
            for other, found in present.items():
                found = [f for f in found if f != "package.json"]
                if other != files and found and not set(found) & set(files):
                    gaps.append(f"{found[0]} is a {slot} the Dev tooling line does not name (it names {tool}) - delete "
                                f"it, or record the change in #Architecture")
    lint = re.search(r"(?i)\b(ruff|eslint|biome|flake8|pylint|golangci|rubocop|clippy)\b", dev or "")
    for name in ("Makefile", "justfile", "Justfile"):
        f = base / name
        if not (lint and f.is_file()):
            continue
        m = re.search(r"(?ms)^lint\s*:[^\n]*\n((?:[ \t]+[^\n]*\n?)*)", f.read_text(encoding="utf-8", errors="replace"))
        if m and m.group(1).strip() and not re.search(rf"(?i){lint.group(1)}", m.group(1)):
            gaps.append(f"{name}: `lint` does not run {lint.group(1)} (the Dev tooling line's linter) - /structure ends "
                        f"runnable: the task runs it now")
    # .gitignore and .env.example
    gi, lost = base / ".gitignore", []
    if gi.is_file():
        pats = [l.strip() for l in gi.read_text(encoding="utf-8", errors="replace").splitlines()
                if l.strip() and not l.lstrip().startswith("#")]
        leaks = [n for n in (".env", ".env.bak", ".env.local", "prod.env.local") if not ignored(pats, n)]
        if leaks:
            gaps.append(f".gitignore does not ignore {', '.join(leaks)} - .env and every variant or backup "
                        f"(`.env`, `.env.*`, `*.env.local`), with `!.env.example`")
        if ignored(pats, ".env.example"):
            gaps.append(".gitignore ignores .env.example - add `!.env.example`: it is the one committed env file")
        # merge, never replace: a logged Codex run replaced .gitignore, lost `.agents/`, and its save took the install
        old = [l.strip() for l in git(base, "show", "HEAD:.gitignore").splitlines()
               if l.strip() and not l.lstrip().startswith("#")]
        lost = [l for l in old if l not in pats]
        if lost:
            gaps.append(f".gitignore lost {len(lost)} line(s) the committed one had: {', '.join(lost[:6])} - put them "
                        f"back: add your lines to the existing file, never replace it")
    import fnmatch
    dirpats = [l.strip().strip("/") for l in (gi.read_text(encoding="utf-8", errors="replace").splitlines()
                                               if gi.is_file() else []) if l.strip() and l.strip()[0] not in "#!"]
    tracked = git(base, "ls-files").splitlines()
    for p in INSTALL_PATHS:
        parts = p.split("/")
        if (base / p).is_dir() and not any(install_root(t) == p for t in tracked) and parts[0] + "/" not in lost and                 parts[0] not in lost and not any(
                fnmatch.fnmatchcase("/".join(parts[:i]), pat.removeprefix("**/")) for pat in dirpats
                for i in range(1, len(parts) + 1)):
            gaps.append(f".gitignore does not ignore the playbook's install {p}/ - add `{p}/` (the save leaves it out "
                        f"either way; this keeps it out of every other commit)")
    for envdir in (".venv", "venv", "node_modules"):  # the install made them: the save's `git add -A` would take them
        if (base / envdir).is_dir() and not any(fnmatch.fnmatchcase(envdir, pat.removeprefix("**/")) for pat in dirpats):
            gaps.append(f".gitignore does not ignore {envdir}/ - the install made it; add `{envdir}/`")
    ex = base / ".env.example"
    if ex.is_file():
        lines = ex.read_text(encoding="utf-8", errors="replace").splitlines()
        env = {}
        for i, l in enumerate(lines):
            m = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", l)
            if m:
                env[m.group(1)] = (m.group(2).split(" #")[0].strip().strip("'\""), i)
        for name, (val, i) in env.items():
            if SECRET_NAME.search(name) and val and "CHANGE_ME" not in val:
                gaps.append(f".env.example: {name} holds a value that could pass a check - `CHANGE_ME__{name}__CHANGE_ME`")
            elif SECRET_NAME.search(name) and val and not env_comment(lines, i):
                gaps.append(f".env.example: {name} has no comment saying how to get or generate the real value")
        dbs = [n for n in env if re.search(r"(?i)(?:database|db|postgres|mongo|mysql)\w*_(?:url|dsn|uri)$|^(?:database|db)_?(?:url|dsn|uri)$", n)]
        test = [n for n in dbs if "TEST" in n.upper()]
        if (dbs or DATASTORE.search(values)) and not test:
            gaps.append(".env.example declares no isolated test datastore (`TEST_DATABASE_URL` or equivalent) - its own "
                        "variable, never the development one")
        for t in test:
            same = [n for n in dbs if n != t and env[n][0] and env[n][0] == env[t][0]]
            if same:
                gaps.append(f".env.example: {t} has the same value as {same[0]} - the test datastore must differ")
    # the config-layering files
    plat = next((p for p in (find_in_project(base, "platform.yaml"), find_in_project(base, "platform.yml")) if p), None)
    if plat is None or not any((plat.parent / n).is_file() for n in ("product.yaml", "product.yml")):
        gaps.append("no platform.yaml + product.yaml - the layered config (engine knobs, product knobs) beside a typed "
                    "loader, never an empty config/")
    else:
        # the loader may sit anywhere the map names it: a logged run was refused "no loader beside config/platform.yaml"
        # for app/platform/config.py and added a second loader (~330K tokens on each of two tools, 2026-10-03)
        loaders = structure_loaders(base)
        beside = [p for p in plat.parent.iterdir() if p.is_file() and p.suffix in CODE_EXT]
        if not loaders and not beside:
            gaps.append(f"no typed loader for {plat.relative_to(base).as_posix()} - one code file (in the project's "
                        f"own language) that reads it, product.yaml and .env: beside them, or wherever STRUCTURE.md "
                        f"names it")
        elif len(loaders) > 1:
            gaps.append(f"{len(loaders)} config loaders read platform.yaml: "
                        f"{', '.join(p.relative_to(base).as_posix() for p in loaders)} - keep one, delete the others")
    dirs = project_dirs(base)
    # decisions with a home on disk
    for what, rx, home in STRUCTURE_HOMES:
        hit = re.search(rx, values)
        if not hit or re.search(rf"(?i)\bno\s+{re.escape(hit.group(0))}", values):
            continue
        if what == "migrations" and not any(d.name in ("migrations", "alembic", "prisma", "drizzle", "migrate")
                                            for d in dirs):
            gaps.append(f"#Architecture records {hit.group(0)}, and there is no {home} on disk - create it and list "
                        f"it under ## Where decisions live")
        if what == "container" and not any(base.glob("**/Dockerfile")) and not any(base.glob("**/*.Dockerfile")):
            gaps.append(f"#Architecture records a {hit.group(0).lower()}, and there is no {home} - create it and "
                        f"list it under ## Where decisions live")
        decide = re.search(r"(?ms)^##\s+Where decisions live\s*$(.*?)(?=^##\s|\Z)", text)
        if what == "background worker" and decide and not re.search(r"(?i)worker|queue|\bjobs?\b", decide.group(1)):
            gaps.append(f"#Architecture records a {hit.group(0)} - no worker or queue row under ## Where decisions live")
    if re.search(r"(?i)compose", values) is None and any(base.glob("*compose*.y*ml")):
        gaps.append("docker-compose file at the root, but #Architecture's runtime target uses none - delete it, or "
                    "record why in #Architecture")
    squeezed = re.sub(r"[\s`_-]", "", text).lower()  # "LLM Provider adapter" names `LLMProvider`
    for port in sorted(set(STRUCTURE_PORT.findall(values))):
        if text and port.lower() not in squeezed:
            gaps.append(f"#Architecture's adapter `{port}` has no home in STRUCTURE.md - a row under ## Where decisions "
                        f"live naming the module's adapters/ folder")
    # AI and agent homes
    struct = structure_fields(secs.get("Structure", ""))
    if st.header.get("AI product") == "yes":
        if not any(d.name == "prompts" for d in dirs):
            gaps.append("AI product: no prompts/ folder - versioned YAML inside the backend package, never inline")
        if not any(re.search(r"(?i)prompts", k) and re.search(r"(?i)prompts/", v) for k, v in struct.items()):
            gaps.append("AI product: #Structure's Prompts location is empty - the prompts/ path")
    if st.header.get("Agent") == "yes":
        best = max(dirs, key=lambda d: sum((d / x).is_dir() for x in AGENT_DIRS), default=None)
        have = {x for x in AGENT_DIRS if best is not None and (best / x).is_dir()}
        if len(have) < 2:
            gaps.append("Agent: no agent module with tools/ · guards/ · adapters/ · tests/ - create the folders "
                        "(AGENT.md §Structure, printed in the start)")
        elif have != set(AGENT_DIRS):
            gaps.append(f"Agent: {best.relative_to(base).as_posix()}/ has no "
                        f"{' · '.join(x + '/' for x in AGENT_DIRS if x not in have)} - create it (AGENT.md §Structure)")
        if not any(d.name == "evals" for d in dirs):
            gaps.append("Agent: no evals/ folder (evals/agent/ + labels/, or the project's eval folder) - create it")
        if re.search(r"platform/audit", text):
            gaps.append("Agent: the audit log sits in platform/ - it belongs to a module that owns it (e.g. audit/)")
    # no product logic (P44): a logged run wrote payroll rules with a hard-coded statutory rate into a module
    gaps += [f"{f} has {n} lines of code - /structure writes folders, config and empty modules only; product logic "
             f"is /build's: leave one comment saying what goes there" for f, n in structure_product_code(base, text)]
    gaps += structure_run_gaps(base, text, secs.get("Structure", ""))
    if not any(re.search(r"(?i)folder|map|purpose", k) and v.strip() for k, v in struct.items()):
        gaps.append("#Structure: the folder → purpose summary is empty")
    if not re.search(r"(?im)^.*evidence:.*check_structure", secs.get("Structure", "")):
        gaps.append("#Structure has no `evidence:` line naming check_structure.py - `evidence: python "
                    "scripts/check_structure.py → <its last line> · STRUCTURE.md · <date>` (this `set` runs it)")
    return gaps


# ---- /structure ends RUNNABLE and writes its boilerplate in ONE call (owner decisions 2026-10-04) -------------
# Only the plain runs of a logged 4-tool round ended runnable (a lockfile, lint, a passing test); 5 of 8 scaffolds could
# not run, two playbook runs committed stub lockfiles and one Dockerfile copied a uv.lock the repo did not have. One
# tool wrote its 74 starter files in 74 calls (plain: 38), each call re-sending the whole conversation (S6/S11).
LOCK_REAL = {"uv.lock": r"\[\[package\]\]", "poetry.lock": r"\[\[package\]\]|content-hash", "pdm.lock": r"content_hash|"
             r"\[\[package\]\]", "Cargo.lock": r"\[\[package\]\]", "package-lock.json": r'"lockfileVersion"',
             "pnpm-lock.yaml": r"lockfileVersion", "yarn.lock": r"yarn lockfile|__metadata", "bun.lock":
             r"lockfileVersion", "Gemfile.lock": r"DEPENDENCIES", "composer.lock": r'"content-hash"', "go.sum": r"\S"}
LOCK_PENDING = re.compile(r"(?im)^.*\block pending\b.*$")
SMOKE_PASS = re.compile(r"(?i)\b\d+\s+passed\b|\bpass(?:ed|es)?\b|\bok\b|✓|\bsuccess")
RUN_FAIL = re.compile(r"(?i)\b[1-9]\d*\s+(?:failed|errors?|problems?)\b|(?<!\d )\bfail(?:ed|ure)?\b|\bFAIL\b|"
                      r"\btraceback\b|\berror:")
LINTERS = r"\blint|ruff|eslint|biome|flake8|pylint|golangci|rubocop|clippy"
# a smoke test may import its modules one by one, or walk the package
IMPORT_WALK = re.compile(r"walk_packages|iter_modules|import_module|importlib|import\.meta\.glob|readdirSync|globSync|"
                         r"\bglob\(")
NO_NETWORK = re.compile(r"(?i)could not resolve|name or service not known|getaddrinfo|ENOTFOUND|EAI_AGAIN|ECONNREFUSED|"
                        r"ECONNRESET|ETIMEDOUT|network is unreachable|temporary failure in name resolution|no route to "
                        r"host|failed to fetch|failed to download|dns error|tcp connect error|connection (?:refused|"
                        r"reset|timed out)|offline|ConnectError|Max retries exceeded|unable to access")


def structure_manifests(base: Path) -> list[Path]:
    """The dependency manifests at the root and one folder down (frontend/package.json), never the install's."""
    tops = [base] + [d for d in sorted(base.iterdir()) if d.is_dir() and d.name not in SKIP_DIRS
                     and not d.name.startswith(".")]
    return [d / n for d in tops for n in LOCKS if (d / n).is_file()
            and (n != "go.mod" or re.search(r"(?m)^require\b", (d / n).read_text(encoding="utf-8", errors="replace")))]


def manifest_deps(man: Path) -> int:
    """How many dependencies a manifest names (runtime + dev); 0 when it cannot tell."""
    text = man.read_text(encoding="utf-8", errors="replace")
    if man.name == "package.json":
        try:
            data = json.loads(text)
        except ValueError:
            return 0
        return sum(len(data.get(k) or {}) for k in ("dependencies", "devDependencies"))
    if man.name == "pyproject.toml":
        lists = re.findall(r"(?ms)^\s*(?:dependencies|dev|test|lint)\s*=\s*\[(.*?)\]", text)
        return sum(len(re.findall(r"[\"'][A-Za-z0-9]", x)) for x in lists)
    return 0


def lock_is_real(f: Path, man: Path | None = None) -> bool:
    """Written by the package manager: its own markers, and - when the manifest names dependencies - more than the
    project itself resolved (a logged run committed a package-lock.json holding only its workspace root)."""
    text = f.read_text(encoding="utf-8", errors="replace")
    wants = manifest_deps(man) if man is not None else 0
    if f.name == "package-lock.json":
        try:
            pkgs = json.loads(text).get("packages") or {}
        except ValueError:
            return False
        return '"lockfileVersion"' in text and (not wants or len(pkgs) > 1)
    if f.name in ("uv.lock", "Cargo.lock", "poetry.lock") and wants and text.count("[[package]]") < 2:
        return False
    if f.name.startswith("requirements"):
        reqs = [l for l in text.splitlines() if l.strip() and not l.lstrip().startswith(("#", "-"))]
        return bool(reqs) and all("==" in l or " @ " in l for l in reqs)
    rx = LOCK_REAL.get(f.name)
    return f.name == "bun.lockb" or (rx is not None and re.search(rx, text) is not None)


def structure_run_gaps(base: Path, struct_md: str, section: str) -> list[str]:
    """/structure ends runnable (owner, 2026-10-04): a real lockfile per manifest, the linter and ONE smoke test ran,
    their last lines in #Structure's evidence - or `lock pending` when there was no network."""
    gaps: list[str] = []
    pending = LOCK_PENDING.search(re.sub(r"<!--.*?-->", "", section, flags=re.S)) is not None
    locks: list[str] = []
    for man in structure_manifests(base):
        rel = man.relative_to(base).as_posix()
        lock = next((d / lk for lk in LOCKS[man.name] for d in (man.parent, base) if (d / lk).is_file()), None)
        if lock is None:
            if not pending:
                gaps.append(f"{rel} has no lockfile - resolve it with the package manager and install from it "
                            f"(`status.py prove` runs the commands); no network: record the `lock pending` line it "
                            f"prints")
            continue
        locks.append(lock.name)
        if not lock_is_real(lock, man):
            gaps.append(f"{lock.relative_to(base).as_posix()} is a stub (no resolved package) - let the package manager "
                        f"write it; never a hand-written lockfile")
    smokes = sorted((f for f in project_files(base, CODE_EXT) if "smoke" in f.name.lower()), key=lambda f: len(f.parts))
    if not smokes:
        gaps.append("no smoke test - ONE test file named *smoke* (e.g. tests/test_smoke.py) that imports every module "
                    "under ## Modules and shows a CHANGE_ME value failing the boot")
    else:
        rel = smokes[0].relative_to(base).as_posix()
        t = smokes[0].read_text(encoding="utf-8", errors="replace")
        if "CHANGE_ME" not in t:
            gaps.append(f"{rel} never shows a CHANGE_ME value failing the boot - set one and assert the loader refuses "
                        f"it (a placeholder that boots is a live incident)")
        mods = re.search(r"(?ms)^##\s+Modules\s*$(.*?)(?=^##\s|\Z)", struct_md)
        names = [m.rstrip("/").rsplit("/", 1)[-1] for m in re.findall(r"(?m)^\s*\|\s*`([^`\n]+)`",
                                                                     mods.group(1) if mods else "")]
        missing = [n for n in names if not re.search(rf"\b{re.escape(n)}\b", t)]
        if missing and not IMPORT_WALK.search(t):
            gaps.append(f"{rel} does not import every module ({', '.join(missing[:4])}) - import each one, or walk the "
                        f"package")
    lines = [l for l in section.splitlines() if "evidence:" in l]
    if not pending:
        smoke_ev = [l for l in lines if re.search(r"(?i)smoke", l) or any(f.name in l for f in smokes)]
        lint_ev = [l for l in lines if re.search(rf"(?i){LINTERS}", l) and l not in smoke_ev]
        how = "`status.py prove \"<lock>\" \"<install>\" \"<lint>\" \"<smoke test>\"` prints the line to paste"
        if not smoke_ev:
            gaps.append(f"#Structure has no evidence line for the smoke test - {how}")
        elif not SMOKE_PASS.search(smoke_ev[0].split("→")[-1]) or RUN_FAIL.search(smoke_ev[0].split("→")[-1]):
            gaps.append(f"the smoke test's evidence shows no pass: {smoke_ev[0].strip()[:120]!r} - fix it and run "
                        f"`status.py prove` again")
        if not lint_ev:
            gaps.append(f"#Structure has no evidence line for the linter - {how}")
        elif RUN_FAIL.search(lint_ev[0].split("→")[-1]):
            gaps.append(f"the linter's evidence shows a failure: {lint_ev[0].strip()[:120]!r}")
    # STRUCTURE.md's "Checks you run" results come from the printed lines: a logged run typed "All checks passed!"
    # and "3 passed" there before prove ran, prove then stopped at `lock pending`, and the table was never corrected
    checks = re.search(r"(?ms)^##\s+Checks you run\s*$(.*?)(?=^##\s|\Z)", struct_md)
    printed = " ".join(lines).lower()
    for row in re.findall(r"(?m)^\|(.+)\|\s*$", checks.group(1) if checks else ""):
        cells = [c.strip() for c in row.split("|")]
        if len(cells) < 3 or set(cells[-1]) <= set("-: ") or cells[0].lower() in ("check",):
            continue
        cmd, result = cells[-2].strip("` "), cells[-1]
        if "check_structure" in cmd or re.search(r"(?i)lock pending|not run|not decided", result):
            continue  # set runs the structure check itself; an honest not-run is fine
        said = re.sub(r"^\s*\d{4}-\d{2}-\d{2}\s*[:·-]?\s*", "", result).strip().strip("`").lower()
        if said and said not in printed:
            gaps.append(f"STRUCTURE.md `## Checks you run` says {result[:60]!r} for `{cmd[:40]}`, but no evidence line "
                        f"in #Structure printed it - copy the result from `status.py prove`'s lines (or write "
                        f"`not run: <why>`), never a result typed by hand")
    # a Dockerfile that copies a file the repo does not have fails its first build (a logged run: a uv.lock)
    lock_names = {n for v in LOCKS.values() for n in v}
    for df in [base / "Dockerfile"] + sorted(base.glob("*/Dockerfile")):
        if not df.is_file() or any(part in SKIP_DIRS for part in df.relative_to(base).parts):
            continue
        for line in df.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"(?i)^\s*(?:COPY|ADD)\s+(.+)$", line)
            if not m or "--from" in m.group(1):
                continue
            args = re.findall(r'"([^"]+)"', m.group(1)) if m.group(1).strip().startswith("[") else \
                [a for a in m.group(1).split() if not a.startswith("--")]
            for src in args[:-1]:
                if re.search(r"[*?$]|://", src) or (df.parent / src).exists() or (base / src).exists():
                    continue
                if pending and Path(src).name in lock_names:
                    continue
                gaps.append(f"{df.relative_to(base).as_posix()} copies {src}, which is not in the repo - its first "
                            f"build fails on it")
    return gaps


BUNDLE_LINE = re.compile(r"^>>>\s*(file|folders?):\s*(.*?)\s*$")


def bundle_entries(text: str) -> tuple[list[str], list[tuple[str, str]], list[str]]:
    """A scaffold bundle: `>>> folders: a/ b/` lines and `>>> file: <path>` lines, each file's content below its line."""
    folders: list[str] = []
    files: list[tuple[str, str]] = []
    bad: list[str] = []
    cur: str | None = None
    buf: list[str] = []

    def flush() -> None:
        if cur is not None:
            body = "\n".join(buf).strip("\n")
            files.append((cur, body + "\n" if body.strip() else ""))
    for line in text.splitlines():
        m = BUNDLE_LINE.match(line)
        if not m:
            if cur is not None:
                buf.append(line)
            elif line.strip():
                bad.append(f"a line before any `>>> file:` entry: {line.strip()[:60]!r}")
            continue
        flush()
        cur, buf = None, []
        if m.group(1) == "file":
            cur = m.group(2)
        else:
            folders += m.group(2).split()
    flush()
    return folders, files, bad


def bundle_path_problem(rel: str) -> str | None:
    r = rel.replace("\\", "/").strip()
    parts = [x for x in r.split("/") if x not in ("", ".")]
    if not parts or r.startswith("/") or re.match(r"^[A-Za-z]:", r) or ".." in parts:
        return f"{rel!r} is not a path inside the project"
    if parts[0] == ".git" or install_root("/".join(parts)):
        return f"{rel!r} is inside .git or the playbook's install"
    if len(parts) == 1 and parts[0] in ("PRODUCT.md", "STATUS.md"):
        return f"{rel!r} is the spine - `set structure filled` writes #Structure"
    return None


# ---- /structure P46: the script writes every starter file that does not depend on the product's decisions ---------
# A logged run typed 45 starter files (31,561 chars, ~25K output tokens) in its bundle; the root docs, the .gitignore
# base lines, the per-folder package files and their tests/ markers are the same in every project, so `scaffold` writes
# them from templates/ and STRUCTURE.md's own tables - the bundle keeps only what the product decided.
STARTER_DOCS = (("starter-CHANGELOG.md", "CHANGELOG.md"), ("starter-SECURITY.md", "SECURITY.md"),
                ("starter-CONTRIBUTING.md", "CONTRIBUTING.md"))
STARTER_IGNORE = {"": (".env", ".env.*", "!.env.example", ".env.bak", "*.env.local"),
                  "python": (".venv/", "__pycache__/", ".pytest_cache/", ".ruff_cache/", ".mypy_cache/"),
                  "node": ("node_modules/", "dist/", "coverage/")}
# folders that hold data, pages or other non-code files: never a Python package
STARTER_DATA_DIRS = {"prompts", "templates", "static", "assets", "locales", "labels", "fixtures", "migrations", "evals",
                     "public", "docs", "scripts", "alembic", "i18n", "translations"}
STARTER_CHECK = {"make": "`make check`", "just": "`just check`", "npm": "`npm run check`", "pnpm": "`pnpm run check`",
                 "yarn": "`yarn check`", "bun": "`bun run check`", "task": "`task check`", "poe": "`poe check`"}
TEST_FOLDERS = ("tests/", "test/", "__tests__/")


def structure_stack(base: Path, dev: str) -> str:
    """'python', 'node' or '' - which starter lines and package files fit the manifest the Dev tooling line names."""
    if re.search(r"(?i)\buv\b|poetry|pyproject|\bpip\b|python|ruff|pytest", dev or "") or (base / "pyproject.toml").exists():
        return "python"
    if re.search(r"(?i)package\.json|\bnpm\b|pnpm|yarn|\bbun\b|node|typescript", dev or "") or \
            (base / "package.json").exists():
        return "node"
    return ""


def structure_tree_notes(text: str) -> dict[str, str]:
    """STRUCTURE.md's fenced tree as {'app/questions/': 'its # note'} - full paths rebuilt from the indentation."""
    notes: dict[str, str] = {}
    for block in re.findall(r"```[^\n]*\n(.*?)```", text, re.S):
        stack: list[tuple[int, str]] = []
        for line in block.splitlines():
            m = re.match(r"^([\s|`+\-│├└─]*)([A-Za-z0-9._\-]+)/\s*(?:#\s*(.*))?$", line.rstrip())
            if not m or m.group(2) in (".", ".."):
                continue
            depth = len(m.group(1))
            stack = [(d, n) for d, n in stack if d < depth] + [(depth, m.group(2))]
            notes["/".join(n for _, n in stack) + "/"] = (m.group(3) or "").strip()
    return notes


def structure_map_dirs(text: str) -> tuple[dict[str, str], list[str]]:
    """The folders STRUCTURE.md's tables name, {path/: what it is for}, and the ## Modules paths: each module and its
    tests/, each folder home under ## Where decisions live, each folder under ## Where does a new file go? the tree
    draws."""
    def rows(heading: str) -> list[list[str]]:
        m = re.search(rf"(?ms)^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)", text)
        out = [[c.strip() for c in line.strip().strip("|").split("|")] for line in (m.group(1) if m else "").splitlines()
               if line.lstrip().startswith("|") and not set(line.strip()) <= set("|-: ")]
        return out[1:]  # the header row

    def folder(cell: str, bare: bool = False) -> str | None:
        """The cell's first backticked folder (`app/x/`); `bare`: a ## Modules path written without its slash."""
        tok = next((t for t in re.findall(r"`([^`\n]+)`", cell) if t.endswith("/") or
                    (bare and "/" in t and "." not in t.rsplit("/", 1)[-1])), None)
        return None if tok is None or re.search(r"[<>*{}\s:]", tok) or tok.startswith(("/", "..")) else \
            re.sub(r"^\./", "", tok).rstrip("/") + "/"

    def plain(cell: str) -> str:
        s = re.sub(r"`([^`]*)`", r"\1", cell).strip()
        return re.split(r"(?<=[.;])\s", s, maxsplit=1)[0].rstrip(".;") + "." if s and s != "-" else ""

    drawn = {Path(p).name for p in structure_tree_notes(text)}
    found: dict[str, str] = {}
    mods: list[str] = []
    for cells in rows("Modules"):
        mod = folder(cells[0], bare=True) if cells else None
        if mod:
            mods.append(mod)
            found.setdefault(mod, plain(cells[1]) if len(cells) > 1 else "")
            tests = next((folder(c) for c in cells[2:] if (folder(c) or "").startswith(mod) and
                          (folder(c) or "").endswith(TEST_FOLDERS)), None)
            found.setdefault(tests or mod + "tests/", f"Tests for {mod}.")
    for cells in rows("Where decisions live"):
        home = next((folder(c) for c in cells if folder(c)), None)
        if home:
            found.setdefault(home, plain(next((x for x in cells if folder(x) != home), "")))
    for cells in rows("Where does a new file go?"):
        f = folder(cells[0]) if cells else None
        if f and Path(f).name in drawn:
            found.setdefault(f, "")
    return found, mods


def structure_docstring(text: str) -> str:
    """A module docstring that fits a 79-column line."""
    import textwrap
    one = f'"""{text}"""'
    return one + "\n" if len(one) <= 79 else '"""' + "\n".join(textwrap.wrap(text, 76)) + '\n"""\n'


def structure_starters(base: Path, bundle_names: list[str], dev: str) -> list[str]:
    """Write what no product decision shapes, after the bundle: the root docs from templates/, the standard .gitignore
    lines, and for every folder STRUCTURE.md's tables name - the folder, its package file (Python: `__init__.py` with
    the table's one line, or the tree's note) or a README.md, and each module's tests/. A file the bundle wrote, or one
    already on disk, is kept."""
    smd = base / "STRUCTURE.md"
    text = smd.read_text(encoding="utf-8", errors="replace") if smd.is_file() else ""
    stack = structure_stack(base, dev)
    status_md = base / "STATUS.md"
    head = status_md.read_text(encoding="utf-8", errors="replace") if status_md.is_file() else ""
    product = (re.search(r"(?m)^# STATUS\s*[—-]\s*(.+?)\s*$", head) or [None, "this project"])[1]
    ai = bool(re.search(r"AI product:\s*yes", head))
    said: list[str] = []
    # the root docs
    runner = (structure_tools(dev or "").get("task runner") or ("",))[0].lower()
    check = next((v for k, v in STARTER_CHECK.items() if re.search(rf"\b{k}\b", runner)), "the task runner's `check` task")
    docs = []
    for tpl_name, dest in STARTER_DOCS:
        tpl = tool_file("templates", tpl_name)
        if tpl is None or (base / dest).exists() or dest in bundle_names:
            continue
        body = tpl.read_text(encoding="utf-8").replace("{product}", product).replace("{check}", check).replace(
            "{prompts}", "\n   Prompts are versioned YAML files, never inline in code." if ai else "")
        (base / dest).write_text(body, encoding="utf-8", newline="\n")
        docs.append(dest)
    if docs:
        said.append("from the playbook's templates: " + ", ".join(docs))
    # the .gitignore lines every project needs (added to the file, never replacing a line)
    gi = base / ".gitignore"
    have = gi.read_text(encoding="utf-8", errors="replace") if gi.is_file() else ""
    lines = {l.strip() for l in have.splitlines()}
    add = [l for l in STARTER_IGNORE[""] + STARTER_IGNORE.get(stack, ()) if l not in lines]
    pats = [l.strip() for l in (have + "\n" + "\n".join(add)).splitlines() if l.strip() and not l.startswith("#")]
    if ignored(pats, ".env.example"):  # an earlier `!.env.example` is overridden by a later `.env.*`
        add.append("!.env.example")
    if add:
        gi.write_text((have.rstrip("\n") + "\n" if have.strip() else "") + "\n".join(add) + "\n", encoding="utf-8",
                      newline="\n")
        said.append(f".gitignore: {len(add)} standard line(s) added")
    if not text:
        return said
    # the folders the map names, each with the one file that keeps it in git and says what goes there
    notes = structure_tree_notes(text)
    want, mods = structure_map_dirs(text)
    parents = {Path(p).parent.as_posix() for p in mods}
    root = parents.pop() + "/" if len(parents) == 1 and parents != {"."} else None
    for rel in notes:  # a module's sub-folders the tree draws (adapters/, guards/ ...): the check needs them on disk
        if any(rel.startswith(m) and rel != m for m in mods):
            want.setdefault(rel, "")
    if root:
        want.setdefault(root, "")
        for n in bundle_names:  # a folder the bundle writes Python into is a package too, up to the root
            parts = n.split("/")[:-1] if n.endswith(".py") and n.startswith(root) else []
            for i in range(root.count("/") + 1, len(parts) + 1):
                want.setdefault("/".join(parts[:i]) + "/", "")
    made = {"folder(s)": 0, "__init__.py": 0, "README.md": 0, ".gitkeep": 0}
    for rel in sorted(want, key=lambda p: (p.count("/"), p)):
        if bundle_path_problem(rel.rstrip("/")):
            continue
        d = base / rel
        if not d.is_dir():
            d.mkdir(parents=True, exist_ok=True)
            made["folder(s)"] += 1
        # a module's own row first, then the tree's note, then the other tables' line
        what = (want[rel] if rel in mods or rel.endswith(TEST_FOLDERS) else "") or notes.get(rel) or want[rel] or \
            next((v for k, v in notes.items() if k.endswith("/" + rel)), "")
        what = (what[:1].upper() + what[1:] if not re.match(r"\S*[./]", what) else what).rstrip(".") + "." if what else ""
        package = stack == "python" and not set(rel.strip("/").split("/")) & STARTER_DATA_DIRS and (
            (root is not None and rel.startswith(root)) or any(rel.startswith(m) for m in mods))
        if package:
            if not (d / "__init__.py").exists() and rel + "__init__.py" not in bundle_names:
                (d / "__init__.py").write_text(structure_docstring(what or rel), encoding="utf-8", newline="\n")
                made["__init__.py"] += 1
        elif not any(d.iterdir()):
            name = "README.md" if what and not rel.endswith(TEST_FOLDERS) else ".gitkeep"
            (d / name).write_text(f"# {Path(rel).name.capitalize()}\n\n{what}\n" if name == "README.md" else "",
                                  encoding="utf-8", newline="\n")
            made[name] += 1
    if any(made.values()):
        said.append("from STRUCTURE.md's tables: " + ", ".join(f"{n} {k}" for k, n in made.items() if n))
    return said


def scaffold(base: Path, src: Path, dev: str) -> str:
    """`status.py scaffold --from <bundle>`: every folder and starter file in ONE call. An existing .gitignore is added
    to, any other existing file kept; .gitattributes, the gitleaks config and scripts/check_structure.py come from the
    playbook (never written by the run: the checker's copy must equal the playbook's)."""
    if not src.is_file():
        raise Refused(f"scaffold: no bundle at {src} - write it first (outside the repo)")
    folders, files, bad = bundle_entries(src.read_text(encoding="utf-8"))
    bad += [pr for pr in (bundle_path_problem(x) for x in folders + [f for f, _ in files]) if pr]
    names = [re.sub(r"^(?:\./)+", "", f.replace("\\", "/")) for f, _ in files]
    bad += [f"{n!r} appears twice" for n in sorted({n for n in names if names.count(n) > 1})]
    if not files and not folders:
        bad.append("no `>>> folders:` or `>>> file:` line")
    if bad:
        raise Refused("scaffold: nothing written - " + "; ".join(dict.fromkeys(bad)) + ". The bundle: `>>> folders: "
                      "a/ b/` lines, then `>>> file: <path>` with the file's content below it")
    holders = {Path(f).parent.as_posix() for f in names if Path(f).name != ".gitkeep"}
    dropped = [f for f in names if Path(f).name == ".gitkeep" and Path(f).parent.as_posix() in holders]
    made, kept, merged = 0, [], 0
    for d in folders:
        (base / d).mkdir(parents=True, exist_ok=True)
    for (raw, body), rel in zip(files, names):
        if rel in dropped:
            continue
        f = base / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        if f.is_file() and f.name == ".gitignore":  # merge, never replace: a committed line stays
            have = f.read_text(encoding="utf-8", errors="replace")
            add = [l for l in body.splitlines() if l.strip() and l.strip() not in {x.strip() for x in have.splitlines()}]
            if add:
                f.write_text(have.rstrip("\n") + "\n" + "\n".join(add) + "\n", encoding="utf-8", newline="\n")
                merged += len(add)
            continue
        if f.exists():
            kept.append(rel)
            continue
        f.write_text(body, encoding="utf-8", newline="\n")
        made += 1
    copied = []
    for name, dest, when in (("gitattributes", base / ".gitattributes", True),
                             ("gitleaks.toml", base / ".gitleaks.toml", re.search(r"(?i)gitleaks", dev or "") and
                              not (base / "gitleaks.toml").exists())):
        tpl = tool_file("templates", name)
        if when and tpl is not None and not dest.exists():
            dest.write_bytes(tpl.read_bytes())
            copied.append(dest.name)
    engine = tool_file("templates", "check_structure.py")
    if engine is not None:  # a re-run replaces an older copy where it is
        dest = next((d / "check_structure.py" for d in [base, *project_dirs(base)] if (d / "check_structure.py").is_file()),
                    base / "scripts" / "check_structure.py")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(engine.read_bytes())
        copied.append(dest.relative_to(base).as_posix())
    starters = structure_starters(base, names, dev)  # after the copies: scripts/ already holds the check
    return "\n".join(
        [f"scaffold: wrote {made} file(s) and {len(set(folders))} folder(s) in one call"
         + (f" · .gitignore: {merged} line(s) added to the existing file" if merged else "")
         + (f" · from the playbook: {', '.join(copied)}" if copied else ""),
         *(f"  {s}" for s in starters),
         *([f"  kept {len(kept)} existing file(s), not overwritten: {', '.join(kept[:8])}"
            f"{' ...' if len(kept) > 8 else ''} - change one with the edit tool only if it must change"] if kept else []),
         *([f"  dropped .gitkeep in {len(dropped)} folder(s) that hold a file"] if dropped else []),
         "Next: make it run in ONE call - `status.py prove \"<lock>\" \"<install>\" \"<lint>\" \"<smoke test>\"` (the "
         "start printed the commands for this stack)"])


def prove(base: Path, cmds: list[str], today: str) -> tuple[int, str]:
    """`status.py prove "<cmd>" ...`: run the lock, install, lint and smoke-test commands in order, stop at the first
    failure, and print the evidence lines to paste (the script writes them: never a hand-typed result). No network on
    a failing command: the `lock pending` line instead - an accepted outcome, never a failure."""
    out: list[str] = []
    for c in cmds:
        try:
            r = subprocess.run(c, shell=True, cwd=base, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=900)
            text, code = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", (r.stdout or "") + "\n" + (r.stderr or "")), r.returncode
        except subprocess.TimeoutExpired:
            text, code = "timed out after 900 s", 124
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        last = lines[-1] if lines else f"exit {code}"
        if code == 0:
            out.append(f"evidence: {c} → {last[:160]} · {today}")
            continue
        # once an earlier command here succeeded (a logged `uv lock` resolved 119 packages) the network works: a
        # later download error is a real failure to fix, never `lock pending`
        net = None if out else next((l for l in lines if NO_NETWORK.search(l)), None)
        if net is not None:
            out.append(f"evidence: lock pending - no network ({net[:120]}) · {today}")
            out.append(f"  `{c}` could not reach the network: paste the line above into #Structure (the lockfile, the "
                       f"install, lint and the smoke test wait for /foundation); nothing else to do now")
            return 0, "Paste these lines into #Structure as they are:\n" + "\n".join(out)
        out.append(f"FAILED (exit {code}): {c}")
        out += [f"  {l[:200]}" for l in lines[-15:]]
        out.append("Fix what it names and run `status.py prove` again with the same commands.")
        return 1, "\n".join(out)
    return 0, "Paste these lines into #Structure as they are:\n" + "\n".join(out)


def structure_run_commands(dev: str) -> str:
    """The lock · install · lint · smoke-test commands for the manifest the Dev tooling line names."""
    lint = (re.search(r"(?i)\b(ruff|eslint|biome|flake8|pylint)\b", dev or "") or [None, ""])[1].lower()
    lint_py = {"ruff": "ruff check .", "flake8": "flake8", "pylint": "pylint app"}.get(lint, "ruff check .")
    for rx, cmds in ((r"\buv\b", ("uv lock", "uv sync", f"uv run {lint_py}", "uv run pytest tests/test_smoke.py -q")),
                     (r"poetry", ("poetry lock", "poetry install", f"poetry run {lint_py}",
                                  "poetry run pytest tests/test_smoke.py -q")),
                     (r"\bpnpm\b", ("pnpm install", "pnpm run lint", "pnpm exec vitest run tests/smoke.test.ts")),
                     (r"\byarn\b", ("yarn install", "yarn lint", "yarn vitest run tests/smoke.test.ts")),
                     (r"\bbun\b", ("bun install", "bun run lint", "bun test tests/smoke.test.ts")),
                     (r"package\.json|\bnpm\b", ("npm install", "npm run lint", "npx vitest run tests/smoke.test.ts")),
                     (r"\bcargo\b", ("cargo generate-lockfile", "cargo build", "cargo clippy -- -D warnings",
                                     "cargo test smoke")),
                     (r"pyproject", ("uv lock", "uv sync", f"uv run {lint_py}", "uv run pytest tests/test_smoke.py -q"))):
        if re.search(rf"(?i){rx}", dev or ""):
            return " ".join(f'"{c}"' for c in cmds)
    return '"<resolve the lockfile>" "<install from it>" "<the linter>" "<the smoke test>"'


# Production safeguards' bullets that decide a scaffolding file; the rest (AI security, rollout, budgets) belong to
# /architect and /build. `status.py rules structure` still prints every section whole.
STRUCTURE_SAFEGUARDS = ("Secrets never get pushed", "Placeholders must FAIL", "Tests never touch")
# the quality bar's bullets that decide a folder or a file; data paths and accessibility are /build's
STRUCTURE_BAR = ("Modular", "Layered", "Provider/adapter", "Intention-revealing", "Change safely")


CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".go", ".rs", ".java", ".kt", ".rb", ".php", ".cs", ".swift",
            ".vue", ".svelte", ".scala", ".ex", ".exs", ".dart", ".c", ".cpp", ".h"}


def structure_code(base: Path) -> list[str]:
    """Source files already in the project (docs and ADRs are not code): any = brownfield."""
    found = []
    for root, dirs, names in os.walk(base):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS]
        found += [n for n in names if Path(n).suffix in CODE_EXT]
        if found:
            return found
    return found


def structure_ref(name: str) -> Path | None:
    here = Path(__file__).resolve().parent
    return next((f for f in (here.parent / "commands" / "structure" / "references" / name,
                             here.parent / "skills" / "structure" / "references" / name) if f.is_file()), None)


def structure_rules_text(brownfield: bool, filled: bool, arch_empty: bool, spine: bool = False) -> str:
    """The rules this run applies, word for word: re-run and declined rules only when the run is one."""
    principles = rule_file("PRINCIPLES.md")
    safe = re.split(r"\n(?=- \*\*)", print_sections(principles, ["Production safeguards"]))
    safe = [b for b in safe if b.startswith("##") or any(b.startswith(f"- **{w}") for w in STRUCTURE_SAFEGUARDS)]
    bar = re.split(r"\n(?=- \*\*)", print_sections(principles, ["Architecture & quality bar"]))
    bar = [b for b in bar if b.startswith("##") or any(b.startswith(f"- **{w}") for w in STRUCTURE_BAR)]
    # §Status only where a bypass or a stop is recorded: the start's header already says how the close records it
    mech = ["Status"] * arch_empty + ["Spine resolution"] * (brownfield and not spine) + \
        ["Re-run semantics"] * filled + ["Declined runs"] * arch_empty
    root = structure_ref("root-scaffolding.md")
    return "\n\n".join(
        ["Rules for /structure, word for word from the rule files (these ARE the rule files for this phase - do not "
         "open them; `status.py rules structure` prints the sections whole):",
         "===== PRINCIPLES.md =====\n" + "\n".join(bar).rstrip() + "\n\n" + "\n".join(safe)]
        + (["===== MECHANISMS.md =====\n" + print_sections(rule_file("MECHANISMS.md"), mech)] if mech else [])
        + (["===== root-scaffolding.md (this skill's references/) =====\n" + root.read_text(encoding="utf-8").strip()] if root else []))


# the provenance tag /architect writes on each line: /structure derives from the decision, not from who chose it
PROVENANCE = re.compile(r"\s*(?:—|-)\s*`?_?(?:default taken, not user-chosen|user-chosen)[^`_]*_?`?\s*$")


def structure_blocks(base: Path) -> list[str]:
    """docs/architecture.md's `## Building blocks` table as `block what it is for` - the module names, so the run
    opens no architecture file to find them."""
    f = base / "docs" / "architecture.md"
    text = f.read_text(encoding="utf-8", errors="replace") if f.is_file() else ""
    m = re.search(r"(?ms)^##\s+(?:\d+[.)]\s*)?Building blocks\s*$(.*?)(?=^##\s|\Z)", text)
    rows = [l for l in (m.group(1) if m else "").strip().split("\n\n")[0].splitlines() if l.lstrip().startswith("|")]
    out = []
    for line in rows[2:]:  # the header and its divider
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2:
            what = cells[1].replace("`", "").split(";")[0]
            out.append(f"{cells[0]} {what if len(what) <= 70 else what[:70].rsplit(' ', 1)[0] + '…'}")
    return out


def structure_start_text(st: "Status") -> str:
    """`next --phase structure`: what decides every scaffolding file, what to write and what `set structure filled`
    refuses - one call, instead of PRINCIPLES.md, MECHANISMS.md and PRODUCT.md read whole (P1, P25)."""
    base = st.base if st.base is not None else Path(".")
    prod = base / "PRODUCT.md"
    secs = product_sections(prod.read_text(encoding="utf-8")) if prod.is_file() else {}
    arch_body = re.sub(r"<!--.*?-->", "", secs.get("Architecture", ""), flags=re.S).strip()
    arch = structure_fields(arch_body)
    values = "\n".join(arch.values())
    filled = st.state("structure") == "filled"
    out = ["/structure start (never read PRODUCT.md, PRINCIPLES.md or MECHANISMS.md whole - what this phase "
           "derives from is here):",
           f"  - Flags: UI {st.header.get('UI', 'unknown')} · AI product {st.header.get('AI product', 'unknown')} · "
           f"Agent {st.header.get('Agent', 'unknown')}"]
    top = sorted(d.name for d in base.iterdir() if d.is_dir() and d.name not in SKIP_DIRS
                 and not d.name.startswith(".") and d.name != "status")
    code = structure_code(base)
    out.append("  - The tree now: " + (f"top-level folders {', '.join(top)} - brownfield: propose the target layout + a "
                                       f"migration note, never move files blindly" if code else
                                       f"no code yet{' (folders: ' + ', '.join(top) + ')' if top else ''} - nothing "
                                       f"to probe; lay it out"))
    scope = scope_fields(re.sub(r"<!--.*?-->", "", secs.get("Scope", ""), flags=re.S))
    blocks = structure_blocks(base)  # /architect's blocks already split the in-scope list: then the core feature only
    core = [(k, " ".join(v)) for k, v in scope.items()
            if re.search(r"(?i)core feature" if blocks else r"(?i)core feature|^in[- ]scope", k)]
    if core:
        out.append("  - #Scope, the concerns that become modules:")
        out += [f"      {k}: {v[:220]}{'…' if len(v) > 220 else ''}" for k, v in core]
    if blocks:
        out.append("  - The module names - docs/architecture.md's `## Building blocks` (block: what it is for): "
                   + " · ".join(blocks))
    if not arch_body:
        out.append("  - #Architecture is EMPTY: warn \"/architect has not run - the tools and the runtime target are "
                   "undecided\" and offer /architect first. The user goes on: record it (`status.py set structure "
                   "declined ...` to stop, or carry on detecting the stack from the repo and record each tool you pick)")
    else:
        out.append("  - #Architecture, whole (it decides every scaffolding file; open an ADR only where a line points "
                   "into it):")
        out += ["      " + PROVENANCE.sub("", l) for l in arch_body.splitlines() if l.strip()]
        tools = structure_tools(next((v for k, v in arch.items() if re.match(r"(?i)dev tooling", k)), ""))
        want = [f"{slot}: {t[0]} → {t[1][0]}" for slot, t in tools.items() if t]
        if want:
            out.append("  - The Dev tooling line's files (scaffold exactly these; any other hook runner or task runner "
                       "is refused): " + " · ".join(want))
        homes = [f"{what} → {home}" for what, rx, home in STRUCTURE_HOMES if re.search(rx, values)]
        ports = sorted(set(STRUCTURE_PORT.findall(values)))
        if homes or ports:
            out.append("  - Decisions with a home on disk (a row each under `## Where decisions live`, the path "
                       "created now): " + " · ".join(homes + [f"`{p}` → its module's adapters/" for p in ports]))
    if st.header.get("Agent") == "yes":
        agent = Path(agent_rules())
        if agent.is_file():
            out.append("  - Agent: yes - AGENT.md §Structure, word for word (apply every row; folders created now):")
            out.append(print_sections(agent, ["Structure"]))
    engine = tool_file("templates", "check_structure.py")
    tpl = tool_file("templates", "PRODUCT.md")
    fields = product_sections(tpl.read_text(encoding="utf-8")).get("Structure", "") if tpl else ""
    dev = next((v for k, v in arch.items() if re.match(r"(?i)dev tooling", k)), "")
    out += [
        "  - THE ORDER (each call re-sends the whole conversation): 1. decide the shape, modules and homes; ask the "
        "user anything open - before any file · 2. ONE bundle, then `status.py scaffold --from <bundle>` · 3. ONE "
        "`status.py prove` · 4. ONE message: what was laid out, any Step 3c clash, the save question; a yes = ONE call, "
        "`status.py set structure filled --section-from <file> --commit \"<one line>\"`. NEVER run: a type checker, "
        "a secret-scan sweep, a separate lint, test or check_structure.py run, a second prove after a pass, a "
        "--dry-run before the save - prove and set run every check counted here.",
        f"  - STRUCTURE.md: the form is {struct_template_path()} (read in your first turn), sections in order: "
        + " · ".join(n for n, _ in STRUCT_DOC_SECTIONS) + ". Every `<...>` filled, every comment deleted, each "
        "header row kept exactly (a backticked `LLMProvider` is a name, not a path). Full sentences.",
        "  - The bundle: ONE file outside the repo, `>>> file: <path>` with the content below it (`>>> folders: a/ b/` "
        "only for a folder no table names) - what it holds and what `scaffold` writes itself: root-scaffolding.md "
        "below. ONE config loader, in the project's language, reading platform.yaml, product.yaml and .env, beside "
        "them or where STRUCTURE.md names it. Folders, config and empty modules only - product logic is /build's (a "
        "module file over 40 lines of code is refused). Never edit or run scripts/check_structure.py (`set` runs it).",
        "  - prove, ONE call: `status.py prove " + structure_run_commands(dev) + "` - a real lockfile, the install, "
        "the linter, the smoke test; it stops at the first failure (fix it, run it again) and prints the evidence "
        "lines; no network: a `lock pending` line instead.",
        "  - #Structure is these fields, labels as written, in a scratch file outside the repo, plus `evidence: python "
        "scripts/check_structure.py → <its last line> · STRUCTURE.md · <date>` and the lines `prove` printed:",
        *("      " + l for l in fields.splitlines() if l.startswith("- **")),
        "  - `set structure filled` refuses, every problem in one list - each exit criterion, plus: a check_structure "
        "failure (map vs tree, a placeholder test, a print-only task, a hook skipping the check) · a "
        "hook/task runner the Dev tooling line does not name · a `lint` task skipping its linter · a .gitignore that "
        "lost a committed line · two loaders · a stub lockfile · a Checks-you-run result no evidence line printed · "
        "a Dockerfile copying a missing file · a compose file the runtime target does not use · no `evidence:` line. "
        "It prints the rest of the close.",
    ]
    return "\n".join(out) + "\n\n" + structure_rules_text(bool(code), filled, not arch_body, prod.is_file())


# ---- /contracts (P1, P2, P4, P20, P37, P42-P45) -----------------------------------------------------------------
# Its Step 0 was four commands in one turn - next, `rules contracts` (27 KB: 17 sections, the close's among them),
# `refs contracts` (8 KB) and six PRODUCT.md sections (18 KB on a logged test project after /structure): ~60 KB in
# the conversation before any work, re-sent on each of a run's 60-90 calls. A replay on next.26 cost the same as
# next.25 - the calls Step 0 saved went to more test runs. The start prints what the contracts are built from, the
# order, the record's shape and what `set contracts filled` refuses; the close's rules come with `set`. `set
# contracts filled` names the record's gaps and an earlier phase's failing check in ONE refusal (they were three
# rounds), and `--dry-run` lists them all.
PHASE_RULES["contracts"] = {
    "PRINCIPLES.md": ["Per-feature contract", "Architecture & quality bar", "Documentation-driven", "Communication"],
    "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status", "Follow the pointer"],
}
PHASE_CLOSE_RULES["contracts"] = {
    "PRINCIPLES.md": ["The exit-criteria gate", "Reviews, vision & confidence"],
    "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"],
}
CLOSE_STEPS["contracts"] = (
    "every unit and number against #Architecture and #Vision: a run cap in the policy above #Vision's cost per use, "
    "a unit named one way in the code and another in #Architecture",
    "#Architecture (datastore · migrations approach · the externals) and #Scope - a table for an entity no scoped "
    "feature needs, a schema built outside the recorded migration path",
    "the record's paths, the migrations, the evidence lines, money types and values, the tenant key per table, the "
    "exported contract, the Agent rows and docs/contracts.md's shape")
START_HOLDS["contracts"] = ("the #Architecture, #Scope, #Structure and #Foundation\n    lines the contracts are "
                            "built from, the questions, the five steps and their proofs,\n    the #Contracts labels, "
                            "this phase's rules")
CONTRACTS_HEAD = (
    "This phase closes with ONE call - `status.py set contracts filled --section-from <file> --commit \"<one line>\"`, "
    "#Contracts in a scratch file outside the repo (never an edit tool on PRODUCT.md): it checks the record AND the "
    "code, names every gap at once (an earlier phase's failing check included), saves the project (leave `--commit` "
    "out when the user said not to save - no git call of your own) and prints the rest of the close. `--dry-run` "
    "instead of `--commit`: the same checks, nothing written - every rule they apply is printed below (P45).",
    "Commands work in PowerShell and in bash: one command per call - no &&, tail, grep or export; never `cd <path> &&`. "
    "An output over 30 lines goes to a file. The same command fails 3 times: stop and tell the user what fails. Plain "
    "symbols (≤ →), never LaTeX.",
    "No commit during the run: the one save at the close takes every change. A `Read:` line quotes each input file "
    "you opened beyond what `next` printed (an ADR, an existing model): `status.py quote <file> \"<words>\"` prints "
    "the line to paste.",
)
# P46: docs/contracts.md is the run's last write, after round 2's answer, saved in the same call - it was written
# before the dry-run and round 2 and re-sent on each of their calls. The dry-run before it prints its shape and checks
# (they left the start: printed when they are needed).
CONTRACTS_DOC_PENDING = (
    f"\n  {CONTRACTS_DOC} is not written yet, so its checks wait for the save. After round 2's looks-good, ONE "
    f"message: write it, then - in that same message, after it - `set contracts filled --section-from <file> --commit "
    f"\"<one line>\"` (no `--commit` on \"don't save yet\"). Its shape, "
    f"the reader's part first: `## Overview` (3-5 plain sentences, then ONE ```mermaid erDiagram: the tables, their "
    f"links, the tenant key) · `## Boundary units` (boundary · the unit both sides use · the test that proves it) · "
    f"`## PII` (a table: field · why kept · how long · deletion path) · then the workings: "
    f"`## Owner's answers` (round 1, word for word) · `## Versioning` and the rest. The save refuses it missing, not starting with the Overview and its diagram, or with no PII table or "
    f"Owner's answers. Never re-read what you wrote: `set` checks it.")
# PRINCIPLES.md §Production safeguards, the bullets the data's shape decides (~1.6 of 3.2 KB)
CONTRACTS_SAFEGUARDS = ("Security baseline", "Tests never touch", "AI-specific security", "Observability & audit",
                        "Rollout safety")
# the #Architecture rows a contract is built from, per kind, at most n each
CONTRACTS_ARCH = (("Stack + tools", r"(?i)^(?:language|(?:web |agent )?framework|datastore|database|orm)\b", 5),
                  ("Externals", r"\S", 8), ("Resilience", r"(?i)migrat|budget", 2), ("Identity custody", r"\S", 1))


# Printed by name in the start, whole by `status.py rules contracts` (P47: the realistic start was 31K, over Claude
# Code's 30K cut): §Declined runs and §Re-run semantics fire only on a stop or a re-run; Per-feature contract's
# evidence rule is verify.md §Evidence lines and its boundary map is step 4; Follow the pointer's duty here is the
# `Read:` quote (the head) - its binding force is on the phases that read #Contracts; §Status's part here is one
# sentence (the head carries the close's command).
CONTRACTS_BY_NAME = {"Declined runs": "before stopping or skipping this phase",
                     "Per-feature contract": "its evidence and boundary rules are verify.md and step 4 above",
                     "Documentation-driven": "its record rule is the #Contracts shape above: a decision, an evidence "
                                             "line or a pointer per field, the reasoning in docs/contracts.md",
                     "Follow the pointer": "the `Read:` quote above is its part for this phase",
                     "Status": "STATUS.md is written only by status.py, never by hand, and no state line goes into "
                               "PRODUCT.md; any other moment: `status.py how`"}


def contracts_rules_text(st: "Status") -> str:
    """The start's rules: spine resolution only without a PRODUCT.md; §Declined runs only while an earlier gate is
    unmet; the CONTRACTS_BY_NAME sections by name; the safeguard bullets this phase decides; §Context hygiene (a long
    phase: most of its tokens are re-sent output) without its history paragraph."""
    base = st.base if st.base is not None else Path(".")
    skip = {"Spine resolution"} if (base / "PRODUCT.md").is_file() else set()
    skip |= set(CONTRACTS_BY_NAME)
    if not all(st.state(p) in ("filled", "overridden") for p in ("architect", "structure", "foundation")):
        skip.discard("Declined runs")
    if st.state("contracts") not in ("filled", "overridden"):
        skip.add("Re-run semantics")  # its trigger cannot fire
    named = [f"§{s} ({why})" for s, why in CONTRACTS_BY_NAME.items() if s in skip]
    named = named or ["nothing more"]
    want = {k: [s for s in v if s not in skip] for k, v in PHASE_RULES["contracts"].items()}
    # its history paragraph is no rule; items 2-3 (a progress line per step, the open decisions asked first) are
    # the start's order and round 1 - the rest word for word
    hygiene = re.sub(r"(?s)\*\*Why this exists\.\*\*.*?\n\n", "",
                     print_sections(rule_file("MECHANISMS-ON-DEMAND.md"), ["Context hygiene"]))
    hygiene = re.sub(r"(?s)\n2\. \*\*One progress line.*?(?=\n4\. )",
                     "\n(items 2-3, a progress line per step and the open decisions asked first: the order and round 1 "
                     "above)", hygiene)
    return (rules_text(want, "Rules for /contracts, word for word from the rule files (these ARE the rule files for "
                             "this phase - do not open them; `status.py rules contracts` prints them again, with "
                             + " · ".join(named) + "; the close's rules come with `set contracts filled`):")
            + "\n\n===== PRINCIPLES.md §Production safeguards - the bullets /contracts decides =====\n"
            + principle_bullets("Production safeguards", CONTRACTS_SAFEGUARDS) + "\n\n" + hygiene)


def contracts_start_text(st: "Status") -> str:
    """`next --phase contracts`: the spine lines the contracts are built from, the questions, the order, the five
    steps and their proofs, the record's shape and what `set contracts filled` refuses - one call."""
    base = st.base if st.base is not None else Path(".")
    prod = base / "PRODUCT.md"
    secs = product_sections(prod.read_text(encoding="utf-8")) if prod.is_file() else {}
    clean = {k: re.sub(r"<!--.*?-->", "", v, flags=re.S) for k, v in secs.items()}

    def cut(s: str, n: int = 220) -> str:
        s = " ".join(s.split())
        return s if len(s) <= n else s[:n] + "…"

    out = ["/contracts start - never read PRODUCT.md, the rule files, AGENT.md or this skill's reference files whole "
           "(what this phase needs from them is here):"]
    arch = clean.get("Architecture", "")
    rows = lambda label: [re.sub(r"^[-*+|\s]+", "", l).strip() for l in field(arch, label).splitlines()  # noqa: E731
                          if l.strip() and not l.strip().startswith("|--")]
    picked: list[str] = []
    for label, rx, n in CONTRACTS_ARCH:
        picked += [r for r in rows(label) if re.search(rx, r) and r not in picked][:n]
    if picked:
        out.append("  - #Architecture (each external is a boundary; the datastore and migrations approach are fixed - "
                   "a clash is Step 3c, never a silent change):")
        out += [f"      {cut(r)}" for r in picked]
    else:
        out.append("  - #Architecture is empty: warn - the datastore and the migrations approach come from it (Step 0)")
    scope = scope_fields(clean.get("Scope", ""))
    core = [l for k, v in scope.items() if re.search(r"core feature|^in[- ]scope", k, re.I) for l in v][:8]
    out += (["  - #Scope (model only what these need; an entity no scoped feature needs is a Step 3c conflict):"]
            + [f"      {cut(l)}" for l in core] if core else ["  - #Scope is empty: warn and offer /scope first"])
    struct = field(clean.get("Structure", ""), "Folder")
    out.append(f"  - #Structure (STRUCTURE.md holds the whole map): {cut(struct, 420)}" if struct.strip() else "  - #Structure is empty: warn (Step 0)")
    out.append("      A folder this phase adds (docs/contracts/, a schemas folder) goes into STRUCTURE.md's map in the "
               "same message - #structure's check refuses a folder the map does not draw.")
    test_db = field(clean.get("Foundation", ""), "Isolated test datastore")
    out.append(f"  - #Foundation's test datastore: {cut(test_db)}" if test_db.strip() else
               "  - #Foundation records no test datastore: warn - migrations need one to run on (Step 0); the user "
               "goes on -> record the override")
    status = base / "STATUS.md"
    items = [o for o in (Status.load(status).rows["Open items"] if status.is_file() else [])
             if not o[5] and re.search(r"(?i)contract|schema|migrat|retention|tenant", o[3] + o[4])]
    spine = [cut(l.strip().lstrip("-* "), 200) for k in ("Scope", "Plan", "Architecture", "Structure", "Foundation")
             for l in clean.get(k, "").splitlines() if re.search(r"/contracts\b", l)]
    ui, ai, agent = (st.header.get(k, "unknown") for k in ("UI", "AI product", "Agent"))
    out.append(f"  - Flags: UI {ui} · AI product {ai} · Agent {agent}")
    out += ["  - Round 1 - ONE message, numbered as written, each with 2-4 ready choices ((Recommended) first) and "
            "room for their own words; an answer the lines above already give is shown to confirm, never asked "
            "blank. These are the owner's - never decided for them:",
            "      1. Who calls it from outside the app - nothing · a webhook another service sends · a public API · a "
            "client in another repo? (nothing: the versioning field says `N/A — <reason>`; else an exported contract "
            "file + /v1 additive-only)",
            "      2. Whose data is kept apart from whose - the tenant/owner key (per customer company · per user · one "
            "user only: N/A)?",
            "      3. How long is each kind of personal data kept, and how is it deleted (a number of months, or until "
            "the user deletes it)?",
            "      4. Only if money moves or is capped: the currency, stored as integer minor units (Recommended) or a "
            "fixed decimal?"]
    n = 5
    for o in items:
        out.append(f"      {n}. open item {o[0]} (from /{o[2]}): {cut(o[3], 160)} - clears when {cut(o[4], 100)}")
        n += 1
    for l in spine[:6]:
        out.append(f"      {n}. left for /contracts in the spine: {l}")
        n += 1
    out += ["    Each answer goes word for word under `## Owner's answers` in docs/contracts.md. After it, run "
            "unattended - say so; a question asked mid-run stalls the rest behind it.",
            # P46: each call re-sends everything before it - reads and questions first, the long document last
            "  - Then, in order - reads first, the long document last: every file you need to read (an ADR, an "
            "existing model) in ONE call now · the five steps below (one line printed as each lands) · their proofs "
            "(`evidence:` lines) · the section file and `set contracts filled --section-from <file> --dry-run` in ONE "
            "message - fix every gap it lists · round 2: ONE message - a table of what was frozen (table · tenant key "
            "· units · personal data kept how long · contract file), any clash with #Architecture or #Scope (Step "
            "3c), then one question: \"Looks good - save (Recommended)\" · \"Looks good - don't save yet\" · "
            "\"Change something\" · on a looks-good, ONE message: docs/contracts.md (the dry-run prints its shape) "
            "and, after it in that same message, `set contracts filled --section-from <file> --commit \"<one "
            "line>\"` (no `--commit` on \"don't save yet\").",
            "  - What this phase must NOT do: no product logic - a declared route returns 501 until /build; no edit "
            "of a migration that has run (add a new one); no change to a decision #Architecture recorded (a clash is "
            "Step 3c); no commit before the close."]
    here = Path(__file__).resolve().parent
    refs = next((d for d in (here.parent / "commands" / "contracts" / "references",
                             here.parent / "skills" / "contracts" / "references") if d.is_dir()), None)
    for name in ("contract-steps.md", "verify.md"):
        f = refs / name if refs else None
        if f is not None and f.is_file():
            # its title and `>` note say how it is printed - not a rule, so not re-sent on every call
            body = f.read_text(encoding="utf-8")
            out += ["", f"===== this skill's {name} - word for word; do not open it ====="]
            out.append(body[body.index("\n## "):].strip() if "\n## " in body else body.rstrip())
    tpl = tool_file("templates", "PRODUCT.md")
    labels = product_sections(tpl.read_text(encoding="utf-8")).get("Contracts", "") if tpl else ""
    out += ["", "  - #Contracts is these fields, labels as written, in a scratch file outside the repo; each field a "
                "decision, the paths in backticks, an `evidence:` line under it; nothing to record: `N/A — <reason>`:"]
    out += ["      " + l for l in labels.splitlines() if l.startswith("- **")]
    out += ["  - `set contracts filled` refuses, every problem in one list: each refusal the steps and proofs above "
            "name (no migration file, or app code that builds the schema · money as a float · a table without the "
            "tenant key · no evidence line that ran a migration · a cited file or `file::test` that is not there) · a "
            "path #Contracts names that does not exist · no "
            "exported contract file named, unless the versioning field says N/A · "
            + ("an (Agent) row missing by name (tool schemas · action policy · model output · trace · hand-off · "
               "eval case) · " if agent == "yes" else "")
            + f"{CONTRACTS_DOC}'s shape (the dry-run prints it) · an earlier filled phase whose check fails now · a "
            "Read quote not found in its file.",
            "  - `set contracts filled` prints the rest of the close and the git facts for the save."]
    if agent == "yes" or (ai != "no" and agent == "unknown"):
        rules = Path(agent_rules())
        if rules.is_file():
            out += ["", "===== AGENT.md §Contracts - "
                        + ("applies only if the AI acts on its own (ask it in round 1); " if agent != "yes" else "")
                        + "record every row; do not open the file =====", print_sections(rules, ["Contracts"])]
    return "\n".join(out) + "\n\n" + contracts_rules_text(st)


# ---- /tickets (P1 P2 P20 P25 P37 P41 P43 P45) ----------------------------------------------------------------------
# A logged Claude /tickets run took 38 calls and 6.84M tokens re-read: PRINCIPLES.md and MECHANISMS.md whole, five
# section reads, a 33K-character grep of the contract files re-sent on ~30 later calls, three calls to find the
# templates, a verify.py of its own, a lookup of the open-item command and a commit the hook refused - and it read
# "proceed with the list" as a yes to two decisions it never asked. Step 0 then grew to four commands printing ~88 KB.
# The start now prints what the backlog derives from (#Plan, #Scope's lines, the names the contract files define, the
# lanes), the two question rounds, the record's shape and the refusal list; `set tickets filled --commit` checks
# docs/issues/ and TICKETS.md in code - every problem in one list - saves, and prints the close.
PHASE_RULES["tickets"] = {
    "PRINCIPLES.md": ["Per-feature contract", "Architecture & quality bar"],
    "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status"],
}
PHASE_CLOSE_RULES["tickets"] = {"PRINCIPLES.md": ["The exit-criteria gate"],
                                "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"]}
CLOSE_STEPS["tickets"] = (
    "every number this phase introduced (a ticket count, a seat count, a date) against #Plan's milestones and dates",
    "#Plan's milestones, #Scope's non-goals and the names the contract files define - a ticket that builds a non-goal, "
    "or names a type no contract defines",
    "every ticket's files, lane, owner, security line, Depends On, consumed names, shared files, strategy and Demo, "
    "every milestone, and TICKETS.md's lanes, graph and day-1 table")
TICKETS_HEAD = (
    "This phase closes with ONE call - `status.py set tickets filled --commit \"<one line>\"`, after the ticket files "
    "and TICKETS.md are written (no --section-from: /tickets writes no PRODUCT.md section, its record is "
    "docs/issues/*.md + TICKETS.md): it checks every ticket and the plan, names every problem at once, saves the "
    "project (no git call of your own) and prints the rest of the close. To see the gaps first, add `--dry-run`: the "
    "same checks, nothing written. Every rule they apply is printed below - the scripts' source says nothing more (P45).",
    "Commands work in PowerShell and in bash: one command per call - no &&, tail, grep or export; never `cd <path> &&`. "
    "The same command fails 3 times: stop and tell the user what fails. Plain symbols (≤ →), never LaTeX.",
    "No commit during the run: the one save at `set` takes every change and leaves the playbook's install out.",
    "This phase writes docs/issues/*.md, TICKETS.md and the two .github templates - never product code, a spine "
    "section or another doc (a logged run edited a module docstring and STRUCTURE.md mid-run, and the hook refused "
    "its commit): a mismatch you find goes in the close, for the phase that owns it (P44).",
    "Two question rounds, each ONE message (round 1: the numbered questions below; round 2: the whole proposal) - "
    "never answer a question for the user; a reply that skips one is asked again, never read as a yes.",
)
TICKET_SKIP = SKIP_DIRS | {"htmlcov"}
TICKETS_INLINE = 28000  # characters of the whole `next --phase tickets` output; Claude Code shows 30,000
TICKET_SPINE = re.compile(r"`(?:\./)?(PRODUCT|CHANGELOG|STRUCTURE|TICKETS|STATUS)\.md`")


def tickets_ref(name: str) -> Path | None:
    here = Path(__file__).resolve().parent
    return next((f for f in (here.parent / "commands" / "tickets" / "references" / name,
                             here.parent / "skills" / "tickets" / "references" / name, here / "tickets" / name)
                 if f.is_file()), None)


def ticket_sources(base: Path) -> list[Path]:
    """The project's own files a consumed name may live in - never an installed library or the playbook's install
    (the shared SKIP_DIRS lost .venv and .git in a later edit: every name in site-packages then 'existed')."""
    out = []
    for dirpath, dirnames, files in os.walk(base):
        dirnames[:] = [x for x in dirnames if x not in TICKET_SKIP and not x.endswith(".egg-info")]
        out += [Path(dirpath) / f for f in files if Path(f).suffix.lower() in SYMBOL_SOURCES]
    return out


def contract_paths(base: Path, body: str) -> tuple[list[str], list[str]]:
    """The files #Contracts names: (on disk, missing). A path with a wildcard or a folder is not a file claim."""
    names = dict.fromkeys(p.strip("/") for p in re.findall(r"`([^`\s*]+\.[A-Za-z]{1,5})`", body)
                          if "/" in p or (base / p).exists())
    return [p for p in names if (base / p).is_file()], [p for p in names if not (base / p).exists()]


def py_contract_names(src: str) -> str:
    """One line of names a ticket may consume: classes with their fields, functions with their route, tables with
    their columns, module constants. A logged run grepped these into a 33K-character file and re-sent it ~30 times."""
    import ast
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return "(does not parse)"
    out = []
    for n in tree.body:
        if isinstance(n, ast.ClassDef):
            inner = [b.target.id for b in n.body if isinstance(b, ast.AnnAssign) and isinstance(b.target, ast.Name)]
            inner += [t.id for b in n.body if isinstance(b, ast.Assign) for t in b.targets if isinstance(t, ast.Name)
                      and t.id != "model_config"]
            inner += [b.name + "()" for b in n.body if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef))
                      and not b.name.startswith("_")]
            out.append(n.name + (f"({', '.join(inner)})" if inner else ""))
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("_"):
            route = next((f" [{d.func.attr.upper()} {d.args[0].value}]" for d in n.decorator_list
                          if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.args
                          and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value, str)), "")
            out.append(f"{n.name}(){route}")
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                if not isinstance(t, ast.Name) or t.id.startswith("_") or t.id in ("router", "metadata", "logger"):
                    continue
                v = n.value
                if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "Table":
                    cols = dict.fromkeys(str(a.args[0].value) for a in v.args[1:] if isinstance(a, ast.Call) and a.args
                                         and isinstance(a.args[0], ast.Constant))
                    out.append(f"{t.id}(table: {', '.join(cols)})")
                else:
                    out.append(t.id)
    return " · ".join(out)


# #Plan fields a backlog is not sliced from: re-sent on every call of the run, read by none of its steps
PLAN_SKIP = re.compile(r"(?i)^- \*\*(?:four[- ]risks|usability checkpoint|north[- ]star|concern[- ]area|detail|read)\b")


def plan_for_tickets(plan: str) -> str:
    out, skip = [], False
    for line in plan.splitlines():
        if re.match(r"^- ", line):
            skip = bool(PLAN_SKIP.match(line))
        elif not line.startswith(" "):
            skip = False
        if not skip:
            out.append(line)
    return "\n".join(out)


def contract_names_text(base: Path, files: list[str], cap: int = 300) -> list[str]:
    out = []
    for p in files:
        if p.startswith("migrations/") or TICKET_SPINE.fullmatch(f"`{p}`"):  # tables, never a migration's internals
            continue
        if not p.endswith(".py"):
            out.append(f"      {p}")
            continue
        line = py_contract_names((base / p).read_text(encoding="utf-8", errors="replace"))
        out.append(f"      {p}: {line[:cap]}" + (" … (more: open the file by line range)" if len(line) > cap else ""))
    return out


def tickets_rules_text(filled: bool, gate: bool, whole: bool = False) -> str:
    """The rules this run applies, word for word: re-run and declined rules only when the run is one. The start
    leaves out the principles the skill's header names and the spine resolution the start itself does; `rules
    tickets` (whole) prints them too."""
    mech = PHASE_RULES["tickets"]["MECHANISMS.md"] if whole else ["Re-run semantics"] * filled + ["Declined runs"] * gate
    slicing, plan_md = tickets_ref("slicing.md"), tickets_ref("tickets-md.md")
    parts = ["Rules for /tickets, word for word from the rule files and this skill's references (these ARE the files "
             "for this phase - do not open them; `status.py rules tickets` prints them with the principles):",
             *(["===== PRINCIPLES.md =====\n" + print_sections(rule_file("PRINCIPLES.md"),
                                                             PHASE_RULES["tickets"]["PRINCIPLES.md"])] if whole else []),
             *(["===== MECHANISMS.md =====\n" + print_sections(rule_file("MECHANISMS.md"), mech)] if mech else [])]
    if slicing:
        parts.append(f"===== {slicing.as_posix()} (§Vertical slicing, §Horizontal slicing and §Per-ticket content: "
                     f"`status.py section <this path> \"<§>\"` - the template below carries the per-ticket fields) "
                     f"=====\n" + print_sections(slicing, ["§Lanes are modules", "§Epics", "§Waiting or building against",
                                                          "§Choose the strategy", "§Size by behaviour"]))
    if plan_md:
        parts.append(f"===== {plan_md.as_posix()} =====\n" + print_sections(plan_md, ["§The sections", "§The flow graph",
                                                                                  "§Day 1"]))
    return "\n\n".join(parts)


def tickets_start_text(st: "Status", lead: int = 0) -> str:
    """`next --phase tickets`: what the backlog derives from, the two question rounds, the record's shape and what
    `set tickets filled` refuses - one call, instead of four commands, the schema files and the references (P1, P25).
    `lead`: the characters `next` printed above it (its notes vary with the project's open items)."""
    base = st.base if st.base is not None else Path(".")
    prod = base / "PRODUCT.md"
    secs = product_sections(prod.read_text(encoding="utf-8")) if prod.is_file() else {}
    clean = lambda s: re.sub(r"<!--.*?-->", "", s, flags=re.S).strip()  # noqa: E731
    plan, contracts = clean(secs.get("Plan", "")), clean(secs.get("Contracts", ""))
    filled = st.state("tickets") == "filled"
    adhoc = tickets_ref("adhoc-capture.md")
    out = ["/tickets start (never read PRODUCT.md, STRUCTURE.md, PRINCIPLES.md, MECHANISMS.md, the contract files or "
           "the skill's references whole - what the backlog derives from is here):",
           f"  - Mode: no argument or a planning phrase -> Mode A, this start. A described bug, gap or debt item -> Mode "
           f"B: `status.py section {adhoc.as_posix() if adhoc else 'references/adhoc-capture.md'} intro` and its "
           f"sections are the whole procedure; nothing below applies. Unsure which -> ask, never regenerate a backlog."]
    gates = [p for p, sec in (("plan", plan), ("contracts", contracts))
             if st.state(p) not in ("filled", "overridden") or not sec]
    for p in gates:
        out.append(f"  - GATE: #{p.capitalize()} is {st.state(p)}{'' if secs.get(p.capitalize(), '').strip() else ' and empty'} - "
                   f"tickets would {'have no milestones' if p == 'plan' else 'invent their own types'}. Ask in ONE "
                   f"message: \"/{p} has not run. Run /{p} first (Recommended), or go on - then type your reason in "
                   f"your own words.\" Stop -> `status.py set tickets declined --reason \"<what was missing>\" --gate "
                   f"{p}`, no ticket files. Go on -> `status.py bypass --from tickets --gate {p} --reason \"<the user's "
                   f"reply, as typed>\"` - never a reason in your words (a logged run wrote its own).")
    have, missing = contract_paths(base, contracts)
    if missing:
        out.append(f"  - STOP: #Contracts names files that do not exist ({', '.join(missing[:8])}) - that is drift, not "
                   f"a missing section: say so and offer /contracts; no ticket names a type from a file that is gone.")
    folder = base / "docs" / "issues"
    old = sorted(f.name for f in folder.glob("*.md")) if folder.is_dir() else []
    epics: dict[str, int] = {}
    for f in old:
        m = re.match(r"^(M\d+-[A-Z0-9]+)-(\d+)", f)
        if m:
            epics[m.group(1)] = max(epics.get(m.group(1), 0), int(m.group(2)))
    if old or (base / "TICKETS.md").is_file() or filled:
        out.append(f"  - A re-run ({len(old)} file(s) in docs/issues/; TICKETS.md {'exists' if (base / 'TICKETS.md').is_file() else 'missing'}): "
                   f"keep every epic code, a new ticket takes the next number, skip a ticket that exists, rewrite "
                   f"TICKETS.md from the confirmed proposal (publishing.md §An earlier backlog)."
                   + (" Epics and their last number: " + " · ".join(f"{e}-{n:02d}" for e, n in sorted(epics.items()))
                      if epics else "")
                   + (" docs/issues/README.md remains from an earlier backlog: migrate its plan into TICKETS.md and delete it."
                      if (folder / "README.md").is_file() else ""))
    if plan:
        out.append("  - #Plan (each milestone becomes epics; a milestone with no ticket gets one line in TICKETS.md: "
                   "'<M>: no tickets - <why>', e.g. a phase that owns it; the risks, checkpoint, detail and Read "
                   "fields left out):")
        out += ["      " + l for l in plan_for_tickets(plan).splitlines() if l.strip()]
    scope = scope_fields(clean(secs.get("Scope", "")))
    keep = [(k, " ".join(v)) for k, v in scope.items() if re.search(r"(?i)core feature|non[- ]goal", k)]
    if keep:
        out.append("  - #Scope (Step 3c: no ticket builds a non-goal):")
        out += [f"      {k}: {v[:500]}{'…' if len(v) > 500 else ''}" for k, v in keep]
    if have:
        out.append("  - The names the contract files define - a ticket's Consumes uses these exact names, backticked; a "
                   "name the ticket itself creates is marked `(new)`; `set` refuses any other:")
        out += contract_names_text(base, have)
    structure = (base / "STRUCTURE.md").read_text(encoding="utf-8") if (base / "STRUCTURE.md").is_file() else ""
    for name in ("Modules", "Hub files"):
        m = re.search(rf"^## {name}\s*$(.*?)(?=^## |\Z)", structure, re.M | re.S)
        if m:
            out.append(f"  - STRUCTURE.md ## {name}" + (" (one lane per module, named after its folder):"
                                                        if name == "Modules" else ":"))
            out += ["      " + l for l in clean(m.group(1)).splitlines() if l.strip()]
    if structure and not re.search(r"\bissues/", structure):  # the structure check `set` runs refuses an undrawn folder
        out.append("  - STRUCTURE.md does not draw docs/issues/ yet: in the turn that writes the tickets, add "
                   "`issues/  # one file per ticket, written by /tickets` under docs/ in its tree and one dated line "
                   "under ## Changes - the only STRUCTURE.md edit this phase makes (a logged run's save was refused "
                   "for it).")
    remote = git(base, "remote", "get-url", "origin")
    out.append(f"  - Remote: origin = {remote} - round 1 asks whether to publish; publish.py checks `gh` and its scopes "
               f"before writing anything" if remote else
               "  - Remote: none - local files only; say so in the close, never `gh repo create`, ask no publish question")
    tpl, pr = tool_file("templates", "feature_ticket_template.md"), tool_file("templates", "pull_request_template.md")
    copies = [f"`cp {src.as_posix()} {dst}`" for src, dst in ((tpl, ".github/ISSUE_TEMPLATE/feature_ticket.md"),
                                                               (pr, ".github/PULL_REQUEST_TEMPLATE.md"))
              if src and not (base / dst).is_file()]
    if copies:
        out.append("  - Templates missing - copy them in the turn that writes the tickets (make .github/ISSUE_TEMPLATE/ "
                   "first): " + " · ".join(copies))
    lanes = sorted({m.group(1).strip("/").rsplit("/", 1)[-1] for m in re.finditer(
        r"^\|\s*`([^`]+)`", (re.search(r"^## Modules\s*$(.*?)(?=^## |\Z)", structure, re.M | re.S) or [None, ""])[1]
        if structure else "", re.M)})
    out += [
        "  - Round 1 - ask these in ONE message, numbered as written, each with your recommendation, before any proposal:",
        f"      1. Who builds: how many seats side by side on day one (1, or 2-10), each a person, an agent, or an agent "
        f"a person operates (who reviews its PRs)? Pre-fill from #Plan's capacity line (\"2 developers x 15 h - still "
        f"right?\"); {len(lanes) or 'the'} lanes - say how many can start at once.",
        "      2. The slicing strategy per milestone - one line per milestone with your recommendation (vertical unless "
        "the milestone has no user-visible surface): keep or switch? (The invocation named one: skip this question.)",
        "      3. Owners: Senior on every lane (Recommended), or name the lanes a Junior owns.",
        *(["      4. Publish to GitHub: issues + Delivery Board (Recommended) · issues only, no board · local files only."]
          if remote else []),
        f"      {5 if remote else 4}. One question per decision a ticket needs that no section records (where a field "
        f"comes from, who flips a switch), with your recommendation - never decided silently (a logged run read "
        f"\"proceed\" as a yes to two it never asked). None: say so in one line.",
        "  - Round 2 - ONE message: the whole proposal - milestone → epic → ticket, every ticket `ID · title · lane · "
        "owner · depends on · builds against`, every title with \"and\" flagged, the parallel table and the day-1 rows - "
        "then two options: \"Looks good - write and save\" / \"Change something\". A change -> show the changed list "
        "and ask again. That yes is the save: no third question.",
        "  - After the yes, few calls: the templates (if missing), every ticket file and TICKETS.md (several per call), "
        "then `status.py set tickets filled --commit \"tickets: <n> tickets in <e> epics across <l> lanes\"`; a "
        "refusal names every problem once - fix them all, run it again. Order (each call re-sends all before it): "
        "the ticket files and TICKETS.md are the last writes - nothing read or run between the yes and them, no "
        "check of your own after them (`set` checks every file).",
        "  - Each ticket: docs/issues/<ID>_<slug>.md, ID = M<n>-<EPIC>-<nn> (EPIC: an uppercase code unique in its "
        "milestone, never SLICE, TICK or ADHOC), no front matter, the template's headings as written (shown below "
        "without its comments). Field rules: Epic `[M<n>-<EPIC>] <name>` · Lane = one module, every ticket of an epic "
        "in its lane · Owner = Senior unless round 1 named a Junior lane · Target Files = one backticked file per line, "
        "everything /build will write: code, its tests, `docs/features/<feature>.md` · Consumes / Exposes = backticked "
        "names, `(new)` before a name this ticket creates · Depends On = the IDs whose merge it waits for, or None · "
        "Builds Against = the IDs whose contract it uses before they merge, or None · Demo = what a reviewer sees "
        "working after the merge (vertical: never n/a) · the DoD keeps every security line.",
        *(["      " + l for l in re.sub(r"<!--.*?-->\n?", "", tpl.read_text(encoding="utf-8").split("\n---\n", 1)[-1],
                                       flags=re.S).strip().splitlines() if l.strip()] if tpl else []),
        "  - `set tickets filled` refuses, every problem in one list: no ticket files · a ticket file not named "
        "<ID>_<slug>.md · one ID in two files · front matter · not exactly one Slice Strategy ticked · no exact target "
        "file (a file with its extension, never a folder) · PRODUCT/CHANGELOG/STRUCTURE/TICKETS/STATUS.md in Target "
        "Files · no docs/features/<feature>.md, or no test file in a ticket that is not docs-only · a lane that is no STRUCTURE.md module · "
        "no Owner · no security line in the DoD · a vertical slice with no Demo · a Depends On that does not exist, or a "
        "cycle · a consumed name the code does not have (mark a name the ticket creates `(new)`) · two tickets of one "
        "milestone writing the same file with no Depends On between them (order them, or list the file under "
        "TICKETS.md ## Hub files) · a #Plan milestone with no ticket and no reason in TICKETS.md · no TICKETS.md, no "
        "Mermaid graph, a lane with no `lane_<name>` box or a box that is no lane · a status mark in TICKETS.md "
        "(checkbox, Status column, done mark) · a day-1 ticket with a Depends On · docs/issues/README.md that remains.",
        "  - Publish (round 1 chose it) after the save - an issue body is its committed file: write <scratch>/plan.json "
        "and run `python " + (tool_file("tickets", "publish.py") or Path("commands/tickets/publish.py")).as_posix()
        + " <scratch>/plan.json` (`--no-board` = issues only; `--dry-run` = what it would create). Its OK/FAIL lines "
        "are the close's evidence. plan.json: {\"product\": \"<name>\", \"seat\": \"SR1\", \"milestones\": [{\"title\": "
        "\"M1 - ...\", \"due\": \"YYYY-MM-DD\" or null}], \"epics\": [{\"id\": \"M1-LOG\", \"name\": \"...\", "
        "\"milestone\": \"M1 - ...\", \"lane\": \"events\", \"owner\": \"Senior\"}], \"tickets\": [{\"id\": "
        "\"M1-LOG-01\", \"title\": \"...\", \"file\": \"docs/issues/M1-LOG-01_x.md\", \"epic\": \"M1-LOG\", "
        "\"depends_on\": []}]}."]
    rules = tickets_rules_text(filled, bool(gates))
    if playbook_tool() != "antigravity" and lead + len("\n".join(out)) + len(rules) > TICKETS_INLINE:
        # Claude Code shows 30,000 characters of a command's output: a big project's start goes over, and round 1
        # needs none of the slicing rules - round 2 does
        out.append("  - The slicing and TICKETS.md rules (word for word) were left out to keep this start readable: "
                   "run `status.py rules tickets` in your first call after the round-1 answers, before the proposal.")
        return "\n".join(out)
    return "\n".join(out) + "\n\n" + rules


# LEAN: /build's first call prints only what THIS ticket needs. On a logged pair run (same ticket, same commit) the
# four start commands printed 80 KB - too big to show, saved to a file, read back in three parts, then re-sent on ~85
# calls, 18% of the run - and plain Claude built the same ticket to the same quality on a third of the tokens. The
# rules for coding arrive first; the rules for the close arrive with the close gate (`gate.py --close`, which runs
# `rules build --close`), when they are needed, and ride along for the close's few calls. `rules build` still prints
# the whole list. The close's list was 18 KB in next.30-32 (printed by `ticket`): only these six sections steer a
# ticket's close; the spine overview, re-running a phase and following pointers never do (audit A15).
BUILD_EARLY = {
    "PRINCIPLES.md": ["Per-feature contract", "Architecture & quality bar", "Production safeguards", "Composed skills"],
    "MECHANISMS.md": ["Spine resolution", "Declined runs", "Status", "Commit the work"],
}
BUILD_LATE = {
    "PRINCIPLES.md": ["Documentation-driven", "Reviews, vision & confidence", "The exit-criteria gate"],
    "MECHANISMS.md": ["Step 3c", "Step 3b", "Plain-language close"],
}
CONTRACT_NAME = re.compile(r"`([A-Za-z_][A-Za-z0-9_]{2,})`")


def rules_text(want: dict[str, list[str]], title: str) -> str:
    return "\n\n".join([title] + [f"===== {name} =====\n" + print_sections(rule_file(name), secs)
                                  for name, secs in want.items() if secs])


def build_early() -> dict[str, list[str]]:
    return BUILD_EARLY


def build_close_text() -> str:
    """`rules build --close`: the close's order and rules, printed by gate.py --close when the close gate passes."""
    return (BUILD_CLOSE_ORDER + "\n\n" + "\n".join(CLOSE_CHECKLIST) + "\n\n"
            + rules_text(BUILD_LATE, "Rules for the close, word for word from the rule files:"))


BUILD_CLOSE_ORDER = ("The close, in this order, each once: (1) this close gate - done; (2) Step 3c's contradiction "
                     "check; (3) the feature doc in ONE write - the review table, this gate's numbers, Step 3c's "
                     "result, each changed file the ticket did not name with why; (4) commit it; (5) `status.py ticket`; "
                     "(6) `status.py set build filled`, the save question (it commits the record - the code was "
                     "committed before review), the transition guard, the four-block close.")


def find_ticket(base: Path, tid: str) -> Path | None:
    folder = base / "docs" / "issues"
    files = sorted(folder.glob("*.md")) if folder.is_dir() else []
    return next((f for f in files if f.stem == tid or f.name.startswith(f"{tid}_")), None) or \
        next((f for f in files if f"[{tid}]" in f.read_text(encoding="utf-8", errors="replace")), None)


def live_path_digest() -> str:
    """The *[always]* checks whole; every other check as its trigger and its bold rule - a trigger nobody reads cannot
    match, and the whole file is 7 KB carried on every call."""
    f = tool_file("build", "references", "live-path-checks.md")
    if f is None:
        return ""
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.startswith("- *[always"):
            out.append(line)
        elif m := re.match(r"- \*\[(.*?)\]\*\s+\*\*(.*?)\*\*", line):
            out.append(f"- [{m.group(1)}] {m.group(2)}")
    return (f"===== live-path checks ({f.as_posix()}; the *[always]* ones whole, the rest by trigger - read one by "
            f"`status.py section` only when its trigger matches) =====\n" + "\n".join(out))


def contract_locations(base: Path, body: str, limit: int = 15) -> list[str]:
    """Where each name the ticket's contract uses is defined, so the run greps nothing to find its seams."""
    names = list(dict.fromkeys(CONTRACT_NAME.findall(body)))[:limit]
    files = [p for p in project_files(base, SOURCE) if not is_test(p.relative_to(base).as_posix())]
    out = []
    for name in names:
        rx = re.compile(rf"^\s*(?:async\s+def|def|class|export\s+(?:async\s+)?(?:function|class|const|type|interface))"
                        rf"\s+{re.escape(name)}\b|^\s*{re.escape(name)}\s*[:=]", re.M)
        hit = None
        for p in files:
            text = p.read_text(encoding="utf-8", errors="replace")
            if m := rx.search(text):
                hit = f"{p.relative_to(base).as_posix()}:{text.count(chr(10), 0, m.start()) + 1}"
                break
        out.append(f"  {name} -> {hit or 'not defined yet (new in this ticket?)'}")
    return out


def demo_section(spec: str) -> str:
    """The ticket's Demo section, up to the next heading."""
    m = next(re.finditer(r"(?im)^#{2,3} .*\bdemo\b.*$", spec), None)
    if not m:
        return ""
    rest = spec[m.end():]
    nxt = re.search(r"^#{2,3} ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def demo_claims(spec: str) -> list[str]:
    """The Demo split into the claims a test must prove, one per clause: "gains one order per case, its email the
    case's sender, its status and tracking as the case says" is four claims. A logged Gemini build proved three and
    never sent the status - its fake accepted any request, so every test passed."""
    lines = [ln.strip(" -*") for ln in demo_section(spec).splitlines() if ln.strip() and "<!--" not in ln]
    claims = []
    for sentence in re.split(r"(?<=[.;!?])\s+", re.sub(r"[`*_]", "", " ".join(lines))):
        head, _, rest = sentence.partition(": ")
        if rest and len(head.split()) <= 6:  # "Run the script: ..." - the entry point, not a claim
            sentence = rest
        for part in re.split(r",\s+|\s+and\s+", sentence):
            part = part.strip(" .;!?")
            if len(part.split()) >= 2:
                claims.append(part)
    return claims


# a changed file that talks to an outside service needs a RED cut of its own: a fake that accepts any request lets
# every test pass while the request is wrong (a logged Gemini build's orders never carried their status)
OUTSIDE_CALL = re.compile(r"(?m)^\s*(?:import|from)\s+(?:httpx|requests|aiohttp|urllib3|urllib\.request|boto3|stripe|"
                          r"shopify|openai|anthropic|twilio|sendgrid|smtplib)\b"
                          r"|(?:from\s+|require\()['\"](?:axios|node-fetch|openai|stripe|@anthropic-ai/sdk)['\"]")
REACH_LINE = re.compile(r"(?im)^\W*real-world reach:\s*(.+)$")


def remote_line(base: Path) -> str:
    """P16: the git host, detected now (a logged build's close said "no remote" while `git remote -v` showed one,
    trusting an old open item). Reviews find their base the same way with or without one."""
    url = git(base, "remote", "get-url", "origin")
    default = next((b for b in ("main", "master") if git(base, "rev-parse", "--verify", "--quiet", b)), "main")
    if not url:
        return (f"Git remote: none - reviews compare against `git merge-base HEAD {default}`; no issues, PRs or board "
                f"this run. Say exactly that in the close.")
    host = next((h for h in ("github", "gitlab", "bitbucket") if h in url.lower()), "another host")
    head = "set" if git(base, "rev-parse", "--verify", "--quiet", "refs/remotes/origin/HEAD") else "NOT set (run: git remote set-head origin --auto)"
    return (f"Git remote: origin = {url} ({host}); origin/HEAD {head}. Reviews still find their base with "
            f"`git merge-base HEAD {default}`. Never write \"no remote\" in this run's close - an older note saying so is stale.")


def runbook_start_rules(base: Path, dev: str) -> list[str]:
    """The runbook's rules for starting the app (a paragraph naming the dev command with always/never/without/only):
    a logged /test started uvicorn its own way and spent 3 live-path runs finding a Windows rule the runbook held."""
    f = base / "docs" / "runbook.md"
    if not dev or not f.is_file():
        return []
    paras = re.split(r"\n\s*\n", f.read_text(encoding="utf-8", errors="replace"))
    return [" ".join(p.split())[:360] for p in paras
            if dev in p and re.search(r"(?i)\b(always|never|without|only|must)\b", p)
            and not p.lstrip().startswith(("#", "|", "```"))][:2]


def dev_server(base: Path, foundation: str) -> tuple[str, str, str]:
    """(start command, port, health URL) from the project itself: a `dev`/`serve`/`start` recipe in the justfile,
    Makefile or package.json, the port in it (else in #Foundation), and the health path #Foundation records.
    An empty field means the project does not say - the start then marks it MISSING instead of inventing it."""
    cmd, body = "", ""
    for name, runner in (("justfile", "just"), ("Justfile", "just"), (".justfile", "just"), ("Makefile", "make")):
        f = base / name
        if f.is_file():
            text = f.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^(dev|serve|start|run)(?:\s+[^:\n=]*)?:(?!=)[^\n]*\n((?:[ \t]+\S[^\n]*\n?)+)", text, re.M)
            if m:
                cmd, body = f"{runner} {m.group(1)}", m.group(2)
                break
    if not cmd and (base / "package.json").is_file():
        try:
            scripts = json.loads((base / "package.json").read_text(encoding="utf-8")).get("scripts") or {}
            key = next((k for k in ("dev", "start", "serve") if k in scripts), None)
            if key:
                cmd, body = f"npm run {key}", scripts[key]
        except ValueError:
            pass
    pm = re.search(r"(?:--port[ =]|PORT=|-p )(\d{2,5})", body) or re.search(r"localhost:(\d{2,5})", foundation)
    port = pm.group(1) if pm else ""
    hm = re.search(r"`(/(?:healthz?|health[\w/-]*|ready[\w/-]*|livez?))`|localhost:\d+(/(?:healthz?|health[\w/-]*))",
                   foundation)
    path = next((g for g in hm.groups() if g), "") if hm else ""
    return cmd, port, (f"http://localhost:{port}{path}" if port and path else "")


DB_PORTS = {"postgres": 5432, "postgresql": 5432, "mysql": 3306, "mariadb": 3306, "mongodb": 27017, "redis": 6379}


def env_precheck(base: Path) -> str | None:
    """The databases .env names, reached from HERE before the run starts: a logged run spent 8 calls (netstat,
    docker ps, a hung suite) finding a stopped container that one local socket check names. None when all answer."""
    import socket
    from urllib.parse import urlsplit
    env = base / ".env"
    if not env.is_file():
        return None
    down = []
    for ln in env.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\s*(TEST_DATABASE_URL|DATABASE_URL)\s*=\s*['\"]?([^'\"\s#]+)", ln)
        if not m:
            continue
        try:
            u = urlsplit(m.group(2))
            host, port = u.hostname, u.port or DB_PORTS.get(u.scheme.split("+")[0].lower())
        except ValueError:
            continue
        if not host or not port or (host, port) in [(h, p_) for _, h, p_ in down]:
            continue
        try:
            socket.create_connection((host, port), timeout=1).close()
        except OSError:
            down.append((m.group(1), host, port))
    if not down:
        return None
    hint = ""
    for name in ("justfile", "Justfile", "Makefile", "docker-compose.yml", "compose.yaml", "compose.yml", "README.md"):
        f = base / name
        if f.is_file():
            h = re.search(r"docker(?:\s+compose)?\s+start\s+([\w.-]+)|container_name:\s*([\w.-]+)",
                          f.read_text(encoding="utf-8", errors="replace"))
            if h:
                hint = f" - e.g. `docker start {h.group(1) or h.group(2)}`"
                break
    return (f"! the database does not answer: {', '.join(f'{k} {h}:{p_}' for k, h, p_ in down)}. Start it first{hint}, "
            f"then run this start again - never debug it call by call (a stopped container hangs the suite)")


def module_rules(base: Path, files: list[str]) -> str | None:
    """The STRUCTURE.md dependency rows for the modules a ticket touches: a logged build re-read the 26 KB file 10
    times to learn what one module may import."""
    f = base / "STRUCTURE.md"
    if not f.is_file():
        return None
    rows, header = {}, None
    for ln in f.read_text(encoding="utf-8", errors="replace").splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")] if ln.strip().startswith("|") else []
        if not cells:
            header = None
            continue
        if header is None:
            header = cells if any(re.search(r"(?i)\bimport", c) for c in cells) else []
            continue
        if not header or set("".join(cells)) <= set("-: "):
            continue
        col = next(i for i, c in enumerate(header) if re.search(r"(?i)\bimport", c))
        if col < len(cells):
            rows[cells[0].strip("`").rstrip("/").split("/")[-1]] = cells[col]
    mods = []
    for t in files:
        parts = t.split("/")
        mod = next((x for x in parts[:2] if x in rows), None)
        if mod and mod not in mods:
            mods.append(mod)
    if not mods:
        return None
    return ("Module rules (STRUCTURE.md's dependency table - no need to open it; a new arrow is a design change to "
            "ask about):\n" + "\n".join(f"  {m} may import: {rows[m]}" for m in mods))


TICKET_CMD = re.compile(r"status\.py[\"']?\s+ticket\s+([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)")


def other_tickets(conversation: str, tid: str) -> list[str]:
    """Ticket ids this conversation already recorded with `status.py ticket`, other than `tid`."""
    return sorted({t for t in TICKET_CMD.findall(conversation) if t != tid})


def this_conversation(base: Path) -> str:
    """The newest session log of this project, as text (Claude Code JSONL, or the Antigravity conversation that
    names this folder); "" when there is none."""
    sc = session_costs()
    if sc is None:
        return ""
    try:
        logs = sorted(sc.project_log_dir(base).glob("*.jsonl"), key=os.path.getmtime)
        if logs:
            return logs[-1].read_text(encoding="utf-8", errors="replace")
        db = sc.newest_antigravity(base)
        return db.read_bytes().decode("utf-8", errors="replace") if db else ""
    except Exception:  # a warning, never a reason to fail the start
        return ""


def build_start_text(st: Status, tid: str, today: str, lean: bool = False) -> str:
    base = st.base
    tf = find_ticket(base, tid)
    if tf is None:
        raise Refused(f"no ticket file for {tid} in docs/issues/ - run /tickets, or name the ticket exactly as its "
                      f"file does")
    text = tf.read_text(encoding="utf-8", errors="replace")
    secs = ticket_sections(text)
    parts = [f"===== ticket {tid}: {tf.relative_to(base).as_posix()} (the spec: build exactly this) =====",
             text.strip()]
    done = other_tickets(this_conversation(base), tid)
    if done:  # a logged Antigravity conversation built two tickets: the second re-sent the first's history, 40M tokens
        parts.insert(0, f"! this conversation already recorded {', '.join(done)}: every call re-sends that history. "
                        f"Tell the user to open a NEW conversation for {tid} (state is on disk; nothing is lost) - "
                        f"continue here only if they say so")
    pre = env_precheck(base)
    if pre:
        parts.insert(0, pre)
    plan = base / "TICKETS.md"
    if plan.is_file() and tid not in plan.read_text(encoding="utf-8", errors="replace"):
        parts.append(f"! {tid} is not in TICKETS.md - confirm with the user that it is in scope before building")
    rows = []
    for f in TARGET.findall(secs.get("Target Files", "")):
        p = base / f
        rows.append(f"  {f} - " + (f"{p.read_text(encoding='utf-8', errors='replace').count(chr(10))} lines"
                                    if p.is_file() else "new"))
    if rows:
        parts.append("Target files (read these, a line range when big - nothing else up front):\n" + "\n".join(rows))
    mr = module_rules(base, TARGET.findall(secs.get("Target Files", "")))
    if mr:
        parts.append(mr)
    locs = contract_locations(base, secs.get("Contract", ""))
    if locs:
        parts.append("Contract names, where each is defined:\n" + "\n".join(locs))
    prod = base / "PRODUCT.md"
    spine = product_sections(prod.read_text(encoding="utf-8", errors="replace")) if prod.is_file() else {}
    policy = spine.get("Project", "")
    # #Contracts' project-wide rules (units, formats, tenant key, idempotency, versioning) and any line naming this
    # ticket's contract - what every ticket must obey (a lean build found "email trimmed and lower-cased" there) -
    # without the file lists, evidence and receipts; the ticket is the rest of the spine
    contracts = spine.get("Contracts", "")
    if not has_content(contracts):
        parts.append("! #Contracts is empty - warn the user and offer /contracts first (allow override)")
    else:
        names = list(dict.fromkeys(CONTRACT_NAME.findall(secs.get("Contract", ""))))
        keep, rule = [], False
        for line in contracts.splitlines():
            if re.match(r"- \*\*", line):
                rule = bool(re.match(r"(?i)- \*\*[^*]*(unit|scale|format|version|pii|tenant|idempot)", line))
            named = any(re.search(rf"\b{re.escape(n)}\b", line) for n in names)
            if (rule or named) and line.strip() and "evidence:" not in line:
                keep.append(line.rstrip())
        if keep:
            text_ = "\n".join(keep)
            parts.append("===== PRODUCT.md #Contracts: the rules every ticket obeys, and lines naming this ticket's "
                         "contract (read more of #Contracts only where one points further) =====\n"
                         + (text_[:4000] + "\n... (more: status.py section PRODUCT.md Contracts)" if len(text_) > 4000
                            else text_))
    if has_content(policy):
        parts.append("===== PRODUCT.md #Project policy (this project's own rules for every ticket) =====\n"
                     + policy.strip())
    branch = git(base, "rev-parse", "--abbrev-ref", "HEAD")
    if branch in ("main", "master"):
        title = next((re.sub(r"^#\s*(\[[^\]]*\])?\s*", "", l) for l in text.splitlines() if l.startswith("# ")), "")
        parts.append(f"! on {branch}: create the ticket branch before the first write - "
                     f"git switch -c {tid.lower()}-{slug(title, 24) if title else 'work'}")
    # ready-to-run commands, never placeholders the run must fill: the gate picks the recipe + the ticket's tests
    # itself; the dev server's command, port and health URL come from the project (its dev recipe, #Foundation)
    dev, port, health = dev_server(base, spine.get("Foundation", ""))
    entries = [next(g for g in m.groups() if g) for m in DEMO_ENTRY.finditer(demo_section(text))]
    live = (f'check --cmd "{dev or "<MISSING: the dev start command - #Foundation names none>"}" '
            f'--port {port or "<MISSING: port>"} --health '
            f'{health or "<MISSING: a health URL - #Foundation names none>"}')
    tools = [("gate", tool_file("build", "gate.py"), f"--ticket {tid}    (the close gate: --ticket {tid} --close)"),
             ("wire cuts", tool_file("build", "wirecut.py"),
              '--cut "[D<n>=]<file>::<text to break>::<replacement>::<test command>" (repeat --cut; no JSON file)'),
             ("live path", tool_file("foundation", "devserver.py"),
              live + (f"    (then the demo's entry: {', '.join(entries[:3])})" if entries else ""))]
    if lean:  # the lean path proves wiring by the reviews and the gate, not by cuts
        tools = [t for t in tools if t[0] != "wire cuts"]
    parts.append("Commands (one call each; every path is absolute):\n" + "\n".join(
        f"  {name}: python \"{p.as_posix()}\" {args}" for name, p, args in tools if p))
    claims = [] if lean else demo_claims(text)
    if claims:  # DP1-DP3: what `status.py ticket` checks, told before the first line of code
        parts.append("Demo claims - each needs a test that FAILS when you break the code doing it: one wire cut per "
                     "claim, tagged with its number (--cut \"D2=<file>::...\"); a claim no test can prove: --uncut "
                     "\"D<n>: <why>\" on the ticket row, said to the user:\n"
                     + "\n".join(f"  D{i}: {c}" for i, c in enumerate(claims, 1))
                     + "\nA changed file that calls an outside service (HTTP client, vendor SDK) needs a RED cut of "
                       "its own that breaks what it SENDS - a fake that accepts any request passes every test.")
    touches = sorted({w.lower() for w in SECURITY_TICKET.findall(text)})
    if touches or OUTSIDE_CALL.search(text):
        parts.append("Real-world reach: before round 1, ask what REAL thing this code could touch by mistake (a real "
                     "shop, account, inbox, payment, user) and guard it with a test; the feature doc carries "
                     "`Real-world reach: <what> - guarded by test_<name>` (or `- not guarded: <why>`, said to the user).")
    parts.append(remote_line(base))
    # P44: the ticket's boundary, printed (a logged lean build fixed a project-level check on its ticket branch)
    parts.append("This ticket must NOT: merge (the branch waits for /ship) · write PRODUCT.md · change another ticket's "
                 "file without the user's yes · fix a project-level problem on this branch · re-run a check to get its "
                 "number (the close gate's record counts on the exact files it checked; `status.py ticket` names any "
                 "file changed since - `--dry-run` lists every gap and writes nothing) · run a check the gate does not "
                 "(an extra type checker, a second scan).\n" + DEV_CHECK_HEAD[2])
    parts.append(f"Security review: REQUIRED - the ticket touches {', '.join(touches)}: round 1 starts the security "
                 f"helper" if touches else "Security review: not required by the ticket's words - it names no auth, "
                 "tenant, money, secret, personal data or upload; code you add that touches one needs it after all "
                 "(`ticket` checks the diff): otherwise the code review covers it; say so in --review")
    if lean:
        mark_rules_read(base, "build", today)
        return "\n\n".join(p for p in parts if p)
    review = tool_file("build", "references", "review-stretch.md")
    if review:
        parts.append(f"Review helper prompt: {review.as_posix()} §Helper prompt (give it to ONE helper; it reads the "
                     f"rest itself)")
    parts.append(live_path_digest())
    parts.append(rules_text(build_early(), "Rules for coding this ticket, word for word from the rule files (the "
                                            "close's rules print with `status.py ticket`):"))
    mark_rules_read(base, "build", today)
    return "\n\n".join(p for p in parts if p)


def template_lines() -> set[str]:
    """The scaffold lines a project copied from the template: never content, however full they look."""
    here = Path(__file__).resolve().parent
    for cand in (here.parent / "templates" / "PRODUCT.md", here / "PRODUCT.md"):
        if cand.exists():
            return {l.strip() for l in cand.read_text(encoding="utf-8").splitlines() if l.strip()}
    return set()


SCAFFOLD = template_lines()
PLACEHOLDER = [re.compile(r"`docs/[^`]+`\s*\(reasoning \+ workings; this section stays a RECORD\)"),
               re.compile(r"`evidence:[^`]*`"), re.compile(r"<[^>]*>"), re.compile(r"\(e\.g\.[^)]*\)")]


def has_content(body: str) -> bool:
    for line in body.splitlines():
        s = re.sub(r"<!--.*?-->", "", line).strip()
        if not s or s in SCAFFOLD or s.startswith(("<!--", "_An override marks", "|")):
            continue
        m = re.match(r"^[-*]\s*(\[[ x]\]\s*)?\*\*[^*]+\*\*\s*(.*)$", s)
        if m:
            box, rest = (m.group(1) or "").strip(), m.group(2)
            for p in PLACEHOLDER:
                rest = p.sub("", rest)
            if box == "[x]" or (box != "[ ]" and re.search(r"[A-Za-z0-9]", rest)):
                return True
            continue
        if s.startswith("- [ ]") or (s.startswith("-") and "·" in s and "**" not in s):
            continue  # an unticked criterion, or a scaffold hint line (the table-stakes list)
        return True
    return False


def migrate(text: str, today: str, archive_path: str, tickets_md: bool = False, base: Path = Path(".")
            ) -> tuple[Status, str, str, list[str]]:
    """Returns (status, new PRODUCT.md, archive text, report). Every removed line goes to the archive verbatim.

    A phase's state is its latest-dated marker (running -> overridden on a later date is overridden). An override
    of ONE criterion is not a phase state: it stays in PRODUCT.md and becomes an open item. A marker inside a log
    that has rows is about one ticket or release: it becomes an open item.
    """
    lines = text.splitlines()
    kept, removed, report = [], [], []
    st = Status.new("", today)
    st.base = base
    title = next((l for l in lines if l.startswith("# PRODUCT")), "# PRODUCT — (unnamed)")
    st.product = title.split("—", 1)[-1].strip() if "—" in title else title[2:].strip()
    archive = [f"# Status archive — moved out of PRODUCT.md by `status.py migrate` on {today}", "",
               "Every line below was removed from PRODUCT.md unchanged. STATUS.md holds the same facts as rows.", ""]
    section = None
    marks: dict[str, list[tuple[str, str, str, str]]] = {}   # section -> [(date, kind, note, due)]
    items: list[list[str]] = []                              # open items: [since, from, what, clears]
    log_rows: dict[str, list[list[str]]] = {k: [] for k in LOG_SECTIONS}
    for line in lines:
        m = re.match(r"^## (\S+(?: log)?)", line)
        if m:
            section = m.group(1)
            if section in LOG_SECTIONS:
                removed.append(line)
                archive += ["", f"<!-- was PRODUCT.md#{section} -->", line]
                continue
        u = unwrap(line)
        nr, ov, rn, of = NOT_RUN.match(u), OVERRIDE.match(u), RUNNING.match(u), OVERRIDE_FIELD.match(u)
        if section in LOG_SECTIONS:
            removed.append(line)
            archive.append(line)
            if line.startswith("|") and not line.startswith("|---"):
                cells = split_row(line)
                if cells and cells[0].lower() not in ("feature", "date"):
                    log_rows[section].append(cells)
            elif nr or ov:
                marks.setdefault(section, []).append(((nr or ov).group(1), "declined" if nr else "overridden",
                                                      (nr or ov).group(2), ""))
            continue
        if HEADER.match(line):
            removed.append(line)
            archive += ["## Was the PRODUCT.md header", "", line]
            upd = re.search(r"Last updated:\s*" + DAY, line)
            ai = re.search(r"AI product\?\s*\**(yes|no)", line, re.I)
            stg = re.search(r"Stage:\s*\**`?/?([\w-]+)", line)
            if upd:
                st.header["Updated"] = upd.group(1)
            if ai:
                st.header["AI product"] = ai.group(1).lower()
            if stg and stg.group(1) in CHAIN:
                st.header["Stage"] = stg.group(1)
            continue
        pm = PLAYBOOK_LINE.match(line)
        if pm and section is None:
            removed.append(line)
            archive.append(line)
            if "override" in pm.group(1).lower():
                st.header["Order"] = short(pm.group(1), archive_path)
            continue
        if section and ov and CRITERION.search(u):
            kept.append(line)  # part of the section's record; the owed criterion is tracked as an open item
            items.append([ov.group(1), section, short(f"criterion bypassed: {ov.group(2)}", archive_path, 170),
                          "the bypassed criterion is met, or the override is re-confirmed"])
            continue
        if section and (nr or rn or ov or of):
            removed.append(line)
            archive += [f"(from PRODUCT.md#{section})", line]
            if rn:
                marks.setdefault(section, []).append((rn.group(1), "running", rn.group(3), rn.group(2)))
            elif of or ov:
                g = of or ov
                marks.setdefault(section, []).append((g.group(1), "overridden", g.group(2), ""))
            else:
                marks.setdefault(section, []).append((nr.group(1), "declined", nr.group(2), ""))
            continue
        kept.append(line)
    secs = product_sections("\n".join(kept))
    ui = re.search(r"Has user-facing UI\?\**\s*\**(yes|no)", secs.get("Design", ""), re.I)
    if ui:
        st.header["UI"] = ui.group(1).lower()
    rank = {"declined": 0, "running": 1, "overridden": 2}

    def latest(sec: str):
        ms = marks.get(sec, [])
        return max(ms, key=lambda x: (x[0], rank[x[1]])) if ms else None

    def apply(phase: str, sec: str, content: bool) -> None:
        r, last = st.phase(phase), latest(sec)
        if last and last[1] in ("running", "overridden"):
            note = short(last[2], archive_path)
            r[1:6] = [last[1], last[0], last[3], "", note if last[1] == "running" else f"Override: {note}"]
        elif content:
            r[1:6] = ["filled", st.header["Updated"] or today, "", "unknown" if phase in VERIFY else "", "migrated"]
            if last:
                report.append(f"#{sec}: an old Not run line sits beside content - recorded filled; line archived")
        elif last:
            r[1:6] = ["declined", last[0], "", "", f"Not run: {short(last[2], archive_path)}"]

    for phase, sec in PHASE_SECTION.items():
        apply(phase, sec, has_content(secs.get(sec, "")))
    for old, (new, phase) in LOG_SECTIONS.items():
        for cells in log_rows[old]:
            want = len(COLUMNS[new])
            if new == "Tickets":
                tid = re.search(r"`?([A-Z][A-Z0-9]*-[A-Z0-9-]+)`?", cells[0])
                row = [tid.group(1) if tid else cells[0], "migrated", cells[1] if len(cells) > 1 else "",
                       cells[2] if len(cells) > 2 else "", "not counted", "", cells[3] if len(cells) > 3 else ""]
            else:
                row = (cells + [""] * want)[:want]
            st.rows[new].append([c if len(c) <= CAP["cell"] else short(c, archive_path, 120) for c in row])
        if phase and log_rows[old]:
            for d, kind, note, _ in marks.get(old, []):
                items.append([d, phase, short(f"{'Not run' if kind == 'declined' else 'Override'}: {note}",
                                             archive_path, 170), "the ticket or release it names moves on"])
        if phase:
            apply(phase, old, bool(log_rows[old]))
        elif marks.get(old):
            for d, kind, note, _ in marks[old]:
                items.append([d, "drift-check", short(note, archive_path, 170), "the next drift check"])
    if tickets_md:
        st.phase("tickets")[1:6] = ["filled", st.header["Updated"] or today, "", "", "migrated: TICKETS.md exists"]
    for i, (since, frm, what, clears) in enumerate(sorted(items), 1):
        frm_phase = next((p for p, s in PHASE_SECTION.items() if s == frm), frm)
        st.rows["Open items"].append([str(i), since, frm_phase if frm_phase in CHAIN else "drift-check", what,
                                      clears, ""])
    st.archive = archive_path
    if not st.header["Updated"]:
        st.header["Updated"] = today
    if st.header["AI product"] == "unknown":
        report.append("AI product: not recorded in PRODUCT.md - ask the user, then `status.py flag --ai yes|no`")
    for p in sorted(VERIFY):
        if st.state(p) == "filled":
            report.append(f"#{p}: verdict unknown after migrate - ask the user for its last result, then "
                          f"`status.py set {p} filled --verdict pass|fail`")
    if st.header["UI"] == "unknown":
        report.append("UI: not recorded in PRODUCT.md#Design - ask the user, then `status.py flag --ui yes|no`")
    new_product = "\n".join(kept).rstrip("\n") + "\n"
    arch_text = "\n".join(archive).rstrip("\n") + "\n"
    # Nothing lost: every old line is kept or removed, and every removed line is in the archive verbatim.
    left = Counter(removed) - Counter(arch_text.splitlines())
    if sorted(lines) != sorted(kept + removed) or left:
        raise Refused(f"migrate would lose {sum(left.values()) or 'a'} line(s) - refusing; nothing written")
    report.insert(0, f"{len(removed)} lines move to {archive_path} verbatim; {len(kept)} stay in PRODUCT.md; "
                     f"{len(st.rows['Open items'])} open items")
    return st, new_product, arch_text, report


# ---- main -----------------------------------------------------------------------------------------------------
# ---- /foundation (P1, P2, P4, P20, P25, P39) -----------------------------------------------------------------------
# Its start was four commands and 74 KB (a logged agent project: the close's rule sections, verify.md whole,
# skeleton-steps.md as headings only), then "open now" agent.md, each of the eight steps and each Step 3b proof by
# section: up to 16 more calls, each re-sending a 150-250K-token conversation. A logged Claude run spent 143 calls;
# a logged Gemini run closed with decorative guards that only a hand review found. The start now prints in ONE call
# the project facts the steps need (computed - no ls, git or `which` of the run's own), the sections it derives from,
# the steps and the proofs whole, and only the rules the build uses. The close's rules arrive with `set foundation
# filled`, which refuses every countable gap - the tree's and the record's - in one list, on /foundation's own close
# only (phase_check keeps the older, smaller foundation_gaps, so a project filled under older rules is never blocked).
FOUNDATION_HEAD = (
    "This phase closes with ONE call once Step 3b's proofs pass and the user said yes: `status.py set foundation "
    "filled --section-from <file> --commit \"<one line>\"` (the section in a scratch file outside the repo, never an "
    "edit tool on PRODUCT.md). It checks the record and the tree, names every problem at once, saves through the "
    "commit hooks and prints the rest of the close: no git call of your own (no `--commit` on a no).",
    "An `evidence:` line: <command> → <result> · <a file in THIS repo that the command checks, never a playbook "
    "script> · <date> - `set` resolves every file and `file::test` it cites. Cite the command you ran.",
    "The same command fails 3 times: stop. Tell the user what fails, what you tried and what you need - never a "
    "4th try of the same fix.",
    "Commands work in PowerShell and in bash: one command per call - no &&, tail, grep or export; never `cd <path> "
    "&&`. Output over 30 lines goes to a scratch file; read only its last lines.",
    "The playbook's scripts (status.py, devserver.py, ci_local.py, proof.py, audit.py) are tools, not reading: run "
    "them; their output and refusals say what to do - never open their source or the rule files to pass a check: "
    "`set foundation filled --section-from <file> --dry-run` lists every gap and writes nothing. `set` wraps long "
    "lines itself - never measure them. Plain symbols (≤ →), never LaTeX.",
    "Step 3b's proofs run through `proof.py -- <command>` (devserver.py and ci_local.py log their own; a plant: "
    "`proof.py plant`): `set` matches every `evidence:` line to that log, and plants a fake secret through the "
    "hooks itself.",
)
# next.68: Documentation-driven and Composed skills moved to the close (the record and the evidence lines are written
# there), and verify.md's Saving is left out of the start (the head and the order line say it; `set` does it) - 1.9 KB
# less on every call of the phase, paying for the new proof, plant and runbook lines
PHASE_RULES["foundation"] = {
    "PRINCIPLES.md": ["The 5-step spine", "Architecture & quality bar", "Production safeguards", "Communication"],
    "MECHANISMS.md": ["Spine resolution", "Re-run semantics", "Declined runs", "Status", "Follow the pointer"],
}
PHASE_CLOSE_RULES["foundation"] = {
    "PRINCIPLES.md": ["Per-feature contract", "Reviews, vision & confidence", "The exit-criteria gate",
                      "Documentation-driven", "Composed skills"],
    "MECHANISMS.md": ["Step 3b", "Step 3c", "Commit the work", "Plain-language close"],
}
CLOSE_STEPS["foundation"] = (  # /foundation runs steps 2-3 before its save question: here only after a later fix
    "(done before the save question; again only if a fix since changed a number) every number this phase introduced "
    "against #Vision and #Architecture: a port, a pinned version, a price the tracer uses",
    "(done before the save question; again only after a fix) #Architecture (adapters · tool choices · CI approach · "
    "the datastore and its custody, test datastore included) and #Structure's map",
    "the cited files and tests, the hooks, the lockfiles, fallback secrets, the test engine and variable, CI's run and "
    "scans, the placeholder boot proof, the bot and the runbook")
START_HOLDS["foundation"] = ("the project facts, #Architecture and #Structure, the eight\n    steps, the proofs, this "
                            "phase's rules, the close")
# binaries the machine must have (pre-commit, ruff, lefthook come with the project's own dev dependencies)
FOUNDATION_TOOLS = ("uv", "poetry", "pdm", "node", "npm", "pnpm", "bun", "docker", "gitleaks", "just", "make", "psql")
DATASTORES = re.compile(r"(?i)\b(postgres(?:ql)?|mysql|mariadb|sql server|mssql|cockroach(?:db)?|sqlite|mongo(?:db)?|"
                        r"redis|dynamodb|firestore|supabase|neon)\b")
TEST_RUNNERS = re.compile(r"(?i)^\W*(?:\S*[/\\])?(?:uv run |poetry run |pdm run |npx |pnpm (?:exec )?|python3? -m )?"
                          r"(?:pytest|jest|vitest|mocha|go test|cargo test|npm (?:run )?test|just test|make test|"
                          r"rspec|phpunit)\b")
SECRET_SCANNERS = r"gitleaks|trufflehog|detect-secrets|ggshield|secretlint"
DEP_SCANNERS = (r"pip-audit|uv-secure|safety (?:check|scan)|npm audit|pnpm audit|yarn (?:npm )?audit|bun audit|"
                r"osv-scanner|cargo audit|cargo deny|govulncheck|bundler?[- ]audit|trivy|grype|snyk|audit-ci|"
                r"dependency-check")
WORKING_FOLDER_SCAN = re.compile(r"\bgitleaks\s+(?:dir|directory)\b|\bgitleaks\s+(?:detect|protect)\b[^\n]*--no-git\b")
RUNNER_CALL = re.compile(r"(?m)^\s*(?:-\s*)?(?:run:\s*)?(?:\|\s*)?.*?\b(just|make|npm run|pnpm(?: run)?|yarn|task|"
                         r"pre-commit run|nox|tox)\b")
UPDATE_BOTS = (".github/dependabot.yml", ".github/dependabot.yaml", "renovate.json", "renovate.json5", ".renovaterc",
               ".renovaterc.json", ".github/renovate.json", ".github/renovate.json5", ".gitlab/renovate.json")
# AGENT.md §Foundation's seven items, by the words a record names them with (P8: any honest wording)
AGENT_ITEMS = (("1 (framework pinned, a fake model)", r"fake (?:model|llm|provider|client)|framework|scripted model"),
               ("2 (a read tool through the tier check, a write refused)", r"\btiers?\b|read[- ]tool|write tool|"
                                                                            r"forbidden|registry|policy gate"),
               ("3 (a cap hands off)", r"\bcaps?\b|step (?:cap|limit)|max(?:imum)? (?:steps|turns)|escalat|hand(?:ed)?"
                                       r"[- ]?off"),
               ("4 (the kill switch)", r"kill[- ]?switch"),
               ("5 (a trace is written)", r"\btrac(?:e|es|er|ing)\b"),
               ("6 (untrusted input in a tool result stays data)", r"untrusted|inject"),
               ("7 (the eval harness in CI)", r"\bevals?\b|golden"))
# a design token read back, or the shell a route renders - not any "token" (a logged record's `Bearer <token>` login)
UI_PROOF = re.compile(r"(?i)design[- ]tokens?|tokens?\.css|token[_ -]?(?:read|resolv)|\bvar\(--|--[a-z][\w-]*\s*:\s*\S|"
                      r"stylesheet|\.css\b|\bshell\b|base\.html|root layout|layout\.(?:tsx|jsx|vue|svelte|html)")
PHRASE_LIST = re.compile(r"(?i)[\"'/][^\"'\n]{0,30}\b(?:ignore|disregard)\b[^\n]{0,50}\b(?:instructions?|rules|"
                         r"previous|prior|above)\b")
MONEY_COLUMN = {  # a money column typed as a float in what reaches the database (models, migrations, schema files)
    ".py": re.compile(r"[\"'](\w+)[\"']\s*,\s*(?:sa\.|sqlalchemy\.)?(?:Float|REAL|DOUBLE(?:_PRECISION)?)\b"
                      r"|\b(\w+)\s*(?::[^=\n]*)?=\s*(?:sa\.)?(?:Column|mapped_column)\(\s*(?:sa\.)?(?:Float|Double)\b"
                      r"|\b(\w+)\s*=\s*models\.FloatField\("),
    ".sql": FLOAT_DECL[".sql"], ".prisma": FLOAT_DECL[".prisma"], ".ts": FLOAT_DECL[".ts"], ".js": FLOAT_DECL[".js"],
}


def project_slug(st: "Status", base: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (st.product or base.resolve().name).lower()).strip("-") or "app"


def hooks_state(base: Path) -> tuple[list[str], bool]:
    """(the hook configs found, installed?) - the same test E6 refuses on."""
    found = [c for c in HOOK_CONFIGS if (base / c).exists()]
    hooks = git(base, "rev-parse", "--git-path", "hooks")
    hook_dir = (base / hooks) if hooks else base / ".git" / "hooks"
    return found, (base / ".git").exists() and (hook_dir / "pre-commit").is_file()


def env_example_keys(base: Path) -> tuple[list[str], list[str]]:
    """(the CHANGE_ME variables, the TEST_ variables) of .env.example."""
    f = base / ".env.example"
    text = read_text(f) if f.is_file() else ""
    return (re.findall(r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*\S*CHANGE_ME", text, re.M),
            re.findall(r"^\s*(TEST_[A-Z0-9_]*)\s*=", text, re.M))


def evidence_lines(body: str) -> list[str]:
    return [m.group(1) for m in EVIDENCE.finditer(re.sub(r"<!--.*?-->", "", body, flags=re.S))]


def evidence_command(line: str) -> str:
    return re.split(r"→|->", line, maxsplit=1)[0]


def text_of(base: Path, names) -> str:
    out = []
    for n in names:
        p = base / n
        if p.is_dir():
            out += [read_text(f) for f in sorted(p.rglob("*")) if f.is_file()]
        elif p.is_file():
            out.append(read_text(p))
    return "\n".join(out)


def ci_and_what_it_calls(base: Path) -> str:
    """The CI files, plus the task runner and hook config they call - a scan run as `just check` in CI counts (P8)."""
    ci = text_of(base, CI_FILES)
    calls = {m.group(1) for m in RUNNER_CALL.finditer(ci)}
    more = []
    if calls & {"just"}:
        more += ["justfile", "Justfile", ".justfile"]
    if calls & {"make"}:
        more += ["Makefile"]
    if calls & {"npm run", "pnpm", "pnpm run", "yarn"}:
        more += ["package.json"]
    if calls & {"task"}:
        more += ["Taskfile.yml", "Taskfile.yaml"]
    if calls & {"pre-commit run"}:
        more += [".pre-commit-config.yaml"]
    return ci + "\n" + text_of(base, more)


def open_item_says(st: "Status", pattern: str) -> bool:
    return any(re.search(pattern, r[3], re.I) and not r[5] for r in st.rows["Open items"])


def item_blocks(body: str) -> list[str]:
    """Each line with the lines indented under it: a record line and its sub-bullets read as one claim."""
    lines = [l for l in body.splitlines() if l.strip()]
    ind = [len(l) - len(l.lstrip()) for l in lines]
    out = []
    for i in range(len(lines)):
        j = i + 1
        while j < len(lines) and ind[j] > ind[i]:
            j += 1
        out.append("\n".join(lines[i:j]))
    return out


def earlier_check_gaps(st: "Status", phase: str, base: Path) -> list[str]:
    """An earlier filled phase whose check fails now, worded as cmd_set's own refusal - in the same list as this
    phase's gaps, so the fix is one round, not two."""
    out = []
    for p in CHAIN[:CHAIN.index(phase)]:
        if st.state(p) != "filled" or earlier_override(st, p):
            continue
        failed = phase_check(p, base)
        if failed:
            out.append(f"#{p}'s check fails now, so this phase cannot close on it - {failed}. Fix it, or record the "
                       f"user's reason: status.py open --from {phase} --what \"Override: #{p}'s check fails - <the "
                       f"user's own words>\" --clears \"#{p}'s check passes\"")
    return out


def foundation_close_gaps(base: Path, st: "Status") -> list[str]:
    """`set foundation filled`: the tree's checks (foundation_gaps) and the record's, every problem in one list."""
    gaps = foundation_gaps(base)
    prod = base / "PRODUCT.md"
    secs = product_sections(read_text(prod)) if prod.is_file() else {}
    body, arch = re.sub(r"<!--.*?-->", "", secs.get("Foundation", ""), flags=re.S), secs.get("Architecture", "")
    evidence = evidence_lines(body)
    ui, agent = (base / "DESIGN.md").is_file(), st.header.get("Agent") == "yes"
    placeholders, test_vars = env_example_keys(base)
    # E2: the placeholder guard replayed through the real entrypoint, not a unit test of the validator - a logged run's
    # validator passed its test while the app answered /health on every placeholder
    if placeholders and not any(re.search(r"\.env\.example|--env-file", evidence_command(e))
                                and not TEST_RUNNERS.search(evidence_command(e)) for e in evidence):
        gaps.append("no evidence line boots the app on .env.example's placeholders: start it the way prod does on "
                    "the unedited file (devserver.py refuses --cmd \"<start>\" ... --env-file .env.example, or the "
                    "image with --env-file .env.example) and record that command - a unit test of the validator is not "
                    "this proof (verify.md §Guards)")
    # E8: the seed stops at identity - money types reach the database at /contracts, where their units are decided
    for p in foundation_files(base, set(MONEY_COLUMN)):
        rel = p.relative_to(base).as_posix()
        if is_test(rel):
            continue
        names = sorted({n for m in MONEY_COLUMN[p.suffix.lower()].finditer(read_text(p)) for n in m.groups()
                        if n and is_money(n) and not re.search(rf"(?im)^.*\b{n}\b.*\bfloat\b", body)})  # named, why
        if names:
            gaps.append(f"{rel} stores money as a float ({', '.join(names[:4])}): money columns and domain models are "
                        f"/contracts' - the seed stops at identity (skeleton-steps.md §2.); or name the field on a "
                        f"line of #Foundation with why it is a float")
    # E11: untrusted input is defended by structure, never a list of phrases a reworded attack walks past
    if agent:
        for p in foundation_files(base, SOURCE):
            rel = p.relative_to(base).as_posix()
            if is_test(rel) or "evals/" in f"/{rel}":  # an eval case's attack text is data, not a guard
                continue
            hits = [l for l in read_text(p).splitlines() if PHRASE_LIST.search(l) and not l.lstrip().startswith("#")]
            if len(hits) >= 2 or any(re.search(r"re\.compile|RegExp|new RegExp|/[gimsu]*\s*[,)]", l) for l in hits):
                gaps.append(f"{rel} matches injection phrases ({hits[0].strip()[:60]}...): a blocklist is not the "
                            f"defence - pass tool output to the model as data and let the policy gate decide actions "
                            f"(AGENT.md §Foundation item 6)")
        blocks = [b for b in item_blocks(body) if "evidence:" in b]
        missing = [what for what, rx in AGENT_ITEMS
                   if not any(re.search(rx, b.splitlines()[0], re.I) for b in blocks)]
        if missing:
            gaps.append(f"Agent: yes - no evidence line for AGENT.md §Foundation item {', '.join(missing)}: each item "
                        f"gets a line naming it and its `evidence:`")
    # E9 + the audit: a UI's tokens resolve at runtime (or its shell renders), and the audit is a gate, not a memory
    if ui:
        if not any(UI_PROOF.search(e) for e in evidence) and not open_item_says(st, r"design token|stylesheet|\bUI shell\b|\bthe shell\b"):
            gaps.append("UI product: no evidence line reads a design token back at runtime, or shows a route rendering "
                        "the UI shell when DESIGN.md chose no stylesheet (skeleton-steps.md §7.)")
        copy = next((p for p in foundation_files(base, {".py"}) if p.as_posix().endswith("frontend-audit/audit.py")),
                    None)
        hook_text, ci_text = text_of(base, HOOK_CONFIGS), ci_and_what_it_calls(base)
        if copy is None:
            gaps.append("UI product: no committed copy of the frontend audit (<tooling>/frontend-audit/audit.py): copy "
                        "the installed engine and run it from the commit hook and CI (skeleton-steps.md §6.)")
        else:
            where = [w for w, t in (("the commit hook", hook_text), ("CI", ci_text)) if "frontend-audit" not in t]
            if where:
                gaps.append(f"UI product: {' and '.join(where)} never run{'s' if len(where) == 1 else ''} "
                            f"{copy.relative_to(base).as_posix()}: a gate you must remember is not a gate")
    # CI runs both scans, fail-closed; the secret scan reads what git holds, never the working folder
    if any((base / c).exists() for c in CI_FILES):
        ci_text = ci_and_what_it_calls(base)
        lacks = [w for w, rx in (("a secret scan", SECRET_SCANNERS), ("a dependency-vulnerability scan", DEP_SCANNERS))
                 if not re.search(rf"(?i)\b(?:{rx})\b", ci_text)]
        if lacks and not open_item_says(st, r"secret scan|dependency|vulnerab|CVE"):
            gaps.append(f"CI runs no {' and no '.join(lacks)} (directly or through the task runner it calls): add "
                        f"{'them' if len(lacks) > 1 else 'it'}, failing on a finding")
    for name in (*HOOK_CONFIGS, *CI_FILES, "justfile", "Justfile", "Makefile", "package.json"):
        p = base / name
        files = [f for f in sorted(p.rglob("*")) if f.is_file()] if p.is_dir() else [p] if p.is_file() else []
        for f in files:
            bad = [l.strip() for l in read_text(f).splitlines()
                   if WORKING_FOLDER_SCAN.search(l) and not l.lstrip().startswith(("#", "//"))]
            if bad:
                gaps.append(f"{f.relative_to(base).as_posix()} runs `{bad[0][:70]}`: that reads the working folder "
                            f"(the gitignored .env, .venv) - scan what git holds: `gitleaks git` (CI, the history) and "
                            f"`gitleaks git --staged` (the hook)")
    # the dependency-update bot, on day one
    if not any((base / b).is_file() for b in UPDATE_BOTS) and not open_item_says(st, r"dependabot|renovate|"
                                                                                       r"dependency[- ]update"):
        gaps.append("no dependency-update bot (.github/dependabot.yml or a Renovate config): wire it now, grouping "
                    "tightly-coupled packages, or record why not with `status.py open --from foundation`")
    # the contract's Writes: the runbook someone opens at 2am
    if not (base / "docs" / "runbook.md").is_file() and not list((base / "docs").glob("runbook*.md")):
        gaps.append("no docs/runbook.md: boot, the .env variables and how to generate each, what every guard refuses "
                    "and how to prove it, reset and re-seed, the suite on the isolated datastore (Step 3)")
    # the isolated test datastore has its own variable, unless the record says each test rolls back
    if DATASTORES.search(arch) and (base / ".env.example").is_file() and not test_vars \
            and not re.search(r"(?i)roll(?:s|ed)? back|rollback", body):
        gaps.append("the test datastore has no variable of its own in .env.example (TEST_DATABASE_URL or the chosen "
                    "datastore's equivalent): sharing the development datastore is not isolation (test-datastore.md)")
    return gaps + foundation68_gaps(base, st, body, arch, evidence)


# next.68 - what the logged 4-tool /foundation round found that the record checks let through (each a refusal below):
# runbooks and records naming the playbook's install or the owner's own folders (a clone breaks), no type checker,
# an echo fake under the golden tests, a real AI adapter that did not fit its caller, a provider error that crashed
# the run, a secret scan that skipped .env.example or did nothing at all, invented plants and results, a PowerShell
# recipe that proved nothing, `localhost` URLs that hang on Windows + Docker.
RUNBOOK_FILES = ("docs/runbook.md",)
RUNNER_FILES = ("justfile", "Justfile", ".justfile", "Makefile", "package.json", "Taskfile.yml", "Taskfile.yaml")
# a file inside the playbook's install, or this machine's own folders - neither exists in a teammate's clone
INSTALL_FILE = re.compile(r"(?i)(?<![\w-])\.(?:agents|codex|gemini|claude[/\\](?:skills|product-playbook|agents|plugins)|"
                          r"cursor[/\\](?:agents|skills))[/\\][\w./\\-]*|plugins[/\\]cache[/\\]|<playbook>|"
                          r"\$\{?CLAUDE_PLUGIN_ROOT\}?")
PERSONAL_PATH = re.compile(r"(?i)\b[a-z]:[/\\]+Users[/\\]+[^/\\\s`'\"]+|file:///|(?<![\w.])/(?:home|Users)/[^/\s`'\"]+/")
PY_TYPECHECK = r"\b(?:pyright|basedpyright|mypy|pyre|pytype)\b|\bty check\b"
TS_TYPECHECK = r"\btsc\b|vue-tsc|svelte-check|astro check|nuxi typecheck"
# "the real model only with a flag" is not this proof (a logged record): the adapter itself, in the caller's place
REAL_ADAPTER = re.compile(r"(?i)\breal (?:[\w-]+ )?(?:adapter|provider|client)\b")
PROVIDER_DOWN = re.compile(r"(?i)dead[ _-](?:end[ _]?point|url|host|port)|unreachable|127\.0\.0\.1:9\b|connection (?:error|"
                           r"refused|failure)|provider (?:fails|failure|down|error)|\bdown\b|time[sd]? ?out|"
                           r"APIError|outage")
AI_PROVIDER = re.compile(r"(?i)\bLLM|model provider|\bAI provider|anthropic|openai|mistral|gemini|bedrock|litellm|"
                         r"azure openai|vertex")
FALLBACK = re.compile(r"(?i)hand(?:s|ed)?(?:[- ]?(?:off|over)| (?:it |the \w+ )?to)|fallback|falls? back|degrad|works as today|to a (?:person|"
                      r"human)|not sure")
MODEL_CALLS = {"complete", "acomplete", "generate", "agenerate", "chat", "achat", "invoke", "ainvoke", "run", "arun",
               "predict", "create", "respond", "reply", "draft", "request", "call", "__call__"}
FAKE_CLASS = re.compile(r"(?i)fake|stub|echo|dummy|scripted|mock")
EVAL_MISS = re.compile(r"(?i)\bmiss(?:es|ed)?\b|\bwrong\b|regress|scores? [^\n]{0,20}\bfail|fails on|\bred\b")
NOOP_SCAN = re.compile(r"(?i)detect_secrets\.main|detect-secrets\s+scan\b(?![^\n]*--baseline[^\n]*&&)|"
                       r"(?:gitleaks|trufflehog|detect-secrets\S*|ggshield|secretlint)[^\n|]*(?:\|\|\s*(?:true|exit 0|:)\b|"
                       r";\s*true\b)")
# a database URL on localhost - a value, a "Form:" comment or a runbook table: each is what someone copies into .env
DB_URL_LOCALHOST = re.compile(r"(?im)(?:^\s*([A-Z][A-Z0-9_]*)\s*=\s*)?\S*?\b(?:postgres(?:ql)?(?:\+\w+)?|mysql(?:\+\w+)?|"
                              r"mariadb|redis|rediss|mongodb(?:\+srv)?|amqp|nats)://(?:[^\s@/]*@)?localhost\b")
SHELL_LOADS_ENV = re.compile(r"(?i)source \.env|(?:^|\s)\. \.?/?\.env\b|set -a|Get-Content[^\n]*\.env|dotenv|"
                             r"export \$\(|proof\.py --env")
PROOF_LOG = "playbook-proofs.jsonl"


def project_texts(base: Path, names) -> list[tuple[str, str]]:
    out = []
    for n in names:
        p = base / n
        files = [f for f in sorted(p.rglob("*")) if f.is_file()] if p.is_dir() else [p] if p.is_file() else []
        out += [(f.relative_to(base).as_posix(), read_text(f)) for f in files]
    return out


def runbook_texts(base: Path) -> list[tuple[str, str]]:
    return project_texts(base, RUNBOOK_FILES) + [(p.relative_to(base).as_posix(), read_text(p)) for p in
                                                  sorted((base / "docs").glob("runbook?*.md"))]


def install_path_gaps(base: Path, body: str) -> list[str]:
    """Fix 1: what a teammate's clone runs never points into the playbook's install or this machine's folders."""
    out = []
    sources = [("#Foundation", body)] + runbook_texts(base) + project_texts(base, (*RUNNER_FILES, *HOOK_CONFIGS,
                                                                                  *CI_FILES))
    for name, text in sources:
        hit = next(((m.group(0), kind) for l in text.splitlines()
                    for m, kind in ((PERSONAL_PATH.search(l), "personal"), (INSTALL_FILE.search(l), "install")) if m),
                   None)
        if hit:
            out.append(f"{name} names `{hit[0][:60]}` - " + (
                "a file of the playbook's install, which is gitignored and personal, so a clone breaks: the runbook "
                "and task runner use the project's own commands (a task-runner target, or devserver.py / ci_local.py "
                "copied into the repo's tooling folder and committed); an evidence line names the tool alone "
                "(`devserver.py check ...`)" if hit[1] == "install" else
                "a folder on this machine only: write a path relative to the repo (an evidence line names the tool "
                "alone, a scratch file as <scratch>/<name>)"))
    return out


def runbook_gaps(base: Path, arch: str) -> list[str]:
    """Fix 1 + 7: the runbook boots a fresh clone, cites files that exist, and its recipes run in PowerShell too."""
    out = []
    keys = re.findall(r"(?m)^\s*([A-Z][A-Z0-9_]*)\s*=", read_text(base / ".env.example"))
    for name, text in runbook_texts(base):
        if (base / ".env.example").is_file() and ".env.example" not in text:
            out.append(f"{name} never says how .env is made from .env.example: a newcomer's first boot stops at the "
                       f"guard - add the step (copy it, then the values to set and how to make each)")
        if DATASTORES.search(arch) and not re.search(r"(?i)\bsqlite\b", " ".join(DATASTORES.findall(arch))) and \
                not re.search(r"(?i)migrat|bootstrap|createdb|create (?:the )?database|\bdb[-_ ]?(?:up|setup|create|"
                              r"init|reset)\b|compose up|setup", text):
            out.append(f"{name} never creates or migrates the dev database: a fresh clone has none - name the "
                       f"command (the task runner's bootstrap/migrate target)")
        cited = sorted({m.group(1) for m in re.finditer(r"`([\w.-]+(?:/[\w.-]+)+\.[A-Za-z0-9]{1,6})(?:::[\w\[\]-]+)?`",
                                                        text)})
        missing = [c for c in cited if not (base / c).exists() and not install_root(c)]
        if missing:
            out.append(f"{name} cites {', '.join(missing[:4])}, which do{'es' if len(missing) == 1 else ''} not exist "
                       f"in the repo: fix the path or drop the line")
        if not SHELL_LOADS_ENV.search(text):
            for m in re.finditer(r"\$env:\w+\s*=\s*\$env:(\w+)|(?<![\w$])\w+=[\"']?\$\{?(\w+)\}?", text):
                var = m.group(1) or m.group(2)
                if var in keys:
                    out.append(f"{name}: `{m.group(0)}` reads {var} from the shell, but it lives in .env - in a fresh "
                               f"shell it is empty and the recipe proves nothing (a logged PowerShell recipe ran the "
                               f"suite green instead of refusing): give the value, or one command for both shells "
                               f"(a task-runner target, or `proof.py --env KEY=@{var} -- <command>`)")
                    break
    return out


def type_check_gaps(base: Path, body: str, st: "Status") -> list[str]:
    """Fix 2: a typed language gets its type checker in the hooks or CI (a plain run had pyright strict, 0 errors)."""
    names = {p.name for p in foundation_files(base, {".toml", ".txt", ".json", ".cfg", ".py"})}
    text = text_of(base, HOOK_CONFIGS) + "\n" + ci_and_what_it_calls(base) + "\n" + text_of(base, RUNNER_FILES)
    if re.search(r"(?i)\bno type[- ]?check", body) or open_item_says(st, r"type[- ]?check"):
        return []
    out = []
    if names & {"pyproject.toml", "setup.py", "setup.cfg"} and not re.search(PY_TYPECHECK, text, re.I):
        out.append("a Python project with no type checker in the hooks or CI (pyright or mypy): add the one "
                   "#Architecture recorded, or the user's choice from the step-0 card, failing on an error - or "
                   "record why not: a #Foundation line `no type checker: <the user's reason>`")
    if "tsconfig.json" in names and not re.search(TS_TYPECHECK, text, re.I):
        out.append("a TypeScript project with no type check in the hooks or CI (`tsc --noEmit`, or vue-tsc / "
                   "svelte-check): add it, failing on an error - or record why not (`no type checker: <reason>`)")
    return out


def echo_fakes(base: Path) -> list[str]:
    """Fix 3: a fake model whose answer is its own input - golden and behaviour tests on it pass by construction."""
    import ast
    out = []
    for p in foundation_files(base, {".py", ".ts", ".tsx", ".js"}):
        rel = p.relative_to(base).as_posix()
        if not (is_test(rel) or re.search(r"(?i)(^|/)(evals?|fakes?|stubs?|mocks?)(/|\.|_)", rel)):
            continue
        text = read_text(p)
        if p.suffix != ".py":
            m = re.search(r"(?is)class\s+(\w*(?:Fake|Stub|Echo|Dummy|Mock)\w*).*?\b(" + "|".join(MODEL_CALLS - {
                "__call__"}) + r")\s*\(\s*(\w+)[^)]*\)\s*(?::[^{]+)?\{\s*return\s+(?:`[^`]*\$\{\s*)?\3\b", text)
            if m:
                out.append(f"{rel}: {m.group(1)}.{m.group(2)} returns its input")
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and FAKE_CLASS.search(n.name)):
            for fn in (n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                       and n.name in MODEL_CALLS):
                params = {a.arg for a in fn.args.args + fn.args.kwonlyargs} - {"self", "cls"}
                if fn.args.vararg:
                    params.add(fn.args.vararg.arg)
                for r in (n for n in ast.walk(fn) if isinstance(n, ast.Return) and n.value is not None):
                    funcs = {id(c.func) for c in ast.walk(r.value) if isinstance(c, ast.Call)}
                    used = {n.id for n in ast.walk(r.value) if isinstance(n, ast.Name) and id(n) not in funcs}
                    if used and used <= params:
                        out.append(f"{rel}: {cls.name}.{fn.name} returns its input ({', '.join(sorted(used))})")
                        break
    return out


def ai_adapter_gaps(base: Path, body: str, arch: str, st: "Status") -> list[str]:
    """Fix 4 + 5: the REAL provider adapter fits the caller's interface, and its failure takes #Architecture's path."""
    if not (st.header.get("AI product") == "yes" or st.header.get("Agent") == "yes") or not AI_PROVIDER.search(arch):
        return []
    blocks = [b for b in item_blocks(body) if "evidence:" in b]
    real = [b for b in blocks if REAL_ADAPTER.search(b)]
    out = []
    if not real:
        out.append("no evidence line shows the REAL AI adapter in the caller's place: a test builds the real adapter "
                   "(no network: point it at a dead endpoint) and passes it where the caller takes the fake - a "
                   "fake can fit a method the real class lacks (a logged loop called `.complete`, the adapter had "
                   "only `acomplete`) (skeleton-steps.md §5.)")
    lines = sorted((b for b in item_blocks(arch) if AI_PROVIDER.search(b) and FALLBACK.search(b)), key=len)  # the bullet
    if lines and not any(PROVIDER_DOWN.search(b) for b in real):
        out.append(f"#Architecture records what happens when the AI provider fails ({' '.join(lines[0].split())[:90]}"
                   f"...) and no evidence line shows it: the real adapter on a dead endpoint -> that path (a hand-off), "
                   f"not an exception (a logged run's connection error crashed the run) (skeleton-steps.md §5.)")
    return out


def secret_scan_gaps(base: Path) -> list[str]:
    """Fix 6 + B: the scan reads .env.example too, and no scanner line is a no-op."""
    out = []
    for n in (".gitleaks.toml", "gitleaks.toml", ".github/gitleaks.toml"):
        m = re.search(r"(?s)\bpaths\s*=\s*\[(.*?)\]", read_text(base / n)) if (base / n).is_file() else None
        if m and re.search(r"env\\?\.example", m.group(1)):
            out.append(f"{n} allowlists .env.example by its path: a real key pasted there is never caught - allowlist "
                       f"only the documented placeholder values (`regexes`), never the file")
    for name, text in project_texts(base, (*HOOK_CONFIGS, *CI_FILES, *RUNNER_FILES)):
        bad = [l.strip() for l in text.splitlines() if NOOP_SCAN.search(l) and not l.lstrip().startswith(("#", "//"))]
        if bad:
            out.append(f"{name} runs `{bad[0][:80]}`: that secret scan cannot fail (it writes a baseline, or its "
                       f"failure is swallowed) - run the scanner's failing form (`gitleaks git --staged`, "
                       f"`detect-secrets-hook --baseline ...`)")
    return out


def localhost_gaps(base: Path) -> list[str]:
    """Fix 8: on Windows + Docker `localhost` may resolve to ::1 first and hang; 127.0.0.1 never does."""
    out = []
    for name, text in [(".env.example", read_text(base / ".env.example"))] + runbook_texts(base):
        hits = [m.group(1) or m.group(0).split("://")[0].strip("`'\"(") for m in DB_URL_LOCALHOST.finditer(text)]
        if hits:
            out.append(f"{name} connects to a database with `localhost` ({', '.join(dict.fromkeys(hits[:4]))}): write "
                       f"127.0.0.1 - on Windows with Docker, localhost can resolve to IPv6 ::1 first and hang (a "
                       f"logged run lost a boot to it)")
    return out


def proof_entries(base: Path) -> list[dict]:
    g = git(base, "rev-parse", "--git-common-dir")
    if not g:
        return []
    f = (Path(g) if Path(g).is_absolute() else base / g) / PROOF_LOG
    out = []
    for line in read_text(f).splitlines() if f.is_file() else []:
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


RUNNER_PREFIX = re.compile(r"^(?:(?:uv|poetry|pdm|hatch) run|npx|pnpm (?:exec|dlx)|bunx|python3? -m|py -m)\s+", re.I)


def cmd_tokens(s: str) -> list[str]:
    """A command as comparable words: placeholders, asides and the interpreter dropped, a path by its last part."""
    s = re.sub(r"<[^<>]*>|\([^()]*\)|`|\.\.\.|…", " ", s)
    s = re.sub(r"^\s*(?:\$env:\w+\s*=\s*\S+\s*;\s*|[A-Za-z_]\w*=\S*\s+)+", "", s)  # leading env assignments
    s = re.sub(r"^\s*(?:\S*python\S*\s+)?\S*proof\.py\s+(?:--env\s+\S+\s+)*(?:--\s+)?(?!plant)", "", s)  # the wrapper
    s = s.strip()
    while True:
        t = re.sub(r"^\S*python(?:3(?:\.\d+)?)?(?:\.exe)?\s+(?!-m\b)", "", s, flags=re.I)
        t = RUNNER_PREFIX.sub("", t)
        if t == s:
            break
        s = t
    out = []
    for t in s.split():
        t = t.strip("\"'“”,;")
        if not t:
            continue
        if re.search(r"[/\\]", t) and "://" not in t and not t.startswith("-"):
            t = re.split(r"[/\\]", t.rstrip("/\\"))[-1] or t
        out.append(t.lower())
    return out


def significant(toks: list[str]) -> set[str]:
    keep = set(toks[:1])
    if len(toks) > 1 and not toks[1].startswith("-"):
        keep.add(toks[1])
    return keep | {t for t in toks if t.startswith("-") or re.search(r"[.:/]", t)}


def entry_tokens(e: dict) -> list[str]:
    return cmd_tokens(str(e.get("cmd", "")))


def result_contradiction(result: str, e: dict) -> str:
    """'' when the line's result agrees with what the log saw; else what disagrees."""
    tail = " ".join(str(e.get("tail", "")).split()).lower()
    m = re.search(r"(?i)\bexit(?: code)?\s*[=:]?\s*(\d+)", result)
    if m and int(m.group(1)) != int(e.get("exit", -1)):
        return f"says exit {m.group(1)}, the run exited {e.get('exit')}"
    for n, w in re.findall(r"(?i)\b(\d+) (passed|failed|skipped|errors?)\b", result):
        if not re.search(rf"\b{n} {w.lower()}", tail):
            return f"says {n} {w}, the run's output does not"
    for q in re.findall(r"(?:^|(?<=[\s(]))[\"“]([^\"”]{8,}?)[\"”](?=[\s,.;:)]|$)", result):
        q = " ".join(q.rstrip("…. ").split()).lower()
        if q and q not in tail:
            return f"quotes \"{q[:50]}\", which the run never printed"
    if re.search(r"(?i)\brefus|\bfailed\b|\bblocked\b|\brejected\b|\bexit [1-9]", result) and int(e.get("exit", 0)) == 0 \
            and not re.search(r"refus|fail|error|block|reject|denied|exit [1-9]", tail):
        return "says it was refused, the run exited 0 and printed no refusal"
    return ""


def proof_gaps(base: Path, evidence: list[str]) -> list[str]:
    """A: every `evidence:` line cites a run the proof log holds (proof.py / devserver.py / ci_local.py wrote it), and
    says what that run showed - a logged record cited a plant that never happened and results a re-run did not give."""
    entries = proof_entries(base)
    runs = [e for e in entries if e.get("kind") == "run"]
    plants = [e for e in entries if e.get("kind") == "plant"]
    unseen, wrong = [], []
    for line in evidence:
        cmd, result = re.split(r"→|->", line, maxsplit=1) if re.search(r"→|->", line) else (line, "")
        result = result.split(" · ")[0]
        if re.match(r"(?i)\W*browser\b", cmd):
            continue  # a browser check: judged, never a command's proof
        if re.search(r"(?i)\bplant(?:ed|ing)?\b", cmd):
            if re.search(r"(?i)\bsecret|api[- ]?key|fake (?:\w+ )?(?:token|key)|\bghp_|github token|aws key", cmd):
                continue  # the secret plant is set's own (secret_plant_gap)
            value = re.search(r"#[0-9a-fA-F]{3,8}\b", cmd)
            paths = [re.split(r"[/\\]", t)[-1] for t in re.findall(r"[\w./\\-]+\.[A-Za-z0-9]{1,6}\b", cmd)]
            hit = [p for p in plants if (not paths or any(str(p.get("file", "")).endswith(x) for x in paths))
                   and (not value or value.group(0).lower() in str(p.get("text", "")).lower())]
            if not hit:
                unseen.append(f"`{' '.join(cmd.split())[:80]}` (no logged plant of that value in that file)")
            elif re.search(r"(?i)refus|fail|block|exit [1-9]", result) and not any(p.get("refused") for p in hit):
                wrong.append(f"`{' '.join(cmd.split())[:60]}` says refused, the logged plant went through")
            continue
        parts = [p for p in re.split(r"(?i)\bthen\b|;|&&", cmd) if cmd_tokens(p)]
        matched = []
        for part in parts:
            toks = cmd_tokens(part)
            sig = significant(toks)
            m = sorted((e for e in runs if (et := entry_tokens(e)) and et[0] == toks[0] and sig <= set(et)),
                       key=lambda e: len(set(entry_tokens(e)) ^ set(toks)))  # the closest run first
            if not m:
                unseen.append(f"`{' '.join(part.split())[:80]}`")
                break
            matched += m
        else:
            if matched and result:
                why = [result_contradiction(result, e) for e in matched]
                if all(why):
                    wrong.append(f"`{' '.join(cmd.split())[:60]}` {why[0]}")
    out = []
    if unseen:
        out.append(f"{len(unseen)} evidence line(s) cite a run the proof log never saw: {'; '.join(unseen[:4])}"
                   f"{' ...' if len(unseen) > 4 else ''} - run each proof through `proof.py -- <command>` "
                   f"(devserver.py and ci_local.py log their own; a plant: `proof.py plant --file <path> --text "
                   f"\"<what>\"`) and cite what it printed, never a result written afterwards")
    if wrong:
        out.append(f"{len(wrong)} evidence line(s) say what the logged run did not: {'; '.join(wrong[:4])} - cite the "
                   f"run's own result")
    return out


def secret_plant_gap(base: Path, st: "Status") -> list[str]:
    """B: `set` plants a fresh fake token in a throwaway copy and commits it through the installed hooks - a logged
    hook ran a scanner command that exits 0 doing nothing, and two planted tokens were committed."""
    if not hooks_state(base)[1] or open_item_says(st, r"secret[- ]scan"):  # no commit yet: the snapshot has no parent
        return []
    f = tool_file("foundation", "proof.py")
    if f is None:
        return []
    import importlib.util
    spec = importlib.util.spec_from_file_location("playbook_proof", f)
    proof = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(proof)
        entry = proof.plant_secret(base)
        proof.log(base, entry)
    except (SystemExit, Exception) as e:  # noqa: BLE001 - reported, never a crash of the record call
        return [f"the secret-scan proof could not run ({str(e)[:120]}): fix it, or record why with `status.py open "
                f"--from foundation --what \"secret scan not proven: <why>\"`"]
    if entry["refused"]:
        return []
    lines = [l for l in entry["tail"].splitlines() if l.strip()][-3:]
    return [f"the commit hooks let a planted fake secret through (set planted a fresh fake GitHub token in a "
            f"throwaway copy and committed it: {' | '.join(lines)[:200]}) - the secret scan in the hook does not "
            f"block: run the scanner's failing form (`gitleaks git --staged`), then run this `set` again"]


def foundation68_gaps(base: Path, st: "Status", body: str, arch: str, evidence: list[str]) -> list[str]:
    gaps = install_path_gaps(base, body) + runbook_gaps(base, arch) + type_check_gaps(base, body, st)
    fakes = echo_fakes(base)
    if fakes:
        gaps.append(f"a fake model returns its input ({'; '.join(fakes[:3])}): golden and behaviour tests on it pass "
                    f"by construction - a fake answers from a script (fixed replies, one of them wrong, which the "
                    f"harness must score as a miss) (skeleton-steps.md §5.)")
    if st.header.get("Agent") == "yes":
        item7 = [b for b in item_blocks(body) if "evidence:" in b and re.search(AGENT_ITEMS[6][1],
                                                                                 b.splitlines()[0], re.I)]
        if item7 and not any(EVAL_MISS.search(b) for b in item7):
            gaps.append("Agent: yes - the eval harness's evidence never shows it failing: run it on one scripted "
                        "WRONG case and show the miss (a harness that cannot fail proves nothing)")
    gaps += ai_adapter_gaps(base, body, arch, st) + secret_scan_gaps(base) + localhost_gaps(base)
    gaps += proof_gaps(base, evidence) + secret_plant_gap(base, st)
    return gaps


def foundation_facts(st: "Status", base: Path, found: str) -> list[str]:
    """What the steps need to know about this project and machine, computed once."""
    slug = project_slug(st, base)
    remote = git(base, "remote")
    out = [f"  - project: {slug} - a local container is `{slug}-pg` (or the engine's name), databases "
           f"`{slug.replace('-', '_')}_dev` and `{slug.replace('-', '_')}_test`, never another project's "
           f"(skeleton-steps.md §4.)",
           f"  - git: branch {git(base, 'branch', '--show-current') or '(none)'} · remote: "
           + (remote.replace(chr(10), ', ') if remote else "none - CI's proof is ci_local.py plus the open item "
                                                           "`CI has not run on a remote`")]
    mans = []
    for f in foundation_files(base):
        if f.name in LOCKS:
            lock = next((lk for lk in LOCKS[f.name] for d in (f.parent, base) if (d / lk).is_file()), None)
            mans.append(f"{f.relative_to(base).as_posix()} ({lock or 'NO LOCKFILE yet'})")
    none = "none yet - step 1 writes the dependencies into the one /structure created"
    out.append(f"  - manifests: {', '.join(mans) or none}")
    py = base / "pyproject.toml"
    if py.is_file():
        pin = re.search(r"^requires-python\s*=\s*[\"']([^\"']+)", read_text(py), re.M)
        have = env_python(base)
        out.append(f"  - Python: pins {pin.group(1) if pin else '(no requires-python)'} · .venv "
                   f"{'.'.join(map(str, have)) if have else 'not created yet'}")
    hooks, installed = hooks_state(base)
    out.append(f"  - commit hooks: {', '.join(hooks) or 'none configured'}"
               + (f" · installed: {'yes' if installed else 'NO - install them (step 6)'}" if hooks else ""))
    out.append(f"  - CI: {', '.join(c for c in CI_FILES if (base / c).exists()) or 'none yet (step 8)'}")
    ph, tv = env_example_keys(base)
    names = (": " + ", ".join(ph[:14]) + (" ..." if len(ph) > 14 else "")) if ph else ""
    dot_env = "exists (the user's - never print its values)" if (base / ".env").is_file() else "not created yet"
    out.append(f"  - .env.example: {len(ph)} CHANGE_ME variable(s){names} · test datastore variable: "
               f"{', '.join(tv) or 'none yet (step 4)'} · .env {dot_env}")
    secs = product_sections(read_text(base / "PRODUCT.md")) if (base / "PRODUCT.md").is_file() else {}
    arch = secs.get("Architecture", "")
    engines = sorted({m.group(1).lower() for m in DATASTORES.finditer(arch)})
    custody = [" ".join(l.split())[:220] for l in arch.splitlines() if re.search(r"(?i)custody", l)][:1]
    out.append(f"  - #Architecture's datastore: {', '.join(engines) or 'none named'}"
               + (f" · {custody[0]}" if custody else "") + " - the tests use the same engine (test-datastore.md)")
    ui = (base / "DESIGN.md").is_file()
    out.append("  - UI: " + ("DESIGN.md exists - the frontend audit joins the hooks and CI (step 6), the tokens or the "
                             "shell are proven at runtime (step 7)" if ui else "no DESIGN.md - steps 6's audit and 7 "
                                                                               "do not apply"))
    words = (arch + secs.get("Structure", "")).lower()
    tools = [t for t in FOUNDATION_TOOLS if t == "docker" or re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", words)]
    out.append("  - on this machine: " + " · ".join(f"{t} {'yes' if shutil.which(t) else 'NOT FOUND'}" for t in tools)
               + " - a tool not found: ask the user once, in the step-0 card (MECHANISMS-ON-DEMAND.md §Context hygiene)")
    dev = tool_file("foundation", "devserver.py")
    ci = tool_file("foundation", "ci_local.py")
    cmd, port, health = dev_server(base, found)
    start = (f"--cmd \"{cmd or '<start command>'}\" --port {port or '<port>'} --health {health or '<health url>'}")
    if dev:
        out += [f"  - boot (item 1, Step 3b): python {dev.as_posix()} check {start}",
                f"  - the placeholder proof (Step 3b): python {dev.as_posix()} refuses {start} --env-file .env.example "
                f"- never copy over the user's .env",
                f"  - leave it running / stop it: devserver.py start ... · devserver.py stop --port <port> - never a "
                f"background start of your own (a logged run spent 14 calls on a port Windows kept)"]
    if ci:
        out.append(f"  - CI's steps here (Step 3b, after a commit): python {ci.as_posix()} - one replay; a step "
                   f"failing for this machine's reason: --skip it (UNVERIFIED); after a fix, --only that step")
    pf = tool_file("foundation", "proof.py")
    if pf:
        out.append(f"  - every other proof (Step 3b): python {pf.as_posix()} -- <command> (it logs what the run printed; "
                   f"`set` matches each evidence line to the log) · the dev-DB refusal: proof.py --env "
                   f"TEST_DATABASE_URL=@DATABASE_URL -- <test command> · a plant: proof.py plant --file <path> --text "
                   f"\"<what>\" --also \"<the CI step>\" (a throwaway copy, your folder untouched) · the secret plant is "
                   f"`set`'s own")
    out.append("  - project files (runbook, task runner, CI, hooks) name the project's own commands: devserver.py, "
               "ci_local.py and proof.py are the playbook's and a clone has none - copy one into the repo's tooling "
               "folder and commit it before a project file names it")
    langs = [n for n, rx in (("Python", r"(?i)\bpython\b"), ("TypeScript", r"(?i)\btypescript\b|\btsx?\b"))
             if re.search(rx, words)]
    if langs:
        tc = re.search(rf"(?i){PY_TYPECHECK}|{TS_TYPECHECK}", words)
        out.append(f"  - type checker ({', '.join(langs)}): " + (
            f"{tc.group(0)} (#Architecture) - in the hooks and CI (step 6)" if tc else
            "#Architecture names none - ask in the step-0 card: pyright (Recommended) / mypy / tsc --noEmit / none "
            "(the user's reason, recorded as `no type checker: <reason>`)"))
    missing = []
    if not (base / ".gitattributes").is_file() and tool_file("templates", "gitattributes"):
        missing.append(f"no .gitattributes: copy {tool_file('templates', 'gitattributes').as_posix()}")
    if "gitleaks" in words and not any((base / n).is_file() for n in (".gitleaks.toml", "gitleaks.toml")) \
            and tool_file("templates", "gitleaks.toml"):
        missing.append(f"gitleaks has no config: copy {tool_file('templates', 'gitleaks.toml').as_posix()}")
    if ui and tool_file("frontend-audit", "audit.py"):
        out.append(f"  - the frontend audit engine to copy (step 6): {tool_file('frontend-audit', 'audit.py').as_posix()}")
    out += [f"  - {m}" for m in missing]
    return out


def ref_text(name: str) -> str:
    f = tool_file("foundation", "references", name)
    if f is None:
        return ""
    lines = read_text(f).splitlines()
    while lines and (lines[0].startswith(">") or not lines[0].strip()):  # the header says how it is opened
        lines.pop(0)
    return "\n".join(lines).rstrip()


FOUNDATION_SPLIT = "\n===== PRODUCT.md - the sections this phase derives from ====="
# Claude Code's Bash tool cuts a command's output at 30,000 characters (its tool description); the start with the
# notes above it must stay under that. The four commands before next.66 each did (the largest 27.9 KB); one 68 KB
# start would not. Over this size the facts, the refusals and the order print inline, the rest goes to one file.
FOUNDATION_INLINE = 22000


def foundation_start_out(st: "Status") -> str:
    """What `next --phase foundation` prints after its notes. Antigravity (~4 KB window, cut from the top): the head
    and the whole start in the tools folder's file (fit_start). Elsewhere: whole when it fits, else the inline part
    and one file in the project's .git folder (never committed, never another project's) to read once."""
    full = foundation_start_text(st)
    if playbook_tool() == "antigravity":
        return fit_start("\n".join(FOUNDATION_HEAD) + "\n\n" + full, "foundation")
    if len(full) <= FOUNDATION_INLINE or FOUNDATION_SPLIT not in full:
        return "\n" + full
    import tempfile
    inline, rest = full.split(FOUNDATION_SPLIT, 1)
    base = st.base if st.base is not None else Path(".")
    folder = base / ".git" if (base / ".git").is_dir() else Path(tempfile.gettempdir()) / (
        "playbook-" + hashlib.sha1(str(base.resolve()).encode()).hexdigest()[:10])
    folder.mkdir(parents=True, exist_ok=True)
    f = folder / "foundation-start.md"
    f.write_text(FOUNDATION_SPLIT.lstrip("\n") + rest + "\n", encoding="utf-8")
    return "\n".join(["", inline, "",
                      f"  - NEXT, in your next call: read `{f.as_posix()}` ONCE, whole (one read: "
                      f"{len(rest.encode('utf-8')) // 1024} KB, too long to print here) - #Architecture, #Structure"
                      f"{', #Design' if (base / 'DESIGN.md').is_file() else ''}"
                      f"{', AGENT.md §Foundation' if st.header.get('Agent') == 'yes' else ''}, the eight steps, the "
                      f"proofs and this phase's rules (`status.py rules foundation` prints the rules alone again). With this "
                      f"output it is everything the phase reads: never open PRODUCT.md, the rule files or the "
                      f"reference files."])


def foundation_start_text(st: "Status") -> str:
    """`next --phase foundation`: one call, everything the phase reads (P1, P2, P25)."""
    base = st.base if st.base is not None else Path(".")
    prod = base / "PRODUCT.md"
    text = read_text(prod) if prod.is_file() else ""
    secs = product_sections(text)
    found = secs.get("Foundation", "")
    ui = (base / "DESIGN.md").is_file()
    out = ["/foundation start - everything this phase reads is below: never open PRODUCT.md, the rule files, AGENT.md "
           "or this skill's reference files (after a summarised conversation, run this `next` again).",
           "Facts from this project, computed - no ls, git status or `which` of your own:",
           *foundation_facts(st, base, found),
           "  - `set foundation filled` refuses, every problem in one list: a cited file or test that does not exist "
           "· hooks configured but not installed · a manifest without its lockfile · a CHANGE_ME variable with a "
           "fallback in code · tests on another engine than #Architecture's · no CI, or no remote and no open item · "
           "no project environment, or a task-runner line outside it · no evidence line booting the app on "
           ".env.example · a money column as a float · Agent: a phrase blocklist, an AGENT.md item with no evidence "
           "line · UI: no token read back (or shell rendered), the audit copy not in the hook and CI · CI without a "
           "secret scan and a dependency scan · `gitleaks dir` · no dependency-update bot · no docs/runbook.md · no "
           "TEST_ datastore variable · an evidence line the proof log never saw, or a result it did not print · "
           "a planted fake secret the hook lets through (set plants it) · a scanner that cannot fail · gitleaks "
           "allowlisting .env.example by path · an install or personal path in the runbook, task runner or record · "
           "a runbook with no .env step, no database step, a missing file or a shell-only recipe · no type checker · "
           "a fake model that echoes its input · AI: no evidence for the real adapter and its failure path · "
           "localhost in .env.example's connection URLs.",
           "  - The order: step-0 card (only a decision an earlier section left open, or a tool not found) · the "
           "eight steps, one progress line each · Step 3b's proofs, each ending in an `evidence:` line · Step 3c and "
           "the #Vision numbers · ONE message: what runs and what was proven (a line each), what is owed, any clash, "
           "then \"Anything to change? If not: Save this "
           "version of your project? (yes / no)\" · on a yes, close each open item this phase settled (`status.py "
           "close <n> --how \"...\"` - the save commits STATUS.md with it), then `set foundation filled "
           "--section-from <file> --commit \"<one line>\"`.",
           "  - Order (each call re-sends all before it): reads and the step-0 card first; docs/runbook.md and the "
           "section file are the last writes, in ONE call after every proof passed, before the ONE message; on the "
           "yes, `set` in the next call - no check of your own between (`set` checks the record and the tree)."]
    names = ["Architecture", "Structure"] + (["Design"] if ui else []) + (["Foundation"] if has_content(found) else [])
    policy = re.sub(r"<!--.*?-->", "", secs.get("Project policy", ""), flags=re.S).strip()
    out.append("\n===== PRODUCT.md - the sections this phase derives from =====")
    if policy:
        out.append(print_sections(prod, ["Project policy"]))
    out.append(print_sections(prod, [n for n in names if n in secs]) if text else "(no PRODUCT.md)")
    if st.header.get("Agent") == "yes":
        out.append(f"\n===== AGENT.md §Foundation - apply every item =====\n"
                   + print_sections(Path(agent_rules()), ["§Foundation"]))
    steps = ref_text("skeleton-steps.md")
    if not ui:  # step 7 and step 6's audit block are a UI product's
        steps = re.sub(r"(?ms)^\*\*UI product \(`DESIGN\.md` exists\): the frontend audit.*?(?=^## )", "", steps)
        steps = re.sub(r"(?ms)^## 7\..*?(?=^## )", "", steps)
    out.append("\n===== skeleton-steps.md - Step 2's eight steps in full =====\n" + steps)
    recipes = tool_file("foundation", "references", "test-datastore.md")
    if recipes:
        out.append("\n===== test-datastore.md =====\n" + print_sections(recipes, ["The recipes"]))
    proofs = re.sub(r"(?ms)^## Saving\n.*?(?=^## |\Z)", "", ref_text("verify.md")).rstrip()  # the save is `set`'s
    out.append("\n===== verify.md - Step 3b's proofs =====\n" + proofs)
    want = {k: list(v) for k, v in PHASE_RULES["foundation"].items()}
    skip = set()
    if prod.is_file():  # what "PRODUCT.md" means is settled once it exists
        skip.add("Spine resolution")
    if not has_content(found):
        skip.add("Re-run semantics")
    if st.state("structure") in ("filled", "overridden"):
        skip.add("Declined runs")
    want["MECHANISMS.md"] = [s for s in want["MECHANISMS.md"] if s not in skip]
    out.append("\n" + rules_text(want, "Rules for /foundation, word for word from the rule files (these ARE the rule "
                                       "files for this phase - do not open them; the close's rules print with `set "
                                       "foundation filled`):"))
    out.append("\n" + print_sections(rule_file("MECHANISMS-ON-DEMAND.md"), ["Context hygiene"]))
    return "\n".join(out)


def how_text() -> str:
    width = max(len(w) for w, _ in HOW)
    return "Which status.py command records what (MECHANISMS.md §Status):\n\n" + "\n".join(
        f"  {when.ljust(width)}  {cmd}" for when, cmd in HOW)


class HelpfulParser(argparse.ArgumentParser):
    """A wrong command prints every command with when to use it, so a run that guessed (`status.py status`,
    `how structure`) finds the right one in the same turn instead of probing with -h."""

    def error(self, message: str) -> None:
        sys.stderr.write(f"{self.prog}: error: {message}\n\n{how_text()}\n")
        raise SystemExit(2)


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):  # a refusal names §2b; a cp1252 console would mangle it
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = HelpfulParser(prog="status.py", description="the one writer of STATUS.md")
    ap.add_argument("--file", default="STATUS.md")
    ap.add_argument("--today", default=dt.date.today().isoformat())
    sub = ap.add_subparsers(dest="cmd", required=True, parser_class=HelpfulParser)
    sub.add_parser("show")
    p = sub.add_parser("next"); p.add_argument("--phase"); p.add_argument("--ticket")
    p.add_argument("--mode", choices=["lean", "full"], help="the user's choice (`/build <id> full`); none: the tool decides")
    p.add_argument("--step", help="/design-system: what one turn needs (foundations | sample | write)")
    p.add_argument("--family", help="/design-system --step: the chosen family, its number or name")
    sub.add_parser("how")
    sub.add_parser("route")
    p = sub.add_parser("rules"); p.add_argument("phase"); p.add_argument("--close", action="store_true")
    p = sub.add_parser("refs"); p.add_argument("phase")
    p = sub.add_parser("engine"); p.add_argument("--write", action="store_true")
    p = sub.add_parser("section"); p.add_argument("path"); p.add_argument("names", nargs="*")
    p.add_argument("--own", action="append", default=[]); p.add_argument("--headings", action="store_true")
    p = sub.add_parser("quote"); p.add_argument("pairs", nargs="+", metavar="FILE WORDS")
    p = sub.add_parser("init"); p.add_argument("--product", required=True)
    p.add_argument("--ai", choices=["yes", "no"])  # no --ui: /vision cannot know it; /architect records it
    p = sub.add_parser("set"); p.add_argument("phase"); p.add_argument("state")
    for o in ("--reason", "--gate", "--due", "--note"):
        p.add_argument(o)
    p.add_argument("--verdict", choices=["pass", "fail"])
    p.add_argument("--section-from", dest="section_from", help="a file holding the section's body: written into "
                   "PRODUCT.md, then checked; refused -> PRODUCT.md is put back")
    # /vision's bookkeeping in its one close call: STATUS.md made, the AI answer recorded (P6)
    p.add_argument("--product", help="set vision on a new project: the product's name - STATUS.md is created")
    p.add_argument("--ai", choices=["yes", "no"]); p.add_argument("--agent", choices=["yes", "no"])
    p.add_argument("--commit", metavar="MESSAGE", help="with filled: save the project (git add + commit) in this call")
    p.add_argument("--no-commit", dest="no_commit", action="store_true", help="dev-check / test: record without "
                   "saving (they save by default; only when the user said not to save)")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", help="run every check, list every gap, write "
                   "nothing (P45: instead of reading the scripts or running a check by hand)")
    p = sub.add_parser("save"); p.add_argument("-m", "--message", required=True)
    p = sub.add_parser("scaffold"); p.add_argument("--from", dest="src", required=True)
    p = sub.add_parser("prove"); p.add_argument("cmds", nargs="+", metavar="COMMAND")
    p = sub.add_parser("flag"); p.add_argument("--ui", choices=["yes", "no"]); p.add_argument("--ai", choices=["yes", "no"])
    p.add_argument("--agent", choices=["yes", "no"]); p.add_argument("--order-override")
    p = sub.add_parser("ticket"); p.add_argument("id"); p.add_argument("--dod", required=True)
    p.add_argument("--verified", required=True); p.add_argument("--doc", required=True)
    p.add_argument("--runs", type=int); p.add_argument("--review")
    p.add_argument("--no-cuts", dest="no_cuts"); p.add_argument("--not-wired", dest="not_wired")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", help="list every gap the row would be refused "
                   "for, write nothing")
    p.add_argument("--uncut", action="append", default=[])
    p.add_argument("--self-review-ok", dest="self_review_ok")
    p = sub.add_parser("release")
    for o in ("--what", "--reviews", "--skipped", "--docs", "--record", "--rollback", "--pr"):
        p.add_argument(o, required=True)
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--commit")  # /ship's close (v2 alignment)
    p = sub.add_parser("drift"); p.add_argument("--found", required=True); p.add_argument("--rec", required=True)
    p = sub.add_parser("open"); p.add_argument("--from", dest="frm", required=True)
    p.add_argument("--what", required=True); p.add_argument("--clears", required=True)
    p = sub.add_parser("bypass"); p.add_argument("--from", dest="frm", required=True)
    p.add_argument("--gate", required=True); p.add_argument("--reason", required=True)
    p = sub.add_parser("close"); p.add_argument("n"); p.add_argument("--how", required=True)
    p = sub.add_parser("check"); p.add_argument("--product")
    p = sub.add_parser("migrate"); p.add_argument("--product", default="PRODUCT.md"); p.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    for k, v in vars(a).items():
        if isinstance(v, str) and k != "file":
            setattr(a, k, undo_msys_path(v))
    path, today = Path(a.file), a.today
    lock = None
    try:
        need_date(today, "--today")
        if a.cmd == "next" and a.ticket and (a.phase or "").lstrip("/") != "build":
            raise Refused("--ticket goes with --phase build")
        if a.cmd == "next" and getattr(a, "step", None):  # /design-system: one turn's reading in one call
            print(design_step_text(a.phase or "", a.step, a.family))
            return 0
        if a.cmd == "next" and (a.phase or "").lstrip("/") in SUPPORT_STARTS:  # 2.0: a skill outside the chain,
            skill = a.phase.lstrip("/")                                          # STATUS.md or not
            rules = phase_rules_text(skill)
            print(playbook_line())
            print(fit_start(((rules + "\n\n") if rules else "") + "\n".join([*run_habits(), SUPPORT_HABIT]) + "\n\n"
                            + SUPPORT_STARTS[skill](path, today), skill))
            return 0
        if a.cmd == "set" and a.phase.lstrip("/") == "adopt":  # /adopt's one record call: STATUS.md may not exist
            print(adopt_record(path, a, today))
            return 0
        if a.cmd == "next":  # first, even when STATUS.md does not exist yet: the first run is where it matters
            # LEAN: a /build start carries the close checklist only at the close (`ticket` prints it)
            lean = bool(a.phase) and (a.mode or playbook_mode(a.phase)) == "lean" \
                and a.phase.lstrip("/") in LEAN_PHASES
            head = (LEAN_CLOSE[:1] * lean + DEV_CHECK_HEAD if (a.phase or "").lstrip("/") == "dev-check" else
                    TEST_HEAD if (a.phase or "").lstrip("/") == "test" else
                    LEAN_CLOSE if lean else () if a.ticket else
                    QUESTION_CLOSE if (a.phase or "").lstrip("/") in QUESTION_PHASES else
                    STRUCTURE_HEAD if (a.phase or "").lstrip("/") == "structure" else
                    FOUNDATION_HEAD if (a.phase or "").lstrip("/") == "foundation" else
                    CONTRACTS_HEAD if (a.phase or "").lstrip("/") == "contracts" else
                    TICKETS_HEAD if (a.phase or "").lstrip("/") == "tickets" else
                    RELEASEOPS_HEAD.get((a.phase or "").lstrip("/"), CLOSE_CHECKLIST))
            print(playbook_line(), *head, sep="\n", flush=True)
            if (a.phase or "").lstrip("/") == "vision" and not path.exists():  # a new project: the normal first run
                base = path.resolve().parent
                fresh = not (base / "PRODUCT.md").exists() and not code_files(base, 1)
                # ONE start command: the rules come with it (a logged Antigravity run chained `next; rules` with `;`,
                # the command went to the background, and it spent a call reading the task's log)
                print(fit_start("\n".join(["Next: /vision - a new project (no STATUS.md yet)", *run_habits(),
                                           "\n" + vision_start_text(new=fresh),
                                           "\n" + phase_rules_text("vision", new=fresh)])))
                mark_rules_read(base, "vision", today)
                return 0
        if a.cmd == "how":
            print(how_text())
            return 0
        if a.cmd == "route":  # /playbook's one start call - answers even with no STATUS.md
            print(route_text(path, today))
            return 0
        if a.cmd == "rules" and a.close:  # the close's rules, printed by gate.py --close when the close gate passes
            if a.phase.lstrip("/") in PHASE_CLOSE_RULES:
                print(phase_close_text(a.phase.lstrip("/")))
                return 0
            if a.phase.lstrip("/") != "build":
                raise Refused(f"--close is for /{', /'.join(['build', *PHASE_CLOSE_RULES])}: the other phases' rules "
                              f"print whole with `rules <phase>`")
            print(build_close_text())
            return 0
        if a.cmd == "rules" and a.phase.lstrip("/") == "tickets":  # the start's rules + references, word for word
            base_ = path.resolve().parent
            print(tickets_rules_text(True, True, whole=True))
            mark_rules_read(base_, "tickets", today)
            return 0
        if a.cmd == "rules":
            text = phase_rules_text(a.phase.lstrip("/"))
            if text is None:
                raise Refused(f"no rule list for /{a.phase.lstrip('/')}: open PRINCIPLES.md and MECHANISMS.md whole "
                              f"(phases with a list: {', '.join(PHASE_RULES)})")
            print(text)
            mark_rules_read(path.parent if path.parent != Path("") else Path("."), a.phase.lstrip("/"), today)
            return 0
        if a.cmd == "engine":
            text = engine_hash_text()
            if a.write:  # the playbook's maintainers, after changing a checker; check.py fails while it is stale
                (Path(__file__).resolve().parent / "engine.sha256").write_text(text, encoding="utf-8", newline="\n")
            print(text, end="")
            return 0
        if a.cmd == "refs":
            text = phase_refs_text(a.phase.lstrip("/"))
            # "none" is an answer, not a refusal: the start's generic line sent a logged Cursor /vision here
            print(text if text is not None else f"/{a.phase.lstrip('/')} has no reference files of its own - "
                                                f"nothing to read; go on")
            return 0
        if a.cmd == "section":
            print(print_sections(Path(a.path), a.names, a.own, a.headings))
            return 0
        if a.cmd == "scaffold":  # /structure's boilerplate in one call (S6/S11): 74 one-file calls on a logged run
            base_ = path.resolve().parent
            prod_ = base_ / "PRODUCT.md"
            arch_ = structure_fields(product_sections(prod_.read_text(encoding="utf-8")).get("Architecture", "")) \
                if prod_.is_file() else {}
            print(scaffold(base_, Path(a.src), next((v for k, v in arch_.items() if re.match(r"(?i)dev tooling", k)),
                                                     "")))
            return 0
        if a.cmd == "prove":
            code_, text_ = prove(path.resolve().parent, a.cmds, today)
            print(text_)
            return code_
        if a.cmd == "quote":  # every receipt in one call: a logged /test spent 9 calls on 9 quotes
            if len(a.pairs) % 2:
                raise Refused("quote takes pairs: <file> <words> [<file> <words> ...]")
            bad = 0
            for name, words in zip(a.pairs[::2], a.pairs[1::2]):
                try:
                    print(quote_line(name, words, today, path.resolve().parent))
                except Refused as e:
                    bad += 1
                    print(f"  x {name}: {e}")
            return 1 if bad else 0
        if a.cmd == "init":
            if path.exists():
                raise Refused(f"{path} already exists - use `set`, or `migrate` for a project that has none")
            st = Status.new(a.product, today)
            st.header["UI"], st.header["AI product"] = "unknown", a.ai or "unknown"
            st.save(path)
            print(f"created {path}")
            return 0
        if a.cmd == "migrate":
            prod = Path(a.product)
            if path.exists():
                raise Refused(f"{path} already exists - this project is already migrated")
            if not prod.exists():
                raise Refused(f"{prod} not found")
            arch = "docs/status-archive.md"
            st, new_prod, arch_text, report = migrate(prod.read_text(encoding="utf-8"), today, arch,
                                                         (prod.parent / "TICKETS.md").exists(), prod.resolve().parent)
            print("\n".join(report))
            print(st.render_all())
            if not a.write:
                print("(dry run - nothing written; add --write to apply)")
                return 0
            ap_ = prod.parent / arch
            ap_.parent.mkdir(parents=True, exist_ok=True)
            if ap_.exists():
                raise Refused(f"{ap_} already exists - refusing to overwrite it")
            ap_.write_text(arch_text, encoding="utf-8", newline="\n")
            prod.write_text(new_prod, encoding="utf-8", newline="\n")
            st.save(path)
            print(f"wrote {path}, {prod}, {ap_}")
            return 0
        new_status = a.cmd == "set" and a.phase == "vision" and bool(a.product) and not path.exists()
        if a.cmd == "set" and a.product and not new_status:
            raise Refused("--product is only for `set vision` on a new project (no STATUS.md yet)")
        if not path.exists() and not new_status:
            raise Refused(f"{path} not found - run `status.py init --product <name>` (new project) or "
                          f"`status.py migrate` (a project whose status is still in PRODUCT.md)"
                          + (". /vision: `set vision filled --section-from <file> --product \"<name>\" --ai yes|no "
                             "--agent yes|no` creates it" if a.cmd == "set" and a.phase == "vision" else ""))
        if a.cmd == "save":  # a yes given after the record: the same one call as `set --commit`
            done = save_commit(path.resolve().parent, a.message)
            print(done + ("\nNow the close's steps 5-6: the transition guard, then the four blocks - the first line says "
                          "\"Saved\" with the commit, the last is the `Open a NEW conversation` line `set` printed"
                          if done.startswith("saved") else ""))
            return 0
        if a.cmd in MUTATING:
            lock = Lock(path.resolve().parent)
            lock.__enter__()
        if new_status:
            st = Status.new(a.product, today)
            st.header["UI"] = "unknown"
            st.base = path.resolve().parent
        else:
            st = Status.load(path)
        st.today = today
        if a.cmd == "set" and (a.ai or a.agent):
            apply_flags(st, a.ai, a.agent)
        if a.cmd == "show":
            print(st.render_all(), end="")
            return 0
        if a.cmd == "next":
            run = a.phase.lstrip("/") if a.phase else None
            if run and run not in CHAIN:
                raise Refused(f"unknown phase {run!r}; the phases are: {', '.join(CHAIN)}")
            n = next_phase(st, run)
            notes = n["notes"]
            if run == "foundation":  # its start prints AGENT.md §Foundation inline: no "open now" read
                notes = [x for x in notes if not x.startswith("Agent: yes - open now")]
            if a.ticket:  # LEAN: a build start keeps what can block THIS build; earlier phases' items are a count
                later = [x for x in notes if x.startswith(("open item", "rules changed since", "running:"))]
                notes = [x for x in notes if x not in later]
                if later:
                    notes.append(f"{len(later)} earlier-phase notes (open items, re-run offers): `status.py next` "
                                 f"lists them - none blocks this ticket")
                # a project-level fix is not this ticket's: a logged lean build obeyed "copy the playbook's check over
                # it and commit" on its ticket branch, and the neutral review's one MEDIUM was that unrelated change
                notes = [f"NOT THIS TICKET'S - tell the user in the close, never change it on the ticket branch: {x}"
                         if re.search(r"check fails now|differs from the playbook's check", x) else x for x in notes]
            if run in ("dev-check", "test"):  # P3: earlier phases' re-run offers are a count (~3.5 KB on a logged start)
                later = [x for x in notes if x.startswith("rules changed since")]
                notes = [x for x in notes if x not in later] + ([
                    f"{len(later)} earlier phases were filled under older rules: `status.py next` lists the re-run "
                    f"offers - none changes this phase"] if later else [])
                # P9: a project-level fix is not this phase's (the checkpoint and the suite never edit project code)
                notes = [f"NOT THIS PHASE'S - tell the user in the close, never change it here: {x}"
                         if re.search(r"check fails now|differs from the playbook's check", x) else x for x in notes]
            if run == "architect":  # its start prints AGENT.md §Architect itself: no file to open
                notes = [x.replace("Agent: yes - open now: ", "Agent: yes - printed at the end of this start, from ")
                         for x in notes]
            if run == "contracts":  # its start prints AGENT.md §Contracts itself: no file to open
                notes = [x.replace("Agent: yes - open now: ", "Agent: yes - printed in this start, from ")
                         for x in notes]
            if run == "structure":  # AGENT.md §Structure is printed by the start: nothing to open
                notes = [x for x in notes if not x.startswith("Agent: yes - open now")]
            print(f"Next: {n['line'] if not a.ticket else n['line'][:160]}")
            for x in notes:
                print(f"  - {x}")
            cost = last_conversation(st.base)
            if cost:
                print(f"  - cost: {cost}")
            print("\n".join(run_habits()))
            if run in LEAN_PHASES and st.base is not None:
                remember_mode(st.base, run, a.mode)
            lean = run is not None and playbook_mode(run, st.base) == "lean"
            if a.ticket:  # LEAN: one call, one small output - the gate above, then only what this ticket needs
                if not lean:
                    print("\n" + print_sections(rule_file("MECHANISMS-ON-DEMAND.md"), ["Context hygiene"]))
                # Antigravity shows ~4 KB of a ~29 KB full start: there it goes to a file read once (fit_start)
                print(fit_start("\n" + build_start_text(st, a.ticket, today, lean=lean), "build"))
                return 0
            if run == "dev-check":  # one start call: its tickets, the gate for THIS checkout, the scope, the rules (P1)
                rules_ = "" if lean else "\n\n" + phase_rules_text("dev-check")
                print(fit_start("\n" + dev_check_start_text(st) + rules_, "dev-check"))
                if not lean:
                    mark_rules_read(st.base or Path("."), "dev-check", today)
                return 0
            if run == "test":  # one start call, every tool: built tickets, criteria vs tests, surfaces, commands, rules
                print(fit_start("\n" + test_start_text(st) + "\n\n" + phase_rules_text("test"), "test"))
                mark_rules_read(st.base or Path("."), "test", today)
                return 0
            if run == "vision":  # its rules come with it: one start command
                print(fit_start("\n" + vision_start_text() + "\n\n" + phase_rules_text("vision")))
                mark_rules_read(st.base, "vision", today)
                return 0
            if run == "validate":  # one start command: the bet's lines, the rounds, the record, its rules (2.0)
                print(fit_start("\n" + validate_start_text(st) + "\n\n" + phase_rules_text("validate"), "validate"))
                mark_rules_read(st.base or Path("."), "validate", today)
                return 0
            if run == "scope":  # its rules come with it: one start command (/vision's lesson, next.55)
                print(fit_start("\n" + scope_start_text(st) + "\n\n" + phase_rules_text("scope"), "scope"))
                mark_rules_read(st.base, "scope", today)
                return 0
            if run == "structure":  # its rules come with it: one start command (/scope's lesson)
                print(fit_start("\n" + structure_start_text(st), "structure"))
                mark_rules_read(st.base or Path("."), "structure", today)
                return 0
            if run == "design-system":  # one start command: its rules come with it (P1)
                print(fit_start("\n" + design_start_text(st), "design-system"))
                mark_rules_read(st.base or Path("."), "design-system", today)
                return 0
            if run == "contracts":  # one start call: the spine lines, the steps and proofs, the rules (P1, P2)
                print(fit_start("\n" + contracts_start_text(st), "contracts"))
                mark_rules_read(st.base or Path("."), "contracts", today)
                return 0
            if run == "tickets":  # its rules and references come with it: one start command (/structure's lesson)
                lead = sum(len(x) + 1 for x in (playbook_line(), *TICKETS_HEAD, n["line"], *notes, *run_habits()))
                print(fit_start("\n" + tickets_start_text(st, lead + 12 * len(notes)), "tickets"))
                mark_rules_read(st.base or Path("."), "tickets", today)
                return 0
            if run == "vision":
                print("\n" + vision_start_text())
            if run == "architect":  # P1: one start call - the spine facts, AGENT.md §Architect and the rules inline
                print(fit_start("\n" + architect_start_text(st) + "\n\n" + architect_rules_text(st), "architect"))
                mark_rules_read(st.base or Path("."), "architect", today)
                return 0
            if run == "plan":  # P1: one start call - the rules come inline, so nothing tells the run to fetch them
                print(fit_start("\n" + plan_start_text(st) + "\n  - these ARE this phase's rules (`status.py rules "
                                "plan` prints them again after a summarised conversation)", "plan"))
                mark_rules_read(st.base or Path("."), "plan", today)
                return 0
            if run in RELEASEOPS_START:  # one start command: the spine lines, the fields, the refusals, the rules
                START_HOLDS.setdefault(run, RELEASEOPS_HOLDS[run])
                print(fit_start("\n" + RELEASEOPS_START[run](st), run))
                mark_rules_read(st.base or Path("."), run, today)
                return 0
            if run == "foundation":  # one start command: facts, sections, steps, proofs and rules (P1)
                print(foundation_start_out(st))
                mark_rules_read(st.base or Path("."), "foundation", today)
                return 0
            if lean:  # the lean path carries no rule files: SKILL.md §Lean path and the start above are the run
                return 0
            if run in PHASE_RULES:  # its own call: rules + notes in one output passed Claude Code's inline limit
                print(f"  - this phase's rules: status.py rules {run}  (run it now; it replaces opening the rule files)")
            if run in HYGIENE_PHASES:  # printed, not pointed at: a file opened "on its trigger" is a file some models never open
                print("\n" + print_sections(rule_file("MECHANISMS-ON-DEMAND.md"), ["Context hygiene"]))
            return 0
        if a.cmd == "check":
            errs, warns = problems(st, today, Path(a.product) if a.product else None)
            if a.product and st.state("vision") == "filled" and Path(a.product).is_file():
                # the filled phase's own checks too (a logged Codex run read "STATUS.md is valid" as its vision check)
                warns += [f"#vision's check: {g}" for g in vision_gaps(Path(a.product).resolve().parent, st.header)]
            for w in warns:
                print(f"  ! {w}")
            for e in errs:
                print(f"  x {e}")
            print("OK - STATUS.md is valid" if not errs else f"FAIL - {len(errs)} problem(s)")
            return 1 if errs else 0
        if a.cmd == "set" and a.section_from:
            msg = set_with_section(st, a, today, path.resolve().parent / "PRODUCT.md")
        elif a.cmd == "set":
            msg = cmd_set(st, a, today)
        elif a.cmd == "flag":
            if a.ui:
                st.header["UI"] = a.ui
            apply_flags(st, a.ai, a.agent)
            if a.order_override:
                st.header["Order"] = f"Override {today}: {capped('reason', a.order_override)}"
            msg = "flags updated"
        elif a.cmd == "ticket":
            msg = cmd_ticket(st, a, today)
        elif a.cmd == "release":
            msg = cmd_release(st, a, today)
        elif a.cmd == "drift":
            st.rows["Drift"].append([today, capped("found", a.found), capped("rec", a.rec)])
            msg = "drift recorded"
        elif a.cmd == "open":
            msg = cmd_open(st, a, today)
        elif a.cmd == "bypass":
            msg = cmd_bypass(st, a, today)
        elif a.cmd == "close":
            msg = cmd_close(st, a, today)
        else:
            raise Refused(f"unknown command {a.cmd}")
        errs, _ = problems(st, today, None)
        if errs:
            raise Refused("the result would be invalid: " + "; ".join(errs))
        written = st.save(path)
        print(msg + "".join(f"\n  wrote {w}" for w in written))
        if a.cmd == "drift":  # /drift-check's record: its close ends on the printed handoff
            print(handoff_card(st))
        if a.cmd == "ticket":  # the close's rules came with the close gate (gate.py --close); only the rest remains
            print("Next, the close's step (6): `status.py set build filled`, the save question (it commits the "
                  "record), the transition guard, the four-block close - by the rules the close gate printed "
                  "(`status.py rules build --close` prints them again)")
        if a.cmd == "release":  # /ship's close: the save, the rest of the close, the handoff (STATUS.md re-read)
            print(ship_close_text(path, today, a.commit))
        saved = None
        if (a.cmd == "set" and a.state == "filled" and a.phase in AUTO_SAVE and not a.commit
                and not getattr(a, "no_commit", False)):  # owner 2026-10-06: the verification phases save unasked
            a.commit = f"{a.phase}: {a.verdict.upper() if a.verdict else 'recorded'} - #{PHASE_SECTION[a.phase]} written"
        if a.cmd == "set" and a.commit and st.base is not None:
            saved = save_commit(st.base, a.commit)
            print(saved)
        if a.cmd == "set" and (a.state == "filled" or (a.phase == "validate" and a.state in ("running", "overridden")
                                                         and a.section_from)):  # /validate's close, any outcome
            if a.phase in PHASE_CLOSE_RULES and not (a.note or "").lower().startswith("adopted"):
                print(close_steps_text(a.phase, saved))  # the full rules on request: a re-run of set reprinted ~3.5K tokens
            if a.phase in PHASE_CLOSE_RULES and a.section_from and not (a.note or "").lower().startswith("adopted"):
                facts = repo_facts(st.base, getattr(a, "purpose", None), readme=a.phase == "vision", saved=bool(saved))
                if facts:
                    print(facts)
            if a.phase in PHASE_CLOSE_RULES and not saved:
                print("For the close's last line, AFTER the answer to the save question (never in its message):")
            print(handoff_card(st, a.phase))
        return 0
    except DryRun as e:
        print(f"DRY RUN - nothing written. {e}")
        return 0
    except Refused as e:
        print(f"REFUSED - {e}\n(Everything to change is named above. Never open the playbook's scripts to work around "
              f"a refusal - a logged run read status.py 10 times; if it is unclear, ask the user.)", file=sys.stderr)
        return 1
    finally:
        if lock is not None:
            lock.__exit__()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
