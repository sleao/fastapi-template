# Service layer — orchestration only, no framework

Applies to `src/api/<module>/service_layer/**`.

- Signatures are `async def <name>(command, unit_of_work) -> result` for write
  handlers (`commands.py`) and `async def <name>(<params>, unit_of_work) -> result`
  for read handlers (`queries.py`). Never `from fastapi`. Never an
  `AsyncSession`. Enforced by the "Service layer is framework-free" contract.
- Open the transaction with `async with unit_of_work:`; the UoW is
  depth-counted, so calling another handler that also opens it is safe — only
  the outermost block commits.
- Handlers raise `DomainError` subclasses from the module's `domain/errors.py`.
  Translation to HTTP happens in `api/entrypoints/_error_handlers.py`.
- Append emitted events to `unit_of_work.collected_events`; the `MessageBus`
  delivers them post-commit.
- Cross-module calls go through the **public façade only**:
  `api.<other>.service_layer.{queries,commands}`,
  `api.<other>.domain.{events,commands,errors}`. Never `api.<other>.adapters.*`
  or `api.<other>.entrypoints.*`. Prefer reading a value off the returned
  aggregate (a domain property) over importing the other module's enums.
- Use full names: `command`, `unit_of_work`, `field_name`, `value` — never
  `cmd`, `uow`, `k`, `v`.
