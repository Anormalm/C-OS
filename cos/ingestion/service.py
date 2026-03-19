from __future__ import annotations

from dataclasses import dataclass

from cos.configs.settings import Settings
from cos.core.models import Chunk, Document
from cos.ingestion.chunking import chunk_text
from cos.ingestion.preprocessing import normalize_text


@dataclass
class IngestionService:
    settings: Settings

    def ingest(self, document: Document) -> list[Chunk]:
        normalized = normalize_text(document.content)
        return chunk_text(
            normalized,
            document_id=document.id,
            max_chars=self.settings.chunk_size,
            overlap=self.settings.chunk_overlap,
        )
