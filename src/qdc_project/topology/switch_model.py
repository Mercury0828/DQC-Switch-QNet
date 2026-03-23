from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class SwitchState:
    """Explicit cross-rack switch state with reconfiguration lockout."""

    reconfiguration_latency: int
    active_link: Optional[Tuple[str, str]] = None
    locked_until: int = 0
    reconfiguration_time_accum: int = 0
    reconfiguration_events: int = 0

    def can_generate(self, now: int) -> bool:
        return now >= self.locked_until

    def ensure_link(self, rack_pair: Tuple[str, str], now: int) -> int:
        canonical = tuple(sorted(rack_pair))
        if self.active_link == canonical:
            return max(now, self.locked_until)
        start = max(now, self.locked_until)
        self.locked_until = start + self.reconfiguration_latency
        self.active_link = canonical
        self.reconfiguration_time_accum += self.reconfiguration_latency
        self.reconfiguration_events += 1
        return self.locked_until
