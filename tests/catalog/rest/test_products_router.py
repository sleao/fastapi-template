"""Router tests for ``/products`` via the FastAPI TestClient.

Overrides the UoW and auth dependencies (never patches internals) so the full
parse → command → handler → schema path runs against the in-memory UoW.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.catalog.entrypoints.api import router as catalog_router
from api.entrypoints._error_handlers import register_domain_error_handlers
from api.shared.infrastructure.auth import get_current_user
from api.shared.infrastructure.dependencies import get_unit_of_work
from tests.factory import create_product, create_user_identity
from tests.fakes import FakeUnitOfWork


@pytest.fixture
def unit_of_work() -> FakeUnitOfWork:
    return FakeUnitOfWork(products=[create_product(sku="SEED")])


@pytest.fixture
def client(unit_of_work: FakeUnitOfWork) -> TestClient:
    app = FastAPI()
    register_domain_error_handlers(app)
    app.include_router(catalog_router)
    app.dependency_overrides[get_unit_of_work] = lambda: unit_of_work
    app.dependency_overrides[get_current_user] = lambda: create_user_identity()
    return TestClient(app)


class TestUnauthenticated:
    def test_missing_token_is_401(self, unit_of_work: FakeUnitOfWork) -> None:
        app = FastAPI()
        app.include_router(catalog_router)
        app.dependency_overrides[get_unit_of_work] = lambda: unit_of_work
        # auth NOT overridden -> real dependency requires a bearer token
        response = TestClient(app).get("/products")
        assert response.status_code == 401


class TestCreateProduct:
    def test_create_returns_201_camelcase(self, client: TestClient) -> None:
        response = client.post(
            "/products",
            json={"name": "Gizmo", "sku": "SKU-NEW", "priceCents": 4200},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["sku"] == "SKU-NEW"
        assert body["priceCents"] == 4200  # serialised camelCase

    def test_duplicate_sku_is_409(self, client: TestClient) -> None:
        response = client.post(
            "/products",
            json={"name": "Dupe", "sku": "SEED", "priceCents": 1},
        )
        assert response.status_code == 409
        assert response.json()["code"] == "duplicate_sku"


class TestGetProduct:
    def test_unknown_id_is_404(self, client: TestClient) -> None:
        response = client.get("/products/00000000-0000-0000-0000-0000000000ff")
        assert response.status_code == 404
