"""SQLAlchemy ORM for ordering — imperative mapping to the ``Order`` dataclass.

Note there is **no** SQLAlchemy ``ForeignKey`` from ``orders.product_id`` to
``products.id``: modules own their own tables and reference sibling aggregates
by id only. Referential integrity across module boundaries is enforced in the
service layer (``place_order`` validates the product via the catalog façade),
not by a cross-module FK. This keeps the modules independently migratable.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    String,
    Table,
    Uuid,
)

from api.ordering.domain.models import Order
from api.shared.infrastructure.database import mapper_registry, utcnow

metadata = mapper_registry.metadata


orders = Table(
    "orders",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid.uuid7),
    Column("customer_id", Uuid, nullable=False),
    Column("product_id", Uuid, nullable=False),  # sibling-module ref by id only
    Column("quantity", Integer, nullable=False),
    Column("unit_price_cents", BigInteger, nullable=False),
    Column("status", String, nullable=False, default="PLACED"),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    ),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
)


mapper_registry.map_imperatively(Order, orders)
