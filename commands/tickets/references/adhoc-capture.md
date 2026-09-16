# Mode B — ad-hoc issue capture (`/tickets "<description>"`)

> Opened only when `/tickets` is invoked WITH a description. Bare `/tickets` is batch decomposition
> (Mode A) and never reads this file.

Triggered mid-build by `/tickets "Bug: Gemini API timeout is unhandled on slow 3G"`. **Fast path — touch nothing else.**
1. **Classify** the text: `bug` · `edge-case` · `tech-debt` · `security`. Security items are never downgraded.
2. **Locate the owning file and its lane** via `STRUCTURE.md` + the architecture: the example above is an LLM
   provider concern → `src/providers/llm/geminiProvider.ts`, in the lane of the module that holds it. Confirm the
   path exists; if you cannot resolve one confidently, say so and record the candidates rather than guessing a
   path into the ticket.
3. **Write one ticket** `[ADHOC-<nn>]` into `docs/issues/` using the same template, filling: what happened ·
   expected vs actual · reproduction or trigger condition · affected file(s) · suspected cause · a DoD that
   includes a **regression test proving the fix**.
4. **Publish** it as a single issue with the classification as a label, its ticket file as the body, unchanged
   (`publishing.md` §An issue body is its ticket file), subject to the same dedup and remote guards from Step 2,
   **plus a real parent reference**: resolve the parent ticket's *issue number* from the dedup index already
   fetched in Step 2 and write `#N` into the ticket file, so GitHub renders the bidirectional timeline link.
   **A parent with no published issue degrades to the plain ID with the reason stated — never a guessed
   number**, which would link the bug to an unrelated issue. It carries its lane's `lane:` and `owner:` labels
   and gets its card on the Delivery Board with all four fields set (`publishing.md` §The Delivery Board).
5. **Do not** read `#Plan`, regenerate, renumber or modify any milestone ticket or epic, or edit `TICKETS.md` —
   a bug is not part of the plan. One invocation, one issue.
