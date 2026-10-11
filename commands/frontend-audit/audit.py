#!/usr/bin/env python3
"""frontend-audit — mechanical enforcement of the /design-system universal laws.

The heart is a REAL WCAG contrast engine (OKLCH or hex -> relative luminance ->
ratio), so Law 7 is *computed*, never asserted. Plus regex checks for the other
mechanically-checkable laws. Judgment laws (archetype fit, hierarchy) are out of
scope here — this is the floor a machine can guarantee.

Usage:  python audit.py <file-or-dir> [more files...]
        python audit.py --baseline <git-ref> <file-or-dir> [more...]   (only findings NEW since <git-ref>)
        python audit.py --version
Exit:   non-zero if any ERROR-level law fails (with --baseline: any NEW error; 2 if git cannot answer).
Portable: stdlib only.

A project's commit hooks and CI run a COMMITTED COPY of this file (kept at <tooling>/frontend-audit/audit.py,
wired by /foundation), because a clean clone has no plugin. The copy carries ENGINE_VERSION, and the
installed engine says on every run when that copy is older, newer or edited - see engine_copy_notes().
"""
import sys, os, re, math, glob, subprocess, ast
from collections import Counter

# The playbook release this engine shipped in. tools/check.py (check 5) holds it equal to the release,
# so a project copy can say which checks it carries.
ENGINE_VERSION = "2.1.0"

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
# A `var(--x)` REFERENCE with no fallback. `var(--x, 1rem)` is excluded on purpose: a declared
# fallback is a deliberate choice, not a defect. This is the one class the rest of the audit is
# blind to - CSS drops a declaration whose var() names an undefined token ("invalid at
# computed-value time"), so the colour silently never arrives and nothing reports it.
_VAR_REF_RE = re.compile(r"var\(\s*(--[\w-]+)\s*\)")
# foreground token -> the surface it sits on (by shadcn naming convention)
PAIRS = [
    ("--foreground", "--background"), ("--card-foreground", "--card"),
    ("--popover-foreground", "--popover"), ("--primary-foreground", "--primary"),
    ("--secondary-foreground", "--secondary"), ("--muted-foreground", "--background"),
    ("--muted-foreground", "--card"), ("--accent-foreground", "--accent"),
    ("--destructive-foreground", "--destructive"),
    # Common non-shadcn aliases — so projects that didn't adopt shadcn token names
    # still get a REAL contrast check (rather than silently passing unchecked).
    ("--text", "--background"), ("--text", "--bg"), ("--text", "--surface"),
    ("--text-muted", "--background"), ("--text-muted", "--bg"), ("--text-muted", "--surface"),
    ("--muted", "--surface"), ("--fg", "--bg"), ("--text-secondary", "--surface"),
]

# --- Law 7, the two bars ---------------------------------------------------
# WCAG has two thresholds and a status palette straddles them: 4.5:1 for text, 3:1 for a
# "meaningful graphic" (1.4.11). A status colour is the single most common place a palette drifts
# below AA - the value is picked for BRIGHTNESS so the dot reads as "amber", then reused as a label.
STATUS_ROLES = ("success", "warning", "destructive", "danger", "error", "info")
STATUS_SURFACES = ("--card", "--background", "--popover", "--muted")
# A token whose NAME marks it as a graphic (dot / indicator / fill / bar / chart) is held to 3:1;
# anything else carrying a status role is held to the 4.5:1 text bar.
_GRAPHICAL_RE = re.compile(r"-(?:dot|indicator|fill|bar|chart)(?:-[\w-]+)?$")
# Explicit opt-out: `--x: <value>;  /* decorative */` - a declaration, never an inference.
_DECORATIVE_RE = re.compile(r"(--[\w-]+)\s*:[^;]+;\s*/\*[^*]*\bdecorative\b[^*]*\*/", re.I)

def decorative_tokens(text):
    return set(_DECORATIVE_RE.findall(text))

def status_findings(path, mode, tokens, decorative, findings):
    """Law 7 - status colours against the surfaces they sit on, at the bar their ROLE implies."""
    surfaces = [s for s in STATUS_SURFACES if s in tokens]
    if not surfaces:
        return
    for name, value in sorted(tokens.items()):
        if not any(role in name for role in STATUS_ROLES):
            continue
        if name.endswith("-foreground") or name in decorative:
            continue  # -foreground is text ON the status colour - covered by PAIRS
        graphic = bool(_GRAPHICAL_RE.search(name))
        bar, kind = (3.0, "non-text 3:1") if graphic else (4.5, "text 4.5:1")
        for surf in surfaces:
            ratio = contrast(value, tokens[surf])
            if ratio is None:
                continue
            if ratio >= bar:
                findings.append(("PASS", "Law7-status", path,
                                 f"[{mode}] {name} on {surf} = {ratio:.2f}:1 (meets {kind})"))
            else:
                hint = ""
                if not graphic and ratio >= 3.0:
                    hint = (" - passes 3:1 as a graphic but fails the text bar; if this token is never "
                            "used as text, mark it `/* decorative */` or name it --...-dot")
                findings.append(("ERROR", "Law7-status", path,
                                 f"[{mode}] {name} on {surf} = {ratio:.2f}:1 - below the {kind} bar"
                                 f" for a {'graphical indicator' if graphic else 'status colour used as text'}{hint}"))

def collect_tokens(text):
    return {k: v.strip() for k, v in _TOKEN_RE.findall(text)}

def collect_var_refs(text):
    """Every `var(--x)` referenced with no fallback."""
    return set(_VAR_REF_RE.findall(text))

def _block(text, selector):
    """Inner text of the first `selector { ... }` block (token blocks have no nested braces)."""
    m = re.search(re.escape(selector) + r"\s*\{(.*?)\}", text, re.S)
    return m.group(1) if m else ""

EXTENDS = re.compile(r"""\{%-?\s*extends\s+["']([^"']+)["']""")
DOCUMENT = re.compile(r"<!doctype|<html\b|<head\b", re.I)


def has_viewport(path, text, depth=0):
    """Law 21's viewport is a property of the PAGE, not of every file: a Jinja/Django child template gets it from
    the layout it extends, and a fragment (no <html>/<head>, no extends) is inserted into a page that has one. A
    logged build got two false errors - a red check, a skipped hook, "DoD partial" - for a page whose base.html
    carried the tag. A parent that cannot be found keeps the error: unverified is not passed."""
    if "viewport" in text:
        return True
    m = EXTENDS.search(text)
    if m:
        if depth > 5:
            return False
        here = os.path.dirname(os.path.abspath(path))
        name = m.group(1).replace("/", os.sep)
        # the parent by its name, from this folder up through each ancestor, its templates/ folder and its
        # sub-folders' templates/ - a loader with several folders (app/ui/templates beside app/audit/templates)
        while True:
            cands = [os.path.join(here, name), os.path.join(here, "templates", name)]
            cands += sorted(glob.glob(os.path.join(here, "*", "templates", name)))
            for cand in cands:
                if os.path.isfile(cand):
                    with open(cand, encoding="utf-8", errors="replace") as f:
                        return has_viewport(cand, f.read(), depth + 1)
            up = os.path.dirname(here)
            if up == here:
                return False
            here = up
    return not DOCUMENT.search(text)  # a fragment is not a page

def audit_text(path, text, findings, right_classes=frozenset(), pairs=()):
    # Law 7 + 22 — COMPUTED contrast on every fg/surface pair, in BOTH light and dark modes.
    root = collect_tokens(_block(text, ":root")) or collect_tokens(text)
    dark_raw = _block(text, ".dark")
    modes = [("light", root)]
    if dark_raw:
        dark = dict(root); dark.update(collect_tokens(dark_raw))
        modes.append(("dark", dark))
    decorative = decorative_tokens(text)
    checked_any = False
    for mode, tokens in modes:
        status_findings(path, mode, tokens, decorative, findings)
        for fg, bg in [*PAIRS, *pairs]:
            if fg in tokens and bg in tokens:
                ratio = contrast(tokens[fg], tokens[bg])
                if ratio is None:
                    continue
                checked_any = True
                level = "PASS" if ratio >= 4.5 else ("WARN" if ratio >= 3.0 else "ERROR")
                findings.append((level, "Law7-contrast", path,
                                 f"[{mode}] {fg} on {bg} = {ratio:.2f}:1 "
                                 f"({'AA' if ratio>=4.5 else 'AA-large only' if ratio>=3 else 'FAILS AA'})"))
    # Honest coverage (the anti-false-pass): if colour tokens exist but NO recognized
    # foreground/surface pair was checkable, never report "contrast: ok" — say it wasn't verified.
    if not path.lower().endswith(".md") and not checked_any \
            and any(luminance(v) is not None for v in root.values()):
        findings.append(("WARN", "Law7-unverified", path,
                         "contrast NOT verified - no recognized foreground/surface token pairs found "
                         "(name tokens per shadcn --x-foreground/--x, or extend PAIRS) - do not assume it passes"))
    # Law 22 — single-mode warning (component code defines :root colour tokens but no .dark)
    if not path.lower().endswith(".md") and _block(text, ":root") and not dark_raw \
            and any(k in root for k in ("--background", "--foreground")):
        findings.append(("WARN", "Law22-theme", path,
                         "defines :root tokens but no .dark block - single-mode (Law 22 wants light+dark)"))
    # Law 22 — a .dark class block must also be reachable from the OS preference, not manual-toggle-only.
    # A prefers-color-scheme rule that swaps tokens contains a `--token:` assignment; one that only sets
    # `color-scheme:` (our common bug) does not. Heuristic, so WARN (a JS theme-provider may set .dark).
    if not path.lower().endswith(".md") and dark_raw \
            and not re.search(r"prefers-color-scheme:\s*dark.{0,500}?--[\w-]+\s*:", text, re.S):
        findings.append(("WARN", "Law22-system", path,
                         "dark tokens apply only via manual .dark toggle - no prefers-color-scheme rule "
                         "swaps the token set; confirm a theme provider sets .dark from the OS (Law 22)"))

    # Markdown is documentation/spec — only its colour tokens are machine-checkable
    # (the contrast pass above). The code-pattern checks below are for component
    # code only, else a Don't-list line like "No `transition: all`" false-positives.
    if path.lower().endswith(".md"):
        return

    # T2-A: the dev-only Theme Studio block is stripped for the production build — don't audit its own
    # chrome (its colour-input hex literal, the palette-emoji entity, its small panel labels).
    text = re.sub(r"<!--[^>]*\bTHEME STUDIO\b.*?/THEME STUDIO[^>]*-->", "", text, flags=re.S | re.I)
    anti_pattern_findings(path, text, findings)
    table_findings(path, text, findings, right_classes)
    caption_tier_findings(path, text, findings)
    form_findings(path, text, findings)
    security_findings(path, text, findings)

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
        findings.append(("ERROR", "Law14-raw-hex", path, f"raw hex {m.group(0)} in component code (use a token - and check its class exists in the built CSS)"))

    # Law 12 — no transition: all
    for m in re.finditer(r"transition:\s*all|transition-all", text):
        findings.append(("ERROR", "Law12-transition-all", path, "transition: all (animate transform/opacity only)"))

    # Law 12 (Tier >= 1) — a heavy-motion library must ship a prefers-reduced-motion fallback (a11y)
    _heavy = re.search(r"\b(?:gsap|ScrollTrigger|@react-three|react-three|three/examples"
                       r"|framer-motion|lottie)\b|from\s+['\"]three['\"]|from\s+['\"]motion/react['\"]"
                       r"|require\(\s*['\"]three['\"]\s*\)", text)
    # A valid guard is the media query OR an idiomatic reduced-motion hook (Framer `useReducedMotion`,
    # etc.) — accept both so correct Framer/React components don't false-positive.
    _guarded = ("prefers-reduced-motion" in text
                or re.search(r"\b(?:use|get)?[Pp]refers[Rr]educed[Mm]otion\b|\buseReducedMotion\b", text))
    if _heavy and not _guarded:
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
    for m in re.finditer(r"--font-(sans|body|base|display)\s*:\s*([^;,]+)", text):
        role, first = m.group(1), m.group(2).strip().strip('"\'').lower()
        if first in ("inter", "roboto", "arial", "system-ui", "helvetica"):
            if role == "display":
                findings.append(("ERROR", "Law1-default-font", path, f"display/identity font is generic '{first}' - pick a distinctive face"))
            else:
                findings.append(("WARN", "Law1-default-font", path, f"body font '{first}' - OK only behind a distinctive --font-display"))

    # Law 1 — the display face must be DISTINCT from the body face, not a width/weight variant of it
    # (e.g. "Inter Tight" over "Inter" is a near-twin, not a distinctive display). Strip family suffixes
    # and compare stems; a sans/serif pair of the same superfamily (IBM Plex Sans/Serif) is NOT flagged.
    _fv = dict(re.findall(r"--font-(sans|body|base|display)\s*:\s*([^;,]+)", text))
    _body = next((_fv[k] for k in ("sans", "body", "base") if k in _fv), None)
    if _body and "display" in _fv:
        def _stem(s):
            s = s.strip().strip('"\'').lower()
            return re.sub(r"\b(tight|condensed|expanded|extended|narrow|display|text|semicondensed|sc)\b", "", s).strip()
        s_raw, d_raw = _body.strip().strip('"\'').lower(), _fv["display"].strip().strip('"\'').lower()
        if s_raw != d_raw and _stem(s_raw) == _stem(d_raw) and _stem(d_raw):
            findings.append(("WARN", "Law1-near-twin", path,
                             f"display font '{d_raw}' is a width/weight variant of the body face '{s_raw}' "
                             "- not a distinctive display identity (Law 1)"))

    # Law 3 — font-size below the 12px floor, in px AND rem/em (T5-3: rem/em ×16 root were slipping through)
    for m in re.finditer(r"font-size:\s*([0-9.]+)(px|rem|em)\b", text):
        px = float(m.group(1)) * (16 if m.group(2) in ("rem", "em") else 1)
        if px < 12:
            findings.append(("ERROR", "Law3-tiny-font", path, f"font-size {m.group(1)}{m.group(2)} (~{px:.0f}px) below 12px floor - declare the step as a type-scale token in :root (--text-xs: 0.75rem) and use var(--text-xs), never another raw size"))

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
    if path.lower().endswith((".html", ".htm")) and not has_viewport(path, text):
        findings.append(("ERROR", "Law21-viewport", path, "missing <meta name=viewport> - not mobile-ready"))
    if multicol and not has_bp:
        findings.append(("ERROR", "Law21-responsive", path,
                         "multi-column/grid layout with no responsive breakpoint (@media min/max-width, @container) - desktop-only"))

# --- Category J - accessibility (Laws 23-26) -------------------------------
# The 22 laws covered type, colour, depth, motion, tokens, tables, responsive and theming, and NOTHING
# under assistive technology - so a page whose live total was silent to a screen reader scored 86 pass /
# 0 errors, while #Plan delegated its accessibility criterion to "frontend-audit passes with no errors".
# A check that cannot fail on what it appears to certify stops anyone from looking, which is worse than
# no check. These four are the mechanically decidable subset; everything else stays a judgment law, and
# the report says so rather than implying the category is covered.
LIVE_HINT = re.compile(r"\{[^{}]*\b(?:total|sum|count|balance|owe[sd]?|remaining|status|result)\b",
                       re.IGNORECASE)
GENERIC_NAME = re.compile(r">\s*(?:click here|here|read more|learn more|more|\.\.\.)\s*<", re.IGNORECASE)

def a11y_findings(path, text, findings):
    if not path.lower().endswith((".html", ".htm", ".tsx", ".jsx", ".vue", ".svelte")):
        return
    # Law 23 - a region whose text changes without a reload must announce itself.
    if LIVE_HINT.search(text) and "aria-live" not in text and 'role="status"' not in text:
        findings.append(("WARN", "Law23-live-region", path,
                         "a value that looks computed/updating, and no aria-live or role=status - a "
                         "sighted user sees the total change and a screen-reader user hears nothing"))
    # Law 24 - semantic elements. A clickable <div> is invisible to keyboard and AT.
    if re.search(r"<div[^>]*\bonClick\b", text) and "role=" not in text:
        findings.append(("ERROR", "Law24-semantics", path,
                         "<div onClick> with no role - not focusable, not announced, not keyboard-"
                         "operable; use <button>"))
    # Law 25 - accessible names: an icon-only control, or link text that names nothing.
    if re.search(r"<(?:button|a)\b[^>]*>\s*<(?:svg|img|i)\b", text) \
            and "aria-label" not in text and "sr-only" not in text and "visually-hidden" not in text:
        findings.append(("ERROR", "Law25-accessible-name", path,
                         "icon-only control with no aria-label / visually-hidden text - announced as "
                         "\"button\" with no indication of what it does"))
    if GENERIC_NAME.search(text):
        findings.append(("WARN", "Law25-link-text", path,
                         "link text that names nothing (\"click here\", \"read more\") - useless in a "
                         "screen reader's list-of-links view"))
    # Law 26 - heading order: a document that starts at <h2>, or skips a level.
    levels = [int(m.group(1)) for m in re.finditer(r"<h([1-6])\b", text)]
    if levels:
        if levels[0] != 1 and path.lower().endswith((".html", ".htm")):
            findings.append(("WARN", "Law26-heading-order", path,
                             f"first heading is <h{levels[0]}>, not <h1> - the page has no title in the "
                             "heading outline AT navigates by"))
        for a, b in zip(levels, levels[1:]):
            if b > a + 1:
                findings.append(("WARN", "Law26-heading-order", path,
                                 f"heading level jumps h{a} -> h{b} - the outline has a hole in it"))
                break

# The generic-AI tells a script can see (after Impeccable's deterministic rules): WARN only - each has a rare
# legitimate use, and a person decides.
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
PURE_BLACK = re.compile(r"(?i)(?:background(?:-color)?|--background|--card)\s*:\s*(?:#000(?:000)?\b|black\b|"
                        r"oklch\(\s*0%?\s+0\s+0)")
GRADIENT = re.compile(r"(?i)(?:linear|radial|conic)-gradient\(([^;{}]*)")


def anti_pattern_findings(path, text, findings):
    """AP1 emoji used as an icon in a button or link · AP2 an untinted pure-black surface · AP3 the purple-blue
    gradient (two oklch stops with hues 250-320)."""
    for m in re.finditer(r"(?is)<(button|a)\b[^>]*>(.*?)</\1>", text):
        if EMOJI.search(re.sub(r"<[^>]+>", "", m.group(2))):
            findings.append(("WARN", "AP1-emoji-icon", path,
                             "an emoji as the icon of a button or link - it renders differently on every system "
                             "and reads out as its name; use an SVG icon with aria-hidden"))
            break
    if PURE_BLACK.search(text):
        findings.append(("WARN", "AP2-pure-black", path,
                         "an untinted pure-black surface - tint it toward the palette's hue (oklch(0.15 0.01 <hue>))"))
    for m in GRADIENT.finditer(text):
        hues = [float(h) for h in re.findall(r"oklch\(\s*[\d.]+%?\s+[\d.]+\s+([\d.]+)", m.group(1))]
        if sum(250 <= h <= 320 for h in hues) >= 2:
            findings.append(("WARN", "AP3-purple-gradient", path,
                             "a purple-blue gradient - the generic AI look (Law 5: one dominant + ONE accent)"))
            break
    # AP4 bounce / elastic easing: an overshooting cubic-bezier (a y value outside 0..1) or a bounce/elastic name
    for m in re.finditer(r"cubic-bezier\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)", text):
        if not 0 <= float(m.group(2)) <= 1 or not 0 <= float(m.group(4)) <= 1:
            findings.append(("WARN", "AP4-bounce-easing", path,
                             f"{m.group(0)} overshoots - a bouncy easing reads as a toy in an app; ease-out "
                             "(cubic-bezier(0.2, 0, 0, 1)) settles without a bounce"))
            break
    else:
        if BOUNCE.search(text):
            findings.append(("WARN", "AP4-bounce-easing", path,
                             "a bounce or elastic easing - it reads as a toy in an app; use an ease-out curve"))
    # AP5 a thick coloured stripe down one side of a card, alert or list item (a quote's rule is fine)
    for sel, body in css_rules(text):
        w = re.search(r"border-(?:left|inline-start)\s*:\s*([\d.]+)(px|rem)\s+solid\s+([^;]+)", body)
        if w and float(w.group(1)) * (16 if w.group(2) == "rem" else 1) >= 3 \
                and not re.search(r"(?i)blockquote|quote", sel) and "--border" not in w.group(3):
            findings.append(("WARN", "AP5-side-stripe", path,
                             f"`{sel.strip()[:40]}` has a {w.group(1)}{w.group(2)} coloured stripe down one side - a "
                             "generic AI tell; mark the state with a dot, an icon or the card's own tint"))
            break
    # AP6 a text column wider than ~80 characters is hard to read (45-75 is the comfortable measure)
    for m in re.finditer(r"max-width\s*:\s*([\d.]+)ch\b", text):
        if float(m.group(1)) > 80:
            findings.append(("WARN", "AP6-line-length", path,
                             f"max-width: {m.group(1)}ch - lines over ~80 characters tire the eye; 60-75ch for text"))
            break
    # AP7 a card inside a card: two borders and two paddings for one group
    if path.lower().endswith((".html", ".htm", ".tsx", ".jsx", ".vue", ".svelte")) and nested_card(text):
        findings.append(("WARN", "AP7-nested-cards", path,
                         "a card inside a card - two borders and two paddings for one group; use spacing or a "
                         "divider inside the outer card"))
    # AP8 grey text on a coloured fill: the muted grey loses its contrast on the accent
    fills = r"var\(\s*--(?:primary|accent|destructive|success|warning|info)\s*\)"
    if any(re.search(rf"background(?:-color)?\s*:\s*{fills}", b) and
           re.search(r"(?<![\w-])color\s*:\s*var\(\s*--muted-foreground\s*\)", b) for _, b in css_rules(text)) or \
            re.search(r"(?s)class(?:Name)?=[\"'{][^\"'}]*\bbg-(?:primary|accent|destructive)\b[^\"'}]*"
                      r"\btext-muted-foreground\b", text):
        findings.append(("WARN", "AP8-grey-on-colour", path,
                         "muted grey text on a coloured fill - use the fill's own --*-foreground token"))
    # AP9 an untinted grey: a neutral token with no chroma at all (tint it toward the palette's hue)
    greys = sorted({k for k, v in _TOKEN_RE.findall(text) if untinted_grey(v)})  # light and dark blocks alike
    if greys:
        findings.append(("WARN", "AP9-untinted-grey", path,
                         f"{len(greys)} untinted grey token(s) ({', '.join(sorted(greys)[:3])}) - a grey with no hue "
                         "looks dead beside the accent; give it a chroma of ~0.005-0.02 at the palette's hue"))


BOUNCE = re.compile(r"(?i)\b(?:ease(?:In|Out|InOut)?(?:Bounce|Elastic|Back)|bounce\.(?:in|out)|elastic\.(?:in|out)|"
                    r"back\.out|easeOutBack|animate-bounce)\b")


def css_rules(text):
    """(selector, declarations) of every innermost CSS rule - flat enough for these heuristics, nested @media included."""
    return [(m.group(1).strip(), m.group(2)) for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", text)
            if not m.group(1).strip().startswith("@")]


def untinted_grey(value):
    """A colour with no hue that is neither white nor black: oklch(L 0 H) or a #rgb whose three channels are equal."""
    m = _OKLCH_RE.search(value)
    if m:
        return float(m.group(2)) == 0 and 0.05 < float(m.group(1).rstrip("%")) < 0.995
    m = re.fullmatch(r"\s*#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\s*", value)
    if m:
        hx = m.group(1) if len(m.group(1)) == 6 else "".join(c * 2 for c in m.group(1))
        return hx[0:2] == hx[2:4] == hx[4:6] and hx[0:2].lower() not in ("00", "ff")
    return False


_TAG_RE = re.compile(r"<(/?)([A-Za-z][\w.-]*)((?:[^>\"'{]|\"[^\"]*\"|'[^']*'|\{[^}]*\})*)>")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


def is_card(name, attrs):
    """`<Card>` (a component) or an element whose class list holds the word `card`."""
    if name == "Card":
        return True
    m = re.search(r"\bclass(?:Name)?\s*=\s*[\"'{]([^\"'}]*)", attrs)
    return bool(m and re.search(r"(?<![\w-])card(?![\w-])", m.group(1)))


def nested_card(text):
    """True when a card opens while another card is still open (a tag stack, lenient like a browser)."""
    stack = []
    for m in _TAG_RE.finditer(re.sub(r"(?s)<!--.*?-->|<(script|style)\b.*?</\1>", "", text)):
        close, name, attrs = m.group(1), m.group(2), m.group(3)
        if close:
            for i in range(len(stack) - 1, -1, -1):
                if stack[i][0] == name:
                    del stack[i:]
                    break
            continue
        if name.lower() in VOID or attrs.rstrip().endswith("/"):
            continue
        card = is_card(name, attrs)
        if card and any(c for _, c in stack):
            return True
        stack.append((name, card))
    return False


# --- Law 20 (table alignment), Law 3 (caption tier), forms and security ----
NUMERIC_CELL = re.compile(r"^[\s€$£¥+\-−(]*\d[\d.,\s  ]*%?\)?\s*(?:€|EUR|USD|GBP|kr|x)?\s*$")
RIGHT = re.compile(r"(?i)text-(?:right|end)\b|text-align\s*:\s*(?:right|end)|align\s*=\s*[\"']?right|\bnum(?:eric)?\b|"
                   r"tabular")


def cell_align(attrs, right_classes):
    """'right' when the cell is right-aligned by its own attributes, its style or a class some stylesheet aligns right."""
    if RIGHT.search(attrs):
        return "right"
    m = re.search(r"\bclass(?:Name)?\s*=\s*[\"'{]([^\"'}]*)", attrs)
    if m and set(m.group(1).split()) & right_classes:
        return "right"
    if re.search(r"(?i)text-center\b|text-align\s*:\s*center|align\s*=\s*[\"']?center", attrs):
        return "center"
    return "left"


def right_aligned_classes(texts):
    """Class names a stylesheet in the set aligns right (`.num { text-align: right }`)."""
    out = set()
    for text in texts:
        for sel, body in css_rules(text):
            if re.search(r"text-align\s*:\s*(?:right|end)", body):
                out |= set(re.findall(r"\.([\w-]+)", sel))
    return out


def table_findings(path, text, findings, right_classes):
    """Law 20: a header aligned unlike its column's cells, and a column of numbers that is not right-aligned."""
    if not path.lower().endswith((".html", ".htm", ".tsx", ".jsx", ".vue", ".svelte")):
        return
    seen = set()  # one finding per rule per file: the first table that shows it
    for table in re.findall(r"(?is)<table\b.*?</table>", text):
        head, cols = [], {}
        for row in re.findall(r"(?is)<tr\b[^>]*>(.*?)</tr>", table):
            if "colspan" in row.lower():
                continue
            cells = re.findall(r"(?is)<(th|td)\b([^>]*)>(.*?)</\1>", row)
            if cells and all(c[0].lower() == "th" for c in cells) and not head:
                head = [cell_align(a, right_classes) for _, a, _ in cells]
                continue
            for i, (_, a, inner) in enumerate(cells):
                cols.setdefault(i, []).append((cell_align(a, right_classes),
                                               re.sub(r"<[^>]+>|\{[^}]*\}", "", inner).strip()))
        for i, cells in sorted(cols.items()):
            aligns = {a for a, _ in cells}
            values = [v for _, v in cells if v]
            if len(values) >= 2 and all(NUMERIC_CELL.match(v) for v in values) and aligns != {"right"}:
                if "num" not in seen:
                    findings.append(("WARN", "Law20-numeric-align", path,
                                     f"table column {i + 1} holds numbers ({ascii(values[0][:12])} ...) but is not "
                                     "right-aligned with tabular figures - the digits do not line up"))
                seen.add("num")
            elif head and i < len(head) and len(aligns) == 1 and head[i] not in aligns and "head" not in seen:
                findings.append(("WARN", "Law20-header-align", path,
                                 f"table column {i + 1}: the header is {head[i]}-aligned over {next(iter(aligns))}-"
                                 "aligned cells - a header and its cells share one alignment"))
                seen.add("head")


CAPTION_SEL = re.compile(r"(?i)\b(?:th|caption|label|legend|kbd|code|small|sup|sub)\b|overline|eyebrow|badge|chip|tag|"
                         r"meta|caption|hint|footnote|num|tabular|mono|kicker")


def caption_tier_findings(path, text, findings):
    """Law 3: 12-13px is the caption tier - uppercase labels, overlines, table headers, numerals. Body text is >= 14."""
    for sel, body in css_rules(text):
        m = re.search(r"font-size\s*:\s*([0-9.]+)(px|rem|em)\b", body)
        if not m:
            continue
        px = float(m.group(1)) * (16 if m.group(2) in ("rem", "em") else 1)
        if 12 <= px < 14 and not CAPTION_SEL.search(sel) and "uppercase" not in body and "tabular" not in body \
                and not sel.startswith(":root"):
            findings.append(("WARN", "Law3-caption-tier", path,
                             f"`{sel[:40]}` sets {m.group(1)}{m.group(2)} (~{px:.0f}px) body text - 12-13px is the "
                             "caption tier (uppercase labels, overlines, table headers, numerals); body text >= 14px"))
            return


def form_findings(path, text, findings):
    """FORMS: an input, select or textarea no label names - a placeholder vanishes as you type and is not a label."""
    if not path.lower().endswith((".html", ".htm", ".tsx", ".jsx", ".vue", ".svelte")):
        return
    labelled = set(re.findall(r"(?:\bfor|htmlFor)\s*=\s*[\"'{]+([\w-]+)", text))
    for m in re.finditer(r"(?is)<(input|select|textarea)\b([^>]*)>", text):
        attrs = m.group(2)
        if re.search(r"(?i)type\s*=\s*[\"']?(?:hidden|submit|button|reset|image)\b", attrs) or \
                re.search(r"aria-label(?:ledby)?\s*=", attrs):
            continue
        idm = re.search(r"\bid\s*=\s*[\"'{]+([\w-]+)", attrs)
        if idm and idm.group(1) in labelled:
            continue
        before = text[:m.start()]
        if before.rfind("<label") > before.rfind("</label>"):
            continue  # wrapped in its <label>
        findings.append(("WARN", "Forms-label", path,
                         f"a <{m.group(1)}> no label names (a placeholder is not a label) - add <label for> or "
                         "aria-label"))
        return


def security_findings(path, text, findings):
    """SECURITY: what a page can do to its user - a new tab that can steer the opener, a javascript: link, raw HTML."""
    if not path.lower().endswith((".html", ".htm", ".tsx", ".jsx", ".vue", ".svelte")):
        return
    for m in re.finditer(r"(?is)<a\b([^>]*)>", text):
        if re.search(r"target\s*=\s*[\"'{]+_blank", m.group(1)) and not re.search(r"noopener|noreferrer", m.group(1)):
            findings.append(("WARN", "Security-blank-target", path,
                             "a link opens a new tab with no rel=\"noopener noreferrer\" - the new page can steer this one"))
            break
    if re.search(r"(?i)href\s*=\s*[\"'{]+\s*javascript:", text):
        findings.append(("WARN", "Security-js-url", path, "a javascript: link - use a <button> with a handler"))
    raw = re.search(r"dangerouslySetInnerHTML|\bv-html\s*=|\{@html\b|\.innerHTML\s*=(?!=)|\|\s*safe\b", text)
    if raw:
        findings.append(("WARN", "Security-raw-html", path,
                         f"raw HTML is put into the page ({raw.group(0).strip()}) - only text that is escaped or "
                         "sanitised first (a user's text here runs as script)"))


def check_token_refs(defined, refs, findings):
    """Law 14b - a referenced token that nothing defines.

    ERROR when the audited set actually defines tokens (so a missing name is provably orphaned);
    WARN "unverified" when it defines none at all - the same anti-false-pass convention Law 7 uses,
    rather than erroring on every component audited without its stylesheet.
    """
    if not refs:
        return
    if not defined:
        for path in sorted(refs):
            findings.append(("WARN", "Law14b-unverified", path,
                             f"{len(refs[path])} var(--token) references NOT verified - no token "
                             "definitions in the audited set (pass DESIGN.md or the stylesheet too)"))
        return
    for path in sorted(refs):
        missing = sorted(refs[path] - defined)
        if missing:
            findings.append(("ERROR", "Law14b-undefined", path,
                             f"references {len(missing)} token(s) nothing defines: "
                             + ", ".join(missing[:8]) + (" ..." if len(missing) > 8 else "")
                             + " - CSS drops these declarations silently (the value never arrives)"))

# ---------- runner ---------------------------------------------------------

EXTS = (".html", ".htm", ".css", ".tsx", ".jsx", ".vue", ".svelte", ".md")

def iter_files(args):
    for a in args:
        if os.path.isdir(a):
            for ext in EXTS:
                yield from glob.glob(os.path.join(a, "**", "*" + ext), recursive=True)
        elif os.path.isfile(a):
            yield a

COPY_PATHSPEC = "*frontend-audit/audit.py"
_VERSION_RE = re.compile(r'^ENGINE_VERSION = "([^"]*)"', re.MULTILINE)

def version_tuple(v):
    """'1.9.0' -> (1, 9, 0). Compared as numbers: as text, 1.9.0 sorts after 1.48.0 - which is how a real
    build once ran an engine five checks behind the installed one."""
    return tuple(int(n) for n in re.findall(r"\d+", v or "")) or (0,)

def _engine_code(text):
    """What the engine DOES, with its version line removed - two releases whose checks are identical compare
    equal, so a version bump alone never asks anyone to refresh a copy. Compared as parsed code, not text:
    a project's formatter rewrites its committed copy (split imports, quotes, spacing), and a text compare
    then called a copy with the same checks OLDER on every release. Comments, docstrings and import order
    do not count; code that does not parse falls back to the text."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _VERSION_RE.sub("", text.replace("\r\n", "\n"))
    imports, body = set(), []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "ENGINE_VERSION" for t in node.targets):
            continue
        if isinstance(node, ast.Import):
            imports |= {(a.name, a.asname) for a in node.names}
            continue
        body.append(node)
    module = ast.Module(body=body, type_ignores=[])
    for node in ast.walk(module):
        if (isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body
                and isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0].value, "value", None), str)):
            node.body = node.body[1:] or [ast.Pass()]
    return sorted(imports), ast.dump(module)

def engine_copy_notes():
    """Compare this engine with the copies committed in the current git project.

    Hooks and CI run the project's copy; Claude Code runs the installed engine. When they differ, the two
    gates check different laws, so say so. Informational: never changes the pass/warn/error counts.
    """
    here = os.path.realpath(__file__)
    git = dict(capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], **git)
        if top.returncode != 0:
            return ["engine copy: not checked - not inside a git project"]
        root = top.stdout.strip()
        listed = subprocess.run(["git", "-C", root, "ls-files", "-z", "--", COPY_PATHSPEC], **git)
    except (OSError, subprocess.SubprocessError) as exc:
        return [f"engine copy: not checked - git unavailable ({exc.__class__.__name__})"]
    # A project-level copy install commits the INSTALLED engine under .claude/ (Claude Code) or .agents/ (Cursor,
    # Antigravity) - that is a skill, not the copy the hooks and CI run, so it is never the thing being judged.
    copies = [os.path.realpath(os.path.join(root, p)) for p in listed.stdout.split("\0")
              if p and "/.claude/" not in "/" + p and "/.agents/" not in "/" + p]
    if os.path.normcase(here) in {os.path.normcase(c) for c in copies}:
        return []  # this IS the project's copy, running in a hook or CI
    if not copies:
        return ["engine copy: none committed in this project - commit hooks and CI do not run this audit "
                "(/foundation wires it for a UI product)"]
    mine = open(here, encoding="utf-8").read()
    notes = []
    for path in copies:
        rel = os.path.relpath(path, root)
        try:
            theirs = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            notes.append(f"engine copy: {rel} is listed by git but unreadable"); continue
        if _engine_code(theirs) == _engine_code(mine):
            notes.append(f"engine copy: {rel} has the same checks as this engine {ENGINE_VERSION}"); continue
        m = _VERSION_RE.search(theirs)
        v = m.group(1) if m else "unversioned"
        if version_tuple(v) < version_tuple(ENGINE_VERSION):
            notes.append(f"engine copy: {rel} is {v}, OLDER than this engine {ENGINE_VERSION} - hooks and CI "
                         f"run fewer checks. Refresh: copy {here} over it and commit.")
        elif version_tuple(v) > version_tuple(ENGINE_VERSION):
            notes.append(f"engine copy: {rel} is {v}, NEWER than this engine {ENGINE_VERSION} - update the "
                         f"product-playbook plugin, then re-run this audit.")
        else:
            notes.append(f"engine copy: {rel} says {v} but its checks differ from this engine - it was edited "
                         f"in place, so hooks and CI do not run the released checks. Refresh: copy {here} over it.")
    return notes

def scan(texts, config=None):
    """{path: text} -> findings. One function for the live tree and for its --baseline copy."""
    findings = []
    defined, refs = set(), {}
    right = right_aligned_classes(texts.values())
    pairs = tuple(tuple(x) for x in (config or {}).get("pairs", ()))
    for p, text in texts.items():
        audit_text(p, text, findings, right, pairs)
        a11y_findings(p, text, findings)
        # Law 14b is cross-file by nature: `audit.py DESIGN.md frontend/` must resolve a component's
        # tokens against the DESIGN.md in the same run, so collect across the whole file set first.
        defined |= set(collect_tokens(text))
        r = collect_var_refs(text)
        if r:
            refs[p] = r
    check_token_refs(defined, refs, findings)
    return findings

def baseline_texts(ref, paths):
    """The same files as they were at `ref`. A file new since then has no baseline, so all of it is new.
    Raises RuntimeError when git cannot answer - a baseline run never degrades to a whole-file pass."""
    def git(*args):
        return subprocess.run(["git", *args], capture_output=True)
    if git("rev-parse", "--verify", "--quiet", ref + "^{commit}").returncode != 0:
        raise RuntimeError(f"--baseline {ref}: not a commit in this git repository")
    out = {}
    for p in paths:
        rel = os.path.relpath(p).replace(os.sep, "/")
        r = git("show", f"{ref}:./{rel}")
        if r.returncode == 0:
            out[p] = r.stdout.decode("utf-8", errors="ignore")
    return out

def parse_args(argv):
    """-> (baseline ref or None, the remaining path arguments)."""
    ref, rest, i = None, [], 0
    while i < len(argv):
        a = argv[i]
        if a == "--baseline":
            if i + 1 >= len(argv):
                raise RuntimeError("--baseline needs a git ref (e.g. --baseline main)")
            ref = argv[i + 1]; i += 2; continue
        if a.startswith("--baseline="):
            ref = a.split("=", 1)[1]; i += 1; continue
        rest.append(a); i += 1
    return ref, rest

CONFIG_NAME = ".frontend-audit.json"


def load_config():
    """The project's `.frontend-audit.json`, from this folder up to the git root: {"pairs": [["--fg", "--bg"], ...]}
    adds foreground/surface token pairs to the contrast check; {"ignore": ["AP9", "Law23-live-region:src/legacy/*"]}
    skips WARN findings by rule id (or its prefix), optionally only for files matching a glob. An ERROR is never
    skipped. -> (config, its folder) or ({}, None); a file that is not that shape raises RuntimeError (exit 2)."""
    here = os.path.abspath(".")
    while True:
        f = os.path.join(here, CONFIG_NAME)
        if os.path.isfile(f):
            import json
            try:
                cfg = json.load(open(f, encoding="utf-8"))
            except ValueError as e:
                raise RuntimeError(f"{f} is not valid JSON ({e})")
            ok = isinstance(cfg, dict) and set(cfg) <= {"pairs", "ignore"} \
                and isinstance(cfg.get("pairs", []), list) and isinstance(cfg.get("ignore", []), list) \
                and all(isinstance(x, list) and len(x) == 2 and all(isinstance(t, str) and t.startswith("--") for t in x)
                        for x in cfg.get("pairs", [])) \
                and all(isinstance(x, str) and x.strip() for x in cfg.get("ignore", []))
            if not ok:
                raise RuntimeError(f"{f}: expected {{\"pairs\": [[\"--fg\", \"--bg\"]], \"ignore\": [\"<rule>\" or "
                                   f"\"<rule>:<glob>\"]}}")
            return cfg, here
        if os.path.isdir(os.path.join(here, ".git")) or os.path.dirname(here) == here:
            return {}, None
        here = os.path.dirname(here)


def ignored(finding, cfg, where):
    """True for a WARN the config's ignore list names (never an ERROR)."""
    import fnmatch
    level, law, path = finding[0], finding[1], finding[2]
    if level != "WARN":
        return False
    rel = os.path.relpath(os.path.abspath(path), where).replace(os.sep, "/") if where else path
    for item in cfg.get("ignore", []):
        rule, _, pat = item.partition(":")
        if (law == rule or law.startswith(rule + "-") or law.split("-")[0] == rule) and (
                not pat or fnmatch.fnmatch(rel, pat)):
            return True
    return False


def main(argv):
    if argv[:1] == ["--version"]:
        print(f"frontend-audit engine {ENGINE_VERSION}"); return 0
    try:
        ref, argv = parse_args(argv)
    except RuntimeError as e:
        print(f"frontend-audit: {e}"); return 2
    paths = list(iter_files(argv or ["."]))
    if not paths:
        print("frontend-audit: no files to scan"); return 0
    texts = {}
    for p in paths:
        try:
            texts[p] = open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
    try:
        cfg, where = load_config()
    except (RuntimeError, OSError) as e:
        print(f"frontend-audit: {e}"); return 2
    findings = scan(texts, cfg)
    skipped = [f for f in findings if ignored(f, cfg, where)]
    findings = [f for f in findings if f not in skipped]
    already = None
    if ref:
        # Diff-scoped: a finding counts only if the same file had fewer of it at `ref`. Matched as a multiset
        # on (level, law, file, message) - messages carry no line numbers, so an edit above a finding does not
        # make it "new", while a second copy of the same raw hex does.
        try:
            old = [f for f in scan(baseline_texts(ref, list(texts)), cfg) if not ignored(f, cfg, where)]
        except (RuntimeError, OSError) as e:
            print(f"frontend-audit: {e} - run without --baseline for the whole-file audit"); return 2
        budget = Counter(old)
        kept = []
        for f in findings:
            if budget[f] > 0:
                budget[f] -= 1
            else:
                kept.append(f)
        already = Counter(f[0] for f in findings) - Counter(f[0] for f in kept)
        findings = kept

    order = {"ERROR": 0, "WARN": 1, "PASS": 2}
    findings.sort(key=lambda f: order.get(f[0], 3))
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    passes = sum(1 for f in findings if f[0] == "PASS")

    # ASCII-only output — portable across OSes / terminals (no PYTHONUTF8 needed).
    title = f"=== frontend-audit engine {ENGINE_VERSION} "
    print(title + "=" * max(3, 60 - len(title)))
    if where:
        print(f"  config {os.path.join(where, CONFIG_NAME)}: {len(cfg.get('pairs', []))} extra token pair(s); "
              f"{len(skipped)} warn(s) skipped by its ignore list (an ERROR is never skipped)")
    if already is not None:
        print(f"  baseline {ref}: only findings NEW since then are listed and counted.")
        print(f"  already present at {ref} (not listed): {already['ERROR']} error | {already['WARN']} warn")
    for level, law, path, msg in findings:
        tag = {"ERROR": "[FAIL]", "WARN": "[WARN]", "PASS": "[PASS]"}[level]
        print(f"  {tag}  [{law}]  {os.path.basename(path)} - {msg}")
    # Per-law roll-up (T5-4) so a clean run shows EVERY law was checked, not just contrast.
    LAWS = [("Law7", "contrast"), ("Law14", "no-raw-hex"), ("Law14b", "tokens-defined"),
            ("Law12", "motion"), ("Law1", "font"),
            ("Law3", "type-floor"), ("Law13", "focus"), ("Law21", "responsive"), ("Law22", "theming"),
            ("Law23", "live-regions"), ("Law24", "semantics"), ("Law25", "accessible-names"),
            ("Law26", "heading-order"), ("Law20", "table-alignment"), ("AP", "anti-patterns"), ("Forms", "forms"),
            ("Security", "security")]
    roll = []
    for tag, name in LAWS:
        cat = [f for f in findings if re.match(r"AP\d+-" if tag == "AP" else re.escape(tag) + "-", f[1])]
        e = sum(1 for f in cat if f[0] == "ERROR"); w = sum(1 for f in cat if f[0] == "WARN")
        roll.append(f"{name}:{'FAIL' if e else ('warn' if w else 'ok')}")
    print("-" * 60)
    print("  laws: " + "  ".join(roll))
    print(f"  {passes} pass | {warns} warn | {errors} error  ({len(paths)} files)")
    # Say what this did NOT check. A green run on a page with no accessibility problems visible to a
    # regex reads as "accessible" and stops anyone from looking - the exact failure category J was added
    # for. Keyboard order, real AT behaviour and anything needing a rendered page stay out of reach here.
    print("  NOT checked: keyboard traps/tab order, focus management, real screen-reader output,")
    print("  alt-text quality, colour-only meaning, anything requiring a rendered page. Green here is")
    print("  a floor, not an accessibility pass - a human still has to drive it with a keyboard.")
    for note in engine_copy_notes():
        print("  " + note)
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
