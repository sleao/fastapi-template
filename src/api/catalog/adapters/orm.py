"""SQLAlchemy ORM for catalog — imperative mapping to domain dataclasses.

The domain class (``Product``) lives in ``api.catalog.domain.models`` and stays
framework-free. This module maps it to a physical table via
``mapper_registry.map_imperatively``. Alembic autogenerate discovers the table
through ``mapper_registry.metadata`` (the same ``MetaData`` as ``Base``).
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    String,
    Table,
    Uuid,
)

from api.catalog.domain.models import Product
from api.shared.infrastructure.database import mapper_registry, utcnow

metadata = mapper_registry.metadata


products = Table(
    "products",
    metadata,
    Column("id", Uuid, primary_key=True, default=uuid.uuid7),
    Column("name", String, nullable=False),
    Column("sku", String, unique=True, nullable=False),
    Column("price_cents", BigInteger, nullable=False),
    Column("status", String, nullable=False, default="ACTIVE"),
    Column("description", String, nullable=True),
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


mapper_registry.map_imperatively(Product, products)
