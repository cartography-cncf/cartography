"""Compile typed analysis jobs into Cypher GraphJobs and generated cleanups."""

from __future__ import annotations

import re
from functools import singledispatch
from typing import Any
from typing import cast

from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AddToSet
from cartography.graph.analysis import AddValuesToSet
from cartography.graph.analysis import AnalysisEffect
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import Case
from cartography.graph.analysis import IncrementalMatch
from cartography.graph.analysis import IncrementalTarget
from cartography.graph.analysis import Param
from cartography.graph.analysis import PropertyEffect
from cartography.graph.analysis import RawCypher
from cartography.graph.analysis import RelationshipEffect
from cartography.graph.analysis import RelationshipPropertyEffect
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperties
from cartography.graph.analysis import SetProperty
from cartography.graph.analysis import SetRelationshipProperty
from cartography.graph.analysis import SetRelationshipPropertyIfMissing
from cartography.graph.analysis import StatementEffect
from cartography.graph.analysis import Var
from cartography.graph.job import GraphJob
from cartography.graph.statement import GraphStatement
from cartography.models.core.relationships import LinkDirection


def compile_query(
    statement: AnalysisStatement,
    *,
    scope: ScopeById | None = None,
    scope_index: int = 0,
) -> str:
    if statement.query:
        if scope or statement.incremental_on:
            raise ValueError("Raw analysis queries do not support structural scoping.")
        return statement.query
    if statement.match is None:
        raise ValueError("AnalysisStatement requires match or query.")
    for effect in statement.effects:
        _cleanup_effect(effect)
    prefixes: list[str] = []
    if scope:
        prefixes.append(_declared_scope_match(scope, scope_index))
    prefixes.extend(_incremental_matches(statement))
    return "\n".join(
        (
            *prefixes,
            statement.match.strip(),
            *(_compile_effect(e) for e in statement.effects),
        )
    )


def to_graph_statement(
    statement: AnalysisStatement,
    parent_job_name: str,
    sequence_num: int,
    *,
    scope: ScopeById | None = None,
    scope_index: int = 0,
) -> GraphStatement:
    return GraphStatement(
        compile_query(statement, scope=scope, scope_index=scope_index),
        iterative=statement.iterative,
        iterationsize=statement.iterationsize,
        parent_job_name=parent_job_name,
        parent_job_sequence_num=sequence_num,
    )


def relationships_added(job: AnalysisJob) -> tuple[RelationshipEffect, ...]:
    relationships: list[RelationshipEffect] = []
    for effect in _effects(job):
        rel_effect = _relationship_effect(effect)
        if rel_effect and rel_effect not in relationships:
            relationships.append(rel_effect)
    return tuple(relationships)


def properties_set(
    job: AnalysisJob,
) -> tuple[PropertyEffect | RelationshipPropertyEffect, ...]:
    properties: list[PropertyEffect | RelationshipPropertyEffect] = []
    for effect in _effects(job):
        prop_effect = _property_effect(effect)
        if prop_effect and prop_effect not in properties:
            properties.append(prop_effect)
    return tuple(properties)


def to_graph_job(job: AnalysisJob) -> GraphJob:
    statements: list[GraphStatement] = []
    parent_name = job.short_name or job.name

    cleanup_effects = _cleanup_effects(job)

    for effect in cleanup_effects:
        if effect.cleanup_before_statements:
            statements.append(
                _cleanup_statement(job, effect, parent_name, len(statements) + 1)
            )

    for scope_index, statement in enumerate(job.statements):
        statements.append(
            to_graph_statement(
                statement,
                parent_name,
                len(statements) + 1,
                scope=job.scope,
                scope_index=scope_index,
            )
        )

    for effect in cleanup_effects:
        if not effect.cleanup_before_statements:
            statements.append(
                _cleanup_statement(job, effect, parent_name, len(statements) + 1)
            )

    return GraphJob(job.name, statements, job.short_name)


def cleanup_query(effect: AnalysisEffect, scope: ScopeById | None) -> str:
    return _cleanup_query(effect, scope)


def _effects(job: AnalysisJob) -> tuple[StatementEffect, ...]:
    return tuple(effect for statement in job.statements for effect in statement.effects)


def _cleanup_effects(job: AnalysisJob) -> tuple[AnalysisEffect, ...]:
    cleanups: list[AnalysisEffect] = []
    for effect in _effects(job):
        cleanup = _cleanup_effect(effect)
        if cleanup and cleanup not in cleanups:
            cleanups.append(cleanup)
    return tuple(cleanups)


def _cleanup_statement(
    job: AnalysisJob,
    effect: AnalysisEffect,
    parent_name: str,
    sequence_num: int,
) -> GraphStatement:
    return GraphStatement(
        cleanup_query(effect, job.scope),
        iterative=True,
        iterationsize=job.cleanup_iterationsize,
        parent_job_name=parent_name,
        parent_job_sequence_num=sequence_num,
    )


_CYPHER_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(value: str, description: str) -> str:
    if not _CYPHER_IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid Cypher {description}: {value!r}")
    return value


def _declared_scope_match(
    scope: ScopeById,
    scope_index: int,
) -> str:
    if scope.scope_on is None:
        raise ValueError("ScopeById requires scope_on for analysis queries.")
    alias = (
        scope.scope_on
        if isinstance(scope.scope_on, str)
        else scope.scope_on[scope_index]
    )
    scope_label = _validate_identifier(scope.label, "scope label")
    id_property = _validate_identifier(scope.id_property, "scope ID property")
    id_param = _validate_identifier(scope.id_param, "scope ID parameter")
    rel_label = _validate_identifier(scope.rel_label, "scope relationship label")
    _validate_identifier(alias, "scope variable")
    return (
        f"MATCH (scope:{scope_label} "
        f"{{{id_property}: ${id_param}}})-[:{rel_label}]->({alias})"
    )


def _incremental_targets(
    statement: AnalysisStatement,
) -> tuple[IncrementalMatch, ...]:
    incremental_on = statement.incremental_on
    if incremental_on is None:
        return ()
    targets: tuple[IncrementalTarget, ...]
    if isinstance(incremental_on, (str, IncrementalMatch)):
        targets = (incremental_on,)
    else:
        targets = tuple(incremental_on)
    return tuple(
        target if isinstance(target, IncrementalMatch) else IncrementalMatch(target)
        for target in targets
    )


def _incremental_matches(statement: AnalysisStatement) -> tuple[str, ...]:
    if statement.match is None:
        return ()
    matches: list[str] = []
    for target in _incremental_targets(statement):
        variable = _validate_identifier(target.variable, "incremental variable")
        if target.relationship:
            rel_type = _relationship_type_for_alias(statement.match, variable)
            rel_label = f":{rel_type}" if rel_type else ""
            matches.append(
                f"MATCH ()-[{variable}{rel_label} " "{lastupdated: $UPDATE_TAG}]->()"
            )
        else:
            label = _node_label_for_alias(statement.match, variable)
            node_label = f":{label}" if label else ""
            matches.append(
                f"MATCH ({variable}{node_label} " "{lastupdated: $UPDATE_TAG})"
            )
    return tuple(matches)


def _node_label_for_alias(match: str, alias: str) -> str | None:
    pattern = re.compile(rf"\(\s*{re.escape(alias)}\s*:\s*([A-Za-z_][A-Za-z0-9_]*)")
    found = pattern.search(match)
    return found.group(1) if found else None


def _relationship_type_for_alias(match: str, alias: str) -> str | None:
    pattern = re.compile(rf"\[\s*{re.escape(alias)}\s*:\s*([A-Za-z_][A-Za-z0-9_]*)")
    found = pattern.search(match)
    return found.group(1) if found else None


def _require_label(label: str | None) -> str:
    if not label:
        raise ValueError("Property effects require label for cleanup.")
    return label


def _scope_match(scope: ScopeById, alias: str) -> str:
    return f"({alias}:{scope.label} {{{scope.id_property}: ${scope.id_param}}})"


@singledispatch
def _compile_effect(effect: StatementEffect) -> str:
    raise TypeError(f"Unsupported analysis effect: {effect!r}")


@_compile_effect.register
def _(effect: SetProperty) -> str:
    return f"SET {effect.node}.{effect.property} = {_cypher_literal(effect.value)}"


@_compile_effect.register
def _(effect: SetProperties) -> str:
    assignments = ", ".join(
        f"{effect.node}.{key} = {_cypher_literal(value)}"
        for key, value in effect.properties.items()
    )
    return f"SET {assignments}"


@_compile_effect.register
def _(effect: SetRelationshipProperty) -> str:
    return f"SET {effect.rel}.{effect.property} = {_cypher_literal(effect.value)}"


@_compile_effect.register
def _(effect: SetRelationshipPropertyIfMissing) -> str:
    return f"SET {effect.rel}.{effect.property} = {_cypher_literal(effect.value)}"


@_compile_effect.register
def _(effect: AddToSet) -> str:
    value = _cypher_literal(effect.value)
    return _add_to_set_query(effect.node, effect.property, value)


@_compile_effect.register
def _(effect: AddValuesToSet) -> str:
    return "\n".join(
        _add_to_set_query(effect.node, effect.property, _cypher_literal(value))
        for value in effect.values
    )


def _add_to_set_query(node: str, property_name: str, value: str) -> str:
    return (
        f"SET {node}.{property_name} = "
        f"CASE WHEN {node}.{property_name} IS NULL THEN [{value}] "
        f"WHEN NOT {value} IN {node}.{property_name} "
        f"THEN {node}.{property_name} + [{value}] "
        f"ELSE {node}.{property_name} END"
    )


@_compile_effect.register
def _(effect: AddRelationship) -> str:
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
    firstseen_value = _cypher_literal(effect.firstseen or RawCypher("timestamp()"))
    return (
        f"MERGE {rel}\n"
        f"ON CREATE SET {effect.rel_alias}.firstseen = {firstseen_value}\n"
        f"SET {effect.rel_alias}.lastupdated = $UPDATE_TAG{property_assignments}"
    )


@singledispatch
def _relationship_effect(_: StatementEffect) -> RelationshipEffect | None:
    return None


@_relationship_effect.register
def _(effect: AddRelationship) -> RelationshipEffect:
    return RelationshipEffect(
        effect.source_label or "",
        effect.rel,
        effect.target_label or "",
        tuple(effect.properties or ()),
        LinkDirection.OUTWARD if not effect.undirected else None,
        effect.scoped_to,
        cleanup_where=effect.cleanup_where or "",
    )


@singledispatch
def _property_effect(
    _: StatementEffect,
) -> PropertyEffect | RelationshipPropertyEffect | None:
    return None


@_property_effect.register
def _(effect: SetProperty) -> PropertyEffect:
    return PropertyEffect(_require_label(effect.label), (effect.property,))


@_property_effect.register
def _(effect: SetProperties) -> PropertyEffect:
    return PropertyEffect(_require_label(effect.label), tuple(effect.properties))


@_property_effect.register
def _(effect: AddToSet) -> PropertyEffect:
    return PropertyEffect(_require_label(effect.label), (effect.property,))


@_property_effect.register
def _(effect: AddValuesToSet) -> PropertyEffect:
    return PropertyEffect(_require_label(effect.label), (effect.property,))


@_property_effect.register
def _(effect: SetRelationshipProperty) -> RelationshipPropertyEffect:
    return RelationshipPropertyEffect(
        effect.source_label or "",
        effect.rel_label or "",
        (effect.property,),
        effect.target_label,
    )


@singledispatch
def _cleanup_effect(effect: StatementEffect) -> AnalysisEffect | None:
    raise TypeError(f"Unsupported analysis effect: {effect!r}")


@_cleanup_effect.register
def _(effect: SetProperty) -> PropertyEffect:
    return cast(PropertyEffect, _property_effect(effect))


@_cleanup_effect.register
def _(effect: SetProperties) -> PropertyEffect:
    return cast(PropertyEffect, _property_effect(effect))


@_cleanup_effect.register
def _(effect: AddToSet) -> PropertyEffect:
    return cast(PropertyEffect, _property_effect(effect))


@_cleanup_effect.register
def _(effect: AddValuesToSet) -> PropertyEffect:
    return cast(PropertyEffect, _property_effect(effect))


@_cleanup_effect.register
def _(effect: SetRelationshipProperty) -> RelationshipPropertyEffect:
    return cast(RelationshipPropertyEffect, _property_effect(effect))


@_cleanup_effect.register
def _(_: SetRelationshipPropertyIfMissing) -> None:
    return None


@_cleanup_effect.register
def _(effect: AddRelationship) -> RelationshipEffect:
    return cast(RelationshipEffect, _relationship_effect(effect))


@singledispatch
def _cleanup_query(effect: AnalysisEffect, scope: ScopeById | None) -> str:
    raise TypeError(f"Unsupported cleanup effect: {effect!r}")


@_cleanup_query.register
def _(effect: RelationshipEffect, scope: ScopeById | None) -> str:
    source = f"(source:{effect.source_label})"
    target = f"(target:{effect.target_label})"
    rel = f"[r:{effect.rel_label}]"
    if effect.direction == LinkDirection.INWARD:
        pattern = f"{source}<-{rel}-{target}"
    elif effect.direction == LinkDirection.OUTWARD:
        pattern = f"{source}-{rel}->{target}"
    else:
        pattern = f"{source}-{rel}-{target}"

    match = f"MATCH {pattern}"
    if scope:
        scoped_alias = effect.scoped_to
        match = (
            f"MATCH {_scope_match(scope, 'scope')}-[:{scope.rel_label}]->"
            f"({scoped_alias})\n{match}"
        )

    filters = ["r.lastupdated <> $UPDATE_TAG"]
    if effect.cleanup_where:
        filters.append(f"({effect.cleanup_where})")

    return (
        f"{match}\n"
        f"WHERE {' AND '.join(filters)}\n"
        "WITH r LIMIT $LIMIT_SIZE\n"
        "DELETE r"
    )


@_cleanup_query.register
def _(effect: PropertyEffect, scope: ScopeById | None) -> str:
    node = f"(node:{effect.node_label})"
    match = f"MATCH {node}"
    if scope:
        match = f"MATCH {_scope_match(scope, 'scope')}-[:{scope.rel_label}]->{node}"
    props = ", ".join(f"node.{prop}" for prop in effect.properties)
    filters = " OR ".join(f"node.{prop} IS NOT NULL" for prop in effect.properties)
    return f"{match}\nWHERE {filters}\nWITH node LIMIT $LIMIT_SIZE\nREMOVE {props}"


@_cleanup_query.register
def _(effect: RelationshipPropertyEffect, scope: ScopeById | None) -> str:
    source = f"(source:{effect.source_label})"
    target = f"(target:{effect.target_label})" if effect.target_label else "(target)"
    rel = f"[r:{effect.rel_label}]"
    if effect.direction == LinkDirection.INWARD:
        pattern = f"{source}<-{rel}-{target}"
    else:
        pattern = f"{source}-{rel}->{target}"

    match = f"MATCH {pattern}"
    if scope:
        match = f"MATCH {_scope_match(scope, 'scope')}-[:{scope.rel_label}]->(source)\n{match}"

    props = ", ".join(f"r.{prop}" for prop in effect.properties)
    filters = " OR ".join(f"r.{prop} IS NOT NULL" for prop in effect.properties)
    return f"{match}\nWHERE {filters}\nWITH r LIMIT $LIMIT_SIZE\nREMOVE {props}"


@singledispatch
def _cypher_literal(value: Any) -> str:
    raise TypeError(f"Unsupported Cypher literal: {value!r}")


@_cypher_literal.register
def _(value: Var) -> str:
    return value.value


@_cypher_literal.register
def _(value: Param) -> str:
    return value.name if value.name.startswith("$") else f"${value.name}"


@_cypher_literal.register
def _(value: RawCypher) -> str:
    return value.value


@_cypher_literal.register
def _(value: Case) -> str:
    branches = " ".join(
        f"WHEN {condition} THEN {_cypher_literal(result)}"
        for condition, result in value.when
    )
    return f"CASE {branches} ELSE {_cypher_literal(value.else_)} END"


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
