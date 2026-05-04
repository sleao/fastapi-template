from api.domain.auth.schemas import UserIdentity
from api.domain.items.enums import ItemStatus
from api.domain.items.schemas import ItemRow


def create_test_user(
    id: int = 1,
    company_id: int = 1,
    role: str = "READER",
) -> UserIdentity:
    return UserIdentity(id=id, company_id=company_id, role=role)


def create_test_item_row(
    id: int = 1,
    name: str = "Test Item",
    description: str | None = None,
    status: ItemStatus = ItemStatus.ACTIVE,
    owner_id: int = 1,
    company_id: int = 1,
) -> ItemRow:
    return ItemRow(
        id=id,
        name=name,
        description=description,
        status=status,
        owner_id=owner_id,
        company_id=company_id,
    )
