"""Behaviour tests for commands/frontend-audit/render_check.py (run by tools/check.py, check 53d).

Three fixture pages drawn in a real browser: a good phone page passes; a page whose main action is below the first
phone screen fails on it; a page whose menu fills the first phone screen with small text fails on both. With no
Playwright or no browser the script must say NOT RUN (exit 3), never pass - then these tests are skipped, loudly.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "commands" / "frontend-audit" / "render_check.py"

HEAD = ("<!doctype html><html><head><meta name='viewport' content='width=device-width'><style>"
        "body{margin:0;font:16px/1.5 system-ui;color:#1a1a1a;background:#fff} button{font-size:16px;"
        "padding:12px 20px;background:#0b5394;color:#fff;border:0} nav a{display:block;padding:14px;color:#1a1a1a}"
        ".note{font-size:12.5px}</style></head><body>")
GOOD = HEAD + ("<nav><a href='#'>Queue</a></nav><main><h1>Reply to Sam</h1><p>The order shipped on Monday.</p>"
               "<button>Approve and send</button><p>" + "More detail. " * 40 + "</p></main></body></html>")
BURIED = HEAD + ("<main><h1>Dashboard</h1>" + "<p>" + "Numbers and charts. " * 30 + "</p>" * 1
                 + "<div style='height:1400px'></div><button>Approve and send</button></main></body></html>")
# a sample drawn with a host's web components (Polaris from Shopify's CDN) draws nothing outside the host - here a
# component with a shadow root and no slot, so its light-DOM text never shows. NOT RUN, never a FAIL.
HOST = HEAD + ("<script>for (const t of ['s-page', 's-button']) customElements.define(t, class extends HTMLElement {"
               "constructor() { super(); this.attachShadow({mode: 'open'}); } });</script>"
               "<s-page heading='Reply'><s-button>Approve and send</s-button></s-page></body></html>")
# an undefined custom element shows its children as ordinary text: that page is measured as usual
PLAIN_TAG = HEAD + "<my-card><h1>Reply</h1><button>Approve and send</button><p>Shipped Monday.</p></my-card></body></html>"
NAV_FIRST = HEAD + ("<nav>" + "".join(f"<a href='#'>Menu item {i}</a>" for i in range(10)) + "</nav><main>"
                    + "".join(f"<p class='note'>small print {i}</p>" for i in range(12))
                    + "<button>Approve and send</button></main></body></html>")


def run(page: Path) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(SCRIPT), str(page), "--main", "Approve and send"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout + p.stderr


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        pages = {}
        for name, html in (("good", GOOD), ("buried", BURIED), ("nav-first", NAV_FIRST), ("host", HOST),
                           ("plain-tag", PLAIN_TAG)):
            pages[name] = d / f"{name}.html"
            pages[name].write_text(html, encoding="utf-8")
        code, out = run(pages["good"])
        if code == 3:
            if "NOT RUN" not in out:
                fails.append(f"exit 3 without saying NOT RUN: {out}")
            print(f"SKIPPED - render_check.py could not run here ({out.strip()[:120]}); its fixtures were not drawn")
            return 1 if fails else 0
        if code != 0:
            fails.append(f"a good phone page should pass: {out}")
        code, out = run(pages["buried"])
        if code != 1 or "below the 812px first screen" not in out:
            fails.append(f"a main action 1400px down should fail: {out}")
        code, out = run(pages["nav-first"])
        if code != 1 or "collapse it on a phone" not in out or "under 14px" not in out:
            fails.append(f"a menu filling the first screen, with mostly small text, should fail on both: {out}")
        code, out = run(pages["host"])
        if code != 3 or "NOT RUN" not in out or "<s-page>" not in out:
            fails.append(f"a page of host web components that draw nothing here should be NOT RUN (exit 3), never "
                         f"a FAIL: {out}")
        code, out = run(pages["plain-tag"])
        if code != 0:
            fails.append(f"a custom tag that draws its text should be measured and pass: {out}")
    for f in fails:
        print(f"  x {f}")
    print("OK - render_check.py behaves" if not fails else f"FAIL - {len(fails)} render_check.py test(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
