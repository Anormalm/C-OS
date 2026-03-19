from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from cos.core.models import InsightSummary, StatementStatus
from cos.diagnostics.metrics import MetricsRegistry
from cos.graph.base import GraphStore


@dataclass
class InsightService:
    graph_store: GraphStore
    metrics: MetricsRegistry

    def summarize(self) -> InsightSummary:
        entities = {e.id: e for e in self.graph_store.entities.values()} if hasattr(self.graph_store, "entities") else {}
        statements = self.graph_store.list_statements()
        usage = Counter()
        last_seen: dict[str, datetime] = {}
        contradictions = 0

        for statement in statements:
            usage[statement.subject] += 1
            usage[statement.object] += 1
            last_seen[statement.subject] = max(last_seen.get(statement.subject, statement.valid_from), statement.valid_from)
            last_seen[statement.object] = max(last_seen.get(statement.object, statement.valid_from), statement.valid_from)
            if statement.status == StatementStatus.contradicted:
                contradictions += 1

        recurring = []
        for entity_id, count in usage.most_common(10):
            label = entities.get(entity_id).name if entity_id in entities else entity_id
            recurring.append({"entity_id": entity_id, "label": label, "count": count})

        cutoff = datetime.now(timezone.utc) - timedelta(days=60)
        abandoned = []
        for entity_id, ts in last_seen.items():
            if ts < cutoff:
                label = entities.get(entity_id).name if entity_id in entities else entity_id
                abandoned.append({"entity_id": entity_id, "label": label, "last_active": ts.isoformat()})

        contradiction_rate = (contradictions / len(statements)) if statements else 0.0
        created = self.metrics.counters.get("entity_created", 0)
        resolved = self.metrics.counters.get("entity_resolved_existing", 0)
        dedup_rate = (resolved / (resolved + created)) if (resolved + created) else 0.0

        notes = []
        if recurring:
            notes.append("Recurring conceptual clusters detected.")
        if abandoned:
            notes.append("Inactive idea trajectories found.")
        if contradiction_rate > 0.1:
            notes.append("High contradiction frequency suggests unstable belief state.")

        return InsightSummary(
            recurring_topics=recurring,
            abandoned_topics=abandoned[:20],
            contradiction_rate=round(contradiction_rate, 4),
            deduplication_rate=round(dedup_rate, 4),
            notes=notes,
        )
