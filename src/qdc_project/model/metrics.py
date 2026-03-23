from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class SimulationMetrics:
    runtime: int = 0
    objective_value: int = 0
    latency_breakdown: Dict[str, int] = field(
        default_factory=lambda: {
            "local_gate": 0,
            "intra_rack_epr": 0,
            "cross_rack_epr": 0,
            "switch_reconfiguration": 0,
            "wait_time": 0,
            "retry_overhead_hook": 0,
        }
    )
    epr_counts: Dict[str, int] = field(
        default_factory=lambda: {"intra_rack": 0, "cross_rack": 0, "distilled": 0}
    )
    peak_buffer_occupancy: int = 0
    average_buffer_occupancy: float = 0.0
    average_epr_wait_time: float = 0.0
    split_ratio: float = 0.0

    def finalize(self) -> None:
        self.objective_value = self.runtime + self.latency_breakdown["switch_reconfiguration"]
