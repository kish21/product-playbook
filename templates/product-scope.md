<!-- /scope's fields and its PRODUCT.md section: the run writes ONE fields file (`### <field>` + its text, for
every field below); `status.py set scope filled --from-fields <file>` renders docs/scope.md (templates/scope.md) and
the section below `## Section`, each fact typed once. The syntax is templates/product-vision.md's. -->
## Fields
- core feature - ONE sentence: the one thing the first version does, in clear words; the first `in scope` row builds it
- why core - 2-3 plain sentences: why this one capability, alone, shows the product works (the riskiest assumption it tests)
- example - one concrete case of it: one person, one moment, with names and numbers, marked `(illustrative)` when invented (`(owner)` when the owner gave it)
- core loop - a ```mermaid flowchart: what starts it, what the product does, what the person sees or gets, what we learn
- capacity - who builds the first version · hours a week · how many weeks, as the user answered or picked (a concrete value)
- in scope [table: Item | What the user can do | Done when | Moves which number] - one row per in-scope item; Done when = a check anyone can run
- shape [table: Week | What gets done] - the first version week by week (or day by day), within the capacity
- deferred [table: Item | Comes in when] - one row per item left for later; Comes in when = `when <the signal, with a number where there is one>`; an item that extends the core starts `beyond the core:`
- never [table: Item | Why not] - one row per thing deliberately never built
- table stakes [table: Item | Decision] - one row for EVERY item the start lists; Decision = `in now` · `deferred - when <trigger>` · `N/A - <reason>`
- failure - 2-4 plain sentences: what we would see if the first version fails (the number that shows it) and what we would do then
- vision check [table: Vision promise | In this scope] - one row per vision promise: the vision line, who it's for, the job, each step of the worked example, the north star, the AI line (an AI product); In this scope = `kept` · `deferred - <reason>` · `changed - <how, and who picked it>`, never a bare `agrees`
- decisions [table: Decision | Why | Who decided] - one row per decision this scope took; Who decided = owner · picked from our options · proposed
- options considered - `- **<option>.** <why it is not the core>` per option
- answers - each of the owner's answers word for word, one per question; a picked option as `picked: <option text>`
- numbers [optional] [table: Number | From] - every number in this scope; From = owner · from the vision (owner's answer, not yet worked out) · proposed
- read [optional] - only an input file you opened yourself beyond what `next` printed: one line per file, as `status.py quote <file> "<words>"` prints it (`<file> · <date> · "<quote>"`)
- superseded [optional] - a re-run that reverses a recorded decision: `superseded <date>: <the old decision> - <why>` per line

## Section
- **THE core feature:** {{core feature:line}}
- **Capacity:** {{capacity:line}}
- **In scope (now):**
{{in scope:each:  - {1}: {2} - done when {3} (moves {4})}}
- **Deferred:**
{{deferred:each:  - {1} - {2}}}
- **Non-goals:**
{{never:each:  - {1} - {2}}}
- **Table stakes:**
{{table stakes:each:  - {1}: {2}}}
- **Superseded:** {{superseded:line}}
- **Detail:** `docs/scope.md` (the story for people; this section is the summary every later phase reads)
- **Read (file · date · verbatim quote):** none
