"""Demand forecasting primitives used by the energy optimizer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import pandas as pd


@dataclass(frozen=True, slots=True)
class ForecastPoint:
    """Represents a single forecasted demand point."""

    timestamp: datetime
    demand_lps: float
    confidence: float


@dataclass(frozen=True, slots=True)
class DemandForecastConfig:
    """Configuration parameters for the demand forecaster."""

    horizon_hours: int = 24
    lookback_hours: int = 72
    min_history_points: int = 24
    smoothing_factor: float = 0.25
    backcast_hours: int = 6


class DemandForecaster:
    """Generates short horizon demand forecasts from recent telemetry."""

    def __init__(self, config: DemandForecastConfig | None = None) -> None:
        self.config = config or DemandForecastConfig()

    def forecast(
        self,
        demand_series: pd.Series | Iterable[tuple[datetime, float]],
        *,
        horizon_hours: int | None = None,
    ) -> list[ForecastPoint]:
        series = self._normalize_series(demand_series)
        if len(series) < self.config.min_history_points:
            raise ValueError("insufficient demand history for forecasting")

        hourly = series.resample("1H").mean().dropna()
        if hourly.empty:
            raise ValueError("unable to resample demand history to hourly cadence")

        lookback_hours = min(self.config.lookback_hours, len(hourly))
        hourly = hourly.tail(lookback_hours)

        pattern = hourly.groupby(hourly.index.hour).mean()
        variability = hourly.groupby(hourly.index.hour).std().fillna(0.0)
        baseline = float(hourly.iloc[-1])
        backcast_window = min(self.config.backcast_hours, len(hourly))
        trend = float(hourly.diff().tail(backcast_window).mean() or 0.0)

        points: list[ForecastPoint] = []
        last_timestamp = hourly.index[-1]
        horizon = horizon_hours or self.config.horizon_hours
        for hour_offset in range(1, horizon + 1):
            ts = last_timestamp + pd.Timedelta(hours=hour_offset)
            hour_of_day = ts.hour
            seasonal = float(pattern.get(hour_of_day, baseline))
            smoothed = (
                self.config.smoothing_factor * seasonal
                + (1 - self.config.smoothing_factor) * baseline
            )
            trend_adjusted = smoothed + trend * min(hour_offset, self.config.backcast_hours) * 0.5
            demand = max(0.0, trend_adjusted)
            std = float(variability.get(hour_of_day, variability.mean() or 0.0))
            confidence = self._confidence(demand, std)
            points.append(
                ForecastPoint(
                    timestamp=ts.to_pydatetime(),
                    demand_lps=demand,
                    confidence=confidence,
                ),
            )
        return points

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _normalize_series(self, series: pd.Series | Iterable[tuple[datetime, float]]) -> pd.Series:
        if isinstance(series, pd.Series):
            base = series
        else:
            base = pd.Series({ts: value for ts, value in series})
        if base.empty:
            raise ValueError("empty demand series")
        if not isinstance(base.index, pd.DatetimeIndex):
            base.index = pd.to_datetime(base.index, utc=True)
        normalized = (
            base.sort_index()
            .astype(float)
            .resample("15T")
            .mean()
            .interpolate(limit_direction="both")
        )
        return normalized.dropna()

    def _confidence(self, demand: float, std: float) -> float:
        if demand <= 0:
            return 0.5
        ratio = std / max(demand, 1e-3)
        confidence = 1.0 - min(0.5, ratio)
        return max(0.5, min(0.99, confidence))
