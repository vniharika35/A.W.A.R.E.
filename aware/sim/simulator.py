"""Digital twin simulator producing deterministic telemetry events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd
import wntr

from .config import SimulationConfig
from .network import build_demo_network
from .tariff_loader import load_tariff_curve
from .telemetry import TelemetryEvent


@dataclass(slots=True)
class SimulationResult:
    """Container holding generated telemetry data frames."""

    pressure: pd.DataFrame
    demand: pd.DataFrame
    flow: pd.DataFrame
    tank_level: pd.DataFrame
    tariff: pd.Series

    def to_events(self, config: SimulationConfig) -> list[TelemetryEvent]:
        """Convert the simulation result to normalized telemetry events."""
        events: list[TelemetryEvent] = []
        base_ts = config.start_timestamp

        def _append_frame(df: pd.DataFrame, entity_type: str, metric: str, unit: str) -> None:
            for timedelta_index, row in df.iterrows():
                ts = base_ts + _timedelta_from_index(timedelta_index)
                for entity_id, value in row.items():
                    events.append(
                        TelemetryEvent(
                            timestamp=ts,
                            entity_type=entity_type,
                            entity_id=entity_id,
                            metric=metric,
                            value=float(value),
                            unit=unit,
                        ),
                    )

        _append_frame(self.pressure, "junction", "pressure_kpa", "kPa")
        _append_frame(self.demand, "junction", "demand_lps", "L/s")
        _append_frame(self.flow, "pipe", "flow_lps", "L/s")
        _append_frame(self.tank_level, "tank", "level_m", "m")

        for timedelta_index, price in self.tariff.items():
            ts = base_ts + _timedelta_from_index(timedelta_index)
            events.append(
                TelemetryEvent(
                    timestamp=ts,
                    entity_type="tariff",
                    entity_id="day_ahead",
                    metric="price_per_mwh",
                    value=float(price),
                    unit="USD/MWh",
                ),
            )

        return sorted(events, key=lambda event: event.timestamp)


class DigitalTwinSimulator:
    """Runs hydraulic simulation and emits telemetry events."""

    def __init__(self, config: SimulationConfig | None = None) -> None:
        self.config = config or SimulationConfig()

    def run(self) -> SimulationResult:
        """Execute the hydraulic simulator and return data frames."""
        config = self.config
        np.random.seed(config.random_seed)

        wn = build_demo_network(config)
        tariff_series = load_tariff_curve(config.tariff_path, config)

        # Use the WNTR simulator for deterministic runs
        simulator = wntr.sim.WNTRSimulator(wn)
        results = simulator.run_sim()

        pressure = results.node["pressure"][wn.junction_name_list]
        demand = results.node["demand"][wn.junction_name_list]
        flow = results.link["flowrate"][wn.pipe_name_list]

        tank_head = results.node["head"][wn.tank_name_list]
        tank_level = tank_head.copy()
        for tank_name in wn.tank_name_list:
            elevation = wn.get_node(tank_name).elevation
            tank_level[tank_name] = tank_level[tank_name] - elevation

        return SimulationResult(
            pressure=pressure,
            demand=demand,
            flow=flow,
            tank_level=tank_level,
            tariff=tariff_series,
        )

    def iter_events(self) -> Iterator[TelemetryEvent]:
        """Iterate over telemetry events suitable for ingestion."""
        result = self.run()
        events = result.to_events(self.config)
        for event in events:
            yield event

    def save_replay(self, path: Path) -> Path:
        """Persist a deterministic replay CSV for later use."""
        events = list(self.iter_events())
        data = pd.DataFrame([event.asdict() for event in events])
        path.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(path, index=False)
        return path


def _timedelta_from_index(idx: pd.Index | timedelta | float | int) -> timedelta:
    if isinstance(idx, pd.Index):
        # Use the first value if an index is passed
        idx = idx[0]
    if isinstance(idx, pd.Timedelta):
        return idx.to_pytimedelta()
    if isinstance(idx, timedelta):
        return idx
    # EPANET results use seconds as floats
    return timedelta(seconds=float(idx))
