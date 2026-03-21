from cos.configs.settings import Settings
from cos.core.models import (
    AdviceFeedbackRequest,
    CheckinRequest,
    FeedbackRating,
    IngestionRequest,
    RetrievalQueryType,
    RetrievalRequest,
    WeeklySummaryRequest,
)
from cos.runtime import COSRuntime


def test_onboarding_progress_flow():
    runtime = COSRuntime(Settings())
    start = runtime.onboarding_status()
    assert start.progress_ratio == 0.0

    for i in range(5):
        runtime.ingest_text(IngestionRequest(text=f"Project{i} is active.", source_type="note"))
    for _ in range(3):
        runtime.retrieve(
            RetrievalRequest(query="What is active?", query_type=RetrievalQueryType.exploratory)
        )
    runtime.checkin(CheckinRequest(reflection="I paused too many tasks and need focus."))

    end = runtime.onboarding_status()
    assert end.completed is True
    assert end.progress_ratio == 1.0


def test_feedback_summary_counts():
    runtime = COSRuntime(Settings())
    runtime.submit_feedback(
        AdviceFeedbackRequest(advice_title="Do weekly review", rating=FeedbackRating.useful)
    )
    runtime.submit_feedback(
        AdviceFeedbackRequest(advice_title="Do weekly review", rating=FeedbackRating.not_useful)
    )
    runtime.submit_feedback(
        AdviceFeedbackRequest(advice_title="Close loops", rating=FeedbackRating.useful)
    )

    summary = runtime.feedback_summary()
    assert summary.total == 3
    assert summary.useful == 2
    assert summary.not_useful == 1
    assert summary.useful_rate > 0


def test_weekly_summary_has_actions():
    runtime = COSRuntime(Settings())
    runtime.ingest_text(
        IngestionRequest(
            text="Atlas uses Python. Atlas supports onboarding. Atlas is active.",
            source_type="note",
        )
    )
    report = runtime.weekly_summary(WeeklySummaryRequest(persona="general", days=7))
    assert report.highlights
    assert report.recommended_next_actions
