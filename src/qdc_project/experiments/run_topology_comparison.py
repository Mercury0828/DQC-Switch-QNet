from __future__ import annotations

from pathlib import Path

from qdc_project.algorithms.placement_greedy import RackAwareGreedyPlacer
from qdc_project.algorithms.scheduler_unified import UnifiedSchedulerConfig
from qdc_project.circuit.benchmark_families import build_named_family
from qdc_project.plotting.barplots import write_markdown_table
from qdc_project.plotting.topology_viz import write_topology_svg
from qdc_project.simulation.engine import SimulationEngine
from qdc_project.simulation.logger import SimulationLogger
from qdc_project.topology.library import build_topology, get_topology_profile


def main() -> None:
    topologies = ['clos_small', 'spine_leaf_small', 'fat_tree_small', 'clos_medium']
    output_dir = Path('outputs/topology_comparison')
    logger = SimulationLogger()
    rows = []
    for topo_name in topologies:
        profile = get_topology_profile(topo_name)
        write_topology_svg(output_dir / f'{topo_name}.svg', profile)
        topology = build_topology(topo_name)
        dag = build_named_family('qft', 'medium')
        placement = RackAwareGreedyPlacer().place(dag, topology)
        state = SimulationEngine(topology).run_unified(dag, placement, UnifiedSchedulerConfig())
        row = logger.to_row(topo_name, state)
        row['topology'] = topo_name
        row['racks'] = profile.racks
        row['qpus_per_rack'] = profile.qpus_per_rack
        rows.append(row)
    logger.write_csv(output_dir / 'topology_summary.csv', rows)
    write_markdown_table(output_dir / 'topology_summary.md', rows, columns=['topology', 'runtime', 'objective_value', 'cross_rack_epr', 'wait_time'])
    print(f'Topology comparison outputs written to {output_dir}')


if __name__ == '__main__':
    main()
