from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationEvent:
    event_type: str
    start_time: int
    end_time: int
    detail: str
