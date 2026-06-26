"""Shared FastAPI dependency providers.

App/DB configs, the DB session, the shared HTTPX client, the app lifespan, and
the request-scoped Unit of Work live here. Module-specific repository factories
live in each module's ``entrypoints/dependencies.py``; the UoW dependency is
shared because every module's routes use it.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Annotated, TypeAlias

from fastapi import Depends, FastAPI, Request
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.shared.infrastructure.messagebus import MessageBus
from api.shared.infrastructure.session import DatabaseConfig, DatabaseSessionManager
from api.shared.infrastructure.unit_of_work import (
    AbstractUnitOfWork,
    SqlAlchemyUnitOfWork,
)
from api.shared.settings import Config


# ── Configs ──
@lru_cache
def get_db_config() -> DatabaseConfig:  # pragma: no cover
    return DatabaseConfig()


@lru_cache
def get_app_config() -> Config:  # pragma: no cover
    return Config()


# ── HTTPX ──
async def get_httpx_session() -> AsyncGenerator[AsyncClient, None]:  # pragma: no cover
    async with AsyncClient() as client:
        yield client


# ── DB session (raw — for reads outside a UoW) ──
async def get_db_session(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:  # pragma: no cover
    async with request.app.state.pg_session_manager.session() as session:
        yield session


# ── Unit of Work (the primary transactional entry point for handlers) ──
def get_pg_sessionmaker(request: Request) -> "async_sessionmaker[AsyncSession]":
    """Return the request app's published ``async_sessionmaker``."""
    return request.app.state.pg_sessionmaker


def get_unit_of_work(request: Request) -> AbstractUnitOfWork:  # pragma: no cover
    return SqlAlchemyUnitOfWork(get_pg_sessionmaker(request))


def get_message_bus(request: Request) -> MessageBus:  # pragma: no cover
    """The app-scoped singleton bus (built and subscribed in ``create_app``).

    Inject this in a write route to deliver events post-commit:
    ``await message_bus.dispatch_events(unit_of_work)``.
    """
    return request.app.state.message_bus


HttpxSessionDep: TypeAlias = Annotated[AsyncClient, Depends(get_httpx_session)]
DbSessionDep: TypeAlias = Annotated[AsyncSession, Depends(get_db_session)]
AppConfigDep: TypeAlias = Annotated[Config, Depends(get_app_config)]
DbConfigDep: TypeAlias = Annotated[DatabaseConfig, Depends(get_db_config)]
UnitOfWorkDep: TypeAlias = Annotated[AbstractUnitOfWork, Depends(get_unit_of_work)]
MessageBusDep: TypeAlias = Annotated[MessageBus, Depends(get_message_bus)]


# ── Lifespan ──
@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover
    """Own shared resources for the full app lifetime."""
    session_manager = DatabaseSessionManager(get_db_config())
    app.state.pg_session_manager = session_manager
    # Publish the sessionmaker so the UoW dependency builds real sessions.
    app.state.pg_sessionmaker = session_manager.sessionmaker
    yield
    await session_manager.close()
