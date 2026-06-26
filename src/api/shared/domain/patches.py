"""Pure-Python helpers for building and applying partial-update patches.

These helpers preserve the **omitted-vs-null distinction** that a naive
``value is not None`` filter destroys. On a PATCH/PUT request a client can
either *omit* a nullable field (leave it untouched) or *explicitly send null*
to clear it. The two are semantically different and a partial update must
honour both:

- field omitted        -> not in the patch -> existing value preserved
- field set to null    -> in the patch with value ``None`` -> cleared to NULL
- field set to a value -> in the patch with that value -> overwritten

The mechanism that carries this distinction is a "fields_set" — the set of
field names the client actually supplied (the request schema's
``model_fields_set`` at the entrypoint). Commands carry it as a ``fields_set``
attribute.

This module is part of the domain layer: pure Python only.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any


def build_patch(command: Any, *, ignore: tuple[str, ...] = ()) -> dict[str, Any]:
    """Build a ``{field_name: value}`` patch from a command's ``fields_set``.

    Returns one entry per name in ``command.fields_set`` that is a real
    dataclass field of ``command`` and is not listed in ``ignore``. Values are
    read straight off the command, so explicitly-null fields are *included*
    (they clear the target) while unset fields are *omitted*.
    """
    declared_field_names = {dataclass_field.name for dataclass_field in dataclasses.fields(command)}
    return {
        field_name: getattr(command, field_name)
        for field_name in command.fields_set
        if field_name in declared_field_names and field_name not in ignore
    }


def apply_patch(target: object, patch: Mapping[str, Any]) -> None:
    """Apply every entry of ``patch`` onto ``target`` via ``setattr``.

    Deliberately performs **no** ``value is not None`` filtering: the caller is
    responsible for passing only the fields the client actually set, so an
    explicit ``None`` here clears the corresponding attribute to NULL.
    """
    for field_name, value in patch.items():
        setattr(target, field_name, value)
