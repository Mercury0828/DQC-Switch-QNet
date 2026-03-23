from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple

from qdc_project.algorithms.scheduler_baseline import Placement
from qdc_project.circuit.dag_utils import CircuitDAG
from qdc_project.topology.qdc_topology import QDCTopology


@dataclass
class RackAwareGreedyPlacer:
    """Greedy placement that groups heavily interacting logical qubits within racks first."""

    def place(self, dag: CircuitDAG, topology: QDCTopology) -> Placement:
        logical_qubits = sorted({qubit for gate in dag.gates.values() for qubit in gate.qubits})
        interactions: Dict[Tuple[str, str], int] = Counter()
        degree: Dict[str, int] = Counter()
        for gate in dag.gates.values():
            if len(gate.qubits) == 2:
                a, b = sorted(gate.qubits)
                interactions[(a, b)] += 1
                degree[a] += 1
                degree[b] += 1

        rack_capacity = topology.config.qpus_per_rack * topology.config.data_qubits_per_qpu
        rack_loads = {rack_id: 0 for rack_id in topology.racks}
        rack_assignments: Dict[str, str] = {}
        qpu_loads = {qpu_id: 0 for qpu_id in topology.qpus}
        adjacency = defaultdict(list)
        for (a, b), weight in interactions.items():
            adjacency[a].append((b, weight))
            adjacency[b].append((a, weight))

        for logical in sorted(logical_qubits, key=lambda item: (-degree[item], item)):
            preferred_scores = Counter()
            for neighbor, weight in adjacency[logical]:
                if neighbor in rack_assignments:
                    preferred_scores[rack_assignments[neighbor]] += weight
            candidate_racks = [
                rack_id for rack_id, load in rack_loads.items() if load < rack_capacity
            ]
            if not candidate_racks:
                raise ValueError("Insufficient rack capacity for greedy placement")
            rack_id = min(
                candidate_racks,
                key=lambda rid: (
                    -preferred_scores[rid],
                    rack_loads[rid],
                    rid,
                ),
            )
            rack_assignments[logical] = rack_id
            rack_loads[rack_id] += 1

        mapping: Dict[str, str] = {}
        for logical in logical_qubits:
            rack_id = rack_assignments[logical]
            feasible_qpus: List[str] = [
                qpu.qpu_id
                for qpu in topology.rack_qpus(rack_id)
                if qpu_loads[qpu.qpu_id] < qpu.data_qubits
            ]
            if not feasible_qpus:
                feasible_qpus = [
                    qpu_id
                    for qpu_id, qpu in topology.qpus.items()
                    if qpu_loads[qpu_id] < qpu.data_qubits
                ]
            selected = min(feasible_qpus, key=lambda qid: (qpu_loads[qid], qid))
            mapping[logical] = selected
            qpu_loads[selected] += 1
        return Placement(mapping)
