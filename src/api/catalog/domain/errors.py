"""Catalog domain errors — subclasses of the shared ``DomainError`` hierarchy.

The composition root translates each base to its HTTP status; these subclasses
give callers a typed handle without leaking framework concerns.
"""

from __future__ import annotations

from uuid import UUID

from api.shared.domain.errors import ConflictError, NotFoundError


class ProductNotFoundError(NotFoundError):
    def __init__(self, product_id: UUID) -> None:
        super().__init__(f"Product {product_id} not found")


class DuplicateSkuError(ConflictError):
    def __init__(self, sku: str) -> None:
        super().__init__(f"A product with SKU {sku!r} already exists")
        self.payload = {"code": "duplicate_sku"}
