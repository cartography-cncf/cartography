from __future__ import annotations

import importlib
import inspect
from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass
from dataclasses import fields as dataclass_fields
from pathlib import Path
from pkgutil import walk_packages
from types import ModuleType
from typing import Any
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
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import OtherRelationships
from cartography.models.ontology.mapping import ONTOLOGY_NODES_MAPPING
from cartography.models.ontology.mapping import SEMANTIC_LABELS_MAPPING

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
Schema = TypeVar("Schema", CartographyNodeSchema, CartographyRelSchema)
RelationshipKey = tuple[str, str, str, LinkDirection | None]
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
class PermissionRelationshipDefinition:
    """A relationship generated from a provider permission evaluation file."""

    provider: str
    source_label: str
    target_label: str
    relationship_name: str
    permissions: tuple[str, ...]
    config_path: str


@dataclass(frozen=True)
class Property:
    """A graph property computed from one or more data-model declarations."""

    name: str
    source_names: tuple[str, ...]
    descriptions: tuple[str, ...]
    indexed: bool
    ontology: bool
    generated_by: tuple[str, ...]
    property_refs: tuple[PropertyRef, ...]
    analysis_jobs: tuple[AnalysisJobDefinition, ...]


@dataclass(frozen=True)
class Node:
    """A graph node computed from every schema contributing to one label."""

    label: str
    descriptions: tuple[str, ...]
    extra_labels: tuple[str, ...]
    conditional_labels: tuple[ConditionalNodeLabel, ...]
    properties: tuple[Property, ...]
    modules: tuple[str, ...]
    schemas: tuple[CartographyNodeSchema, ...]
    ontology_labels: tuple[str, ...] = ()

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


@dataclass(frozen=True)
class DataModel:
    """Runtime view of Cartography's complete declarative graph model."""

    nodes: tuple[Node, ...]
    relationships: tuple[Relationship, ...]
    analysis_jobs: tuple[AnalysisJobDefinition, ...] = ()
    permission_relationships: tuple[PermissionRelationshipDefinition, ...] = ()
    diagnostics: tuple[str, ...] = ()

    def get_node(self, label: str) -> Node | None:
        return next((node for node in self.nodes if node.label == label), None)

    def for_module(self, module: str) -> DataModel:
        return DataModel(
            nodes=tuple(node for node in self.nodes if module in node.modules),
            relationships=tuple(
                relationship
                for relationship in self.relationships
                if module in relationship.modules
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
            diagnostics=self.diagnostics,
        )


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


def inspect_data_model(
    package: ModuleType = cartography.models,
) -> DataModel:
    """Discover model classes and build a normalized runtime graph view."""
    analysis_jobs = iter_analysis_jobs()
    permission_relationships = iter_permission_relationships()
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
    return build_data_model(
        iter_model_classes(package),
        analysis_jobs,
        permission_relationships,
    )


def build_data_model(
    model_classes: Iterable[ModelClass],
    analysis_jobs: Iterable[AnalysisJobDefinition] = (),
    permission_relationships: Iterable[PermissionRelationshipDefinition] = (),
) -> DataModel:
    """Build a data model from discovered classes without duplicating declarations."""
    node_entries: dict[str, dict[str, Any]] = {}
    relationship_entries: dict[RelationshipKey, dict[str, Any]] = {}
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
    return DataModel(
        nodes=nodes,
        relationships=relationships,
        analysis_jobs=analysis_job_definitions,
        permission_relationships=permission_relationship_definitions,
        diagnostics=tuple(sorted(diagnostics)),
    )


def _instantiate(
    model_class: type[Schema],
    diagnostics: list[str],
) -> Schema | None:
    try:
        return model_class()
    except (TypeError, ValueError) as error:
        qualified_name = f"{model_class.__module__}.{model_class.__qualname__}"
        diagnostics.append(f"Could not instantiate {qualified_name}: {error}")
        return None


def _new_node_entry() -> dict[str, Any]:
    return {
        "descriptions": set(),
        "extra_labels": set(),
        "conditional_labels": [],
        "ontology_labels": set(),
        "properties": {},
        "modules": set(),
        "schemas": [],
    }


def _new_relationship_entry() -> dict[str, Any]:
    return {
        "descriptions": set(),
        "properties": {},
        "modules": set(),
        "origins": set(),
        "schemas": [],
        "analysis_jobs": {},
        "permission_relationships": {},
    }


def _add_node_schema(
    node_entries: dict[str, dict[str, Any]],
    relationship_entries: dict[RelationshipKey, dict[str, Any]],
    schema: CartographyNodeSchema,
) -> None:
    entry = node_entries.setdefault(schema.label, _new_node_entry())
    entry["schemas"].append(schema)
    entry["modules"].add(_module_name(type(schema)))
    description = _class_description(type(schema))
    if description:
        entry["descriptions"].add(description)

    extra_labels = schema.extra_node_labels
    if isinstance(extra_labels, ExtraNodeLabels):
        for label in extra_labels.labels:
            if isinstance(label, ConditionalNodeLabel):
                entry["conditional_labels"].append(label)
            else:
                entry["extra_labels"].add(label)

    properties = entry["properties"]
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
    relationship_entries: dict[RelationshipKey, dict[str, Any]],
    owner_label: str,
    schema: CartographyRelSchema,
    origin: str,
) -> None:
    source_label, target_label = _directed_labels(owner_label, schema)
    key = (source_label, schema.rel_label, target_label, LinkDirection.OUTWARD)
    entry = relationship_entries.setdefault(key, _new_relationship_entry())
    entry["schemas"].append(schema)
    entry["modules"].add(_module_name(type(schema)))
    entry["origins"].add(origin)
    description = _class_description(type(schema))
    if description:
        entry["descriptions"].add(description)
    properties = entry["properties"]
    _add_properties(properties, schema.properties, _module_name(type(schema)))
    _add_generated_property(properties, "firstseen", "querybuilder")


def _directed_labels(
    owner_label: str,
    schema: CartographyRelSchema,
) -> tuple[str, str]:
    if schema.direction == LinkDirection.OUTWARD:
        return owner_label, schema.target_node_label
    return schema.target_node_label, owner_label


def _new_property_entry() -> dict[str, Any]:
    return {
        "source_names": set(),
        "descriptions": set(),
        "indexed": False,
        "ontology": False,
        "generated_by": set(),
        "property_refs": [],
        "analysis_jobs": {},
    }


def _add_properties(
    entries: dict[str, dict[str, Any]],
    properties: CartographyNodeProperties | CartographyRelProperties,
    generated_by: str,
) -> None:
    for dataclass_field in dataclass_fields(properties):
        property_ref = getattr(properties, dataclass_field.name)
        entry = entries.setdefault(dataclass_field.name, _new_property_entry())
        entry["source_names"].add(property_ref.name)
        if property_ref.description:
            entry["descriptions"].add(property_ref.description)
        entry["indexed"] = bool(
            entry["indexed"]
            or dataclass_field.name in {"id", "lastupdated"}
            or property_ref.extra_index
        )
        entry["generated_by"].add(generated_by)
        entry["property_refs"].append(property_ref)


def _add_generated_property(
    entries: dict[str, dict[str, Any]],
    name: str,
    generated_by: str,
    indexed: bool = False,
    ontology: bool = False,
    analysis_job: AnalysisJobDefinition | None = None,
    source_name: str | None = None,
) -> None:
    entry = entries.setdefault(name, _new_property_entry())
    if source_name:
        entry["source_names"].add(source_name)
    entry["indexed"] = bool(entry["indexed"] or indexed)
    entry["ontology"] = bool(entry["ontology"] or ontology)
    entry["generated_by"].add(generated_by)
    if analysis_job:
        entry["analysis_jobs"][analysis_job.qualified_name] = analysis_job


def _add_ontology_properties(
    node_entries: dict[str, dict[str, Any]],
) -> None:
    for mapping_groups in (
        ONTOLOGY_NODES_MAPPING,
        SEMANTIC_LABELS_MAPPING,
    ):
        for mapping_group, mappings_by_module in mapping_groups.items():
            for ontology_mapping in mappings_by_module.values():
                for node_mapping in ontology_mapping.nodes:
                    node_entry = node_entries.get(node_mapping.node_label)
                    if node_entry is None:
                        continue
                    node_entry["ontology_labels"].update(
                        _ontology_labels_for_mapping_group(mapping_group, node_entry)
                    )
                    properties = node_entry["properties"]
                    _add_generated_property(
                        properties,
                        "_ont_source",
                        "ontology",
                        ontology=True,
                    )
                    for field_mapping in node_mapping.fields:
                        _add_generated_property(
                            properties,
                            f"_ont_{field_mapping.ontology_field}",
                            "ontology",
                            indexed=field_mapping.indexed,
                            ontology=True,
                            source_name=field_mapping.node_field,
                        )


def _ontology_labels_for_mapping_group(
    mapping_group: str,
    node_entry: dict[str, Any],
) -> set[str]:
    """Identify the ontology label already declared by a mapped node schema."""
    singular_group = (
        f"{mapping_group[:-3]}y"
        if mapping_group.endswith("ies")
        else mapping_group[:-1] if mapping_group.endswith("s") else mapping_group
    )
    normalized_candidates = {
        singular_group,
        {
            "device": "deviceinstance",
            "firewall": "networkaccesscontrol",
            "group": "usergroup",
            "role": "permissionrole",
            "user": "useraccount",
            "vpc": "virtualnetwork",
        }.get(singular_group, singular_group),
    }
    labels = {
        *node_entry["extra_labels"],
        *(label.label for label in node_entry["conditional_labels"]),
    }
    return {
        label
        for label in labels
        if label.lower().replace("_", "") in normalized_candidates
    }


def _add_permission_relationships(
    relationship_entries: dict[RelationshipKey, dict[str, Any]],
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
    for definition in definitions:
        key = (
            definition.source_label,
            definition.relationship_name,
            definition.target_label,
            LinkDirection.OUTWARD,
        )
        entry = relationship_entries.setdefault(key, _new_relationship_entry())
        entry["modules"].add(definition.provider)
        entry["origins"].add("permission_evaluation")
        definition_key = (
            f"{definition.provider}:{definition.source_label}:"
            f"{definition.relationship_name}:{definition.target_label}"
        )
        entry["permission_relationships"][definition_key] = definition
        for property_name in provider_properties[definition.provider]:
            _add_generated_property(
                entry["properties"],
                property_name,
                f"permission_evaluation:{definition.provider}",
            )


def _add_analysis_jobs(
    node_entries: dict[str, dict[str, Any]],
    relationship_entries: dict[RelationshipKey, dict[str, Any]],
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
                        node_entry["properties"],
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
    relationship_entries: dict[RelationshipKey, dict[str, Any]],
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
    entry = relationship_entries.setdefault(key, _new_relationship_entry())
    entry["modules"].add(definition.module)
    entry["origins"].add("analysis")
    entry["analysis_jobs"][definition.qualified_name] = definition
    properties = entry["properties"]
    for property_name in ("firstseen", "lastupdated", *effect.properties):
        _add_generated_property(
            properties,
            property_name,
            generated_by,
            analysis_job=definition,
        )


def _add_analysis_relationship_properties(
    relationship_entries: dict[RelationshipKey, dict[str, Any]],
    effect: RelationshipPropertyEffect,
    definition: AnalysisJobDefinition,
    generated_by: str,
    diagnostics: list[str],
) -> None:
    matching_entries = []
    for (
        source_label,
        rel_label,
        target_label,
        direction,
    ), entry in relationship_entries.items():
        if direction is None or rel_label != effect.rel_label:
            continue
        if effect.direction == LinkDirection.OUTWARD:
            labels_match = source_label == effect.source_label and (
                effect.target_label is None or target_label == effect.target_label
            )
        else:
            labels_match = target_label == effect.source_label and (
                effect.target_label is None or source_label == effect.target_label
            )
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
        entry["modules"].add(definition.module)
        entry["origins"].add("analysis")
        entry["analysis_jobs"][definition.qualified_name] = definition
        for property_name in effect.properties:
            _add_generated_property(
                entry["properties"],
                property_name,
                generated_by,
                analysis_job=definition,
            )


def _build_node(label: str, entry: dict[str, Any]) -> Node:
    properties = entry["properties"]
    conditional_labels = {
        (
            conditional.label,
            tuple(sorted(conditional.conditions.items())),
        ): conditional
        for conditional in entry["conditional_labels"]
    }
    return Node(
        label=label,
        descriptions=tuple(sorted(entry["descriptions"])),
        extra_labels=tuple(sorted(entry["extra_labels"])),
        conditional_labels=tuple(
            sorted(
                conditional_labels.values(),
                key=lambda conditional: (
                    conditional.label,
                    tuple(sorted(conditional.conditions.items())),
                ),
            )
        ),
        properties=tuple(
            _build_property(name, property_entry)
            for name, property_entry in sorted(properties.items())
        ),
        modules=tuple(sorted(entry["modules"])),
        schemas=tuple(entry["schemas"]),
        ontology_labels=tuple(sorted(entry["ontology_labels"])),
    )


def _build_relationship(
    key: RelationshipKey,
    entry: dict[str, Any],
) -> Relationship:
    source_label, label, target_label, direction = key
    properties = entry["properties"]
    return Relationship(
        source_label=source_label,
        label=label,
        target_label=target_label,
        direction=direction,
        descriptions=tuple(sorted(entry["descriptions"])),
        properties=tuple(
            _build_property(name, property_entry)
            for name, property_entry in sorted(properties.items())
        ),
        modules=tuple(sorted(entry["modules"])),
        origins=tuple(sorted(entry["origins"])),
        schemas=tuple(entry["schemas"]),
        analysis_jobs=tuple(
            entry["analysis_jobs"][name] for name in sorted(entry["analysis_jobs"])
        ),
        permission_relationships=tuple(
            entry["permission_relationships"][name]
            for name in sorted(entry["permission_relationships"])
        ),
    )


def _build_property(name: str, entry: dict[str, Any]) -> Property:
    return Property(
        name=name,
        source_names=tuple(sorted(entry["source_names"])),
        descriptions=tuple(sorted(entry["descriptions"])),
        indexed=bool(entry["indexed"]),
        ontology=bool(entry["ontology"]),
        generated_by=tuple(sorted(entry["generated_by"])),
        property_refs=tuple(entry["property_refs"]),
        analysis_jobs=tuple(
            entry["analysis_jobs"][name] for name in sorted(entry["analysis_jobs"])
        ),
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
