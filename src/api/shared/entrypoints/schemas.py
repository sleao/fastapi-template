"""Shared request/response schema primitives.

Every HTTP schema inherits ``BaseSchema`` so fields auto-serialise to camelCase
on the wire while staying snake_case in Python. ``PaginationParams`` /
``PaginationMeta`` are the canonical paging request/response shapes — inject
``PaginationParams`` via ``Depends()`` rather than inlining ``Query(...)`` in
every endpoint.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PaginationParams(BaseSchema):
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        return self.per_page


class PaginationMeta(BaseSchema):
    has_next_page: bool
    next_page: int | None
    page: int
    per_page: int
    total: int

    @classmethod
    def build(cls, *, page: int, per_page: int, total: int) -> "PaginationMeta":
        """Derive pagination meta from the page window and total count."""
        has_next_page = page * per_page < total
        return cls(
            page=page,
            per_page=per_page,
            total=total,
            has_next_page=has_next_page,
            next_page=page + 1 if has_next_page else None,
        )


class UserIdentity(BaseSchema):
    """The authenticated caller, as resolved by ``get_current_user``.

    Keep this minimal and provider-agnostic — wire your real auth provider's
    claims into it in ``api.shared.infrastructure.auth``.
    """

    id: UUID
    email: str
