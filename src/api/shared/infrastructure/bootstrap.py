"""Composition glue — singleton bus for the app lifetime."""

from __future__ import annotations

from api.shared.infrastructure.messagebus import MessageBus


def build_message_bus() -> MessageBus:
    """Build the application's singleton MessageBus.

    The UoW is request-scoped; callers pass it into
    ``bus.handle(message, unit_of_work)``.
    """
    return MessageBus()
