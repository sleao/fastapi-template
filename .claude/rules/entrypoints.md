# Entrypoints — the only place HTTP exists

Applies to `src/api/<module>/entrypoints/**`.

- `api.py` defines a single FastAPI `APIRouter`. Routes are thin: parse input →
  build a domain `Command` (writes) or query params (reads) → call
  `service_layer.{commands,queries}.<handler>(command, unit_of_work)` →
  serialise the result via the module's `schemas.py`.
- No business logic. No `HTTPException` for domain conditions — those are
  `DomainError` subclasses raised by the service layer and translated centrally.
- No SQLAlchemy session reach-around. Inject `UnitOfWorkDep` (from
  `api.shared.infrastructure.dependencies`) and pass it to the handler.
- `schemas.py` request/response models inherit `BaseSchema` (camelCase on the
  wire). Reuse `PaginationParams` / `PaginationMeta` from
  `api.shared.entrypoints.schemas` — inject `PaginationParams` via `Depends()`.
- `dependencies.py` holds module-scoped `Depends` factories (e.g. an ABAC
  resource loader).
- `event_handlers.py` exports `register_handlers(bus)`, called once by
  `create_app()`; subscribe this module's reactions there.
- `settings.py` is a `BaseSettings` with this module's `<MODULE>_` env prefix.
