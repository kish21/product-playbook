---
name: architect
description: >
  Phase 2 (Development), step 1 of product-playbook. Decide the tech stack + tools + key
  architecture decisions, benchmarked to the best current-year open-source options, aligned
  to the product. Use at the start of building, or run /architect "what stack", "tech
  decisions", "how should we build this". Writes the Architecture section of PRODUCT.md.
  Run /structure next.
---

# `/architect` — Phase 2 · Development ① · run as an **architect**

> Part of **product-playbook**. Reads + updates the shared spine `PRODUCT.md`.
> Apply `PRINCIPLES.md` (bundled `PRINCIPLES.md`; see README for its path per install mode) — load-bearing this phase:
> **benchmark best-2026-OSS**, **patterns & anti-patterns**, **provider/adapter for externals**,
> **resilience strategy**, **perf/cost budget**, **migrations (not raw schema)**, **no-hardcoding /
> no secret in code**, **typed-contracts intent**, **layered/decoupled**. (Depth lives in Step 2 +
> PRINCIPLES; the gate below just confirms it's recorded and real.)

## Contract
- **Purpose:** choose the stack/tools/decisions before any folders exist, aligned to the product.
- **Reads:** `PRODUCT.md#Vision`, `#Scope`, `#Plan`.
- **Writes:** `PRODUCT.md#Architecture` — stack+tools+why · ADRs · externals behind adapters · resilience · perf/cost budget · (AI) prompt-versioning/eval.
- **Exit criteria (the gate — small: is the section complete?):**
  - [ ] `#Architecture` is complete and **traces to scope/plan** (no gold-plating): stack+tools+why, every external behind an adapter, key ADRs (incl. patterns applied / anti-patterns avoided), migrations approach, and the **decisions for the concern areas this product needs** — resilience · perf/cost budget · security/no-secret-in-code · observability, **+ (AI) prompt-versioning/eval/tracing** — each recorded or marked **N/A**.

## Step 0 — Context + prior-gate check
- Read `#Vision/#Scope/#Plan`. If `#Scope`/`#Plan` are empty, warn and offer to run them first (allow override).
- Brownfield: detect the existing stack from the repo and record it as the starting point.

## Step 1 — Apply principles (this phase)
- **Benchmark to the current year, OSS-first:** pick what leading teams use *now*; prefer open source unless told otherwise. Justify each choice in one line.
- **Patterns & anti-patterns awareness:** know the established design patterns for this kind of system *and* its common anti-patterns (e.g. god-objects, tight coupling to a vendor, dead config, N+1 / blocking the event loop, distributed-monolith). Apply the right patterns; consciously avoid the anti-patterns — adapted to *this* project, not cargo-culted.
- **Provider/adapter for every external:** no vendor SDK in business logic — wrap it behind a config-selected interface so it's swappable via `.env`.
- **No-hardcoding & typed contracts:** decisions must keep values in config and payloads typed.

## Step 2 — Guided decisions
1. **What kind of system is it?** (web app · API · CLI · data/ML · agentic). Match the scope, not ambition.
   Then name the **2–3 design patterns** that fit it and the **2–3 anti-patterns** to avoid (current-year), and how this design honours/avoids them — record the notable ones as ADRs.
2. **Choose the stack core** (language · framework · datastore · key libs). One-line why each; flag anything paid and its trigger to adopt.
3. **List every external** and the **adapter interface** it will hide behind (e.g. `LLMProvider`, `Storage`) — *and* its **failure/resilience strategy** (timeouts · retry-transient-only · fallback/circuit-breaker). This is what keeps it swappable, testable, and resilient.
4. **Set a rough perf/cost budget** where it matters (latency + cost-per-operation), since the stack choice locks it in — or mark **N/A**.
5. **If it's an AI product:** decide **prompt-versioning**, an **eval harness**, and **LLM tracing/observability** as ADRs (don't let them emerge).
6. **Record 2–4 ADRs** for the load-bearing choices (decision · why · rejected alternative).
- Give **one recommendation** for the stack; get a yes/no. Keep it plain — explain *why* for a newcomer.

## Step 3 — Write back to `PRODUCT.md`
Fill `#Architecture`: stack+tools+why · ADRs (patterns/anti-patterns) · externals behind adapters + resilience · perf/cost budget · migrations approach · (AI) prompt-versioning/eval/tracing.

## Step 3b — Principle-gate: verify the decisions are real, not vague
Walk this phase's load-bearing principles (Step 1) and confirm each is **concretely decided**, not hand-waved:
- every external actually has an adapter interface **and** a resilience strategy (no raw vendor SDK in logic);
- patterns/anti-patterns are *addressed by the design*, not just listed;
- secrets go to `.env` (none in code); a migrations approach exists for any datastore.
**If any is vague or missing, STOP and decide it.** (No code yet, so the evidence is concrete, consistent
decisions in `#Architecture`; `/build` later re-verifies them in code via `/code-review`.)

## Step 4 — Handoff
"Stack and decisions recorded. Now build the **first concrete thing**: run **`/structure`** to lay
out clean folders and explain what each is for."
