"""In-memory fakes implementing the repository ABCs + a no-op Unit of Work.

Service-layer and router tests run against these instead of a real database.
The fakes implement the *same* ABCs as the SQLAlchemy repositories — keeping
the two in sync is the whole point, so a method added to the ABC must be added
here too (the ``test_uow_wires_modules`` arch test and ABC abstractness guard
against drift).
"""

from __future__ import annotations

from uuid import UUID

from api.catalog.adapters.repositories import AbstractProductRepository
from api.catalog.domain.models import Product
from api.ordering.adapters.repositories import AbstractOrderRepository
from api.ordering.domain.models import Order
from api.shared.domain.time import utcnow
from api.shared.infrastructure.unit_of_work import AbstractUnitOfWork


class FakeProductRepository(AbstractProductRepository):
    def __init__(self, products: list[Product] | None = None) -> None:
        self._by_id: dict[UUID, Product] = {p.id: p for p in (products or [])}

    async def get_by_id(self, product_id: UUID) -> Product | None:
        product = self._by_id.get(product_id)
        return product if product and product.deleted_at is None else None

    async def get_by_sku(self, sku: str) -> Product | None:
        return next(
            (p for p in self._by_id.values() if p.sku == sku and p.deleted_at is None),
            None,
        )

    async def add(self, product: Product) -> Product:
        self._by_id[product.id] = product
        return product

    async def update(self, entity: Product, patch: dict) -> Product:
        entity.apply_patch(patch)
        return entity

    async def soft_delete(self, entity: Product) -> None:
        entity.deleted_at = utcnow()

    async def list_page(
        self, *, search: str | None, limit: int, offset: int
    ) -> tuple[list[Product], int]:
        rows = [p for p in self._by_id.values() if p.deleted_at is None]
        if search:
            rows = [p for p in rows if search.lower() in p.name.lower()]
        rows.sort(key=lambda p: (p.name.lower(), str(p.id)))
        return rows[offset : offset + limit], len(rows)


class FakeOrderRepository(AbstractOrderRepository):
    def __init__(self, orders: list[Order] | None = None) -> None:
        self._by_id: dict[UUID, Order] = {o.id: o for o in (orders or [])}

    async def get_by_id(self, order_id: UUID) -> Order | None:
        order = self._by_id.get(order_id)
        return order if order and order.deleted_at is None else None

    async def add(self, order: Order) -> Order:
        self._by_id[order.id] = order
        return order

    async def update(self, entity: Order, patch: dict) -> Order:
        entity.apply_patch(patch)
        return entity

    async def soft_delete(self, entity: Order) -> None:
        entity.deleted_at = utcnow()

    async def list_for_customer(self, customer_id: UUID) -> list[Order]:
        return [
            o for o in self._by_id.values() if o.customer_id == customer_id and o.deleted_at is None
        ]


class FakeUnitOfWork(AbstractUnitOfWork):
    """Depth-counted no-op UoW holding in-memory repos.

    Reuses the real ``AbstractUnitOfWork`` reentrancy logic (so nested
    ``async with`` behaves exactly like production) but never touches a DB.
    Repos are created once and persist across context entries.
    """

    def __init__(
        self,
        *,
        products: list[Product] | None = None,
        orders: list[Order] | None = None,
    ) -> None:
        self._depth = 0
        self.committed = False
        self.rolled_back = False
        self.collected_events = []
        self.catalog_products = FakeProductRepository(products)
        self.ordering_orders = FakeOrderRepository(orders)

    async def _enter(self) -> None:
        return None

    async def _commit(self) -> None:
        self.committed = True

    async def _rollback(self) -> None:
        self.rolled_back = True

    async def _close(self) -> None:
        return None
