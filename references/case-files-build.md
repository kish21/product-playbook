# Case files — `/build`

War stories behind the rules in `commands/build.md`. Each heading is pointed to from the rule it
evidences as `(case file: <heading>)`. Stories are verbatim; where a rule's longer mechanism prose
was condensed in `build.md`, the full text is kept here under *Full rule context*.

### Wrong serving surface
*(Backs: the live-path exit criterion — verify on the runtime the USER actually runs.)*
A project often has several serving surfaces (deployed app, local dev shim/gateway, env-configured
URLs). A new endpoint/route must be registered on EVERY surface, and verifying only the surface you
deployed proves nothing about the one the user opens. Real instance: an endpoint live-verified on the
cloud 404'd for the owner, whose frontend pointed at a local shim missing the route.

### The pinned plan was wrong
*(Backs: Step 0 — "The plan you were handed is wrong.")*
Real instance: a pinned "target contract" asserted a provenance field didn't exist and required
collapsing two schemas to add it — the field **already existed**, one level coarser, and the actual
defect was that the consumer's slice didn't carry it. Verifying first turned a 2–3-session refactor
into a one-seam fix; the same doc also claimed a prior session had shipped a flag that was never
built, and listed the wrong destination for deferred work.

### Rotted skills
*(Backs: Step 0 — "The project's own skills have rotted.")*
Real instance: a repo's three most relevant skills each contradicted the shipped system — one said
the QC stage used "no LLM, schema check only" when it runs a vision judge; one listed brief fields
that had been deleted and told you to use a storage vendor the project migrated off; one said the LLM
reviewer was "blocking" when a locked decision made judgements explicitly non-blocking. Two of them
also contradicted **each other**. Following them would have re-added a deleted field, written to the
wrong bucket, and broken a locked architectural decision.

### The 97% cache bill
*(Backs: Step 1 — session economy.)*
Measured on a shipped project: 97% of a ~$2,900-API-equivalent month was cache re-reads from
600–900-call sessions; generated code was a few percent. The one-subtask policy existed the whole
time — it wasn't enforced, and nothing measured adherence.
*Full rule context:* every API call re-reads the full history, so a session that outgrows its subtask
is the single biggest token leak. Prefer handoff + fresh session at a natural checkpoint (or after a
long debugging detour closes, where `/compact` helps); keep bulky tool output (test logs, scrapes,
JSON dumps) in files rather than chat; delegate broad code searches to subagents that return
conclusions, not file dumps.

### Licence gates, twice
*(Backs: Step 1 — third-party content licences are a feasibility gate.)*
Real instances, same project, twice: a non-commercially-licensed image model needed an
`allow_noncommercial_models` gate; and a music-bed library where Pixabay grants no sublicensing
right, the free-music aggregators explicitly "cannot and does not license music", and CC0 offers no
indemnity — you're not buying the asset, you're buying someone to sue.
*Full rule context:* the moment your product *redistributes* the asset (or its output) to a customer
who then uses it commercially, you are sublicensing, and most "free"/"royalty-free" terms do not
grant that right. Check, in this order: (1) does the licence grant sublicensing / redistribution
inside a product, not just "use in your own work"? (2) is attribution required — and can your UI
actually carry it? (3) is there an indemnity, or does the licence disclaim all warranty? (4) is the
"source" an aggregator that disclaims licence accuracy — in which case its metadata is an unverified
claim you'd be reselling? Read the primary licence page, not your memory or a blog. Ask early — an
owner may pick an option on a wrong premise (yours included). Build the mechanism anyway if it is
config-driven (it's identical under every licensing outcome, so nothing is wasted) but ship it OFF
with an empty table, pin the off-state with a test, file the decision as its own issue, and do not
let the changelog/docs claim the gap is closed.

### The event-loop staircase
*(Backs: latency lesson 1 — sync SDK call inside `async def`.)*
Real instance: 5 concurrent signed-URL calls = 9.06s staircase; to_thread + credential-keyed cache →
0.38s, 24×.
*Full rule context:* measure the staircase before touching code (fire N concurrent, print
per-request start/end — end times at ~equal spacing IS the diagnostic). Kill per-request client
construction: cache the vendor client keyed by its credentials so rotation still lands — a fresh
client can cost seconds of TLS setup per request while a warm one answers in tens of ms. Pin with
timing tests: a fake client that `time.sleep`s, two calls via `gather`, assert wall < serial — the
delete-the-wire pin for concurrency.

### The second serializer
*(Backs: latency lesson 2 — the platform's concurrency setting.)*
Real instance: same feature — after the event-loop fix deployed, prod still stair-stepped ~0.7s
apart; one config-driven `@modal.concurrent` took 5 concurrent calls from a 2.70s staircase to 0.80s
overlapping.
*Full rule context:* serverless platforms often default to ONE input per container (Modal, Lambda
without reserved concurrency tuning): deploy a perfectly non-blocking handler and concurrent requests
still stair-step, queued above your event loop. A local verify cannot see this layer. Check the cost
model before turning the knob: input-concurrency usually REDUCES container fan-out (no idle cost) —
unlike warm pools, which cost money idle.

### The writable verdict column
*(Backs: a cached-verdict DB column is part of the trust boundary.)*
Real instance: an endpoint whose comment claimed "nothing the client says is trusted" — true of the
request BODY, false of the ROW.
*Full rule context:* row-level security (Supabase/Postgres RLS, most ORMs' row scoping) authorises
the row, not the column: the owner can usually PATCH *any* column on their own row straight through
the data API with their own token, and your frontend's field allowlist is no defence because the
attacker doesn't use your frontend. If a cache reads `verdict.hash == recomputed_hash → skip the
checks`, and the user can write `verdict`, they can self-grant a pass with zero checks run — and
forge whatever artifact the pass mints (handing them the hash in your own API response completes
it). The BEFORE-UPDATE trigger must reject non-service-role writes. Drop the guard and the cache
silently becomes the bypass — say so in both files.

### Service-role vs RLS
*(Backs: service-role reads must re-state the scoping RLS would have applied.)*
Real instance: an option-sets repo read with the service role — the RLS policy scoping rows to
`tenant_id IS NULL` existed and was silently irrelevant; the fix was re-stating the filter in the
repo query, intent-regex-guarded before the raw `.or_`, both test-pinned.
*Full rule context:* the service key authorises the *server process*, not the request: the row
policies you carefully wrote simply do not run. A service-role read of a shared/config table needs
its scope in the query itself (an explicit tenant filter, or `tenant_id IS NULL` for global rows);
because nothing structural enforces this, pin it with a test asserting the filter is present — a
remembered rule on the hottest code path is the one that gets dropped in a refactor. A PostgREST
`.or_(...)` filter is an injection surface exactly like SQL.

### Suggestion vs confirmation
*(Backs: an AI suggestion and a user confirmation are structurally distinct.)*
Real instance: enrichment ranked funnel-stage/KPI suggestions as badges; the confirmed value rode a
separate wire outside the auto-fill object + carried-suggestions state, test-pinned — so no future
prefill change can silently promote a guess into a user decision.
*Full rule context:* if a suggested value travels in the same field/object as a confirmed one and a
boolean says which it is, some merge/prefill/auto-fill path will eventually write the suggestion into
the confirmed slot — the type system was told they're the same thing. Only an explicit user action
moves one across.

### Intent as a set-selector
*(Backs: a client-supplied selector may only choose among server-approved sets.)*
Real instance: `intent` on suggest/enrich endpoints is a pure set-selector for per-intent KPI
options; `sanitize_choices` enforces the closed set server-side, so a forged intent yields at worst
another approved list, never attacker-authored KPIs in prompts or storage.
*Full rule context:* design it so the worst-case forgery is *a different admin-approved list* — drop
off-list values with a log line, dedupe, cap counts from config. The moment a selector can smuggle
content — an option label, a prompt fragment — it stops being a selector and becomes an injection
channel.

### The cached Re-run
*(Backs: cache key by exclusion; explicit Re-run must bypass the cache.)*
Real instance: a Discovery "Re-run" returned `cache_hit` with nothing in the UI saying so — and the
same cache, keyed on inputs alone with no logic version, kept serving pre-fix output after a deploy,
making a correct, test-verified fix look broken in the app.
*Full rule context:* a hand-picked allowlist of "the fields that matter" silently misses the next
field someone adds — and *"I forgot to add the new field to the hash"* is exactly how a stale PASS
gets served on broken input. A hash match computed server-side from current state is a *proof* the
verdict is unchanged, not a guess — that is what makes skipping the re-run safe, and it is a
different thing entirely from trusting a verdict the client handed you. A button that promises a
fresh answer and silently serves a stored one is an untrue affordance; the user's click is what
authorizes the spend. Coerce the force flag strictly (`payload.get("force") is True`) so a stringly
`"true"` can't silently burn money.

### The unread secret name
*(Backs: exercise the PRODUCTION ENTRYPOINT — dependency construction is untested code.)*
Real instance: a token-signing key derived from `SUPABASE_SERVICE_ROLE_KEY` — a name a key-migration
had disabled — read clean in review, passed 472 tests + a live GPU smoke, and 500'd the endpoint on
request #1, because every test injected the key and the smoke drove the GPU, so the entrypoint's
`secret()` call had literally never executed.
*Full rule context:* unit tests inject dependencies (a fake repo, a stub provider, a literal
`signing_key=…`); the production entrypoint *builds* them (reads secrets, constructs clients,
derives keys) and NONE of that runs under the tests. A single smoke of the deepest layer drives a
*different* layer. Hit the deployed/served endpoint once with a trivial request (even
unauthenticated — a clean typed error envelope proves the entrypoint built its deps and reached the
guard; a raw 500 means it died constructing them), and pin a test that the secret/env names the
entrypoint reads are exactly the ones the boot-guard/config requires, so a rename can't pass a green
boot and still crash.

### ffmpeg without drawtext
*(Backs: verify the deployed BINARY has the FEATURES you use.)*
Real instance: the John-Van-Sickle static ffmpeg is `7.0.2` with NO `drawtext` filter (JVS omits
libfreetype) — every caption/overlay assembly would 500 on the deployed function, while 472 tests +
a local ffmpeg + a local graph-validation all passed; the live smoke of the deployed image caught it,
and the fix was a BtbN build with freetype/fribidi/harfbuzz.
*Full rule context:* a pinned/static third-party binary (an ffmpeg, an image-magick, a pandoc) can
carry the right name and version yet be built *without an optional feature you depend on* — the
feature-set is a property of the *deployed* build, not the code. Smoke the ACTUAL feature
(`-filters | grep drawtext`, a one-frame render using it), not just `--version`.

### Altitude too low
*(Backs: a criterion's test must sit at the criterion's ALTITUDE.)*
Real instance: a criterion read "≥1 real product image persisted under the tenant prefix, surviving
reload". It was marked met on a unit test of the upload function — while the function that called it
was never invoked from anywhere, so no image was ever persisted. 900+ backend and 250+ frontend tests
stayed green; the feature was completely inert. The criterion had even NAMED its own verification
("integration on a real product page") and a weaker one was substituted.

### The wire-cut restore
*(Backs: delete-the-wire mechanics — cut wires on a COMMITTED baseline.)*
Real instance: a wire-cut restore reverted the very change under test; the red-test proof survived
but the fix had to be re-applied by hand.
*Full rule context:* if nothing goes red when the wire is cut, the claim is untested no matter how
many tests surround it — this is the only thing that distinguishes "the pieces exist" from "the
pieces are connected", the drift-verification rule applied to WIRING. `git checkout -- <file>`
restores HEAD and silently wipes an uncommitted fix along with the cut.

### The wrong column
*(Backs: delete-the-wire proves a wire EXISTS, not that it goes somewhere CORRECT.)*
Real instance: a scraped brand name was mapped from `projects.title` because one write path set
`title = productName`. Two others set `"{productName} — {intent}"` and
`"{source.title} — fork from {stage}"` — so a forked project's brand name would have become
"Acme — fork from story", flowing into the script, the captions and `correct_spelling`, the field
that drives TTS PRONUNCIATION. It passed review, passed a lockstep column↔contract test, and passed
delete-the-wire — cutting the line turned tests red, because the wire was real. It simply pointed at
the wrong column. Caught only by an adversarial read; the honest fix was a dedicated column, not a
cleverer read of the wrong one.
*Full rule context:* a name describes what a field is *called*, never what every path *stores* in
it; the other writers are where the bug is. A field-map/lockstep test catches a missing route and can
never catch a wrong one, so do not let it stand in for judgement; and when the correct source does
not exist yet, remove the destination field rather than approximating it — contract surface with no
honest source will be re-plumbed wrongly by the next person.

### Check after the render
*(Backs: check WHERE each check runs relative to the point of use it guards.)*
Real instance: a selector field was re-validated “at the merge” against its closed vocabulary — and
the merge ran after the LLM prompt was rendered, so a client-forged value still reached the prompt
while the sibling audit marked the field ✅. Found only when a review agent asked “at what LINE does
the sibling's check run?”; the fix moved the check before the render — and before the cache-key hash,
so forged values could not mint cache entries either.
*Full rule context:* schema/construction-time checks cover everything downstream; a check inside a
later processing step covers only what runs after it — while reading as covered in every audit that
only asks *does a check exist?* Sanitizing after the hash caches the verdict under the dirty input.

### The URL row outside the config
*(Backs: a config-driven collector only collects what the config RENDERS.)*
The same disease wears three coats: a field asked by only 2 of 25 mode×mission combinations, an
AI-inferred value binned because the current mode renders no box for it, and a page's SINGLE core
input (a URL row rendered outside the config array) saved as NULL on every create while its value sat
on screen. Real instance: the URL-paste fast path of a product ran enrichment on the pasted URL,
displayed everything — and persisted `product_url = NULL` on create, proven against the live DB;
downstream stages that re-crawl the URL silently had nothing to crawl. Green suite throughout: every
test exercised rendered fields.
*Full rule context:* enumerate every input surface that is not in the config list (a fixed row
hard-coded in the page, a value a background fetch produced, state copied in from another mode) and
prove each one reaches the payload — an altitude test on the real mode's field list. A missing box
means route the value directly (or leave the slot honestly blank), not drop it.

### The stale streaming comment
*(Backs: a code comment's behavioral claim is a spec.)*
Real instance: a restore path's comment said "thumbnails appear as their URLs arrive" — the
implementation used `Promise.allSettled`, so nothing rendered until the SLOWEST of five slow requests
returned (~15-20s), which users read as "my images are gone". Data, requests and responses were all
verified correct before anyone re-read the comment against the code.
*Full rule context:* all-or-nothing on the slowest request is a latency bug wearing a correctness
costume — if N parallel fetches feed a display, render each result as it arrives.

### Blank brand colours
*(Backs: a green suite right after you WIDEN what's legal means UNTESTED.)*
Real instance: allowing brand colours to be blank left 977 tests green; hand-reading the consumers
found an image-prompt builder that nested the accent inside `if primary:` and silently dropped the
only colour that had been measured.
*Full rule context:* making a previously-impossible state valid (a field may now be empty, a list may
now be shorter, an enum gained a member) cannot break tests that never construct that state — the
green is evidence about the old world only.

### Two data-loss bugs
*(Backs: anything the user can edit gets a ROUND-TRIP test.)*
Real instance: two separate data-loss bugs in one feature — values shown to the user and never saved,
then values saved but destroyed the moment the user reopened and re-saved.
*Full rule context:* a field in the create payload but missing from the update allowlist; state
cleared on restore and then written back as empty — one round-trip test (save → reopen → save)
catches the whole class.

### KPI residue across intents
*(Backs: a context switch that changes which options are LEGAL must clear old confirmations.)*
Real instance: per-intent KPI options — switching the mission mid-session clears confirmed KPIs
(test-pinned), while a cross-intent duplicate's leftover KPIs render as removable chips instead of
silently persisting into a context that never offered them.
*Full rule context:* values confirmed under the previous set are unvalidated residue — keeping them
silently ships choices the new context never offered; dropping them silently loses user input. The
switch the user performs *in-session* clears (they watched it happen); residue arriving *indirectly*
(duplicate, restore, fork) renders as visible, removable items so the user decides. This is the
round-trip rule's cross-context sibling; no single-context test can catch it.

### The flag that stripped the head
*(Backs: your own fixtures cannot falsify an assumption about what a THIRD PARTY sends you.)*
Real instance: a scraper called with `onlyMainContent: true` to strip nav/footer boilerplate — the
same flag strips `<head>`, so `<link rel=stylesheet>` and `<meta property="og:image">` never arrived.
A whole brand-colour feature shipped, deployed, and could NEVER have worked; 900+ tests passed
because every fixture was hand-written HTML that included a `<head>`, and a local diagnostic using
plain HTTP had one too. Two real customer URLs, not one, were needed before the pattern was visible.
*Full rule context:* unit tests feed the parser markup *you wrote*, so they prove your code handles
the input you imagined — never that the vendor actually delivers it. Save one real vendor response as
a fixture, or write a diagnostic calling the live vendor with your production options. Corollary:
when two consumers want opposite things from one payload (trimmed content for extraction, full
document for metadata), request both formats rather than picking one and hoping.

### The browser-journey traps
*(Backs: Playwright/E2E false-pass/false-fail traps — each cost a real debugging round on a shipped project.)*
Anchor waits on a **unique interactive element** (`getByRole('button', {name: …})`), never `text=` —
Playwright `text=` is a case-insensitive substring match and will fire on incidental copy (a heading
wait matched a sidebar step label); **keep the browser open until every in-flight request resolves**
— closing the page mid-request cancels the local server's HTTP handler and can strand server-side
state mid-write; and when the app has long (>1 min) backend calls, assert on the **persisted state
after completion** (DB row/API read-back), not just what's painted, so the pass is evidence not
theater. **Also verify the server you're actually hitting**: dev servers silently bind a FALLBACK
port when the default is taken (Vite 5173→5175 when another instance runs) — read the bound port from
the server's own startup output and align the test BASE URL *and* any CORS allowlist to it; and when
an **env-gated UI element** (a button behind a feature-flag env var) comes back "missing", first
confirm the instance under test was launched with those env vars — the element being absent on a
*different* running instance is the classic false-fail.

### The wrong wrap width
*(Backs: spot-check generated output with the SHIPPED config values.)*
Real instance: captions wrapped at a hard-coded 42 chars; a pre-merge visual check used
`wrap_chars=28` (which fit a 704px portrait frame) but the code SHIPPED `42` — every real render
clipped the caption off both edges, because the check exercised a different config than production.
Fixes: validate at the shipped value, and make the wrap width-aware —
`fit = width·(1-2·margin)/(font·glyph_ratio)` — so it can't overflow any frame.
*Full rule context:* read the value from the real config the way the running code reads it (or
better, build the validation payload from the same config loader). When the output depends on config
that interacts with runtime state — a fixed line-wrap width vs the actual frame width, a page size vs
the paper, a font size vs the box — a fixed constant that "looked fine once" is fragile; derive it
from the state it must fit.

### The schema-valid empty output
*(Backs: gate rule 8 — schema-valid ≠ structurally sound; reject band wider than the ask.)*
Real instance: a generation stage used schema-enforced structured output, so every response was
"valid" — but the schema put no minimum on a list field and no length expectation on the prose
field. A draft with zero list entries and a ten-word body passed, was wrapped as a healthy
(non-degraded) result, and the downstream stage that expanded those entries silently emitted
nothing. The review gate only fired on provider FAILURE, so a structurally empty success sailed
past it. Fix: a post-generation structural check of exactly what the prompt asked for (entry
count, word-count band), routing misses into the same degraded→human-review path a provider
failure gets — draft kept so the reviewer sees why. The calibration that made it a gate instead
of noise: the prompt's target band is the ASK; the reject line is a config'd tolerance factor
beyond it (clamped ≥1 so a bad knob degrades to the exact band rather than dividing by zero),
because models routinely land near-misses on counts and a gate that pauses every run gets
ignored or disabled.

### The regenerate loop
*(Backs: gate rule 9 — one failure flag with N causes must name the cause in the payload.)*
Real instance: a generation stage's single `degraded` boolean accumulated three causes over time —
provider outage (placeholder served), structural quality shortfall (real draft kept, off-target),
and blank upstream inputs (the model invented content to fill the holes). Every surface showed the
same generic copy: "degraded — review and regenerate." For the third cause that advice is actively
harmful: regenerating re-runs the same blank inputs, so the user loops forever while the actual fix
lives one stage upstream (complete the missing fields). The flag itself was well-tested; no test
ever asserted the MESSAGE matched the cause, and the defect was only caught by a fresh-eyes ship
review asking "what does the user read, and is it true for every path that sets this flag?" Fix:
the result payload names the cause (the list of blank fields), and each surface routes to the
right remediation — the pipeline pause-note and the UI toast name the fields and point at the
upstream stage, while the other causes keep the regenerate copy. The test additions pin the note
text per cause at the caller's altitude, not just the boolean.

### The reset selection

A generation stage produced four variants and the user could pick one; the pick was persisted in
its own column. The pipeline's automated runner, on every run, persisted the fresh variants AND
`selected_index=0` — reasonable-looking on the first run (someone has to pick a default), fatal on
every re-run: regeneration silently snapped the user's deliberate choice back to variant 1 with no
signal. The sibling stage never had the bug — its runner simply never wrote its selection column —
so the asymmetry itself was the finding. The fix made the write optional (`None` = column
untouched), removed the automation write entirely, and moved the default to READ time: every
reader already resolved an absent index to variant 0, so the first run still landed on the hero
variant without any writer having to say so. The test that pins it sits at the storage altitude:
the UPDATE payload sent to the DB must not CONTAIN the column when no explicit selection is being
made — asserting the call args alone would miss a repo layer that "helpfully" fills the default
back in.


## The final-batch verdict

A GPU-synthesis endpoint capped how many items one request could process and handed the leftovers
back as `meta.remaining`; the client looped until the list came back empty. A new feature added a
whole-set computation to that endpoint — a verdict spanning EVERY item, using this batch's freshly
measured values merged over the values already persisted on the row. It ran only on the final
batch, on the reasoning that a mid-batch verdict would just be rewritten by the next call. That
reasoning was right, and the implementation was still wrong: the page persisted measurements once,
AFTER the whole loop finished. So on any set larger than one batch, the final call looked at
batches 1..n-1, found nothing persisted, and emitted a confident refusal — "N items have no
measurement yet, regenerate them" — whose suggested fix re-spent the money and refused again. A
second manifestation was quieter: on a re-run, the final batch's verdict mixed fresh values for
its own items with the PREVIOUS run's stale values for every earlier one, so the verdict looked
successful while being computed from audio that no longer existed.

Every test passed. The suite covered the single-batch happy path, the honest refusal, the subset
regeneration and the mid-batch omission — but nothing exercised the FINAL call of a multi-batch
run, which is the only place the bug lives. The fix was one line in the client loop (persist this
batch before requesting the next, which doubles as crash insurance for work already paid for) plus
a test that drives the real two-call protocol end to end: first call returns `remaining` and no
verdict, the measurements are persisted, the second call's verdict spans every item.

The generalisable shape: **when a server-side computation spans the whole set but runs on one
batch, its inputs for the other batches come from storage — so "when does the client persist?" is
part of that computation''s contract, not a client detail.** Write the batched protocol down and
test the last call, not just the first.


## The number that justified the feature

A tracked issue opened with a crisp piece of arithmetic: the text-to-speech voice reads at ~1.3
words per second, the generation prompt asks for ~2, so every script is written half again too long
and the quality gate blocks it after the money is spent. That number survived into a plan, a memory
note, a config default and several code comments. It was the reason the feature existed.

It was wrong. The same session was also fixing an off-by-one in how scenes were numbered — labels
added a `+1` to an index that was already 1-based, so every message named the scene after the one it
meant. The issue's "~1.3 w/s" had been computed by dividing one scene's word count by the NEXT
scene's audio length: an artifact of exactly the bug being fixed, quoted as the evidence for a
different fix. Measured against the real audio, the voice read at 2.58 w/s — *faster* than the
prompt's assumption. The real defect was a single scene carrying 31 words in a 7-second slot, which
no voice could have delivered.

Nothing in the code could have revealed this. Every claim about the code was true: the estimators
really did disagree, the counters really were duplicated, the prompt really did hardcode a rate. The
only thing that could falsify the number was running the real system against real data — and that
happened late, during the live verify, *after* the conservative default had already been calibrated
to 1.4 w/s. That default would have shipped scripts too short to fill the ad, in the opposite
direction from the bug it was meant to fix.

Two things follow. **Measure the premise before you calibrate to it** — if a number justifies the
work, reproducing it is part of Step 0, not part of the final verification. And **when the measured
value contradicts the plan, fix the record everywhere it was copied to** — the issue, the config
comment, the design doc, the changelog — and state the corrected claim plainly, including the part
where the feature is now worth less than it was sold as. The honest version here was: the ask and
the check now come from one measured number instead of two unverified constants, which is a
correctness win, not the 2x saving the issue promised.

## The global row a client could aim at

A feature needed to know how fast a given text-to-speech voice actually speaks, so it measured every
synthesis and accumulated the result in a table keyed by `(provider, voice, language)`. The table
was deliberately global rather than per-tenant: a voice's speed is a property of the voice, so the
first customer to use it calibrates it for everyone and nobody starts uncalibrated.

The design doc argued this was safe, and gave a reason that sounded complete: the table holds only
counts and durations — no names, no text, no tenant identifier — so there is nothing to leak. That
reasoning is true and it covers exactly one direction. It never asks whether one tenant can WRITE
into the number every other tenant reads.

They could. The request handler carefully stamped the provider and voice from server config, because
those select which paid vendor tier runs — but `language` was passed through from the client, and it
was the third component of the key. So a caller could aim its writes at the precise row everyone
else reads, or mint new ones with an arbitrary string, and the values being accumulated derived from
content that same caller controlled. No data crossed a boundary; the damage was that other tenants'
generations would be built on a number quietly dragged off true, which is close to undiagnosable
from their side.

The obvious one-line fix — stamp `language` from config like the other identity fields — was wrong
for a reason worth remembering: that field also reached the synthesis engine, so hard-stamping it
would have silently switched a live project's audio to a different locale. **A field can be an
identity key in one place and a functional setting in another; fix the key, not the field.** The
shipped fix mapped the tag through a closed, config-owned set when computing the key (a client may
choose among approved values, never contribute one) and added a plausibility bound so a single batch
outside a believable range is discarded rather than banked — which covers broken input, a
mis-measured batch and a deliberate skew identically, so intent never has to be guessed.

The residual was accepted and written down: a tenant can still contribute *plausible* values, which
is the entire point of sharing. Per-tenant rows were rejected as the cure being worse than the
disease.

## The stub that looked like a feature

A page on a shipped project carried a button offering to rewrite a line of copy so it would fit the
slot it had to fill. The button had been there for months. It picked a random string from a
hardcoded five-item array of generic marketing sentences and wrote it straight into the user's
content — ignoring the item, its length constraint, the brand rules, and the quality verdict that
had just been computed for it.

Nothing ever failed. Both test suites were green throughout. The button rendered, responded to a
click, and changed the text on screen, which is the entire observable surface of "it works". A stub
that returns *something* is indistinguishable from a feature at every level a normal test operates
at — the only thing that separates them is whether the returned value has any relationship to the
inputs, and no assertion was ever written about that relationship because nobody had written the
feature yet.

It surfaced the way these always surface: a user hit the exact dead end the button existed to
resolve, clicked it, and got an irrelevant sentence. The placeholder was not discovered by the
people maintaining the code. It was discovered by the person it stranded.

Two rules came out of it. First, when you deliberately ship a placeholder, ship the failing test
with it — a skipped or `xfail` test naming what the real thing must do, so the debt is a red mark
in the suite rather than a comment nobody re-reads. Second, when you finally replace one, pin its
removal *by its literal content*: a repo scan asserting those five exact strings appear in no
production file, plus a scan asserting the real call has exactly the callers it should. A remembered
rule ("don't put the fake content back") gets skipped under pressure; a scan fails the build.

The same replacement also earned a smaller companion rule. The stub wrote its output straight into
the user's content, so there was nothing to reject. The real version proposes, and the user applies —
because an AI suggestion and a user confirmation are different facts, and a placeholder that writes
immediately hides that distinction along with everything else.

## The gate that confiscated the key

A quality check on a shipped project was blocking users at a stage boundary. The owner's instruction
was blunt: the check should highlight problems and offer a fix, never withhold passage. It looked
like a one-line change — a frontend early-return that refused to navigate when the verdict came back
invalid.

It was three walls, and the second one is the reason this is a case file.

The first was the obvious early-return. The third was the server refusing to record an override,
which is why "continue anyway" could not even be offered. The second was invisible from anywhere the
word "block" appeared: the gate's own runner built the downstream job package *only if the verdict
was valid*, and the next stage refused to start without that package. The gate did not merely judge —
it **issued the artifact the rest of the pipeline required**. Delete the visible check and the door
is still shut, now for a reason with no error message attached to it.

Every test passed throughout, because every test asked the same question: *does the check still
report correctly?* None asked *can a user who ignores the check actually proceed?* The rule that
falls out is to test the gate's **negative** path as a user journey, not as a verdict assertion.

There was a fourth wall, and the owner found it in the running app rather than anyone finding it in
the code. Several screens each kept their own **local restatement** of the server's refusal message —
literal copy along the lines of "pass the quality check first" — so the product went on saying the
gate existed after the gate was gone. The fix was to render the server's own message everywhere and
pin the removal with a repo scan on the phrase itself.

Hence the two halves of the rule. **Find every place the verdict is enforced**, with particular
suspicion of anything that both judges and *issues* a token, package or approval — that shape hides
the enforcement behind a missing artifact rather than a visible check. Then **grep the gate's
vocabulary, not just its logic**, because copy is enforcement too as far as a user is concerned.


## The config the database outranked

A project kept its form definitions in two places: a typed config file in the frontend source, and a
table the admin dashboard could edit so an operator could change a form without a deploy. The
resolution order was one line in a hook — database row first, source file as fallback — and it was
correctly documented right there.

Months earlier a required file-upload field had been made optional, because the file it collected
reached storage and then reached nothing else; requiring it gated a submit on a dead end. That change
edited the source file *and* shipped a migration for the table, and its migration header even said so:
the row wins at runtime, so both must move together.

When the feature finally shipped that made the upload real, the obvious task was to revert the copy
and make the field required again. Editing the source file was a two-character change and it would
have done **nothing**. The database row was the value in force; the source file had been the fallback
the whole time. Nothing would have failed — it lints, it type-checks, the parity tests pass, a code
review reads clean — and the operator would have reported that the change "didn't work" with nobody
able to see why. The only thing that catches this is reading the value back out of the running
system rather than out of the file you just edited.

Querying the live table before writing anything then exposed a second, sharper problem. The original
migration had applied its update to **every row containing that field**, not just the one row that
had motivated it. Going out that was harmless — only one row held the old value, so the rest were
no-ops. Coming back it would have been silently destructive: two other form variants had that field
optional *by deliberate design*, and a mirror-image revert would have quietly reversed both
decisions with no discussion and no test to catch it.

So the revert was scoped to one variant, one form, one field. And because a data migration has no
suite to go red, it was verified the way such things have to be: back up every row first, apply,
then assert that **exactly one row changed and the other twenty-four were byte-identical**. That
sentence is the evidence. "The migration ran without error" is not.

---

## The read-back that always said unset

A junior ticket filed two follow-up issues and added them to the project board. The board's own
skill already carried the right rule — *add the card AND set every single-select (Status, Owner,
Lane), then re-list the board and confirm the card reads the way you set it.* Only the first half
happened: `gh project item-add` created the cards, and no field was ever set.

The owner asked whether the tickets were properly filed under the junior view. The check looked
like diligence:

```bash
gh project item-list 4 --owner kish21 --format json \
  | jq '.items[] | {owner: (.Owner // "UNSET"), lane: (.Lane // "UNSET")}'
```

Every card came back `Owner=UNSET, Lane=UNSET`. That confirmed the suspicion, and two claims were
reported to the owner: the two new tickets were unstamped (true, by accident), **and** the parent
ticket was unstamped too, therefore "the board fields have been going unset on this project more
broadly" (false).

`gh project item-list --format json` returns its field keys **lowercase** — `owner`, `lane`,
`status`. `.Owner` matches nothing. The `// "UNSET"` fallback then converts "your filter is
malformed" into "the board is empty", with no error, for every card ever queried. The same query
would have said UNSET against a perfectly maintained board — which is exactly what it did: a later
count with the correct keys showed **107 of 116 cards had Owner set and 106 had Lane**.

The damage was not only the wrong claim. Believing the parent was unstamped, the agent *stamped
it* — overwriting whatever Lane it already carried, on a card it had no reason to touch, with no
record of the previous value. A broken read turned into an unnecessary write.

The tell was available and ignored: a fallback that reports the same value for *absence* and for
*never asked correctly* should never be trusted on its first negative. One glance at a card known
to be set — or one `jq keys` on a single item — would have shown lowercase keys immediately.

**The general rule this earns:** a probe that reports absence proves nothing until it has proved it
can report presence. Point it at a known-positive first. This is not specific to `gh` or `jq` —
`grep` with the wrong flag, a query with the wrong filter, a test file the runner never collected,
and a scan whose glob excludes its own target all report "clean" in exactly the same voice as a
genuine pass, and none of them raise.
