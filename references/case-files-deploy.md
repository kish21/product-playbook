# Case files — /deploy

War stories behind the one-line lessons in `commands/deploy.md`. Each heading is pointed to from
the skill file as `(case file: <heading>)`. All of them come from one logged `/deploy` run on a product that
had never been deployed: a single-page web app built with a bundler, a separate serverless GPU backend,
and a managed database-and-auth vendor, taken to a public custom domain in one day with the owner at the
host's dashboard.

## The demo buttons that shipped two passwords

The run's secret checks passed: the secret scanner, plus a search for API-key prefixes. The site went
public with **the login emails and passwords of two real accounts typed into the sign-in page**, behind
"try a demo" buttons. The owner spotted it about fifteen minutes after go-live. The skill did not, and
neither did the agent.

Containment needed the owner at the auth vendor's dashboard: both accounts banned, their passwords changed
through SQL because the dashboard could not set one, sign-up switched off. Then a code fix: the demo
buttons render only on the dev server, and a test scans the source for them.

A secret scanner looks for things shaped like keys. A password in a string literal, a sign-in call with
typed-in arguments and a real account's email are not key-shaped, so the scan was never going to find
them. The rule asks two separate questions for that reason: what credentials the BUILT output carries,
and every way a stranger can get a session — sign-up, demo or quick-login buttons, magic links, guest
modes.

## Public sign-up where every click spends money

The skill called deploying before `#Dev-complete` legitimate, and it is. It never asked what the public
URL exposed. Here every action in the product started a paid GPU job, sign-up was open to anyone, and
the security work had been deliberately deferred "until outside users" — which the public URL made
today. Fixed during the run: sign-up switched off at the auth vendor, and demo accounts created by the
owner. The rule makes it a question asked in Step 0, whenever `#Dev-complete` is empty.

## The env list that had drifted to half

The skill said to generate the env-var list from `.env.example`. That file listed 15 of the 32 endpoint
variables the code read, plus one variable nothing read at all. A list generated from it would have been
exactly as wrong, and the missing ones are build-time values, which fail silently (next case file).

It was worse than drift. Several URLs were not variables at all: the code built them from another URL
with a string replace that matched only the local dev server's path shape. On the production host's URL
shape the replace silently produced the wrong endpoint. `.env.example` is a claim about what the code
reads; the code's own reads are the fact.

## The site that looked live

The skill promised that an unset variable fails loudly, by name, at the boot guard, and called that the
single most likely first-deploy failure. That is true of a server. In a single-page app built by a
bundler, the browser's values are baked into the JavaScript when the site is BUILT. An unset one is not
rejected by anything: that page falls back to a mock or a disabled button, and the site looks live while
it quietly is not.

The check that holds is to search the built output for each value the page needs. These values ship to
every visitor, so they are public by design, and reading them handles no secret.

## Three things to deploy and one Host slot

Step 0 checked for one runtime target. `#Architecture` had recorded the backend's host and nothing for
the site, so the skill sent the run back to `/architect` as if nothing had been decided. The run ended
with three deployables: the site, a small forwarder in front of the backend vendor, and the backend that
already ran. The template had one Host slot for all three. A product is often more than one thing to
deploy, and each one needs its own recorded host, its own category and its own proof.

## The static site with no start command

The categories were PaaS, container, VPS and the user's own machine. The template demanded a start
command and a health path. A static single-page app has neither: the host builds it and serves the files.
The proof that held was different: the root answered 200, a deep link answered 200 (so the host's fallback
to `index.html` worked), the served JavaScript contained the production API base, and one call from the
site reached the real backend.

## Thirty-four public values typed into a dashboard

"Secrets are the user's to paste" assumed every value is a secret. Here every browser value was public by
design: it is baked into the built JavaScript and every visitor can read it. Typing 34 of them into the
host's dashboard would have been the option that drifts, and a value that exists only in a dashboard is
exactly the dead config the principles warn about. The run committed the public endpoint URLs in the file
the build reads, and pasted only the true secrets.

## Previews on production data

Nothing in the skill mentioned preview deployments. Many hosts build a URL for every branch or pull
request by default. That code is unmerged and unreviewed, and it runs with the production values, so it
talks to the production backend and reads and writes production data. The run turned previews off.

## The signed-in path the agent must not walk

The agent could make every public request itself. The real user path was behind a sign-in, and the agent
must not hold a real account's password. The owner walked it, and it was recorded as owner-verified
(manual), not as an `evidence:` line, because no command anyone can re-run stands behind it. The skill
did not say this, which left the gate either impossible to meet or a temptation to use credentials.
