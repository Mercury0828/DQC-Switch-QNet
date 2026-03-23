# DQC-Switch-QNet

This repository implements the first phased delivery from the `DQC_switch_qnet.pdf` specification:

- Phase 1: simulator core with hierarchical QDC topology, explicit switch reconfiguration state, EPR inventory/buffer accounting, and DAG execution.
- Phase 2: minimal baselines with random placement, average/non-architecture-aware placement, and direct-only on-demand scheduling.

## Repository layout

- `configs/`: static experiment and topology settings.
- `src/qdc_project/circuit/`: DAG data structures and workload loaders/generators.
- `src/qdc_project/topology/`: QDC topology and switch model.
- `src/qdc_project/model/`: simulator state, metrics, and invariant checks.
- `src/qdc_project/algorithms/`: baseline placement and scheduling algorithms.
- `src/qdc_project/simulation/`: execution engine and CSV logger.
- `src/qdc_project/plotting/`: lightweight schedule export for representative examples.
- `src/qdc_project/experiments/`: runnable entry points.
- `tests/`: invariant-focused unit tests.

## Run

```bash
PYTHONPATH=src python -m qdc_project.experiments.run_representative
PYTHONPATH=src python -m qdc_project.experiments.run_benchmarks
PYTHONPATH=src pytest
```

## Notes on dependencies

The implementation is written to remain runnable in restricted environments with only the Python standard library and `pytest` available. The specification's `NetworkX`, `NumPy`, `Pandas`, `Matplotlib`, and `Qiskit` integrations are left as explicit extension points for later phases.
