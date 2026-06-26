"""Root application settings.

One ``Config`` for app-wide concerns, read from the environment with the
``APP_`` prefix (e.g. ``APP_ENVIRONMENT=PROD``). Each business module owns a
separate ``settings.py`` with its own ``<MODULE>_`` prefix so module config
never leaks across boundaries.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEV = "DEV"
    STAGING = "STAGING"
    PROD = "PROD"


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    environment: Environment = Environment.DEV
    version: str = "0.1.0"

    @property
    def docs_url(self) -> str | None:  # pragma: no cover
        """Swagger only outside production."""
        return "/docs" if self.environment == Environment.DEV else None
