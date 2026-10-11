"""Behaviour tests for commands/build/gate.py and wirecut.py (run by tools/check.py, check 53f).

gate.py: two passing commands and a failing one in ONE call → PASS, PASS, FAIL with the failing lines, exit 1, the
result line quoted, the full output in a log inside .git; --stop stops at the failure. wirecut.py: a cut the test
guards → RED; a cut the test does not guard → NOT CAUGHT, exit 1; a find text that is not unique → SKIP; every file
byte-identical afterwards; a cut left behind by a killed run is restored first.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "commands" / "build" / "gate.py"
CUT = ROOT / "commands" / "build" / "wirecut.py"
TEMPLATE = ROOT / "templates" / "feature-doc.md"
EXAMPLE = ROOT / "templates" / "feature-doc-example.md"
# the shape a logged build wrote (names invented): a CLI line first, code names, rule codes, the point buried
BAD_DOC = """# Demo guests

`python -m app.cli guests seed-demo` seeds persona `late_walkin` with a `PlantedVisit` (`is_decoy`).

## In short
Seeds two demo guests by natural key (R3, R4), portable across engines per #Architecture.

## What you can do now
Run `python -m app.cli guests seed-demo`, then open seed_service.py.

## What it protects you from
Guards: R6 - a rerun would corrupt the scoring.

## Not done yet
Archetype: none

---

## For developers and coding agents
Real-world reach: none - not guarded: no outside call

### Review
CLEAN
"""
PY = f'"{sys.executable}"'


def run(args: list[str], cwd: Path) -> tuple[int, str]:
    p = subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return p.returncode, p.stdout + p.stderr


def main() -> int:
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        subprocess.run(["git", "init", "-q"], cwd=d)
        ok = f'{PY} -c "print(\'3 passed in 0.1s\')"'
        bad = f'{PY} -c "import sys; print(\'FAILED tests/test_x.py::test_y - boom\'); print(\'1 failed in 0.2s\'); sys.exit(1)"'
        code, out = run([str(GATE), ok, bad, ok], d)
        lines = out.splitlines()
        if code != 1 or sum(ln.startswith("PASS") for ln in lines) != 2 or not any(ln.startswith("FAIL (exit 1)") for ln in lines):
            fails.append(f"gate should pass two, fail one and exit 1: {out[:300]}")
        if not any(ln.strip().startswith("| FAILED tests/test_x.py::test_y") for ln in lines) \
                or "result: 3 passed in 0.1s" not in out:
            fails.append(f"gate should print the failing line and the result line: {out[:300]}")
        if "GATE FAIL - 1 of 3 failed" not in out or not list((d / ".git" / "playbook-gate").glob("*.log")):
            fails.append("gate should summarise and keep the full output in .git/playbook-gate")
        code, out = run([str(GATE), "--stop", bad, ok], d)
        if code != 1 or any(ln.startswith("PASS") for ln in out.splitlines()):
            fails.append(f"gate --stop should stop at the first failure: {out[:200]}")
        code, out = run([str(GATE), ok], d)
        if code != 0 or "GATE PASS" not in out:
            fails.append(f"gate should pass when every command passes: {out[:200]}")
        rec = [json.loads(ln) for ln in (d / ".git" / "playbook-gate" / "results.jsonl").read_text(
            encoding="utf-8").splitlines() if ln.strip()] if (d / ".git" / "playbook-gate" / "results.jsonl").is_file() else []
        if [r.get("passed") for r in rec] != [False, False, True] or rec[-1].get("commands") != [ok]:
            fails.append(f"gate should record each run's commands and verdict for `status.py ticket`: {rec}")

        src = d / "app.py"
        original = "def allowed(user):\n    return user == 'owner'\n\ndef other():\n    return 1\n"
        src.write_text(original, encoding="utf-8")
        test = f'{PY} -c "import app, sys; sys.exit(0 if app.allowed(\'owner\') and not app.allowed(\'x\') else 1)"'
        cuts = [
            {"name": "check removed", "file": "app.py", "find": "user == 'owner'", "replace": "True", "test": test},
            {"name": "unguarded", "file": "app.py", "find": "return 1", "replace": "return 2", "test": test},
            {"name": "not unique", "file": "app.py", "find": "return", "replace": "yield", "test": test},
        ]
        (d / "cuts.json").write_text(json.dumps(cuts), encoding="utf-8")
        code, out = run([str(CUT), "cuts.json"], d)
        if code != 1 or "RED         check removed" not in out:
            fails.append(f"wirecut should report a guarded cut RED: {out[:300]}")
        if "NOT CAUGHT  unguarded" not in out:
            fails.append(f"wirecut should report an unguarded cut NOT CAUGHT: {out[:300]}")
        if "SKIP        not unique" not in out or "occurs 2 times" not in out:
            fails.append(f"wirecut should skip a find text that is not unique: {out[:300]}")
        if src.read_text(encoding="utf-8") != original:
            fails.append("wirecut left app.py changed")
        # a run killed mid-cut: the broken file and its saved copy are left behind
        wc = d / ".git" / "playbook-wirecut"
        wc.mkdir(exist_ok=True)
        (wc / "1.orig").write_text(original, encoding="utf-8")
        (wc / "1.json").write_text(json.dumps({"file": "app.py", "copy": "1.orig"}), encoding="utf-8")
        src.write_text("broken", encoding="utf-8")
        (d / "one.json").write_text(json.dumps(cuts[:1]), encoding="utf-8")
        code, out = run([str(CUT), "one.json"], d)
        if "restored app.py" not in out or code != 0 or src.read_text(encoding="utf-8") != original:
            fails.append(f"wirecut should restore a killed run's cut first: {out[:300]}")
        code, out = run([str(CUT), "missing.json"], d)
        if code != 2:
            fails.append("wirecut should refuse a missing cuts file with exit 2")
        # DP1: a cut tagged with its Demo claim (D2=...) is recorded per cut, claim and result, for `status.py ticket`
        code, out = run([str(CUT), "--cut", f"D2=app.py::user == 'owner'::True::{test}",
                         "--cut", f"app.py::return 1::return 2::{test}"], d)
        last = json.loads((wc / "results.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        got = [(c.get("file"), c.get("claim"), c.get("result")) for c in last.get("cuts", [])]
        if got != [("app.py", "D2", "RED"), ("app.py", "", "NOT CAUGHT")]:
            fails.append(f"wirecut should record each cut's file, Demo claim and result: {got} / {out[:200]}")
        if src.read_text(encoding="utf-8") != original:
            fails.append("wirecut left app.py changed after a tagged cut")
        # --ticket: the gate picks the project's check recipe + the ticket's Verification Command itself (A13);
        # --close: on a pass it prints the close's order and rules, on a fail nothing more (A1/A15)
        (d / "docs" / "issues").mkdir(parents=True)
        (d / "docs" / "issues" / "M1-A-01_x.md").write_text(
            f"# [M1-A-01] x\n\n### 🧪 Verification Command\n```bash\n{ok}\n```\n", encoding="utf-8")
        code, out = run([str(GATE), "--ticket", "M1-A-01"], d)
        if code != 0 or f"gate: {ok}" not in out or "The close, in this order" in out:
            fails.append(f"gate --ticket should run the ticket's Verification Command, and print no close rules: {out[:300]}")
        (d / "Makefile").write_text("check:\n\techo ok\n", encoding="utf-8")
        code, out = run([str(GATE), "--ticket", "M1-A-01", "--close"], d)
        if "gate: make check" not in out:
            fails.append(f"gate --ticket should put the project's check recipe first: {out[:300]}")
        (d / "Makefile").unlink()
        os.environ["PLAYBOOK_MODE"] = "lean"
        try:
            code, out = run([str(GATE), "--ticket", "M1-A-01", "--close"], d)
        finally:
            os.environ.pop("PLAYBOOK_MODE", None)
        if code != 0 or "The close (lean path)" not in out or "--section-from" in out:
            fails.append(f"a passing lean close gate should print /build's lean close (#57 item 9): {out[-300:]}")
        os.environ["PLAYBOOK_MODE"] = "full"
        try:
            code, out = run([str(GATE), "--ticket", "M1-A-01", "--close"], d)
        finally:
            os.environ.pop("PLAYBOOK_MODE", None)
        if code != 0 or "The close, in this order" not in out or "Step 3c" not in out:
            fails.append(f"a passing close gate should print the close's order and rules: {out[-300:]}")
        (d / "docs" / "issues" / "M1-A-01_x.md").write_text(
            f"# [M1-A-01] x\n\n### 🧪 Verification Command\n```bash\n{bad}\n```\n", encoding="utf-8")
        code, out = run([str(GATE), "--ticket", "M1-A-01", "--close"], d)
        if code != 1 or "The close, in this order" in out:
            fails.append(f"a failing close gate should exit 1 and print no close rules: {out[-300:]}")
        code, out = run([str(GATE), "--close"], d)
        if code != 2:
            fails.append("gate --close without --ticket should exit 2")
        # the close REUSES a passing gate of the same commands and ticket when only docs/status changed since - and
        # runs again after ANY other change: committed code, an uncommitted edit, a new file, DESIGN.md (audit 5, fix 2)
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        (d / "util.py").write_text("X = 1\n", encoding="utf-8")  # the reuse test's own code file (app.py: wire-cut test's)
        (d / "docs" / "issues" / "M1-A-01_x.md").write_text(  # a passing verification (the test above left a failing one)
            f"# [M1-A-01] x\n\n### 🧪 Verification Command\n```bash\n{ok}\n```\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "base for reuse"], cwd=d)
        code, out = run([str(GATE), "--ticket", "M1-A-01"], d)
        (d / "docs" / "features").mkdir(parents=True, exist_ok=True)
        (d / "docs" / "features" / "x.md").write_text("# doc\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "doc only"], cwd=d)
        code, out = run([str(GATE), "--ticket", "M1-A-01", "--close"], d)
        if code != 0 or "REUSED" not in out or "The close" not in out or "PASS  " in out.replace("GATE PASS", ""):
            fails.append(f"a close gate over code unchanged since a passing gate should reuse it and print the close rules: {out[:300]}")
        # STRUCTURE.md is check_structure.py's input and a logged close edited it after the gate; a runbook may be
        # another check's: only the run's own records (feature doc, status, changelog) are doc-only (audit 6)
        for change in ("util.py", "DESIGN.md", "new_module.py", "STRUCTURE.md", "docs/runbook.md"):
            (d / change).write_text("# changed\n" + ((d / change).read_text(encoding="utf-8") if (d / change).exists() else ""),
                                    encoding="utf-8")
            code, out = run([str(GATE), "--ticket", "M1-A-01", "--close"], d)
            if "REUSED" in out:
                fails.append(f"a close gate reused a run although {change} changed (uncommitted or new): {out[:200]}")
            subprocess.run(["git", "add", "-A"], cwd=d)
            subprocess.run([*g, "commit", "-qm", f"change {change}"], cwd=d)
        # the loop's last gate checked docs/runbook.md uncommitted; committing it changes no file a check reads, so
        # that pass counts - a logged /test re-ran the full suite after each commit of files it had already checked
        code, out = run([str(GATE), "--ticket", "M1-A-01", "--close"], d)
        if "REUSED" not in out:
            fails.append(f"a gate over the exact files an uncommitted run already checked should reuse it after the "
                         f"commit: {out[:200]}")
        code, out = run([str(GATE), "--ticket", "M1-A-01", "--close", "--fresh"], d)
        if "REUSED" in out or code != 0:
            fails.append(f"--fresh should run the checks again: {out[:200]}")
        (d / "STATUS.md").write_text("# status\n", encoding="utf-8")
        subprocess.run(["git", "add", "STATUS.md"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "status"], cwd=d)
        (d / "STATUS.md").write_text("# status changed\n", encoding="utf-8")
        run([str(GATE), ok], d)
        last = json.loads((d / ".git" / "playbook-gate" / "results.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        if last.get("dirty") != ["STATUS.md"] or not last.get("tree"):
            fails.append(f"the gate should record the dirty path whole (git_out's strip once cut 'STATUS.md' to "
                         f"'TATUS.md') and the tree it checked: {last}")
        code, out = run([str(GATE), "--ticket", "M1-A-01", "--close"], d)
        if "REUSED" not in out:
            fails.append(f"after a fresh passing close gate, a second close with nothing changed should reuse it: {out[:200]}")
        code, out = run([str(GATE), "--ticket", "M1-A-01", "--close", f'{PY} -c "print(1)"'], d)
        if "REUSED" in out:
            fails.append("a close gate with DIFFERENT commands reused a run of other commands")
        # the gate runs its commands in order: the same commands in another order are another run (audit 6)
        one, two = f'{PY} -c "print(1)"', f'{PY} -c "print(2)"'
        run([str(GATE), "--ticket", "M1-A-01", "--close", "--only", one, two], d)
        code, out = run([str(GATE), "--ticket", "M1-A-01", "--close", "--only", two, one], d)
        if "REUSED" in out:
            fails.append(f"a close gate reused a run of the same commands in another order: {out[:200]}")
        code, out = run([str(GATE), "--ticket", "M1-A-01", "--close", "--only", two, one], d)
        if "REUSED" not in out:
            fails.append(f"the same commands in the same order should reuse (the order test's own check): {out[:200]}")
        # named commands ADD to the automatic checks; --only replaces them, and says so (audit 3, finding 1)
        (d / "docs" / "issues" / "M1-A-01_x.md").write_text(
            f"# [M1-A-01] x\n\n### 🧪 Verification Command\n```bash\n{ok}\n```\n", encoding="utf-8")
        extra = f'{PY} -c "print(\'extra ran\')"'
        code, out = run([str(GATE), "--ticket", "M1-A-01", extra], d)
        if f"gate: {ok} · {extra}" not in out:
            fails.append(f"a command named after --ticket should be added after the ticket's own, not replace it: {out[:300]}")
        code, out = run([str(GATE), "--ticket", "M1-A-01", "--only", extra], d)
        if "--only" not in out or f"PASS" not in out or f"  {ok}" in out:
            fails.append(f"--only should run just the named commands and say so: {out[:300]}")
        # a ticket with no Verification Command: the gate says the ticket's behaviour is UNVERIFIED (finding 2)
        (d / "docs" / "issues" / "M1-A-01_x.md").write_text("# [M1-A-01] x\n", encoding="utf-8")
        code, out = run([str(GATE), "--ticket", "M1-A-01", extra], d)
        rec = json.loads((d / ".git" / "playbook-gate" / "results.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        if "UNVERIFIED" not in out or rec.get("ticket_cmds") != [] or rec.get("ticket") != "M1-A-01":
            fails.append(f"a gate with no ticket verification should say UNVERIFIED and record none: {out[:300]} {rec}")
        # the cuts on the command line, no JSON file (a logged build spent 9 calls making one)
        code, out = run([str(CUT), "--cut", f"app.py::user == 'owner'::True::{test}"], d)
        if code != 0 or "RED" not in out or src.read_text(encoding="utf-8") != original:
            fails.append(f"wirecut --cut should cut, go RED and restore: {out[:300]}")
        code, out = run([str(CUT), "--cut", "app.py::only two"], d)
        if code != 2 or "four parts" not in out:
            fails.append(f"wirecut --cut with a malformed cut should exit 2 and say why: {out[:200]}")
        # the close gate refuses a feature doc whose top half a person cannot read (#57 item 13): red on the logged
        # shape (a CLI line, code names, rule codes, the trace lines on top), green on the template's example
        (d / "docs" / "features").mkdir(parents=True, exist_ok=True)
        (d / "docs" / "features" / "demo.md").write_text(BAD_DOC, encoding="utf-8")
        code, out = run([str(GATE), "--ticket", "M1-A-01", "--close", "--only", ok], d)
        if code != 1 or "FEATURE DOC docs/features/demo.md" not in out:
            fails.append(f"the close gate should refuse a feature doc written for the agent: {out[-400:]}")
        (d / "docs" / "features" / "demo.md").write_text(EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        code, out = run([str(GATE), "--ticket", "M1-A-01", "--close", "--only", ok], d)
        if code != 0 or "FEATURE DOC" in out:
            fails.append(f"the close gate should pass the template's example feature doc: {out[-400:]}")
    fails += featuredoc_cases()
    for f in fails:
        print(f"  x {f}")
    print("OK - gate.py, wirecut.py and featuredoc.py behave" if not fails else f"FAIL - {len(fails)} build tool test(s)")
    return 1 if fails else 0


def featuredoc_cases() -> list[str]:
    """featuredoc.py's top-half rule, each refusal shown red ALONE on a doc that is otherwise the clean example."""
    sys.path.insert(0, str(ROOT / "commands" / "build"))
    from featuredoc import top_half_gaps
    fails = []
    good = EXAMPLE.read_text(encoding="utf-8")
    for name, text in (("the template", TEMPLATE.read_text(encoding="utf-8")), ("the example", good)):
        if top_half_gaps(text):
            fails.append(f"featuredoc: {name} should be clean: {top_half_gaps(text)}")
    if len(top_half_gaps(BAD_DOC)) < 5:
        fails.append(f"featuredoc: the logged shape should fail on several counts: {top_half_gaps(BAD_DOC)}")
    lead = "Guests can wander off while they wait instead of standing at the door."
    cases = {
        "a second backticked name": (lead, lead + " It sets `is_ready`."),
        "a rule code": (lead, lead + " See R3."),
        "a section code": (lead, lead + " As #Contracts says."),
        "a snake_case name": (lead, lead + " It flips is_ready."),
        "a file name": (lead, lead + " It lives in notify_service.py."),
        "a trace line": (lead, lead + "\nArchetype: none"),
        "a fenced block": (lead, lead + "\n```\nmake demo\n```"),
        "a missing heading": ("## 4. Not done yet\n", ""),
        "no developer half": ("## 5. For developers and coding agents", "## 5. Developer notes"),
        "no --- line": ("\n---\n", "\n"),
    }
    for name, (find, repl) in cases.items():
        if find not in good:
            fails.append(f"featuredoc case {name!r}: {find[:40]!r} is not in the example")
            continue
        if not top_half_gaps(good.replace(find, repl, 1)):
            fails.append(f"featuredoc: {name} in the top half was not refused")
    # #60: the template and the example number every heading; a doc written before that (no numbers) is still
    # accepted - the numbering, long sentences and dash chains are WARNINGS (prose rules warn, owner 2026-10-09)
    from featuredoc import warnings
    for name, text in (("the template", TEMPLATE.read_text(encoding="utf-8")), ("the example", good)):
        if warnings(text):
            fails.append(f"featuredoc: {name} should raise no warning: {warnings(text)}")
    old = good.replace("## 1. In short", "## In short").replace("### 5.4 Review", "### Review")
    if top_half_gaps(old) or "2 heading(s) without a number" not in " ".join(warnings(old)):
        fails.append(f"featuredoc: unnumbered headings should be accepted and warned: {top_half_gaps(old)} "
                     f"{warnings(old)}")
    long = good.replace(lead, lead + " " + " ".join(["The host can then"] * 9) + " sit down.", 1)
    dash = good.replace(lead, lead + " It is quick — and it is quiet.", 1)
    if "over 30" not in " ".join(warnings(long)) or "em-dash" not in " ".join(warnings(dash)):
        fails.append(f"featuredoc: a sentence over 30 words and a dash chain should warn: {warnings(long)} "
                     f"{warnings(dash)}")
    if top_half_gaps(long) or top_half_gaps(dash):
        fails.append("featuredoc: long sentences and dashes are warnings, never a refusal")
    return fails


if __name__ == "__main__":
    sys.exit(main())
