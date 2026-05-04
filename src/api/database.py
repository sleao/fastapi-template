from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class DatabaseConfig(BaseSettings):
    PG_HOST: str = "localhost"
    PG_PORT: int = 5432
    PG_DATABASE: str = "myapp"
    PG_USER: str = "postgres"
    PG_PASSWORD: str = "postgres"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"


class DatabaseSessionManager:
    def __init__(self, config: DatabaseConfig):
        self._engine = create_async_engine(config.database_url)
        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close(self) -> None:
        await self._engine.dispose()
