from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, item_id: str, vector: list[float], metadata: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def query(self, vector: list[float], top_k: int = 10) -> list[tuple[str, float, dict[str, Any]]]:
        raise NotImplementedError
