# FastAPI Domain Template

A **bootstrap** for modular-monolith FastAPI services in the **cosmic-python**
style (Ports & Adapters + service layer + in-process message bus). Each business
capability is a self-contained module — `domain → adapters → service_layer →
entrypoints` — and modules talk to each other only through a narrow public
façade. The boundaries are **enforced by tooling** (`import-linter` +
`tests/architecture/`), so the architecture can't silently rot.

It ships with two worked example modules — **`catalog`** (products) and
**`ordering`** (orders) — that demonstrate the whole pattern, including a
cross-module façade call under one transaction and a cross-module event
reaction.

> Bootstrapping a new project? Copy this repo, then rename/replace `catalog`
> and `ordering` with your own modules. See **"Make it yours"** below.

## Why this exists

- **One place to start.** Batteries-included: UoW, message bus, domain errors →
  HTTP, Alembic, Docker Postgres, tests at every layer, and the architecture
  contracts already wired.
- **Agent-ready.** `CLAUDE.md` + `.claude/rules/` encode the conventions so AI
  agents (and humans) write code that fits the architecture by default.
- **Honest seams.** Auth is a clearly-marked stub; the event-delivery trade-off
  is documented, not hidden.

## Stack

Python 3.14+ · FastAPI · SQLAlchemy 2.0 (async) · Pydantic v2 · Postgres ·
Alembic · `uv` · `just` · `ruff` · `pytest` · `import-linter`.

## Quickstart

```bash
cp .env.tpl .env          # adjust if needed
uv sync                   # install deps (incl. dev group)
just db                   # start Postgres 17 (Docker)
just create-migration "initial schema"   # autogenerate from the ORM
just apply-migration
just dev-api              # http://localhost:8000/api/v1/docs
```

Run the gates anytime (no Docker needed — tests use in-memory SQLite + fakes):

```bash
just test          # full suite
just arch-test     # architecture invariants only
just lint          # ruff check + format check
just lint-imports  # the 4 import-linter contracts
```

## Layout

```
src/api/
├── shared/                 # cross-cutting kernel (not a business module)
│   ├── domain/             # pure-Python: errors, events, identifiers, time, patches
│   ├── infrastructure/     # database, session, unit_of_work, messagebus, repository,
│   │                       #   dependencies, auth
│   └── entrypoints/schemas.py   # BaseSchema, PaginationParams/Meta, UserIdentity
├── catalog/                # ── example module ──
│   ├── domain/             #   models, commands, events, errors, enums (framework-free)
│   ├── adapters/           #   orm.py (imperative mapping) + repositories.py
│   ├── service_layer/      #   commands.py (writes) + queries.py (reads)
│   ├── entrypoints/        #   api.py (router), schemas.py, event_handlers.py
│   └── settings.py         #   CATALOG_ env prefix
├── ordering/               # ── example module (calls catalog via the façade) ──
└── entrypoints/
    ├── main.py             # create_app() — composition root
    ├── _error_handlers.py  # DomainError → HTTP
    └── settings.py
tests/        # module-first: tests/<module>/{domain,adapters,service_layer,rest}/ + integration/ + architecture/
migrations/   # Alembic (env.py calls register_all_orm_mappings)
docs/architecture.md        # the full design rationale
.claude/rules/              # per-layer rules for agents and humans
```

## How a request flows

```
HTTP → entrypoints/api.py     parse → build Command / query params
     → service_layer          open UoW, orchestrate, raise DomainError, collect events
     → adapters/repositories  SQLAlchemy ↔ domain entities
     → domain                 invariants & behaviour (pure Python)
   ← entrypoints/schemas.py    serialise (camelCase) ; DomainError → HTTP centrally
```

The cross-module example: `POST /orders` → `ordering.place_order` calls
`catalog.get_product` (façade) under the same depth-counted UoW to validate the
product and snapshot its price, then emits `OrderPlaced`. Discontinuing a
product emits `ProductDiscontinued`, which ordering subscribes to.

## Make it yours

1. Rename the project in `pyproject.toml`; set `root_path`/title in
   `entrypoints/main.py`.
2. Replace `catalog`/`ordering` with your own modules (see **"Adding a new
   module"** in `CLAUDE.md` — it's a 10-step checklist the contracts verify).
3. Wire real authentication in `shared/infrastructure/auth.py` (the shipped stub
   is dev-only and trusts any token).
4. Tighten `ALLOWED_ORIGINS` in `entrypoints/main.py`.
5. Keep `just lint-imports` + `just arch-test` green — they are your guardrails.

## Learn more

- `docs/architecture.md` — the design: layers, façade, UoW, message bus, the
  contracts, and the event-delivery trade-off.
- `CLAUDE.md` — agent/contributor rules + the "add a module" checklist.
- `.claude/rules/` — focused rules per layer.
- `INDEX.md` — one-screen repository map.
