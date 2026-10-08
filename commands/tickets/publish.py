#!/usr/bin/env python3
"""tickets publish engine - publishes a confirmed backlog to GitHub and reads every part of it back.

One command does what `references/publishing.md` §Mirror the plan structure onto GitHub, §Epics are parent
issues and §The Delivery Board describe, then runs `references/verification.md` §After publishing over what
GitHub now holds. It never creates a repository, never edits or closes an existing issue, never moves a
ticket between epics and never changes a board value someone already set.

Usage:  python publish.py <plan.json>                 publish, read back, prove, second pass
        python publish.py <plan.json> --dry-run       say what would be created; write nothing
        python publish.py <plan.json> --no-board      issues, links and labels only (no `project` scope)
Exit:   0 all read-backs green · 1 a read-back or a proof failed · 2 the run refused to start (pre-flight)

plan.json (written by /tickets from the CONFIRMED proposal, never from memory):
  {"product": "<name>", "seat": "SR1",
   "milestones": [{"title": "M1 - ...", "due": "YYYY-MM-DD" | null}],
   "epics":   [{"id": "M1-LOG", "name": "...", "milestone": "M1 - ...", "lane": "events", "owner": "Senior"}],
   "tickets": [{"id": "M1-LOG-01", "title": "...", "file": "docs/issues/M1-LOG-01_x.md",
                "epic": "M1-LOG", "depends_on": ["M1-..."]}]}
A ticket takes its milestone, lane and owner from its epic: every ticket of an epic shares its lane.
Portable: stdlib + the `gh` CLI. A report is written beside the plan as <plan>.report.json.
"""
import json, os, re, subprocess, sys, tempfile

TAG = re.compile(r"^\[([A-Za-z0-9-]+)\]")
STATUS_OPTIONS = ("Todo", "In Queue", "In Progress", "Done")
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
        plan = json.load(f)
    epics = {e["id"]: e for e in plan.get("epics", [])}
    ids = [e["id"] for e in plan.get("epics", [])] + [t["id"] for t in plan.get("tickets", [])]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise Refused(f"IDs appear more than once in the plan: {dup}")
    milestones = {m["title"] for m in plan.get("milestones", [])}
    for e in plan.get("epics", []):
        if e["milestone"] not in milestones:
            raise Refused(f"epic {e['id']} names milestone {e['milestone']!r}, which the plan does not list")
    known = {t["id"] for t in plan.get("tickets", [])}
    for t in plan.get("tickets", []):
        if t["epic"] not in epics:
            raise Refused(f"ticket {t['id']} names epic {t['epic']}, which the plan does not list")
        for d in t.get("depends_on", []):
            if d not in known:
                raise Refused(f"ticket {t['id']} depends on {d}, which the plan does not list")
    return plan, epics


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
    def __init__(self, gh, repo, plan, epics, bodies, board=True, dry=False, log=print):
        self.gh, self.repo, self.plan, self.epics, self.bodies = gh, repo, plan, epics, bodies
        self.board, self.dry, self.log = board, dry, log
        self.created = {"milestones": 0, "labels": 0, "epics": 0, "tickets": 0, "sub_issues": 0,
                        "blocked_by": 0, "cards": 0}
        self.problems = []
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

    def issues(self, ms):
        by_tag, by_title = index_issues(self.gh, self.repo)
        for e in self.plan["epics"]:
            if find(by_tag, by_title, e["id"], self.epic_title(e)):
                self.log(f"Skipping [{e['id']}]: exists")
                continue
            self.created["epics"] += 1
            if not self.dry:
                self.gh.rest("POST", f"repos/{self.repo}/issues", {
                    "title": self.epic_title(e), "body": self.epic_body(e), "milestone": ms[e["milestone"]],
                    "labels": [f"lane: {e['lane']}", f"owner: {e['owner'].lower()}"]})
        for t in self.plan["tickets"]:
            if find(by_tag, by_title, t["id"], self.ticket_title(t)):
                self.log(f"Skipping [{t['id']}]: exists")
                continue
            e = self.epics[t["epic"]]
            self.created["tickets"] += 1
            self.created_ticket_ids.add(t["id"])
            if not self.dry:
                self.gh.rest("POST", f"repos/{self.repo}/issues", {
                    "title": self.ticket_title(t), "body": self.bodies[t["id"]], "milestone": ms[e["milestone"]],
                    "labels": [f"lane: {e['lane']}", f"owner: {e['owner'].lower()}"]})

    def resolve(self):
        """ID -> issue, after every epic and ticket exists. An ID with no issue stops the links."""
        by_tag, by_title = index_issues(self.gh, self.repo)
        out = {}
        for e in self.plan["epics"]:
            out[e["id"]] = find(by_tag, by_title, e["id"], self.epic_title(e))
        for t in self.plan["tickets"]:
            out[t["id"]] = find(by_tag, by_title, t["id"], self.ticket_title(t))
        return out

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
                            "... on ProjectV2SingleSelectField{id name options{id name}}}}}}}", {"p": pid})
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

    def ensure_options(self, pid, fields, name, wanted, has_cards):
        """A missing field is created; a missing option is added only while no card is on the board - the
        API rewrites every option to add one, which would wipe values already set."""
        f = fields.get(name)
        opt = lambda n: {"name": n, "color": "GRAY", "description": ""}
        if not f:
            if not self.dry:
                self.gh.graphql("mutation($p:ID!,$n:String!,$o:[ProjectV2SingleSelectFieldOptionInput!]!)"
                                "{createProjectV2Field(input:{projectId:$p,dataType:SINGLE_SELECT,name:$n,"
                                "singleSelectOptions:$o}){projectV2Field{... on ProjectV2SingleSelectField{id}}}}",
                                {"p": pid, "n": name, "o": [opt(w) for w in wanted]})
            return
        have = [o["name"] for o in f["options"]]
        missing = [w for w in wanted if w not in have]
        if not missing:
            return
        if has_cards:
            self.problems.append(f"board field {name!r} has no option {missing} and cards already exist - add "
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
        seat = self.plan.get("seat", "SR1")
        f = self.fields(pid)
        for name, wanted in (("Status", STATUS_OPTIONS), ("Owner", OWNER_OPTIONS), ("Lane", lanes), ("Seat", [seat])):
            self.ensure_options(pid, f, name, list(wanted), bool(existing))
        f = self.fields(pid)
        for t in self.plan["tickets"]:
            it = iss.get(t["id"])
            if not it:
                continue
            e = self.epics[t["epic"]]
            card = existing.get(it["number"])
            if not card:
                self.created["cards"] += 1
                if self.dry:
                    continue
                d = self.gh.graphql("mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c})"
                                    "{item{id}}}", {"p": pid, "c": it["node_id"]})
                card = {"id": d["addProjectV2ItemById"]["item"]["id"], "values": {}}
            # Set only what is unset: a Status someone moved to In Progress is theirs, never reset to Todo.
            want = {"Status": "Todo", "Owner": e["owner"], "Lane": e["lane"], "Seat": seat}
            todo = {k: v for k, v in want.items() if not card["values"].get(k)}
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

    # --- verification.md §After publishing: each read back from GitHub, never assumed ---
    def read_back(self, iss, pid):
        verdict = {}
        # Epics are parents: each epic's sub-issues are exactly its planned tickets.
        subs_ok, n_subs = True, 0
        for e in self.plan["epics"]:
            if not iss.get(e["id"]):
                subs_ok = False
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
                deps_ok = False
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
        # Bodies are their files: every ticket this run created returns its committed file.
        fresh = {it["number"]: it for it in self.gh.rest_all(f"repos/{self.repo}/issues?state=all")
                 if "pull_request" not in it}
        bad = [t["id"] for t in self.plan["tickets"] if t["id"] in self.created_ticket_ids and iss.get(t["id"])
               and normalise(fresh[iss[t["id"]]["number"]]["body"]) != normalise(self.bodies[t["id"]])]
        n = len(self.created_ticket_ids)
        verdict["bodies"] = (not bad, f"{n} bodies · {n - len(bad)} equal")
        self.problems += [f"[{i}] body differs from its committed file" for i in bad]
        # Board: every ticket is a card with all four fields set.
        if pid:
            items = self.items(pid)
            full = [t["id"] for t in self.plan["tickets"] if iss.get(t["id"]) and iss[t["id"]]["number"] in items
                    and all(items[iss[t["id"]]["number"]]["values"].get(k) for k in ("Status", "Owner", "Lane", "Seat"))]
            on = sum(1 for t in self.plan["tickets"] if iss.get(t["id"]) and iss[t["id"]]["number"] in items)
            ok = len(full) == len(self.plan["tickets"])
            verdict["board"] = (ok, f"{on} cards · {len(full)} with all four fields")
            if not ok:
                self.problems.append("board: some ticket has no card or an unset field")
        return verdict

    # --- a read-back never seen failing proves nothing: break one of each, watch it go red, restore ---
    def prove(self, iss):
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
        for what, ok in results:
            if not ok:
                self.problems.append(f"prove: the {what} read-back did not go red when broken, or did not come back")
        return results


def publish(gh, repo, plan, epics, bodies, board=True, dry=False, log=print):
    r = Run(gh, repo, plan, epics, bodies, board, dry, log)
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
    iss = r.resolve()
    missing = [i for i, it in iss.items() if not it]
    if missing:
        r.problems.append(f"no issue found after publishing: {missing}")
        return r, {}, [], None
    r.sub_issues(iss)
    r.blocked_by(iss)
    pid = r.cards(iss) if board else None
    verdict = r.read_back(iss, pid)
    # A proof breaks a link that read back present; over a red read-back there is nothing to break.
    proofs = r.prove(iss) if all(ok for ok, _ in verdict.values()) else []
    if not proofs and all(ok for ok, _ in verdict.values()) is False:
        r.problems.append("prove: skipped - a read-back is already red")
    # A second run must create nothing: plan it again from what GitHub now holds, writing nothing.
    second = Run(gh, repo, plan, epics, bodies, board, dry=True, log=lambda *_: None)
    second.milestones(); second.labels(); second.issues(ms)
    second.sub_issues(iss); second.blocked_by(iss)
    if board:
        second.cards(iss)
    return r, verdict, proofs, second.created


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 2
    dry, board = "--dry-run" in argv, "--no-board" not in argv
    try:
        plan, epics = load_plan(args[0])
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
    r, verdict, proofs, second = publish(gh, repo, plan, epics, bodies, board, dry)
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
    print(f"gh calls: {gh.calls}")
    report = {"repo": repo, "created": c, "verdict": {k: {"ok": v[0], "line": v[1]} for k, v in verdict.items()},
              "proofs": dict(proofs), "second_pass": second, "problems": r.problems, "gh_calls": gh.calls}
    with open(args[0] + ".report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return 1 if r.problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
