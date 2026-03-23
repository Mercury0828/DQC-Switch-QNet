# DQC-Switch-QNet

This repository now implements all phased layers requested by the `DQC_switch_qnet.pdf` design document:

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
- `src/qdc_project/plotting/`: schedule/barplot/heatmap CSV exports.
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

## Notes on dependencies

The implementation is written to remain runnable in restricted environments with only the Python standard library and `pytest` available. Qiskit loading remains an explicit hook in `loaders.py`; richer plotting or benchmark imports can be layered in when optional dependencies are installed.
