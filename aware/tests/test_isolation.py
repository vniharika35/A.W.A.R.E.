from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aware.backend.isolation import IsolationPlanner
from aware.backend.isolation import IsolationPlannerConfig
from aware.backend.isolation import IsolationPolicy
from aware.backend.isolation.network import WaterNetworkGraph


@pytest.fixture()
def sample_graph() -> WaterNetworkGraph:
    return WaterNetworkGraph.sample()


@pytest.fixture()
def planner(sample_graph: WaterNetworkGraph) -> IsolationPlanner:
    config = IsolationPlannerConfig(policy=IsolationPolicy.MINIMIZE_CUSTOMERS, max_hops=3)
    return IsolationPlanner(graph=sample_graph, config=config)


def test_planner_prefers_lower_customer_impact(planner: IsolationPlanner) -> None:
    plan = planner.plan("P_J2_J3", start_node="J2", end_node="J3")
    customers = [step.customers_affected for step in plan.steps]
    assert customers[0] == min(customers)
    assert plan.approval_required is True


def test_planner_respects_radius(sample_graph: WaterNetworkGraph) -> None:
    constrained = IsolationPlanner(
        graph=sample_graph,
        config=IsolationPlannerConfig(policy=IsolationPolicy.MINIMIZE_CUSTOMERS, max_hops=1),
    )
    plan = constrained.plan("P_J1_J2", start_node="J1", end_node="J2")
    allowed = {"V_RES_J1", "V_J1_J2", "V_J2_J3", "V_J2_J5"}
    assert set(step.valve_id for step in plan.steps).issubset(allowed)


def test_isolation_plan_endpoint(client: TestClient) -> None:
    payload = {"leak_pipe_id": "P_J2_J3", "start_node": "J2", "end_node": "J3"}
    response = client.post("/isolation/plan", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["approval_required"] is True
    assert len(body["steps"]) >= 1


def test_isolation_execute_requires_approval(client: TestClient) -> None:
    execute_payload = {"leak_pipe_id": "P_J2_J3", "valve_ids": ["V_J2_J3"]}
    response = client.post("/isolation/execute", json=execute_payload)
    assert response.status_code == 400


def test_isolation_execute_and_rollback(client: TestClient) -> None:
    # Seed plan to move state to ISOLATING
    client.post(
        "/isolation/plan",
        json={"leak_pipe_id": "P_J2_J3", "start_node": "J2", "end_node": "J3"},
    )
    execute_payload = {
        "leak_pipe_id": "P_J2_J3",
        "valve_ids": ["V_J2_J3"],
        "approved_by": "alex",
    }
    exec_response = client.post("/isolation/execute", json=execute_payload)
    assert exec_response.status_code == 200
    actions = exec_response.json()["actions"]
    assert actions[0]["action"] == "close"
    rollback_payload = {
        "leak_pipe_id": "P_J2_J3",
        "valve_ids": ["V_J2_J3"],
        "approved_by": "alex",
    }
    rollback_response = client.post("/isolation/rollback", json=rollback_payload)
    assert rollback_response.status_code == 200
    assert rollback_response.json()["actions"][0]["action"] == "open"
