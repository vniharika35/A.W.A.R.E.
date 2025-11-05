"""Utility for loading or synthesizing day-ahead tariff curves."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import SimulationConfig


def load_tariff_curve(path: Path, config: SimulationConfig) -> pd.Series:
    """Load a tariff curve from CSV or synthesize one if unavailable."""

    if path.exists():
        frame = pd.read_csv(path, parse_dates=["timestamp"], dtype={"price_mwh": float})
    else:
        frame = _synthesize_tariff(config)

    frame = frame.sort_values("timestamp").reset_index(drop=True)
    base_timestamp = frame.loc[0, "timestamp"]
    frame["offset_seconds"] = (frame["timestamp"] - base_timestamp).dt.total_seconds()

    series = pd.Series(
        data=frame["price_mwh"].to_numpy(),
        index=pd.to_timedelta(frame["offset_seconds"], unit="s"),
        name="price_mwh",
    )

    desired_index = pd.timedelta_range(
        start=0,
        periods=config.steps() + 1,
        freq=f"{config.cadence_seconds}S",
    )
    aligned = series.reindex(desired_index, method="ffill")
    aligned.index.name = "offset"
    return aligned


def _synthesize_tariff(config: SimulationConfig) -> pd.DataFrame:
    """Generate a deterministic synthetic tariff curve."""

    periods = max(config.steps() // 30, 24)
    start = config.start_timestamp
    timestamps = pd.date_range(start=start, periods=periods, freq="1H", tz=start.tzinfo)

    base_price = 55.0
    amplitude = 15.0
    noise = np.zeros_like(np.arange(periods), dtype=float)
    values = base_price + amplitude * np.sin(np.linspace(0, 2 * np.pi, periods)) + noise

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "price_mwh": np.round(values, 2),
        }
    )
