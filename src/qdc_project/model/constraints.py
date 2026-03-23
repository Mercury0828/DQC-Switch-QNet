from __future__ import annotations

from qdc_project.circuit.dag_utils import CircuitDAG
from qdc_project.model.state import SimulationState


class InvariantViolation(RuntimeError):
    pass


def validate_postconditions(state: SimulationState, dag: CircuitDAG) -> None:
    if set(dag.gates) != state.executed_gates:
        raise InvariantViolation("Every gate must execute exactly once")

    for gate_id, gate in dag.gates.items():
        start = state.gate_start_times[gate_id]
        for pred in gate.predecessors:
            if state.gate_end_times[pred] > start:
                raise InvariantViolation(f"Precedence violated by gate {gate_id}")

    for qpu_id, qpu_state in state.qpu_state.items():
        qpu = state.topology.qpus[qpu_id]
        if qpu_state.active_data_qubits > qpu.data_qubits:
            raise InvariantViolation(f"Data capacity exceeded on {qpu_id}")
        if qpu_state.active_comm_qubits < 0 or qpu_state.buffer_occupancy < 0:
            raise InvariantViolation(f"Negative communication or buffer state on {qpu_id}")
        if qpu_state.active_comm_qubits > qpu.comm_qubits:
            raise InvariantViolation(f"Communication capacity exceeded on {qpu_id}")
        if qpu_state.buffer_occupancy > qpu.buffer_qubits:
            raise InvariantViolation(f"Buffer capacity exceeded on {qpu_id}")
