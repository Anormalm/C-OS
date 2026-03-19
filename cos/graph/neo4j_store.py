from __future__ import annotations

from datetime import datetime

from cos.core.models import EntityNode, StatementNode
from cos.graph.base import GraphStore

try:
    from neo4j import GraphDatabase
except ImportError:  # pragma: no cover
    GraphDatabase = None


class Neo4jGraphStore(GraphStore):
    def __init__(self, uri: str, user: str, password: str) -> None:
        if GraphDatabase is None:
            raise RuntimeError("neo4j package not installed")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self.driver.close()

    def upsert_entity(self, entity: EntityNode) -> EntityNode:
        query = """
        MERGE (e:Entity {name_key: toLower($name)})
        ON CREATE SET e.id = $id, e.name = $name, e.aliases = $aliases, e.created_at = datetime($created_at)
        ON MATCH SET e.aliases = apoc.coll.toSet(coalesce(e.aliases, []) + $aliases), e.updated_at = datetime($updated_at)
        RETURN coalesce(e.id, $id) AS id, e.name AS name, coalesce(e.aliases, []) AS aliases
        """
        with self.driver.session() as session:
            row = session.run(
                query,
                id=entity.id,
                name=entity.name,
                aliases=entity.aliases,
                created_at=entity.created_at.isoformat(),
                updated_at=entity.updated_at.isoformat(),
            ).single()
        return EntityNode(id=row["id"], name=row["name"], aliases=row["aliases"])

    def find_entities_by_name(self, name: str, limit: int = 5) -> list[EntityNode]:
        query = """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($name)
           OR any(alias IN coalesce(e.aliases, []) WHERE toLower(alias) CONTAINS toLower($name))
        RETURN e.id AS id, e.name AS name, coalesce(e.aliases, []) AS aliases
        LIMIT $limit
        """
        with self.driver.session() as session:
            rows = session.run(query, name=name, limit=limit)
            return [EntityNode(id=r["id"], name=r["name"], aliases=r["aliases"]) for r in rows]

    def get_entity(self, entity_id: str) -> EntityNode | None:
        query = "MATCH (e:Entity {id: $id}) RETURN e.id AS id, e.name AS name, coalesce(e.aliases, []) AS aliases"
        with self.driver.session() as session:
            row = session.run(query, id=entity_id).single()
        if row is None:
            return None
        return EntityNode(id=row["id"], name=row["name"], aliases=row["aliases"])

    def add_statement(self, statement: StatementNode) -> StatementNode:
        query = """
        MATCH (s:Entity {id: $subject}), (o:Entity {id: $object})
        CREATE (st:Statement {
            id: $id,
            relation: $relation,
            valid_from: datetime($valid_from),
            valid_to: CASE WHEN $valid_to IS NULL THEN NULL ELSE datetime($valid_to) END,
            ingestion_time: datetime($ingestion_time),
            source: $source,
            confidence: $confidence,
            status: $status,
            contradiction_of: $contradiction_of
        })
        CREATE (s)-[:ASSERTS]->(st)-[:POINTS_TO]->(o)
        """
        with self.driver.session() as session:
            session.run(
                query,
                id=statement.id,
                subject=statement.subject,
                object=statement.object,
                relation=statement.relation,
                valid_from=statement.valid_from.isoformat(),
                valid_to=statement.valid_to.isoformat() if statement.valid_to else None,
                ingestion_time=statement.ingestion_time.isoformat(),
                source=statement.source,
                confidence=statement.confidence,
                status=statement.status.value,
                contradiction_of=statement.contradiction_of,
            ).consume()
        return statement

    def get_statement(self, statement_id: str) -> StatementNode | None:
        query = """
        MATCH (s:Entity)-[:ASSERTS]->(st:Statement {id: $id})-[:POINTS_TO]->(o:Entity)
        RETURN st.id AS id, s.id AS subject, st.relation AS relation, o.id AS object,
               st.valid_from AS valid_from, st.valid_to AS valid_to, st.ingestion_time AS ingestion_time,
               st.source AS source, st.confidence AS confidence, st.status AS status, st.contradiction_of AS contradiction_of
        """
        with self.driver.session() as session:
            row = session.run(query, id=statement_id).single()
        if row is None:
            return None
        return self._statement_from_row(row)

    def update_statement(self, statement: StatementNode) -> None:
        query = """
        MATCH (st:Statement {id: $id})
        SET st.valid_to = CASE WHEN $valid_to IS NULL THEN NULL ELSE datetime($valid_to) END,
            st.status = $status,
            st.contradiction_of = $contradiction_of
        """
        with self.driver.session() as session:
            session.run(
                query,
                id=statement.id,
                valid_to=statement.valid_to.isoformat() if statement.valid_to else None,
                status=statement.status.value,
                contradiction_of=statement.contradiction_of,
            ).consume()

    def list_statements(self) -> list[StatementNode]:
        query = """
        MATCH (s:Entity)-[:ASSERTS]->(st:Statement)-[:POINTS_TO]->(o:Entity)
        RETURN st.id AS id, s.id AS subject, st.relation AS relation, o.id AS object,
               st.valid_from AS valid_from, st.valid_to AS valid_to, st.ingestion_time AS ingestion_time,
               st.source AS source, st.confidence AS confidence, st.status AS status, st.contradiction_of AS contradiction_of
        """
        with self.driver.session() as session:
            rows = session.run(query)
            return [self._statement_from_row(r) for r in rows]

    def statements_by_key(self, subject: str, relation: str) -> list[StatementNode]:
        query = """
        MATCH (s:Entity {id: $subject})-[:ASSERTS]->(st:Statement {relation: $relation})-[:POINTS_TO]->(o:Entity)
        RETURN st.id AS id, s.id AS subject, st.relation AS relation, o.id AS object,
               st.valid_from AS valid_from, st.valid_to AS valid_to, st.ingestion_time AS ingestion_time,
               st.source AS source, st.confidence AS confidence, st.status AS status, st.contradiction_of AS contradiction_of
        """
        with self.driver.session() as session:
            rows = session.run(query, subject=subject, relation=relation)
            return [self._statement_from_row(r) for r in rows]

    def statements_at_time(
        self,
        at_time: datetime,
        ingestion_as_of: datetime | None = None,
        entity_id: str | None = None,
    ) -> list[StatementNode]:
        query = """
        MATCH (s:Entity)-[:ASSERTS]->(st:Statement)-[:POINTS_TO]->(o:Entity)
        WHERE st.valid_from <= datetime($at_time)
          AND (st.valid_to IS NULL OR st.valid_to > datetime($at_time))
          AND ($ingestion_as_of IS NULL OR st.ingestion_time <= datetime($ingestion_as_of))
          AND ($entity_id IS NULL OR s.id = $entity_id OR o.id = $entity_id)
        RETURN st.id AS id, s.id AS subject, st.relation AS relation, o.id AS object,
               st.valid_from AS valid_from, st.valid_to AS valid_to, st.ingestion_time AS ingestion_time,
               st.source AS source, st.confidence AS confidence, st.status AS status, st.contradiction_of AS contradiction_of
        """
        with self.driver.session() as session:
            rows = session.run(
                query,
                at_time=at_time.isoformat(),
                ingestion_as_of=ingestion_as_of.isoformat() if ingestion_as_of else None,
                entity_id=entity_id,
            )
            return [self._statement_from_row(r) for r in rows]

    def neighbors(self, entity_id: str, hops: int = 1, limit: int = 50) -> dict[str, list[StatementNode]]:
        query = """
        MATCH (start:Entity {id: $entity_id})
        CALL apoc.path.expandConfig(start, {maxLevel: $hops, relationshipFilter:'ASSERTS>|POINTS_TO>', bfs:true, limit:$limit}) YIELD path
        WITH nodes(path) AS ns
        UNWIND ns AS n
        WITH DISTINCT n WHERE n:Statement
        MATCH (s:Entity)-[:ASSERTS]->(n)-[:POINTS_TO]->(o:Entity)
        RETURN n.id AS id, s.id AS subject, n.relation AS relation, o.id AS object,
               n.valid_from AS valid_from, n.valid_to AS valid_to, n.ingestion_time AS ingestion_time,
               n.source AS source, n.confidence AS confidence, n.status AS status, n.contradiction_of AS contradiction_of
        LIMIT $limit
        """
        with self.driver.session() as session:
            rows = session.run(query, entity_id=entity_id, hops=hops, limit=limit)
            statements = [self._statement_from_row(r) for r in rows]
        return {entity_id: statements}

    @staticmethod
    def _statement_from_row(row) -> StatementNode:
        def _convert(value) -> datetime | None:
            if value is None:
                return None
            if isinstance(value, datetime):
                return value
            return datetime.fromisoformat(str(value))

        return StatementNode(
            id=row["id"],
            subject=row["subject"],
            relation=row["relation"],
            object=row["object"],
            valid_from=_convert(row["valid_from"]),
            valid_to=_convert(row["valid_to"]),
            ingestion_time=_convert(row["ingestion_time"]),
            source=row["source"],
            confidence=row["confidence"],
            status=row["status"],
            contradiction_of=row["contradiction_of"],
        )
