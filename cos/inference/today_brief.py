from __future__ import annotations

from dataclasses import dataclass

from cos.core.models import AdviceRequest, TodayBriefResponse, WeeklySummaryRequest
from cos.inference.action_tracker import ActionTrackerService
from cos.inference.next_step import NextStepService
from cos.inference.onboarding import OnboardingService
from cos.inference.weekly_summary import WeeklySummaryService


@dataclass
class TodayBriefService:
    onboarding_service: OnboardingService
    weekly_summary_service: WeeklySummaryService
    next_step_service: NextStepService
    action_tracker: ActionTrackerService

    def build(self) -> TodayBriefResponse:
        onboarding = self.onboarding_service.status()
        weekly = self.weekly_summary_service.generate(WeeklySummaryRequest(persona="general", days=7))
        next_step = self.next_step_service.generate(AdviceRequest(persona="general", horizon_days=7))

        reminder = onboarding.recommended_next_step or "Keep writing your thoughts."
        next_action = next_step.action
        weekly_snippet = weekly.highlights[0] if weekly.highlights else "No weekly highlight yet."

        return TodayBriefResponse(
            reminder=reminder,
            next_action=next_action,
            weekly_snippet=weekly_snippet,
            onboarding_progress=onboarding.progress_ratio,
            completed_actions_last_7d=self.action_tracker.completed_count(days=7),
        )
