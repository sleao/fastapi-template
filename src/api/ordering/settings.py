"""Ordering module settings — env prefix ``ORDERING_``."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class OrderingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ORDERING_")

    # Example knob — the largest quantity a single order line may request.
    max_order_quantity: int = 1000
