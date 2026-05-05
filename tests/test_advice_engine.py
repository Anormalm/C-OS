from cos.configs.settings import Settings
from cos.core.models import AdviceRequest, CheckinRequest, IngestionRequest, UserPersona
from cos.runtime import COSRuntime


def test_advice_contains_actionable_items():
    runtime = COSRuntime(Settings())
    runtime.ingest_text(
        IngestionRequest(
            text=(
                "Atlas requires GPU cluster. "
                "Atlas requires budget approval. "
                "2025-01-01 Atlas is active. "
                "2025-02-01 Atlas is paused."
            ),
            source_type="note",
            source_uri="test://advice",
        )
    )

    response = runtime.generate_advice(AdviceRequest(persona=UserPersona.founder))
    assert response.advice
    assert any(item.actions for item in response.advice)
    assert any(item.priority.value in {"high", "medium", "low"} for item in response.advice)


def test_checkin_returns_ingestion_and_advice():
    runtime = COSRuntime(Settings())
    response = runtime.checkin(
        CheckinRequest(
            reflection="I changed priorities again and paused documentation work.",
            persona=UserPersona.manager,
            focus="consistency",
        )
    )
    assert response.ingestion.statement_count >= 0
    assert response.advice.persona == UserPersona.manager


def test_next_step_returns_single_action():
    runtime = COSRuntime(Settings())
    runtime.ingest_text(
        IngestionRequest(
            text="I pause projects when milestones are unclear. Atlas is active.",
            source_type="note",
            source_uri="test://next-step",
        )
    )
    result = runtime.next_step(AdviceRequest(persona=UserPersona.general, focus="consistency"))
    assert result.title
    assert result.action
    assert result.estimated_minutes >= 5
