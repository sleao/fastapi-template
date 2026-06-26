"""Ordering HTTP routes — ``/orders/*``."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from api.ordering.domain.commands import CancelOrder, PlaceOrder
from api.ordering.entrypoints.schemas import (
    OrderListResponse,
    OrderResponse,
    PlaceOrderRequest,
)
from api.ordering.service_layer import commands, queries
from api.shared.infrastructure.auth import CurrentUserDep
from api.shared.infrastructure.dependencies import UnitOfWorkDep

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(
    body: PlaceOrderRequest,
    unit_of_work: UnitOfWorkDep,
    _user: CurrentUserDep,
) -> OrderResponse:
    command = PlaceOrder(
        customer_id=body.customer_id,
        product_id=body.product_id,
        quantity=body.quantity,
    )
    order = await commands.place_order(command, unit_of_work)
    return OrderResponse.from_domain(order)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    unit_of_work: UnitOfWorkDep,
    _user: CurrentUserDep,
    customer_id: UUID = Query(...),
) -> OrderListResponse:
    orders = await queries.list_orders_for_customer(customer_id, unit_of_work)
    return OrderListResponse.from_domain(orders)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    unit_of_work: UnitOfWorkDep,
    _user: CurrentUserDep,
) -> OrderResponse:
    order = await queries.get_order(order_id, unit_of_work)
    return OrderResponse.from_domain(order)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: UUID,
    unit_of_work: UnitOfWorkDep,
    _user: CurrentUserDep,
) -> OrderResponse:
    order = await commands.cancel_order(CancelOrder(order_id=order_id), unit_of_work)
    return OrderResponse.from_domain(order)
