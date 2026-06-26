"""Pure-Python identifier helpers and semantic UUID aliases.

A single shared id factory (``new_uuid``) so every module's domain models agree
on one implementation, plus semantic aliases over ``UUID`` so a command field
reads as ``ProductId`` / ``OrderId`` rather than an anonymous ``UUID`` and a
mix-up is easier to spot in review.

The aliases are plain ``typing.TypeAlias`` declarations — documentation only,
no runtime enforcement. Add new ones here as modules grow more id fields.

This module is part of the domain layer: pure Python only.
"""

from __future__ import annotations

import uuid
from typing import TypeAlias
from uuid import UUID


def new_uuid() -> UUID:
    """Return a fresh time-ordered UUID7 (sortable by creation time)."""
    return uuid.uuid7()


# Semantic id aliases — readability only (see module docstring).
ProductId: TypeAlias = UUID
OrderId: TypeAlias = UUID
CustomerId: TypeAlias = UUID
