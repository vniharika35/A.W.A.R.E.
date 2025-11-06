from __future__ import annotations

import pytest

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

    assert len(events) == len(replayed)
    for original, restored in zip(events, replayed, strict=False):
        assert original.timestamp == restored.timestamp
        assert original.entity_type == restored.entity_type
        assert original.entity_id == restored.entity_id
        assert original.metric == restored.metric
        assert original.unit == restored.unit
        assert original.source == restored.source
        assert original.quality == pytest.approx(restored.quality, rel=1e-6, abs=1e-9)
        assert original.value == pytest.approx(restored.value, rel=1e-6, abs=1e-9)
