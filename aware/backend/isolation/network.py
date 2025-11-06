"""Graph abstractions shared between the simulator and isolation planner."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
from typing import Iterable
from typing import Set
from typing import Tuple


@dataclass(frozen=True, slots=True)
class Valve:
    id: str
    connects: Tuple[str, str]  # junction ids
    customers_affected: int
    loss_rate_lps: float


class WaterNetworkGraph:
    """Minimal graph abstraction for isolation planning.

    The graph is undirected with valves represented on edges. Junctions
    are nodes that may supply customers. Metadata per valve indicates how many
    customers would be isolated and an estimated water loss rate.
    """

    def __init__(self, valves: Iterable[Valve]) -> None:
        self.valves: Dict[str, Valve] = {valve.id: valve for valve in valves}
        self.adjacency: Dict[str, Set[str]] = {}
        for valve in valves:
            a, b = valve.connects
            self.adjacency.setdefault(a, set()).add(b)
            self.adjacency.setdefault(b, set()).add(a)

    def neighbors(self, node: str) -> Set[str]:
        return self.adjacency.get(node, set())

    def valve_between(self, a: str, b: str) -> Valve | None:
        for valve in self.valves.values():
            if {a, b} == set(valve.connects):
                return valve
        return None

    @classmethod
    def sample(cls) -> "WaterNetworkGraph":
        valves = [
            Valve("V_RES_J1", ("RES1", "J1"), customers_affected=120, loss_rate_lps=6.0),
            Valve("V_J1_J2", ("J1", "J2"), customers_affected=80, loss_rate_lps=4.0),
            Valve("V_J2_J3", ("J2", "J3"), customers_affected=45, loss_rate_lps=2.5),
            Valve("V_J3_J4", ("J3", "J4"), customers_affected=30, loss_rate_lps=1.5),
            Valve("V_J2_J5", ("J2", "J5"), customers_affected=55, loss_rate_lps=2.0),
        ]
        return cls(valves)
