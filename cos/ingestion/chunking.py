from __future__ import annotations

from cos.core.models import Chunk


def chunk_text(
    text: str,
    document_id: str,
    max_chars: int = 1000,
    overlap: int = 120,
) -> list[Chunk]:
    if max_chars <= 0:
        raise ValueError("max_chars must be > 0")
    if overlap >= max_chars:
        raise ValueError("overlap must be smaller than max_chars")

    chunks: list[Chunk] = []
    start = 0
    sequence = 0

    while start < len(text):
        end = min(len(text), start + max_chars)
        window = text[start:end].strip()
        if window:
            chunks.append(
                Chunk(
                    document_id=document_id,
                    text=window,
                    sequence=sequence,
                    metadata={"char_start": start, "char_end": end},
                )
            )
            sequence += 1
        if end >= len(text):
            break
        start = end - overlap

    return chunks
