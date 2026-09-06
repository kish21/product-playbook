# Case files — `/contracts`

War stories behind the rules in `commands/contracts.md`. Each heading is pointed to from its rule.

## The template the parser read differently

**product-playbook #64, 2026-09-06.** The `/tickets` issue template gained a `Lane` field and
guidance for the `Target Files` list so that Lanekeeper (which parses the issue body as the lane
boundary) would read it. The headings were checked against Lanekeeper's config defaults — they
matched — and the change was ready to publish.

Running Lanekeeper's actual `boundary.read` on a ticket filled from the template returned **six
paths, not three**: the parser takes every backticked span under the heading, and the guidance
comment said "a file such as `src/services/quoteEngine.ts`, never `src/services/`". The
pre-existing template had carried the same defect for three releases. A second run with the Lane
field left blank returned the **HTML comment as the lane name**, because the section runs to the
next heading and nothing strips comments.

Both were fixed by template layout (no backticks in that comment; the Lane comment moved above its
heading) and a Lanekeeper issue was filed for the parser. Neither would have been found by reading
the parser's heading list, which is what "verifying the contract" had meant up to that point. The
consumer's code is the spec; a filled example through it is the test.
