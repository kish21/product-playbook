#!/usr/bin/env python3
"""board.py - moves a ticket's card on the Delivery Board (GitHub Projects v2) and reads it back. ONE module for
every phase that moves a card: /build (In Progress at the start, In Review at the record) and /ship's land.py
(In Review on a hand-off, Done after the merge). /tickets' publish.py creates the board and its fields.

Rules every move keeps:
  - read back: what the card reads is what GitHub holds after the move, never what was sent;
  - never backwards: a Status past the one asked for (Todo < In Queue < In Progress < In Review < Done) is left;
  - a board this run cannot reach is ONE line saying so and what to do - never "moved" without the read-back.
A logged build closed with "no board was set up" while the ticket's card sat in Todo; a logged /ship
opened its PR and left the card at Todo. The two moves lived in two scripts; this is the one.

    python board.py <ticket id> "In Progress" [--seat SR1]     one line: what the card reads now
    python board.py <ticket id> --show                          the card's Status and Seat, nothing changed

Portable: stdlib + the `gh` CLI (needs the `project` scope: gh auth refresh -s project).
PLAYBOOK_BOARD=off skips GitHub entirely (tests, offline work).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

TIMEOUT = 30
REMOTE = re.compile(r"github\.com[:/]+([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")
# a Status someone set past this one is theirs: a move never pulls a card back from review or done
ORDER = ("", "todo", "in queue", "in progress", "in review", "done")

CARD_FIELDS = (
    "id project{id title "
    "status:field(name:\"Status\"){... on ProjectV2SingleSelectField{id options{id name}}} "
    "seat:field(name:\"Seat\"){... on ProjectV2SingleSelectField{id options{id name description}}}} "
    "statusValue:fieldValueByName(name:\"Status\"){... on ProjectV2ItemFieldSingleSelectValue{name}} "
    "seatValue:fieldValueByName(name:\"Seat\"){... on ProjectV2ItemFieldSingleSelectValue{name}}")
CARD_QUERY = ("query($q:String!){search(query:$q,type:ISSUE,first:10){nodes{... on Issue{number title state "
              "projectItems(first:10){nodes{" + CARD_FIELDS + "}}}}}}")
ISSUE_QUERY = ("query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n){number title state "
               "projectItems(first:10){nodes{" + CARD_FIELDS + "}}}}}")
SET_VALUE = ("mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,"
             "fieldId:$f,value:{singleSelectOptionId:$o}}){projectV2Item{id}}}")


class BoardError(Exception):
    """GitHub could not be asked: the message is the one line the user hears."""


def board_off() -> bool:
    return os.environ.get("PLAYBOOK_BOARD", "").lower() == "off"


def explain(text: str) -> str:
    """A gh failure, in the words the user acts on."""
    if re.search(r"(?i)scope|INSUFFICIENT|read:project|\bproject\b.*permission", text):
        return "gh lacks the `project` scope - run: gh auth refresh -s project"
    if re.search(r"(?i)auth login|not logged|authentication", text):
        return "gh is not signed in - run: gh auth login"
    return f"GitHub refused: {text.strip()[:160]}"


def gh_graphql(query: str, variables: dict) -> dict:
    """The default door to GitHub: `gh api graphql`, the payload on stdin. A test passes its own function instead."""
    try:
        p = subprocess.run(["gh", "api", "graphql", "--input", "-"], input=json.dumps({"query": query,
                           "variables": variables}), capture_output=True, text=True, encoding="utf-8",
                           timeout=TIMEOUT)
    except FileNotFoundError:
        raise BoardError("the gh command is not installed")
    except subprocess.TimeoutExpired:
        raise BoardError(f"GitHub did not answer in {TIMEOUT}s")
    data = json.loads(p.stdout) if p.stdout.strip().startswith("{") else {}
    if p.returncode != 0 or data.get("errors"):
        raise BoardError(explain(json.dumps(data.get("errors")) if data.get("errors") else (p.stderr or p.stdout)))
    return data.get("data") or {}


def graphql_via(run) -> callable:
    """A gql door over a `run(args) -> (code, stdout, stderr)` function (land.py's, so its tests fake one host)."""
    def gql(query: str, variables: dict) -> dict:
        args = ["gh", "api", "graphql", "-f", f"query={query}"]
        for k, v in variables.items():
            args += ["-F" if isinstance(v, int) else "-f", f"{k}={v}"]
        code, out, err = run(args)
        data = json.loads(out) if (out or "").strip().startswith("{") else {}
        if code != 0 or data.get("errors"):
            raise BoardError(explain(json.dumps(data.get("errors")) if data.get("errors") else (err or out or "")))
        return data.get("data") or {}
    return gql


def repo_of(base: str = ".") -> str | None:
    """owner/name from the `origin` remote, when it is on GitHub; None otherwise (no network call)."""
    try:
        url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=base, capture_output=True, text=True,
                             timeout=TIMEOUT).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = REMOTE.search(url)
    return f"{m.group(1)}/{m.group(2)}" if m else None


def find_card(tid: str, repo: str, gql=gh_graphql) -> tuple[dict | None, dict | None]:
    """(the issue titled [tid], its Delivery Board card); either None when GitHub has none."""
    d = gql(CARD_QUERY, {"q": f'repo:{repo} is:issue in:title "[{tid}]"'})
    issues = [n for n in (d.get("search") or {}).get("nodes") or []
              if n and (n.get("title") or "").startswith(f"[{tid}]")]
    if not issues:
        return None, None
    issue = issues[0]
    cards = [c for c in (issue.get("projectItems") or {}).get("nodes") or [] if c]
    card = next((c for c in cards if (c["project"].get("title") or "").endswith("Delivery Board")), None) \
        or (cards[0] if cards else None)
    return issue, card


def issue_cards(number: int, repo: str, gql=gh_graphql) -> list[dict]:
    """Every board card of issue #number (an issue can sit on more than one board)."""
    owner, name = repo.split("/", 1)
    d = gql(ISSUE_QUERY, {"o": owner, "r": name, "n": int(number)})
    issue = ((d.get("repository") or {}).get("issue")) or {}
    return [c for c in (issue.get("projectItems") or {}).get("nodes") or [] if c]


def value(card: dict, key: str) -> str:
    return ((card.get(key) or {}).get("name") or "") if card else ""


def option(field: dict | None, name: str) -> dict | None:
    return next((o for o in (field or {}).get("options") or [] if o["name"].lower() == name.lower()), None)


def at_or_past(now: str, want: str) -> bool:
    """True when a card at `now` must not be moved to `want`: it is already there, or further along."""
    a, b = now.lower(), want.lower()
    return a in ORDER and b in ORDER and a != "" and ORDER.index(a) >= ORDER.index(b)


def move(tid: str, status: str, seat: str | None = None, repo: str | None = None, gql=gh_graphql,
         base: str = ".") -> str:
    """/build: find the card by ticket id; set its Status (never backwards) and, when it has none, its Seat; read
    both back. One line."""
    if board_off():
        return f"Board: not checked (PLAYBOOK_BOARD=off) - {tid}'s card was not moved"
    repo = repo or repo_of(base)
    if not repo:
        return f"Board: none - this project has no GitHub remote, so {tid} has no card to move"
    try:
        issue, card = find_card(tid, repo, gql)
        if issue is None:
            return f"Board: no issue titled [{tid}] in {repo} - no card moved (publish the backlog with /tickets)"
        if card is None:
            return f"Board: issue #{issue['number']} ({tid}) has no card on a board - nothing moved"
        proj, item = card["project"], card["id"]
        now, have_seat = value(card, "statusValue"), value(card, "seatValue")
        notes, changed = [], False
        if at_or_past(now, status):
            notes.append(f"Status already {now}")
        else:
            field = proj.get("status") or {}
            opt = option(field, status)
            if not field.get("id"):
                notes.append(f"the board has no Status field - Status left {now or 'unset'}")
            elif not opt:
                notes.append(f"the board's Status has no {status!r} option - left at {now or 'unset'}; add the option "
                             f"on the board to use it")
            else:
                gql(SET_VALUE, {"p": proj["id"], "i": item, "f": field["id"], "o": opt["id"]})
                changed = True
        if seat and have_seat and have_seat != seat:
            notes.append(f"! its Seat is {have_seat}, not {seat} - not this seat's ticket: STOP and tell the user")
        elif seat and not have_seat:
            field = proj.get("seat") or {}
            opt = next((o for o in field.get("options") or [] if o["name"] == seat), None)
            if opt and field.get("id"):
                gql(SET_VALUE, {"p": proj["id"], "i": item, "f": field["id"], "o": opt["id"]})
                changed = True
            else:
                notes.append(f"the board's Seat has no {seat!r} option - Seat left empty")
        if changed:  # the read-back: what GitHub holds now, never what was sent
            _, card = find_card(tid, repo, gql)
            now, have_seat = value(card, "statusValue"), value(card, "seatValue")
            if now.lower() != status.lower() and not any(n.startswith("Status already") for n in notes):
                notes.append(f"! the read-back says Status {now or 'unset'}, not {status} - move it by hand")
        tail = f" · {' · '.join(notes)}" if notes else ""
        return (f"Board: {tid} card (#{issue['number']}) reads Status {now or 'unset'}, Seat {have_seat or 'empty'}"
                f"{' (read back)' if changed else ''}{tail}")
    except BoardError as e:
        return f"Board: not moved - {e}; move {tid}'s card to {status} by hand"


def move_issue(number: int, status: str, repo: str, gql=gh_graphql, missing_option_ok: bool = False) \
        -> list[tuple[str, str]]:
    """/ship: set every board card of issue #number to `status` (never backwards) and read each back.
    Returns (OK | FAIL | NOTE, line) pairs; FAIL only when a card does not read what it should."""
    what = f"card #{number}"
    if board_off():
        return [("NOTE", f"{what}: not checked (PLAYBOOK_BOARD=off) - not moved")]
    try:
        cards = issue_cards(number, repo, gql)
    except BoardError as e:  # its message already names the fix (a scope, a sign-in) or what happened (a timeout)
        return [("FAIL", f"{what}: the board could not be read - {e}. Then run this again")]
    except (KeyError, TypeError, ValueError) as e:
        return [("FAIL", f"{what}: GitHub's answer about the board was not in the expected shape ({e!r}) - run this "
                         f"again; if it fails twice, move the card by hand")]
    if not cards:
        return [("OK", f"{what}: no board card for this issue - nothing to move")]
    out, skip = [], set()
    try:
        for c in cards:
            field, now = (c.get("project") or {}).get("status") or {}, value(c, "statusValue")
            opt = option(field, status)
            if not opt:
                skip.add(c["id"])
                line = (f"{what}: the board '{c['project']['title']}' has no Status option '{status}' - add it on the "
                        f"board (adding it from a script resets every card's Status); the card stays at "
                        f"{now or 'unset'}")
                out.append(("NOTE" if missing_option_ok else "FAIL", line))
            elif at_or_past(now, status) and now.lower() != status.lower():
                skip.add(c["id"])
                out.append(("OK", f"{what}: Status reads {now} on '{c['project']['title']}' - already past "
                                  f"{status}, never moved back"))
            elif now != opt["name"]:
                gql(SET_VALUE, {"p": c["project"]["id"], "i": c["id"], "f": field["id"], "o": opt["id"]})
        for c in issue_cards(number, repo, gql):  # the read-back
            if c["id"] in skip:
                continue
            got = value(c, "statusValue")
            out.append(("OK", f"{what}: Status reads {got} on '{c['project']['title']}'") if got.lower() == status.lower()
                       else ("FAIL", f"{what}: Status reads {got or 'unset'}, not {status}"))
    except BoardError as e:
        out.append(("FAIL", f"{what}: not moved - {e}; move it to {status} by hand"))
    return out


def show(tid: str, repo: str | None = None, gql=gh_graphql, base: str = ".") -> str:
    repo = repo or repo_of(base)
    if not repo:
        return "Board: none - no GitHub remote"
    try:
        issue, card = find_card(tid, repo, gql)
    except BoardError as e:
        return f"Board: not read - {e}"
    if issue is None or card is None:
        return f"Board: {tid} has no card"
    return f"Board: {tid} card (#{issue['number']}) reads Status {value(card, 'statusValue') or 'unset'}, " \
           f"Seat {value(card, 'seatValue') or 'empty'}"


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    seat = argv[argv.index("--seat") + 1] if "--seat" in argv and argv.index("--seat") + 1 < len(argv) else None
    if argv and "--show" in argv:
        print(show(argv[0]))
        return 0
    if len(argv) < 2 or argv[0].startswith("-"):
        print('usage: python board.py <ticket id> "In Progress" [--seat SR1]')
        return 2
    print(move(argv[0], argv[1], seat))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
