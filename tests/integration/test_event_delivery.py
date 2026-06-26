"""End-to-end event delivery across modules via the MessageBus.

Discontinuing a product emits ``ProductDiscontinued``; the bus delivers it to
ordering's subscriber. This is the cross-module reaction working for real —
just without a DB (fakes) or HTTP (direct handler call + dispatch_events).
"""

from __future__ import annotations

import logging

from api.catalog.domain.commands import DiscontinueProduct
from api.catalog.entrypoints.event_handlers import register_handlers as register_catalog
from api.catalog.service_layer import commands
from api.ordering.entrypoints.event_handlers import register_handlers as register_ordering
from api.shared.infrastructure.messagebus import MessageBus
from tests.factory import create_product
from tests.fakes import FakeUnitOfWork


async def test_discontinuing_product_notifies_ordering(caplog) -> None:
    bus = MessageBus()
    register_catalog(bus)
    register_ordering(bus)

    product = create_product()
    unit_of_work = FakeUnitOfWork(products=[product])

    # Direct handler call (the route pattern), then deliver collected events.
    await commands.discontinue_product(DiscontinueProduct(product_id=product.id), unit_of_work)
    with caplog.at_level(logging.INFO):
        await bus.dispatch_events(unit_of_work)

    assert any("ProductDiscontinued" in message for message in caplog.messages)
    assert unit_of_work.collected_events == []  # fully drained
