from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from cos.core.models import ExtractedTriple, StatementNode
from cos.graph.base import GraphStore
from cos.resolution.contradiction import ContradictionResolver
from cos.resolution.dedup import EntityResolver


@dataclass
class ResolutionService:
    graph_store: GraphStore

    def __post_init__(self) -> None:
        self.entity_resolver = EntityResolver(self.graph_store)
        self.contradiction_resolver = ContradictionResolver(self.graph_store)

    def resolve_triple(
        self,
        triple: ExtractedTriple,
        source: str,
        default_valid_from: datetime | None = None,
    ) -> tuple[StatementNode, int, int, int]:
        subject, subject_created = self.entity_resolver.resolve(triple.subject)
        obj, object_created = self.entity_resolver.resolve(triple.object)
        valid_from = triple.timestamp or default_valid_from or datetime.now(timezone.utc)
        statement = StatementNode(
            subject=subject.id,
            relation=triple.relation,
            object=obj.id,
            valid_from=valid_from,
            source=source,
            confidence=triple.confidence,
        )
        self.graph_store.add_statement(statement)
        contradictions = self.contradiction_resolver.apply(statement)
        created_count = int(subject_created) + int(object_created)
        resolved_count = int(not subject_created) + int(not object_created)
        return statement, created_count, resolved_count, contradictions
