"""run_report.py - what a phase run actually did, read from its session log, against what the phase requires.

A rule a model skips silently is caught only if someone reads the log. This does the reading: it lists the
commands the run executed, the questions it asked, its web searches and the files it wrote, then checks the
steps every phase owes (MECHANISMS.md §Step 3b) and the ones this phase adds. Each check is a fact found in the
log or not found - never a judgement of quality (that stays UNVERIFIED (judged)).

    python run_report.py [--phase PHASE] [LOG]

LOG is a Claude Code session (.jsonl) or an Antigravity conversation (.db). Without LOG: the newest Claude Code
session for the current folder, else the newest Antigravity conversation that mentions it. Without --phase: the
phase the run named in `status.py next --phase <phase>`.
Exit 0 = every required step found; 1 = a step missing; 2 = no log found. Plain Python 3.9+, no dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

CLOSE_BLOCKS = ("What just happened", "What I skipped or couldn't do", "Test this yourself", "What YOU do next")
# What every writing phase owes, then what each phase adds: (label, kind, pattern). Kinds: cmd (a command it ran),
# text (its own messages), search (a web search), read (a file it opened).
COMMON = [
    # The script path may sit in a shell variable set by an earlier command (`S=.../status.py`, then `python $S`).
    ("ran `status.py next --phase <phase>` first", "cmd", r"(?s)(status\.py|\$\w+).*\bnext\s+--phase\s+{phase}\b"),
    # A phase with a rule list reads its sections through `status.py rules <phase>` instead (L3).
    # the lean /build start (`next --phase build --ticket`) prints the phase's rule sections itself (next.30)
    ("opened PRINCIPLES.md (or ran `status.py rules <phase>`)", "read",
     r"PRINCIPLES\.md|\brules\s+{phase}\b|\bnext\s+--phase\s+{phase}\s+--ticket\b"),
    ("opened MECHANISMS.md (or ran `status.py rules <phase>`)", "read",
     r"(?i)mechanisms\.md|\brules\s+{phase}\b|\bnext\s+--phase\s+{phase}\s+--ticket\b"),
    ("recorded the phase: `status.py set <phase> filled`", "cmd", r"(?s)(status\.py|\$\w+).*\bset\s+{phase}\s+(filled|running)"),
    ("asked the save question", "text", r"Save this version of your project\?"),
    ("committed on the answer", "cmd", r"git\s+(-C\s+\S+\s+)?commit\b"),
] + [(f"close block: {b}", "text", re.escape(b)) for b in CLOSE_BLOCKS]
PHASE = {
    "architect": [("ran at least one web search", "search", r".")],
    "structure": [("ran the structure check", "cmd", r"check_structure\.py")],
    "design-system": [("ran the audit engine", "cmd", r"audit\.py"),
                      ("asked for the user's own look before proposing", "text", r"(?i)look in mind|your own|reference")],
    "vision": [("ran at least one web search", "search", r".")],
}


def claude_events(path: Path) -> dict:
    ev = {"cmd": [], "text": [], "search": [], "read": [], "ask": [], "write": [], "failed": [], "seq": [],
          "edits": [], "agent": []}
    cmd_ids: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("type") == "user":  # a command's result: is_error marks a non-zero exit
            content = d.get("message", {}).get("content")
            said = content if isinstance(content, str) else " ".join(
                b.get("text", "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text")
            if said.strip() and not d.get("isMeta") and not said.lstrip().startswith("<"):
                ev["seq"].append(("user", said))  # the user's own words: a typed message
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error") \
                        and b.get("tool_use_id") in cmd_ids:
                    ev["failed"].append(cmd_ids[b["tool_use_id"]])
            continue
        if d.get("type") != "assistant":
            continue
        for b in d.get("message", {}).get("content", []):
            if b.get("type") == "text":
                ev["text"].append(b["text"])
            elif b.get("type") == "tool_use":
                name, inp = b.get("name", ""), b.get("input", {})
                if name in ("Bash", "PowerShell"):
                    ev["cmd"].append(inp.get("command", ""))
                    ev["seq"].append(("cmd", inp.get("command", "")))
                    cmd_ids[b.get("id", "")] = inp.get("command", "")
                elif name in ("WebSearch", "WebFetch"):
                    ev["search"].append(inp.get("query") or inp.get("url", ""))
                elif name == "Read":
                    ev["read"].append(inp.get("file_path", ""))
                elif name in ("Write", "Edit"):
                    ev["write"].append(inp.get("file_path", ""))
                    if name == "Edit":  # one model call with several edits is one round trip, not several
                        ev["edits"].append((inp.get("file_path", ""), d.get("message", {}).get("id", "")))
                elif name in ("Agent", "Task"):
                    ev["agent"].append(inp.get("prompt", ""))
                elif name == "AskUserQuestion":
                    qs = [q.get("question", "") for q in inp.get("questions", [])]
                    ev["ask"] += qs
                    ev["text"] += qs
                    ev["seq"] += [("ask", q) for q in qs]
                elif name == "Skill":
                    ev["read"].append(inp.get("skill", ""))
                if name in ("Bash", "PowerShell"):  # a file read by a shell command counts as opened
                    ev["read"].append(inp.get("command", ""))
    return ev


def antigravity_events(path: Path) -> dict:
    ev = {"cmd": [], "text": [], "search": [], "read": [], "ask": [], "write": [], "seq": [], "edits": [], "agent": []}
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:  # read-only and closed at once: the file is the tool's live conversation store
        rows = con.execute("select step_payload from steps order by idx").fetchall()
    finally:
        con.close()
    seen: set[str] = set()
    for (payload,) in rows:
        t = payload.decode("utf-8", "ignore") if isinstance(payload, bytes) else str(payload or "")
        t = re.sub(r"[\x00-\x08\x0b-\x1f]+", " ", t)
        if m := re.search(r'(?:(call_\d+)\s+run_command\s+\{)?"CommandLine":"((?:[^"\\]|\\.)*)"', t):
            # Antigravity logs one call in several steps (request, running, result): count a call id once, or one
            # command reads as three and the loop check fires on a command run once
            if m.group(1) not in seen:
                ev["cmd"].append(m.group(2))
                ev["read"].append(m.group(2))
                ev["seq"].append(("cmd", m.group(2)))
            if m.group(1):
                seen.add(m.group(1))
        if m := re.search(r'\bview_file\s+\{"AbsolutePath":"([^"]+)"', t):
            ev["read"].append(m.group(1))
        if re.search(r"\b(search_web|read_url_content)\s+\{", t):
            q = re.search(r'"(?:query|Url)":"([^"]*)"', t)
            ev["search"].append(q.group(1) if q else "search")
        if m := re.search(r'(?:(call_\d+)\s+)?\b(write_to_file|replace_file_content|multi_replace_file_content)'
                          r'\s+\{.*?"TargetFile":"([^"]+)"', t):
            ev["write"].append(m.group(3))
            key = m.group(1) or m.group(0)[:80]  # one call is logged in several steps: count it once
            if m.group(2) != "write_to_file" and key not in seen:
                ev["edits"].append((m.group(3), key))
                seen.add(key)
        if re.search(r"\bask_question\b", t) and '"questions"' in t:
            qs = [q for q in re.findall(r'"question":"((?:[^"\\]|\\.)*)"', t) if q not in ev["ask"]]
            ev["seq"] += [("ask", q) for q in qs]
            ev["ask"] += qs
            ev["text"] += qs
        # Only the model's own messages count as what it said: a step that calls a tool also carries the tool's
        # result (a skill file it opened quotes "Save this version..." without the run ever asking it).
        if not re.search(r"\bcall_\d+\b", t):
            ev["text"].append(t)
    return ev


def newest_log(cwd: Path) -> Path | None:
    slug = re.sub(r"[:\\/]", "-", str(cwd))
    home = Path.home()
    claude = sorted((p for d in (home / ".claude" / "projects").glob("*") if d.name.lower() == slug.lower()
                     for p in d.glob("*.jsonl")), key=lambda p: p.stat().st_mtime, reverse=True)
    if claude:
        return claude[0]
    ag = sorted((home / ".gemini" / "antigravity-ide" / "conversations").glob("*.db"),
                key=lambda p: p.stat().st_mtime, reverse=True)
    needle = cwd.as_posix().lower().encode()
    for p in ag[:10]:
        if needle in p.read_bytes().lower().replace(b"\\\\", b"/").replace(b"\\", b"/"):
            return p
    return None


def report(ev: dict, phase: str | None) -> tuple[list[tuple[str, bool]], str | None]:
    if phase is None:
        for c in ev["cmd"]:
            if m := re.search(r"next\s+--phase\s+([\w-]+)", c):
                phase = m.group(1)
                break
    rows = []
    for label, kind, pat in COMMON + PHASE.get(phase or "", []):
        rx = re.compile(pat.replace("{phase}", re.escape(phase or "")))
        rows.append((label, any(rx.search(x or "") for x in ev[kind])))
    # A phase runs in a new conversation (MECHANISMS.md §Plain-language close): an earlier phase's Step 0 in the
    # same log means this one began carrying that phase's whole conversation. A batch the user chose is the
    # exception, and reads as a miss here on purpose - the report cannot see the choice, the reader can.
    started = [m.group(1) for c in ev["cmd"] for m in re.finditer(r"next\s+--phase\s+([\w-]+)", c)]
    rows.append(("ran in its own conversation (no earlier phase in this log)", not started or started[0] == phase))
    rows.append(("asked the user before recording an override (the reason is theirs)", not unasked_override(ev)))
    if phase == "build":
        rows += build_rows(ev)
    loop = looped(ev)
    rows.append((f"stopped a failing command by its 3rd try{f' (not: {loop[:80]!r})' if loop else ''}", not loop))
    return rows, phase


OVERRIDE = re.compile(r"\bbypass\b.*--reason|--what\s+\\?[\"']?Override:|\bset\s+[\w-]+\s+overridden\b|--self-review-ok\b")
ASKS_REASON = re.compile(r"(?i)override|reason|skip|bypass|go on|continue|fails")


def unasked_override(ev: dict) -> str | None:
    """An override recorded with no question to the user about it, and no message from them, since the run began.
    Its reason is then the model's words: a logged Gemini run wrote "test project with dev SQLite..." after asking
    only whether to go on writing tickets. The run's opening message is its command, not an answer: not counted."""
    seq = ev.get("seq", [])
    start = next((i for i, (k, _) in enumerate(seq) if k == "cmd"), 0)
    for i, (kind, text) in enumerate(seq):
        if kind == "cmd" and OVERRIDE.search(text):
            if not any(k == "user" or (k == "ask" and ASKS_REASON.search(x)) for k, x in seq[start:i]):
                return text
    return None


EDIT_CALLS = 3
READERS = "|".join(("cat", "sed", "head", "tail", "grep", "rg", "Get-Content", "type", "less", "more", "Select-String"))
SCRIPT =r"(?:status|gate|wirecut|devserver|audit|check_structure|ci_local|render_check)\.py"
MERGE = re.compile(r"\bgit\s+(?:-C\s+\S+\s+)?merge\b(?!-base)")


def build_rows(ev: dict) -> list[tuple[str, bool]]:
    """What made a logged build slow or unsafe, as rows: 67 edits over ~35 round trips (each re-sending a 200k-token
    conversation), /code-review wrapped in a helper that then started its own reviewer (the diff read twice), and a
    Gemini build that merged its own branch into main."""
    calls: dict[str, set] = {}
    for f, msg in ev.get("edits", []):
        calls.setdefault(f, set()).add(msg)
    many = sorted(((len(m), f) for f, m in calls.items() if len(m) > EDIT_CALLS), reverse=True)
    wrapped = [p for p in ev.get("agent", []) if re.search(r"(?i)code-review", p)]
    merged = [c for c in ev["cmd"] if MERGE.search(c)]
    worst = f" (not: {Path(many[0][1]).name} in {many[0][0]} calls)" if many else ""
    opened = [r for r in ev.get("read", []) if re.search(rf"{SCRIPT}$", (r or "").replace("\\", "/").strip())
              or re.search(rf"(?i)\b(?:{READERS})\b[^|;&]*{SCRIPT}", r or "")]
    return [(f"never opened the playbook's own scripts - they are tools: run them"
             f"{f' (not: {Path(opened[0].split()[-1]).name})' if opened else ''}", not opened),
            (f"edited each file in at most {EDIT_CALLS} calls - whole-file writes, edits batched{worst}", not many),
            ("ran /code-review directly, never inside a helper agent (it starts its own reviewer)", not wrapped),
            (f"never merged (merging is /ship's){f' (not: {merged[0][:60]!r})' if merged else ''}", not merged)]


def looped(ev: dict) -> str | None:
    """A4: the same command failing 3 times (a Claude log marks the failure), or - where the log does not say
    (Antigravity) - the same command run 3 times in a row. Returns that command, or None."""
    flat = lambda c: " ".join(c.split())  # noqa: E731
    if "failed" in ev:
        counts: dict[str, int] = {}
        for c in map(flat, ev["failed"]):
            counts[c] = counts.get(c, 0) + 1
            if counts[c] >= 3:
                return c
        return None
    cmds = [flat(c) for c in ev["cmd"]]
    return next((c for i, c in enumerate(cmds[2:], 2) if c == cmds[i - 1] == cmds[i - 2]), None)


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:  # a captured stream in tests
        pass
    ap = argparse.ArgumentParser(prog="run_report.py", description="what a phase run did, from its session log")
    ap.add_argument("log", nargs="?")
    ap.add_argument("--phase")
    a = ap.parse_args(argv)
    path = Path(a.log) if a.log else newest_log(Path.cwd())
    if path is None or not path.is_file():
        print("no session log found - pass its path (a Claude .jsonl or an Antigravity .db)")
        return 2
    ev = antigravity_events(path) if path.suffix == ".db" else claude_events(path)
    rows, phase = report(ev, a.phase)
    print(f"Run report · {path.name} · phase: /{phase or '?'}")
    print(f"  {len(ev['cmd'])} commands · {len(ev['ask'])} questions · {len(ev['search'])} web searches · "
          f"{len(set(ev['write']))} files written")
    for q in ev["ask"][:8]:
        print(f"  asked: {q[:110]}")
    missing = [label for label, ok in rows if not ok]
    for label, ok in rows:
        print(f"  {'✓' if ok else '✗'} {label}")
    print("OK - every required step is in the log" if not missing
          else f"MISSING {len(missing)}: a step the phase requires is not in the log")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
