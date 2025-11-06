from __future__ import annotations

import math
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest

from aware.ml.detectors import LeakDetector
from aware.ml.detectors import LeakDetectorConfig
from aware.sim.telemetry import TelemetryEvent


def _generate_events(
    leak_start: int | None = None,
    length: int = 240,
) -> list[TelemetryEvent]:
    base_ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
    events: list[TelemetryEvent] = []
    for idx in range(length):
        timestamp = base_ts + timedelta(seconds=idx * 2)
        pressure = 205.0 + 0.2 * math.sin(idx / 12)
        flow = 8.0 + 0.05 * math.cos(idx / 10)
        demand = 3.0 + 0.03 * math.sin(idx / 8)
        if leak_start is not None and idx >= leak_start:
            pressure -= 3.5
            flow += 3.0
            demand += 2.5
        events.extend(
            [
                TelemetryEvent(
                    timestamp=timestamp,
                    entity_type="junction",
                    entity_id="J1",
                    metric="pressure_kpa",
                    value=pressure,
                    unit="kPa",
                ),
                TelemetryEvent(
                    timestamp=timestamp,
                    entity_type="pipe",
                    entity_id="P_J1_J2",
                    metric="flow_lps",
                    value=flow,
                    unit="L/s",
                ),
                TelemetryEvent(
                    timestamp=timestamp,
                    entity_type="junction",
                    entity_id="J1",
                    metric="demand_lps",
                    value=demand,
                    unit="L/s",
                ),
            ]
        )
    return events


def test_detector_flags_leak() -> None:
    events = _generate_events(leak_start=90)
    detector = LeakDetector(LeakDetectorConfig(baseline_window=60, minimum_support=90))
    detector.fit_baseline(events)
    results = detector.detect(events)
    assert any(result.triggered for result in results[-30:])
    latest = results[-1]
    assert latest.probability > 0.5
    reason_metrics = {reason.metric for reason in latest.reasons}
    assert "pressure" in reason_metrics
    assert "flow" in reason_metrics


def test_detector_respects_baseline() -> None:
    events = _generate_events(leak_start=None, length=360)
    config = LeakDetectorConfig(
        baseline_window=120,
        trigger_threshold=4.0,
        hysteresis=1.2,
        decay=0.5,
        minimum_support=180,
    )
    detector = LeakDetector(config)
    detector.fit_baseline(events)
    results = detector.detect(events)
    tail = results[-60:]
    assert all(not result.triggered for result in tail)
    assert max(result.probability for result in tail) < 0.4


@pytest.mark.parametrize(
    ("window", "expect_error"),
    [
        (180, True),  # 60 timestamps < minimum support
        (360, False),  # 120 timestamps == minimum support
    ],
)
def test_detector_requires_minimum_support(window: int, expect_error: bool) -> None:
    events = _generate_events(leak_start=180, length=360)
    detector = LeakDetector(LeakDetectorConfig(baseline_window=30, minimum_support=120))
    detector.fit_baseline(events)
    subset = events[-window:]
    if expect_error:
        with pytest.raises(ValueError):
            detector.detect(subset)
    else:
        detector.detect(subset)
