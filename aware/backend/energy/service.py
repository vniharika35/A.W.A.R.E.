"""Service layer bridging the DB to the energy optimization modules."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Sequence

import pandas as pd
from sqlalchemy.orm import Session

from aware.ml.energy import DemandForecaster
from aware.ml.energy import EnergyOptimizationReport
from aware.ml.energy import EnergyOptimizer
from aware.ml.energy import ForecastPoint
from aware.ml.energy import PumpScheduler

from ..models import TelemetryRecord


class EnergyService:
    """Generates forecasts and optimization plans from persisted telemetry."""

    def __init__(
        self,
        session: Session,
        *,
        forecaster: DemandForecaster | None = None,
        scheduler: PumpScheduler | None = None,
    ) -> None:
        self.session = session
        self.forecaster = forecaster or DemandForecaster()
        self.scheduler = scheduler or PumpScheduler()

    def demand_forecast(self, *, horizon_hours: int | None = None) -> list[ForecastPoint]:
        lookback = max(self.forecaster.config.lookback_hours, (horizon_hours or 0) * 2)
        lookback = max(lookback, 48)
        demand_series = self._load_metric_series("demand_lps", lookback_hours=lookback)
        return self.forecaster.forecast(demand_series, horizon_hours=horizon_hours)

    def optimize_energy(
        self,
        *,
        horizon_hours: int | None = None,
        pump_ids: Sequence[str] | None = None,
        max_parallel_pumps: int | None = None,
        pressure_floor_kpa: float | None = None,
        energy_per_pump_mwh: float | None = None,
    ) -> EnergyOptimizationReport:
        demand_lookback = max(self.forecaster.config.lookback_hours, (horizon_hours or 24) * 2)
        tariff_lookback = max(72, (horizon_hours or 24) * 2)
        demand_series = self._load_metric_series("demand_lps", lookback_hours=demand_lookback)
        tariff_series = self._load_metric_series("price_per_mwh", lookback_hours=tariff_lookback)

        config = replace(
            self.scheduler.config,
            pump_ids=tuple(pump_ids) if pump_ids else self.scheduler.config.pump_ids,
            max_parallel_pumps=max_parallel_pumps or self.scheduler.config.max_parallel_pumps,
            min_pressure_kpa=pressure_floor_kpa or self.scheduler.config.min_pressure_kpa,
            energy_per_pump_mwh=energy_per_pump_mwh or self.scheduler.config.energy_per_pump_mwh,
        )
        scheduler = PumpScheduler(config)
        optimizer = EnergyOptimizer(self.forecaster, scheduler)
        return optimizer.optimize(
            demand_series,
            tariff_series,
            horizon_hours=horizon_hours,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_metric_series(self, metric: str, *, lookback_hours: int) -> pd.Series:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        rows = (
            self.session.query(TelemetryRecord.timestamp, TelemetryRecord.value)
            .filter(TelemetryRecord.metric == metric)
            .filter(TelemetryRecord.timestamp >= cutoff)
            .order_by(TelemetryRecord.timestamp)
            .all()
        )
        if not rows:
            raise ValueError(f"no telemetry available for metric {metric}")
        frame = pd.DataFrame(rows, columns=["timestamp", "value"])
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        aggregated = frame.groupby("timestamp")["value"].sum().sort_index()
        return aggregated
