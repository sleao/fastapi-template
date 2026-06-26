"""Ordering event handlers.

Subscribers to events from this and other modules. ``on_product_discontinued``
reacts to **catalog**'s ``ProductDiscontinued`` (imported via the public
events façade) — the canonical cross-module reaction pattern. Handlers have the
shape ``async def <name>(event, unit_of_work) -> None`` and run post-commit; the
UoW is available so a handler can do follow-up writes in its own transaction.
"""

from __future__ import annotations

import logging

from api.catalog.domain.events import ProductDiscontinued
from api.shared.infrastructure.unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)


async def on_product_discontinued(
    event: ProductDiscontinued, unit_of_work: AbstractUnitOfWork
) -> None:
    # A real handler might flag or notify customers with open orders for the
    # product. Here we just record the reaction to demonstrate the wiring.
    _ = unit_of_work
    logger.info("ordering observed ProductDiscontinued for product %s", event.product_id)
