"""Telemetry primitives shared between the simulator and ingestion API."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
from typing import Iterator
from typing import Sequence


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    """Represents a single telemetry observation emitted by the digital twin."""

    timestamp: datetime
    entity_type: str
    entity_id: str
    metric: str
    value: float
    unit: str
    source: str = "simulator"
    quality: float = 1.0

    def asdict(self) -> dict[str, object]:
        """Convert the event to a dictionary suitable for JSON serialization."""
        return asdict(self)


def to_serializable(events: Sequence[TelemetryEvent]) -> list[dict[str, object]]:
    """Convert a sequence of telemetry events into JSON-serializable dictionaries."""
    return [event.asdict() for event in events]


def iter_serialized(events: Iterable[TelemetryEvent]) -> Iterator[dict[str, object]]:
    """Iterate over serialized telemetry events lazily."""
    for event in events:
        yield event.asdict()
