from __future__ import annotations

from typing import Any

import numpy as np

from cos.vector.base import VectorStore


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._vectors: dict[str, np.ndarray] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    def upsert(self, item_id: str, vector: list[float], metadata: dict[str, Any]) -> None:
        self._vectors[item_id] = np.array(vector, dtype=np.float32)
        self._metadata[item_id] = metadata

    def query(self, vector: list[float], top_k: int = 10) -> list[tuple[str, float, dict[str, Any]]]:
        if not self._vectors:
            return []
        q = np.array(vector, dtype=np.float32)
        q_norm = np.linalg.norm(q) or 1.0
        ranked: list[tuple[str, float, dict[str, Any]]] = []
        for item_id, v in self._vectors.items():
            denom = (np.linalg.norm(v) or 1.0) * q_norm
            score = float(np.dot(v, q) / denom)
            ranked.append((item_id, score, self._metadata[item_id]))
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:top_k]
