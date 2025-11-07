from __future__ import annotations

from fastapi.testclient import TestClient

from .utils import seed_synthetic_energy_history


def test_dashboard_summary_and_alerts(client: TestClient) -> None:
    seed_synthetic_energy_history(client)

    summary = client.get("/ux/dashboard/summary")
    assert summary.status_code == 200
    summary_body = summary.json()
    assert summary_body["alerts_open"] >= 0
    assert summary_body["kpis"]
    assert summary_body["energy"] is None or summary_body["energy"]["expected_savings_pct"] >= 0

    alerts = client.get("/ux/dashboard/alerts", params={"limit": 3})
    assert alerts.status_code == 200
    alert_items = alerts.json()
    assert len(alert_items) >= 1
    assert {item["type"] for item in alert_items} <= {"leak", "energy", "isolation"}


def test_dashboard_map_and_scenarios(client: TestClient) -> None:
    seed_synthetic_energy_history(client)

    map_response = client.get("/ux/dashboard/map")
    assert map_response.status_code == 200
    body = map_response.json()
    assert len(body["nodes"]) >= 4
    assert len(body["pipes"]) >= 3

    scenarios = client.get("/ux/dashboard/scenarios")
    assert scenarios.status_code == 200
    scenario_items = scenarios.json()
    assert len(scenario_items) >= 2
    assert all("steps" in item for item in scenario_items)
