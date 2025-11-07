"""Shared backend helpers for telemetry conversions and explainability."""

from __future__ import annotations

from collections.abc import Iterable

from aware.ml.detectors import LeakDetectionResult
from aware.sim.telemetry import TelemetryEvent

from .models import TelemetryRecord


def records_to_events(records: Iterable[TelemetryRecord]) -> list[TelemetryEvent]:
    ordered = sorted(records, key=lambda record: record.timestamp)
    return [
        TelemetryEvent(
            timestamp=record.timestamp,
            entity_type=record.entity_type,
            entity_id=record.entity_id,
            metric=record.metric,
            value=float(record.value),
            unit=record.unit,
            source=record.source,
            quality=float(record.quality or 1.0),
        )
        for record in ordered
    ]


def leak_result_to_dict(result: LeakDetectionResult) -> dict[str, object]:
    return {
        "timestamp": result.timestamp.isoformat(),
        "entity_id": result.entity_id,
        "probability": result.probability,
        "triggered": result.triggered,
        "reasons": [
            {
                "metric": reason.metric,
                "score": reason.score,
                "details": reason.details,
            }
            for reason in result.reasons
        ],
    }
