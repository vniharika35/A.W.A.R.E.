# A.W.A.R.E.

Agent for Water Autonomy, Resilience, and Efficiency couples a municipal water
digital twin with a multi-agent decision system. We detect leaks before they
burst, orchestrate safe valve isolation, and optimize pump energy consumption
under strict safety guardrails.

## Personas We Serve
- **Alex (Control Room Operator):** trusts high-confidence, explainable alerts and can
  approve or auto-execute mitigation steps within minutes.
- **Maya (Field Technician):** receives walk-through valve sequences on mobile, with
  clear rollback steps and safety checks.
- **Jordan (Asset Manager):** quantifies ROI via NRW, outage minutes, and energy spend
  reductions backed by audit-ready reports.

## Key Metrics
Leading indicators: false-alarm rate ≤ 5%, time-to-first-action ≤ 3 minutes,
confidence calibration error ≤ 10%.

Lagging indicators: NRW reduction ≥ 15%, outage minutes reduction ≥ 30%, energy
cost per MGal reduction ≥ 15% (synthetic proxy during MVP).

## Phase Roadmap
1. **Phase 0 — Kickoff:** Align on scope, personas, and success metrics; bootstrap
   the repo, CI, and documentation.
2. **Phase 1 — Digital Twin & Telemetry:** Stand up EPANET-driven simulations and
   telemetry ingestion.
3. **Phase 2 — Leak Detection:** Deliver calibrated leak detection with
   explainability.
4. **Phase 3 — Isolation Sequencing & Actuation:** Plan and audit valve operations
   with safe rollbacks.
5. **Phase 4 — Energy Optimization:** Forecast demand and schedule pumps against
   tariffs.
6. **Phase 5 — Operator UX:** Provide real-time visualization, explainability, and
   scenario exploration.
7. **Phase 6 — Multi-Agent Orchestration:** Coordinate Planner, Leak-Detect,
   Energy-Opt, Actuator, and Watcher agents via policy guardrails.
8. **Phase 7 — Packaging & Demo:** Ship reproducible deployment, docs, and demo.

Team credits: **Team A.W.A.R.E — Niharika Verma, Dhruv Verma**.
