# Choosing the shape — the split, and how folders are organised

> Opened by /structure at Step 2, before anything is drawn. SKILL.md carries the two decisions; this
> file carries the reasoning, the worked example and the failure each rule came from.

## §The split — classified from the product, never asked

A product with a **user-facing UI** *and* server-side logic, data or externals is **full-stack, and
full-stack is two folders**: a backend package and `frontend/` side by side. The stack decides the names
*inside* each folder; it does not decide whether the split exists.

**A UI-tooling constraint binds the UI only.** React and shadcn decide what `frontend/` is written in.
They say nothing about the server language — and letting them imply one is exactly how a full-stack
product became a single TypeScript app: `/architect` collapsed the stack row, `/structure` derives shape
from that row, and nothing classified the shape from the *product*. Every gate passed.

**The tell that it had gone wrong:** the AI-prompts rule points at a backend package, there was none, and
the run recorded a *deviation* to put `prompts/` elsewhere. The skill hit its own rule, found the target
missing, and worked around it instead of asking why a full-stack AI product had no backend package.

So: **collapsing full-stack into one app is the exception and is recorded with a reason.** It used to be
the other way round — the collapse was silent and the correct placement is what needed a note. And if
`#Architecture`'s stack implies a shape that disagrees with the classification, **surface it rather than
following the stack** (`MECHANISMS.md` §Step 3c).

## §Modules or layers — where a feature lives

**Dependencies point inward in both shapes** — routes may call domain logic; domain logic never imports a
route or a vendor SDK. That rule is not the question here.

The question is **where a feature lives**. Take a real one — "how a bill is split" — and count the
folders it lands in. In a domain-module tree: one. In a layer tree: `domain/money.ts` +
`db/repositories/split-repository.ts` + `schemas/api-v1.ts` + `components/features/item-assignment/` —
four, because each folder holds a *file type* rather than a *concern*.

`PRINCIPLES.md` says **one module = one concern**, and in product terms a concern is `split`, `ocr`,
`bills`. **`schemas/` is not a concern, it is a file type.** A tree of file types satisfies the letter of
that rule while inverting its intent: the thing a developer actually changes is the one thing that is not
modular.

- **Domain modules — the default.** Two or more concerns with their own rules, which is most products.
  One folder per thing the product *does*, holding everything that concern needs — its types, its
  persistence, its logic — and declaring what it may depend on.
- **Layers** — a genuinely single-concern service (one CRUD resource, a thin gateway, a library), or a
  team that already works that way. Then `layered-shapes.md` is the shape.

```
src/
├── queue/        # position + wait estimate. service.ts · routes.ts · schema.ts · queue.test.ts  Depends on: nothing
├── parties/      # persistence, host-link identity, seating state. + store.ts            Depends on: db
├── notify/       # a turn -> a typed TableReadyText, behind a config-selected interface. Depends on: SMS provider
├── platform/     # ONLY what no module owns: db connection, clock, ids, logger, config loader
└── app.ts        # the registry: registerQueue(app) · registerParties(app) · registerNotify(app) - one line each
```

**Each module owns its own boundary types** — the typed contract in and out lives with the module, not in
a global `schemas/`. A module's dependency line is part of its definition: write it down, and a module
that depends on everything is a module nobody has decided yet.

## §A module is a complete lane — routes and tests inside, one registry line outside

A module folder that holds only the rules, while *every* module's handlers sit in one `http/` folder and
*every* module's stores in one `platform/` folder, is by-role in name and by-tool in practice: the thing
two people change at once is the shared folder. On one real run seven of fifteen tickets named
`backend/src/index.ts`, and the backlog could not be split between two people however it was grouped.
(case file: The drawers everyone reached into)

1. **A module folder holds everything for its responsibility** — its rules, its own store or adapter,
   **its routes and handlers**, its boundary types, **its tests**. `parties/{service,store,routes,schema}.ts
   + parties.test.ts`, not `http/party-handlers.ts` + `platform/sqlite-parties-store.ts` + `tests/parties/`.
2. **The app reaches a module through ONE registry line.** `app.ts` (the route table, the DI wiring) is the
   only code file every module touches, and each module adds exactly one line to it. A shared handlers or
   routes folder is the layer shape wearing a module's name.
3. **`platform/` (or `shared/`) holds only what no module owns** — the db connection, clock, ids, logger,
   the config loader. A store used by one module lives in that module.
4. **The frontend follows the same rule** when it has more than one module: `join/`, `wait/`,
   `host/` each with its page, its components, its API calls and its tests; `ui/` only for the
   `DESIGN.md` parts with no product logic; `app.tsx` is the route registry.
5. **Name the hub files in `STRUCTURE.md`** under a `## Hub files` heading — the registry files, the
   config loader, the dependency manifest: the files every lane may touch by one line. `/tickets` lists
   them as shared, and `check_structure.py` verifies each exists.
   Three or more hub files that are not registries is the tell that a folder is still shared by tool.

**Cost, as a side effect:** `STRUCTURE.md` writes one rationale per folder, so four modules is a shorter
document than thirteen layers, with nothing lost.
