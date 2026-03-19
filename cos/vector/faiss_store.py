from __future__ import annotations

from typing import Any

import numpy as np

from cos.vector.base import VectorStore

try:
    import faiss
except ImportError:  # pragma: no cover
    faiss = None


class FaissVectorStore(VectorStore):
    def __init__(self, dim: int) -> None:
        if faiss is None:
            raise RuntimeError("faiss-cpu package not installed")
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.ids: list[str] = []
        self.metadata: dict[str, dict[str, Any]] = {}

    def upsert(self, item_id: str, vector: list[float], metadata: dict[str, Any]) -> None:
        arr = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(arr) or 1.0
        arr = arr / norm
        if item_id in self.metadata:
            # FAISS IndexFlat does not support true update; append-only fallback.
            self.metadata[item_id] = metadata
            return
        self.index.add(arr.reshape(1, -1))
        self.ids.append(item_id)
        self.metadata[item_id] = metadata

    def query(self, vector: list[float], top_k: int = 10) -> list[tuple[str, float, dict[str, Any]]]:
        if not self.ids:
            return []
        q = np.array(vector, dtype=np.float32)
        q = (q / (np.linalg.norm(q) or 1.0)).reshape(1, -1)
        scores, indices = self.index.search(q, top_k)
        out = []
        for idx, score in zip(indices[0], scores[0], strict=False):
            if idx < 0 or idx >= len(self.ids):
                continue
            item_id = self.ids[idx]
            out.append((item_id, float(score), self.metadata[item_id]))
        return out
