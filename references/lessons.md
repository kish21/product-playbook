# LESSONS.md — what went wrong before, stated as rules

> Split out of `PRINCIPLES.md` at v1.29.0 alongside `MECHANISMS.md`. These are harvested from real
> projects rather than derived from a principle, they grow every time something breaks, and they are
> read on demand — which is exactly why they must not sit in the file every session loads verbatim.
> §Lesson format is the rule that governs how the list above it is written, so the two travel together.
## §Lessons baked in (generalised from real project struggles)


Phrased generically so they apply to any project:

- **Dead config** — a setting silently overridden upstream, or applied as a no-op. Verify the value actually *flows* end-to-end.
- **Fail-loud on misconfig, fail-closed on security** — refuse to boot on insecure/known-constant defaults; secret-scan source.
- **No swallowed errors** — route failures explicitly (don't `print`+continue); retry only transient errors, never bare `Exception` (a silent failure looks healthy).
- **Measure/reproduce before fixing** — a scary number is often a *display/measurement artifact* (a 0–1 value read on a 0–10 scale; a matcher quirk), not the bug. Don't act on a guessed root cause.
- **Eval/benchmark integrity** — distinguish "blocked/errored/dropped" from "genuinely low quality", or the metrics lie.
- **Units/scale agree across boundaries** — confirm both sides agree on units/scale/shape when a value crosses a boundary.
- **Schema ↔ code consistency** — via migrations; a column the code reads must exist; CI bootstraps from the real schema.
- **Environment/platform gotchas** — cross-platform (stdout encoding, caches cleared between runs, corporate proxy/SSL); don't assume network egress.
- **Defer paid infra/features until a real trigger** — anti-creep at the infra level; record the trigger.
- **A check that cannot fail is worse than no check** — it stops anyone from looking. Break what a new check guards and watch it go red *before* trusting it; a green run over a page whose live total is silent to a screen reader, or a gate whose region regex matches nothing, both report the same "pass".
- **A decision nothing executes is deferred, not recorded** — four separate defects were one pattern: a phase recorded the runtime target, the design tokens, the frozen schemas and the project's agent rules, and no phase carried any of them into what runs. When a phase decides something, name the phase that executes it.
- **A pointer is an instruction to open the file** — a record naming `src/schemas/*` is not the contract; a phase that reads the record instead of the artefact fills the gap by inventing one.
- **Testable is not reachable** — an exit criterion can be perfectly verifiable and still require something no plan delivers (a public URL, a second device, another person). Name each prerequisite and the milestone that produces it.
- **Docs must match reality** — reconcile code ↔ docs; no false claims.
- **A guarantee that nothing executes decays silently** — an assertion file no runner reads drifts freely (a second schema, a required field missing) because the only thing ever compared is a name, so **gate its structure in CI, or scope the claim to what is actually checked** — overclaiming a guarantee is worse than not having one, it stops anyone going to look (case file: The 53 assertions nothing read).
- **A correct no-op must still leave a trace** — a guard that declines, a check that finds nothing, a job
  with no work to do: if it writes nothing, *"ran and found nothing"* is indistinguishable from *"never
  ran"*, and whatever orients from the output keeps proposing the same thing. One dated line, replaced
  not appended (§Declined runs is this rule applied to the playbook's own phases).
- **A rule the project does not apply to ITSELF is the one most likely to be broken** — the author knows
  the reasoning, so the file feels exempt from it; four instances shipped in one week here (a ~15KB prune
  rule in a 25.8KB file, a permitted bare override contradicting a required recorded one, a "name your
  target user" gate in a repo that named none, a skill count stale on the storefront). Audit the project
  against its own stated rules first — that list is free, specific, and nobody else will run it.
- **Proving a new check fails first is also a test of the FAILURE path** — the run that turns it red is
  usually the only time the error branch ever executes, so a crash there hides until the day something
  actually breaks (case: check 14's proof run died printing a `→` on a cp1252 console, inside the
  reporter, on the one code path that reports problems — invisible in Linux CI).
- **A heading is not a behaviour** — a section titled for a check (`prior-gate check`, `validation`,
  `retry`) is read by everyone as proof the check exists, so nobody looks inside; assert on the BODY
  in CI, or the title outlives the code that once backed it (case file: The gate that was only a heading).
- **Fresh-eyes review, but verify findings against the real code** — don't rubber-stamp an audit; some findings are already done or misdiagnosed.
- **Tests passing ≠ it works** — verify the path the product *actually runs*, not just the function in isolation; trace callers / cross-file wiring.
- **Every "done" records HOW it was verified** — evidence, not just "done".
- **Multi-tenant isolation at DB *and* app (defense-in-depth)** — one missing scope filter is a silent cross-tenant leak.
- **Policy-as-code: "parses" ≠ "governs"** — a syntactically-valid but ruleless policy (comments-only / zero statements) silently degrades to the engine's default (deny-all, or worse allow-all); load-validate that it defines ≥1 rule and fail-loud. Build the authz query from **escaped identifiers + structured request/entity objects**, never string-interpolated into policy text — a crafted name (tool/resource/role) is an injection point like SQL. Default-deny; any eval error / no-decision → **deny**.

## §Lesson format — rule up front, story in the case file


Skills are loaded verbatim into every session that runs them, so their size is a per-session cost
and an attention cost: a checklist of sharp one-liners gets followed; a wall of war stories gets
skimmed. Therefore every harvested lesson is written in two parts:

- **In the skill file:** the **bold one-line rule** plus at most one sentence of mechanism — enough
  to act on, nothing more.
- **In `references/case-files-<skill>.md`:** the full war story, verbatim, under its own heading,
  pointed to from the rule as `(case file: <heading>)`. Opened on demand, never auto-loaded.
- **A rule that applies only SOMETIMES moves into the skill's OWN `commands/<skill>/references/`, never into a case file.** A case file is repo-only evidence — `install.sh` does not ship it — so a rule parked there is gone for every installed user, while a directory-form skill's `references/` installs beside `SKILL.md` and is size-exempt precisely because it is opened on demand. (case file: The prune that would have deleted the rules)

Gardening cadence: roughly every 10 merged lessons (or when a skill file passes ~15KB), run a prune
pass — condense, merge overlapping rules, retire ones that stopped earning their place. A lesson
that can't be stated as one bold line isn't distilled enough to be a rule yet.
