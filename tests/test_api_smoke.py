from fastapi.testclient import TestClient

from cos.app import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_basic_ingest_and_retrieve_smoke():
    with TestClient(app) as client:
        ingest_response = client.post(
            "/ingest/text",
            json={
                "text": "2026-01-01 Phoenix is active. Phoenix uses Python.",
                "source_type": "note",
                "source_uri": "smoke://input",
            },
        )
        assert ingest_response.status_code == 200

        retrieve_response = client.post(
            "/query/retrieve",
            json={"query": "What does Phoenix use?", "query_type": "factual", "top_k": 3},
        )
        assert retrieve_response.status_code == 200
        assert isinstance(retrieve_response.json(), list)


def test_coach_advice_smoke():
    with TestClient(app) as client:
        response = client.post("/coach/advice", json={"persona": "general", "focus": "consistency"})
    assert response.status_code == 200
    data = response.json()
    assert "advice" in data
    assert "caution" in data


def test_sprint2_endpoints_smoke():
    with TestClient(app) as client:
        onboarding = client.get("/onboarding/status")
        assert onboarding.status_code == 200

        summary = client.post("/summary/weekly", json={"persona": "general", "days": 7})
        assert summary.status_code == 200

        feedback = client.post(
            "/coach/feedback",
            json={
                "advice_title": "Test Advice",
                "rating": "useful",
                "persona": "general",
            },
        )
        assert feedback.status_code == 200
