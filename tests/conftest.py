"""Shared test fixtures.

- ``fake_uow``: an in-memory Unit of Work for service-layer and router tests
  (no database). Override the UoW dependency with it in router tests.
- ``db_session``: a real ``AsyncSession`` over an in-memory SQLite database with
  every module's tables created from the shared metadata — for adapter tests,
  so they run with zero Docker/Postgres setup.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from api.shared.infrastructure.database import mapper_registry, register_all_orm_mappings
from tests.fakes import FakeUnitOfWork


@pytest.fixture
def fake_uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    register_all_orm_mappings()
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(mapper_registry.metadata.create_all)

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    async with sessionmaker() as session:
        yield session

    await engine.dispose()
