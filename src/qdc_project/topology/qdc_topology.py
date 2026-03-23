from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class QPU:
    """Physical QPU with separate data, communication, and EPR buffer capacities."""

    qpu_id: str
    rack_id: str
    data_qubits: int
    comm_qubits: int
    buffer_qubits: int


@dataclass(frozen=True)
class Rack:
    rack_id: str
    qpus: Tuple[QPU, ...]


@dataclass(frozen=True)
class TopologyConfig:
    racks: int
    qpus_per_rack: int
    data_qubits_per_qpu: int
    comm_qubits_per_qpu: int
    buffer_qubits_per_qpu: int
    intra_epr_latency: int
    cross_epr_latency: int
    switch_reconfig_latency: int
    gate_durations: Dict[str, int] = field(default_factory=lambda: {
        "single_qubit": 1,
        "local_cx": 1,
        "remote_cx": 1,
    })


class QDCTopology:
    """Hierarchical QDC topology used by the simulator."""

    def __init__(self, config: TopologyConfig) -> None:
        self.config = config
        self.racks: Dict[str, Rack] = {}
        self.qpus: Dict[str, QPU] = {}
        for rack_index in range(config.racks):
            rack_id = f"rack_{rack_index}"
            qpus: List[QPU] = []
            for qpu_index in range(config.qpus_per_rack):
                qpu_id = f"{rack_id}_qpu_{qpu_index}"
                qpu = QPU(
                    qpu_id=qpu_id,
                    rack_id=rack_id,
                    data_qubits=config.data_qubits_per_qpu,
                    comm_qubits=config.comm_qubits_per_qpu,
                    buffer_qubits=config.buffer_qubits_per_qpu,
                )
                qpus.append(qpu)
                self.qpus[qpu_id] = qpu
            self.racks[rack_id] = Rack(rack_id=rack_id, qpus=tuple(qpus))

    def qpu_ids(self) -> List[str]:
        return list(self.qpus.keys())

    def same_rack(self, qpu_a: str, qpu_b: str) -> bool:
        return self.qpus[qpu_a].rack_id == self.qpus[qpu_b].rack_id

    def epr_latency(self, qpu_a: str, qpu_b: str) -> int:
        if qpu_a == qpu_b:
            return 0
        if self.same_rack(qpu_a, qpu_b):
            return self.config.intra_epr_latency
        return self.config.cross_epr_latency

    def gate_duration(self, gate_name: str, qpu_a: str, qpu_b: str | None = None) -> int:
        if qpu_b is None or qpu_a == qpu_b:
            return self.config.gate_durations.get("single_qubit", 1)
        if self.same_rack(qpu_a, qpu_b):
            return self.config.gate_durations.get("local_cx", 1)
        return self.config.gate_durations.get("remote_cx", 1)

    def rack_qpus(self, rack_id: str) -> Iterable[QPU]:
        return self.racks[rack_id].qpus
