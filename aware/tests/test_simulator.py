from __future__ import annotations

from datetime import timedelta

import pandas as pd

from aware.sim.config import SimulationConfig
from aware.sim.simulator import DigitalTwinSimulator


def test_simulator_emits_deterministic_events() -> None:
    config = SimulationConfig(duration_seconds=120, cadence_seconds=2)
    simulator = DigitalTwinSimulator(config)

    events_first = list(simulator.iter_events())
    events_second = list(DigitalTwinSimulator(config).iter_events())

    assert events_first == events_second
    assert len(events_first) > 0

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
