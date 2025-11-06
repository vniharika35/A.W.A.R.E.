"""FastAPI application exposing telemetry ingestion endpoints."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from datetime import datetime
from datetime import timezone

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from sqlalchemy.orm import Session

from aware.backend.isolation import IsolationPlanner
from aware.backend.isolation import IsolationPlannerConfig
from aware.backend.isolation import IsolationPolicy
from aware.backend.isolation import IsolationStateMachine
from aware.backend.isolation import IsolationStatus
from aware.backend.isolation.network import WaterNetworkGraph
from aware.ml.detectors import LeakDetectionResult
from aware.ml.detectors import LeakDetector
from aware.ml.detectors import LeakDetectorConfig
from aware.sim.telemetry import TelemetryEvent

from .db import get_engine
from .db import get_session
from .models import IsolationAction
from .models import TelemetryRecord
from .schemas import IsolationActionResponse
from .schemas import IsolationExecuteRequest
from .schemas import IsolationPlanRequest
from .schemas import IsolationPlanResponse
from .schemas import IsolationStep
from .schemas import TelemetryIngestRequest
from .schemas import TelemetryIngestResponse
from .schemas import TelemetryStats


app = FastAPI(title="A.W.A.R.E. Telemetry Ingestion", version="0.1.0")

_graph = WaterNetworkGraph.sample()
_planner = IsolationPlanner(
    graph=_graph,
    config=IsolationPlannerConfig(
        policy=IsolationPolicy.MINIMIZE_CUSTOMERS,
        max_hops=3,
        max_radius_meters=500.0,
    ),
)
_state_machine = IsolationStateMachine()


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


@app.post("/isolation/plan", response_model=IsolationPlanResponse, tags=["isolation"])
def plan_isolation(
    payload: IsolationPlanRequest,
) -> IsolationPlanResponse:
    plan = _planner.plan(
        leak_pipe_id=payload.leak_pipe_id,
        start_node=payload.start_node,
        end_node=payload.end_node,
    )
    for status in (IsolationStatus.SUSPECTED, IsolationStatus.ISOLATING):
        try:
            _state_machine.transition(status)
        except ValueError:
            continue
    return IsolationPlanResponse(
        leak_pipe_id=plan.leak_pipe_id,
        approval_required=plan.approval_required,
        steps=[
            IsolationStep(
                order=step.order,
                valve_id=step.valve_id,
                customers_affected=step.customers_affected,
                loss_rate_lps=step.loss_rate_lps,
            )
            for step in plan.steps
        ],
    )


@app.post("/isolation/execute", response_model=IsolationActionResponse, tags=["isolation"])
def execute_isolation(
    payload: IsolationExecuteRequest,
    session: Session = Depends(get_session),
) -> IsolationActionResponse:
    approval_provided = payload.approved_by is not None
    if not approval_provided:
        raise HTTPException(status_code=400, detail="Operator approval required")

    actions = []
    now = datetime.now(timezone.utc)
    for valve_id in payload.valve_ids:
        action = IsolationAction(
            leak_pipe_id=payload.leak_pipe_id,
            valve_id=valve_id,
            action="close",
            status="completed",
            timestamp=now,
            performed_by=payload.approved_by or "unknown",
        )
        session.add(action)
        actions.append(action)
    session.commit()
    try:
        _state_machine.transition(IsolationStatus.ISOLATED)
    except ValueError:
        pass
    return IsolationActionResponse(actions=[action.as_dict() for action in actions])


@app.post("/isolation/rollback", response_model=IsolationActionResponse, tags=["isolation"])
def rollback_isolation(
    payload: IsolationExecuteRequest,
    session: Session = Depends(get_session),
) -> IsolationActionResponse:
    actions = []
    now = datetime.now(timezone.utc)
    for valve_id in payload.valve_ids:
        action = IsolationAction(
            leak_pipe_id=payload.leak_pipe_id,
            valve_id=valve_id,
            action="open",
            status="completed",
            timestamp=now,
            performed_by=payload.approved_by or "system",
        )
        session.add(action)
        actions.append(action)
    session.commit()
    for status in (IsolationStatus.RECOVERY, IsolationStatus.NORMAL):
        try:
            _state_machine.transition(status)
        except ValueError:
            continue
    return IsolationActionResponse(actions=[action.as_dict() for action in actions])
