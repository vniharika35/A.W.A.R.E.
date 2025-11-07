"""FastAPI application exposing telemetry ingestion endpoints."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from datetime import timezone

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from sqlalchemy.orm import Session

from aware.backend.energy import EnergyService
from aware.backend.isolation import IsolationPlanner
from aware.backend.isolation import IsolationPlannerConfig
from aware.backend.isolation import IsolationPolicy
from aware.backend.isolation import IsolationStateMachine
from aware.backend.isolation import IsolationStatus
from aware.backend.isolation.network import WaterNetworkGraph
from aware.backend.ux import DashboardService
from aware.ml.detectors import LeakDetector
from aware.ml.detectors import LeakDetectorConfig

from .db import get_engine
from .db import get_session
from .models import IsolationAction
from .models import TelemetryRecord
from .schemas import DashboardAlert
from .schemas import DashboardMapResponse
from .schemas import DashboardScenario
from .schemas import DashboardSummaryResponse
from .schemas import DemandForecastPoint
from .schemas import DemandForecastResponse
from .schemas import EnergyOptimizationRequest
from .schemas import EnergyOptimizationResponse
from .schemas import IsolationActionResponse
from .schemas import IsolationExecuteRequest
from .schemas import IsolationPlanRequest
from .schemas import IsolationPlanResponse
from .schemas import IsolationStep
from .schemas import PumpScheduleStepOut
from .schemas import TelemetryIngestRequest
from .schemas import TelemetryIngestResponse
from .schemas import TelemetryStats
from .utils import leak_result_to_dict
from .utils import records_to_events


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

    events = records_to_events(records)
    config = LeakDetectorConfig(minimum_support=min(240, len(events) // 2))
    detector = LeakDetector(config)
    detector.fit_baseline(events)
    results = detector.detect(events)
    latest = results[-1]
    return {
        "status": "ok",
        "sample_size": len(events),
        "latest": leak_result_to_dict(latest),
        "alerts": [leak_result_to_dict(result) for result in results[-15:]],
    }


@app.get("/ux/dashboard/summary", response_model=DashboardSummaryResponse, tags=["ux"])
def dashboard_summary(session: Session = Depends(get_session)) -> DashboardSummaryResponse:
    service = DashboardService(session)
    snapshot = service.summary()
    return DashboardSummaryResponse(**snapshot)


@app.get("/ux/dashboard/alerts", response_model=list[DashboardAlert], tags=["ux"])
def dashboard_alerts(
    limit: int = 5,
    session: Session = Depends(get_session),
) -> list[DashboardAlert]:
    service = DashboardService(session)
    alerts = service.alerts(limit=limit)
    return [DashboardAlert(**item) for item in alerts]


@app.get("/ux/dashboard/map", response_model=DashboardMapResponse, tags=["ux"])
def dashboard_map(session: Session = Depends(get_session)) -> DashboardMapResponse:
    service = DashboardService(session)
    snapshot = service.map_state()
    return DashboardMapResponse(**snapshot)


@app.get("/ux/dashboard/scenarios", response_model=list[DashboardScenario], tags=["ux"])
def dashboard_scenarios(session: Session = Depends(get_session)) -> list[DashboardScenario]:
    service = DashboardService(session)
    return [DashboardScenario(**item) for item in service.scenarios()]


@app.get("/energy/forecast", response_model=DemandForecastResponse, tags=["energy"])
def energy_forecast(
    horizon_hours: int = 24,
    session: Session = Depends(get_session),
) -> DemandForecastResponse:
    if not 1 <= horizon_hours <= 168:
        raise HTTPException(status_code=400, detail="horizon_hours must be between 1 and 168")
    service = EnergyService(session)
    points = service.demand_forecast(horizon_hours=horizon_hours)
    issued_at = datetime.now(timezone.utc)
    return DemandForecastResponse(
        issued_at=issued_at,
        horizon_hours=horizon_hours,
        points=[
            DemandForecastPoint(
                timestamp=point.timestamp,
                demand_lps=round(point.demand_lps, 3),
                confidence=point.confidence,
            )
            for point in points
        ],
    )


@app.post("/energy/optimize", response_model=EnergyOptimizationResponse, tags=["energy"])
def energy_optimize(
    payload: EnergyOptimizationRequest,
    session: Session = Depends(get_session),
) -> EnergyOptimizationResponse:
    service = EnergyService(session)
    report = service.optimize_energy(
        horizon_hours=payload.horizon_hours,
        pump_ids=payload.pump_ids,
        max_parallel_pumps=payload.max_parallel_pumps,
        pressure_floor_kpa=payload.pressure_floor_kpa,
        energy_per_pump_mwh=payload.energy_per_pump_mwh,
    )
    steps = [
        PumpScheduleStepOut(
            start=step.start,
            end=step.end,
            pump_ids=list(step.pump_ids),
            pumps_on=step.pumps_on,
            expected_cost_usd=step.expected_cost_usd,
            expected_pressure_kpa=step.expected_pressure_kpa,
            price_signal=step.price_signal,
            demand_signal=step.demand_signal,
            reason=step.reason,
        )
        for step in report.schedule.steps
    ]
    forecast_points = [
        DemandForecastPoint(
            timestamp=point.timestamp,
            demand_lps=round(point.demand_lps, 3),
            confidence=point.confidence,
        )
        for point in report.forecast
    ]
    return EnergyOptimizationResponse(
        issued_at=report.issued_at,
        horizon_hours=report.horizon_hours,
        baseline_cost_usd=report.schedule.baseline_cost_usd,
        optimized_cost_usd=report.schedule.optimized_cost_usd,
        expected_savings_pct=report.expected_savings_pct,
        roi_confidence=report.roi_confidence,
        pressure_guard_breaches=report.pressure_guard_breaches,
        time_to_first_action_minutes=report.time_to_first_action_minutes,
        steps=steps,
        forecast=forecast_points,
    )


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
