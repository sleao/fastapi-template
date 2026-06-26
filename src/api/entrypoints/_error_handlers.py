"""Shared ``DomainError`` → HTTP translators.

Registered by ``create_app()`` so the service layer can raise typed domain
errors and never touch ``HTTPException``. Subclasses inherit dispatch via
FastAPI's exception lookup, e.g. ``ProductNotFoundError(NotFoundError)`` → 404.

Any ``DomainError`` may attach a ``payload`` dict (e.g. ``{"code": "..."}``)
that is merged into the JSON body, so clients can branch on a stable
machine-readable code regardless of the HTTP status.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from api.shared.domain.errors import (
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)


def _error_response(exception: DomainError, status_code: int) -> JSONResponse:
    content: dict = {"detail": str(exception)}
    payload = getattr(exception, "payload", None)
    if payload is not None:
        content.update(payload)
    return JSONResponse(status_code=status_code, content=content)


def register_domain_error_handlers(app: FastAPI) -> None:
    """Register the four base ``DomainError`` → HTTP translators on ``app``."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exception: NotFoundError):
        return _error_response(exception, status.HTTP_404_NOT_FOUND)

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exception: ForbiddenError):
        return _error_response(exception, status.HTTP_403_FORBIDDEN)

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exception: ConflictError):
        return _error_response(exception, status.HTTP_409_CONFLICT)

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exception: ValidationError):
        return _error_response(exception, status.HTTP_422_UNPROCESSABLE_ENTITY)
