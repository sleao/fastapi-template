from typing import Annotated, TypeAlias

from fastapi import Depends

from api.domain.items.repository import ItemRepository, SqlAlchemyItemRepository
from api.rest.dependencies import DbSessionDep


def get_item_repository(session: DbSessionDep) -> ItemRepository:
    return SqlAlchemyItemRepository(session)


ItemRepoDep: TypeAlias = Annotated[ItemRepository, Depends(get_item_repository)]
