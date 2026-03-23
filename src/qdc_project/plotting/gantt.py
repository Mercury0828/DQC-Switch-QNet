from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from qdc_project.model.state import SimulationState


_BLUE = '#4b4be8'
_RED = '#ff4d4d'


def write_text_gantt(path: Path, state: SimulationState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["kind,label,start,end"]
    for event in sorted(state.event_log, key=lambda item: (item.start_time, item.event_type, item.detail)):
        lines.append(f"{event.event_type},{event.detail},{event.start_time},{event.end_time}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _gate_rows(state: SimulationState) -> List[Tuple[str, int, int, str]]:
    gates = []
    unique_times = sorted(set(state.gate_start_times.values()) | set(state.gate_end_times.values()))
    time_to_slot: Dict[int, int] = {t: idx + 1 for idx, t in enumerate(unique_times)}
    for gate_id in sorted(state.gate_start_times, key=lambda gid: state.gate_start_times[gid]):
        start = time_to_slot[state.gate_start_times[gate_id]]
        end = time_to_slot[state.gate_end_times[gate_id]]
        mode = state.gate_execution_mode.get(gate_id, 'local')
        color = _RED if mode in {'direct', 'split'} else _BLUE
        gates.append((gate_id, start, max(start + 1, end), color))
    return gates


def write_gantt_svg(path: Path, state: SimulationState, title: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    gates = _gate_rows(state)
    width, height = 760, 560
    left, top, plot_w, plot_h = 90, 70, 560, 390
    title = title or 'Complete Gate Scheduling Gantt Chart'
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>text { font-family: Arial, Helvetica, sans-serif; font-size: 12px; } .title { font-size: 18px; } .label { font-size: 14px; }</style>',
        f'<text class="title" x="{width/2}" y="35" text-anchor="middle">{title}</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="white" stroke="#333" />',
    ]
    for i in range(6):
        x = left + plot_w * i / 6
        parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+plot_h}" stroke="#e6e6e6" />')
    for i in range(6):
        y = top + plot_h * i / 5
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" stroke="#eeeeee" />')
    max_slot = max((end for _, _, end, _ in gates), default=5)
    total_gates = len(gates)
    for idx, (_, start, end, color) in enumerate(gates):
        y = top + plot_h - ((idx + 1) / max(total_gates, 1)) * (plot_h - 10)
        x = left + ((start - 0.5) / max(max_slot, 1)) * plot_w
        w = max(8, ((end - start) / max(max_slot, 1)) * plot_w)
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="8" fill="{color}" stroke="#555" stroke-width="0.5" />')
    for slot in range(1, max_slot + 1):
        x = left + ((slot - 0.5) / max(max_slot, 1)) * plot_w
        parts.append(f'<text x="{x:.1f}" y="{top+plot_h+26}" text-anchor="middle" class="label">{slot}</text>')
    for tick in range(0, total_gates + 1, max(1, total_gates // 5 or 1)):
        y = top + plot_h - (tick / max(total_gates, 1)) * (plot_h - 10)
        parts.append(f'<text x="{left-15}" y="{y+4:.1f}" text-anchor="end" class="label">{tick}</text>')
    parts.append(f'<text x="{width/2}" y="{top+plot_h+55}" text-anchor="middle" class="label">Time Slot</text>')
    parts.append(f'<text x="28" y="{top+plot_h/2}" transform="rotate(-90 28,{top+plot_h/2})" text-anchor="middle" class="label">Gate Index</text>')

    same_count = sum(1 for _, _, _, c in gates if c == _BLUE)
    cross_count = sum(1 for _, _, _, c in gates if c == _RED)
    box_x, box_y = left + plot_w - 215, top + plot_h - 170
    parts.append(f'<rect x="{box_x}" y="{box_y}" width="170" height="84" rx="6" fill="#f7ecd2" stroke="#8a7d63" />')
    parts.append(f'<text x="{box_x+14}" y="{box_y+24}" class="label">Total Gates: {total_gates}</text>')
    parts.append(f'<text x="{box_x+14}" y="{box_y+46}" class="label">Cross-QPU: {cross_count}</text>')
    parts.append(f'<text x="{box_x+14}" y="{box_y+68}" class="label">Same-QPU: {same_count}</text>')

    legend_x, legend_y = left + plot_w - 200, top + plot_h - 70
    parts.append(f'<rect x="{legend_x}" y="{legend_y}" width="190" height="56" rx="5" fill="white" stroke="#d0d0d0" />')
    parts.append(f'<rect x="{legend_x+12}" y="{legend_y+12}" width="36" height="12" fill="{_RED}" />')
    parts.append(f'<text x="{legend_x+58}" y="{legend_y+22}" class="label">Cross-QPU Gates</text>')
    parts.append(f'<rect x="{legend_x+12}" y="{legend_y+32}" width="36" height="12" fill="{_BLUE}" />')
    parts.append(f'<text x="{legend_x+58}" y="{legend_y+42}" class="label">Same-QPU Gates</text>')
    parts.append('</svg>')
    path.write_text('\n'.join(parts), encoding='utf-8')



def iter_gate_bars(state: SimulationState) -> Iterable[Tuple[str, int, int]]:
    for gate_id in sorted(state.gate_start_times):
        yield gate_id, state.gate_start_times[gate_id], state.gate_end_times[gate_id]
