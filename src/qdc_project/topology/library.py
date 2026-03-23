from __future__ import annotations

from dataclasses import dataclass

from qdc_project.topology.qdc_topology import QDCTopology, TopologyConfig


@dataclass(frozen=True)
class TopologyProfile:
    name: str
    racks: int
    qpus_per_rack: int
    data_qubits_per_qpu: int
    comm_qubits_per_qpu: int
    buffer_qubits_per_qpu: int
    intra_epr_latency: int
    cross_epr_latency: int
    switch_reconfig_latency: int
    style: str


_TOPOLOGIES = {
    'clos_small': TopologyProfile('clos_small', 3, 2, 6, 2, 3, 2, 6, 2, 'clos'),
    'spine_leaf_small': TopologyProfile('spine_leaf_small', 3, 2, 6, 2, 3, 2, 7, 3, 'spine_leaf'),
    'fat_tree_small': TopologyProfile('fat_tree_small', 4, 2, 6, 2, 3, 2, 8, 4, 'fat_tree'),
    'clos_medium': TopologyProfile('clos_medium', 4, 3, 6, 2, 3, 2, 7, 3, 'clos'),
}


def get_topology_profile(name: str) -> TopologyProfile:
    return _TOPOLOGIES[name]


def build_topology(name: str) -> QDCTopology:
    profile = get_topology_profile(name)
    return QDCTopology(
        TopologyConfig(
            racks=profile.racks,
            qpus_per_rack=profile.qpus_per_rack,
            data_qubits_per_qpu=profile.data_qubits_per_qpu,
            comm_qubits_per_qpu=profile.comm_qubits_per_qpu,
            buffer_qubits_per_qpu=profile.buffer_qubits_per_qpu,
            intra_epr_latency=profile.intra_epr_latency,
            cross_epr_latency=profile.cross_epr_latency,
            switch_reconfig_latency=profile.switch_reconfig_latency,
        )
    )
