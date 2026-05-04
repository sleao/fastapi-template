import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.domain.auth.enums import UserRoles
from api.domain.auth.schemas import UserIdentity

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> UserIdentity:
    # Wire in your auth provider's token verification here.
    # On failure, raise HTTPException(status_code=401).
    raise NotImplementedError


def require_role(*roles: UserRoles):
    """Dependency factory that restricts access to users with one of the given roles."""

    async def _check(user: UserIdentity = CurrentUserDep) -> UserIdentity:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return Depends(_check)


def require_own_company():
    """Dependency factory that ensures the user can only access their own company's resources.

    Expects `company_id` to be present as a path parameter in the route.
    """

    async def _check(
        company_id: int,
        user: UserIdentity = CurrentUserDep,
    ) -> UserIdentity:
        if user.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this company",
            )
        return user

    return Depends(_check)


CurrentUserDep: UserIdentity = Depends(get_current_user)
