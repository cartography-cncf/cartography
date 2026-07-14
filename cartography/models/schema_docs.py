from __future__ import annotations

from pathlib import Path

from cartography.models.introspection import DataModel
from cartography.models.introspection import Node
from cartography.models.introspection import Property
from cartography.models.introspection import Relationship

GENERATED_NOTICE = "<!-- Generated from the data model. Do not edit manually. -->"


def render_module_schema(model: DataModel, module: str) -> str:
    """Render one module's introspected data model as schema Markdown."""
    module_model = model.for_module(module)
    if not module_model.nodes:
        raise ValueError(f'No nodes found for module "{module}".')

    owned_labels = {node.label for node in module_model.nodes}
    assigned_relationships = _assign_relationships(
        module_model.relationships,
        owned_labels,
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
        for relationship in module_model.relationships
    )
    lines.extend(["```", ""])

    for node in module_model.nodes:
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
    ontology_labels = (
        *node.extra_labels,
        *(conditional.label for conditional in node.conditional_labels),
    )
    if ontology_labels:
        formatted_labels = ", ".join(f"`{label}`" for label in ontology_labels)
        lines.extend(
            [
                f"> **Ontology Mapping**: This node has the extra "
                f"{'label' if len(ontology_labels) == 1 else 'labels'} "
                f"{formatted_labels}.",
                "",
            ]
        )

    lines.extend(
        [
            "| Field | Description |",
            "|-------|-------------|",
        ]
    )
    for prop in sorted(node.properties, key=_property_sort_key):
        field_name = f"**{prop.name}**" if prop.indexed else prop.name
        lines.append(
            f"| {field_name} | {_escape_table_cell(_property_description(prop))} |"
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


def _assign_relationships(
    relationships: tuple[Relationship, ...],
    owned_labels: set[str],
) -> dict[str, tuple[Relationship, ...]]:
    assigned: dict[str, list[Relationship]] = {}
    for relationship in relationships:
        if relationship.source_label in owned_labels:
            owner = relationship.source_label
        elif relationship.target_label in owned_labels:
            owner = relationship.target_label
        else:
            continue
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
