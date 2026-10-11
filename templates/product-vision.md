<!-- /vision's fields and its PRODUCT.md section. The run writes ONE fields file: `### <field>` on its own line,
the field's text under it, for every field in `## Fields`. `status.py set vision filled --from-fields <file>` renders
docs/vision.md (from templates/vision.md) and the section below `## Section` from it, so each fact is typed once.
`status.py next --phase vision` prints the field list; a run never opens this file.
Field line: `- <name> [optional] [table: <col> | <col>] - <what to write>`. A table field is one `| a | b |` row per
item. In the section and the layout: `{{name}}` the field, `{{name:first}}` its first line, `{{name:rest}}` the lines
after it, `{{name:line}}` all of it on one line, `{{name:each:<pattern>}}` a table field row by row ({1} = column 1). -->
## Fields
- vision - ONE sentence: the world this product creates once it works, not what the product is
- plain words - 2-3 short sentences anyone understands (the problem today, what the product does, what changes), then one sentence on what it is not
- who - first line: the main user and the moment they need this (the owner's words or a picked option); then one `- **<segment or moment>.** <one line>` per main user group
- others [optional] - people inside the business who use it: `- **<role>.** <what they do with it>`
- scale [optional] - how many people, from the brief or a search [n]
- job - when <situation>, I want to <motivation>, so I can <outcome>
- first users - how the first 10 users find it, and why they switch from today's way
- problem - first line: what goes wrong today, for whom; then `- **<case>.** <one line>` per case
- root causes - `- **<root cause>.** <one line [n]>` per cause
- why now - first line: one takeaway (no search behind it: `why now: the owner's claim, not verified`); then `1. **<lead-in>.** <one line [n]>` per reason
- market - first line: how it is solved today, naming 2-3 real comparables (from the searches); then `**Our angle.** <the sharpening insight>`
- solved today [table: Approach | Who does it | Where it falls short] - one row per way it is solved today
- worked example - one real-looking case start to finish, with names and numbers, one line (a number that is not the owner's: illustrative)
- experience [table: When | What happens] - one person's days with the product: Day 0 the trigger, then what the product does, then the outcome
- what makes it work [optional] - `- **<lead-in>.** <one line>` per point
- how it works - first line: one takeaway; then a ```mermaid flowchart (input, steps, decision, what the user sees)
- ai - first line: what the AI does · what a person decides · the accuracy bar · the cost per use (`n/a` when it uses no AI); then any detail
- brief [optional] [table: Brief point | Our answer | Section] - the user gave a brief: one row per point or question of it, in its order
- value - first line: the value proposition, how this is better or different; then `1. **<value driver>.** <one line [n]>` per driver
- business model - free / paid / internal, as the user said or picked
- target - the north-star target: a number and a date
- inputs - the 2-3 input metrics and their numbers, one line
- guardrail - what must not get worse while chasing the target, with its number
- instrumentation - how it is measured ("nothing records this yet" is a finding)
- riskiest - first line: the riskiest assumption; then `- **For:** <evidence [n]>` · `- **Against:** <evidence [n]>` · `- **How we test it:** <the cheapest test>` · `- **Other risks:** <one line each>`
- constraints - first line: the rules that apply · the languages · where the data comes from; then `- **<rule, in plain words>.** What it means for us: <one line [n]>` per rule
- competitors [table: Product | Market | Does | Does not | Same job / nearby] - the owner's market first
- in scope - `- <item>` per line: what the first version includes
- out of scope - `- <item>` per line: what it leaves out
- open questions - `1. <a question still open, and who answers it>` per question
- answers - each of the owner's answers word for word, one per question; a picked option as `picked: <option text>`
- searches - one line per search: `- <why now | local | same job | nearby | rules> · <query> · <what it settled> · <link>`; a name never searched: `- Not searched · <name> · <where the name came from>`
- terms [table: Term | Number | From] - one row per term in the target and the inputs; From = owner · proposed · searched · derived; no bar given: `bar: not set`
- sources - `1. <short name> · <what it is: a page, a law, the owner's claim> · <link>` per footnote [n]
- read [optional] - only an input file you opened yourself beyond what `next` printed: one line per file, as `status.py quote <file> "<words>"` prints it (`<file> · <date> · "<quote>"`)
- superseded [optional] - a re-run that reverses a recorded decision: `superseded <date>: <the old decision> - <why>` per line

## Section
- **Vision:** {{vision:line}}
- **In plain words:** {{plain words:line}}
- **Worked example:** {{worked example:line}}
- **Who it's for:** {{who:first}}
- **Problem (why now):** {{problem:first}} Why now: {{why now:first}}
- **Value proposition:** {{value:first}}
- **Current-year market:** {{market:first}}
- **North star — target + date:** {{target:line}}
- **North star — input metrics:** {{inputs:line}}
- **North star — guardrail:** {{guardrail:line}}
- **North star — instrumentation:** {{instrumentation:line}}
- **Job-to-be-done:** {{job:line}}
- **Riskiest assumption:** {{riskiest:first}}
- **Business model:** {{business model:line}}
- **Constraints:** {{constraints:first}}
- **First users:** {{first users:line}}
- **AI:** {{ai:first}}
- **Superseded:** {{superseded:line}}
- **Detail:** `docs/vision.md` (the story for people; this section is the summary every later phase reads)
- **Read (file · date · verbatim quote):** none
