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
    logger = SimulationLogger()
    rows = []
    for qubits in (4, 6, 8):
        topology = QDCTopology(TopologyConfig(2, 2, max(4, qubits), 1, 3, 2, 7, 3))
        dag = generate_synthetic_workload(qubits, depth=qubits * 2, two_qubit_probability=0.7, seed=qubits)
        placement = RackAwareGreedyPlacer().place(dag, topology)
        state = SimulationEngine(topology).run_unified(dag, placement, UnifiedSchedulerConfig())
        row = logger.to_row(f'scale_{qubits}', state)
        row['qubits'] = qubits
        rows.append(row)
    out = Path('outputs/scaling/scaling_summary.csv')
    logger.write_csv(out, rows)
    write_heatmap_data(Path('outputs/scaling/scaling_heatmap.csv'), rows)
    print(f'Scaling outputs written to {out}')


if __name__ == '__main__':
    main()
