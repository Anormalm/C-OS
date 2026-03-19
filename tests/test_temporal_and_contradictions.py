from datetime import datetime, timezone

from cos.configs.settings import Settings
from cos.core.models import IngestionRequest, TemporalQueryRequest
from cos.runtime import COSRuntime


def test_bitemporal_truth_and_contradictions():
    runtime = COSRuntime(Settings())
    text = """
    2024-01-01 Atlas is active.
    2024-03-01 Atlas is paused.
    """
    response = runtime.ingest_text(IngestionRequest(text=text, source_type="note", source_uri="test://note"))
    assert response.statement_count == 2
    assert response.contradictions == 1

    jan_truth = runtime.temporal_query(
        TemporalQueryRequest(at_time=datetime(2024, 1, 15, tzinfo=timezone.utc), entity="Atlas")
    )
    assert len(jan_truth) == 1
    jan_obj = runtime.graph_store.get_entity(jan_truth[0].object)
    assert jan_obj is not None
    assert jan_obj.name.lower() == "active"

    apr_truth = runtime.temporal_query(
        TemporalQueryRequest(at_time=datetime(2024, 4, 1, tzinfo=timezone.utc), entity="Atlas")
    )
    assert len(apr_truth) == 1
    apr_obj = runtime.graph_store.get_entity(apr_truth[0].object)
    assert apr_obj is not None
    assert apr_obj.name.lower() == "paused"
