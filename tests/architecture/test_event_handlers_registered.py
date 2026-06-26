"""``create_app()`` calls ``register_<module>_handlers(bus)`` for every module.

Deleting a registration line would silently leave a module's events without
subscribers; this fails fast on that mistake.
"""

from __future__ import annotations

import inspect

from api.entrypoints import main


def test_register_handlers_called_for_every_module() -> None:
    source = inspect.getsource(main.create_app)
    for module_name in ("catalog", "ordering"):
        assert f"register_{module_name}_handlers(bus)" in source, (
            f"create_app() does not call register_{module_name}_handlers(bus)"
        )
