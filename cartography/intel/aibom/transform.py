import hashlib
import json
import logging
from typing import Any
from typing import cast

logger = logging.getLogger(__name__)

_RELATIONSHIP_TARGET_FIELD_BY_TYPE = {
    "USES_MODEL": "uses_model_component_ids",
    "USES_TOOL": "uses_tool_component_ids",
    "EXPOSES_TOOL": "exposes_tool_component_ids",
    "CUSTOM": "custom_component_ids",
}


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _as_str(value: Any) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned
    return None


def _json_dumps(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, sort_keys=True)


def _flatten_count_map(
    value: Any,
) -> tuple[list[str], list[int]]:
    if value is None:
        return [], []

    keys: list[str] = []
    counts: list[int] = []
    for key in sorted(value):
        count = value.get(key)
        keys.append(key)
        counts.append(count)
    return keys, counts


def _build_component_id(source_key: str, component: dict[str, Any]) -> str:
    return _stable_hash(
        "|".join(
            [
                source_key,
                _as_str(component.get("component_type")) or "unknown",
                _as_str(component.get("name")) or "",
                _as_str(component.get("file_path")) or "",
                str(component.get("line_number") or ""),
                _as_str(component.get("instance_id")) or "",
            ],
        ),
    )


def _build_component_logical_id(component: dict[str, Any]) -> str:
    return _stable_hash(
        "|".join(
            [
                _as_str(component.get("component_type")) or "unknown",
                _as_str(component.get("name")) or "",
                _as_str(component.get("file_path")) or "",
                _as_str(component.get("framework")) or "",
                _as_str(component.get("model_name")) or "",
                _as_str(component.get("storage_uri")) or "",
                _as_str(component.get("skill_format")) or "",
            ],
        ),
    )


def _build_component_payload(
    source_key: str,
    component_type: str,
    component: dict[str, Any],
) -> dict[str, Any]:
    digest = source_key.partition("@")[2]
    manifest_digests = [digest] if digest else []
    normalized_component_type = (
        _as_str(component.get("component_type")) or component_type
    )
    decision_annotation = component.get("decision_annotation") or {}
    component_metadata = component.get("metadata") or {}
    evidence_locations = decision_annotation.get("evidence_locations") or []
    component_primary_evidence = None
    component_primary_evidence_start_line = None
    component_primary_evidence_end_line = None
    for evidence_location in evidence_locations:
        component_primary_evidence = _as_str(evidence_location.get("file_path"))
        component_primary_evidence_start_line = evidence_location.get("start_line")
        component_primary_evidence_end_line = evidence_location.get("end_line")
        # Take the first location of evidence as the primary evidence for the component.
        if component_primary_evidence:
            break

    return {
        "id": _build_component_id(source_key, component),
        "logical_id": _build_component_logical_id(component),
        "name": _as_str(component.get("name")),
        "category": normalized_component_type,
        "component_type": normalized_component_type,
        "instance_id": _as_str(component.get("instance_id")),
        "file_path": _as_str(component.get("file_path")),
        "line_number": component.get("line_number"),
        "model_name": _as_str(component.get("model_name")),
        "embedding_model": _as_str(component.get("embedding_model")),
        "framework": _as_str(component.get("framework")),
        "detection_source": _as_str(component.get("detection_source")),
        "confidence": component.get("confidence"),
        "heuristic_confidence": component.get("heuristic_confidence"),
        "agentic_confidence": component.get("agentic_confidence"),
        "needs_agentic": component.get("needs_agentic"),
        "agentic_hint": _as_str(component.get("agentic_hint")),
        "description": _as_str(component.get("description")),
        "text": _as_str(component.get("text")),
        "transport": _as_str(component.get("transport")),
        "config_source": _as_str(component.get("config_source")),
        "storage_uri": _as_str(component.get("storage_uri")),
        "dataset_source": _as_str(component.get("dataset_source")),
        "skill_format": _as_str(component.get("skill_format")),
        "sdk_version": _as_str(component.get("sdk_version")),
        "kb_concept": _as_str(component.get("kb_concept")),
        "kb_label": _as_str(component.get("kb_label")),
        "component_primary_evidence": component_primary_evidence,
        "component_primary_evidence_start_line": component_primary_evidence_start_line,
        "component_primary_evidence_end_line": component_primary_evidence_end_line,
        "decision": _as_str(decision_annotation.get("decision")),
        "decision_justification": _as_str(decision_annotation.get("justification")),
        "metadata_json": _json_dumps(component_metadata),
        "manifest_digests": manifest_digests,
        "uses_model_component_ids": [],
        "uses_tool_component_ids": [],
        "exposes_tool_component_ids": [],
        "custom_component_ids": [],
    }


def _build_source_component_ids(
    source_key: str,
    source_components: Any,
) -> list[str]:
    component_ids: list[str] = []
    for items in source_components.values():
        for component in items:
            component_ids.append(_build_component_id(source_key, component))

    return component_ids


def _build_source_payload(
    source_key: str,
    source_data: dict[str, Any],
    analysis: dict[str, Any],
    report_location: str | None,
) -> dict[str, Any]:
    report_metadata = analysis.get("metadata", {})
    report_summary = analysis.get("summary", {})
    report_risk = analysis.get("risk")

    source_summary = source_data.get("summary", {})
    source_metadata = source_data.get("metadata", {})
    source_components = source_data.get("components", {})
    source_relationships = source_data.get("relationships", [])
    component_ids = _build_source_component_ids(source_key, source_components)

    report_component_types = report_summary.get("component_types")
    source_component_counts = {
        category: len(items) for category, items in source_components.items()
    }

    total_components = source_summary.get("assets_discovered")
    if total_components is None:
        total_components = sum(source_component_counts.values())

    total_relationships = len(source_relationships)

    digest = source_key.partition("@")[2]
    manifest_digests = [digest] if digest else []
    image_uri = _as_str(source_data.get("source_name")) or source_key
    report_component_type_names, report_component_type_counts = _flatten_count_map(
        report_component_types,
    )
    source_component_type_names, source_component_type_counts = _flatten_count_map(
        source_component_counts,
    )

    return {
        "id": _stable_hash(source_key),
        "image_uri": image_uri,
        "manifest_digests": manifest_digests,
        "image_matched": bool(manifest_digests),
        "report_location": report_location,
        "run_id": _as_str(report_metadata.get("run_id")),
        "analyzer_version": _as_str(report_metadata.get("analyzer_version")),
        "analysis_status": _as_str(report_metadata.get("status")),
        "report_schema_version": _as_str(report_metadata.get("report_schema_version")),
        "report_started_at": _as_str(report_metadata.get("started_at")),
        "report_completed_at": _as_str(report_metadata.get("completed_at")),
        "report_output_format": _as_str(report_metadata.get("output_format")),
        "llm_model": _as_str(report_metadata.get("llm_model")),
        "sources_requested": report_metadata.get("sources_requested"),
        "sources_analyzed": report_metadata.get("sources_analyzed"),
        "sources_with_errors": report_metadata.get("sources_with_errors"),
        "error_count": report_metadata.get("error_count"),
        "prompt_tokens": report_metadata.get("prompt_tokens"),
        "completion_tokens": report_metadata.get("completion_tokens"),
        "total_tokens": report_metadata.get("total_tokens"),
        "report_total_sources": report_summary.get("total_sources"),
        "report_total_components": report_summary.get("total_components"),
        "report_total_relationships": report_summary.get("total_relationships"),
        "pending_agent_review": report_summary.get("pending_agent_review"),
        "test_only_components": report_summary.get("test_only_components"),
        "report_component_types": report_component_type_names,
        "report_component_type_counts": report_component_type_counts,
        "risk_score": report_summary.get("risk_score")
        or (report_risk or {}).get("score"),
        "risk_severity": _as_str(report_summary.get("risk_severity"))
        or _as_str((report_risk or {}).get("severity")),
        "source_key": source_key,
        "source_name": _as_str(source_data.get("source_name")) or source_key,
        "source_path": _as_str(source_data.get("source_path")),
        "source_status": _as_str(source_summary.get("status")),
        "source_kind": _as_str(source_summary.get("source_kind")),
        "total_components": total_components,
        "total_relationships": total_relationships,
        "assets_discovered": source_summary.get("assets_discovered"),
        "last_generated_at": _as_str(source_summary.get("last_generated_at")),
        "source_elapsed_s": source_metadata.get("elapsed_s"),
        "source_prompt_tokens": source_metadata.get("prompt_tokens"),
        "source_completion_tokens": source_metadata.get("completion_tokens"),
        "source_total_tokens": source_metadata.get("total_tokens"),
        "source_component_types": source_component_type_names,
        "source_component_type_counts": source_component_type_counts,
        "component_ids": component_ids,
    }


def transform_aibom_source_payloads(
    document: dict[str, Any],
    report_location: str | None = None,
) -> list[dict[str, Any]]:
    """
    Transform raw AIBOM rc4 source data into AIBOMSource payloads.
    """
    analysis = document["aibom_analysis"]
    sources = analysis.get("sources")

    payloads: list[dict[str, Any]] = []
    for source_key, source_data in sources.items():
        payloads.append(
            _build_source_payload(
                source_key,
                source_data,
                analysis,
                report_location,
            ),
        )

    return payloads


def _parse_aibom_component_records(document: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract raw component records from the AIBOM rc4 report.

    This is the component-specific traversal step that finds component nodes in
    the report and preserves the source context needed for downstream transforms.
    """
    analysis = document["aibom_analysis"]
    sources = analysis.get("sources")

    component_records: list[dict[str, Any]] = []
    for source_key, source_data in sources.items():
        components = source_data.get("components", {})

        for component_type, items in components.items():
            for component in items:
                component_records.append(
                    {
                        "source_key": source_key,
                        "component_type": component_type,
                        "component": component,
                    },
                )

    return component_records


def _parse_aibom_relationship_records(document: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract raw relationship records from the AIBOM rc4 report.
    """
    analysis = document["aibom_analysis"]
    sources = analysis.get("sources")

    relationship_records: list[dict[str, Any]] = []
    for source_key, source_data in sources.items():
        relationships = source_data.get("relationships", [])

        for relationship in relationships:
            relationship_records.append(
                {
                    "source_key": source_key,
                    "relationship": relationship,
                },
            )

    return relationship_records


def _build_relationship_component_lookup(
    component_records: list[dict[str, Any]],
) -> tuple[dict[tuple[str, ...], str], set[tuple[str, str, str]]]:
    """
    Build a mixed-shape endpoint lookup for relationship resolution.

    Keys are tuples scoped by source key and map to the stable
    AIBOMComponent.id values derived during transform:
    - (source_key, instance_id) for relationship endpoints that provide
      source_instance_id/target_instance_id.
    - (source_key, component_type, component_name) for fallback endpoints
      resolved by type/name.

    Returns:
    - component_lookup: maps either key shape above to AIBOMComponent.id.
    - ambiguous_type_name_keys: the subset of (source_key, component_type,
      component_name) keys that map to multiple component ids and therefore
      must not be used for fallback resolution.
    """
    component_lookup: dict[tuple[str, ...], str] = {}
    ambiguous_type_name_keys: set[tuple[str, str, str]] = set()
    for component_record in component_records:
        source_key = component_record["source_key"]
        component_type = component_record["component_type"]
        component = component_record["component"]
        component_id = _build_component_id(source_key, component)

        component_instance_id = _as_str(component.get("instance_id"))
        if component_instance_id:
            component_lookup[(source_key, component_instance_id)] = component_id

        normalized_component_type = (
            _as_str(component.get("component_type")) or component_type
        )
        component_name = _as_str(component.get("name")) or ""
        type_name_key = (
            source_key,
            normalized_component_type,
            component_name,
        )
        existing_id = component_lookup.get(type_name_key)
        if existing_id is not None and existing_id != component_id:
            ambiguous_type_name_keys.add(type_name_key)
        component_lookup[type_name_key] = component_id

    return component_lookup, ambiguous_type_name_keys


def _build_component_payloads_by_id(
    component_records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    component_payloads_by_id: dict[str, dict[str, Any]] = {}

    for component_record in component_records:
        source_key = component_record["source_key"]
        component_type = component_record["component_type"]
        component = component_record["component"]
        component_payload = _build_component_payload(
            source_key,
            component_type,
            component,
        )
        component_payloads_by_id[cast(str, component_payload["id"])] = component_payload

    return component_payloads_by_id


def _resolve_relationship_component_ids(
    source_key: str,
    relationship: dict[str, Any],
    component_lookup: dict[tuple[str, ...], str],
    source_component_lookup_key: tuple[str, ...],
    target_component_lookup_key: tuple[str, ...],
    ambiguous_type_name_keys: set[tuple[str, str, str]],
) -> tuple[str, str] | None:
    """
    Resolve source/target component ids for one relationship endpoint pair.

    The caller precomputes lookup keys per relationship, preferring
    `(source_key, instance_id)` when both instance ids are present and falling
    back to `(source_key, component_type, component_name)` otherwise.
    Fallback keys marked ambiguous are rejected to avoid silently choosing the
    wrong endpoint.
    """
    if (
        source_component_lookup_key in ambiguous_type_name_keys
        or target_component_lookup_key in ambiguous_type_name_keys
    ):
        relationship_type = _as_str(relationship.get("relationship_type"))
        logger.warning(
            "Skipping ambiguous AIBOM relationship %s on source %s: %s -> %s",
            relationship_type,
            source_key,
            relationship.get("source_name"),
            relationship.get("target_name"),
        )
        return None

    source_component_id = component_lookup.get(source_component_lookup_key)
    target_component_id = component_lookup.get(target_component_lookup_key)
    if not source_component_id or not target_component_id:
        relationship_type = _as_str(relationship.get("relationship_type"))
        logger.warning(
            "Skipping unresolved AIBOM relationship %s on source %s: %s -> %s",
            relationship_type,
            source_key,
            relationship.get("source_name"),
            relationship.get("target_name"),
        )
        return None

    return source_component_id, target_component_id


def transform_aibom_component_payloads(
    document: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Transform raw AIBOM rc4 component data into AIBOMComponent payloads.

    This consumes the raw AIBOM report, extracts component records, resolves
    report relationships onto component ids, and emits schema-ready component
    payloads.
    """
    component_records = _parse_aibom_component_records(document)
    component_payloads_by_id = _build_component_payloads_by_id(component_records)
    component_lookup, ambiguous_type_name_keys = _build_relationship_component_lookup(
        component_records,
    )
    relationship_records = _parse_aibom_relationship_records(document)

    for relationship_record in relationship_records:
        source_key = relationship_record["source_key"]
        relationship = relationship_record["relationship"]
        relationship_type = _as_str(relationship.get("relationship_type"))
        if relationship_type is None:
            continue
        source_component_lookup_key: tuple[str, ...]
        target_component_lookup_key: tuple[str, ...]
        # Prefer instance-id endpoint matching when both endpoint ids are
        # present; otherwise fall back to type/name endpoint matching.
        source_instance_id = _as_str(relationship.get("source_instance_id"))
        target_instance_id = _as_str(relationship.get("target_instance_id"))
        if source_instance_id and target_instance_id:
            source_component_lookup_key = (source_key, source_instance_id)
            target_component_lookup_key = (source_key, target_instance_id)
        else:
            source_component_lookup_key = (
                source_key,
                _as_str(relationship.get("source_type")) or "",
                _as_str(relationship.get("source_name")) or "",
            )
            target_component_lookup_key = (
                source_key,
                _as_str(relationship.get("target_type")) or "",
                _as_str(relationship.get("target_name")) or "",
            )

        target_field = _RELATIONSHIP_TARGET_FIELD_BY_TYPE.get(relationship_type)
        if target_field is None:
            logger.info(
                "Skipping unsupported AIBOM relationship type %s",
                relationship_type,
            )
            continue

        resolved_component_ids = _resolve_relationship_component_ids(
            source_key,
            relationship,
            component_lookup,
            source_component_lookup_key=source_component_lookup_key,
            target_component_lookup_key=target_component_lookup_key,
            ambiguous_type_name_keys=ambiguous_type_name_keys,
        )
        if resolved_component_ids is None:
            continue

        source_component_id, target_component_id = resolved_component_ids
        source_component_payload = component_payloads_by_id.get(source_component_id)
        if source_component_payload is None:
            continue

        target_component_ids = cast(list[str], source_component_payload[target_field])
        if target_component_id not in target_component_ids:
            target_component_ids.append(target_component_id)

    return list(component_payloads_by_id.values())
