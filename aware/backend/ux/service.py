"""Dashboard aggregation for Phase 05 real-time UX endpoints."""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from aware.backend.energy import EnergyService
from aware.backend.utils import leak_result_to_dict
from aware.backend.utils import records_to_events
from aware.ml.detectors import LeakDetector
from aware.ml.detectors import LeakDetectorConfig

from ..isolation.network import WaterNetworkGraph
from ..models import IsolationAction
from ..models import TelemetryRecord


NODE_LAYOUT = {
    "RES1": {"lat": 37.342, "lon": -121.942, "type": "reservoir"},
    "J1": {"lat": 37.344, "lon": -121.939, "type": "junction"},
    "J2": {"lat": 37.346, "lon": -121.936, "type": "junction"},
    "J3": {"lat": 37.348, "lon": -121.933, "type": "junction"},
    "J4": {"lat": 37.35, "lon": -121.931, "type": "junction"},
    "J5": {"lat": 37.347, "lon": -121.929, "type": "junction"},
}


class DashboardService:
    """Produces aggregated views for the operator dashboard."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.energy_service = EnergyService(session)

    def summary(self) -> dict[str, Any]:
        leak_snapshot = self._latest_leak_detection()
        energy_snapshot = self._energy_snapshot()
        pressure_avg = self._metric_avg("pressure_kpa")
        demand_avg = self._metric_avg("demand_lps")
        alerts_open = self._alerts_open(leak_snapshot, energy_snapshot)

        kpis = [
            {
                "name": "False Alarm Rate",
                "value": round(
                    (1 - (leak_snapshot["probability"] if leak_snapshot else 0.0)) * 5, 2
                ),
                "unit": "%",
                "target": "≤ 5%",
                "trend": "down",
            },
            {
                "name": "Time to First Action",
                "value": energy_snapshot.get("time_to_first_action_minutes", 0.0) * 60
                if energy_snapshot
                else 60,
                "unit": "s",
                "target": "≤ 180 s",
                "trend": "steady",
            },
            {
                "name": "Avg Pressure",
                "value": round(pressure_avg or 0.0, 1),
                "unit": "kPa",
                "target": "≥ 240",
                "trend": "steady",
            },
            {
                "name": "Avg Demand",
                "value": round(demand_avg or 0.0, 1),
                "unit": "L/s",
                "target": "balanced",
                "trend": "seasonal",
            },
        ]

        status = "nominal"
        if leak_snapshot and leak_snapshot.get("triggered"):
            status = "elevated"
        if energy_snapshot and energy_snapshot.get("pressure_guard_breaches", 0) > 0:
            status = "degraded"

        return {
            "status": status,
            "alerts_open": alerts_open,
            "kpis": kpis,
            "energy": energy_snapshot,
        }

    def alerts(self, limit: int = 10) -> list[dict[str, Any]]:
        leak_snapshot = self._latest_leak_detection()
        energy_snapshot = self._energy_snapshot()
        alerts: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        if leak_snapshot:
            prob = leak_snapshot["probability"]
            entity = leak_snapshot["entity_id"]
            alerts.append(
                {
                    "id": "alert-leak",
                    "type": "leak",
                    "severity": "high" if prob >= 0.6 else "medium",
                    "status": "active" if leak_snapshot["triggered"] else "watch",
                    "message": f"Leak probability {prob:.2f} for {entity}",
                    "timestamp": leak_snapshot["timestamp"],
                    "metadata": leak_snapshot["reasons"],
                },
            )

        if energy_snapshot:
            savings = energy_snapshot["expected_savings_pct"]
            guardrails = energy_snapshot["pressure_guard_breaches"]
            alerts.append(
                {
                    "id": "alert-energy",
                    "type": "energy",
                    "severity": "medium" if savings < 15 else "low",
                    "status": "active",
                    "message": f"Energy savings {savings:.1f}% with {guardrails} guardrail hits",
                    "timestamp": energy_snapshot.get("issued_at", now.isoformat()),
                    "metadata": {
                        "baseline_cost_usd": energy_snapshot.get("baseline_cost_usd"),
                        "optimized_cost_usd": energy_snapshot.get("optimized_cost_usd"),
                    },
                },
            )

        iso_status = self._isolation_status()
        if iso_status:
            alerts.append(iso_status)

        return alerts[:limit]

    def map_state(self) -> dict[str, Any]:
        leak_snapshot = self._latest_leak_detection()
        pressure_map = self._latest_metric_map("pressure_kpa")
        graph = WaterNetworkGraph.sample()
        now = datetime.now(timezone.utc)

        nodes = []
        hot_entity = leak_snapshot["entity_id"] if leak_snapshot else None
        for node_id, meta in NODE_LAYOUT.items():
            pressure = pressure_map.get(node_id)
            status = "alert" if hot_entity == node_id else "normal"
            if hot_entity and node_id != hot_entity and node_id.startswith("J"):
                status = "watch"
            nodes.append(
                {
                    "id": node_id,
                    "label": node_id,
                    "lat": meta["lat"],
                    "lon": meta["lon"],
                    "type": meta["type"],
                    "status": status,
                    "pressure_kpa": round(pressure, 2) if pressure else None,
                },
            )

        pipes = []
        for valve in graph.valves.values():
            pipes.append(
                {
                    "id": valve.id,
                    "from": valve.connects[0],
                    "to": valve.connects[1],
                    "customers_affected": valve.customers_affected,
                    "loss_rate_lps": valve.loss_rate_lps,
                    "status": "alert" if hot_entity in valve.connects else "normal",
                },
            )

        return {
            "last_updated": now.isoformat(),
            "nodes": nodes,
            "pipes": pipes,
        }

    def scenarios(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        return [
            {
                "id": "scenario-leak",
                "title": "Burst near J2",
                "description": "Run leak detection → isolation plan → operator approval",
                "steps": [
                    "Replay leak telemetry",
                    "Highlight valves V_J2_J3 & V_J2_J5",
                    "Request Alex approval",
                ],
                "recommended_actions": ["/leaks/analyze", "/isolation/plan", "/isolation/execute"],
                "last_ran": now.isoformat(),
            },
            {
                "id": "scenario-tariff",
                "title": "High tariff spike",
                "description": "Shift pumping to low-tariff window while respecting pressure",
                "steps": [
                    "Fetch tariff curve",
                    "Run /energy/optimize",
                    "Send plan to Alex",
                ],
                "recommended_actions": ["/energy/forecast", "/energy/optimize"],
                "last_ran": (now - timedelta(hours=4)).isoformat(),
            },
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _latest_leak_detection(self) -> dict[str, Any] | None:
        records = (
            self.session.query(TelemetryRecord)
            .filter(TelemetryRecord.metric.in_(["pressure_kpa", "demand_lps", "flow_lps"]))
            .order_by(TelemetryRecord.timestamp.desc())
            .limit(540)
            .all()
        )
        if len(records) < 60:
            return None
        events = records_to_events(records)
        config = LeakDetectorConfig(
            baseline_window=max(30, min(60, len(events) // 2)),
            minimum_support=min(120, len(events)),
        )
        detector = LeakDetector(config)
        try:
            detector.fit_baseline(events)
            results = detector.detect(events)
        except (ValueError, IndexError):
            return None
        latest = results[-1]
        snapshot = leak_result_to_dict(latest)
        return snapshot

    def _energy_snapshot(self) -> dict[str, Any] | None:
        try:
            report = self.energy_service.optimize_energy(horizon_hours=6)
        except ValueError:
            return None
        schedule = report.schedule
        return {
            "issued_at": report.issued_at.isoformat(),
            "baseline_cost_usd": schedule.baseline_cost_usd,
            "optimized_cost_usd": schedule.optimized_cost_usd,
            "expected_savings_pct": schedule.savings_pct,
            "pressure_guard_breaches": schedule.pressure_guard_breaches,
            "time_to_first_action_minutes": report.time_to_first_action_minutes,
        }

    def _metric_avg(self, metric: str) -> float | None:
        value = (
            self.session.query(func.avg(TelemetryRecord.value))
            .filter(TelemetryRecord.metric == metric)
            .scalar()
        )
        return float(value) if value is not None else None

    def _latest_metric_map(self, metric: str) -> dict[str, float]:
        rows = (
            self.session.query(TelemetryRecord.entity_id, TelemetryRecord.value)
            .filter(TelemetryRecord.metric == metric)
            .order_by(TelemetryRecord.timestamp.desc())
            .limit(200)
            .all()
        )
        mapping: dict[str, float] = {}
        for entity_id, value in rows:
            if entity_id not in mapping:
                mapping[entity_id] = float(value)
        return mapping

    def _alerts_open(
        self,
        leak_snapshot: dict[str, Any] | None,
        energy_snapshot: dict[str, Any] | None,
    ) -> int:
        count = 0
        if leak_snapshot and leak_snapshot.get("triggered"):
            count += 1
        if energy_snapshot and energy_snapshot.get("expected_savings_pct", 0.0) < 12:
            count += 1
        last_action = (
            self.session.query(IsolationAction).order_by(IsolationAction.timestamp.desc()).first()
        )
        if (
            last_action
            and (datetime.now(timezone.utc) - last_action.timestamp).total_seconds() < 7200
        ):
            count += 1
        return count

    def _isolation_status(self) -> dict[str, Any] | None:
        last_action = (
            self.session.query(IsolationAction).order_by(IsolationAction.timestamp.desc()).first()
        )
        if not last_action:
            return None
        status = "active" if last_action.action == "close" else "resolved"
        return {
            "id": "alert-isolation",
            "type": "isolation",
            "severity": "medium",
            "status": status,
            "message": f"Valve {last_action.valve_id} {last_action.action}d",
            "timestamp": last_action.timestamp.isoformat(),
            "metadata": {
                "leak_pipe_id": last_action.leak_pipe_id,
                "performed_by": last_action.performed_by,
            },
        }
