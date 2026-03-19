from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from time import perf_counter


@dataclass
class MetricsRegistry:
    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    latencies_ms: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def inc(self, key: str, amount: int = 1) -> None:
        self.counters[key] += amount

    def observe_latency(self, key: str, ms: float) -> None:
        self.latencies_ms[key].append(ms)

    def snapshot(self) -> dict[str, object]:
        avg = {}
        for key, values in self.latencies_ms.items():
            avg[key] = round(sum(values) / len(values), 2) if values else 0.0
        return {
            "counters": dict(self.counters),
            "latency_ms_avg": avg,
        }


class LatencyTimer:
    def __init__(self, registry: MetricsRegistry, key: str) -> None:
        self.registry = registry
        self.key = key
        self.start = 0.0

    def __enter__(self) -> "LatencyTimer":
        self.start = perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        elapsed = (perf_counter() - self.start) * 1000.0
        self.registry.observe_latency(self.key, elapsed)
