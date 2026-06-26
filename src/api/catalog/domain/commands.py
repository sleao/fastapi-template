"""Catalog commands — frozen dataclasses passed into service-layer handlers."""

from __future__ import annotations

from dataclasses import dataclass

from api.shared.domain.identifiers import ProductId


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateProduct:
    name: str
    sku: str
    price_cents: int
    description: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateProduct:
    product_id: ProductId
    name: str | None = None
    price_cents: int | None = None
    description: str | None = None
    # Names the client actually sent (from the request's ``model_fields_set``).
    # Lets the handler tell an omitted field from one explicitly set to null.
    fields_set: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True, kw_only=True)
class DiscontinueProduct:
    product_id: ProductId
