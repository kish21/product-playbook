<!-- The layout of docs/scope.md. status.py renders it from /scope's fields file (`set scope filled --from-fields`;
the fields are listed in templates/product-scope.md, the syntax is templates/vision.md's). The script numbers every
heading. A run never opens this file. The writing rules of templates/vision.md apply to every field; no playbook words
in a field ("spine", "PRODUCT.md", "#Vision", a command name): write "the vision", "what brings it in". -->
# {{product}} — scope
_Version 0.1 · {{date}} · what the first version does, and what it leaves out_

## 1. The core feature we will test
**{{core feature:line}}**

For example: {{example:line}}

{{core loop}}

## 2. In the first version
**Each part of the first version, and the check that says it is done.**

| Item | What the user can do | Done when | Moves which number |
|---|---|---|---|
{{in scope}}

## 3. Who builds it, and when
**{{capacity:line}}**

| Week (or days) | What gets done |
|---|---|
{{shape}}

## 4. Later, and what brings each in
| Item | Comes in when |
|---|---|
{{deferred}}

## 5. Never
| Item | Why not |
|---|---|
{{never}}

## 6. The basics everyone expects
| Item | Decision |
|---|---|
{{table stakes}}

## 7. Checked against the vision
{{vision check}}

## 8. Other options we considered
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
