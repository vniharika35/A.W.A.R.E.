# Phase 07 Demo Script — A.W.A.R.E.

## Prep (5 minutes)
1. Copy `.env.example` → `.env` and tweak credentials if needed.
2. Install deps & start services:
   ```bash
   make install
   docker compose up db api redis -d
   ```
3. Seed telemetry + multi-agent evidence:
   ```bash
   make demo
   ```

## Demo Flow (≈10 minutes)
1. **Telemetry & Leak Detection**
   - Ingest replay or synthetic data (`make simulate` optional).
   - Hit `/leaks/analyze` via FastAPI docs or curl to show explainable alert.
2. **Energy Optimization**
   ```bash
   curl "http://localhost:8001/energy/forecast?horizon_hours=12" | jq '.points[0:3]'
   curl -X POST http://localhost:8001/energy/optimize -H 'Content-Type: application/json' \
        -d '{"horizon_hours":24,"pump_ids":["pump_a","pump_b"],"max_parallel_pumps":2}' | jq '.expected_savings_pct'
   ```
3. **Dashboard UX**
   ```bash
   curl http://localhost:8001/ux/dashboard/summary | jq '.kpis'
   curl http://localhost:8001/ux/dashboard/map | jq '.nodes[0]'
   ```
4. **Multi-Agent Orchestrator**
   ```bash
   python -m aware.agents | jq '.[].type'
   ```
   - Highlight Watcher chaos + safe mode in the JSON timeline (available under `build/demo-events.json`).
5. **Packaging Story**
   - Show `docker compose ps` proving api/db/redis/agents containers.
   - Point to policy YAML + demo script for TA handoff.

## Reset / Shutdown
```bash
docker compose down
rm -rf build/
```
