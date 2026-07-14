from __future__ import annotations

from pathlib import Path

from cartography.models.introspection import DataModel
from cartography.models.introspection import Node
from cartography.models.introspection import Property
from cartography.models.introspection import Relationship

GENERATED_NOTICE = "<!-- Generated from the data model. Do not edit manually. -->"
_STANDARD_RELATIONSHIP_PROPERTIES = frozenset({"firstseen", "lastupdated"})


def render_module_schema(model: DataModel, module: str) -> str:
    """Render one module's introspected data model as schema Markdown."""
    module_nodes = tuple(node for node in model.nodes if module in node.modules)
    if not module_nodes:
        raise ValueError(f'No nodes found for module "{module}".')

    module_relationships = _module_relationships(
        model.relationships,
        module_nodes,
        module,
    )
    assigned_relationships = _assign_relationships(
        module_relationships,
        module_nodes,
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
) -> list[str]:
    lines = [
        f"### {node.label}",
        "",
        _single_description(node.descriptions, f"node {node.label}")
        or f"Representation of a `{node.label}` node.",
        "",
    ]
    conditional_label_names = {
        conditional_label.label for conditional_label in node.conditional_labels
    }
    unconditional_ontology_labels = tuple(
        label for label in node.ontology_labels if label not in conditional_label_names
    )
    if unconditional_ontology_labels:
        formatted_labels = ", ".join(
            f"`{label}`" for label in unconditional_ontology_labels
        )
        lines.extend(
            [
                f"> **Ontology Mapping**: This node uses the ontology "
                f"{'label' if len(unconditional_ontology_labels) == 1 else 'labels'} "
                f"{formatted_labels}.",
                "",
            ]
        )
    additional_labels = tuple(
        label for label in node.extra_labels if label not in node.ontology_labels
    )
    if additional_labels:
        formatted_labels = ", ".join(f"`{label}`" for label in additional_labels)
        lines.extend(
            [
                f"> **Additional Labels**: This node also uses " f"{formatted_labels}.",
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
            lines.append(
                f"> - `{conditional_label.label}`{ontology_note} when {conditions}."
            )
        lines.append("")
    for projection_label in node.ontology_projections:
        lines.extend(
            [
                f"> **Ontology Projection**: `{node.label}` contributes data "
                f"to canonical `{projection_label}` nodes.",
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
            f"  - Source: {_relationship_provenance(relationship)}",
        ]
        permissions = _relationship_permissions(relationship)
        if permissions:
            detail_lines.append(f"  - Evaluated permissions: {permissions}")
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
) -> tuple[Relationship, ...]:
    relevant_labels = {
        label for node in nodes for label in (node.label, *node.ontology_labels)
    }
    return tuple(
        relationship
        for relationship in relationships
        if module in relationship.modules
        or relationship.source_label in relevant_labels
        or relationship.target_label in relevant_labels
    )


def _assign_relationships(
    relationships: tuple[Relationship, ...],
    nodes: tuple[Node, ...],
) -> dict[str, tuple[Relationship, ...]]:
    assigned: dict[str, list[Relationship]] = {}
    nodes_by_label = {node.label: node for node in nodes}
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
                if relationship.source_label in node.ontology_labels
                or relationship.target_label in node.ontology_labels
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


def _relationship_provenance(relationship: Relationship) -> str:
    sources: list[str] = []
    schema_names = ", ".join(
        f"`{type(schema).__name__}`"
        for schema in sorted(
            relationship.schemas,
            key=lambda schema: type(schema).__name__,
        )
    )
    schema_suffix = f" ({schema_names})" if schema_names else ""
    origin_labels = {
        "node_schema": "node schema relationship",
        "sub_resource": "sub-resource relationship",
        "matchlink": "MatchLink",
    }
    for origin in ("node_schema", "sub_resource", "matchlink"):
        if origin in relationship.origins:
            sources.append(f"{origin_labels[origin]}{schema_suffix}")
    sources.extend(
        f"analysis job `{definition.job.name}`"
        for definition in relationship.analysis_jobs
    )
    if "analysis" in relationship.origins and not relationship.analysis_jobs:
        sources.append("analysis job")
    sources.extend(
        (
            f"{definition.provider.upper()} permission evaluation "
            f"from `{definition.config_path}`"
        )
        for definition in relationship.permission_relationships
    )
    if (
        "permission_evaluation" in relationship.origins
        and not relationship.permission_relationships
    ):
        sources.append("permission evaluation")
    return "; ".join(sources) or "unknown"


def _relationship_permissions(relationship: Relationship) -> str | None:
    permissions = sorted(
        {
            permission
            for definition in relationship.permission_relationships
            for permission in definition.permissions
        }
    )
    return ", ".join(f"`{permission}`" for permission in permissions) or None


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
    return {"aibom": "AIBOM"}.get(module, module.replace("_", " ").title())


def _model_modules(model: DataModel) -> list[str]:
    return sorted({module for node in model.nodes for module in node.modules})


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
