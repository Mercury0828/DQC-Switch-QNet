from __future__ import annotations

import random
from typing import List

from qdc_project.circuit.dag_utils import CircuitDAG, Gate


def generate_synthetic_workload(
    num_qubits: int,
    depth: int,
    two_qubit_probability: float,
    seed: int,
) -> CircuitDAG:
    rng = random.Random(seed)
    qubits = [f"q{i}" for i in range(num_qubits)]
    last_gate_for_qubit = {qubit: None for qubit in qubits}
    gates: List[Gate] = []

    for layer in range(depth):
        if rng.random() < two_qubit_probability and num_qubits >= 2:
            a, b = sorted(rng.sample(qubits, 2))
            predecessors = tuple(
                pred for pred in {last_gate_for_qubit[a], last_gate_for_qubit[b]} if pred is not None
            )
            gate = Gate(f"g{layer}", "cx", (a, b), predecessors=predecessors)
            last_gate_for_qubit[a] = gate.gate_id
            last_gate_for_qubit[b] = gate.gate_id
        else:
            qubit = rng.choice(qubits)
            predecessor = last_gate_for_qubit[qubit]
            gate = Gate(
                f"g{layer}",
                "single",
                (qubit,),
                predecessors=((predecessor,) if predecessor is not None else ()),
            )
            last_gate_for_qubit[qubit] = gate.gate_id
        gates.append(gate)
    return CircuitDAG.from_gates(gates)
