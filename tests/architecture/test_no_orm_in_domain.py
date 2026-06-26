"""Belt-and-braces: every ``api/<module>/domain/**/*.py`` is framework-free.

The "Domain is pure Python" import-linter contract forbids framework imports;
this catches sneakier forms (``Mapped[...]``, ``relationship(...)``) that a
re-export chain could hide from static import analysis.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_FILES = sorted(
    path
    for path in (PROJECT_ROOT / "src" / "api").glob("*/domain/**/*.py")
    if path.name != "__init__.py"
)

FORBIDDEN_PATTERNS = (
    re.compile(r"\bMapped\["),
    re.compile(r"\bfrom sqlalchemy\b"),
    re.compile(r"\bimport sqlalchemy\b"),
    re.compile(r"\bfrom fastapi\b"),
    re.compile(r"\bimport fastapi\b"),
    re.compile(r"\bfrom pydantic\b"),
    re.compile(r"\bimport pydantic\b"),
    re.compile(r"\brelationship\("),
    re.compile(r"\bmapped_column\("),
)


@pytest.mark.parametrize(
    "domain_file",
    DOMAIN_FILES,
    ids=lambda domain_file: str(domain_file.relative_to(PROJECT_ROOT)),
)
def test_domain_file_has_no_orm_tokens(domain_file: Path) -> None:
    content = domain_file.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_PATTERNS:
        match = pattern.search(content)
        assert match is None, (
            f"{domain_file.relative_to(PROJECT_ROOT)} has forbidden token: {match.group(0)!r}"
        )
