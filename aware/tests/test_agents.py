from __future__ import annotations

from aware.agents import load_policy
from aware.agents import run_episode


def test_run_episode_produces_plan() -> None:
    events = run_episode()
    types = [event.type for event in events]
    assert "telemetry.window" in types
    assert "alert.leak" in types
    assert "plan.isolation" in types
    assert "energy.plan" in types
    assert "actuation.pending" in types


def test_watcher_triggers_safe_mode(tmp_path) -> None:
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        """
agents:
  actuator:
    require_approval: false
    auto_execute: true
  watcher:
    chaos_chance: 0.0
    safe_mode_on_failure: true
"""
    )
    events = run_episode(policy_path=str(policy_path), chaos_override=1.0)
    types = [event.type for event in events]
    assert "actuation.approved" in types
    assert "chaos.injected" in types
    assert any(event.type == "system.mode" and event.payload["mode"] == "safe" for event in events)


def test_policy_loader_merges_defaults(tmp_path) -> None:
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        """
agents:
  watcher:
    chaos_chance: 0.2
"""
    )
    policy = load_policy(str(policy_path))
    assert policy["agents"]["watcher"]["chaos_chance"] == 0.2
    assert policy["agents"]["watcher"]["safe_mode_on_failure"] is True
