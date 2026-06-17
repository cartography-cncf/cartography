from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Literal
from typing import Sequence

from cartography.graph.job import GraphJob
from cartography.graph.statement import GraphStatement
from cartography.models.core.relationships import LinkDirection


@dataclass(frozen=True)
class ScopedTo:
    label: str
    id_param: str
    id_property: str = "id"
    rel_label: str = "RESOURCE"

    def match(self, alias: str) -> str:
        return f"({alias}:{self.label} {{{self.id_property}: ${self.id_param}}})"


@dataclass(frozen=True)
class AnalysisStatement:
    query: str | None = None
    comment: str = ""
    match: str | None = None
    effects: Sequence[StatementEffect] = ()
    iterative: bool = False
    iterationsize: int = 0

    def __post_init__(self) -> None:
        if self.query and (self.match or self.effects):
            raise ValueError(
                "AnalysisStatement accepts query or match/effects, not both."
            )
        if not self.query and (not self.match or not self.effects):
            raise ValueError("AnalysisStatement requires query or match/effects.")

    def compile_query(self) -> str:
        if self.query:
            return self.query
        assert self.match
        return "\n".join(
            (self.match.strip(), *(_compile_effect(e) for e in self.effects))
        )

    def to_graph_statement(
        self,
        parent_job_name: str,
        sequence_num: int,
    ) -> GraphStatement:
        return GraphStatement(
            self.compile_query(),
            iterative=self.iterative,
            iterationsize=self.iterationsize,
            parent_job_name=parent_job_name,
            parent_job_sequence_num=sequence_num,
        )


@dataclass(frozen=True)
class SetProperty:
    node: str
    property: str
    value: Any
    label: str = ""


@dataclass(frozen=True)
class SetProperties:
    node: str
    properties: dict[str, Any]
    label: str = ""


@dataclass(frozen=True)
class SetRelationshipProperty:
    rel: str
    property: str
    value: Any
    source_label: str = ""
    rel_label: str = ""
    target_label: str | None = None


@dataclass(frozen=True)
class AddToSet:
    node: str
    property: str
    value: Any
    label: str = ""


@dataclass(frozen=True)
class AddRelationship:
    source: str
    rel: str
    target: str
    source_label: str = ""
    target_label: str = ""
    rel_alias: str = "r"
    properties: dict[str, Any] | None = None
    undirected: bool = False
    firstseen: Any = None
    scoped_to: Literal["source", "target"] = "source"


@dataclass(frozen=True)
class Expr:
    value: str


StatementEffect = (
    SetProperty | SetProperties | SetRelationshipProperty | AddToSet | AddRelationship
)


def _compile_effect(effect: StatementEffect) -> str:
    if isinstance(effect, SetProperty):
        return f"SET {effect.node}.{effect.property} = {_cypher_literal(effect.value)}"
    if isinstance(effect, SetProperties):
        assignments = ", ".join(
            f"{effect.node}.{key} = {_cypher_literal(value)}"
            for key, value in effect.properties.items()
        )
        return f"SET {assignments}"
    if isinstance(effect, SetRelationshipProperty):
        return f"SET {effect.rel}.{effect.property} = {_cypher_literal(effect.value)}"
    if isinstance(effect, AddToSet):
        value = _cypher_literal(effect.value)
        return (
            f"SET {effect.node}.{effect.property} = "
            f"CASE WHEN {effect.node}.{effect.property} IS NULL THEN [{value}] "
            f"WHEN NOT {value} IN {effect.node}.{effect.property} "
            f"THEN {effect.node}.{effect.property} + [{value}] "
            f"ELSE {effect.node}.{effect.property} END"
        )
    rel = (
        f"({effect.source})-[{effect.rel_alias}:{effect.rel}]-({effect.target})"
        if effect.undirected
        else f"({effect.source})-[{effect.rel_alias}:{effect.rel}]->({effect.target})"
    )
    property_assignments = ""
    if effect.properties:
        property_assignments = ", " + ", ".join(
            f"{effect.rel_alias}.{key} = {_cypher_literal(value)}"
            for key, value in effect.properties.items()
        )
    firstseen_value = _cypher_literal(effect.firstseen or Expr("timestamp()"))
    return (
        f"MERGE {rel}\n"
        f"ON CREATE SET {effect.rel_alias}.firstseen = {firstseen_value}\n"
        f"SET {effect.rel_alias}.lastupdated = $UPDATE_TAG{property_assignments}"
    )


def _cypher_literal(value: Any) -> str:
    if isinstance(value, Expr):
        return value.value
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_cypher_literal(v) for v in value) + "]"
    raise TypeError(f"Unsupported Cypher literal: {value!r}")


@dataclass(frozen=True)
class RelationshipEffect:
    source_label: str
    rel_label: str
    target_label: str
    properties: tuple[str, ...] = ()
    direction: LinkDirection | None = LinkDirection.OUTWARD
    scoped_to: Literal["source", "target"] = "source"

    def cleanup_query(self, scope: ScopedTo | None) -> str:
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
        return (
            f"{match}\n"
            f"WHERE {' AND '.join(filters)}\n"
            "WITH r LIMIT $LIMIT_SIZE\n"
            "DELETE r"
        )


@dataclass(frozen=True)
class PropertyEffect:
    node_label: str
    properties: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.properties:
            raise ValueError("PropertyEffect requires at least one property.")

    def cleanup_query(self, scope: ScopedTo | None) -> str:
        node = f"(node:{self.node_label})"
        match = f"MATCH {node}"
        if scope:
            match = f"MATCH {scope.match('scope')}-[:{scope.rel_label}]->{node}"
        props = ", ".join(f"node.{prop}" for prop in self.properties)
        filters = " OR ".join(f"node.{prop} IS NOT NULL" for prop in self.properties)
        return f"{match}\nWHERE {filters}\nWITH node LIMIT $LIMIT_SIZE\nREMOVE {props}"


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

    def cleanup_query(self, scope: ScopedTo | None) -> str:
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
        filters = " OR ".join(f"r.{prop} IS NOT NULL" for prop in self.properties)
        return f"{match}\nWHERE {filters}\nWITH r LIMIT $LIMIT_SIZE\nREMOVE {props}"


AnalysisEffect = RelationshipEffect | PropertyEffect | RelationshipPropertyEffect


@dataclass(frozen=True)
class AnalysisJob:
    name: str
    statements: Sequence[AnalysisStatement]
    scope: ScopedTo | None = None
    short_name: str | None = None
    cleanup_iterationsize: int = 10000

    def __post_init__(self) -> None:
        if not self.statements:
            raise ValueError("AnalysisJob requires at least one statement.")

    def relationships_added(self) -> tuple[RelationshipEffect, ...]:
        relationships: list[RelationshipEffect] = []
        for effect in self._effects():
            if isinstance(effect, AddRelationship):
                rel_effect = RelationshipEffect(
                    effect.source_label,
                    effect.rel,
                    effect.target_label,
                    tuple(effect.properties or ()),
                    LinkDirection.OUTWARD if not effect.undirected else None,
                    effect.scoped_to,
                )
                if rel_effect not in relationships:
                    relationships.append(rel_effect)
        return tuple(relationships)

    def properties_set(self) -> tuple[PropertyEffect | RelationshipPropertyEffect, ...]:
        properties: list[PropertyEffect | RelationshipPropertyEffect] = []
        for effect in self._effects():
            prop_effect: PropertyEffect | RelationshipPropertyEffect | None = None
            if isinstance(effect, SetProperty):
                if not effect.label:
                    continue
                prop_effect = PropertyEffect(effect.label, (effect.property,))
            elif isinstance(effect, SetProperties):
                if not effect.label:
                    continue
                prop_effect = PropertyEffect(effect.label, tuple(effect.properties))
            elif isinstance(effect, AddToSet):
                prop_effect = PropertyEffect(effect.label, (effect.property,))
            elif isinstance(effect, SetRelationshipProperty):
                prop_effect = RelationshipPropertyEffect(
                    effect.source_label,
                    effect.rel_label,
                    (effect.property,),
                    effect.target_label,
                )
            if prop_effect and prop_effect not in properties:
                properties.append(prop_effect)
        return tuple(properties)

    def to_graph_job(self) -> GraphJob:
        statements: list[GraphStatement] = []
        parent_name = self.short_name or self.name

        cleanup_effects = self._cleanup_effects()

        for effect in cleanup_effects:
            if isinstance(effect, (PropertyEffect, RelationshipPropertyEffect)):
                statements.append(
                    self._cleanup_statement(effect, parent_name, len(statements) + 1)
                )

        for offset, statement in enumerate(self.statements, start=len(statements) + 1):
            statements.append(statement.to_graph_statement(parent_name, offset))

        for effect in cleanup_effects:
            if isinstance(effect, RelationshipEffect):
                statements.append(
                    self._cleanup_statement(effect, parent_name, len(statements) + 1)
                )

        return GraphJob(self.name, statements, self.short_name)

    def _effects(self) -> tuple[StatementEffect, ...]:
        return tuple(
            effect for statement in self.statements for effect in statement.effects
        )

    def _cleanup_effects(self) -> tuple[AnalysisEffect, ...]:
        cleanups: list[AnalysisEffect] = []
        for effect in self._effects():
            cleanup: AnalysisEffect
            if isinstance(effect, SetProperty):
                if not effect.label:
                    continue
                cleanup = PropertyEffect(effect.label, (effect.property,))
            elif isinstance(effect, SetProperties):
                if not effect.label:
                    continue
                cleanup = PropertyEffect(effect.label, tuple(effect.properties))
            elif isinstance(effect, AddToSet):
                if not effect.label:
                    continue
                cleanup = PropertyEffect(effect.label, (effect.property,))
            elif isinstance(effect, SetRelationshipProperty):
                cleanup = RelationshipPropertyEffect(
                    effect.source_label,
                    effect.rel_label,
                    (effect.property,),
                    effect.target_label,
                )
            elif isinstance(effect, AddRelationship):
                cleanup = RelationshipEffect(
                    effect.source_label,
                    effect.rel,
                    effect.target_label,
                    tuple(effect.properties or ()),
                    LinkDirection.OUTWARD if not effect.undirected else None,
                    effect.scoped_to,
                )
            else:
                continue
            if cleanup not in cleanups:
                cleanups.append(cleanup)
        return tuple(cleanups)

    def _cleanup_statement(
        self,
        effect: AnalysisEffect,
        parent_name: str,
        sequence_num: int,
    ) -> GraphStatement:
        return GraphStatement(
            effect.cleanup_query(self.scope),
            iterative=True,
            iterationsize=self.cleanup_iterationsize,
            parent_job_name=parent_name,
            parent_job_sequence_num=sequence_num,
        )
