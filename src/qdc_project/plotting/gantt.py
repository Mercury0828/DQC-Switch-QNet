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


def write_gantt_svg(path: Path, state: SimulationState, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    events = sorted(state.event_log, key=lambda item: (item.start_time, item.event_type, item.detail))
    if not events:
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="120"></svg>', encoding='utf-8')
        return
    width = 1100
    row_h = 26
    margin_left = 170
    margin_top = 60
    max_time = max(event.end_time for event in events) or 1
    height = margin_top + row_h * len(events) + 60
    colors = {
        'gate': '#4E79A7',
        'cross_rack_generation': '#E15759',
        'intra_rack_generation': '#59A14F',
        'distillation': '#B07AA1',
        'split_completion': '#F28E2B',
        'consume_epr': '#9C755F',
        'collective_batch': '#76B7B2',
    }
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>text { font-family: monospace; font-size: 12px; } .title { font-size: 18px; font-weight: bold; }</style>',
        f'<text class="title" x="{width/2}" y="28" text-anchor="middle">{title}</text>',
    ]
    plot_w = width - margin_left - 40
    for idx, event in enumerate(events):
        y = margin_top + idx * row_h
        x = margin_left + plot_w * (event.start_time / max_time)
        w = max(4, plot_w * ((event.end_time - event.start_time) / max_time))
        parts.append(f'<text x="{margin_left - 10}" y="{y + 15}" text-anchor="end">{event.event_type}:{event.detail}</text>')
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="16" fill="{colors.get(event.event_type, "#BAB0AC")}" />')
    for tick in range(6):
        t = max_time * tick / 5
        x = margin_left + plot_w * (tick / 5)
        parts.append(f'<line x1="{x:.1f}" y1="{margin_top-8}" x2="{x:.1f}" y2="{height-30}" stroke="#cccccc" />')
        parts.append(f'<text x="{x:.1f}" y="{height-10}" text-anchor="middle">{t:.1f}</text>')
    parts.append('</svg>')
    path.write_text('\n'.join(parts), encoding='utf-8')


def iter_gate_bars(state: SimulationState) -> Iterable[Tuple[str, int, int]]:
    for gate_id in sorted(state.gate_start_times):
        yield gate_id, state.gate_start_times[gate_id], state.gate_end_times[gate_id]
