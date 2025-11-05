"""Simulation configuration primitives for the A.W.A.R.E. digital twin."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Optional


DEFAULT_TARIFF_PATH = Path(__file__).resolve().parent / "assets" / "tariff_day_ahead.csv"


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Container for digital twin simulation parameters."""

    cadence_seconds: int = 2
    duration_seconds: int = 600
    start_timestamp: datetime = datetime(2025, 1, 1, tzinfo=timezone.utc)
    random_seed: int = 42
    tariff_path: Path = DEFAULT_TARIFF_PATH
    replay_output: Optional[Path] = None

    def steps(self) -> int:
        """Return the number of simulation steps."""
        return int(self.duration_seconds / self.cadence_seconds)
