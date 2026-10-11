"""tools/test_early_24.py - batch 2.4, the early phases (/playbook, /vision, /scope, /plan, /adopt's PRODUCT.md) and
the shared turn rules (#46 #59 #60 #62 #63 #64 #65). Each check below was shown red on the 2.3 text before its fix.

A logged chain took 6 owner turns to a saved vision (plain: 3): a "Start /vision now?" turn, a separate drafts turn,
and a close that restated the work. The shared rule printed in every start still said "one recommendation + yes/no"
while every skill asks options. /adopt still wrote the whole template (every empty section) into a new PRODUCT.md.

    python tools/test_early_24.py      # check.py runs it (check 66)
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import status  # noqa: E402
import test_fields as tf  # noqa: E402


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def step0(skill: str) -> str:
    text = read(f"commands/{skill}/SKILL.md")
    m = re.search(r"(?ms)^## Step 0.*?(?=^## )", text)
    return m.group(0) if m else ""


def test_three_turn_vision(fails: list[str]) -> None:
    """#62: the drafts are options INSIDE round 2 - round 2's answers are the go-ahead to write (3 owner turns)."""
    skill = read("commands/vision/SKILL.md")
    if re.search(r"(?i)one message of drafts|then one message of drafts", skill):
        fails.append("/vision still sends the drafts as a message of their own (a 4th owner turn)")
    if "inside round 2" not in skill:
        fails.append("/vision should say the drafts are options inside round 2")
    start = status.vision_start_text()
    if "drafts' answers" in start or "round 2's answers" not in start:
        fails.append("the /vision start should write the fields after round 2's answers, not after a drafts turn")


def test_playbook_asks_the_idea(fails: list[str]) -> None:
    """#62: on a fresh folder /playbook asks for the idea in its first reply (the idea is the yes); it never adds a
    confirm turn of its own at a phase's exit gate."""
    skill = read("commands/playbook/SKILL.md")
    if "What's your idea?" not in skill:
        fails.append("/playbook should ask \"What's your idea?\" on a fresh folder, in the same reply as the map")
    if re.search(r"(?i)surface the result and\s+\*\*pause\*\*", skill):
        fails.append("/playbook still pauses for a confirm at a phase's exit gate (the phase saves and asks itself)")


def test_options_rule_everywhere(fails: list[str]) -> None:
    """#59/#62: the shared Communication rule (printed in every start) is the options rule, never a yes/no."""
    principles = read("PRINCIPLES.md")
    m = re.search(r"(?ms)^## Communication.*?(?=^## )", principles)
    sec = m.group(0) if m else ""
    if "recommendation + yes/no" in sec or "(Recommended)" not in sec:
        fails.append("PRINCIPLES.md §Communication should ask options with one (Recommended), never a yes/no")
    for skill in ("scope", "playbook"):
        head = read(f"commands/{skill}/SKILL.md")[:1500]
        if re.search(r"one[- ]recommendation(?: \+ confirm)?\*\*", head):
            fails.append(f"/{skill}'s header still names the one-recommendation rule")


def test_close_six_lines(fails: list[str]) -> None:
    """#62 item B, #65 item 17: a document phase's close is at most 6 lines and never restates the document."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "p"
        tf.fresh(d)
        code, out = tf.close(d, "vision", tf.FIXTURES["vision"])
        if code != 0:
            fails.append(f"setup: the vision fixture should close: {out[-300:]!r}")
            return
        if "6 lines in all: the guard line, then `" not in out or "Nothing to test by hand" in out:
            fails.append(f"the vision close should be 6 lines with no 'nothing to test' line: {out[-900:]!r}")
    # review 2.4 early-2/3: ONE description of the line order everywhere (the guard line first, `Saved` second, What
    # YOU do next = the last two lines), and the close rule `rules --close` prints defers to it
    for skill in ("vision", "scope", "plan"):
        if "the guard line, then `Saved (commit ...).`" not in read(f"commands/{skill}/SKILL.md"):
            fails.append(f"/{skill}'s close should state the line order `set` prints (guard line, then Saved)")
    if "the short close `set` prints wins" not in read("references/mechanisms.md"):
        fails.append("MECHANISMS.md §Plain-language close should say the early phases' short close wins")
    if "then the four blocks" in read("tools/status.py"):
        fails.append("`status.py save` still says 'the four blocks' (the early phases' close has three)")


def test_starts_print_only_what_happens(fails: list[str]) -> None:
    """#62: a new project's /vision start drops Documentation-driven (never on its normal path); the edge cases live in
    the start, printed when true - the skills' Step 0 keep the normal path. /scope over an empty #Vision prints the
    override command itself."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "p"
        tf.fresh(d)
        code, out = tf.run(d, "next", "--phase", "vision")
        if "## Documentation-driven" in out:
            fails.append("a new project's /vision start should not print §Documentation-driven")
        tf.close(d, "vision", tf.FIXTURES["vision"])
        (d / "PRODUCT.md").write_text(status.product_header("Demo"), encoding="utf-8")
        code, out = tf.run(d, "next", "--phase", "scope")
        if "status.py bypass --from scope --gate vision" not in out:
            fails.append(f"/scope over an empty #Vision should print the override command: {out[:900]!r}")
    for skill in ("vision", "scope", "plan"):
        s0 = step0(skill)
        for gone in ("Re-running this phase", "superseded <date>"):  # the override line stays (check 9)
            if gone in s0:
                fails.append(f"/{skill} Step 0 still carries an edge case ({gone!r}) - `next` prints it when true")
        if "next" not in s0:
            fails.append(f"/{skill} Step 0 lost its first command")


def test_override_reason_is_options(fails: list[str]) -> None:
    """review 2.4 early-4: "never a typed reason" contradicted the Other option; the reason is options, Other = the
    user's own words, and `--reason` carries the picked option's words."""
    for rel in ("commands/scope/SKILL.md", "commands/plan/SKILL.md", "PRINCIPLES.md"):
        text = read(rel)
        if "never a typed reason" in text or "reason in the user's own words" in text:
            fails.append(f"{rel}: the override reason is options (Other = the user's own words), never 'typed'")
    how = status.how_text()
    if "<the user's own words>" in how or "<the picked option's words>" not in how:
        fails.append("`status.py how` should show `--reason \"<the picked option's words>\"`")


def test_vision_refine_prints_the_record(fails: list[str]) -> None:
    """review 2.4 early-1: /vision's Step 0 says `next` prints #Vision on a refine run - it printed only the rules, so
    a refine run read PRODUCT.md whole."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "p"
        tf.fresh(d)
        tf.close(d, "vision", tf.FIXTURES["vision"])
        code, out = tf.run(d, "next", "--phase", "vision")
        if "Nobody waits at the door guessing." not in out or "#Vision now" not in out:
            fails.append(f"a refine run's /vision start should print the #Vision fields: {out[:900]!r}")
        if "Fresh start" in out:
            fails.append("a refine run's /vision start should not say fresh start")


def test_adopt_writes_only_filled_sections(fails: list[str]) -> None:
    """#63: the project never gets the full template - /adopt writes only the sections it filled; a later adopt or
    phase adds its own section in the phases' order."""
    import test_status as ts
    import test_support_v2 as sv
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "proj"
        for rel, body in sv.ADOPT_REPO.items():
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text(body, encoding="utf-8")
        sv.git_init(d)
        src = Path(t) / "draft.md"
        src.write_text(sv.ADOPT_DRAFT, encoding="utf-8")
        code, out = ts.run(d, "set", "adopt", "filled", "--section-from", str(src), "--product", "Toolshed",
                           "--no-commit")
        prod = (d / "PRODUCT.md").read_text(encoding="utf-8") if (d / "PRODUCT.md").exists() else ""
        heads = [h for h in re.findall(r"(?m)^## (\S+)", prod) if h != "Project"]
        if code or heads != ["Vision", "Scope", "Architecture", "Tests"]:
            fails.append(f"a new PRODUCT.md from /adopt should hold only the filled sections: {heads} {out[-300:]!r}")
        code, out = ts.run(d, "next", "--phase", "adopt")
        offer = next((l for l in out.splitlines() if "fill only its empty sections" in l), "")
        # review 2.4 early-9: the offer named every missing section (#Design, #Contracts, ...) while /adopt drafts
        # only the sections a repo can evidence
        if "#Structure" not in offer or any(f"#{k}" in offer for k in ("Design", "Contracts", "Plan", "Validation")):
            fails.append(f"the adopt start offers to fill only the empty sections /adopt drafts: {offer!r}")
        src.write_text(sv.ADOPT_DRAFT.replace("## Plan\n", "## Plan\n- **Phases / milestones (core first):** M1 "
                                                           "reservations work end to end\n"), encoding="utf-8")
        code, out = ts.run(d, "set", "adopt", "filled", "--section-from", str(src), "--no-commit")
        prod = (d / "PRODUCT.md").read_text(encoding="utf-8")
        heads = [h for h in re.findall(r"(?m)^## (\S+)", prod) if h != "Project"]
        if code or heads != ["Vision", "Scope", "Plan", "Architecture", "Tests"]:
            fails.append(f"re-adopting adds #Plan in the phases' order: {heads} {out[-300:]!r}")


def test_adopt_leaves_out(fails: list[str]) -> None:
    """review 2.4 early-10: /adopt's Step 2 leaves a section with no evidence OUT of the draft (never written empty);
    its table, exit criteria and confirm-loop still said the section "stays empty"."""
    # review 2.4 early minor: the (AI) and (Agent) field names are conditions a literal copier wrote for every repo;
    # the start says when they apply (the name stays as printed: /architect's check matches it); the unused
    # drop_empty_sections (its docstring said /adopt drafts from the full template) is gone
    start = status.adopt_start_text(ROOT / "STATUS.md", "2026-10-10")
    if "only when a repo file shows an AI feature" not in start:
        fails.append("the adopt start should say an (AI) / (Agent) field is drafted only when a repo file shows one")
    if hasattr(status, "drop_empty_sections"):
        fails.append("status.drop_empty_sections is never called and contradicts /adopt Step 2 - remove it")
    text = read("commands/adopt/SKILL.md")
    for old in ("Leave empty when", "no evidence stays empty", "stays empty rather", "Leave them empty"):
        if old in text:
            fails.append(f"/adopt still says {old!r} - a section or field with no evidence is left out")


def test_status_changes_saved_in_one_call(fails: list[str]) -> None:
    """review 2.4 early-8: `next` told the run to commit an uncommitted STATUS.md with two git commands of its own
    (CAPABILITIES.md: never a git call of your own; on Codex each asks for approval). It names one `status.py save`
    call that commits STATUS.md and status/ only - the user's other unsaved work stays out of the commit."""
    import subprocess
    import test_support_v2 as sv
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "p"
        tf.fresh(d)
        sv.git_init(d)
        tf.close(d, "vision", tf.FIXTURES["vision"])
        subprocess.run(["git", "add", "-A"], cwd=d, capture_output=True)
        subprocess.run(["git", "commit", "-qm", "x", "--no-verify"], cwd=d, capture_output=True)
        # a STATUS.md change no save took (an open item after its phase's save now saves itself)
        tf.run(d, "flag", "--ui", "yes")
        (d / "work.txt").write_text("the user's unsaved work\n", encoding="utf-8")
        code, out = tf.run(d, "next")
        if "git add STATUS.md" in out or "status.py save --status-only -m" not in out:
            fails.append(f"next should name one `status.py save --status-only` call, no git call: {out[-400:]!r}")
        code, out = tf.run(d, "save", "--status-only", "-m", "status: record what the last phase closed")
        left = subprocess.run(["git", "status", "--porcelain"], cwd=d, capture_output=True, text=True).stdout
        if code or "saved: commit" not in out or "work.txt" not in left or "STATUS.md" in left or "status/" in left:
            fails.append(f"save --status-only should commit STATUS.md and status/ only: {out[-300:]!r} left {left!r}")


def test_cursor_start_file_in_project(fails: list[str]) -> None:
    """review 2.4 early-11: on Cursor a long start went into the tools folder - with a user-wide install that is
    ~/.cursor/product-playbook/, outside the workspace (its sandbox may refuse it, a read may ask approval), and two
    windows overwrote each other's file. It goes into the project's .git folder (never committed, this project's
    own), as /foundation's long start does; the header says the tool cuts long output (Cursor cuts, it does not keep
    only the end)."""
    import os
    real, cwd = status.playbook_tool, os.getcwd()
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "p"
        (d / ".git").mkdir(parents=True)
        try:
            status.playbook_tool = lambda: "cursor"
            os.chdir(d)
            out = status.fit_start("L" * (status.CURSOR_INLINE_MAX + 1), "tickets")
        finally:
            status.playbook_tool = real
            os.chdir(cwd)
        f = d / ".git" / "playbook-tickets-start.md"
        if not f.is_file() or f.resolve().as_posix() not in Path(out.split("`")[1]).resolve().as_posix():
            fails.append(f"Cursor's start file should be the project's .git/playbook-tickets-start.md: {out[:300]!r}")
        if "shows only the end" in out or "Your tool cuts long output" not in out:
            fails.append(f"Cursor's start header should say the tool cuts long output: {out[:200]!r}")


def test_small_rules(fails: list[str]) -> None:
    """#64: "trigger" is on the owner's list of playbook words; #59: the helper returns what the enrichment options are
    built from, and a tool with no helper runs the whole brief; #46: which commands ask for approval on Codex."""
    if not status.DOC_PLAYBOOK_WORDS.search("Each item has a trigger."):
        fails.append("'trigger' should warn as a playbook word in a person's document")
    brief = read("agents/vision-research.md")
    if not re.search(r"(?i)\bscale\b", brief) or not re.search(r"(?i)inside the business", brief):
        fails.append("the research helper should return the scale and the people inside the business")
    if "page opens" not in read("commands/vision/SKILL.md"):
        fails.append("/vision: a tool with no helper runs the brief's searches AND its page opens")
    if not re.search(r"(?im)^## Commands that ask for approval", read("references/capabilities.md")):
        fails.append("references/capabilities.md should say which commands ask for approval (Codex)")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    fails: list[str] = []
    for test in (test_three_turn_vision, test_playbook_asks_the_idea, test_options_rule_everywhere,
                 test_close_six_lines, test_starts_print_only_what_happens, test_vision_refine_prints_the_record,
                 test_override_reason_is_options,
                 test_adopt_writes_only_filled_sections, test_status_changes_saved_in_one_call,
                 test_adopt_leaves_out, test_cursor_start_file_in_project,
                 test_small_rules):
        test(fails)
    for f in fails:
        print(f"  x {f}")
    print("OK - early phases 2.4" if not fails else f"FAIL - {len(fails)} early-phase test(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
