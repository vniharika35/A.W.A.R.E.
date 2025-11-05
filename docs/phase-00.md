# Phase 00 — Kickoff

## Goal & Scope
- Bootstrap the A.W.A.R.E. repository with mandated structure (`aware/` scaffold,
  docs, CI, governance files).
- Align with personas (Alex, Maya, Jordan) and success metrics (false-alarm ≤ 5%,
  TFA ≤ 3 min, calibration error ≤ 10%, NRW ≥ 15% reduction, outage minutes ≥ 30%
  reduction, energy cost/MGal ≥ 15% reduction).
- Capture demo size (small, ~10–20 pipes/nodes) and hardware limits (≤ 4 CPU,
  ≤ 8 GB RAM, no GPU) for all subsequent design decisions.

## Design Decisions (trade-offs, risks)
- Adopt synthetic telemetry for the MVP to respect data availability and enable
  controlled leak injection scenarios.
- Keep the digital twin scope to a single pressure zone to stay within hardware
  constraints while maintaining realism.
- Commit to GitHub Actions + GHCR + MkDocs Material to streamline CI, container
  publishing, and documentation with minimal manual steps.
- Reserve secrets (`POSTGRES_URL`, `REDIS_URL`, `JWT_SECRET`, `EPANET_MODEL_URL`,
  `TARIFF_CSV_URL`) early to avoid rework during later phases.

## Implementation Notes (modules, schemas, configs)
- Repository scaffolded under `aware/` with sub-directories for backend, ml, sim,
  web, infra, tests, docs (placeholders tracked with `.gitkeep`).
- Added MIT `LICENSE`, Contributor Covenant `CODE_OF_CONDUCT.md`,
  `CONTRIBUTING.md`, `.editorconfig`, `.gitignore`, issue templates, and PR
  template enforcing phase/KPI alignment.
- Configured MkDocs (`mkdocs.yml`) with Material theme, nav, and documentation
  artifacts (`docs/index.md`, ADR-001, personas journeys, risk log, phase report
  template population).

## Results (target vs actual metrics, screenshots/GIFs)
- CI workflows defined (`.github/workflows/ci.yml`, `docs.yml`, `release.yml`) —
  ready for GitHub Actions.
- Documentation site builds locally via `make docs-serve` (to be validated in
  Phase 0 acceptance tests).
- No runtime metrics yet; this phase focuses on scaffolding and governance.

## Tests (what ran, coverage %, pass/fail)
- Pending initial `make ci` run (requires tooling setup in this phase).
- Docker Compose smoke will be added with service definitions in later phases.

## Acceptance Checklist (all criteria met)
- [x] Repo scaffolded with required structure and governance files.
- [x] Personas, KPIs, and constraints documented (ADR, user journeys, risk log).
- [ ] CI pipeline executed successfully.
- [ ] GitHub Pages published (pending remote setup after merge).

## Next Steps (follow-ups, debt)
1. Finalize tooling in Phase 0: pre-commit hooks, Makefile targets, Docker
   scaffolding, and baseline CI script execution.
2. Prepare PR #phase-00, merge after CI green, tag `v0.0.0-phase-00`, and enable
   GitHub Pages.
3. Gather EPANET model selection, simulation cadence, and database preferences
   ahead of Phase 1.
