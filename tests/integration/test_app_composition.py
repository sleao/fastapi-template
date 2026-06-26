"""Composition-root wiring: routes mounted, bus built, handlers subscribed.

These assertions don't enter the app lifespan, so they need no database.
"""

from __future__ import annotations

from api.entrypoints.main import create_app


def test_create_app_mounts_module_routers() -> None:
    app = create_app()
    paths = set(app.openapi()["paths"])
    assert "/products" in paths
    assert "/orders" in paths
    assert "/healthcheck" in paths


def test_create_app_builds_message_bus_with_subscriber() -> None:
    """ordering subscribes to catalog's ProductDiscontinued at boot."""
    from api.catalog.domain.events import ProductDiscontinued

    app = create_app()
    bus = app.state.message_bus
    assert len(bus._event_handlers[ProductDiscontinued]) == 1
