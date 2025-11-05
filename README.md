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

## Getting Started (Phase 0)
1. Install prerequisites: Docker, Docker Compose, Python 3.11+, Node 18+, and `make`.
2. Clone the repository and install pre-commit hooks:
   ```bash
   git clone git@github.com:vniharika35/A.W.A.R.E..git
   cd A.W.A.R.E.
   pip install pre-commit
   pre-commit install
   ```
3. Build the documentation locally:
   ```bash
   make docs-serve
   ```
4. Run the baseline checks:
   ```bash
   make ci
   ```

Comprehensive quick-start instructions for the digital twin, leak detection pipeline, and UI will arrive in later phases.

## Governance & Process
- Conventional Commits with SemVer releases (`v0.X.0-phase-0X`).
- Every phase merges via PR `phase-0X/<title>`, includes `docs/phase-0X.md`, and publishes GitHub Pages.
- Branch protection: 1 review, linear history, required `ci.yml` checks.
- CI/CD: GitHub Actions driving linting, tests, Docker builds, and docs publication.

## License
Released under the MIT License. See `LICENSE` for details.
