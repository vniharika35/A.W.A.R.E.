# Risk Log — Phase 0 Baseline

| ID | Risk | Probability | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| R-001 | Synthetic data may not capture real-world noise patterns, reducing model generalizability. | Medium | High | Incorporate domain expert review, inject realistic noise, and validate with public benchmark datasets where available. |
| R-002 | Hardware limits (≤ 4 CPU, ≤ 8 GB RAM) could constrain simulation fidelity and CI runtime. | Medium | Medium | Keep the EPANET model small, use deterministic seeds, and enable configurable sampling rates. |
| R-003 | Confidence calibration might drift without continuous monitoring. | Medium | High | Implement calibration checks in CI, log ECE/Brier metrics, and schedule periodic recalibration tasks. |
| R-004 | Autonomous valve sequencing could cause service disruption if guardrails fail. | Low | High | Require simulation-before-execution, Watcher agent overrides, and instant rollback workflows. |
| R-005 | Documentation or evidence gaps may block phase acceptance gates. | Medium | Medium | Automate doc generation (MkDocs), enforce PR checklist, and store evidence artifacts alongside phase reports. |
| R-006 | WNTR simulation drift or solver instability could break deterministic replays. | Low | Medium | Pin WNTR version, seed random inputs, and persist golden replay CSVs for regression comparison. |
