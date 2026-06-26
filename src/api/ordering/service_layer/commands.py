"""Ordering write handlers.

``place_order`` is the cross-module example: it reaches into **catalog** through
the public façade (``api.catalog.service_layer.queries.get_product``) to (a)
prove the product exists, (b) honour catalog's ``is_orderable`` domain rule, and
(c) snapshot the product's price onto the order. Both handlers run under the one
depth-counted UoW — the inner ``get_product`` call enters the same UoW at a
deeper level and the single outermost ``commit()`` flushes everything atomically.

Note the *only* catalog symbol imported is the façade query. No catalog
``adapters`` / ``entrypoints`` / ``domain.models`` import — the orderability rule
is read off the returned aggregate's ``is_orderable`` property, so ordering never
needs catalog's status enum.
"""

from __future__ import annotations

from api.catalog.service_layer.queries import get_product
from api.ordering.domain.commands import CancelOrder, PlaceOrder
from api.ordering.domain.errors import (
    InvalidQuantityError,
    OrderNotFoundError,
    ProductNotOrderableError,
)
from api.ordering.domain.events import OrderPlaced
from api.ordering.domain.models import Order
from api.shared.infrastructure.unit_of_work import AbstractUnitOfWork


async def place_order(command: PlaceOrder, unit_of_work: AbstractUnitOfWork) -> Order:
    if command.quantity <= 0:
        raise InvalidQuantityError()

    async with unit_of_work:
        # Cross-module read via the catalog façade, under the same UoW. Raises
        # catalog's ProductNotFoundError (→ 404) if the product doesn't exist.
        product = await get_product(command.product_id, unit_of_work)
        if not product.is_orderable:
            raise ProductNotOrderableError(command.product_id)

        order = await unit_of_work.ordering_orders.add(
            Order(
                customer_id=command.customer_id,
                product_id=product.id,
                quantity=command.quantity,
                unit_price_cents=product.price_cents,  # price snapshot
            )
        )
        unit_of_work.collected_events.append(
            OrderPlaced(
                order_id=order.id,
                customer_id=order.customer_id,
                product_id=order.product_id,
                total_cents=order.total_cents,
            )
        )
        await unit_of_work.commit()
        return order


async def cancel_order(command: CancelOrder, unit_of_work: AbstractUnitOfWork) -> Order:
    async with unit_of_work:
        order = await unit_of_work.ordering_orders.get_by_id(command.order_id)
        if order is None:
            raise OrderNotFoundError(command.order_id)

        order.cancel()  # raises ConflictError if already cancelled
        await unit_of_work.ordering_orders.update(order, {"status": order.status})
        await unit_of_work.commit()
        return order
