# DQC-Switch-QNet

This repository implements the switch-networked QDC simulator and paper-style evaluation pipeline described by the new design specification.

## Experiment organization

The experiment suite is organized in the same *evaluation progression* style requested by the user, while keeping the QDC model/algorithms grounded in the new specification rather than the old UNIQ formulation:

1. **Evaluation Setup**: architecture profiles, benchmark families, baseline definitions, and experiment metadata.
2. **Representative Example**: interpretable event timeline plus resource-usage view.
3. **Algorithm-Level Comparison**: synthetic workloads across small / medium / large / very large scales.
4. **Benchmark-Style Comparison**: MCT / QFT / Grover / RCA families under matched QDC settings.
5. **Resource Sensitivity**: data qubits, communication qubits, buffers, and latency/look-ahead knobs.
6. **Topology / Architecture Comparison**: multiple switch-networked QDC architectures with topology visualization.
7. **Framework-Level Comparison**: full-pipeline comparison across multiple metrics.
8. **Optional Scaling / Overhead Analysis**: compilation/runtime trends and overhead breakdowns.

## Repository layout

- `configs/`: experiment-suite settings.
- `src/qdc_project/circuit/`: DAG utilities, synthetic workloads, and benchmark-family generators.
- `src/qdc_project/topology/`: QDC topology core plus named architecture profiles.
- `src/qdc_project/model/`: simulator state, metrics, and invariants.
- `src/qdc_project/algorithms/`: placement/scheduling policies.
- `src/qdc_project/plotting/`: output helpers for tables, schedule/resource plots, and topology diagrams.
- `src/qdc_project/experiments/`: evaluation scripts following the paper-style progression.
- `outputs/`: generated result tables and figures.

## First 5 figures implemented

1. Representative schedule timeline (`outputs/representative/*_gantt.svg`)
2. Representative communication/EPR resource usage (`outputs/representative/*_resource_usage.svg`)
3. Benchmark average runtime comparison (`outputs/benchmarks/benchmark_runtime.svg`)
4. Scaling runtime heatmap (`outputs/scaling/scaling_runtime.svg`)
5. Topology visualization panels (`outputs/topology_comparison/*.svg`)

## Run

```bash
PYTHONPATH=src python -m qdc_project.experiments.run_representative
PYTHONPATH=src python -m qdc_project.experiments.run_algorithm_comparison
PYTHONPATH=src python -m qdc_project.experiments.run_benchmarks
PYTHONPATH=src python -m qdc_project.experiments.run_sensitivity
PYTHONPATH=src python -m qdc_project.experiments.run_topology_comparison
PYTHONPATH=src python -m qdc_project.experiments.run_framework_comparison
PYTHONPATH=src pytest
```

## Notes

- The simulator remains event-driven and explicit about switch reconfiguration, EPR generation/consumption, and buffer accounting.
- In this environment, `matplotlib` is not installable due package-repository/network restrictions, so the generated figures are exported as deterministic SVGs from simulator outputs rather than through matplotlib. The experiment organization and figure logic still follow the requested paper-style progression.
