from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Literal
from typing import Sequence

from cartography.models.core.relationships import LinkDirection


@dataclass(frozen=True)
class ScopedTo:
    label: str
    id_param: str
    id_property: str = "id"
    rel_label: str = "RESOURCE"


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


@dataclass(frozen=True)
class SetProperty:
    node: str
    property: str
    value: Any
    label: str | None = None


@dataclass(frozen=True)
class SetProperties:
    node: str
    properties: dict[str, Any]
    label: str | None = None


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
    label: str | None = None


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
    cleanup_where: str = ""


@dataclass(frozen=True)
class Expr:
    value: str


StatementEffect = (
    SetProperty | SetProperties | SetRelationshipProperty | AddToSet | AddRelationship
)


@dataclass(frozen=True)
class RelationshipEffect:
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
    node_label: str
    properties: tuple[str, ...]
    cleanup_before_statements: bool = True

    def __post_init__(self) -> None:
        if not self.properties:
            raise ValueError("PropertyEffect requires at least one property.")


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
