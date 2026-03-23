from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

from qdc_project.model.state import SimulationState


def write_text_gantt(path: Path, state: SimulationState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["gate_id,start,end"]
    for gate_id in sorted(state.gate_start_times):
        lines.append(f"{gate_id},{state.gate_start_times[gate_id]},{state.gate_end_times[gate_id]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def iter_gate_bars(state: SimulationState) -> Iterable[Tuple[str, int, int]]:
    for gate_id in sorted(state.gate_start_times):
        yield gate_id, state.gate_start_times[gate_id], state.gate_end_times[gate_id]
