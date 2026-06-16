from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from typing import Sequence

from cartography.graph.job import GraphJob
from cartography.graph.statement import GraphStatement
from cartography.models.core.relationships import LinkDirection


@dataclass(frozen=True)
class AnalysisScope:
    label: str
    id_param: str
    id_property: str = "id"
    rel_label: str = "RESOURCE"

    def match(self, alias: str) -> str:
        return f"({alias}:{self.label} {{{self.id_property}: ${self.id_param}}})"


@dataclass(frozen=True)
class AnalysisStatement:
    query: str
    comment: str = ""
    iterative: bool = False
    iterationsize: int = 0

    def to_graph_statement(
        self,
        parent_job_name: str,
        sequence_num: int,
    ) -> GraphStatement:
        return GraphStatement(
            self.query,
            iterative=self.iterative,
            iterationsize=self.iterationsize,
            parent_job_name=parent_job_name,
            parent_job_sequence_num=sequence_num,
        )


@dataclass(frozen=True)
class RelationshipEffect:
    source_label: str
    rel_label: str
    target_label: str
    properties: tuple[str, ...] = ()
    direction: LinkDirection = LinkDirection.OUTWARD
    scoped_to: Literal["source", "target"] = "source"

    def cleanup_query(self, scope: AnalysisScope | None) -> str:
        source = f"(source:{self.source_label})"
        target = f"(target:{self.target_label})"
        rel = f"[r:{self.rel_label}]"
        if self.direction == LinkDirection.INWARD:
            pattern = f"{source}<-{rel}-{target}"
        elif self.direction == LinkDirection.OUTWARD:
            pattern = f"{source}-{rel}->{target}"
        else:
            pattern = f"{source}-{rel}-{target}"

        match = f"MATCH {pattern}"
        if scope:
            scoped_alias = self.scoped_to
            match = (
                f"MATCH {scope.match('scope')}-[:{scope.rel_label}]->"
                f"({scoped_alias})\n{match}"
            )

        filters = ["r.lastupdated <> $UPDATE_TAG"]
        return f"{match}\nWHERE {' AND '.join(filters)}\nDELETE r"


@dataclass(frozen=True)
class PropertyEffect:
    node_label: str
    properties: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.properties:
            raise ValueError("PropertyEffect requires at least one property.")

    def cleanup_query(self, scope: AnalysisScope | None) -> str:
        node = f"(node:{self.node_label})"
        match = f"MATCH {node}"
        if scope:
            match = f"MATCH {scope.match('scope')}-[:{scope.rel_label}]->{node}"
        props = ", ".join(f"node.{prop}" for prop in self.properties)
        return f"{match}\nREMOVE {props}"


@dataclass(frozen=True)
class RelationshipPropertyEffect:
    source_label: str
    rel_label: str
    properties: tuple[str, ...]
    target_label: str | None = None
    direction: LinkDirection = LinkDirection.OUTWARD

    def __post_init__(self) -> None:
        if not self.properties:
            raise ValueError(
                "RelationshipPropertyEffect requires at least one property."
            )

    def cleanup_query(self, scope: AnalysisScope | None) -> str:
        source = f"(source:{self.source_label})"
        target = f"(target:{self.target_label})" if self.target_label else "(target)"
        rel = f"[r:{self.rel_label}]"
        if self.direction == LinkDirection.INWARD:
            pattern = f"{source}<-{rel}-{target}"
        else:
            pattern = f"{source}-{rel}->{target}"

        match = f"MATCH {pattern}"
        if scope:
            match = (
                f"MATCH {scope.match('scope')}-[:{scope.rel_label}]->(source)\n"
                f"{match}"
            )

        props = ", ".join(f"r.{prop}" for prop in self.properties)
        return f"{match}\nREMOVE {props}"


AnalysisEffect = RelationshipEffect | PropertyEffect | RelationshipPropertyEffect


@dataclass(frozen=True)
class AnalysisJob:
    name: str
    effect: AnalysisEffect
    statements: Sequence[AnalysisStatement]
    scope: AnalysisScope | None = None
    short_name: str | None = None
    cleanup_iterationsize: int = 10000

    def __post_init__(self) -> None:
        if not self.statements:
            raise ValueError("AnalysisJob requires at least one statement.")

    def relationships_added(self) -> tuple[RelationshipEffect, ...]:
        if isinstance(self.effect, RelationshipEffect):
            return (self.effect,)
        return ()

    def properties_set(self) -> tuple[PropertyEffect | RelationshipPropertyEffect, ...]:
        if isinstance(self.effect, (PropertyEffect, RelationshipPropertyEffect)):
            return (self.effect,)
        return ()

    def to_graph_job(self) -> GraphJob:
        statements: list[GraphStatement] = []
        parent_name = self.short_name or self.name

        if isinstance(self.effect, (PropertyEffect, RelationshipPropertyEffect)):
            statements.append(self._cleanup_statement(parent_name, 1))

        for offset, statement in enumerate(self.statements, start=len(statements) + 1):
            statements.append(statement.to_graph_statement(parent_name, offset))

        if isinstance(self.effect, RelationshipEffect):
            statements.append(self._cleanup_statement(parent_name, len(statements) + 1))

        return GraphJob(self.name, statements, self.short_name)

    def _cleanup_statement(
        self,
        parent_name: str,
        sequence_num: int,
    ) -> GraphStatement:
        return GraphStatement(
            self.effect.cleanup_query(self.scope),
            iterative=True,
            iterationsize=self.cleanup_iterationsize,
            parent_job_name=parent_name,
            parent_job_sequence_num=sequence_num,
        )
