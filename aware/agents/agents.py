"""Agent definitions participating in the orchestration loop."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any
from typing import Sequence

from aware.backend.isolation import IsolationPlanner
from aware.backend.isolation import IsolationPlannerConfig
from aware.backend.isolation import IsolationPolicy
from aware.backend.isolation.network import WaterNetworkGraph

from .bus import AgentEvent
from .bus import EventBus


@dataclass(slots=True)
class Agent:
    name: str
    bus: EventBus
    policy: dict[str, Any]

    def __post_init__(self) -> None:
        for event_type in self.subscriptions():
            self.bus.subscribe(event_type, self._handle_event)

    def subscriptions(self) -> Sequence[str]:
        return ()

    def _handle_event(self, event: AgentEvent) -> None:
        self.handle(event)

    def handle(self, event: AgentEvent) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        self.bus.publish(AgentEvent(type=event_type, payload=payload, source=self.name))


class LeakDetectAgent(Agent):
    """Consumes telemetry windows and emits leak alerts with explainability."""

    def subscriptions(self) -> Sequence[str]:
        return ("telemetry.window",)

    def handle(self, event: AgentEvent) -> None:
        window = event.payload
        pressure_drop = float(window.get("pressure_drop_kpa", 0.0))
        flow_delta = float(window.get("flow_delta_lps", 0.0))
        demand_delta = float(window.get("demand_delta_lps", 0.0))
        score = 0.45 * pressure_drop + 0.35 * flow_delta + 0.2 * demand_delta
        probability = max(0.01, min(0.99, score / 10))
        threshold = float(self.policy.get("trigger_threshold", 0.6))
        triggered = probability >= threshold
        self.emit(
            "alert.leak",
            {
                "probability": round(probability, 3),
                "triggered": triggered,
                "entity_id": window.get("entity_id", "zone-1"),
                "reasons": [
                    {"metric": "pressure", "details": f"Δ {pressure_drop:.2f} kPa"},
                    {"metric": "flow", "details": f"Δ {flow_delta:.2f} L/s"},
                    {"metric": "demand", "details": f"Δ {demand_delta:.2f} L/s"},
                ],
            },
        )


class PlannerAgent(Agent):
    """Requests isolation plans for confirmed leak alerts."""

    def __post_init__(self) -> None:
        graph = WaterNetworkGraph.sample()
        planner_config = IsolationPlannerConfig(
            policy=IsolationPolicy.MINIMIZE_CUSTOMERS,
            max_hops=self.policy.get("max_hops", 3),
            max_radius_meters=self.policy.get("max_radius_m", 500.0),
        )
        self._planner = IsolationPlanner(graph=graph, config=planner_config)
        super().__post_init__()

    def subscriptions(self) -> Sequence[str]:
        return ("alert.leak",)

    def handle(self, event: AgentEvent) -> None:
        if not event.payload.get("triggered"):
            return
        leak_pipe = event.payload.get("pipe_id", "P_J2_J3")
        plan = self._planner.plan(leak_pipe_id=leak_pipe, start_node="J2", end_node="J3")
        self.emit(
            "plan.isolation",
            {
                "leak_pipe_id": plan.leak_pipe_id,
                "steps": [
                    {
                        "valve_id": step.valve_id,
                        "customers": step.customers_affected,
                        "loss_rate_lps": step.loss_rate_lps,
                    }
                    for step in plan.steps
                ],
                "radius_m": self.policy.get("max_radius_m", 500.0),
            },
        )


class EnergyOptAgent(Agent):
    """Responds to alerts by proposing energy savings plans."""

    def subscriptions(self) -> Sequence[str]:
        return ("alert.leak",)

    def handle(self, event: AgentEvent) -> None:
        min_savings = float(self.policy.get("min_savings_pct", 12.0))
        probability = float(event.payload.get("probability", 0.0))
        savings = max(min_savings, round(probability * 20, 2))
        plan = {
            "savings_pct": savings,
            "pressure_guard": 0,
            "notes": "Shift pumping to low-tariff hours",
        }
        self.emit("energy.plan", plan)


class ActuatorAgent(Agent):
    """Decides whether to auto-execute isolation plans."""

    def subscriptions(self) -> Sequence[str]:
        return ("plan.isolation",)

    def handle(self, event: AgentEvent) -> None:
        require_approval = bool(self.policy.get("require_approval", True))
        auto_execute = bool(self.policy.get("auto_execute", False))
        if require_approval or not auto_execute:
            self.emit(
                "actuation.pending",
                {
                    "reason": "approval-required",
                    "leak_pipe_id": event.payload.get("leak_pipe_id"),
                },
            )
        else:
            self.emit(
                "actuation.approved",
                {
                    "leak_pipe_id": event.payload.get("leak_pipe_id"),
                    "valves": [step["valve_id"] for step in event.payload.get("steps", [])],
                },
            )


class WatcherAgent(Agent):
    """Monitors the bus, injects chaos, and enforces safe degradation."""

    def __init__(
        self,
        name: str,
        bus: EventBus,
        policy: dict[str, Any],
        *,
        rng: Random | None = None,
    ) -> None:
        self._rng = rng or Random(int(policy.get("chaos_seed", 42)))
        self._safe_mode = False
        super().__init__(name, bus, policy)

    def subscriptions(self) -> Sequence[str]:
        return ("*",)

    def handle(self, event: AgentEvent) -> None:
        max_radius = self.policy.get("max_radius_m", 600)
        if event.type == "plan.isolation" and event.payload.get("radius_m", 0) > max_radius:
            self._trigger_safe_mode("radius-breach")
        chaos_chance = self.policy.get("chaos_chance", 0.0)
        if event.type == "actuation.approved" and self._rng.random() < chaos_chance:
            self.emit(
                "chaos.injected",
                {
                    "reason": "simulated actuator fault",
                    "original_event": event.payload,
                },
            )
            if self.policy.get("safe_mode_on_failure", True):
                self._trigger_safe_mode("chaos")
        if event.type == "system.mode" and event.payload.get("mode") == "safe":
            self._safe_mode = True

    def _trigger_safe_mode(self, reason: str) -> None:
        if self._safe_mode:
            return
        self.emit(
            "system.mode",
            {
                "mode": "safe",
                "reason": reason,
            },
        )
        self._safe_mode = True
