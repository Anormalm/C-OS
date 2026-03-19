from __future__ import annotations

from dataclasses import dataclass

from cos.core.models import StatementNode, StatementStatus
from cos.graph.base import GraphStore


def overlaps(a_start, a_end, b_start, b_end) -> bool:
    a_to = a_end
    b_to = b_end
    if a_to is None and b_to is None:
        return True
    if a_to is None:
        return a_start < b_to
    if b_to is None:
        return b_start < a_to
    return a_start < b_to and b_start < a_to


@dataclass
class ContradictionResolver:
    graph_store: GraphStore

    def apply(self, new_statement: StatementNode) -> int:
        contradictions = 0
        contradicted_ids: list[str] = []
        existing = self.graph_store.statements_by_key(new_statement.subject, new_statement.relation)
        for statement in existing:
            if statement.id == new_statement.id:
                continue
            if statement.object == new_statement.object:
                continue
            if statement.status != StatementStatus.asserted:
                continue
            if not overlaps(
                statement.valid_from,
                statement.valid_to,
                new_statement.valid_from,
                new_statement.valid_to,
            ):
                continue
            statement.status = StatementStatus.contradicted
            statement.valid_to = new_statement.valid_from
            self.graph_store.update_statement(statement)
            contradictions += 1
            contradicted_ids.append(statement.id)

        if contradicted_ids:
            new_statement.contradiction_of = contradicted_ids[-1]
            self.graph_store.update_statement(new_statement)
        return contradictions
