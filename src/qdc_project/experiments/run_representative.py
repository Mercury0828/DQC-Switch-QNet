from __future__ import annotations

from pathlib import Path

from qdc_project.algorithms.scheduler_baseline import AveragePlacementStrategy, RandomPlacementStrategy
from qdc_project.circuit.loaders import load_handcrafted_representative
from qdc_project.plotting.gantt import write_text_gantt
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
    dag = load_handcrafted_representative()
    topology = build_default_topology()
    engine = SimulationEngine(topology)
    logger = SimulationLogger()

    placements = {
        "random": RandomPlacementStrategy(seed=7).place(dag, topology),
        "average": AveragePlacementStrategy().place(dag, topology),
    }
    rows = []
    output_dir = Path("outputs/representative")

    for name, placement in placements.items():
        state = engine.run_direct_only(dag, placement)
        rows.append(logger.to_row(name, state))
        write_text_gantt(output_dir / f"{name}_gantt.csv", state)

    logger.write_csv(output_dir / "summary.csv", rows)
    print(f"Representative outputs written to {output_dir}")


if __name__ == "__main__":
    main()
