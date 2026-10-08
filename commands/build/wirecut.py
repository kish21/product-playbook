"""wirecut.py - every cut-the-wire proof of a ticket in ONE call: break each wire, watch its test go red, restore.

A test only proves a wire is connected if cutting the wire turns it red. A logged build cut 13 wires one call at a
time, each call re-sending a 200k-token conversation. List the cuts in a JSON file instead:

    [{"name": "session token not verified",
      "file": "app/shops/adapters/session_token.py",
      "find": "verify_signature=True", "replace": "verify_signature=False",
      "test": "uv run pytest app/shops/tests/test_install.py -q"}]

    python wirecut.py cuts.json
    python wirecut.py --cut "app/x.py::verify_signature=True::verify_signature=False::uv run pytest -q" [--cut ...]

A cut that proves one claim of the ticket's Demo carries its number, as the start printed it: `--cut "D3=app/x.py::..."`
or `"claim": "D3"` in the JSON. `status.py ticket` needs every Demo claim proven by a RED cut (a logged Gemini build
never sent the order status its Demo named, and its fake accepted any request, so every test passed).

For each cut: `find` must occur exactly once in `file` (else SKIP - say which); the file is changed, the test runs,
and the file's original bytes are put back and checked. RED = the test failed with the wire cut (the proof);
NOT CAUGHT = the test still passed, so it does not guard that wire. A copy of each file is kept inside .git while
its cut runs; a run that was killed is restored first thing on the next run. Each run appends its result to
.git/playbook-wirecut/results.jsonl, which `status.py ticket` reads.

Exit 0 = every cut RED, 1 = a cut NOT CAUGHT or SKIPPED, 2 = a bad cuts file.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

FAILED_LINE = re.compile(r"^(FAILED \S+|ERROR \S+|\d+ failed.*)", re.M)


def backup_dir() -> Path:
    r = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True)
    d = (Path(r.stdout.strip()) if r.returncode == 0 else Path(".")) / "playbook-wirecut"
    d.mkdir(parents=True, exist_ok=True)
    return d


def restore_leftovers(folder: Path) -> None:
    for meta in folder.glob("*.json"):
        info = json.loads(meta.read_text(encoding="utf-8"))
        shutil.copyfile(folder / info["copy"], info["file"])
        print(f"restored {info['file']} from a cut an earlier run did not finish")
        (folder / info["copy"]).unlink(missing_ok=True)
        meta.unlink()


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    usage = ('usage: python wirecut.py --cut "[D<n>=]<file>::<text to break>::<replacement>::<test command>" [--cut ...]\n'
             '       python wirecut.py <cuts.json>   (a list of {"name","file","find","replace","test"})')
    if argv and argv[0] == "--cut":  # LEAN: cuts on the command line - a logged build spent 9 calls making a JSON file
        cuts = []
        for i in range(0, len(argv), 2):
            parts = argv[i + 1].split("::") if argv[i] == "--cut" and i + 1 < len(argv) else []
            if len(parts) != 4 or not all(p.strip() for p in (parts[0], parts[1], parts[3])):
                print(f"wirecut: bad --cut {argv[i + 1] if i + 1 < len(argv) else ''!r}: four parts joined by ::\n{usage}")
                return 2
            claim = re.match(r"(D\d+)=", parts[0])
            file = parts[0][claim.end():] if claim else parts[0]
            cuts.append({"name": f"{file}: {parts[1][:50]}", "file": file, "find": parts[1],
                         "replace": parts[2], "test": parts[3], "claim": claim.group(1) if claim else ""})
        argv = []
    elif len(argv) != 1:
        print(usage)
        return 2
    try:
        cuts = cuts if not argv else json.loads(Path(argv[0]).read_text(encoding="utf-8"))
        assert isinstance(cuts, list) and cuts
        for c in cuts:
            assert all(isinstance(c.get(k), str) for k in ("name", "file", "find", "replace", "test")), c
    except (OSError, ValueError, AssertionError) as e:
        print(f"wirecut: bad cuts file: {e}")
        return 2
    folder = backup_dir()
    restore_leftovers(folder)
    bad, done = 0, []
    for n, c in enumerate(cuts, 1):
        path = Path(c["file"])
        done.append({"file": c["file"], "claim": c.get("claim") or "", "result": "SKIP"})
        if not path.is_file():
            print(f"SKIP        {c['name']}: {c['file']} does not exist")
            bad += 1
            continue
        original = path.read_bytes()
        text = original.decode("utf-8")
        count = text.count(c["find"])
        if count != 1:
            print(f"SKIP        {c['name']}: the find text occurs {count} times in {c['file']} (needs exactly 1)")
            bad += 1
            continue
        digest = hashlib.sha256(original).hexdigest()
        copy = f"{n}.orig"
        (folder / copy).write_bytes(original)
        (folder / f"{n}.json").write_text(json.dumps({"file": str(path), "copy": copy}), encoding="utf-8")
        t0 = time.time()
        try:
            path.write_bytes(text.replace(c["find"], c["replace"]).encode("utf-8"))
            r = subprocess.run(c["test"], shell=True, capture_output=True, text=True, encoding="utf-8",
                               errors="replace")
        finally:
            path.write_bytes(original)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            print(f"wirecut: {c['file']} was NOT restored - copy {folder / copy} over it before anything else")
            return 2
        (folder / copy).unlink()
        (folder / f"{n}.json").unlink()
        secs = time.time() - t0
        if r.returncode != 0:
            why = FAILED_LINE.findall((r.stdout or "") + (r.stderr or ""))
            print(f"RED         {c['name']} ({secs:.0f}s) - {why[0][:160] if why else f'exit {r.returncode}'}")
            done[-1]["result"] = "RED"
        else:
            done[-1]["result"] = "NOT CAUGHT"
            print(f"NOT CAUGHT  {c['name']} ({secs:.0f}s) - `{c['test']}` still passed with the wire cut")
            bad += 1
    print(f"{len(cuts) - bad} of {len(cuts)} cuts RED · every file restored and checked")
    # The record `status.py ticket` reads: a ticket row needs a run on its branch with every cut RED (LP1 - a
    # logged Gemini build ran no cut at all, and shipped a service nothing calls).
    git = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()  # noqa: E731
    with open(folder / "results.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"branch": git("rev-parse", "--abbrev-ref", "HEAD"), "head": git("rev-parse", "HEAD"),
                            "red": len(cuts) - bad, "total": len(cuts), "date": time.strftime("%Y-%m-%d"),
                            "cuts": done}) + "\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
