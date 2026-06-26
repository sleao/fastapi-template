"""Domain-object factories for tests.

Build domain entities with sensible defaults so tests state only what matters.
Add new factories here as modules grow.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from api.catalog.domain.enums import ProductStatus
from api.catalog.domain.models import Product
from api.ordering.domain.enums import OrderStatus
from api.ordering.domain.models import Order
from api.shared.entrypoints.schemas import UserIdentity


def create_product(
    *,
    name: str = "Widget",
    sku: str = "SKU-1",
    price_cents: int = 1999,
    status: ProductStatus = ProductStatus.ACTIVE,
    description: str | None = None,
) -> Product:
    return Product(
        name=name,
        sku=sku,
        price_cents=price_cents,
        status=status,
        description=description,
    )


def create_order(
    *,
    customer_id: UUID | None = None,
    product_id: UUID | None = None,
    quantity: int = 1,
    unit_price_cents: int = 1999,
    status: OrderStatus = OrderStatus.PLACED,
) -> Order:
    return Order(
        customer_id=customer_id or uuid4(),
        product_id=product_id or uuid4(),
        quantity=quantity,
        unit_price_cents=unit_price_cents,
        status=status,
    )


def create_user_identity(*, email: str = "user@example.com") -> UserIdentity:
    return UserIdentity(id=uuid4(), email=email)
