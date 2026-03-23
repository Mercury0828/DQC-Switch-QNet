from __future__ import annotations

from pathlib import Path

from qdc_project.algorithms.placement_greedy import RackAwareGreedyPlacer
from qdc_project.algorithms.scheduler_unified import UnifiedSchedulerConfig
from qdc_project.circuit.synthetic_generators import generate_synthetic_workload
from qdc_project.plotting.barplots import write_markdown_table
from qdc_project.plotting.heatmaps import write_heatmap_data, write_heatmap_svg
from qdc_project.simulation.engine import SimulationEngine
from qdc_project.simulation.logger import SimulationLogger
from qdc_project.topology.qdc_topology import QDCTopology, TopologyConfig


def main() -> None:
    logger = SimulationLogger()
    rows = []
    for qubits in (6, 8, 10, 12):
        topology = QDCTopology(TopologyConfig(3, 2, max(6, qubits), 2, 3, 2, 7, 3))
        dag = generate_synthetic_workload(qubits, depth=qubits * 3, two_qubit_probability=0.7, seed=qubits)
        placement = RackAwareGreedyPlacer().place(dag, topology)
        state = SimulationEngine(topology).run_unified(dag, placement, UnifiedSchedulerConfig())
        row = logger.to_row(f'scale_{qubits}', state)
        row['qubits'] = qubits
        row['depth'] = qubits * 3
        rows.append(row)
    out = Path('outputs/scaling/scaling_summary.csv')
    logger.write_csv(out, rows)
    write_markdown_table(Path('outputs/scaling/scaling_summary.md'), rows, columns=['qubits', 'depth', 'runtime', 'objective_value', 'solver_time_seconds'])
    write_heatmap_data(Path('outputs/scaling/scaling_heatmap.csv'), rows)
    write_heatmap_svg(Path('outputs/scaling/scaling_runtime.svg'), rows, 'qubits', 'depth', 'runtime', 'Scaling runtime heatmap')
    print(f'Scaling outputs written to {out}')


if __name__ == '__main__':
    main()
