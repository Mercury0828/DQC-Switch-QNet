from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetryPolicy:
    retry_penalty: int = 1

    def record_retry(self, state_metrics) -> None:
        state_metrics.latency_breakdown["retry_overhead_hook"] += self.retry_penalty
