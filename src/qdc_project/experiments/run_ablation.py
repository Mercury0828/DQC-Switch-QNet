from __future__ import annotations

from pathlib import Path

from qdc_project.algorithms.placement_greedy import RackAwareGreedyPlacer
from qdc_project.algorithms.scheduler_unified import UnifiedSchedulerConfig
from qdc_project.circuit.synthetic_generators import generate_synthetic_workload
from qdc_project.plotting.barplots import write_barplot_data
from qdc_project.simulation.engine import SimulationEngine
from qdc_project.simulation.logger import SimulationLogger
from qdc_project.topology.qdc_topology import QDCTopology, TopologyConfig


def build_default_topology() -> QDCTopology:
    return QDCTopology(TopologyConfig(2, 2, 4, 1, 2, 2, 7, 3))


def main() -> None:
    dag = generate_synthetic_workload(6, 14, 0.8, seed=23)
    topology = build_default_topology()
    placement = RackAwareGreedyPlacer().place(dag, topology)
    engine = SimulationEngine(topology)
    logger = SimulationLogger()
    configs = {
        'full': UnifiedSchedulerConfig(True, True, True),
        'no_split': UnifiedSchedulerConfig(True, False, True),
        'no_collective': UnifiedSchedulerConfig(False, True, True),
        'no_distill': UnifiedSchedulerConfig(True, True, False),
    }
    rows = []
    for name, config in configs.items():
        state = engine.run_unified(dag, placement, config)
        rows.append(logger.to_row(name, state))
    out = Path('outputs/ablation/ablation_summary.csv')
    logger.write_csv(out, rows)
    write_barplot_data(Path('outputs/ablation/ablation_runtime_table.csv'), rows)
    print(f'Ablation outputs written to {out}')


if __name__ == '__main__':
    main()
