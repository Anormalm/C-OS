from cos.configs.settings import Settings
from cos.core.models import (
    AdviceFeedbackRequest,
    EvaluationRunRequest,
    FeedbackRating,
    IngestionRequest,
)
from cos.runtime import COSRuntime


def test_evaluation_run_returns_expected_fields():
    runtime = COSRuntime(Settings())
    result = runtime.run_evaluation(EvaluationRunRequest(top_k=3, dataset="default"))
    assert result.case_count > 0
    assert 0.0 <= result.hybrid_hit_at_k <= 1.0
    assert 0.0 <= result.vector_hit_at_k <= 1.0
    assert runtime.last_evaluation is not None


def test_quality_dashboard_reflects_feedback_and_usage():
    runtime = COSRuntime(Settings())
    runtime.ingest_text(IngestionRequest(text="Nova uses Python.", source_type="note"))
    runtime.submit_feedback(
        AdviceFeedbackRequest(advice_title="Test advice", rating=FeedbackRating.useful)
    )
    dashboard = runtime.quality_dashboard()
    assert dashboard.ingestion_documents >= 1
    assert dashboard.advice_useful_rate >= 0.0
    assert isinstance(dashboard.recommendations, list)
