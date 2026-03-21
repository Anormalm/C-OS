from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from cos.core.models import AdviceRequest, StatementStatus, WeeklySummaryRequest, WeeklySummaryResponse
from cos.inference.advice import AdviceService
from cos.inference.feedback import FeedbackService


@dataclass
class WeeklySummaryService:
    graph_store: object
    advice_service: AdviceService
    feedback_service: FeedbackService

    def generate(self, request: WeeklySummaryRequest) -> WeeklySummaryResponse:
        period_end = datetime.now(timezone.utc)
        period_start = period_end - timedelta(days=request.days)
        statements = self.graph_store.list_statements()

        recent = [statement for statement in statements if statement.ingestion_time >= period_start]
        if request.focus:
            focus = request.focus.lower()
            recent = [
                statement
                for statement in recent
                if focus in self._label(statement.subject).lower()
                or focus in self._label(statement.object).lower()
                or focus in statement.relation.lower()
            ]

        topic_counter = Counter()
        wins = []
        risks = []

        for statement in recent:
            subject_label = self._label(statement.subject)
            object_label = self._label(statement.object)
            topic_counter[subject_label] += 1
            topic_counter[object_label] += 1

            if statement.relation in {"supports", "uses", "leads_to"}:
                wins.append(f"{subject_label} {statement.relation} {object_label}")
            if statement.relation == "is" and object_label.lower() in {"active", "completed"}:
                wins.append(f"{subject_label} moved to {object_label}")
            if statement.status == StatementStatus.contradicted:
                risks.append(f"Contradiction: {subject_label} {statement.relation} {object_label}")
            if statement.relation == "is" and object_label.lower() in {"paused", "blocked"}:
                risks.append(f"Stall detected: {subject_label} is {object_label}")

        highlights = []
        for topic, count in topic_counter.most_common(3):
            highlights.append(f"Topic '{topic}' appeared {count} times this period.")
        if not highlights:
            highlights.append("Not enough recent data. Add more notes this week.")

        feedback = self.feedback_service.summary()
        if feedback.total:
            highlights.append(
                f"Coach advice usefulness this period: {feedback.useful_rate * 100:.1f}% "
                f"({feedback.useful}/{feedback.total})."
            )

        advice = self.advice_service.generate(
            AdviceRequest(persona=request.persona, focus=request.focus, horizon_days=request.days)
        )
        recommended_next_actions = []
        for item in advice.advice[:3]:
            if item.actions:
                recommended_next_actions.append(item.actions[0])

        return WeeklySummaryResponse(
            period_start=period_start,
            period_end=period_end,
            persona=request.persona,
            focus=request.focus,
            highlights=highlights[:5],
            risks=risks[:5] if risks else ["No major risks detected this period."],
            wins=wins[:5] if wins else ["No explicit wins recorded this period."],
            recommended_next_actions=recommended_next_actions,
            stats={
                "recent_statements": len(recent),
                "topics_tracked": len(topic_counter),
                "feedback_total": feedback.total,
                "feedback_useful_rate": feedback.useful_rate,
            },
        )

    def _label(self, entity_id: str) -> str:
        entity = self.graph_store.get_entity(entity_id)
        return entity.name if entity else entity_id
