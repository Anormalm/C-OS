from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

from cos.core.models import (
    AdviceItem,
    AdvicePriority,
    AdviceRequest,
    AdviceResponse,
    StatementNode,
    StatementStatus,
    UserPersona,
)
from cos.inference.insights import InsightService
from cos.inference.llm import JSONLLMClient


PERSONA_GUIDES: dict[UserPersona, dict[str, str]] = {
    UserPersona.general: {
        "cadence": "weekly reflection",
        "framing": "Keep recommendations small and practical.",
    },
    UserPersona.student: {
        "cadence": "3 focused study blocks per week",
        "framing": "Prioritize prerequisites and revision loops.",
    },
    UserPersona.founder: {
        "cadence": "weekly execution review",
        "framing": "Convert uncertainty into tested assumptions quickly.",
    },
    UserPersona.manager: {
        "cadence": "weekly alignment check",
        "framing": "Reduce ambiguity and unblock dependencies.",
    },
    UserPersona.creator: {
        "cadence": "twice-weekly publishing cycle",
        "framing": "Favor output momentum over perfect planning.",
    },
}


@dataclass
class AdviceService:
    graph_store: object
    insight_service: InsightService
    llm_client: JSONLLMClient | None = None

    def persona_catalog(self) -> list[dict[str, str]]:
        return [
            {
                "persona": persona.value,
                "cadence": config["cadence"],
                "framing": config["framing"],
            }
            for persona, config in PERSONA_GUIDES.items()
        ]

    def generate(self, request: AdviceRequest) -> AdviceResponse:
        insights = self.insight_service.summarize()
        statements = self.graph_store.list_statements()
        active_statements = [s for s in statements if s.status == StatementStatus.asserted]

        advice: list[AdviceItem] = []
        advice.extend(self._baseline_advice(request.persona, active_statements))

        if insights.contradiction_rate >= 0.1:
            advice.append(
                AdviceItem(
                    title="Stabilize Contradictory Beliefs",
                    why="Your memory has a high contradiction rate, which usually causes decision drift.",
                    actions=[
                        self._persona_prefix(request.persona, "Pick one key topic and write a single current definition."),
                        "Mark old assumptions as historical, not current truth.",
                        "Set a recurring review to update definitions once per week.",
                    ],
                    evidence=[f"Contradiction rate: {insights.contradiction_rate * 100:.1f}%"],
                    priority=AdvicePriority.high,
                    confidence=0.85,
                )
            )

        if insights.abandoned_topics:
            labels = [item["label"] for item in insights.abandoned_topics[:3]]
            advice.append(
                AdviceItem(
                    title="Close Open Loops On Abandoned Ideas",
                    why="Unclosed ideas create mental overhead and reduce focus.",
                    actions=[
                        self._persona_prefix(request.persona, "Choose one abandoned topic to either archive or restart."),
                        "Write a 3-line closure note: what was learned, why paused, next condition to resume.",
                        "Keep only active topics in your weekly plan.",
                    ],
                    evidence=[f"Inactive topics: {', '.join(labels)}"],
                    priority=AdvicePriority.medium,
                    confidence=0.78,
                )
            )

        execution_gaps = self._execution_gaps(active_statements)
        if execution_gaps:
            subject, requirements = execution_gaps[0]
            advice.append(
                AdviceItem(
                    title="Convert Requirements Into Execution",
                    why="You often define prerequisites without linking them to concrete implementation actions.",
                    actions=[
                        self._persona_prefix(
                            request.persona,
                            f"For '{subject}', convert one requirement into a first concrete step today.",
                        ),
                        "Define a done-criterion for that step.",
                        "Record completion status in your next note.",
                    ],
                    evidence=[f"{subject} requires {', '.join(requirements[:3])}, but no matching usage statements found."],
                    priority=AdvicePriority.high,
                    confidence=0.81,
                )
            )

        stall_patterns = self._stalled_subjects(active_statements)
        if stall_patterns:
            advice.append(
                AdviceItem(
                    title="Address Repeated Active-To-Paused Pattern",
                    why="Work repeatedly moves from active to paused, indicating a consistent failure point.",
                    actions=[
                        self._persona_prefix(request.persona, "Identify the exact stage where momentum drops."),
                        "Reduce the next milestone to a one-day deliverable.",
                        "Remove one dependency before restarting the effort.",
                    ],
                    evidence=[f"Observed on: {', '.join(stall_patterns[:3])}"],
                    priority=AdvicePriority.high,
                    confidence=0.83,
                )
            )

        if request.focus:
            focus = request.focus.lower()
            focused = [
                item
                for item in advice
                if focus in item.title.lower()
                or focus in item.why.lower()
                or any(focus in evidence.lower() for evidence in item.evidence)
            ]
            if focused:
                advice = focused
            else:
                advice.append(
                    AdviceItem(
                        title=f"Focused Plan For: {request.focus}",
                        why="No direct pattern matched this focus, so this is a scoped execution plan.",
                        actions=[
                            self._persona_prefix(request.persona, f"Define one specific outcome for '{request.focus}'."),
                            "List 3 blockers and remove the easiest one first.",
                            f"Review progress after {min(request.horizon_days, 14)} days.",
                        ],
                        evidence=["Focus term did not strongly match existing pattern signals."],
                        priority=AdvicePriority.medium,
                        confidence=0.62,
                    )
                )

        advice = self._dedupe_advice(advice)[:5]
        caution = (
            "This is reflective productivity guidance based on your notes; "
            "it is not medical, legal, or financial advice."
        )
        base_response = AdviceResponse(
            generated_at=datetime.now(timezone.utc),
            persona=request.persona,
            focus=request.focus,
            advice=advice,
            caution=caution,
        )
        rewritten = self._rewrite_with_llm(base_response)
        return rewritten or base_response

    def _baseline_advice(self, persona: UserPersona, statements: list[StatementNode]) -> list[AdviceItem]:
        if statements:
            return [
                AdviceItem(
                    title="Run A Consistent Review Cadence",
                    why="Regular review turns memory into better decisions.",
                    actions=[
                        self._persona_prefix(persona, f"Schedule a {PERSONA_GUIDES[persona]['cadence']}."),
                        "At each review, keep one priority and drop one low-value idea.",
                        "Capture one evidence-backed lesson in C-OS after each review.",
                    ],
                    evidence=[f"Current asserted statements: {len(statements)}"],
                    priority=AdvicePriority.medium,
                    confidence=0.76,
                )
            ]
        return [
            AdviceItem(
                title="Seed Useful Memory First",
                why="Advice quality depends on having enough real examples from your own thinking.",
                actions=[
                    self._persona_prefix(persona, "Add 5 short notes from recent decisions."),
                    "Include dates and outcomes whenever possible.",
                    "Ask C-OS one question after each note to reinforce retrieval quality.",
                ],
                evidence=["No asserted statements available yet."],
                priority=AdvicePriority.high,
                confidence=0.9,
            )
        ]

    def _execution_gaps(self, statements: list[StatementNode]) -> list[tuple[str, list[str]]]:
        req_by_subject: dict[str, list[str]] = defaultdict(list)
        has_execution: set[str] = set()
        for statement in statements:
            subject = self._label(statement.subject)
            obj = self._label(statement.object)
            if statement.relation == "requires":
                req_by_subject[subject].append(obj)
            if statement.relation in {"uses", "supports", "leads_to"}:
                has_execution.add(subject)

        gaps = [(subject, reqs) for subject, reqs in req_by_subject.items() if subject not in has_execution]
        gaps.sort(key=lambda row: len(row[1]), reverse=True)
        return gaps

    def _stalled_subjects(self, statements: list[StatementNode]) -> list[str]:
        status_by_subject: dict[str, set[str]] = defaultdict(set)
        for statement in statements:
            if statement.relation != "is":
                continue
            subject = self._label(statement.subject)
            state = self._label(statement.object).lower()
            status_by_subject[subject].add(state)

        stalled = []
        for subject, states in status_by_subject.items():
            if "active" in states and ("paused" in states or "blocked" in states):
                stalled.append(subject)
        return stalled

    def _label(self, entity_id: str) -> str:
        entity = self.graph_store.get_entity(entity_id)
        return entity.name if entity else entity_id

    def _rewrite_with_llm(self, response: AdviceResponse) -> AdviceResponse | None:
        if not self.llm_client or not response.advice:
            return None

        compact = [
            {
                "title": item.title,
                "why": item.why,
                "actions": item.actions,
                "priority": item.priority.value,
                "confidence": item.confidence,
                "evidence": item.evidence,
            }
            for item in response.advice
        ]
        system_prompt = (
            "You are improving user-facing coaching language for non-technical users. "
            "Do not invent new facts. Keep advice practical and short."
        )
        user_prompt = (
            "Rewrite the advice list in simpler plain English while preserving intent.\n"
            "Return strict JSON as: {\"advice\": [{\"title\": str, \"why\": str, \"actions\": [str]}], \"caution\": str}\n"
            f"Input JSON:\n{compact}"
        )
        rewritten = self.llm_client.generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
        if not rewritten:
            return None

        rows = rewritten.get("advice")
        if not isinstance(rows, list) or not rows:
            return None

        merged: list[AdviceItem] = []
        for idx, original in enumerate(response.advice):
            if idx >= len(rows):
                merged.append(original)
                continue
            row = rows[idx]
            if not isinstance(row, dict):
                merged.append(original)
                continue

            title = str(row.get("title") or original.title).strip()
            why = str(row.get("why") or original.why).strip()
            actions = row.get("actions")
            if isinstance(actions, list):
                cleaned_actions = [str(action).strip() for action in actions if str(action).strip()]
                if not cleaned_actions:
                    cleaned_actions = original.actions
            else:
                cleaned_actions = original.actions

            merged.append(
                AdviceItem(
                    title=title,
                    why=why,
                    actions=cleaned_actions[:3],
                    evidence=original.evidence,
                    priority=original.priority,
                    confidence=original.confidence,
                )
            )

        caution = rewritten.get("caution")
        caution_text = str(caution).strip() if caution else response.caution
        return AdviceResponse(
            generated_at=response.generated_at,
            persona=response.persona,
            focus=response.focus,
            advice=merged,
            caution=caution_text,
        )

    @staticmethod
    def _dedupe_advice(advice: list[AdviceItem]) -> list[AdviceItem]:
        seen: set[str] = set()
        output = []
        for item in advice:
            key = item.title.lower().strip()
            if key in seen:
                continue
            seen.add(key)
            output.append(item)
        return output

    @staticmethod
    def _persona_prefix(persona: UserPersona, action: str) -> str:
        prefix_map = {
            UserPersona.general: "Next step:",
            UserPersona.student: "Study move:",
            UserPersona.founder: "Execution move:",
            UserPersona.manager: "Team move:",
            UserPersona.creator: "Creation move:",
        }
        return f"{prefix_map[persona]} {action}"
