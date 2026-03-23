from __future__ import annotations

from pathlib import Path

from qdc_project.algorithms.placement_greedy import RackAwareGreedyPlacer
from qdc_project.algorithms.scheduler_unified import UnifiedSchedulerConfig
from qdc_project.circuit.synthetic_generators import generate_synthetic_workload
from qdc_project.plotting.heatmaps import write_heatmap_data
from qdc_project.simulation.engine import SimulationEngine
from qdc_project.simulation.logger import SimulationLogger
from qdc_project.topology.qdc_topology import QDCTopology, TopologyConfig


def main() -> None:
    dag = generate_synthetic_workload(6, 12, 0.75, seed=101)
    logger = SimulationLogger()
    rows = []
    for buffer_qubits in (1, 2, 3):
        for comm_qubits in (1, 2):
            topology = QDCTopology(TopologyConfig(2, 2, 4, comm_qubits, buffer_qubits, 2, 7, 3))
            placement = RackAwareGreedyPlacer().place(dag, topology)
            state = SimulationEngine(topology).run_unified(dag, placement, UnifiedSchedulerConfig())
            row = logger.to_row(f'buf_{buffer_qubits}_comm_{comm_qubits}', state)
            row['buffer_qubits'] = buffer_qubits
            row['comm_qubits'] = comm_qubits
            rows.append(row)
    out = Path('outputs/sensitivity/sensitivity_summary.csv')
    logger.write_csv(out, rows)
    write_heatmap_data(Path('outputs/sensitivity/sensitivity_heatmap.csv'), rows)
    print(f'Sensitivity outputs written to {out}')


if __name__ == '__main__':
    main()
