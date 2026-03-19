from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from cos.core.models import Chunk, ExtractedTriple
from cos.extraction.temporal import extract_timestamp

RELATION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\s*(.+?)\s+(?:is|are|was|were)\s+(.+?)\s*$", flags=re.IGNORECASE), "is"),
    (re.compile(r"^\s*(.+?)\s+uses\s+(.+?)\s*$", flags=re.IGNORECASE), "uses"),
    (re.compile(r"^\s*(.+?)\s+requires\s+(.+?)\s*$", flags=re.IGNORECASE), "requires"),
    (re.compile(r"^\s*(.+?)\s+causes\s+(.+?)\s*$", flags=re.IGNORECASE), "causes"),
    (re.compile(r"^\s*(.+?)\s+supports\s+(.+?)\s*$", flags=re.IGNORECASE), "supports"),
    (re.compile(r"^\s*(.+?)\s+leads to\s+(.+?)\s*$", flags=re.IGNORECASE), "leads_to"),
    (re.compile(r"^\s*(.+?)\s*->\s*(.+?)\s*$", flags=re.IGNORECASE), "related_to"),
]

LEADING_DATE_RE = re.compile(
    r"^\s*(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})[\s,:-]+"
)


def split_sentences(text: str) -> list[str]:
    lines = [line.strip(" -\t") for line in text.splitlines() if line.strip()]
    sentences: list[str] = []
    for line in lines:
        parts = re.split(r"(?<=[.!?])\s+", line)
        for part in parts:
            cleaned = part.strip()
            if cleaned:
                sentences.append(cleaned)
    return sentences


def normalize_atom(value: str) -> str:
    value = value.strip(" .,:;()[]{}\"'")
    value = re.sub(r"\s+", " ", value)
    return value[:200]


@dataclass
class ExtractionService:
    default_confidence: float = 0.73

    def extract_triples(self, chunk: Chunk, default_timestamp: datetime | None = None) -> list[ExtractedTriple]:
        triples: list[ExtractedTriple] = []
        for sentence in split_sentences(chunk.text):
            sentence_ts = extract_timestamp(sentence) or default_timestamp
            relation_sentence = LEADING_DATE_RE.sub("", sentence).strip()
            for pattern, relation in RELATION_PATTERNS:
                match = pattern.match(relation_sentence)
                if not match:
                    continue
                subject = normalize_atom(match.group(1))
                obj = normalize_atom(match.group(2))
                if not subject or not obj or subject == obj:
                    continue
                triples.append(
                    ExtractedTriple(
                        subject=subject,
                        relation=relation,
                        object=obj,
                        timestamp=sentence_ts,
                        confidence=self.default_confidence,
                    )
                )
                break
        return triples
