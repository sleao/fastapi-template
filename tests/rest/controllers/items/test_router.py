import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.domain.items.repository import ItemRepository
from api.rest.controllers.auth.dependencies import get_current_user
from api.rest.controllers.items.dependencies import get_item_repository
from tests.factory import create_test_item_row, create_test_user


class MockItemRepository(ItemRepository):
    async def filter(self, params, company_id):
        return [create_test_item_row()], 1

    async def get_by_id(self, item_id, company_id):
        if item_id == 1:
            return create_test_item_row()
        return None


@pytest.fixture
def app() -> FastAPI:
    from api.rest.controllers.items.router import router

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: create_test_user()
    app.dependency_overrides[get_item_repository] = lambda: MockItemRepository()
    return app


@pytest.fixture
async def client(app: FastAPI):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_list_items_requires_auth():
    from api.rest.controllers.items.router import router

    bare_app = FastAPI()
    bare_app.include_router(router)
    async with AsyncClient(transport=ASGITransport(app=bare_app), base_url="http://test") as c:
        response = await c.get("/items/")
    assert response.status_code == 403


async def test_list_items(client: AsyncClient):
    response = await client.get("/items/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Test Item"


async def test_get_item_found(client: AsyncClient):
    response = await client.get("/items/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Item"


async def test_get_item_not_found(client: AsyncClient):
    response = await client.get("/items/999")
    assert response.status_code == 404


async def test_filter_options(client: AsyncClient):
    response = await client.get("/items/filter-options")
    assert response.status_code == 200
    data = response.json()
    assert "orderBy" in data
    assert "status" in data
