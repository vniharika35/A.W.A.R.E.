"""CLI helper to run the multi-agent orchestrator demo."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .orchestrator import run_episode


def main() -> None:
    default_policy = Path("aware/infra/policies/phase-06-policy.yaml")
    env_policy = os.getenv("AGENT_POLICY")
    policy_path: Path | None = None
    if env_policy:
        candidate = Path(env_policy)
        policy_path = candidate if candidate.exists() else None
    elif default_policy.exists():
        policy_path = default_policy

    chaos_env = os.getenv("WATCHER_CHAOS_CHANCE")
    chaos_override = float(chaos_env) if chaos_env else None

    events = run_episode(
        policy_path=str(policy_path) if policy_path else None,
        chaos_override=chaos_override,
    )
    print(json.dumps([event.__dict__ for event in events], default=str, indent=2))


if __name__ == "__main__":
    main()
