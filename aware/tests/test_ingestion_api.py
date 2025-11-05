from __future__ import annotations

from datetime import datetime
from datetime import timedelta

from fastapi.testclient import TestClient

from aware.sim.config import SimulationConfig
from aware.sim.simulator import DigitalTwinSimulator


def _generate_events(count: int) -> list[dict[str, object]]:
    config = SimulationConfig(duration_seconds=120, cadence_seconds=2)
    events = list(DigitalTwinSimulator(config).iter_events())[:count]

    payload: list[dict[str, object]] = []
    for idx, event in enumerate(events):
        payload.append(
            {
                "timestamp": (event.timestamp + timedelta(seconds=idx * 0.01)).isoformat(),
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "metric": event.metric,
                "value": event.value,
                "unit": event.unit,
                "source": event.source,
                "quality": event.quality,
            },
        )
    return payload


def test_ingest_and_query_stats(client: TestClient) -> None:
    payload = {"events": _generate_events(120)}
    response = client.post("/telemetry", json=payload)
    assert response.status_code == 200
    assert response.json()["inserted"] == len(payload["events"])

    stats = client.get("/telemetry/stats")
    assert stats.status_code == 200
    metrics = {item["metric"]: item["count"] for item in stats.json()}
    assert metrics["pressure_kpa"] >= 1
    assert metrics["flow_lps"] >= 1
    assert metrics["price_per_mwh"] >= 1

    latest = client.get("/telemetry/latest", params={"limit": 5})
    assert latest.status_code == 200
    assert len(latest.json()) == 5


def test_bulk_ingest_10k_events(client: TestClient) -> None:
    events = _generate_events(500)
    events_len = len(events)
    # Repeat the set to exceed 10k rows while keeping runtime small
    repeated = []
    for i in range(20):  # 500 * 20 = 10,000
        for j, event in enumerate(events):
            clone = dict(event)
            base_ts = datetime.fromisoformat(str(event["timestamp"]))
            offset = i * events_len + j
            clone["timestamp"] = (base_ts + timedelta(seconds=offset * 0.01)).isoformat()
            repeated.append(clone)

    response = client.post("/telemetry", json={"events": repeated})
    assert response.status_code == 200
    assert response.json()["inserted"] == len(repeated)
