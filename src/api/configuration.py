from enum import StrEnum

from pydantic_settings import BaseSettings


class Environment(StrEnum):
    DEV = "DEV"
    STAGING = "STAGING"
    PROD = "PROD"


class Config(BaseSettings):
    ENVIRONMENT: Environment = Environment.DEV
    APP_VERSION: str = "1.0"

    TIMEZONE: str = "UTC"
    HTTP_TIMEOUT: float = 10.0

    HOME_MESSAGE: str = "© My API — All rights reserved"

    @property
    def docs_url(self):  # pragma: no cover
        return "/docs" if self.ENVIRONMENT == Environment.DEV else None
