"""Ordering domain events."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from api.shared.domain.events import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderPlaced(DomainEvent):
    order_id: UUID
    customer_id: UUID
    product_id: UUID
    total_cents: int
