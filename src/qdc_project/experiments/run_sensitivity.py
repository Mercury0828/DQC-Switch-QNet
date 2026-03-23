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
    dag = generate_synthetic_workload(8, 24, 0.75, seed=101)
    logger = SimulationLogger()
    rows = []
    for buffer_qubits in (1, 2, 3, 4):
        for comm_qubits in (1, 2, 3):
            topology = QDCTopology(TopologyConfig(3, 2, 6, comm_qubits, buffer_qubits, 2, 7, 3))
            placement = RackAwareGreedyPlacer().place(dag, topology)
            state = SimulationEngine(topology).run_unified(dag, placement, UnifiedSchedulerConfig())
            row = logger.to_row(f'buf_{buffer_qubits}_comm_{comm_qubits}', state)
            row['buffer_qubits'] = buffer_qubits
            row['comm_qubits'] = comm_qubits
            rows.append(row)
    out = Path('outputs/sensitivity/sensitivity_summary.csv')
    logger.write_csv(out, rows)
    write_markdown_table(Path('outputs/sensitivity/sensitivity_summary.md'), rows, columns=['buffer_qubits', 'comm_qubits', 'runtime', 'objective_value', 'peak_buffer'])
    write_heatmap_data(Path('outputs/sensitivity/sensitivity_heatmap.csv'), rows)
    write_heatmap_svg(Path('outputs/sensitivity/sensitivity_runtime.svg'), rows, 'comm_qubits', 'buffer_qubits', 'runtime', 'Sensitivity runtime heatmap')
    print(f'Sensitivity outputs written to {out}')


if __name__ == '__main__':
    main()
