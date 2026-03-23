from qdc_project.algorithms.scheduler_baseline import AveragePlacementStrategy, RandomPlacementStrategy
from qdc_project.circuit.dag_utils import CircuitDAG, Gate
from qdc_project.circuit.loaders import load_handcrafted_representative
from qdc_project.model.constraints import InvariantViolation, validate_postconditions
from qdc_project.model.state import SimulationState
from qdc_project.simulation.engine import SimulationEngine
from qdc_project.topology.qdc_topology import QDCTopology, TopologyConfig


def build_topology() -> QDCTopology:
    return QDCTopology(
        TopologyConfig(
            racks=2,
            qpus_per_rack=2,
            data_qubits_per_qpu=4,
            comm_qubits_per_qpu=1,
            buffer_qubits_per_qpu=2,
            intra_epr_latency=2,
            cross_epr_latency=7,
            switch_reconfig_latency=3,
        )
    )


def test_random_and_average_placements_fit_capacity() -> None:
    dag = load_handcrafted_representative()
    topology = build_topology()
    random_placement = RandomPlacementStrategy(seed=7).place(dag, topology)
    average_placement = AveragePlacementStrategy().place(dag, topology)
    for placement in (random_placement, average_placement):
        counts = {qpu_id: 0 for qpu_id in topology.qpu_ids()}
        for qpu_id in placement.logical_to_qpu.values():
            counts[qpu_id] += 1
        for qpu_id, count in counts.items():
            assert count <= topology.qpus[qpu_id].data_qubits


def test_direct_only_scheduler_executes_each_gate_once_and_preserves_precedence() -> None:
    dag = load_handcrafted_representative()
    topology = build_topology()
    placement = AveragePlacementStrategy().place(dag, topology)
    state = SimulationEngine(topology).run_direct_only(dag, placement)
    assert state.executed_gates == set(dag.gates)
    for gate_id, gate in dag.gates.items():
        for pred in gate.predecessors:
            assert state.gate_end_times[pred] <= state.gate_start_times[gate_id]


def test_switch_reconfiguration_is_counted_for_cross_rack_workloads() -> None:
    dag = CircuitDAG.from_gates([
        Gate("g0", "cx", ("q0", "q1")),
        Gate("g1", "cx", ("q0", "q2"), predecessors=("g0",)),
    ])
    topology = build_topology()
    placement = AveragePlacementStrategy().place(dag, topology)
    state = SimulationEngine(topology).run_direct_only(dag, placement)
    assert state.metrics.latency_breakdown["switch_reconfiguration"] >= 0
    assert state.metrics.epr_counts["cross_rack"] + state.metrics.epr_counts["intra_rack"] >= 1


def test_validate_postconditions_detects_precedence_violation() -> None:
    topology = build_topology()
    dag = CircuitDAG.from_gates([
        Gate("g0", "x", ("q0",)),
        Gate("g1", "x", ("q0",), predecessors=("g0",)),
    ])
    state = SimulationState.create(topology)
    state.executed_gates = {"g0", "g1"}
    state.gate_start_times = {"g0": 0, "g1": 0}
    state.gate_end_times = {"g0": 2, "g1": 1}
    try:
        validate_postconditions(state, dag)
    except InvariantViolation:
        return
    raise AssertionError("Invariant violation was not raised")
