from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from api.domain.auth.schemas import UserIdentity
from api.domain.items.schemas import ItemFilterParams
from api.rest.controllers.auth.dependencies import CurrentUserDep, require_role
from api.domain.auth.enums import UserRoles
from api.rest.controllers.items.dependencies import ItemRepoDep
from api.rest.controllers.items.schemas import (
    FilterOptionsResponse,
    ItemResponse,
    ListItemsResponse,
)

router = APIRouter(prefix="/items", tags=["Items"])


@router.get("/filter-options", response_model=FilterOptionsResponse)
async def filter_options(user: UserIdentity = CurrentUserDep):
    return FilterOptionsResponse()


@router.get("/", response_model=ListItemsResponse)
async def list_items(
    repo: ItemRepoDep,
    params: Annotated[ItemFilterParams, Query()],
    user: UserIdentity = CurrentUserDep,
):
    rows, total = await repo.filter(params, user.company_id)
    return ListItemsResponse.from_result(rows, total, params.page, params.per_page)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    repo: ItemRepoDep,
    user: UserIdentity = CurrentUserDep,
):
    item = await repo.get_by_id(item_id, user.company_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return ItemResponse.model_validate(item.__dict__)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    repo: ItemRepoDep,
    user: UserIdentity = require_role(UserRoles.ADMINISTRATOR, UserRoles.MANAGER),
):
    item = await repo.get_by_id(item_id, user.company_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
