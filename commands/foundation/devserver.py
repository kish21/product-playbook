"""devserver.py - start, check and stop a dev server in ONE call, and never leave the port taken.

A server started in the background on Windows can keep its port after it is "stopped", and finding and killing it
costs many calls. This does the start, the health poll and the stop itself, kills the whole
process tree, then proves the port is free - and prints one line.

    python devserver.py check --cmd "<start command>" --port 8000 --health http://localhost:8000/healthz
    python devserver.py start --cmd "<start command>" --port 8000 [--health URL]   (leave it running)
    python devserver.py stop --port 8000                                          (stop it, free the port)
    python devserver.py refuses --cmd "<start command>" --port 8000 --health <url> --env-file .env.example

check: exit 0 = it booted and answered (the line says what it answered), 1 = it did not (the log's last lines).
refuses: the placeholder guard's proof through the real entrypoint, in one call - exit 0 = the app, started on the
file's values, stopped before answering and its output names a variable of the file; 1 = it booted (the guard is
decorative: a validator can pass its unit test while the app answers /health on every placeholder).
--env-file: KEY=VALUE lines put into the app's environment, over the shell's - the app's own .env loader leaves an
environment value alone in the usual loaders (python-dotenv, pydantic-settings, dotenv for Node), so .env is untouched.
The log goes to the system temp folder, never into the project. Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re

import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

WIN = os.name == "nt"


def state_dir() -> Path:
    d = Path(tempfile.gettempdir()) / f"devserver-{hashlib.sha1(os.getcwd().encode()).hexdigest()[:10]}"
    d.mkdir(exist_ok=True)
    return d


def listeners(port: int) -> set[int]:
    """PIDs listening on the port (netstat on Windows, lsof elsewhere)."""
    pids: set[int] = set()
    if WIN:
        out = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True, errors="replace").stdout
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[3].upper() == "LISTENING" and parts[1].rsplit(":", 1)[-1] == str(port):
                pids.add(int(parts[4]))
    else:
        try:
            out = subprocess.run(["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"], capture_output=True,
                                 text=True).stdout
            pids = {int(p) for p in out.split() if p.isdigit()}
        except FileNotFoundError:  # a minimal Linux without lsof: ss prints users:(("name",pid=123,fd=4))
            out = subprocess.run(["ss", "-ltnpH", f"sport = :{port}"], capture_output=True, text=True).stdout
            pids = {int(p) for p in re.findall(r"pid=(\d+)", out)}
    return pids - {0}


def kill_tree(pid: int) -> None:
    if WIN:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            time.sleep(1)
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


def stop(port: int) -> str:
    pidfile = state_dir() / f"{port}.pid"
    if pidfile.is_file():
        kill_tree(int(pidfile.read_text()))
        pidfile.unlink()
    for _ in range(10):  # a reloader's worker can outlive its parent for a moment
        left = listeners(port)
        if not left:
            return f"port {port} free"
        for pid in left:
            kill_tree(pid)
        time.sleep(0.5)
    return f"port {port} STILL taken by PID {', '.join(map(str, sorted(listeners(port))))}"


def env_file(path: str | None) -> dict[str, str]:
    """KEY=VALUE lines of a dotenv file (comments, blanks and `export ` skipped; one level of quotes removed)."""
    if not path:
        return {}
    out = {}
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if m and not line.lstrip().startswith("#"):
            v = m.group(2).strip()
            out[m.group(1)] = v[1:-1] if len(v) > 1 and v[0] == v[-1] and v[0] in "\"'" else v.split(" #")[0].strip()
    return out


def start(cmd: str, port: int, extra: dict[str, str] | None = None) -> tuple[subprocess.Popen, Path]:
    held = listeners(port)
    if held:
        raise SystemExit(f"REFUSED - port {port} is already taken by PID {', '.join(map(str, sorted(held)))}: "
                         f"`devserver.py stop --port {port}` first")
    log = state_dir() / f"{port}.log"
    flags = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if WIN else {"start_new_session": True}
    proc = subprocess.Popen(cmd, shell=True, stdout=log.open("w", encoding="utf-8"), stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, env={**os.environ, **(extra or {})}, **flags)
    (state_dir() / f"{port}.pid").write_text(str(proc.pid))
    return proc, log


def wait_health(url: str, proc: subprocess.Popen, timeout: float) -> tuple[bool, str]:
    t0 = time.time()
    last = "no answer"
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            return False, f"the process exited with code {proc.returncode} before answering"
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                body = r.read(300).decode("utf-8", "replace")
                return True, f"GET {url} -> {r.status} {' '.join(body.split())[:160]} ({time.time() - t0:.1f}s)"
        except urllib.error.HTTPError as e:
            last = f"GET {url} -> {e.code}"
            if e.code < 500:
                return True, f"{last} ({time.time() - t0:.1f}s)"
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
            last = f"no answer ({e.__class__.__name__})"
        time.sleep(0.5)
    return False, f"{last} after {timeout:.0f}s"


def tail(log: Path, n: int = 15) -> str:
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines() if log.is_file() else []
    return "\n".join(f"    {l}" for l in lines[-n:])


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(prog="devserver.py")
    ap.add_argument("action", choices=["check", "start", "stop", "refuses"])
    ap.add_argument("--cmd")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--health", help="URL that answers when the app is up")
    ap.add_argument("--timeout", type=float, default=60)
    ap.add_argument("--env-file", dest="env_file", help="KEY=VALUE lines put into the app's environment")
    a = ap.parse_args(argv)
    if a.action == "stop":
        said = stop(a.port)
        print(said)
        return 0 if "free" in said else 1
    if not a.cmd or (a.action in ("check", "refuses") and not a.health):
        print("REFUSED - check and refuses need --cmd and --health; start needs --cmd", file=sys.stderr)
        return 1
    extra = env_file(a.env_file)
    proc, log = start(a.cmd, a.port, extra)
    ok, said = wait_health(a.health, proc, a.timeout) if a.health else (True, "started (no health URL given)")
    if a.action == "refuses":
        freed = stop(a.port)
        if ok:
            print(f"BOOTED on {a.env_file or 'the shell environment'}: {said} - the guard is decorative: it must stop "
                  f"the boot in the entrypoint, naming the variable; stopped, {freed}")
            return 1
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines() if log.is_file() else []
        keys = [k for k, v in extra.items() if "CHANGE_ME" in v] or list(extra)  # the placeholders, when it has any
        named = [l.strip() for l in lines if any(re.search(rf"\b{re.escape(k)}\b", l) for k in keys)]
        if keys and not named:
            print(f"DID NOT BOOT, but its output names no variable of {a.env_file}: the refusal must say which one "
                  f"and how to get a real value; {said}; stopped, {freed}\n{tail(log)}")
            return 1
        print(f"REFUSED TO BOOT on {a.env_file or 'the shell environment'}: {said}; stopped, {freed}")
        print("\n".join(f"    {l[:200]}" for l in (named or lines)[-6:]))
        return 0 if "free" in freed else 1
    if a.action == "start" and ok:
        print(f"running: {said}; log {log.as_posix()}; stop with `devserver.py stop --port {a.port}`")
        return 0
    freed = stop(a.port)
    print(f"{'BOOTED' if ok else 'DID NOT BOOT'}: {said}; stopped, {freed}")
    if not ok:
        print(tail(log))
    return 0 if ok and "free" in freed else 1


class Tee:
    """Prints as usual and keeps a copy, for the proof log."""

    def __init__(self, stream):
        self.stream, self.kept = stream, []

    def write(self, s: str) -> int:
        self.kept.append(s)
        return self.stream.write(s)

    def flush(self) -> None:
        self.stream.flush()


def logged(argv: list[str]) -> int:
    """main(), then one line in the project's proof log (proof.py beside this file): a record's `evidence:` line
    cites a run the log holds. No proof.py beside it (an older copy): nothing is logged."""
    for stream in (sys.stdout, sys.stderr):  # before the wrap: main() cannot reconfigure a Tee
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    tee = Tee(sys.stdout)
    sys.stdout = tee
    try:
        code = main(argv)
    finally:
        sys.stdout = tee.stream
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import proof
        proof.log(Path.cwd(), {"kind": "run", "cmd": f"{Path(__file__).name} {subprocess.list2cmdline(argv)}",
                               "exit": code, "tail": "".join(tee.kept)})
    except Exception:  # noqa: BLE001 - the log never stops the tool
        pass
    return code


if __name__ == "__main__":
    sys.exit(logged(sys.argv[1:]))
