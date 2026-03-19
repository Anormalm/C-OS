from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from cos.core.models import EntityNode
from cos.graph.base import GraphStore


@dataclass
class EntityResolver:
    graph_store: GraphStore

    def resolve(self, name: str) -> tuple[EntityNode, bool]:
        matches = self.graph_store.find_entities_by_name(name, limit=1)
        if matches:
            return matches[0], False
        entity = EntityNode(name=name, aliases=[], created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        return self.graph_store.upsert_entity(entity), True
