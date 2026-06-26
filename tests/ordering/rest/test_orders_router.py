"""Router tests for ``/orders``."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.entrypoints._error_handlers import register_domain_error_handlers
from api.ordering.entrypoints.api import router as ordering_router
from api.shared.infrastructure.auth import get_current_user
from api.shared.infrastructure.dependencies import get_unit_of_work
from tests.factory import create_product, create_user_identity
from tests.fakes import FakeUnitOfWork


@pytest.fixture
def product():
    return create_product(price_cents=1000)


@pytest.fixture
def client(product) -> TestClient:
    unit_of_work = FakeUnitOfWork(products=[product])
    app = FastAPI()
    register_domain_error_handlers(app)
    app.include_router(ordering_router)
    app.dependency_overrides[get_unit_of_work] = lambda: unit_of_work
    app.dependency_overrides[get_current_user] = lambda: create_user_identity()
    return TestClient(app)


class TestPlaceOrder:
    def test_place_order_returns_201_with_total(self, client: TestClient, product) -> None:
        response = client.post(
            "/orders",
            json={
                "customerId": str(product.id),
                "productId": str(product.id),
                "quantity": 2,
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["totalCents"] == 2000
        assert body["status"] == "PLACED"

    def test_unknown_product_is_404(self, client: TestClient, product) -> None:
        response = client.post(
            "/orders",
            json={
                "customerId": str(product.id),
                "productId": "00000000-0000-0000-0000-0000000000ee",
                "quantity": 1,
            },
        )
        assert response.status_code == 404
