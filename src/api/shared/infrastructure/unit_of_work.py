"""Unit of Work — depth-counted Postgres transaction boundary + repo registry.

Composition pattern: an outer handler enters ``async with unit_of_work:``,
calls inner handlers (which may also use ``async with``), and only the
outermost ``commit()`` actually flushes. Inner handlers can call
``unit_of_work.commit()`` defensively (in case they're called standalone)
without breaking the outer transaction — ``commit()`` only records intent; the
actual flush happens on the outermost ``__aexit__``. Same shape for
``rollback()``.

This is the **Postgres** transaction boundary. The UoW holds one session and
exposes every module's repositories as attributes (``catalog_products``,
``ordering_orders``, …), all bound to that single session, so a handler that
spans modules commits atomically.

Repositories are typed against their **abstract** bases here so test code can
substitute fakes (``unit_of_work.catalog_products = FakeProductRepository()``).
``SqlAlchemyUnitOfWork`` populates the concrete implementations in ``_enter``.
"""

from __future__ import annotations

from abc import abstractmethod
from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from api.catalog.adapters.repositories import AbstractProductRepository
    from api.ordering.adapters.repositories import AbstractOrderRepository
    from api.shared.domain.events import DomainEvent


class AbstractUnitOfWork(AbstractAsyncContextManager["AbstractUnitOfWork"]):
    """Depth-counted Postgres transaction boundary shared across modules.

    Only the outermost ``__aexit__`` calls ``_commit`` / ``_rollback`` /
    ``_close``; inner ``commit()`` calls just record intent so atomicity holds
    across composed handlers.
    """

    collected_events: list["DomainEvent"]
    _depth: int = 0
    _commit_requested: bool = False

    # ── Module repositories (one attribute per module aggregate) ──
    catalog_products: "AbstractProductRepository"
    ordering_orders: "AbstractOrderRepository"

    async def __aenter__(self) -> "AbstractUnitOfWork":
        if self._depth == 0:
            # ``_enter`` may raise (e.g. session connect failure); only
            # increment ``_depth`` after a successful entry so a botched enter
            # leaves the UoW clean for retry.
            await self._enter()
            self._commit_requested = False
        self._depth += 1
        return self

    async def __aexit__(self, exception_type, exception, traceback) -> None:
        self._depth -= 1
        if self._depth != 0:
            return
        try:
            if exception_type is not None:
                await self._rollback()
            elif self._commit_requested:
                await self._commit()
        finally:
            # ``_close`` always runs — even if commit/rollback raised — so the
            # session is never leaked.
            await self._close()

    async def commit(self) -> None:
        """Record intent to commit; the flush happens at the outermost exit."""
        self._commit_requested = True

    async def rollback(self) -> None:
        """Cancel any pending commit; flush a rollback at the outermost exit."""
        self._commit_requested = False
        if self._depth == 1:
            await self._rollback()

    @abstractmethod
    async def _enter(self) -> None: ...

    @abstractmethod
    async def _commit(self) -> None: ...

    @abstractmethod
    async def _rollback(self) -> None: ...

    @abstractmethod
    async def _close(self) -> None: ...


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """Postgres-backed UoW bound to the app's async session factory."""

    def __init__(self, session_factory: "async_sessionmaker[AsyncSession]") -> None:
        self._session_factory = session_factory
        self._depth = 0

    async def _enter(self) -> None:
        # Local imports keep the import graph clean: the shared kernel must not
        # drag in module-specific adapters until a request actually opens a UoW.
        # (This edge is a documented import-linter carve-out — see pyproject.)
        from api.catalog.adapters.repositories import SqlAlchemyProductRepository
        from api.ordering.adapters.repositories import SqlAlchemyOrderRepository

        self._session = self._session_factory()
        self.collected_events = []
        self.catalog_products: SqlAlchemyProductRepository = SqlAlchemyProductRepository(
            self._session
        )
        self.ordering_orders: SqlAlchemyOrderRepository = SqlAlchemyOrderRepository(self._session)

    async def _commit(self) -> None:
        await self._session.commit()

    async def _rollback(self) -> None:
        await self._session.rollback()

    async def _close(self) -> None:
        await self._session.close()
