from __future__ import annotations

from qdc_project.algorithms.scheduler_baseline import DirectOnlyScheduler, Placement
from qdc_project.circuit.dag_utils import CircuitDAG
from qdc_project.model.constraints import validate_postconditions
from qdc_project.model.state import SimulationState
from qdc_project.topology.qdc_topology import QDCTopology


class SimulationEngine:
    def __init__(self, topology: QDCTopology) -> None:
        self.topology = topology

    def run_direct_only(self, dag: CircuitDAG, placement: Placement) -> SimulationState:
        state = SimulationState.create(self.topology)
        scheduler = DirectOnlyScheduler()
        state = scheduler.run(dag, placement, state)
        validate_postconditions(state, dag)
        return state
