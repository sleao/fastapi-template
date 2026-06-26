"""Ordering repositories — return domain entities, not ORM rows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import select

import api.ordering.adapters.orm  # noqa: F401 — ensures the imperative mapping registers
from api.ordering.domain.models import Order
from api.shared.infrastructure.repository import BaseRepository


class AbstractOrderRepository(ABC):
    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Order | None: ...

    @abstractmethod
    async def add(self, order: Order) -> Order: ...

    @abstractmethod
    async def list_for_customer(self, customer_id: UUID) -> list[Order]: ...


class SqlAlchemyOrderRepository(BaseRepository[Order], AbstractOrderRepository):
    _model = Order

    async def add(self, order: Order) -> Order:
        self._session.add(order)
        await self._session.flush()
        await self._session.refresh(order)
        return order

    async def list_for_customer(self, customer_id: UUID) -> list[Order]:
        statement = (
            select(Order)
            .where(Order.customer_id == customer_id, Order.deleted_at.is_(None))
            .order_by(Order.created_at.desc(), Order.id)
        )
        return list(await self._session.scalars(statement))
