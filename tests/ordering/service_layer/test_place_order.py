"""Service-layer tests for ordering's cross-module ``place_order``.

The same in-memory UoW exposes both ``catalog_products`` and
``ordering_orders``, so ``place_order`` exercises the real catalog façade call
under one transaction — exactly as in production, just without a DB.
"""

from __future__ import annotations

import pytest

from api.catalog.domain.enums import ProductStatus
from api.catalog.domain.errors import ProductNotFoundError
from api.ordering.domain.commands import PlaceOrder
from api.ordering.domain.errors import InvalidQuantityError, ProductNotOrderableError
from api.ordering.domain.events import OrderPlaced
from api.ordering.service_layer import commands
from tests.factory import create_product
from tests.fakes import FakeUnitOfWork


class TestPlaceOrder:
    async def test_snapshots_price_and_emits_event(self) -> None:
        """GIVEN an active product WHEN place_order THEN price is snapshotted."""
        product = create_product(price_cents=2500)
        unit_of_work = FakeUnitOfWork(products=[product])

        order = await commands.place_order(
            PlaceOrder(customer_id=product.id, product_id=product.id, quantity=3),
            unit_of_work,
        )

        assert order.unit_price_cents == 2500
        assert order.total_cents == 7500
        assert unit_of_work.committed is True
        assert any(isinstance(event, OrderPlaced) for event in unit_of_work.collected_events)

    async def test_unknown_product_raises_catalog_not_found(self) -> None:
        """The catalog façade's own error propagates through ordering."""
        unit_of_work = FakeUnitOfWork()
        with pytest.raises(ProductNotFoundError):
            await commands.place_order(
                PlaceOrder(
                    customer_id=create_product().id, product_id=create_product().id, quantity=1
                ),
                unit_of_work,
            )

    async def test_discontinued_product_is_not_orderable(self) -> None:
        product = create_product(status=ProductStatus.DISCONTINUED)
        unit_of_work = FakeUnitOfWork(products=[product])
        with pytest.raises(ProductNotOrderableError):
            await commands.place_order(
                PlaceOrder(customer_id=product.id, product_id=product.id, quantity=1),
                unit_of_work,
            )

    async def test_zero_quantity_is_invalid(self) -> None:
        product = create_product()
        unit_of_work = FakeUnitOfWork(products=[product])
        with pytest.raises(InvalidQuantityError):
            await commands.place_order(
                PlaceOrder(customer_id=product.id, product_id=product.id, quantity=0),
                unit_of_work,
            )
