# Architecture

A **modular-monolith** FastAPI application in the **cosmic-python**
(Ports & Adapters + service layer + message bus) style. One deployable, many
independent modules; the boundaries between them are enforced by tooling, not
convention.

## Why this shape

- **Modules over layers.** Code that changes together lives together. A feature
  touches one module's `domain → adapters → service_layer → entrypoints` stack,
  not four top-level `models/`, `schemas/`, `routers/` folders.
- **A monolith you could split later.** Modules only touch each other through a
  narrow public façade, so a module can be extracted into its own service with
  minimal surgery — the seams already exist.
- **Enforced, not hoped-for.** `import-linter` contracts + `tests/architecture/`
  fail the build when a boundary is crossed. The architecture can't quietly rot.

## The layers (within each module)

```
entrypoints  →  service_layer  →  adapters  →  domain  ←  settings
```

| Layer | Knows about | Never imports |
| --- | --- | --- |
| `domain` | pure Python | `fastapi`, `sqlalchemy`, `pydantic`, `starlette` |
| `adapters` | `domain`, `shared.infrastructure` | `service_layer`, `entrypoints` |
| `service_layer` | `domain`, `adapters`, the façade | `fastapi`, `AsyncSession` |
| `entrypoints` | everything below | — |

- **domain** — framework-free dataclasses (`models.py`), commands, events,
  errors, enums. Aggregates carry behaviour (`Product.discontinue()`); they are
  pure, not anemic. Mapped entities are mutable/unslotted (SQLAlchemy hydrates
  them in place); commands and events are frozen + slotted.
- **adapters** — `orm.py` maps domain dataclasses to tables *imperatively*
  (`mapper_registry.map_imperatively`), so the domain class never imports
  SQLAlchemy. `repositories.py` returns domain entities, not rows.
- **service_layer** — handlers shaped `(command, unit_of_work) -> result`
  (writes) or `(params, unit_of_work) -> result` (reads). Orchestration only;
  raises `DomainError`, never `HTTPException`.
- **entrypoints** — the only place HTTP exists. Thin routers, request/response
  schemas, FastAPI dependencies, event-handler registration, module settings.

## The public façade

Cross-module calls go through exactly these paths:

```python
api.<other>.service_layer.queries        # reads
api.<other>.service_layer.commands       # writes
api.<other>.domain.events                # integration messages
api.<other>.domain.commands
api.<other>.domain.errors
```

Everything else is forbidden. Worked example: `ordering.place_order` needs to
validate a product and snapshot its price. It calls
`api.catalog.service_layer.queries.get_product` (façade) under the *same* UoW,
and honours catalog's orderability rule by reading the returned aggregate's
`is_orderable` **property** — so it never imports catalog's status enum or
models. When you're tempted to import a sibling's internals, expose a query
handler or a domain property instead.

## The Unit of Work

`SqlAlchemyUnitOfWork` (`shared/infrastructure/unit_of_work.py`) is the Postgres
transaction boundary and the registry of every module's repositories on a
single session. It is **depth-counted**: `async with unit_of_work:` is
reentrant, and only the outermost block commits. This lets a handler compose
other handlers — including across modules — under one atomic transaction:

```python
async with unit_of_work:                      # depth 1, opens session
    product = await get_product(id, unit_of_work)   # depth 2 in/out, no commit
    order = await unit_of_work.ordering_orders.add(...)
    await unit_of_work.commit()                # records intent
# outermost __aexit__ -> single COMMIT (or ROLLBACK on exception)
```

Repositories are typed against their abstract bases on `AbstractUnitOfWork`, so
tests substitute `FakeUnitOfWork` (`tests/fakes.py`) with in-memory repos and no
database.

## The message bus

`MessageBus` (`shared/infrastructure/messagebus.py`) is an in-process,
synchronous, post-commit pub/sub. Handlers append events to
`unit_of_work.collected_events`; `dispatch_events(unit_of_work)` delivers them to
subscribers registered at boot by each module's
`entrypoints/event_handlers.py::register_handlers(bus)`.

**Event-delivery trade-off (a decision you should make consciously).** The
template's routes call service handlers *directly* (`await commands.create_product(...)`)
— the thinnest, most common starting point. They do not auto-deliver events.
Two ways to deliver:

1. **Route-level dispatch** — inject `MessageBusDep` and, after a write handler,
   `await message_bus.dispatch_events(unit_of_work)`. One line per write route.
2. **Bus-routed commands** (canonical cosmic-python) — register command handlers
   (`bus.register_command(CreateProduct, create_product)`) and have routes call
   `await bus.handle(command, unit_of_work)`, which runs the handler then drains
   events. Centralises delivery at the cost of an indirection.

`tests/integration/test_event_delivery.py` shows the cross-module reaction
working for real (catalog `ProductDiscontinued` → ordering subscriber) via
`dispatch_events`. Wire your chosen option into routes when you need events
delivered in the HTTP path.

`IntegrationEvent` is a marker for events destined for external publication
(outbox + broker) later; today it is delivered identically to `DomainEvent`, so
that change lands entirely in the bus.

## Errors → HTTP

The service layer raises `DomainError` subclasses (`NotFoundError`,
`ForbiddenError`, `ConflictError`, `ValidationError`). `create_app()` registers
one translator per base class; subclasses inherit dispatch, so
`ProductNotFoundError(NotFoundError)` returns 404 with no extra wiring. A
`ValidationError` may attach a `payload` dict (e.g. `{"code": "duplicate_sku"}`)
merged into the 422 body for a stable machine-readable code.

## The contracts (`pyproject.toml` → `[tool.importlinter]`)

1. **Independence** — the business modules don't import each other except via
   the façade (and a small set of documented system-wiring carve-outs: the UoW
   importing repos, `register_all_orm_mappings` importing each `orm.py`, the
   composition root importing routers/handlers).
2. **Layers** — `entrypoints > service_layer > adapters > domain > settings`,
   `exhaustive` (every subpackage must fit a layer).
3. **Domain is pure Python** — `domain/` can't import `fastapi`, `sqlalchemy`,
   `pydantic`, `starlette`.
4. **Service layer is framework-free** — `service_layer/` can't import `fastapi`
   or `starlette`.

`tests/architecture/` backs these with runtime checks (`lint-imports` passes,
no ORM tokens in `domain/`, UoW wiring present, routers mounted, handlers
registered, settings prefixes). `just lint-imports` + `just arch-test` are the
gates.

## ORM registration

Business tables are mapped imperatively in each module's `adapters/orm.py`.
`register_all_orm_mappings()` (`shared/infrastructure/database.py`) imports every
`orm.py` so the `map_imperatively(...)` side effects register against the shared
`mapper_registry`. Both `create_app()` and Alembic `migrations/env.py` call it,
so autogenerate sees every table. **Add one line there per new module.**

## Authentication seam

`shared/infrastructure/auth.py::get_current_user` is the single place to wire
your auth provider; it returns a `UserIdentity`. The shipped implementation is a
permissive **dev stub** (any bearer token → a fixed identity) so the template
runs out of the box — replace it before shipping. For resource-level
authorization, add a module `entrypoints/dependencies.py` resource loader and a
`require(...)`-style dependency in the route's `dependencies=[...]`.
