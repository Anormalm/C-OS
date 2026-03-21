from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from cos.core.models import (
    EvaluationRunRequest,
    EvaluationRunResponse,
    IngestionRequest,
    RetrievalQueryType,
    RetrievalRequest,
)
from cos.inference.feedback import FeedbackService
from cos.vector.embeddings import HashingEmbedder


@dataclass
class BenchmarkCase:
    facts: str
    query: str
    expected_entity: str


DEFAULT_CASES = [
    BenchmarkCase(
        facts="Atlas uses Neo4j. Atlas requires GPU cluster.",
        query="What does Atlas use?",
        expected_entity="Neo4j",
    ),
    BenchmarkCase(
        facts="Beacon supports onboarding. Beacon leads to retention gains.",
        query="What supports onboarding?",
        expected_entity="Beacon",
    ),
    BenchmarkCase(
        facts="Apollo is active. 2025-03-01 Apollo is paused.",
        query="What is Apollo status?",
        expected_entity="paused",
    ),
]


class RuntimeLike(Protocol):
    settings: object
    vector_store: object
    graph_store: object

    def ingest_text(self, request: IngestionRequest): ...

    def retrieve(self, request: RetrievalRequest): ...


@dataclass
class EvaluationService:
    runtime_factory: Callable[[], RuntimeLike]
    feedback_service: FeedbackService

    def run(self, request: EvaluationRunRequest) -> EvaluationRunResponse:
        cases = self._dataset(request.dataset)
        runtime = self.runtime_factory()

        for idx, case in enumerate(cases):
            runtime.ingest_text(
                IngestionRequest(
                    text=case.facts,
                    source_type="evaluation",
                    source_uri=f"eval://{request.dataset}/{idx}",
                )
            )

        hybrid = self._evaluate(runtime, cases, request.top_k, self._hybrid_hits)
        vector = self._evaluate(runtime, cases, request.top_k, self._vector_hits)
        gain = hybrid - vector

        notes = []
        if gain > 0:
            notes.append("Hybrid retrieval outperformed vector-only baseline.")
        elif gain < 0:
            notes.append("Hybrid retrieval underperformed baseline; inspect ranking weights.")
        else:
            notes.append("Hybrid retrieval matched vector baseline on this dataset.")

        feedback = self.feedback_service.summary()
        if feedback.total:
            notes.append(
                f"Advice useful rate from collected feedback: {feedback.useful_rate * 100:.1f}%."
            )

        return EvaluationRunResponse(
            dataset=request.dataset,
            top_k=request.top_k,
            case_count=len(cases),
            hybrid_hit_at_k=round(hybrid, 4),
            vector_hit_at_k=round(vector, 4),
            gain_over_vector=round(gain, 4),
            notes=notes,
        )

    @staticmethod
    def _evaluate(
        runtime: RuntimeLike,
        cases: list[BenchmarkCase],
        top_k: int,
        scorer: Callable[[RuntimeLike, BenchmarkCase, int], bool],
    ) -> float:
        hits = 0
        for case in cases:
            if scorer(runtime, case, top_k):
                hits += 1
        return hits / len(cases) if cases else 0.0

    @staticmethod
    def _hybrid_hits(runtime: RuntimeLike, case: BenchmarkCase, top_k: int) -> bool:
        results = runtime.retrieve(
            RetrievalRequest(
                query=case.query,
                query_type=RetrievalQueryType.factual,
                top_k=top_k,
            )
        )
        expected = case.expected_entity.lower()
        for result in results:
            payload = result.payload
            subject = EvaluationService._label(runtime, payload.get("subject")).lower()
            obj = EvaluationService._label(runtime, payload.get("object")).lower()
            if expected in {subject, obj}:
                return True
        return False

    @staticmethod
    def _vector_hits(runtime: RuntimeLike, case: BenchmarkCase, top_k: int) -> bool:
        embedder = HashingEmbedder(dim=runtime.settings.embedding_dim)
        query_vec = embedder.embed(case.query)
        ranked = runtime.vector_store.query(query_vec, top_k=top_k * 3)
        expected = case.expected_entity.lower()

        count = 0
        for item_id, _score, metadata in ranked:
            if metadata.get("kind") != "statement":
                continue
            statement = runtime.graph_store.get_statement(item_id)
            if statement is None:
                continue
            subject = EvaluationService._label(runtime, statement.subject).lower()
            obj = EvaluationService._label(runtime, statement.object).lower()
            count += 1
            if expected in {subject, obj}:
                return True
            if count >= top_k:
                break
        return False

    @staticmethod
    def _label(runtime: RuntimeLike, entity_id: str | None) -> str:
        if not entity_id:
            return ""
        entity = runtime.graph_store.get_entity(entity_id)
        return entity.name if entity else entity_id

    @staticmethod
    def _dataset(dataset: str) -> list[BenchmarkCase]:
        if dataset == "default":
            return DEFAULT_CASES
        raise ValueError(f"Unknown dataset: {dataset}")
