from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from qdc_project.algorithms.placement_greedy import RackAwareGreedyPlacer
from qdc_project.algorithms.scheduler_baseline import AveragePlacementStrategy, RandomPlacementStrategy
from qdc_project.algorithms.scheduler_unified import UnifiedSchedulerConfig
from qdc_project.circuit.synthetic_generators import generate_synthetic_workload
from qdc_project.plotting.barplots import write_markdown_table
from qdc_project.simulation.engine import SimulationEngine
from qdc_project.simulation.logger import SimulationLogger
from qdc_project.topology.library import build_topology


def main() -> None:
    topology = build_topology('clos_small')
    engine = SimulationEngine(topology)
    logger = SimulationLogger()
    output_dir = Path('outputs/algorithm_comparison')
    rows = []
    scale_specs = [('small', 6, 18), ('medium', 8, 24), ('large', 10, 30), ('very_large', 12, 36)]
    for scale, qubits, depth in scale_specs:
        dag = generate_synthetic_workload(qubits, depth, 0.7, seed=qubits + depth)
        runs = [
            ('random_direct', RandomPlacementStrategy(seed=qubits).place(dag, topology), 'direct', None),
            ('stagewise_direct', AveragePlacementStrategy().place(dag, topology), 'direct', None),
            ('full_method', RackAwareGreedyPlacer().place(dag, topology), 'unified', UnifiedSchedulerConfig()),
        ]
        for name, placement, mode, config in runs:
            state = engine.run_direct_only(dag, placement) if mode == 'direct' else engine.run_unified(dag, placement, config)
            row = logger.to_row(f'{scale}:{name}', state)
            row['scale'] = scale
            row['method'] = name
            rows.append(row)
    logger.write_csv(output_dir / 'algorithm_comparison.csv', rows)
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['method']].append(float(row['runtime']))
    summary = [{'method': method, 'avg_runtime': round(sum(vals) / len(vals), 3)} for method, vals in sorted(grouped.items())]
    write_markdown_table(output_dir / 'algorithm_comparison.md', rows, columns=['scale', 'method', 'runtime', 'objective_value', 'solver_time_seconds'])
    write_markdown_table(output_dir / 'algorithm_summary.md', summary)
    print(f'Algorithm comparison outputs written to {output_dir}')


if __name__ == '__main__':
    main()
