#!/usr/bin/env python3
"""frontend-audit — mechanical enforcement of the /design-system universal laws.

The heart is a REAL WCAG contrast engine (OKLCH or hex -> relative luminance ->
ratio), so Law 7 is *computed*, never asserted. Plus regex checks for the other
mechanically-checkable laws. Judgment laws (archetype fit, hierarchy) are out of
scope here — this is the floor a machine can guarantee.

Usage:  python audit.py <file-or-dir> [more files...]
Exit:   non-zero if any ERROR-level law fails.
Portable: stdlib only.
"""
import sys, os, re, math, glob

# ---------- colour math ----------------------------------------------------

def _srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def luminance_from_hex(hx):
    hx = hx.lstrip('#')
    if len(hx) == 3:
        hx = ''.join(ch * 2 for ch in hx)
    r, g, b = (int(hx[i:i+2], 16) for i in (0, 2, 4))
    return 0.2126 * _srgb_to_lin(r) + 0.7152 * _srgb_to_lin(g) + 0.0722 * _srgb_to_lin(b)

def luminance_from_oklch(L, C, H):
    """OKLCH -> OKLab -> linear sRGB -> relative luminance (WCAG)."""
    h = math.radians(H)
    a, b = C * math.cos(h), C * math.sin(h)
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    R = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    G = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    B = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    R, G, B = (max(0.0, min(1.0, v)) for v in (R, G, B))
    return 0.2126 * R + 0.7152 * G + 0.0722 * B

_OKLCH_RE = re.compile(r"oklch\(\s*([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)", re.I)

def luminance(value):
    """Accept a raw token value ('oklch(...)' or '#hex') -> luminance or None."""
    m = _OKLCH_RE.search(value)
    if m:
        return luminance_from_oklch(float(m.group(1)), float(m.group(2)), float(m.group(3)))
    m = re.search(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", value)
    if m:
        return luminance_from_hex(m.group(0))
    return None

def contrast(v1, v2):
    l1, l2 = luminance(v1), luminance(v2)
    if l1 is None or l2 is None:
        return None
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)

# ---------- token + law checks ---------------------------------------------

_TOKEN_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")
# foreground token -> the surface it sits on (by shadcn naming convention)
PAIRS = [
    ("--foreground", "--background"), ("--card-foreground", "--card"),
    ("--popover-foreground", "--popover"), ("--primary-foreground", "--primary"),
    ("--secondary-foreground", "--secondary"), ("--muted-foreground", "--background"),
    ("--muted-foreground", "--card"), ("--accent-foreground", "--accent"),
    ("--destructive-foreground", "--destructive"),
]

def collect_tokens(text):
    return {k: v.strip() for k, v in _TOKEN_RE.findall(text)}

def _block(text, selector):
    """Inner text of the first `selector { ... }` block (token blocks have no nested braces)."""
    m = re.search(re.escape(selector) + r"\s*\{(.*?)\}", text, re.S)
    return m.group(1) if m else ""

def audit_text(path, text, findings):
    # Law 7 + 22 — COMPUTED contrast on every fg/surface pair, in BOTH light and dark modes.
    root = collect_tokens(_block(text, ":root")) or collect_tokens(text)
    dark_raw = _block(text, ".dark")
    modes = [("light", root)]
    if dark_raw:
        dark = dict(root); dark.update(collect_tokens(dark_raw))
        modes.append(("dark", dark))
    for mode, tokens in modes:
        for fg, bg in PAIRS:
            if fg in tokens and bg in tokens:
                ratio = contrast(tokens[fg], tokens[bg])
                if ratio is None:
                    continue
                level = "PASS" if ratio >= 4.5 else ("WARN" if ratio >= 3.0 else "ERROR")
                findings.append((level, "Law7-contrast", path,
                                 f"[{mode}] {fg} on {bg} = {ratio:.2f}:1 "
                                 f"({'AA' if ratio>=4.5 else 'AA-large only' if ratio>=3 else 'FAILS AA'})"))
    # Law 22 — single-mode warning (component code defines :root colour tokens but no .dark)
    if not path.lower().endswith(".md") and _block(text, ":root") and not dark_raw \
            and any(k in root for k in ("--background", "--foreground")):
        findings.append(("WARN", "Law22-theme", path,
                         "defines :root tokens but no .dark block - single-mode (Law 22 wants light+dark)"))

    # Markdown is documentation/spec — only its colour tokens are machine-checkable
    # (the contrast pass above). The code-pattern checks below are for component
    # code only, else a Don't-list line like "No `transition: all`" false-positives.
    if path.lower().endswith(".md"):
        return

    # T2-A: the dev-only Theme Studio block is stripped for the production build — don't audit its own
    # chrome (its colour-input hex literal, the palette-emoji entity, its small panel labels).
    text = re.sub(r"<!--[^>]*\bTHEME STUDIO\b.*?/THEME STUDIO[^>]*-->", "", text, flags=re.S | re.I)

    # Law 14 — no raw hex outside :root token declarations (component code)
    body = re.sub(r":root\s*\{.*?\}", "", text, flags=re.S)
    body = re.sub(r"\.dark\s*\{.*?\}", "", body, flags=re.S)
    # lookbehind excludes & so HTML numeric entities like the 🎨 emoji (&#127912;) aren't read as hex
    for m in re.finditer(r"(?<![\w/&])#[0-9a-fA-F]{6}\b", body):
        ctx = body[max(0, m.start()-60):m.start()]
        if "href" in ctx:
            continue
        if "theme-color" in ctx:   # T1-a: <meta theme-color> is an HTML attr — can't use a token
            findings.append(("WARN", "Law14-theme-color", path, f"theme-color {m.group(0)} OK (HTML attr) - keep it mirroring --primary"))
            continue
        findings.append(("ERROR", "Law14-raw-hex", path, f"raw hex {m.group(0)} in component code (use a token)"))

    # Law 12 — no transition: all
    for m in re.finditer(r"transition:\s*all|transition-all", text):
        findings.append(("ERROR", "Law12-transition-all", path, "transition: all (animate transform/opacity only)"))

    # Law 12 (Tier >= 1) — a heavy-motion library must ship a prefers-reduced-motion fallback (a11y)
    _heavy = re.search(r"\b(?:gsap|ScrollTrigger|@react-three|react-three|three/examples"
                       r"|framer-motion|lottie)\b|from\s+['\"]three['\"]|from\s+['\"]motion/react['\"]"
                       r"|require\(\s*['\"]three['\"]\s*\)", text)
    if _heavy and "prefers-reduced-motion" not in text:
        findings.append(("WARN", "Law12-reduced-motion", path,
                         f"heavy-motion lib ('{_heavy.group(0)}') with no prefers-reduced-motion guard "
                         "(Tier >=1 needs a static fallback)"))

    # Law 12 — transitions should not animate layout/paint properties (jank); transform/opacity only
    for m in re.finditer(r"transition(?:-property)?:\s*([^;{}]+)", text):
        props = m.group(1).lower()
        if re.search(r"\b(width|height|top|left|right|bottom|margin|padding|background|box-shadow)\b", props):
            findings.append(("WARN", "Law12-layout-anim", path,
                             f"transition targets a layout/paint property ({m.group(1).strip()[:40]}) "
                             "- animate transform/opacity instead"))

    # Law 12 — overlong durations drag (unless an intentional scroll-driven effect)
    for m in re.finditer(r"(?:transition(?:-duration)?|animation(?:-duration)?):[^;{}]*?([0-9.]+)(ms|s)\b", text):
        ms = float(m.group(1)) * (1000 if m.group(2) == "s" else 1)
        if ms > 1000:
            findings.append(("WARN", "Law12-long-duration", path,
                             f"animation duration ~{ms:.0f}ms > 1000ms - confirm it's an intentional "
                             "scroll-driven effect, not motion that drags"))

    # Law 1 — the DISPLAY/identity face must be distinctive (ERROR if generic); a generic BODY face is a WARN
    # (Inter/Roboto are fine as the body/UI face when paired with a distinctive --font-display).
    for m in re.finditer(r"--font-(sans|display)\s*:\s*([^;,]+)", text):
        role, first = m.group(1), m.group(2).strip().strip('"\'').lower()
        if first in ("inter", "roboto", "arial", "system-ui", "helvetica"):
            if role == "display":
                findings.append(("ERROR", "Law1-default-font", path, f"display/identity font is generic '{first}' - pick a distinctive face"))
            else:
                findings.append(("WARN", "Law1-default-font", path, f"body font '{first}' - OK only behind a distinctive --font-display"))

    # Law 3 — font-size below the 12px floor, in px AND rem/em (T5-3: rem/em ×16 root were slipping through)
    for m in re.finditer(r"font-size:\s*([0-9.]+)(px|rem|em)\b", text):
        px = float(m.group(1)) * (16 if m.group(2) in ("rem", "em") else 1)
        if px < 12:
            findings.append(("ERROR", "Law3-tiny-font", path, f"font-size {m.group(1)}{m.group(2)} (~{px:.0f}px) below 12px floor"))

    # Law 13 — interactive elements should define focus-visible (presence heuristic)
    if re.search(r"<(button|input|a)\b", text, re.I) and "focus-visible" not in text:
        findings.append(("WARN", "Law13-focus", path, "interactive elements but no :focus-visible found"))

    # Law 21 — responsive / mobile-first (heuristic). A real breakpoint = @media min/max-width,
    # @container, or a Tailwind responsive prefix — NOT prefers-reduced-motion / prefers-color-scheme.
    has_bp = (bool(re.search(r"@media[^{]*\b(?:min-width|max-width)\b", text))
              or "@container" in text
              or bool(re.search(r"\b(?:sm|md|lg|xl|2xl):[A-Za-z]", text))
              or "auto-fit" in text or "auto-fill" in text or "minmax(" in text or "clamp(" in text)
    multicol = (bool(re.search(r"grid-template-columns\s*:[^;]*\d{3,}px", text))
                or bool(re.search(r"grid-template-columns\s*:(?:[^;]*\b1fr\b){2,}", text)))
    if path.lower().endswith((".html", ".htm")) and "viewport" not in text:
        findings.append(("ERROR", "Law21-viewport", path, "missing <meta name=viewport> - not mobile-ready"))
    if multicol and not has_bp:
        findings.append(("ERROR", "Law21-responsive", path,
                         "multi-column/grid layout with no responsive breakpoint (@media min/max-width, @container) - desktop-only"))

# ---------- runner ---------------------------------------------------------

EXTS = (".html", ".htm", ".css", ".tsx", ".jsx", ".vue", ".svelte", ".md")

def iter_files(args):
    for a in args:
        if os.path.isdir(a):
            for ext in EXTS:
                yield from glob.glob(os.path.join(a, "**", "*" + ext), recursive=True)
        elif os.path.isfile(a):
            yield a

def main(argv):
    paths = list(iter_files(argv or ["."]))
    if not paths:
        print("frontend-audit: no files to scan"); return 0
    findings = []
    for p in paths:
        try:
            audit_text(p, open(p, encoding="utf-8", errors="ignore").read(), findings)
        except OSError:
            pass

    order = {"ERROR": 0, "WARN": 1, "PASS": 2}
    findings.sort(key=lambda f: order.get(f[0], 3))
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    passes = sum(1 for f in findings if f[0] == "PASS")

    # ASCII-only output — portable across OSes / terminals (no PYTHONUTF8 needed).
    print("=== frontend-audit " + "=" * 41)
    for level, law, path, msg in findings:
        tag = {"ERROR": "[FAIL]", "WARN": "[WARN]", "PASS": "[PASS]"}[level]
        print(f"  {tag}  [{law}]  {os.path.basename(path)} - {msg}")
    # Per-law roll-up (T5-4) so a clean run shows EVERY law was checked, not just contrast.
    LAWS = [("Law7", "contrast"), ("Law14", "no-raw-hex"), ("Law12", "motion"), ("Law1", "font"),
            ("Law3", "type-floor"), ("Law13", "focus"), ("Law21", "responsive"), ("Law22", "theming")]
    roll = []
    for tag, name in LAWS:
        cat = [f for f in findings if f[1].startswith(tag + "-")]
        e = sum(1 for f in cat if f[0] == "ERROR"); w = sum(1 for f in cat if f[0] == "WARN")
        roll.append(f"{name}:{'FAIL' if e else ('warn' if w else 'ok')}")
    print("-" * 60)
    print("  laws: " + "  ".join(roll))
    print(f"  {passes} pass | {warns} warn | {errors} error  ({len(paths)} files)")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
