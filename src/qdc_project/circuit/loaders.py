from __future__ import annotations

from typing import List

from qdc_project.circuit.dag_utils import CircuitDAG, Gate


class QiskitUnavailableError(RuntimeError):
    pass


def load_qiskit_circuit_dag(_name: str) -> CircuitDAG:
    """Hook for later benchmark loading from Qiskit. Kept explicit for phased delivery."""

    try:
        import qiskit  # noqa: F401
    except ModuleNotFoundError as exc:
        raise QiskitUnavailableError(
            "Qiskit is not installed in this environment. Use synthetic workloads for now."
        ) from exc
    raise NotImplementedError("Qiskit benchmark conversion is planned for a later phase.")


def load_handcrafted_representative() -> CircuitDAG:
    gates: List[Gate] = [
        Gate("g0", "h", ("q0",)),
        Gate("g1", "cx", ("q0", "q1"), predecessors=("g0",)),
        Gate("g2", "cx", ("q1", "q2"), predecessors=("g1",)),
        Gate("g3", "x", ("q2",), predecessors=("g2",)),
        Gate("g4", "cx", ("q0", "q3"), predecessors=("g1",)),
        Gate("g5", "measure", ("q2",), predecessors=("g3", "g4")),
    ]
    return CircuitDAG.from_gates(gates)
