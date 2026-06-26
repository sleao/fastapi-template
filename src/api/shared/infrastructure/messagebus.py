"""In-process MessageBus.

Stateless w.r.t. the UoW: each ``handle(message, unit_of_work)`` call receives
the request-scoped UoW. Event handlers are registered once at app startup; the
bus is a singleton, the UoW is per-request.

Dispatch is synchronous and post-commit. A handler failure logs and re-raises;
remaining queued events are dropped (the transaction has already committed — we
fail fast rather than silently swallow errors).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from api.shared.domain.events import Event
from api.shared.infrastructure.unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)

EventHandler = Callable[[Event, AbstractUnitOfWork], Awaitable[None]]
CommandHandler = Callable[[Any, AbstractUnitOfWork], Awaitable[Any]]


class MessageBus:
    """Singleton message bus. UoW is per-request, passed to ``handle()``."""

    def __init__(self) -> None:
        self._event_handlers: dict[type[Event], list[EventHandler]] = defaultdict(list)
        self._command_handlers: dict[type, CommandHandler] = {}

    def subscribe(self, event_type: type[Event], handler: EventHandler) -> None:
        self._event_handlers[event_type].append(handler)

    def register_command(self, command_type: type, handler: CommandHandler) -> None:
        if command_type in self._command_handlers:
            raise ValueError(f"Command handler already registered: {command_type!r}")
        self._command_handlers[command_type] = handler

    async def handle(self, message: Any, unit_of_work: AbstractUnitOfWork) -> Any:
        """Run the registered command handler (if any) then deliver events.

        Routing writes through the bus is the canonical cosmic-python pattern;
        the template's routes instead call service handlers directly (thinner,
        and what most apps start with) and deliver events via
        ``dispatch_events`` — see ``docs/architecture.md`` for the trade-off.
        """
        result: Any = None
        if type(message) in self._command_handlers:
            handler = self._command_handlers[type(message)]
            result = await handler(message, unit_of_work)
        await self.dispatch_events(unit_of_work)
        return result

    async def dispatch_events(self, unit_of_work: AbstractUnitOfWork) -> None:
        """Deliver every event the UoW collected to its subscribers, in order.

        Call this *after* the transaction has committed. Handlers run
        synchronously; a failure logs and re-raises, dropping remaining events.
        """
        while unit_of_work.collected_events:
            event = unit_of_work.collected_events.pop(0)
            for handler in self._event_handlers.get(type(event), []):
                try:
                    await handler(event, unit_of_work)
                except Exception:
                    logger.exception(
                        "event handler %r failed for event %r; remaining queued events are dropped",
                        getattr(handler, "__qualname__", repr(handler)),
                        type(event).__name__,
                    )
                    raise
