from __future__ import annotations

from pathlib import Path

from qdc_project.algorithms.placement_greedy import RackAwareGreedyPlacer
from qdc_project.algorithms.scheduler_baseline import AveragePlacementStrategy, RandomPlacementStrategy
from qdc_project.algorithms.scheduler_unified import UnifiedSchedulerConfig
from qdc_project.circuit.benchmark_families import build_named_family
from qdc_project.circuit.loaders import load_handcrafted_representative
from qdc_project.plotting.paper_figures import (
    create_algorithm_figure,
    create_framework_comparison_figure,
    create_representative_figure,
    create_sensitivity_figure,
    create_setup_table,
    create_topology_comparison_figure,
    create_topology_gallery,
)
from qdc_project.simulation.engine import SimulationEngine
from qdc_project.simulation.logger import SimulationLogger
from qdc_project.topology.library import build_topology, get_topology_profile
from qdc_project.topology.qdc_topology import QDCTopology, TopologyConfig


def _representative_state():
    dag = load_handcrafted_representative()
    topology = QDCTopology(TopologyConfig(2, 2, 4, 1, 2, 2, 7, 3))
    placement = RackAwareGreedyPlacer().place(dag, topology)
    return SimulationEngine(topology).run_unified(dag, placement, UnifiedSchedulerConfig(True, True, True))


def _algorithm_rows():
    from qdc_project.experiments.run_algorithm_comparison import main as run_algo
    run_algo()
    # regenerate rows directly for composition
    topology = build_topology('clos_small')
    engine = SimulationEngine(topology)
    logger = SimulationLogger()
    rows = []
    for scale, qubits, depth in [('small', 6, 18), ('medium', 8, 24), ('large', 10, 30), ('very_large', 12, 36)]:
        from qdc_project.circuit.synthetic_generators import generate_synthetic_workload
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
    return rows


def _sensitivity_rows():
    rows = {family: [] for family in ['mct', 'qft', 'grover', 'rca']}
    logger = SimulationLogger()
    for family in rows:
        for comm_qubits in [1, 2, 3, 4]:
            topology = QDCTopology(TopologyConfig(3, 2, 6, comm_qubits, 3, 2, 7, 3))
            dag = build_named_family(family, 'medium')
            engine = SimulationEngine(topology)
            runs = [
                ('random_direct', RandomPlacementStrategy(seed=comm_qubits).place(dag, topology), 'direct', None),
                ('stagewise_direct', AveragePlacementStrategy().place(dag, topology), 'direct', None),
                ('full_method', RackAwareGreedyPlacer().place(dag, topology), 'unified', UnifiedSchedulerConfig()),
            ]
            for name, placement, mode, config in runs:
                state = engine.run_direct_only(dag, placement) if mode == 'direct' else engine.run_unified(dag, placement, config)
                row = logger.to_row(f'{family}:{name}:{comm_qubits}', state)
                row['comm_qubits'] = comm_qubits
                row['method'] = name
                rows[family].append(row)
    return rows


def _topology_rows():
    logger = SimulationLogger()
    rows = []
    for topo_name in ['clos_small', 'spine_leaf_small', 'fat_tree_small', 'clos_medium']:
        topology = build_topology(topo_name)
        dag = build_named_family('qft', 'medium')
        placement = RackAwareGreedyPlacer().place(dag, topology)
        state = SimulationEngine(topology).run_unified(dag, placement, UnifiedSchedulerConfig())
        row = logger.to_row(topo_name, state)
        row['topology'] = topo_name
        rows.append(row)
    return rows


def _framework_rows():
    logger = SimulationLogger()
    topology = build_topology('clos_small')
    engine = SimulationEngine(topology)
    rows = []
    for family in ['mct', 'qft', 'grover', 'rca']:
        dag = build_named_family(family, 'medium')
        stagewise = AveragePlacementStrategy().place(dag, topology)
        proposed = RackAwareGreedyPlacer().place(dag, topology)
        for label, placement, mode, config in [
            ('stagewise_direct', stagewise, 'direct', None),
            ('full_framework', proposed, 'unified', UnifiedSchedulerConfig()),
        ]:
            state = engine.run_direct_only(dag, placement) if mode == 'direct' else engine.run_unified(dag, placement, config)
            row = logger.to_row(f'{family}:{label}', state)
            row['family'] = family
            row['framework'] = label
            rows.append(row)
    return rows


def main() -> None:
    out = Path('outputs/paper_figures')
    create_setup_table(
        out / 'evaluation_setup.svg',
        ['Scale', 'Qubits', 'Topology', 'Comm/QPU', 'Buffer/QPU'],
        [
            ['small', '6', 'clos_small', '2', '3'],
            ['medium', '8', 'clos_small', '2', '3'],
            ['large', '10', 'clos_small', '2', '3'],
            ['very_large', '12', 'clos_medium', '2', '3'],
        ],
    )
    create_representative_figure(out / 'fig8_representative_example.svg', _representative_state())
    create_algorithm_figure(out / 'fig9_algorithm_comparison.svg', _algorithm_rows())
    create_sensitivity_figure(out / 'fig10_resource_sensitivity.svg', _sensitivity_rows())
    create_topology_gallery(out / 'fig11_topology_gallery.svg', [get_topology_profile(n) for n in ['clos_small', 'spine_leaf_small', 'fat_tree_small']])
    create_topology_comparison_figure(out / 'fig12_topology_comparison.svg', _topology_rows())
    create_framework_comparison_figure(out / 'fig13_framework_comparison.svg', _framework_rows())
    print(f'Paper-style figures written to {out}')


if __name__ == '__main__':
    main()
