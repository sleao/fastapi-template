"""Every module's router is mounted and its known routes are live in the app."""

from __future__ import annotations

from api.entrypoints.main import create_app

# (path, HTTP method) pairs that must be present in the live OpenAPI schema.
EXPECTED_ROUTES = {
    ("/products", "post"),
    ("/products", "get"),
    ("/products/{product_id}", "get"),
    ("/orders", "post"),
    ("/orders/{order_id}", "get"),
}


def test_expected_routes_are_present() -> None:
    paths = create_app().openapi()["paths"]
    live = {(path, method) for path, operations in paths.items() for method in operations}
    missing = {pair for pair in EXPECTED_ROUTES if pair not in live}
    assert not missing, f"routes not mounted: {missing}"
