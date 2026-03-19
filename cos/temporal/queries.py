from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from cos.core.models import StatementNode
from cos.graph.base import GraphStore


@dataclass
class TemporalQueryService:
    graph_store: GraphStore

    def truth_at(
        self,
        at_time: datetime,
        ingestion_as_of: datetime | None = None,
        entity_id: str | None = None,
    ) -> list[StatementNode]:
        return self.graph_store.statements_at_time(at_time, ingestion_as_of, entity_id)
