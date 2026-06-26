"""Service-layer tests for catalog write handlers, against the in-memory UoW."""

from __future__ import annotations

import pytest

from api.catalog.domain.commands import (
    CreateProduct,
    DiscontinueProduct,
    UpdateProduct,
)
from api.catalog.domain.errors import DuplicateSkuError, ProductNotFoundError
from api.catalog.domain.events import ProductCreated, ProductDiscontinued
from api.catalog.service_layer import commands
from tests.factory import create_product
from tests.fakes import FakeUnitOfWork


class TestCreateProduct:
    async def test_creates_and_emits_event(self) -> None:
        """GIVEN a fresh SKU WHEN create_product THEN it persists + emits."""
        unit_of_work = FakeUnitOfWork()
        command = CreateProduct(name="Gadget", sku="SKU-9", price_cents=500)

        product = await commands.create_product(command, unit_of_work)

        assert product.sku == "SKU-9"
        assert unit_of_work.committed is True
        assert any(isinstance(event, ProductCreated) for event in unit_of_work.collected_events)

    async def test_duplicate_sku_raises_conflict(self) -> None:
        """GIVEN an existing SKU WHEN create_product THEN DuplicateSkuError."""
        existing = create_product(sku="SKU-DUP")
        unit_of_work = FakeUnitOfWork(products=[existing])

        with pytest.raises(DuplicateSkuError):
            await commands.create_product(
                CreateProduct(name="x", sku="SKU-DUP", price_cents=1), unit_of_work
            )


class TestUpdateProduct:
    async def test_omitted_field_is_preserved_null_clears(self) -> None:
        """Omitted description preserved; explicit null clears it."""
        product = create_product(description="original")
        unit_of_work = FakeUnitOfWork(products=[product])

        # name set, description omitted -> description preserved
        await commands.update_product(
            UpdateProduct(product_id=product.id, name="Renamed", fields_set=frozenset({"name"})),
            unit_of_work,
        )
        assert product.name == "Renamed"
        assert product.description == "original"

        # description explicitly null -> cleared
        await commands.update_product(
            UpdateProduct(
                product_id=product.id,
                description=None,
                fields_set=frozenset({"description"}),
            ),
            unit_of_work,
        )
        assert product.description is None

    async def test_unknown_product_raises_not_found(self) -> None:
        unit_of_work = FakeUnitOfWork()
        with pytest.raises(ProductNotFoundError):
            await commands.update_product(
                UpdateProduct(product_id=create_product().id), unit_of_work
            )


class TestDiscontinueProduct:
    async def test_discontinue_emits_event(self) -> None:
        product = create_product()
        unit_of_work = FakeUnitOfWork(products=[product])

        await commands.discontinue_product(DiscontinueProduct(product_id=product.id), unit_of_work)

        assert any(
            isinstance(event, ProductDiscontinued) for event in unit_of_work.collected_events
        )
