"""Utility to wire up agents and run a mini-episode for testing/demo."""

from __future__ import annotations

from typing import Any

from .agents import ActuatorAgent
from .agents import EnergyOptAgent
from .agents import LeakDetectAgent
from .agents import PlannerAgent
from .agents import WatcherAgent
from .bus import AgentEvent
from .bus import EventBus
from .policies import load_policy


def run_episode(
    *,
    policy_path: str | None = None,
    telemetry_window: dict[str, Any] | None = None,
    chaos_override: float | None = None,
) -> list[AgentEvent]:
    policy = load_policy(policy_path)
    if chaos_override is not None:
        policy["agents"].setdefault("watcher", {})["chaos_chance"] = chaos_override

    bus = EventBus()

    LeakDetectAgent("LeakDetect", bus, policy["agents"].get("leak_detect", {}))
    PlannerAgent("Planner", bus, policy["agents"].get("planner", {}))
    EnergyOptAgent("EnergyOpt", bus, policy["agents"].get("energy_opt", {}))
    ActuatorAgent("Actuator", bus, policy["agents"].get("actuator", {}))
    WatcherAgent("Watcher", bus, policy["agents"].get("watcher", {}))

    snapshot = telemetry_window or {
        "entity_id": "zone-1",
        "pressure_drop_kpa": 8.0,
        "flow_delta_lps": 7.0,
        "demand_delta_lps": 4.0,
    }
    bus.publish(AgentEvent(type="telemetry.window", payload=snapshot, source="orchestrator"))
    return list(bus.history())
