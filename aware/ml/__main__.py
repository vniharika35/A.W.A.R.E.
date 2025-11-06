"""CLI utilities for leak detection experiments."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from aware.ml.detectors import LeakDetector
from aware.ml.detectors import LeakDetectorConfig
from aware.sim.telemetry import TelemetryEvent


def main() -> None:
    parser = argparse.ArgumentParser(description="Run leak detection on a telemetry CSV")
    parser.add_argument("telemetry", type=Path, help="Path to telemetry CSV")
    parser.add_argument("--baseline-window", type=int, default=60, help="Baseline window length")
    parser.add_argument("--output", type=Path, help="Optional path to write detection results")
    args = parser.parse_args()

    frame = pd.read_csv(args.telemetry, parse_dates=["timestamp"])
    events = [TelemetryEvent(**row) for row in frame.to_dict(orient="records")]

    detector = LeakDetector(LeakDetectorConfig(baseline_window=args.baseline_window))
    detector.fit_baseline(events)
    results = detector.detect(events)

    records = []
    for result in results:
        reasons_str = "; ".join(f"{reason.metric}:{reason.score:.2f}" for reason in result.reasons)
        records.append(
            {
                "timestamp": result.timestamp.isoformat(),
                "probability": result.probability,
                "triggered": result.triggered,
                "reasons": reasons_str,
            }
        )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(records).to_csv(args.output, index=False)
    else:
        for record in records[-10:]:
            print(
                f"{record['timestamp']} | prob={record['probability']:.2f} | "
                f"triggered={record['triggered']} | reasons={record['reasons']}"
            )


if __name__ == "__main__":
    main()
