from __future__ import annotations

from pathlib import Path

from qdc_project.topology.library import TopologyProfile


def write_topology_svg(path: Path, profile: TopologyProfile) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width = 240 + profile.qpus_per_rack * 150
    height = 120 + profile.racks * 100
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>text { font-family: monospace; font-size: 13px; } .title { font-size: 18px; font-weight: bold; }</style>',
        f'<text class="title" x="{width/2}" y="30" text-anchor="middle">Topology: {profile.name}</text>',
    ]
    if profile.style in {'clos', 'spine_leaf', 'fat_tree'}:
        core_x = width - 120
        parts.append(f'<rect x="{core_x}" y="55" width="80" height="{profile.racks*80}" fill="#dddddd" stroke="#333" />')
        parts.append(f'<text x="{core_x+40}" y="75" text-anchor="middle">switch fabric</text>')
    for rack in range(profile.racks):
        y = 70 + rack * 90
        parts.append(f'<rect x="30" y="{y}" width="{160 + profile.qpus_per_rack*120}" height="55" fill="#f7f7f7" stroke="#555" rx="8" />')
        parts.append(f'<text x="50" y="{y+20}">rack_{rack}</text>')
        for qpu in range(profile.qpus_per_rack):
            x = 110 + qpu * 120
            parts.append(f'<rect x="{x}" y="{y+10}" width="90" height="28" fill="#4E79A7" opacity="0.85" />')
            parts.append(f'<text x="{x+45}" y="{y+28}" text-anchor="middle" fill="white">qpu_{qpu}</text>')
            if profile.style in {'clos', 'spine_leaf', 'fat_tree'}:
                parts.append(f'<line x1="{x+90}" y1="{y+24}" x2="{core_x}" y2="{95 + rack*80}" stroke="#999" />')
    parts.append('</svg>')
    path.write_text('\n'.join(parts), encoding='utf-8')
