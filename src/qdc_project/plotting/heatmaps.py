from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping, Sequence


def write_heatmap_data(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_heatmap_svg(
    path: Path,
    rows: Sequence[Mapping[str, object]],
    x_key: str,
    y_key: str,
    value_key: str,
    title: str,
    width: int = 860,
    height: int = 480,
) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    xs = sorted({str(row[x_key]) for row in rows})
    ys = sorted({str(row[y_key]) for row in rows})
    value_map = {(str(row[x_key]), str(row[y_key])): float(row[value_key]) for row in rows}
    values = list(value_map.values()) or [0.0]
    min_v, max_v = min(values), max(values)
    margin_left, margin_top = 100, 70
    cell_w = max(70, (width - margin_left - 40) / max(1, len(xs)))
    cell_h = max(50, (height - margin_top - 60) / max(1, len(ys)))

    def color(value: float) -> str:
        frac = 0.5 if max_v == min_v else (value - min_v) / (max_v - min_v)
        r = int(20 + frac * 200)
        g = int(60 + (1 - frac) * 120)
        b = int(220 - frac * 140)
        return f'#{r:02x}{g:02x}{b:02x}'

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>text { font-family: monospace; font-size: 12px; } .title { font-size: 18px; font-weight: bold; }</style>',
        f'<text class="title" x="{width/2}" y="30" text-anchor="middle">{title}</text>',
    ]
    for i, x in enumerate(xs):
        parts.append(f'<text x="{margin_left + i*cell_w + cell_w/2:.1f}" y="{margin_top - 12}" text-anchor="middle">{x}</text>')
    for j, y in enumerate(ys):
        parts.append(f'<text x="{margin_left - 10}" y="{margin_top + j*cell_h + cell_h/2:.1f}" text-anchor="end">{y}</text>')
        for i, x in enumerate(xs):
            value = value_map.get((x, y), 0.0)
            fill = color(value)
            rect_x = margin_left + i * cell_w
            rect_y = margin_top + j * cell_h
            parts.append(f'<rect x="{rect_x:.1f}" y="{rect_y:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" fill="{fill}" stroke="#ffffff" />')
            parts.append(f'<text x="{rect_x + cell_w/2:.1f}" y="{rect_y + cell_h/2 + 4:.1f}" text-anchor="middle">{value:.2f}</text>')
    parts.append('</svg>')
    path.write_text('\n'.join(parts), encoding='utf-8')
