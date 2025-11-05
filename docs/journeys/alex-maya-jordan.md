# User Journeys — Alex, Maya, Jordan

## Alex — Control Room Operator
1. Monitors the A.W.A.R.E. dashboard with live telemetry, KPI cards, and alert
   summaries.
2. Receives a fused leak alert with confidence score, top contributing signals,
   and simulation-before-execution preview.
3. Reviews the recommended valve isolation plan, estimated impact radius, and
   energy implications.
4. Approves auto-execution or requests manual confirmation from Maya while the
   Watcher agent tracks guardrails.
5. After resolution, audits the action log, ensuring compliance and noting
   lessons learned for future tuning.

## Maya — Field Technician
1. Receives a mobile notification with an actionable job: isolate valves in the
   affected zone.
2. Reviews the guided valve sequence, torque requirements, and safety checks.
3. Executes the sequence, confirming each step in the mobile UI while the system
   updates the digital twin state.
4. Observes live pressure stabilization data and can trigger an instant
   rollback if conditions deviate from the simulation.
5. Submits a short field report (photos, notes) that is appended to the audit
   log for Jordan and Alex to review.

## Jordan — Asset Manager
1. Starts the day with KPI cards tracking NRW, outage minutes, and energy spend
   reductions over the current sprint.
2. Reviews the audit trail of recent leak events, including alert accuracy,
   time-to-first-action, and customer impact estimates.
3. Examines the energy optimization report comparing actual vs baseline pump
   schedules and cost savings.
4. Prepares compliance or board-ready reports using exportable summaries and
   visualizations directly from the documentation site.
5. Identifies assets for proactive maintenance based on recurring anomalies or
   high-risk zones flagged by the Planner agent.
