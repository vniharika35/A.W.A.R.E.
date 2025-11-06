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
