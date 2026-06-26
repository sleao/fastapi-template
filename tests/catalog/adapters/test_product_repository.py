"""Adapter (repository) tests against a real in-memory SQLite session.

Proves the SQLAlchemy queries and the imperative mapping actually work — these
are the only tests that touch a DB, and they need no Docker (SQLite in-memory).
"""

from __future__ import annotations

from api.catalog.adapters.repositories import SqlAlchemyProductRepository
from tests.factory import create_product


class TestSqlAlchemyProductRepository:
    async def test_add_then_get_by_id_round_trips(self, db_session) -> None:
        repository = SqlAlchemyProductRepository(db_session)
        product = await repository.add(create_product(sku="SKU-RT"))

        fetched = await repository.get_by_id(product.id)

        assert fetched is not None
        assert fetched.sku == "SKU-RT"

    async def test_get_by_sku(self, db_session) -> None:
        repository = SqlAlchemyProductRepository(db_session)
        await repository.add(create_product(sku="SKU-FIND"))

        assert (await repository.get_by_sku("SKU-FIND")) is not None
        assert (await repository.get_by_sku("missing")) is None

    async def test_list_page_filters_and_paginates(self, db_session) -> None:
        repository = SqlAlchemyProductRepository(db_session)
        await repository.add(create_product(name="Alpha", sku="A"))
        await repository.add(create_product(name="Beta", sku="B"))
        await repository.add(create_product(name="Alpaca", sku="C"))

        rows, total = await repository.list_page(search="alp", limit=10, offset=0)

        assert total == 2
        assert {product.name for product in rows} == {"Alpha", "Alpaca"}

    async def test_soft_delete_hides_row(self, db_session) -> None:
        repository = SqlAlchemyProductRepository(db_session)
        product = await repository.add(create_product(sku="SKU-DEL"))

        await repository.soft_delete(product)

        assert (await repository.get_by_id(product.id)) is None
