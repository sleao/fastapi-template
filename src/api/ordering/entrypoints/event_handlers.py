"""Ordering event-handler registration — called once by ``create_app()``.

Subscribes ordering's reactions to the bus. This is where cross-module event
wiring lives: ordering listens for catalog's ``ProductDiscontinued``.
"""

from __future__ import annotations

from api.catalog.domain.events import ProductDiscontinued
from api.ordering.service_layer.handlers import on_product_discontinued
from api.shared.infrastructure.messagebus import MessageBus


def register_handlers(bus: MessageBus) -> None:
    bus.subscribe(ProductDiscontinued, on_product_discontinued)
