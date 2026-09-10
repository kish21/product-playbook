# Case files — `PRINCIPLES.md`

War stories behind the one-line lessons in `PRINCIPLES.md` §Lessons baked in. Each heading is
pointed to from the rule as `(case file: <heading>)`. Opened on demand, never auto-loaded.

## The 53 assertions nothing read

This repo's own `VISION.md` claimed *"`evals/evals.json` proves each skill matches this VISION;
re-run on change."* Nothing read it. CI parsed the file for JSON validity and compared the **set of
skill names** against `commands/` — and never once looked at a `prompt` or an `expected_output`.
Fifty-three assertions, green forever. This is failure mode #3 from the repo's own README (*"I
relied on green tests while the app was dead in production"*), sitting inside the repo that
preaches against it.

The file did not merely go stale. It grew a **second schema**: six cases — the five `/tickets` cases
and `build-lane-mode` — had drifted to `assertions` + `expected_artifacts` and carried **no
`expected_output` at all**, the one field skill-creator's schema (`references/schemas.md`)
requires. They were merged, released and cached in three plugin versions without anything noticing,
**because the only field anything compared was a name.** Separately, `evals.json`'s own note
promised *"2-3 trigger/behaviour checks per skill"* while `contracts`, `dev-check` and `eval` each
shipped exactly one.

The overclaim was the active harm: it stopped anyone from going to look. A file described as a
guarantee is a file nobody audits.

The fix had two halves, and only one of them was cheap. **Structure** got a real gate —
`tools/check.py` check 8, run in CI on every case: required fields present and non-empty, unique
ids, list fields are lists, **no field name has drifted** (an allow-list, which is what caught
`assertions`), and at least two cases per skill. The gate was written first and run **red on all 15
pre-existing violations** before any data was touched, then mutation-tested per violation class
(duplicate id, blank required field, list field given a string, drifted field name, a skill dropped
to one case — each red with a distinct message). **Execution** was not fixed: running the cases
needs `claude plugin eval`, an API budget and tolerance for non-determinism across 56 LLM-judged
cases. So the *claim* was scoped instead — `VISION.md` now says CI gates the file's **structure**,
not its verdicts, and that a green build means the assertions are **well-formed, not met**, with
the execution half left standing as an open item in `docs/lane-mode.md`.

That is the shape of the lesson: when you cannot afford to run the thing, you can still gate its
structure, and you must shrink the sentence that describes it down to what is actually checked.

**The same shape elsewhere:** *the absence of a record reads as "fine"* — a phase that declines to
run leaves no trace, and a skipped step is indistinguishable from a step that passed.

## The gate that was only a heading

`/eval` shipped with `## Step 0 — Context + prior-gate check` from the day the phase template landed.
Fourteen sibling skills carried the same heading and, under it, an actual gate: *"if `#Scope` is
missing/empty, warn and offer `/scope` first (allow override)"*. `/eval` carried the heading and,
under it, a read: *"Read `#Vision/#Scope/#Plan` for the goal and `#Tests` for what's covered."*
Reading a section is not gating on it.

It surfaced on a real run (`~/Downloads/subscription-tracker`, 2026-09-08). The project was mid-Build:
two features in `#Build log`, `#Dev-complete` entirely unchecked, `#Tests` entirely empty. The user ran
`/eval` — three phases early. The run stopped, correctly. But it stopped on the agent's own judgement,
not because the skill asked; a run that scored the half-built product instead would have violated no
instruction in the file. The orientation the playbook exists to give — *"you are early, run `/dev-check`
then `/test` first"* — was never in the text.

Two things made it invisible for five releases:

1. **The heading answered the question.** Anyone auditing "does `/eval` gate?" greps for the gate's
   name, finds it, and stops. The title is the most convincing possible evidence that the behaviour
   exists, and it costs nothing to keep after the behaviour never arrived.
2. **An eval case asserted the missing behaviour.** `eval-declined-run-leaves-a-trace` states that
   `/eval` "finds `#Tests` (and `#Dev-complete`) empty, declines to measure" — a gate the skill body
   never specified. Nothing executes the eval cases, so the assertion sat there agreeing with the
   heading rather than contradicting the body.

The fix was one bullet in `/eval` and a CI check that reads the body, not the title: every phase skill
except `/vision` (which opens the chain) must name a prior `#Section` in Step 0 **and** offer an
override. Written before the fix, it went red on three skills, not one — `/build` named `/contracts`
with no override, and `/dev-check` had no prior-gate at all, so a checkpoint run over an empty
`#Build log` passed by having nothing to fail. The bug the ticket described was real; it was also
one instance of a class, and only a check that ignored headings could see the other two.
