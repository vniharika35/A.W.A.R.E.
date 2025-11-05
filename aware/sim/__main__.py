"""Command line entrypoint for running the simulator."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import SimulationConfig
from .simulator import DigitalTwinSimulator


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the A.W.A.R.E. digital twin simulator")
    parser.add_argument("--duration", type=int, default=600, help="Simulation duration in seconds")
    parser.add_argument("--cadence", type=int, default=2, help="Telemetry cadence in seconds")
    parser.add_argument("--replay", type=Path, help="Optional path to store replay CSV")
    args = parser.parse_args()

    config = SimulationConfig(duration_seconds=args.duration, cadence_seconds=args.cadence)
    simulator = DigitalTwinSimulator(config)
    events = list(simulator.iter_events())

    if args.replay:
        simulator.save_replay(args.replay)
        print(f"Saved replay with {len(events)} events to {args.replay}")
    else:
        print(f"Generated {len(events)} telemetry events at {args.cadence}s cadence")


if __name__ == "__main__":
    main()
