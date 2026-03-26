from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cos.core.models import ActionCompletionEvent, ActionCompletionRequest


@dataclass
class ActionTrackerService:
    log_path: str | None = None
    events: list[ActionCompletionEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.log_path:
            path = Path(self.log_path)
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    self.events.append(ActionCompletionEvent.model_validate_json(line))

    def complete(self, request: ActionCompletionRequest) -> ActionCompletionEvent:
        event = ActionCompletionEvent(
            action_text=request.action_text,
            advice_title=request.advice_title,
            persona=request.persona,
            focus=request.focus,
            note=request.note,
        )
        self.events.append(event)
        if self.log_path:
            path = Path(self.log_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fp:
                fp.write(json.dumps(event.model_dump(mode="json")) + "\n")
        return event

    def completed_count(self, days: int = 7) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return sum(1 for event in self.events if event.created_at >= cutoff)
