<!-- The layout of docs/vision.md. status.py renders it from /vision's fields file (`set vision filled --from-fields`;
the fields are listed in templates/product-vision.md): `{{name}}` is a field, `{{name:first}}` its first line,
`{{name:rest}}` the lines after it, `{{name:line}}` all of it on one line. A table field fills the rows under its
header. A heading ending `{{?name}}` is dropped when that field is empty or n/a; a line whose optional field is empty
is dropped. The script numbers every heading, so a dropped section leaves no gap. A run never opens this file.
Writing rules for the fields (a newcomer reads this document, and so does a coding agent):
- A field's first line is its plain takeaway.
- One idea per sentence, about 15-18 words on average, none over 30. No em-dash or ` · ` chains in body prose.
- Explain every rule, law or term in plain words the first time it appears ("CCD2, the EU rule on credit offers").
- Where a fact came from is a footnote mark `[1]` listed under sources, never inside the sentence.
- Only what the user gave or picked goes in who, the problem, why now, the riskiest assumption and the business model. -->
# {{product}} — product vision
_Version 0.1 · {{date}} · what we are building, for whom, and how we will know it works_

## 1. Vision in one line
**{{vision:line}}**

{{plain words}}

## 2. Who it is for
**{{who:first}}**

**The job:** {{job:line}}
### 2.1 Main users {{?who:rest}}
{{who:rest}}
### 2.2 Others who use it {{?others}}
{{others}}
### 2.3 Scale {{?scale}}
{{scale}}
### 2.4 The first users
{{first users}}

## 3. The problem
**{{problem:first}}**

{{problem:rest}}
### 3.1 Why it happens
{{root causes}}

## 4. Why now
**{{why now:first}}**

{{why now:rest}}

## 5. How it is solved today
**{{market:first}}**

| Approach | Who does it | Where it falls short |
|---|---|---|
{{solved today}}

{{market:rest}}

## 6. The experience
**{{worked example:line}}**

| When | What happens |
|---|---|
{{experience}}

{{what makes it work}}

## 7. How it works
{{how it works}}
### 7.1 Where AI is used, and where a person decides {{?ai}}
{{ai}}
### 7.2 Your brief, answered {{?brief}}
| Brief point | Our answer | Section |
|---|---|---|
{{brief}}

## 8. Value and business model
**{{value:first}}**

{{value:rest}}

Business model: {{business model:line}}

## 9. How we will know
**North star: {{target:line}}**

| Type | Metric and number |
|---|---|
| Input | {{inputs:line}} |
| Guardrail | {{guardrail:line}} |

How it is measured: {{instrumentation:line}}

## 10. Riskiest assumption
**{{riskiest:first}}**

{{riskiest:rest}}

## 11. Rules, languages and data
**{{constraints:first}}**

{{constraints:rest}}

## 12. Competitors
| Product | Market | Does | Does not | Same job / nearby |
|---|---|---|---|---|
{{competitors}}

## 13. Scope at a glance
The details belong to the scope.

**In scope:**
{{in scope}}

**Out of scope:**
{{out of scope}}

## 14. Open questions
{{open questions}}

## Appendix A — Workings
### A.1 Owner's answers
{{answers}}
### A.2 Search list
{{searches}}
### A.3 North-star terms
| Term | Number | From |
|---|---|---|
{{terms}}
### A.4 Sources
{{sources}}
### A.5 Changes from the last version {{?superseded}}
{{superseded}}
