"""proof.py - run a proof once and log what it showed, so a record cites a run that really happened.

    python proof.py [--env KEY=VALUE | --env KEY=@NAME]... -- <command ...>
    python proof.py plant --file <path> --text "<content>" [--also "<command>"]
    python proof.py plant-secret

run (the default): runs the command through the shell, prints its last lines and `proof: exit N - logged`.
  --env KEY=@NAME puts the value of NAME from .env into KEY (never printed): one form for PowerShell and bash, e.g.
  `--env TEST_DATABASE_URL=@DATABASE_URL -- uv run pytest -q` points the tests at the dev database on purpose.
plant: in a throwaway git worktree holding this folder's current state (your folder, its index and its branch are
  never touched), writes <content> into <path>, commits it through the commit hooks (a gate must refuse it), and runs
  --also there with the plant in place (e.g. the CI step that must fail too). Then the worktree is removed.
plant-secret: the same with a freshly generated fake token in a new file; only the secret-scan hooks run (pre-commit:
  the others are skipped). Exit 0 = the hook refused the commit, 1 = the commit went through.
Every run is appended to playbook-proofs.jsonl in the git folder (never committed): the command, its exit code and
the last lines of its output. A record's `evidence:` line cites what this printed. Standard library only.
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
import string
import subprocess
import sys
import tempfile
from pathlib import Path

LOG_NAME = "playbook-proofs.jsonl"
TAIL_LINES = 80
SECRET_SCANNERS = r"gitleaks|trufflehog|detect-secrets|detect_secrets|ggshield|secretlint"
INSTALL_DIRS = (".agents", ".claude", ".cursor", ".codex", ".gemini")
LINKED = (".venv", "venv", "node_modules")  # the project's installed environments, linked into the worktree


def run_git(cwd: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-c", "user.name=proof", "-c", "user.email=proof@localhost",
                           "-c", "commit.gpgsign=false", *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


def log_file(base: Path) -> Path:
    g = run_git(base, "rev-parse", "--git-common-dir")
    if g.returncode == 0 and g.stdout.strip():
        d = Path(g.stdout.strip())
        return (d if d.is_absolute() else base / d) / LOG_NAME
    return Path(tempfile.gettempdir()) / f"proofs-{hashlib.sha1(str(base.resolve()).encode()).hexdigest()[:10]}" \
        / LOG_NAME


def log(base: Path, entry: dict) -> None:
    """Append one run to the project's proof log (the git folder: never committed, never another project's)."""
    f = log_file(base)
    f.parent.mkdir(parents=True, exist_ok=True)
    entry = {"time": dt.datetime.now().isoformat(timespec="seconds"), **entry}
    entry["tail"] = "\n".join(str(entry.get("tail", "")).splitlines()[-TAIL_LINES:])[-8000:]
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def dotenv(base: Path) -> dict[str, str]:
    out = {}
    f = base / ".env"
    if f.is_file():
        for line in f.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            m = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
            if m:
                out[m.group(1)] = m.group(2).strip().strip("\"'")
    return out


ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")  # colour codes
SECRETISH = re.compile(r"(?i)secret|password|passwd|token|api_?key|private")


def env_for(base: Path, pairs: list[str]) -> tuple[dict, list[str]]:
    """(the environment, how each pair is shown): a value from .env is shown by its name, a secret-looking one masked."""
    env, shown, file = dict(os.environ), [], None
    for p in pairs:
        k, _, v = p.partition("=")
        if not k or not _:
            raise SystemExit(f"proof.py: --env takes KEY=VALUE or KEY=@NAME, not {p!r}")
        if v.startswith("@"):
            file = file if file is not None else dotenv(base)
            if v[1:] not in file and v[1:] not in os.environ:
                raise SystemExit(f"proof.py: {v[1:]} is in neither .env nor the environment")
            env[k] = file.get(v[1:], os.environ.get(v[1:], ""))
            shown.append(f"{k}=<{v[1:]}>")
        else:
            env[k] = v
            shown.append(f"{k}=***" if SECRETISH.search(k) else p)
    return env, shown


def cmd_run(base: Path, a) -> int:
    if len(a.command) == 1:  # one string: the shell reads it as written (pipes, quotes)
        command = a.command[0].strip()
    else:  # separate words: quoted back as the shell would have seen them
        import shlex
        command = subprocess.list2cmdline(a.command) if os.name == "nt" else shlex.join(a.command)
    if not command:
        raise SystemExit("proof.py: name the command after --")
    env, shown = env_for(base, a.env or [])
    p = subprocess.run(command, shell=True, cwd=base, env=env, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
    tail = "\n".join(out.rstrip().splitlines()[-25:])
    print(tail)
    log(base, {"kind": "run", "cmd": command, "env": shown, "exit": p.returncode, "tail": out})
    print(f"proof: exit {p.returncode} - logged ({' '.join(shown + [command])})")
    return p.returncode


def snapshot(base: Path) -> str:
    """A commit object holding this folder as it is now (tracked and new files, .gitignore respected, the playbook's
    install left out), made through a temporary index: the real index, branch and files are never touched."""
    fd, idx = tempfile.mkstemp(prefix="proof-index-")
    os.close(fd)
    os.unlink(idx)
    env = {**os.environ, "GIT_INDEX_FILE": idx}
    try:
        head = run_git(base, "rev-parse", "--verify", "-q", "HEAD").stdout.strip()
        if head:
            run_git(base, "read-tree", head, env=env)
        add = run_git(base, "add", "-A", "--", ".", *(f":(exclude){d}" for d in INSTALL_DIRS), env=env)
        if add.returncode != 0:
            raise SystemExit(f"proof.py: could not snapshot the folder - {add.stderr.strip()[:200]}")
        tree = run_git(base, "write-tree", env=env).stdout.strip()
        c = run_git(base, "commit-tree", tree, *(["-p", head] if head else []), "-m", "proof snapshot")
        if c.returncode != 0:
            raise SystemExit(f"proof.py: could not snapshot the folder - {c.stderr.strip()[:200]}")
        return c.stdout.strip()
    finally:
        Path(idx).unlink(missing_ok=True)


def link(src: Path, dst: Path) -> bool:
    try:
        if os.name == "nt":
            import _winapi
            _winapi.CreateJunction(str(src), str(dst))
        else:
            os.symlink(src, dst, target_is_directory=True)
        return True
    except OSError:
        return False


def unlink_dir_link(p: Path) -> bool:
    """Remove a junction/symlink itself - never what it points at."""
    is_link = p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())
    if not is_link and os.name == "nt":
        try:
            is_link = bool(os.lstat(p).st_file_attributes & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT
        except (OSError, AttributeError):
            is_link = False
    if not is_link:
        return not p.exists()
    try:
        os.unlink(p)
    except OSError:
        os.rmdir(p)
    return not p.exists()


def hook_skips(tree: Path, keep: str) -> str:
    """pre-commit hook ids to SKIP: every hook whose id and entry do not match `keep`."""
    cfg = tree / ".pre-commit-config.yaml"
    if not cfg.is_file():
        return ""
    text = cfg.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"(?m)^\s*-\s+id:\s*", text)[1:]
    skip = []
    for b in blocks:
        hid = b.split()[0].strip("\"'") if b.split() else ""
        body = b.split("\n- ")[0]
        if hid and not re.search(keep, hid + "\n" + body, re.I):
            skip.append(hid)
    return ",".join(dict.fromkeys(skip))


def plant(base: Path, rel: str, text: str, also: str = "", secret_only: bool = False) -> dict:
    """Commit a plant through the hooks in a throwaway worktree of the current state; the result as a log entry."""
    tmp = Path(tempfile.mkdtemp(prefix="proof-plant-"))
    tree = tmp / "w"
    commit = snapshot(base)
    add = run_git(base, "worktree", "add", "--detach", str(tree), commit)
    if add.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        raise SystemExit(f"proof.py: could not make the throwaway worktree - {add.stderr.strip()[:200]}")
    linked = [tree / n for n in LINKED if (base / n).is_dir() and not (tree / n).exists() and link(base / n, tree / n)]
    try:
        target = tree / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        before = target.read_text(encoding="utf-8", errors="replace") if target.is_file() else ""
        target.write_text(before + text + ("\n" if not text.endswith("\n") else ""), encoding="utf-8")
        run_git(tree, "add", "--", rel)
        env = dict(os.environ)
        if secret_only:
            skips = hook_skips(tree, SECRET_SCANNERS)
            if skips:
                env["SKIP"] = skips
        c = subprocess.run(["git", "-c", "user.name=proof", "-c", "user.email=proof@localhost", "-c",
                            "commit.gpgsign=false", "commit", "-m", "proof: planted - must be refused"], cwd=tree,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        moved = run_git(tree, "rev-parse", "HEAD").stdout.strip() != commit
        out = (c.stdout or "") + "\n" + (c.stderr or "")
        entry = {"kind": "plant", "file": rel, "text": text, "cmd": f"plant {rel}", "exit": 0 if moved else 1,
                 "refused": not moved, "tail": out}
        if also:
            a = subprocess.run(also, shell=True, cwd=tree, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env=env)
            entry.update({"also": also, "also_exit": a.returncode,
                          "also_tail": "\n".join(((a.stdout or "") + "\n" + (a.stderr or "")).splitlines()[-40:])})
        return entry
    finally:
        ok = all(unlink_dir_link(p) for p in linked)
        if ok:
            run_git(base, "worktree", "remove", "--force", str(tree))
            shutil.rmtree(tmp, ignore_errors=True)
        run_git(base, "worktree", "prune")
        if not ok:
            print(f"proof.py: left {tree} in place - a link to the project's environment could not be removed "
                  f"safely; delete the links in it first", file=sys.stderr)


def fake_token() -> str:
    rnd = random.SystemRandom()
    return "gh" + "p_" + "".join(rnd.choice(string.ascii_letters + string.digits) for _ in range(36))


def plant_secret(base: Path) -> dict:
    """The secret scan's proof: a fresh fake token in a new file, committed through the scanner hooks only."""
    rel = f"proof-plant-{random.SystemRandom().randrange(10**6):06d}.txt"
    entry = plant(base, rel, f"token = {fake_token()}\n", secret_only=True)
    entry.update({"kind": "plant-secret", "cmd": "plant-secret", "text": "<a fake GitHub token>"})
    return entry


def show(entry: dict) -> None:
    lines = [l for l in entry["tail"].splitlines() if l.strip()]
    keep = [l for l in lines if re.search(r"(?i)fail|error|refus|leak|secret|found|\[FAIL\]", l)] or lines
    print("\n".join(keep[-12:]))
    if "also" in entry:
        print(entry["also_tail"])
        print(f"also: `{entry['also']}` exit {entry['also_exit']}")


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    base = Path.cwd()
    if argv and argv[0] in ("plant", "plant-secret"):
        ap = argparse.ArgumentParser(prog=f"proof.py {argv[0]}")
        if argv[0] == "plant":
            ap.add_argument("--file", required=True)
            ap.add_argument("--text", required=True)
            ap.add_argument("--also", default="")
        a = ap.parse_args(argv[1:])
        if run_git(base, "rev-parse", "--show-toplevel").returncode != 0:
            raise SystemExit("proof.py: a plant needs a git repository (the hooks run on a commit)")
        entry = plant_secret(base) if argv[0] == "plant-secret" else plant(base, a.file.replace("\\", "/"), a.text,
                                                                            a.also)
        log(base, entry)
        show(entry)
        what = "the fake token" if argv[0] == "plant-secret" else f"the plant in {entry['file']}"
        print(f"proof: the commit hooks {'REFUSED' if entry['refused'] else 'LET THROUGH'} {what} - logged; your "
              f"folder was not touched")
        return 0 if entry["refused"] else 1
    ap = argparse.ArgumentParser(prog="proof.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--env", action="append", help="KEY=VALUE, or KEY=@NAME for NAME's value in .env")
    ap.add_argument("command", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    if a.command and a.command[0] == "--":
        a.command = a.command[1:]
    return cmd_run(base, a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
