from __future__ import annotations

from pathlib import Path

from qdc_project.algorithms.placement_greedy import RackAwareGreedyPlacer
from qdc_project.algorithms.scheduler_unified import UnifiedSchedulerConfig
from qdc_project.circuit.synthetic_generators import generate_synthetic_workload
from qdc_project.plotting.barplots import write_barplot_data, write_barplot_svg, write_markdown_table
from qdc_project.simulation.engine import SimulationEngine
from qdc_project.simulation.logger import SimulationLogger
from qdc_project.topology.qdc_topology import QDCTopology, TopologyConfig


def build_default_topology() -> QDCTopology:
    return QDCTopology(TopologyConfig(3, 2, 6, 2, 3, 2, 7, 3))


def main() -> None:
    dag = generate_synthetic_workload(8, 24, 0.8, seed=23)
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
        row = logger.to_row(name, state)
        rows.append(row)
    out = Path('outputs/ablation/ablation_summary.csv')
    logger.write_csv(out, rows)
    write_barplot_data(Path('outputs/ablation/ablation_runtime_table.csv'), rows)
    write_markdown_table(Path('outputs/ablation/ablation_runtime_table.md'), rows, columns=['name', 'runtime', 'objective_value', 'distilled_epr', 'split_ratio'])
    write_barplot_svg(Path('outputs/ablation/ablation_runtime.svg'), rows, 'name', 'runtime', 'Ablation runtime comparison')
    print(f'Ablation outputs written to {out}')


if __name__ == '__main__':
    main()
