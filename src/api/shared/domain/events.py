"""Event base hierarchy.

``DomainEvent`` is delivered in-process only, post-commit, by the
``MessageBus``. ``IntegrationEvent`` is a marker for events that should
eventually be published externally (outbox + broker); today they are dispatched
identically to ``DomainEvent``. The split lets a later change to dispatch logic
land entirely in the ``MessageBus`` without touching any module.

Events are frozen dataclasses. Handlers append them to
``unit_of_work.collected_events``; the bus drains them after the outermost
``commit()`` succeeds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True, kw_only=True)
class Event:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=_now_utc)


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent(Event):
    """In-process only. Sibling modules subscribe; no external publication."""


@dataclass(frozen=True, slots=True, kw_only=True)
class IntegrationEvent(Event):
    """Marked for eventual external publication.

    Same in-process delivery as ``DomainEvent`` today. Reserved as a migration
    anchor so later infra work changes only the ``MessageBus``.
    """
