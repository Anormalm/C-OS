from cos.configs.settings import Settings
from cos.core.models import AdviceRequest, IngestionRequest
from cos.runtime import COSRuntime


class _FakeLLMClient:
    def generate_json(self, system_prompt: str, user_prompt: str):
        return {
            "advice": [
                {
                    "title": "Pick one tiny step",
                    "why": "Smaller tasks are easier to finish consistently.",
                    "actions": ["Do one 20-minute task now."],
                }
            ],
            "caution": "Guidance only.",
        }


def test_runtime_builds_deepseek_client_when_configured():
    runtime = COSRuntime(
        Settings(
            llm_provider="deepseek",
            llm_api_key="test-key",
            llm_model="deepseek-v4-pro",
            llm_base_url="https://api.deepseek.com",
        )
    )
    assert runtime.llm_client is not None


def test_advice_rewrites_with_llm_when_available():
    runtime = COSRuntime(Settings())
    runtime.advice.llm_client = _FakeLLMClient()
    runtime.ingest_text(
        IngestionRequest(
            text="Atlas is active. Atlas requires milestone clarity.",
            source_type="note",
            source_uri="test://llm",
        )
    )
    response = runtime.generate_advice(AdviceRequest(persona="general"))
    assert response.advice
    assert response.advice[0].title == "Pick one tiny step"
    assert response.advice[0].actions[0] == "Do one 20-minute task now."
