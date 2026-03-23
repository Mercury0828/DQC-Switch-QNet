from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from qdc_project.model.metrics import SimulationMetrics
from qdc_project.topology.qdc_topology import QDCTopology
from qdc_project.topology.switch_model import SwitchState


@dataclass
class EPRRecord:
    pair_id: str
    endpoints: Tuple[str, str]
    generated_at: int
    consumed_at: Optional[int] = None
    kind: str = "cross_rack"


@dataclass
class QPUState:
    busy_until: int = 0
    active_data_qubits: int = 0
    active_comm_qubits: int = 0
    buffer_occupancy: int = 0


@dataclass
class SimulationState:
    topology: QDCTopology
    switch_state: SwitchState
    qpu_state: Dict[str, QPUState] = field(default_factory=dict)
    epr_inventory: Dict[Tuple[str, str], List[EPRRecord]] = field(default_factory=dict)
    executed_gates: Set[str] = field(default_factory=set)
    gate_start_times: Dict[str, int] = field(default_factory=dict)
    gate_end_times: Dict[str, int] = field(default_factory=dict)
    metrics: SimulationMetrics = field(default_factory=SimulationMetrics)
    buffer_occupancy_samples: List[int] = field(default_factory=list)

    @classmethod
    def create(cls, topology: QDCTopology) -> "SimulationState":
        qpu_state = {qpu_id: QPUState() for qpu_id in topology.qpu_ids()}
        return cls(
            topology=topology,
            switch_state=SwitchState(topology.config.switch_reconfig_latency),
            qpu_state=qpu_state,
        )

    def record_buffer_sample(self) -> None:
        total = sum(state.buffer_occupancy for state in self.qpu_state.values())
        self.buffer_occupancy_samples.append(total)
        self.metrics.peak_buffer_occupancy = max(self.metrics.peak_buffer_occupancy, total)

    def finalize_metrics(self) -> None:
        self.metrics.runtime = max(self.gate_end_times.values(), default=0)
        if self.buffer_occupancy_samples:
            self.metrics.average_buffer_occupancy = sum(self.buffer_occupancy_samples) / len(
                self.buffer_occupancy_samples
            )
        waits = [
            record.consumed_at - record.generated_at
            for records in self.epr_inventory.values()
            for record in records
            if record.consumed_at is not None
        ]
        if waits:
            self.metrics.average_epr_wait_time = sum(waits) / len(waits)
        self.metrics.latency_breakdown[
            "switch_reconfiguration"
        ] = self.switch_state.reconfiguration_time_accum
        self.metrics.finalize()
