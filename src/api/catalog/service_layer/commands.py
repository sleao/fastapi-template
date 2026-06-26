"""Catalog write handlers.

Signatures are ``async def <name>(command, unit_of_work) -> result``. Each
handler opens the UoW, works via repositories, appends emitted events to
``unit_of_work.collected_events``, then commits. Handlers raise ``DomainError``
subclasses; the composition root maps them to HTTP. Never import ``fastapi``;
never touch an ``AsyncSession`` directly.
"""

from __future__ import annotations

from api.catalog.domain.commands import (
    CreateProduct,
    DiscontinueProduct,
    UpdateProduct,
)
from api.catalog.domain.errors import DuplicateSkuError, ProductNotFoundError
from api.catalog.domain.events import ProductCreated, ProductDiscontinued
from api.catalog.domain.models import Product
from api.shared.domain.patches import build_patch
from api.shared.infrastructure.unit_of_work import AbstractUnitOfWork


async def create_product(command: CreateProduct, unit_of_work: AbstractUnitOfWork) -> Product:
    async with unit_of_work:
        existing = await unit_of_work.catalog_products.get_by_sku(command.sku)
        if existing is not None:
            raise DuplicateSkuError(command.sku)

        product = await unit_of_work.catalog_products.add(
            Product(
                name=command.name,
                sku=command.sku,
                price_cents=command.price_cents,
                description=command.description,
            )
        )
        unit_of_work.collected_events.append(ProductCreated(product_id=product.id, sku=product.sku))
        await unit_of_work.commit()
        return product


async def update_product(command: UpdateProduct, unit_of_work: AbstractUnitOfWork) -> Product:
    async with unit_of_work:
        product = await unit_of_work.catalog_products.get_by_id(command.product_id)
        if product is None:
            raise ProductNotFoundError(command.product_id)

        patch = build_patch(command, ignore=("product_id",))
        updated = await unit_of_work.catalog_products.update(product, patch)
        await unit_of_work.commit()
        return updated


async def discontinue_product(
    command: DiscontinueProduct, unit_of_work: AbstractUnitOfWork
) -> Product:
    async with unit_of_work:
        product = await unit_of_work.catalog_products.get_by_id(command.product_id)
        if product is None:
            raise ProductNotFoundError(command.product_id)

        product.discontinue()  # raises ConflictError if already discontinued
        await unit_of_work.catalog_products.update(product, {"status": product.status})
        unit_of_work.collected_events.append(ProductDiscontinued(product_id=product.id))
        await unit_of_work.commit()
        return product
