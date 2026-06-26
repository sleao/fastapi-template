# Domain layer — pure Python only

Applies to `src/api/<module>/domain/**`.

- No imports of `fastapi`, `sqlalchemy`, `pydantic`, or `starlette` — enforced by
  the "Domain is pure Python" import-linter contract and `tests/architecture/test_no_orm_in_domain.py`.
- No I/O of any kind (no HTTP, no DB, no filesystem, no env reads).
- Domain models are dataclasses: `@dataclass(kw_only=True)` for **mapped**
  entities (`models.py` — no `slots=True`, no `frozen=True`, because SQLAlchemy
  hydrates them in place and keeps a weakref); `@dataclass(frozen=True, slots=True, kw_only=True)`
  for commands and events (never mapped).
- "Pure" means **framework-free and I/O-free — not anemic**. Aggregate roots
  carry behaviour (methods that enforce invariants or evolve their own state),
  e.g. `Product.discontinue()`, `Order.cancel()`.
- Errors are `DomainError` subclasses (`NotFoundError`, `ForbiddenError`,
  `ConflictError`, `ValidationError`) from `api.shared.domain.errors` — never
  `HTTPException`.
- Events are `DomainEvent` / `IntegrationEvent` subclasses in this module's
  `domain/events.py`. Commands are frozen dataclasses in `domain/commands.py`.

If you need framework-y behaviour, you're in the wrong layer — move it to
`adapters/`, `service_layer/`, or `entrypoints/`.
