"""Isolation planner implementation."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable
from typing import List

from .config import IsolationPlannerConfig
from .config import IsolationPolicy
from .network import Valve
from .network import WaterNetworkGraph


@dataclass(frozen=True, slots=True)
class IsolationStep:
    order: int
    valve_id: str
    customers_affected: int
    loss_rate_lps: float


@dataclass(frozen=True, slots=True)
class IsolationPlan:
    leak_pipe_id: str
    steps: List[IsolationStep]
    approval_required: bool

    def summary(self) -> dict[str, object]:
        return {
            "leak_pipe_id": self.leak_pipe_id,
            "approval_required": self.approval_required,
            "steps": [step.__dict__ for step in self.steps],
        }


class IsolationPlanner:
    """Compute an ordered list of valve closures to isolate a leaking segment."""

    def __init__(
        self,
        graph: WaterNetworkGraph | None = None,
        config: IsolationPlannerConfig | None = None,
    ) -> None:
        self.graph = graph or WaterNetworkGraph.sample()
        self.config = config or IsolationPlannerConfig()

    def plan(self, leak_pipe_id: str, start_node: str, end_node: str) -> IsolationPlan:
        visited: set[str] = set()
        queue = deque([(start_node, 0), (end_node, 0)])
        valve_hops: dict[str, int] = {}

        while queue:
            node, hops = queue.popleft()
            if hops > self.config.max_hops:
                continue
            if node in visited:
                continue
            visited.add(node)
            for neighbor in self.graph.neighbors(node):
                valve = self.graph.valve_between(node, neighbor)
                if valve is None:
                    continue
                next_hops = hops + 1
                if next_hops <= self.config.max_hops:
                    existing = valve_hops.get(valve.id)
                    if existing is None or next_hops < existing:
                        valve_hops[valve.id] = next_hops
                    queue.append((neighbor, next_hops))

        candidate_valves = [self.graph.valves[valve_id] for valve_id in valve_hops.keys()]
        ranked = self._rank_valves(candidate_valves)
        steps = [
            IsolationStep(
                order=index + 1,
                valve_id=valve.id,
                customers_affected=valve.customers_affected,
                loss_rate_lps=valve.loss_rate_lps,
            )
            for index, valve in enumerate(ranked)
        ]
        return IsolationPlan(
            leak_pipe_id=leak_pipe_id,
            steps=steps,
            approval_required=True,
        )

    def _rank_valves(self, valves: Iterable[Valve]) -> List[Valve]:
        policy = self.config.policy

        def primary(valve: Valve) -> float:
            if policy == IsolationPolicy.MINIMIZE_CUSTOMERS:
                return valve.customers_affected
            return valve.loss_rate_lps

        def secondary(valve: Valve) -> float:
            if policy == IsolationPolicy.MINIMIZE_CUSTOMERS:
                return valve.loss_rate_lps
            return valve.customers_affected

        sorted_valves = sorted(
            valves,
            key=lambda valve: (primary(valve), secondary(valve)),
        )
        return list(sorted_valves)
