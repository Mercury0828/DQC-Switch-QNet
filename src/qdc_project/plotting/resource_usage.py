from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from qdc_project.model.state import SimulationState



def _build_step_series(state: SimulationState) -> List[Tuple[float, int]]:
    changes: Dict[float, int] = {}
    for event in state.event_log:
        if event.event_type in {'cross_rack_generation', 'intra_rack_generation'}:
            changes[event.end_time] = changes.get(event.end_time, 0) + 2
        elif event.event_type in {'consume_epr'}:
            changes[event.start_time] = changes.get(event.start_time, 0) - 2
        elif event.event_type == 'distillation':
            changes[event.start_time] = changes.get(event.start_time, 0) - 2
            changes[event.end_time] = changes.get(event.end_time, 0) + 2
    occupancy = 0
    series = [(1.0, 0)]
    sorted_times = sorted(changes)
    slot_map = {t: idx + 1 for idx, t in enumerate(sorted_times)}
    for t in sorted_times:
        slot = float(slot_map[t])
        series.append((slot, occupancy))
        occupancy += changes[t]
        series.append((slot, occupancy))
    if series:
        series.append((max(p[0] for p in series) + 1, 0))
    return series


def write_resource_usage_svg(path: Path, state: SimulationState, title: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    series = _build_step_series(state)
    width, height = 760, 560
    left, top, plot_w, plot_h = 90, 70, 560, 390
    capacity = sum(qpu.buffer_qubits for qpu in state.topology.qpus.values())
    peak = max((v for _, v in series), default=0)
    avg = sum(v for _, v in series) / max(1, len(series))
    title = title or 'Communication Qubits Utilization Over Time'
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>text { font-family: Arial, Helvetica, sans-serif; font-size: 12px; } .title { font-size: 18px; } .label { font-size: 14px; }</style>',
        f'<text class="title" x="{width/2}" y="35" text-anchor="middle">{title}</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="white" stroke="#333" />',
    ]
    for i in range(1, 5):
        x = left + plot_w * i / 5
        y = top + plot_h * i / 5
        parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+plot_h}" stroke="#e6e6e6" />')
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" stroke="#eeeeee" />')
    max_slot = max((t for t, _ in series), default=5)
    max_pct = 100.0
    avg_pct = (avg / max(capacity, 1)) * 100.0
    points = []
    fill_points = [f'{left},{top+plot_h}']
    for t, v in series:
        x = left + ((t - 1) / max(max_slot - 1, 1)) * plot_w
        pct = (v / max(capacity, 1)) * 100.0
        y = top + plot_h - (pct / max_pct) * plot_h
        points.append(f'{x:.1f},{y:.1f}')
        fill_points.append(f'{x:.1f},{y:.1f}')
    fill_points.append(f'{left+plot_w},{top+plot_h}')
    parts.append(f'<polygon points="{" ".join(fill_points)}" fill="#9bbad0" opacity="0.85" />')
    parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="#0a27ff" stroke-width="2.5" />')
    avg_y = top + plot_h - (avg_pct / max_pct) * plot_h
    parts.append(f'<line x1="{left}" y1="{avg_y:.1f}" x2="{left+plot_w}" y2="{avg_y:.1f}" stroke="#ff6666" stroke-width="1.5" stroke-dasharray="6,4" />')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left+plot_w}" y2="{top}" stroke="#f4c061" stroke-width="1.2" stroke-dasharray="3,4" />')
    parts.append(f'<text x="{left+plot_w-140}" y="{top+22}" class="label">Avg: {avg_pct:.1f}%</text>')
    parts.append(f'<text x="{left+plot_w-140}" y="{top+44}" class="label">Max: 100.0%</text>')
    box_x, box_y = left + plot_w - 230, top + 110
    parts.append(f'<rect x="{box_x}" y="{box_y}" width="190" height="94" rx="6" fill="#f7ecd2" stroke="#8a7d63" />')
    parts.append(f'<text x="{box_x+12}" y="{box_y+26}" class="label">Total EPR Capacity: {capacity}</text>')
    parts.append(f'<text x="{box_x+12}" y="{box_y+50}" class="label">Peak Occupied: {peak}</text>')
    parts.append(f'<text x="{box_x+12}" y="{box_y+74}" class="label">Avg Occupied: {avg:.1f}</text>')
    for i in range(6):
        pct = i * 20
        y = top + plot_h - (pct / 100.0) * plot_h
        parts.append(f'<text x="{left-14}" y="{y+4:.1f}" text-anchor="end" class="label">{pct}</text>')
    for slot in range(1, int(max_slot) + 1):
        x = left + ((slot - 1) / max(max_slot - 1, 1)) * plot_w
        parts.append(f'<text x="{x:.1f}" y="{top+plot_h+26}" text-anchor="middle" class="label">{slot}</text>')
    parts.append(f'<text x="{width/2}" y="{top+plot_h+55}" text-anchor="middle" class="label">Time Slot</text>')
    parts.append(f'<text x="28" y="{top+plot_h/2}" transform="rotate(-90 28,{top+plot_h/2})" text-anchor="middle" class="label">EPR Utilization Ratio (%)</text>')
    parts.append('</svg>')
    path.write_text('\n'.join(parts), encoding='utf-8')
