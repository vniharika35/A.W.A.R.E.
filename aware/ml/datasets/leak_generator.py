"""Utilities for synthesising leak-labelled telemetry datasets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Sequence

import pandas as pd

from aware.sim.config import SimulationConfig
from aware.sim.simulator import DigitalTwinSimulator
from aware.sim.telemetry import TelemetryEvent


@dataclass(frozen=True, slots=True)
class LeakScenario:
    pipe_id: str
    start_offset: timedelta
    severity: float  # percentage increase in flow/demand [0, 1]
    duration: timedelta = timedelta(minutes=5)


@dataclass(frozen=True, slots=True)
class LabelledTelemetry:
    events: list[TelemetryEvent]
    labels: pd.DataFrame


def generate_leak_dataset(
    scenarios: Sequence[LeakScenario],
    config: SimulationConfig | None = None,
) -> LabelledTelemetry:
    config = config or SimulationConfig()
    simulator = DigitalTwinSimulator(config)
    base_events = list(simulator.iter_events())
    frame = pd.DataFrame(event.asdict() for event in base_events)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)

    labels = pd.DataFrame(
        0,
        index=sorted(frame["timestamp"].unique()),
        columns=[scenario.pipe_id for scenario in scenarios],
        dtype=int,
    )

    for scenario in scenarios:
        start = config.start_timestamp + scenario.start_offset
        end = start + scenario.duration
        mask = (frame["timestamp"] >= start) & (frame["timestamp"] <= end)
        pipe_mask = (frame["entity_type"] == "pipe") & (frame["entity_id"] == scenario.pipe_id)
        demand_mask = frame["metric"].isin(["flow_lps", "demand_lps"])
        indexes = frame[mask & pipe_mask & demand_mask].index
        frame.loc[indexes, "value"] *= 1.0 + scenario.severity
        labels.loc[(labels.index >= start) & (labels.index <= end), scenario.pipe_id] = 1

    mutated_events = [TelemetryEvent(**row) for row in frame.to_dict(orient="records")]
    return LabelledTelemetry(events=mutated_events, labels=labels)


def export_dataset(dataset: LabelledTelemetry, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    events_path = directory / "telemetry.csv"
    labels_path = directory / "labels.csv"
    events = pd.DataFrame(event.asdict() for event in dataset.events)
    events.to_csv(events_path, index=False)
    dataset.labels.to_csv(labels_path)
