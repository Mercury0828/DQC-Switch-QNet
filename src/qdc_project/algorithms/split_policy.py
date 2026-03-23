from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from qdc_project.algorithms.scheduler_baseline import Placement
from qdc_project.circuit.dag_utils import CircuitDAG, Gate
from qdc_project.topology.qdc_topology import QDCTopology


@dataclass
class SplitDecision:
    mode: str
    relay_qpu: Optional[str] = None


@dataclass
class DirectVsSplitPolicy:
    enable_split: bool = True

    def choose(self, gate: Gate, placement: Placement, topology: QDCTopology) -> SplitDecision:
        qpu_a, qpu_b = (placement.logical_to_qpu[qubit] for qubit in gate.qubits)
        if topology.same_rack(qpu_a, qpu_b) or not self.enable_split:
            return SplitDecision(mode="direct")

        direct_cost = topology.config.cross_epr_latency + topology.config.gate_durations.get("remote_cx", 1)
        relay_candidates = [
            qpu_id
            for qpu_id, qpu in topology.qpus.items()
            if qpu.rack_id == topology.qpus[qpu_b].rack_id and qpu_id != qpu_b
        ]
        if not relay_candidates:
            return SplitDecision(mode="direct")
        relay = min(relay_candidates)
        split_cost = (
            topology.config.cross_epr_latency
            + topology.config.intra_epr_latency
            + topology.config.gate_durations.get("remote_cx", 1)
        )
        if split_cost <= direct_cost + topology.config.switch_reconfig_latency:
            return SplitDecision(mode="split", relay_qpu=relay)
        return SplitDecision(mode="direct")
