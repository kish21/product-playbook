# Deployment

**In short:** `<3 plain sentences: where it runs and who can reach it, how to deploy it again, how to roll it back>`

> The host comes from docs/architecture.md and is not chosen again here. This file names the secrets and how to
> generate each one. It never holds a secret value: the person who owns a secret pastes it into the host.

**One row per deployable unit.** A unit is anything built, run or served on its own: the site, the API, a worker,
a forwarder in front of a vendor. Each unit's host is copied from docs/architecture.md.

| Unit | Host | Category | Who chose it | Live URL |
|---|---|---|---|---|
| `<unit>` | `<runtime target>` | `PaaS, container-anywhere, VPS, the user's own machine, or static site / CDN` | `<user-chosen, or default taken>` | `<url>` |

**Last deployed:** `<YYYY-MM-DD>`. **Why now:** `<the milestone that needs a URL, or the user's reason>`.
**Host product:** `<the product the host recommends today for this category, checked on <YYYY-MM-DD>>`.
**Cost and free-tier limits:** `<per unit: each limit, what happens at it (throttled, blocked or billed), what each dashboard usage counter counts and when it resets>`.

## 1. Build and start

One column per unit. A static site has no start command: write `none — static`.

| | `<unit>` | `<unit>` |
|---|---|---|
| Install | `<command>` | `<command>` |
| Build | `<command>` | `<command>` |
| Start | `<command, or none — static>` | `<command>` |
| Node/Python/runtime version | `<pinned version, the same one CI uses>` | `<version>` |
| Package manager + version | `<pinned in the repo; what the host's build image ships; how a mismatch is fixed>` | `<…>` |
| Folder the host builds from | `<the unit's own folder, not the repo root>` | `<folder>` |
| Deploy entrypoint | `<the repo's documented script or task>` | `<…>` |

## 2. Environment variables the host needs

This list comes from what the code reads: the config loader and every build-time read. `.env.example` is checked
against it. Never retype it by hand, or it drifts from the code.

| Variable | Unit | Secret? | Read at | Lives in | How to get the value |
|---|---|---|---|---|---|
| `<VAR>` | `<unit>` | yes/no | build/boot | pasted into host / committed in `<file>` | `<where it comes from, or the command that generates it>` |

**`.env.example` differences:** `<variables the code reads that it lacks, and variables it lists that nothing reads, or "none">`

**Paste the secrets into the host yourself.** They are never committed, never written here and never asked for in
chat. **A public build-time value is committed** in the file the build reads. It ships to every visitor anyway, and
a value kept only in a dashboard drifts. A secret found in a build-time value is already public. Move it behind the
server and rotate it.

**Read at boot:** an unset variable does not fail quietly. The boot guard rejects it by name. That is the guard
working, and it is the most likely first-deploy failure. **Read at build:** an unset variable fails silently. The
page falls back to a mock or a dead button. So each one is checked in the built output:
`<the search and what it found>`.

**The secrets file on the owner's machine or a server:** only its owner can read it:
`<chmod 600 .env, or on Windows: icacls .env /inheritance:r /grant:r "<you>:F">`. **No secret value in any log:**
`<what was searched (the app's logs, the dev server's log) and what was found (none)>`.

## 3. Migrations on deploy

The architecture says how migrations run. This section names the command, because a claim with no command behind
it is a plan, not a deployment.

- **Command:** `<command>`
- **Where it runs:** `<a release or build step, a one-shot job, or the entrypoint>`. It runs on one instance, never on
  every copy at once.
- **If it fails:** `<what happens: does the deploy stop, does the old version keep serving?>`
- **Backwards compatibility:** a migration ships before the code that needs it, or behind a flag. Then a rollback
  never lands on a schema the old code cannot read.

## 4. First deploy: the steps that were actually taken

**Deploy order:** `<which units deploy on merge and which by hand; a backend and its migrations go live before a
frontend change that needs them is merged>`. **When the host builds on merge, merging is deploying.** It goes through
the pull request, on the user's clear word.

**Custom domain and DNS:** the user attaches them at the host's dashboard. A DNS route never goes into committed
config.

1. `<step>`
2. `<step>`

## 5. Who can get in

Checked before the URL was public.

- **Credentials in the built output:** `<the search over the build folder (password strings, sign-in calls with
  typed-in values, real account emails) and what it found>`
- **Every way a stranger can get signed in:** `<sign-up, demo or quick-login buttons, magic links, guest mode>`. Each
  one is closed, or open because the user said so.
- **What a visitor can see:** `<vendor hostnames, account or workspace names and internal URLs found in the built
  output and its network calls>`. Each one is fine, or hidden behind `<the domain and forwarder>` because the user
  said so.
- **Behind a proxy or forwarder:** `<what the backend keys on (caller IP, origin or host) and how the visitor's
  address reaches it>`, or `no proxy`
- **Preview deployments:** `<off, or on against their own backend and data: which>`. Unmerged code never runs on
  production data.
- **What a stranger can reach and spend** (asked when the pre-release code check had not passed): `<the paid actions a
  signed-in stranger can start, and what was closed>`

## 6. Proof it works

Not "the build went green". A request that was answered.

- **Health path:** `curl -s <url>/health` returned `<response>`, per unit that has one
- **A static site:** the root returned `<200>` and a deep link returned `<200>`. The served JavaScript contains the
  production API base: `<the search>`. One call from the site reaches the real backend: `<which>`
- **One real user path:** `<command or the exact steps>` returned `<what came back>`

`evidence: <command> → <result> · docs/deployment.md · <YYYY-MM-DD>`

A path behind a sign-in is walked by the owner, because the agent holds no real account's credentials:
`owner-verified (manual) <YYYY-MM-DD>: <what they did> → <what they saw>`. It is not an `evidence:` line.

## 7. Rollback

The path you actually have, not the one you would like. Every release checks its rollback against this section.

- **Revert:** `<how: redeploy the previous build, revert the pull request, or re-tag>`
- **Migration down:** `<command, or "none: forward-only, and here is why">`
- **Flag off:** `<the flag, if the risky change is behind one>`
- **Signal to watch after deploy:** `<the one metric or log line that says it went wrong>`
- **Rehearsed:** `<date>: a deliberately bad release (one extra migration) on <a fake host folder or a local copy>, rolled back by <the steps>, and <what answered after>`, with its `evidence:` line. Or `not rehearsed - <why>` and an open item.

A rehearsal finds two traps. With no down-migrations, the old code can refuse the newer schema. Then the rollback
is restoring the database backup taken before the deploy. And a release folder copied from another can still run
the old code. An environment inside it, such as a Python virtualenv, points at the original folder. So build each
release in its own folder from the repo.

## 8. Known gaps

Anything that blocked and could not be fixed today: a quota, a DNS change not yet live everywhere, a paid tier, an account someone
else has to create. A recorded gap with a date beats a green tick that is not true.
