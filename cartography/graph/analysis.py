from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from typing import Sequence
from typing import TypeAlias

from cartography.models.core.relationships import LinkDirection


@dataclass(frozen=True)
class CleanupScopedTo:
    """Restrict generated cleanup to nodes attached to a scoped resource."""

    label: str
    id_param: str
    id_property: str = "id"
    rel_label: str = "RESOURCE"


@dataclass(frozen=True)
class AnalysisStatement:
    """
    One analysis statement, either raw Cypher or a match plus typed effects.

    query is for hand-written Cypher and cannot be combined with match/effects.
    match provides the read pattern for typed effects. effects declare the write
    operations and generated cleanup coverage. iterative and iterationsize apply
    only to this statement's write query; generated cleanup statements are
    iterative separately and use AnalysisJob.cleanup_iterationsize.
    """

    query: str | None = None
    comment: str | None = None
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


@dataclass(frozen=True)
class SetProperty:
    """Set one node property; label is required for generated cleanup."""

    node: str
    property: str
    value: CypherValue
    label: str | None = None


@dataclass(frozen=True)
class SetProperties:
    """Set multiple node properties; label is required for generated cleanup."""

    node: str
    properties: dict[str, CypherValue]
    label: str | None = None


@dataclass(frozen=True)
class SetRelationshipProperty:
    """Set one relationship property and declare its cleanup pattern."""

    rel: str
    property: str
    value: CypherValue
    source_label: str | None = None
    rel_label: str | None = None
    target_label: str | None = None


@dataclass(frozen=True)
class SetRelationshipPropertyIfMissing:
    """Set one relationship property only when the match already excludes existing values."""

    rel: str
    property: str
    value: CypherValue


@dataclass(frozen=True)
class AddToSet:
    """Append a value to a list-like node property if it is not already present."""

    node: str
    property: str
    value: CypherValue
    label: str | None = None


@dataclass(frozen=True)
class AddValuesToSet:
    """Append multiple values to a list-like node property."""

    node: str
    property: str
    values: Sequence[CypherValue]
    label: str | None = None


@dataclass(frozen=True)
class AddRelationship:
    """Create a relationship and declare the labels needed for generated cleanup."""

    source: str
    rel: str
    target: str
    source_label: str | None = None
    target_label: str | None = None
    rel_alias: str = "r"
    properties: dict[str, CypherValue] | None = None
    undirected: bool = False
    firstseen: CypherValue = None
    # Override to "target" when cleanup scope reaches the target, not the source.
    scoped_to: Literal["source", "target"] = "source"
    cleanup_where: str | None = None


@dataclass(frozen=True)
class Var:
    """Cypher variable or property reference used as an effect value."""

    value: str


@dataclass(frozen=True)
class Param:
    """Cypher parameter reference used as an effect value."""

    name: str


@dataclass(frozen=True)
class RawCypher:
    """Raw Cypher expression used as an effect value."""

    value: str


@dataclass(frozen=True)
class Case:
    """Cypher CASE expression with raw Cypher conditions."""

    when: Sequence[tuple[str, CypherValue]]
    else_: CypherValue


CypherValue: TypeAlias = (
    str | bool | int | float | list[str] | None | Var | Param | RawCypher | Case
)

StatementEffect = (
    SetProperty
    | SetProperties
    | SetRelationshipProperty
    | SetRelationshipPropertyIfMissing
    | AddToSet
    | AddValuesToSet
    | AddRelationship
)


@dataclass(frozen=True)
class RelationshipEffect:
    """Relationship cleanup declaration derived from AddRelationship effects."""

    source_label: str
    rel_label: str
    target_label: str
    properties: tuple[str, ...] = ()
    direction: LinkDirection | None = LinkDirection.OUTWARD
    scoped_to: Literal["source", "target"] = "source"
    cleanup_before_statements: bool = False
    cleanup_where: str = ""


@dataclass(frozen=True)
class PropertyEffect:
    """Node-property cleanup declaration derived from property effects."""

    node_label: str
    properties: tuple[str, ...]
    cleanup_before_statements: bool = True

    def __post_init__(self) -> None:
        if not self.properties:
            raise ValueError("PropertyEffect requires at least one property.")


@dataclass(frozen=True)
class RelationshipPropertyEffect:
    """Relationship-property cleanup declaration derived from relationship effects."""

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


AnalysisEffect = RelationshipEffect | PropertyEffect | RelationshipPropertyEffect


@dataclass(frozen=True)
class AnalysisJob:
    """Named analysis job compiled into a GraphJob with generated cleanup."""

    name: str
    statements: Sequence[AnalysisStatement]
    scope: CleanupScopedTo | None = None
    short_name: str | None = None
    cleanup_iterationsize: int = 10000

    def __post_init__(self) -> None:
        if not self.statements:
            raise ValueError("AnalysisJob requires at least one statement.")
