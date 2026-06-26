"""Abstract repository protocol + shared SQLAlchemy CRUD helper.

``AbstractRepository`` is the minimal contract every module's repository
satisfies. ``BaseRepository`` is the shared SQLAlchemy CRUD helper that
per-module ``adapters/repositories.py`` classes inherit from for the trivial
operations (``get_by_id`` / ``soft_delete`` / ``update``), so module repos can
focus on their genuinely module-specific queries.

It works with the imperatively-mapped domain dataclasses — they expose the
``id``, ``deleted_at``, and ``apply_patch`` attributes the helper needs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.shared.infrastructure.database import utcnow

EntityT = TypeVar("EntityT")


class AbstractRepository(ABC, Generic[EntityT]):
    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> EntityT | None: ...

    @abstractmethod
    async def add(self, entity: EntityT) -> None: ...


ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Shared SQLAlchemy CRUD helper.

    Subclasses set ``_model = <MappedClass>`` and get ``get_by_id`` /
    ``soft_delete`` / ``update`` for free, layering their module-specific
    queries on top.
    """

    _model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: UUID) -> ModelT | None:
        result = await self._session.execute(
            select(self._model).where(
                self._model.id == entity_id,
                self._model.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def update(self, entity: ModelT, /, patch: dict[str, Any]) -> ModelT:
        entity.apply_patch(patch)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def soft_delete(self, entity: ModelT, /) -> None:
        entity.deleted_at = utcnow()
        await self._session.flush()
