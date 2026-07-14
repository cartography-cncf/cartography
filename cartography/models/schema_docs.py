from __future__ import annotations

from pathlib import Path

from cartography.models.introspection import DataModel
from cartography.models.introspection import Node
from cartography.models.introspection import Property
from cartography.models.introspection import Relationship

GENERATED_NOTICE = "<!-- Generated from the data model. Do not edit manually. -->"


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
    ontology_labels = node.ontology_labels
    if ontology_labels:
        formatted_labels = ", ".join(f"`{label}`" for label in ontology_labels)
        lines.extend(
            [
                f"> **Ontology Mapping**: This node uses the ontology "
                f"{'label' if len(ontology_labels) == 1 else 'labels'} "
                f"{formatted_labels}.",
                "",
            ]
        )

    lines.extend(
        [
            "Ontology-generated fields are shown in *italics*.",
            "",
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
        lines.extend(
            [
                f"- {description or _default_relationship_description(relationship)}",
                "",
                "    ```cypher",
                f"    {_relationship_pattern(relationship)}",
                "    ```",
                "",
            ]
        )
    return lines


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
        owners: tuple[str, ...]
        if relationship.source_label in nodes_by_label:
            owners = (relationship.source_label,)
        elif relationship.target_label in nodes_by_label:
            owners = (relationship.target_label,)
        else:
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
    return module.replace("_", " ").title()


def _model_modules(model: DataModel) -> list[str]:
    return sorted({module for node in model.nodes for module in node.modules})


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
