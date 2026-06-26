"""Catalog enums — stored as strings (no native PG enums)."""

from __future__ import annotations

from enum import StrEnum


class ProductStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISCONTINUED = "DISCONTINUED"
