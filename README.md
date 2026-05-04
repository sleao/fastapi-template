# FastAPI Domain Template

A production-ready FastAPI template using **Hexagonal Architecture** (Ports & Adapters), organized by domain. Each domain owns its models, schemas, and repository. The REST layer is a thin adapter that wires everything together via FastAPI dependency injection.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  REST Layer  (src/api/rest/)                                │
│  Controllers, HTTP schemas, FastAPI deps, app factory        │
└────────────────────────┬────────────────────────────────────┘
                         │ calls
┌────────────────────────▼────────────────────────────────────┐
│  Domain Layer  (src/api/domain/)                            │
│  ORM models, domain schemas, repository ports (ABCs)         │
└────────────────────────┬────────────────────────────────────┘
                         │ implemented by
┌────────────────────────▼────────────────────────────────────┐
│  Integration Layer  (src/api/integrations/)                 │
│  External service adapters                                   │
└─────────────────────────────────────────────────────────────┘
```

The key rule: **dependencies only point inward**. The domain layer knows nothing about FastAPI, HTTP, or external services. The REST layer knows about domain schemas but not about SQLAlchemy internals.

---

## Directory Structure

```
src/api/
├── configuration.py          # App-level Config (pydantic-settings)
├── database.py               # DatabaseConfig + DatabaseSessionManager
│
├── domain/
│   ├── base/
│   │   └── model.py          # SQLAlchemy DeclarativeBase (shared by all models)
│   ├── auth/
│   │   ├── enums.py          # UserRoles
│   │   └── schemas.py        # UserIdentity (Pydantic)
│   └── items/                # ← example domain (replace/copy for new domains)
│       ├── enums.py          # Domain-specific enums
│       ├── models.py         # SQLAlchemy ORM model
│       ├── schemas.py        # Domain Pydantic schemas (no camelCase)
│       └── repository.py     # Abstract port + SQLAlchemy adapter
│
├── integrations/             # One subdir per external service
│   └── your_service/
│       ├── config.py         # Service config (pydantic-settings)
│       ├── service.py        # Service logic
│       ├── dependencies.py   # FastAPI dep aliases
│       └── exceptions.py     # Exception hierarchy
│
└── rest/
    ├── __init__.py           # create_app() factory
    ├── dependencies.py       # Shared deps: DbSession, HttpxSession, lifespan
    ├── schemas.py            # BaseSchema (camelCase), PaginationMeta
    └── controllers/
        ├── auth/
        │   ├── router.py     # /auth/* endpoints
        │   └── dependencies.py  # CurrentUserDep, require_role(), require_own_company()
        └── items/            # ← example domain controller
            ├── router.py     # /items/* endpoints
            ├── dependencies.py  # ItemRepoDep
            └── schemas.py    # HTTP response schemas (inherit BaseSchema/PaginationMeta)
```

---

## Layer-by-Layer Explanation

### 1. Domain Layer

The domain layer contains pure business objects. No FastAPI, no HTTP.

**Base model** — single SQLAlchemy `DeclarativeBase` shared across all domains:

```python
# domain/base/model.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

**ORM Model** — uses SQLAlchemy 2.0 `Mapped[]` typed annotations:

```python
# domain/items/models.py
class Item(Base):
    __tablename__ = "item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ItemStatus] = mapped_column(Enum(ItemStatus), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

Soft delete is a convention: always add `deleted_at` and filter with `.where(Model.deleted_at.is_(None))`.

**Domain schemas** — plain `BaseModel`, no camelCase. These travel between the repository and the controller:

```python
# domain/items/schemas.py
class ItemRow(BaseModel):
    id: int
    name: str
    status: str
    company_id: int
```

**Repository port** — an `abc.ABC` that defines what the domain needs from storage. The REST layer depends on this interface, never on the SQLAlchemy implementation:

```python
# domain/items/repository.py
class ItemRepository(abc.ABC):
    @abc.abstractmethod
    async def filter(self, params: ItemFilterParams, company_id: int) -> tuple[list[ItemRow], int]: ...

    @abc.abstractmethod
    async def get_by_id(self, item_id: int, company_id: int) -> Item | None: ...
```

**Repository adapter** — the SQLAlchemy implementation lives in the same file, right below the port. Simple operations (get by id, create, update) are written inline. Complex listing/filtering operations use a builder pattern — `_build_base_stmt()` → `_apply_filters()` → `_apply_ordering()` — to keep each concern separate:

```python
class SqlAlchemyItemRepository(ItemRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def filter(self, params, company_id):
        query = self._build_base_stmt(company_id)
        query = self._apply_filters(query, params)
        query = self._apply_ordering(query, params)

        count_stmt = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        offset = (params.page - 1) * params.per_page
        rows = (await self.session.execute(query.limit(params.per_page).offset(offset))).mappings().all()

        return [ItemRow.model_validate(dict(row)) for row in rows], total
```

---

### 2. Integration Layer

External service adapters. Each integration gets its own subdirectory under `integrations/`, following a consistent layout:

```
integrations/your_service/
├── config.py      — Service config (BaseSettings, @computed_field for derived URLs)
├── service.py     — Service logic (HTTP calls, token verification, etc.)
├── dependencies.py — FastAPI dep aliases: YourServiceDep, YourConfigDep
└── exceptions.py  — Exception hierarchy: YourServiceError → specific errors
```

The domain layer must never import from `integrations/`. The REST layer depends on service classes through FastAPI `Depends`, keeping the integration swappable.

---

### 3. REST Layer

**`create_app()`** — the app factory, in `rest/__init__.py`. Never instantiate `FastAPI()` at module level; always use a factory so tests can create isolated instances:

```python
def create_app() -> FastAPI:
    config = get_app_config()
    app = FastAPI(title="My API", root_path="/api/v1", docs_url=config.docs_url, lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origin_regex=ALLOWED_ORIGINS, ...)
    app.include_router(AuthRouter)
    app.include_router(ItemsRouter)
    return app
```

Start with: `uvicorn --factory --reload src.api.rest:create_app`

**Lifespan** — manages the DB session pool for the full app lifetime:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    _session_manager = DatabaseSessionManager(get_db_config())
    app.state.pg_session_manager = _session_manager
    yield
    await _session_manager.close()
```

The session manager is stored on `app.state` and accessed per-request in `get_db_session`.

**Shared dependency aliases** — all follow `Annotated[Type, Depends(fn)]`:

```python
DbSessionDep:  TypeAlias = Annotated[AsyncSession, Depends(get_db_session)]
HttpxSessionDep: TypeAlias = Annotated[AsyncClient, Depends(get_httpx_session)]
AppConfigDep:  TypeAlias = Annotated[Config, Depends(get_app_config)]
```

**HTTP schemas** inherit from `BaseSchema` (auto camelCase JSON keys):

```python
# rest/schemas.py
class BaseSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class PaginationMeta(BaseSchema):
    has_next_page: bool
    next_page: int | None
    page: int
    per_page: int
    total: int
```

Response schemas that return lists inherit from `PaginationMeta` and add a `from_result()` factory:

```python
class ListItemsResponse(PaginationMeta):
    items: list[ItemResponse]

    @classmethod
    def from_result(cls, rows, total, page, per_page) -> "ListItemsResponse":
        has_next_page = total > (page * per_page)
        return cls(
            items=[ItemResponse.from_row(row) for row in rows],
            has_next_page=has_next_page,
            next_page=page + 1 if has_next_page else None,
            total=total, page=page, per_page=per_page,
        )
```

---

## Auth & Authorization

**Authentication** — `get_current_user` in `rest/controllers/auth/dependencies.py` is the single place to wire your auth provider. It receives the Bearer token and must return a `UserIdentity`. `CurrentUserDep` is a pre-built `Depends(get_current_user)` used as a default argument:

```python
# rest/controllers/auth/dependencies.py
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> UserIdentity:
    # Wire in your auth provider's token verification here.
    # On failure, raise HTTPException(status_code=401).
    raise NotImplementedError
```

```python
@router.get("/protected", response_model=UserIdentity)
async def protected(user: UserIdentity = CurrentUserDep):
    return user
```

**Authorization by role** — `require_role()` is a dependency factory that returns a `Depends`:

```python
@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    repo: ItemRepoDep,
    user: UserIdentity = require_role(UserRoles.ADMINISTRATOR, UserRoles.MANAGER),
):
    ...
```

**Authorization by company** — `require_own_company()` reads the `company_id` path param and ensures it matches the JWT:

```python
@router.get("/{company_id}/data")
async def company_data(user: UserIdentity = require_own_company()):
    ...
```

---

## Configuration

Two `BaseSettings` classes, both using `@lru_cache` for singleton behavior:

| Class | File | Env vars |
|---|---|---|
| `Config` | `configuration.py` | `ENVIRONMENT`, `APP_VERSION`, `HOME_MESSAGE` |
| `DatabaseConfig` | `database.py` | `PG_HOST`, `PG_PORT`, `PG_DATABASE`, `PG_USER`, `PG_PASSWORD` |

Copy `.env.tpl` → `.env` and fill in values before running locally.

---

## Adding a New Domain

1. **Create the domain package**: `src/api/domain/your_domain/`

```
your_domain/
├── __init__.py
├── enums.py       # StrEnum for status, ordering, types
├── models.py      # SQLAlchemy model inheriting Base
├── schemas.py     # Domain Pydantic models (plain BaseModel)
└── repository.py  # ABC port + SqlAlchemy adapter
```

2. **Create the controller package**: `src/api/rest/controllers/your_domain/`

```
your_domain/
├── __init__.py
├── dependencies.py   # YourRepoDep = Annotated[..., Depends(get_your_repo)]
├── schemas.py        # HTTP schemas inheriting BaseSchema / PaginationMeta
└── router.py         # APIRouter with prefix and routes
```

3. **Register the router** in `rest/controllers/__init__.py` and `rest/__init__.py`:

```python
# rest/controllers/__init__.py
from api.rest.controllers.your_domain.router import router as YourDomainRouter

# rest/__init__.py
app.include_router(YourDomainRouter)
```

4. **Add tests** under `tests/rest/controllers/your_domain/test_router.py`, using `dependency_overrides` to inject a mock repository.

---

## Testing

Tests override FastAPI dependencies to inject mock repositories — no DB required:

```python
@pytest.fixture
def app() -> FastAPI:
    from api.rest.controllers.items.router import router

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: create_test_user()
    app.dependency_overrides[get_item_repository] = lambda: MockItemRepository()
    return app
```

Each test module creates its own minimal `FastAPI()` app with only the router under test, preventing cross-router interference.

Repository tests can compile SQLAlchemy queries to SQL strings and assert on structure without touching a real DB.

Run tests:

```bash
just test
just test-cov
```

---

## Running Locally

```bash
cp .env.tpl .env
# fill in .env values

uv sync
just dev
```

API docs available at `http://localhost:8000/api/v1/docs` (DEV environment only).
