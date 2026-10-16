#!/usr/bin/env python3
"""env_init.py - make the local .env from .env.example, so a first boot never waits on a person.

    python env_init.py [--root <project>] [--example .env.example] [--env .env]

Run by /foundation (and named by every phase start while .env is missing); stdlib only, so a project
may copy it into its tooling folder and name that copy in docs/runbook.md.

What it does, in this order:
  1. makes sure git ignores .env BEFORE a value is written (`git check-ignore .env`; when it is not
     ignored, `.env` is added to .gitignore and the output says so). A .env git already tracks is
     reported, never written to.
  2. .env missing: writes it from .env.example (comments and order kept). .env present: NEVER changes a
     line of it - only a variable .env.example has and .env lacks is appended, filled the same way.
  3. fills what can be made on this machine, and only a value .env.example leaves as a CHANGE_ME
     placeholder:
       - a local secret (session / cookie / signing / HMAC / JWT / encryption key, or a comment saying
         to generate it): a new random value (secrets.token_hex(32))
       - the environment (APP_ENV, NODE_ENV, ...): development
       - the fake model switch (USE_REAL_MODEL=false, USE_FAKE_MODEL=true, a provider whose comment
         names a fake/scripted/stub one): the fake
       - a local database URL or path: the comment's own example (`for example ...`, `e.g. ...`,
         `format: ...`), else the runbook's `NAME=value` line, when it points at this machine; generic
         `user:pass` filled from docker-compose's POSTGRES_/MYSQL_ variables; a SQLite one with no
         example: data/<project>_dev.db (TEST_: _test.db)
       - any other non-secret setting whose comment gives an example
     A comment may decide instead: `env-init: secret` · `env-init: outside` · `env-init: value <v>`.
  4. leaves every real outside credential (cloud / model / third-party keys, tenant and client ids,
     webhooks, other services' URLs) as its CHANGE_ME placeholder: the app's guard refuses it only in
     real mode or production.
  5. prints one short list - filled automatically / needed from you only for real mode (where to get
     each, from its comment) / still CHANGE_ME with no local value known. It NEVER prints a value.

Exit: 0 done (or nothing to do) · 1 refused (.env tracked by git, or the ignore could not be made) ·
2 no .env.example.
"""
from __future__ import annotations

import argparse
import os
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

PLACEHOLDER = "CHANGE_ME"
LINE = re.compile(r"^(\s*(?:export\s+)?)([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*)(.*)$")
TAG = re.compile(r"env-init:\s*(secret|outside|value)\b\s*(\S*)", re.I)

ENV_NAME = re.compile(r"^(?:APP_|PYTHON_|NODE_|RACK_|RAILS_|FLASK_|DJANGO_|DEPLOY_)?ENV(?:IRONMENT)?$|^NODE_ENV$", re.I)
REAL_SWITCH = re.compile(r"^(?:USE|ENABLE)_(?:REAL|LIVE)_\w+$|^\w*_(?:REAL|LIVE)_(?:MODEL|LLM|AI|PROVIDER)S?$", re.I)
FAKE_SWITCH = re.compile(r"^(?:USE|ENABLE)_(?:FAKE|STUB|MOCK|SCRIPTED)_?\w*$|^\w*_(?:FAKE|STUB|MOCK)_(?:MODEL|LLM|AI|"
                         r"PROVIDER)S?$", re.I)
PROVIDER = re.compile(r"(?:MODEL|LLM|AI|CHAT|EMBEDDING)S?_(?:PROVIDER|BACKEND|MODE|CLIENT)$|^PROVIDER$", re.I)
FAKE_WORD = re.compile(r"`?\b(fake|scripted|stub|mock|offline|local-fake)\b`?", re.I)
DATASTORE = re.compile(r"^(?:TEST_)?(?:DATABASE|DB|POSTGRES(?:QL)?|PG|MYSQL|MARIADB|MONGO(?:DB)?|SQLITE|REDIS)"
                       r"(?:_\w+)?_(?:URL|URI|DSN|PATH|FILE)$|^(?:TEST_)?(?:DATABASE|DB)_?(?:URL|URI|DSN|PATH|FILE)?$",
                       re.I)
LOCAL_SECRET = re.compile(r"SECRET|SIGNING|HMAC|SALT|PEPPER|COOKIE|CSRF|JWT|ENCRYPTION|FERNET|SESSION", re.I)
GENERATE = re.compile(r"(?i)\bgenerat|token_hex|token_urlsafe|openssl rand|\brandom\b|uuid4")
# a credential someone else issues: a vendor prefix, a key / id / token kind, or a webhook and another service's URL
OUTSIDE_NAME = re.compile(
    r"API_?KEY|ACCESS_KEY|ACCESS_TOKEN|AUTH_TOKEN|CLIENT_(?:ID|SECRET)|TENANT|ACCOUNT_?(?:ID|SID)|WEBHOOK|"
    r"PRIVATE_KEY|SERVICE_ACCOUNT|BOT_TOKEN|_REGION$|_PROJECT(?:_ID)?$|_ENDPOINT$|_BASE_URL$|_HOST$|_URL$|"
    r"^(?:AWS|AZURE|GCP|GCLOUD|GOOGLE|VERTEX|BEDROCK|GEMINI|OPENAI|ANTHROPIC|CLAUDE|MISTRAL|COHERE|GROQ|HF|HUGGINGFACE|"
    r"STRIPE|PAYPAL|TWILIO|SENDGRID|MAILGUN|POSTMARK|RESEND|SLACK|DISCORD|GITHUB|GITLAB|SENTRY|DATADOG|PINECONE|"
    r"SUPABASE|FIREBASE|CLOUDFLARE|VERCEL|NEON|ENTRA|OKTA|AUTH0|CLERK|SHOPIFY|HUBSPOT|SALESFORCE|ZENDESK)_", re.I)
OUTSIDE_COMMENT = re.compile(
    r"(?i)\bconsole\b|dashboard|\bportal\b|\bissued\b|shared with|\bvendor\b|third[- ]party|sign up|"
    r"\bfrom (?:your|the) (?:provider|cloud|account)|\bcreate (?:it|one|an?) (?:in|at|on)\b|access key|api key|"
    r"subscription|\bIAM\b")
EXAMPLE = re.compile(r"(?i)(?:for example|e\.g\.|examples?:|format:|form:|default:|defaults? to)\s*[:(]?\s*`?([^\s`),;]+)")
DB_PART = re.compile(r"^(?:TEST_)?(?:DATABASE|DB|POSTGRES(?:QL)?|PG|MYSQL|MARIADB)_(HOST|USER|PASSWORD|NAME)$", re.I)
URL_IN = re.compile(r"\b([a-z][a-z0-9+.-]*://[^\s`)'\"]+)")
LOCAL_HOSTS = ("127.0.0.1", "localhost", "[::1]", "::1")
GENERIC_CRED = re.compile(r"(?i)^(?:user(?:name)?|pass(?:word)?|pwd|secret|<[^>]*>|x+|\.\.\.|changeme|change_me)$")
LOOKS_PLACEHOLDER = re.compile(r"(?i)<[^>]*>|\.\.\.|CHANGE_ME|your[-_]|xxx")
COMPOSE = ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")


def parse(text: str) -> list[tuple[int, str, str, str]]:
    """(line index, name, value, comment) for each variable; the comment is the block right above it + inline."""
    lines, out = text.splitlines(), []
    for i, line in enumerate(lines):
        m = LINE.match(line)
        if not m or line.lstrip().startswith("#"):
            continue
        value, inline = m.group(4), ""
        if " #" in value:
            value, inline = value.split(" #", 1)
        above, j = [], i - 1
        while j >= 0 and lines[j].lstrip().startswith("#"):
            above.insert(0, lines[j].lstrip().lstrip("#").strip())
            j -= 1
        out.append((i, m.group(2), value.strip().strip("'\""), " ".join(above + [inline.strip()]).strip()))
    return out


def project_slug(root: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "_", root.resolve().name.lower()).strip("_") or "app"


def runbook_value(root: Path, name: str) -> str:
    """`NAME=value` (also `export NAME=`, `$env:NAME = "..."`) in docs/runbook*.md or README.md."""
    rx = re.compile(rf"(?:^|[\s`]|\$env:)(?:export\s+)?{re.escape(name)}\s*=\s*[\"']?([^\s\"'`]+)")
    for f in [*sorted((root / "docs").glob("runbook*.md")), root / "README.md"]:
        if f.is_file():
            for m in rx.finditer(f.read_text(encoding="utf-8", errors="replace")):
                if PLACEHOLDER not in m.group(1) and not m.group(1).startswith("$"):
                    return m.group(1)
    return ""


def compose_creds(root: Path) -> dict[str, str]:
    """POSTGRES_/MYSQL_ user, password and database from the project's compose file (its own local values)."""
    out: dict[str, str] = {}
    for n in COMPOSE:
        f = root / n
        if f.is_file():
            for m in re.finditer(r"(?m)^\s*-?\s*((?:POSTGRES|MYSQL|MARIADB)_(?:USER|PASSWORD|DB|DATABASE))\s*[:=]\s*"
                                 r"[\"']?([^\s\"'#]+)", f.read_text(encoding="utf-8", errors="replace")):
                if "${" not in m.group(2):
                    out.setdefault(m.group(1).upper().split("_", 1)[1], m.group(2))
    return out


def is_local(url: str) -> bool:
    if url.lower().startswith("sqlite") or "://" not in url:
        return not LOOKS_PLACEHOLDER.search(url)
    host = re.sub(r"^[^/]*//(?:[^@/]*@)?", "", url).split("/", 1)[0]
    host = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
    return host in LOCAL_HOSTS


def fill_creds(url: str, creds: dict[str, str]) -> str:
    """Generic `user:pass@` in an example: the compose file's own values, else '' (no local value known)."""
    m = re.match(r"^([^:/]+://)([^:@/]+)(?::([^@/]*))?@(.*)$", url)
    if not m:
        return "" if LOOKS_PLACEHOLDER.search(url) else url
    user, pw = m.group(2), m.group(3) or ""
    if GENERIC_CRED.match(user) or (pw and GENERIC_CRED.match(pw)):
        if not creds.get("USER") or not creds.get("PASSWORD"):
            return ""
        user, pw = creds["USER"], creds["PASSWORD"]
    out = f"{m.group(1)}{user}{':' + pw if pw else ''}@{m.group(4)}"
    return "" if LOOKS_PLACEHOLDER.search(out) else out


def example_of(comment: str) -> str:
    url = URL_IN.search(comment)
    if url:
        return url.group(1).rstrip(".")
    m = EXAMPLE.search(comment)
    return m.group(1).rstrip(".") if m else ""


def datastore_value(name: str, comment: str, root: Path, creds: dict[str, str]) -> str:
    for found in (example_of(comment), runbook_value(root, name)):
        if found and is_local(found):
            val = fill_creds(found, creds) if "://" in found else found
            if val:
                return val
    if re.search(r"(?i)sqlite", comment):
        test = "_test" if name.upper().startswith("TEST_") or "_TEST" in name.upper() else "_dev"
        path = f"data/{project_slug(root)}{test}.db"
        return path if re.search(r"(?i)_(?:PATH|FILE)$", name) else f"sqlite:///{path}"
    return ""


def classify(name: str, comment: str, root: Path, creds: dict[str, str]) -> tuple[str, str, str]:
    """(kind, value, why): kind is filled / outside / unknown."""
    tag = TAG.search(comment)
    if tag:
        kind = tag.group(1).lower()
        if kind == "secret":
            return "filled", secrets.token_hex(32), "a new random secret"
        if kind == "value" and tag.group(2):
            return "filled", tag.group(2), "the value its comment gives"
        return "outside", "", ""
    if ENV_NAME.match(name):
        return "filled", "development", "development"
    if REAL_SWITCH.match(name):
        return "filled", "false", "the fake model on"
    if FAKE_SWITCH.match(name):
        return "filled", "true", "the fake model on"
    if PROVIDER.match(name):
        fake = FAKE_WORD.search(comment)
        return ("filled", fake.group(1).lower(), "the fake model on") if fake else ("unknown", "", "")
    part = DB_PART.match(name)
    if part:
        val = {"HOST": "127.0.0.1", "USER": creds.get("USER", ""), "PASSWORD": creds.get("PASSWORD", ""),
               "NAME": f"{project_slug(root)}_{'test' if 'TEST' in name.upper() else 'dev'}"}[part.group(1).upper()]
        return ("filled", val, "a local database") if val else ("unknown", "", "")
    if DATASTORE.match(name) and not re.search(r"(?i)^(?:SENTRY|DATADOG)_", name):
        val = datastore_value(name, comment, root, creds)
        return ("filled", val, "a local database") if val else ("unknown", "", "")
    outside = bool(OUTSIDE_NAME.search(name) or OUTSIDE_COMMENT.search(comment))
    if not outside and (LOCAL_SECRET.search(name) or GENERATE.search(comment)):
        return "filled", secrets.token_hex(32), "a new random secret"
    if outside:
        return "outside", "", ""
    ex = example_of(comment)
    if ex and not LOOKS_PLACEHOLDER.search(ex) and not re.search(r"(?i)key|token|passw|credential", name):
        return "filled", ex, "the example in its comment"
    return "unknown", "", ""


def git(root: Path, *args: str) -> subprocess.CompletedProcess | None:
    if not shutil.which("git"):
        return None
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None


def listed_in_gitignore(root: Path, rel: str) -> bool:
    """No git repository yet: the root .gitignore's own patterns, the last match winning (a `!` re-includes)."""
    import fnmatch
    gi = root / ".gitignore"
    hit = False
    for raw in (gi.read_text(encoding="utf-8", errors="replace").splitlines() if gi.is_file() else []):
        pat = raw.strip()
        if not pat or pat.startswith("#"):
            continue
        neg = pat.startswith("!")
        pat = pat.lstrip("!").lstrip("/").rstrip("/")
        if fnmatch.fnmatchcase(rel, pat) or fnmatch.fnmatchcase(rel.rsplit("/", 1)[-1], pat):
            hit = not neg
    return hit


def ensure_ignored(root: Path, env: Path) -> tuple[bool, str]:
    """(ok, what was done). Never writes a value before this holds."""
    rel = os.path.relpath(env, root).replace(os.sep, "/")
    inside = git(root, "rev-parse", "--is-inside-work-tree")
    in_git = inside is not None and inside.returncode == 0 and inside.stdout.strip() == "true"
    if in_git:
        tracked = git(root, "ls-files", "--error-unmatch", "--", rel)
        if tracked is not None and tracked.returncode == 0:
            return False, (f"{rel} is committed to git - remove it from the index first (`git rm --cached {rel}`, "
                           f"then rotate every secret it held); nothing written")
        chk = git(root, "check-ignore", "-q", "--", rel)
        if chk is not None and chk.returncode == 0:
            return True, f"git ignores {rel}"
    elif listed_in_gitignore(root, rel):
        return True, f".gitignore ignores {rel} (not a git repository yet)"
    gi = root / ".gitignore"
    text = gi.read_text(encoding="utf-8", errors="replace") if gi.is_file() else ""
    with gi.open("a", encoding="utf-8", newline="\n") as f:
        f.write(("" if not text or text.endswith("\n") else "\n") + rel + "\n")
    if in_git:
        chk = git(root, "check-ignore", "-q", "--", rel)
        if chk is None or chk.returncode != 0:
            return False, (f"added {rel} to .gitignore, but git still does not ignore it (a later `!` rule?) - fix "
                           f".gitignore; nothing written")
    return True, f"added {rel} to .gitignore - git did not ignore it"


def render(value: str) -> str:
    return f'"{value}"' if re.search(r"[\s#'\"]", value) else value


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="make the local .env from .env.example (never prints a value)")
    ap.add_argument("--root", default=".")
    ap.add_argument("--example", default=".env.example")
    ap.add_argument("--env", default=".env")
    a = ap.parse_args(argv)
    root = Path(a.root)
    example, env = root / a.example, root / a.env
    if not example.is_file():
        print(f"env_init: no {a.example} in {root.resolve().as_posix()} - /structure writes it; nothing to do")
        return 2
    ok, ignore_line = ensure_ignored(root, env)
    if not ok:
        print(f"env_init: REFUSED - {ignore_line}")
        return 1
    ex_text = example.read_text(encoding="utf-8", errors="replace")
    ex_lines, creds = ex_text.splitlines(), compose_creds(root)
    have = {v[1] for v in parse(env.read_text(encoding="utf-8", errors="replace"))} if env.is_file() else set()
    filled, outside, unknown, add = [], [], [], []
    for i, name, value, comment in parse(ex_text):
        if name in have:
            continue
        line = ex_lines[i]
        if PLACEHOLDER in value:
            kind, new, why = classify(name, comment, root, creds)
            if kind == "filled":
                m = LINE.match(line)
                line = f"{m.group(1)}{name}{m.group(3)}{render(new)}"
                filled.append(f"{name} ({why})")
            else:
                where = re.sub(r"\s+", " ", TAG.sub("", comment)).strip()[:140] or "no comment in .env.example"
                (outside if kind == "outside" else unknown).append(f"{name} - {where}")
        j, block = i - 1, []
        while j >= 0 and ex_lines[j].lstrip().startswith("#"):
            block.insert(0, ex_lines[j])
            j -= 1
        add.append((block, line))
    if env.is_file() and not add:
        print(f"env_init: {a.env} exists and has every variable of {a.example} - left as it is ({ignore_line})")
        return 0
    if env.is_file():
        text = env.read_text(encoding="utf-8", errors="replace")
        with env.open("a", encoding="utf-8", newline="\n") as f:
            f.write(("" if not text or text.endswith("\n") else "\n")
                    + "\n# added by env_init.py from .env.example\n"
                    + "".join("".join(b + "\n" for b in block) + line + "\n" for block, line in add))
        head = f"env_init: {a.env} exists - its lines are untouched; added {len(add)} variable(s) it lacked"
    else:
        out = list(ex_lines)  # every variable is new: each line replaced in place, the comments kept
        for (i, *_), (_, line) in zip(parse(ex_text), add):
            out[i] = line
        with env.open("x", encoding="utf-8", newline="\n") as f:  # "x": never over a file made since the check
            f.write("\n".join(out) + "\n")
        head = f"env_init: wrote {a.env} from {a.example}"
    if os.name == "posix":
        env.chmod(0o600)
    print(f"{head} ({ignore_line}); no value is printed")
    print(f"  filled automatically: {', '.join(filled) or 'nothing'}")
    print(f"  needed from you only for real mode (the fake model and development boot without them): "
          + ("; ".join(outside) if outside else "nothing"))
    if unknown:
        print(f"  still CHANGE_ME, no local value known - set before the first boot if the app reads it in "
              f"development: {'; '.join(unknown)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
