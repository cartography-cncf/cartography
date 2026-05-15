import hashlib
import logging
from collections import Counter
from dataclasses import dataclass
from typing import Any

from cartography.intel.aibom.parser import ParsedAIBOMDocument

logger = logging.getLogger(__name__)

_RELATIONSHIP_TARGET_FIELD_BY_TYPE = {
    "USES_TOOL": "uses_tool_component_ids",
    "USES_LLM": "uses_model_component_ids",
    "USES_MODEL": "uses_model_component_ids",
    "USES_MEMORY": "uses_memory_component_ids",
    "USES_RETRIEVER": "uses_retriever_component_ids",
    "USES_EMBEDDING": "uses_embedding_component_ids",
    "USES_PROMPT": "uses_prompt_component_ids",
}

_NORMALIZED_RELATIONSHIP_TYPE_BY_SOURCE_TYPE = {
    "USES_LLM": "USES_MODEL",
}


@dataclass(frozen=True)
class TransformedAIBOMDocument:
    source_payloads: list[dict[str, Any]]
    component_payloads: list[dict[str, Any]]
    workflow_payloads: list[dict[str, Any]]
    component_category_counts: Counter[str]
    relationship_type_counts: Counter[str]


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _resolve_component_id(
    relationship_endpoint_instance_id: str | None,
    relationship_endpoint_name: str | None,
    relationship_endpoint_category: str | None,
    component_ids_by_instance_id: dict[str, str],
    component_ids_by_name_and_category: dict[tuple[str, str], str],
) -> str | None:
    if relationship_endpoint_instance_id:
        component_id = component_ids_by_instance_id.get(
            relationship_endpoint_instance_id,
        )
        if component_id:
            return component_id
    if relationship_endpoint_name and relationship_endpoint_category:
        return component_ids_by_name_and_category.get(
            (relationship_endpoint_name, relationship_endpoint_category),
        )
    return None


def _get_component_logical_identity_base(component: Any) -> str:
    return "|".join(
        [
            component.category,
            component.name,
            component.file_path or "",
            component.assigned_target or "",
            component.framework or "",
        ],
    )


def _get_component_logical_id(
    component: Any,
    duplicate_logical_identity_bases: set[str],
) -> str:
    logical_identity_parts = [
        component.category,
        component.name,
        component.file_path or "",
        component.assigned_target or "",
        component.framework or "",
    ]
    logical_identity_base = "|".join(logical_identity_parts)

    # When multiple components share the same stable callsite fields within a
    # single source, add a deterministic fallback to avoid collapsing distinct
    # detections that happen to look identical at the higher-level fingerprint.
    if logical_identity_base in duplicate_logical_identity_bases:
        logical_identity_parts.extend(
            [
                component.instance_id or "",
                str(component.line_number) if component.line_number is not None else "",
            ],
        )

    return _stable_hash("|".join(logical_identity_parts))


def transform_aibom_document(
    document: ParsedAIBOMDocument,
    manifest_digests: list[str],
) -> TransformedAIBOMDocument:
    source_payloads_by_id: dict[str, dict[str, Any]] = {}
    component_payloads_by_id: dict[str, dict[str, Any]] = {}
    workflow_payloads_by_id: dict[str, dict[str, Any]] = {}
    component_category_counts: Counter[str] = Counter()
    relationship_type_counts: Counter[str] = Counter()

    for source in document.sources:
        source_id = _stable_hash(
            "|".join(
                [
                    document.image_uri,
                    document.scanner_name or "",
                    document.scan_scope or "",
                    source.source_key,
                ],
            ),
        )
        source_component_ids: list[str] = []
        source_workflow_ids: list[str] = []
        workflow_id_map: dict[str, str] = {}
        component_ids_by_instance_id: dict[str, str] = {}
        component_ids_by_name_and_category: dict[tuple[str, str], str] = {}

        for workflow in source.workflows:
            workflow_hash = _stable_hash(f"{source_id}|{workflow.workflow_id}")
            workflow_id_map[workflow.workflow_id] = workflow_hash
            workflow_payloads_by_id[workflow_hash] = {
                "id": workflow_hash,
                "source_id": source_id,
                "workflow_id": workflow.workflow_id,
                "function": workflow.function,
                "file_path": workflow.file_path,
                "line": workflow.line,
                "distance": workflow.distance,
            }
            source_workflow_ids.append(workflow_hash)

        should_load_components = (
            source.source_status or "completed"
        ).lower() == "completed" and bool(manifest_digests)
        logical_identity_base_counts = Counter(
            _get_component_logical_identity_base(component)
            for component in source.components
        )
        duplicate_logical_identity_bases = {
            logical_identity_base
            for logical_identity_base, count in logical_identity_base_counts.items()
            if count > 1
        }
        for component in source.components:
            if not should_load_components:
                continue

            component_hash_input = "|".join(
                [
                    source_id,
                    component.category,
                    component.name,
                    component.file_path or "",
                    (
                        str(component.line_number)
                        if component.line_number is not None
                        else ""
                    ),
                    component.instance_id or "",
                ],
            )
            component_id = _stable_hash(component_hash_input)
            workflow_ids = [
                workflow_id_map[workflow_id]
                for workflow_id in component.workflow_ids
                if workflow_id in workflow_id_map
            ]

            if component_id not in component_payloads_by_id:
                component_category_counts[component.category] += 1

            component_payloads_by_id[component_id] = {
                "id": component_id,
                "logical_id": _get_component_logical_id(
                    component,
                    duplicate_logical_identity_bases,
                ),
                "name": component.name,
                "category": component.category,
                "instance_id": component.instance_id,
                "assigned_target": component.assigned_target,
                "file_path": component.file_path,
                "line_number": component.line_number,
                "model_name": component.model_name,
                "framework": component.framework,
                "label": component.label,
                "manifest_digests": manifest_digests,
                "workflow_ids": workflow_ids,
                "uses_tool_component_ids": [],
                "uses_model_component_ids": [],
                "uses_memory_component_ids": [],
                "uses_retriever_component_ids": [],
                "uses_embedding_component_ids": [],
                "uses_prompt_component_ids": [],
            }
            source_component_ids.append(component_id)

            if component.instance_id:
                component_ids_by_instance_id[component.instance_id] = component_id
            component_ids_by_name_and_category[(component.name, component.category)] = (
                component_id
            )

        for relationship in source.relationships:
            if not should_load_components:
                continue

            source_component_id = _resolve_component_id(
                relationship.source_instance_id,
                relationship.source_name,
                relationship.source_category,
                component_ids_by_instance_id,
                component_ids_by_name_and_category,
            )
            target_component_id = _resolve_component_id(
                relationship.target_instance_id,
                relationship.target_name,
                relationship.target_category,
                component_ids_by_instance_id,
                component_ids_by_name_and_category,
            )

            if not source_component_id or not target_component_id:
                logger.warning(
                    "Skipping unresolved AIBOM relationship %s between %s and %s",
                    relationship.relationship_type,
                    relationship.source_instance_id or relationship.source_name,
                    relationship.target_instance_id or relationship.target_name,
                )
                continue

            relationship_field = _RELATIONSHIP_TARGET_FIELD_BY_TYPE.get(
                relationship.relationship_type,
            )
            if relationship_field is None:
                logger.info(
                    "Skipping unsupported AIBOM relationship type %s",
                    relationship.relationship_type,
                )
                continue

            source_component_payload = component_payloads_by_id[source_component_id]
            target_component_ids = source_component_payload[relationship_field]
            if target_component_id not in target_component_ids:
                target_component_ids.append(target_component_id)

            normalized_relationship_type = (
                _NORMALIZED_RELATIONSHIP_TYPE_BY_SOURCE_TYPE.get(
                    relationship.relationship_type,
                    relationship.relationship_type,
                )
            )
            relationship_type_counts[normalized_relationship_type] += 1

        source_payloads_by_id[source_id] = {
            "id": source_id,
            "image_uri": document.image_uri,
            "manifest_digests": manifest_digests,
            "image_matched": bool(manifest_digests),
            "scan_scope": document.scan_scope,
            "report_location": document.report_location,
            "scanner_name": document.scanner_name,
            "scanner_version": document.scanner_version,
            "analyzer_version": document.analyzer_version,
            "analysis_status": document.analysis_status,
            "report_total_sources": document.total_sources,
            "report_total_components": document.total_components,
            "report_total_workflows": document.total_workflows,
            "report_total_relationships": document.total_relationships,
            "report_category_summary_json": document.category_summary_json,
            "source_key": source.source_key,
            "source_status": source.source_status,
            "source_kind": source.source_kind,
            "total_components": source.total_components,
            "total_workflows": source.total_workflows,
            "total_relationships": source.total_relationships,
            "category_summary_json": source.category_summary_json,
            "component_ids": sorted(set(source_component_ids)),
            "workflow_ids": sorted(set(source_workflow_ids)),
        }

    return TransformedAIBOMDocument(
        source_payloads=list(source_payloads_by_id.values()),
        component_payloads=list(component_payloads_by_id.values()),
        workflow_payloads=list(workflow_payloads_by_id.values()),
        component_category_counts=component_category_counts,
        relationship_type_counts=relationship_type_counts,
    )
