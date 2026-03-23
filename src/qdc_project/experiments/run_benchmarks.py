from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from qdc_project.algorithms.placement_greedy import RackAwareGreedyPlacer
from qdc_project.algorithms.scheduler_baseline import AveragePlacementStrategy, RandomPlacementStrategy
from qdc_project.algorithms.scheduler_unified import UnifiedSchedulerConfig
from qdc_project.circuit.synthetic_generators import generate_synthetic_workload
from qdc_project.plotting.barplots import write_barplot_data, write_barplot_svg, write_markdown_table
from qdc_project.simulation.engine import SimulationEngine
from qdc_project.simulation.logger import SimulationLogger
from qdc_project.topology.qdc_topology import QDCTopology, TopologyConfig


def build_default_topology() -> QDCTopology:
    return QDCTopology(
        TopologyConfig(
            racks=3,
            qpus_per_rack=2,
            data_qubits_per_qpu=6,
            comm_qubits_per_qpu=2,
            buffer_qubits_per_qpu=3,
            intra_epr_latency=2,
            cross_epr_latency=7,
            switch_reconfig_latency=3,
        )
    )


def main() -> None:
    topology = build_default_topology()
    engine = SimulationEngine(topology)
    logger = SimulationLogger()
    output_dir = Path("outputs/benchmarks")
    rows = []
    seeds = [11, 13, 17]
    workload_specs = [
        ('dense_cross_rack', 8, 22, 0.85),
        ('mixed_random', 8, 22, 0.55),
        ('light_remote', 8, 22, 0.25),
    ]

    for workload_name, num_qubits, depth, prob in workload_specs:
        for seed in seeds:
            dag = generate_synthetic_workload(num_qubits, depth, prob, seed=seed)
            runs = [
                ("random_direct", RandomPlacementStrategy(seed=31 + seed).place(dag, topology), "direct", None),
                ("average_direct", AveragePlacementStrategy().place(dag, topology), "direct", None),
                (
                    "greedy_unified",
                    RackAwareGreedyPlacer().place(dag, topology),
                    "unified",
                    UnifiedSchedulerConfig(enable_collective=True, enable_split=True, enable_distillation=False),
                ),
            ]
            for run_name, placement, mode, config in runs:
                state = engine.run_direct_only(dag, placement) if mode == "direct" else engine.run_unified(dag, placement, config)
                row = logger.to_row(f"{workload_name}:{seed}:{run_name}", state)
                row["workload"] = workload_name
                row["placement"] = run_name
                row["seed"] = seed
                rows.append(row)

    aggregates = []
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row['workload'], row['placement'])].append(row)
    for (workload, placement), group in sorted(grouped.items()):
        avg_runtime = sum(float(item['runtime']) for item in group) / len(group)
        avg_objective = sum(float(item['objective_value']) for item in group) / len(group)
        avg_split_ratio = sum(float(item['split_ratio']) for item in group) / len(group)
        aggregates.append({
            'workload': workload,
            'placement': placement,
            'avg_runtime': round(avg_runtime, 3),
            'avg_objective': round(avg_objective, 3),
            'avg_split_ratio': round(avg_split_ratio, 3),
        })

    logger.write_csv(output_dir / "benchmark_summary.csv", rows)
    write_barplot_data(output_dir / "benchmark_runtime_table.csv", aggregates)
    write_markdown_table(output_dir / 'benchmark_runtime_table.md', aggregates)
    overall = []
    by_placement = defaultdict(list)
    for row in aggregates:
        by_placement[row['placement']].append(row['avg_runtime'])
    for placement, values in sorted(by_placement.items()):
        overall.append({'placement': placement, 'avg_runtime': round(sum(values) / len(values), 3)})
    write_barplot_svg(output_dir / 'benchmark_runtime.svg', overall, 'placement', 'avg_runtime', 'Benchmark average runtime by method')
    print(f"Benchmark outputs written to {output_dir / 'benchmark_summary.csv'}")


if __name__ == "__main__":
    main()
