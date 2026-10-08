"""Behaviour tests for commands/foundation/devserver.py, ci_local.py and proof.py (run by tools/check.py, check 53e).

devserver.py: a server that answers → BOOTED and the port is free afterwards; a boot that exits → DID NOT BOOT with its
own error line; a taken port → refused. ci_local.py: a workflow's run steps run in order (block scalars included), an
action is listed as covered, a failing step fails the run and prints its output - with PyYAML and without it; --only
runs one step. proof.py: a run logged with its exit and output, --env from .env unprinted, a plant committed through
the hooks in a throwaway copy (refused or let through) with the folder untouched.
"""
from __future__ import annotations

import socket
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEV = ROOT / "commands" / "foundation" / "devserver.py"
CI = ROOT / "commands" / "foundation" / "ci_local.py"
PROOF = ROOT / "commands" / "foundation" / "proof.py"
sys.path.insert(0, str(CI.parent))
import ci_local  # noqa: E402

WORKFLOW = """name: ci
on: [push]
env:
  GREETING: hello
jobs:
  check:
    runs-on: ubuntu-latest
    env:
      TARGET: world
    steps:
      - uses: actions/checkout@v5
      - name: Say hello
        run: |
          echo "$GREETING $TARGET" > out.txt
          grep -q "hello world" out.txt
      - name: One line
        run: test -f out.txt
      - name: Breaks
        run: echo "the step's own error"; exit 3
      - name: Never reached
        run: echo unreachable > never.txt
"""


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def run(args: list[str], cwd: Path) -> tuple[int, str]:
    p = subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=180)
    return p.returncode, p.stdout + p.stderr


def proof_log(d: Path) -> list[dict]:
    import json
    f = d / ".git" / "playbook-proofs.jsonl"
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()] if f.is_file() else []


def test_proof(d: Path, g: list[str], fails: list[str]) -> None:
    """proof.py: a run is logged with its exit and output; --env KEY=@NAME takes NAME from .env, unprinted; a plant is
    committed through the hooks in a throwaway copy - refused or let through, the folder untouched."""
    log = proof_log(d)
    if not any(e["cmd"].startswith("ci_local.py") and e["exit"] == 1 and "Breaks" in e["tail"] for e in log):
        fails.append(f"ci_local should log its run (exit 1, the failed step) in the proof log: {[e['cmd'] for e in log]}")
    code, out = run([str(PROOF), "--", "python", "-c", "print('hello from the proof'); raise SystemExit(3)"], d)
    e = proof_log(d)[-1]
    if code != 3 or "proof: exit 3 - logged" not in out or e["exit"] != 3 or "hello from the proof" not in e["tail"]:
        fails.append(f"proof.py should run, print and log the command with its exit: {out.strip()[:200]} / {e}")
    (d / ".env").write_text("DATABASE_URL=postgresql://dev:sekret@127.0.0.1:5432/shop_dev\n", encoding="utf-8")
    code, out = run([str(PROOF), "--env", "TEST_DATABASE_URL=@DATABASE_URL", "--", "python", "-c",
                     "import os; print(os.environ['TEST_DATABASE_URL'].endswith('shop_dev'))"], d)
    e = proof_log(d)[-1]
    if code != 0 or "True" not in out or "sekret" in out or "TEST_DATABASE_URL=<DATABASE_URL>" not in e["env"]:
        fails.append(f"proof.py --env KEY=@NAME should pass .env's value without printing it: {out.strip()[:200]}")
    (d / ".env").unlink()
    (d / "work.txt").write_text("uncommitted work\n", encoding="utf-8")
    (d / ".venv").mkdir()
    (d / ".venv" / "keep.txt").write_text("the project's environment\n", encoding="utf-8")
    hook = d / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nif git diff --cached | grep -q 'ghp_'; then echo 'leaks found: 1'; exit 1; fi\n",
                    encoding="utf-8")
    hook.chmod(0o755)
    before = subprocess.run(["git", "status", "--porcelain"], cwd=d, capture_output=True, text=True).stdout
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout
    code, out = run([str(PROOF), "plant-secret"], d)
    if code != 0 or "REFUSED the fake token" not in out or proof_log(d)[-1]["refused"] is not True:
        fails.append(f"proof.py plant-secret through a scanning hook should be refused: {out.strip()[:300]}")
    hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    code, out = run([str(PROOF), "plant", "--file", "ui/x.html", "--text", '<p style="color: #ff0000">',
                     "--also", "python -c \"import pathlib; print(pathlib.Path('ui/x.html').read_text())\""], d)
    e = proof_log(d)[-1]
    if code != 1 or "LET THROUGH" not in out or e["refused"] or "#ff0000" not in e.get("also_tail", ""):
        fails.append(f"proof.py plant through a hook that passes should say so, --also seeing the plant: "
                     f"{out.strip()[:300]}")
    after = subprocess.run(["git", "status", "--porcelain"], cwd=d, capture_output=True, text=True).stdout
    if after != before or head != subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True,
                                                 text=True).stdout or (d / "ui").exists() \
            or not (d / ".venv" / "keep.txt").is_file() \
            or subprocess.run(["git", "worktree", "list"], cwd=d, capture_output=True, text=True).stdout.count("\n") != 1:
        fails.append(f"a plant must leave the folder, its branch, its environment and the worktree list untouched: "
                     f"{before!r} -> {after!r}")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        port = free_port()
        code, out = run([str(DEV), "check", "--cmd", f"{sys.executable} -m http.server {port}", "--port", str(port),
                         "--health", f"http://127.0.0.1:{port}/"], d)
        if code != 0 or "BOOTED" not in out or f"port {port} free" not in out:
            fails.append(f"devserver check on a server that answers: {out.strip()[:200]}")
        code, out = run([str(DEV), "check", "--cmd", f"{sys.executable} -c \"print('missing SECRET_KEY'); "
                         f"raise SystemExit(3)\"", "--port", str(port), "--health", f"http://127.0.0.1:{port}/",
                         "--timeout", "15"], d)
        if code != 1 or "DID NOT BOOT" not in out or "missing SECRET_KEY" not in out:
            fails.append(f"devserver check on a boot that exits should fail and show its error: {out.strip()[:200]}")
        # E2: the placeholder proof in one call - the app started as prod starts it, on .env.example's values. A guard
        # that only a request handler calls lets the app answer on every placeholder (a logged run): `refuses` fails it.
        app = d / "app.py"
        app.write_text("import os, sys, http.server, socketserver\n"
                       "v = os.environ.get('SECRET_KEY', '')\n"
                       "if os.environ.get('GUARD') == 'on' and 'CHANGE_ME' in v:\n"
                       "    print('Refusing to start: SECRET_KEY is still the .env.example placeholder'); sys.exit(2)\n"
                       "socketserver.TCPServer(('127.0.0.1', int(sys.argv[1])), "
                       "http.server.SimpleHTTPRequestHandler).serve_forever()\n", encoding="utf-8")
        (d / ".env.example").write_text("# how to get it: openssl rand -base64 32\n"
                                        "SECRET_KEY=CHANGE_ME__SECRET_KEY__CHANGE_ME\nGUARD=on\n", encoding="utf-8")
        start = ["--cmd", f"{sys.executable} app.py {port}", "--port", str(port), "--health",
                 f"http://127.0.0.1:{port}/", "--timeout", "15"]
        code, out = run([str(DEV), "refuses", *start, "--env-file", ".env.example"], d)
        if code != 0 or "REFUSED TO BOOT" not in out or "SECRET_KEY" not in out or f"port {port} free" not in out:
            fails.append(f"devserver refuses on a guard that stops the boot should pass, naming the variable: "
                         f"{out.strip()[:240]}")
        (d / ".env.example").write_text("SECRET_KEY=CHANGE_ME__SECRET_KEY__CHANGE_ME\nGUARD=off\n", encoding="utf-8")
        code, out = run([str(DEV), "refuses", *start, "--env-file", ".env.example"], d)
        if code != 1 or "BOOTED" not in out or "decorative" not in out or f"port {port} free" not in out:
            fails.append(f"devserver refuses on an app that boots on the placeholders should fail: {out.strip()[:240]}")
        (d / "real.env").write_text("SECRET_KEY=a-real-value\nGUARD=on\n", encoding="utf-8")
        code, out = run([str(DEV), "check", *start, "--env-file", "real.env"], d)
        if code != 0 or "BOOTED" not in out:
            fails.append(f"devserver check --env-file should pass the file's values to the app: {out.strip()[:240]}")
        # a port of its own: on Linux the checked server's port sits in TIME_WAIT and refuses a plain bind
        holder = socket.socket()
        holder.bind(("127.0.0.1", 0))
        holder.listen()
        taken = holder.getsockname()[1]
        code, out = run([str(DEV), "start", "--cmd", "echo x", "--port", str(taken)], d)
        holder.close()
        if code == 0 or "already taken" not in out:
            fails.append(f"devserver start on a taken port should be refused: {out.strip()[:200]}")

        (d / ".github/workflows").mkdir(parents=True)
        (d / ".github/workflows/ci.yml").write_text(WORKFLOW, encoding="utf-8")
        code, out = run([str(CI)], d)
        if code != 2 or "commit first" not in out:
            fails.append(f"ci_local outside a repo with a commit should be refused: {out.strip()[:200]}")
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q"], cwd=d)
        subprocess.run(["git", "add", "-A"], cwd=d)
        subprocess.run([*g, "commit", "-qm", "ci"], cwd=d)
        code, out = run([str(CI)], d)
        if "NOT RUN" in out:
            print(f"SKIPPED ci_local part - {out.strip()[:120]}")
        else:
            if code != 1 or "✓ Say hello" not in out or "✓ One line" not in out or "✗ Breaks: exit 3" not in out:
                fails.append(f"ci_local should pass two steps and fail the third: {out.strip()[:300]}")
            if "the step's own error" not in out:
                fails.append("ci_local should print a failed step's output")
            if "clean checkout of" not in out or (d / "out.txt").exists():
                fails.append("ci_local should run in a clean checkout, writing nothing into the project folder")
            if "covered by this machine" not in out or "Verified LOCALLY" not in out:
                fails.append("ci_local should list the action as covered and say the proof is local")
            (d / ".env").write_text("DATABASE_URL=postgresql://dev:pw@localhost:5432/shop_dev\n", encoding="utf-8")
            (d / ".github/workflows/ci.yml").write_text(WORKFLOW.replace(
                "  GREETING: hello", "  GREETING: hello\n  DATABASE_URL: postgresql://dev:pw@localhost:5432/shop_dev"),
                encoding="utf-8")
            subprocess.run(["git", "add", ".github"], cwd=d)
            subprocess.run([*g, "commit", "-qm", "dev db"], cwd=d)
            code, out = run([str(CI)], d)
            if code != 2 or "development database" not in out:
                fails.append(f"ci_local should refuse steps that get the .env database: {out.strip()[:200]}")
            if subprocess.run(["git", "worktree", "list"], cwd=d, capture_output=True, text=True).stdout.count("\n") != 1:
                fails.append("ci_local left a worktree behind")
            (d / ".github/workflows/ci.yml").write_text(WORKFLOW, encoding="utf-8")
            subprocess.run(["git", "add", ".github"], cwd=d)
            subprocess.run([*g, "commit", "-qm", "back"], cwd=d)
            (d / ".env").unlink()
            code, out = run([str(CI), "--only", "Say hello"], d)  # one fixed step re-run alone, never the whole CI
            if "✓ Say hello" not in out or "✓ One line" in out or "Breaks: exit" in out:
                fails.append(f"ci_local --only should run that step alone: {out.strip()[:300]}")
            test_proof(d, g, fails)
        small = ci_local.small_yaml_steps(WORKFLOW)
        steps = small["jobs"]["check"]["steps"]
        if [s.get("name") for s in steps[1:]] != ["Say hello", "One line", "Breaks", "Never reached"] \
                or "grep -q" not in steps[1].get("run", "") or small["jobs"]["check"]["env"].get("TARGET") != "world" \
                or small["env"].get("GREETING") != "hello" or steps[0].get("uses") != "actions/checkout@v5":
            fails.append(f"the small workflow reader (no PyYAML) misread the layout: {small}")
    for f in fails:
        print(f"  x {f}")
    print("OK - devserver.py and ci_local.py behave" if not fails else f"FAIL - {len(fails)} foundation tool test(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
