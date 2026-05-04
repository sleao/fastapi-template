import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.rest import create_app


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
async def client(app: FastAPI):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
