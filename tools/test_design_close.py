"""/design-system's start and close on a realistic record (run by tools/check.py, check 53e; a plain script, not pytest).

The record is what a model would write for a logged B2B test product (payroll consultants, FastAPI + Jinja + HTMX):
#Design with the owner's answers, a DESIGN.md that opens for a reader then holds its 9 sections with OKLCH tokens in
light and dark, the stylesheet the app loads with a self-hosted font, an approved sample in both interface languages
that shows what #Scope asks for, and its three screenshots. It must record the first time; each fault a logged run
made is planted alone and must be refused by name; the logged Gemini shapes planted together must be refused ONCE,
every fault named. render_check.py needs a browser, so `set`'s re-run of it is stubbed here (tools/test_render_check.py
drives the real one; its --shots is driven below when Playwright is here).
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import status  # noqa: E402

TODAY = "2026-10-03"
REAL_RECHECK = status.render_recheck
RENDER = {"code": 0, "out": "render_check: PASS"}

VISION = """- **Who it's for:** Payroll consultants in Belgian SME payroll teams; the question comes from their customers.
- **Value proposition:** Every figure exact, every cause tied to the rule behind it, drafted in Dutch or French.
- **North-star target:** 50% of pay-change questions answered with an approved draft in under 10 minutes by 2027-06-30
- **Constraints:** Dutch, French and German · fake data only
"""
SCOPE = """- **THE core feature (the one thing):** The agent finds why an employee's net pay changed and drafts the reply.
- **In scope (now):** a screen where the consultant sees the draft and approves or edits it
- **Deferred (out for now + the trigger that would bring it in):**
  - Replies in German - when a pilot client works in a German-speaking area
  - The signed-in user from the company login in the header - when SSO is connected
- **Non-goals (deliberately never building):** sending the reply automatically
- **Table stakes (the list `next` prints, one line each: `<item>: in now` · `<item>: deferred - when <trigger>`):**
  - the languages its users need: in now - Dutch and French, with German deferred - until a German-speaking client
  - what happens when the AI is wrong or unsure: in now - an amount it cannot explain is shown as unexplained, never guessed
  - password reset: deferred - when the company login is connected
"""
ARCH = """- **Stack + tools (and why, 2026 OSS-first):** one Python modular monolith, server-rendered pages.
  - Web: FastAPI with Jinja + HTMX pages (the consultant's screen is a list, a draft and two buttons) — default taken, not user-chosen
"""
EU_ARCH = ARCH + "  - Hosting: a managed EU host only (GDPR) — user-chosen\n"
SHOPIFY_ARCH = ARCH + "  - The owner's screens: an embedded app inside the Shopify admin, drawn with Polaris web components\n"
TOKENS = """@font-face { font-family: "Source Serif 4"; src: url("fonts/source-serif-4.woff2") format("woff2"); }
:root {
  --background: oklch(0.985 0.002 247);   --foreground: oklch(0.21 0.02 255);
  --card: oklch(1 0 0);                   --card-foreground: oklch(0.21 0.02 255);
  --primary: oklch(0.45 0.11 245);        --primary-foreground: oklch(0.985 0 0);
  --muted: oklch(0.955 0.006 247);        --muted-foreground: oklch(0.47 0.02 255);
  --border: oklch(0.90 0.006 247);  --ring: oklch(0.55 0.11 245);  --radius: 0.5rem;
  --text-sm: 0.875rem; --text-base: 1rem; --text-2xl: 1.5rem;
}
.dark {
  --background: oklch(0.17 0.01 255);     --foreground: oklch(0.96 0.005 247);
  --card: oklch(0.21 0.012 255);          --card-foreground: oklch(0.96 0.005 247);
  --primary: oklch(0.72 0.11 245);        --primary-foreground: oklch(0.17 0.01 255);
  --muted: oklch(0.27 0.012 255);         --muted-foreground: oklch(0.74 0.015 250);
  --border: oklch(0.32 0.012 255);  --ring: oklch(0.65 0.11 245);
}
@media (prefers-color-scheme: dark) { :root:not(.light) { --background: oklch(0.17 0.01 255); --foreground: oklch(0.96 0.005 247); } }
"""
IN_SHORT = """## 0. In short
Consultants check one drafted answer at a time, on a laptop, for hours a day: the screen puts the cause, its amount
and its rule side by side and keeps approve and edit in reach. Dutch and French, switched in the page; fonts served
from the app itself. Screenshots: `docs/design/shots/`.

**Principles**, each traced to the line it comes from:
1. Exact before friendly: amounts and rules first (#Vision: "Every figure exact")
2. The consultant decides: approve and edit lead (#Vision: "approved draft")
3. Evidence beside every figure: the rule on the same row (#Vision: "every cause tied to the rule behind it")
4. Unsure is shown, never guessed: an unexplained amount is marked (#Scope: "shown as unexplained, never guessed")

"""
SECTIONS = {
    1: "- **Principles (from Step 1):** Exact before friendly · The consultant decides · Evidence beside every figure\n"
       "- **Reference brands:** Linear",
    2: "- **Brand decision:** cool neutral + ONE blue accent; a manual toggle can override the OS.\n"
       "- **Stylesheet the app loads:** "
       "`app/web/static/css/tokens.css`\n\n```css\n" + TOKENS + "```",
    3: "- **Fonts:** Source Serif 4 (self-hosted) · IBM Plex Sans · **Base body size:** 16px · **Scale ratio:** 1.2",
    4: "- **Source:** Jinja macros skinned with the tokens; buttons 44px tall.",
    5: "- **Pattern:** top bar + one reading column.\n- **Pages this app needs:** question queue · one question · "
       "activity log · settings · sign-in",
    6: "- **Ladder:** base → `--shadow-sm` → `--shadow-lg`.",
    7: "- **Motion tier:** Tier 0 CSS.",
    8: "- **Do:** lead with the question. **Don't:** no KPI cards on the question page.",
    9: "- **Approach:** mobile-first; breakpoints mobile <640 · tablet 640–1024 · desktop >=1024.",
}
TITLES = {1: "Visual Theme", 2: "Color & Roles", 3: "Typography", 4: "Components", 5: "Layout",
          6: "Depth & Elevation", 7: "Motion", 8: "Do's & Don'ts", 9: "Responsive & Agent Guide"}
SAMPLE = ("<!doctype html><html lang='nl'><head><meta name='viewport' content='width=device-width'>"
          "<link rel='stylesheet' href='../../app/web/static/css/tokens.css'></head><body><main>"
          "<p>Illustrative figures — not the product's rules.</p>"
          "<nav data-lang-switch><button lang='nl'>NL</button><button lang='fr'>FR</button></nav>"
          "<h1>Waarom daalde het nettoloon in maart?</h1><p lang='fr'>Pourquoi le salaire net a-t-il baissé en mars ?</p>"
          "<button>Antwoord goedkeuren</button><p>Minder betaalde uren: − € 61,40</p>"
          "<p data-must=\"unsure\">Onverklaard: € 0,42 - niet geraden</p>"
          "<p data-must=\"not-sent\">Er wordt niets verstuurd: u verstuurt het goedgekeurde antwoord.</p>"
          "<section data-state=\"empty\"><p>Geen vragen die op u wachten.</p></section>"
          "<section data-state=\"loading\" aria-busy=\"true\"><p>De loonstroken worden gelezen…</p></section>"
          "<section data-state=\"error\" role=\"alert\"><p>De loongegevens van maart ontbreken.</p></section>"
          "</main></body></html>")
RENDER_LINE = ("  - `evidence: python C:/pb/commands/frontend-audit/render_check.py docs/design/sample.html --main "
               "\"Antwoord goedkeuren\" --shots docs/design/shots → render_check: PASS · 2026-10-03`")
SECTION = """- **Has user-facing UI?** yes: the consultant's screens, server-rendered with Jinja + HTMX.
- **Design principles (4–6, derived from vision):** agreed by the owner 2026-10-03, each with its why in `DESIGN.md` §1.
  1. Exact before friendly - amounts and their rules come before tone.
  2. The consultant decides - approve and edit lead every page.
  3. Evidence beside every figure - the rule sits on the same row.
  4. Calm, not clinical - a quiet page keeps the focus on the answer.
  5. Two languages, one layout - Dutch and French share every position.
- **Archetype (aesthetic family + why it fits):** Calm Authority / Trust - payroll answers are judged on exactness. _user-chosen_
  - Own reference: "like our payroll software, but calmer - more like Linear"
  - Picker answers (the owner's): read-heavy · consultants at a desk, many hours a day · calm authority
  - Interface languages: Dutch, French · switch: yes (the owner's answer)
  - Sample for: main screen - the consultant's question page (the owner's answer)
  - Font delivery: self-hosted (`app/web/static/css/fonts/source-serif-4.woff2` + its OFL licence)
- **Foundations summary (font pairing · base body size + type scale · one accent + palette · density · depth · motion):** Source Serif 4 + IBM Plex Sans · 16px, scale 1.2 · one blue accent, light and dark · medium · Tier 0
- **Tokens:** OKLCH, AA in light and dark - see `DESIGN.md` §2 and `app/web/static/css/tokens.css`
RENDER_LINE
- **Approved sample page (path):** `docs/design/sample.html` (approved 2026-10-03) · **DESIGN.md (path):** `DESIGN.md`
""".replace("RENDER_LINE", RENDER_LINE)


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


def design_md(sections: dict[int, str] = SECTIONS, head: str = IN_SHORT) -> str:
    return "# DESIGN.md — Pay-change answers design system\n\n" + head + "\n\n".join(
        f"## {n}. {TITLES[n]}\n{body}" for n, body in sorted(sections.items()))


def project(d: Path, arch: str = ARCH, files: bool = True, scope: str = SCOPE, vision: str = VISION) -> None:
    """A /design-system project: the spine's earlier sections; with `files`, what the run wrote (the app's base
    page, the stylesheet and its font, the sample and its screenshots, DESIGN.md)."""
    for f in d.iterdir():
        shutil.rmtree(f) if f.is_dir() else f.unlink()
    code, out = run(d, "init", "--product", "Pay-change answers")
    assert code == 0, out
    run(d, "flag", "--ui", "yes")
    run(d, "flag", "--ai", "yes", "--agent", "no")
    tpl = status.tool_file("templates", "PRODUCT.md").read_text(encoding="utf-8")
    for sec, body in (("Vision", vision), ("Scope", scope), ("Architecture", arch)):
        tpl = status.replace_section(tpl, sec, body)
    (d / "PRODUCT.md").write_text(tpl, encoding="utf-8")
    if not files:
        return
    for rel, text in (("app/web/static/css/tokens.css", TOKENS), ("docs/design/sample.html", SAMPLE),
                      ("app/web/templates/base.html", "<link rel=\"stylesheet\" href=\"/static/css/tokens.css\">"),
                      ("app/web/static/css/fonts/source-serif-4.woff2", "wOF2"),
                      *((f"docs/design/shots/sample-{w}.png", "png") for w in (375, 768, 1280))):
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text(text, encoding="utf-8")
    (d / "DESIGN.md").write_text(design_md(), encoding="utf-8")


def close(d: Path, section: str = SECTION, *extra: str) -> tuple[int, str]:
    src = d.parent / "section.md"
    src.write_text(section, encoding="utf-8")
    return run(d, "set", "design-system", "filled", "--section-from", str(src), *extra)


def test_start(fails: list[str], d: Path) -> None:
    project(d, files=False)
    code, out = run(d, "next", "--phase", "design-system")
    for want, why in (("/design-system start", "the start's own heading"),
                      ("Round 1 - ONE message or form", "round 1 grouped (P37)"),
                      ("Round 2 - ONE message", "round 2 grouped"),
                      ("\"Do you have a look in mind", "the own-look question, word for word"),
                      ("\"I tried it - looks good (Recommended)\" · \"Change something\"",
                       "the confirm's two options (a merged change/save yes-no was misread)"),
                      ("The Theme Studio button", "the confirm says where the Theme Studio is (a logged owner never "
                                                  "opened it)"),
                      ("\"What is this sample for?\"", "who the sample is for (a logged run drew a customer card for "
                                                       "a jury demo)"),
                      ("the end user's main screen (Recommended)", "no demo in #Vision: the main screen recommended"),
                      ("Project folder: ", "the absolute project folder (a logged `set` ran from a subfolder)"),
                      ("\"Keep as proposed (Recommended)\"", "round 2 offers keep-as-proposed first"),
                      ("12. Conversational / AI-chat", "the 13 families named"),
                      ("## The 3-question picker", "the picker printed"),
                      ("## §Design principles", "the principles' levers printed"),
                      ("Payroll consultants in Belgian SME", "#Vision's audience"),
                      ("FastAPI with Jinja + HTMX", "#Architecture's UI line"),
                      ("render_check.py", "the rendered check's command"),
                      ("--shots", "the screenshots the rendered check saves"),
                      ("python -m pip install playwright", "what to do on NOT RUN"),
                      ("--step foundations --family <N>", "one call for the round-2 turn's reading"),
                      ("--step sample", "one call for the sample turn's reading"),
                      ("--step write", "one call for the write turn's reading"),
                      ("--remove", "the Theme Studio leaves the approved sample"),
                      ("===== PRINCIPLES.md =====", "this phase's rules inline"),
                      ("## Architecture & quality bar", "Accessibility (UI) printed"),
                      ("no UI code yet - greenfield", "the mode"),
                      ("data-state=\"empty\"", "the app states the sample shows"),
                      ("pre-filled: Dutch, French, from #Scope", "the interface languages from #Scope's CURRENT line"),
                      ("Fonts: self-hosted", "fonts self-hosted by default"),
                      ("(Recommended) - or a font service", "with no EU custody line, the owner chooses"),
                      ("(data-must=\"unsure\")", "#Scope's must-show: the unsure state"),
                      ("(data-must=\"not-sent\")", "#Scope's must-show: nothing is sent"),
                      ("Verb + Noun", "destructive actions and labels")):
        if want not in out:
            fails.append(f"start: {why} missing ({want!r})")
    # SETUP-11 (2.3 review): the start and build-loop.md gave the confirm two different texts, so the user saw
    # different wording on each tool; one string in both places
    loop = (ROOT / "commands" / "design-system" / "references" / "build-loop.md").read_text(encoding="utf-8")
    quote = re.search(r"""\*"(Open <the sample's absolute path> in your browser\..*?Export copies\s+the tokens\.)"\*""",
                      loop, re.S)
    if not quote or " ".join(quote.group(1).split()) not in " ".join(out.split()):
        fails.append("start: the sample's confirm line is not build-loop.md's line word for word (SETUP-11)")
    if "own browser at 375, 768 and 1280 px, saved in that folder as `<sample>-375.png`" not in out:
        fails.append("start: the no-renderer route names other widths or file names than render_check.py's "
                     "375/768/1280 (SETUP-6: DESIGN.md links <sample>-1280.png)")
    for unwanted, why in (("## §Step 3b", "the close's rules (they print at `set`)"),
                          ("## §Plain-language close", "the close's rules"),
                          ("## §Re-run semantics", "re-run rules on a first run"),
                          ("## §Spine resolution", "spine resolution with a spine present"),
                          ("Host:", "a host line for a product with no host"),
                          ("pre-filled: Dutch, French, German", "German: #Scope deferred it (the old #Vision line)"),
                          ("data-must=\"signed-in-user\"", "a must-show from a deferred line"),
                          ("R/build-loop.md", "a literal R/ path (a logged run's section calls failed on it)"),
                          ("Anything to change? If not:", "the merged change/save question"),
                          ("status.py rules design-system  (run it now", "a second rules call")):
        if unwanted in out:
            fails.append(f"start prints {why}")
    feature = status.design_must("- **In scope (now):**\n  - the app sends reminders automatically\n"
                                 "  - a transparent pricing page")
    if feature:
        fails.append(f"a feature that sends automatically, or 'transparent pricing', is no must-show: {feature}")
    if len(out) > 22000:
        fails.append(f"start is {len(out)} bytes - the old start + reads were ~84 KB; keep it under 22 KB")
    project(d, files=False, vision=VISION + "- **Purpose:** a demo for a bank's innovation challenge jury\n")
    code, out = run(d, "next", "--phase", "design-system")
    if "presenter view that shows how the product decides (Recommended)" not in out or "challenge jury" not in out:
        fails.append("start: a #Vision demo for a jury should recommend the presenter view, quoting the line")
    project(d, EU_ARCH, files=False)
    code, out = run(d, "next", "--phase", "design-system")
    if "DECIDED, say why:" not in out or "GDPR" not in out:
        fails.append("start: an EU-only #Architecture should make self-hosted fonts a decided default, with the line")
    project(d, SHOPIFY_ARCH)
    code, out = run(d, "next", "--phase", "design-system")
    if "Host: the UI lives inside Shopify (an admin app)" not in out or "shopify.dev" not in out:
        fails.append(f"start: a Shopify admin app should name the host and its docs: {out[-3000:]!r}")
    if "retrofit territory" not in out or "section R/" in out:
        fails.append("start with UI code: retrofit territory, with the reference's real path (never a literal `R/`)")
    run(d, "flag", "--ui", "no")
    code, out = run(d, "next", "--phase", "design-system")
    if "write NOTHING" not in out or "Round 1" in out:
        fails.append("start with UI no should say write nothing and stop - no rounds")
    tool = status.playbook_tool
    status.playbook_tool = lambda: "antigravity"
    try:
        run(d, "flag", "--ui", "yes")
        code, out = run(d, "next", "--phase", "design-system")
        f = ROOT / "tools" / "design-system-start.md"
        if "design-system-start.md" not in out or len(out) > 3500 or not f.is_file() or "Round 1" not in \
                f.read_text(encoding="utf-8"):
            fails.append(f"Antigravity: the start should go to design-system-start.md, short output ({len(out)} B)")
        f.unlink(missing_ok=True)
        code, out = run(d, "next", "--phase", "design-system", "--step", "sample", "--family", "8")
        f = ROOT / "tools" / "design-system-sample.md"
        if code != 0 or len(out) > 600 or not f.is_file() or "Build the sample page" not in f.read_text(encoding="utf-8"):
            fails.append(f"Antigravity: a --step should go to its file with a short pointer ({len(out)} B): {out}")
        f.unlink(missing_ok=True)
    finally:
        status.playbook_tool = tool


def test_steps(fails: list[str], d: Path) -> None:
    """One call per turn: a logged Cursor run made 25 `section` calls, a Claude run 7."""
    project(d, files=False)
    code, out = run(d, "next", "--phase", "design-system", "--step", "foundations")
    if code == 0 or "needs --family" not in out or "8. Calm Authority / Trust" not in out:
        fails.append(f"--step foundations with no family should be refused with the 13 listed: {out[:300]}")
    code, out = run(d, "next", "--phase", "design-system", "--step", "foundations", "--family", "Pastel Dream")
    if code == 0 or "no family" not in out:
        fails.append(f"an unknown family should be refused: {out[:300]}")
    for args, wants in ((("foundations", "8"), ("### 8. Calm Authority", "## How Step 3", "## §Concrete foundations",
                                                 "## Accents", "## A. Type", "## B. Colour", "## I. Theming")),
                        (("foundations", "calm authority"), ("### 8. Calm Authority",)),
                        (("sample", "8"), ("## §Build the sample page", "## §Confirm the sample", "## Bucket A",
                                           "## Notes", "## J. Accessibility")),
                        (("sample", "10"), ("## Bucket B",)),
                        (("write", None), ("## The skeleton", "## 0. In short", "## §Emit the token stylesheet",
                                           "## §Emit `DESIGN.md`", "### §Audit timing", "Self-check digest"))):
        cmd = ["next", "--phase", "design-system", "--step", args[0]] + (["--family", args[1]] if args[1] else [])
        code, out = run(d, *cmd)
        missing = [w for w in wants if w not in out]
        if code != 0 or missing:
            fails.append(f"--step {' '.join(a for a in args if a)}: missing {missing} (exit {code}): {out[:200]}")
        if len(out) > 29000:
            fails.append(f"--step {args[0]} prints {len(out)} characters - Claude cuts a command's output at 30,000")
    code, out = run(d, "next", "--phase", "scope", "--step", "sample")
    if code == 0:
        fails.append("--step goes with --phase design-system only")


def test_close(fails: list[str], d: Path) -> None:
    project(d)
    code, out = close(d, SECTION, "--dry-run")
    if code != 0 or "no gap" not in out or status.AUDIT_LINE in (d / "DESIGN.md").read_text(encoding="utf-8"):
        fails.append(f"--dry-run on the realistic record: no gap and nothing written: {out[:600]}")
    code, out = close(d)
    if code != 0:
        fails.append(f"the realistic record should record the first time: {out}")
    text = (d / "PRODUCT.md").read_text(encoding="utf-8")
    if "Read (file · date · verbatim quote):** none" not in text:
        fails.append("set should write the Read line when the run opened nothing beyond the start")
    if "Change anything? If not:" not in out or "Open a NEW conversation" not in out:
        fails.append(f"set should print the rest of the close and the handoff: {out}")
    if "## §Step 3b" in out:
        fails.append("set should print the close's checklist, not the whole rule sections (they are on request)")
    written = (d / "DESIGN.md").read_text(encoding="utf-8")
    if not re.search(re.escape(status.AUDIT_LINE) + r".*`audit\.py DESIGN\.md docs/design/sample\.html`: \d+ pass · "
                     r"\d+ warn · 0 fail", written):
        fails.append("set should write the audit's own counts into DESIGN.md §2 (3 of 4 logged files stated a stale "
                     "count)")
    # #34: Google's open DESIGN.md format reads a YAML front matter; the script renders it from the stylesheet
    fm = re.match(r"---\n(.*?)\n---\n", written, re.S)
    if not fm or 'name: "Pay-change answers"' not in fm.group(1) or \
            'primary: "oklch(0.45 0.11 245)"' not in fm.group(1) or "fontSize: 1rem" not in fm.group(1) or \
            "md: 0.5rem" not in fm.group(1):
        fails.append(f"set should write DESIGN.md's front matter from tokens.css (name, colors, typography, rounded): "
                     f"{written[:500]!r}")
    if RENDER.get("shots") != "docs/design/shots":
        fails.append(f"set should re-run render_check with the evidence's --shots folder, retaking the screenshots "
                     f"without the Theme Studio: {RENDER.get('shots')!r}")
    again = status.design_front_matter(d, written, status.Status.load(d / "STATUS.md"))
    if again.count("version: alpha") != 1 or again != written:
        fails.append("a second close should replace the front matter, never stack a second one")
    code, out = run(d, "next", "--phase", "design-system")
    if "--dry-run` lists them now" not in out:
        fails.append("a re-run's start should say which command lists what today's rules refuse in the old record")

    def refused(section: str, want: str, why: str, arch: str = ARCH, design: str | None = None,
                sample: str | None = None, render: tuple[int, str] = (0, "render_check: PASS"),
                drop: tuple[str, ...] = (), scope: str = SCOPE) -> None:
        project(d, arch, scope=scope)
        if design is not None:
            (d / "DESIGN.md").write_text(design, encoding="utf-8")
        if sample is not None:
            (d / "docs/design/sample.html").write_text(sample, encoding="utf-8")
        for rel in drop:
            (d / rel).unlink()
        RENDER["code"], RENDER["out"] = render
        code, out = close(d, section)
        RENDER["code"], RENDER["out"] = 0, "render_check: PASS"
        if code == 0 or want not in out:
            fails.append(f"{why}: should be refused naming {want!r}: {out[:600]}")

    def passes(section: str, why: str, arch: str = ARCH, design: str | None = None, sample: str | None = None,
               render: tuple[int, str] = (0, "render_check: PASS"), drop: tuple[str, ...] = (),
               scope: str = SCOPE) -> None:
        project(d, arch, scope=scope)
        if design is not None:
            (d / "DESIGN.md").write_text(design, encoding="utf-8")
        if sample is not None:
            (d / "docs/design/sample.html").write_text(sample, encoding="utf-8")
        for rel in drop:
            (d / rel).unlink()
        RENDER["code"], RENDER["out"] = render
        code, out = close(d, section)
        RENDER["code"], RENDER["out"] = 0, "render_check: PASS"
        if code != 0:
            fails.append(f"{why}: should record: {out[:600]}")

    # the single-fault cases test the record checks; the audit engine (~3 s a run) ran on the record above and runs
    # again on the Gemini shapes below - stubbed in between so this suite stays inside check.py's time
    real_check, real_write = status.phase_check, status.design_write_audit
    status.phase_check, status.design_write_audit = (lambda phase, base: None), (lambda *a: None)
    three = re.sub(r"(?m)^  [45]\. .*\n", "", SECTION)
    refused(three, "3 found, 4-6 wanted", "3 principles")
    seven = SECTION.replace("  5. Two", "  6. Six - x.\n  7. Seven - y.\n  5. Two")
    refused(seven, "7 found, 4-6 wanted", "7 principles")
    inline = re.sub(r"(?m)^  \d\. .*\n", "", SECTION).replace(
        "each with its why in `DESIGN.md` §1.", "Exact · Decides · Evidence · Calm · Bilingual")
    passes(inline, "five principles on one line, separated by ·")
    refused(SECTION.replace("Calm Authority / Trust", "Trustworthy Fintech Minimal"), "names none of the 13",
            "an invented family")
    passes(SECTION.replace("Calm Authority / Trust", "Other: the consultant's payroll software"),
           "`Other: <their reference>`")
    refused(SECTION.replace("  - Own reference:", "  - Look:"), "own reference is not recorded", "no own reference")
    refused(SECTION.replace("  - Picker answers", "  - Answers"), "picker answers are not recorded",
            "no picker answers")
    refused(SECTION.replace("`docs/design/sample.html` (approved", "`docs/design/gone.html` (approved"),
            "gone.html does not exist", "a sample that does not exist")
    passes(SECTION.replace("`docs/design/sample.html` (approved", "docs/design/sample.html (approved"),
           "a sample path with no backticks (a logged false refusal: 417K tokens)")
    refused(SECTION.replace("`docs/design/sample.html` (approved 2026-10-03)", "the review screen"),
            "names no page file", "a sample field with no page path")
    refused(SECTION, "no \"illustrative figures", "numbers with no label",
            sample=SAMPLE.replace("Illustrative figures — not the product's rules.", "Welcome."))
    refused(SECTION.replace(RENDER_LINE + "\n", ""), "no rendered check recorded", "no render_check line")
    refused(SECTION.replace(" --main \"Antwoord goedkeuren\"", ""), "needs the sample's path and --main",
            "a render_check line with no --main")
    fail_out = (1, "  [FAIL] 375px: the main action 'Approve' ends at 1393px, below the 812px first screen")
    refused(SECTION, "below the 812px first screen", "a sample that fails the rendered check now", render=fail_out)
    passes(SECTION + "- Override 2026-10-03: the owner keeps the long intro above the buttons (their words)\n",
           "a render failure with the user's override recorded", render=fail_out)
    passes(SECTION, "a render check that cannot run here, its 3 screenshots saved", render=(3, "NOT RUN"))
    shots = tuple(f"docs/design/shots/sample-{w}.png" for w in (375, 768, 1280))
    refused(SECTION, "fewer than 3 screenshots", "a render check that cannot run here and no screenshots",
            render=(3, "NOT RUN"), drop=shots)
    refused(SECTION, "fewer than 3 screenshots", "two screenshots", drop=shots[:1])
    not_run = SECTION.replace("→ render_check: PASS", "→ NOT RUN - Playwright is not installed")
    refused(not_run, "recorded as NOT RUN", "a NOT RUN render check (2 of 4 logged runs)")
    passes(not_run + "- Override 2026-10-03: the owner checks it on their own phone (their words)\n",
           "NOT RUN with the owner's override and reason")
    browser = SECTION.replace(RENDER_LINE, "  - evidence: screenshots docs/design/shots (the tool's own browser, 375 · "
                                           "768 · 1440) · 2026-10-03")
    passes(browser, "the tool's own browser with its 3 screenshots")
    refused(browser, "fewer than 3 screenshots", "the tool's own browser with no screenshots", drop=shots)
    refused(SECTION, "inside Shopify (an admin app)", "a Shopify admin app with no Shopify design link",
            arch=SHOPIFY_ARCH)
    refused(SECTION + "- Polaris: https://shopify.dev\n", "inside Shopify (an admin app)",
            "a host linked by its homepage only", arch=SHOPIFY_ARCH)
    passes(SECTION + "- Host rules: https://shopify.dev/docs/api/app-home/polaris-web-components\n",
           "a deep link on the host's docs", arch=SHOPIFY_ARCH)
    passes(SECTION + "- Host platform: none - the merchant screens moved to our own web app (owner, 2026-10-03)\n",
           "`Host platform: none - <why>`", arch=SHOPIFY_ARCH)
    nine = dict(SECTIONS)
    nine.pop(9)
    refused(SECTION, "no section 9", "DESIGN.md without §9", design=design_md(nine))
    held = dict(SECTIONS)
    held[1] = held[1].replace("Linear", "<only products the owner named, else delete this line>")
    refused(SECTION, "template placeholders: <only products", "a template placeholder left",
            design=design_md(held))
    inv = dict(SECTIONS)
    inv[5] = "- **Pattern:** top bar + one reading column."
    refused(SECTION, "§5 has no page inventory", "§5 without the page inventory", design=design_md(inv))
    css = dict(SECTIONS)
    css[2] = css[2].replace("- **Stylesheet the app loads:** `app/web/static/css/tokens.css`\n", "")
    refused(SECTION, "§2 names no stylesheet path", "§2 without the stylesheet path", design=design_md(css))
    refused(SECTION.replace("16px, scale 1.2", "base $\\geq 16$px"), "LaTeX", "LaTeX in #Design")
    refused(SECTION.replace("yes: the consultant's screens", "no: an API only"), "has no UI", "#Design says no UI")
    refused(SECTION.replace("Source Serif 4 + IBM Plex Sans · 16px, scale 1.2 · one blue accent, light and dark · "
                            "medium · Tier 0", ""), "`Foundations summary` is empty", "an empty field")
    # app states: the sample shows the main screen empty, loading and with an error
    refused(SECTION, "no loading state", "a sample with no loading state",
            sample=SAMPLE.replace('data-state=\"loading\"', 'class=\"busy\"'))
    refused(SECTION, "no empty, loading or error state", "a happy-path-only sample",
            sample=re.sub(r"<section data-state.*?</section>", "", SAMPLE))
    passes(SECTION + "- App states: loading not shown - the draft is ready when the page opens\n",
           "`App states: <which> not shown - <why>`", sample=SAMPLE.replace('data-state=\"loading\"', 'class=\"busy\"'))
    # next.68: the Theme Studio leaves the approved sample (its button covered phone controls in 4 of 4 logged runs)
    refused(SECTION, "still holds the Theme Studio", "a sample that still holds the Theme Studio",
            sample=SAMPLE.replace("</body>", "<!-- ===== THEME STUDIO (dev-only) ===== --><button class='ts-open'>"
                                             "Theme Studio</button><!-- ===== /THEME STUDIO ===== --></body>"))
    # next.68: what #Scope asks the screen to show (2 of 4 logged samples showed the unexplained amount)
    refused(SECTION, "data-must=\"unsure\"", "the unexplained amount not marked",
            sample=SAMPLE.replace(' data-must=\"unsure\"', ""))
    passes(SECTION + "- Must-show: unsure not shown - the sample case explains every cent (owner, 2026-10-03)\n",
           "`Must-show: <id> not shown - <why>`", sample=SAMPLE.replace(' data-must=\"unsure\"', ""))
    # next.68: the interface language(s) the owner chose (a logged sample came out in German; 0 of 4 switched)
    refused(SECTION.replace("  - Interface languages: Dutch, French · switch: yes (the owner's answer)\n", ""),
            "interface language(s) are not recorded", "no Interface languages line")
    refused(SECTION, "is in `de`", "a German sample for a Dutch + French interface",
            sample=SAMPLE.replace("<html lang='nl'>", "<html lang='de'>"))
    refused(SECTION, "has no French", "a switching interface with no French in the sample (a dead toggle)",
            sample=SAMPLE.replace(" lang='fr'", ""))
    passes(SECTION.replace("switch: yes", "switch: no"), "Dutch + French without a switch: one language shown",
           sample=SAMPLE.replace(" lang='fr'", ""))
    refused(SECTION.replace(" · switch: yes (the owner's answer)", ""), "whether the user switches",
            "two languages, the switch not recorded")
    english = SAMPLE.replace("<html lang='nl'>", "<html lang='en'>")
    passes(SECTION.replace("Interface languages: Dutch, French · switch: yes", "Interface languages: English · "
                                                                              "switch: no"),
           "an English interface the owner chose", sample=english)
    # next.68: fonts self-hosted unless the owner chose a service (4 of 4 logged samples loaded Google Fonts)
    google = SAMPLE.replace("</head>", "<link href='https://fonts.googleapis.com/css2?family=IBM+Plex+Sans' "
                                       "rel='stylesheet'></head>")
    refused(SECTION, "fonts.googleapis.com", "a sample loading Google Fonts", sample=google)
    project(d)
    (d / "app/web/templates/base.html").write_text("<link href='https://fonts.googleapis.com/css2?family=Inter' "
                                                    "rel='stylesheet'><link rel=\"stylesheet\" "
                                                    "href=\"/static/css/tokens.css\">", encoding="utf-8")
    code, out = close(d)
    if code == 0 or "app/web/templates/base.html → fonts.googleapis.com" not in out:
        fails.append(f"the app's base template loading Google Fonts should be refused: {out[:500]}")
    passes(SECTION.replace("Font delivery: self-hosted (`app/web/static/css/fonts/source-serif-4.woff2` + its OFL "
                           "licence)", "Font delivery: Google Fonts - owner chose: \"fine for the pilot, fake data\""),
           "a font service the owner chose, in their words", sample=google)
    refused(SECTION.replace("  - Font delivery: self-hosted (`app/web/static/css/fonts/source-serif-4.woff2` + its "
                            "OFL licence)\n", ""), "how the fonts load is not recorded", "no Font delivery line")
    refused(SECTION, "not in the project: app/web/static/css/tokens.css: fonts/source-serif-4.woff2",
            "a self-hosted font file that is not there", drop=("app/web/static/css/fonts/source-serif-4.woff2",))
    # next.68: DESIGN.md opens for a reader, names no brand the owner did not, and states no hand-typed count
    refused(SECTION, "does not open for a reader", "DESIGN.md with no In short section", design=design_md(head=""))
    refused(SECTION.replace("\"like our payroll software, but calmer - more like Linear\"",
                            "\"No specific product. Calm and professional.\""), "Reference brands (Linear)",
            "Reference brands against the owner's 'no specific product' (4 of 4 logged runs)")
    counted = dict(SECTIONS)
    counted[2] = counted[2].replace("cool neutral", "audit: 50 pass, cool neutral")
    refused(SECTION, "audit count by hand (\"50 pass\")", "a hand-typed audit count (3 of 4 logged runs)",
            design=design_md(counted))
    # #37: who the sample is for (a logged run drew one customer card for a product shown to a jury)
    refused(SECTION.replace("  - Sample for: main screen - the consultant's question page (the owner's answer)\n", ""),
            "who the sample is for is not recorded", "no Sample for line")
    presenter = SECTION.replace("Sample for: main screen", "Sample for: presenter")
    refused(presenter, "data-view=\"end-user\"", "a presenter view with no end user's screen in it")
    passes(presenter, "a presenter view with the end user's screen in its frame",
           sample=SAMPLE.replace("<main>", "<main><div data-view=\"end-user\" class=\"phone-frame\">")
           .replace("</main>", "</div></main>"))
    # #37 (a logged run): #Scope has the accessibility baseline in now -> DESIGN.md has its own section
    a11y_scope = SCOPE + "  - accessibility baseline: in now - WCAG 2.2 AA, keyboard and screen reader\n"
    refused(SECTION, "no `## 10. Accessibility`", "the accessibility baseline in now, no section", scope=a11y_scope)
    passes(SECTION, "the accessibility baseline in now, with its section", scope=a11y_scope,
           design=design_md() + "\n\n## 10. Accessibility\n- **Target:** WCAG 2.2 AA\n")
    passes(SECTION, "the accessibility baseline deferred: no section needed",
           scope=SCOPE + "  - accessibility baseline: deferred - when the pilot ends\n")
    status.phase_check, status.design_write_audit = real_check, real_write
    # the logged Gemini shapes, together: one refusal, every fault named (the real audit runs: D2 is in it)
    gemini = three.replace("  - Own reference:", "  - Look:").replace("  - Picker answers", "  - Answers") \
        .replace(RENDER_LINE + "\n", "")
    project(d, SHOPIFY_ARCH)
    (d / "app/web/templates/base.html").unlink()
    code, out = close(d, gemini)
    want = ("3 found", "own reference is not recorded", "picker answers are not recorded", "no rendered check",
            "inside Shopify", "imported by no app file")
    missing = [w for w in want if w not in out]
    if code == 0 or missing or out.count("REFUSED") != 1:
        fails.append(f"the logged Gemini shapes should be refused once naming all {len(want)}; missing {missing}: "
                     f"{out[:900]}")


def test_register_folders(fails: list[str], d: Path) -> None:
    """The folders /design-system made get their tree line in STRUCTURE.md (a logged run was refused by /structure's
    check at `set` and edited STRUCTURE.md by hand: 4 calls)."""
    d = d / "reg"
    d.mkdir()
    (d / "STRUCTURE.md").write_text("# Structure\n\n```\n.\n├── app/\n│   └── web/\n└── docs/\n```\n\n## Modules\n",
                                    encoding="utf-8")
    for rel in ("docs/design/shots", "app/web/static/fonts"):
        (d / rel).mkdir(parents=True)
    added = status.design_register_folders(d, [d / "docs/design/shots", d / "app/web/static/fonts"])
    text = (d / "STRUCTURE.md").read_text(encoding="utf-8")
    import importlib.util  # loaded by path: an import would leave templates/__pycache__, which the installer refuses
    spec = importlib.util.spec_from_file_location("check_structure", ROOT / "templates" / "check_structure.py")
    check_structure = importlib.util.module_from_spec(spec)
    dont, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(check_structure)
    finally:
        sys.dont_write_bytecode = dont
    drawn = check_structure.drawn_folders(str(d / "STRUCTURE.md"))
    if added != ["docs/design", "docs/design/shots", "app/web/static", "app/web/static/fonts"] or \
            not {"design", "shots", "static", "fonts"} <= drawn or "## Modules" not in text:
        fails.append(f"set should draw the folders it made in STRUCTURE.md's tree: {added} {sorted(drawn)}\n{text}")
    if status.design_register_folders(d, [d / "docs/design/shots"]):
        fails.append("a folder already drawn should not be added twice")


def test_recheck_retakes_shots(fails: list[str], d: Path) -> None:
    """`set`'s re-run of render_check passes the evidence's --shots folder: the screenshots are retaken after the
    Theme Studio left the page (a logged run kept screenshots with its button over the phone controls)."""
    (d / "s.html").write_text(SAMPLE, encoding="utf-8")
    seen: list[list[str]] = []
    real_run = status.subprocess.run

    class Done:
        returncode, stdout, stderr = 0, "render_check: PASS", ""
    status.subprocess.run = lambda cmd, **kw: seen.append(list(cmd)) or Done()
    try:
        REAL_RECHECK(d, "s.html", "Antwoord goedkeuren", "docs/design/shots")
    finally:
        status.subprocess.run = real_run
    if not seen or seen[0][-2:] != ["--shots", "docs/design/shots"]:
        fails.append(f"render_recheck should pass --shots <the evidence's folder> to render_check.py: {seen}")


def test_anti_patterns(fails: list[str], d: Path) -> None:
    """#37: the generic-AI tells the audit engine can see, each a WARN (never a refusal)."""
    engine = status.tool_file("frontend-audit", "audit.py")
    page = d / "ap.html"
    for name, html in (("AP1-emoji-icon", "<button>\U0001F680 Launch</button>"),
                       ("AP2-pure-black", "<style>body{background:#000}</style>"),
                       ("AP3-purple-gradient", "<style>.h{background:linear-gradient(90deg,oklch(0.6 0.2 270),"
                                               "oklch(0.6 0.2 300))}</style>")):
        page.write_text("<!doctype html><html lang='en'><head><meta name='viewport' content='width=device-width'>"
                        f"</head><body><main><h1>Plan</h1>{html}</main></body></html>", encoding="utf-8")
        out = subprocess.run([sys.executable, str(engine), str(page)], capture_output=True, text=True,
                             encoding="utf-8", errors="replace").stdout
        if f"[WARN] {name}" not in out and not re.search(rf"WARN.*{name}", out):
            fails.append(f"audit.py should warn {name}: {out[-400:]}")
    page.write_text("<!doctype html><html lang='en'><head><meta name='viewport' content='width=device-width'></head>"
                    "<body><main><h1>Plan</h1><button>Approve reply</button><style>.h{background:linear-gradient("
                    "oklch(0.6 0.1 200),oklch(0.7 0.1 210))}</style></main></body></html>", encoding="utf-8")
    out = subprocess.run([sys.executable, str(engine), str(page)], capture_output=True, text=True, encoding="utf-8",
                         errors="replace").stdout
    if "AP1" in out or "AP2" in out or "AP3" in out:
        fails.append(f"a clean page should raise no anti-pattern warning: {out[-400:]}")


def test_presets_pass_the_audit(fails: list[str], d: Path) -> None:
    """palettes.md's status colours on each base, light and dark, through the playbook's own audit: the shared values
    failed it 11 times in a logged run (a 1.65M-token fix loop)."""
    pal = status.design_ref("palettes.md").read_text(encoding="utf-8")
    line = re.search(r"\*\*Semantic status.*?(?=\n- \*\*|\n## |\Z)", pal, re.S).group(0)
    light, dark = re.split(r"\s—\sdark:", line, maxsplit=1)
    tok = {m: dict(re.findall(r"(success|warning|destructive|info)\s+`(oklch\([^)]*\))`", s)) for m, s in
           (("light", light), ("dark", dark))}
    if any(len(v) != 4 for v in tok.values()):
        fails.append(f"palettes.md should give success, warning, destructive and info for light AND dark: {tok}")
        return
    for base in re.findall(r"(?s)/\* (COOL NEUTRAL|WARM NEUTRAL)[^*]*\*/\s*(:root\{.*?\})\s*(\.dark\{.*?\})", pal):
        name, root, darkb = base

        def card(block: str) -> str:  # shadcn's popover is the card surface in each mode
            return re.search(r"--card:\s*(oklch\([^)]*\))", block).group(1)
        css = (root[:-1] + "".join(f" --{k}:{v};" for k, v in tok["light"].items()) + f" --popover:{card(root)}; }}\n"
               + darkb[:-1] + "".join(f" --{k}:{v};" for k, v in tok["dark"].items())
               + f" --popover:{card(darkb)}; }}\n")
        f = d / f"palette-{name.split()[0].lower()}.css"
        f.write_text(css, encoding="utf-8")
        engine = status.tool_file("frontend-audit", "audit.py")
        r = subprocess.run([sys.executable, str(engine), str(f)], capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        bad = [l.strip() for l in r.stdout.splitlines() if "Law7-status" in l and "[FAIL]" in l]
        if bad:
            fails.append(f"palettes.md's status colours fail the audit on the {name} base: {bad[:3]}")


def test_scripts(fails: list[str], d: Path) -> None:
    """theme_studio.py --remove takes the studio out and keeps the page; render_check.py --shots saves 3 widths."""
    page = d / "sample.html"
    page.write_text(SAMPLE.replace("<main>", "<div id='ts_stage'><main>").replace("</main>", "</main></div>"),
                    encoding="utf-8")
    studio = str(ROOT / "commands" / "design-system" / "theme_studio.py")
    presets = [a for p in ("A|oklch(0.5 0.1 230)|oklch(0.7 0.1 230)", "B|oklch(0.5 0.1 150)|oklch(0.7 0.1 150)",
                           "C|oklch(0.5 0.1 30)|oklch(0.7 0.1 30)") for a in ("--preset", p)]
    subprocess.run([sys.executable, studio, str(page), *presets], capture_output=True)
    added = page.read_text(encoding="utf-8")
    r = subprocess.run([sys.executable, studio, str(page), "--remove"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    after = page.read_text(encoding="utf-8")
    if status.STUDIO_MARK not in added or r.returncode != 0 or status.STUDIO_MARK in after or "ts-open" in after \
            or "Antwoord goedkeuren" not in after or not after.rstrip().endswith("</html>"):
        fails.append(f"theme_studio.py --remove should take the studio out and keep the page: {r.stdout}{r.stderr}")
    try:
        import playwright  # noqa: F401
    except ImportError:
        print("SKIPPED - render_check.py --shots: no Playwright here")
        return
    shots = d / "shots"
    r = subprocess.run([sys.executable, str(ROOT / "commands" / "frontend-audit" / "render_check.py"), str(page),
                        "--main", "Antwoord goedkeuren", "--shots", str(shots)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode == 3:
        print(f"SKIPPED - render_check.py --shots could not run here ({r.stdout.strip()[:100]})")
        return
    got = sorted(p.name for p in shots.glob("*.png")) if shots.is_dir() else []
    if got != ["sample-1280.png", "sample-375.png", "sample-768.png"]:
        fails.append(f"render_check.py --shots should save one screenshot per width: {got} {r.stdout[-300:]}")


def test_findings_2026_10_11(fails: list[str], tmp: Path) -> None:
    """A logged run picked shadcn/ui + Tailwind for a stack whose #Architecture named neither, then filed the clash it
    had made as an open item - written after the save, so it sat uncommitted (as /structure's had)."""
    d = tmp / "ds-2026-10-11"
    d.mkdir()
    project(d, files=False)
    _, out = run(d, "next", "--phase", "design-system")
    if "#Architecture names no UI component source" not in out:
        fails.append("the start should say no component source is named, and add no library: " + out[:300])
    project(d, arch=ARCH + "  - UI components: shadcn/ui with Tailwind CSS — user-chosen\n", files=False)
    _, out = run(d, "next", "--phase", "design-system")
    if "Components come from the source #Architecture names (shadcn/ui)" not in out:
        fails.append("the start should name the component source #Architecture records")
    st = status.Status.load(d / "STATUS.md")
    gaps = status.architect_gaps(d, st)
    if any("component source" in g for g in gaps):
        fails.append(f"a named component source should satisfy /architect: {[g for g in gaps if 'component' in g]}")
    project(d, files=False)
    if not any("UI component source" in g for g in status.architect_gaps(d, status.Status.load(d / "STATUS.md"))):
        fails.append("/architect with UI yes and no component source should be refused")
    for c in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"], ["add", "-A"],
              ["commit", "-q", "-m", "start"]):
        subprocess.run(["git", *c], cwd=d, capture_output=True)
    st = status.Status.load(d / "STATUS.md")
    for r in st.rows["Phases"]:
        if r[0] == "design-system":
            r[1], r[2] = "filled", TODAY
    st.save(d / "STATUS.md")
    subprocess.run(["git", "commit", "-qam", "design saved"], cwd=d, capture_output=True)
    code, out = run(d, "open", "--from", "design-system", "--what", "Clash: a b", "--clears", "/architect decides")
    left = subprocess.run(["git", "status", "--porcelain"], cwd=d, capture_output=True, text=True).stdout
    if code != 0 or "saved: commit" not in out or left.strip():
        fails.append(f"an open item recorded after its phase's save should save itself: {out[-300:]!r} {left!r}")


def test_antigravity_approval_2026_10_11(fails: list[str], tmp: Path) -> None:
    """A logged Antigravity run read every step's file up front, ran the after-approval `--remove` itself, saved a
    design the owner never confirmed and cut its close's last line. On Antigravity the write step and the save wait
    for the owner's answer; every other tool is unchanged."""
    d = tmp / "ag-2026-10-11"
    d.mkdir()
    project(d)
    tools = Path(status.__file__).resolve().parent
    marker, kept = tools / status.AG_APPROVAL, None
    if marker.is_file():
        kept = marker.read_text(encoding="utf-8")
    real = status.playbook_tool
    try:
        status.playbook_tool = lambda: "claude"
        code, out = run(d, "next", "--phase", "design-system", "--step", "write")
        if code != 0 or "STOP before the write step" in out:
            fails.append(f"on Claude the write step should need no --approved: {out[:200]!r}")
        if any("not approved the sample" in g for g in status.design_record_gaps(d, status.Status.load(d / "STATUS.md"))):
            fails.append("on Claude the save should not ask for an Antigravity approval")
        if "copied whole to its last word" in status.handoff_card(status.Status.load(d / "STATUS.md")):
            fails.append("on Claude the handoff should be unchanged")
        status.playbook_tool = lambda: "antigravity"
        marker.unlink(missing_ok=True)
        code, out = run(d, "next", "--phase", "design-system", "--step", "write")
        if code == 0 or "STOP before the write step" not in out:
            fails.append(f"on Antigravity the write step should wait for the owner's confirm: {out[:200]!r}")
        if not any("not approved the sample" in g for g in status.design_record_gaps(d, status.Status.load(d / "STATUS.md"))):
            fails.append("on Antigravity the save should refuse a sample the owner never approved")
        code, out = run(d, "next", "--phase", "design-system", "--step", "write", "--approved", "Change something")
        if code == 0 or marker.is_file():
            fails.append("on Antigravity a 'Change something' answer should not open the write step")
        code, out = run(d, "next", "--phase", "design-system", "--step", "write", "--approved",
                        "I tried it - looks good (Recommended)")
        if code != 0 or "--dry-run" not in out:
            fails.append(f"after the owner's yes the write step should open and point at --dry-run: {out[:300]!r}")
        if any("not approved the sample" in g for g in status.design_record_gaps(d, status.Status.load(d / "STATUS.md"))):
            fails.append("after the owner's yes the save should not ask again")
        if "copied whole to its last word" not in status.handoff_card(status.Status.load(d / "STATUS.md")):
            fails.append("on Antigravity the handoff should say to copy the last line whole")
    finally:
        status.playbook_tool = real
        marker.unlink(missing_ok=True)
        if kept is not None:
            marker.write_text(kept, encoding="utf-8")
        for step in status.DESIGN_STEPS:
            (tools / f"design-system-{step}.md").unlink(missing_ok=True)


def main() -> int:
    fails: list[str] = []
    real = status.render_recheck
    status.render_recheck = lambda base, sample, main, shots=None: (RENDER.__setitem__("shots", shots) or
                                                                     (RENDER["code"], RENDER["out"]))
    tmp = Path(tempfile.mkdtemp())
    d = tmp / "p"
    d.mkdir()
    try:
        test_start(fails, d)
        test_steps(fails, d)
        test_close(fails, d)
        test_register_folders(fails, tmp)
        test_recheck_retakes_shots(fails, tmp)
        test_anti_patterns(fails, tmp)
        test_presets_pass_the_audit(fails, tmp)
        test_scripts(fails, tmp)
        test_findings_2026_10_11(fails, tmp)
        test_antigravity_approval_2026_10_11(fails, tmp)
    finally:
        status.render_recheck = real
        shutil.rmtree(tmp, ignore_errors=True)
    for f in fails:
        print(f"FAIL {f}")
    print("OK - /design-system start and close" if not fails else f"{len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
