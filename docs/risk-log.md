# Risk Log — Phase 0 Baseline

| ID | Risk | Probability | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| R-001 | Synthetic data may not capture real-world noise patterns, reducing model generalizability. | Medium | High | Incorporate domain expert review, inject realistic noise, and validate with public benchmark datasets where available. |
| R-002 | Hardware limits (≤ 4 CPU, ≤ 8 GB RAM) could constrain simulation fidelity and CI runtime. | Medium | Medium | Keep the EPANET model small, use deterministic seeds, and enable configurable sampling rates. |
| R-003 | Confidence calibration might drift without continuous monitoring. | Medium | High | Implement calibration checks in CI, log ECE/Brier metrics, and schedule periodic recalibration tasks. |
| R-004 | Autonomous valve sequencing could cause service disruption if guardrails fail. | Low | High | Require simulation-before-execution, Watcher agent overrides, and instant rollback workflows. |
| R-005 | Documentation or evidence gaps may block phase acceptance gates. | Medium | Medium | Automate doc generation (MkDocs), enforce PR checklist, and store evidence artifacts alongside phase reports. |
| R-006 | WNTR simulation drift or solver instability could break deterministic replays. | Low | Medium | Pin WNTR version, seed random inputs, and persist golden replay CSVs for regression comparison. |
| R-007 | Rule-based leak detector may overfit synthetic scenarios leading to false positives on real data. | Medium | High | Backtest against diverse synthetic leaks, calibrate thresholds with replay evidence, and plan ML upgrade in later phases. |
| R-008 | Manual approval could delay isolation beyond KPI targets if Alex is unavailable. | Medium | Medium | Provide escalation alerts, enable delegated approvals, and revisit auto-execution once trust metrics exceed targets. |
| R-009 | Forecast + tariff models may diverge from live SCADA, reducing energy-savings accuracy. | Medium | High | Validate forecasts against field data, add drift monitors, and allow operator overrides on `/energy/optimize`. |
