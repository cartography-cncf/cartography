from __future__ import annotations

import importlib
import inspect
from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass
from dataclasses import fields as dataclass_fields
from pkgutil import walk_packages
from types import ModuleType
from typing import Any
from typing import TypeVar

import cartography.models
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

    def get_property(self, name: str) -> Property | None:
        return next((prop for prop in self.properties if prop.name == name), None)


@dataclass(frozen=True)
class Relationship:
    """A directed graph relationship computed from attached rels or MatchLinks."""

    source_label: str
    label: str
    target_label: str
    descriptions: tuple[str, ...]
    properties: tuple[Property, ...]
    modules: tuple[str, ...]
    origins: tuple[str, ...]
    schemas: tuple[CartographyRelSchema, ...]


@dataclass(frozen=True)
class DataModel:
    """Runtime view of Cartography's complete declarative graph model."""

    nodes: tuple[Node, ...]
    relationships: tuple[Relationship, ...]
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
            if not issubclass(value, _MODEL_BASE_CLASSES):
                continue
            qualified_name = f"{value.__module__}.{value.__qualname__}"
            discovered[qualified_name] = value

    for qualified_name in sorted(discovered):
        yield discovered[qualified_name]


def inspect_data_model(
    package: ModuleType = cartography.models,
) -> DataModel:
    """Discover model classes and build a normalized runtime graph view."""
    return build_data_model(iter_model_classes(package))


def build_data_model(model_classes: Iterable[ModelClass]) -> DataModel:
    """Build a data model from discovered classes without duplicating declarations."""
    node_entries: dict[str, dict[str, Any]] = {}
    relationship_entries: dict[tuple[str, str, str], dict[str, Any]] = {}
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
        if issubclass(model_class, CartographyNodeSchema):
            node_schema = _instantiate(model_class, diagnostics)
            if node_schema is not None:
                _add_node_schema(node_entries, relationship_entries, node_schema)
        elif issubclass(model_class, CartographyRelSchema):
            relationship_classes.append(model_class)

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

    nodes = tuple(
        _build_node(label, entry) for label, entry in sorted(node_entries.items())
    )
    relationships = tuple(
        _build_relationship(key, entry)
        for key, entry in sorted(relationship_entries.items())
    )
    return DataModel(
        nodes=nodes,
        relationships=relationships,
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
    }


def _add_node_schema(
    node_entries: dict[str, dict[str, Any]],
    relationship_entries: dict[tuple[str, str, str], dict[str, Any]],
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
    relationship_entries: dict[tuple[str, str, str], dict[str, Any]],
    owner_label: str,
    schema: CartographyRelSchema,
    origin: str,
) -> None:
    source_label, target_label = _directed_labels(owner_label, schema)
    key = (source_label, schema.rel_label, target_label)
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
) -> None:
    entry = entries.setdefault(name, _new_property_entry())
    entry["indexed"] = bool(entry["indexed"] or indexed)
    entry["ontology"] = bool(entry["ontology"] or ontology)
    entry["generated_by"].add(generated_by)


def _add_ontology_properties(
    node_entries: dict[str, dict[str, Any]],
) -> None:
    for mapping_groups in (
        ONTOLOGY_NODES_MAPPING,
        SEMANTIC_LABELS_MAPPING,
    ):
        for mappings_by_module in mapping_groups.values():
            for ontology_mapping in mappings_by_module.values():
                for node_mapping in ontology_mapping.nodes:
                    node_entry = node_entries.get(node_mapping.node_label)
                    if node_entry is None:
                        continue
                    properties = node_entry["properties"]
                    for field_mapping in node_mapping.fields:
                        _add_generated_property(
                            properties,
                            f"_ont_{field_mapping.ontology_field}",
                            "ontology",
                            indexed=field_mapping.indexed,
                            ontology=True,
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
    )


def _build_relationship(
    key: tuple[str, str, str],
    entry: dict[str, Any],
) -> Relationship:
    source_label, label, target_label = key
    properties = entry["properties"]
    return Relationship(
        source_label=source_label,
        label=label,
        target_label=target_label,
        descriptions=tuple(sorted(entry["descriptions"])),
        properties=tuple(
            _build_property(name, property_entry)
            for name, property_entry in sorted(properties.items())
        ),
        modules=tuple(sorted(entry["modules"])),
        origins=tuple(sorted(entry["origins"])),
        schemas=tuple(entry["schemas"]),
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
