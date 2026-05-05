from __future__ import annotations

from fastapi import APIRouter, HTTPException

from cos.core.models import (
    ActionCompletionRequest,
    AdviceFeedbackRequest,
    AdviceRequest,
    CheckinRequest,
    EvaluationRunRequest,
    IngestionRequest,
    RetrievalRequest,
    TemporalQueryRequest,
    WeeklySummaryRequest,
)
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

    @router.post("/coach/next-step")
    def coach_next_step(request: AdviceRequest):
        return runtime.next_step(request)

    @router.post("/coach/checkin")
    def coach_checkin(request: CheckinRequest):
        return runtime.checkin(request)

    @router.post("/coach/feedback")
    def coach_feedback(request: AdviceFeedbackRequest):
        return runtime.submit_feedback(request)

    @router.get("/coach/feedback/summary")
    def coach_feedback_summary():
        return runtime.feedback_summary()

    @router.get("/onboarding/status")
    def onboarding_status():
        return runtime.onboarding_status()

    @router.post("/onboarding/starter-pack")
    def onboarding_starter_pack():
        starter_notes = [
            "Project Atlas is active. Atlas requires clear milestones.",
            "I struggle with consistency when tasks are too large.",
            "Breaking work into one-day tasks improves execution.",
            "I tend to pause projects when dependencies are unclear.",
            "Weekly reflection helps me restart paused work faster.",
        ]
        ingested = []
        for idx, note in enumerate(starter_notes):
            ingested.append(
                runtime.ingest_text(
                    IngestionRequest(
                        text=note,
                        source_type="onboarding",
                        source_uri=f"onboarding://starter-{idx}",
                    )
                ).model_dump(mode="json")
            )
        return {"ingested": len(ingested), "status": runtime.onboarding_status()}

    @router.post("/summary/weekly")
    def weekly_summary(request: WeeklySummaryRequest):
        return runtime.weekly_summary(request)

    @router.get("/today/brief")
    def today_brief():
        return runtime.today_brief()

    @router.post("/today/action")
    def today_action(request: ActionCompletionRequest):
        return runtime.complete_action(request)

    @router.post("/evaluation/run")
    def evaluation_run(request: EvaluationRunRequest):
        return runtime.run_evaluation(request)

    @router.get("/quality/dashboard")
    def quality_dashboard():
        return runtime.quality_dashboard()

    @router.get("/diagnostics/metrics")
    def metrics():
        return runtime.metrics.snapshot()

    @router.get("/diagnostics/llm")
    def llm_status():
        return runtime.llm_status()

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
