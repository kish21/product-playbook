"""Behaviour tests for commands/tickets/publish.py against an in-memory GitHub (run by tools/check.py, check 48).

The fake answers the same REST paths and GraphQL operations the engine sends, including the two behaviours a
real board has that bite: a new project already has Status without `In Queue`, and rewriting a field's options
gives every option a new id, so values already set on cards are lost.
"""
import importlib.util, itertools, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("publish", ROOT / "commands" / "tickets" / "publish.py")
publish = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish)


class FakeGitHub:
    def __init__(self, repo="acme/app"):
        self.repo, self.calls = repo, 0
        self.ids = itertools.count(1000)
        self.issues, self.milestones, self.labels = {}, {}, set()
        self.subs, self.parent, self.blocked = {}, {}, {}
        self.projects, self.drop_sub_posts = {}, False

    # --- REST ---
    def rest(self, method, path, payload=None, missing_ok=False):
        self.calls += 1
        path = path.split("?")[0].replace(f"repos/{self.repo}/", "")
        by_id = {i["id"]: i for i in self.issues.values()}
        if path == "milestones" and method == "POST":
            m = {"title": payload["title"], "number": len(self.milestones) + 1, "due_on": payload.get("due_on")}
            self.milestones[m["title"]] = m
            return m
        if path == "labels" and method == "POST":
            self.labels.add(payload["name"])
            return {}
        if path == "issues" and method == "POST":
            n = len(self.issues) + 1
            i = {"number": n, "id": next(self.ids), "node_id": f"I_{n}", "title": payload["title"],
                 "body": payload["body"], "milestone": payload.get("milestone"), "labels": payload.get("labels")}
            self.issues[n] = i
            return i
        m = re.fullmatch(r"issues/(\d+)(/.*)?", path)
        if not m:
            raise AssertionError(f"unexpected {method} {path}")
        n, rest = int(m.group(1)), m.group(2) or ""
        if rest == "" and method == "GET":
            return self.issues[n]
        if rest == "/parent":
            p = self.parent.get(n)
            if p is None:
                if missing_ok:
                    return None
                raise RuntimeError("404")
            return self.issues[p]
        if rest == "/sub_issues" and method == "POST":
            if not self.drop_sub_posts:
                child = by_id[payload["sub_issue_id"]]["number"]
                self.subs.setdefault(n, []).append(child)
                self.parent[child] = n
            return {}
        if rest == "/sub_issue" and method == "DELETE":
            child = by_id[payload["sub_issue_id"]]["number"]
            self.subs[n].remove(child)
            self.parent.pop(child, None)
            return {}
        if rest == "/sub_issues/priority" and method == "PATCH":
            child = by_id[payload["sub_issue_id"]]["number"]
            lst = self.subs[n]
            lst.remove(child)
            if "after_id" in payload:
                lst.insert(lst.index(by_id[payload["after_id"]]["number"]) + 1, child)
            else:
                lst.insert(lst.index(by_id[payload["before_id"]]["number"]), child)
            return {}
        if rest == "/dependencies/blocked_by" and method == "POST":
            b = by_id[payload["issue_id"]]["number"]
            if b in self.blocked.setdefault(n, []):
                raise RuntimeError("422 Target issue has already been taken")
            self.blocked[n].append(b)
            return {}
        m2 = re.fullmatch(r"/dependencies/blocked_by/(\d+)", rest)
        if m2 and method == "DELETE":
            self.blocked[n].remove(by_id[int(m2.group(1))]["number"])
            return {}
        raise AssertionError(f"unexpected {method} {path}")

    def rest_all(self, path):
        self.calls += 1
        path = path.split("?")[0].replace(f"repos/{self.repo}/", "")
        if path == "issues":
            return [dict(i) for i in self.issues.values()]
        if path == "milestones":
            return list(self.milestones.values())
        if path == "labels":
            return [{"name": n} for n in self.labels]
        m = re.fullmatch(r"issues/(\d+)/(sub_issues|dependencies/blocked_by)", path)
        n, kind = int(m.group(1)), m.group(2)
        nums = self.subs.get(n, []) if kind == "sub_issues" else self.blocked.get(n, [])
        return [dict(self.issues[x]) for x in nums]

    # --- GraphQL (Projects v2) ---
    def graphql(self, q, v=None):
        self.calls += 1
        v = v or {}
        if "repositoryOwner" in q:
            nodes = [{"id": pid, "number": p["number"], "title": p["title"]} for pid, p in self.projects.items()]
            return {"repository": {"id": "R_1"}, "repositoryOwner": {"id": "U_1", "projectsV2": {"nodes": nodes}}}
        if "createProjectV2(" in q:
            pid = f"P_{len(self.projects) + 1}"
            self.projects[pid] = {"number": len(self.projects) + 1, "title": v["t"], "items": {},
                                  "fields": {"Status": {"id": "F_Status", "name": "Status",
                                                        "options": self._opts(["Todo", "In Progress", "Done"])}}}
            return {"createProjectV2": {"projectV2": {"id": pid, "number": 1}}}
        if "linkProjectV2ToRepository" in q:
            return {}
        if "fields(first:50)" in q:
            return {"node": {"fields": {"nodes": list(self.projects[v["p"]]["fields"].values())}}}
        if "items(first:100" in q:
            p = self.projects[v["p"]]
            nodes = []
            for iid, it in p["items"].items():
                vals = []
                for fname, oid in it["values"].items():
                    f = p["fields"][fname]
                    o = next((o for o in f["options"] if o["id"] == oid), None)
                    if o:  # an option id that no longer exists reads as unset, as on GitHub
                        vals.append({"name": o["name"], "field": {"name": fname}})
                nodes.append({"id": iid, "content": {"number": it["number"], "repository": {"nameWithOwner": self.repo}},
                              "fieldValues": {"nodes": vals}})
            return {"node": {"items": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": nodes}}}
        if "createProjectV2Field" in q:
            p = self.projects[v["p"]]
            p["fields"][v["n"]] = {"id": f"F_{v['n']}", "name": v["n"], "options": self._opts([o["name"] for o in v["o"]])}
            return {}
        if "updateProjectV2ItemFieldValue" in q:
            p = self.projects[v["p"]]
            for k in itertools.count():
                if f"f{k}" not in v:
                    break
                fname = next(f["name"] for f in p["fields"].values() if f["id"] == v[f"f{k}"])
                p["items"][v["i"]]["values"][fname] = v[f"o{k}"]
            return {}
        if "updateProjectV2Field(" in q:
            for p in self.projects.values():
                for f in p["fields"].values():
                    if f["id"] == v["f"]:
                        f["options"] = self._opts([o["name"] for o in v["o"]])  # new ids: old values are lost
            return {}
        if "addProjectV2ItemById" in q:
            p = self.projects[v["p"]]
            number = next(i["number"] for i in self.issues.values() if i["node_id"] == v["c"])
            iid = f"PVTI_{number}"
            p["items"][iid] = {"number": number, "values": {}}
            return {"addProjectV2ItemById": {"item": {"id": iid}}}
        raise AssertionError(f"unexpected graphql: {q[:80]}")

    def _opts(self, names):
        return [{"id": f"O_{next(self.ids)}", "name": n} for n in names]


PLAN = {
    "product": "App", "seat": "SR1",
    "milestones": [{"title": "M1 — First", "due": "2026-10-01"}],
    "epics": [{"id": "M1-AUTH", "name": "Sign in", "milestone": "M1 — First", "lane": "auth", "owner": "Senior"},
              {"id": "M1-FEED", "name": "The feed", "milestone": "M1 — First", "lane": "feed", "owner": "Junior"}],
    "tickets": [{"id": "M1-AUTH-01", "title": "Sign in with email", "file": "a.md", "epic": "M1-AUTH", "depends_on": []},
                {"id": "M1-AUTH-02", "title": "Sign out", "file": "b.md", "epic": "M1-AUTH", "depends_on": ["M1-AUTH-01"]},
                {"id": "M1-FEED-01", "title": "See the feed", "file": "c.md", "epic": "M1-FEED",
                 "depends_on": ["M1-AUTH-01"]}],
}
BODIES = {"M1-AUTH-01": "# Sign in\n- [ ] works\n", "M1-AUTH-02": "# Sign out\n", "M1-FEED-01": "# Feed\n"}


def run(gh, plan=PLAN, bodies=BODIES):
    epics = {e["id"]: e for e in plan["epics"]}
    return publish.publish(gh, gh.repo, plan, epics, bodies, board=True, dry=False, log=lambda *_: None)


def all_ok(verdict, proofs, second):
    return all(ok for ok, _ in verdict.values()) and all(ok for _, ok in proofs) and sum(second.values()) == 0


def main():
    fails = []

    def expect(cond, what):
        if not cond:
            fails.append(what)

    # 1. A fresh publish creates everything once, reads it all back green, proves each read-back can fail.
    gh = FakeGitHub()
    r, verdict, proofs, second = run(gh)
    fresh_calls = gh.calls
    expect(r.created == {"milestones": 1, "labels": 4, "epics": 2, "tickets": 3, "sub_issues": 3, "blocked_by": 2,
                         "cards": 3}, f"fresh publish created {r.created}")
    expect(all_ok(verdict, proofs, second) and not r.problems, f"fresh publish not green: {r.problems} {verdict} {proofs}")
    expect(len(proofs) == 3, f"expected three proofs (sub-issue, blocked-by, body), got {proofs}")
    expect(gh.subs.get(1) == [3, 4], f"the proof did not restore the epic's build order: {gh.subs.get(1)}")
    expect(gh.milestones["M1 — First"]["due_on"] == "2026-10-01T00:00:00Z", "the milestone lost its date")
    expect("owner: senior" in gh.labels and "lane: auth" in gh.labels, f"label spelling: {gh.labels}")
    expect(gh.issues[3]["body"] == BODIES["M1-AUTH-01"], "an issue body is not its committed file")

    # 2. A second real run creates nothing and stays green.
    r2, verdict2, proofs2, second2 = run(gh)
    expect(sum(r2.created.values()) == 0, f"re-run created {r2.created}")
    expect(all_ok(verdict2, proofs2, second2), f"re-run not green: {r2.problems}")

    # 3. A card someone moved to In Progress is never reset to Todo.
    p = next(iter(gh.projects.values()))
    status = p["fields"]["Status"]
    card = next(it for it in p["items"].values() if it["number"] == 3)
    card["values"]["Status"] = next(o["id"] for o in status["options"] if o["name"] == "In Progress")
    run(gh)
    expect(card["values"]["Status"] == next(o["id"] for o in status["options"] if o["name"] == "In Progress"),
           "a re-run reset a card's Status")

    # 4. A ticket already under another epic is reported and left there, never moved.
    gh4 = FakeGitHub()
    run(gh4)
    gh4.subs[1].remove(4); gh4.parent[4] = 2; gh4.subs[2].append(4)
    r4, v4, _, _ = run(gh4)
    expect(gh4.parent[4] == 2, "the engine moved a ticket between epics")
    expect(any("[M1-AUTH-02] is under #2" in x for x in r4.problems), f"the regroup was not reported: {r4.problems}")

    # 5. A link GitHub silently dropped turns the read-back red - the reason read-backs exist.
    gh5 = FakeGitHub()
    gh5.drop_sub_posts = True
    r5, v5, _, _ = run(gh5)
    expect(not v5["sub_issues"][0], "a dropped sub-issue link read back green")

    # 6. A body edited on GitHub after this run created it is caught.
    gh6 = FakeGitHub()
    orig = gh6.rest
    def edit_after_create(method, path, payload=None, missing_ok=False):
        out = orig(method, path, payload, missing_ok)
        if method == "POST" and path.endswith("/issues") and payload["title"].startswith("[M1-FEED-01]"):
            gh6.issues[out["number"]]["body"] = "someone typed here\n"
        return out
    gh6.rest = edit_after_create
    r6, v6, _, _ = run(gh6)
    expect(not v6["bodies"][0], "an edited body read back green")

    # 7. A ticked box is progress, not an edit.
    expect(publish.normalise("- [x] a  \r\n\n") == publish.normalise("- [ ] a"), "ticks or whitespace count as edits")

    # 8. A plan that names something it does not list is refused before anything is written.
    bad = {**PLAN, "tickets": PLAN["tickets"] + [{"id": "M1-X-01", "title": "x", "file": "x", "epic": "M1-NOPE",
                                                   "depends_on": []}]}
    import json, tempfile, os
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(bad, f)
    try:
        publish.load_plan(path)
        fails.append("a plan naming an unlisted epic was accepted")
    except publish.Refused:
        pass
    finally:
        os.unlink(path)

    # 9. A new lane on a board that already has cards is reported, never added by rewriting the options.
    gh9 = FakeGitHub()
    run(gh9)
    plan9 = {**PLAN, "epics": PLAN["epics"] + [{"id": "M1-PAY", "name": "Pay", "milestone": "M1 — First",
                                                "lane": "pay", "owner": "Senior"}],
             "tickets": PLAN["tickets"] + [{"id": "M1-PAY-01", "title": "Pay", "file": "d.md", "epic": "M1-PAY",
                                            "depends_on": []}]}
    r9, _, _, _ = run(gh9, plan9, {**BODIES, "M1-PAY-01": "# Pay\n"})
    p9 = next(iter(gh9.projects.values()))
    set_lanes = [it["values"].get("Lane") for it in p9["items"].values() if it["number"] != 7]
    lane_ids = {o["id"] for o in p9["fields"]["Lane"]["options"]}
    expect(all(x in lane_ids for x in set_lanes), "adding a lane wiped the lanes already set on cards")
    expect(any("has no option ['pay']" in x for x in r9.problems), f"the missing lane was not reported: {r9.problems}")

    # 10. The engine's calls stay bounded (one card mutation sets all four fields; ids come from one list).
    expect(fresh_calls < 100, f"a three-ticket publish used {fresh_calls} GitHub calls")

    return fails


if __name__ == "__main__":
    f = main()
    for x in f:
        print("x", x)
    print("OK" if not f else f"FAIL - {len(f)}")
    sys.exit(1 if f else 0)
