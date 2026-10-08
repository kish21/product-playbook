"""Behaviour tests for tools/run_report.py (run by tools/check.py). A complete run passes; a run that skipped a
required step is reported missing it - in both log formats the report reads (Claude Code .jsonl, Antigravity .db).
"""
from __future__ import annotations
import contextlib
import io
import json
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import run_report  # noqa: E402

CLOSE = ("**What just happened** x\n**What I skipped or couldn't do** x\n**Test this yourself** x\n"
         "**What YOU do next** x")


def claude_log(path: Path, skip: str = "") -> None:
    steps = [("Bash", {"command": "S=/p/tools/status.py && python $S next --phase structure"}),
             ("Read", {"file_path": "/p/PRINCIPLES.md"}), ("Read", {"file_path": "/p/references/mechanisms.md"}),
             ("Bash", {"command": "python scripts/check_structure.py"}),
             ("Bash", {"command": "python $S set structure filled"}),
             ("AskUserQuestion", {"questions": [{"question": "Save this version of your project? (yes / no)"}]}),
             ("Bash", {"command": "git commit -m structure"})]
    rows = []
    for name, inp in steps:
        if skip and skip in json.dumps(inp):
            continue
        rows.append({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": name, "input": inp}]}})
    close = "\n".join(l for l in CLOSE.splitlines() if not (skip and skip in l))
    rows.append({"type": "assistant", "message": {"content": [{"type": "text", "text": close}]}})
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


def antigravity_db(path: Path, skip: str = "") -> None:
    payloads = ['call_1 run_command {"CommandLine":"python .agents/product-playbook/status.py next --phase structure"}',
                'call_2 view_file {"AbsolutePath":"c:/p/.agents/product-playbook/PRINCIPLES.md"}',
                'call_3 view_file {"AbsolutePath":"c:/p/.agents/product-playbook/MECHANISMS.md"}',
                'call_4 run_command {"CommandLine":"python scripts/check_structure.py"}',
                'call_5 run_command {"CommandLine":"python .agents/product-playbook/status.py set structure filled"}',
                'call_6 ask_question {"questions":[{"options":["yes","no"],"question":"Save this version of your project? (yes / no)"}]}',
                'call_7 run_command {"CommandLine":"git commit -m structure"}',
                # a skill file the run opened: its text names the close blocks, which must not count as said
                'call_8 view_file {"AbsolutePath":"c:/p/SKILL.md"} What just happened · Test this yourself', CLOSE]
    con = sqlite3.connect(path)
    con.execute("create table steps (idx integer, step_payload blob)")
    for i, p in enumerate(x for x in payloads if not (skip and skip in x)):
        con.execute("insert into steps values (?, ?)", (i, ("\x12\x03" + p).encode()))
    con.commit()
    con.close()


def run(path: Path) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = run_report.main([str(path)])
    return code, out.getvalue()


def test_build_rows(fails: list[str]) -> None:
    """A logged build: 67 edits over ~35 round trips, /code-review wrapped in a helper that started its own reviewer,
    and (Gemini) a branch merged into main by /build itself. Each is a ✗ row; batched edits, a direct review and no
    merge are ✓."""
    good = {"cmd": ["git merge-base HEAD main", "git commit -m x"], "edits": [("a.py", "m1"), ("a.py", "m1"),
            ("a.py", "m2"), ("a.py", "m3")], "agent": ["Run /security-review on this branch and return the findings"]}
    good["read"] = ["python C:/p/tools/status.py next --phase build --ticket M1-A-01"]  # running a script is fine
    rows = dict(run_report.build_rows(good))
    if not all(rows.values()):
        fails.append(f"a build with batched edits, a direct review and no merge should pass: {rows}")
    bad = {"cmd": ["git checkout main", "git merge feature/x --no-ff"],
           "edits": [("a.py", f"m{i}") for i in range(4)],
           "agent": ["Deep code review. If the `code-review` skill is available, use it at level high"]}
    rows = run_report.build_rows(bad)
    bad["read"] = ["c:/Users/x/proof/p/.agents/product-playbook/status.py"]  # view_file on the playbook's own script
    rows = run_report.build_rows(bad)
    for want in ("edited each file in at most 3 calls", "ran /code-review directly", "never merged",
                 "never opened the playbook's own scripts"):
        if not any(label.startswith(want) and not ok for label, ok in rows):
            fails.append(f"a build that broke {want!r} should be a ✗ row: {rows}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    fails: list[str] = []
    test_build_rows(fails)
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        for fmt, make, ext in (("Claude", claude_log, "jsonl"), ("Antigravity", antigravity_db, "db")):
            ok = d / f"ok.{ext}"
            make(ok)
            code, out = run(ok)
            if code != 0:
                fails.append(f"{fmt}: a complete run should pass: {out}")
            for skip, label in (("What just happened** x", "close block: What just happened"),
                                ("check_structure", "ran the structure check"), ("PRINCIPLES", "opened PRINCIPLES.md"),
                                ("set structure", "recorded the phase"), ("git commit", "committed on the answer")):
                bad = d / f"skip-{re.sub(r'\W+', '_', skip)}.{ext}"
                make(bad, skip)
                code, out = run(bad)
                if code != 1 or f"✗ {label}" not in out:
                    fails.append(f"{fmt}: a run that skipped {skip!r} should be reported missing {label!r}: {out}")
        via_rules = d / "via-rules.jsonl"  # L3: `status.py rules` stands in for opening both rule files
        claude_log(via_rules, "PRINCIPLES")
        rows = via_rules.read_text(encoding="utf-8").splitlines()
        rows = [r for r in rows if "mechanisms.md" not in r]
        rows.insert(0, json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash",
                    "input": {"command": "python $S rules structure"}}]}}))
        via_rules.write_text("\n".join(rows) + "\n", encoding="utf-8")
        code, out = run(via_rules)
        if code != 0:
            fails.append(f"a run that printed its rules with `status.py rules` should pass: {out}")
        # a phase begun in a conversation an earlier phase already used carries all of it
        shared = d / "shared.jsonl"
        claude_log(shared)
        rows = shared.read_text(encoding="utf-8").splitlines()
        rows.insert(0, json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash",
                    "input": {"command": "python $S next --phase architect"}}]}}))
        shared.write_text("\n".join(rows) + "\n", encoding="utf-8")
        for path, want in ((ok_log := d / "ok.jsonl", "✓ ran in its own conversation"),
                           (shared, "✗ ran in its own conversation")):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                run_report.main([str(path), "--phase", "structure"])
            if want not in buf.getvalue():
                fails.append(f"{path.name}: expected {want!r}: {buf.getvalue()[-300:]}")
        # A4: the same command failing 3 times is a loop (Claude marks the failure; Antigravity: 3 in a row)
        for tries, want in ((2, "✓ stopped a failing command"), (3, "✗ stopped a failing command")):
            looping = d / f"loop{tries}.jsonl"
            claude_log(looping)
            rows = looping.read_text(encoding="utf-8").splitlines()
            for i in range(tries):
                rows.insert(1, json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use",
                            "id": f"t{i}", "name": "Bash", "input": {"command": "uv run  pytest"}}]}}))
                rows.insert(2, json.dumps({"type": "user", "message": {"content": [{"type": "tool_result",
                            "tool_use_id": f"t{i}", "is_error": True, "content": "Exit code 1"}]}}))
            looping.write_text("\n".join(rows) + "\n", encoding="utf-8")
            code, out = run(looping)
            if want not in out:
                fails.append(f"a command that failed {tries} times: expected {want!r}: {out[-300:]}")
        loop_db = d / "loop.db"
        antigravity_db(loop_db)
        con = sqlite3.connect(loop_db)
        for i in range(3):
            con.execute("insert into steps values (?, ?)", (100 + i, (f'\x12\x03call_9{i} run_command {{"CommandLine":'
                                                                      '"npm test"}').encode()))
        con.commit()
        con.close()
        code, out = run(loop_db)
        if "✗ stopped a failing command" not in out:
            fails.append(f"Antigravity: the same command 3 times in a row should be flagged: {out[-300:]}")
        # an override recorded with no question about it and no message from the user: the reason is the model's
        over = 'python $S open --from tickets --what "Override: #foundation\'s check fails - test project" --clears x'
        for asked, want in ((None, "✗ asked the user before recording an override"),
                            ("Foundation's check fails. Go on anyway? If so, what is your reason?",
                             "✓ asked the user before recording an override")):
            log = d / f"over{bool(asked)}.jsonl"
            claude_log(log)
            rows = log.read_text(encoding="utf-8").splitlines()
            extra = [{"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash",
                                                                     "input": {"command": over}}]}}]
            if asked:
                extra.insert(0, {"type": "assistant", "message": {"content": [{"type": "tool_use", "name":
                             "AskUserQuestion", "input": {"questions": [{"question": asked}]}}]}})
            rows[2:2] = [json.dumps(x) for x in extra]
            log.write_text("\n".join(rows) + "\n", encoding="utf-8")
            code, out = run(log)
            if want not in out:
                fails.append(f"override {'after' if asked else 'with no'} question: expected {want!r}: {out[-300:]}")
        over_db = d / "over.db"  # Antigravity logs the command JSON-escaped: --what \"Override: ...
        antigravity_db(over_db)
        con = sqlite3.connect(over_db)
        con.execute("insert into steps values (?, ?)", (3, ('\x12\x03call_55 run_command {"CommandLine":"python s.py '
                                                           'open --from tickets --what \\"Override: #foundation\'s check '
                                                           'fails - x\\" --clears y"}').encode()))
        con.commit()
        con.close()
        code, out = run(over_db)
        if "✗ asked the user before recording an override" not in out:
            fails.append(f"Antigravity: an unasked override (escaped quotes) should be flagged: {out[-300:]}")
        once_db = d / "once.db"  # one call logged in three steps (request, running, result) is one command
        antigravity_db(once_db)
        con = sqlite3.connect(once_db)
        for i in range(3):
            con.execute("insert into steps values (?, ?)", (100 + i, ('\x12\x03call_77 run_command {"CommandLine":'
                                                                      '"npm test"}').encode()))
        con.commit()
        con.close()
        code, out = run(once_db)
        if "✓ stopped a failing command" not in out:
            fails.append(f"Antigravity: one call logged in three steps is not a loop: {out[-300:]}")
    import replay  # R4: the replay tool builds a runnable command without spending anything
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = replay.main(["--project", str(ROOT), "--ref", "HEAD", "--phase", "structure", "--dry-run"])
    if code != 0 or ":structure" not in out.getvalue() or "--max-budget-usd" not in out.getvalue():
        fails.append(f"replay.py --dry-run should print a budget-capped command for the phase: {out.getvalue()}")
    for f in fails:
        print(f"  x {f}")
    print("OK - run_report.py behaves" if not fails else f"FAIL - {len(fails)} run_report.py test(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
