"""2.4 setup group (/foundation #32, /contracts #43, /design-system #37, /frontend-audit #55, #60, #62): run by
tools/check.py (check 74). Each case is a fault a logged run or the issue named; each was shown red on the 2.3 code.

  - the audit engine: table alignment (Law 20), the caption tier (Law 3), anti-patterns AP4-AP9, form labels and page
    security warn by rule id; a clean page warns on none of them; `.frontend-audit.json` adds token pairs and skips a
    named WARN (never an ERROR), and a malformed one stops the run (exit 2)
  - the documents a person reads number every heading (#60): docs/contracts.md, docs/runbook.md and DESIGN.md
    (`## 0. In short`, so its sections 1-10 keep their numbers); their plain-English estimates only warn
  - a folder /foundation or /contracts adds is drawn in STRUCTURE.md by `set` (a run edited the map by hand 6 times)
  - a `set foundation|contracts filled --dry-run` writes nothing: it names the folders the real `set` would draw
  - a write command run from a sub-folder uses the project root's STATUS.md (a `set` from a sub-folder failed);
    so do `flag`, `bypass` and `waive` (2.4 review: they still failed)
  - the setup phases' close is short and never restates the document (#62)

    python tools/test_setup_fcd_24.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import status  # noqa: E402

AUDIT = ROOT / "commands" / "frontend-audit" / "audit.py"
STATUS = ROOT / "tools" / "status.py"
GIT = ["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false"]

BAD_PAGE = """<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width">
<style>
:root{ --background:oklch(0.98 0 0); --foreground:oklch(0.2 0.02 250); --primary:oklch(0.5 0.15 250);
  --muted-foreground:oklch(0.45 0.01 250); }
.dark{ --background:oklch(0.2 0.02 250); --foreground:oklch(0.96 0.01 250); --muted-foreground:oklch(0.75 0.02 250); }
.cta{ transition: transform 200ms cubic-bezier(0.68,-0.55,0.27,1.55); background: var(--primary);
  color: var(--muted-foreground); }
.alert{ border-left: 4px solid var(--primary); }
.prose{ max-width: 110ch; }
.intro{ font-size: 13px; }
a:focus-visible{ outline: 2px solid; }
</style></head><body><h1>Title</h1>
<div class="card"><div class="card inner">x</div></div>
<table><tr><th>Name</th><th>Amount</th></tr><tr><td>A</td><td>12,50</td></tr><tr><td>B</td><td>3,00</td></tr></table>
<table><tr><th class="text-right">Day</th><th>Who</th></tr><tr><td>Mon</td><td>A</td></tr><tr><td>Tue</td><td>B</td></tr>
</table>
<input id="q" placeholder="Search">
<a href="https://x.example" target="_blank">the x site</a>
<a href="javascript:void(0)">open the menu</a>
<div id="out"></div><script>document.getElementById("out").innerHTML = location.hash;</script>
</body></html>
"""
GOOD_PAGE = """<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width">
<style>
:root{ --background:oklch(0.98 0.004 250); --foreground:oklch(0.2 0.02 250); --primary:oklch(0.5 0.15 250);
  --primary-foreground:oklch(0.99 0.003 250); }
.dark{ --background:oklch(0.2 0.02 250); --foreground:oklch(0.96 0.01 250); }
@media (prefers-color-scheme: dark){ :root{ --background:oklch(0.2 0.02 250); --foreground:oklch(0.96 0.01 250); } }
.cta{ transition: transform 200ms cubic-bezier(0.2,0,0,1); background: var(--primary);
  color: var(--primary-foreground); }
blockquote{ border-left: 4px solid var(--primary); }
.prose{ max-width: 68ch; }
th.label{ font-size: 12px; text-transform: uppercase; }
.num{ text-align: right; font-variant-numeric: tabular-nums; }
a:focus-visible{ outline: 2px solid; }
</style></head><body><h1>Title</h1>
<div class="card"><p>x</p></div>
<table><tr><th class="label">Name</th><th class="label num">Amount</th></tr>
<tr><td>A</td><td class="num">12,50</td></tr><tr><td>B</td><td class="num">3,00</td></tr></table>
<label for="q">Search</label><input id="q">
<label>Name <input name="n"></label>
<a href="https://x.example" target="_blank" rel="noopener noreferrer">the x site</a>
</body></html>
"""
NEW_RULES = ("AP4-bounce-easing", "AP5-side-stripe", "AP6-line-length", "AP7-nested-cards", "AP8-grey-on-colour",
             "AP9-untinted-grey", "Law20-numeric-align", "Law20-header-align", "Law3-caption-tier", "Forms-label",
             "Security-blank-target", "Security-js-url", "Security-raw-html")


def audit(d: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(AUDIT), *args], cwd=d, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout + p.stderr


def test_audit(t: Path, fails: list[str]) -> None:
    d = t / "audit"
    d.mkdir()
    (d / "bad.html").write_text(BAD_PAGE, encoding="utf-8")
    (d / "good.html").write_text(GOOD_PAGE, encoding="utf-8")
    code, out = audit(d, "bad.html")
    for rule in NEW_RULES:
        if f"[{rule}]" not in out:
            fails.append(f"audit: the bad page should warn {rule}")
    if code != 0:
        fails.append(f"audit: warnings alone must not fail the run (exit {code})")
    for cat in ("table-alignment:warn", "anti-patterns:warn", "forms:warn", "security:warn"):
        if cat not in out:
            fails.append(f"audit: the roll-up should show {cat}")
    code, out = audit(d, "good.html")
    hit = [r for r in NEW_RULES if f"[{r}]" in out]
    if hit:
        fails.append(f"audit: the clean page should warn none of the new rules, got {hit}")
    # the config: an extra pair is contrast-checked; an ignored WARN is counted, never an ERROR
    (d / "own.css").write_text(":root{ --ink: oklch(0.9 0.01 250); --paper: oklch(0.95 0.01 250); }\n"
                               ".x{ color: #ff0000; transition: transform 1s cubic-bezier(0.3,1.6,0.6,1); }\n",
                               encoding="utf-8")
    code, out = audit(d, "own.css")
    if "--ink on --paper" in out:
        fails.append("audit: a pair the config does not name should not be checked")
    (d / ".frontend-audit.json").write_text(json.dumps({"pairs": [["--ink", "--paper"]],
                                                         "ignore": ["AP4", "Law14-raw-hex"]}), encoding="utf-8")
    code, out = audit(d, "own.css")
    if "--ink on --paper" not in out:
        fails.append("audit: the config's pair should be contrast-checked")
    if "[AP4-bounce-easing]" in out or "1 warn(s) skipped by its ignore list" not in out:
        fails.append("audit: the config's ignore should skip AP4 and say how many it skipped")
    if "[Law14-raw-hex]" not in out or code != 1:
        fails.append("audit: an ERROR is never skipped by the config")
    (d / ".frontend-audit.json").write_text('{"ignore": "AP4"}', encoding="utf-8")
    code, out = audit(d, "own.css")
    if code != 2 or "expected" not in out:
        fails.append(f"audit: a malformed config should stop the run with exit 2 (got {code})")


CONTRACTS_DOC = """# Contracts

## <O>Overview
Three tables keep the payslips apart per company.

```mermaid
erDiagram
  COMPANY ||--o{ PAYSLIP : has
```

## <P>Personal data
| Field | Why kept | How long | How it is deleted |
|---|---|---|---|
| name | to show the payslip | 24 months | purge job |

## <A>Owner's answers
1. Per company.
"""


def cdoc(o: str, p: str, a: str) -> str:
    return CONTRACTS_DOC.replace("<O>", o).replace("<P>", p).replace("<A>", a)


def test_documents(t: Path, fails: list[str]) -> None:
    d = t / "docs-proj"
    (d / "docs").mkdir(parents=True)
    (d / "docs" / "contracts.md").write_text(cdoc("", "", ""), encoding="utf-8")
    gaps = status.contracts_doc_gaps(d, "docs/contracts.md")
    if not any("without a number" in g for g in gaps):
        fails.append(f"contracts.md: unnumbered headings should be refused, got {gaps}")
    (d / "docs" / "contracts.md").write_text(cdoc("1. ", "2. ", "3. "), encoding="utf-8")
    gaps = status.contracts_doc_gaps(d, "docs/contracts.md")
    if gaps:
        fails.append(f"contracts.md: a numbered document with its parts should pass, got {gaps}")
    (d / "docs" / "runbook.md").write_text("# Runbook\n\n## Start it\nCopy .env.example to .env.\n", encoding="utf-8")
    if not any("without a number" in g for g in status.runbook_gaps(d, "")):
        fails.append("runbook.md: an unnumbered heading should be refused")
    (d / "docs" / "runbook.md").write_text("# Runbook\n\n## 1. Start it\nCopy .env.example to .env.\n",
                                           encoding="utf-8")
    if any("without a number" in g for g in status.runbook_gaps(d, "")):
        fails.append("runbook.md: a numbered runbook should pass the numbering check")
    trace = "".join(f"{i}. Principle {i}: why (#Vision: \"line {i}\")\n" for i in range(1, 5))
    old = f"# DESIGN.md\n\n## In short\nCalm pages.\n\n{trace}\n## 1. Visual Theme\nx\n"
    if not any("without a number" in g for g in status.design_doc_gaps(old, "")):
        fails.append("DESIGN.md: `## In short` without its number should be refused")
    new = old.replace("## In short", "## 0. In short")
    if status.design_doc_gaps(new, ""):
        fails.append(f"DESIGN.md: `## 0. In short` should open it for a reader, got {status.design_doc_gaps(new, '')}")
    # plain English warns, never refuses (#60, owner 2026-10-09)
    long = " ".join(["word"] * 40) + "."
    (d / "docs" / "contracts.md").write_text(cdoc("1. ", "2. ", "3. ").replace(
        "Three tables keep the payslips apart per company.", long), encoding="utf-8")
    if not any("over 30" in w for w in status.PHASE_WARN_23["contracts"](d, None)):
        fails.append("contracts.md: a 40-word sentence should be a plain-English warning")
    (d / "DESIGN.md").write_text(new.replace("Calm pages.", long + " Then — this · that — again."), encoding="utf-8")
    warns = status.PHASE_WARN_23["design-system"](d, None)
    if not any("DESIGN.md (In short)" in w for w in warns) or any("playbook words" in w for w in warns):
        fails.append(f"DESIGN.md: the In short part should get the prose warnings (never the #Vision traces), got {warns}")


STRUCTURE = """# Structure

## 2. Modules

```text
app/          # the product
    api/      # routes
tools/        # the project's scripts
```
"""


def git(d: Path, *args: str) -> None:
    subprocess.run([*GIT, *args], cwd=d, check=True, capture_output=True)


def test_folders(t: Path, fails: list[str]) -> None:
    d = t / "fold"
    d.mkdir()
    git(d, "init", "-q")
    (d / "STRUCTURE.md").write_text(STRUCTURE, encoding="utf-8")
    (d / "STATUS.md").write_text("# Status\n", encoding="utf-8")
    git(d, "add", "-A")
    git(d, "commit", "-q", "-m", "structure: saved")
    for rel in ("tools/frontend-audit/audit.py", "docs/contracts/payslip.md", ".venv/lib/site.py",
                "app/api/health.py"):
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text("x\n", encoding="utf-8")
    note = status.register_phase_folders(d, "foundation")
    text = (d / "STRUCTURE.md").read_text(encoding="utf-8")
    if "    frontend-audit/   # holds audit.py (added by /foundation)" not in text:
        fails.append(f"folders: tools/frontend-audit/ should be drawn under tools/ with what it holds:\n{text}")
    if "contracts/   # holds payslip.md (added by /foundation)" not in text or "docs/" not in text:
        fails.append("folders: docs/ and docs/contracts/ should be drawn")
    if ".venv" in text or text.count("api/") != 1:
        fails.append("folders: a hidden folder or one already drawn should never be drawn")
    if "drew 3 new folder(s)" not in note:
        fails.append(f"folders: set should name what it drew, got {note!r}")
    if status.register_phase_folders(d, "foundation"):
        fails.append("folders: a second set should draw nothing new")
    # 2.4 review: `--dry-run` promises nothing written, and a dry run drew the folders in STRUCTURE.md
    (d / "STATUS.md").unlink()
    subprocess.run([sys.executable, str(STATUS), "--today", "2026-10-09", "init", "--product", "Demo"], cwd=d,
                   capture_output=True, check=True)
    (d / "PRODUCT.md").write_text("# Demo\n\n## Foundation\n\nx\n", encoding="utf-8")
    git(d, "add", "-A")
    git(d, "commit", "-q", "-m", "foundation: folders drawn")
    (d / "docs" / "runbooks").mkdir(parents=True)
    (d / "docs" / "runbooks" / "boot.md").write_text("x\n", encoding="utf-8")
    before = (d / "STRUCTURE.md").read_bytes()
    p = subprocess.run([sys.executable, str(STATUS), "--today", "2026-10-09", "set", "foundation", "filled",
                        "--dry-run"], cwd=d, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if (d / "STRUCTURE.md").read_bytes() != before:
        fails.append("folders: a dry run must leave STRUCTURE.md as it was")
    if "would draw 1 new folder(s)" not in p.stdout + p.stderr or "never edit the map" not in p.stdout + p.stderr:
        fails.append(f"folders: a dry run names what the real set would draw: {(p.stdout + p.stderr)[-400:]!r}")


def test_subfolder(t: Path, fails: list[str]) -> None:
    d = t / "sub-proj"
    (d / "frontend").mkdir(parents=True)
    git(d, "init", "-q")

    def run(cwd: Path, *args: str) -> tuple[int, str]:
        p = subprocess.run([sys.executable, str(STATUS), "--today", "2026-10-09", *args], cwd=cwd,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        return p.returncode, p.stdout + p.stderr

    code, out = run(d, "init", "--product", "Demo")
    if code != 0:
        fails.append(f"subfolder: init failed: {out[:200]}")
        return
    code, out = run(d / "frontend", "open", "--from", "design-system", "--what", "fonts folder", "--clears", "later")
    held = " ".join(f.read_text(encoding="utf-8") for f in d.rglob("*.md") if "frontend" not in f.parts)
    if code != 0 or "project root" not in out or "fonts folder" not in held:
        fails.append(f"subfolder: a write command from a sub-folder should use the root's STATUS.md: {out[:300]}")
    for args, word in ((("flag", "--ui", "yes"), "UI"), (("bypass", "--from", "structure", "--gate", "architect",
                                                          "--reason", "the owner said so"), "bypassed")):
        code, out = run(d / "frontend", *args)
        if code != 0 or "project root" not in out:
            fails.append(f"subfolder: `{args[0]}` from a sub-folder should use the root's STATUS.md: {out[:300]}")
    if (d / "frontend" / "STATUS.md").exists():
        fails.append("subfolder: no second STATUS.md in the sub-folder")


def test_close(fails: list[str]) -> None:
    for phase in ("foundation", "contracts", "design-system"):
        text = status.close_steps_text(phase, "saved: commit abc1234")
        if "each block at most 2 lines" not in text or "never restate DESIGN.md, the runbook" not in text:
            fails.append(f"close: /{phase}'s close should be short and link the documents, never restate them")
    if "each block at most 2 lines" in status.close_steps_text("build", "saved: commit abc1234"):
        fails.append("close: the setup close is for the setup phases only")


def main() -> int:
    fails: list[str] = []
    t = Path(tempfile.mkdtemp(prefix="pb-setup24-"))
    try:
        for name, case in (("audit", lambda: test_audit(t, fails)), ("documents", lambda: test_documents(t, fails)),
                           ("folders", lambda: test_folders(t, fails)), ("subfolder", lambda: test_subfolder(t, fails)),
                           ("close", lambda: test_close(fails))):
            try:
                case()
            except Exception as e:  # noqa: BLE001 - a missing piece is a failure to report, not a crash
                fails.append(f"{name}: {type(e).__name__}: {e}")
    finally:
        shutil.rmtree(t, onerror=lambda f, p, e: (os.chmod(p, 0o700), f(p)))
    for f in fails:
        print(f"FAIL {f}")
    if fails:
        return 1
    print("OK - the 2.4 setup fixes behave (audit rules + config, numbered documents, folders drawn, root STATUS.md, "
          "short close)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
