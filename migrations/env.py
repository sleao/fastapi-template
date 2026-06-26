"""Alembic environment.

The critical line is ``register_all_orm_mappings()``: it imports every module's
``adapters/orm.py`` so their imperative ``map_imperatively(...)`` side effects
register against the shared ``mapper_registry``. Without it, autogenerate would
see an empty ``target_metadata`` and propose dropping every table.

The DB URL is built from ``PG_*`` env vars (the same ``DatabaseConfig`` the app
uses), so migrations and the runtime never drift on connection settings.
"""

from __future__ import annotations

import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.pool import NullPool

from api.shared.infrastructure.database import mapper_registry, register_all_orm_mappings
from api.shared.infrastructure.session import DatabaseConfig

# Load every module's imperative mappings into the shared metadata.
register_all_orm_mappings()
target_metadata = mapper_registry.metadata

config = context.config
config.set_main_option("sqlalchemy.url", DatabaseConfig().database_url)


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
