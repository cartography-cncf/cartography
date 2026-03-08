import logging
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
class ParsedAIBOMComponent:
    name: str
    category: str
    instance_id: str | None
    assigned_target: str | None
    file_path: str | None
    line_number: int | None
    workflow_ids: list[str]


@dataclass(frozen=True)
class ParsedAIBOMSource:
    source_key: str
    image_uri: str
    source_status: str | None
    scanner_name: str | None
    scanner_version: str | None
    scan_scope: str | None
    components: list[ParsedAIBOMComponent]
    workflows: list[ParsedAIBOMWorkflow]


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
        workflow_ids=workflow_ids,
    )
    return parsed_component, embedded_workflows


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


def parse_aibom_document(
    document: dict[str, Any],
) -> list[ParsedAIBOMSource]:
    image_uri = _as_str(document.get("image_uri"))
    if not image_uri:
        raise ValueError("AIBOM envelope is missing required image_uri field")

    scan_scope = _as_str(document.get("scan_scope"))

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

    if scanner_version is None:
        metadata_obj = analysis_obj.get("metadata")
        if isinstance(metadata_obj, dict):
            scanner_version = _as_str(metadata_obj.get("analyzer_version"))

    if scanner_name is None:
        scanner_name = "cisco-aibom"

    sources_obj = analysis_obj.get("sources")
    if not isinstance(sources_obj, dict):
        raise ValueError("AIBOM document has invalid sources format")

    parsed_sources: list[ParsedAIBOMSource] = []

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

        components, embedded_workflows = _parse_components(
            source_payload_obj.get("components"),
        )

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

        parsed_sources.append(
            ParsedAIBOMSource(
                source_key=source_key,
                image_uri=image_uri,
                source_status=source_status,
                scanner_name=scanner_name,
                scanner_version=scanner_version,
                scan_scope=scan_scope,
                components=components,
                workflows=list(workflows_by_id.values()),
            ),
        )

    return parsed_sources
