"""Ordering commands."""

from __future__ import annotations

from dataclasses import dataclass

from api.shared.domain.identifiers import CustomerId, OrderId, ProductId


@dataclass(frozen=True, slots=True, kw_only=True)
class PlaceOrder:
    customer_id: CustomerId
    product_id: ProductId
    quantity: int


@dataclass(frozen=True, slots=True, kw_only=True)
class CancelOrder:
    order_id: OrderId
