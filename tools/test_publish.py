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
        # GitHub's issue list lags a fresh issue: hide[n] = how many more list reads leave issue n out
        self.hide, self.lag_new, self.lose_response = {}, 0, set()

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
            self.hide[n] = self.lag_new
            tag = payload["title"][1:].split("]")[0]
            if tag in self.lose_response:  # created, but the response never came back - and the list never shows it
                self.hide[n] = float("inf")
                raise RuntimeError("gh api POST issues failed: HTTP 502 Bad Gateway")
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
            shown = []
            for n, i in self.issues.items():
                if self.hide.get(n, 0) > 0:
                    self.hide[n] -= 1
                    continue
                shown.append(dict(i))
            return shown
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
            p["fields"][v["n"]] = {"id": f"F_{v['n']}", "name": v["n"], "options": self._opts(
                [o["name"] for o in v["o"]], {o["name"]: o.get("description", "") for o in v["o"]})}
            return {}
        if "updateProjectV2ItemFieldValue" in q:
            p = self.projects[v["p"]]
            for k in itertools.count():
                if f"f{k}" not in v:
                    break
                fname = next(f["name"] for f in p["fields"].values() if f["id"] == v[f"f{k}"])
                p["items"][v["i"]]["values"][fname] = v[f"o{k}"]
            return {}
        if "clearProjectV2ItemFieldValue" in q:
            p = self.projects[v["p"]]
            fname = next(f["name"] for f in p["fields"].values() if f["id"] == v["f"])
            p["items"][v["i"]]["values"].pop(fname, None)
            return {}
        if "updateProjectV2Field(" in q:
            for p in self.projects.values():
                for f in p["fields"].values():
                    if f["id"] == v["f"]:
                        f["options"] = self._opts([o["name"] for o in v["o"]],  # new ids: old values are lost
                                                  {o["name"]: o.get("description", "") for o in v["o"]})
            return {}
        if "addProjectV2ItemById" in q:
            p = self.projects[v["p"]]
            number = next(i["number"] for i in self.issues.values() if i["node_id"] == v["c"])
            iid = f"PVTI_{number}"
            p["items"][iid] = {"number": number, "values": {}}
            return {"addProjectV2ItemById": {"item": {"id": iid}}}
        raise AssertionError(f"unexpected graphql: {q[:80]}")

    def _opts(self, names, descs=None):
        return [{"id": f"O_{next(self.ids)}", "name": n, "description": (descs or {}).get(n, "")} for n in names]


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


SLEPT = []


def run(gh, plan=PLAN, bodies=BODIES):
    epics = {e["id"]: e for e in plan["epics"]}
    return publish.publish(gh, gh.repo, plan, epics, bodies, board=True, dry=False, log=lambda *_: None,
                           sleep=SLEPT.append)


def seats_on_board(gh):
    """Issue number -> the Seat its card reads, and the Seat field's option names."""
    p = next(iter(gh.projects.values()))
    names = {o["id"]: o["name"] for o in p["fields"]["Seat"]["options"]}
    return ({it["number"]: names.get(it["values"].get("Seat")) for it in p["items"].values()},
            [o["name"] for o in p["fields"]["Seat"]["options"]])


# Two senior seats and a junior one: the lanes split over SR1, SR2 and JR1 - three seats, three options.
PLAN3 = {
    "product": "App", "seats": ["SR1", "SR2", "JR1"],
    "milestones": PLAN["milestones"],
    "epics": [{**PLAN["epics"][0], "seat": "SR1"}, {**PLAN["epics"][1], "seat": "JR1"},
              {"id": "M1-PAY", "name": "Pay", "milestone": "M1 — First", "lane": "pay", "owner": "Senior", "seat": "SR2"}],
    "tickets": PLAN["tickets"] + [{"id": "M1-PAY-01", "title": "Pay", "file": "d.md", "epic": "M1-PAY", "depends_on": []}],
}
BODIES3 = {**BODIES, "M1-PAY-01": "# Pay\n"}


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
    expect([w for w, _ in proofs] == ["sub-issue", "blocked-by", "body", "seat"],
           f"expected four proofs (sub-issue, blocked-by, body, seat), got {proofs}")
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

    # 11. The issue list lags every new issue: the created numbers come from the create calls, so every link
    #     and card is still made, the bodies are read on their own, and the second pass creates nothing.
    gh11 = FakeGitHub()
    gh11.lag_new = 3
    del SLEPT[:]
    r11, v11, p11, s11 = run(gh11)
    expect(all_ok(v11, p11, s11) and not r11.problems, f"a lagging list broke the publish: {r11.problems} {v11}")
    expect(r11.created["sub_issues"] == 3 and r11.created["blocked_by"] == 2 and r11.created["cards"] == 3,
           f"a lagging list skipped links or cards: {r11.created}")
    expect(SLEPT == [], f"the run waited for the list although every create returned its number: {SLEPT}")

    # 12. An issue a run did not create, missing from the first lists, is found by re-reading with backoff.
    gh12 = FakeGitHub()
    run(gh12)
    for n in gh12.issues:
        gh12.hide[n] = 2
    del SLEPT[:]
    r12 = publish.Run(gh12, gh12.repo, PLAN, {e["id"]: e for e in PLAN["epics"]}, BODIES, sleep=SLEPT.append,
                      log=lambda *_: None)
    iss12 = r12.resolve()
    expect(all(iss12.values()), f"the retry did not find the lagging issues: {iss12}")
    expect(SLEPT == [2, 4], f"the retry did not back off 2 s then 4 s: {SLEPT}")

    # 13. An issue the list never shows (its create response was lost): it is named, the run exits non-zero,
    #     and every other issue still gets its links and its card - never 0 of 48 again.
    gh13 = FakeGitHub()
    gh13.lose_response = {"M1-AUTH-02"}
    del SLEPT[:]
    r13, v13, p13, _ = run(gh13)
    expect(SLEPT == [2, 4, 8], f"the missing issue was not re-read 3 times with backoff: {SLEPT}")
    expect(not v13["issues"][0] and any("M1-AUTH-02" in x and "no issue found" in x for x in r13.problems),
           f"the missing issue was not named: {r13.problems}")
    expect(r13.problems, "a run with a missing issue would exit 0")
    expect(gh13.subs.get(1) == [3] and gh13.subs.get(2) == [5], f"the found tickets lost their epic: {gh13.subs}")
    expect(gh13.blocked.get(5) == [3], f"the found tickets lost their blocked-by link: {gh13.blocked}")
    seats13, _ = seats_on_board(gh13)
    expect(sorted(seats13) == [3, 5] and all(seats13.values()), f"the found tickets got no card: {seats13}")
    expect(v13["sub_issues"][0] and v13["blocked_by"][0] and v13["board"][0] and len(p13) == 4,
           f"the read-backs over the found issues did not run green: {v13} {p13}")

    # 14. Seats per lane: one Seat option per seat the plan names, each card at its lane's seat, all green.
    gh14 = FakeGitHub()
    r14, v14, p14, s14 = run(gh14, PLAN3, BODIES3)
    seats14, options14 = seats_on_board(gh14)
    expect(options14 == ["SR1", "SR2", "JR1"], f"a 3-seat plan made Seat options {options14}")
    expect(seats14 == {4: "SR1", 5: "SR1", 6: "JR1", 7: "SR2"}, f"cards not at their lane's seat: {seats14}")
    expect(all_ok(v14, p14, s14) and not r14.problems, f"a per-lane-seat publish not green: {r14.problems}")
    expect(("seat", True) in p14, f"the seat proof did not go red then green: {p14}")

    # 15. A card at the wrong seat turns the board read-back red (red when broken, green when restored), and
    #     a re-run never overwrites the seat someone set - it names it.
    p15 = next(iter(gh14.projects.values()))
    seat_ids = {o["name"]: o["id"] for o in p15["fields"]["Seat"]["options"]}
    card15 = next(it for it in p15["items"].values() if it["number"] == 7)
    card15["values"]["Seat"] = seat_ids["SR1"]
    r15, v15, _, _ = run(gh14, PLAN3, BODIES3)
    expect(not v15["board"][0], "a card at the wrong seat read back green")
    expect(any("[M1-PAY-01] Seat SR1 (planned SR2)" in x for x in r15.problems),
           f"the wrong seat was not named: {r15.problems}")
    expect(card15["values"]["Seat"] == seat_ids["SR1"], "a re-run overwrote a seat someone set")
    card15["values"]["Seat"] = seat_ids["SR2"]
    r15b, v15b, p15b, s15b = run(gh14, PLAN3, BODIES3)
    expect(all_ok(v15b, p15b, s15b) and not r15b.problems,
           f"the restored seat did not read back green: {r15b.problems}")
    #     The seat proof catches a read-back that only asks "is Seat set?" (the bug that let 48 cards sit at SR1).
    real_check = publish.Run.card_wrong
    publish.Run.card_wrong = lambda self, t, values: [k for k in ("Status", "Owner", "Lane", "Seat")
                                                     if not values.get(k)]
    try:
        _, _, p15c, _ = run(gh14, PLAN3, BODIES3)
    finally:
        publish.Run.card_wrong = real_check
    expect(("seat", False) in p15c, f"the seat proof passed a read-back that never compares the seat: {p15c}")

    # 16. An older plan: one plan-wide seat (or none) still publishes, every card at it.
    gh16 = FakeGitHub()
    plan16 = {k: v for k, v in PLAN.items() if k != "seat"}
    r16, v16, p16, s16 = run(gh16, plan16)
    seats16, options16 = seats_on_board(gh16)
    expect(options16 == ["SR1"] and set(seats16.values()) == {"SR1"} and all_ok(v16, p16, s16),
           f"a plan with no seats did not publish at SR1: {options16} {seats16} {r16.problems}")
    seats1, options1 = seats_on_board(gh)
    expect(options1 == ["SR1"] and set(seats1.values()) == {"SR1"}, f"a single-seat plan: {options1} {seats1}")

    # 17. A re-run compares EVERY planned ticket's body with its file, not only the ones it created.
    gh17 = FakeGitHub()
    run(gh17)
    gh17.issues[5]["body"] = "someone typed here\n"
    r17, v17, _, _ = run(gh17)
    expect(sum(r17.created.values()) == 0, f"re-run created {r17.created}")
    expect(v17["bodies"] == (False, "3 bodies · 2 equal"), f"a re-run did not compare existing bodies: {v17['bodies']}")
    expect(any("[M1-FEED-01] body differs" in x for x in r17.problems), f"the edited body was not named: {r17.problems}")

    # 18. A plan whose seats do not add up is refused before anything is written.
    pay2 = {"id": "M1-PAY2", "name": "Pay 2", "milestone": "M1 — First", "lane": "pay", "owner": "Senior", "seat": "SR1"}
    for bad_plan, why in (({**PLAN3, "seats": ["SR1", "SR2"]}, "a seat the seats list does not name"),
                          ({**PLAN3, "epics": PLAN3["epics"] + [pay2]}, "one lane at two seats")):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(bad_plan, f)
        try:
            publish.load_plan(path)
            fails.append(f"a plan with {why} was accepted")
        except publish.Refused:
            pass
        finally:
            os.unlink(path)

    # 19. #42 item 18: what each seat is (senior/junior, person/agent) rides on the board as the Seat option's
    #     description; a board that already has cards is never rewritten for it - it is a note, not a failure.
    gh19 = FakeGitHub()
    info = {"SR1": "senior · person", "SR2": "senior · agent", "JR1": "junior · agent, a person reviews its PRs"}
    r19, v19, p19, s19 = run(gh19, {**PLAN3, "seat_info": info}, BODIES3)
    descs = {o["name"]: o["description"] for o in next(iter(gh19.projects.values()))["fields"]["Seat"]["options"]}
    expect(descs == info, f"the Seat options do not say what each seat is: {descs}")
    expect(all_ok(v19, p19, s19) and not r19.problems, f"a publish with seat descriptions not green: {r19.problems}")
    r19b, v19b, _, _ = run(gh14, {**PLAN3, "seat_info": info}, BODIES3)
    seats19b, _ = seats_on_board(gh14)
    expect(any("do not say what the seat is" in n for n in r19b.notes) and not r19b.problems
           and all(seats19b.values()), f"a board with cards should get a note and keep its seats: {r19b.notes} "
                                       f"{r19b.problems} {seats19b}")

    # 20. #42 body item 4: the team grows (a new seat SR3 takes the pay lane) and /tickets runs again. Without
    #     --reseat the board is left and the new option is named with the flag that fixes it; with --reseat every
    #     card's Owner, Lane and Seat follow the plan again, the read-backs go green, and a Status someone moved stays.
    gh20 = FakeGitHub()
    run(gh20, PLAN3, BODIES3)
    p20 = next(iter(gh20.projects.values()))
    status20 = {o["name"]: o["id"] for o in p20["fields"]["Status"]["options"]}
    card20 = next(it for it in p20["items"].values() if it["number"] == 4)
    card20["values"]["Status"] = status20["In Progress"]
    plan20 = {**PLAN3, "seats": ["SR1", "SR2", "SR3", "JR1"],
              "epics": [e if e["id"] != "M1-PAY" else {**e, "seat": "SR3"} for e in PLAN3["epics"]]}
    r20, v20, _, _ = run(gh20, plan20, BODIES3)
    expect(any("--reseat" in x for x in r20.problems) and seats_on_board(gh20)[0][7] == "SR2",
           f"a new seat on a board with cards should be named with --reseat, the cards left: {r20.problems}")
    epics20 = {e["id"]: e for e in plan20["epics"]}
    r20b, v20b, p20b, s20b = publish.publish(gh20, gh20.repo, plan20, epics20, BODIES3, board=True, dry=False,
                                             log=lambda *_: None, sleep=SLEPT.append, reseat=True)
    seats20, options20 = seats_on_board(gh20)
    p20 = next(iter(gh20.projects.values()))
    status20 = {o["id"]: o["name"] for o in p20["fields"]["Status"]["options"]}
    card20 = next(it for it in p20["items"].values() if it["number"] == 4)
    expect("SR3" in options20 and seats20 == {4: "SR1", 5: "SR1", 6: "JR1", 7: "SR3"}
           and all_ok(v20b, p20b, s20b) and not r20b.problems,
           f"--reseat should move the pay card to SR3 and read back green: {seats20} {options20} {r20b.problems}")
    expect(status20.get(card20["values"].get("Status")) == "In Progress",
           f"--reseat must never touch a Status someone moved: {card20['values']}")

    return fails


if __name__ == "__main__":
    f = main()
    for x in f:
        print("x", x)
    print("OK" if not f else f"FAIL - {len(f)}")
    sys.exit(1 if f else 0)
