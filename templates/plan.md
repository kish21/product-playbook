<!-- The layout of docs/plan.md: the whole plan a person reads. status.py renders it from /plan's fields file (`set
plan filled --from-fields`; the fields are listed in templates/product-plan.md, the syntax is templates/vision.md's).
Everything in the plan's PRODUCT.md section is here too, from the same fields. The script numbers every heading. A run
never opens this file. The writing rules of templates/vision.md apply to every field; no playbook words in a field
(record, spine, PRODUCT.md, a command name). Every number the user has not given sits in the open items, never as
"(proposed)" in the text. `{{product}}`, `{{date}}` and `{{ai note}}` are written by the script - never a field. -->
# {{product}} — plan
_Version 0.1 · {{date}} · how the first version gets built, milestone by milestone_

## 1. In short
**{{summary:line}}**
- **What the demo will prove:** {{will prove:line}}
- **What it will NOT prove yet:** {{will not prove:line}}

## 2. Planning assumptions
- **Who builds it:** {{capacity:line}}
- **Start:** {{start:line}}
- **How long each milestone takes:** {{durations:line}}
- **AI model and its cost:** {{ai note}}

## 3. Timeline
| Milestone | Dates | Delivers | Exit criterion |
|---|---|---|---|
{{milestones:each:| {1} {2} | {3} | {4} | {5} |}}

**North star:** {{north star:line}}

**Deadline:** {{deadline:line}}

### 3.1 Who builds what, in parallel {{?workstreams}}
| Workstream | Owner | Milestone | Dates |
|---|---|---|---|
{{workstreams}}

## 4. Milestones
{{milestones:each:### {1} — {2}\n- **Dates:** {3}\n- **Delivers:**{4:list}\n- **Done when:** {5}\n- **Retires which risk:** {6}\n- **Needs:** {7}\n}}

## 5. The four risks
| Milestone | Retires which risk, and how we will know |
|---|---|
{{milestones:each:| {1} | {6} |}}

## 6. Usability check before going public
{{usability}}

## 7. Schedule risks and buffer
{{schedule risks}}
- **Buffer:** {{buffer:line}}

## 8. Everything in scope has a milestone
| In scope now | Milestone |
|---|---|
{{coverage}}

{{vision kept in part}}

## 9. Open items
{{open items}}

## 10. Areas covered
| Area | When | Why |
|---|---|---|
{{areas}}

## Appendix A — Workings
### A.1 Owner's answers
{{answers}}
### A.2 Checked against the scope
{{scope check}}
### A.3 Changes from the last version {{?superseded}}
{{superseded}}
