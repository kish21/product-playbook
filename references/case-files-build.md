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
