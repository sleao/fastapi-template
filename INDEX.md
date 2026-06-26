# Repository map

> One-screen orientation for new engineers and AI agents. For the full
> rationale see `docs/architecture.md`; for layer rules see `.claude/rules/`.

## Modules

| Module | Purpose | Router | Public façade |
| --- | --- | --- | --- |
| `catalog` | Products (CRUD + discontinue) | `src/api/catalog/entrypoints/api.py` | `service_layer.{queries,commands}`, `domain.{events,commands,errors}` |
| `ordering` | Orders; reads catalog via façade; reacts to `ProductDiscontinued` | `src/api/ordering/entrypoints/api.py` | `service_layer.{queries,commands}`, `domain.{events,commands,errors}` |

Each module is a `domain → adapters → service_layer → entrypoints` stack.

## Cross-cutting

| Path | Purpose |
| --- | --- |
| `src/api/shared/domain/` | Pure-Python kernel: `errors`, `events`, `identifiers`, `time`, `patches` |
| `src/api/shared/infrastructure/` | `database` (registry + mixins), `session`, `unit_of_work`, `messagebus`, `repository`, `dependencies`, `auth` |
| `src/api/shared/entrypoints/schemas.py` | `BaseSchema`, `PaginationParams`, `PaginationMeta`, `UserIdentity` |
| `src/api/entrypoints/main.py` | `create_app()` — composition root |
| `src/api/entrypoints/_error_handlers.py` | `DomainError → HTTP` translators |
| `migrations/env.py` | Alembic env — calls `register_all_orm_mappings()` |

## Tooling

| Command | What it does |
| --- | --- |
| `just dev-api` | Run the API via `uvicorn --factory api.entrypoints.main:create_app` |
| `just lint-imports` | Run the 4 import-linter contracts |
| `just arch-test` | Run `tests/architecture/` |
| `just test` | Full pytest suite |
| `just db` / `just apply-migration` | Postgres + migrations |

## Architecture tests (`tests/architecture/`)

- `test_lint_imports_runs.py` — the import-linter contracts pass.
- `test_no_orm_in_domain.py` — no ORM/framework tokens in any `domain/`.
- `test_uow_wires_modules.py` — the UoW exposes every module's repos.
- `test_event_handlers_registered.py` — `create_app()` registers each module's handlers.
- `test_routers_mounted.py` — every module's known routes are live.
- `test_module_settings_env_prefix.py` — each module's settings uses its `<MODULE>_` prefix.
