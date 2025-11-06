from __future__ import annotations

from datetime import timedelta

import pandas as pd
import pytest

from aware.sim.config import SimulationConfig
from aware.sim.simulator import DigitalTwinSimulator


def _assert_events_close(first, second) -> None:
    assert first.timestamp == second.timestamp
    assert first.entity_type == second.entity_type
    assert first.entity_id == second.entity_id
    assert first.metric == second.metric
    assert first.unit == second.unit
    assert first.source == second.source
    assert first.quality == pytest.approx(second.quality, rel=1e-6, abs=1e-9)
    assert first.value == pytest.approx(second.value, rel=1e-6, abs=1e-9)


def test_simulator_emits_deterministic_events() -> None:
    config = SimulationConfig(duration_seconds=120, cadence_seconds=2)
    simulator = DigitalTwinSimulator(config)

    events_first = list(simulator.iter_events())
    events_second = list(DigitalTwinSimulator(config).iter_events())

    assert len(events_first) > 0
    assert len(events_first) == len(events_second)
    for event_a, event_b in zip(events_first, events_second, strict=False):
        _assert_events_close(event_a, event_b)

    timestamps = [event.timestamp for event in events_first]
    assert min(timestamps) == config.start_timestamp
    assert max(timestamps) - min(timestamps) >= timedelta(seconds=config.duration_seconds)


def test_simulation_result_shapes() -> None:
    config = SimulationConfig(duration_seconds=60, cadence_seconds=2)
    result = DigitalTwinSimulator(config).run()

    expected_steps = config.steps() + 1
    assert isinstance(result.pressure, pd.DataFrame)
    assert result.pressure.shape[0] == expected_steps
    assert result.demand.shape[0] == expected_steps
    assert result.flow.shape[0] == expected_steps
    assert result.tank_level.shape[0] == expected_steps
