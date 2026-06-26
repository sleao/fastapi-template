"""Postgres connection settings + async session manager.

``DatabaseSessionManager`` owns the engine and the ``async_sessionmaker`` for
the full app lifetime (opened/closed by the lifespan). The
``SqlAlchemyUnitOfWork`` is built from the published ``sessionmaker`` — it, not
this manager, decides when to commit. The ``session()`` context manager is kept
for the rare read path that wants a raw session outside a UoW.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PG_")

    host: str = "localhost"
    port: int = 5432
    database: str = "app"
    user: str = "postgres"
    password: str = "postgres"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class DatabaseSessionManager:
    """Owns the engine + sessionmaker for the app lifetime."""

    def __init__(self, config: DatabaseConfig) -> None:
        self._engine = create_async_engine(config.database_url)
        # Public so the UoW dependency can build sessions from it directly.
        self.sessionmaker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self._engine, expire_on_commit=False
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Raw session for reads outside a UoW. Commits on clean exit."""
        async with self.sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close(self) -> None:
        await self._engine.dispose()
