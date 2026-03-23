from __future__ import annotations

from dataclasses import dataclass
from typing import List

from qdc_project.circuit.dag_utils import CircuitDAG


@dataclass
class CollectiveBatchingPolicy:
    lookahead_depth: int = 3
    max_batch_size: int = 3

    def plan_batch_size(self, dag: CircuitDAG, topological_order: List[str], start_index: int, same_rack_only: bool) -> int:
        if not same_rack_only:
            return 1
        count = 0
        for gate_id in topological_order[start_index : start_index + self.lookahead_depth]:
            gate = dag.gates[gate_id]
            if len(gate.qubits) == 2:
                count += 1
        return max(1, min(self.max_batch_size, count))
