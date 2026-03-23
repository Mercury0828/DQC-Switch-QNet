from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict

from qdc_project.model.state import SimulationState


class SimulationLogger:
    def to_row(self, name: str, state: SimulationState) -> Dict[str, float]:
        metrics = state.metrics
        row: Dict[str, float] = {
            "name": name,
            "runtime": metrics.runtime,
            "objective_value": metrics.objective_value,
            "solver_time_seconds": metrics.solver_time_seconds,
            "intra_rack_epr": metrics.epr_counts["intra_rack"],
            "cross_rack_epr": metrics.epr_counts["cross_rack"],
            "distilled_epr": metrics.epr_counts["distilled"],
            "split_consumed": metrics.epr_counts["split_consumed"],
            "batched_epr": metrics.epr_counts["batched"],
            "collective_batches": metrics.collective_batches,
            "avg_epr_wait": metrics.average_epr_wait_time,
            "peak_buffer": metrics.peak_buffer_occupancy,
            "avg_buffer": metrics.average_buffer_occupancy,
            "wait_time": metrics.latency_breakdown["wait_time"],
            "switch_reconfiguration": metrics.latency_breakdown["switch_reconfiguration"],
            "retry_overhead_hook": metrics.latency_breakdown["retry_overhead_hook"],
            "split_ratio": metrics.split_ratio,
        }
        for key, value in metrics.latency_breakdown.items():
            row[f"latency_{key}"] = value
        return row

    def write_csv(self, path: Path, rows: list[Dict[str, float]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
