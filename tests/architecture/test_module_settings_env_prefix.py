"""Each module's settings uses its own ``<MODULE>_`` env prefix.

Keeps module configuration namespaced so env vars never collide across modules.
"""

from __future__ import annotations

import pytest

from api.catalog.settings import CatalogSettings
from api.ordering.settings import OrderingSettings


@pytest.mark.parametrize(
    ("settings_class", "expected_prefix"),
    [
        (CatalogSettings, "CATALOG_"),
        (OrderingSettings, "ORDERING_"),
    ],
)
def test_settings_env_prefix(settings_class, expected_prefix) -> None:
    assert settings_class.model_config["env_prefix"] == expected_prefix
