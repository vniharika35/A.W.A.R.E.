# A.W.A.R.E.

Agent for Water Autonomy, Resilience, and Efficiency — a proactive, self-healing decision system for municipal water utilities that couples a digital twin with multi-agent orchestration to anticipate failures, execute autonomous responses, and optimize energy use.

**Team A.W.A.R.E — Niharika Verma, Dhruv Verma**

## Mission & Personas
- **Alex (Control Room Operator):** receives few, high-confidence, explainable alerts ready for rapid approval or auto-execution.
- **Maya (Field Technician):** follows guided valve sequences on mobile for safe, auditable interventions.
- **Jordan (Asset Manager):** monitors NRW, outage minutes, and energy spend improvements with audit-ready reports.

Success metrics (Phase 0 commitments):
- False-alarm rate ≤ 5%
- Time-to-first-action ≤ 3 minutes
- Confidence calibration error ≤ 10%
- NRW ↓ ≥ 15%, outage minutes ↓ ≥ 30%, energy cost/MGal ↓ ≥ 15%

## Repository Layout
```
aware/
  backend/    # FastAPI services, background workers
  ml/         # Detection & forecasting models
  sim/        # Digital twin adapters (EPANET/wntr)
  web/        # React + Vite + Tailwind dashboard
  infra/      # IaC, deployment descriptors
  tests/      # Shared testing utilities & suites
  docs/       # MkDocs content & phase deliverables
```

Supporting assets sit at the repository root (CI/CD, configuration, documentation scaffolding).

## Getting Started (Phase 1)
1. Install prerequisites: Docker, Docker Compose, Python 3.11+, Node 18+, and `make`.
2. Clone the repository and install pre-commit hooks:
   ```bash
   git clone git@github.com:vniharika35/A.W.A.R.E..git
   cd A.W.A.R.E.
   pip install pre-commit
   pre-commit install
   ```
3. Launch the telemetry stack locally:
   ```bash
   docker compose up db api -d
   make simulate  # emits events + optional replay CSV
   ```
4. Explore the ingestion API (FastAPI docs available at http://localhost:8001/docs).
5. Build the documentation locally:
   ```bash
   make docs-serve
   ```
6. Run the baseline checks:
   ```bash
   make ci
   ```

### Useful Commands
- `make run-api` — start the FastAPI ingestion service locally.
- `make simulate` — run the digital twin simulator and export a replay CSV.
- `make leak-detect` — run the rule-based leak detector against a telemetry CSV (override `TELEMETRY=...` for custom data).
- `make docs-serve` — preview MkDocs documentation.

### Energy Optimization Quick Start (Phase 04)
1. Ensure telemetry exists (run `make simulate` or POST historical data to `/telemetry`).
2. Request a demand outlook:
   ```bash
   curl "http://localhost:8001/energy/forecast?horizon_hours=24" | jq '.points[0:3]'
   ```
3. Generate a pump plan aligned with tariffs and guardrails:
   ```bash
   curl -X POST http://localhost:8001/energy/optimize \\
     -H 'Content-Type: application/json' \\
     -d '{"horizon_hours":24,"pump_ids":["pump_a","pump_b"],"max_parallel_pumps":2,"pressure_floor_kpa":240}'
   ```
4. Review `expected_savings_pct`, `pressure_guard_breaches`, and per-hour `steps` before Alex approves execution downstream.

### Dashboard API Preview (Phase 05)
1. Pull KPI + ROI summary:
   ```bash
   curl http://localhost:8001/ux/dashboard/summary | jq '.kpis'
   ```
2. Stream the alerts feed that powers Alex’s sidebar:
   ```bash
   curl "http://localhost:8001/ux/dashboard/alerts?limit=5" | jq '.[] | {type,severity,message}'
   ```
3. Render the map overlay and scenario player using `/ux/dashboard/map` + `/ux/dashboard/scenarios` in the upcoming React shell.

### Multi-Agent Orchestrator (Phase 06)
Run a deterministic episode with the default policy:
```bash
python -m aware.agents | jq '.[].type'
```
For custom guardrails, edit `aware/infra/policies/phase-06-policy.yaml` (e.g., toggle auto-exec) and rerun the command to watch Watcher enforce safe mode when chaos hooks fire.

Comprehensive quick-start instructions for the digital twin, leak detection pipeline, and UI will arrive in later phases.

## Governance & Process
- Conventional Commits with SemVer releases (`v0.X.0-phase-0X`).
- Every phase merges via PR `phase-0X/<title>`, includes `docs/phase-0X.md`, and publishes GitHub Pages.
- Branch protection: 1 review, linear history, required `ci.yml` checks.
- CI/CD: GitHub Actions driving linting, tests, Docker builds, and docs publication.

## License
Released under the MIT License. See `LICENSE` for details.
