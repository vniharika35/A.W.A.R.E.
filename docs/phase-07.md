# Phase 07 — Packaging & Demo Readiness

## Goal & Scope
- Provide a reproducible deployment story (docker-compose, Make targets, env templates).
- Capture a TA-ready demo script showcasing telemetry → UX → agents.
- Ensure artifacts (replay, demo events, policy) live in-repo for handoff.

## Design Decisions
- **`.env.example` + env_file:** docker-compose + dev tools read from `.env`, keeping secrets local while documenting required vars.
- **Make targets as UX:** `make demo`, `make orchestrator`, and `make compose-up/down` encapsulate the standard runbook.
- **Demo artifacts under `build/`:** `make demo` seeds the replay CSV + agent timeline, so demos can run offline.
- **Docs-first handoff:** MkDocs nav now includes the demo script alongside prior phase reports.

## Implementation Notes
- `docker-compose.yml` now loads `.env`, parameterises API/energy settings, and adds an `agents` service wired to `python -m aware.agents`.
- `.env.example` documents DB/API/agent knobs; `.gitignore` already protects `.env`.
- `Makefile` additions: `demo`, `compose-up`, `compose-down`, `orchestrator`, and a real `e2e` step that exercises the agents.
- `docs/demo-script-phase-07.md` walks TAs through the live demo with exact commands.
- README quick-start updated with Energy, Dashboard, and Orchestrator sections.

## Results
- Fresh checkout → `cp .env.example .env && make install && make demo` produces replay + agent timeline plus docs served via docker-compose.
- Demo script + new targets shorten TA onboarding to <15 minutes.
- Agents, energy optimizer, and UX endpoints now share the same environment contract.

## Tests / Evidence
- Manual verification via `make demo`, `docker compose up api db redis agents -d`, and curling the documented endpoints.
- Automated coverage remains in `pytest` (blocked locally by pytest<8, see repo instructions).

## Acceptance Checklist
- [x] `.env` template + docker-compose wiring.
- [x] Make targets for demo/orchestrator/compose.
- [x] Demo script captured in docs + nav.
- [x] README updated with packaging guidance.

## Next Steps
- Automate demo recording (asciinema) using the scripted commands.
- Extend docker-compose with a React container once the dashboard UI lands.
