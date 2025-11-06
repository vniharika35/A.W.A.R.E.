"""Configuration objects for isolation planning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IsolationPolicy(str, Enum):
    MINIMIZE_CUSTOMERS = "minimize_customers"
    MINIMIZE_WATER_LOSS = "minimize_water_loss"


@dataclass(frozen=True, slots=True)
class IsolationPlannerConfig:
    policy: IsolationPolicy = IsolationPolicy.MINIMIZE_CUSTOMERS
    max_hops: int = 3
    max_radius_meters: float = 500.0
