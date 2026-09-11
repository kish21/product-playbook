# Agent instructions — read this first

> Scaffolded by `/structure`. **This file is a pointer, not a copy.** The spine is the source of truth;
> duplicating it here creates exactly the two-sources-of-truth drift `/drift-check` hunts. Keep it to
> what an agent would otherwise get wrong on its first edit.
>
> **If a tool owns a delimited block in this file** (`<!-- BEGIN:x -->` … `<!-- END:x -->` — Next.js
> writes one on every `next dev`), **write outside it and never rewrite it.** A naive overwrite is
> silently reverted on the next run, which is worse than not writing at all.

## Read before you touch anything

1. **`PRODUCT.md`** — the spine. Vision, locked scope, the plan, the architecture decisions, the build
   log. A fresh read of the code alone re-litigates decisions that were already made and recorded.
2. **`STRUCTURE.md`** — where things go and why. Do not invent a new home for a file.
3. **`DESIGN.md`** — the token vocabulary, if this product has a UI. Tokens come from here, never hex.

## The rules an agent breaks first

Each line is a rule a fresh agent would otherwise violate, and each is enforced somewhere. Later phases
append their own — one line each, never a paragraph.

- **Config:** nothing reads the environment directly. Every value goes through the project's config
  loader, and secrets live in `.env` (never a code file, never a committed value).
- **Prompts (AI products):** versioned YAML under the prompts folder, never inline in code.
- **Database:** schema changes are migrations. Never hand-edit the schema, never edit a past migration.
- **Non-goals are locked.** The spine's out-of-scope list is a decision, not a backlog. Reopening one is
  a `/scope` conversation, not a pull request.
- **Tests:** the test datastore is never the development one; the guard fails closed on purpose.

## Decisions with teeth (fill these in — one line each, with the *why*)

- `<ADR-n>`: `<the decision>` — **`<the consequence of breaking it>`**.
- `<a token/unit/boundary rule>` — **`<the measured reason it is not the obvious choice>`**.

An agent obeys a rule it understands and quietly "fixes" one it does not: *"`--success` is teal, not
green, because green is the brand colour (measured: green-on-green is 1.31:1)"* survives a refactor;
*"use teal"* does not.
