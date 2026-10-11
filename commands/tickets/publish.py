#!/usr/bin/env python3
"""tickets publish engine - publishes a confirmed backlog to GitHub and reads every part of it back.

One command does what `references/publishing.md` §Mirror the plan structure onto GitHub, §Epics are parent
issues and §The Delivery Board describe, then runs `references/verification.md` §After publishing over what
GitHub now holds. It never creates a repository, never edits or closes an existing issue, never moves a
ticket between epics and never changes a board value someone already set - except, with --reseat, the plan's
own Owner, Lane and Seat after the user changed the seats at a /tickets re-run (Status is never touched).

Usage:  python publish.py                            publish the backlog committed in this folder
        python publish.py --dry-run                  say what would be created; write nothing
        python publish.py --no-board                 issues, links and labels only (no `project` scope)
        python publish.py --reseat                   the seats or lanes changed (a 2 -> 5 team): every card's
                                                     Owner, Lane and Seat are set again from the plan; Status stays
        python publish.py <plan.json> [flags]        an explicit plan (tests, an older backlog)
Exit:   0 all read-backs green · 1 a read-back or a proof failed · 2 the run refused to start (pre-flight)

With no plan file the plan is READ from the committed files (derive_plan): each docs/issues/<ID>_<slug>.md gives
its title (`# [ID] title`), epic (`[M1-LOG] name`), lane, owner and Depends On; TICKETS.md gives the product
(`# Tickets — <name>`), the milestone titles (`## M1 — <title>`) and the Lanes table's Seat column; PRODUCT.md
#Plan gives each milestone's end date. The model never types plan.json, and a re-run needs no scratch file.

plan.json, when one is given:
  {"product": "<name>", "seats": ["SR1", "SR2"],
   "milestones": [{"title": "M1 - ...", "due": "YYYY-MM-DD" | null}],
   "epics":   [{"id": "M1-LOG", "name": "...", "milestone": "M1 - ...", "lane": "events", "owner": "Senior",
                "seat": "SR2"}],
   "tickets": [{"id": "M1-LOG-01", "title": "...", "file": "docs/issues/M1-LOG-01_x.md",
                "epic": "M1-LOG", "depends_on": ["M1-..."]}]}
A ticket takes its milestone, lane, owner and seat from its epic: every ticket of an epic shares its lane, and
every epic of a lane shares its seat (TICKETS.md's lane table). `seats` lists every seat the user named (SR1..SRn,
JR1..JRn) - one board option each. An older plan with one plan-wide `"seat": "SR1"` still works: every epic sits there.
Portable: stdlib + the `gh` CLI. With a plan file, a report is written beside it as <plan>.report.json.
"""
import json, os, re, subprocess, sys, tempfile, time

TAG = re.compile(r"^\[([A-Za-z0-9-]+)\]")
STATUS_OPTIONS = ("Todo", "In Queue", "In Progress", "In Review", "Done")  # In Review: /ship land.py review
LIST_RETRIES = (2, 4, 8)   # seconds between re-reads of the issue list: GitHub's list lags a fresh issue
OWNER_OPTIONS = ("Senior", "Junior")
LANE_COLOR, OWNER_COLOR = "1D76DB", "5319E7"


class Refused(Exception):
    """The run must not start: nothing has been written."""


# ---------- the only door to GitHub -----------------------------------------------------------------------

class GH:
    """Every GitHub call goes through here, so a test can put a fake GitHub behind the same three methods."""

    def __init__(self, repo=None):
        self.repo = repo
        self.calls = 0

    def _run(self, args, payload=None):
        self.calls += 1
        path = None
        if payload is not None:
            fd, path = tempfile.mkstemp(suffix=".json")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            args = args + ["--input", path]
        try:
            p = subprocess.run(["gh"] + args, capture_output=True, text=True, encoding="utf-8")
        finally:
            if path:
                os.unlink(path)
        return p.returncode, p.stdout, p.stderr

    def rest(self, method, path, payload=None, missing_ok=False):
        """REST call. Returns parsed JSON, or None for a 404 when missing_ok."""
        code, out, err = self._run(["api", "-X", method, path, "-H", "Accept: application/vnd.github+json"],
                                   payload)
        if code != 0:
            if missing_ok and "404" in (err + out):
                return None
            raise RuntimeError(f"gh api {method} {path} failed: {(err or out).strip()[:300]}")
        return json.loads(out) if out.strip() else None

    def rest_all(self, path):
        """Every page of a list endpoint (per_page=100), so an index is never truncated."""
        items, page = [], 1
        sep = "&" if "?" in path else "?"
        while True:
            batch = self.rest("GET", f"{path}{sep}per_page=100&page={page}") or []
            items += batch
            if len(batch) < 100:
                return items
            page += 1

    def graphql(self, query, variables=None):
        code, out, err = self._run(["api", "graphql"], {"query": query, "variables": variables or {}})
        data = json.loads(out) if out.strip() else {}
        if code != 0 or data.get("errors"):
            raise RuntimeError(f"graphql failed: {(json.dumps(data.get('errors')) if data else err)[:400]}")
        return data["data"]

    def auth_scopes(self):
        code, out, err = self._run(["auth", "status"])
        text = out + err
        if code != 0:
            raise Refused("`gh` is not signed in - run `gh auth login`, then /tickets again")
        m = re.search(r"Token scopes:\s*(.*)", text)
        return {s.strip(" '\"") for s in m.group(1).split(",")} if m else set()


# ---------- the plan and the committed files ------------------------------------------------------------

def load_plan(path):
    with open(path, encoding="utf-8") as f:
        return check_plan(json.load(f))


def check_plan(plan):
    epics = {e["id"]: e for e in plan.get("epics", [])}
    ids = [e["id"] for e in plan.get("epics", [])] + [t["id"] for t in plan.get("tickets", [])]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise Refused(f"IDs appear more than once in the plan: {dup}")
    milestones = {m["title"] for m in plan.get("milestones", [])}
    for e in plan.get("epics", []):
        if e["milestone"] not in milestones:
            raise Refused(f"epic {e['id']} names milestone {e['milestone']!r}, which the plan does not list")
    seats = plan_seats(plan)
    lane_seat = {}
    for e in plan.get("epics", []):
        s = epic_seat(plan, e)
        if s not in seats:
            raise Refused(f"epic {e['id']} sits at seat {s!r}, which the plan's seats {seats} do not list")
        if lane_seat.setdefault(e["lane"], s) != s:
            raise Refused(f"lane {e['lane']!r} has two seats ({lane_seat[e['lane']]!r} and {s!r}) - one lane, one seat")
    known = {t["id"] for t in plan.get("tickets", [])}
    for t in plan.get("tickets", []):
        if t["epic"] not in epics:
            raise Refused(f"ticket {t['id']} names epic {t['epic']}, which the plan does not list")
        for d in t.get("depends_on", []):
            if d not in known:
                raise Refused(f"ticket {t['id']} depends on {d}, which the plan does not list")
    return plan, epics


# ---------- the plan, read from the committed files (the model never types plan.json) ----------------------

TICKET_FILE = re.compile(r"^(M\d+-[A-Z0-9]+-\d+)[_.]")
TICKET_REF = re.compile(r"\bM\d+-[A-Z0-9]+-\d+\b")
DATE = r"\d{4}-\d{2}-\d{2}"


def _section(text, word):
    m = re.search(rf"(?ims)^#{{2,3}} [^\n]*{word}[^\n]*$(.*?)(?=^#{{1,3}} |\Z)", text)
    return re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S).strip() if m else ""


def _table(text, heading):
    """The rows of the first table under `## <heading>`, as dicts keyed by the header row (lower case)."""
    m = re.search(rf"(?ims)^## {heading}\b[^\n]*$(.*?)(?=^## |\Z)", text)
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in (m.group(1) if m else "").splitlines()
            if ln.strip().startswith("|")]
    if len(rows) < 2:
        return []
    head = [h.lower() for h in rows[0]]
    return [dict(zip(head, r)) for r in rows[2:]]


def _seat_key(s):
    m = re.match(r"([A-Z]+)(\d+)$", s)
    return (0 if s.startswith("SR") else 1, m.group(1) if m else s, int(m.group(2)) if m else 0)


def derive_plan(base="."):
    """plan.json from what is committed: docs/issues/<ID>_<slug>.md (title, epic, lane, owner, Depends On),
    TICKETS.md (product, milestone titles, the lane -> seat table) and PRODUCT.md #Plan (each milestone's end date).
    A re-run needs no file a run left in a scratch folder (a logged run typed a 47K plan.json into one)."""
    base = os.path.abspath(base)
    read = lambda *p: open(os.path.join(base, *p), encoding="utf-8").read() if os.path.isfile(os.path.join(base, *p)) else ""  # noqa: E731
    plan_md, product = read("TICKETS.md"), read("PRODUCT.md")
    if not plan_md:
        raise Refused("no TICKETS.md - run /tickets first (the plan is read from TICKETS.md and docs/issues/)")
    head = re.search(r"(?m)^# [^\n]*?[—–-]\s*(.+)$", plan_md)
    titles = {m.group(1): f"{m.group(1)} — {m.group(2).strip()}" for m in
              re.finditer(r"(?m)^## (M\d+)\s*[—–:-]+\s*(.+?)\s*$", plan_md)}
    sec = re.search(r"(?ms)^## Plan\s*$(.*?)(?=^## |\Z)", product)
    plan_sec = sec.group(1) if sec else ""
    seat_of, seat_info = {}, {}
    for row in _table(plan_md, "Lanes"):
        lane = row.get("lane", "").strip("` ")
        if lane and row.get("seat", "").strip():
            seat_of[lane] = row["seat"].strip("` ")
            # what the seat is (senior/junior, person/agent) - the board's Seat option description
            info = " · ".join(v for v in (row.get("seat type", "").strip(), row.get("operator", "").strip())
                              if v and v not in ("-", "not recorded"))
            if info:
                seat_info[seat_of[lane]] = info
    folder = os.path.join(base, "docs", "issues")
    files = sorted(f for f in os.listdir(folder) if TICKET_FILE.match(f)) if os.path.isdir(folder) else []
    if not files:
        raise Refused("no ticket files in docs/issues/ - run /tickets first")
    epics, tickets = {}, []
    for name in files:
        tid = TICKET_FILE.match(name).group(1)
        text = read("docs", "issues", name)
        eid, ms = tid.rsplit("-", 1)[0], tid.split("-")[0]
        h = re.search(rf"(?m)^# \[{re.escape(tid)}\]\s*(.+)$", text)
        row = re.search(rf"`{re.escape(tid)}`\s*([^·|`\n]+)", plan_md)
        title = (h.group(1) if h else row.group(1) if row else name.split("_", 1)[-1][:-3].replace("-", " ")).strip()
        lane = next((l.strip("` /") for l in _section(text, "Lane").splitlines() if l.strip()), "")
        lane = lane.rsplit("/", 1)[-1]
        owner = next((l.strip() for l in _section(text, "Owner").splitlines() if l.strip()), "Senior")
        ename = re.search(rf"\[{re.escape(eid)}\]\s*(.+)", _section(text, "Epic"))
        erow = re.search(rf"`{re.escape(eid)}`\s*([^|\n]+)", plan_md)
        if eid not in epics:
            epics[eid] = {"id": eid, "name": (ename.group(1) if ename else erow.group(1) if erow else eid).strip(),
                          "milestone": titles.get(ms, ms), "lane": lane, "owner": owner,
                          "seat": seat_of.get(lane, "SR1")}
        deps = [d for d in TICKET_REF.findall(_section(text, "Depends On")) if d != tid]
        tickets.append({"id": tid, "title": title, "file": f"docs/issues/{name}", "epic": eid,
                        "depends_on": list(dict.fromkeys(deps))})
    milestones = []
    for title in dict.fromkeys(e["milestone"] for e in epics.values()):
        ms = title.split(" ", 1)[0]
        due = re.search(rf"\b{ms}\b[^\n·]*?{DATE}\s*(?:→|->|to|–)\s*({DATE})", plan_sec)
        milestones.append({"title": title, "due": due.group(1) if due else None})
    seats = sorted({e["seat"] for e in epics.values()} | set(seat_of.values()), key=_seat_key)
    plan = {"product": (head.group(1).strip() if head else os.path.basename(base)), "seats": seats,
            "milestones": milestones, "epics": list(epics.values()), "tickets": tickets}
    if seat_info:
        plan["seat_info"] = seat_info
    return check_plan(plan)


def plan_seats(plan):
    """The seats the user named, in order - one board option each. An older plan names one plan-wide seat."""
    seats = list(plan.get("seats") or [])
    if not seats:
        seats = [plan.get("seat", "SR1")]
    for e in plan.get("epics", []):  # an old plan with a seat on an epic but no seats list
        if not plan.get("seats") and e.get("seat") and e["seat"] not in seats:
            seats.append(e["seat"])
    return seats


def epic_seat(plan, e):
    """The seat an epic's lane sits at: the epic's own, else the plan-wide one (an older plan), else the first."""
    return e.get("seat") or plan.get("seat") or plan_seats(plan)[0]


def committed_body(git, path):
    """A ticket's body is its file as committed at HEAD - never a working-tree copy nobody committed."""
    dirty = git(["status", "--porcelain", "--", path]).strip()
    if dirty:
        raise Refused(f"{path} has uncommitted changes - commit docs/issues/ before publishing")
    try:
        return git(["show", f"HEAD:{path}"])
    except RuntimeError:
        raise Refused(f"{path} is not committed - commit docs/issues/ before publishing")


def real_git(args):
    p = subprocess.run(["git"] + args, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip())
    return p.stdout


def normalise(body):
    """How publishing.md compares a body with a file: line endings, trailing whitespace, ticks."""
    lines = (body or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [re.sub(r"\[[xX]\]", "[ ]", ln.rstrip()) for ln in lines]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


# ---------- reading what GitHub holds -------------------------------------------------------------------

def index_issues(gh, repo):
    """ID tag -> issue, and title -> issue. Pull requests are not issues."""
    by_tag, by_title = {}, {}
    for it in gh.rest_all(f"repos/{repo}/issues?state=all"):
        if "pull_request" in it:
            continue
        m = TAG.match(it["title"])
        if m:
            by_tag.setdefault(m.group(1), it)
        by_title.setdefault(it["title"], it)
    return by_tag, by_title


def find(by_tag, by_title, iid, title):
    return by_tag.get(iid) or by_title.get(title)


# ---------- the run -----------------------------------------------------------------------------------------

class Run:
    def __init__(self, gh, repo, plan, epics, bodies, board=True, dry=False, log=print, sleep=time.sleep,
                 reseat=False):
        self.gh, self.repo, self.plan, self.epics, self.bodies = gh, repo, plan, epics, bodies
        self.board, self.dry, self.log, self.sleep = board, dry, log, sleep
        #  body item 4: a team that grows (2 -> 5 seats) re-runs /tickets; the plan's own fields are then set
        # again on every card - the options rewritten when one is missing (that resets those fields, and every card
        # is set again just after), never Status, which is the people's
        self.reseat = reseat
        self.made = {}           # ID -> the issue its create call returned: never re-found through the lagging list
        self.failed = {}         # ID -> why its create call failed
        self.created = {"milestones": 0, "labels": 0, "epics": 0, "tickets": 0, "sub_issues": 0,
                        "blocked_by": 0, "cards": 0}
        self.problems = []
        self.notes = []          # said in the output, never a failure (a board left as it is, and why)
        self.created_ticket_ids = set()
        self.elsewhere = set()   # issue numbers left under another epic, reported, never moved

    # --- what a plan needs ---
    def epic_title(self, e):
        return f"[{e['id']}] {e['name']}"

    def ticket_title(self, t):
        return f"[{t['id']}] {t['title']}"

    def epic_body(self, e):
        return (f"**Milestone:** {e['milestone']}\n**Lane:** `{e['lane']}`\n**Owner:** {e['owner']}\n\n"
                "The plan is in `TICKETS.md`. This epic's tickets are its sub-issues; GitHub counts the progress.\n")

    def labels_needed(self):
        need = {}
        for e in self.plan["epics"]:
            need[f"lane: {e['lane']}"] = LANE_COLOR
            need[f"owner: {e['owner'].lower()}"] = OWNER_COLOR
        return need

    # --- publish, in publishing.md's order: milestones -> labels -> epics -> tickets -> links -> cards ---
    def milestones(self):
        have = {m["title"]: m for m in self.gh.rest_all(f"repos/{self.repo}/milestones?state=all")}
        for m in self.plan["milestones"]:
            if m["title"] in have:
                continue
            self.created["milestones"] += 1
            if self.dry:
                continue
            payload = {"title": m["title"]}
            if m.get("due"):
                payload["due_on"] = f"{m['due']}T00:00:00Z"
            else:
                self.log(f"note: milestone {m['title']!r} has no date in #Plan - created without one")
            have[m["title"]] = self.gh.rest("POST", f"repos/{self.repo}/milestones", payload)
        return {t: m["number"] for t, m in have.items() if m}

    def labels(self):
        have = {l["name"] for l in self.gh.rest_all(f"repos/{self.repo}/labels")}
        for name, color in self.labels_needed().items():
            if name in have:
                continue
            self.created["labels"] += 1
            if not self.dry:
                self.gh.rest("POST", f"repos/{self.repo}/labels", {"name": name, "color": color})

    def _create(self, iid, payload):
        """One issue. Its number comes from this response, never from the list; a failed create is recorded
        and the run goes on - one issue that is not there never stops the others' links and cards."""
        try:
            it = self.gh.rest("POST", f"repos/{self.repo}/issues", payload)
        except RuntimeError as err:
            self.failed[iid] = str(err)[:200]
            return
        if it and it.get("number"):
            self.made[iid] = it

    def issues(self, ms, known=None):
        """Create every epic and ticket that does not exist. `known` (ID -> issue) counts as existing: the
        second pass passes what the first one resolved, so a list that lags never reads as 'to create'."""
        known = known or {}
        by_tag, by_title = index_issues(self.gh, self.repo)
        for e in self.plan["epics"]:
            if known.get(e["id"]) or find(by_tag, by_title, e["id"], self.epic_title(e)):
                self.log(f"Skipping [{e['id']}]: exists")
                continue
            self.created["epics"] += 1
            if not self.dry:
                self._create(e["id"], {
                    "title": self.epic_title(e), "body": self.epic_body(e), "milestone": ms[e["milestone"]],
                    "labels": [f"lane: {e['lane']}", f"owner: {e['owner'].lower()}"]})
        for t in self.plan["tickets"]:
            if known.get(t["id"]) or find(by_tag, by_title, t["id"], self.ticket_title(t)):
                self.log(f"Skipping [{t['id']}]: exists")
                continue
            e = self.epics[t["epic"]]
            self.created["tickets"] += 1
            self.created_ticket_ids.add(t["id"])
            if not self.dry:
                self._create(t["id"], {
                    "title": self.ticket_title(t), "body": self.bodies[t["id"]], "milestone": ms[e["milestone"]],
                    "labels": [f"lane: {e['lane']}", f"owner: {e['owner'].lower()}"]})

    def resolve(self, retry=True):
        """ID -> issue (None when not found), after every epic and ticket exists. An issue this run created is
        taken from its create response; the rest from the issue list, re-read with backoff while anything is
        still missing (GitHub's list lags a fresh issue by seconds)."""
        wanted = [(e["id"], self.epic_title(e)) for e in self.plan["epics"]] +                  [(t["id"], self.ticket_title(t)) for t in self.plan["tickets"]]
        out = {iid: self.made.get(iid) for iid, _ in wanted}
        delays = list(LIST_RETRIES) if retry and not self.dry else []
        while True:
            if all(out.values()):
                return out
            by_tag, by_title = index_issues(self.gh, self.repo)
            for iid, title in wanted:
                out[iid] = out[iid] or find(by_tag, by_title, iid, title)
            if all(out.values()) or not delays:
                return out
            self.sleep(delays.pop(0))

    def sub_issues(self, iss):
        for e in self.plan["epics"]:
            if not iss.get(e["id"]):
                continue
            n = iss[e["id"]]["number"]
            listed = {s["number"] for s in self.gh.rest_all(f"repos/{self.repo}/issues/{n}/sub_issues")}
            for t in [t for t in self.plan["tickets"] if t["epic"] == e["id"]]:
                it = iss.get(t["id"])
                if not it or it["number"] in listed:
                    continue
                parent = self.gh.rest("GET", f"repos/{self.repo}/issues/{it['number']}/parent", missing_ok=True)
                if parent:
                    self.log(f"[{t['id']}] already sits under #{parent['number']} - left there "
                             f"(moving it is an owner-confirmed regroup)")
                    self.problems.append(f"[{t['id']}] is under #{parent['number']}, not [{e['id']}]")
                    self.elsewhere.add(it["number"])
                    continue
                self.created["sub_issues"] += 1
                if not self.dry:
                    self.gh.rest("POST", f"repos/{self.repo}/issues/{n}/sub_issues", {"sub_issue_id": it["id"]})

    def blocked_by(self, iss):
        for t in self.plan["tickets"]:
            it = iss.get(t["id"])
            if not it or not t.get("depends_on"):
                continue
            have = {b["number"] for b in self.gh.rest_all(
                f"repos/{self.repo}/issues/{it['number']}/dependencies/blocked_by")}
            for d in t["depends_on"]:
                blocker = iss.get(d)
                if not blocker or blocker["number"] in have:
                    continue
                self.created["blocked_by"] += 1
                if not self.dry:
                    self.gh.rest("POST", f"repos/{self.repo}/issues/{it['number']}/dependencies/blocked_by",
                                 {"issue_id": blocker["id"]})

    # --- the Delivery Board ---
    def project(self):
        owner, name = self.repo.split("/")
        title = f"{self.plan['product']} — Delivery Board"
        q = ("query($o:String!,$n:String!){repository(owner:$o,name:$n){id}"
             " repositoryOwner(login:$o){id ... on User{projectsV2(first:100){nodes{id number title}}}"
             " ... on Organization{projectsV2(first:100){nodes{id number title}}}}}")
        d = self.gh.graphql(q, {"o": owner, "n": name})
        found = [p for p in d["repositoryOwner"]["projectsV2"]["nodes"] if p["title"] == title]
        if found:
            return found[0]["id"], d["repository"]["id"], False
        if self.dry:
            return None, d["repository"]["id"], True
        p = self.gh.graphql("mutation($o:ID!,$t:String!){createProjectV2(input:{ownerId:$o,title:$t})"
                            "{projectV2{id number}}}", {"o": d["repositoryOwner"]["id"], "t": title})
        pid = p["createProjectV2"]["projectV2"]["id"]
        self.gh.graphql("mutation($p:ID!,$r:ID!){linkProjectV2ToRepository(input:{projectId:$p,repositoryId:$r})"
                        "{repository{id}}}", {"p": pid, "r": d["repository"]["id"]})
        return pid, d["repository"]["id"], True

    def fields(self, pid):
        d = self.gh.graphql("query($p:ID!){node(id:$p){... on ProjectV2{fields(first:50){nodes{"
                            "... on ProjectV2SingleSelectField{id name options{id name description}}}}}}}",
                            {"p": pid})
        return {f["name"]: f for f in d["node"]["fields"]["nodes"] if f}

    def items(self, pid):
        out, cursor = {}, None
        while True:
            d = self.gh.graphql(
                "query($p:ID!,$c:String){node(id:$p){... on ProjectV2{items(first:100,after:$c){"
                "pageInfo{hasNextPage endCursor} nodes{id content{... on Issue{number repository{nameWithOwner}}}"
                " fieldValues(first:20){nodes{... on ProjectV2ItemFieldSingleSelectValue{name"
                " field{... on ProjectV2SingleSelectField{name}}}}}}}}}}", {"p": pid, "c": cursor})
            page = d["node"]["items"]
            for it in page["nodes"]:
                c = it.get("content") or {}
                if c.get("repository", {}).get("nameWithOwner", "").lower() == self.repo.lower():
                    vals = {v["field"]["name"]: v["name"] for v in it["fieldValues"]["nodes"] if v and v.get("field")}
                    out[c["number"]] = {"id": it["id"], "values": vals}
            if not page["pageInfo"]["hasNextPage"]:
                return out
            cursor = page["pageInfo"]["endCursor"]

    def ensure_options(self, pid, fields, name, wanted, has_cards, desc=None):
        """A missing field is created; a missing option is added only while no card is on the board - the
        API rewrites every option to add one, which would wipe values already set. `desc` gives an option its
        description (the Seat options say what the seat is: senior/junior, person/agent - )."""
        f = fields.get(name)
        desc = desc or {}
        old = {o["name"]: o.get("description") or "" for o in (f or {}).get("options", [])}
        opt = lambda n: {"name": n, "color": "GRAY", "description": desc.get(n) or old.get(n, "")}
        if not f:
            if not self.dry:
                self.gh.graphql("mutation($p:ID!,$n:String!,$o:[ProjectV2SingleSelectFieldOptionInput!]!)"
                                "{createProjectV2Field(input:{projectId:$p,dataType:SINGLE_SELECT,name:$n,"
                                "singleSelectOptions:$o}){projectV2Field{... on ProjectV2SingleSelectField{id}}}}",
                                {"p": pid, "n": name, "o": [opt(w) for w in wanted]})
            return
        have = [o["name"] for o in f["options"]]
        missing = [w for w in wanted if w not in have]
        stale = [n for n in have if desc.get(n) and desc[n] != old.get(n)]
        if not missing and stale and has_cards:
            self.notes.append(f"board field {name!r}: option(s) {stale} do not say what the seat is - cards exist, so "
                              f"it is left (rewriting the options resets every card's {name}); add the description "
                              f"on the board: " + "; ".join(f"{n} = {desc[n]}" for n in stale))
            return
        if not missing and not stale:
            return
        if not missing:
            if not self.dry:
                self.gh.graphql("mutation($f:ID!,$o:[ProjectV2SingleSelectFieldOptionInput!]!){updateProjectV2Field("
                                "input:{fieldId:$f,singleSelectOptions:$o}){projectV2Field{... on ProjectV2SingleSelectField{id}}}}",
                                {"f": f["id"], "o": [opt(n) for n in have]})
            return
        if has_cards:
            self.problems.append(f"board field {name!r} has no option {missing} and cards already exist - add "
                                 f"the option on the board, then run /tickets again (adding it here would reset "
                                 f"every card's {name}); the seats or lanes changed on purpose: run this command "
                                 f"again with --reseat (it sets every card's Owner, Lane and Seat again; Status stays)"
                                 if name != "Status" else
                                 f"the option on the board, then run /tickets again (adding it here would reset "
                                 f"every card's {name})")
            return
        if not self.dry:
            self.gh.graphql("mutation($f:ID!,$o:[ProjectV2SingleSelectFieldOptionInput!]!){updateProjectV2Field("
                            "input:{fieldId:$f,singleSelectOptions:$o}){projectV2Field{... on ProjectV2SingleSelectField{id}}}}",
                            {"f": f["id"], "o": [opt(n) for n in have + missing]})

    def cards(self, iss):
        pid, _, new = self.project()
        if self.dry and new:
            self.created["cards"] = len(self.plan["tickets"])
            return None
        existing = self.items(pid)
        lanes = sorted({e["lane"] for e in self.plan["epics"]})
        f = self.fields(pid)
        for name, wanted in (("Status", STATUS_OPTIONS), ("Owner", OWNER_OPTIONS), ("Lane", lanes),
                             ("Seat", plan_seats(self.plan))):
            self.ensure_options(pid, f, name, list(wanted), bool(existing) and not (self.reseat and name != "Status"),
                                (self.plan.get("seat_info") or {}) if name == "Seat" else None)
        f = self.fields(pid)
        if self.reseat and existing and not self.dry:
            existing = self.items(pid)  # a rewritten option list cleared those fields: read the cards again
        for t in self.plan["tickets"]:
            it = iss.get(t["id"])
            if not it:
                continue
            card = existing.get(it["number"])
            if not card:
                self.created["cards"] += 1
                if self.dry:
                    continue
                d = self.gh.graphql("mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c})"
                                    "{item{id}}}", {"p": pid, "c": it["node_id"]})
                card = {"id": d["addProjectV2ItemById"]["item"]["id"], "values": {}}
            # Set only what is unset: a Status someone moved to In Progress is theirs, never reset to Todo.
            want = {"Status": "Todo", **self.planned(t)}
            todo = {k: v for k, v in want.items() if not card["values"].get(k)
                    or (self.reseat and k != "Status" and card["values"].get(k) != v)}
            if not todo or self.dry:
                continue
            parts, vars_ = [], {"p": pid, "i": card["id"]}
            for k, (name, value) in enumerate(todo.items()):
                field = f.get(name)
                option = next((o for o in (field or {}).get("options", []) if o["name"] == value), None)
                if not option:
                    self.problems.append(f"[{t['id']}] board field {name!r} has no option {value!r}")
                    continue
                vars_[f"f{k}"], vars_[f"o{k}"] = field["id"], option["id"]
                parts.append(f"s{k}:updateProjectV2ItemFieldValue(input:{{projectId:$p,itemId:$i,fieldId:$f{k},"
                             f"value:{{singleSelectOptionId:$o{k}}}}}){{projectV2Item{{id}}}}")
            if parts:
                decl = "".join(f",$f{k}:ID!,$o{k}:String!" for k in range(len(todo)) if f"f{k}" in vars_)
                self.gh.graphql(f"mutation($p:ID!,$i:ID!{decl}){{{' '.join(parts)}}}", vars_)
        return pid

    def planned(self, t):
        """The board values a ticket's card must read: its epic's owner and lane, its lane's seat."""
        e = self.epics[t["epic"]]
        return {"Owner": e["owner"], "Lane": e["lane"], "Seat": epic_seat(self.plan, e)}

    def card_wrong(self, t, values):
        """What is wrong with one card: an unset Status, or an Owner, Lane or Seat that is not the plan's."""
        bad = [] if values.get("Status") else ["Status unset"]
        for k, v in self.planned(t).items():
            if values.get(k) != v:
                bad.append(f"{k} {values.get(k) or 'unset'} (planned {v})")
        return bad

    # --- verification.md §After publishing: each read back from GitHub, never assumed ---
    def read_back(self, iss, pid):
        verdict = {}
        # Every planned epic and ticket is an issue. One that is not is named; the rest are still checked.
        missing = [i for i, it in iss.items() if not it]
        verdict["issues"] = (not missing, f"{len(iss) - len(missing)} of {len(iss)} found")
        if missing:
            why = "; ".join(f"{i}: create failed - {self.failed[i]}" for i in missing if i in self.failed)
            self.problems.append(f"no issue found after publishing: {missing} - their links and cards were not "
                                 f"made; run the same command again once they show{' (' + why + ')' if why else ''}")
        # Epics are parents: each epic's sub-issues are exactly its planned tickets.
        subs_ok, n_subs = True, 0
        for e in self.plan["epics"]:
            if not iss.get(e["id"]):
                continue
            got = {s["number"] for s in self.gh.rest_all(f"repos/{self.repo}/issues/{iss[e['id']]['number']}/sub_issues")}
            want = {iss[t["id"]]["number"] for t in self.plan["tickets"] if t["epic"] == e["id"] and iss.get(t["id"])}
            if got != want - self.elsewhere:
                subs_ok = False
                self.problems.append(f"epic [{e['id']}] sub-issues {sorted(got)} != planned {sorted(want - self.elsewhere)}")
            n_subs += len(got)
        verdict["sub_issues"] = (subs_ok, f"{len(self.plan['epics'])} epics · {n_subs} sub-issues")
        # Dependencies are links: blocked_by is exactly Depends On, closed blockers included.
        deps_ok, n_links, n_iss = True, 0, 0
        for t in self.plan["tickets"]:
            if not iss.get(t["id"]):
                continue
            got = {b["number"] for b in self.gh.rest_all(
                f"repos/{self.repo}/issues/{iss[t['id']]['number']}/dependencies/blocked_by")}
            want = {iss[d]["number"] for d in t.get("depends_on", []) if iss.get(d)}
            if got != want:
                deps_ok = False
                self.problems.append(f"[{t['id']}] blocked by {sorted(got)} != Depends On {sorted(want)}")
            n_links += len(got)
            n_iss += 1
        verdict["blocked_by"] = (deps_ok, f"{n_iss} issues · {n_links} links")
        # Bodies are their files: every planned ticket's issue - created now or by an earlier run - returns its
        # committed file. One the list does not show yet is read on its own.
        fresh = {it["number"]: it for it in self.gh.rest_all(f"repos/{self.repo}/issues?state=all")
                 if "pull_request" not in it}
        found = [t for t in self.plan["tickets"] if iss.get(t["id"])]
        bad = []
        for t in found:
            n = iss[t["id"]]["number"]
            it = fresh.get(n) or self.gh.rest("GET", f"repos/{self.repo}/issues/{n}")
            if normalise(it["body"]) != normalise(self.bodies[t["id"]]):
                bad.append(t["id"])
        verdict["bodies"] = (not bad, f"{len(found)} bodies · {len(found) - len(bad)} equal")
        self.problems += [f"[{i}] body differs from its committed file" for i in bad]
        # Board: every ticket is a card, Status set, Owner, Lane and Seat as planned.
        if pid:
            items = self.items(pid)
            cards = [t for t in found if iss[t["id"]]["number"] in items]
            wrong = {t["id"]: self.card_wrong(t, items[iss[t["id"]]["number"]]["values"]) for t in cards}
            right = [i for i, w in wrong.items() if not w]
            ok = len(right) == len(found)
            verdict["board"] = (ok, f"{len(cards)} cards · {len(right)} with all four fields as planned")
            for t in found:
                if t["id"] not in wrong:
                    self.problems.append(f"board: [{t['id']}] has no card")
                elif wrong[t["id"]]:
                    self.problems.append(f"board: [{t['id']}] " + ", ".join(wrong[t["id"]]) +
                                         " - fix it on the board; the plan changed on purpose (new seats or lanes): "
                                         "run this command again with --reseat")
        return verdict

    # --- a read-back never seen failing proves nothing: break one of each, watch it go red, restore ---
    def set_value(self, pid, item_id, field, option_id):
        if option_id is None:
            self.gh.graphql("mutation($p:ID!,$i:ID!,$f:ID!){clearProjectV2ItemFieldValue(input:{projectId:$p,"
                            "itemId:$i,fieldId:$f}){projectV2Item{id}}}", {"p": pid, "i": item_id, "f": field})
        else:
            self.gh.graphql("mutation($p:ID!,$i:ID!,$f0:ID!,$o0:String!){s0:updateProjectV2ItemFieldValue(input:{"
                            "projectId:$p,itemId:$i,fieldId:$f0,value:{singleSelectOptionId:$o0}}){projectV2Item{id}}}",
                            {"p": pid, "i": item_id, "f0": field, "o0": option_id})

    def prove_seat(self, iss, pid):
        """Put one card in a seat its lane does not sit at (or clear it, with one seat), watch the board
        read-back go red, put the planned seat back, watch it go green."""
        t = next((t for t in self.plan["tickets"] if iss.get(t["id"])), None)
        seat = self.fields(pid).get("Seat") or {}
        card = self.items(pid).get(iss[t["id"]]["number"]) if t else None
        if not card or not seat:
            return []
        planned = self.planned(t)["Seat"]
        ids = {o["name"]: o["id"] for o in seat["options"]}
        other = next((n for n in ids if n != planned), None)
        self.set_value(pid, card["id"], seat["id"], ids[other] if other else None)
        red = bool(self.card_wrong(t, self.items(pid)[iss[t["id"]]["number"]]["values"]))
        self.set_value(pid, card["id"], seat["id"], ids.get(planned))
        green = not self.card_wrong(t, self.items(pid)[iss[t["id"]]["number"]]["values"])
        return [("seat", red and green)]

    def prove(self, iss, pid=None):
        results = []
        linked = [t for t in self.plan["tickets"] if iss.get(t["id"]) and iss.get(t["epic"])]
        if linked:
            t = linked[0]
            e_n, it = iss[t["epic"]]["number"], iss[t["id"]]
            order = [s["id"] for s in self.gh.rest_all(f"repos/{self.repo}/issues/{e_n}/sub_issues")]
            self.gh.rest("DELETE", f"repos/{self.repo}/issues/{e_n}/sub_issue", {"sub_issue_id": it["id"]})
            got = {s["number"] for s in self.gh.rest_all(f"repos/{self.repo}/issues/{e_n}/sub_issues")}
            red = it["number"] not in got
            self.gh.rest("POST", f"repos/{self.repo}/issues/{e_n}/sub_issues", {"sub_issue_id": it["id"]})
            pos = order.index(it["id"]) if it["id"] in order else -1
            if pos > 0:  # put it back where it was, so the epic keeps its build order
                self.gh.rest("PATCH", f"repos/{self.repo}/issues/{e_n}/sub_issues/priority",
                             {"sub_issue_id": it["id"], "after_id": order[pos - 1]})
            elif pos == 0 and len(order) > 1:
                self.gh.rest("PATCH", f"repos/{self.repo}/issues/{e_n}/sub_issues/priority",
                             {"sub_issue_id": it["id"], "before_id": order[1]})
            back = [s["id"] for s in self.gh.rest_all(f"repos/{self.repo}/issues/{e_n}/sub_issues")]
            results.append(("sub-issue", red and back == order))
        dep = next((t for t in self.plan["tickets"] if iss.get(t["id"]) and t.get("depends_on")
                    and iss.get(t["depends_on"][0])), None)
        if dep:
            n, b = iss[dep["id"]]["number"], iss[dep["depends_on"][0]]
            self.gh.rest("DELETE", f"repos/{self.repo}/issues/{n}/dependencies/blocked_by/{b['id']}")
            got = {x["number"] for x in self.gh.rest_all(f"repos/{self.repo}/issues/{n}/dependencies/blocked_by")}
            red = b["number"] not in got
            self.gh.rest("POST", f"repos/{self.repo}/issues/{n}/dependencies/blocked_by", {"issue_id": b["id"]})
            got = {x["number"] for x in self.gh.rest_all(f"repos/{self.repo}/issues/{n}/dependencies/blocked_by")}
            results.append(("blocked-by", red and b["number"] in got))
        two = [t for t in self.plan["tickets"] if iss.get(t["id"])][:2]
        if len(two) == 2 and normalise(self.bodies[two[0]["id"]]) != normalise(self.bodies[two[1]["id"]]):
            body = self.gh.rest("GET", f"repos/{self.repo}/issues/{iss[two[0]['id']]['number']}")["body"]
            results.append(("body", normalise(body) != normalise(self.bodies[two[1]["id"]])))
        if pid:
            results += self.prove_seat(iss, pid)
        for what, ok in results:
            if not ok:
                self.problems.append(f"prove: the {what} read-back did not go red when broken, or did not come back")
        return results


def publish(gh, repo, plan, epics, bodies, board=True, dry=False, log=print, sleep=time.sleep, reseat=False):
    r = Run(gh, repo, plan, epics, bodies, board, dry, log, sleep, reseat)
    ms = r.milestones()
    r.labels()
    r.issues(ms)
    if dry:
        iss = r.resolve()
        r.sub_issues(iss)
        r.blocked_by(iss)
        if board:
            r.cards(iss)
        return r, {}, [], None
    # An issue the list never shows is named at the end (exit 1); every issue that IS there still gets its
    # links and its card - one missing read-back never skips the steps that do not depend on it.
    iss = r.resolve()
    r.sub_issues(iss)
    r.blocked_by(iss)
    pid = r.cards(iss) if board else None
    verdict = r.read_back(iss, pid)
    # A proof breaks a link that read back present; over a red read-back there is nothing to break. A missing
    # issue is not such a read-back: the proofs run over the issues that are there.
    green = all(ok for k, (ok, _) in verdict.items() if k != "issues")
    proofs = r.prove(iss, pid) if green else []
    if not green:
        r.problems.append("prove: skipped - a read-back is already red")
    # A second run must create nothing: plan it again from what GitHub now holds, writing nothing. What this
    # run resolved counts as existing, so the list's lag never reads as 'to create'.
    second = Run(gh, repo, plan, epics, bodies, board, dry=True, log=lambda *_: None)
    second.milestones(); second.labels(); second.issues(ms, known=iss)
    second.sub_issues(iss); second.blocked_by(iss)
    if board:
        second.cards(iss)
    return r, verdict, proofs, second.created


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) > 1 or "--help" in argv or "-h" in args:
        print(__doc__)
        return 2
    dry, board, reseat = "--dry-run" in argv, "--no-board" not in argv, "--reseat" in argv
    try:
        plan, epics = load_plan(args[0]) if args else derive_plan(".")
        gh = GH()
        scopes = gh.auth_scopes()
        need = {"repo"} | ({"project"} if board else set())
        if scopes and not need <= scopes:
            raise Refused(f"the token lacks {sorted(need - scopes)} - run `gh auth refresh -s project`, or "
                          f"publish without the board (--no-board, said in the close)")
        code, out, _ = gh._run(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
        if code != 0 or not out.strip():
            raise Refused("no GitHub repository for this folder - never create one here; the local files stay")
        repo = out.strip()
        bodies = {t["id"]: committed_body(real_git, t["file"]) for t in plan["tickets"]}
    except Refused as e:
        print(f"REFUSED - nothing published: {e}")
        return 2
    r, verdict, proofs, second = publish(gh, repo, plan, epics, bodies, board, dry, reseat=reseat)
    c = r.created
    print(("DRY RUN - would create: " if dry else "created: ") + " · ".join(f"{v} {k}" for k, v in c.items()))
    for name, (ok, line) in verdict.items():
        print(f"{'OK  ' if ok else 'FAIL'} {name}: {line}")
    for what, ok in proofs:
        print(f"{'OK  ' if ok else 'FAIL'} prove {what}: red when broken, green when restored")
    if second is not None:
        extra = sum(second.values())
        print(f"{'OK  ' if extra == 0 else 'FAIL'} second pass: {extra} to create")
        if extra:
            r.problems.append(f"second pass would create {second}")
    for p in r.problems:
        print(f"  x {p}")
    for n in r.notes:
        print(f"  note: {n}")
    print(f"gh calls: {gh.calls}")
    report = {"repo": repo, "created": c, "verdict": {k: {"ok": v[0], "line": v[1]} for k, v in verdict.items()},
              "proofs": dict(proofs), "second_pass": second, "problems": r.problems, "gh_calls": gh.calls}
    if args:
        with open(args[0] + ".report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    return 1 if r.problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
