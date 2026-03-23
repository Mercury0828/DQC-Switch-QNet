from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Mapping, Sequence, Tuple

from qdc_project.model.state import SimulationState
from qdc_project.plotting.resource_usage import _build_step_series
from qdc_project.topology.library import TopologyProfile

FONT = 'font-family: Arial, Helvetica, sans-serif;'


def _header(width: int, height: int, title: str) -> List[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'<style>text {{{FONT} font-size: 12px;}} .title {{{FONT} font-size: 16px; font-weight: bold;}} .subtitle {{{FONT} font-size: 13px; font-weight: bold;}}</style>',
        f'<text class="title" x="{width/2}" y="24" text-anchor="middle">{title}</text>',
    ]


def _footer(parts: List[str], path: Path) -> None:
    parts.append('</svg>')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(parts), encoding='utf-8')


def _axes(parts: List[str], x: float, y: float, w: float, h: float, xlabel: str, ylabel: str, title: str) -> None:
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white" stroke="#333" />')
    for i in range(1, 5):
        gy = y + h * i / 5
        parts.append(f'<line x1="{x}" y1="{gy:.1f}" x2="{x+w}" y2="{gy:.1f}" stroke="#e5e5e5" />')
    parts.append(f'<text class="subtitle" x="{x+w/2}" y="{y-8}" text-anchor="middle">{title}</text>')
    parts.append(f'<text x="{x+w/2}" y="{y+h+28}" text-anchor="middle">{xlabel}</text>')
    parts.append(f'<text x="{x-42}" y="{y+h/2}" transform="rotate(-90 {x-42},{y+h/2})" text-anchor="middle">{ylabel}</text>')


def _line_chart(parts: List[str], rect: Tuple[float, float, float, float], series: Sequence[Tuple[str, Sequence[Tuple[float, float]], str]], xlabel: str, ylabel: str, title: str) -> None:
    x, y, w, h = rect
    _axes(parts, x, y, w, h, xlabel, ylabel, title)
    all_x = [p[0] for _, pts, _ in series for p in pts] or [0.0]
    all_y = [p[1] for _, pts, _ in series for p in pts] or [0.0]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    if max_x == min_x:
        max_x += 1
    if max_y == min_y:
        max_y += 1
    legend_x = x + w - 120
    legend_y = y + 10
    for idx, (name, pts, color) in enumerate(series):
        coords = []
        for px, py in pts:
            sx = x + (px - min_x) / (max_x - min_x) * w
            sy = y + h - (py - min_y) / (max_y - min_y) * h
            coords.append(f'{sx:.1f},{sy:.1f}')
            parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="3" fill="{color}" />')
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{" ".join(coords)}" />')
        ly = legend_y + idx * 18
        parts.append(f'<line x1="{legend_x}" y1="{ly}" x2="{legend_x+14}" y2="{ly}" stroke="{color}" stroke-width="2" />')
        parts.append(f'<text x="{legend_x+20}" y="{ly+4}">{name}</text>')


def _grouped_bars(parts: List[str], rect: Tuple[float, float, float, float], categories: Sequence[str], series: Sequence[Tuple[str, Sequence[float], str]], xlabel: str, ylabel: str, title: str) -> None:
    x, y, w, h = rect
    _axes(parts, x, y, w, h, xlabel, ylabel, title)
    max_y = max((max(vals) for _, vals, _ in series if vals), default=1.0)
    group_w = w / max(1, len(categories))
    bar_w = group_w / max(1, len(series) + 1)
    for c_idx, category in enumerate(categories):
        cx = x + c_idx * group_w
        parts.append(f'<text x="{cx + group_w/2}" y="{y+h+14}" text-anchor="middle">{category}</text>')
        for s_idx, (_, vals, color) in enumerate(series):
            val = vals[c_idx]
            bh = (val / max_y) * (h * 0.9)
            bx = cx + bar_w * (s_idx + 0.4)
            by = y + h - bh
            parts.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w*0.8:.1f}" height="{bh:.1f}" fill="{color}" />')
    lx = x + w - 140
    ly = y + 12
    for idx, (name, _, color) in enumerate(series):
        yy = ly + idx * 18
        parts.append(f'<rect x="{lx}" y="{yy-8}" width="12" height="12" fill="{color}" />')
        parts.append(f'<text x="{lx+18}" y="{yy+2}">{name}</text>')


def _table(parts: List[str], rect: Tuple[float, float, float, float], columns: Sequence[str], rows: Sequence[Sequence[str]], title: str) -> None:
    x, y, w, h = rect
    parts.append(f'<text class="subtitle" x="{x+w/2}" y="{y-8}" text-anchor="middle">{title}</text>')
    ncols = len(columns)
    nrows = len(rows) + 1
    cell_w = w / ncols
    cell_h = h / nrows
    for r in range(nrows):
        for c in range(ncols):
            cx, cy = x + c * cell_w, y + r * cell_h
            fill = '#f3f3f3' if r == 0 else 'white'
            parts.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" fill="{fill}" stroke="#333" />')
            text = columns[c] if r == 0 else rows[r-1][c]
            parts.append(f'<text x="{cx+cell_w/2:.1f}" y="{cy+cell_h/2+4:.1f}" text-anchor="middle">{text}</text>')


def create_representative_figure(path: Path, state: SimulationState) -> None:
    width, height = 1200, 420
    parts = _header(width, height, 'Fig. 8 style: Representative switch-networked QDC example')
    left = (50, 60, 520, 300)
    right = (640, 60, 500, 300)
    _axes(parts, *left, 'Time', 'Event index', 'Scheduling / communication timeline')
    events = sorted(state.event_log, key=lambda e: (e.start_time, e.event_type, e.detail))
    max_t = max((e.end_time for e in events), default=1)
    colors = {'gate': '#e74c3c', 'cross_rack_generation': '#ff7f50', 'intra_rack_generation': '#2e86de', 'distillation': '#8e44ad', 'split_completion': '#f39c12', 'consume_epr': '#16a085'}
    for idx, event in enumerate(events[:18]):
        ex = left[0] + (event.start_time / max_t) * left[2]
        ew = max(4, ((event.end_time - event.start_time) / max_t) * left[2])
        ey = left[1] + left[3] - (idx + 1) * (left[3] / 20)
        parts.append(f'<rect x="{ex:.1f}" y="{ey:.1f}" width="{ew:.1f}" height="10" fill="{colors.get(event.event_type, "#999")}" />')
    series = _build_step_series(state)
    _line_chart(parts, right, [('EPR occupancy', series, '#2e86de')], 'Time', 'Occupancy', 'Communication / EPR usage over time')
    _footer(parts, path)


def create_algorithm_figure(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    width, height = 1200, 420
    parts = _header(width, height, 'Fig. 9 style: Algorithm-level comparison across workload scales')
    scales = ['small', 'medium', 'large', 'very_large']
    methods = [('full_method', '#4E79A7'), ('random_direct', '#F28E2B'), ('stagewise_direct', '#59A14F')]
    obj_series = []
    time_series = []
    for method, color in methods:
        obj_vals, time_vals = [], []
        for scale in scales:
            match = next(row for row in rows if row['scale'] == scale and row['method'] == method)
            obj_vals.append(float(match['objective_value']))
            time_vals.append(float(match['solver_time_seconds']) + 1e-6)
        obj_series.append((method, obj_vals, color))
        time_series.append((method, time_vals, color))
    _grouped_bars(parts, (50, 70, 500, 280), scales, obj_series, 'Problem scale', 'Objective', 'Objective value comparison')
    _grouped_bars(parts, (640, 70, 500, 280), scales, time_series, 'Problem scale', 'Compilation time (s)', 'Algorithm execution time comparison')
    _footer(parts, path)


def create_sensitivity_figure(path: Path, family_to_rows: Mapping[str, Sequence[Mapping[str, object]]]) -> None:
    width, height = 1200, 900
    parts = _header(width, height, 'Fig. 10 style: Resource sensitivity across benchmark families')
    rects = [(50, 60, 500, 320), (640, 60, 500, 320), (50, 470, 500, 320), (640, 470, 500, 320)]
    colors = {'full_method': '#4E79A7', 'random_direct': '#F28E2B', 'stagewise_direct': '#59A14F'}
    for rect, family in zip(rects, ['mct', 'qft', 'grover', 'rca']):
        rows = family_to_rows[family]
        grouped = {}
        for method in ['full_method', 'random_direct', 'stagewise_direct']:
            pts = sorted((float(r['comm_qubits']), float(r['objective_value'])) for r in rows if r['method'] == method)
            grouped[method] = pts
        _line_chart(parts, rect, [(m, grouped[m], colors[m]) for m in grouped], 'Communication qubits per QPU', 'Objective', f'{family.upper()} family')
    _footer(parts, path)


def _topology_shape(parts: List[str], profile: TopologyProfile, ox: float, oy: float, label: str) -> None:
    parts.append(f'<text class="subtitle" x="{ox+150}" y="{oy-10}" text-anchor="middle">{label}</text>')
    core_x = ox + 240
    parts.append(f'<rect x="{core_x}" y="{oy+30}" width="50" height="{profile.racks*38}" fill="#dddddd" stroke="#333" />')
    for rack in range(profile.racks):
        ry = oy + 30 + rack * 42
        parts.append(f'<rect x="{ox}" y="{ry}" width="200" height="28" fill="#f8f8f8" stroke="#555" />')
        parts.append(f'<text x="{ox+12}" y="{ry+18}">rack_{rack}</text>')
        for q in range(profile.qpus_per_rack):
            qx = ox + 70 + q * 40
            parts.append(f'<circle cx="{qx}" cy="{ry+14}" r="7" fill="#4E79A7" />')
            parts.append(f'<line x1="{qx}" y1="{ry+14}" x2="{core_x}" y2="{ry+14}" stroke="#aaa" />')


def create_topology_gallery(path: Path, profiles: Sequence[TopologyProfile]) -> None:
    width, height = 1200, 420
    parts = _header(width, height, 'Fig. 11 style: QDC topology gallery')
    positions = [(40, 70), (390, 70), (740, 70)]
    for (ox, oy), profile in zip(positions, profiles[:3]):
        _topology_shape(parts, profile, ox, oy, profile.name)
    _footer(parts, path)


def create_topology_comparison_figure(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    width, height = 1200, 420
    parts = _header(width, height, 'Fig. 12 style: Comparison across QDC topologies')
    xs = list(range(len(rows)))
    labels = [str(r['topology']) for r in rows]
    obj_pts = list(zip(xs, [float(r['objective_value']) for r in rows]))
    time_pts = list(zip(xs, [float(r['solver_time_seconds']) + 1e-6 for r in rows]))
    _line_chart(parts, (50, 70, 500, 280), [('objective', obj_pts, '#4E79A7')], 'Topology index', 'Objective', 'Objective value across topologies')
    _line_chart(parts, (640, 70, 500, 280), [('runtime', time_pts, '#E15759')], 'Topology index', 'Compilation time (s)', 'Algorithm execution time across topologies')
    for i, label in enumerate(labels):
        x = 50 + (i / max(1, len(labels)-1)) * 500
        parts.append(f'<text x="{x:.1f}" y="368" text-anchor="middle">{label}</text>')
        x2 = 640 + (i / max(1, len(labels)-1)) * 500
        parts.append(f'<text x="{x2:.1f}" y="368" text-anchor="middle">{label}</text>')
    _footer(parts, path)


def create_framework_comparison_figure(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    width, height = 1200, 860
    parts = _header(width, height, 'Fig. 13 style: Framework-level comparison')
    families = ['mct', 'qft', 'grover', 'rca']
    baseline = [next(r for r in rows if r['family'] == fam and r['framework'] == 'stagewise_direct') for fam in families]
    full = [next(r for r in rows if r['family'] == fam and r['framework'] == 'full_framework') for fam in families]
    scatter = list(zip([float(r['objective_value']) for r in baseline], [float(r['objective_value']) for r in full]))
    improvements = [(i, (1 - float(f['objective_value']) / max(float(b['objective_value']), 1e-6)) * 100) for i, (b, f) in enumerate(zip(baseline, full))]
    run_b = [float(r['runtime']) for r in baseline]
    run_f = [float(r['runtime']) for r in full]
    comp_b = [float(r['solver_time_seconds']) + 1e-6 for r in baseline]
    comp_f = [float(r['solver_time_seconds']) + 1e-6 for r in full]
    _line_chart(parts, (50, 70, 500, 300), [('pairs', scatter, '#4E79A7')], 'Baseline objective', 'Our objective', '(a) Objective comparison')
    _line_chart(parts, (640, 70, 500, 300), [('improvement', improvements, '#2E86DE')], 'Benchmark index', 'Improvement (%)', '(b) Performance improvement')
    _grouped_bars(parts, (50, 470, 500, 280), families, [('full_framework', run_f, '#4E79A7'), ('stagewise_direct', run_b, '#F28E2B')], 'Benchmark family', 'Runtime', '(c) Circuit runtime')
    _grouped_bars(parts, (640, 470, 500, 280), families, [('full_framework', comp_f, '#4E79A7'), ('stagewise_direct', comp_b, '#F28E2B')], 'Benchmark family', 'Compile time (s)', '(d) Algorithm execution time')
    _footer(parts, path)


def create_setup_table(path: Path, columns: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    parts = _header(900, 260, 'Evaluation setup')
    _table(parts, (40, 60, 820, 160), columns, rows, 'Workload / architecture settings')
    _footer(parts, path)
