<!-- /architect's fields. The run writes ONE fields file outside the repo: `### <field>` on its own line,
the field's text under it (a heading inside a field is `####`). `status.py set architect filled --from-fields <file>`
renders PRODUCT.md#Architecture (the AI's summary), docs/architecture.md (the human story, numbered headings) and, only
for a decision that CHANGED on a re-run, docs/adr/NNNN-<slug>.md - so each fact is typed once. `status.py fields
architect` prints this file; a run never opens it or templates/architecture.md. -->
## Writing rules
- Plain words in full sentences a newcomer can read aloud; no slash-joined word lists; no playbook words (`/structure`,
  "gate", "phase") in the document's sections; a term a newcomer would not know is explained in `conventions`.
- IDs, each defined once: C constraint · R rule · D decision · I interface · RK risk · Q open question · A owner answer.
  A MUST or NEVER lives only in `rules`; a choice and the options that lost only in `decisions`; elsewhere a few plain
  words and the ID (`EU only (C3)`).
- A number is a FACT (points to its Appendix B or D line), a TARGET (names the C# or A# it serves) or an ESTIMATE
  (`(estimate)` with its working). Every number has its unit; every date is YYYY-MM-DD. No LaTeX.
- An unknown is a Q# with what we assume until then - never "maybe" or "TBD". No product, vendor or library that no
  search or owner answer named.
- Diagrams (```mermaid): plain words on every arrow ("run the pilot", "score the results"), never a tool command.
  Draw every check that holds, blocks or reroutes as a branch (`alt` in a sequence, a `{decision}` node in a
  flowchart). The source of the data (a fake-data generator included) and the output that proves the north star are
  boxes of their own. Every user action #Scope names (approve, ignore, "not for me" ...) is on the context diagram.
- Kinds (the first row of the overview's table names every kind the product is) add lines, placed after the named
  section's table: web app - (security) Sessions · (running) Browsers and screens. SaaS - (data) Tenancy, Customer exit ·
  (security) Accounts · (running) Plans and limits. API - (building blocks) API contract · (running) Rate limits. AI
  agent - (ai part) Loop limits, Acts as, Untrusted input, Stop switch, Reversible, Memory, Hand-over, Disclosure, More than one
  agent. Mobile - (data) Offline and sync · (running) Release. Scheduled job - (data) Input contract, Run record ·
  (running) Started by, Deadline, Backfill, Volume. Pipeline - (data) Delivery · (running) Backlog. CLI or library -
  (building blocks) the interfaces are the public API · (running) Release.
- Provenance, on every stack, custody, runtime and identity row and every decision: `user-chosen` (the user picked
  that option) or `default taken, not user-chosen` (you recommended it; "go with your recommendation" included).

## Fields
- constraints - round 1's answers, one `- <key>: <answer>` line each: team · money · infrastructure (managed only ·
  some · self-host - the option the user picked, as worded) · lock-in · data location · login (`none: its own accounts`
  when nobody uses a company login) · already chosen
- stack - one `- <area>: <choice and version>, <one-line why> — <provenance>` per row (language, framework, datastore,
  key libraries); a paid item names its trigger to adopt
- data custody - one line: where the data lives (local or self-hosted · managed-serverless · embedded), why — provenance
- runtime [table: Unit | Category | Host and region | Cost and free-tier limits | Provenance] - one row per deployable
  unit; Category is one of container-anywhere · PaaS · VPS · user's machine · static site / CDN · CI; a later move of
  the same unit is its own row (`from M4, ...`)
- identity - one line: who holds the login, how the app checks it (a stable user id, a role, fails closed) —
  provenance; `N/A - nobody logs in` only when constraints' login is `none`
- dev tooling - five lines: `- hook runner: ...` · `- secret scanner: ...` · `- task runner: ...` ·
  `- formatter/linter: ...` · `- dependency manifest: ...`; Python or TypeScript adds `- type checker: ...`
- externals [table: External | Used for | Adapter interface | Timeout · retry · if it is down | Stand-in for local work
  and CI | How to replace it] - every system the product calls and does not own; the interface name plain (LLMProvider)
- concerns - five lines: `- resilience: ...` · `- budget: ...` (latency and cost per operation, from the dominant cost)
  · `- migrations: ...` (or N/A without a SQL database) · `- security: ...` (secrets in .env, the scanner) ·
  `- observability: ...`
- ai [AI product] - `- prompt versioning: ...` · `- eval harness: ...` · `- tracing: ...` · `- model: <id>, released
  YYYY-MM-DD, <region or endpoint>` (from its page this run) · `- runtime config: max_tokens ... · timeout ... ·
  thinking ... · retry and refusal fallback ... · caching ... · streaming ...`
- cost per use [AI product] - numbers only, the script works it out and checks it against #Vision's cap: `- use:
  <answer, conversation ...>` · `- calls per use: <n>` · `- worst case calls: <n>` · `- input tokens: <n>` · `- output
  tokens: <n incl. thinking>` · `- input price per 1M: <n>` · `- output price per 1M: <n>` · `- currency: <€ or $>` ·
  `- source: <the pricing page you opened>`
- agent [Agent: yes] - AGENT.md §Architect's ten rows, `1. Framework: ... — <provenance>` to `10. AI disclosure: ...`
- decisions - one block per load-bearing decision, 4-10, the most consequential first, technology choices AND the
  system's own principles (patterns applied, anti-patterns avoided): `#### D1. <the decision, one sentence>` then
  `- problem: <what it solves>` · `- options: <the options considered>` · `- why: <why this one, C# or A#>` · `- costs:
  <what it costs or rules out>` · `- revisit: <a trigger>` · `- rule: <R# or none>` · `- provenance: <one of the two>`
- change D<n> [re-run only] - a recorded decision that changed: `- was: ...` · `- now: ...` · `- why: ...` ·
  `- affects: ...`; the script writes the ADR and marks the decision superseded
- overview - 3-5 sentences (what it is, who or what uses it, its shape, the one or two ideas the design rests on), the
  context diagram (the product one box, its boundaries as subgraphs, each arrow saying what crosses it), then the
  summary table `| Area | Choice | Why (C# / A#) | D# |` (kind, language and framework, where it runs, data store, then
  2-6 areas the product has)
- what drives the design - `| # | Constraint | Number | Source | Proven by |`, 4-10 rows, the most decisive first;
  then `**Out of scope for this architecture:**` the non-goals and deferred items, one line each
- rules - `| # | Rule | From | Enforced by [block] | Proven by |`, 4-10 rows, each a MUST or NEVER sentence
- how it works - 5-10 numbered steps (who, what, what is checked, where in the code), the sequence diagram with a
  `Note` per step and every check as an `alt` branch, then `**When a step fails:**` `| Step | What can go wrong | What
  the product does | What the user or operator sees |` and `**Other flows:**`
- building blocks - `| Block | Responsible for | Owns | Calls |` (3-8 domain modules such as `billing/`), then
  `**Interfaces:**` `| # | Interface | Called by | In → out | Errors | Sync or async | Who may call |`; the externals
  table is added by the script
- data - `| Entity | Key fields and links | Sensitivity now → with real data | Stored in | Kept for · deleted how |`, then
  **States of <record>:**, **Consistency:**, **What leaves the boundary:**, **Schema changes:**
- conventions and terms - `| Concern | Convention | Enforced where |` (money, time, identifiers, error shape, log
  fields, configuration keys), then `**Terms:**`
- security and privacy - `| Concern | How it is handled | Enforced by (layer) |` (people's identity, the process's
  identity, who can do what, secrets, data protection, audit trail), then the top 2-5 threats; a law is named only with
  its source and the specific obligation
- ai part [AI product] - what the model does and never does, actions and tiers, guardrails in code, how it is checked
  (`| Check | When it runs | Pass bar |`; when a person approves or edits the AI's text, a check on the final approved
  text at that moment), prompt versions and tracing, if the model is down or wrong; the model, runtime and cost lines
  are added by the script
- running it - Started by · First day (what a developer runs on their own machine, e.g. a local database, never the
  paid managed one) · Ship a change · Watched · Backup and recovery · the monthly cost table (`| Item |
  Plan or size | <currency> a month | Source |` with a **Total** against a C#) · Deliberately left out for now; the
  runtime table and the tooling line are added by the script
- mapping to the plan - `| Milestone | Needs from the architecture | Decisions it may reopen |`, one row per #Plan
  milestone (M1 ...), then `**Scope items:**` every #Scope "in now" item and table stake with where it lives here
- risks and open questions - `| # | Risk | Likelihood · impact | What reduces it | Watched by |`, then `| # | Open
  question | Who answers | Needed by | Until then we assume | Blocks |`
- answers - Appendix A: each question in short, then the owner's answer word for word, `A1.` ...; a picked option as
  `picked: <option text>`
- searches - Appendix B: one line per search `- <decision> · <query> · what it settled · <link to the page you opened>`
- options [optional] - Appendix C: the options shown before each question, one line each (agent: `#### Framework
  options`, a 3-4 row table with a registry link per version)
- sources - Appendix D: links the body relies on that Appendix B lacks (or `none beyond Appendix B`), then
  `**Not verified:**` and each fact no page you opened confirmed (or `nothing - every fact has its page in Appendix B`)
- plan notes [optional] - a choice this run that changes #Plan or #Scope (the user's answer wins - never ask which
  side wins): `- <M5 or the line's first words>: <what changes> - because <the answer>`; the script writes the dated
  `superseded` note on that line
- open items [optional] - `- <what is still open> | <what clears it>`: recorded in STATUS.md in the same save
