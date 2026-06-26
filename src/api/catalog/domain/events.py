"""Catalog domain events.

Emitted by the catalog service layer onto ``unit_of_work.collected_events`` and
drained post-commit by the ``MessageBus``. Sibling modules subscribe to these
via the public façade (``from api.catalog.domain.events import ...``) — see
``api.ordering.entrypoints.event_handlers``.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from api.shared.domain.events import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class ProductCreated(DomainEvent):
    product_id: UUID
    sku: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ProductDiscontinued(DomainEvent):
    product_id: UUID
