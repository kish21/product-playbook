#!/usr/bin/env python3
"""session_cost.py - what a phase run actually cost, read from the Claude Code session log.

MECHANISMS-ON-DEMAND.md §Context hygiene item 4: a close reports time, tokens and cost from the session
log or says "not measured" - never an estimate (live closes guessed "$1.50-2.50" for a $20 run). This is
the one command that produces those numbers, so a run has no reason to guess.

Usage:  python tools/session_cost.py [<session>.jsonl]            # default: newest log for the cwd's project
        python tools/session_cost.py --project ~/projects/my-app  # newest log of another project
        python tools/session_cost.py --rates 5,25,0.5,6.25         # $/M for input, output, cache read, cache write

Reads `message.usage` on assistant rows, de-duplicated by message id (a streamed reply is logged in
several rows). Wall clock is first->last timestamp, so it includes the time the user spent answering.
Agent working time is wall clock minus every wait that ended in the user's input - a typed reply or an
answered question card; a background job's notification is the agent's own wait and stays in. It is the
figure `/playbook` §Sitting lengths quotes, so a run measured here compares with that table.
Rates default to Opus 5 list prices; pass --rates for another model. Stdlib only.
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def project_log_dir(project: Path) -> Path:
    """Claude Code keys a project's logs by its absolute path with ':' and separators replaced by '-'
    (c:/Users/me/app -> c--Users-me-app); the drive letter's case varies, so both are tried."""
    raw = str(project.resolve())
    key = "".join("-" if ch in ":\\/" else ch for ch in raw)
    base = Path.home() / ".claude" / "projects"
    for candidate in (key, key[0].lower() + key[1:], key[0].upper() + key[1:]):
        if (base / candidate).is_dir():
            return base / candidate
    return base / key


def newest_log(project: Path) -> Path:
    logs = sorted(project_log_dir(project).glob("*.jsonl"), key=os.path.getmtime)
    if not logs:
        sys.exit(f"no session log under {project_log_dir(project)}")
    return logs[-1]


FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def is_user_input(row: dict, question_ids: set) -> bool:
    """A row the user produced: a typed message (not a meta row, not a background job's notification) or the
    answer to a question card. Tool results are the agent's own work."""
    if row.get("type") != "user" or row.get("isMeta"):
        return False
    content = (row.get("message") or {}).get("content")
    if isinstance(content, list):
        results = [b for b in content if isinstance(b, dict) and b.get("type") == "tool_result"]
        if results:
            return any(b.get("tool_use_id") in question_ids for b in results)
        content = " ".join(b.get("text", "") for b in content if isinstance(b, dict))
    return not str(content or "").lstrip().startswith("<task-notification>")


def measure(log: Path) -> dict:
    seen: set[str] = set()
    calls = out = inp = cache_read = cache_write = 0
    first = last = None
    tools: dict[str, int] = {}
    questions = 0
    question_ids: set[str] = set()
    latest = None  # the newest timestamp so far; rows are not always logged in time order
    waiting = 0.0  # seconds spent waiting for the user's input
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        ts = row.get("timestamp")
        if ts:
            first = first or ts
            last = ts
        # Only the conversation moves the clock: an attachment or queue row logged beside a reply must not
        # shorten the wait that reply ends.
        if ts and row.get("type") in ("assistant", "user") and not row.get("isMeta"):
            now = datetime.strptime(ts, FMT)
            if latest and now > latest and is_user_input(row, question_ids):
                waiting += (now - latest).total_seconds()
            latest = max(latest, now) if latest else now
        if row.get("type") != "assistant":
            continue
        msg = row.get("message") or {}
        if msg.get("id") not in seen:
            seen.add(msg.get("id"))
            usage = msg.get("usage") or {}
            calls += 1
            out += usage.get("output_tokens", 0)
            inp += usage.get("input_tokens", 0)
            cache_read += usage.get("cache_read_input_tokens", 0)
            cache_write += usage.get("cache_creation_input_tokens", 0)
        for block in msg.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tools[block["name"]] = tools.get(block["name"], 0) + 1
                if block["name"] == "AskUserQuestion":
                    questions += 1
                    question_ids.add(block.get("id"))
    minutes = 0.0
    if first and last:
        minutes = (datetime.strptime(last, FMT) - datetime.strptime(first, FMT)).total_seconds() / 60
    return {"log": log.name, "calls": calls, "minutes": round(minutes, 1), "input": inp, "output": out,
            "cache_read": cache_read, "cache_write": cache_write, "questions": questions, "tools": tools,
            "working": round(max(0.0, minutes - waiting / 60), 1)}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("log", nargs="?", help="a session .jsonl; default: the newest for --project")
    ap.add_argument("--project", default=".", help="project directory whose newest log to read")
    ap.add_argument("--rates", default="5,25,0.5,6.25",
                    help="$ per million tokens: input,output,cache-read,cache-write (default Opus 5)")
    args = ap.parse_args(argv)
    # A Windows console (cp1252) cannot print the separators below and would die mid-report - the same
    # trap tools/check.py guards against in done().
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    log = Path(args.log) if args.log else newest_log(Path(args.project))
    m = measure(log)
    r_in, r_out, r_cr, r_cw = (float(x) for x in args.rates.split(","))
    cost = (m["input"] * r_in + m["output"] * r_out + m["cache_read"] * r_cr + m["cache_write"] * r_cw) / 1e6
    print(f"session {m['log']}")
    print(f"  calls {m['calls']} · {m['minutes']} min wall (includes time the user spent answering) · "
          f"questions asked {m['questions']}")
    print(f"  agent working {m['working']} min (wall minus every wait for the user's reply or answer)")
    print(f"  tokens: output {m['output']:,} · cache read {m['cache_read']:,} · cache write "
          f"{m['cache_write']:,} · input {m['input']:,}")
    print(f"  avg context per call {m['cache_read'] // max(m['calls'], 1):,} tokens")
    print(f"  ≈ ${cost:.2f} at {args.rates} $/M (in,out,cache-read,cache-write)")
    print("  tools: " + ", ".join(f"{k} {v}" for k, v in sorted(m["tools"].items(), key=lambda kv: -kv[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
