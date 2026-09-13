# Case files — `/adopt`

War stories behind the rules in `commands/adopt.md`. Each heading is pointed to from its rule.

## Sent to a gate that sends you back

**`kish21/UI_to_Prompt` ("Sketch2Prompt"), 2026-09-13.** A browser app with no spine and no docs beyond an
AI Studio template README. `/adopt` wrote `PRODUCT.md`; `#Vision` held only "what it does" and "competition
entry only" — the vision sentence, audience, value proposition, north star and riskiest assumption were all
empty, and the run had recorded that. Its close recommended **`/scope`**, because the first handoff rule
was "no Non-goals → `/scope`" and non-goals are almost never inferable from a repo, so that rule fired for
nearly every adoption. The user ran `/scope`; its Step 0 flagged `#Vision` as incomplete and wrote a
`_Not run_` line pointing at `/vision`. The user asked why they had not been sent to `/vision` in the first
place. The rules had been written from "what is still empty" in no particular order, and none of them
checked whether the phase being recommended would even start. A handoff is a routing decision: it walks
the chain in order and checks the target's `Reads:` line before it names the phase.
