from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PaginationParams(BaseSchema):
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=100)


class PaginationMeta(BaseSchema):
    has_next_page: bool
    next_page: int | None
    page: int
    per_page: int
    total: int
