from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from qdc_project.algorithms.batching_policy import CollectiveBatchingPolicy
from qdc_project.algorithms.retry_policy import RetryPolicy
from qdc_project.algorithms.scheduler_baseline import Placement
from qdc_project.algorithms.split_policy import DirectVsSplitPolicy
from qdc_project.circuit.dag_utils import CircuitDAG, Gate
from qdc_project.model.state import EPRRecord, SimulationState


@dataclass
class UnifiedSchedulerConfig:
    enable_collective: bool = True
    enable_split: bool = True
    enable_distillation: bool = False
    lookahead_depth: int = 3
    distillation_latency: int = 2
    distilled_fidelity: float = 0.95
    raw_intra_fidelity: float = 0.8
    raw_cross_fidelity: float = 0.7


class UnifiedScheduler:
    def __init__(self, config: UnifiedSchedulerConfig | None = None) -> None:
        self.config = config or UnifiedSchedulerConfig()
        self._epr_counter = 0
        self._batch_counter = 0
        self.split_policy = DirectVsSplitPolicy(enable_split=self.config.enable_split)
        self.batching_policy = CollectiveBatchingPolicy(lookahead_depth=self.config.lookahead_depth)
        self.retry_policy = RetryPolicy()

    def run(self, dag: CircuitDAG, placement: Placement, state: SimulationState) -> SimulationState:
        started = time.perf_counter()
        topo_order = dag.topological_order()
        for index, gate_id in enumerate(topo_order):
            self._schedule_gate(dag, topo_order, index, dag.gates[gate_id], placement, state)
        state.metrics.solver_time_seconds = time.perf_counter() - started
        state.finalize_metrics()
        return state

    def _schedule_gate(
        self,
        dag: CircuitDAG,
        topo_order: List[str],
        index: int,
        gate: Gate,
        placement: Placement,
        state: SimulationState,
    ) -> None:
        qpus = tuple(placement.logical_to_qpu[qubit] for qubit in gate.qubits)
        predecessor_ready = max((state.gate_end_times[pred] for pred in gate.predecessors), default=0)
        earliest = max([predecessor_ready] + [state.qpu_state[qpu].busy_until for qpu in qpus])
        state.metrics.latency_breakdown["wait_time"] += max(0, earliest - predecessor_ready)

        mode = "local"
        if len(qpus) == 1 or qpus[0] == qpus[-1]:
            start = earliest
            duration = state.topology.gate_duration(gate.name, qpus[0], None)
        elif state.topology.same_rack(qpus[0], qpus[1]):
            mode = "collective" if self.config.enable_collective else "direct"
            batch_size = self.batching_policy.plan_batch_size(dag, topo_order, index, same_rack_only=True)
            ready = self._ensure_intra_epr_pool(qpus[0], qpus[1], batch_size, earliest, state)
            record = self._consume_ready_epr(tuple(sorted(qpus)), ready, state, expected_kind=("intra_rack", "distilled"))
            start = max(ready, record.generated_at)
            duration = state.topology.gate_duration(gate.name, qpus[0], qpus[1])
            if record.kind == "distilled":
                mode = "distilled"
        else:
            decision = self.split_policy.choose(gate, placement, state.topology)
            state.metrics.remote_gate_count += 1
            if decision.mode == "split" and decision.relay_qpu is not None:
                mode = "split"
                start = self._realize_split(qpus[0], qpus[1], decision.relay_qpu, earliest, state)
                state.metrics.split_gate_count += 1
            else:
                mode = "direct"
                start = self._realize_direct(qpus[0], qpus[1], earliest, state)
            duration = state.topology.gate_duration(gate.name, qpus[0], qpus[1])

        end = start + duration
        for qpu in set(qpus):
            state.qpu_state[qpu].busy_until = end
        state.gate_start_times[gate.gate_id] = start
        state.gate_end_times[gate.gate_id] = end
        state.gate_execution_mode[gate.gate_id] = mode
        state.executed_gates.add(gate.gate_id)
        state.metrics.latency_breakdown["local_gate"] += duration
        state.log_event("gate", start, end, f"{gate.gate_id}:{mode}")

    def _ensure_intra_epr_pool(
        self,
        qpu_a: str,
        qpu_b: str,
        batch_size: int,
        earliest: int,
        state: SimulationState,
    ) -> int:
        key = tuple(sorted((qpu_a, qpu_b)))
        endpoint_capacity = min(
            state.topology.qpus[qpu_a].buffer_qubits,
            state.topology.qpus[qpu_b].buffer_qubits,
        )
        batch_size = min(batch_size, endpoint_capacity)
        available = [record for record in state.epr_inventory.get(key, []) if record.consumed_at is None]
        required = max(0, batch_size - len(available))
        generation_start = earliest
        if required > 1:
            batch_id = f"batch_{self._batch_counter}"
            self._batch_counter += 1
            state.metrics.collective_batches += 1
            state.log_event("collective_batch", generation_start, generation_start, batch_id)
        else:
            batch_id = None
        for _ in range(required):
            generation_start = self._generate_epr(
                key,
                generation_start,
                state,
                kind="intra_rack",
                fidelity=self.config.raw_intra_fidelity,
                batch_id=batch_id,
            )
            if batch_id is not None:
                state.metrics.epr_counts["batched"] += 1
        if self.config.enable_distillation:
            distilled = self._distill_if_possible(key, generation_start, state)
            if distilled is not None:
                return distilled.generated_at
        return generation_start

    def _realize_direct(self, qpu_a: str, qpu_b: str, earliest: int, state: SimulationState) -> int:
        key = tuple(sorted((qpu_a, qpu_b)))
        ready = self._generate_epr(
            key,
            earliest,
            state,
            kind="cross_rack",
            fidelity=self.config.raw_cross_fidelity,
        )
        self._consume_ready_epr(key, ready, state, expected_kind=("cross_rack",))
        return ready

    def _realize_split(self, qpu_a: str, qpu_b: str, relay_qpu: str, earliest: int, state: SimulationState) -> int:
        cross_key = tuple(sorted((qpu_a, relay_qpu)))
        intra_key = tuple(sorted((relay_qpu, qpu_b)))
        cross_ready = self._generate_epr(
            cross_key,
            earliest,
            state,
            kind="cross_rack",
            fidelity=self.config.raw_cross_fidelity,
        )
        intra_ready = self._ensure_intra_epr_pool(relay_qpu, qpu_b, 1, cross_ready, state)
        cross_record = self._consume_ready_epr(cross_key, cross_ready, state, expected_kind=("cross_rack",))
        intra_record = self._consume_ready_epr(intra_key, intra_ready, state, expected_kind=("intra_rack", "distilled"))
        completion = max(cross_ready, intra_ready)
        state.metrics.epr_counts["split_consumed"] += 2
        state.log_event(
            "split_completion",
            completion,
            completion,
            f"{cross_record.pair_id}+{intra_record.pair_id}",
        )
        return completion

    def _generate_epr(
        self,
        key: Tuple[str, str],
        earliest: int,
        state: SimulationState,
        kind: str,
        fidelity: float,
        batch_id: Optional[str] = None,
    ) -> int:
        qpu_a, qpu_b = key
        generation_start = earliest
        if kind == "cross_rack":
            rack_pair = (
                state.topology.qpus[qpu_a].rack_id,
                state.topology.qpus[qpu_b].rack_id,
            )
            generation_start = state.switch_state.ensure_link(rack_pair, earliest)
            if not state.switch_state.can_generate(generation_start):
                self.retry_policy.record_retry(state.metrics)
                generation_start = state.switch_state.locked_until
        for qpu_id in key:
            qpu_state = state.qpu_state[qpu_id]
            qpu = state.topology.qpus[qpu_id]
            if qpu_state.active_comm_qubits + 1 > qpu.comm_qubits:
                generation_start = max(generation_start, qpu_state.busy_until)
            if qpu_state.buffer_occupancy + 1 > qpu.buffer_qubits:
                self.retry_policy.record_retry(state.metrics)
                generation_start = max(generation_start, qpu_state.busy_until)
            qpu_state.active_comm_qubits += 1
            qpu_state.buffer_occupancy += 1
        latency = state.topology.epr_latency(qpu_a, qpu_b)
        ready_time = generation_start + latency
        pair_id = f"epr_{self._epr_counter}"
        self._epr_counter += 1
        record = EPRRecord(
            pair_id=pair_id,
            endpoints=key,
            generated_at=ready_time,
            kind=kind,
            fidelity=fidelity,
            batch_id=batch_id,
        )
        state.epr_inventory.setdefault(key, []).append(record)
        for qpu_id in key:
            state.qpu_state[qpu_id].active_comm_qubits -= 1
        metric_key = "cross_rack" if kind == "cross_rack" else "intra_rack"
        state.metrics.epr_counts[metric_key] += 1
        state.metrics.latency_breakdown[f"{metric_key}_epr"] += latency
        state.record_buffer_sample()
        state.log_event(f"{kind}_generation", generation_start, ready_time, pair_id)
        return ready_time

    def _consume_ready_epr(
        self,
        key: Tuple[str, str],
        at_time: int,
        state: SimulationState,
        expected_kind: Tuple[str, ...],
    ) -> EPRRecord:
        records: List[EPRRecord] = state.epr_inventory[key]
        available = [
            record
            for record in records
            if record.consumed_at is None and record.generated_at <= at_time and record.kind in expected_kind
        ]
        if not available:
            raise RuntimeError(f"No ready EPR for {key} with kind {expected_kind}")
        selected = max(available, key=lambda record: (record.fidelity, -record.generated_at))
        selected.consumed_at = at_time
        for qpu_id in key:
            state.qpu_state[qpu_id].buffer_occupancy -= 1
        state.record_buffer_sample()
        state.log_event("consume_epr", at_time, at_time, selected.pair_id)
        return selected

    def _distill_if_possible(self, key: Tuple[str, str], at_time: int, state: SimulationState) -> Optional[EPRRecord]:
        records = [
            record
            for record in state.epr_inventory.get(key, [])
            if record.consumed_at is None and record.kind == "intra_rack"
        ]
        if len(records) < 2:
            return None
        first, second = sorted(records, key=lambda record: record.generated_at)[:2]
        first.consumed_at = at_time
        second.consumed_at = at_time
        distilled_time = at_time + self.config.distillation_latency
        for qpu_id in key:
            state.qpu_state[qpu_id].buffer_occupancy -= 1
        distilled = EPRRecord(
            pair_id=f"epr_{self._epr_counter}",
            endpoints=key,
            generated_at=distilled_time,
            kind="distilled",
            fidelity=self.config.distilled_fidelity,
            source_pair_ids=(first.pair_id, second.pair_id),
        )
        self._epr_counter += 1
        state.epr_inventory.setdefault(key, []).append(distilled)
        state.metrics.epr_counts["distilled"] += 1
        state.metrics.latency_breakdown["distillation"] += self.config.distillation_latency
        state.record_buffer_sample()
        state.log_event("distillation", at_time, distilled_time, distilled.pair_id)
        return distilled
