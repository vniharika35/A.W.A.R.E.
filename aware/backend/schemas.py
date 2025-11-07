"""Pydantic schemas for telemetry ingestion and inspection."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable
from typing import List

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator


class IsolationPlanRequest(BaseModel):
    leak_pipe_id: str = Field(..., examples=["P_J1_J2"])
    start_node: str = Field(..., examples=["J1"])
    end_node: str = Field(..., examples=["J2"])


class IsolationStep(BaseModel):
    order: int
    valve_id: str
    customers_affected: int
    loss_rate_lps: float


class IsolationPlanResponse(BaseModel):
    leak_pipe_id: str
    approval_required: bool
    steps: List[IsolationStep]


class IsolationExecuteRequest(BaseModel):
    leak_pipe_id: str
    valve_ids: List[str]
    approved_by: str | None = None


class IsolationActionResponse(BaseModel):
    actions: List[dict[str, object]]


class TelemetryEventIn(BaseModel):
    timestamp: datetime
    entity_type: str = Field(..., examples=["junction", "pipe", "tank", "tariff"])
    entity_id: str
    metric: str
    value: float
    unit: str
    source: str = "simulator"
    quality: float = 1.0

    model_config = ConfigDict(extra="forbid")

    @field_validator("quality")
    @classmethod
    def _quality_range(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("quality must be between 0 and 1")
        return value


class TelemetryIngestRequest(BaseModel):
    events: List[TelemetryEventIn]

    model_config = ConfigDict(extra="forbid")

    def to_records(self) -> Iterable[TelemetryEventIn]:
        return self.events


class TelemetryIngestResponse(BaseModel):
    inserted: int
    skipped: int = 0


class TelemetryStats(BaseModel):
    metric: str
    count: int


class DemandForecastPoint(BaseModel):
    timestamp: datetime
    demand_lps: float
    confidence: float


class DemandForecastResponse(BaseModel):
    issued_at: datetime
    horizon_hours: int
    points: List[DemandForecastPoint]


class PumpScheduleStepOut(BaseModel):
    start: datetime
    end: datetime
    pump_ids: List[str]
    pumps_on: int
    expected_cost_usd: float
    expected_pressure_kpa: float
    price_signal: float
    demand_signal: float
    reason: str


class EnergyOptimizationRequest(BaseModel):
    horizon_hours: int = Field(24, ge=1, le=168)
    pump_ids: List[str] = Field(default_factory=lambda: ["pump_a", "pump_b"])
    max_parallel_pumps: int = Field(2, ge=1, le=4)
    pressure_floor_kpa: float = Field(240.0, ge=150.0, le=400.0)
    energy_per_pump_mwh: float = Field(0.85, gt=0.0, le=5.0)

    model_config = ConfigDict(extra="forbid")


class EnergyOptimizationResponse(BaseModel):
    issued_at: datetime
    horizon_hours: int
    baseline_cost_usd: float
    optimized_cost_usd: float
    expected_savings_pct: float
    roi_confidence: float
    pressure_guard_breaches: int
    time_to_first_action_minutes: float
    steps: List[PumpScheduleStepOut]
    forecast: List[DemandForecastPoint]
