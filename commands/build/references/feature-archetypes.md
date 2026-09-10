# Feature archetypes — the rules that apply only to SOME features

> Loaded by `/build` **Step 2 · 3 (Code)**, on demand. Each cluster below applies only when the
> feature you are building IS that kind of thing — a gate, an async job, a latency fix, or code that
> touches a trust boundary. `SKILL.md` carries the trigger; this file carries the rules.
>
> Every rule here came from a real bug on a shipped project. The war story behind each
> `(case file: …)` pointer lives in `references/case-files-build.md` in the repo.

## §Gates

Trigger: **the feature is a GATE — a validator, quality check, policy engine, anything whose job is to say "no"** — ten rules, each from a real bug on a shipped project

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

## §Async jobs

Trigger: **the feature is an ASYNC JOB — work that outlives the request (spawn + poll, queue + callback)** — six rules, same provenance

1. **The job handle IS the money — the component that polls must be the component that spawns.** Pick ONE spawner; unattended processing = durable backend job store + server-side poller — built fully or deferred *explicitly*.
2. **Sign the handle you give the client.** HMAC it server-side binding `{tenant/project, resource, vendor-id, attempt}`; verification failure is a refusal, never a lookup.
3. **Persist each result the moment a poll finds it** — on persist FAILURE keep the job **pending with the same handle** so the next poll retries without re-paying.
4. **Know your vendor's timeout taxonomy.** "Pending" and "died by timeout" may share a type (Modal's `FunctionTimeoutError` *subclasses* `TimeoutError`) — catch the terminal one FIRST; surface refused handles as failed.
5. **A mid-batch action must merge, never replace** — a retry that resets the outstanding set abandons every other in-flight handle.
6. **A whole-set computation that runs on the FINAL batch reads the earlier batches from storage — so the loop must persist each batch BEFORE requesting the next.** Client-driven batching plus a persist-at-the-end write means the last call sees batches 1..n-1 as missing and emits a confidently wrong verdict; the single-batch tests all pass. (case file: The final-batch verdict)

## §Latency and concurrency

Trigger: **the feature is a LATENCY/CONCURRENCY fix — measure the staircase first, then expect MORE THAN ONE serializer:**

1. **A sync SDK call inside `async def` serializes the whole PROCESS, not just the request.** The equal-spaced staircase IS the diagnostic; fix = `asyncio.to_thread` + credential-keyed client cache, pinned by a timing test. (case file: The event-loop staircase)
2. **The code fix and the PLATFORM's concurrency setting are SEPARATE serializers producing the IDENTICAL symptom — re-measure after each layer, on the runtime the user runs.** The platform knob (`@modal.concurrent`) is config-driven; deployed re-measure is part of the exit criterion. (case file: The second serializer)

## §Trust boundaries and shared state

Trigger: the feature reads or writes anything **shared across tenants, cached, or produced by an**
**AI suggestion** — or takes a selector from the client.

- **Sharing state ACROSS tenants to share a benefit? "No tenant data in it" answers only READ leakage — ask who can WRITE it, and what part of its KEY a client controls.** A row every tenant reads, keyed partly by a client-supplied field, lets one tenant choose whose value to move; fix by resolving the key server-side from a closed set AND bounding how far any single contribution can move the shared value. (case file: The global row a client could aim at)
- **Caching a verdict into a DB column? THE COLUMN IS PART OF THE TRUST BOUNDARY — check who can WRITE it before you trust READING it.** RLS authorises the **row, not the column**; fix = backend-owned column or server-secret HMAC — **cache and guard are ONE mechanism**. (case file: The writable verdict column)
- **A service-role/admin DB client bypasses RLS on EVERY query — each service-role read must RE-STATE the scoping RLS would have applied, and a test must pin it.** Also regex-validate client fragments BEFORE raw query-builder strings. (case file: Service-role vs RLS)
- **An AI SUGGESTION and a user CONFIRMATION are different facts — keep them structurally distinct, not flag-distinct.** Confirmed value outside the auto-fill object; suggestions render as evidence; test: suggest-only leaves the confirmed slot EMPTY. (case file: Suggestion vs confirmation)
- **State that records a HUMAN decision gets ONE writer — the human path. An automation/pipeline path must never (re)write it, even to a "sensible default"; resolve absence at READ time instead.** A machine write that looks harmless on the first run silently destroys the user's choice on every re-run. (case file: The reset selection)
- **A client-supplied selector may only ever CHOOSE AMONG server-approved sets — never contribute content.** Validate against the server-side registry; enforce the closed set server-side. (case file: Intent as a set-selector)
- **Caching a computed verdict/result? Build the cache key by EXCLUSION, never by inclusion.** Hash the whole input minus volatile fields + thresholds + checker version + **the SHAPE of what it stores** (a cached verdict that gains a new field must MISS — an `extra="ignore"` model deserializes the old one cleanly and hash-matches forever) (pin: threshold/check/shape → MISS, rotated URL → HIT); **an explicit "Re-run / Refresh" affordance must BYPASS the cache — skip the READ, keep the WRITE**, force strictly coerced. (case file: The cached Re-run)
