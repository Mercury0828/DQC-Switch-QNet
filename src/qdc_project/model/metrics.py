from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class SimulationMetrics:
    runtime: int = 0
    objective_value: float = 0.0
    latency_breakdown: Dict[str, float] = field(
        default_factory=lambda: {
            "local_gate": 0.0,
            "intra_rack_epr": 0.0,
            "cross_rack_epr": 0.0,
            "switch_reconfiguration": 0.0,
            "wait_time": 0.0,
            "retry_overhead_hook": 0.0,
            "distillation": 0.0,
        }
    )
    epr_counts: Dict[str, int] = field(
        default_factory=lambda: {
            "intra_rack": 0,
            "cross_rack": 0,
            "distilled": 0,
            "split_consumed": 0,
            "batched": 0,
        }
    )
    peak_buffer_occupancy: int = 0
    average_buffer_occupancy: float = 0.0
    average_epr_wait_time: float = 0.0
    split_ratio: float = 0.0
    remote_gate_count: int = 0
    split_gate_count: int = 0
    collective_batches: int = 0
    solver_time_seconds: float = 0.0

    def finalize(self) -> None:
        penalty = (
            self.latency_breakdown["switch_reconfiguration"]
            + self.latency_breakdown["retry_overhead_hook"]
            + self.latency_breakdown["distillation"]
        )
        self.objective_value = self.runtime + penalty
        if self.remote_gate_count:
            self.split_ratio = self.split_gate_count / self.remote_gate_count
