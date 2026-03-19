from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime

from cos.core.models import EntityNode, StatementNode
from cos.graph.base import GraphStore


def canonical_name(name: str) -> str:
    return " ".join(name.lower().split())


class InMemoryGraphStore(GraphStore):
    def __init__(self) -> None:
        self.entities: dict[str, EntityNode] = {}
        self.entity_name_index: dict[str, str] = {}
        self.statements: dict[str, StatementNode] = {}
        self.statement_keys: dict[tuple[str, str], list[str]] = defaultdict(list)
        self.entity_edges: dict[str, list[str]] = defaultdict(list)

    def upsert_entity(self, entity: EntityNode) -> EntityNode:
        key = canonical_name(entity.name)
        existing_id = self.entity_name_index.get(key)
        if existing_id:
            existing = self.entities[existing_id]
            alias_set = {a.lower() for a in existing.aliases}
            for alias in entity.aliases + [entity.name]:
                if alias.lower() not in alias_set:
                    existing.aliases.append(alias)
            if entity.embedding is not None:
                existing.embedding = entity.embedding
            existing.metadata.update(entity.metadata)
            existing.updated_at = entity.updated_at
            self.entities[existing_id] = existing
            return existing

        self.entities[entity.id] = entity
        self.entity_name_index[key] = entity.id
        for alias in entity.aliases:
            self.entity_name_index[canonical_name(alias)] = entity.id
        return entity

    def find_entities_by_name(self, name: str, limit: int = 5) -> list[EntityNode]:
        key = canonical_name(name)
        if key in self.entity_name_index:
            entity_id = self.entity_name_index[key]
            return [self.entities[entity_id]]
        partials = [
            entity
            for entity in self.entities.values()
            if key in canonical_name(entity.name)
            or any(key in canonical_name(alias) for alias in entity.aliases)
        ]
        return partials[:limit]

    def get_entity(self, entity_id: str) -> EntityNode | None:
        return self.entities.get(entity_id)

    def add_statement(self, statement: StatementNode) -> StatementNode:
        self.statements[statement.id] = statement
        self.statement_keys[(statement.subject, statement.relation)].append(statement.id)
        self.entity_edges[statement.subject].append(statement.id)
        self.entity_edges[statement.object].append(statement.id)
        return statement

    def get_statement(self, statement_id: str) -> StatementNode | None:
        return self.statements.get(statement_id)

    def update_statement(self, statement: StatementNode) -> None:
        if statement.id not in self.statements:
            raise KeyError(f"Unknown statement id {statement.id}")
        self.statements[statement.id] = statement

    def list_statements(self) -> list[StatementNode]:
        return list(self.statements.values())

    def statements_by_key(self, subject: str, relation: str) -> list[StatementNode]:
        ids = self.statement_keys.get((subject, relation), [])
        return [self.statements[sid] for sid in ids]

    def statements_at_time(
        self,
        at_time: datetime,
        ingestion_as_of: datetime | None = None,
        entity_id: str | None = None,
    ) -> list[StatementNode]:
        results: list[StatementNode] = []
        for statement in self.statements.values():
            if entity_id and entity_id not in (statement.subject, statement.object):
                continue
            if statement.valid_from > at_time:
                continue
            if statement.valid_to is not None and statement.valid_to <= at_time:
                continue
            if ingestion_as_of and statement.ingestion_time > ingestion_as_of:
                continue
            results.append(statement)
        return results

    def neighbors(self, entity_id: str, hops: int = 1, limit: int = 50) -> dict[str, list[StatementNode]]:
        if entity_id not in self.entities:
            return {}
        queue = deque([(entity_id, 0)])
        seen = {entity_id}
        out: dict[str, list[StatementNode]] = defaultdict(list)

        while queue and sum(len(v) for v in out.values()) < limit:
            current, depth = queue.popleft()
            if depth > hops:
                continue
            for statement_id in self.entity_edges.get(current, []):
                stmt = self.statements[statement_id]
                out[current].append(stmt)
                other = stmt.object if stmt.subject == current else stmt.subject
                if other not in seen and depth < hops:
                    seen.add(other)
                    queue.append((other, depth + 1))
        return dict(out)
