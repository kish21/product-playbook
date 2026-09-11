# Layered shapes — the per-layer trees

> Opened by /structure **only when Step 2a chose layers** over domain modules. With domain modules
> the tree in SKILL.md Step 2a is the shape and this file does not apply. The dependency-direction
> rule is identical either way.

**Backend** (the proven base — adapt names to the stack):
```
app/
├── api/         # HTTP routes, one file per concern — thin, no business logic
├── domain/      # business/domain logic (the "what")
├── db/          # data access / persistence (repositories, queries)
├── providers/   # adapters for every external (LLM, DB, vendor SDK) — swappable via config
├── infra/       # cross-cutting: logging, audit, rate-limit, cost, circuit-breaker
├── auth/        # authn / authz
├── schemas/     # typed models / DTOs (contracts that cross boundaries)
├── validators/  # input validation
├── config/      # loader + layered config — SEE BELOW — reads .env
├── jobs/        # background / scheduled tasks
└── main.py      # entrypoint
# AI/agentic ONLY (when PRODUCT.md says AI), as app/ sub-packages: agents/ · pipeline/ (orchestration) · app/prompts/ (versioned YAML) · retrieval/
```
**`config/` layered pattern (the no-hardcoding engine) — ACTUALLY CREATE THESE FILES, don't leave
`config/` empty:** `loader.py` (typed loader that reads the YAML + `.env`) + `platform.yaml`
(engine/technical knobs) + `product.yaml` (product/business knobs, change without code) + a root
`.env.example` (secret *names* only). This is *how* you keep secrets and tunables out of code — it is a
deliverable of this skill, not just a description.

**Frontend** (Next.js App Router shown — adapt to the framework):
```
frontend/
├── app/          # routes: one folder per route (+ layouts, pages)
├── components/   # reusable UI, grouped: ui/ (primitives) · features/ · layout/ · auth/
├── lib/          # client utils: api client · hooks · theme · types · constants
├── public/       # static assets / brand
└── middleware.ts # edge middleware (auth, redirects)
```
**Full-stack** = backend `app/` and `frontend/` side by side.
