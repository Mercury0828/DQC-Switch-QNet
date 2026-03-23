from __future__ import annotations

from typing import List

from qdc_project.circuit.dag_utils import CircuitDAG, Gate


def build_mct_family(num_qubits: int, depth: int) -> CircuitDAG:
    gates: List[Gate] = []
    last = {f'q{i}': None for i in range(num_qubits)}
    gid = 0
    for layer in range(depth):
        control = f'q{layer % max(1, num_qubits - 1)}'
        target = f'q{(layer + 1) % num_qubits}'
        preds = tuple(pred for pred in {last[control], last[target]} if pred is not None)
        gate = Gate(f'g{gid}', 'cx', (control, target), predecessors=preds)
        gid += 1
        gates.append(gate)
        last[control] = gate.gate_id
        last[target] = gate.gate_id
    return CircuitDAG.from_gates(gates)


def build_qft_family(num_qubits: int) -> CircuitDAG:
    gates: List[Gate] = []
    last = {f'q{i}': None for i in range(num_qubits)}
    gid = 0
    for i in range(num_qubits):
        q = f'q{i}'
        preds = ((last[q],) if last[q] is not None else ())
        h_gate = Gate(f'g{gid}', 'h', (q,), predecessors=preds)
        gid += 1
        gates.append(h_gate)
        last[q] = h_gate.gate_id
        for j in range(i + 1, num_qubits):
            q2 = f'q{j}'
            preds = tuple(pred for pred in {last[q], last[q2]} if pred is not None)
            gate = Gate(f'g{gid}', 'cx', (q, q2), predecessors=preds)
            gid += 1
            gates.append(gate)
            last[q] = gate.gate_id
            last[q2] = gate.gate_id
    return CircuitDAG.from_gates(gates)


def build_grover_family(num_qubits: int, rounds: int) -> CircuitDAG:
    gates: List[Gate] = []
    last = {f'q{i}': None for i in range(num_qubits)}
    gid = 0
    for _ in range(rounds):
        for i in range(num_qubits):
            q = f'q{i}'
            preds = ((last[q],) if last[q] is not None else ())
            gate = Gate(f'g{gid}', 'h', (q,), predecessors=preds)
            gid += 1
            gates.append(gate)
            last[q] = gate.gate_id
        for i in range(num_qubits - 1):
            q1, q2 = f'q{i}', f'q{i+1}'
            preds = tuple(pred for pred in {last[q1], last[q2]} if pred is not None)
            gate = Gate(f'g{gid}', 'cx', (q1, q2), predecessors=preds)
            gid += 1
            gates.append(gate)
            last[q1] = gate.gate_id
            last[q2] = gate.gate_id
    return CircuitDAG.from_gates(gates)


def build_rca_family(num_qubits: int) -> CircuitDAG:
    gates: List[Gate] = []
    last = {f'q{i}': None for i in range(num_qubits)}
    gid = 0
    for i in range(0, num_qubits - 1, 2):
        qa, qb = f'q{i}', f'q{i+1}'
        preds = tuple(pred for pred in {last[qa], last[qb]} if pred is not None)
        gate = Gate(f'g{gid}', 'cx', (qa, qb), predecessors=preds)
        gid += 1
        gates.append(gate)
        last[qa] = gate.gate_id
        last[qb] = gate.gate_id
        if i + 2 < num_qubits:
            qc = f'q{i+2}'
            preds = tuple(pred for pred in {last[qb], last[qc]} if pred is not None)
            gate = Gate(f'g{gid}', 'cx', (qb, qc), predecessors=preds)
            gid += 1
            gates.append(gate)
            last[qb] = gate.gate_id
            last[qc] = gate.gate_id
    return CircuitDAG.from_gates(gates)


def build_named_family(name: str, scale: str) -> CircuitDAG:
    scale_map = {
        'small': 6,
        'medium': 8,
        'large': 10,
        'very_large': 12,
    }
    n = scale_map.get(scale, 8)
    if name == 'mct':
        return build_mct_family(n, depth=n * 2)
    if name == 'qft':
        return build_qft_family(n)
    if name == 'grover':
        return build_grover_family(n, rounds=max(2, n // 3))
    if name == 'rca':
        return build_rca_family(n)
    raise ValueError(f'Unknown benchmark family: {name}')
