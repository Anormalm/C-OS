from cos.configs.settings import Settings
from cos.core.models import ActionCompletionRequest, IngestionRequest
from cos.runtime import COSRuntime


def test_today_brief_and_action_completion():
    runtime = COSRuntime(Settings())
    runtime.ingest_text(IngestionRequest(text="Atlas uses Neo4j. Atlas is active.", source_type="note"))

    initial = runtime.today_brief()
    assert initial.reminder
    assert initial.next_action
    assert initial.weekly_snippet

    runtime.complete_action(
        ActionCompletionRequest(
            action_text="Execution move: Define one small next task.",
            advice_title="Run A Consistent Review Cadence",
        )
    )
    updated = runtime.today_brief()
    assert updated.completed_actions_last_7d >= initial.completed_actions_last_7d
