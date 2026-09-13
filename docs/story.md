# The personal story: the vibe coding trap

In this AI era, everyone is building a product. I did too.

Armed with tools like Claude Code, Cursor, and Copilot, I was coding at 100mph. I felt like a superhero. I was spinning up files, adding features in minutes, and generating entire modules with single prompts. We call it "vibe coding." It feels like magic — until the vibe fades and reality hits.

Suddenly, I found myself staring at a product that was slipping away from me. I was completely lost.

Here is exactly how it happened:
1. **I let features creep in that nobody needed:** because the AI made building so easy, I kept adding "cool" ideas. Soon, the core purpose of my app was buried under a mountain of secondary features.
2. **I trusted config settings that silently did nothing:** the AI generated configuration blocks that were silently overridden upstream. Everything looked correct in the files, but the value never flowed end to end.
3. **I relied on green tests while the app was dead in production:** my test suites were passing perfectly, but the critical path the product ran on was broken because of decoupled runtime wiring.
4. **I hardcoded vendor APIs directly into my business logic:** I let the AI wire code straight to a specific vendor's SDK. When I needed to swap providers, I had to refactor half the codebase.
5. **I accidentally exposed secrets and skipped tenant isolation:** a missing security filter almost let users see another customer's data, and placeholder keys were constantly in danger of being committed.

**The lesson:** AI is an incredible *execution engine*, but it is not a *discipline engine*. Build without guardrails and it does not just build your product — it multiplies the entropy, debt and chaos at 100mph.

So I wrote a playbook. Not a document — executable skills with evidence-based gates that force both me and the AI to keep engineering discipline, one step at a time. What it enforces is the process; the judgment stays mine.
