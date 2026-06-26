"""The SqlAlchemyUnitOfWork wires every module's repositories.

If a refactor drops a module's repo slot from ``_enter``, handlers that reach
``unit_of_work.<module>_*`` break at runtime — this catches it at test time.
"""

from __future__ import annotations

import inspect

from api.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def test_uow_enter_wires_all_module_repos() -> None:
    source = inspect.getsource(SqlAlchemyUnitOfWork._enter)
    for attribute, repository in (
        ("self.catalog_products", "SqlAlchemyProductRepository"),
        ("self.ordering_orders", "SqlAlchemyOrderRepository"),
    ):
        assert attribute in source, f"UoW._enter missing {attribute}"
        assert repository in source, f"UoW._enter missing {repository}"
