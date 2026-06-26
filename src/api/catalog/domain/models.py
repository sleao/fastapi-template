"""Catalog domain models.

Framework-free dataclasses. SQLAlchemy mappings live in
``api.catalog.adapters.orm`` via ``mapper_registry.map_imperatively(...)``.

Mutability (no ``frozen=True``) is required for imperative-mapping hydration —
SQLAlchemy mutates the instance when loading a row. We also avoid
``slots=True``: SQLAlchemy keeps a weakref to every mapped instance, and a
slots-only class without a ``__weakref__`` slot raises ``TypeError`` on map.
Commands and events keep ``slots=True`` because they are never mapped.

The aggregate carries its own behaviour (``discontinue``, ``apply_patch``) —
"pure" means framework-free, not anemic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from api.catalog.domain.enums import ProductStatus
from api.shared.domain.errors import ConflictError
from api.shared.domain.identifiers import new_uuid
from api.shared.domain.patches import apply_patch as _apply_patch
from api.shared.domain.time import utcnow


@dataclass(kw_only=True)
class Product:
    name: str
    sku: str
    price_cents: int
    status: ProductStatus = ProductStatus.ACTIVE
    description: str | None = None
    id: UUID = field(default_factory=new_uuid)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    deleted_at: datetime | None = None

    def apply_patch(self, data: dict[str, Any]) -> None:
        _apply_patch(self, data)

    @property
    def is_orderable(self) -> bool:
        """Whether the product can be placed on an order.

        Exposed as domain behaviour so sibling modules (ordering) can honour
        the rule by reading a boolean, without importing catalog's status enum
        — keeping the cross-module surface to the public façade only.
        """
        return self.status is ProductStatus.ACTIVE and self.deleted_at is None

    def discontinue(self) -> None:
        """Mark the product discontinued. Doing it twice is treated as a
        conflict so the caller learns the state was already terminal."""
        if self.status is ProductStatus.DISCONTINUED:
            raise ConflictError(f"Product {self.id} is already discontinued")
        self.status = ProductStatus.DISCONTINUED
