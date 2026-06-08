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

def audit_text(path, text, findings):
    tokens = collect_tokens(text)

    # Law 7 — COMPUTED contrast on every defined foreground/surface pair
    for fg, bg in PAIRS:
        if fg in tokens and bg in tokens:
            ratio = contrast(tokens[fg], tokens[bg])
            if ratio is None:
                continue
            level = "PASS" if ratio >= 4.5 else ("WARN" if ratio >= 3.0 else "ERROR")
            findings.append((level, "Law7-contrast", path,
                             f"{fg} on {bg} = {ratio:.2f}:1 "
                             f"({'AA' if ratio>=4.5 else 'AA-large only' if ratio>=3 else 'FAILS AA'})"))

    # Markdown is documentation/spec — only its colour tokens are machine-checkable
    # (the contrast pass above). The code-pattern checks below are for component
    # code only, else a Don't-list line like "No `transition: all`" false-positives.
    if path.lower().endswith(".md"):
        return

    # Law 14 — no raw hex outside :root token declarations (component code)
    body = re.sub(r":root\s*\{.*?\}", "", text, flags=re.S)
    body = re.sub(r"\.dark\s*\{.*?\}", "", body, flags=re.S)
    for m in re.finditer(r"(?<![\w/])#[0-9a-fA-F]{6}\b", body):
        if "href" in body[max(0, m.start()-8):m.start()]:
            continue
        findings.append(("ERROR", "Law14-raw-hex", path, f"raw hex {m.group(0)} in component code (use a token)"))

    # Law 12 — no transition: all
    for m in re.finditer(r"transition:\s*all|transition-all", text):
        findings.append(("ERROR", "Law12-transition-all", path, "transition: all (animate transform/opacity only)"))

    # Law 1 — Inter/Roboto/Arial as the PRIMARY (first) font family
    for m in re.finditer(r"--font-(?:sans|display)\s*:\s*([^;]+);", text):
        first = m.group(1).split(",")[0].strip().strip('"\'').lower()
        if first in ("inter", "roboto", "arial", "system-ui", "helvetica"):
            findings.append(("ERROR", "Law1-default-font", path, f"primary font is '{first}' - pick a distinctive face"))

    # Law 3 — font-size below the floor (13px), excluding the 12px caption tier check is heuristic
    for m in re.finditer(r"font-size:\s*(\d+)px", text):
        if int(m.group(1)) < 12:
            findings.append(("ERROR", "Law3-tiny-font", path, f"font-size {m.group(1)}px below 12px floor"))

    # Law 13 — interactive elements should define focus-visible (presence heuristic)
    if re.search(r"<(button|input|a)\b", text, re.I) and "focus-visible" not in text:
        findings.append(("WARN", "Law13-focus", path, "interactive elements but no :focus-visible found"))

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
    print("-" * 60)
    print(f"  {passes} pass | {warns} warn | {errors} error  ({len(paths)} files)")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
