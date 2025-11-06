"""Rule-based multi-sensor leak detection with simple calibration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import exp
from typing import Iterable

import pandas as pd

from aware.sim.telemetry import TelemetryEvent


@dataclass(frozen=True, slots=True)
class Reason:
    metric: str
    score: float
    details: str


@dataclass(frozen=True, slots=True)
class LeakDetectionResult:
    timestamp: datetime
    entity_id: str
    probability: float
    triggered: bool
    reasons: tuple[Reason, ...]


@dataclass(frozen=True, slots=True)
class LeakDetectorConfig:
    baseline_window: int = 60
    trigger_threshold: float = 2.5
    hysteresis: float = 0.8
    decay: float = 0.6
    minimum_support: int = 45
    max_reasons: int = 3


class LeakDetector:
    """Fuse pressure, demand, and flow anomalies into calibrated leak probabilities."""

    def __init__(self, config: LeakDetectorConfig | None = None) -> None:
        self.config = config or LeakDetectorConfig()
        self._baseline: dict[str, tuple[float, float]] | None = None

    def fit_baseline(self, events: Iterable[TelemetryEvent]) -> None:
        frame = self._events_to_features(events)
        if frame.empty:
            raise ValueError("No telemetry events supplied for baseline fit")

        baseline = {}
        window = frame.iloc[: self.config.baseline_window]
        for column in ["pressure_mean", "pressure_drop", "flow_total", "demand_total"]:
            mean = float(window[column].mean())
            std = float(window[column].std(ddof=1) or 1.0)
            baseline[column] = (mean, std)
        self._baseline = baseline

    def detect(self, events: Iterable[TelemetryEvent]) -> list[LeakDetectionResult]:
        if self._baseline is None:
            raise RuntimeError("Baseline not fitted; call fit_baseline() first")
        frame = self._events_to_features(events)
        if len(frame) < self.config.minimum_support:
            raise ValueError("Insufficient telemetry history for leak detection")

        cumulative = 0.0
        results: list[LeakDetectionResult] = []
        for row in frame.itertuples():
            z_scores = self._compute_z_scores(row)
            score = max(z_scores.values())
            cumulative = max(0.0, cumulative * self.config.decay + score - self.config.hysteresis)
            probability = self._calibrate_probability(cumulative)
            triggered = probability >= self._trigger_probability()
            reasons = self._top_reasons(z_scores)
            results.append(
                LeakDetectionResult(
                    timestamp=row.Index,
                    entity_id="zone-1",
                    probability=probability,
                    triggered=triggered,
                    reasons=reasons,
                ),
            )
        return results

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _events_to_features(self, events: Iterable[TelemetryEvent]) -> pd.DataFrame:
        frame = pd.DataFrame(event.asdict() for event in events)
        if frame.empty:
            return frame
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        frame = frame.set_index("timestamp").sort_index()

        pressure = frame[frame["metric"] == "pressure_kpa"].groupby("timestamp")["value"].mean()
        demand = frame[frame["metric"] == "demand_lps"].groupby("timestamp")["value"].sum()
        flow = frame[frame["metric"] == "flow_lps"].groupby("timestamp")["value"].sum()

        features = (
            pd.DataFrame(
                {
                    "pressure_mean": pressure,
                    "flow_total": flow.abs(),
                    "demand_total": demand.abs(),
                }
            )
            .fillna(method="ffill")
            .dropna()
        )
        baseline_pressure = float(features["pressure_mean"].iloc[0])
        features["pressure_drop"] = (baseline_pressure - features["pressure_mean"]).clip(lower=0.0)
        return features

    def _compute_z_scores(self, row: pd.Series | pd.Index) -> dict[str, float]:
        assert self._baseline is not None
        z_scores: dict[str, float] = {}
        for key, value in {
            "pressure": row.pressure_drop,
            "flow": row.flow_total,
            "demand": row.demand_total,
        }.items():
            mean, std = self._baseline_mapping(key)
            deviation = value - mean if key != "pressure" else value
            z_scores[key] = max(0.0, deviation / std)
        return z_scores

    def _baseline_mapping(self, key: str) -> tuple[float, float]:
        assert self._baseline is not None
        mapping = {
            "pressure": self._baseline["pressure_drop"],
            "flow": self._baseline["flow_total"],
            "demand": self._baseline["demand_total"],
        }
        return mapping[key]

    def _calibrate_probability(self, cumulative: float) -> float:
        # Logistic-style calibration derived from target trigger threshold
        beta = self.config.trigger_threshold
        alpha = 1.4
        return 1.0 / (1.0 + exp(-alpha * (cumulative - beta)))

    def _trigger_probability(self) -> float:
        # Probability equivalent of trigger threshold when cumulative == trigger_threshold
        alpha = 1.4
        return 1.0 / (1.0 + exp(-alpha * 0.0))

    def _top_reasons(self, scores: dict[str, float]) -> tuple[Reason, ...]:
        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top = ordered[: self.config.max_reasons]
        return tuple(
            Reason(metric=metric, score=score, details=self._reason_details(metric, score))
            for metric, score in top
            if score > 0.0
        )

    def _reason_details(self, metric: str, score: float) -> str:
        if metric == "pressure":
            return f"Pressure drop z-score {score:.2f}"
        if metric == "flow":
            return f"Flow increase z-score {score:.2f}"
        if metric == "demand":
            return f"Demand increase z-score {score:.2f}"
        return f"Signal score {score:.2f}"
