"""Catalog repositories — return domain entities, not ORM rows.

``get_by_id`` / ``update`` / ``soft_delete`` are inherited from
``BaseRepository``; the methods below are the genuinely product-specific
queries. Repositories never raise HTTP exceptions — the service layer raises
``DomainError`` subclasses, translated to HTTP at the edge.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import func, select

import api.catalog.adapters.orm  # noqa: F401 — ensures the imperative mapping registers
from api.catalog.domain.models import Product
from api.shared.infrastructure.repository import BaseRepository


class AbstractProductRepository(ABC):
    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> Product | None: ...

    @abstractmethod
    async def get_by_sku(self, sku: str) -> Product | None: ...

    @abstractmethod
    async def add(self, product: Product) -> Product: ...

    @abstractmethod
    async def list_page(
        self, *, search: str | None, limit: int, offset: int
    ) -> tuple[list[Product], int]: ...


class SqlAlchemyProductRepository(BaseRepository[Product], AbstractProductRepository):
    _model = Product

    async def get_by_sku(self, sku: str) -> Product | None:
        statement = select(Product).where(Product.sku == sku, Product.deleted_at.is_(None))
        return await self._session.scalar(statement)

    async def add(self, product: Product) -> Product:
        self._session.add(product)
        await self._session.flush()
        await self._session.refresh(product)
        return product

    async def list_page(
        self, *, search: str | None, limit: int, offset: int
    ) -> tuple[list[Product], int]:
        conditions = [Product.deleted_at.is_(None)]
        if search:
            conditions.append(func.lower(Product.name).contains(search.lower()))

        total = await self._session.scalar(
            select(func.count()).select_from(Product).where(*conditions)
        )
        statement = (
            select(Product)
            .where(*conditions)
            .order_by(func.lower(Product.name), Product.id)
            .limit(limit)
            .offset(offset)
        )
        rows = list(await self._session.scalars(statement))
        return rows, total or 0
