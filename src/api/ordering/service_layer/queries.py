"""Ordering read handlers."""

from __future__ import annotations

from uuid import UUID

from api.ordering.domain.errors import OrderNotFoundError
from api.ordering.domain.models import Order
from api.shared.infrastructure.unit_of_work import AbstractUnitOfWork


async def get_order(order_id: UUID, unit_of_work: AbstractUnitOfWork) -> Order:
    async with unit_of_work:
        order = await unit_of_work.ordering_orders.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order


async def list_orders_for_customer(
    customer_id: UUID, unit_of_work: AbstractUnitOfWork
) -> list[Order]:
    async with unit_of_work:
        return await unit_of_work.ordering_orders.list_for_customer(customer_id)
