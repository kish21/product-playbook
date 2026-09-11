# Deployment

> Written by `/deploy`. The host is **copied from `PRODUCT.md#Architecture`**, never re-decided here.
> Secrets are never written into this file — it names the variables and how to generate them; the values
> are pasted into the host by the person who owns them.

**Host:** `<the runtime target from #Architecture>` · **category:** `PaaS | container-anywhere | VPS |
the user's own machine` · **chosen in** `#Architecture` (`<user-chosen | default taken>`)
**Live URL:** `<url>` · **last deployed:** `<YYYY-MM-DD>`

## 1. Build and start

| | |
|---|---|
| Install | `<command>` |
| Build | `<command>` |
| Start | `<command>` |
| Node/Python/runtime version | `<pinned version — the same one CI uses>` |

## 2. Environment variables the host needs

**Generated from `.env.example`** — every variable the config loader's boot guard requires. Do not retype
this list by hand; read the file, or it drifts from the guard and the first deploy fails closed.

| Variable | Secret? | How to get the value |
|---|---|---|
| `<VAR>` | yes/no | `<where it comes from, or the command that generates it>` |

**Paste these into the host yourself.** They are never committed, never written here, and never asked for
in chat. A variable left unset does not fail quietly: the boot guard rejects it **by name** — that is the
guard working, and it is the single most likely first-deploy failure.

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

1. `<step>`
2. `<step>`

## 5. Proof it works

Not "the build went green" — a request that was answered.

- **Health path:** `curl -s <url>/health` → `<response>`
- **One real user path:** `<command or the exact steps>` → `<what came back>`

`evidence: <command> → <result> · docs/deployment.md · <YYYY-MM-DD>`

## 6. Rollback

The path you **actually have**, not the one you would like. `/ship` attaches its rollout-safety checks to
this section on every release.

- **Revert:** `<how — redeploy the previous build, revert the PR, re-tag>`
- **Migration down:** `<command, or "none — forward-only, and here is why">`
- **Flag off:** `<the flag, if the risky change is behind one>`
- **Signal to watch after deploy:** `<the one metric or log line that says it went wrong>`

## 7. Known gaps

Anything that blocked and was not fixable today — a quota, DNS propagation, a paid tier, an account that
has to be created by someone else. A recorded gap with a date beats a green tick that is not true.
