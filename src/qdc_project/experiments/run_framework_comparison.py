from __future__ import annotations

from pathlib import Path

from qdc_project.algorithms.placement_greedy import RackAwareGreedyPlacer
from qdc_project.algorithms.scheduler_baseline import AveragePlacementStrategy
from qdc_project.algorithms.scheduler_unified import UnifiedSchedulerConfig
from qdc_project.circuit.benchmark_families import build_named_family
from qdc_project.plotting.barplots import write_markdown_table
from qdc_project.simulation.engine import SimulationEngine
from qdc_project.simulation.logger import SimulationLogger
from qdc_project.topology.library import build_topology


def main() -> None:
    output_dir = Path('outputs/framework_comparison')
    logger = SimulationLogger()
    rows = []
    topology = build_topology('clos_small')
    engine = SimulationEngine(topology)
    for family in ['mct', 'qft', 'grover', 'rca']:
        dag = build_named_family(family, 'medium')
        stagewise = AveragePlacementStrategy().place(dag, topology)
        proposed = RackAwareGreedyPlacer().place(dag, topology)
        runs = [
            ('stagewise_direct', stagewise, 'direct', None),
            ('full_framework', proposed, 'unified', UnifiedSchedulerConfig()),
        ]
        for label, placement, mode, config in runs:
            state = engine.run_direct_only(dag, placement) if mode == 'direct' else engine.run_unified(dag, placement, config)
            row = logger.to_row(f'{family}:{label}', state)
            row['family'] = family
            row['framework'] = label
            rows.append(row)
    logger.write_csv(output_dir / 'framework_summary.csv', rows)
    write_markdown_table(output_dir / 'framework_summary.md', rows, columns=['family', 'framework', 'runtime', 'solver_time_seconds', 'cross_rack_epr', 'wait_time', 'peak_buffer'])
    print(f'Framework comparison outputs written to {output_dir}')


if __name__ == '__main__':
    main()
