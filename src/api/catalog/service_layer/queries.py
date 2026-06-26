"""Catalog read handlers.

Shape: ``async def <name>(<params>, unit_of_work) -> result``. This is the
public read façade other modules import (e.g. ordering validates a product via
``get_product``). Never imports ``fastapi``; raises ``DomainError`` subclasses.
"""

from __future__ import annotations

from uuid import UUID

from api.catalog.domain.errors import ProductNotFoundError
from api.catalog.domain.models import Product
from api.shared.infrastructure.unit_of_work import AbstractUnitOfWork


async def get_product(product_id: UUID, unit_of_work: AbstractUnitOfWork) -> Product:
    async with unit_of_work:
        product = await unit_of_work.catalog_products.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        return product


async def list_products(
    unit_of_work: AbstractUnitOfWork,
    *,
    search: str | None,
    limit: int,
    offset: int,
) -> tuple[list[Product], int]:
    async with unit_of_work:
        return await unit_of_work.catalog_products.list_page(
            search=search, limit=limit, offset=offset
        )
