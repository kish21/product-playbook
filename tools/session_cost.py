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
Agent working time is wall clock minus every wait that ended in the user's input - a typed reply, an
answered question card or an approved plan; a background job's notification is the agent's own wait and stays
in. It is how a phase's short/long size (status.py PHASE_SIZE, which `/playbook` quotes) is checked against a
real run. A tool permission prompt leaves no row of its own, so time spent approving a tool counts as working
time here.
The cost is Claude Code's own total, from the `cost-state` row it writes when a session ends; before then it is
"not final". A list-price sum is printed only with --rates, and labelled "not the bill": a logged replay's list-price
sum was $20.05 where Claude Code's own total was $11.86 (the calls were counted once; the prices were wrong for the
model). Stdlib only.
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
USER_ANSWERED = ("AskUserQuestion", "ExitPlanMode")  # tools whose result is the user's answer, not the agent's work


def is_user_input(row: dict, question_ids: set) -> bool:
    """Of the conversation rows measure() passes in, one the user produced: a typed message (not a background
    job's notification) or the answer to a question card or plan. Other tool results are the agent's own work."""
    if row.get("type") != "user":
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
            last = max(last, ts) if last else ts  # rows are not always logged in time order
        # Only the conversation moves the clock: an attachment, queue or meta row logged beside a reply must not
        # shorten the wait that reply ends, nor count as the user's input.
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
                if block["name"] in USER_ANSWERED:
                    question_ids.add(block.get("id"))
    minutes = 0.0
    if first and last:
        minutes = (datetime.strptime(last, FMT) - datetime.strptime(first, FMT)).total_seconds() / 60
    return {"log": log.name, "calls": calls, "minutes": round(minutes, 1), "input": inp, "output": out,
            "cache_read": cache_read, "cache_write": cache_write, "questions": questions, "tools": tools,
            "working": round(max(0.0, minutes - waiting / 60), 1)}


def own_total(log: Path) -> dict | None:
    """Claude Code's own cost, from the `cost-state` row it writes when a session ends: {"total": $, "models":
    {model: $}}. None while the session is still running."""
    found = None
    with log.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"cost-state"' in line:
                row = json.loads(line)
                if row.get("type") == "cost-state":
                    found = row
    if not found:
        return None
    models = {m: u.get("costUSD", 0.0) for m, u in (found.get("modelUsage") or {}).items()}
    return {"total": found.get("totalCostUSD", sum(models.values())), "models": models}


def last_finished(project: Path):
    """The newest session of this project that has ended (so holds its own total): (log, own_total, measure)."""
    logs = sorted(project_log_dir(project).glob("*.jsonl"), key=os.path.getmtime, reverse=True)
    for log in logs[:20]:
        own = own_total(log)
        if own:
            return log, own, measure(log)
    return None


def varint(b: bytes, i: int) -> tuple[int, int]:
    r = s = 0
    while True:
        x = b[i]
        i += 1
        r |= (x & 0x7F) << s
        s += 7
        if x < 0x80:
            return r, i


def pb_ints(b: bytes, path: str = "", out: dict | None = None, depth: int = 0) -> dict:
    """Every integer of a protobuf message by field path (.1.4.2 -> value); nested messages are tried as messages."""
    out = {} if out is None else out
    i = 0
    try:
        while i < len(b):
            key, i = varint(b, i)
            f, wt = key >> 3, key & 7
            if f == 0:
                return out
            p = f"{path}.{f}"
            if wt == 0:
                out[p], i = varint(b, i)
            elif wt == 1:
                i += 8
            elif wt == 5:
                i += 4
            elif wt == 2:
                n, i = varint(b, i)
                if depth < 6:
                    pb_ints(b[i:i + n], p, out, depth + 1)
                i += n
            else:
                return out
    except IndexError:
        pass
    return out


def antigravity_tokens(db: Path) -> dict:
    """Antigravity keeps one gen_metadata row per model call; its usage block (.1.4) holds new input (.2), output
    (.3) and cached input (.5). Read from the file itself - the field meanings are not documented, but new + cached
    grows call by call exactly like a conversation's context. A logged Gemini close guessed half the real total."""
    import sqlite3
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        rows = con.execute("select data from gen_metadata").fetchall()
    finally:
        con.close()
    t = {"calls": 0, "input": 0, "cache_read": 0, "output": 0, "peak": 0}
    for (data,) in rows:
        v = pb_ints(data if isinstance(data, bytes) else bytes(data))
        if ".1.4.2" not in v:
            continue
        t["calls"] += 1
        t["input"] += v.get(".1.4.2", 0)
        t["output"] += v.get(".1.4.3", 0)
        t["cache_read"] += v.get(".1.4.5", 0)
        t["peak"] = max(t["peak"], v.get(".1.4.2", 0) + v.get(".1.4.5", 0))
    return t


def newest_antigravity(project: Path) -> Path | None:
    dbs = sorted((Path.home() / ".gemini" / "antigravity-ide" / "conversations").glob("*.db"), key=os.path.getmtime,
                 reverse=True)
    needle = project.resolve().as_posix().lower().encode()
    for db in dbs[:10]:
        if needle in db.read_bytes().lower().replace(b"\\\\", b"/").replace(b"\\", b"/"):
            return db
    return None


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("log", nargs="?", help="a session .jsonl; default: the newest for --project")
    ap.add_argument("--project", default=".", help="project directory whose newest log to read")
    ap.add_argument("--rates", help="$ per million tokens: input,output,cache-read,cache-write - a list-price "
                                    "figure, printed only when asked for; the cost is Claude Code's own total")
    args = ap.parse_args(argv)
    # A Windows console (cp1252) cannot print the separators below and would die mid-report - the same
    # trap tools/check.py guards against in done().
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    log = Path(args.log) if args.log else None
    if log is None and not list(project_log_dir(Path(args.project)).glob("*.jsonl")):
        log = newest_antigravity(Path(args.project))
    if log is not None and log.suffix == ".db":
        t = antigravity_tokens(log)
        print(f"session {log.name} (Antigravity)")
        print(f"  calls {t['calls']} · tokens: new input {t['input']:,} · cached input {t['cache_read']:,} · output "
              f"{t['output']:,} · context sent {t['input'] + t['cache_read']:,} (largest call {t['peak']:,})")
        print("  cost: not measured - Antigravity's file records tokens, not prices; your plan's usage page has the "
              "bill. Time: not in the file - say 'not measured'")
        return 0
    log = log or newest_log(Path(args.project))
    m = measure(log)
    own = own_total(log)
    print(f"session {m['log']}")
    print(f"  calls {m['calls']} · {m['minutes']} min wall (includes time the user spent answering) · "
          f"questions asked {m['questions']}")
    print(f"  agent working {m['working']} min (wall minus every wait for the user's reply or answer)")
    print(f"  tokens: output {m['output']:,} · cache read {m['cache_read']:,} · cache write "
          f"{m['cache_write']:,} · input {m['input']:,}")
    print(f"  avg context per call {m['cache_read'] // max(m['calls'], 1):,} tokens")
    if own:
        print(f"  cost ${own['total']:.2f} - Claude Code's own total ("
              + ", ".join(f"{k} ${v:.2f}" for k, v in own["models"].items()) + ")")
    else:
        print("  cost: not final - Claude Code writes its own total when this session ends; run this again then "
              "(`status.py next` in the next conversation prints it)")
    if args.rates:
        r_in, r_out, r_cr, r_cw = (float(x) for x in args.rates.split(","))
        cost = (m["input"] * r_in + m["output"] * r_out + m["cache_read"] * r_cr + m["cache_write"] * r_cw) / 1e6
        print(f"  list-price figure ${cost:.2f} at {args.rates} $/M (in,out,cache-read,cache-write) - not the bill")
    print("  tools: " + ", ".join(f"{k} {v}" for k, v in sorted(m["tools"].items(), key=lambda kv: -kv[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
