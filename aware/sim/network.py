"""Constructs a small EPANET-compatible network using WNTR."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import wntr

from .config import SimulationConfig


NETWORK_NAME: Final[str] = "aware_demo"


def build_demo_network(config: SimulationConfig) -> wntr.network.WaterNetworkModel:
    """Return a deterministic demo network for simulation.

    The layout includes:
    - One reservoir feeding the zone ("RES1")
    - One elevated storage tank ("TANK1")
    - Three junctions in a loop ("J1", "J2", "J3")
    - Four pipes and one pump with a head curve controlling tank refill
    """

    wn = wntr.network.WaterNetworkModel()
    wn.name = NETWORK_NAME

    # Global hydraulic options tuned for small demo network
    wn.options.hydraulic.demand_model = "PDD"
    wn.options.time.duration = config.duration_seconds
    wn.options.time.hydraulic_timestep = config.cadence_seconds
    wn.options.time.report_timestep = config.cadence_seconds
    wn.options.time.pattern_timestep = config.cadence_seconds
    wn.options.hydraulic.trials = 20

    # Patterns
    pattern_name = "demand_pattern"
    wn.add_pattern(pattern_name, [1.0] * max(1, config.steps()))

    # Nodes
    wn.add_reservoir("RES1", base_head=210.0)
    wn.add_tank(
        "TANK1",
        elevation=190.0,
        init_level=4.0,
        min_level=1.0,
        max_level=7.0,
        diameter=15.0,
        min_volume=0.0,
    )

    wn.add_junction("J1", base_demand=0.010, elevation=185.0, demand_pattern=pattern_name)
    wn.add_junction("J2", base_demand=0.015, elevation=183.0, demand_pattern=pattern_name)
    wn.add_junction("J3", base_demand=0.009, elevation=184.0, demand_pattern=pattern_name)

    # Links
    wn.add_pipe("P_RES_J1", "RES1", "J1", length=800.0, diameter=0.35, roughness=110.0)
    wn.add_pipe("P_J1_J2", "J1", "J2", length=600.0, diameter=0.30, roughness=110.0)
    wn.add_pipe("P_J2_J3", "J2", "J3", length=700.0, diameter=0.30, roughness=110.0)
    wn.add_pipe("P_J3_J1", "J3", "J1", length=550.0, diameter=0.30, roughness=110.0)

    wn.add_pump(
        "P_RES_T1",
        "RES1",
        "TANK1",
        pump_type="POWER",
        pump_parameter=60.0,
    )

    wn.get_link("P_RES_J1").status = wntr.network.LinkStatus.Open
    wn.get_link("P_J1_J2").status = wntr.network.LinkStatus.Open
    wn.get_link("P_J2_J3").status = wntr.network.LinkStatus.Open
    wn.get_link("P_J3_J1").status = wntr.network.LinkStatus.Open

    wn.add_pipe("P_T1_J2", "TANK1", "J2", length=750.0, diameter=0.30, roughness=115.0)
    wn.get_link("P_T1_J2").status = wntr.network.LinkStatus.Open

    return wn


def export_demo_network(config: SimulationConfig, path: Path) -> None:
    """Write the demo network to an EPANET INP file."""

    wn = build_demo_network(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    wn.write_inpfile(str(path))
