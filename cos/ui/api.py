from __future__ import annotations

from fastapi import APIRouter, HTTPException

from cos.core.models import AdviceRequest, CheckinRequest, IngestionRequest, RetrievalRequest, TemporalQueryRequest
from cos.ingestion.async_queue import AsyncIngestionQueue
from cos.runtime import COSRuntime


def create_router(runtime: COSRuntime, async_queue: AsyncIngestionQueue) -> APIRouter:
    router = APIRouter()

    def _entity_label(entity_id: str) -> str:
        entity = runtime.graph_store.get_entity(entity_id)
        return entity.name if entity else entity_id

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/ingest/text")
    def ingest_text(request: IngestionRequest):
        return runtime.ingest_text(request)

    @router.post("/ingest/text/async")
    async def ingest_text_async(request: IngestionRequest):
        job_id = await async_queue.submit(request)
        return {"job_id": job_id, "status": "queued"}

    @router.get("/ingest/jobs/{job_id}")
    def ingestion_job(job_id: str):
        job = async_queue.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        return job

    @router.post("/query/retrieve")
    def retrieve(request: RetrievalRequest):
        results = runtime.retrieve(request)
        output = []
        for result in results:
            row = result.model_dump(mode="json")
            payload = row.get("payload", {})
            if "subject" in payload:
                payload["subject_label"] = _entity_label(payload["subject"])
            if "object" in payload:
                payload["object_label"] = _entity_label(payload["object"])
            row["payload"] = payload
            output.append(row)
        return output

    @router.post("/query/temporal")
    def temporal(request: TemporalQueryRequest):
        statements = runtime.temporal_query(request)
        output = []
        for statement in statements:
            row = statement.model_dump(mode="json")
            row["subject_label"] = _entity_label(statement.subject)
            row["object_label"] = _entity_label(statement.object)
            output.append(row)
        return output

    @router.get("/insights/summary")
    def insights():
        return runtime.insights.summarize()

    @router.get("/coach/personas")
    def coach_personas():
        return runtime.advice.persona_catalog()

    @router.post("/coach/advice")
    def coach_advice(request: AdviceRequest):
        return runtime.generate_advice(request)

    @router.post("/coach/checkin")
    def coach_checkin(request: CheckinRequest):
        return runtime.checkin(request)

    @router.get("/diagnostics/metrics")
    def metrics():
        return runtime.metrics.snapshot()

    @router.get("/graph/entity/{entity_id}")
    def graph_neighbors(entity_id: str, hops: int = 1, limit: int = 50):
        entity = runtime.graph_store.get_entity(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="entity not found")
        return {
            "entity": entity.model_dump(mode="json"),
            "neighbors": {
                key: [statement.model_dump(mode="json") for statement in statements]
                for key, statements in runtime.graph_store.neighbors(entity_id, hops=hops, limit=limit).items()
            },
        }

    @router.get("/timeline/entity/{entity_id}")
    def timeline(entity_id: str):
        entity = runtime.graph_store.get_entity(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="entity not found")
        trajectory = runtime.trajectories.entity_trajectory(entity_id)
        return {
            "entity": entity.model_dump(mode="json"),
            "trajectory": [statement.model_dump(mode="json") for statement in trajectory],
        }

    return router
