from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, TypeAlias

from fastapi import Depends, FastAPI, Query, Request
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.configuration import Config
from api.database import DatabaseConfig, DatabaseSessionManager


@dataclass
class Pagination:
    limit: int = Query(20, ge=1, le=100)
    offset: int = Query(0, ge=0)


@lru_cache
def get_db_config() -> DatabaseConfig:  # pragma: no cover
    return DatabaseConfig()


@lru_cache
def get_app_config() -> Config:  # pragma: no cover
    return Config()


async def get_httpx_session() -> AsyncGenerator[AsyncClient, None]:  # pragma: no cover
    async with AsyncClient() as client:
        yield client


async def get_db_session(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:  # pragma: no cover
    async with request.app.state.pg_session_manager.session() as session:
        yield session


HttpxSessionDep: TypeAlias = Annotated[AsyncClient, Depends(get_httpx_session)]
DbSessionDep: TypeAlias = Annotated[AsyncSession, Depends(get_db_session)]
AppConfigDep: TypeAlias = Annotated[Config, Depends(get_app_config)]
DbConfigDep: TypeAlias = Annotated[DatabaseConfig, Depends(get_db_config)]


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover
    """Manages shared resources for the full application lifetime."""
    _session_manager = DatabaseSessionManager(get_db_config())
    app.state.pg_session_manager = _session_manager
    yield
    await _session_manager.close()
