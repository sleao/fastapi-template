"""Authentication seam — the single place to wire your auth provider.

``get_current_user`` receives the Bearer token and must return a
``UserIdentity``. Replace the dev stub below with real token verification
(JWT signature check, introspection call, session lookup, …) and map the
provider's claims onto ``UserIdentity``.

The dev stub is intentionally permissive so the template runs out of the box:
**any** Bearer token resolves to a fixed identity, and a missing token is 401.
It must never reach production — gate it on the environment or replace it.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.shared.entrypoints.schemas import UserIdentity

_bearer_scheme = HTTPBearer(auto_error=False)

# Fixed identity returned by the dev stub. Swap for real claim extraction.
_DEV_USER = UserIdentity(
    id=UUID("00000000-0000-0000-0000-000000000001"),
    email="dev@example.com",
)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> UserIdentity:  # pragma: no cover
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # TODO: verify ``credentials.credentials`` against your auth provider and
    # build a ``UserIdentity`` from the verified claims. The dev stub below
    # trusts any token — do not ship it.
    return _DEV_USER


CurrentUserDep = Annotated[UserIdentity, Depends(get_current_user)]
