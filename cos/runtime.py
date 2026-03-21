from __future__ import annotations

from datetime import datetime, timezone

from cos.configs.settings import Settings
from cos.core.models import (
    AdviceRequest,
    AdviceResponse,
    AdviceFeedbackEvent,
    AdviceFeedbackRequest,
    AdviceFeedbackSummary,
    CheckinRequest,
    CheckinResponse,
    Document,
    EvaluationRunRequest,
    EvaluationRunResponse,
    OnboardingStatus,
    IngestionRequest,
    IngestionResponse,
    QualityDashboardResponse,
    RetrievalRequest,
    RetrievalResult,
    StatementNode,
    TemporalQueryRequest,
    WeeklySummaryRequest,
    WeeklySummaryResponse,
)
from cos.diagnostics.metrics import LatencyTimer, MetricsRegistry
from cos.inference.evaluation import EvaluationService
from cos.extraction.extractor import ExtractionService
from cos.graph.base import GraphStore
from cos.graph.in_memory import InMemoryGraphStore
from cos.graph.neo4j_store import Neo4jGraphStore
from cos.inference.advice import AdviceService
from cos.inference.feedback import FeedbackService
from cos.ingestion.service import IngestionService
from cos.inference.insights import InsightService
from cos.inference.onboarding import OnboardingService
from cos.inference.weekly_summary import WeeklySummaryService
from cos.resolution.service import ResolutionService
from cos.temporal.queries import TemporalQueryService
from cos.temporal.trajectory import TrajectoryAnalyzer
from cos.vector.base import VectorStore
from cos.vector.embeddings import HashingEmbedder
from cos.vector.faiss_store import FaissVectorStore
from cos.vector.hybrid_retriever import HybridRetriever
from cos.vector.in_memory import InMemoryVectorStore


class COSRuntime:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.metrics = MetricsRegistry()
        self.graph_store = self._build_graph_store()
        self.vector_store = self._build_vector_store()
        self.embedder = HashingEmbedder(dim=settings.embedding_dim)

        self.ingestion = IngestionService(settings)
        self.extraction = ExtractionService()
        self.resolution = ResolutionService(self.graph_store)
        self.temporal = TemporalQueryService(self.graph_store)
        self.trajectories = TrajectoryAnalyzer(self.graph_store)
        self.retriever = HybridRetriever(self.graph_store, self.vector_store, self.embedder)
        self.insights = InsightService(self.graph_store, self.metrics)
        self.advice = AdviceService(self.graph_store, self.insights)
        self.feedback = FeedbackService(log_path=settings.feedback_log_path)
        self.onboarding = OnboardingService(self.metrics)
        self.weekly_summary_service = WeeklySummaryService(
            graph_store=self.graph_store,
            advice_service=self.advice,
            feedback_service=self.feedback,
        )
        self.evaluation = EvaluationService(
            runtime_factory=lambda: COSRuntime(settings),
            feedback_service=self.feedback,
        )
        self.last_evaluation: EvaluationRunResponse | None = None

    def _build_graph_store(self) -> GraphStore:
        if self.settings.graph_backend.lower() == "neo4j":
            return Neo4jGraphStore(
                uri=self.settings.neo4j_uri,
                user=self.settings.neo4j_user,
                password=self.settings.neo4j_password,
            )
        return InMemoryGraphStore()

    def _build_vector_store(self) -> VectorStore:
        if self.settings.vector_backend.lower() == "faiss":
            return FaissVectorStore(dim=self.settings.embedding_dim)
        return InMemoryVectorStore()

    def ingest_text(self, request: IngestionRequest) -> IngestionResponse:
        with LatencyTimer(self.metrics, "ingestion_ms"):
            document = Document(
                source_type=request.source_type,
                source_uri=request.source_uri,
                content=request.text,
                metadata=request.metadata,
            )
            chunks = self.ingestion.ingest(document)

            triple_count = 0
            statement_count = 0
            contradiction_count = 0

            for chunk in chunks:
                triples = self.extraction.extract_triples(chunk, default_timestamp=request.valid_from)
                triple_count += len(triples)

                for triple in triples:
                    statement, created_count, resolved_count, contradictions = self.resolution.resolve_triple(
                        triple=triple,
                        source=document.source_uri or document.source_type,
                        default_valid_from=request.valid_from or datetime.now(timezone.utc),
                    )
                    self.metrics.inc("entity_created", created_count)
                    self.metrics.inc("entity_resolved_existing", resolved_count)
                    self.metrics.inc("contradictions", contradictions)

                    self._index_statement(statement)
                    self._index_entity(statement.subject)
                    self._index_entity(statement.object)

                    statement_count += 1
                    contradiction_count += contradictions

            self.metrics.inc("documents_ingested")
            self.metrics.inc("chunks_ingested", len(chunks))
            self.metrics.inc("triples_extracted", triple_count)
            self.metrics.inc("statements_created", statement_count)

            return IngestionResponse(
                document_id=document.id,
                chunk_count=len(chunks),
                triple_count=triple_count,
                statement_count=statement_count,
                contradictions=contradiction_count,
            )

    def _index_statement(self, statement: StatementNode) -> None:
        subject = self.graph_store.get_entity(statement.subject)
        obj = self.graph_store.get_entity(statement.object)
        statement_text = f"{subject.name if subject else statement.subject} {statement.relation} {obj.name if obj else statement.object}"
        embedding = self.embedder.embed(statement_text)
        statement.embedding = embedding
        self.graph_store.update_statement(statement)
        self.vector_store.upsert(
            statement.id,
            embedding,
            metadata={
                "kind": "statement",
                "subject": statement.subject,
                "relation": statement.relation,
                "object": statement.object,
            },
        )

    def _index_entity(self, entity_id: str) -> None:
        entity = self.graph_store.get_entity(entity_id)
        if entity is None:
            return
        if entity.embedding is None:
            entity.embedding = self.embedder.embed(entity.name)
            self.graph_store.upsert_entity(entity)
        self.vector_store.upsert(entity.id, entity.embedding, metadata={"kind": "entity", "name": entity.name})

    def retrieve(self, request: RetrievalRequest) -> list[RetrievalResult]:
        with LatencyTimer(self.metrics, "retrieval_ms"):
            self.metrics.inc("retrieval_queries")
            return self.retriever.retrieve(request.query, request.query_type, request.top_k)

    def temporal_query(self, request: TemporalQueryRequest) -> list[StatementNode]:
        with LatencyTimer(self.metrics, "temporal_query_ms"):
            entity_id = None
            if request.entity:
                candidates = self.graph_store.find_entities_by_name(request.entity, limit=1)
                entity_id = candidates[0].id if candidates else None
            return self.temporal.truth_at(request.at_time, request.ingestion_as_of, entity_id)

    def generate_advice(self, request: AdviceRequest) -> AdviceResponse:
        with LatencyTimer(self.metrics, "advice_ms"):
            return self.advice.generate(request)

    def checkin(self, request: CheckinRequest) -> CheckinResponse:
        self.metrics.inc("coach_checkins")
        ingestion = self.ingest_text(
            IngestionRequest(
                text=request.reflection,
                source_type="checkin",
                source_uri="web-ui://coach-checkin",
                metadata={"persona": request.persona.value, "focus": request.focus},
            )
        )
        advice = self.generate_advice(AdviceRequest(persona=request.persona, focus=request.focus))
        return CheckinResponse(ingestion=ingestion, advice=advice)

    def submit_feedback(self, request: AdviceFeedbackRequest) -> AdviceFeedbackEvent:
        with LatencyTimer(self.metrics, "feedback_ms"):
            event = self.feedback.add(request)
            self.metrics.inc("advice_feedback_total")
            if request.rating.value == "useful":
                self.metrics.inc("advice_feedback_useful")
            else:
                self.metrics.inc("advice_feedback_not_useful")
            return event

    def feedback_summary(self) -> AdviceFeedbackSummary:
        return self.feedback.summary()

    def onboarding_status(self) -> OnboardingStatus:
        return self.onboarding.status()

    def weekly_summary(self, request: WeeklySummaryRequest) -> WeeklySummaryResponse:
        with LatencyTimer(self.metrics, "weekly_summary_ms"):
            self.metrics.inc("weekly_summaries_generated")
            return self.weekly_summary_service.generate(request)

    def run_evaluation(self, request: EvaluationRunRequest) -> EvaluationRunResponse:
        with LatencyTimer(self.metrics, "evaluation_ms"):
            result = self.evaluation.run(request)
            self.last_evaluation = result
            self.metrics.inc("evaluation_runs")
            return result

    def quality_dashboard(self) -> QualityDashboardResponse:
        with LatencyTimer(self.metrics, "quality_dashboard_ms"):
            onboarding = self.onboarding.status()
            feedback = self.feedback.summary()
            insights = self.insights.summarize()
            snapshot = self.metrics.snapshot()
            counters = snapshot.get("counters", {})
            latency_avg = snapshot.get("latency_ms_avg", {})

            recommendations = []
            if onboarding.progress_ratio < 1.0:
                recommendations.append("Complete onboarding milestones for better model calibration.")
            if feedback.total and feedback.useful_rate < 0.6:
                recommendations.append("Advice usefulness is low; revise advice heuristics and prompts.")
            if not feedback.total:
                recommendations.append("Collect user feedback on advice to improve quality tracking.")
            if counters.get("retrieval_queries", 0) < 3:
                recommendations.append("Run more retrieval queries before judging memory quality.")
            if "retrieval_ms" in latency_avg and latency_avg["retrieval_ms"] > 500:
                recommendations.append("Retrieval latency exceeds target; optimize graph expansion weights.")
            if not recommendations:
                recommendations.append("Quality signals look healthy; continue collecting production data.")

            return QualityDashboardResponse(
                onboarding_progress=onboarding.progress_ratio,
                advice_useful_rate=feedback.useful_rate,
                retrieval_queries=counters.get("retrieval_queries", 0),
                ingestion_documents=counters.get("documents_ingested", 0),
                contradiction_rate=insights.contradiction_rate,
                deduplication_rate=insights.deduplication_rate,
                latency_ms_avg=latency_avg,
                last_evaluation=self.last_evaluation,
                recommendations=recommendations,
            )
