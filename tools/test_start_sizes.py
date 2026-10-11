"""P47: every phase's start stays under START_CAP characters on a realistic filled project (run by tools/check.py).

Claude Code shows a tool output whole only up to 30,000 characters; a longer one is cut to a file the model then reads
again, so the start is paid twice (a logged /structure start reached 59K chars and was read twice). A size written down
with no check crept: this test runs the real `status.py next --phase <phase>` for every skill in manifest.json, in a
subprocess, on a project filled like a logged run, and names each phase over the cap with its size.

Antigravity's short start (3,500 bytes) is held by tools/test_status.py ag_start_fits and the close tests; this test is
the Claude Code / Cursor / Codex route (no TOOL file beside status.py).

A start prints the playbook's install path (commands, rule files) and the project folder, so its size grows with
where both sit. The test measures every start as if the playbook were installed at a LONG_INSTALL-character path and
the project sat at a LONG_PROJECT-character path: each printed copy of the real path counts as that long. A real
plugin install is ~100 characters (C:/Users/<name>/.claude/plugins/cache/<marketplace>/<plugin>/<version>/) and a
long user name or another agent's install route adds more; a start measured from a short checkout fit the cap and
broke it on a real install. The arithmetic is used, not a copy under a deep folder: no copy of the repo per run and no
Windows 260-character path limit. A printed copy of the install path in a form the count does not know fails the test
(the folder's name appearing more often than the full path), so the margin can not silently fall away.

The fixture is built only from the fixtures already in tools/test_*.py (no test project's files are shipped). Its
#Vision/#Scope/#Plan/#Architecture/#Structure and docs/*.md are padded with neutral sub-bullets to the character
sizes a logged run's records had (REAL_SIZES), so a start that quotes a section grows as it would on a real project.

    python tools/test_start_sizes.py            # check, exit 1 on any phase over the cap
    python tools/test_start_sizes.py --sizes    # print every phase's size
    python tools/test_start_sizes.py --cap 10000  # prove the check goes red
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import test_structure_close as S  # noqa: E402  the project after a realistic /structure run
import test_tickets_close as K  # noqa: E402  a full #Plan and #Contracts
import test_design_close as D  # noqa: E402  #Vision and #Scope with table stakes

START_CAP = 25000  # characters; Claude Code cuts at 30,000 - the margin is for a project bigger than the fixture
LONG_INSTALL = 160  # characters: each printed install path is counted at this length (a real install is ~100)
LONG_PROJECT = 100  # characters: each printed project folder is counted at this length
# Phases over the cap while their own fix is on another branch (P46/P47, 2026-10-06): reported, not failed. Empty this
# when those branches merge - the main window runs this test then, and every phase must fit.
WAITING: set[str] = set()  # all three fixed and merged (2026-10-06)

# character sizes of a logged run's records (PRODUCT.md sections and docs/*.md) after /structure; sizes only
REAL_SIZES = {"Vision": 4500, "Scope": 4100, "Plan": 5400, "Architecture": 9400, "Structure": 3000,
              "docs/vision.md": 18800, "docs/scope.md": 4100, "docs/plan.md": 5400, "docs/architecture.md": 37400}
PAD = ("the team keeps this decision written down here so a later phase quotes it word for word and never asks the "
       "owner the same question twice")


def padded(text: str, size: int) -> str:
    """`text` with neutral sub-bullets added under its fields, round robin, until it is `size` characters."""
    lines = text.rstrip("\n").split("\n")
    fields = [i for i, l in enumerate(lines) if l.startswith("- **")] or [len(lines) - 1]
    extra: dict[int, list[str]] = {i: [] for i in fields}
    n, k = len(text), 0
    while n < size:
        line = f"  - note {k + 1}: {PAD}"
        extra[fields[k % len(fields)]].append(line)
        n += len(line) + 1
        k += 1
    out: list[str] = []
    for i, l in enumerate(lines):
        if i in extra and i != fields[0]:  # a new field: the previous field's notes close its block
            out.extend(extra.pop(max(f for f in fields if f < i)))
        out.append(l)
    for f in list(extra):
        out.extend(extra.pop(f))
    return "\n".join(out) + "\n"


def doc(title: str, size: int) -> str:
    body = f"# {title}\n\n## Owner's answers\n\n1. Two months of fake payroll data for one employee.\n\n## Workings\n\n"
    return padded(body + "- **Reasoning:** each choice below names the answer it came from.\n", size)


def project(d: Path) -> None:
    """The project after /structure, every earlier record filled to a logged run's size, the template's later
    sections still empty (as on a real project at that point)."""
    S.hr_project(d)
    template = (ROOT / "templates" / "PRODUCT.md").read_text(encoding="utf-8")
    product = S.status.product_sections(S.PRODUCT)
    filled = {"Vision": D.VISION, "Scope": D.SCOPE + product["Scope"].split("- **In scope (now):**", 1)[-1],
              "Plan": K.PLAN, "Architecture": S.ARCHITECTURE, "Structure": S.SECTION_OK}
    text = template
    for name, body in filled.items():
        text = S.status.replace_section(text, name, padded(body, REAL_SIZES[name]))
    (d / "PRODUCT.md").write_text(text, encoding="utf-8", newline="\n")
    for rel, title in (("docs/vision.md", "Vision"), ("docs/scope.md", "Scope"), ("docs/plan.md", "Plan"),
                       ("docs/architecture.md", "Architecture")):
        S.write(d, rel, doc(title, REAL_SIZES[rel]))


def phases() -> list[str]:
    return [c["id"] for c in json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))["commands"]]


def path_copies(out: str, path: Path) -> int:
    """How many times `path` is printed in `out` (forward or back slashes, any case)."""
    low = out.lower()
    forms = {path.as_posix().lower(), str(path).lower()}
    return sum(low.count(f) for f in forms)


def long_size(out: str, project_dir: Path) -> int:
    """`out`'s length with every printed install path counted at LONG_INSTALL characters and every printed project
    folder at LONG_PROJECT (the project folder sits outside the install, so the two never overlap)."""
    n = len(out) + path_copies(out, ROOT) * (LONG_INSTALL - len(ROOT.as_posix()))
    return n + path_copies(out, project_dir) * (LONG_PROJECT - len(project_dir.as_posix()))


def start_size(d: Path, phase: str) -> tuple[int, int, str]:
    p = subprocess.run([sys.executable, str(ROOT / "tools" / "status.py"), "next", "--phase", phase], cwd=d,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, long_size(p.stdout, d), p.stdout


def sizes(d: Path) -> dict[str, tuple[int, int, str]]:
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(zip(phases(), pool.map(lambda ph: start_size(d, ph), phases())))


def main(argv: list[str]) -> int:
    cap = int(argv[argv.index("--cap") + 1]) if "--cap" in argv else START_CAP
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "p"
        project(d)
        got = sizes(d)
    if "--sizes" in argv:
        for ph, (code, n, _) in got.items():
            print(f"{ph:16} {n:7,}{'  OVER' if n > cap else ''}")
    fails = []
    short = [ph for ph, (_, n, _) in got.items() if n < 500]
    if len(got) < 20 or short:
        fails.append(f"a start printed almost nothing - the fixture did not reach it: {', '.join(short)}")
    # the folder name as a path segment, once every full install path is taken out: in a checkout named
    # `product-playbook` (the public repo's CI, /home/runner/work/product-playbook/product-playbook) every start also
    # prints the product's own name and its commands (/product-playbook:plan), and the parent folder has the same name
    seg = re.compile(rf"(?i)[\\/]{re.escape(ROOT.name)}(?![\w.:-])")
    full = re.compile("|".join(re.escape(f) for f in {ROOT.as_posix(), str(ROOT)}), re.I)
    unknown = [ph for ph, (_, _, out) in got.items() if seg.search(full.sub("", out))]
    if unknown:
        fails.append(f"the install path is printed in a form this test does not count at {LONG_INSTALL} characters "
                     f"(the folder name {ROOT.name} without its full path): {', '.join(unknown)}")
    over = [(ph, n) for ph, (_, n, _) in got.items() if n > cap]
    waiting = [(ph, n) for ph, n in over if ph in WAITING]
    over = [(ph, n) for ph, n in over if ph not in WAITING]
    if over:
        fails.append(f"start over {cap:,} characters at a {LONG_INSTALL}-character install path (Claude Code cuts at "
                     f"30,000 and the run reads it twice): "
                     + " · ".join(f"/{ph} {n:,}" for ph, n in over))
    for ph, (_, n, out) in got.items():  # a start that hands the rest to a file read whole: that file is paid too
        m = re.search(r"read `([^`]+-start\.md)` ONCE", out)
        if m and Path(m.group(1)).is_file():
            size = len(Path(m.group(1)).read_text(encoding="utf-8"))
            print(f"note: /{ph} prints {n:,} chars and points at {Path(m.group(1)).name} ({size:,} chars, read whole)")
    for ph, n in waiting:
        print(f"note: /{ph} start is {n:,} chars, over {cap:,} - its fix is on another branch (WAITING)")
    if fails:
        print("FAIL: " + "\n      ".join(fails))
        return 1
    fit = {ph: n for ph, (_, n, _) in got.items() if n <= cap}
    print(f"OK - {len(fit)} of {len(got)} starts under {cap:,} characters at a {LONG_INSTALL}-character install path (largest /{max(fit, key=fit.get)} "
          f"{max(fit.values()):,}){f'; {len(waiting)} WAITING' if waiting else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
