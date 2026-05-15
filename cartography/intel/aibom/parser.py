import json
import logging
from collections import Counter
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedAIBOMWorkflow:
    workflow_id: str
    function: str | None
    file_path: str | None
    line: int | None
    distance: int | None


@dataclass(frozen=True)
class ParsedAIBOMRelationship:
    relationship_type: str
    source_instance_id: str | None
    source_name: str | None
    source_category: str | None
    target_instance_id: str | None
    target_name: str | None
    target_category: str | None


@dataclass(frozen=True)
class ParsedAIBOMComponent:
    name: str
    category: str
    instance_id: str | None
    assigned_target: str | None
    file_path: str | None
    line_number: int | None
    model_name: str | None
    framework: str | None
    label: str | None
    workflow_ids: list[str]


@dataclass(frozen=True)
class ParsedAIBOMSource:
    source_key: str
    source_status: str | None
    source_kind: str | None
    total_components: int
    total_workflows: int
    total_relationships: int
    category_summary_json: str | None
    components: list[ParsedAIBOMComponent]
    workflows: list[ParsedAIBOMWorkflow]
    relationships: list[ParsedAIBOMRelationship]


@dataclass(frozen=True)
class ParsedAIBOMDocument:
    image_uri: str
    report_location: str | None
    scan_scope: str | None
    scanner_name: str | None
    scanner_version: str | None
    analyzer_version: str | None
    analysis_status: str | None
    total_sources: int
    total_components: int
    total_workflows: int
    total_relationships: int
    category_summary_json: str | None
    sources: list[ParsedAIBOMSource]


def _as_str(value: Any) -> str | None:
    """Return a stripped non-empty string, or None."""
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned
    return None


def _parse_workflow(workflow: dict[str, Any]) -> ParsedAIBOMWorkflow | None:
    workflow_id = _as_str(workflow.get("id")) or _as_str(workflow.get("workflow_id"))
    if not workflow_id:
        logger.warning("Skipping AIBOM workflow missing id: %s", workflow)
        return None
    return ParsedAIBOMWorkflow(
        workflow_id=workflow_id,
        function=_as_str(workflow.get("function")),
        file_path=_as_str(workflow.get("file_path")),
        line=workflow.get("line"),
        distance=workflow.get("distance"),
    )


def _parse_component(
    component: dict[str, Any],
    category_hint: str | None,
) -> tuple[ParsedAIBOMComponent | None, list[ParsedAIBOMWorkflow]]:
    name = _as_str(component.get("name"))
    if not name:
        logger.warning("Skipping AIBOM component missing name: %s", component)
        return None, []

    category = _as_str(component.get("category")) or category_hint or "unknown"

    embedded_workflows: list[ParsedAIBOMWorkflow] = []
    workflow_ids: list[str] = []
    workflow_objects = component.get("workflows")
    if isinstance(workflow_objects, list):
        for workflow_obj in workflow_objects:
            if not isinstance(workflow_obj, dict):
                continue
            workflow = _parse_workflow(workflow_obj)
            if workflow is None:
                continue
            embedded_workflows.append(workflow)
            workflow_ids.append(workflow.workflow_id)

    parsed_component = ParsedAIBOMComponent(
        name=name,
        category=category,
        instance_id=_as_str(component.get("instance_id")),
        assigned_target=_as_str(component.get("assigned_target")),
        file_path=_as_str(component.get("file_path")),
        line_number=component.get("line_number"),
        model_name=_as_str(component.get("model_name")),
        framework=_as_str(component.get("framework")),
        label=_as_str(component.get("label")),
        workflow_ids=workflow_ids,
    )
    return parsed_component, embedded_workflows


def _extract_rel_endpoint(
    relationship: dict[str, Any],
    primary_key: str,
    fallback_key: str,
) -> tuple[str | None, str | None, str | None]:
    endpoint_obj = relationship.get(primary_key)
    if not isinstance(endpoint_obj, dict):
        endpoint_obj = relationship.get(fallback_key)
    if isinstance(endpoint_obj, dict):
        return (
            _as_str(endpoint_obj.get("instance_id")) or _as_str(endpoint_obj.get("id")),
            _as_str(endpoint_obj.get("name")),
            _as_str(endpoint_obj.get("category")),
        )

    primary_prefix_values = (
        _as_str(relationship.get(f"{primary_key}_instance_id"))
        or _as_str(relationship.get(f"{primary_key}_id")),
        _as_str(relationship.get(f"{primary_key}_name")),
        _as_str(relationship.get(f"{primary_key}_category")),
    )
    if any(primary_prefix_values):
        prefix = fallback_key if fallback_key in {"from", "to"} else primary_key
        return (
            primary_prefix_values[0]
            or _as_str(relationship.get(f"{prefix}_instance_id"))
            or _as_str(relationship.get(f"{prefix}_id")),
            primary_prefix_values[1] or _as_str(relationship.get(f"{prefix}_name")),
            primary_prefix_values[2] or _as_str(relationship.get(f"{prefix}_category")),
        )

    prefix = fallback_key if fallback_key in {"from", "to"} else primary_key
    return (
        _as_str(relationship.get(f"{prefix}_instance_id"))
        or _as_str(relationship.get(f"{prefix}_id")),
        _as_str(relationship.get(f"{prefix}_name")),
        _as_str(relationship.get(f"{prefix}_category")),
    )


def _parse_relationship(
    relationship: dict[str, Any],
) -> ParsedAIBOMRelationship | None:
    relationship_type = (
        _as_str(relationship.get("relationship_type"))
        or _as_str(relationship.get("relationship"))
        or _as_str(relationship.get("type"))
        or _as_str(relationship.get("label"))
    )
    if not relationship_type:
        logger.warning("Skipping AIBOM relationship missing type: %s", relationship)
        return None

    source_instance_id, source_name, source_category = _extract_rel_endpoint(
        relationship,
        "source",
        "from",
    )
    target_instance_id, target_name, target_category = _extract_rel_endpoint(
        relationship,
        "target",
        "to",
    )

    if not any([source_instance_id, source_name]) or not any(
        [target_instance_id, target_name]
    ):
        logger.warning(
            "Skipping AIBOM relationship missing component endpoints: %s",
            relationship,
        )
        return None

    return ParsedAIBOMRelationship(
        relationship_type=relationship_type,
        source_instance_id=source_instance_id,
        source_name=source_name,
        source_category=source_category,
        target_instance_id=target_instance_id,
        target_name=target_name,
        target_category=target_category,
    )


def _parse_components(
    components_obj: Any,
) -> tuple[list[ParsedAIBOMComponent], list[ParsedAIBOMWorkflow]]:
    components: list[ParsedAIBOMComponent] = []
    embedded_workflows: list[ParsedAIBOMWorkflow] = []

    if isinstance(components_obj, list):
        for component_obj in components_obj:
            if not isinstance(component_obj, dict):
                logger.warning(
                    "Skipping non-dict component entry: %s",
                    type(component_obj).__name__,
                )
                continue
            parsed_component, parsed_workflows = _parse_component(component_obj, None)
            if parsed_component is not None:
                components.append(parsed_component)
            embedded_workflows.extend(parsed_workflows)
        return components, embedded_workflows

    if not isinstance(components_obj, dict):
        raise ValueError("AIBOM document has invalid components format")

    for category, category_components_obj in components_obj.items():
        category_hint = _as_str(category)
        if not isinstance(category_components_obj, list):
            logger.warning(
                "Skipping non-list component category %s: %s",
                category,
                type(category_components_obj).__name__,
            )
            continue
        for component_obj in category_components_obj:
            if not isinstance(component_obj, dict):
                logger.warning(
                    "Skipping non-dict component entry in category %s: %s",
                    category,
                    type(component_obj).__name__,
                )
                continue
            parsed_component, parsed_workflows = _parse_component(
                component_obj,
                category_hint,
            )
            if parsed_component is not None:
                components.append(parsed_component)
            embedded_workflows.extend(parsed_workflows)

    return components, embedded_workflows


def _parse_relationships(
    relationships_obj: Any,
) -> list[ParsedAIBOMRelationship]:
    relationships: list[ParsedAIBOMRelationship] = []

    if relationships_obj is None:
        return relationships

    if not isinstance(relationships_obj, list):
        logger.warning(
            "Skipping invalid AIBOM relationships payload: expected list, got %s",
            type(relationships_obj).__name__,
        )
        return relationships

    for relationship_obj in relationships_obj:
        if not isinstance(relationship_obj, dict):
            logger.warning(
                "Skipping non-dict relationship entry: %s",
                type(relationship_obj).__name__,
            )
            continue
        parsed_relationship = _parse_relationship(relationship_obj)
        if parsed_relationship is not None:
            relationships.append(parsed_relationship)

    return relationships


def parse_aibom_document(
    document: dict[str, Any],
    report_location: str | None = None,
) -> ParsedAIBOMDocument:
    image_uri = _as_str(document.get("image_uri"))
    if not image_uri:
        raise ValueError("AIBOM envelope is missing required image_uri field")

    scan_scope = _as_str(document.get("scan_scope"))

    analyzer_version: str | None = None
    analysis_status: str | None = None
    scanner_name: str | None = None
    scanner_version: str | None = None

    scanner_obj = document.get("scanner")
    if isinstance(scanner_obj, dict):
        scanner_name = _as_str(scanner_obj.get("name"))
        scanner_version = _as_str(scanner_obj.get("version"))

    report_obj = document.get("report")
    if not isinstance(report_obj, dict):
        raise ValueError("AIBOM envelope is missing required report field")

    analysis_obj = report_obj.get("aibom_analysis")
    if not isinstance(analysis_obj, dict):
        raise ValueError("AIBOM envelope is missing or has invalid aibom_analysis")

    metadata_obj = analysis_obj.get("metadata")
    if isinstance(metadata_obj, dict):
        analyzer_version = _as_str(metadata_obj.get("analyzer_version"))
        analysis_status = _as_str(metadata_obj.get("status"))

    summary_obj = analysis_obj.get("summary")
    if isinstance(summary_obj, dict):
        analysis_status = _as_str(summary_obj.get("status")) or analysis_status

    if scanner_version is None:
        scanner_version = analyzer_version

    if scanner_name is None:
        scanner_name = "cisco-aibom"

    sources_obj = analysis_obj.get("sources")
    if not isinstance(sources_obj, dict):
        raise ValueError("AIBOM document has invalid sources format")

    parsed_sources: list[ParsedAIBOMSource] = []
    category_counter: Counter[str] = Counter()
    total_workflows = 0
    total_relationships = 0

    for source_key_raw, source_payload_obj in sources_obj.items():
        source_key = str(source_key_raw)
        if not isinstance(source_payload_obj, dict):
            logger.warning(
                "Skipping AIBOM source %s: expected dict, got %s",
                source_key,
                type(source_payload_obj).__name__,
            )
            continue

        source_summary = source_payload_obj.get("summary")
        if not isinstance(source_summary, dict):
            source_summary = {}
        source_status = _as_str(source_payload_obj.get("status")) or _as_str(
            source_summary.get("status"),
        )
        source_kind = _as_str(source_payload_obj.get("source_kind")) or _as_str(
            source_summary.get("source_kind"),
        )

        components, embedded_workflows = _parse_components(
            source_payload_obj.get("components"),
        )
        relationships = _parse_relationships(source_payload_obj.get("relationships"))

        workflows_by_id: dict[str, ParsedAIBOMWorkflow] = {}
        workflow_objects = source_payload_obj.get("workflows")
        if isinstance(workflow_objects, list):
            for workflow_obj in workflow_objects:
                if not isinstance(workflow_obj, dict):
                    continue
                workflow = _parse_workflow(workflow_obj)
                if workflow is None:
                    continue
                workflows_by_id[workflow.workflow_id] = workflow

        for workflow in embedded_workflows:
            workflows_by_id[workflow.workflow_id] = workflow

        source_category_counter = Counter(
            component.category for component in components
        )
        total_components = len(components)
        source_workflows = list(workflows_by_id.values())
        source_total_workflows = len(source_workflows)
        source_total_relationships = len(relationships)
        category_counter.update(source_category_counter)
        total_workflows += source_total_workflows
        total_relationships += source_total_relationships

        parsed_sources.append(
            ParsedAIBOMSource(
                source_key=source_key,
                source_status=source_status,
                source_kind=source_kind,
                total_components=total_components,
                total_workflows=source_total_workflows,
                total_relationships=source_total_relationships,
                category_summary_json=(
                    json.dumps(dict(source_category_counter), sort_keys=True)
                    if source_category_counter
                    else None
                ),
                components=components,
                workflows=source_workflows,
                relationships=relationships,
            ),
        )

    total_sources = 0
    if isinstance(summary_obj, dict) and isinstance(
        summary_obj.get("total_sources"), int
    ):
        total_sources = summary_obj["total_sources"]
    if not total_sources:
        total_sources = len(parsed_sources)

    return ParsedAIBOMDocument(
        image_uri=image_uri,
        report_location=report_location,
        scan_scope=scan_scope,
        scanner_name=scanner_name,
        scanner_version=scanner_version,
        analyzer_version=analyzer_version,
        analysis_status=analysis_status,
        total_sources=total_sources,
        total_components=sum(source.total_components for source in parsed_sources),
        total_workflows=total_workflows,
        total_relationships=total_relationships,
        category_summary_json=(
            json.dumps(dict(category_counter), sort_keys=True)
            if category_counter
            else None
        ),
        sources=parsed_sources,
    )
