from __future__ import annotations

from dataclasses import fields as dataclass_fields
from dataclasses import replace
from pathlib import Path

from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.introspection import DataModel
from cartography.models.introspection import Node
from cartography.models.introspection import Property
from cartography.models.introspection import Relationship

GENERATED_NOTICE = "<!-- Generated from the data model. Do not edit manually. -->"
_STANDARD_RELATIONSHIP_PROPERTIES = frozenset({"firstseen", "lastupdated"})


def render_module_schema(model: DataModel, module: str) -> str:
    """Render one module's introspected data model as schema Markdown."""
    if module == "ontology":
        return _render_ontology_schema(model)

    module_nodes = tuple(
        sorted(
            (
                _node_for_module(node, module)
                for node in model.nodes
                if module in node.modules
            ),
            key=_node_sort_key,
        )
    )
    if not module_nodes:
        raise ValueError(f'No nodes found for module "{module}".')

    module_relationships = _module_relationships(
        model.relationships,
        module_nodes,
        module,
        model.nodes,
    )
    assigned_relationships = _assign_relationships(
        module_relationships,
        module_nodes,
        model.nodes,
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
        for relationship in module_relationships
    )
    lines.extend(["```", ""])

    for node in module_nodes:
        lines.extend(_render_node(node, assigned_relationships.get(node.label, ())))

    return "\n".join(lines).rstrip() + "\n"


def _node_for_module(node: Node, module: str) -> Node:
    """Scope aggregated labels to schemas owned by the rendered module."""
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
            tuple(sorted(conditional.conditions.items())),
        ): conditional
        for item in provenance
        for conditional in item.conditional_labels
    }
    scoped_conditional_labels = tuple(
        sorted(
            conditional_labels.values(),
            key=lambda conditional: (
                conditional.label,
                tuple(sorted(conditional.conditions.items())),
            ),
        )
    )
    declared_labels = {
        *extra_labels,
        *(conditional.label for conditional in scoped_conditional_labels),
    }
    return replace(
        node,
        extra_labels=tuple(sorted(extra_labels)),
        partial_extra_labels=tuple(sorted(partial_labels)),
        conditional_labels=scoped_conditional_labels,
        ontology_labels=tuple(
            label for label in node.ontology_labels if label in declared_labels
        ),
    )


def _node_sort_key(node: Node) -> tuple[str, str]:
    return node.label.casefold(), node.label


def _render_ontology_schema(model: DataModel) -> str:
    """Render the cross-module ontology catalog."""
    canonical_nodes = tuple(node for node in model.nodes if "ontology" in node.modules)
    semantic_nodes = tuple(
        Node(
            label=semantic_label.label,
            descriptions=(
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
    assigned_relationships = _assign_relationships(
        relationships,
        catalog_nodes,
        model.nodes,
    )
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
        "of existing relationships. They do not create relationships.",
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
                assigned_relationships.get(node.label, ()),
                ontology_kind=ontology_kind,
                concrete_node_labels=implementations_by_label.get(node.label, ()),
            )
        )
    return "\n".join(lines).rstrip() + "\n"


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
        dict[str, object],
    ] = {}
    key: tuple[str, str, str, LinkDirection | None]

    for constraint in model.ontology_relationship_constraints:
        key = (
            constraint.source_label,
            constraint.label,
            constraint.target_label,
            LinkDirection.OUTWARD,
        )
        entries[key] = {"constrained": True, "implementations": []}

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
                entry = entries.setdefault(
                    key,
                    {"constrained": False, "implementations": []},
                )
                implementations = entry["implementations"]
                assert isinstance(implementations, list)
                implementations.append(relationship)

    relationships = [
        _build_ontology_catalog_relationship(key, entry)
        for key, entry in entries.items()
    ]
    relationships.extend(
        relationship
        for relationship in _module_relationships(
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
    entry: dict[str, object],
) -> Relationship:
    source_label, label, target_label, direction = key
    constrained = bool(entry["constrained"])
    implementations = entry["implementations"]
    assert isinstance(implementations, list)
    typed_implementations = tuple(
        relationship
        for relationship in implementations
        if isinstance(relationship, Relationship)
    )
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


def write_module_schema_docs(
    model: DataModel,
    modules: list[str],
    output_root: Path,
    preserve_existing: bool = False,
) -> None:
    """Write generated schema docs while optionally preserving manual pages."""
    for module in modules:
        output_path = output_root / module / "schema.md"
        if preserve_existing and output_path.exists():
            print(f"Preserved {output_path}")
            continue
        content = render_module_schema(model, module)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        print(f"Wrote {output_path}")


def generate_missing_schema_docs(
    model: DataModel,
    output_root: Path,
) -> None:
    """Generate schema pages for modules that do not have a manual page."""
    write_module_schema_docs(
        model,
        _model_modules(model),
        output_root=output_root,
        preserve_existing=True,
    )


def _render_node(
    node: Node,
    relationships: tuple[Relationship, ...],
    ontology_kind: str | None = None,
    concrete_node_labels: tuple[str, ...] = (),
) -> list[str]:
    lines = [
        f"### {node.label}",
        "",
        _single_description(node.descriptions, f"node {node.label}")
        or f"Representation of a `{node.label}` node.",
        "",
    ]
    if ontology_kind == "abstract":
        lines.extend(
            [
                "> **Abstract Ontology Node**: This is a dedicated canonical node "
                "created separately from provider-specific nodes.",
                "",
            ]
        )
    elif ontology_kind == "semantic":
        lines.extend(
            [
                "> **Semantic Label**: This label is applied directly to "
                "provider-specific nodes; it does not create a separate node.",
                "",
            ]
        )
        if concrete_node_labels:
            concrete_labels = ", ".join(f"`{label}`" for label in concrete_node_labels)
            lines.extend(
                [
                    f"> **Implementations**: {concrete_labels}.",
                    "",
                ]
            )
    conditional_label_names = {
        conditional_label.label for conditional_label in node.conditional_labels
    }
    unconditional_ontology_labels = tuple(
        label for label in node.ontology_labels if label not in conditional_label_names
    )
    universal_ontology_labels = tuple(
        label
        for label in unconditional_ontology_labels
        if label not in node.partial_extra_labels
    )
    partial_ontology_labels = tuple(
        label
        for label in unconditional_ontology_labels
        if label in node.partial_extra_labels
    )
    if universal_ontology_labels:
        formatted_labels = ", ".join(
            _ontology_label_link(label) for label in universal_ontology_labels
        )
        lines.extend(
            [
                f"> **Ontology Mapping**: This node uses the ontology "
                f"{'label' if len(universal_ontology_labels) == 1 else 'labels'} "
                f"{formatted_labels}.",
                "",
            ]
        )
    if partial_ontology_labels:
        formatted_labels = ", ".join(
            _ontology_label_link(label) for label in partial_ontology_labels
        )
        lines.extend(
            [
                f"> **Ontology Mapping**: Some schema variants may also use the "
                f"ontology "
                f"{'label' if len(partial_ontology_labels) == 1 else 'labels'} "
                f"{formatted_labels}.",
                "",
            ]
        )
    universal_additional_labels = tuple(
        label
        for label in node.extra_labels
        if label not in node.ontology_labels and label not in node.partial_extra_labels
    )
    partial_additional_labels = tuple(
        label
        for label in node.extra_labels
        if label not in node.ontology_labels and label in node.partial_extra_labels
    )
    if universal_additional_labels:
        formatted_labels = ", ".join(
            f"`{label}`" for label in universal_additional_labels
        )
        lines.extend(
            [
                f"> **Additional Labels**: This node also uses " f"{formatted_labels}.",
                "",
            ]
        )
    if partial_additional_labels:
        formatted_labels = ", ".join(
            f"`{label}`" for label in partial_additional_labels
        )
        lines.extend(
            [
                f"> **Additional Labels**: Some schema variants may also use "
                f"{formatted_labels}.",
                "",
            ]
        )
    if node.conditional_labels:
        lines.extend(["> **Conditional Labels**:", ">"])
        for conditional_label in node.conditional_labels:
            ontology_note = (
                " (ontology label)"
                if conditional_label.label in node.ontology_labels
                else ""
            )
            conditions = " and ".join(
                f"`{field}` equals `{value}`"
                for field, value in sorted(conditional_label.conditions.items())
            )
            formatted_label = (
                _ontology_label_link(conditional_label.label)
                if conditional_label.label in node.ontology_labels
                else f"`{conditional_label.label}`"
            )
            lines.append(f"> - {formatted_label}{ontology_note} when {conditions}.")
        lines.append("")
    for projection_label in node.ontology_projections:
        lines.extend(
            [
                f"> **Ontology Projection**: `{node.label}` contributes data "
                f"to canonical {_ontology_label_link(projection_label)} nodes.",
                "",
            ]
        )

    if any(prop.ontology for prop in node.properties):
        lines.extend(
            [
                "Ontology-generated fields are shown in *italics*.",
                "",
            ]
        )
    if node.properties:
        lines.extend(
            [
                "| Field | Index | Description |",
                "|-------|-------|-------------|",
            ]
        )
        for prop in sorted(node.properties, key=_property_sort_key):
            field_name = f"*{prop.name}*" if prop.ontology else prop.name
            index = "Yes" if prop.indexed else ""
            lines.append(
                f"| {field_name} | {index} | "
                f"{_escape_table_cell(_property_description(prop))} |"
            )
    else:
        lines.extend(
            [
                "No normalized properties are defined for this semantic label.",
                "",
            ]
        )

    lines.extend(["", "#### Relationships", ""])
    if not relationships:
        lines.extend(["No relationships.", ""])
        return lines

    for relationship in relationships:
        description = _single_description(
            relationship.descriptions,
            (
                f"relationship {relationship.source_label}-"
                f"{relationship.label}->{relationship.target_label}"
            ),
        )
        detail_lines = [
            f"- {description or _default_relationship_description(relationship)}",
        ]
        permissions = _relationship_permissions(relationship)
        if permissions:
            detail_lines.append(f"  - Evaluated permissions: {permissions}")
        target_preconditions = _relationship_target_preconditions(relationship)
        if target_preconditions:
            detail_lines.append(f"  - Target precondition: {target_preconditions}")
        relationship_properties = tuple(
            prop
            for prop in relationship.properties
            if not _is_standard_relationship_property(prop)
        )
        if relationship_properties:
            detail_lines.extend(
                [
                    "  - Properties:",
                    "",
                    "    | Field | Description |",
                    "    |-------|-------------|",
                    *(
                        "    | "
                        f"{prop.name} | "
                        f"{_escape_table_cell(_relationship_property_description(prop))} |"
                        for prop in sorted(
                            relationship_properties,
                            key=_property_sort_key,
                        )
                    ),
                ]
            )
        lines.extend(
            [
                *detail_lines,
                "",
                "    ```cypher",
                f"    {_relationship_pattern(relationship)}",
                "    ```",
                "",
            ]
        )
    return lines


def _ontology_label_link(label: str) -> str:
    return f"[`{label}`](../ontology/schema.html#{label.lower()})"


def _is_standard_relationship_property(prop: Property) -> bool:
    return prop.name in _STANDARD_RELATIONSHIP_PROPERTIES or prop.name.startswith("_")


def _relationship_property_description(prop: Property) -> str:
    description = _property_description(prop)
    if description != "No description provided." or not prop.source_names:
        return description
    source_fields = ", ".join(f"`{name}`" for name in prop.source_names)
    return f"Value sourced from {source_fields}."


def _module_relationships(
    relationships: tuple[Relationship, ...],
    nodes: tuple[Node, ...],
    module: str,
    all_nodes: tuple[Node, ...],
) -> tuple[Relationship, ...]:
    node_labels = {node.label for node in nodes}
    primary_labels = {node.label for node in all_nodes}
    return tuple(
        relationship
        for relationship in relationships
        if module in relationship.modules
        or relationship.source_label in node_labels
        or relationship.target_label in node_labels
        or any(
            _relationship_matches_broad_node(
                relationship,
                node,
                primary_labels,
                require_explicit_match=module == "aws",
            )
            for node in nodes
        )
    )


def _assign_relationships(
    relationships: tuple[Relationship, ...],
    nodes: tuple[Node, ...],
    all_nodes: tuple[Node, ...],
) -> dict[str, tuple[Relationship, ...]]:
    assigned: dict[str, list[Relationship]] = {}
    nodes_by_label = {node.label: node for node in nodes}
    primary_labels = {node.label for node in all_nodes}
    for relationship in relationships:
        owners = tuple(
            dict.fromkeys(
                label
                for label in (
                    relationship.source_label,
                    relationship.target_label,
                )
                if label in nodes_by_label
            )
        )
        if not owners:
            owners = tuple(
                node.label
                for node in nodes
                if _relationship_matches_broad_node(
                    relationship,
                    node,
                    primary_labels,
                )
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


def _relationship_matches_broad_node(
    relationship: Relationship,
    node: Node,
    primary_labels: set[str],
    require_explicit_match: bool = False,
) -> bool:
    broad_labels = {
        *node.extra_labels,
        *node.ontology_labels,
        *(label.label for label in node.conditional_labels),
    }
    if not broad_labels:
        return False

    if relationship.schemas:
        return any(
            _schema_matches_broad_node(
                schema,
                node,
                broad_labels,
                primary_labels,
                require_explicit_match,
            )
            for schema in relationship.schemas
        )

    if relationship.analysis_jobs:
        return _analysis_context_matches_node(
            relationship,
            node,
            require_explicit_match,
        ) and any(
            endpoint in broad_labels and endpoint not in primary_labels
            for endpoint in (relationship.source_label, relationship.target_label)
        )

    return not require_explicit_match and any(
        endpoint in broad_labels and endpoint not in primary_labels
        for endpoint in (relationship.source_label, relationship.target_label)
    )


def _analysis_context_matches_node(
    relationship: Relationship,
    node: Node,
    require_explicit_match: bool = False,
) -> bool:
    contexts = relationship.analysis_context_modules
    if not contexts:
        return True
    if () in contexts:
        return not require_explicit_match
    node_modules = set(node.modules)
    return any(node_modules.intersection(context) for context in contexts)


def _schema_matches_broad_node(
    schema: CartographyRelSchema,
    node: Node,
    broad_labels: set[str],
    primary_labels: set[str],
    require_explicit_match: bool = False,
) -> bool:
    target_matches_extra_labels = (
        not require_explicit_match
        and schema.target_node_label not in primary_labels
        or schema.match_target_extra_labels
    )
    if (
        target_matches_extra_labels
        and schema.target_node_label in broad_labels
        and _matcher_fits_node(schema.target_node_matcher, node)
    ):
        return True

    source_label = schema.source_node_label
    source_matcher = schema.source_node_matcher
    source_matches_extra_labels = bool(
        source_label
        and (
            (not require_explicit_match and source_label not in primary_labels)
            or schema.match_source_extra_labels
        )
    )
    return bool(
        source_matches_extra_labels
        and source_label in broad_labels
        and source_matcher is not None
        and _matcher_fits_node(source_matcher, node)
    )


def _matcher_fits_node(
    matcher: SourceNodeMatcher | TargetNodeMatcher,
    node: Node,
) -> bool:
    matcher_keys = {field.name for field in dataclass_fields(matcher)}
    node_properties = {prop.name for prop in node.properties}
    return matcher_keys <= node_properties


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
    if prop.name == "_ont_source":
        return "Module that populated this node's ontology fields."
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


def _default_relationship_description(relationship: Relationship) -> str:
    if relationship.analysis_jobs:
        jobs = ", ".join(
            f"`{definition.job.name}`" for definition in relationship.analysis_jobs
        )
        return (
            f"Analysis job {jobs} generates "
            f"`{_relationship_pattern(relationship)}`."
        )
    return (
        f"`{relationship.source_label}` connects to "
        f"`{relationship.target_label}` through `{relationship.label}`."
    )


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
        "gcp": "GCP",
        "sentinelone": "SentinelOne",
        "socketdev": "Socket.dev",
    }
    return title_overrides.get(module, module.replace("_", " ").title())


def _model_modules(model: DataModel) -> list[str]:
    return sorted({module for node in model.nodes for module in node.modules})


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
