from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import exp

from cos.core.models import RetrievalQueryType, RetrievalResult, StatementNode
from cos.graph.base import GraphStore
from cos.vector.base import VectorStore
from cos.vector.embeddings import HashingEmbedder


def recency_score(statement: StatementNode, now: datetime) -> float:
    age_days = max((now - statement.ingestion_time).days, 0)
    return exp(-age_days / 365.0)


@dataclass
class HybridRetriever:
    graph_store: GraphStore
    vector_store: VectorStore
    embedder: HashingEmbedder

    def retrieve(
        self,
        query: str,
        query_type: RetrievalQueryType,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        query_vec = self.embedder.embed(query)
        candidates = self.vector_store.query(query_vec, top_k=top_k * 3)
        now = datetime.now(timezone.utc)

        weights = {
            RetrievalQueryType.factual: (0.4, 0.4, 0.2),
            RetrievalQueryType.exploratory: (0.6, 0.3, 0.1),
            RetrievalQueryType.temporal: (0.3, 0.3, 0.4),
        }[query_type]
        w_vector, w_graph, w_temporal = weights

        scored: list[RetrievalResult] = []
        for item_id, vec_score, metadata in candidates:
            kind = metadata.get("kind")
            if kind == "statement":
                statement = self.graph_store.get_statement(item_id)
                if statement is None:
                    continue
                graph_context = self.graph_store.neighbors(statement.subject, hops=1, limit=10)
                graph_score = min(sum(len(v) for v in graph_context.values()) / 10.0, 1.0)
                temporal = recency_score(statement, now)
                final = (w_vector * vec_score) + (w_graph * graph_score) + (w_temporal * temporal)
                scored.append(
                    RetrievalResult(
                        statement_id=statement.id,
                        score=final,
                        explanation=f"vector={vec_score:.3f}, graph={graph_score:.3f}, temporal={temporal:.3f}",
                        payload=statement.model_dump(mode="json"),
                    )
                )
            elif kind == "entity":
                entity = self.graph_store.get_entity(item_id)
                if entity is None:
                    continue
                graph_context = self.graph_store.neighbors(entity.id, hops=1, limit=20)
                graph_score = min(sum(len(v) for v in graph_context.values()) / 20.0, 1.0)
                final = (w_vector * vec_score) + (w_graph * graph_score)
                scored.append(
                    RetrievalResult(
                        entity_id=entity.id,
                        score=final,
                        explanation=f"vector={vec_score:.3f}, graph={graph_score:.3f}",
                        payload=entity.model_dump(mode="json"),
                    )
                )

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]
