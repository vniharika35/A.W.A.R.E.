# Phase 02 — Leak Detection

## Goal & Scope
- Deliver a rule-based, multi-sensor leak detector that fuses pressure, demand, and flow signals.
- Provide calibrated probabilities, “why-now” explanations, and baseline management for Alex.
- Generate synthetic leak-labelled telemetry that covers multiple pipes, severities, and start times for Jordan’s KPI tracking.

## Design Decisions (trade-offs, risks)
- **Rule-first approach:** Implement Z-score + CUSUM detector to ensure transparency and fast tuning while leaving space for ML upgrades in later phases.
- **Calibration:** Use logistic-style scaling tied to trigger thresholds so probabilities map cleanly to operator expectations (≥0.5 ⇒ action).
- **Synthetic leaks:** Modify simulator outputs in-memory instead of rerunning heavy hydraulics to keep within CPU/RAM limits.
- **Explainability:** Surface top contributing metrics (pressure, flow, demand) with z-scores to support Alex’s review requirements.

## Implementation Notes (modules, schemas, configs)
- `aware/ml/detectors/rule_based.py` — leak detector, dataclasses, cumulative scoring, calibration, and explanation scaffolding.
- `aware/ml/datasets/leak_generator.py` — helper to inject leak scenarios and export labelled datasets.
- `aware/ml/__main__.py` — CLI to run detection against any telemetry CSV (backed by `make leak-detect`).
- `aware/backend/app.py` — new `/leaks/analyze` endpoint returning probabilities, triggers, and reasons based on recent telemetry.
- Tests cover synthetic event generation, detector stability, and API responses (`aware/tests/test_leak_detection.py`, `aware/tests/test_ingestion_api.py`).

```mermaid
graph TD
  Telemetry[Telemetry Events] -->|Pressure/Flow/Demand| FeaturePrep[Feature Extraction]
  FeaturePrep --> ZScore[Z-Score + CUSUM]
  ZScore --> Calibration[Logistic Calibration]
  Calibration --> Alerts[Leak Alerts + Reasons]
  Alerts --> API[/leaks/analyze]
```

## Results (target vs actual metrics, screenshots/GIFs)
- Leak test scenario triggered probability **0.83** within 30 s of leak onset; false positives remained < 0.5 in baseline run.
- `/leaks/analyze` returns latest probability, trigger flag, and top reasons with z-scores (pressure drop & flow increase).
- CLI sample (`make leak-detect`) prints calibrated probabilities for bundled telemetry.

## Tests (what ran, coverage %, pass/fail)
- `pytest aware/tests/test_leak_detection.py` — deterministic fusion & baseline guard ✔️
- `pytest aware/tests/test_ingestion_api.py::test_leak_analysis_endpoint` — API round-trip with injected leak ✔️
- Existing simulator + ingestion suites continue to pass locally (`make test`).

## Acceptance Checklist (all criteria met)
- [x] Leak detector produces calibrated probabilities with explainability.
- [x] Synthetic leak dataset generation supports multiple pipes, severities, and start offsets.
- [x] Online `/leaks/analyze` endpoint surfaces latest alert context for Alex.
- [x] Tests cover detector baseline, leak triggering, and API integration.

## Next Steps (follow-ups, debt)
1. Introduce ML-based detectors (IsolationForest/XGBoost) alongside rule-based baseline for ensemble comparisons.
2. Store calibration metrics (ECE/Brier) per run to chart drift across replays.
3. Extend synthetic scenarios to include sensor dropout cases before Phase 6 guardrails.
