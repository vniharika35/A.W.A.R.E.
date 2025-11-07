from __future__ import annotations

from fastapi.testclient import TestClient

from .utils import seed_synthetic_energy_history


def test_energy_forecast_endpoint(client: TestClient) -> None:
    seed_synthetic_energy_history(client)
    response = client.get("/energy/forecast", params={"horizon_hours": 12})
    assert response.status_code == 200
    body = response.json()
    assert body["horizon_hours"] == 12
    assert len(body["points"]) == 12
    confidences = [point["confidence"] for point in body["points"]]
    assert min(confidences) >= 0.5


def test_energy_optimize_endpoint(client: TestClient) -> None:
    seed_synthetic_energy_history(client)
    response = client.post(
        "/energy/optimize",
        json={
            "horizon_hours": 24,
            "pump_ids": ["pump_a", "pump_b", "pump_c"],
            "max_parallel_pumps": 2,
            "pressure_floor_kpa": 235.0,
            "energy_per_pump_mwh": 0.8,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["expected_savings_pct"] >= 12.0
    assert body["pressure_guard_breaches"] >= 0
    assert body["time_to_first_action_minutes"] >= 0
    assert len(body["steps"]) == 24
    assert len(body["forecast"]) == 24
