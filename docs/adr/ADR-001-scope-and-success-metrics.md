# ADR-001 — Scope and Success Metrics

- **Status:** Accepted (Phase 0)
- **Date:** 2025-11-05
- **Context:** We must establish the MVP scope, KPIs, and constraints for the
  A.W.A.R.E. municipal water autonomy agent before development begins. Personas
  Alex, Maya, and Jordan define the operator, field, and asset management needs.

## Decision
We will build a small-scale digital twin (single pressure zone, ~10–20
pipes/nodes) with synthetic telemetry to support accelerated iteration while
respecting course hardware limits (≤ 4 CPU cores, ≤ 8 GB RAM, no GPU). The MVP
must include multi-sensor leak fusion, valve isolation sequencing, pump/tank
energy co-optimization, explainability, and full audit logging.

Success is gated by:
- False-alarm rate ≤ 5%
- Time-to-first-action ≤ 3 minutes
- Confidence calibration error ≤ 10%
- Synthetic proxy KPIs: NRW reduction ≥ 15%, outage minutes reduction ≥ 30%,
  energy cost per MGal reduction ≥ 15%

## Rationale
- Tight KPI targets drive trust for Alex (high-confidence alerts) and Jordan
  (quantifiable ROI) while empowering Maya with reliable playbooks.
- A constrained demo size keeps simulations and CI reproducible within student
  hardware limits.
- Synthetic data unlocks experimentation without waiting for real utility data
  while still enforcing realistic failure and tariff patterns.

## Implications
- All detection models require calibration layers and confidence reporting.
- Energy optimization must integrate day-ahead prices and guardrail constraints.
- Digital twin fidelity must be sufficient to recompute valve impacts and pump
  states quickly (< 3 minutes to first action).
- Documentation and audit logging remain first-class citizens for trust and
  compliance reviews.

## Alternatives Considered
- **Larger multi-zone twin:** rejected due to hardware and time constraints.
- **Rules-only leak detection:** rejected because explainable ML with
  calibration is required to meet trust targets and future-proof the system.
- **Manual operations:** rejected because personas demand proactive autonomy with
  fail-safes and rollback.
