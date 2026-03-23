from __future__ import annotations

from pathlib import Path

from qdc_project.algorithms.scheduler_baseline import AveragePlacementStrategy, RandomPlacementStrategy
from qdc_project.circuit.synthetic_generators import generate_synthetic_workload
from qdc_project.simulation.engine import SimulationEngine
from qdc_project.simulation.logger import SimulationLogger
from qdc_project.topology.qdc_topology import QDCTopology, TopologyConfig


def build_default_topology() -> QDCTopology:
    return QDCTopology(
        TopologyConfig(
            racks=2,
            qpus_per_rack=2,
            data_qubits_per_qpu=4,
            comm_qubits_per_qpu=1,
            buffer_qubits_per_qpu=2,
            intra_epr_latency=2,
            cross_epr_latency=7,
            switch_reconfig_latency=3,
        )
    )


def main() -> None:
    topology = build_default_topology()
    engine = SimulationEngine(topology)
    logger = SimulationLogger()
    workloads = {
        "dense_cross_rack": generate_synthetic_workload(6, 12, 0.85, seed=11),
        "mixed_random": generate_synthetic_workload(6, 12, 0.55, seed=13),
        "light_remote": generate_synthetic_workload(6, 12, 0.25, seed=17),
    }
    output_dir = Path("outputs/benchmarks")
    rows = []

    for workload_name, dag in workloads.items():
        placements = {
            "random": RandomPlacementStrategy(seed=31).place(dag, topology),
            "average": AveragePlacementStrategy().place(dag, topology),
        }
        for placement_name, placement in placements.items():
            state = engine.run_direct_only(dag, placement)
            row = logger.to_row(f"{workload_name}:{placement_name}", state)
            row["workload"] = workload_name
            row["placement"] = placement_name
            rows.append(row)

    logger.write_csv(output_dir / "benchmark_summary.csv", rows)
    print(f"Benchmark outputs written to {output_dir / 'benchmark_summary.csv'}")


if __name__ == "__main__":
    main()
