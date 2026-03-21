from __future__ import annotations

from dataclasses import dataclass

from cos.core.models import OnboardingStatus, OnboardingStep
from cos.diagnostics.metrics import MetricsRegistry


@dataclass
class OnboardingService:
    metrics: MetricsRegistry

    def status(self) -> OnboardingStatus:
        counters = self.metrics.counters
        steps = [
            OnboardingStep(
                id="ingest_notes",
                title="Add your first notes",
                target=5,
                completed=counters.get("documents_ingested", 0),
                done=counters.get("documents_ingested", 0) >= 5,
                helper="Add at least 5 notes to help C-OS learn your patterns.",
            ),
            OnboardingStep(
                id="ask_memory",
                title="Ask memory questions",
                target=3,
                completed=counters.get("retrieval_queries", 0),
                done=counters.get("retrieval_queries", 0) >= 3,
                helper="Ask 3 real questions to calibrate retrieval quality.",
            ),
            OnboardingStep(
                id="checkin",
                title="Do your first coach check-in",
                target=1,
                completed=counters.get("coach_checkins", 0),
                done=counters.get("coach_checkins", 0) >= 1,
                helper="Write one reflection and get tailored next steps.",
            ),
        ]

        total_target = sum(step.target for step in steps)
        total_done = sum(min(step.completed, step.target) for step in steps)
        progress_ratio = (total_done / total_target) if total_target else 0.0

        next_step = next(
            (step.title for step in steps if not step.done),
            "Onboarding complete. Start weekly summaries.",
        )
        started = any(step.completed > 0 for step in steps)
        completed = all(step.done for step in steps)

        return OnboardingStatus(
            started=started,
            completed=completed,
            progress_ratio=round(progress_ratio, 4),
            steps=steps,
            recommended_next_step=next_step,
        )
