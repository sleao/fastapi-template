"""Ordering HTTP schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from api.ordering.domain.enums import OrderStatus
from api.ordering.domain.models import Order
from api.shared.entrypoints.schemas import BaseSchema


class PlaceOrderRequest(BaseSchema):
    customer_id: UUID
    product_id: UUID
    quantity: int = Field(ge=1)


class OrderResponse(BaseSchema):
    id: UUID
    customer_id: UUID
    product_id: UUID
    quantity: int
    unit_price_cents: int
    total_cents: int
    status: OrderStatus

    @classmethod
    def from_domain(cls, order: Order) -> "OrderResponse":
        return cls(
            id=order.id,
            customer_id=order.customer_id,
            product_id=order.product_id,
            quantity=order.quantity,
            unit_price_cents=order.unit_price_cents,
            total_cents=order.total_cents,
            status=order.status,
        )


class OrderListResponse(BaseSchema):
    items: list[OrderResponse]

    @classmethod
    def from_domain(cls, orders: list[Order]) -> "OrderListResponse":
        return cls(items=[OrderResponse.from_domain(order) for order in orders])
