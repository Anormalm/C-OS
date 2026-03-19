from cos.configs.settings import Settings
from cos.core.models import IngestionRequest, RetrievalQueryType, RetrievalRequest
from cos.runtime import COSRuntime


def test_hybrid_retrieval_returns_relevant_statements():
    runtime = COSRuntime(Settings())
    text = """
    Atlas uses Neo4j.
    Atlas uses FAISS.
    Atlas requires GPU cluster.
    """
    runtime.ingest_text(IngestionRequest(text=text, source_type="note", source_uri="test://retrieval"))

    results = runtime.retrieve(
        RetrievalRequest(query="What does Atlas use?", query_type=RetrievalQueryType.factual, top_k=5)
    )
    assert results
    joined = " ".join(str(r.payload) for r in results)
    assert "uses" in joined
