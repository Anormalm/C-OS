from __future__ import annotations

from dataclasses import dataclass

from cos.configs.settings import Settings
from cos.core.models import IngestionRequest, RetrievalQueryType, RetrievalRequest
from cos.runtime import COSRuntime
from cos.vector.embeddings import HashingEmbedder


@dataclass
class BenchmarkCase:
    facts: str
    query: str
    expected_object: str


CASES = [
    BenchmarkCase(
        facts="Atlas uses Neo4j. Atlas requires GPU cluster.",
        query="What does Atlas use?",
        expected_object="Neo4j",
    ),
    BenchmarkCase(
        facts="Beacon supports onboarding. Beacon leads to retention gains.",
        query="What supports onboarding?",
        expected_object="Beacon",
    ),
]


def vector_only_rank(runtime: COSRuntime, query: str, top_k: int = 5) -> list[str]:
    embedder = HashingEmbedder(dim=runtime.settings.embedding_dim)
    query_vec = embedder.embed(query)
    ranked = runtime.vector_store.query(query_vec, top_k=top_k)
    ids = [item_id for item_id, _score, metadata in ranked if metadata.get("kind") == "statement"]
    out = []
    for statement_id in ids:
        statement = runtime.graph_store.get_statement(statement_id)
        if statement is None:
            continue
        entity = runtime.graph_store.get_entity(statement.object)
        out.append(entity.name if entity else statement.object)
    return out


def hybrid_rank(runtime: COSRuntime, query: str, top_k: int = 5) -> list[str]:
    results = runtime.retrieve(
        RetrievalRequest(query=query, query_type=RetrievalQueryType.factual, top_k=top_k)
    )
    out = []
    for result in results:
        payload = result.payload
        object_id = payload.get("object")
        if object_id is None:
            continue
        entity = runtime.graph_store.get_entity(object_id)
        out.append(entity.name if entity else object_id)
    return out


def evaluate_hit_at_k(rank_fn, runtime: COSRuntime, cases: list[BenchmarkCase], k: int = 3) -> float:
    hits = 0
    for case in cases:
        ranked = rank_fn(runtime, case.query, top_k=k)
        if case.expected_object in ranked[:k]:
            hits += 1
    return hits / len(cases)


def run() -> None:
    runtime = COSRuntime(Settings())
    for idx, case in enumerate(CASES):
        runtime.ingest_text(
            IngestionRequest(
                text=case.facts,
                source_type="benchmark",
                source_uri=f"benchmark://{idx}",
            )
        )

    hybrid = evaluate_hit_at_k(hybrid_rank, runtime, CASES, k=3)
    vector = evaluate_hit_at_k(vector_only_rank, runtime, CASES, k=3)

    print("Benchmark: Retrieval Hit@3")
    print(f"Hybrid: {hybrid:.2f}")
    print(f"Vector only: {vector:.2f}")


if __name__ == "__main__":
    run()
