<!-- The layout of docs/scope.md. status.py renders it from /scope's fields file (`set scope filled --from-fields`;
the fields are listed in templates/product-scope.md, the syntax is templates/vision.md's). The script numbers every
heading. A run never opens this file. The writing rules of templates/vision.md apply to every field; no playbook words
in a field ("spine", "PRODUCT.md", "#Vision", a command name): write "the vision", "what brings it in". Each section
opens with a plain paragraph on why it matters; a table only for a real list. This document has no source list: no
`[n]` marks. -->
# {{product}} — scope
_Version 0.1 · {{date}} · what the first version does, and what it leaves out_

## 1. The core feature we will test
{{core feature:line}}

{{why core}}

For example: {{example:line}}

{{core loop}}

## 2. In the first version
Each part below is something the user can do, with a check anyone can run to say it is done. Nothing else is built
first, so the core can be tested early.

| Item | What the user can do | Done when | Moves which number |
|---|---|---|---|
{{in scope}}

## 3. Who builds it, and when
{{capacity:line}}

The first version is planned to fit that time. This is the order the work happens in.

| Week (or days) | What gets done |
|---|---|
{{shape}}

## 4. Later, and what brings each in
These parts are left out for now, not forgotten. Each one comes back when its signal shows up.

| Item | Comes in when |
|---|---|
{{deferred}}

## 5. Never
We will not build these, so nobody spends time on them by mistake.

| Item | Why not |
|---|---|
{{never}}

## 6. The basics everyone expects
Users expect these even though nobody asks for them. Each one is decided here, so none is missed.

| Item | Decision |
|---|---|
{{table stakes}}

## 7. What failure looks like
{{failure}}

## 8. Checked against the vision
Each promise the vision makes, and what this first version does with it. A promise left for later or changed says why.

| What the vision promised | In this scope |
|---|---|
{{vision check}}

## 9. Decisions taken
| Decision | Why | Who decided |
|---|---|---|
{{decisions}}

## 10. Other options we considered
{{options considered}}

## Appendix A — Workings
### A.1 Owner's answers
{{answers}}
### A.2 Where the numbers come from {{?numbers}}
| Number | From |
|---|---|
{{numbers}}
### A.3 Changes from the last version {{?superseded}}
{{superseded}}
