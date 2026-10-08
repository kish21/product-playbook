"""render_check.py - what audit.py cannot see: the page as a browser draws it (D4).

audit.py reads CSS. A logged run's generic dashboard passed all 164 of its checks while, on a phone, the menu
filled the first screen, the page's main action sat 1,357 px down, and 61% of the text was under 14 px. This
renders the page with Playwright at 375, 768 and 1280 px and fails on:

  - the main action (--main "<its visible text>") not on the first phone screen (375 x 812)
  - navigation taking more than 30% of the first phone screen (it should collapse: Law 21)
  - text under 12 px, or more than 25% of the text under 14 px, at 375 px
  - text below WCAG AA contrast (4.5:1, 3:1 for large text), measured on the drawn colours
  - a page that scrolls sideways at any width

The Theme Studio block (dev-only) is ignored. Limits set from three logged samples: the approved ones had the
main action at 700 px, a 56 px nav and 2% small text.

Usage: python render_check.py <page.html> --main "<main action's visible text>" [--shots <folder>]
(--shots saves <page>-375.png, -768.png and -1280.png there: the screenshots a person and `set` can check)
Exit: 0 pass · 1 a failure · 3 NOT RUN (no Playwright or no browser, or a page of a host's web components that draw
nothing outside the host - record the check as not run, never passed)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

WIDTHS = (375, 768, 1280)
PHONE_H = 812
NAV_SHARE, SMALL_SHARE = 0.30, 0.25

# Drawn text: size, contrast against the composited background (shadow DOM included), outside the Theme Studio.
TEXT_JS = r"""
() => {
  const cv = document.createElement('canvas').getContext('2d', {willReadFrequently: true});
  const rgba = c => { cv.clearRect(0,0,1,1); cv.fillStyle = '#000'; cv.fillStyle = c; cv.fillRect(0,0,1,1);
    const d = cv.getImageData(0,0,1,1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const up = e => e.assignedSlot || e.parentElement || (e.getRootNode().host) || null;
  const studio = e => { for (let x = e; x; x = up(x)) if (x.classList && (x.classList.contains('ts') ||
    x.classList.contains('ts-open') || x.classList.contains('ts-scrim'))) return true; return false; };
  const bg = e => { const layers = []; for (let x = e; x; x = up(x)) { const c = rgba(getComputedStyle(x).backgroundColor);
    if (c[3] > 0) { layers.push(c); if (c[3] >= 1) break; } }
    let r = [255,255,255]; for (const c of layers.reverse()) r = r.map((v,i) => v*(1-c[3]) + c[i]*c[3]); return r; };
  const lin = v => { v /= 255; return v <= .04045 ? v/12.92 : Math.pow((v+.055)/1.055, 2.4); };
  const L = c => .2126*lin(c[0]) + .7152*lin(c[1]) + .0722*lin(c[2]);
  const out = [];
  const walk = root => root.querySelectorAll('*').forEach(el => {
    if (el.shadowRoot) walk(el.shadowRoot);
    if (['TITLE','SCRIPT','STYLE','NOSCRIPT'].includes(el.tagName) || studio(el)) return;
    for (const n of el.childNodes) if (n.nodeType === 3 && n.textContent.trim()) {
      const t = n.assignedSlot || el, cs = getComputedStyle(t), r = t.getBoundingClientRect();
      if (cs.visibility === 'hidden' || cs.display === 'none' || r.width === 0 || r.height === 0) break;
      const f = rgba(cs.color), b = bg(t), fg = f.slice(0,3).map((v,i) => v*f[3] + b[i]*(1-f[3]));
      const a = L(fg), c = L(b);
      out.push([n.textContent.trim().slice(0, 40), parseFloat(cs.fontSize), parseInt(cs.fontWeight) || 400,
                +((Math.max(a,c) + .05) / (Math.min(a,c) + .05)).toFixed(2)]);
      break;
    }
  });
  walk(document);
  return out;
}
"""
# Navigation on screen, and where the main action is, outside the Theme Studio.
LAYOUT_JS = r"""
(main) => {
  const studio = e => !!e.closest('.ts,.ts-open,.ts-scrim');
  const shown = e => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'
      && r.right > 0 && r.left < innerWidth; };
  const navs = [...document.querySelectorAll('nav,[role=navigation],aside')].filter(e => shown(e) && !studio(e))
    .map(e => { const r = e.getBoundingClientRect();
      return [e.tagName.toLowerCase(), Math.max(0, Math.min(r.bottom, innerHeight) - Math.max(r.top, 0))]; });
  const want = main.toLowerCase();
  const says = e => ((e.value || '') + ' ' + e.textContent).toLowerCase().includes(want);
  // the innermost elements that carry the text (no child carries it too), buttons and links first
  // drawn = has a size and is not hidden; it may still sit off the side of the screen (a table scrolled sideways)
  const drawn = e => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const inner = [...document.querySelectorAll('body *')].filter(e => !studio(e) && drawn(e) && says(e)
    && ![...e.children].some(says));
  const act = e => e.closest('button,a,[role=button],input,[type=submit]') || (e.tagName.includes('-') ? e : null);
  const pick = inner.map(e => act(e) || e).filter(drawn);
  const pref = pick.filter(e => e.matches('button,a,[role=button],input') || e.tagName.includes('-'));
  const hits = (pref.length ? pref : pick)
    .map(e => { const r = e.getBoundingClientRect();
      return [Math.round(r.top + scrollY), Math.round(r.height), Math.round(r.left), Math.round(r.right)]; })
    .sort((x, y) => x[0] - y[0]);
  return {navs, main: hits.length ? hits[0] : null, overflow: document.documentElement.scrollWidth
          - document.documentElement.clientWidth};
}
"""


# The page's custom elements (a tag with a hyphen) and the ones still undefined. A host's web components (Polaris from
# Shopify's CDN, <s-page> <s-button>) draw only inside their host: measured here they show no text.
CUSTOM_JS = r"""
() => { const tags = [...new Set([...document.querySelectorAll('*')].map(e => e.localName).filter(t => t.includes('-')))];
  return [tags, tags.filter(t => !customElements.get(t))]; }
"""
FEW_TEXTS = 3


class NotRun(Exception):
    pass


def launch(p):
    """The bundled Chromium, else an installed Chrome or Edge; None when there is no browser at all."""
    for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
        try:
            return p.chromium.launch(**kw)
        except Exception:  # noqa: BLE001 - the next browser, then NOT RUN
            continue
    return None


def check(page_path: Path, main: str, shots: Path | None = None) -> tuple[list[str], list[str]]:
    from playwright.sync_api import sync_playwright
    fails, notes = [], []
    with sync_playwright() as p:
        browser = launch(p)
        if browser is None:
            raise RuntimeError("no browser: `python -m playwright install chromium`")
        for width in WIDTHS:
            page = browser.new_page(viewport={"width": width, "height": PHONE_H if width == 375 else 900})
            page.goto(page_path.resolve().as_uri())
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:  # noqa: BLE001 - a page that keeps a connection open is measured as it stands
                pass
            page.wait_for_timeout(800)
            tags, undefined = page.evaluate(CUSTOM_JS)
            if undefined:  # a component script still loading: give it a moment to define its elements
                try:
                    page.wait_for_function("ts => ts.every(t => customElements.get(t))", arg=undefined, timeout=5000)
                except Exception:  # noqa: BLE001 - never defined here: measured as it stands
                    pass
            texts, lay = page.evaluate(TEXT_JS), page.evaluate(LAYOUT_JS, main)
            if width == 375 and tags and len(texts) < FEW_TEXTS:
                browser.close()
                raise NotRun(f"the page draws with web components ({' '.join(f'<{t}>' for t in tags[:4])}) that drew "
                             f"{len(texts)} text item(s) here - a host's components draw only inside the host (or with "
                             f"its script from the network). Check the page in the host")
            if shots is not None:  # the evidence a person can look at, one per width
                shots.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(shots / f"{page_path.stem}-{width}.png"), full_page=True)
            if lay["overflow"] > 0:
                fails.append(f"{width}px: the page scrolls sideways by {lay['overflow']}px")
            for text, size, weight, ratio in texts:
                large = size >= 24 or (size >= 18.66 and weight >= 700)
                if ratio < (3 if large else 4.5):
                    fails.append(f"{width}px: contrast {ratio}:1 below AA for {text!r}")
            if width == 375:
                if not texts:
                    fails.append("375px: no text drawn - a page whose components load from the network needs "
                                 "the network, or a stand-in, before it can be checked")
                tiny = [t for t in texts if t[1] < 12]
                small = [t for t in texts if t[1] < 14]
                if tiny:
                    fails.append(f"375px: {len(tiny)} text item(s) under 12px, e.g. {tiny[0][0]!r} at {tiny[0][1]}px")
                if texts and len(small) / len(texts) > SMALL_SHARE:
                    fails.append(f"375px: {len(small)} of {len(texts)} text items are under 14px "
                                 f"(budget {SMALL_SHARE:.0%})")
                for tag, h in lay["navs"]:
                    if h > NAV_SHARE * PHONE_H:
                        fails.append(f"375px: a <{tag}> takes {h:.0f}px of the {PHONE_H}px first screen "
                                     f"(budget {NAV_SHARE:.0%}) - collapse it on a phone")
                if lay["main"] is None:
                    fails.append(f"375px: no visible element with the text {main!r} - name the main action as the "
                                 f"page shows it")
                else:
                    top, height, left, right = lay["main"]
                    if top + height > PHONE_H:
                        fails.append(f"375px: the main action {main!r} ends at {top + height}px, below the "
                                     f"{PHONE_H}px first screen")
                    if left >= 375 or right <= 0:
                        fails.append(f"375px: the main action {main!r} is off the side of the screen (x = {left}px) - "
                                     f"a row or table that scrolls sideways hides it")
                notes.append(f"375px: {len(texts)} text items, {len(small)} under 14px; main action at "
                             f"{lay['main'][0] if lay['main'] else '-'}px; nav on screen "
                             f"{max((h for _, h in lay['navs']), default=0):.0f}px")
            page.close()
        browser.close()
    return fails, notes


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(prog="render_check.py")
    ap.add_argument("page")
    ap.add_argument("--main", required=True, help="the visible text of the page's main action")
    ap.add_argument("--shots", help="a folder: save one full-page screenshot per width there (<page>-<width>.png)")
    a = ap.parse_args(argv)
    path = Path(a.page)
    if not path.is_file():
        print(f"REFUSED - {path.as_posix()} not found", file=sys.stderr)
        return 1
    try:
        fails, notes = check(path, a.main, Path(a.shots) if a.shots else None)
    except ImportError:
        print("NOT RUN - Playwright is not installed (`pip install playwright`, then `python -m playwright install "
              "chromium`). Record the rendered check as not run - never as passed.")
        return 3
    except (RuntimeError, NotRun) as e:
        print(f"NOT RUN - {e}. Record the rendered check as not run - never as passed.")
        return 3
    for n in notes:
        print(f"  {n}")
    for f in fails:
        print(f"  [FAIL] {f}")
    print(f"render_check: {'PASS' if not fails else f'{len(fails)} failure(s)'} - {path.as_posix()}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
