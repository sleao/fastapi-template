"""Shared database primitives.

Single source of truth for the SQLAlchemy declarative base, the mapper
registry, and the reusable column mixins. Module-specific tables are
**imperatively** mapped in each module's ``adapters/orm.py`` against
``mapper_registry`` so Alembic autogenerate picks up both declarative- and
imperative-mapped tables from one ``MetaData``.

``utcnow`` is re-exported from the pure-domain ``api.shared.domain.time`` so the
ORM column defaults here and the domain dataclass ``default_factory`` references
share one implementation without dragging SQLAlchemy into the domain layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import UUID, DateTime, MetaData
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, registry

from api.shared.domain.time import utcnow

__all__ = [
    "Base",
    "TimestampedLifecycleMixin",
    "UUIDMixin",
    "mapper_registry",
    "register_all_orm_mappings",
    "utcnow",
]


# Shared registry — imperative mappings in per-module ``adapters/orm.py`` call
# ``mapper_registry.map_imperatively(...)`` against it. ``Base.metadata`` points
# at the same ``MetaData`` so Alembic autogenerate sees both declarative- and
# imperative-mapped tables. ``type_annotation_map`` lives on the registry (not
# the Base) because SQLAlchemy forbids combining a per-base annotation map with
# an external registry.
mapper_registry = registry(
    metadata=MetaData(),
    type_annotation_map={dict[str, Any]: JSONB},
)


class UUIDMixin:
    """UUID7 primary key shared by every table."""

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid7)


class TimestampedLifecycleMixin:
    """``created_at`` / ``updated_at`` / ``deleted_at`` lifecycle timestamps.

    ``deleted_at`` is the nullable soft-delete marker: rows are never hard
    deleted — repositories filter ``.where(<Table>.deleted_at.is_(None))``.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class Base(UUIDMixin, TimestampedLifecycleMixin, DeclarativeBase):
    """Optional declarative base for tables you'd rather not map imperatively.

    The example modules map dataclasses imperatively in ``adapters/orm.py``;
    this base is here for tables where a plain declarative model is simpler.
    Both shapes share ``mapper_registry.metadata``.
    """

    registry = mapper_registry


def register_all_orm_mappings() -> None:
    """Import every module's ``adapters/orm.py`` so imperative mappings load.

    The imports are deferred to call-time: each ``adapters/orm.py`` imports
    ``mapper_registry`` from this module, so importing them at the top here
    would create a cycle. Calling them inside the function body breaks that
    cycle while keeping the targets real (IDE- and refactor-tracked).

    Both ``create_app()`` (boot) and Alembic ``env.py`` call this so every
    ``map_imperatively(...)`` side effect runs against ``mapper_registry``.
    Without it, Alembic autogenerate would miss every imperatively-mapped
    table. Safe to call repeatedly: imports are idempotent.

    Add one line per new module here.
    """
    import api.catalog.adapters.orm  # noqa: F401  (registers imperative mappings)
    import api.ordering.adapters.orm  # noqa: F401
