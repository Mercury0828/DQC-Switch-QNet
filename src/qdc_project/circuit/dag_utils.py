from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class Gate:
    gate_id: str
    name: str
    qubits: Tuple[str, ...]
    predecessors: Tuple[str, ...] = ()


@dataclass
class CircuitDAG:
    gates: Dict[str, Gate]
    successors: Dict[str, List[str]] = field(default_factory=dict)

    @classmethod
    def from_gates(cls, gates: Sequence[Gate]) -> "CircuitDAG":
        gate_map = {gate.gate_id: gate for gate in gates}
        successors = {gate.gate_id: [] for gate in gates}
        for gate in gates:
            for pred in gate.predecessors:
                if pred not in gate_map:
                    raise ValueError(f"Unknown predecessor {pred} for gate {gate.gate_id}")
                successors[pred].append(gate.gate_id)
        return cls(gates=gate_map, successors=successors)

    def topological_order(self) -> List[str]:
        indegree = {gate_id: len(gate.predecessors) for gate_id, gate in self.gates.items()}
        ready = sorted([gate_id for gate_id, degree in indegree.items() if degree == 0])
        order: List[str] = []
        while ready:
            gate_id = ready.pop(0)
            order.append(gate_id)
            for succ in self.successors.get(gate_id, []):
                indegree[succ] -= 1
                if indegree[succ] == 0:
                    ready.append(succ)
                    ready.sort()
        if len(order) != len(self.gates):
            raise ValueError("Circuit contains a cycle")
        return order

    def predecessors_done(self, gate_id: str, executed: Iterable[str]) -> bool:
        done = set(executed)
        return all(pred in done for pred in self.gates[gate_id].predecessors)
