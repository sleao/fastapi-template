from fastapi import APIRouter

from api.domain.auth.enums import UserRoles
from api.domain.auth.schemas import UserIdentity
from api.rest.controllers.auth.dependencies import (
    CurrentUserDep,
    require_own_company,
    require_role,
)
from api.rest.dependencies import AppConfigDep

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/")
async def home(config: AppConfigDep):
    return config.HOME_MESSAGE


@router.get("/protected", response_model=UserIdentity)
async def protected(user: UserIdentity = CurrentUserDep):
    return user


@router.get("/requires_role", response_model=UserIdentity)
async def requires_role(user: UserIdentity = require_role(UserRoles.READER)):
    return user


@router.get("/{company_id}/requires_company", response_model=UserIdentity)
async def requires_company_access(user: UserIdentity = require_own_company()):
    return user
