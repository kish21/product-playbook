"""replay.py - run one phase unattended on a fixed copy of a test project, then report what the run did.

A model or a playbook change that starts skipping a step is caught here before users see it. The project is
copied at a fixed commit into a temporary folder (the original is never touched), the phase runs in Claude Code
with the playbook folder given, questions are answered from --answers (the recommended option by default), and
tools/run_report.py reads the session log. Claude Code only: Antigravity and Cursor cannot be driven from a
script, so their runs stay manual and are checked with run_report.py on their logs.

It spends money: one phase is about $2-4 on the strongest model; --max-budget caps it (default $6).

    python tools/replay.py --project ~/my-test-project --ref <commit> --phase structure \
        [--plugin-dir .] [--model claude-opus-5-5] [--answers "..."] [--max-budget 6] [--dry-run] [--keep]

Exit: the run report's exit code (0 = every required step found), 2 = the replay itself failed.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Every question stays in the log word for word (run_report.py checks for them), and is then answered here.
DEFAULT_ANSWERS = ("This is an unattended replay: nobody will answer. Every question the skill tells you to ask, "
                   "including the save question, write out word for word in a message exactly as you would ask it; "
                   "then treat the answer as the option marked (Recommended), or 'yes'. A running gate needs an "
                   "override: use the reason 'replay: testing the playbook'. Do not push. Stop after this phase's "
                   "close.")


def plugin_name(plugin_dir: Path) -> str:
    m = re.search(r'"name"\s*:\s*"([^"]+)"', (plugin_dir / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    return m.group(1) if m else "product-playbook"


def claude_binary() -> str:
    """The VS Code extension's native binary first (an npm-installed `claude` can lag or break), else PATH."""
    ext = sorted(Path.home().glob(".vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude*"))
    return str(ext[-1]) if ext else (shutil.which("claude") or "claude")


def command(a, workdir: Path) -> list[str]:
    plugin = Path(a.plugin_dir).resolve()
    prompt = f"/{plugin_name(plugin)}:{a.phase}" + (f" {a.args}" if a.args else "")
    cmd = [a.claude or claude_binary(), "-p", prompt,
           "--plugin-dir", str(plugin), "--output-format", "json", "--max-budget-usd", str(a.max_budget),
           "--dangerously-skip-permissions", "--append-system-prompt", a.answers]
    if a.model:
        cmd += ["--model", a.model]
    return cmd


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(prog="replay.py", description="replay one phase unattended and report it")
    ap.add_argument("--project", required=True, help="a git repo of a test project")
    ap.add_argument("--ref", required=True, help="the commit to copy (the state just before the phase)")
    ap.add_argument("--phase", required=True)
    ap.add_argument("--plugin-dir", default=str(ROOT), help="the playbook to test (default: this clone)")
    ap.add_argument("--model")
    ap.add_argument("--answers", default=DEFAULT_ANSWERS)
    ap.add_argument("--max-budget", type=float, default=6.0)
    ap.add_argument("--claude", help="the claude binary (default: on PATH, else the VS Code extension's)")
    ap.add_argument("--dry-run", action="store_true", help="print the command, run nothing")
    ap.add_argument("--keep", action="store_true", help="keep the temporary project copy")
    ap.add_argument("--args", help="words after the skill command (a /build ticket id: M1-CONNECT-01)")
    ap.add_argument("--env", action="append", default=[], metavar="FILE",
                    help="an untracked file to copy from the project (.env), repeatable")
    ap.add_argument("--env-sub", action="append", default=[], metavar="OLD=NEW",
                    help="text replaced in every --env file (point the copy at its own database), repeatable")
    a = ap.parse_args(argv)

    project = Path(a.project).expanduser().resolve()
    workdir = Path(tempfile.mkdtemp(prefix=f"replay-{a.phase}-"))
    cmd = command(a, workdir)
    if a.dry_run:
        print("would copy", f"{project}@{a.ref}", "->", workdir)
        print("would run:", " ".join(json.dumps(c) if " " in c else c for c in cmd))
        shutil.rmtree(workdir, ignore_errors=True)
        return 0
    tar = subprocess.run(["git", "-C", str(project), "archive", a.ref], capture_output=True)
    if tar.returncode != 0:
        print(f"replay: cannot archive {project}@{a.ref}: {tar.stderr.decode(errors='replace').strip()}")
        return 2
    with tarfile.open(fileobj=BytesIO(tar.stdout)) as t:
        t.extractall(workdir, **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
    for name in a.env:  # never committed in the copy either: the project's own .gitignore keeps it out
        text = (project / name).read_text(encoding="utf-8")
        for sub in a.env_sub:
            old, _, new = sub.partition("=")
            if old not in text:
                print(f"replay: --env-sub {old!r} not in {name}; refusing to run against the project's own services")
                return 2
            text = text.replace(old, new)
        (workdir / name).write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=workdir)  # the phase commits into this copy, never the original
    subprocess.run(["git", "add", "-A"], cwd=workdir)
    subprocess.run(["git", "-c", "user.email=replay@local", "-c", "user.name=replay", "commit", "-qm", "replay base"],
                   cwd=workdir)
    print(f"replay: /{a.phase} on {project.name}@{a.ref} in {workdir}")
    r = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        result = json.loads(r.stdout)
    except json.JSONDecodeError:
        print(f"replay: the run failed (exit {r.returncode}): {(r.stderr or r.stdout)[-600:]}")
        return 2
    sid = result.get("session_id", "")
    print(f"replay: session {sid} · cost ${result.get('total_cost_usd', 0):.2f} · turns {result.get('num_turns')}")
    logs = list((Path.home() / ".claude" / "projects").glob(f"*/{sid}.jsonl")) if sid else []
    code = 2
    if logs:
        code = subprocess.run([sys.executable, str(ROOT / "tools" / "run_report.py"), "--phase", a.phase,
                               str(logs[0])]).returncode
    else:
        print("replay: no session log found for the run")
    if not a.keep:
        shutil.rmtree(workdir, ignore_errors=True)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
