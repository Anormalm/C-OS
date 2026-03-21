from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from cos.core.models import (
    AdviceFeedbackEvent,
    AdviceFeedbackRequest,
    AdviceFeedbackSummary,
    FeedbackRating,
)


@dataclass
class FeedbackService:
    log_path: str | None = None
    events: list[AdviceFeedbackEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.log_path:
            path = Path(self.log_path)
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    self.events.append(AdviceFeedbackEvent.model_validate_json(line))

    def add(self, request: AdviceFeedbackRequest) -> AdviceFeedbackEvent:
        event = AdviceFeedbackEvent(
            advice_title=request.advice_title,
            rating=request.rating,
            persona=request.persona,
            note=request.note,
            context_focus=request.context_focus,
        )
        self.events.append(event)
        if self.log_path:
            path = Path(self.log_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(event.model_dump(mode="json"))
            with path.open("a", encoding="utf-8") as fp:
                fp.write(payload + "\n")
        return event

    def summary(self) -> AdviceFeedbackSummary:
        total = len(self.events)
        useful = sum(1 for event in self.events if event.rating == FeedbackRating.useful)
        not_useful = total - useful
        useful_rate = (useful / total) if total else 0.0

        liked = Counter(event.advice_title for event in self.events if event.rating == FeedbackRating.useful)
        disliked = Counter(
            event.advice_title for event in self.events if event.rating == FeedbackRating.not_useful
        )

        return AdviceFeedbackSummary(
            total=total,
            useful=useful,
            not_useful=not_useful,
            useful_rate=round(useful_rate, 4),
            top_liked_advice=[
                {"title": title, "count": count}
                for title, count in liked.most_common(5)
            ],
            top_disliked_advice=[
                {"title": title, "count": count}
                for title, count in disliked.most_common(5)
            ],
        )
