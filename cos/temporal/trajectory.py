from __future__ import annotations

from dataclasses import dataclass

from cos.core.models import StatementNode
from cos.graph.base import GraphStore


@dataclass
class TrajectoryAnalyzer:
    graph_store: GraphStore

    def entity_trajectory(self, entity_id: str) -> list[StatementNode]:
        statements = [
            s
            for s in self.graph_store.list_statements()
            if s.subject == entity_id or s.object == entity_id
        ]
        return sorted(statements, key=lambda s: s.valid_from)
