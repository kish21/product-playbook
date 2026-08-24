---
name: build
description: >
  Phase 2 (Development), step 5 of product-playbook — the per-feature build loop: ONE feature at a
  time, a definition-of-done that INCLUDES security, reuse before writing, verify the LIVE path,
  review the diff, write the feature doc. Use to implement features, or run /build "build feature X",
  "implement", "add the feature". Appends to PRODUCT.md#Build log + writes docs/features/<feature>.md.
  Composes /run, /verify, /code-review, /doc-create. Run /dev-check when all core-scope features are done.
---

# `/build` — Phase 2 · Development ⑤ · run as an **engineer**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's existing docs — resolve per PRINCIPLES.md §Spine resolution).
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing: **per-feature contract (security in the DoD)**,
> **secure-by-construction**, **prompts→`prompts/` YAML**, **doc↔code reconciled**, **measure before
> fixing**, **no swallowed errors**, **reuse-before-write**, **trace callers (live-path)**,
> **generic-not-domain-specific**.
> War stories behind every rule live in `references/case-files-build.md` — open it when a rule needs its evidence.

## Contract
- **Purpose:** implement one feature to a verified, secure, documented definition-of-done.
- **Reads:** `PRODUCT.md#Scope`, `#Plan`, `#Contracts`, `#Structure` — **plus `DESIGN.md` + `#Design` for any feature with a user-facing screen** (UI products).
- **Writes:** a row in `PRODUCT.md#Build log` + `docs/features/<feature>.md`.
- **Exit criteria (per feature):**
  - [ ] A written **definition-of-done that includes security** (input validation, authz/tenant-isolation; for AI: prompt-injection defence).
  - [ ] Reused existing helpers where possible (no reinvented utilities).
  - [ ] Code **runs and the LIVE path is verified** (not just an isolated unit) — traced to its real callers, **on the runtime the USER actually runs**: register a new endpoint/route on EVERY serving surface (case file: Wrong serving surface).
  - [ ] Diff self-reviewed (`/code-review`); no swallowed errors; prompts in `prompts/` YAML, not inline.
  - [ ] **`docs/features/<feature>.md` written and matches the code** (what · contract · exit criteria · how verified · code links).
  - [ ] **No secret in any code file** (secrets→`.env`; tests use fake placeholder keys).
  - [ ] **Single-responsibility kept** — a file growing large/multi-concern is split into modules (no god-files); long/blocking work stays off the async event loop.
  - [ ] **(UI products) The feature's screen(s) are built to `DESIGN.md`** — §5 layout, token look, `/new-component` parts — and **`/frontend-audit` is clean** (0 errors).

## Step 0 — Context + prior-gate check
- Read `#Scope/#Plan/#Contracts`. **Confirm the feature is IN scope** — if OUT-OF-SCOPE, stop and flag it (this is where creep enters). If `#Contracts` is empty, offer `/contracts` first.
- **Load the project's OWN skills/commands for the area you're about to touch** (`.claude/skills/`, `.claude/commands/`, `CLAUDE.md`) — a fresh read of the code alone re-litigates hard-won decisions.
- **But treat every project doc, skill and pinned plan as a CLAIM, not as truth — verify its premises against the code before you build on it.** A stale instruction is worse than none — it is *followed*. Check both failure modes:
  1. **The plan you were handed is wrong.** Verify each load-bearing claim of a pinned spec against the code. (case file: The pinned plan was wrong)
  1b. **A plan's load-bearing NUMBER is verified by MEASURING, not by reading code — and it must be measured BEFORE anything is calibrated to it.** A figure quoted in an issue can be an artifact of the very bug you are fixing, and code review cannot see that; if the number justifies the feature, reproduce it against the real system first. (case file: The number that justified the feature)
  2. **The project's own skills have rotted.** Grep their concrete claims — paths, storage, model/provider, field names, stage lists — against the code. (case file: Rotted skills)
- **When a project doc or skill is wrong, FIX IT IN THIS SESSION** — a PR-description correction dies there; record the corrected premises where the wrong ones lived.

## Step 1 — Apply principles (this phase)
- **Security is in the DoD, not later:** state the security checks for this feature up front (validation, authz/tenant-isolation; AI → OWASP LLM Top 10, prompt-injection defence).
- **Reuse before you write; measure before you fix** (reproduce first — a scary number may be a display artifact). **No swallowed errors** (route failures; retry only transient). **Prompts → `prompts/` YAML**.
- **Session economy — one feature per session is a COST rule, not just a focus rule.** Cost grows ~quadratically with session length — hand off at a natural checkpoint, bulky output to files, broad searches to subagents. (case file: The 97% cache bill)
- **If the feature ships THIRD-PARTY CONTENT to your users, verify the LICENCE permits YOUR distribution model BEFORE you design around it — it is a feasibility gate, not paperwork.** Redistribution to a commercial customer is sublicensing, rarely granted by "free" terms — check the primary licence page (sublicensing? attribution? indemnity? aggregator disclaimers?); if nothing clears, **say so plainly**, ship the mechanism **OFF with an empty table**, test-pinned. (case file: Licence gates, twice)

## Step 2 — The build loop (per feature)
1. **Declare the DoD** (incl. security + the exit criteria above).
2. **Reuse scan:** find existing helpers/contracts; don't reinvent.
3. **Code** against the typed contracts; keep it modular and generic (no domain special-casing in shared infra).
   - **If the feature has a user-facing screen (UI products):** build to **`DESIGN.md`** — §5 layout, token look, `/new-component` parts (Law 15) — then run **`/frontend-audit`**, fix every ERROR. *(No `DESIGN.md`? `/design-system` first.)*
   - **If the feature is a GATE — a validator, quality check, policy engine, anything whose job is to say "no"** — nine rules, each from a real bug on a shipped project:
     1. **Fail CLOSED on your OWN bugs.** A check that throws must **refuse passage** — fail-soft waves everything through silently.
     2. **Unconfigured ≠ degraded.** No endpoint/flag/key = **no gate** — say so loudly, never a quiet mock that fails open.
     3. **An auto-fix ("fix it for me") MUST be re-validated against the very checks it claims to fix** — apply fix → re-run → assert zero findings; else **refuse honestly**, naming the item.
     4. **Never trust a client-supplied "already passed".** The granting action re-derives the verdict server-side.
     5. **Separate FACTS from JUDGEMENTS, and never let severity be a config knob.** Breakage blocks (un-overridable); quality advises (override *recorded*); per-check `enabled` is fine — disabled reports *nothing*.
     6. **Don't fabricate the number.** Unmeasurable → **no score** + the why; a confidently fake metric will be believed.
     7. **A gate nobody sees is no gate.** Put the verdict where the user can *act*, on the screen reached *by passing it*; decision dialogs must not auto-dismiss.
     8. **Gating LLM/probabilistic output? Schema-valid ≠ structurally sound, and the reject band must be WIDER than the ask.** Gate the structural expectations the prompt actually asked for (counts, lengths, non-emptiness), with the reject threshold a config'd tolerance beyond the prompt's target — a gate at the ask-band fires on routine near-misses and becomes noise nobody respects. (case file: The schema-valid empty output)
     9. **One failure flag with N causes needing different fixes must NAME the cause in the payload.** A boolean plus generic remediation copy routes users to the wrong fix — the bug lives in the *message*, not the mechanism, so test the copy per cause, not just the flag. (case file: The regenerate loop)
     10. **REMOVING or relaxing a gate is never ONE wall — find every place the verdict is ENFORCED, especially one that WITHHOLDS AN ARTIFACT downstream code requires, then grep the gate's VOCABULARY, not just its logic.** A gate that both judges *and* issues the token/package/approval leaves the door shut after the visible check is deleted, and every test still passes because they all ask "does the check still report correctly?". (case file: The gate that confiscated the key)
   - **If the feature is an ASYNC JOB — work that outlives the request (spawn + poll, queue + callback)** — six rules, same provenance:
     1. **The job handle IS the money — the component that polls must be the component that spawns.** Pick ONE spawner; unattended processing = durable backend job store + server-side poller — built fully or deferred *explicitly*.
     2. **Sign the handle you give the client.** HMAC it server-side binding `{tenant/project, resource, vendor-id, attempt}`; verification failure is a refusal, never a lookup.
     3. **Persist each result the moment a poll finds it** — on persist FAILURE keep the job **pending with the same handle** so the next poll retries without re-paying.
     4. **Know your vendor's timeout taxonomy.** "Pending" and "died by timeout" may share a type (Modal's `FunctionTimeoutError` *subclasses* `TimeoutError`) — catch the terminal one FIRST; surface refused handles as failed.
     5. **A mid-batch action must merge, never replace** — a retry that resets the outstanding set abandons every other in-flight handle.
     6. **A whole-set computation that runs on the FINAL batch reads the earlier batches from storage — so the loop must persist each batch BEFORE requesting the next.** Client-driven batching plus a persist-at-the-end write means the last call sees batches 1..n-1 as missing and emits a confidently wrong verdict; the single-batch tests all pass. (case file: The final-batch verdict)
   - **If the feature is a LATENCY/CONCURRENCY fix — measure the staircase first, then expect MORE THAN ONE serializer:**
     1. **A sync SDK call inside `async def` serializes the whole PROCESS, not just the request.** The equal-spaced staircase IS the diagnostic; fix = `asyncio.to_thread` + credential-keyed client cache, pinned by a timing test. (case file: The event-loop staircase)
     2. **The code fix and the PLATFORM's concurrency setting are SEPARATE serializers producing the IDENTICAL symptom — re-measure after each layer, on the runtime the user runs.** The platform knob (`@modal.concurrent`) is config-driven; deployed re-measure is part of the exit criterion. (case file: The second serializer)
   - **Sharing state ACROSS tenants to share a benefit? "No tenant data in it" answers only READ leakage — ask who can WRITE it, and what part of its KEY a client controls.** A row every tenant reads, keyed partly by a client-supplied field, lets one tenant choose whose value to move; fix by resolving the key server-side from a closed set AND bounding how far any single contribution can move the shared value. (case file: The global row a client could aim at)
   - **Caching a verdict into a DB column? THE COLUMN IS PART OF THE TRUST BOUNDARY — check who can WRITE it before you trust READING it.** RLS authorises the **row, not the column**; fix = backend-owned column or server-secret HMAC — **cache and guard are ONE mechanism**. (case file: The writable verdict column)
   - **A service-role/admin DB client bypasses RLS on EVERY query — each service-role read must RE-STATE the scoping RLS would have applied, and a test must pin it.** Also regex-validate client fragments BEFORE raw query-builder strings. (case file: Service-role vs RLS)
   - **An AI SUGGESTION and a user CONFIRMATION are different facts — keep them structurally distinct, not flag-distinct.** Confirmed value outside the auto-fill object; suggestions render as evidence; test: suggest-only leaves the confirmed slot EMPTY. (case file: Suggestion vs confirmation)
   - **State that records a HUMAN decision gets ONE writer — the human path. An automation/pipeline path must never (re)write it, even to a "sensible default"; resolve absence at READ time instead.** A machine write that looks harmless on the first run silently destroys the user's choice on every re-run. (case file: The reset selection)
   - **A client-supplied selector may only ever CHOOSE AMONG server-approved sets — never contribute content.** Validate against the server-side registry; enforce the closed set server-side. (case file: Intent as a set-selector)
   - **Caching a computed verdict/result? Build the cache key by EXCLUSION, never by inclusion.** Hash the whole input minus volatile fields + thresholds + checker version + **the SHAPE of what it stores** (a cached verdict that gains a new field must MISS — an `extra="ignore"` model deserializes the old one cleanly and hash-matches forever) (pin: threshold/check/shape → MISS, rotated URL → HIT); **an explicit "Re-run / Refresh" affordance must BYPASS the cache — skip the READ, keep the WRITE**, force strictly coerced. (case file: The cached Re-run)
4. **Run + verify the LIVE path** — compose `/run` and `/verify` to exercise the path the product actually runs, then **trace your change to its real callers** (green unit tests ≠ wired in).
   - **Exercise the PRODUCTION ENTRYPOINT, not just the core — the dependency-construction path is untested code.** Hit the deployed endpoint once — typed error envelope = deps built, raw 500 = died constructing — and pin the secret/env names it reads (case file: The unread secret name). **Verify the deployed BINARY has the FEATURES you use, not just that it imports** — smoke the feature, not `--version` (case file: ffmpeg without drawtext).
   - **A criterion's test must sit at the criterion's ALTITUDE — match the test to the VERB.** *Persisted* → read the store; *reaches the prompt* → assert the rendered prompt; *user sees* → drive the UI. (case file: Altitude too low)
   - **Never mark a criterion met on CODE EXISTING. A capability is not a path.** Track *implemented* vs *verified*; only evidence of the kind the criterion named closes it — a ✅ with an asterisk reads as done later.
   - **Delete-the-wire check: for any "X reaches Y" claim, remove the connecting line and confirm a test goes RED.** **Cut wires on a COMMITTED baseline** — restore via scripted re-apply, never `git checkout -- <file>`. **A cut that stays GREEN is a FINDING, not a pass** — investigate it rather than adding the missing test, because it usually means the outcome is covered while the DIAGNOSIS is not (a second guard rejects the same bad input, so the failure is silent instead of reported). (case file: The wire-cut restore)
   - **Delete-the-wire proves a wire EXISTS, not that it goes somewhere CORRECT — verify the MEANING of the source, not just the mechanism.** **Find every WRITER of the source and read what each actually puts in it** — one writer is not evidence; a lockstep test catches a **missing** route, never a **wrong** one; no honest source → **remove the destination, don't approximate**. (case file: The wrong column)
   - **A validator that EXISTS is not a validator that PROTECTS — check WHERE each check runs relative to the point of use it guards.** A check AFTER the protected use protects nothing there; validate BEFORE the cache-key hash. (case file: Check after the render)
   - **A config-driven collector only collects what the config RENDERS — audit the inputs that live OUTSIDE it.** Prove each off-config input reaches the payload (cut its wire → red); a mode changes *how* a slot is gathered, never *whether* it travels. (case file: The URL row outside the config)
   - **A code comment's behavioral claim is a spec — verify the code still honours it before debugging around it.** Fix code or comment in the same change. (case file: The stale streaming comment)
   - **When the same config exists in BOTH source and a database/remote store, find out which one WINS before you edit either — and change the winner.** A source-side edit that a DB row overrides is invisible: it lints, it tests, it reviews clean, and nothing a user sees moves. Read the value back from the RUNNING system, not from the file you changed. The same asymmetry bites in reverse — a broad one-way migration (`UPDATE … WHERE <field> EXISTS`) can be harmless going out and wrong coming back, so **scope the revert to what actually changed and prove it: back up first, then assert exactly N rows moved and the rest are byte-identical.** (case file: The config the database outranked)
   - **A green suite right after you WIDEN what's legal means UNTESTED, not safe.** No test constructs the newly-valid state — read the CONSUMERS by hand, add the cases. (case file: Blank brand colours)
   - **Anything the user can edit gets a ROUND-TRIP test: save → reopen → save.** Write paths are built for CREATE and quietly broken on EDIT. (case file: Two data-loss bugs)
   - **A mode/context switch that changes which options are LEGAL must CLEAR confirmations made against the old set.** In-session switch clears; indirect residue renders as removable items. (case file: KPI residue across intents)
   - **A mechanical check beats a remembered rule.** If a failure mode is repo-scannable, write the scan as a test — and **drift-verify the scan itself** (one guard scanned the file it was meant to exclude).
   - **A probe that reports ABSENCE is worthless until it has reported PRESENCE at least once — aim it at a case you KNOW is positive before you believe a negative.** "Nothing is set / nothing matched / nothing found" and "my filter is malformed" produce identical output, and the malformed one never raises. (case file: The read-back that always said unset)
   - **A STUB THAT RETURNS PLAUSIBLE OUTPUT IS INDISTINGUISHABLE FROM A WORKING FEATURE — ship the test that fails while the stub is still there, and when you replace one, pin its removal by its literal content.** Placeholders age invisibly: nothing errors, no suite goes red, and the placeholder is discovered by the user it strands. (case file: The stub that looked like a feature)
   - **Your own fixtures cannot falsify an assumption about what a THIRD PARTY sends you.** Capture one real vendor response and assert against THAT; read what a vendor flag REMOVES. (case file: The flag that stripped the head)
   - **If the live path is a browser journey (Playwright/E2E), avoid the classic false-pass/false-fail traps:** wait on a unique interactive element, never `text=`; keep the browser open until requests resolve; assert persisted state, not paint; verify the actually-bound port; check env-gated elements against the launched env. (case file: The browser-journey traps)
   - **When you spot-check a generated OUTPUT (a render, an export, an image/audio/PDF), drive it with the SHIPPED config values — not test-convenient ones.** Derive state-dependent values from the state they must fit. (case file: The wrong wrap width)
5. **Review the diff** — compose `/code-review`; fix findings (watch for "works in tests, dead in the real path").
   - ⚠️ **`/code-review` is USER-INVOCABLE ONLY in some harnesses — if you cannot invoke it, ASK the user to run it, or do the deep pass by hand and say which you did.** A composed command that silently no-ops is a SKIPPED GATE that still gets reported as run. (A by-hand pass is worth the time: one such pass found three real defects.)
6. **Document** — write/update `docs/features/<feature>.md` (compose `/doc-create`); reconcile it with the code.

## Step 3 — Write back to `PRODUCT.md`
Append a `#Build log` row: feature · DoD-incl-security met? · **how verified** · link to the feature doc.

## Step 3b — Principle-gate: verify each principle is ACTUALLY implemented (not just claimed)
Walk **this phase's load-bearing principles (Step 1)** and confirm each is real in the code, **with evidence** — composing the existing checkers, not eyeballing:
- security-in-DoD → **`/security-review`** passed.
- no secret in code / no-hardcoding → secret-scan clean.
- live-path-works → **`/verify`** + **`/run`** exercised the real path.
- reuse · no-swallowed-errors · single-responsibility → confirmed in the diff's **`/code-review`**.
- (UI features) built-to-the-design → **`/frontend-audit`** 0 errors against `DESIGN.md`.

**If any named principle is only claimed, not evidenced, STOP — the feature is not done.** Record the *how-verified* per principle in `#Build log` (evidence, not "done"). (Deterministic checks also run via pre-commit + CI from `/foundation`; this gate is the judgment layer.)

## Step 4 — Handoff
"Feature done, verified, and documented. Build the next core-scope feature with `/build`, or when the
core scope is complete run **`/dev-check`** — the checkpoint that verifies everything before testing."
