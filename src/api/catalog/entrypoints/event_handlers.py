"""Catalog in-process event handler registration.

``register_handlers(bus)`` is called once by ``create_app()``. Catalog has no
subscribers of its own today (it is a *producer* of ``ProductCreated`` /
``ProductDiscontinued``); register any future catalog-internal handlers here.
"""

from __future__ import annotations

from api.shared.infrastructure.messagebus import MessageBus


def register_handlers(bus: MessageBus) -> None:
    _ = bus  # no catalog-internal subscribers yet
