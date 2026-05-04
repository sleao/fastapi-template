import abc
from typing import Any

from sqlalchemy import Select, asc, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.items.models import Item
from api.domain.items.schemas import ItemFilterParams, ItemRow


class ItemRepository(abc.ABC):
    """Port to access item data."""

    @abc.abstractmethod
    async def filter(
        self, params: ItemFilterParams, company_id: int
    ) -> tuple[list[ItemRow], int]:
        """Filter items with pagination, scoped to a company."""

    @abc.abstractmethod
    async def get_by_id(self, item_id: int, company_id: int) -> Item | None:
        """Fetch a single active item by id, scoped to a company."""


class SqlAlchemyItemRepository(ItemRepository):
    """SQLAlchemy adapter for ItemRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, item_id: int, company_id: int) -> Item | None:
        result = await self.session.execute(
            select(Item).where(
                Item.id == item_id,
                Item.company_id == company_id,
                Item.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def filter(
        self, params: ItemFilterParams, company_id: int
    ) -> tuple[list[ItemRow], int]:
        query = self._build_base_stmt(company_id)
        query = self._apply_filters(query, params)
        query = self._apply_ordering(query, params)

        count_stmt = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        offset = (params.page - 1) * params.per_page
        rows = (
            (await self.session.execute(query.limit(params.per_page).offset(offset)))
            .mappings()
            .all()
        )

        return [ItemRow.model_validate(dict(row)) for row in rows], total

    def _build_base_stmt(self, company_id: int) -> Select[Any]:
        return (
            select(
                Item.id,
                Item.name,
                Item.description,
                Item.status,
                Item.owner_id,
                Item.company_id,
            )
            .select_from(Item)
            .where(Item.company_id == company_id, Item.deleted_at.is_(None))
        )

    def _apply_filters(self, query: Select[Any], params: ItemFilterParams) -> Select[Any]:
        if params.status is not None:
            query = query.where(Item.status == params.status)

        if params.query is not None:
            q = f"%{params.query}%"
            query = query.where(
                or_(
                    Item.name.ilike(q),
                    Item.description.ilike(q),
                )
            )

        return query

    def _apply_ordering(self, query: Select[Any], params: ItemFilterParams) -> Select[Any]:
        if params.order_by is None:
            return query

        order_fn = desc if params.order_desc else asc
        return query.order_by(order_fn(text(params.order_by)))
