"""Catalog HTTP schemas — camelCase on the wire via ``BaseSchema``."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from api.catalog.domain.enums import ProductStatus
from api.catalog.domain.models import Product
from api.shared.entrypoints.schemas import BaseSchema, PaginationMeta


class CreateProductRequest(BaseSchema):
    name: str = Field(max_length=255)
    sku: str = Field(max_length=64)
    price_cents: int = Field(ge=0)
    description: str | None = Field(default=None, max_length=2000)


class UpdateProductRequest(BaseSchema):
    name: str | None = Field(default=None, max_length=255)
    price_cents: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=2000)


class ProductResponse(BaseSchema):
    id: UUID
    name: str
    sku: str
    price_cents: int
    status: ProductStatus
    description: str | None

    @classmethod
    def from_domain(cls, product: Product) -> "ProductResponse":
        return cls(
            id=product.id,
            name=product.name,
            sku=product.sku,
            price_cents=product.price_cents,
            status=product.status,
            description=product.description,
        )


class ProductListResponse(BaseSchema):
    items: list[ProductResponse]
    meta: PaginationMeta

    @classmethod
    def from_page(
        cls, products: list[Product], *, page: int, per_page: int, total: int
    ) -> "ProductListResponse":
        return cls(
            items=[ProductResponse.from_domain(product) for product in products],
            meta=PaginationMeta.build(page=page, per_page=per_page, total=total),
        )
