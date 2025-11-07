"""YAML-driven policy loader for the multi-agent orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


DEFAULT_POLICY: dict[str, Any] = {
    "agents": {
        "leak_detect": {"trigger_threshold": 0.6},
        "planner": {"max_hops": 3, "max_radius_m": 500},
        "energy_opt": {"min_savings_pct": 12.0},
        "actuator": {"require_approval": True, "auto_execute": False},
        "watcher": {"chaos_chance": 0.05, "safe_mode_on_failure": True, "max_radius_m": 600},
    }
}


def load_policy(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return DEFAULT_POLICY
    policy_path = Path(path)
    if not policy_path.exists():
        raise FileNotFoundError(f"Policy file not found: {policy_path}")
    with policy_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    merged_agents: dict[str, Any] = {}
    input_agents = data.get("agents", {})
    for agent_name, defaults in DEFAULT_POLICY["agents"].items():
        overrides = input_agents.get(agent_name, {})
        merged_agents[agent_name] = {**defaults, **overrides}
    return {"agents": merged_agents}
