from __future__ import annotations

from datetime import datetime, timezone

from cos.configs.settings import get_settings
from cos.core.models import IngestionRequest, RetrievalQueryType, RetrievalRequest
from cos.runtime import COSRuntime


def run_demo() -> None:
    runtime = COSRuntime(get_settings())
    sample = """
    2025-01-02 Project Atlas is active.
    Project Atlas uses LangGraph.
    Project Atlas requires GPU infrastructure.
    2025-03-01 Project Atlas is paused.
    """
    response = runtime.ingest_text(
        IngestionRequest(
            text=sample,
            source_type="note",
            source_uri="demo://sample",
            valid_from=datetime.now(timezone.utc),
        )
    )
    print("Ingestion:", response.model_dump())
    results = runtime.retrieve(
        RetrievalRequest(
            query="What is Atlas using?",
            query_type=RetrievalQueryType.factual,
            top_k=5,
        )
    )
    print("Retrieval:")
    for result in results:
        print(result.model_dump())


if __name__ == "__main__":
    run_demo()
