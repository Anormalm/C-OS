from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StatementStatus(str, Enum):
    asserted = "asserted"
    contradicted = "contradicted"
    superseded = "superseded"


class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_type: str
    source_uri: str | None = None
    content: str
    ingestion_time: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Chunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    text: str
    sequence: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntityNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    aliases: list[str] = Field(default_factory=list)
    embedding: list[float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class StatementNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    subject: str
    relation: str
    object: str
    embedding: list[float] | None = None
    valid_from: datetime
    valid_to: datetime | None = None
    ingestion_time: datetime = Field(default_factory=utc_now)
    source: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    status: StatementStatus = StatementStatus.asserted
    contradiction_of: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str]:
        return self.subject, self.relation


class ExtractedTriple(BaseModel):
    subject: str
    relation: str
    object: str
    timestamp: datetime | None = None
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class RetrievalQueryType(str, Enum):
    factual = "factual"
    exploratory = "exploratory"
    temporal = "temporal"


class RetrievalResult(BaseModel):
    statement_id: str | None = None
    entity_id: str | None = None
    score: float
    explanation: str
    payload: dict[str, Any]


class IngestionRequest(BaseModel):
    text: str
    source_type: str = "note"
    source_uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    valid_from: datetime | None = None


class RetrievalRequest(BaseModel):
    query: str
    query_type: RetrievalQueryType = RetrievalQueryType.exploratory
    top_k: int = Field(default=10, ge=1, le=100)


class TemporalQueryRequest(BaseModel):
    at_time: datetime
    ingestion_as_of: datetime | None = None
    entity: str | None = None


class IngestionResponse(BaseModel):
    document_id: str
    chunk_count: int
    triple_count: int
    statement_count: int
    contradictions: int


class InsightSummary(BaseModel):
    recurring_topics: list[dict[str, Any]]
    abandoned_topics: list[dict[str, Any]]
    contradiction_rate: float
    deduplication_rate: float
    notes: list[str]


class UserPersona(str, Enum):
    general = "general"
    student = "student"
    founder = "founder"
    manager = "manager"
    creator = "creator"


class AdvicePriority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class AdviceItem(BaseModel):
    title: str
    why: str
    actions: list[str]
    evidence: list[str]
    priority: AdvicePriority
    confidence: float = Field(ge=0.0, le=1.0)


class AdviceRequest(BaseModel):
    persona: UserPersona = UserPersona.general
    focus: str | None = None
    horizon_days: int = Field(default=7, ge=1, le=90)


class AdviceResponse(BaseModel):
    generated_at: datetime = Field(default_factory=utc_now)
    persona: UserPersona
    focus: str | None = None
    advice: list[AdviceItem]
    caution: str


class NextStepResponse(BaseModel):
    generated_at: datetime = Field(default_factory=utc_now)
    persona: UserPersona
    focus: str | None = None
    title: str
    action: str
    why: str
    confidence: float = Field(ge=0.0, le=1.0)
    estimated_minutes: int = Field(ge=5, le=120)
    alternatives: list[str] = Field(default_factory=list)
    caution: str


class CheckinRequest(BaseModel):
    reflection: str = Field(min_length=1)
    persona: UserPersona = UserPersona.general
    focus: str | None = None


class CheckinResponse(BaseModel):
    ingestion: IngestionResponse
    advice: AdviceResponse


class FeedbackRating(str, Enum):
    useful = "useful"
    not_useful = "not_useful"


class AdviceFeedbackRequest(BaseModel):
    advice_title: str = Field(min_length=1)
    rating: FeedbackRating
    persona: UserPersona = UserPersona.general
    note: str | None = None
    context_focus: str | None = None


class AdviceFeedbackEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=utc_now)
    advice_title: str
    rating: FeedbackRating
    persona: UserPersona
    note: str | None = None
    context_focus: str | None = None


class AdviceFeedbackSummary(BaseModel):
    total: int
    useful: int
    not_useful: int
    useful_rate: float
    top_liked_advice: list[dict[str, Any]]
    top_disliked_advice: list[dict[str, Any]]


class OnboardingStep(BaseModel):
    id: str
    title: str
    target: int
    completed: int
    done: bool
    helper: str


class OnboardingStatus(BaseModel):
    started: bool
    completed: bool
    progress_ratio: float
    steps: list[OnboardingStep]
    recommended_next_step: str


class WeeklySummaryRequest(BaseModel):
    persona: UserPersona = UserPersona.general
    days: int = Field(default=7, ge=3, le=30)
    focus: str | None = None


class WeeklySummaryResponse(BaseModel):
    generated_at: datetime = Field(default_factory=utc_now)
    period_start: datetime
    period_end: datetime
    persona: UserPersona
    focus: str | None = None
    highlights: list[str]
    risks: list[str]
    wins: list[str]
    recommended_next_actions: list[str]
    stats: dict[str, Any]


class EvaluationRunRequest(BaseModel):
    top_k: int = Field(default=3, ge=1, le=10)
    dataset: str = "default"


class EvaluationRunResponse(BaseModel):
    generated_at: datetime = Field(default_factory=utc_now)
    dataset: str
    top_k: int
    case_count: int
    hybrid_hit_at_k: float
    vector_hit_at_k: float
    gain_over_vector: float
    notes: list[str] = Field(default_factory=list)


class QualityDashboardResponse(BaseModel):
    generated_at: datetime = Field(default_factory=utc_now)
    onboarding_progress: float
    advice_useful_rate: float
    retrieval_queries: int
    ingestion_documents: int
    contradiction_rate: float
    deduplication_rate: float
    latency_ms_avg: dict[str, float]
    last_evaluation: EvaluationRunResponse | None = None
    recommendations: list[str]


class ActionCompletionRequest(BaseModel):
    action_text: str = Field(min_length=1)
    advice_title: str | None = None
    persona: UserPersona = UserPersona.general
    focus: str | None = None
    note: str | None = None


class ActionCompletionEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=utc_now)
    action_text: str
    advice_title: str | None = None
    persona: UserPersona
    focus: str | None = None
    note: str | None = None


class TodayBriefResponse(BaseModel):
    generated_at: datetime = Field(default_factory=utc_now)
    reminder: str
    next_action: str
    weekly_snippet: str
    onboarding_progress: float
    completed_actions_last_7d: int
