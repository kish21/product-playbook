"""tools/test_setup_24.py - batch 2.4 for /architect (#40) and /structure (#41), with #60 and #62 for both (check 72).

Each fix shown red by breaking exactly what it checks, then green:
  - #41 S4: a STRUCTURE.md table with no `|---|` row gets one from the script at `set structure filled`.
  - #41 (a logged run, item 1): `status.py waive` drops ONE refusal the owner says does not apply, recorded as an open item with
    the owner's words; a secret / .env / install / security refusal is never waived, and a too-short --check refused.
  - #40 A8 / #41 S8: on Cursor the /architect and /structure starts go to a file read once (as on Antigravity).
  - #40 item 12 / A3: the /architect start names the research helper and its brief on every tool, with a fallback.
  - #40 A10: a law named in docs/architecture.md with no source on its line is a warning.
  - #60: plain-English warnings (sentence length, dash chains) on docs/architecture.md and STRUCTURE.md.
  - #62 B: the close of both phases is one line per block (SHORT_CLOSE_ALSO).
  - 2.4 review: the waiver never refuses a cost refusal for "input tokens" (only a token, the secret); the close of
    both phases is 8 lines in one order with a one-line guard; an /architect clash is an open item, never "ask which
    wins"; the helper is given today's date; every start whose round can pass 4 questions says how to ask more.
Run: python tools/test_setup_24.py
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.dont_write_bytecode = True
import status  # noqa: E402
import test_structure_close as S  # noqa: E402


def test_separators(d: Path, fails: list[str]) -> None:
    S.hr_project(d)
    text = (d / "STRUCTURE.md").read_text(encoding="utf-8")
    lines = text.split("\n")
    # drop the first separator row under a table header
    i = next(n for n, l in enumerate(lines) if l.lstrip().startswith("|") and n + 1 < len(lines)
             and status.re.match(r"^\s*\|?\s*:?-{3,}", lines[n + 1]))
    del lines[i + 1]
    (d / "STRUCTURE.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    code, out = S.close(d)
    after = (d / "STRUCTURE.md").read_text(encoding="utf-8").split("\n")
    if "missing `|---|` row" not in out or not status.re.match(r"^\|(?:---\|)+$", after[i + 1]):
        fails.append(f"S4: set structure filled should add the missing separator row: {out[:400]!r}")
    if code != 0:
        fails.append(f"S4: the record with a fixed table should close: {out[:600]!r}")
    p = d / "plain.md"
    p.write_text("# x\n\n| a | b |\n|---|---|\n| 1 | 2 |\n", encoding="utf-8")
    if status.fix_table_separators(p):
        fails.append("S4: a table that has its separator row is left as it is")


def test_waive(d: Path, fails: list[str]) -> None:
    S.hr_project(d)
    (d / "AGENTS.md").unlink()
    (d / "CLAUDE.md").unlink()
    code, out = S.close(d)
    if code == 0 or "at the project root" not in out:
        fails.append(f"waive: the base case should be refused for the missing agent file: {out[:300]!r}")
        return
    for args, want in ((("--check", "root"), "at least 12 characters"),
                       (("--check", ".env.example declares no"), "never waived"),
                       (("--check", "no CLAUDE.md or AGENTS.md"), "")):
        code, out = S.run(d, "waive", "--from", "structure", *args, "--reason", "the owner keeps agent rules elsewhere")
        if want and (code == 0 or want not in out):
            fails.append(f"waive {args}: should be refused with {want!r}: {out[:300]!r}")
        if not want and code != 0:
            fails.append(f"waive {args}: should record an open item: {out[:300]!r}")
    items = "".join(f.read_text(encoding="utf-8") for f in (d / "status" / "open").glob("*.md"))
    if "Waived: \"no CLAUDE.md or AGENTS.md\"" not in items or "the owner keeps agent rules elsewhere" not in items:
        fails.append("waive: the open item should hold the waived words and the owner's reason")
    code, out = S.close(d)
    if code != 0 or "waived by open item" not in out:
        fails.append(f"waive: the next set should drop exactly that refusal and say so: {out[:600]!r}")
    code, out = S.run(d, "waive", "--from", "vision", "--check", "something long enough", "--reason", "x")
    if code == 0:
        fails.append("waive: only /architect and /structure take a per-check waiver")


def test_cursor_start(fails: list[str]) -> None:
    real = status.playbook_tool
    made = []
    try:
        for tool, phase, to_file in (("cursor", "architect", True), ("cursor", "structure", True),
                                     ("cursor", "vision", False), ("claude", "architect", False)):
            status.playbook_tool = lambda t=tool: t
            out = status.fit_start("FULL START " * 50, phase)
            f = Path(status.__file__).resolve().parent / f"{phase}-start.md"
            if to_file and ("ONCE with your file-read tool" not in out or "never run this `next` again" not in out):
                fails.append(f"Cursor /{phase}: the start should go to a file read once: {out[:200]!r}")
            if to_file:
                made.append(f)
            if not to_file and out != "FULL START " * 50:
                fails.append(f"{tool} /{phase}: the start should be printed whole")
    finally:
        status.playbook_tool = real
        for f in made:
            f.unlink(missing_ok=True)
    # 2.4 merge: Cursor reads any start over CURSOR_INLINE_MAX from a file, in every phase (owner: long starts to a
    # file, as on Antigravity); a short one stays inline. And every phase that prints a start through fit_start can
    # name what its file holds - /tickets, /ship, /eval, /deploy and /learn crashed on Antigravity (KeyError).
    long, short = "L" * (status.CURSOR_INLINE_MAX + 1), "S" * 2000
    try:
        for tool, phase, text, to_file in (("cursor", "tickets", long, True), ("cursor", "tickets", short, False),
                                           ("cursor", "ship", long, True), ("cursor", "vision", short, False),
                                           *[("antigravity", p, short, True) for p in
                                             ("tickets", "ship", "eval", "deploy", "learn", "build", "test")]):
            status.playbook_tool = lambda t=tool: t
            try:
                out = status.fit_start(text, phase)
            except Exception as e:  # noqa: BLE001 - the crash is the finding
                fails.append(f"{tool} /{phase}: the start crashed: {type(e).__name__} {e}")
                continue
            f = Path(status.__file__).resolve().parent / f"{phase}-start.md"
            made.append(f)
            if to_file and "ONCE with" not in out:
                fails.append(f"{tool} /{phase} ({len(text)} chars): the start should go to a file read once")
            if not to_file and out != text:
                fails.append(f"{tool} /{phase} ({len(text)} chars): a short start should be printed whole")
    finally:
        status.playbook_tool = real
        for f in made:
            f.unlink(missing_ok=True)


def test_helper_line(fails: list[str]) -> None:
    real = status.playbook_tool
    try:
        for tool in ("claude", "cursor", "antigravity", "codex", "other"):
            status.playbook_tool = lambda t=tool: t
            line = status.arch_helper_line()
            if "architect-research.md" not in line or "Turn A" not in line:
                fails.append(f"{tool}: the research line should name the brief and the two-turn fallback: {line!r}")
            if tool != "other" and "no helper on this tool" in line:
                fails.append(f"{tool}: has a helper route")
        status.playbook_tool = lambda: "claude"
        if "not in the background" not in status.arch_helper_line():
            fails.append("claude: the helper is waited for (the next step needs its report)")
    finally:
        status.playbook_tool = real
    brief = ROOT / "agents" / "architect-research.md"
    if not brief.is_file() or "name: architect-research" not in brief.read_text(encoding="utf-8"):
        fails.append("agents/architect-research.md is missing or not named architect-research")


def test_doc_warnings(fails: list[str]) -> None:
    good = ("# A\n\n## 1. Overview\n\nThe app keeps payslips in the EU. GDPR Art. 5 applies [1].\n\n"
            "## Appendix A — Sources\n\n[1] GDPR Art. 5 https://gdpr-info.eu/art-5-gdpr/\n")
    if status.law_warnings("docs/architecture.md", good):
        fails.append("A10: a law with a footnote on its line is not a warning")
    bad = good.replace(" [1]", "")
    if not status.law_warnings("docs/architecture.md", bad):
        fails.append("A10: a law with no source on its line should warn")
    long = "## 1. Overview\n\n" + " ".join(["word"] * 40) + ".\n"
    if not any("sentences average" in w for w in status.early_doc_warnings("STRUCTURE.md", long)):
        fails.append("#60: a 40-word sentence should warn")


def test_short_close(fails: list[str]) -> None:
    for phase, want in (("architect", "Nothing to test by hand"), ("structure", "smoke-test command")):
        text = status.close_steps_text(phase, "saved: commit abc1234")
        if "ONE line each" not in text or want not in text:
            fails.append(f"#62 B: /{phase}'s close should be one line per block ({want!r})")
    if "ONE line each" in status.close_steps_text("foundation", "saved: commit abc1234"):
        fails.append("#62 B: the short close covers /architect and /structure only in this batch")


def test_review_24(d: Path, fails: list[str]) -> None:
    """2.4 wording review of the setup phases - each red on the code before its fix."""
    cost = "cost per use: `input tokens: about 900` is not a number"
    if status.NEVER_WAIVED.search(cost):
        fails.append("review 3: a cost refusal naming input tokens is waivable - only a token (a secret) is never waived")
    for secret in ("an API token is in the code", "a .env file is committed", "the secret scanner found one"):
        if not status.NEVER_WAIVED.search(secret):
            fails.append(f"review 3: {secret!r} must stay never-waived")
    for phase in ("architect", "structure"):
        text = status.close_steps_text(phase, "saved: commit abc1234")
        if "`Checked by the save:" not in text or "a verdict per exit criterion" in text:
            fails.append(f"review 5: /{phase}'s guard is ONE line (the 8-line close has no room for a verdict list)")
        if "8 lines (the transition guard, the first line, the four blocks, the last two)" not in text:
            fails.append(f"review 5: /{phase}'s close names its 8 lines in order")
    arch = status.close_steps_text("architect", "saved: commit abc1234")
    if "ask which wins" in arch.split("never ask which wins")[-1] or "Clash: <both sides>" not in arch             or "open items" not in arch:
        fails.append("review 8: an /architect clash is an `open items` line of the fields file, never 'ask which wins'")
    if "today's date (2026-10-09)" not in status.arch_helper_line("2026-10-09"):
        fails.append("review 9: the research helper is given today's date")
    S.hr_project(d)
    for phase in ("plan", "scope", "foundation", "contracts", "design-system", "tickets"):
        code, out = S.run(d, "next", "--phase", phase)
        if code != 0 or "more than 4 questions" not in out:
            fails.append(f"review 1: the /{phase} start (a round that can pass 4 questions) says how to ask more")
    for phase in ("architect", "structure"):
        skill = (ROOT / "commands" / phase / "SKILL.md").read_text(encoding="utf-8")
        if "CAPABILITIES.md" in skill or "4 per call" not in skill and "4 questions per call" not in skill:
            fails.append(f"review 1/10: /{phase} names the question tool and its 4-per-call split, no missing file")


def main() -> int:
    fails: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="setup-24-"))
    try:
        d = tmp / "hr"
        test_separators(d, fails)
        test_waive(d, fails)
        test_review_24(tmp / "hr2", fails)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    test_cursor_start(fails)
    test_helper_line(fails)
    test_doc_warnings(fails)
    test_short_close(fails)
    for f in fails:
        print(f"  x {f}")
    print("OK - 2.4 /architect + /structure fixes behave" if not fails else f"FAIL - {len(fails)} test(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
