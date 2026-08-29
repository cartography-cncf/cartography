from __future__ import annotations

import logging
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import LabelKind
from cartography.models.core.relationships import LinkDirection
from cartography.models.introspection import DataModel
from cartography.models.introspection import Node
from cartography.models.introspection import NodeRelationship
from cartography.models.introspection import Property
from cartography.models.introspection import Relationship
from cartography.models.introspection import relationship_touches_node
from cartography.models.introspection import relationships_for_module

logger = logging.getLogger(__name__)

GENERATED_NOTICE = "<!-- Generated from the data model. Do not edit manually. -->"
_STANDARD_RELATIONSHIP_PROPERTIES = frozenset({"firstseen", "lastupdated"})

# Modules with no declarative data model, so their schema page is still hand-written and
# committed. Removing one from this set must be paired with deleting its committed page.
# - _cartography-metadata: written by the sync runner rather than by an intel module.
MANUAL_SCHEMA_MODULES = frozenset(
    {
        "_cartography-metadata",
    }
)

# Deprecated module paths kept as redirect stubs so existing links keep resolving. They
# document no schema of their own and point at the module that superseded them.
REDIRECT_SCHEMA_MODULES = frozenset({"entra"})

# Labels Cartography attaches for its own bookkeeping. They describe no user-facing
# concept and have no section of their own, so they are never rendered.
SYSTEM_LABELS = frozenset({"Ontology"})


def render_module_schema(model: DataModel, module: str) -> str:
    """Render one module's introspected data model as schema Markdown."""
    if module == "ontology":
        return _render_ontology_schema(model)

    module_model = model.for_module(module)
    module_nodes = tuple(sorted(module_model.nodes, key=_node_sort_key))
    if not module_nodes:
        raise ValueError(f'No nodes found for module "{module}".')

    module_relationships = module_model.relationships
    module_node_labels = {node.label for node in module_nodes}
    diagram_relationships = tuple(
        relationship
        for relationship in module_relationships
        if relationship.source_label in module_node_labels
        and relationship.target_label in module_node_labels
    )
    lines = [
        GENERATED_NOTICE,
        "",
        f"## {_module_title(module)} Schema",
        "",
        "```mermaid",
        "graph LR",
    ]
    lines.extend(
        f"    {_mermaid_relationship(relationship)}"
        for relationship in diagram_relationships
    )
    lines.extend(["```", ""])

    for node in module_nodes:
        lines.extend(
            _render_node(node, module_model.relationships_for_node(node.label))
        )

    return "\n".join(lines).rstrip() + "\n"


def _node_sort_key(node: Node) -> tuple[str, str]:
    return node.label.casefold(), node.label


def _render_ontology_schema(model: DataModel) -> str:
    """Render the cross-module ontology catalog."""
    canonical_nodes = tuple(node for node in model.nodes if "ontology" in node.modules)
    semantic_nodes = tuple(
        Node(
            label=semantic_label.label,
            descriptions=semantic_label.descriptions
            or (
                f"`{semantic_label.label}` is a semantic label applied to "
                "provider-specific nodes.",
            ),
            extra_labels=(),
            conditional_labels=(),
            properties=semantic_label.properties,
            modules=("ontology",),
            schemas=(),
        )
        for semantic_label in model.ontology_semantic_labels
    )
    catalog_nodes = canonical_nodes + semantic_nodes
    if not catalog_nodes:
        raise ValueError('No nodes found for module "ontology".')

    relationships = _ontology_catalog_relationships(
        model,
        canonical_nodes,
    )
    assigned_relationships = _assign_relationships(relationships, catalog_nodes)
    implementations_by_label = {
        semantic_label.label: semantic_label.concrete_node_labels
        for semantic_label in model.ontology_semantic_labels
    }
    lines = [
        GENERATED_NOTICE,
        "",
        "## Ontology Schema",
        "",
        "The ontology combines dedicated abstract nodes with semantic labels "
        "applied directly to provider-specific nodes.",
        "",
        "Canonical relationship constraints validate the names and directions "
        "of existing relationships. They do not create relationships and are "
        "not inherited onto concrete node schemas.",
        "",
        "Expected (materialized) ontology edges are relationships actually "
        "produced under ontology labels by models, matchlinks, analysis jobs, "
        "or catalogs. Concrete nodes that carry a semantic endpoint inherit "
        "those edges in their schema view, with the far endpoint kept "
        "semantic.",
        "",
        "```mermaid",
        "graph LR",
    ]
    lines.extend(
        f"    {_mermaid_relationship(relationship)}" for relationship in relationships
    )
    lines.extend(["```", ""])

    canonical_labels = {node.label for node in canonical_nodes}
    for node in sorted(catalog_nodes, key=_node_sort_key):
        ontology_kind = "abstract" if node.label in canonical_labels else "semantic"
        lines.extend(
            _render_node(
                node,
                _node_relationships_for_assigned(
                    node,
                    assigned_relationships.get(node.label, ()),
                ),
                ontology_kind=ontology_kind,
                concrete_node_labels=implementations_by_label.get(node.label, ()),
            )
        )
    return "\n".join(lines).rstrip() + "\n"


@dataclass
class _OntologyCatalogEntry:
    """One canonical edge of the ontology catalog and the edges implementing it."""

    constrained: bool = False
    implementations: list[Relationship] = field(default_factory=list)


def _ontology_catalog_relationships(
    model: DataModel,
    canonical_nodes: tuple[Node, ...],
) -> tuple[Relationship, ...]:
    canonical_labels = {node.label for node in canonical_nodes}
    semantic_labels = {
        semantic_label.label for semantic_label in model.ontology_semantic_labels
    }
    ontology_labels = canonical_labels | semantic_labels
    nodes_by_label = {node.label: node for node in model.nodes}
    entries: dict[
        tuple[str, str, str, LinkDirection | None],
        _OntologyCatalogEntry,
    ] = {}
    key: tuple[str, str, str, LinkDirection | None]

    for constraint in model.ontology_relationship_constraints:
        key = (
            constraint.source_label,
            constraint.label,
            constraint.target_label,
            LinkDirection.OUTWARD,
        )
        entries[key] = _OntologyCatalogEntry(constrained=True)

    # Keyed by identity: a Relationship carrying an analysis job is not hashable,
    # because AnalysisJob holds dict-valued statement parameters.
    represented_relationships: set[int] = set()
    for relationship in model.relationships:
        source_labels = _ontology_endpoint_labels(
            relationship.source_label,
            ontology_labels,
            semantic_labels,
            nodes_by_label,
        )
        target_labels = _ontology_endpoint_labels(
            relationship.target_label,
            ontology_labels,
            semantic_labels,
            nodes_by_label,
        )
        if not source_labels or not target_labels:
            continue
        represented_relationships.add(id(relationship))
        for source_label in source_labels:
            for target_label in target_labels:
                key = (
                    source_label,
                    relationship.label,
                    target_label,
                    relationship.direction,
                )
                entry = entries.setdefault(key, _OntologyCatalogEntry())
                entry.implementations.append(relationship)

    relationships = [
        _build_ontology_catalog_relationship(key, entry)
        for key, entry in entries.items()
    ]
    relationships.extend(
        relationship
        for relationship in relationships_for_module(
            model.relationships,
            canonical_nodes,
            "ontology",
            model.nodes,
        )
        if id(relationship) not in represented_relationships
    )
    return tuple(
        sorted(
            relationships,
            key=lambda relationship: (
                relationship.source_label,
                relationship.label,
                relationship.target_label,
                relationship.direction.name if relationship.direction else "",
            ),
        )
    )


def _ontology_endpoint_labels(
    label: str,
    ontology_labels: set[str],
    semantic_labels: set[str],
    nodes_by_label: dict[str, Node],
) -> tuple[str, ...]:
    if label in ontology_labels:
        return (label,)
    node = nodes_by_label.get(label)
    if node is None:
        return ()
    labels = {
        *node.extra_labels,
        *node.ontology_labels,
        *(conditional.label for conditional in node.conditional_labels),
    }
    return tuple(sorted(labels & semantic_labels))


def _build_ontology_catalog_relationship(
    key: tuple[str, str, str, LinkDirection | None],
    entry: _OntologyCatalogEntry,
) -> Relationship:
    source_label, label, target_label, direction = key
    constrained = entry.constrained
    typed_implementations = tuple(entry.implementations)
    descriptions = (
        (
            (
                f"`{label}` is the canonical relationship name from "
                f"`{source_label}` to `{target_label}`. This constraint validates "
                "existing relationships and does not create them."
            ),
        )
        if constrained
        else ()
    )
    properties_by_name = {
        prop.name: prop
        for relationship in typed_implementations
        for prop in relationship.properties
    }
    return Relationship(
        source_label=source_label,
        label=label,
        target_label=target_label,
        direction=direction,
        descriptions=descriptions,
        properties=tuple(
            properties_by_name[name] for name in sorted(properties_by_name)
        ),
        modules=tuple(
            sorted(
                {
                    module
                    for relationship in typed_implementations
                    for module in relationship.modules
                }
            )
        ),
        origins=tuple(
            sorted(
                {
                    "ontology_aggregation",
                    *({"ontology_constraint"} if constrained else set()),
                    *(
                        origin
                        for relationship in typed_implementations
                        for origin in relationship.origins
                    ),
                }
            )
        ),
        schemas=(),
        analysis_jobs=tuple(
            {
                definition.qualified_name: definition
                for relationship in typed_implementations
                for definition in relationship.analysis_jobs
            }.values()
        ),
        permission_relationships=tuple(
            {
                (
                    definition.provider,
                    definition.source_label,
                    definition.relationship_name,
                    definition.target_label,
                ): definition
                for relationship in typed_implementations
                for definition in relationship.permission_relationships
            }.values()
        ),
        catalog_relationships=tuple(
            {
                (
                    definition.module,
                    definition.source_label,
                    definition.relationship_name,
                    definition.target_label,
                ): definition
                for relationship in typed_implementations
                for definition in relationship.catalog_relationships
            }.values()
        ),
    )


def write_schema_docs(model: DataModel, output_root: Path) -> None:
    """Overwrite the schema page of every module the data model can describe."""
    for module in generated_schema_modules(model):
        output_path = output_root / module / "schema.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_module_schema(model, module))
        logger.info("Wrote %s", output_path)


def generated_schema_modules(model: DataModel) -> list[str]:
    """List the modules whose schema page is generated rather than hand-written."""
    return [
        module
        for module in sorted(
            {module for node in model.nodes for module in node.modules}
        )
        if module not in MANUAL_SCHEMA_MODULES
    ]


def _render_node(
    node: Node,
    relationships: tuple[NodeRelationship, ...],
    ontology_kind: str | None = None,
    concrete_node_labels: tuple[str, ...] = (),
) -> list[str]:
    lines: list[str] = []
    if ontology_kind is not None:
        # Explicit myst target so module pages can link an ontology label without
        # depending on heading-slug anchors, which myst refuses to resolve.
        lines.append(f"({_ontology_anchor(node.label)})=")
    lines.extend([f"### {node.label}", ""])
    lines.extend(_render_descriptions(node.descriptions))
    lines.extend(_render_ontology_kind(ontology_kind, concrete_node_labels))
    lines.extend(_render_label_notes(node))
    lines.extend(_render_properties(node))
    lines.extend(_render_relationships(relationships))
    return lines


def _render_ontology_kind(
    ontology_kind: str | None,
    concrete_node_labels: tuple[str, ...],
) -> list[str]:
    if ontology_kind == "abstract":
        return [
            "> **Abstract Ontology Node**: This is a dedicated canonical node "
            "created separately from provider-specific nodes.",
            "",
        ]
    if ontology_kind != "semantic":
        return []
    lines = [
        "> **Semantic Label**: This label is applied directly to "
        "provider-specific nodes; it does not create a separate node.",
        "",
    ]
    if concrete_node_labels:
        concrete_labels = ", ".join(f"`{label}`" for label in concrete_node_labels)
        lines.extend([f"> **Implementations**: {concrete_labels}.", ""])
    return lines


def _render_label_notes(node: Node) -> list[str]:
    """Render the ontology, additional and conditional label blockquotes."""
    conditional_labels = tuple(
        conditional_label
        for conditional_label in node.conditional_labels
        if conditional_label.label not in SYSTEM_LABELS
    )
    conditional_label_names = {
        conditional_label.label for conditional_label in conditional_labels
    }
    ontology_labels = tuple(
        label for label in node.ontology_labels if label not in SYSTEM_LABELS
    )
    extra_labels = tuple(
        label for label in node.extra_labels if label not in SYSTEM_LABELS
    )
    unconditional_ontology_labels = tuple(
        label for label in ontology_labels if label not in conditional_label_names
    )

    def split_by_universality(labels: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
        return (
            tuple(x for x in labels if x not in node.partial_extra_labels),
            tuple(x for x in labels if x in node.partial_extra_labels),
        )

    universal_ontology, partial_ontology = split_by_universality(
        unconditional_ontology_labels
    )
    universal_additional, partial_additional = split_by_universality(
        tuple(label for label in extra_labels if label not in ontology_labels)
    )

    lines: list[str] = []
    if universal_ontology:
        lines.extend(_ontology_mapping_note(universal_ontology, partial=False))
    if partial_ontology:
        lines.extend(_ontology_mapping_note(partial_ontology, partial=True))
    if universal_additional:
        formatted = ", ".join(f"`{label}`" for label in universal_additional)
        lines.extend([f"> **Additional Labels**: This node also uses {formatted}.", ""])
    if partial_additional:
        formatted = ", ".join(f"`{label}`" for label in partial_additional)
        lines.extend(
            [
                f"> **Additional Labels**: Some schema variants may also use "
                f"{formatted}.",
                "",
            ]
        )
    lines.extend(
        _render_additional_label_definitions(
            node,
            {*universal_additional, *partial_additional},
        )
    )
    lines.extend(_render_conditional_labels(conditional_labels, ontology_labels))
    for projection_label in node.ontology_projections:
        lines.extend(
            [
                f"> **Ontology Projection**: `{node.label}` contributes data "
                f"to canonical {_ontology_label_link(projection_label)} nodes.",
                "",
            ]
        )
    return lines


def _ontology_mapping_note(labels: tuple[str, ...], partial: bool) -> list[str]:
    formatted = ", ".join(_ontology_label_link(label) for label in labels)
    noun = "label" if len(labels) == 1 else "labels"
    if partial:
        return [
            f"> **Ontology Mapping**: Some schema variants may also use the "
            f"ontology {noun} {formatted}.",
            "",
        ]
    return [
        f"> **Ontology Mapping**: This node uses the ontology {noun} {formatted}.",
        "",
    ]


def _render_additional_label_definitions(
    node: Node,
    additional_label_names: set[str],
) -> list[str]:
    definitions = tuple(
        definition
        for definition in node.label_definitions
        if not definition.conditions and definition.label in additional_label_names
    )
    if not definitions:
        return []
    lines = ["> **Additional Label Definitions**:", ">"]
    for definition in definitions:
        details = definition.description
        if definition.kind is LabelKind.COMPATIBILITY:
            compatibility_details = []
            if definition.replacement_label:
                compatibility_details.append(
                    f"Use `{definition.replacement_label}` instead."
                )
            if definition.remove_in:
                compatibility_details.append(
                    f"Scheduled for removal in v{definition.remove_in}."
                )
            if compatibility_details:
                details = f"{details} {' '.join(compatibility_details)}"
        lines.append(f"> - `{definition.label}`: {details}")
    lines.append("")
    return lines


def _render_conditional_labels(
    conditional_labels: tuple[ExtraNodeLabel, ...],
    ontology_labels: tuple[str, ...],
) -> list[str]:
    if not conditional_labels:
        return []
    lines = ["> **Conditional Labels**:", ">"]
    for conditional_label in conditional_labels:
        is_ontology = conditional_label.label in ontology_labels
        conditions = " and ".join(
            f"`{name}` equals `{value}`" for name, value in conditional_label.conditions
        )
        formatted_label = (
            _ontology_label_link(conditional_label.label)
            if is_ontology
            else f"`{conditional_label.label}`"
        )
        ontology_note = " (ontology label)" if is_ontology else ""
        lines.append(
            f"> - {formatted_label}{ontology_note} when {conditions}. "
            f"{conditional_label.description}"
        )
    lines.append("")
    return lines


def _render_properties(node: Node) -> list[str]:
    lines = ["#### Properties", ""]
    if any(prop.ontology for prop in node.properties):
        lines.extend(["Ontology-generated fields are shown in *italics*.", ""])
    if not node.properties:
        lines.extend(
            ["No normalized properties are defined for this semantic label.", ""]
        )
        return lines
    lines.extend(["| Field | Index | Description |", "|-------|-------|-------------|"])
    for prop in sorted(node.properties, key=_property_sort_key):
        field_name = f"*{prop.name}*" if prop.ontology else prop.name
        index = "Yes" if prop.indexed else ""
        lines.append(
            f"| {field_name} | {index} | "
            f"{_escape_table_cell(_property_description(prop))} |"
        )
    return lines


def _render_relationships(relationships: tuple[NodeRelationship, ...]) -> list[str]:
    lines = ["", "#### Relationships", ""]
    if not relationships:
        lines.extend(["No relationships.", ""])
        return lines
    for view in relationships:
        lines.append(f"- {_relationship_summary(view)}")
        permissions = _relationship_permissions(view.relationship)
        if permissions:
            lines.append(f"  - Evaluated permissions: {permissions}")
        target_preconditions = _relationship_target_preconditions(view.relationship)
        if target_preconditions:
            lines.append(f"  - Target precondition: {target_preconditions}")
        lines.extend(_render_relationship_properties(view.relationship))
        lines.append("")
    return lines


def _render_relationship_properties(relationship: Relationship) -> list[str]:
    properties = tuple(
        prop
        for prop in relationship.properties
        if not _is_standard_relationship_property(prop)
    )
    if not properties:
        return []
    return [
        "  - Properties:",
        "",
        "    | Field | Description |",
        "    |-------|-------------|",
        *(
            f"    | {prop.name} | "
            f"{_escape_table_cell(_relationship_property_description(prop))} |"
            for prop in sorted(properties, key=_property_sort_key)
        ),
    ]


def _relationship_summary(view: NodeRelationship) -> str:
    """Lead with the Cypher pattern and only add prose that says something more."""
    pattern = f"`{_node_relationship_pattern(view)}`"
    description = " ".join(view.relationship.descriptions) or _analysis_job_origin(
        view.relationship
    )
    return f"{pattern}: {description}" if description else pattern


def _analysis_job_origin(relationship: Relationship) -> str | None:
    if not relationship.analysis_jobs:
        return None
    jobs = ", ".join(
        f"`{definition.job.name}`" for definition in relationship.analysis_jobs
    )
    return f"generated by analysis job {jobs}."


def _ontology_anchor(label: str) -> str:
    return f"ontology-{label.lower()}"


def _ontology_label_link(label: str) -> str:
    # Deliberately unqualified: the ontology page declares an explicit myst target per
    # label, and myst resolves those project-wide, so the same reference works from any
    # module page without hardcoding a relative path to the ontology page.
    return f"[`{label}`](#{_ontology_anchor(label)})"


def _is_standard_relationship_property(prop: Property) -> bool:
    return prop.name in _STANDARD_RELATIONSHIP_PROPERTIES or prop.name.startswith("_")


def _relationship_property_description(prop: Property) -> str:
    description = _property_description(prop)
    if description != "No description provided." or not prop.source_names:
        return description
    source_fields = ", ".join(f"`{name}`" for name in prop.source_names)
    return f"Value sourced from {source_fields}."


def _assign_relationships(
    relationships: tuple[Relationship, ...],
    nodes: tuple[Node, ...],
) -> dict[str, tuple[Relationship, ...]]:
    """Group each relationship under the node sections that should document it."""
    assigned: dict[str, list[Relationship]] = {}
    nodes_by_label = {node.label: node for node in nodes}
    for relationship in relationships:
        owners = tuple(
            dict.fromkeys(
                label
                for label in (relationship.source_label, relationship.target_label)
                if label in nodes_by_label
            )
        )
        if not owners:
            owners = tuple(
                node.label
                for node in nodes
                if relationship_touches_node(relationship, node)
            )
        for owner in owners:
            assigned.setdefault(owner, []).append(relationship)
    return {
        label: tuple(
            sorted(
                values,
                key=lambda relationship: (
                    relationship.source_label,
                    relationship.label,
                    relationship.target_label,
                    relationship.direction.name if relationship.direction else "",
                ),
            )
        )
        for label, values in assigned.items()
    }


def _node_relationships_for_assigned(
    node: Node,
    relationships: tuple[Relationship, ...],
) -> tuple[NodeRelationship, ...]:
    """Adapt assigned Relationship rows into node-relative views for rendering."""
    carried = {
        node.label,
        *node.extra_labels,
        *node.ontology_labels,
        *(label.label for label in node.conditional_labels),
    }
    views: list[NodeRelationship] = []
    for relationship in relationships:
        matches_source = relationship.source_label in carried
        matches_target = relationship.target_label in carried
        if matches_source and (
            relationship.source_label == node.label or not matches_target
        ):
            other_label = relationship.target_label
            direction = relationship.direction
            inherited = relationship.source_label != node.label
        elif matches_target:
            other_label = relationship.source_label
            direction = (
                None
                if relationship.direction is None
                else (
                    LinkDirection.INWARD
                    if relationship.direction is LinkDirection.OUTWARD
                    else LinkDirection.OUTWARD
                )
            )
            inherited = relationship.target_label != node.label
        else:
            # Catalog row whose endpoints are the section label itself.
            other_label = (
                relationship.target_label
                if relationship.source_label == node.label
                else relationship.source_label
            )
            direction = relationship.direction
            inherited = False
        views.append(
            NodeRelationship(
                node_label=node.label,
                label=relationship.label,
                other_label=other_label,
                direction=direction,
                inherited=inherited,
                relationship=relationship,
            )
        )
    return tuple(views)


def _render_descriptions(descriptions: tuple[str, ...]) -> list[str]:
    """Render one description as a paragraph, several as a list of sync-path variants."""
    if not descriptions:
        return []
    if len(descriptions) == 1:
        return [descriptions[0], ""]
    return [
        "This node label is loaded by more than one sync path:",
        "",
        *(f"- {description}" for description in descriptions),
        "",
    ]


def _single_description(
    descriptions: tuple[str, ...],
    subject: str,
) -> str | None:
    if len(descriptions) > 1:
        raise ValueError(f"Conflicting descriptions for {subject}: {descriptions}")
    return descriptions[0] if descriptions else None


def _property_description(prop: Property) -> str:
    description = _single_description(prop.descriptions, f"property {prop.name}")
    if description:
        return description
    if prop.name == "firstseen":
        return "Timestamp when a sync job first created this node."
    if prop.name == "lastupdated":
        return "Timestamp of the last sync that observed this node."
    if prop.ontology:
        if prop.source_names:
            source_fields = ", ".join(f"`{name}`" for name in prop.source_names)
            return f"Normalized field sourced from {source_fields}."
        return "Property generated by the ontology mapping."
    if prop.analysis_jobs:
        jobs = ", ".join(
            f"`{definition.job.name}`" for definition in prop.analysis_jobs
        )
        return f"Property generated by analysis job: {jobs}."
    return "No description provided."


def _property_sort_key(prop: Property) -> tuple[bool, int, str]:
    priority = {
        "id": 0,
        "firstseen": 1,
        "lastupdated": 2,
    }.get(prop.name, 3)
    return prop.ontology, priority, prop.name


def _relationship_permissions(relationship: Relationship) -> str | None:
    permissions = sorted(
        {
            permission
            for definition in relationship.permission_relationships
            for permission in definition.permissions
        }
    )
    return ", ".join(f"`{permission}`" for permission in permissions) or None


def _relationship_target_preconditions(relationship: Relationship) -> str | None:
    preconditions = {
        definition.target_precondition
        for definition in relationship.permission_relationships
        if definition.target_precondition is not None
    }
    patterns = []
    for precondition in sorted(
        preconditions,
        key=lambda item: (
            item.related_label,
            item.relationship,
            item.direction,
        ),
    ):
        if precondition.direction == "incoming":
            pattern = (
                f"(:{relationship.target_label})"
                f"<-[:{precondition.relationship}]-"
                f"(:{precondition.related_label})"
            )
        else:
            pattern = (
                f"(:{relationship.target_label})"
                f"-[:{precondition.relationship}]->"
                f"(:{precondition.related_label})"
            )
        patterns.append(f"`{pattern}` must exist")
    return "; ".join(patterns) or None


def _relationship_pattern(relationship: Relationship) -> str:
    connector = (
        f"-[:{relationship.label}]-"
        if relationship.direction is None
        else f"-[:{relationship.label}]->"
    )
    return f"(:{relationship.source_label}){connector}(:{relationship.target_label})"


def _node_relationship_pattern(view: NodeRelationship) -> str:
    """Cypher pattern for a node-relative relationship view."""
    if view.direction is None:
        return f"(:{view.node_label})-[:{view.label}]-(:{view.other_label})"
    if view.direction is LinkDirection.OUTWARD:
        return f"(:{view.node_label})-[:{view.label}]->(:{view.other_label})"
    return f"(:{view.other_label})-[:{view.label}]->(:{view.node_label})"


def _mermaid_relationship(relationship: Relationship) -> str:
    connector = (
        f"---|{relationship.label}|"
        if relationship.direction is None
        else f"-- {relationship.label} -->"
    )
    return f"{relationship.source_label} {connector} {relationship.target_label}"


def _module_title(module: str) -> str:
    title_overrides = {
        "aibom": "AIBOM",
        "aws": "AWS",
        "gcp": "GCP",
        "oci": "OCI",
        "sentinelone": "SentinelOne",
        "socketdev": "Socket.dev",
    }
    return title_overrides.get(module, module.replace("_", " ").title())


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
