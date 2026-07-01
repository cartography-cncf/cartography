from __future__ import annotations

from dataclasses import dataclass
from functools import singledispatch
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
        if not self.query:
            for effect in self.effects:
                effect.validate()

    def compile_query(self) -> str:
        if self.query:
            return self.query
        if self.match is None:
            raise ValueError("AnalysisStatement requires match or query.")
        return "\n".join((self.match.strip(), *(e.compile() for e in self.effects)))

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
    label: str | None = None

    def validate(self) -> None:
        _require_label(self.label)

    def compile(self) -> str:
        return f"SET {self.node}.{self.property} = {_cypher_literal(self.value)}"

    def relationship_effect(self) -> RelationshipEffect | None:
        return None

    def property_effect(self) -> PropertyEffect:
        return PropertyEffect(_label(self.label), (self.property,))

    def cleanup_effect(self) -> PropertyEffect:
        return self.property_effect()


@dataclass(frozen=True)
class SetProperties:
    node: str
    properties: dict[str, Any]
    label: str | None = None

    def validate(self) -> None:
        _require_label(self.label)

    def compile(self) -> str:
        assignments = ", ".join(
            f"{self.node}.{key} = {_cypher_literal(value)}"
            for key, value in self.properties.items()
        )
        return f"SET {assignments}"

    def relationship_effect(self) -> RelationshipEffect | None:
        return None

    def property_effect(self) -> PropertyEffect:
        return PropertyEffect(_label(self.label), tuple(self.properties))

    def cleanup_effect(self) -> PropertyEffect:
        return self.property_effect()


@dataclass(frozen=True)
class SetRelationshipProperty:
    rel: str
    property: str
    value: Any
    source_label: str = ""
    rel_label: str = ""
    target_label: str | None = None

    def validate(self) -> None:
        return None

    def compile(self) -> str:
        return f"SET {self.rel}.{self.property} = {_cypher_literal(self.value)}"

    def relationship_effect(self) -> RelationshipEffect | None:
        return None

    def property_effect(self) -> RelationshipPropertyEffect:
        return RelationshipPropertyEffect(
            self.source_label,
            self.rel_label,
            (self.property,),
            self.target_label,
        )

    def cleanup_effect(self) -> RelationshipPropertyEffect:
        return self.property_effect()


@dataclass(frozen=True)
class AddToSet:
    node: str
    property: str
    value: Any
    label: str | None = None

    def validate(self) -> None:
        _require_label(self.label)

    def compile(self) -> str:
        value = _cypher_literal(self.value)
        return (
            f"SET {self.node}.{self.property} = "
            f"CASE WHEN {self.node}.{self.property} IS NULL THEN [{value}] "
            f"WHEN NOT {value} IN {self.node}.{self.property} "
            f"THEN {self.node}.{self.property} + [{value}] "
            f"ELSE {self.node}.{self.property} END"
        )

    def relationship_effect(self) -> RelationshipEffect | None:
        return None

    def property_effect(self) -> PropertyEffect:
        return PropertyEffect(_label(self.label), (self.property,))

    def cleanup_effect(self) -> PropertyEffect:
        return self.property_effect()


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
    # Override to "target" when the target, not the source, is under AnalysisJob.scope.
    scoped_to: Literal["source", "target"] = "source"

    def validate(self) -> None:
        return None

    def compile(self) -> str:
        rel = (
            f"({self.source})-[{self.rel_alias}:{self.rel}]-({self.target})"
            if self.undirected
            else f"({self.source})-[{self.rel_alias}:{self.rel}]->({self.target})"
        )
        property_assignments = ""
        if self.properties:
            property_assignments = ", " + ", ".join(
                f"{self.rel_alias}.{key} = {_cypher_literal(value)}"
                for key, value in self.properties.items()
            )
        firstseen_value = _cypher_literal(self.firstseen or Expr("timestamp()"))
        return (
            f"MERGE {rel}\n"
            f"ON CREATE SET {self.rel_alias}.firstseen = {firstseen_value}\n"
            f"SET {self.rel_alias}.lastupdated = $UPDATE_TAG{property_assignments}"
        )

    def relationship_effect(self) -> RelationshipEffect:
        return RelationshipEffect(
            self.source_label,
            self.rel,
            self.target_label,
            tuple(self.properties or ()),
            LinkDirection.OUTWARD if not self.undirected else None,
            self.scoped_to,
        )

    def property_effect(self) -> PropertyEffect | RelationshipPropertyEffect | None:
        return None

    def cleanup_effect(self) -> RelationshipEffect:
        return self.relationship_effect()


@dataclass(frozen=True)
class Expr:
    value: str


StatementEffect = (
    SetProperty | SetProperties | SetRelationshipProperty | AddToSet | AddRelationship
)


def _require_label(label: str | None) -> None:
    if not label:
        raise ValueError("Property effects require label for cleanup.")


def _label(label: str | None) -> str:
    _require_label(label)
    return label or ""


@singledispatch
def _cypher_literal(value: Any) -> str:
    raise TypeError(f"Unsupported Cypher literal: {value!r}")


@_cypher_literal.register
def _(value: Expr) -> str:
    return value.value


@_cypher_literal.register
def _(value: bool) -> str:
    return str(value).lower()


@_cypher_literal.register
def _(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


@_cypher_literal.register(type(None))
def _(_: None) -> str:
    return "NULL"


@_cypher_literal.register
def _(value: int) -> str:
    return str(value)


@_cypher_literal.register
def _(value: float) -> str:
    return str(value)


@_cypher_literal.register
def _(value: list) -> str:
    return "[" + ", ".join(_cypher_literal(v) for v in value) + "]"


@_cypher_literal.register
def _(value: tuple) -> str:
    return "[" + ", ".join(_cypher_literal(v) for v in value) + "]"


@dataclass(frozen=True)
class RelationshipEffect:
    source_label: str
    rel_label: str
    target_label: str
    properties: tuple[str, ...] = ()
    direction: LinkDirection | None = LinkDirection.OUTWARD
    scoped_to: Literal["source", "target"] = "source"
    cleanup_before_statements: bool = False

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
    cleanup_before_statements: bool = True

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
    cleanup_before_statements: bool = True

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
            rel_effect = effect.relationship_effect()
            if rel_effect and rel_effect not in relationships:
                relationships.append(rel_effect)
        return tuple(relationships)

    def properties_set(self) -> tuple[PropertyEffect | RelationshipPropertyEffect, ...]:
        properties: list[PropertyEffect | RelationshipPropertyEffect] = []
        for effect in self._effects():
            prop_effect = effect.property_effect()
            if prop_effect and prop_effect not in properties:
                properties.append(prop_effect)
        return tuple(properties)

    def to_graph_job(self) -> GraphJob:
        statements: list[GraphStatement] = []
        parent_name = self.short_name or self.name

        cleanup_effects = self._cleanup_effects()

        for effect in cleanup_effects:
            if effect.cleanup_before_statements:
                statements.append(
                    self._cleanup_statement(effect, parent_name, len(statements) + 1)
                )

        for offset, statement in enumerate(self.statements, start=len(statements) + 1):
            statements.append(statement.to_graph_statement(parent_name, offset))

        for effect in cleanup_effects:
            if not effect.cleanup_before_statements:
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
            cleanup = effect.cleanup_effect()
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
