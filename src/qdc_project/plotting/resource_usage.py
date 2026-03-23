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
    series = [(0.0, 0)]
    for t in sorted(changes):
        series.append((t, occupancy))
        occupancy += changes[t]
        series.append((t, occupancy))
    return series


def write_resource_usage_svg(path: Path, state: SimulationState, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    series = _build_step_series(state)
    width, height = 900, 320
    margin_left, margin_right, margin_top, margin_bottom = 70, 30, 50, 50
    max_t = max(t for t, _ in series) or 1.0
    max_y = max(v for _, v in series) or 1
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    pts = []
    for t, v in series:
        x = margin_left + plot_w * (t / max_t)
        y = height - margin_bottom - plot_h * (v / max_y if max_y else 0)
        pts.append(f'{x:.1f},{y:.1f}')
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>text { font-family: monospace; font-size: 12px; } .title { font-size: 18px; font-weight: bold; }</style>',
        f'<text class="title" x="{width/2}" y="28" text-anchor="middle">{title}</text>',
        f'<line x1="{margin_left}" y1="{height-margin_bottom}" x2="{width-margin_right}" y2="{height-margin_bottom}" stroke="black" />',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height-margin_bottom}" stroke="black" />',
        f'<polyline fill="none" stroke="#E15759" stroke-width="3" points="{" ".join(pts)}" />',
        f'<text x="{width/2}" y="{height-10}" text-anchor="middle">time</text>',
        f'<text x="20" y="{height/2}" transform="rotate(-90 20,{height/2})" text-anchor="middle">EPR / communication occupancy</text>',
    ]
    for tick in range(5):
        frac = tick / 4
        y = height - margin_bottom - plot_h * frac
        value = max_y * frac
        parts.append(f'<text x="{margin_left-10}" y="{y+4:.1f}" text-anchor="end">{value:.1f}</text>')
    parts.append('</svg>')
    path.write_text('\n'.join(parts), encoding='utf-8')
