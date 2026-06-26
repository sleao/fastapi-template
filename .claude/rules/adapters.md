# Adapters layer — talks to the outside world

Applies to `src/api/<module>/adapters/**`.

- `orm.py` holds SQLAlchemy `Table` declarations and
  `mapper_registry.map_imperatively(<DomainClass>, <table>)` calls. The domain
  class itself lives in `domain/models.py` and stays framework-free. Add a line
  for the new module in `register_all_orm_mappings()`
  (`api.shared.infrastructure.database`).
- `repositories.py` exposes `Abstract<X>Repository` (ABC) +
  `SqlAlchemy<X>Repository`. Repositories **return domain entities, not ORM
  rows**, and never raise `HTTPException`. Inherit `BaseRepository` for the
  trivial `get_by_id` / `update` / `soft_delete`; write only the
  module-specific queries.
- `providers.py` (when needed) holds clients for external HTTP/SDK calls behind
  module-local interfaces.
- Tables reference sibling-module aggregates **by id only** — no cross-module
  SQLAlchemy `ForeignKey`. Referential integrity across modules is a
  service-layer concern (validate via the other module's façade).
- May import this module's `domain/` and `api.shared.infrastructure.*`. May not
  import this module's `service_layer/` or `entrypoints/`, nor another module's
  internals.
