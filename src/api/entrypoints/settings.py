"""Root settings aggregation.

Composes the app-wide ``Config`` with each module's settings so a single object
gives the whole runtime configuration. Each module keeps its own
``settings.py`` with a distinct env prefix; this just gathers them.
"""

from __future__ import annotations

from functools import lru_cache

from api.catalog.settings import CatalogSettings
from api.ordering.settings import OrderingSettings
from api.shared.settings import Config


@lru_cache
def get_catalog_settings() -> CatalogSettings:  # pragma: no cover
    return CatalogSettings()


@lru_cache
def get_ordering_settings() -> OrderingSettings:  # pragma: no cover
    return OrderingSettings()


@lru_cache
def get_root_config() -> Config:  # pragma: no cover
    return Config()
