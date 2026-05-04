from pydantic import Field

from api.domain.items.enums import ItemOrder, ItemStatus
from api.domain.items.schemas import ItemRow
from api.rest.schemas import BaseSchema, PaginationMeta


class ItemResponse(BaseSchema):
    id: int
    name: str
    description: str | None = None
    status: str
    owner_id: int
    company_id: int

    @classmethod
    def from_row(cls, row: ItemRow) -> "ItemResponse":
        return cls.model_validate(row.model_dump())


class ListItemsResponse(PaginationMeta):
    items: list[ItemResponse]

    @classmethod
    def from_result(
        cls,
        rows: list[ItemRow],
        total: int,
        page: int,
        per_page: int,
    ) -> "ListItemsResponse":
        has_next_page = total > (page * per_page)
        return cls(
            items=[ItemResponse.from_row(row) for row in rows],
            has_next_page=has_next_page,
            next_page=page + 1 if has_next_page else None,
            total=total,
            page=page,
            per_page=per_page,
        )


class FilterOptionsResponse(BaseSchema):
    order_by: list[ItemOrder] = Field(default_factory=lambda: list(ItemOrder))
    status: list[ItemStatus] = Field(default_factory=lambda: list(ItemStatus))
