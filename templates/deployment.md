# Deployment

> Written by `/deploy`. The host is **copied from `PRODUCT.md#Architecture`**, never re-decided here.
> Secrets are never written into this file — it names the variables and how to generate them; the values
> are pasted into the host by the person who owns them.

**One row per deployable unit** — anything built, run or served on its own (the site, the API, a worker, a
forwarder in front of a vendor). Each unit's host is copied from `#Architecture`.

| Unit | Host | Category | Chosen in `#Architecture` | Live URL |
|---|---|---|---|---|
| `<unit>` | `<runtime target>` | `PaaS · container-anywhere · VPS · the user's own machine · static site / CDN` | `<user-chosen · default taken>` | `<url>` |

**Last deployed:** `<YYYY-MM-DD>` · **Why now:** `<the #Plan milestone, or the user's reason>`
**Host product:** `<the product the host recommends today for this category — checked <YYYY-MM-DD>>`
**Cost and free-tier limits:** `<per unit: each limit · what happens at it (throttled, blocked, billed) · what each dashboard usage counter counts and when it resets>`

## 1. Build and start

One column per unit. A static site has no start command: write `none — static`.

| | `<unit>` | `<unit>` |
|---|---|---|
| Install | `<command>` | `<command>` |
| Build | `<command>` | `<command>` |
| Start | `<command · none — static>` | `<command>` |
| Node/Python/runtime version | `<pinned version — the same one CI uses>` | `<version>` |
| Package manager + version | `<pinned in the repo · what the host's build image ships · how a mismatch is fixed>` | `<…>` |
| Folder the host builds from | `<the unit's own folder, not the repo root>` | `<folder>` |
| Deploy entrypoint | `<the repo's documented script or task>` | `<…>` |

## 2. Environment variables the host needs

**Generated from what the code reads** — the config loader and every build-time read — with `.env.example`
checked against it. Do not retype this list by hand, or it drifts from the code.

| Variable | Unit | Secret? | Read at | Lives in | How to get the value |
|---|---|---|---|---|---|
| `<VAR>` | `<unit>` | yes/no | build/boot | pasted into host / committed in `<file>` | `<where it comes from, or the command that generates it>` |

**`.env.example` differences:** `<variables the code reads that it lacks · variables it lists that nothing
reads — or "none">`

**Paste the secrets into the host yourself.** They are never committed, never written here, and never
asked for in chat. **A public build-time value is committed** in the file the build reads, because it ships
to every visitor anyway and a value only in a dashboard drifts. A secret found in a build-time value is
already public: move it behind the server and rotate it. **Read at boot:** a variable left unset does not fail quietly — the boot guard rejects it **by
name**; that is the guard working, and it is the single most likely first-deploy failure. **Read at build:**
an unset one fails **open, silently** — the page falls back to a mock or a dead button — so each one is
checked in the built output: `<the search and what it found>`.

## 3. Migrations on deploy

`#Architecture` records the migrations approach; this section says what *"applied on deploy"* actually
means here, because an assertion with no command behind it is a plan, not a deployment.

- **Command:** `<command>`
- **Where it runs:** `<release/build step · one-shot job · entrypoint>` — on **one** instance, never on
  every replica at once.
- **If it fails:** `<what happens — does the deploy abort, does the old version keep serving?>`
- **Backwards compatibility:** a migration ships before the code that needs it, or behind a flag, so a
  rollback does not land on a schema the old code cannot read.

## 4. First deploy — the steps that were actually taken

**Deploy order:** `<which units deploy on merge and which by hand · a backend and its migrations go live
BEFORE a frontend change that needs them is merged>`. **When the host builds on merge, merging is
deploying:** it goes through the PR flow, on the user's explicit word.

**Custom domain / DNS:** attached by the user at the host's dashboard — never a route in committed config.

1. `<step>`
2. `<step>`

## 5. Who can get in

Checked **before** the URL was public.

- **Credentials in the built output:** `<the search run over the build folder — password strings, sign-in
  calls with typed-in values, real account emails> → <what it found>`
- **Every way a stranger can get signed in:** `<sign-up · demo or quick-login buttons · magic links · guest
  mode>` — each **closed**, or **open because the user said so**
- **What a visitor can see:** `<vendor hostnames · account or workspace names · internal URLs found in the
  built output and its network calls>` — each fine, or hidden behind `<the domain and forwarder>` because
  the user said so
- **Behind a proxy or forwarder:** `<what the backend keys on caller IP, origin or host, and how the
  visitor's address reaches it>` — or `no proxy`
- **Preview deployments:** `<off · on, against their own backend and data: which>` — never unmerged code
  on production data
- **What a stranger can reach and spend** (asked when `#Dev-complete` was empty): `<the paid actions a
  signed-in stranger can trigger, and what was closed>`

## 6. Proof it works

Not "the build went green" — a request that was answered.

- **Health path:** `curl -s <url>/health` → `<response>` — per unit that has one
- **A static site:** root → `<200>` · a deep link → `<200>` · the served JavaScript contains the production
  API base: `<the search>` · one call from the site reaches the real backend: `<which>`
- **One real user path:** `<command or the exact steps>` → `<what came back>`

`evidence: <command> → <result> · docs/deployment.md · <YYYY-MM-DD>`

A path behind a sign-in, walked by the owner because the agent must hold no real account's credentials:
`owner-verified (manual) <YYYY-MM-DD>: <what they did> → <what they saw>` — not an `evidence:` line.

## 7. Rollback

The path you **actually have**, not the one you would like. `/ship` attaches its rollout-safety checks to
this section on every release.

- **Revert:** `<how — redeploy the previous build, revert the PR, re-tag>`
- **Migration down:** `<command, or "none — forward-only, and here is why">`
- **Flag off:** `<the flag, if the risky change is behind one>`
- **Signal to watch after deploy:** `<the one metric or log line that says it went wrong>`

## 8. Known gaps

Anything that blocked and was not fixable today — a quota, DNS propagation, a paid tier, an account that
has to be created by someone else. A recorded gap with a date beats a green tick that is not true.
