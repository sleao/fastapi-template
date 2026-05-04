from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.rest.controllers import AuthRouter, ItemsRouter
from api.rest.dependencies import get_app_config, lifespan

ALLOWED_ORIGINS = r"https://.*\.example\.com"


def create_app() -> FastAPI:
    config = get_app_config()

    app = FastAPI(
        title="My API",
        description="Welcome to My API docs!",
        root_path="/api/v1",
        docs_url=config.docs_url,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,  # type: ignore
        allow_origin_regex=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(AuthRouter)
    app.include_router(ItemsRouter)

    @app.get("/healthcheck", include_in_schema=True)
    def healthcheck():
        """Healthcheck endpoint."""
        return {"status": "ok"}

    return app
