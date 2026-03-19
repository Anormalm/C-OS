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


class CheckinRequest(BaseModel):
    reflection: str = Field(min_length=1)
    persona: UserPersona = UserPersona.general
    focus: str | None = None


class CheckinResponse(BaseModel):
    ingestion: IngestionResponse
    advice: AdviceResponse
