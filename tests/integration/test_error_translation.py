"""The four DomainError → HTTP translators, exercised end-to-end."""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.catalog.domain.errors import DuplicateSkuError, ProductNotFoundError
from api.entrypoints._error_handlers import register_domain_error_handlers


def _app_raising(exception: Exception) -> TestClient:
    app = FastAPI()
    register_domain_error_handlers(app)

    @app.get("/boom")
    async def boom() -> None:
        raise exception

    return TestClient(app)


def test_not_found_maps_to_404() -> None:
    response = _app_raising(ProductNotFoundError(uuid4())).get("/boom")
    assert response.status_code == 404


def test_validation_error_payload_is_merged() -> None:
    response = _app_raising(DuplicateSkuError("SKU-X")).get("/boom")
    assert response.status_code == 409
    assert response.json()["code"] == "duplicate_sku"
