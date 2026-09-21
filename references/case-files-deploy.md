# Case files — /deploy

War stories behind the one-line lessons in `commands/deploy.md`. Each heading is pointed to from
the skill file as `(case file: <heading>)`. All four come from one logged `/deploy` run on a product that
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
