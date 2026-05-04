from sqlalchemy import Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from api.domain.base.model import Base
from api.domain.items.enums import ItemStatus


class Item(Base):
    __tablename__ = "item"

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[ItemStatus] = mapped_column(Enum(ItemStatus), nullable=False)

    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False)
