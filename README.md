# DQC-Switch-QNet

This repository implements the phased simulator stack requested by the `DQC_switch_qnet.pdf` design document:

- Phase 1: simulator core with hierarchical QDC topology, switch reconfiguration state, EPR inventory/buffer accounting, and DAG execution.
- Phase 2: minimal baselines with random placement, average placement, and direct-only scheduling.
- Phase 3: rack-aware greedy placement and unified JIT scheduling.
- Phase 4: split-assisted cross-rack communication.
- Phase 5: collective in-rack batching.
- Phase 6: optional intra-rack distillation support.
- Phase 7: experiment scripts for representative, benchmark, ablation, scaling, and sensitivity studies.

## Repository layout

- `configs/`: static experiment and topology settings.
- `src/qdc_project/circuit/`: DAG data structures and workload loaders/generators.
- `src/qdc_project/topology/`: QDC topology and switch model.
- `src/qdc_project/model/`: simulator state, metrics, and invariant checks.
- `src/qdc_project/algorithms/`: baseline and unified placement/scheduling policies.
- `src/qdc_project/simulation/`: execution engine, events, and CSV logger.
- `src/qdc_project/plotting/`: CSV/SVG/Markdown export helpers for schedules, tables, bar charts, and heatmaps.
- `src/qdc_project/experiments/`: runnable experiment entry points.
- `tests/`: invariant-focused unit tests.

## Run

```bash
PYTHONPATH=src python -m qdc_project.experiments.run_representative
PYTHONPATH=src python -m qdc_project.experiments.run_benchmarks
PYTHONPATH=src python -m qdc_project.experiments.run_ablation
PYTHONPATH=src python -m qdc_project.experiments.run_scaling
PYTHONPATH=src python -m qdc_project.experiments.run_sensitivity
PYTHONPATH=src pytest
```

## Output artifacts

Each experiment now emits:

- raw CSV summaries,
- Markdown tables for quick inspection,
- SVG figures for schedule views, runtime bar charts, and heatmaps.

## Notes on runtime

The simulator is event-driven and currently configured for small-to-medium benchmark sweeps so it still runs quickly on this machine. To make timing comparisons less trivial, the benchmark, scaling, and sensitivity scripts now use larger topologies/workloads and multiple seeds rather than one tiny instance.

## Notes on dependencies

The implementation remains runnable with only the Python standard library and `pytest`. Qiskit loading is still exposed as a hook in `loaders.py`; richer third-party plotting can be added later if desired.
