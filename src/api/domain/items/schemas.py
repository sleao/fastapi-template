from pydantic import BaseModel, Field

from api.domain.items.enums import ItemOrder, ItemStatus


class ItemFilterParams(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=100)
    status: ItemStatus | None = None
    query: str | None = None
    order_by: ItemOrder | None = None
    order_desc: bool = False


class ItemRow(BaseModel):
    id: int
    name: str
    description: str | None = None
    status: str
    owner_id: int
    company_id: int
