from __future__ import annotations

import importlib
import inspect
from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields as dataclass_fields
from dataclasses import replace
from pathlib import Path
from pkgutil import walk_packages
from types import ModuleType
from typing import cast
from typing import TypeVar

import yaml

import cartography.analysis
import cartography.models
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import PropertyEffect
from cartography.graph.analysis import RelationshipEffect
from cartography.graph.analysis import RelationshipPropertyEffect
from cartography.graph.analysis import SetRelationshipPropertyIfMissing
from cartography.graph.analysisbuilder import properties_set
from cartography.graph.analysisbuilder import relationships_added
from cartography.models.aws_tagging import AWS_TAGGABLE_RESOURCES
from cartography.models.bbot.events import BBOT_RELATIONSHIP_CATALOG
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.nodes import LabelKind
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import OtherRelationships
from cartography.models.gcp.resource_catalog import GCP_POLICY_BINDING_TARGET_LABELS
from cartography.models.github.repos import GITHUB_COLLABORATOR_REL_LABELS
from cartography.models.ontology.constraints import ONTOLOGY_REL_CONSTRAINTS
from cartography.models.ontology.mapping import ONTOLOGY_MODELS
from cartography.models.ontology.mapping import ONTOLOGY_NODES_MAPPING
from cartography.models.ontology.mapping import SEMANTIC_LABEL_BY_CATEGORY
from cartography.models.ontology.mapping import SEMANTIC_LABELS_MAPPING
from cartography.models.ontology.mapping import (
    SEMANTIC_LABELS_WITHOUT_NORMALIZED_FIELDS,
)

# Downstream consumers introspect the data model through these names. Everything else in
# this module is an implementation detail and may change without notice.
__all__ = [
    # Entry points
    "inspect_data_model",
    "build_data_model",
    "iter_model_classes",
    "iter_analysis_jobs",
    "iter_permission_relationships",
    "iter_relationship_catalog",
    # Scoping one module's view
    "scope_node_to_module",
    "relationships_for_module",
    "relationships_for_node",
    "relationship_touches_node",
    "labels_carried_by",
    # Result types
    "DataModel",
    "Node",
    "Relationship",
    "NodeRelationship",
    "Property",
    "PropertyProvenance",
    "NodeLabelProvenance",
    "AnalysisJobDefinition",
    "PermissionRelationshipDefinition",
    "TargetPreconditionDefinition",
    "RelationshipCatalogDefinition",
    "OntologySemanticLabel",
    "OntologyRelationshipConstraint",
    "OntologyExpectedEdge",
    "ModelClass",
]

ModelClass = type[
    CartographyNodeSchema
    | CartographyRelSchema
    | CartographyNodeProperties
    | CartographyRelProperties
]

_MODEL_BASE_CLASSES = (
    CartographyNodeSchema,
    CartographyRelSchema,
    CartographyNodeProperties,
    CartographyRelProperties,
)
_Schema = TypeVar("_Schema", CartographyNodeSchema, CartographyRelSchema)
RelationshipKey = tuple[str, str, str, LinkDirection | None]
_INTROSPECTION_EXCLUDE_FLAG = "__cartography_introspection_exclude__"
_ONT_SOURCE_DESCRIPTION = "Module that populated this node's ontology fields."
_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_PERMISSION_RELATIONSHIP_FILES = {
    "aws": (
        Path("cartography/data/permission_relationships.yaml"),
        ("AWSPrincipal",),
    ),
    "gcp": (
        Path("cartography/data/gcp_permission_relationships.yaml"),
        ("GCPPrincipal",),
    ),
    "azure": (
        Path("cartography/data/azure_permission_relationships.yaml"),
        ("EntraUser", "EntraGroup", "EntraServicePrincipal"),
    ),
}


@dataclass(frozen=True)
class AnalysisJobDefinition:
    """An analysis job discovered at its defining module path."""

    job: AnalysisJob
    module: str
    qualified_name: str


@dataclass(frozen=True)
class TargetPreconditionDefinition:
    """Graph state required on a permission relationship target."""

    related_label: str
    relationship: str
    direction: str = "outgoing"


@dataclass(frozen=True)
class PermissionRelationshipDefinition:
    """A relationship generated from a provider permission evaluation file."""

    provider: str
    source_label: str
    target_label: str
    relationship_name: str
    permissions: tuple[str, ...]
    config_path: str
    target_precondition: TargetPreconditionDefinition | None = None


@dataclass(frozen=True)
class RelationshipCatalogDefinition:
    """A runtime-created relationship declared for model introspection."""

    module: str
    source_label: str
    target_label: str
    relationship_name: str
    description: str
    properties: tuple[str, ...]
    catalog_path: str


@dataclass(frozen=True)
class Property:
    """A graph property computed from one or more data-model declarations."""

    name: str
    source_names: tuple[str, ...]
    descriptions: tuple[str, ...]
    indexed: bool
    ontology: bool
    generated_by: tuple[str, ...]
    owner_modules: tuple[str, ...]
    analysis_jobs: tuple[AnalysisJobDefinition, ...]
    provenance: tuple[PropertyProvenance, ...]


@dataclass(frozen=True)
class PropertyProvenance:
    """One module's contribution to an aggregated graph property."""

    module: str
    source_name: str
    description: str | None
    indexed: bool
    property_ref: PropertyRef


@dataclass(frozen=True)
class NodeLabelProvenance:
    """Labels contributed by one node schema."""

    module: str
    schema: str
    description: str | None
    extra_labels: tuple[str, ...]
    conditional_labels: tuple[ExtraNodeLabel, ...]
    label_definitions: tuple[ExtraNodeLabel, ...]


@dataclass(frozen=True)
class Node:
    """A graph node computed from every schema contributing to one label."""

    label: str
    descriptions: tuple[str, ...]
    extra_labels: tuple[str, ...]
    conditional_labels: tuple[ExtraNodeLabel, ...]
    properties: tuple[Property, ...]
    modules: tuple[str, ...]
    schemas: tuple[CartographyNodeSchema, ...]
    ontology_labels: tuple[str, ...] = ()
    ontology_projections: tuple[str, ...] = ()
    partial_extra_labels: tuple[str, ...] = ()
    label_provenance: tuple[NodeLabelProvenance, ...] = ()
    label_definitions: tuple[ExtraNodeLabel, ...] = ()

    def get_property(self, name: str) -> Property | None:
        return next((prop for prop in self.properties if prop.name == name), None)


@dataclass(frozen=True)
class Relationship:
    """A graph relationship computed from schemas or typed analysis jobs."""

    source_label: str
    label: str
    target_label: str
    direction: LinkDirection | None
    descriptions: tuple[str, ...]
    properties: tuple[Property, ...]
    modules: tuple[str, ...]
    origins: tuple[str, ...]
    schemas: tuple[CartographyRelSchema, ...]
    analysis_jobs: tuple[AnalysisJobDefinition, ...]
    permission_relationships: tuple[PermissionRelationshipDefinition, ...] = ()
    catalog_relationships: tuple[RelationshipCatalogDefinition, ...] = ()


@dataclass(frozen=True)
class OntologySemanticLabel:
    """A semantic ontology label aggregated from every provider mapping."""

    label: str
    mapping_group: str | None
    descriptions: tuple[str, ...]
    properties: tuple[Property, ...]
    concrete_node_labels: tuple[str, ...]


@dataclass(frozen=True)
class OntologyRelationshipConstraint:
    """
    A canonical relationship name validated between two ontology labels.

    Constraints only govern name and direction when both endpoints carry the listed
    ontology labels. They do not assert that the edge exists, and they are not
    inherited onto concrete node schemas. See ``OntologyExpectedEdge`` for edges
    that models or analysis actually materialize under ontology labels.
    """

    source_label: str
    label: str
    target_label: str


@dataclass(frozen=True)
class OntologyExpectedEdge:
    """
    A relationship materialized under ontology labels.

    Unlike ``OntologyRelationshipConstraint``, these edges are produced by node
    schemas, matchlinks, analysis jobs, permission evaluation, or the runtime
    catalog. Schema docs and autocomplete project them onto concrete nodes that
    carry either endpoint's semantic label, keeping the far endpoint semantic.
    """

    source_label: str
    label: str
    target_label: str
    direction: LinkDirection | None
    origins: tuple[str, ...]
    constrained: bool
    analysis_jobs: tuple[AnalysisJobDefinition, ...] = ()


@dataclass(frozen=True)
class NodeRelationship:
    """
    One relationship as seen from a specific node label.

    ``other_label`` keeps the opposite endpoint as declared on the underlying
    ``Relationship``. When this view is inherited from a semantic label the
    concrete carries, that far endpoint stays semantic (for example
    ``RESOLVED_IMAGE`` → ``Image``) instead of expanding to every provider
    concrete.
    """

    node_label: str
    label: str
    other_label: str
    direction: LinkDirection | None
    inherited: bool
    relationship: Relationship


@dataclass(frozen=True)
class DataModel:
    """Runtime view of Cartography's complete declarative graph model."""

    nodes: tuple[Node, ...]
    relationships: tuple[Relationship, ...]
    analysis_jobs: tuple[AnalysisJobDefinition, ...] = ()
    permission_relationships: tuple[PermissionRelationshipDefinition, ...] = ()
    ontology_semantic_labels: tuple[OntologySemanticLabel, ...] = ()
    ontology_relationship_constraints: tuple[OntologyRelationshipConstraint, ...] = ()
    ontology_expected_edges: tuple[OntologyExpectedEdge, ...] = ()
    diagnostics: tuple[str, ...] = ()
    catalog_relationships: tuple[RelationshipCatalogDefinition, ...] = ()

    def get_node(self, label: str) -> Node | None:
        return next((node for node in self.nodes if node.label == label), None)

    def relationships_for_node(self, label: str) -> tuple[NodeRelationship, ...]:
        """Return relationships applicable to one node, including inherited ontology edges."""
        return relationships_for_node(self, label)

    def for_module(self, module: str) -> DataModel:
        """
        Narrow the model to one module's view of the graph.

        Nodes keep only the properties and labels that module declares, and relationships
        include the cross-module edges that touch its nodes. This is the same view the
        generated schema page for that module renders.
        """
        nodes = tuple(
            scope_node_to_module(node, module)
            for node in self.nodes
            if module in node.modules
        )
        return DataModel(
            nodes=nodes,
            relationships=relationships_for_module(
                self.relationships,
                nodes,
                module,
                self.nodes,
            ),
            analysis_jobs=tuple(
                definition
                for definition in self.analysis_jobs
                if definition.module == module
            ),
            permission_relationships=tuple(
                definition
                for definition in self.permission_relationships
                if definition.provider == module
            ),
            catalog_relationships=tuple(
                definition
                for definition in self.catalog_relationships
                if definition.module == module
            ),
            ontology_semantic_labels=(
                self.ontology_semantic_labels if module == "ontology" else ()
            ),
            ontology_relationship_constraints=(
                self.ontology_relationship_constraints if module == "ontology" else ()
            ),
            ontology_expected_edges=(
                self.ontology_expected_edges if module == "ontology" else ()
            ),
            diagnostics=self.diagnostics,
        )


# Scoping a module's view of the graph. The generated schema pages and
# DataModel.for_module() share this code so that both answer identically.
def scope_node_to_module(node: Node, module: str) -> Node:
    """Scope an aggregated node to schemas and properties owned by one module."""
    provenance = tuple(item for item in node.label_provenance if item.module == module)
    if not provenance:
        return node

    label_sets = [set(item.extra_labels) for item in provenance]
    extra_labels = set().union(*label_sets)
    universal_labels = set.intersection(*label_sets) if label_sets else set()
    partial_labels = extra_labels - universal_labels
    conditional_labels = {
        (
            conditional.label,
            conditional.conditions,
        ): conditional
        for item in provenance
        for conditional in item.conditional_labels
    }
    scoped_conditional_labels = tuple(
        sorted(
            conditional_labels.values(),
            key=lambda conditional: (
                conditional.label,
                conditional.conditions,
            ),
        )
    )
    label_definitions = tuple(
        sorted(
            {
                definition
                for item in provenance
                for definition in item.label_definitions
            },
            key=lambda definition: (
                definition.label,
                definition.conditions,
                definition.kind.value,
            ),
        )
    )
    declared_labels = {
        *extra_labels,
        *(conditional.label for conditional in scoped_conditional_labels),
    }
    properties = tuple(
        scoped_property
        for prop in node.properties
        if (scoped_property := _scope_property_to_module(prop, module)) is not None
    )
    return replace(
        node,
        descriptions=tuple(
            sorted(
                {
                    item.description
                    for item in provenance
                    if item.description is not None
                }
            )
        ),
        extra_labels=tuple(sorted(extra_labels)),
        partial_extra_labels=tuple(sorted(partial_labels)),
        conditional_labels=scoped_conditional_labels,
        properties=properties,
        modules=(module,),
        schemas=tuple(
            schema
            for schema in node.schemas
            if _schema_owner_module(type(schema).__module__) == module
        ),
        ontology_labels=tuple(
            label for label in node.ontology_labels if label in declared_labels
        ),
        label_definitions=label_definitions,
    )


def _scope_property_to_module(prop: Property, module: str) -> Property | None:
    """Scope one aggregated property to declarations owned by a module."""
    if prop.owner_modules and module not in prop.owner_modules:
        # A generated property another module's ontology mapping contributed. Keeping it
        # would credit this module with a normalized field it never populates.
        return None
    if not prop.provenance:
        return prop

    scoped_provenance = tuple(item for item in prop.provenance if item.module == module)
    if not scoped_provenance:
        return None

    declared_modules = {item.module for item in prop.provenance}
    generated_sources = set(prop.source_names) - {
        item.source_name for item in prop.provenance
    }
    generated_descriptions = set(prop.descriptions) - {
        item.description for item in prop.provenance if item.description is not None
    }
    return replace(
        prop,
        source_names=tuple(
            sorted(
                generated_sources | {item.source_name for item in scoped_provenance},
            )
        ),
        descriptions=tuple(
            sorted(
                generated_descriptions
                | {
                    item.description
                    for item in scoped_provenance
                    if item.description is not None
                },
            )
        ),
        indexed=any(item.indexed for item in scoped_provenance),
        generated_by=tuple(
            sorted(
                {module}
                | {
                    source
                    for source in prop.generated_by
                    if source not in declared_modules
                },
            )
        ),
        provenance=scoped_provenance,
    )


def _schema_owner_module(module_name: str) -> str:
    parts = module_name.split(".")
    if len(parts) > 2 and parts[:2] == ["cartography", "models"]:
        return parts[2]
    return module_name


def _is_runtime_template(model_class: type) -> bool:
    """
    Whether a schema class is a runtime template rather than a described edge.

    Subclasses inherit the flag: a template stays a template however it is specialised.
    """
    return bool(getattr(model_class, _INTROSPECTION_EXCLUDE_FLAG, False))


def labels_carried_by(nodes: Iterable[Node]) -> set[str]:
    """Every label the given nodes answer to, primary plus extra, ontology and conditional."""
    carried: set[str] = set()
    for node in nodes:
        carried.add(node.label)
        carried.update(node.extra_labels)
        carried.update(node.ontology_labels)
        carried.update(label.label for label in node.conditional_labels)
    return carried


def relationships_for_module(
    relationships: tuple[Relationship, ...],
    nodes: tuple[Node, ...],
    module: str,
    all_nodes: tuple[Node, ...] = (),
) -> tuple[Relationship, ...]:
    """
    Select the relationships that describe a module's own slice of the graph.

    An edge qualifies when the module declares it, when it lands on one of the module's
    node labels, or when both endpoints are labels the module's nodes answer to.

    Requiring *both* endpoints is what stops a shared semantic label from dragging in
    other providers: several modules carry `DNSRecord`, so a one-sided match would
    document `(:DNSRecord)-[:DNS_POINTS_TO]->(:AWSEC2Instance)` on the GCP page.

    Ontology endpoints are the documented exception. Canonical nodes (`User`, `Package`)
    and semantic labels (`Container`, `Image`) are defined once and link across
    providers, so an edge between one of them and a label the module carries belongs
    on the module's page even when the module never declares the ontology side. That
    is what lets Kubernetes and Railway inherit ``RESOLVED_IMAGE → Image`` without
    owning an Image concrete.
    """
    own_labels = {node.label for node in nodes}
    carried_labels = labels_carried_by(nodes)
    ontology_endpoint_labels = {
        *(node.label for node in all_nodes if "ontology" in node.modules),
        *(label for node in all_nodes for label in node.ontology_labels),
    }

    def qualifies(relationship: Relationship) -> bool:
        if module in relationship.modules:
            return True
        endpoints = (relationship.source_label, relationship.target_label)
        if any(endpoint in own_labels for endpoint in endpoints):
            return True
        if all(endpoint in carried_labels for endpoint in endpoints):
            return True
        return any(
            endpoint in carried_labels and other in ontology_endpoint_labels
            for endpoint, other in (endpoints, endpoints[::-1])
        )

    return tuple(
        relationship for relationship in relationships if qualifies(relationship)
    )


def relationship_touches_node(relationship: Relationship, node: Node) -> bool:
    """Whether one node answers to either endpoint of a relationship."""
    carried = labels_carried_by((node,))
    return relationship.source_label in carried or relationship.target_label in carried


def relationships_for_node(
    model: DataModel,
    label: str,
) -> tuple[NodeRelationship, ...]:
    """
    Relationships applicable to one node label, including inherited ontology edges.

    Direct edges keep their declared endpoints. Edges whose source or target is a
    semantic/canonical ontology label that this node carries are projected onto the
    concrete with the far endpoint left semantic. Validation-only
    ``ontology_relationship_constraints`` are never included; only edges present in
    ``model.relationships`` (schemas, matchlinks, analysis, catalogs, permissions)
    participate.
    """
    node = _node_view_for_label(model, label)
    if node is None:
        return ()

    # Inherit only through the primary label and ontology labels. Ordinary or
    # compatibility extra labels must not pull in relationships declared against
    # those aliases.
    carried = {node.label, *node.ontology_labels}
    views: dict[tuple[str, str, LinkDirection | None], NodeRelationship] = {}
    for relationship in model.relationships:
        matches_source = relationship.source_label in carried
        matches_target = relationship.target_label in carried
        if not matches_source and not matches_target:
            continue

        # Prefer the primary-label side when a node answers to both endpoints
        # (self-loop or a node that also carries the far ontology label).
        if matches_source and (
            relationship.source_label == node.label or not matches_target
        ):
            other_label = relationship.target_label
            direction = relationship.direction
            inherited = relationship.source_label != node.label
        else:
            other_label = relationship.source_label
            direction = _flip_direction(relationship.direction)
            inherited = relationship.target_label != node.label

        key = (relationship.label, other_label, direction)
        existing = views.get(key)
        if existing is not None and not existing.inherited:
            # Keep a direct declaration over an inherited duplicate.
            continue
        if existing is not None and inherited:
            continue
        views[key] = NodeRelationship(
            node_label=node.label,
            label=relationship.label,
            other_label=other_label,
            direction=direction,
            inherited=inherited,
            relationship=relationship,
        )

    return tuple(
        sorted(
            views.values(),
            key=lambda view: (
                view.label,
                view.other_label,
                view.direction.name if view.direction else "",
                view.inherited,
            ),
        )
    )


def _node_view_for_label(model: DataModel, label: str) -> Node | None:
    """Resolve a primary node or a synthetic view of a semantic ontology label."""
    node = model.get_node(label)
    if node is not None:
        return node
    semantic = next(
        (entry for entry in model.ontology_semantic_labels if entry.label == label),
        None,
    )
    if semantic is None:
        return None
    return Node(
        label=semantic.label,
        descriptions=semantic.descriptions,
        extra_labels=(),
        conditional_labels=(),
        properties=semantic.properties,
        modules=("ontology",),
        schemas=(),
        ontology_labels=(semantic.label,),
    )


def _flip_direction(direction: LinkDirection | None) -> LinkDirection | None:
    if direction is None:
        return None
    if direction is LinkDirection.OUTWARD:
        return LinkDirection.INWARD
    return LinkDirection.OUTWARD


def iter_model_classes(
    package: ModuleType = cartography.models,
) -> Iterator[ModelClass]:
    """Yield model classes defined below a package in deterministic order."""
    discovered: dict[str, ModelClass] = {}
    module_names = sorted(
        module_info.name
        for module_info in walk_packages(
            package.__path__,
            prefix=f"{package.__name__}.",
        )
    )
    for module_name in module_names:
        module = importlib.import_module(module_name)
        for value in vars(module).values():
            if not inspect.isclass(value):
                continue
            if value.__name__.startswith("_"):
                continue
            if _is_runtime_template(value):
                continue
            if value in _MODEL_BASE_CLASSES or value.__module__ != module.__name__:
                continue
            if not any(base in value.__mro__ for base in _MODEL_BASE_CLASSES):
                continue
            qualified_name = f"{value.__module__}.{value.__qualname__}"
            discovered[qualified_name] = value

    for qualified_name in sorted(discovered):
        yield discovered[qualified_name]


def iter_analysis_jobs(
    package: ModuleType = cartography.analysis,
) -> Iterator[AnalysisJobDefinition]:
    """Yield typed analysis jobs defined below a package in deterministic order."""
    # Keyed by identity: some jobs carry dict-valued statement parameters, so
    # AnalysisJob is not hashable.
    discovered: dict[int, AnalysisJobDefinition] = {}
    module_names = sorted(
        module_info.name
        for module_info in walk_packages(
            package.__path__,
            prefix=f"{package.__name__}.",
        )
    )
    for module_name in module_names:
        module = importlib.import_module(module_name)
        for name, value in vars(module).items():
            jobs: tuple[AnalysisJob, ...]
            if isinstance(value, AnalysisJob):
                jobs = (value,)
            elif isinstance(value, tuple) and all(
                isinstance(item, AnalysisJob) for item in value
            ):
                jobs = value
            else:
                continue
            for index, job in enumerate(jobs):
                if id(job) in discovered:
                    continue
                suffix = "" if len(jobs) == 1 else f"[{index}]"
                discovered[id(job)] = AnalysisJobDefinition(
                    job=job,
                    module=_analysis_module_name(module.__name__),
                    qualified_name=f"{module.__name__}.{name}{suffix}",
                )

    yield from sorted(
        discovered.values(),
        key=lambda definition: definition.qualified_name,
    )


def iter_permission_relationships() -> Iterator[PermissionRelationshipDefinition]:
    """Yield concrete relationships from bundled permission evaluation files."""
    definitions: list[PermissionRelationshipDefinition] = []
    for provider, (relative_path, source_labels) in sorted(
        _PERMISSION_RELATIONSHIP_FILES.items()
    ):
        raw_definitions = yaml.safe_load((_REPOSITORY_ROOT / relative_path).read_text())
        if not isinstance(raw_definitions, list):
            raise ValueError(
                f"Permission relationship file {relative_path} must contain a list."
            )
        for raw_definition in raw_definitions:
            if not isinstance(raw_definition, dict):
                raise ValueError(
                    f"Permission relationship file {relative_path} contains "
                    "a non-mapping entry."
                )
            target_label = raw_definition.get("target_label")
            relationship_name = raw_definition.get("relationship_name")
            permissions = raw_definition.get("permissions")
            target_precondition = _parse_target_precondition(
                raw_definition.get("target_precondition"),
                relative_path,
                raw_definition,
            )
            if (
                not isinstance(target_label, str)
                or not isinstance(relationship_name, str)
                or not isinstance(permissions, list)
                or not all(isinstance(permission, str) for permission in permissions)
            ):
                raise ValueError(
                    f"Permission relationship file {relative_path} contains "
                    f"an invalid entry: {raw_definition!r}."
                )
            for source_label in source_labels:
                definitions.append(
                    PermissionRelationshipDefinition(
                        provider=provider,
                        source_label=source_label,
                        target_label=target_label,
                        relationship_name=relationship_name,
                        permissions=tuple(permissions),
                        config_path=relative_path.as_posix(),
                        target_precondition=target_precondition,
                    )
                )
    yield from sorted(
        definitions,
        key=lambda definition: (
            definition.provider,
            definition.source_label,
            definition.relationship_name,
            definition.target_label,
        ),
    )


def _parse_target_precondition(
    value: object,
    relative_path: Path,
    raw_definition: dict[str, object],
) -> TargetPreconditionDefinition | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(
            f"Permission relationship file {relative_path} contains "
            f"an invalid target_precondition: {raw_definition!r}."
        )
    related_label = value.get("related_label")
    relationship = value.get("relationship")
    direction = value.get("direction", "outgoing")
    if (
        not isinstance(related_label, str)
        or not isinstance(relationship, str)
        or not isinstance(direction, str)
        or direction.lower() not in {"incoming", "outgoing"}
    ):
        raise ValueError(
            f"Permission relationship file {relative_path} contains "
            f"an invalid target_precondition: {raw_definition!r}."
        )
    return TargetPreconditionDefinition(
        related_label=related_label,
        relationship=relationship,
        direction=direction.lower(),
    )


def iter_relationship_catalog() -> Iterator[RelationshipCatalogDefinition]:
    """
    Yield relationships created by runtime paths outside declarative schemas.

    These edges come from a data catalog rather than from a schema class, so their
    concrete endpoints only exist once the catalog is expanded.
    """
    definitions = [
        RelationshipCatalogDefinition(
            module="aws",
            source_label=resource.label,
            target_label="AWSTag",
            relationship_name="TAGGED",
            description=(
                f"`{resource.label}` is tagged with an `AWSTag` discovered by "
                "the AWS Resource Groups Tagging API."
            ),
            properties=("firstseen", "lastupdated"),
            catalog_path="cartography.models.aws_tagging.AWS_TAGGABLE_RESOURCES",
        )
        for resource in AWS_TAGGABLE_RESOURCES
    ]
    definitions.extend(
        RelationshipCatalogDefinition(
            module="bbot",
            source_label=source_label,
            target_label=target_label,
            relationship_name=relationship_name,
            description=description,
            properties=(
                "firstseen",
                "lastupdated",
                "_sub_resource_label",
                "_sub_resource_id",
            ),
            catalog_path=("cartography.models.bbot.events.BBOT_RELATIONSHIP_CATALOG"),
        )
        for source_label, relationship_name, target_label, description in (
            BBOT_RELATIONSHIP_CATALOG
        )
    )
    definitions.extend(
        RelationshipCatalogDefinition(
            module="gcp",
            source_label="GCPPolicyBinding",
            target_label=target_label,
            relationship_name="APPLIES_TO",
            description=(
                "Connects a GCP IAM policy binding to the concrete resource "
                "where the policy applies."
            ),
            properties=(
                "firstseen",
                "lastupdated",
                "_sub_resource_label",
                "_sub_resource_id",
            ),
            catalog_path=(
                "cartography.models.gcp.resource_catalog."
                "GCP_POLICY_BINDING_TARGET_LABELS"
            ),
        )
        for target_label in GCP_POLICY_BINDING_TARGET_LABELS
    )
    definitions.extend(
        RelationshipCatalogDefinition(
            module="github",
            source_label="GitHubUser",
            target_label="GitHubRepository",
            relationship_name=rel_label,
            description=(
                f"Grants `{permission}` permission on the repository to a "
                f"collaborator with `{affiliation}` affiliation."
            ),
            properties=("firstseen", "lastupdated"),
            catalog_path=(
                "cartography.models.github.repos.GITHUB_COLLABORATOR_REL_LABELS"
            ),
        )
        for affiliation, permission, rel_label in GITHUB_COLLABORATOR_REL_LABELS
    )
    # Several catalog entries can describe the same edge: AWS lists application and
    # network load balancers separately though both are AWSLoadBalancerV2 nodes.
    deduplicated = {
        (
            definition.module,
            definition.source_label,
            definition.relationship_name,
            definition.target_label,
        ): definition
        for definition in definitions
    }
    yield from (deduplicated[key] for key in sorted(deduplicated))


def inspect_data_model(
    package: ModuleType = cartography.models,
) -> DataModel:
    """Discover model classes and build a normalized runtime graph view."""
    analysis_jobs = iter_analysis_jobs()
    permission_relationships = iter_permission_relationships()
    catalog_relationships = iter_relationship_catalog()
    if package is not cartography.models:
        module = _model_package_name(package)
        analysis_jobs = (
            definition for definition in analysis_jobs if definition.module == module
        )
        permission_relationships = (
            definition
            for definition in permission_relationships
            if definition.provider == module
        )
        catalog_relationships = (
            definition
            for definition in catalog_relationships
            if definition.module == module
        )
    return build_data_model(
        iter_model_classes(package),
        analysis_jobs,
        permission_relationships,
        catalog_relationships,
    )


def build_data_model(
    model_classes: Iterable[ModelClass],
    analysis_jobs: Iterable[AnalysisJobDefinition] = (),
    permission_relationships: Iterable[PermissionRelationshipDefinition] = (),
    catalog_relationships: Iterable[RelationshipCatalogDefinition] = (),
) -> DataModel:
    """Build a data model from discovered classes without duplicating declarations."""
    node_entries: dict[str, _NodeAccumulator] = {}
    relationship_entries: dict[RelationshipKey, _RelationshipAccumulator] = {}
    diagnostics: list[str] = []

    classes = sorted(
        set(model_classes),
        key=lambda model_class: (
            model_class.__module__,
            model_class.__qualname__,
        ),
    )
    relationship_classes: list[type[CartographyRelSchema]] = []

    for model_class in classes:
        if _is_runtime_template(model_class):
            continue
        if inspect.isabstract(model_class):
            continue
        if CartographyNodeSchema in model_class.__mro__:
            node_class = cast(type[CartographyNodeSchema], model_class)
            node_schema = _instantiate(node_class, diagnostics)
            if node_schema is not None:
                _add_node_schema(node_entries, relationship_entries, node_schema)
        elif CartographyRelSchema in model_class.__mro__:
            relationship_classes.append(cast(type[CartographyRelSchema], model_class))

    for relationship_class in relationship_classes:
        relationship_schema = _instantiate(relationship_class, diagnostics)
        if relationship_schema is None or not relationship_schema.source_node_label:
            continue
        _add_relationship(
            relationship_entries,
            relationship_schema.source_node_label,
            relationship_schema,
            origin="matchlink",
        )

    _add_ontology_properties(node_entries)
    analysis_job_definitions = tuple(
        sorted(analysis_jobs, key=lambda definition: definition.qualified_name)
    )
    _add_analysis_jobs(
        node_entries,
        relationship_entries,
        analysis_job_definitions,
        diagnostics,
    )
    permission_relationship_definitions = tuple(
        sorted(
            permission_relationships,
            key=lambda definition: (
                definition.provider,
                definition.source_label,
                definition.relationship_name,
                definition.target_label,
            ),
        )
    )
    _add_permission_relationships(
        relationship_entries,
        permission_relationship_definitions,
    )
    catalog_relationship_definitions = tuple(
        sorted(
            catalog_relationships,
            key=lambda definition: (
                definition.module,
                definition.source_label,
                definition.relationship_name,
                definition.target_label,
            ),
        )
    )
    _add_catalog_relationships(
        relationship_entries,
        catalog_relationship_definitions,
    )

    nodes = tuple(
        _build_node(label, entry) for label, entry in sorted(node_entries.items())
    )
    relationships = tuple(
        _build_relationship(key, entry)
        for key, entry in sorted(
            relationship_entries.items(),
            key=lambda item: _relationship_sort_key(item[0]),
        )
    )
    ontology_semantic_labels = _build_ontology_semantic_labels(nodes)
    ontology_relationship_constraints = tuple(
        OntologyRelationshipConstraint(
            source_label=constraint.src,
            label=constraint.label,
            target_label=constraint.dst,
        )
        for constraint in ONTOLOGY_REL_CONSTRAINTS
    )
    ontology_expected_edges = _build_ontology_expected_edges(
        relationships,
        ontology_semantic_labels,
        nodes,
        ontology_relationship_constraints,
    )
    return DataModel(
        nodes=nodes,
        relationships=relationships,
        analysis_jobs=analysis_job_definitions,
        permission_relationships=permission_relationship_definitions,
        catalog_relationships=catalog_relationship_definitions,
        ontology_semantic_labels=ontology_semantic_labels,
        ontology_relationship_constraints=ontology_relationship_constraints,
        ontology_expected_edges=ontology_expected_edges,
        diagnostics=tuple(sorted(diagnostics)),
    )


def _build_ontology_expected_edges(
    relationships: tuple[Relationship, ...],
    ontology_semantic_labels: tuple[OntologySemanticLabel, ...],
    nodes: tuple[Node, ...],
    ontology_relationship_constraints: tuple[OntologyRelationshipConstraint, ...],
) -> tuple[OntologyExpectedEdge, ...]:
    """Collect relationships whose both endpoints are ontology labels."""
    ontology_labels = {
        *(semantic.label for semantic in ontology_semantic_labels),
        *(node.label for node in nodes if "ontology" in node.modules),
    }
    constrained_keys = {
        (constraint.source_label, constraint.label, constraint.target_label)
        for constraint in ontology_relationship_constraints
    }
    expected: list[OntologyExpectedEdge] = []
    for relationship in relationships:
        if relationship.source_label not in ontology_labels:
            continue
        if relationship.target_label not in ontology_labels:
            continue
        key = (
            relationship.source_label,
            relationship.label,
            relationship.target_label,
        )
        expected.append(
            OntologyExpectedEdge(
                source_label=relationship.source_label,
                label=relationship.label,
                target_label=relationship.target_label,
                direction=relationship.direction,
                origins=relationship.origins,
                # RelConstraints describe outward edges only; an undirected
                # materialized relationship does not satisfy them.
                constrained=(
                    key in constrained_keys
                    and relationship.direction is LinkDirection.OUTWARD
                ),
                analysis_jobs=relationship.analysis_jobs,
            )
        )
    return tuple(
        sorted(
            expected,
            key=lambda edge: (
                edge.source_label,
                edge.label,
                edge.target_label,
                edge.direction.name if edge.direction else "",
            ),
        )
    )


def _instantiate(
    model_class: type[_Schema],
    diagnostics: list[str],
) -> _Schema | None:
    try:
        return model_class()
    except (TypeError, ValueError) as error:
        qualified_name = f"{model_class.__module__}.{model_class.__qualname__}"
        diagnostics.append(f"Could not instantiate {qualified_name}: {error}")
        return None


@dataclass
class _NodeAccumulator:
    """Mutable tally of every schema contributing to one node label."""

    descriptions: set[str] = field(default_factory=set)
    extra_labels: set[str] = field(default_factory=set)
    schema_extra_labels: list[set[str]] = field(default_factory=list)
    label_provenance: list[NodeLabelProvenance] = field(default_factory=list)
    label_definitions: list[ExtraNodeLabel] = field(default_factory=list)
    conditional_labels: list[ExtraNodeLabel] = field(default_factory=list)
    ontology_labels: set[str] = field(default_factory=set)
    ontology_projections: set[str] = field(default_factory=set)
    properties: dict[str, _PropertyAccumulator] = field(default_factory=dict)
    modules: set[str] = field(default_factory=set)
    schemas: list[CartographyNodeSchema] = field(default_factory=list)


@dataclass
class _RelationshipAccumulator:
    """Mutable tally of every declaration contributing to one relationship."""

    descriptions: set[str] = field(default_factory=set)
    properties: dict[str, _PropertyAccumulator] = field(default_factory=dict)
    modules: set[str] = field(default_factory=set)
    origins: set[str] = field(default_factory=set)
    schemas: list[CartographyRelSchema] = field(default_factory=list)
    analysis_jobs: dict[str, AnalysisJobDefinition] = field(default_factory=dict)
    permission_relationships: dict[str, PermissionRelationshipDefinition] = field(
        default_factory=dict
    )
    catalog_relationships: dict[str, RelationshipCatalogDefinition] = field(
        default_factory=dict
    )


@dataclass
class _PropertyAccumulator:
    """Mutable tally of every declaration contributing to one graph property."""

    source_names: set[str] = field(default_factory=set)
    descriptions: set[str] = field(default_factory=set)
    indexed: bool = False
    ontology: bool = False
    generated_by: set[str] = field(default_factory=set)
    owner_modules: set[str] = field(default_factory=set)
    analysis_jobs: dict[str, AnalysisJobDefinition] = field(default_factory=dict)
    provenance: list[PropertyProvenance] = field(default_factory=list)


def _add_node_schema(
    node_entries: dict[str, _NodeAccumulator],
    relationship_entries: dict[RelationshipKey, _RelationshipAccumulator],
    schema: CartographyNodeSchema,
) -> None:
    entry = node_entries.setdefault(schema.label, _NodeAccumulator())
    entry.schemas.append(schema)
    entry.modules.add(_module_name(type(schema)))
    description = _class_description(type(schema))
    if description:
        entry.descriptions.add(description)

    extra_labels = schema.extra_node_labels
    schema_extra_labels: set[str] = set()
    schema_conditional_labels: list[ExtraNodeLabel] = []
    schema_label_definitions: tuple[ExtraNodeLabel, ...] = ()
    if isinstance(extra_labels, ExtraNodeLabels):
        schema_label_definitions = extra_labels.labels
        for label in extra_labels.labels:
            entry.label_definitions.append(label)
            if label.kind is LabelKind.ONTOLOGY:
                entry.ontology_labels.add(label.label)
            if label.conditions:
                entry.conditional_labels.append(label)
                schema_conditional_labels.append(label)
            else:
                entry.extra_labels.add(label.label)
                schema_extra_labels.add(label.label)
    entry.schema_extra_labels.append(schema_extra_labels)
    entry.label_provenance.append(
        NodeLabelProvenance(
            module=_module_name(type(schema)),
            schema=f"{type(schema).__module__}.{type(schema).__qualname__}",
            description=description,
            extra_labels=tuple(sorted(schema_extra_labels)),
            conditional_labels=tuple(schema_conditional_labels),
            label_definitions=schema_label_definitions,
        )
    )

    properties = entry.properties
    _add_properties(properties, schema.properties, _module_name(type(schema)))
    _add_generated_property(properties, "firstseen", "querybuilder")

    if schema.sub_resource_relationship is not None:
        _add_relationship(
            relationship_entries,
            schema.label,
            schema.sub_resource_relationship,
            origin="sub_resource",
        )
    if isinstance(schema.other_relationships, OtherRelationships):
        for relationship in schema.other_relationships.rels:
            _add_relationship(
                relationship_entries,
                schema.label,
                relationship,
                origin="node_schema",
            )


def _add_relationship(
    relationship_entries: dict[RelationshipKey, _RelationshipAccumulator],
    owner_label: str,
    schema: CartographyRelSchema,
    origin: str,
) -> None:
    if _is_runtime_template(type(schema)):
        return
    source_label, target_label = _directed_labels(owner_label, schema)
    key = (source_label, schema.rel_label, target_label, LinkDirection.OUTWARD)
    entry = relationship_entries.setdefault(key, _RelationshipAccumulator())
    entry.schemas.append(schema)
    entry.modules.add(_module_name(type(schema)))
    entry.origins.add(origin)
    description = _class_description(type(schema))
    if description:
        entry.descriptions.add(description)
    properties = entry.properties
    _add_properties(properties, schema.properties, _module_name(type(schema)))
    _add_generated_property(properties, "firstseen", "querybuilder")


def _directed_labels(
    owner_label: str,
    schema: CartographyRelSchema,
) -> tuple[str, str]:
    if schema.direction == LinkDirection.OUTWARD:
        return owner_label, schema.target_node_label
    return schema.target_node_label, owner_label


def _add_properties(
    entries: dict[str, _PropertyAccumulator],
    properties: CartographyNodeProperties | CartographyRelProperties,
    generated_by: str,
) -> None:
    for dataclass_field in dataclass_fields(properties):
        property_ref = getattr(properties, dataclass_field.name)
        entry = entries.setdefault(dataclass_field.name, _PropertyAccumulator())
        entry.source_names.add(property_ref.name)
        if property_ref.description:
            entry.descriptions.add(property_ref.description)
        entry.indexed = bool(
            entry.indexed
            or dataclass_field.name in {"id", "lastupdated"}
            or property_ref.extra_index
        )
        entry.generated_by.add(generated_by)
        entry.provenance.append(
            PropertyProvenance(
                module=generated_by,
                source_name=property_ref.name,
                description=property_ref.description,
                indexed=(
                    dataclass_field.name in {"id", "lastupdated"}
                    or property_ref.extra_index
                ),
                property_ref=property_ref,
            )
        )


def _add_generated_property(
    entries: dict[str, _PropertyAccumulator],
    name: str,
    generated_by: str,
    indexed: bool = False,
    ontology: bool = False,
    analysis_job: AnalysisJobDefinition | None = None,
    source_name: str | None = None,
    description: str | None = None,
    owner_module: str | None = None,
) -> None:
    entry = entries.setdefault(name, _PropertyAccumulator())
    if source_name:
        entry.source_names.add(source_name)
    if description:
        entry.descriptions.add(description)
    entry.indexed = bool(entry.indexed or indexed)
    entry.ontology = bool(entry.ontology or ontology)
    entry.generated_by.add(generated_by)
    if owner_module:
        entry.owner_modules.add(owner_module)
    if analysis_job:
        entry.analysis_jobs[analysis_job.qualified_name] = analysis_job


def _add_ontology_properties(
    node_entries: dict[str, _NodeAccumulator],
) -> None:
    for mapping_group, mappings_by_module in SEMANTIC_LABELS_MAPPING.items():
        for ontology_mapping in mappings_by_module.values():
            for node_mapping in ontology_mapping.nodes:
                node_entry = node_entries.get(node_mapping.node_label)
                if node_entry is None:
                    continue
                node_entry.ontology_labels.update(
                    _ontology_labels_for_mapping_group(mapping_group, node_entry)
                )
                properties = node_entry.properties
                _add_generated_property(
                    properties,
                    "_ont_source",
                    "ontology",
                    ontology=True,
                    description=_ONT_SOURCE_DESCRIPTION,
                    owner_module=ontology_mapping.module_name,
                )
                for field_mapping in node_mapping.fields:
                    _add_generated_property(
                        properties,
                        f"_ont_{field_mapping.ontology_field}",
                        "ontology",
                        indexed=field_mapping.indexed,
                        ontology=True,
                        source_name=field_mapping.node_field,
                        owner_module=ontology_mapping.module_name,
                    )

    for mapping_group, mappings_by_module in ONTOLOGY_NODES_MAPPING.items():
        ontology_model = ONTOLOGY_MODELS[mapping_group]
        if ontology_model is None:
            continue
        projection_label = ontology_model().label
        for ontology_mapping in mappings_by_module.values():
            for node_mapping in ontology_mapping.nodes:
                if not node_mapping.eligible_for_source:
                    continue
                for node_label, node_entry in node_entries.items():
                    is_primary_label = node_label == node_mapping.node_label
                    additional_labels = {
                        *node_entry.extra_labels,
                        *(label.label for label in node_entry.conditional_labels),
                    }
                    is_module_additional_label = (
                        ontology_mapping.module_name in node_entry.modules
                        and node_mapping.node_label in additional_labels
                    )
                    if is_primary_label or is_module_additional_label:
                        node_entry.ontology_projections.add(projection_label)

    for node_entry in node_entries.values():
        declared_labels = {
            *node_entry.extra_labels,
            *(label.label for label in node_entry.conditional_labels),
        }
        node_entry.ontology_labels.update(
            declared_labels.intersection(SEMANTIC_LABELS_WITHOUT_NORMALIZED_FIELDS)
        )


def _ontology_labels_for_mapping_group(
    mapping_group: str,
    node_entry: _NodeAccumulator,
) -> set[str]:
    """Identify the ontology label already declared by a mapped node schema."""
    expected_label = SEMANTIC_LABEL_BY_CATEGORY[mapping_group].label
    labels = {
        *node_entry.extra_labels,
        *(label.label for label in node_entry.conditional_labels),
    }
    return {expected_label} if expected_label in labels else set()


def _build_ontology_semantic_labels(
    nodes: tuple[Node, ...],
) -> tuple[OntologySemanticLabel, ...]:
    """Aggregate semantic labels and normalized fields across provider mappings."""
    nodes_by_label: dict[str, set[str]] = {}
    descriptions_by_label: dict[str, set[str]] = {}
    for node in nodes:
        for definition in node.label_definitions:
            if definition.kind is LabelKind.ONTOLOGY:
                descriptions_by_label.setdefault(definition.label, set()).add(
                    definition.description
                )
        for label in (
            # A node whose primary label is the semantic label carries it too, which is
            # how the canonical ontology nodes (CVE, Package, ...) list themselves.
            node.label,
            *node.extra_labels,
            *node.ontology_labels,
            *(conditional.label for conditional in node.conditional_labels),
        ):
            nodes_by_label.setdefault(label, set()).add(node.label)

    semantic_labels: list[OntologySemanticLabel] = []
    for mapping_group, extra_label in sorted(SEMANTIC_LABEL_BY_CATEGORY.items()):
        label = extra_label.label
        property_entries: dict[str, _PropertyAccumulator] = {}
        _add_generated_property(
            property_entries,
            "_ont_source",
            "ontology",
            ontology=True,
            description=_ONT_SOURCE_DESCRIPTION,
        )
        # Being mapped into a group is not proof of carrying its semantic label: only
        # the labels a node declares are. Legacy modules that set labels in raw Cypher
        # instead of declaring a node schema are therefore absent here, and document
        # their ontology labels on their hand-written schema page.
        concrete_node_labels = set(nodes_by_label.get(label, set()))
        for ontology_mapping in SEMANTIC_LABELS_MAPPING[mapping_group].values():
            for node_mapping in ontology_mapping.nodes:
                for field_mapping in node_mapping.fields:
                    property_name = f"_ont_{field_mapping.ontology_field}"
                    readable_name = field_mapping.ontology_field.replace("_", " ")
                    _add_generated_property(
                        property_entries,
                        property_name,
                        "ontology",
                        indexed=field_mapping.indexed,
                        ontology=True,
                        description=(
                            f"Normalized {readable_name} for nodes carrying `{label}`."
                        ),
                    )
        semantic_labels.append(
            OntologySemanticLabel(
                label=label,
                mapping_group=mapping_group,
                descriptions=tuple(sorted(descriptions_by_label.get(label, set()))),
                properties=tuple(
                    _build_property(name, entry)
                    for name, entry in sorted(property_entries.items())
                ),
                concrete_node_labels=tuple(sorted(concrete_node_labels)),
            )
        )

    for label in SEMANTIC_LABELS_WITHOUT_NORMALIZED_FIELDS:
        semantic_labels.append(
            OntologySemanticLabel(
                label=label,
                mapping_group=None,
                descriptions=tuple(sorted(descriptions_by_label.get(label, set()))),
                properties=(),
                concrete_node_labels=tuple(sorted(nodes_by_label.get(label, set()))),
            )
        )
    return tuple(
        sorted(semantic_labels, key=lambda semantic_label: semantic_label.label)
    )


def _add_permission_relationships(
    relationship_entries: dict[RelationshipKey, _RelationshipAccumulator],
    definitions: tuple[PermissionRelationshipDefinition, ...],
) -> None:
    provider_properties = {
        "aws": ("lastupdated", "has_condition", "condition_keys", "conditions"),
        "gcp": (
            "firstseen",
            "lastupdated",
            "has_condition",
            "condition_title",
            "condition_expression",
        ),
        "azure": ("firstseen", "lastupdated"),
    }
    property_descriptions = {
        "has_condition": "Whether an IAM condition restricts this permission.",
        "condition_keys": "IAM condition context keys used by the permission.",
        "conditions": "IAM conditions that restrict this permission.",
        "condition_title": "Title of the IAM condition that restricts this permission.",
        "condition_expression": (
            "CEL expression that must be satisfied for this permission."
        ),
    }
    for definition in definitions:
        key = (
            definition.source_label,
            definition.relationship_name,
            definition.target_label,
            LinkDirection.OUTWARD,
        )
        entry = relationship_entries.setdefault(key, _RelationshipAccumulator())
        entry.modules.add(definition.provider)
        entry.origins.add("permission_evaluation")
        entry.descriptions.add(
            f"`{definition.source_label}` receives evaluated "
            f"`{definition.relationship_name}` access to "
            f"`{definition.target_label}` from "
            f"{definition.provider.upper()} IAM policies."
        )
        definition_key = (
            f"{definition.provider}:{definition.source_label}:"
            f"{definition.relationship_name}:{definition.target_label}"
        )
        entry.permission_relationships[definition_key] = definition
        for property_name in provider_properties[definition.provider]:
            _add_generated_property(
                entry.properties,
                property_name,
                f"permission_evaluation:{definition.provider}",
                description=property_descriptions.get(property_name),
            )


def _add_catalog_relationships(
    relationship_entries: dict[RelationshipKey, _RelationshipAccumulator],
    definitions: tuple[RelationshipCatalogDefinition, ...],
) -> None:
    for definition in definitions:
        key = (
            definition.source_label,
            definition.relationship_name,
            definition.target_label,
            LinkDirection.OUTWARD,
        )
        entry = relationship_entries.setdefault(key, _RelationshipAccumulator())
        entry.modules.add(definition.module)
        entry.origins.add("runtime_catalog")
        entry.descriptions.add(definition.description)
        definition_key = (
            f"{definition.module}:{definition.source_label}:"
            f"{definition.relationship_name}:{definition.target_label}"
        )
        entry.catalog_relationships[definition_key] = definition
        for property_name in definition.properties:
            _add_generated_property(
                entry.properties,
                property_name,
                f"runtime_catalog:{definition.module}",
            )


def _add_analysis_jobs(
    node_entries: dict[str, _NodeAccumulator],
    relationship_entries: dict[RelationshipKey, _RelationshipAccumulator],
    analysis_jobs: tuple[AnalysisJobDefinition, ...],
    diagnostics: list[str],
) -> None:
    for definition in analysis_jobs:
        generated_by = f"analysis:{definition.job.short_name or definition.job.name}"
        if any(statement.query for statement in definition.job.statements):
            diagnostics.append(
                f"Analysis job {definition.qualified_name} contains raw Cypher "
                "that cannot be introspected."
            )
        try:
            relationship_effects = relationships_added(definition.job)
            property_effects = properties_set(definition.job)
        except (TypeError, ValueError) as error:
            diagnostics.append(
                f"Could not introspect analysis job {definition.qualified_name}: {error}"
            )
            continue

        for relationship_effect in relationship_effects:
            _add_analysis_relationship(
                node_entries,
                relationship_entries,
                relationship_effect,
                definition,
                generated_by,
                diagnostics,
            )
        for property_effect in property_effects:
            if isinstance(property_effect, PropertyEffect):
                node_entry = node_entries.get(property_effect.node_label)
                if node_entry is None:
                    diagnostics.append(
                        f"Analysis job {definition.qualified_name} sets properties "
                        f"on unknown node {property_effect.node_label}."
                    )
                    continue
                for property_name in property_effect.properties:
                    _add_generated_property(
                        node_entry.properties,
                        property_name,
                        generated_by,
                        analysis_job=definition,
                    )
            else:
                _add_analysis_relationship_properties(
                    relationship_entries,
                    property_effect,
                    definition,
                    generated_by,
                    diagnostics,
                )
        for statement in definition.job.statements:
            for effect in statement.effects:
                if not isinstance(effect, SetRelationshipPropertyIfMissing):
                    continue
                _add_analysis_relationship_properties(
                    relationship_entries,
                    RelationshipPropertyEffect(
                        effect.source_label or "",
                        effect.rel_label or "",
                        (effect.property,),
                        effect.target_label,
                    ),
                    definition,
                    generated_by,
                    diagnostics,
                )


def _add_analysis_relationship(
    node_entries: dict[str, _NodeAccumulator],
    relationship_entries: dict[RelationshipKey, _RelationshipAccumulator],
    effect: RelationshipEffect,
    definition: AnalysisJobDefinition,
    generated_by: str,
    diagnostics: list[str],
) -> None:
    if not effect.source_label or not effect.rel_label or not effect.target_label:
        diagnostics.append(
            f"Analysis job {definition.qualified_name} adds a relationship "
            "without complete labels."
        )
        return
    key = (
        effect.source_label,
        effect.rel_label,
        effect.target_label,
        effect.direction,
    )
    entry = relationship_entries.setdefault(key, _RelationshipAccumulator())
    entry.modules.add(definition.module)
    entry.origins.add("analysis")
    entry.analysis_jobs[definition.qualified_name] = definition
    properties = entry.properties
    for property_name in ("firstseen", "lastupdated", *effect.properties):
        _add_generated_property(
            properties,
            property_name,
            generated_by,
            analysis_job=definition,
        )


def _add_analysis_relationship_properties(
    relationship_entries: dict[RelationshipKey, _RelationshipAccumulator],
    effect: RelationshipPropertyEffect,
    definition: AnalysisJobDefinition,
    generated_by: str,
    diagnostics: list[str],
) -> None:
    def endpoints_match(near: str, far: str) -> bool:
        return near == effect.source_label and (
            effect.target_label is None or far == effect.target_label
        )

    matching_entries = []
    for (
        source_label,
        rel_label,
        target_label,
        direction,
    ), entry in relationship_entries.items():
        if rel_label != effect.rel_label:
            continue
        if direction is None:
            # An undirected edge has no orientation, so either reading can match.
            labels_match = endpoints_match(
                source_label, target_label
            ) or endpoints_match(target_label, source_label)
        elif effect.direction == LinkDirection.OUTWARD:
            labels_match = endpoints_match(source_label, target_label)
        else:
            labels_match = endpoints_match(target_label, source_label)
        if labels_match:
            matching_entries.append(entry)
    if not matching_entries:
        diagnostics.append(
            f"Analysis job {definition.qualified_name} sets properties on unknown "
            f"relationship {effect.source_label}-[:{effect.rel_label}]->"
            f"{effect.target_label or '*'}."
        )
        return
    for entry in matching_entries:
        entry.modules.add(definition.module)
        entry.origins.add("analysis")
        entry.analysis_jobs[definition.qualified_name] = definition
        for property_name in effect.properties:
            _add_generated_property(
                entry.properties,
                property_name,
                generated_by,
                analysis_job=definition,
            )


def _build_node(label: str, entry: _NodeAccumulator) -> Node:
    properties = entry.properties
    conditional_labels = {
        (
            conditional.label,
            conditional.conditions,
        ): conditional
        for conditional in entry.conditional_labels
    }
    schema_extra_labels = entry.schema_extra_labels
    universal_extra_labels = (
        set.intersection(*schema_extra_labels) if schema_extra_labels else set()
    )
    partial_extra_labels = entry.extra_labels - universal_extra_labels
    return Node(
        label=label,
        descriptions=tuple(sorted(entry.descriptions)),
        extra_labels=tuple(sorted(entry.extra_labels)),
        conditional_labels=tuple(
            sorted(
                conditional_labels.values(),
                key=lambda conditional: (
                    conditional.label,
                    conditional.conditions,
                ),
            )
        ),
        properties=tuple(
            _build_property(name, property_entry)
            for name, property_entry in sorted(properties.items())
        ),
        modules=tuple(sorted(entry.modules)),
        schemas=tuple(entry.schemas),
        ontology_labels=tuple(sorted(entry.ontology_labels)),
        ontology_projections=tuple(sorted(entry.ontology_projections)),
        partial_extra_labels=tuple(sorted(partial_extra_labels)),
        label_provenance=tuple(
            sorted(
                entry.label_provenance,
                key=lambda provenance: (provenance.module, provenance.schema),
            )
        ),
        label_definitions=tuple(
            sorted(
                set(entry.label_definitions),
                key=lambda definition: (
                    definition.label,
                    definition.conditions,
                    definition.kind.value,
                ),
            )
        ),
    )


def _build_relationship(
    key: RelationshipKey,
    entry: _RelationshipAccumulator,
) -> Relationship:
    source_label, label, target_label, direction = key
    properties = entry.properties
    return Relationship(
        source_label=source_label,
        label=label,
        target_label=target_label,
        direction=direction,
        descriptions=tuple(sorted(entry.descriptions)),
        properties=tuple(
            _build_property(name, property_entry)
            for name, property_entry in sorted(properties.items())
        ),
        modules=tuple(sorted(entry.modules)),
        origins=tuple(sorted(entry.origins)),
        schemas=tuple(entry.schemas),
        analysis_jobs=tuple(
            entry.analysis_jobs[name] for name in sorted(entry.analysis_jobs)
        ),
        permission_relationships=tuple(
            entry.permission_relationships[name]
            for name in sorted(entry.permission_relationships)
        ),
        catalog_relationships=tuple(
            entry.catalog_relationships[name]
            for name in sorted(entry.catalog_relationships)
        ),
    )


def _build_property(name: str, entry: _PropertyAccumulator) -> Property:
    return Property(
        name=name,
        source_names=tuple(sorted(entry.source_names)),
        descriptions=tuple(sorted(entry.descriptions)),
        indexed=bool(entry.indexed),
        ontology=bool(entry.ontology),
        generated_by=tuple(sorted(entry.generated_by)),
        owner_modules=tuple(sorted(entry.owner_modules)),
        analysis_jobs=tuple(
            entry.analysis_jobs[name] for name in sorted(entry.analysis_jobs)
        ),
        provenance=tuple(entry.provenance),
    )


def _class_description(model_class: type) -> str | None:
    docstring = model_class.__dict__.get("__doc__")
    if not docstring:
        return None
    cleaned = inspect.cleandoc(docstring)
    if cleaned.startswith(f"{model_class.__name__}("):
        return None
    return cleaned


def _module_name(model_class: type) -> str:
    parts = model_class.__module__.split(".")
    if len(parts) > 2 and parts[:2] == ["cartography", "models"]:
        return parts[2]
    return model_class.__module__


def _model_package_name(package: ModuleType) -> str:
    parts = package.__name__.split(".")
    if len(parts) > 2 and parts[:2] == ["cartography", "models"]:
        return parts[2]
    return package.__name__


def _analysis_module_name(module_name: str) -> str:
    parts = module_name.split(".")
    if len(parts) > 2 and parts[:2] == ["cartography", "analysis"]:
        return parts[2]
    return module_name


def _relationship_sort_key(key: RelationshipKey) -> tuple[str, str, str, str]:
    source_label, label, target_label, direction = key
    return source_label, label, target_label, direction.name if direction else ""
