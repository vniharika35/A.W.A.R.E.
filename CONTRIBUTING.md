# Contributing to A.W.A.R.E.

Thank you for investing in the A.W.A.R.E. mission. This repository follows a
phase-driven workflow aligned with Design Thinking (Empathize → Define → Ideate)
and the personas Alex, Maya, and Jordan. Please review the guidelines below
before opening an issue or pull request.

## Ground Rules
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md).
- Use Conventional Commits (`type(scope): summary`).
- Target the relevant `phase-0X/<topic>` branch and keep the scope aligned with
  the phase acceptance criteria and KPIs.
- Reference personas, KPIs, and trust requirements in every PR (template
  provided).
- Run `make ci` locally before pushing and ensure GitHub Actions passes.

## Development Process
1. Create an issue or reference an existing one to discuss the change.
2. Branch from `main` using the naming convention `phase-0X/<short-title>`.
3. Implement changes within the `aware/` sub-packages, keeping modules loosely
   coupled and well tested.
4. Update or add documentation in `docs/` and the appropriate `docs/phase-0X.md`.
5. Run the relevant test suites (`make ci`, `make test`, `make e2e`, etc.).
6. Submit a pull request using the template, including evidence (screenshots,
   metrics, logs) and a filled acceptance checklist.

## Tooling
- Formatting and linting are enforced via `pre-commit`.
- Python projects use `ruff`, `mypy`, and `pytest`.
- JavaScript/TypeScript projects use `eslint`, `prettier`, `tsc`, and `vitest`.
- End-to-end scenarios run with `Playwright`.

## Releases
Each merged phase is tagged with `v0.X.0-phase-0X` and triggers a GitHub
Release plus documentation publish to GitHub Pages. Ensure release notes capture
persona impacts, KPI deltas, and trust considerations.

We are building for critical infrastructure. Keep safety, explainability,
and operator trust front and center in every change.
