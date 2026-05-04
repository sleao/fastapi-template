dev:
    uv run uvicorn --reload --factory --host 0.0.0.0 --port 8000 src.api.rest:create_app

test:
    uv run pytest tests/ -v

test-cov:
    uv run pytest tests/ -v --cov=src/api --cov-report=term-missing

lint:
    uv run ruff check src/
    uv run ruff format --check src/

format:
    uv run ruff format src/
    uv run ruff check --fix src/
