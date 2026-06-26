This file provides guidance to Claude Code (claude.ai/code) and other AI agents
working in this repository. These instructions OVERRIDE default behavior.

This is a **bootstrap template**: a modular-monolith FastAPI app in the
**cosmic-python** layout. Copy it, rename the example modules (`catalog`,
`ordering`), and build your own. The architecture is enforced by tooling
(`import-linter` + `tests/architecture/`), so the rules below are checkable, not
just advisory.

## Hard Rules

**Git:** Never commit directly to `main`/`master`. Always work on a feature branch.

**Naming:** Use full, descriptive identifiers everywhere — variables, parameters,
loop targets, comprehension binds. No single-letter or abbreviated names (`r`,
`b`, `uow`, `cmd`, `idx`, `cb`, etc.) even in one-liners. Prefer `for row in rows`,
`unit_of_work` over `uow`, `command` over `cmd`. Narrow exceptions: `i`/`j`/`k`
for numeric counters, `x`/`y` for coordinates. Rename short names you encounter
while editing.

**Imports:** All imports go at module top-level — never inside a function or
method body. The one sanctioned exception is the deferred imports in
`SqlAlchemyUnitOfWork._enter` and `register_all_orm_mappings()`, which exist to
break a load-time cycle and are documented `import-linter` carve-outs.

## Commands

Requires: Python 3.14+, `uv`, `just`, Docker (for Postgres).

```
just dev-api            # Run the API locally (hot-reload, :8000, Swagger at /api/v1/docs)
just db                 # Start PostgreSQL 17 (Docker)
just create-migration "msg"  # Autogenerate an Alembic migration
just apply-migration    # Apply pending migrations
just test               # Run the full test suite
just test tests/catalog # Run one module's tests
just arch-test          # Run tests/architecture/
just lint               # ruff check + format check
just lint-imports       # Run the import-linter contracts
```

## Architecture

Each business capability is a self-contained **module** with its own
`domain → adapters → service_layer → entrypoints` stack. Modules talk to each
other **only** through a public façade.

**Modules** (the two shipped are examples — rename/replace them):

| Module | Concerns |
| --- | --- |
| `api/catalog` | Products: create/update/discontinue, list (a *producer* of events) |
| `api/ordering` | Orders: place/cancel; validates products via the catalog façade; *subscribes* to catalog events |
| `api/shared` | Cross-cutting kernel: UoW, MessageBus, base events/errors, DB, settings, schemas, auth seam |
| `api/entrypoints` | Composition root (`create_app`), root settings, error handlers |

**Entry point:** `src/api/entrypoints/main.py::create_app()` is the composition
root. It loads ORM mappings, mounts each module's router, builds the in-process
`MessageBus`, calls every module's `register_handlers(bus)`, and registers the
`DomainError → HTTP` translators. Base path is `/api/v1`.

**Dependency direction within each module** (enforced, exhaustive):

```
entrypoints  →  service_layer  →  adapters  →  domain  ←  settings
```

`entrypoints` is the only layer that knows HTTP. `service_layer` never imports
`fastapi` or an `AsyncSession`. `domain` is pure Python — no `fastapi`,
`sqlalchemy`, `pydantic`, or `starlette`.

**Public façade** — the only sanctioned cross-module imports:

```python
from api.catalog.service_layer.queries import get_product      # reads
from api.catalog.service_layer.commands import create_product   # writes
from api.catalog.domain.events import ProductDiscontinued       # integration messages
from api.catalog.domain.commands import DiscontinueProduct
from api.catalog.domain.errors import ProductNotFoundError
```

Anything else (`api.<other>.adapters.*`, `api.<other>.entrypoints.*`,
`api.<other>.domain.models`, `api.<other>.domain.enums`) is forbidden by
`import-linter`. If you need a sibling's data, add a `service_layer.queries`
handler in the owning module, or read a value off the returned aggregate (a
domain property) — don't import its internals.

**Carve-out policy:** a new cross-module import not on the façade needs an entry
in `pyproject.toml`'s `ignore_imports` *with a comment explaining why*, a real
importer, and reviewer sign-off. Prefer a `service_layer.queries` handler.

### Layer rules

Detailed, per-layer rules live in `.claude/rules/`:
`domain-purity.md`, `adapters.md`, `service-layer.md`, `entrypoints.md`.
Read the relevant one before editing a layer.

### Key patterns

- **Depth-counted UnitOfWork** (`shared/infrastructure/unit_of_work.py`):
  `async with unit_of_work:` is reentrant; only the outermost block commits, so
  a handler can compose other handlers under one transaction. The UoW holds
  every module's repositories (`unit_of_work.catalog_products`, …) on one
  session. It is the Postgres transaction boundary.
- **Domain models** are framework-free dataclasses in `domain/models.py`,
  mapped imperatively in `adapters/orm.py` via
  `mapper_registry.map_imperatively(...)`. Mapped entities are mutable and not
  slotted (SQLAlchemy hydrates in place); commands/events are frozen + slotted.
- **Errors:** service handlers raise `DomainError` subclasses; `create_app()`
  translates each base class to its HTTP status. Module subclasses inherit
  dispatch.
- **Events:** handlers append to `unit_of_work.collected_events`; the
  `MessageBus` delivers them post-commit via `dispatch_events`. Subscribe in a
  module's `entrypoints/event_handlers.py`.
- **Routers** are thin: parse → build `Command` / query params → call the
  handler with the injected UoW → serialise via `schemas.py`. No business logic,
  no `HTTPException`, no SQLAlchemy.
- **Schemas** inherit `BaseSchema` (camelCase on the wire). Reuse
  `PaginationParams` / `PaginationMeta`.

## Adding a new module

1. `mkdir -p src/api/<module>/{domain,adapters,service_layer,entrypoints}` (+ `__init__.py`).
2. `domain/`: `models.py`, `commands.py`, `events.py`, `errors.py`, `enums.py`.
3. `adapters/`: `orm.py` (Table + `map_imperatively`) and `repositories.py`
   (ABC + SQLAlchemy impl). Add the module to `register_all_orm_mappings()`.
4. `service_layer/`: `commands.py` + `queries.py` (`(…, unit_of_work) -> result`).
5. `entrypoints/`: `api.py` (router), `schemas.py`, `event_handlers.py`
   (`register_handlers`), optional `dependencies.py`. Add `settings.py`.
6. Add a repo slot to `SqlAlchemyUnitOfWork._enter` + `AbstractUnitOfWork`.
7. Wire it in `create_app()`: `include_router` + `register_<module>_handlers(bus)`.
8. Add the module to the `import-linter` `independence` + `layers` contracts and
   the `domain`/`service_layer` forbidden contracts in `pyproject.toml`.
9. Tests under `tests/<module>/{domain,adapters,service_layer,rest}/`.
10. Run `just lint-imports` and `just arch-test`.

## Tests

Module-first: everything scoped to one module lives under `tests/<module>/`,
mirroring the source layers (`domain/`, `adapters/`, `service_layer/`, `rest/`).
Cross-module/system flows go in `tests/integration/`. Architecture invariants
live in `tests/architecture/`.

- Group tests in classes by scenario; docstrings follow GIVEN-WHEN-THEN.
- Use `tests/factory.py` to build domain objects; `tests/fakes.py` for the
  in-memory UoW + repositories (service-layer and router tests need no DB).
- Adapter tests run against in-memory SQLite (`db_session` fixture) — no Docker.
- Override dependencies via `app.dependency_overrides[dep_fn] = lambda: fake` —
  never patch internals. For router tests override `get_unit_of_work` and
  `get_current_user`.
- Run `just lint-imports` / `just arch-test` after changes that touch module
  boundaries.
