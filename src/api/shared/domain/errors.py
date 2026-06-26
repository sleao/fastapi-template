"""Domain error base hierarchy.

Module-specific errors (e.g. ``ProductNotFoundError``) subclass these in each
module's ``domain/errors.py``. The composition root translates each base class
to an HTTP status via ``app.exception_handler`` (see
``api.entrypoints._error_handlers``). Subclasses inherit dispatch automatically,
so ``ProductNotFoundError(NotFoundError)`` is caught by the 404 handler with no
extra wiring.

These are pure-Python exceptions: the domain and service layers raise them and
**never** raise ``HTTPException``.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base for all domain-layer errors. Never instantiated directly."""


class NotFoundError(DomainError):
    """Resource lookup failed -> HTTP 404."""


class ForbiddenError(DomainError):
    """Operation refused by domain policy -> HTTP 403."""


class ConflictError(DomainError):
    """Operation violates a uniqueness/state invariant -> HTTP 409."""


class ValidationError(DomainError):
    """Invariant violation (not Pydantic input validation) -> HTTP 422.

    Subclasses may set a ``payload`` dict (e.g. ``{"code": "..."}``) that the
    error handler merges into the JSON response body so clients can branch on a
    stable machine-readable code.
    """
