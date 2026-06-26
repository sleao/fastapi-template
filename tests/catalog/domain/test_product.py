"""Pure-domain tests for the Product aggregate — no DB, no framework."""

from __future__ import annotations

import pytest

from api.catalog.domain.enums import ProductStatus
from api.shared.domain.errors import ConflictError
from tests.factory import create_product


class TestDiscontinue:
    def test_active_product_becomes_discontinued(self) -> None:
        """GIVEN an active product WHEN discontinued THEN status flips."""
        product = create_product(status=ProductStatus.ACTIVE)
        product.discontinue()
        assert product.status is ProductStatus.DISCONTINUED

    def test_discontinuing_twice_raises_conflict(self) -> None:
        """GIVEN a discontinued product WHEN discontinued again THEN conflict."""
        product = create_product(status=ProductStatus.DISCONTINUED)
        with pytest.raises(ConflictError):
            product.discontinue()


class TestIsOrderable:
    def test_active_is_orderable(self) -> None:
        assert create_product(status=ProductStatus.ACTIVE).is_orderable is True

    def test_discontinued_is_not_orderable(self) -> None:
        assert create_product(status=ProductStatus.DISCONTINUED).is_orderable is False
