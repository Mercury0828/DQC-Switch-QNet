from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from qdc_project.circuit.dag_utils import CircuitDAG, Gate
from qdc_project.model.state import EPRRecord, SimulationState
from qdc_project.topology.qdc_topology import QDCTopology


@dataclass
class Placement:
    logical_to_qpu: Dict[str, str]


class RandomPlacementStrategy:
    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def place(self, dag: CircuitDAG, topology: QDCTopology) -> Placement:
        logical_qubits = sorted({qubit for gate in dag.gates.values() for qubit in gate.qubits})
        qpu_ids = topology.qpu_ids()
        occupancy = {qpu_id: 0 for qpu_id in qpu_ids}
        mapping: Dict[str, str] = {}
        for logical in logical_qubits:
            feasible = [
                qpu_id
                for qpu_id in qpu_ids
                if occupancy[qpu_id] < topology.qpus[qpu_id].data_qubits
            ]
            if not feasible:
                raise ValueError("Insufficient QPU data capacity for random placement")
            selected = self._rng.choice(feasible)
            mapping[logical] = selected
            occupancy[selected] += 1
        return Placement(mapping)


class AveragePlacementStrategy:
    """Simple non-architecture-aware baseline that balances qubits by QPU load only."""

    def place(self, dag: CircuitDAG, topology: QDCTopology) -> Placement:
        logical_qubits = sorted({qubit for gate in dag.gates.values() for qubit in gate.qubits})
        qpu_ids = sorted(topology.qpu_ids())
        occupancy = {qpu_id: 0 for qpu_id in qpu_ids}
        mapping: Dict[str, str] = {}
        for logical in logical_qubits:
            feasible = [
                qpu_id
                for qpu_id in qpu_ids
                if occupancy[qpu_id] < topology.qpus[qpu_id].data_qubits
            ]
            if not feasible:
                raise ValueError("Insufficient QPU data capacity for average placement")
            selected = min(feasible, key=lambda qpu_id: (occupancy[qpu_id], qpu_id))
            mapping[logical] = selected
            occupancy[selected] += 1
        return Placement(mapping)


class DirectOnlyScheduler:
    """Baseline scheduler with explicit EPR generation, buffer accounting, and switch lockout."""

    def __init__(self) -> None:
        self._epr_counter = 0

    def run(self, dag: CircuitDAG, placement: Placement, state: SimulationState) -> SimulationState:
        for gate_id in dag.topological_order():
            gate = dag.gates[gate_id]
            self._schedule_gate(gate, placement, state)
        state.finalize_metrics()
        return state

    def _schedule_gate(self, gate: Gate, placement: Placement, state: SimulationState) -> None:
        qpus = tuple(placement.logical_to_qpu[qubit] for qubit in gate.qubits)
        predecessor_ready = max((state.gate_end_times[pred] for pred in gate.predecessors), default=0)
        earliest = max([predecessor_ready] + [state.qpu_state[qpu].busy_until for qpu in qpus])
        wait_added = max(0, earliest - predecessor_ready)
        state.metrics.latency_breakdown["wait_time"] += wait_added

        if len(qpus) == 1 or qpus[0] == qpus[-1]:
            duration = state.topology.gate_duration(gate.name, qpus[0], None)
            start = earliest
        else:
            start = self._realize_remote_gate(qpus[0], qpus[1], earliest, state)
            duration = state.topology.gate_duration(gate.name, qpus[0], qpus[1])

        end = start + duration
        for qpu in set(qpus):
            state.qpu_state[qpu].busy_until = end
        state.gate_start_times[gate.gate_id] = start
        state.gate_end_times[gate.gate_id] = end
        state.executed_gates.add(gate.gate_id)
        state.metrics.latency_breakdown["local_gate"] += duration

    def _realize_remote_gate(self, qpu_a: str, qpu_b: str, earliest: int, state: SimulationState) -> int:
        key = tuple(sorted((qpu_a, qpu_b)))
        rack_pair = (
            state.topology.qpus[qpu_a].rack_id,
            state.topology.qpus[qpu_b].rack_id,
        )
        generation_start = earliest
        kind = "intra_rack" if state.topology.same_rack(qpu_a, qpu_b) else "cross_rack"
        if kind == "cross_rack":
            generation_start = state.switch_state.ensure_link(rack_pair, earliest)
            if not state.switch_state.can_generate(generation_start):
                raise RuntimeError("Cross-rack EPR generation attempted during switch lockout")
        for qpu_id in key:
            qpu_state = state.qpu_state[qpu_id]
            qpu = state.topology.qpus[qpu_id]
            if qpu_state.active_comm_qubits + 1 > qpu.comm_qubits:
                generation_start = max(generation_start, qpu_state.busy_until)
            if qpu_state.buffer_occupancy + 1 > qpu.buffer_qubits:
                raise RuntimeError(f"Insufficient buffer capacity on {qpu_id}")
            qpu_state.active_comm_qubits += 1
            qpu_state.buffer_occupancy += 1
        latency = state.topology.epr_latency(qpu_a, qpu_b)
        ready_time = generation_start + latency
        pair_id = f"epr_{self._epr_counter}"
        self._epr_counter += 1
        record = EPRRecord(pair_id=pair_id, endpoints=key, generated_at=ready_time, kind=kind)
        state.epr_inventory.setdefault(key, []).append(record)
        for qpu_id in key:
            qpu_state = state.qpu_state[qpu_id]
            qpu_state.active_comm_qubits -= 1
        state.record_buffer_sample()
        if kind == "cross_rack":
            state.metrics.epr_counts["cross_rack"] += 1
            state.metrics.latency_breakdown["cross_rack_epr"] += latency
        else:
            state.metrics.epr_counts["intra_rack"] += 1
            state.metrics.latency_breakdown["intra_rack_epr"] += latency
        self._consume_epr(key, ready_time, state)
        return ready_time

    def _consume_epr(self, key: Tuple[str, str], at_time: int, state: SimulationState) -> None:
        records: List[EPRRecord] = state.epr_inventory[key]
        available = [record for record in records if record.consumed_at is None and record.generated_at <= at_time]
        if not available:
            raise RuntimeError("Remote gate attempted without a ready EPR pair")
        selected = min(available, key=lambda record: record.generated_at)
        selected.consumed_at = at_time
        for qpu_id in key:
            qpu_state = state.qpu_state[qpu_id]
            qpu_state.buffer_occupancy -= 1
        state.record_buffer_sample()
