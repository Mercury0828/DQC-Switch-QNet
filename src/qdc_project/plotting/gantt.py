from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

from qdc_project.model.state import SimulationState


def write_text_gantt(path: Path, state: SimulationState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["kind,label,start,end"]
    for event in sorted(state.event_log, key=lambda item: (item.start_time, item.event_type, item.detail)):
        lines.append(f"{event.event_type},{event.detail},{event.start_time},{event.end_time}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def iter_gate_bars(state: SimulationState) -> Iterable[Tuple[str, int, int]]:
    for gate_id in sorted(state.gate_start_times):
        yield gate_id, state.gate_start_times[gate_id], state.gate_end_times[gate_id]
