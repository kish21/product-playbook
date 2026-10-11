<!-- /plan's fields and its PRODUCT.md section: the run writes ONE fields file (`### <field>` + its text, for
every field below); `status.py set plan filled --from-fields <file>` renders docs/plan.md (templates/plan.md) and the
section below `## Section`, each fact typed once. The syntax is templates/product-vision.md's; in a row pattern,
`{4:list}` puts a cell's `;`-separated parts on their own lines. -->
## Fields
- summary - one takeaway: what is ready on which date
- will prove - what the demo will prove, one line
- will not prove - what it will NOT prove yet (e.g. real demand, until real data), one line
- capacity - who builds it: people × hours a week, from the scope (as confirmed)
- start - the start date, YYYY-MM-DD
- milestones [table: Id | Name | Dates | Delivers | Done when | Retires which risk | Needs] - one row per milestone, core first: Id M1, M2 ...; Dates `YYYY-MM-DD → YYYY-MM-DD` (a worked-out duration: `(derived: <hours> ÷ <hours a week>)`); Delivers: M1 3-5 parts separated by `;`, later ones 1-2 sentences; Done when = a check anyone can run, every #Scope "in now" item in one; Retires = value · usability · feasibility · viability and how we will know; Needs = what must exist first and the milestone or person that delivers it, or `nothing outside this milestone`
- north star [optional] - the plan ends after the north-star date: keep it and flag it · move it · lower the interim bar, as the user picked
- usability - which milestone, how many people try the core task unaided, and what counts as a pass
- schedule risks - `- **<what could slip>.** <what we do if it does>` per risk
- buffer - the slack kept, in days or weeks
- coverage [table: In scope now | Milestone] - one row per #Scope "in now" item (the core feature, each in-scope item, each table stake in now) and the milestone that delivers it
- vision kept in part [optional] - a vision list kept only in part (3 of 4 moments, 5 of 10 first users): what is in, what is out, and why
- open items - `1. <item> · recommended: <value> · decided by: <who, when>` per number or point nobody decided, or `none - every number is the user's`
- areas [table: Area | When | Why] - one row each for security · ai-specific · observability · developer-experience · testing · infra · documentation · product, and one per #Vision constraint (a law, a language); When = `now` · `next` · `later - when <signal>` · `N/A - <reason>`
- answers - each of the owner's answers word for word, one per question; a picked option as `picked: <option text>`
- scope check - one line per thing compared: every milestone traces to the core feature, and no milestone builds what the scope rules out
- read [optional] - only an input file you opened yourself beyond what `next` printed: one line per file, as `status.py quote <file> "<words>"` prints it (`<file> · <date> · "<quote>"`)
- superseded [optional] - a re-run that reverses a recorded decision: `superseded <date>: <the old decision> - <why>` per line

## Section
- **Phases / milestones (core first):**
{{milestones:each:  - {1} — {2}: {4}}}
- **Timeline:** {{capacity:line}}, from {{start:line}}
{{milestones:each:  - {1}: {3}}}
  - North star: {{north star:line}}
- **Exit criteria per milestone:**
{{milestones:each:  - {1}: {5}\n    - Needs: {7}}}
- **Four-risks row per milestone (value · usability · feasibility · viability):**
{{milestones:each:  - {1}: {6}}}
- **Usability checkpoint before going public:** {{usability:line}}
- **Concern-area coverage:**
{{areas:each:  - {1}: {2} - {3}}}
- **Schedule risks + buffer:** {{schedule risks:line}} Buffer: {{buffer:line}}
- **Open items:** {{open items:line}}
- **Superseded:** {{superseded:line}}
- **Detail:** `docs/plan.md` (the whole plan for people; this section is the summary every later phase reads)
- **Read (file · date · verbatim quote):** none
