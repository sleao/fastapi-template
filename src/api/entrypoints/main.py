"""Composition root for the FastAPI application.

``create_app()`` is the single place the whole app is wired:

1. ``register_all_orm_mappings()`` — load every module's imperative mappings
   before any DB session opens.
2. mount each module's router,
3. register the four ``DomainError`` → HTTP translators,
4. build the singleton ``MessageBus`` and call each module's
   ``register_handlers(bus)``.

Adding a module = add its router ``include_router`` line and its
``register_<module>_handlers(bus)`` line here. The architecture tests assert
both are present.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.catalog.entrypoints.api import router as catalog_router
from api.catalog.entrypoints.event_handlers import (
    register_handlers as register_catalog_handlers,
)
from api.entrypoints._error_handlers import register_domain_error_handlers
from api.ordering.entrypoints.api import router as ordering_router
from api.ordering.entrypoints.event_handlers import (
    register_handlers as register_ordering_handlers,
)
from api.shared.infrastructure.database import register_all_orm_mappings
from api.shared.infrastructure.dependencies import get_app_config, lifespan
from api.shared.infrastructure.messagebus import MessageBus

# Tighten this for your deployment. Localhost any-port is convenient in dev.
ALLOWED_ORIGINS = r"http://localhost:\d+"


def create_app() -> FastAPI:
    register_all_orm_mappings()
    config = get_app_config()

    app = FastAPI(
        title="FastAPI Domain Template",
        description="Modular-monolith FastAPI bootstrap (cosmic-python layout).",
        root_path="/api/v1",
        docs_url=config.docs_url,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Map shared domain errors to HTTP. Module subclasses inherit dispatch.
    register_domain_error_handlers(app)

    # Mount module routers.
    app.include_router(catalog_router)
    app.include_router(ordering_router)

    # In-process MessageBus singleton — modules subscribe at boot. The
    # per-request UoW is passed to ``bus.handle(message, unit_of_work)``.
    bus = MessageBus()
    register_catalog_handlers(bus)
    register_ordering_handlers(bus)
    app.state.message_bus = bus

    @app.get("/healthcheck", tags=["meta"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return app
