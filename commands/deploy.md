---
name: deploy
description: >
  Phase 2/3 bridge of product-playbook — connect the repository to the host #Architecture already chose,
  so the product is reachable by someone who is not you. EXECUTES a recorded decision; it never reopens
  it. Use after /dev-check when the product needs to be reachable (a milestone criterion needing a real
  URL, a second device, a real user), or run /deploy "get it live", "deploy it", "put it on a URL",
  "how do I host this". Writes docs/deployment.md + the Deployment section of PRODUCT.md. Run /test next.
---

# `/deploy` — Development ⑦ · run as an **engineer who has been paged at 3am**

> Part of **product-playbook**. Reads + updates the project spine (`PRODUCT.md`, or the project's
> existing docs — resolve per `MECHANISMS.md` §Spine resolution); writes `docs/deployment.md`.
> **Rule files — open by path, never search:** `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` · MECHANISMS.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms.md` · MECHANISMS-ON-DEMAND.md = `${CLAUDE_PLUGIN_ROOT}/references/mechanisms-on-demand.md` (a path still starting with `$`: the same names in `.claude/product-playbook/`, else `~/.claude/product-playbook/`).
> **Open `PRINCIPLES.md` and `MECHANISMS.md` before the first step** (paths above; a situational companion only when a rule points into it), then apply them — load-bearing: **secrets are the user's to paste, never yours to write**,
> **no-hardcoding**, **fail-closed**, **docs match reality**, **honest gap surfacing**.

> **This phase executes a decision; it does not make one.** `#Architecture` already recorded the runtime
> target. Deployment was the one step in the whole chain where a decision was recorded and the user was
> left to work out the execution alone — on a real run, eleven phases in, with green CI and 111 passing
> tests, the app had never been deployed anywhere and no document said how.

## Contract
- **Purpose:** the product is reachable at a URL by someone who is not you, and the steps are written
  down so the next deploy is not a rediscovery.
- **Reads:** `PRODUCT.md#Architecture` (**the runtime target of each deployable unit, data custody and
  migrations approach** — copied, never re-decided), `#Foundation`, `#Plan` (which milestone needs
  reachability), `#Dev-complete`, the config the code actually reads, and `.env.example`.
- **Writes:** `docs/deployment.md` (the companion document) + `PRODUCT.md#Deployment` (a short record
  and a pointer to it).
- **Gate type:** `verification` — pass/fail on a live URL; the preference was settled in `#Architecture`.
  **Not batchable:** it creates a real environment and the first run needs the user at the host's
  dashboard. (`docs/state-model.md` §2d)
- **State model** (`docs/state-model.md` §2c): writes `#Deployment` · `declined` ✓ · `override` ✓ ·
  `running` ✓ (a first deploy waiting on an account, a DNS record or a quota) · `superseded` ✓
- **Exit criteria:**
  - [ ] **Every deployable unit's host is the one `#Architecture` recorded** — copied verbatim, with its
    provenance. A different host here is a contradiction, not a detail (`MECHANISMS.md` §Step 3c). → `Host (copied from #Architecture`
  - [ ] **`docs/deployment.md` exists** and carries: host · build and start commands · the exact env-var
    list · how migrations run on deploy · first-deploy steps · the one command or URL that proves it
    worked · the rollback path. → `docs/deployment.md`
  - [ ] **The env-var list is GENERATED from what the code reads, and `.env.example` is checked against
    it** — the config loader's reads and every build-time read, not retyped. A variable the code reads that
    `.env.example` lacks, or one it lists that nothing reads, is named. Every variable the boot guard
    requires appears in it. → `Env vars set on the host`
  - [ ] **Migrations on deploy are defined, not asserted.** `#Architecture` typically says *"applied on
    deploy"*; name the command, where it runs, and what happens when it fails. → `Migrations on deploy`
  - [ ] **A real request succeeded** against the deployed URL — the health path (a static site: the root
    and a deep link) *and* one real user path; a path behind a sign-in may be owner-verified, recorded as
    such. A build that went green is not a product that answers. → `Proof it answers`
  - [ ] **`/foundation`'s placeholder guard was considered before the first deploy**, not discovered by
    it: the guard is working as designed when it refuses to boot on an unset host variable, and that is
    the single most likely first-deploy failure **for a value read at boot**. → `Env vars set on the host`
  - [ ] **Every value read at BUILD time was checked in the built output.** Nothing rejects an unset one:
    the page falls back to a mock or a dead button, and the site looks live while it is not. → `Env vars set on the host`
  - [ ] **The built output carries no credential of any kind, and every way a stranger can get signed in
    is listed** — each one closed, or open because the user said so. → `Who can get in`
  - [ ] **Preview deployments are off, or run against their own backend and data** — unmerged code never
    reaches production data. → `Who can get in`
  - [ ] **With `#Dev-complete` empty, what a stranger can reach and spend was asked before the URL went
    public**, and the answer is recorded. → `Who can get in`
  - [ ] **No secret was written by this skill, or asked for in chat.** The document says *which* variables
    the host needs and how to generate each value; **the user pastes the secrets into the host
    themselves**. Public build-time values are committed, not pasted. → `Env vars set on the host`

## Step 0 — Context + prior-gate check
- Read `#Architecture`'s **runtime target**, **data custody** and **migrations approach**, `#Foundation`,
  and `#Plan`. Say which host you are executing and that it came from `#Architecture`.
- **List every deployable unit, and read the runtime target for EACH — not "the" runtime target.** A unit
  is anything built, run or served on its own: the site, the API, a worker, a forwarder in front of a
  vendor. (case file: Three things to deploy and one Host slot)
- **If `#Architecture` records no runtime target for a unit**, warn and offer `/architect` for that unit
  first (allow override) — deploying to a host nobody chose is how a project acquires infrastructure it
  cannot justify later.
- **If `#Dev-complete` is empty**, say so: deploying an unfinished product is legitimate (a milestone may
  need a URL before the product is done — that is usually *why* this phase runs early) but it should be a
  choice, not an accident. **Then ask what a stranger can reach and spend once the URL is public** — can
  anyone sign up, and what does each action cost (a paid model call, a GPU job, an email sent)? Security
  work deferred "until outside users" is due the day the URL is public. Record the answer and what was
  closed. (case file: Public sign-up where every click spends money)
- **An override is RECORDED, never a verbal "yes"** (`MECHANISMS.md` §Declined runs): name the gate, ask
  for the **reason in the user's own words**, and write `Override <date>: <reason> — bypassed <gate>` at
  the top of `#Deployment` before continuing.
- **Re-running — `MECHANISMS.md` §Re-run semantics, in full.** A host change keeps the superseded one
  with its dated line: *why the other host lost* is the expensive thing to reconstruct.
- **Stopping at an unmet gate — `MECHANISMS.md` §Declined runs, in full.** One dated `_Not run_` line at
  the top of `#Deployment`, nothing else touched.

## Step 1 — Apply principles (this phase)
- **Secrets are the user's to paste.** Hand over the exact variable names and how to generate each value.
  **Never write a secret into a file, a command you run, or the chat.**
- **A public build-time value is not a secret — commit it; only secrets are pasted.** A value baked into
  the built site ships to every visitor, so typing it into a dashboard only makes it drift. Commit it in
  the file the build reads (`.env.production` or its equivalent, not swallowed by `.gitignore`). **A secret
  found in a build-time value is already public:** stop, tell the user to move it behind the server and
  rotate it — never commit it. (case file: Thirty-four public values typed into a dashboard)
- **No-hardcoding still applies on the host.** The host's env vars are the same config layer as `.env`,
  read through the same loader. A value that only exists in a dashboard is dead config with a bill.
- **Fail-closed reaches production too.** The boot guard that rejects placeholders does not get an
  exemption because it is inconvenient at 2am on the first deploy.

## Step 2 — Write `docs/deployment.md` from the runtime-target CATEGORY

**Scaffold from `templates/deployment.md`.** The steps differ by **category, not by brand** — Vercel,
Railway, Render and Fly are one recipe with different button names; a bare VPS is a genuinely different
one. Use the user's named host in the examples if they have one, and **never turn this into a
supported-vendor list** (same rule as `/foundation`'s test-datastore recipes).

1. **PaaS / managed platform** → connect the repository, set the build and start commands, paste the
   secrets into the dashboard, and let the platform build on push. Migrations run as a release/build step.
2. **Container-anywhere** → build the image, push it to a registry, and run it with the env supplied by
   the runtime. Migrations run as a one-shot job or an entrypoint step, **never on every replica at once**.
3. **VPS** → a process manager, a reverse proxy with TLS, and a deploy script that pulls, builds,
   migrates and restarts. Say where the env file lives and who may read it.
4. **The user's own machine** → the "deploy" is an install and a run command; say plainly what other
   people can and cannot reach, because a milestone criterion may quietly assume they can.
5. **Static site / CDN** → the host builds the site and serves its files: no start command, no health
   path — write `none — static` in both rows. A single-page app needs the host's fallback to `index.html`,
   or every deep link returns 404. (case file: The static site with no start command)

**Several units:** each gets its own category and its own column in the template.

Fill every section of the template. **Generate the env-var list from what the code reads** — the config
loader and every build-time read (`import.meta.env.*`, `process.env.NEXT_PUBLIC_*` and the like) — then
**check `.env.example` against it**: name each variable it lacks and each one nothing reads. Mark each
variable secret or not, **read at build or at boot**, and **committed or pasted**. **Do not invent one
variable of it.** (case file:
The env list that had drifted to half)

## Step 3 — Deploy once, for real, and write down what it took
Do the first deploy *with* the user — they hold the credentials. Then:
- **Before the URL is public, scan the BUILT output for credentials of every kind, and list every way a
  stranger can get signed in.** Search the build folder for password strings, sign-in calls with typed-in
  values and real account emails — a key-format secret scan misses all three. List sign-up, demo or
  quick-login buttons, magic links and guest modes; each is closed, or open because the user said so.
  (case file: The demo buttons that shipped two passwords)
- **Preview deployments are off, unless they have their own backend and data.** A host that builds every
  branch or PR gives unmerged code a URL that talks to the production backend and data. Turn them off, or
  point them at a separate backend, and record which. (case file: Previews on production data)
- **A value read at build time is not boot-time config: an unset one fails OPEN, silently — check each one in
  the built output.** Search the built files for each value the page needs (the API base, the auth
  project URL); these ship to every visitor, so reading them handles no secret. (case file: The site that
  looked live)
- **Prove it answers.** Hit the health path and **one real user path** on the deployed URL, and record the
  command and the response. A green build is not a working product; `/build` already learned that lesson
  on localhost and it is more true here. **A static site:** the root → 200, a deep link → 200, the served
  JavaScript contains the production API base, and one call from the site reaches the real backend.
- **A user path behind a sign-in is the owner's to walk — never sign in with a real account's credentials,
  and never ask for a password.** Record it as `owner-verified (manual) <date>: <what they did> → <what
  they saw>`, not as an `evidence:` line: no command anyone can re-run stands behind it. (case file: The
  signed-in path the agent must not walk)
- **Run the migrations the way the document says**, and record what happened.
- **Record the rollback path you actually have** — not the one you would like. This is where `/ship`'s
  rollout-safety lines (revert · migration-down · flag-off · the post-deploy signal) finally attach to
  something real, and until now they presupposed an environment nothing created.
- **Anything that blocked and was not fixable today** (a quota, a DNS propagation, a paid tier) puts the
  section in the **`running`** state with a due date, rather than a green tick.

## Step 3b — Principle-gate: it is deployed, or it is not (evidence)
Walk the exit criteria and prove each with a command, not a claim. The load-bearing one: **a real request
to the public URL, recorded in the one settled evidence form** (`docs/state-model.md` §2f) —
`` `evidence: curl -s https://<url>/health → 200 ok · docs/deployment.md · 2026-09-11` ``. **No URL
that answered means this gate did not pass**, regardless of how well the build went. An owner-verified
path passes the user-path half; the transition guard reports it `UNVERIFIED — owner-verified`, never `PASS`.

**Close the loop (`MECHANISMS.md` §Step 3b):** update the `Stage:`/`Last updated:` header, reconcile any number this phase introduced against `#Vision` (surface a contradiction, never write over it), and **offer to commit the change** (`MECHANISMS.md` §Commit the work — check the repo exists, name the branch, offer the message, push only if a remote exists and the user says so). Then **run the transition guard** (`MECHANISMS.md` §Step 3b, item 4): re-run this phase's own `evidence:` lines and report a verdict for every exit criterion — `UNVERIFIED` is a normal outcome, silence is not — and check the transition is legal. **Close in plain language** (`MECHANISMS.md` §Plain-language close): two or three sentences of *what just happened* with no playbook dialect, then a numbered *what YOU do next* — the user's own actions, dated where they are time-bound, or "Nothing — you're done".

## Step 3c — Contradiction check (before the gate closes)
Per `MECHANISMS.md` §Step 3c, check what this phase produced against decisions **already recorded** —
here `#Architecture`'s runtime target, data custody and migrations approach, and `#Structure`'s
deliberately-not-scaffolded list (a `Dockerfile` written here contradicts a recorded decision not to have
one). **Carry any decision still OPEN forward** (§Step 3c item 4). On a conflict, **name both sides, ask
which wins, and update the loser** — never leave it standing in two places.

## Step 4 — Handoff
"It's live at `<url>`, and `docs/deployment.md` says how to do it again.
- Next run **`/test`** — the suite now has a real environment to run against, and any milestone criterion
  that needed a public URL (a second device, a real user, a link a stranger opens) is now reachable.
- `/ship` will use the rollback path recorded here on every release from now on."
