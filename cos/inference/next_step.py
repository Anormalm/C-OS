from __future__ import annotations

from dataclasses import dataclass

from cos.core.models import AdvicePriority, AdviceRequest, NextStepResponse
from cos.inference.advice import AdviceService


@dataclass
class NextStepService:
    advice_service: AdviceService

    def generate(self, request: AdviceRequest) -> NextStepResponse:
        advice_response = self.advice_service.generate(request)
        if not advice_response.advice:
            return NextStepResponse(
                persona=request.persona,
                focus=request.focus,
                title="Seed your memory first",
                action="Add 3 short notes from the last week, then ask for your next step again.",
                why="The system needs a small amount of history to generate personalized advice.",
                confidence=0.9,
                estimated_minutes=10,
                alternatives=[],
                caution=advice_response.caution,
            )

        primary = advice_response.advice[0]
        action = primary.actions[0] if primary.actions else "Write one concrete next action in your notes."
        estimated_minutes = self._minutes_for_priority(primary.priority)
        alternatives = [item.title for item in advice_response.advice[1:4]]

        return NextStepResponse(
            persona=advice_response.persona,
            focus=advice_response.focus,
            title=primary.title,
            action=action,
            why=primary.why,
            confidence=primary.confidence,
            estimated_minutes=estimated_minutes,
            alternatives=alternatives,
            caution=advice_response.caution,
        )

    @staticmethod
    def _minutes_for_priority(priority: AdvicePriority) -> int:
        if priority == AdvicePriority.high:
            return 25
        if priority == AdvicePriority.medium:
            return 15
        return 10
