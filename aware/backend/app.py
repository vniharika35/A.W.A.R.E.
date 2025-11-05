"""FastAPI application exposing telemetry ingestion endpoints."""

from __future__ import annotations

from collections import Counter

from fastapi import Depends
from fastapi import FastAPI
from sqlalchemy.orm import Session

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
