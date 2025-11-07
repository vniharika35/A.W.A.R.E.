from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from math import sin
from math import tau
from random import Random

from fastapi.testclient import TestClient


def seed_synthetic_energy_history(client: TestClient, hours: int = 96) -> None:
    rng = Random(42)
    start = datetime.now(timezone.utc) - timedelta(hours=hours)
    events: list[dict[str, object]] = []
    for hour in range(hours):
        timestamp = start + timedelta(hours=hour)
        base_demand = 32 + 9 * sin(tau * (hour % 24) / 24)
        for entity_id in ("zone-a", "zone-b"):
            events.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "entity_type": "junction",
                    "entity_id": entity_id,
                    "metric": "demand_lps",
                    "value": round(base_demand + rng.uniform(-1.5, 1.5), 3),
                    "unit": "L/s",
                    "source": "synthetic",
                    "quality": 0.99,
                },
            )
        price = 70 + 18 * sin(tau * ((hour + 6) % 24) / 24)
        events.append(
            {
                "timestamp": timestamp.isoformat(),
                "entity_type": "tariff",
                "entity_id": "day_ahead",
                "metric": "price_per_mwh",
                "value": round(price, 2),
                "unit": "USD/MWh",
                "source": "synthetic",
                "quality": 1.0,
            },
        )

    response = client.post("/telemetry", json={"events": events})
    assert response.status_code == 200
    assert response.json()["inserted"] == len(events)
