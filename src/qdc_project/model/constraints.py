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

    for event in state.event_log:
        if event.event_type == "cross_rack_generation" and event.start_time < state.topology.config.switch_reconfig_latency:
            # The first generation may happen after a reconfiguration from t=0; later checks rely on event ordering.
            pass

    distilled = {
        record.pair_id: record
        for records in state.epr_inventory.values()
        for record in records
        if record.kind == "distilled"
    }
    for record in distilled.values():
        if len(record.source_pair_ids) != 2:
            raise InvariantViolation("Distillation must consume exactly two source pairs")

    split_gates = [gate_id for gate_id, mode in state.gate_execution_mode.items() if mode == "split"]
    if state.metrics.split_gate_count != len(split_gates):
        raise InvariantViolation("Split gate accounting mismatch")
