from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping, Sequence


def write_barplot_data(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_table(path: Path, rows: Sequence[Mapping[str, object]], columns: Sequence[str] | None = None) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = list(rows[0].keys())
    lines = [
        '| ' + ' | '.join(columns) + ' |',
        '| ' + ' | '.join(['---'] * len(columns)) + ' |',
    ]
    for row in rows:
        lines.append('| ' + ' | '.join(str(row.get(column, '')) for column in columns) + ' |')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_barplot_svg(
    path: Path,
    rows: Sequence[Mapping[str, object]],
    label_key: str,
    value_key: str,
    title: str,
    width: int = 900,
    height: int = 420,
) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    values = [float(row[value_key]) for row in rows]
    labels = [str(row[label_key]) for row in rows]
    max_value = max(values) if max(values) > 0 else 1.0
    margin_left, margin_right, margin_top, margin_bottom = 90, 30, 60, 120
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    bar_width = plot_width / max(1, len(rows))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>text { font-family: monospace; font-size: 12px; } .title { font-size: 18px; font-weight: bold; }</style>',
        f'<text class="title" x="{width/2}" y="30" text-anchor="middle">{title}</text>',
        f'<line x1="{margin_left}" y1="{height-margin_bottom}" x2="{width-margin_right}" y2="{height-margin_bottom}" stroke="black" />',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height-margin_bottom}" stroke="black" />',
    ]
    for idx, (label, value) in enumerate(zip(labels, values)):
        x = margin_left + idx * bar_width + 10
        bar_h = 0 if max_value == 0 else (value / max_value) * plot_height
        y = height - margin_bottom - bar_h
        color = ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F', '#EDC948'][idx % 6]
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(10, bar_width-20):.1f}" height="{bar_h:.1f}" fill="{color}" />')
        parts.append(f'<text x="{x + (bar_width-20)/2:.1f}" y="{height-margin_bottom+16}" text-anchor="end" transform="rotate(-35 {x + (bar_width-20)/2:.1f},{height-margin_bottom+16})">{label}</text>')
        parts.append(f'<text x="{x + (bar_width-20)/2:.1f}" y="{max(margin_top+12, y-6):.1f}" text-anchor="middle">{value:.2f}</text>')
    for tick in range(5):
        frac = tick / 4 if 4 else 0
        value = max_value * frac
        y = height - margin_bottom - plot_height * frac
        parts.append(f'<line x1="{margin_left-5}" y1="{y:.1f}" x2="{margin_left}" y2="{y:.1f}" stroke="black" />')
        parts.append(f'<text x="{margin_left-10}" y="{y+4:.1f}" text-anchor="end">{value:.1f}</text>')
    parts.append('</svg>')
    path.write_text('\n'.join(parts), encoding='utf-8')
