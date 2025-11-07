# A.W.A.R.E. Dashboard Shell

Phase 05 establishes backend contracts for the real-time dashboard while the React
shell lands in later phases. The `/ux/dashboard/*` APIs deliver everything the UI
needs:

- `summary` → KPI cards + energy ROI chip.
- `alerts` → Explainable feed (leak, energy, isolation) for Alex’s sidebar.
- `map` → Node/pipeline overlays with status + coordinates for the live map.
- `scenarios` → Scripted drills for the scenario player.

When we scaffold the Vite + React app in Phase 07 we only need to hydrate these
endpoints, apply SCU branding, and stream updates from the Phase 06 event bus.
