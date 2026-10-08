# Case files — /design-system

The reasons behind `/design-system`'s rules, moved out of the skill when it was rewritten to the clarity
standard (the skill keeps each rule; the why lives here). A run does not need to read this file.

## The answer we anchored

For aesthetics the user's taste is the primary input, so `/design-system` asks before it proposes — the
opposite order to `/architect`'s (`references/build-loop.md` §Why ask before proposing). A named reference is
the strongest signal the session will get. Proposing a family first and asking second anchors the answer: the
user picks from what they were shown instead of saying what they wanted. The picker's three questions are about
the user's own product, so the user answers them; a recommended answer for each keeps it one short exchange.
The full set of 13 families is named because a picker that shows only a shortlist makes "Other" a request to
invent a family nobody showed them.

## The sample that set a price

This phase does not read `#Plan`, so any number in the sample page has been checked against nothing. The sample
proves the look; a figure copied from it into the product would ship a rule no phase decided. The real rules
arrive with `/contracts` and `/build`.

## The spec that styled nothing

`DESIGN.md` is a specification, and a specification is not a stylesheet. A component written against tokens the
app never defines renders unstyled while typecheck, lint and the audit all stay green, so the tokens are emitted
twice — as the spec and as the stylesheet the app's root entry imports — and a design system that exists only as
a document is a decision nothing executes.

## Why the skill says what it does not do

The skill's edge is real apps, and it reuses shadcn/ui + 21st.dev rather than out-designing them; a brochure page
is better served by a dedicated front-end design skill (Law 19, the honesty boundary). The user is here to learn
design, not only to receive a file — hence the plain-language why on every default. The concrete foundations
step exists because popular design skills omit concrete values, which is the cause of "fonts too small" and
"artsy but wrong". The UI gate mirrors the AI-product conditional; a backend product is not owed a design system,
so it writes nothing — declining and being inapplicable are different states. The principles constrain every
later token, and the laws are a floor the run never lowers.
