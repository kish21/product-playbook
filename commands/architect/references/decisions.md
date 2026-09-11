# The decisions that are not stack trivia

> Opened by `/architect` at Step 2. `SKILL.md` names each decision and why it is load-bearing; this file
> carries the questions to ask, the trade-offs, and the failures each rule came from.

## §Custody, runtime and identity

3. **Custody + runtime target — three questions that are NOT stack trivia.** The deployment target decides
   whether a compose file is even the right artifact, whether connection strings or a local service get
   scaffolded, and it is expensive to reverse once `/structure` and `/foundation` have built on it:
   - **Where does the data live?** Local/self-hosted · managed-serverless · embedded. One line of trade-off
     each, and name the **vision-driven** consideration (privacy · cost · portability · lock-in).
   - **Where does this run?** Container-anywhere · a specific PaaS · a VPS · the user's own machine.
     **This is what tells `/structure` and `/foundation` what to scaffold — and it is what `/deploy`
     later EXECUTES**, so record the category, not just a brand name. For a long time this decision was
     recorded and never carried out by anything: `/ship` then assumed a deployed environment nothing had
     created.
   - **Who holds identity?** Self-hosted auth vs the datastore vendor's auth + row-level security. If the
     user already pays for a platform, the "free" self-hosted option may not be the cheaper one. Record
     which, because the **test-isolation recipe follows from it** — `/foundation`'s
     `references/test-datastore.md` branches on exactly this line, and a custody choice made without that
     downstream cost in view is the one that makes the test datastore unaffordable later.
   PRINCIPLES' *defer paid infra until a real need* biases all three toward local — a sensible default, but
   **it must be a stated default the user can decline, not an unvoiced one.** If the user has no opinion,
   recommend one with a reason and **record it as "default taken, not user-chosen"**. Get the same yes/no
   the rest of the stack recommendation gets.

## §AI runtime config

7. **If it's an AI product:** decide **prompt-versioning**, an **eval harness**, **LLM
   tracing/observability** — and the **model runtime config**, as ADRs (don't let them emerge). The
   runtime config is the one that was missing and the one the budget depends on: **model id · thinking /
   reasoning effort · `max_tokens` · timeout · streaming · retry and refusal fallback · prompt caching**.
   Current frontier models run adaptive thinking **by default** and thinking bills as output, so a budget
   written without these is unachievable by construction — on a real run a recorded `≤$0.03/scan` was
   ~$0.05 the moment defaults applied. **Tie the Step-5 budget to this recorded config**, so the number
   and the settings that produce it are read together.

## §Where approvals attach — the self-host blind spot

**Trigger:** the product integrates anything gated by a third party's approval.

- **Check where approvals attach (the self-host blind spot):** for any integration gated by a third
  party's approval — platform publishing APIs, app-store distribution, payment onboarding, regulated-data
  access — ask *"does the approval attach to the app/account, or to the software?"* If it attaches to the
  app, **self-hosting OSS does not bypass it**: you still register and pass every review, so OSS saves
  code, not compliance — and an aggregator renting out its approvals may beat both. Benchmark all three
  routes on **time-to-first-working-result including review wait**, not code effort. Unapproved apps tend
  to fail *silently* (a shipped video product hit this: YouTube force-privates uploads).
