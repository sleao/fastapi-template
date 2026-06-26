"""Ordering domain errors."""

from __future__ import annotations

from uuid import UUID

from api.shared.domain.errors import ConflictError, NotFoundError, ValidationError


class OrderNotFoundError(NotFoundError):
    def __init__(self, order_id: UUID) -> None:
        super().__init__(f"Order {order_id} not found")


class ProductNotOrderableError(ConflictError):
    """The referenced product exists but cannot currently be ordered."""

    def __init__(self, product_id: UUID) -> None:
        super().__init__(f"Product {product_id} is not available for ordering")
        self.payload = {"code": "product_not_orderable"}


class InvalidQuantityError(ValidationError):
    def __init__(self) -> None:
        super().__init__("Order quantity must be a positive integer")
