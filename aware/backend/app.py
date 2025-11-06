"""FastAPI application exposing telemetry ingestion endpoints."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from fastapi import Depends
from fastapi import FastAPI
from sqlalchemy.orm import Session

from aware.ml.detectors import LeakDetectionResult
from aware.ml.detectors import LeakDetector
from aware.ml.detectors import LeakDetectorConfig
from aware.sim.telemetry import TelemetryEvent

from .db import get_engine
from .db import get_session
from .models import TelemetryRecord
from .schemas import TelemetryIngestRequest
from .schemas import TelemetryIngestResponse
from .schemas import TelemetryStats


app = FastAPI(title="A.W.A.R.E. Telemetry Ingestion", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    get_engine(force_init=True)


@app.get("/healthz", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/telemetry", response_model=TelemetryIngestResponse, tags=["telemetry"])
def ingest_telemetry(
    payload: TelemetryIngestRequest,
    session: Session = Depends(get_session),
) -> TelemetryIngestResponse:
    records = [TelemetryRecord(**event.model_dump()) for event in payload.to_records()]
    session.add_all(records)
    session.commit()
    return TelemetryIngestResponse(inserted=len(records))


@app.get("/telemetry/stats", response_model=list[TelemetryStats], tags=["telemetry"])
def telemetry_stats(session: Session = Depends(get_session)) -> list[TelemetryStats]:
    rows = session.query(TelemetryRecord.metric).all()
    counter = Counter(row[0] for row in rows)
    return [TelemetryStats(metric=metric, count=count) for metric, count in sorted(counter.items())]


@app.get("/telemetry/latest", tags=["telemetry"])
def latest_events(
    limit: int = 25,
    session: Session = Depends(get_session),
) -> list[dict[str, object]]:
    query = session.query(TelemetryRecord).order_by(TelemetryRecord.timestamp.desc()).limit(limit)
    return [record.as_dict() for record in query.all()]


@app.get("/leaks/analyze", tags=["leaks"])
def analyze_leaks(
    window: int = 600,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    records = (
        session.query(TelemetryRecord)
        .order_by(TelemetryRecord.timestamp.desc())
        .limit(window)
        .all()
    )
    if not records:
        return {"status": "no-data", "alerts": []}

    events = _records_to_events(records)
    config = LeakDetectorConfig(minimum_support=min(240, len(events) // 2))
    detector = LeakDetector(config)
    detector.fit_baseline(events)
    results = detector.detect(events)
    latest = results[-1]
    return {
        "status": "ok",
        "sample_size": len(events),
        "latest": _result_to_dict(latest),
        "alerts": [_result_to_dict(result) for result in results[-15:]],
    }


def _records_to_events(records: Iterable[TelemetryRecord]) -> list[TelemetryEvent]:
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


def _result_to_dict(result: LeakDetectionResult) -> dict[str, object]:
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
