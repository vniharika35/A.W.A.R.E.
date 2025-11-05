"""Deterministic replay utilities for simulator outputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from typing import Iterator

import pandas as pd

from .telemetry import TelemetryEvent


@dataclass(slots=True)
class TelemetryReplay:
    """Stores a telemetry capture and allows deterministic replays."""

    frame: pd.DataFrame

    @classmethod
    def from_events(cls, events: Iterable[TelemetryEvent]) -> "TelemetryReplay":
        return cls(pd.DataFrame(event.asdict() for event in events))

    @classmethod
    def from_csv(cls, path: Path) -> "TelemetryReplay":
        frame = pd.read_csv(path, parse_dates=["timestamp"])
        return cls(frame)

    def iter_events(self) -> Iterator[TelemetryEvent]:
        for row in self.frame.to_dict(orient="records"):
            yield TelemetryEvent(**row)

    def to_csv(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.frame.to_csv(path, index=False)
        return path
