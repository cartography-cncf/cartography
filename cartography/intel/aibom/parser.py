import os
from dataclasses import dataclass
from typing import Any


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
    image_uri: str | None
    source_status: str | None
    scanner_name: str | None
    scanner_version: str | None
    scan_scope: str | None
    skip_reason: str | None
    components: list[ParsedAIBOMComponent]
    workflows: list[ParsedAIBOMWorkflow]


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _as_str(value: Any) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned
    return None


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
    return None


def _looks_like_local_path(value: str) -> bool:
    if value.startswith("file://"):
        return True
    if os.path.isabs(value):
        return True
    return value.startswith("./") or value.startswith("../")


def _parse_workflow(workflow: dict[str, Any]) -> ParsedAIBOMWorkflow | None:
    workflow_id = _as_str(workflow.get("id")) or _as_str(workflow.get("workflow_id"))
    if not workflow_id:
        return None
    return ParsedAIBOMWorkflow(
        workflow_id=workflow_id,
        function=_as_str(workflow.get("function")),
        file_path=_as_str(workflow.get("file_path")),
        line=_as_int(workflow.get("line")),
        distance=_as_int(workflow.get("distance")),
    )


def _parse_component(
    component: dict[str, Any],
    category_hint: str | None,
) -> tuple[ParsedAIBOMComponent | None, list[ParsedAIBOMWorkflow]]:
    name = _as_str(component.get("name"))
    if not name:
        return None, []

    category = _as_str(component.get("category")) or category_hint or "unknown"

    embedded_workflows: list[ParsedAIBOMWorkflow] = []
    workflow_ids: list[str] = []
    for workflow_obj in _as_list(component.get("workflows")):
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
        line_number=_as_int(component.get("line_number")),
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
                continue
            parsed_component, parsed_workflows = _parse_component(component_obj, None)
            if parsed_component is not None:
                components.append(parsed_component)
            embedded_workflows.extend(parsed_workflows)
        return components, embedded_workflows

    if not isinstance(components_obj, dict):
        return components, embedded_workflows

    for category, category_components_obj in components_obj.items():
        category_hint = _as_str(category)
        for component_obj in _as_list(category_components_obj):
            if not isinstance(component_obj, dict):
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
    report_document = document
    image_uri_override = _as_str(document.get("image_uri"))
    scan_scope = _as_str(document.get("scan_scope"))

    scanner_name: str | None = None
    scanner_version: str | None = None

    scanner_obj = _as_dict(document.get("scanner"))
    if scanner_obj:
        scanner_name = _as_str(scanner_obj.get("name"))
        scanner_version = _as_str(scanner_obj.get("version"))

    report_obj = document.get("report")
    if isinstance(report_obj, dict):
        report_document = report_obj

    analysis_obj = _as_dict(report_document.get("aibom_analysis"))
    if not analysis_obj:
        raise ValueError("AIBOM document is missing aibom_analysis")

    if scanner_version is None:
        metadata_obj = _as_dict(analysis_obj.get("metadata"))
        scanner_version = _as_str(metadata_obj.get("analyzer_version"))

    if scanner_name is None:
        scanner_name = "cisco-aibom"

    sources_obj = analysis_obj.get("sources")
    if not isinstance(sources_obj, dict):
        raise ValueError("AIBOM document has invalid sources format")

    parsed_sources: list[ParsedAIBOMSource] = []

    for source_key_raw, source_payload_obj in sources_obj.items():
        source_key = str(source_key_raw)
        source_payload = _as_dict(source_payload_obj)

        source_summary = _as_dict(source_payload.get("summary"))
        source_status = _as_str(source_payload.get("status")) or _as_str(
            source_summary.get("status")
        )

        image_uri = image_uri_override
        skip_reason: str | None = None
        if image_uri is None:
            if _looks_like_local_path(source_key):
                skip_reason = "source_key_is_local_path"
            else:
                image_uri = source_key

        components, embedded_workflows = _parse_components(
            source_payload.get("components"),
        )

        workflows_by_id: dict[str, ParsedAIBOMWorkflow] = {}
        for workflow_obj in _as_list(source_payload.get("workflows")):
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
                skip_reason=skip_reason,
                components=components,
                workflows=list(workflows_by_id.values()),
            )
        )

    return parsed_sources
