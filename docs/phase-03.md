# Phase 03 — Isolation Sequencing & Actuation

## Goal & Scope
- Generate explainable valve isolation sequences that minimise customer impact while controlling water loss.
- Provide a state machine and audit trail for actions, with Alex kept in the loop until confidence grows.
- Deliver API endpoints for planning, executing, and rolling back valve operations with full logging.

## Design Decisions (trade-offs, risks)
- **Policy:** default to minimising customers affected, using water-loss as a secondary tie breaker to honour Alex/Jordan priorities.
- **Human-in-loop:** `/isolation/execute` rejects changes without `approved_by`, enforcing manual approval until trust metrics improve.
- **Radius:** planner searches at most 3 hops (~500 m) away from the leak to keep operational impact bounded.
- **Audit:** actions recorded in `isolation_actions` table with timestamps and operators for Jordan’s compliance needs.

## Implementation Notes
- `aware/backend/isolation/` contains the planner, graph abstractions, config, and state machine with NORMAL→…→RECOVERY transitions.
- `aware/backend/models.py` adds `IsolationAction`; FastAPI app exposes `/isolation/plan`, `/isolation/execute`, `/isolation/rollback` and logs actions.
- New tests cover planner ranking, approval enforcement, state transitions, and rollback flows.
- `docs/samples/telemetry_sample.csv` reused alongside `make leak-detect`; new docs detail usage and risks.

```mermaid
graph TD
  Leak[Leak Alert] --> Planner[Isolation Planner]
  Planner -->|Valve Sequence| Execution[Execute (requires approval)]
  Execution --> StateMachine[State Machine]
  Execution --> Audit[Audit Log]
  StateMachine -->|Rollback| Recovery
```

## Results
- Planner proposes valves ranked by customer disruption, requiring approval flag before execution.
- API demo: plan → execute (approved) → rollback returns audit entries and state resets to NORMAL.
- State machine prevents invalid transitions (verified via tests).

## Tests
- `pytest aware/tests/test_isolation.py` (planner ordering, approval requirement, rollback path).
- `pytest aware/tests/test_ingestion_api.py::test_leak_analysis_endpoint` ensures leak detection still functional alongside isolation endpoints.

## Acceptance Checklist
- [x] Valve sequence planner reflects policy, radius, and explainability requirements.
- [x] State machine + audit trail implemented with manual approval in place.
- [x] API endpoints for plan/execute/rollback with evidence in tests.
- [x] Documentation updated (phase report, README, MkDocs nav, risk log).

## Next Steps
1. Integrate planner output with UI maps and watch status for Alex (Phase 5).
2. Add hydraulic verification against the digital twin before executing valves.
3. Instrument Watcher to simulate failed valve operations and ensure safe fallback (Phase 6).
