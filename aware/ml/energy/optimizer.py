"""Energy optimization orchestration: forecasting + pump scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from typing import Iterable

from .forecasting import DemandForecaster
from .forecasting import ForecastPoint
from .scheduling import PumpScheduler
from .scheduling import PumpScheduleResult


@dataclass(frozen=True, slots=True)
class EnergyOptimizationReport:
    issued_at: datetime
    horizon_hours: int
    forecast: tuple[ForecastPoint, ...]
    schedule: PumpScheduleResult
    expected_savings_pct: float
    roi_confidence: float
    pressure_guard_breaches: int
    time_to_first_action_minutes: float


class EnergyOptimizer:
    """Combines demand forecasting and pump scheduling into an actionable plan."""

    def __init__(
        self,
        forecaster: DemandForecaster | None = None,
        scheduler: PumpScheduler | None = None,
    ) -> None:
        self.forecaster = forecaster or DemandForecaster()
        self.scheduler = scheduler or PumpScheduler()

    def optimize(
        self,
        demand_series: Iterable[tuple[datetime, float]] | object,
        tariff_series: object,
        *,
        horizon_hours: int | None = None,
    ) -> EnergyOptimizationReport:
        forecast = self.forecaster.forecast(demand_series, horizon_hours=horizon_hours)
        schedule = self.scheduler.build_schedule(forecast, tariff_series)  # type: ignore[arg-type]
        issued_at = datetime.now(timezone.utc)
        horizon = horizon_hours or self.forecaster.config.horizon_hours
        time_to_first_action = self._time_to_first_action_minutes(issued_at, schedule)
        roi_confidence = self._roi_confidence(forecast)
        return EnergyOptimizationReport(
            issued_at=issued_at,
            horizon_hours=horizon,
            forecast=tuple(forecast),
            schedule=schedule,
            expected_savings_pct=schedule.savings_pct,
            roi_confidence=roi_confidence,
            pressure_guard_breaches=schedule.pressure_guard_breaches,
            time_to_first_action_minutes=time_to_first_action,
        )

    def _time_to_first_action_minutes(
        self,
        issued_at: datetime,
        schedule: PumpScheduleResult,
    ) -> float:
        if not schedule.steps:
            return 0.0
        first_start = schedule.steps[0].start
        delta_minutes = (first_start - issued_at).total_seconds() / 60.0
        return max(0.0, round(delta_minutes, 2))

    def _roi_confidence(self, forecast: Iterable[ForecastPoint]) -> float:
        count = sum(1 for _ in forecast)
        confidence = 0.5 + min(0.45, count / 240)
        return round(confidence, 3)
