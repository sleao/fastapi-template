# Copy to .env and adjust. Loaded by `just` (set dotenv-load) and pydantic-settings.

# ── App (APP_ prefix) ──
APP_ENVIRONMENT=DEV
APP_VERSION=0.1.0

# ── Postgres (PG_ prefix) ──
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=app
PG_USER=postgres
PG_PASSWORD=postgres

# ── Module settings (per-module prefixes) ──
# CATALOG_MAX_PAGE_SIZE=100
# ORDERING_MAX_ORDER_QUANTITY=1000
