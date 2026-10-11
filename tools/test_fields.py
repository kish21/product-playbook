"""tools/test_fields.py - #63: the model types each fact ONCE in a fields file; status.py renders docs/<phase>.md and the
phase's PRODUCT.md section from it, checks the required fields, and PRODUCT.md holds only finished phases.

A logged chain wrote each early phase 2-3 times (a drafts message, docs/<phase>.md, a PRODUCT.md section that repeated
it: vision 3,121 + 878 words, scope 829 + 587), and the first save made PRODUCT.md from the full template, so every
later phase re-sent ~1,500 words of empty sections. The fixtures below are what a run would write for the small
restaurant-waitlist product the other tests use. Each check was shown red by breaking what it guards (noted inline).

    python tools/test_fields.py            # the checks (check.py runs it, check 64)
    python tools/test_fields.py --measure  # characters the model types per phase: before (doc + section) vs after
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import status  # noqa: E402

TODAY = "2026-10-09"
os.environ["PLAYBOOK_BOARD"] = "off"

VISION_FIELDS = """\
### vision
Nobody waits at the door guessing.

### plain words
Guests wait outside a full restaurant and give up. The app puts them on a list and texts them when their table is ready. Hosts stop shouting names. It is not a booking system.

### who
Small restaurants with walk-in queues on busy evenings.
- **Hosts at the door.** They run the list on one tablet.
- **Guests on the list.** They get a text and come back.

### job
When the room is full, I want a list that texts guests, so I can seat people without shouting.

### first users
10 restaurants on one street, visited in person; they switch because paper lists fail.

### problem
Walk-ins leave when they cannot see how long the wait is.
- **Lost tables.** A party of four walks away after ten minutes.
- **Shouted names.** The host loses track of who was first.

### root causes
- **No shared list.** The host keeps the queue in their head [1].

### why now
Texting is cheap and every guest carries a phone.
1. **Cheap texts.** A text costs under one cent in 2026 [1].

### market
Waitwhile and Yelp Guest Manager solve it for chains.
**Our angle.** Small restaurants need it without a monthly contract.

### solved today
| Paper list | the host | names get lost |
| Waitwhile | chains | monthly contract |

### worked example
Mia's party of 4 joins the list at 19:05 and gets a text at 19:32.

### experience
| When | What happens |
|---|---|
| Day 0 | Mia's party of 4 joins the list at 19:05 |
| Day 0, 19:32 | the app texts Mia: your table is ready |

### how it works
A guest joins, the host marks a table free, the guest gets a text.
```mermaid
flowchart LR
  A[guest joins] --> B[host marks table free] --> C[text sent]
```

### ai
n/a

### value
A text when the table is ready, so fewer walk-ins leave.
1. **Fewer lost tables.** Each kept party is a table sold [1].

### business model
paid

### target
40 restaurants by 2027-03-31

### inputs
texts sent per week

### guardrail
no-show rate stays under 10%

### instrumentation
nothing records this yet

### riskiest
Guests answer a text.
- **For:** most guests keep their phone at hand [1].
- **Against:** some ignore unknown numbers.
- **How we test it:** one evening with a paper list and real texts.

### constraints
a guest's phone number is personal data (GDPR) · English · the restaurant's own list
- **GDPR, the EU data protection law.** What it means for us: we delete numbers after the visit [1].

### competitors
| Waitwhile | worldwide | waitlists | small-restaurant pricing | same job |

### in scope
- the list
- the text

### out of scope
- bookings

### open questions
1. Do guests answer a text? The owner answers after the test evening.

### answers
1. A waitlist for small restaurants.

### searches
- why now · `restaurant waitlist 2026` · settled: walk-ins grew · https://example.org/a1
- local · `wachtlijst restaurant app Gent` · two local apps · https://example.org/local
- same job · `restaurant waitlist app` · Waitwhile, Yelp Guest Manager · https://example.org/same
- rules · `restaurant guest phone number GDPR` · personal data · https://example.org/rules

### terms
| restaurant | 1+ location, 20+ walk-ins a week | owner |

### sources
1. Example page · a page · https://example.org/a1
"""

SCOPE_FIELDS = """\
### core feature
A host adds a walk-in party to the list and the guest gets a text when the table is ready.

### example
Mia's party of 4 joins at 19:05; the host taps "ready" at 19:32 and Mia gets the text.

### core loop
```mermaid
flowchart LR
  A[party joins] --> B[host taps ready] --> C[guest gets a text]
  C -. wait times .-> A
```

### capacity
solo, ~20 h a week, 4 weeks (owner)

### in scope
| Item | What the user can do | Done when | Moves which number |
|---|---|---|---|
| the list | the host adds a party with a name and a phone number | a party added shows on the list | texts sent per week |
| the ready text | the host taps ready and the guest gets a text | the text arrives within 1 minute | texts sent per week |

### shape
| 1 | the list |
| 2 | the ready text |

### deferred
| a guest's own sign-up page | when 5 restaurants ask for it |

### never
| table bookings | another product's job |

### table stakes
| password reset | N/A - no accounts in the first version |
| email verification | N/A - no accounts |
| account deletion + data export | in now |
| empty / loading / error states | in now |
| privacy policy + terms | in now |
| accessibility baseline | in now |
| a way for a user to report a problem | deferred - when the first restaurant goes live |
| the rules that apply: GDPR for guests' phone numbers | in now |
| the languages its users need: English | in now |

### vision check
- Who it is for: agrees, small restaurants.
- The north star: agrees, texts sent drive restaurants kept.

### options considered
- **A guest app.** Guests would have to install it.

### answers
1. picked: the list and the text
2. solo, 20 h a week, 4 weeks
"""

PLAN_FIELDS = """\
### summary
A host can run the waitlist with real texts by 2026-11-22.

### will prove
A text reaches a guest within a minute of "table ready".

### will not prove
That restaurants pay for it, until the pilot.

### capacity
solo, 20 h/week

### start
2026-10-12

### milestones
| Id | Name | Dates | Delivers | Done when | Retires which risk | Needs |
|---|---|---|---|---|---|---|
| M1 | Core slice | 2026-10-12 → 2026-11-22 (derived: 120 h ÷ 20) | the list; the ready text; error states and an accessible list page | a guest on the list gets a text within 1 minute of ready; error states and the accessibility baseline pass on the list page; account deletion + data export and the privacy policy + terms exist; GDPR deletion runs; English copy | feasibility: the text arrives | nothing outside this milestone |
| M2 | Pilot | 2026-11-23 → 2027-04-30 | Restaurants use it for real on busy evenings. | restaurants seat walk-ins from the list for 14 days | value · usability: they keep using it | a public URL (/deploy, M2) |

### north star
the plan ends 2027-04-30, after 2027-03-31 - kept and flagged (answer 4)

### usability
M2 - hosts run the list unaided on a busy evening; a pass is no help asked.

### schedule risks
- **The text provider's sign-up may slip a week.** We use the slack in M2.

### buffer
1 week in M2

### coverage
| the core feature | M1 |
| the list | M1 |
| the ready text | M1 |
| accessibility baseline | M1 |
| the languages its users need: English | M1 |

### open items
none - every number is the user's

### areas
| security | now | phone numbers are personal data |
| ai-specific | N/A - no AI | the product uses no AI |
| observability | next | logs once the pilot runs |
| developer-experience | now | one command to run it |
| testing | now | the text path is tested |
| infra | next | a host for the pilot |
| documentation | now | the runbook |
| product | now | the pilot feedback |
| GDPR | now | M1 deletes numbers |
| English | now | all copy |

### answers
1. picked: solo, 20 h a week, as recorded
2. from 2026-10-12
3. picked: the pilot follows the core
4. keep the north star and flag it

### scope check
- Every milestone traces to the core feature; no milestone builds a non-goal.
"""
FIXTURES = {"vision": VISION_FIELDS, "scope": SCOPE_FIELDS, "plan": PLAN_FIELDS}


def run(d: Path, *args: str) -> tuple[int, str]:
    out, cwd = io.StringIO(), os.getcwd()
    os.chdir(d)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            try:
                code = status.main(["--file", str(d / "STATUS.md"), "--today", TODAY, *args])
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 2
    finally:
        os.chdir(cwd)
    return code, out.getvalue()


def close(d: Path, phase: str, text: str, *extra: str) -> tuple[int, str]:
    src = d.parent / f"{d.name}-{phase}-fields.md"  # outside the project, as the skill says
    src.write_text(text, encoding="utf-8")
    flags = ("--product", "Demo", "--ai", "no", "--agent", "no") if phase == "vision" and not (d / "STATUS.md").exists() \
        else ()
    return run(d, "set", phase, "filled", "--from-fields", str(src), "--no-commit", *flags, *extra)


def fresh(d: Path) -> None:
    import shutil
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    (d / "README.md").write_text("# Demo\n\nA waitlist for small restaurants.\n", encoding="utf-8")


def chain(d: Path, fails: list[str], upto: str = "plan") -> None:
    fresh(d)
    for phase in ("vision", "scope", "plan"):
        code, out = close(d, phase, FIXTURES[phase])
        if code != 0:
            fails.append(f"the {phase} fixture should close the first time: {out[-700:]!r}")
        if phase == upto:
            return


def headings(text: str) -> list[str]:
    return re.findall(r"(?m)^## (\S+)", text)


def test_required_fields(d: Path, fails: list[str]) -> None:
    """A missing or empty field, an unknown field and a short table row are ONE refusal, and nothing is left behind
    (no PRODUCT.md, no docs/, no STATUS.md). Shown red: field_gaps() returning [] lets the broken file through."""
    fresh(d)
    bad = (VISION_FIELDS.replace("### target\n40 restaurants by 2027-03-31\n", "")
           .replace("### guardrail\nno-show rate stays under 10%", "### guardrail\nTBD")
           .replace("### searches", "### serches")
           .replace("| Waitwhile | worldwide | waitlists | small-restaurant pricing | same job |",
                    "| Waitwhile | worldwide | waitlists |"))
    code, out = close(d, "vision", bad)
    for want in ("`### target` is missing", "`### guardrail` is empty", "unknown field `### serches`",
                 "`### competitors`: a row with 3 cell(s)", "`### searches` is missing"):
        if want not in out:
            fails.append(f"the required-field check should name {want!r} in its one refusal: {out[:600]!r}")
    if code == 0 or out.count("REFUSED") != 1:
        fails.append(f"a fields file with gaps should be refused once: exit {code}")
    left = sorted(p.name for p in d.iterdir())
    if left != ["README.md"]:
        fails.append(f"a refused render should put everything back: left {left}")
    # --dry-run lists the same gaps and writes nothing
    code, out = close(d, "vision", bad, "--dry-run")
    if code != 0 or "DRY RUN" not in out or "`### target` is missing" not in out or (d / "PRODUCT.md").exists():
        fails.append(f"--dry-run should list the gaps and write nothing: {out[:300]!r}")


def test_render(d: Path, fails: list[str]) -> None:
    """One fields file renders both files: numbered headings, optional sections dropped, every PRODUCT.md fact also in
    the document; PRODUCT.md = title + project policy + #Vision only (shown red: product_header() returning the full
    template gives 15 sections)."""
    chain(d, fails, "vision")
    if not (d / "PRODUCT.md").is_file():
        return
    prod = (d / "PRODUCT.md").read_text(encoding="utf-8")
    doc = (d / "docs" / "vision.md").read_text(encoding="utf-8")
    if headings(prod) != ["Project", "Vision"]:
        fails.append(f"after /vision PRODUCT.md should hold the project policy and #Vision only: {headings(prod)}")
    if "{{" in doc or "{{" in prod or "<!--" in doc:
        fails.append("a slot or the layout's comment was left in a rendered file")
    if status.unnumbered_headings(doc):
        fails.append(f"every heading of the rendered document is numbered: {status.unnumbered_headings(doc)[:3]}")
    nums = re.findall(r"(?m)^## (\d+)\.", doc)
    if nums != [str(i) for i in range(1, len(nums) + 1)]:
        fails.append(f"dropped sections leave no gap in the numbering: {nums}")
    if "Others who use it" in doc or "Where AI is used" in doc or "Your brief, answered" in doc:
        fails.append("an empty optional section (others), an n/a AI line and no brief should drop their sections")
    if "```\n## " in doc:
        fails.append("a heading after a dropped section should keep its blank line")
    for label, value in status.section_fields(status.product_sections(prod)["Vision"]).items():
        if label in ("Detail", "Read (file · date · verbatim quote)", "Problem (why now)", "AI"):
            continue
        if value.split(" ")[0] not in doc:
            fails.append(f"#Vision's {label!r} should come from a field the document shows too: {value[:50]!r}")
    if "README.md · 2026-10-09" not in prod:
        fails.append("/vision's Read line comes from README.md, as on the --section-from path")


def test_sections_in_phase_order(d: Path, fails: list[str]) -> None:
    """Each finished phase appends its own section in the phases' order; a phase finishing out of order (validate
    after scope) lands between them; a later re-run replaces its own section only."""
    chain(d, fails)
    if not (d / "PRODUCT.md").is_file():
        return
    prod = (d / "PRODUCT.md").read_text(encoding="utf-8")
    if headings(prod) != ["Project", "Vision", "Scope", "Plan"]:
        fails.append(f"PRODUCT.md should hold exactly the finished phases, in order: {headings(prod)}")
    text = status.replace_section(prod, "Validation", "- **Assumption under test:** guests answer a text\n")
    if headings(text) != ["Project", "Vision", "Validation", "Scope", "Plan"]:
        fails.append(f"a section written out of order is inserted in the phases' order: {headings(text)}")
    before = {k: v for k, v in status.product_sections(prod).items() if k != "Scope"}
    code, out = close(d, "scope", SCOPE_FIELDS.replace("4 weeks (owner)", "5 weeks (owner)"))
    after = status.product_sections((d / "PRODUCT.md").read_text(encoding="utf-8"))
    if code != 0 or "5 weeks" not in after["Scope"] or any(after[k] != v for k, v in before.items()):
        fails.append(f"a re-run rewrites its own section and nothing else: exit {code} {out[-300:]!r}")
    for p in ("Vision", "Scope", "Plan"):
        if status.product_sections(prod).get(p) is None:
            fails.append(f"#{p} missing")
    # what later phases read still parses: /tickets' exit criteria and milestone titles from the rendered #Plan
    plan = status.product_sections(prod)["Plan"]
    crit, titles = status.exit_criteria("## Plan\n" + plan), status.milestone_titles(plan)
    if [c for c, _ in crit.get("M1", [])][:2] != ["M1.1", "M1.2"] or titles.get("M2") != "Pilot":
        fails.append(f"/tickets should read the rendered #Plan: {crit.get('M1', [])[:2]} {titles}")


def test_prose_warns_on_the_fields_path(d: Path, fails: list[str]) -> None:
    """What a script only estimates from prose warns on the fields path (an unmarked number in #Scope), and a #Scope
    table stake in now that the `coverage` table gives a milestone is not refused for its wording; the same stake with
    no coverage row and no exit-criterion match IS refused. Shown red: split_prose_gaps() returning (gaps, [])."""
    chain(d, fails, "scope")
    prod = (d / "PRODUCT.md").read_text(encoding="utf-8")
    if "is not in #Vision and not marked" in prod:
        fails.append("setup")
    plan = PLAN_FIELDS.replace("; English copy", "")
    code, out = close(d, "plan", plan)
    if code != 0 or "! #Scope's table stake 'the languages its users need' is in now" not in out:
        fails.append(f"a stake the coverage table places should only warn: exit {code} {out[-400:]!r}")
    chain(d, fails, "scope")
    code, out = close(d, "plan", plan.replace("| the languages its users need: English | M1 |\n", ""))
    if code == 0 or "'the languages its users need' is in now, and no milestone" not in out:
        fails.append(f"a stake in no milestone and no coverage row should be refused: {out[-400:]!r}")


def test_old_projects_unchanged(d: Path, fails: list[str]) -> None:
    """A project whose PRODUCT.md was written the old way (the full template, long labels, empty later sections) is
    never rewritten: the fields path replaces only the running phase's section; the --section-from path still works
    and still refuses a prose gap there."""
    fresh(d)
    tpl = (ROOT / "templates" / "PRODUCT.md").read_text(encoding="utf-8")
    code, out = close(d, "vision", VISION_FIELDS)  # makes STATUS.md + a vision; then put an old-style spine back
    old = status.replace_section(tpl, "Vision", status.product_sections(
        (d / "PRODUCT.md").read_text(encoding="utf-8"))["Vision"])
    (d / "PRODUCT.md").write_text(old, encoding="utf-8")
    code, out = close(d, "scope", SCOPE_FIELDS)
    new = (d / "PRODUCT.md").read_text(encoding="utf-8")
    keep = {k: v for k, v in status.product_sections(old).items() if k != "Scope"}
    if code != 0 or any(status.product_sections(new).get(k) != v for k, v in keep.items()):
        fails.append(f"an old-style PRODUCT.md keeps every other section byte for byte: exit {code} {out[-300:]!r}")
    if headings(new) != headings(old):
        fails.append("an old-style PRODUCT.md keeps its sections and their order")
    section = status.product_sections(new)["Scope"].replace("(owner)", "")
    src = d.parent / f"{d.name}-old-scope.md"
    src.write_text(section.replace("4 weeks", "4 weeks, 3 restaurants"), encoding="utf-8")
    code, out = run(d, "set", "scope", "filled", "--section-from", str(src), "--no-commit")
    if code == 0 or "not in #Vision and not marked" not in out:
        fails.append(f"the old --section-from path keeps its refusals: {out[-300:]!r}")


def test_json_fields(d: Path, fails: list[str]) -> None:
    """The same fields as JSON (the shape /tickets already writes): text, a list of lines, rows as lists."""
    fresh(d)
    blocks = dict(re.findall(r"(?ms)^### (.+?)\n(.*?)(?=^### |\Z)", VISION_FIELDS))
    data = {k: v.strip() for k, v in blocks.items()}
    data["terms"] = [["restaurant", "1+ location, 20+ walk-ins a week", "owner"]]
    data["in scope"] = ["- the list", "- the text"]
    code, out = close(d, "vision", json.dumps(data, ensure_ascii=False))
    doc = (d / "docs" / "vision.md").read_text(encoding="utf-8") if (d / "docs" / "vision.md").exists() else ""
    if code != 0 or "| restaurant | 1+ location, 20+ walk-ins a week | owner |" not in doc:
        fails.append(f"a JSON fields file should render the same document: exit {code} {out[-300:]!r}")


def test_read_field(d: Path, fails: list[str]) -> None:
    """An input file the run opened itself goes in the `read` field: its receipt lands under the `Read:` line (after
    README.md's on /vision, replacing `none` on /scope) and is checked like any receipt - a misquote is refused.
    Shown red: add_read_receipts() returning the body unchanged drops the receipt."""
    fresh(d)
    line = "Hosts lose about one walk-in party in five on a busy night."
    other = "Most guests wait at the bar or leave within ten minutes."
    (d / "notes.md").write_text(f"# Notes\n\n{line}\n\n{other}\n", encoding="utf-8")
    good = f'\n### read\n  - notes.md · 2026-10-09 · "{line}"\n'
    code, out = close(d, "vision", FIXTURES["vision"] + good)
    prod = d / "PRODUCT.md"
    sec = status.product_sections(prod.read_text(encoding="utf-8")).get("Vision", "") if prod.is_file() else ""
    if code != 0 or not re.search(r'Read \(file[^\n]*README\.md[^\n]*\n  - notes\.md · 2026-10-09 · "Hosts lose', sec):
        fails.append(f"/vision's read field should add its receipt under README.md's: exit {code} {out[-300:]!r}")
    code, out = close(d, "scope", FIXTURES["scope"] + good.replace(line, other))  # a quote twice reads as copied
    sec = status.product_sections(prod.read_text(encoding="utf-8")).get("Scope", "") if prod.is_file() else ""
    if code != 0 or "verbatim quote):**\n  - notes.md · 2026-10-09" not in sec or "only PRODUCT.md sections" in sec:
        fails.append(f"/scope's read field should replace the `none` receipt: exit {code} {out[-300:]!r}")
    code, out = close(d, "plan", FIXTURES["plan"] + '\n### read\n- notes.md · 2026-10-09 · "a line nobody wrote"\n')
    if code == 0 or "Read receipt quote is not in notes.md" not in out:
        fails.append(f"a misquoted read field should be refused: exit {code} {out[-300:]!r}")


def test_templates_agree(fails: list[str]) -> None:
    """Every slot names a listed field; every field the run must write is shown in a rendered file (else it types a
    fact nobody reads); the checks that read the rendered section find their labels."""
    for phase in ("vision", "scope", "plan"):
        spec = status.phase_spec(phase)
        used = set()
        for text in (spec["doc"], spec["section"]):
            for m in status.FIELD_SLOT.finditer(text):
                key = status.field_key(m.group(2).partition(":")[0])
                used.add(key)
                if key not in spec["by"] and key not in status.FIELD_BUILTINS:
                    fails.append(f"templates for {phase}: slot {m.group(0)!r} names no listed field")
        # `read` has no slot: add_read_receipts() places it under the section's `Read:` line
        unused = [f["name"] for f in spec["fields"] if f["name"] not in used and f["name"] != "read"]
        if unused:
            fails.append(f"{phase}: field(s) the run writes but no file shows: {unused}")
        labels = [m.group(1) for m in re.finditer(r"(?m)^- \*\*(.+?):\*\*", spec["section"])]
        for what, rx in {"vision": status.VISION_FIELDS, "scope": status.SCOPE_FIELDS,
                         "plan": status.PLAN_FIELDS}[phase]:
            if not any(re.search(rx, l, re.I) for l in labels):
                fails.append(f"#{phase.capitalize()}'s rendered labels miss {what!r} - its check would not find it")


def test_start_and_rules(d: Path, fails: list[str]) -> None:
    """The start prints the field list (never a template to open) and only the rule sections this run needs: an
    existing project's first /plan run drops Spine resolution, Re-run semantics, Declined runs and Documentation-
    driven; a re-run prints Re-run semantics (#62, #65 item 13). Shown red: situational_skip() returning set()."""
    chain(d, fails, "scope")
    code, out = run(d, "next", "--phase", "plan")
    for want in ("### milestones [table: Id | Name | Dates", "--from-fields <file>", "### coverage"):
        if want not in out:
            fails.append(f"the /plan start should print {want!r}")
    for gone in ("## §Spine resolution", "## §Re-run semantics", "## §Declined runs", "## Documentation-driven",
                 "templates/plan.md", "--section-from"):
        if gone in out:
            fails.append(f"a first /plan run on a project with PRODUCT.md should not print {gone!r}")
    close(d, "plan", PLAN_FIELDS)
    code, out = run(d, "next", "--phase", "plan")
    if "Re-run semantics" not in out:
        fails.append("a /plan re-run should print §Re-run semantics")
    code, out = run(d, "next", "--phase", "scope")
    if "### table stakes [table: Item | Decision]" not in out or "      accessibility baseline" not in out:
        fails.append("the /scope start should print its fields and this product's table stakes")


def measure() -> list[tuple[str, int, int, int]]:
    """(phase, fields file chars, rendered doc chars, rendered section chars) on the fixtures above. Before #63 the
    model typed the document and the section itself (and the copy a drafts message held); now it types the fields."""
    out = []
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "p"
        fails: list[str] = []
        chain(d, fails)
        prod = (d / "PRODUCT.md").read_text(encoding="utf-8")
        for phase in ("vision", "scope", "plan"):
            doc = (d / "docs" / f"{phase}.md").read_text(encoding="utf-8")
            sec = status.product_sections(prod)[phase.capitalize()]
            out.append((phase, len(FIXTURES[phase]), len(doc), len(sec)))
    return out


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if "--measure" in sys.argv:
        tb = ta = 0
        print("phase    typed before (doc + section)   typed after (fields)   saved")
        for phase, f, doc, sec in measure():
            tb, ta = tb + doc + sec, ta + f
            print(f"{phase:8} {doc + sec:>8,} ({doc:,} + {sec:,}){'':10} {f:>8,}{'':12} {1 - f / (doc + sec):.0%}")
        print(f"{'total':8} {tb:>8,}{'':24} {ta:>8,}{'':12} {1 - ta / tb:.0%}")
        # PRODUCT.md as /scope reads it: before, the full template with #Vision filled; now the title, the project
        # policy and #Vision (every later phase re-sends it)
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "p"
            chain(d, [], "vision")
            now = (d / "PRODUCT.md").read_text(encoding="utf-8")
            tpl = (ROOT / "templates" / "PRODUCT.md").read_text(encoding="utf-8")
            then = status.replace_section(tpl, "Vision", status.product_sections(now)["Vision"])
            print(f"PRODUCT.md after /vision: {len(then):,} chars before, {len(now):,} now "
                  f"({1 - len(now) / len(then):.0%} less re-sent by every later phase)")
        return 0
    fails: list[str] = []
    test_templates_agree(fails)
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "p"
        for test in (test_required_fields, test_render, test_sections_in_phase_order,
                     test_prose_warns_on_the_fields_path, test_old_projects_unchanged, test_json_fields,
                     test_start_and_rules, test_read_field):
            test(d, fails)
    for f in fails:
        print(f"  x {f}")
    print("OK - fields render and check" if not fails else f"FAIL - {len(fails)} fields test(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
