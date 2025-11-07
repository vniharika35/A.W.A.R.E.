"""Pump scheduling heuristics that align with tariff windows and pressure guardrails."""

from __future__ import annotations

import math
from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime
from typing import Sequence

import pandas as pd

from .forecasting import ForecastPoint


@dataclass(frozen=True, slots=True)
class PumpScheduleStep:
    start: datetime
    end: datetime
    pump_ids: tuple[str, ...]
    pumps_on: int
    expected_cost_usd: float
    expected_pressure_kpa: float
    price_signal: float
    demand_signal: float
    reason: str


@dataclass(frozen=True, slots=True)
class PumpScheduleResult:
    steps: tuple[PumpScheduleStep, ...]
    baseline_cost_usd: float
    optimized_cost_usd: float
    savings_pct: float
    pressure_guard_breaches: int


@dataclass(frozen=True, slots=True)
class PumpScheduleConfig:
    pump_ids: tuple[str, ...] = ("pump_a", "pump_b")
    max_parallel_pumps: int = 2
    min_pressure_kpa: float = 240.0
    nominal_pressure_kpa: float = 280.0
    pressure_slope_kpa: float = 35.0
    energy_per_pump_mwh: float = 0.85
    demand_weight: float = 0.6
    price_weight: float = 0.4

    def with_overrides(
        self,
        *,
        pump_ids: Sequence[str] | None = None,
        max_parallel_pumps: int | None = None,
        min_pressure_kpa: float | None = None,
        energy_per_pump_mwh: float | None = None,
    ) -> "PumpScheduleConfig":
        return replace(
            self,
            pump_ids=tuple(pump_ids) if pump_ids is not None else self.pump_ids,
            max_parallel_pumps=max_parallel_pumps or self.max_parallel_pumps,
            min_pressure_kpa=min_pressure_kpa or self.min_pressure_kpa,
            energy_per_pump_mwh=energy_per_pump_mwh or self.energy_per_pump_mwh,
        )


class PumpScheduler:
    """Schedules pump operations against tariff windows while enforcing pressure guardrails."""

    def __init__(self, config: PumpScheduleConfig | None = None) -> None:
        self.config = config or PumpScheduleConfig()

    def build_schedule(
        self,
        forecast: Sequence[ForecastPoint],
        tariff_series: pd.Series,
    ) -> PumpScheduleResult:
        if not forecast:
            raise ValueError("forecast required for pump scheduling")
        tariff = self._normalize_tariff(tariff_series)
        if tariff.empty:
            raise ValueError("tariff series is empty")

        demand_max = max(point.demand_lps for point in forecast) or 1.0
        price_min = float(tariff.min())
        price_max = float(tariff.max())
        price_range = max(price_max - price_min, 1e-3)
        low_price_threshold = float(tariff.quantile(0.35))

        steps: list[PumpScheduleStep] = []
        baseline_cost = 0.0
        optimized_cost = 0.0
        guardrail_breaches = 0

        for point in forecast:
            start_ts = self._hour_floor(point.timestamp)
            end_ts = start_ts + pd.Timedelta(hours=1)
            if start_ts in tariff.index:
                hour_price = float(tariff.loc[start_ts])
            else:
                hour_price = float(tariff.asof(start_ts))
                if math.isnan(hour_price):
                    hour_price = float(tariff.iloc[-1])
            demand_signal = point.demand_lps / demand_max
            low_price_signal = 1.0 - (hour_price - price_min) / price_range
            score = (
                demand_signal * self.config.demand_weight
                + low_price_signal * self.config.price_weight
            )
            pumps_desired = min(
                self.config.max_parallel_pumps,
                max(0, round(score * self.config.max_parallel_pumps)),
            )
            if demand_signal > 0.15:
                pumps_desired = max(1, pumps_desired)

            expected_pressure = self._expected_pressure(demand_signal, pumps_desired)
            guardrail_triggered = expected_pressure < self.config.min_pressure_kpa
            if guardrail_triggered:
                guardrail_breaches += 1
                pumps_desired = max(1, pumps_desired)
                expected_pressure = max(expected_pressure, self.config.min_pressure_kpa)

            active_pumps = tuple(self.config.pump_ids[:pumps_desired])
            step_cost = pumps_desired * self.config.energy_per_pump_mwh * hour_price
            optimized_cost += step_cost

            baseline_pumps = self._baseline_pumps(demand_signal)
            baseline_cost += baseline_pumps * self.config.energy_per_pump_mwh * hour_price

            reason = self._reason(
                demand_signal, hour_price, low_price_threshold, guardrail_triggered
            )
            steps.append(
                PumpScheduleStep(
                    start=start_ts.to_pydatetime(),
                    end=end_ts.to_pydatetime(),
                    pump_ids=active_pumps,
                    pumps_on=pumps_desired,
                    expected_cost_usd=round(step_cost, 2),
                    expected_pressure_kpa=round(expected_pressure, 1),
                    price_signal=round(low_price_signal, 3),
                    demand_signal=round(demand_signal, 3),
                    reason=reason,
                ),
            )

        savings_pct = 0.0
        if baseline_cost > 0:
            savings_pct = max(0.0, (baseline_cost - optimized_cost) / baseline_cost * 100)

        return PumpScheduleResult(
            steps=tuple(steps),
            baseline_cost_usd=round(baseline_cost, 2),
            optimized_cost_usd=round(optimized_cost, 2),
            savings_pct=round(savings_pct, 2),
            pressure_guard_breaches=guardrail_breaches,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalize_tariff(self, tariff: pd.Series) -> pd.Series:
        if not isinstance(tariff.index, pd.DatetimeIndex):
            tariff.index = pd.to_datetime(tariff.index, utc=True)
        hourly = (
            tariff.sort_index()
            .astype(float)
            .resample("1H")
            .mean()
            .interpolate(limit_direction="both")
        )
        return hourly

    def _expected_pressure(self, demand_signal: float, pumps_on: int) -> float:
        load_penalty = demand_signal * self.config.pressure_slope_kpa
        relief = pumps_on * (self.config.pressure_slope_kpa * 0.25)
        return self.config.nominal_pressure_kpa - load_penalty + relief

    def _baseline_pumps(self, demand_signal: float) -> int:
        if demand_signal <= 0.05:
            return 0
        return min(
            len(self.config.pump_ids),
            max(1, math.ceil(demand_signal * len(self.config.pump_ids))),
        )

    def _reason(
        self,
        demand_signal: float,
        price: float,
        low_price_threshold: float,
        guardrail_triggered: bool,
    ) -> str:
        if guardrail_triggered:
            return "pressure-guard"
        if price <= low_price_threshold:
            return "charge-low-tariff"
        if demand_signal >= 0.7:
            return "peak-demand"
        if demand_signal <= 0.1 and price > low_price_threshold:
            return "coast-on-storage"
        return "balanced-response"

    def _hour_floor(self, timestamp: datetime) -> pd.Timestamp:
        ts = pd.Timestamp(timestamp)
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        else:
            ts = ts.tz_convert("UTC")
        return ts.floor("H")
