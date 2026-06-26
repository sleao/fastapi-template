"""Ordering domain models.

Framework-free dataclass; mapped imperatively in
``api.ordering.adapters.orm``. An ``Order`` snapshots the product's price at
placement time (``unit_price_cents``) so a later price change in catalog never
rewrites historical orders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from api.ordering.domain.enums import OrderStatus
from api.shared.domain.errors import ConflictError
from api.shared.domain.identifiers import new_uuid
from api.shared.domain.time import utcnow


@dataclass(kw_only=True)
class Order:
    customer_id: UUID
    product_id: UUID
    quantity: int
    unit_price_cents: int
    status: OrderStatus = OrderStatus.PLACED
    id: UUID = field(default_factory=new_uuid)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    deleted_at: datetime | None = None

    @property
    def total_cents(self) -> int:
        return self.unit_price_cents * self.quantity

    def cancel(self) -> None:
        if self.status is OrderStatus.CANCELLED:
            raise ConflictError(f"Order {self.id} is already cancelled")
        self.status = OrderStatus.CANCELLED
