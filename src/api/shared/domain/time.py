"""Pure-Python time helpers shared across the domain.

Single source of truth for "now" so every module's domain models and every
SQLAlchemy column default agree on one implementation. The shared
``api.shared.infrastructure.database`` re-exports ``utcnow`` from here so the
ORM column defaults and the domain dataclass ``default_factory`` references stay
in lock-step without dragging SQLAlchemy into the domain layer.

This module is part of the domain layer: pure Python only. It must not import
``fastapi``, ``sqlalchemy``, ``pydantic``, or ``starlette``.
"""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current time as a timezone-aware UTC ``datetime``."""
    return datetime.now(timezone.utc)
