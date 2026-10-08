"""ci_local.py - run the CI workflow's own steps on this machine, one line per step.

A CI workflow written before the project has a git remote has never run. Passing
these steps locally counts as "verified locally" - never "green on CI" - and an open item stays until CI passes on
a real remote. The steps run from the workflow file itself, so the check and the CI cannot drift apart.

    python ci_local.py [--workflow .github/workflows/ci.yml] [--job <name>] [--skip "<regex>"] [--only "<regex>"]
                       [--keep-going] [--list] [--here]

- Runs in a CLEAN CHECKOUT of HEAD (a temporary git worktree), as a CI runner does: uncommitted work is not in it,
  and nothing a step writes lands in your folder. --here runs in this folder instead.
- Refuses to run when a step would get a database URL from your .env: CI uses throwaway credentials, and a local
  replay must never migrate, seed or test your development data.
- Runs every `run:` step of the job in order, with the workflow's and job's plain `env:` values, in bash.
- A `uses:` step (checkout, setup-python, ...) is listed as covered by this machine, not run.
- A `services:` block (postgres, redis) is listed: point the steps at a local one through env, or --skip them.
- Each step's output goes to a log in the temp folder; a failed step prints its last lines.
Exit: 0 = every run step passed · 1 = a step failed (or nothing ran) · 2 = the workflow could not be read.
Uses PyYAML when installed, else a small reader that handles the usual GitHub Actions layout.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def small_yaml_steps(text: str) -> dict:
    """The usual layout, without PyYAML: jobs → steps with name / run (block or line) / uses / working-directory,
    plus plain `KEY: value` pairs under env: blocks and the names under services:."""
    lines = text.splitlines()
    wf: dict = {"env": {}, "jobs": {}}
    job = None
    in_jobs = False
    i = 0
    ind = lambda s: len(s) - len(s.lstrip(" "))  # noqa: E731
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        if not s or s.startswith("#"):
            i += 1
            continue
        if ind(raw) == 2 and in_jobs and re.match(r"^[\w-]+:\s*$", s):
            job = {"env": {}, "steps": [], "services": []}
            wf["jobs"][s[:-1]] = job
        elif ind(raw) == 0:
            in_jobs = s == "jobs:"
            if s == "env:":
                j = i + 1
                while j < len(lines) and (not lines[j].strip() or ind(lines[j]) > 0):
                    m = re.match(r"^\s+([A-Z_][A-Z0-9_]*):\s*(.*)$", lines[j])
                    if m:
                        wf["env"][m.group(1)] = m.group(2).strip().strip("'\"")
                    j += 1
        elif job is not None and s in ("env:", "services:") and ind(raw) == 4:
            j, key = i + 1, s[:-1]
            while j < len(lines) and (not lines[j].strip() or ind(lines[j]) > 4):
                if key == "env":
                    m = re.match(r"^\s+([A-Z_][A-Z0-9_]*):\s*(.*)$", lines[j])
                    if m and ind(lines[j]) == 6:
                        job["env"][m.group(1)] = m.group(2).strip().strip("'\"")
                elif ind(lines[j]) == 6 and re.match(r"^\s+[\w-]+:\s*$", lines[j]):
                    job["services"].append(lines[j].strip()[:-1])
                j += 1
            i = j
            continue
        elif job is not None and s.startswith("- ") and ind(raw) >= 6:
            step, base_ind = {}, ind(raw)
            first = s[2:]
            body = [" " * (base_ind + 2) + first] + []
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or ind(lines[j]) > base_ind):
                body.append(lines[j])
                j += 1
            k = 0
            while k < len(body):
                m = re.match(r"^\s*(name|run|uses|working-directory|shell):\s*(.*)$", body[k])
                if m and ind(body[k]) == base_ind + 2:
                    key, val = m.group(1), m.group(2).strip()
                    if key == "run" and val in ("|", ">", "|-", ">-"):
                        block, k2 = [], k + 1
                        while k2 < len(body) and (not body[k2].strip() or ind(body[k2]) > base_ind + 2):
                            block.append(body[k2])
                            k2 += 1
                        pad = min((ind(b) for b in block if b.strip()), default=0)
                        step["run"] = "\n".join(b[pad:] for b in block).strip()
                        k = k2
                        continue
                    step[key] = val.strip("'\"")
                k += 1
            job["steps"].append(step)
            i = j
            continue
        i += 1
    return wf


def read_workflow(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text)
        wf = {"env": data.get("env") or {}, "jobs": {}}
        for name, j in (data.get("jobs") or {}).items():
            wf["jobs"][name] = {"env": j.get("env") or {}, "steps": j.get("steps") or [],
                                "services": list((j.get("services") or {}).keys())}
        return wf
    except ImportError:
        return small_yaml_steps(text)


def dev_databases(project: Path) -> dict[str, str]:
    """The database URLs in the project's own .env: a CI step must never be handed one of them. CI generates
    throwaway credentials; a local replay of its steps must not migrate, seed or test the developer's data."""
    env = project / ".env"
    if not env.is_file():
        return {}
    out = {}
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^\s*([A-Z_]*DATABASE_URL)\s*=\s*(\S+)", line)
        if m and "CHANGE_ME" not in m.group(2):
            out[m.group(2).strip("'\"")] = m.group(1)
    return out


def clean_checkout(project: Path) -> Path | None:
    """A detached worktree of HEAD in the temp folder: what a CI runner checks out, and nothing it writes lands in
    the developer's folder. None when this is not a git repo with a commit."""
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=project, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    where = Path(tempfile.mkdtemp(prefix="ci_local-tree-"))
    r = subprocess.run(["git", "worktree", "add", "--detach", "-q", str(where), "HEAD"], cwd=project,
                       capture_output=True, text=True)
    return where if r.returncode == 0 else None


def bash() -> str | None:
    if os.name != "nt":
        return shutil.which("bash")
    git_bash = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe"
    return str(git_bash) if git_bash.is_file() else shutil.which("bash")


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(prog="ci_local.py")
    ap.add_argument("--workflow")
    ap.add_argument("--job")
    ap.add_argument("--skip", help="regex: steps whose name or command matches are not run (say why in the record)")
    ap.add_argument("--only", help="regex: run only the steps whose name or command matches (re-run one fixed step)")
    ap.add_argument("--keep-going", action="store_true")
    ap.add_argument("--list", action="store_true", help="print the steps, run nothing")
    ap.add_argument("--here", action="store_true", help="run in this folder instead of a clean checkout of HEAD")
    a = ap.parse_args(argv)
    wf_path = Path(a.workflow) if a.workflow else next(iter(sorted(Path(".github/workflows").glob("*.y*ml"))), None)
    if wf_path is None or not wf_path.is_file():
        print("REFUSED - no workflow file (.github/workflows/*.yml); give --workflow", file=sys.stderr)
        return 2
    try:
        wf = read_workflow(wf_path)
    except Exception as e:  # noqa: BLE001 - an unreadable workflow is reported, never guessed at
        print(f"REFUSED - cannot read {wf_path.as_posix()}: {e}", file=sys.stderr)
        return 2
    jobs = wf["jobs"]
    names = [a.job] if a.job else list(jobs)
    sh = bash()
    if sh is None:
        print("NOT RUN - no bash on this machine (Git Bash on Windows); CI steps are bash scripts")
        return 1
    logdir = Path(tempfile.mkdtemp(prefix="ci_local-"))
    passed = failed = covered = skipped = 0
    project = Path.cwd()
    dev = dev_databases(project)
    tree = None
    if not a.list and not a.here:
        tree = clean_checkout(project)
        if tree is None:
            print("REFUSED - no commit to check out: commit first (CI runs what is committed), or pass --here",
                  file=sys.stderr)
            return 2
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=project, capture_output=True,
                              text=True).stdout.strip()
        print(f"clean checkout of {head} in {tree.as_posix()} (uncommitted changes are not in it - as on CI)")
    try:
        return run_jobs(a, wf, wf_path, names, sh, logdir, tree or project, dev)
    finally:
        if tree is not None:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=project, capture_output=True)


# a failure no change to the project fixes: a TLS-inspecting proxy, a missing certificate, no network
MACHINE = re.compile(r"(?i)UnknownIssuer|certificate verify failed|self[- ]signed certificate|unable to get local "
                     r"issuer|CERTIFICATE_VERIFY_FAILED|Could not resolve host|Temporary failure in name resolution")


def run_jobs(a, wf, wf_path, names, sh, logdir, cwd_root, dev) -> int:
    jobs = wf["jobs"]
    passed = failed = covered = skipped = 0
    for jn in names:
        job = jobs.get(jn)
        if job is None:
            print(f"REFUSED - no job {jn!r}; jobs: {', '.join(jobs)}", file=sys.stderr)
            return 2
        env = dict(os.environ)
        for k, v in {**wf["env"], **job["env"]}.items():
            v = str(v)
            if "${{" not in v:
                env[k] = v
        mine = sorted(f"{k} (= .env {dev[v]})" for k, v in env.items() if v in dev and not a.list)
        if mine:
            print(f"REFUSED - the steps would run with your development database: {', '.join(mine)}. CI uses "
                  f"throwaway credentials; unset it in this shell, or give the workflow its own test database",
                  file=sys.stderr)
            return 2
        print(f"job {jn} ({wf_path.as_posix()})" + (f" · services {', '.join(job['services'])}: this machine's "
                                                     f"own must be running" if job["services"] else ""))
        for n, step in enumerate(job["steps"], 1):
            label = step.get("name") or step.get("uses") or (step.get("run") or "").splitlines()[0][:60]
            if "run" not in step:
                covered += 1
                print(f"  - {label}: an action ({step.get('uses', '?')}) - covered by this machine, not run")
                continue
            if a.list:
                print(f"  {n:2}. {label}: {' '.join(step['run'].split())[:110]}")
                continue
            if (a.skip and (re.search(a.skip, label) or re.search(a.skip, step["run"]))) or \
                    (a.only and not (re.search(a.only, label) or re.search(a.only, step["run"]))):
                skipped += 1
                print(f"  ~ {label}: skipped ({'--only' if a.only else '--skip'})")
                continue
            cwd = cwd_root / (step.get("working-directory") or ".")
            log = logdir / f"{n:02d}.log"
            t0 = time.time()
            with log.open("w", encoding="utf-8") as fh:
                r = subprocess.run([sh, "-eo", "pipefail", "-c", step["run"]], cwd=cwd, env=env, stdout=fh,
                                   stderr=subprocess.STDOUT)
            took = time.time() - t0
            if r.returncode == 0:
                passed += 1
                print(f"  ✓ {label} ({took:.1f}s)")
            else:
                failed += 1
                last = log.read_text(encoding="utf-8", errors="replace").splitlines()[-12:]
                print(f"  ✗ {label}: exit {r.returncode} ({took:.1f}s) - log {log.as_posix()}")
                print("\n".join(f"      {l}" for l in last))
                if MACHINE.search("\n".join(last)):
                    print("      -> a reason of THIS machine (its proxy or certificates), not of the project: never "
                          "replay the whole CI for it - --skip this step, name it under What I skipped (UNVERIFIED), "
                          "and re-run a fixed step alone with --only")
                if not a.keep_going:
                    break
    if a.list:
        return 0
    verdict = "PASS" if failed == 0 and passed else "FAIL"
    print(f"ci_local: {verdict} - {passed} passed, {failed} failed, {skipped} skipped, {covered} actions covered by "
          f"this machine. Verified LOCALLY, not on a remote: keep the open item until CI is green on the first push.")
    return 0 if verdict == "PASS" else 1


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
