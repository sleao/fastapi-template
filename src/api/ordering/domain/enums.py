"""Ordering enums — stored as strings."""

from __future__ import annotations

from enum import StrEnum


class OrderStatus(StrEnum):
    PLACED = "PLACED"
    CANCELLED = "CANCELLED"
