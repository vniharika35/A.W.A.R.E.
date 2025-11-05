from __future__ import annotations

from aware.sim.config import SimulationConfig
from aware.sim.replay import TelemetryReplay
from aware.sim.simulator import DigitalTwinSimulator


def test_replay_round_trip(tmp_path) -> None:
    config = SimulationConfig(duration_seconds=60, cadence_seconds=2)
    events = list(DigitalTwinSimulator(config).iter_events())

    replay = TelemetryReplay.from_events(events)
    path = tmp_path / "replay.csv"
    replay.to_csv(path)

    loaded = TelemetryReplay.from_csv(path)
    replayed = list(loaded.iter_events())

    assert events == replayed
