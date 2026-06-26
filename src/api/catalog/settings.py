"""Catalog module settings — env prefix ``CATALOG_``.

Per-module settings keep configuration scoped to the module that owns it. Add
fields as the module grows; the root ``Config`` stays app-wide.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class CatalogSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CATALOG_")

    # Example knob — the maximum page size catalog listings allow.
    max_page_size: int = 100
