from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from cos.core.models import EntityNode, StatementNode


class GraphStore(ABC):
    @abstractmethod
    def upsert_entity(self, entity: EntityNode) -> EntityNode:
        raise NotImplementedError

    @abstractmethod
    def find_entities_by_name(self, name: str, limit: int = 5) -> list[EntityNode]:
        raise NotImplementedError

    @abstractmethod
    def get_entity(self, entity_id: str) -> EntityNode | None:
        raise NotImplementedError

    @abstractmethod
    def add_statement(self, statement: StatementNode) -> StatementNode:
        raise NotImplementedError

    @abstractmethod
    def get_statement(self, statement_id: str) -> StatementNode | None:
        raise NotImplementedError

    @abstractmethod
    def update_statement(self, statement: StatementNode) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_statements(self) -> list[StatementNode]:
        raise NotImplementedError

    @abstractmethod
    def statements_by_key(self, subject: str, relation: str) -> list[StatementNode]:
        raise NotImplementedError

    @abstractmethod
    def statements_at_time(
        self,
        at_time: datetime,
        ingestion_as_of: datetime | None = None,
        entity_id: str | None = None,
    ) -> list[StatementNode]:
        raise NotImplementedError

    @abstractmethod
    def neighbors(self, entity_id: str, hops: int = 1, limit: int = 50) -> dict[str, list[StatementNode]]:
        raise NotImplementedError
