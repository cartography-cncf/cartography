import hashlib
import logging
from collections import Counter
from typing import Any

from neo4j import Session

from cartography.client.core.tx import load
from cartography.intel.aibom.parser import ParsedAIBOMDocument
from cartography.models.aibom import AIBOMComponentSchema
from cartography.models.aibom import AIBOMRelationshipSchema
from cartography.models.aibom import AIBOMScanSchema
from cartography.models.aibom import AIBOMSourceSchema
from cartography.models.aibom import AIBOMWorkflowSchema
from cartography.stats import get_stats_client

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _extract_digest(image_uri: str) -> str | None:
    """Extract the digest from an image URI.

    Handles both digest-based URIs (repo@sha256:abc → sha256:abc)
    and plain digest strings. Returns None if no digest is found.
    """
    if "@" in image_uri:
        return image_uri.split("@", 1)[1]
    return None


def _resolve_digest_for_source(
    neo4j_session: Session,
    image_uri: str,
) -> str | None:
    """Resolve an image URI to an ECRImage digest.

    For digest-based URIs (repo@sha256:...), extracts the digest directly.
    For tag-based URIs (repo:tag), looks up via ECRRepositoryImage → ECRImage.

    Returns the digest string or None if no match is found.
    """
    # Fast path: digest is in the URI itself
    digest = _extract_digest(image_uri)
    if digest:
        # Verify the digest actually exists in the graph before accepting it.
        exists = neo4j_session.run(
            "MATCH (img:ECRImage {digest: $digest}) RETURN img.digest LIMIT 1",
            digest=digest,
        ).single()
        return digest if exists else None

    # Slow path: tag-based URI, need to resolve via the graph
    row = neo4j_session.run(
        """
        MATCH (:ECRRepositoryImage {id: $image_uri})-[:IMAGE]->(img:ECRImage)
        WHERE img.type IN ['manifest_list', 'image']
        RETURN img.digest AS digest, img.type AS type
        ORDER BY CASE img.type WHEN 'manifest_list' THEN 0 ELSE 1 END
        LIMIT 1
        """,
        image_uri=image_uri,
    ).single()

    if row:
        return row["digest"]
    return None


def _resolve_component_id(
    relationship_endpoint_instance_id: str | None,
    relationship_endpoint_name: str | None,
    relationship_endpoint_category: str | None,
    component_ids_by_instance_id: dict[str, str],
    component_ids_by_name_and_category: dict[tuple[str, str], str],
) -> str | None:
    if relationship_endpoint_instance_id:
        component_id = component_ids_by_instance_id.get(
            relationship_endpoint_instance_id
        )
        if component_id:
            return component_id
    if relationship_endpoint_name and relationship_endpoint_category:
        return component_ids_by_name_and_category.get(
            (relationship_endpoint_name, relationship_endpoint_category),
        )
    return None


def load_aibom_document(
    neo4j_session: Session,
    document: ParsedAIBOMDocument,
    update_tag: int,
) -> None:
    manifest_digest = _resolve_digest_for_source(
        neo4j_session,
        document.image_uri,
    )
    scan_identity_value = manifest_digest or document.image_uri
    scan_id = _stable_hash(
        "|".join(
            [
                scan_identity_value,
                document.scanner_name or "",
                document.scan_scope or "",
            ]
        ),
    )

    scan_payload = {
        "id": scan_id,
        "image_uri": document.image_uri,
        "manifest_digest": manifest_digest,
        "image_matched": bool(manifest_digest),
        "scan_scope": document.scan_scope,
        "report_location": document.report_location,
        "scanner_name": document.scanner_name,
        "scanner_version": document.scanner_version,
        "analyzer_version": document.analyzer_version,
        "analysis_status": document.analysis_status,
        "total_sources": document.total_sources,
        "total_components": document.total_components,
        "total_workflows": document.total_workflows,
        "total_relationships": document.total_relationships,
        "category_summary_json": document.category_summary_json,
    }

    source_payloads_by_id: dict[str, dict[str, Any]] = {}
    component_payloads_by_id: dict[str, dict[str, Any]] = {}
    relationship_payloads_by_id: dict[str, dict[str, Any]] = {}
    component_category_counts: Counter[str] = Counter()
    relationship_type_counts: Counter[str] = Counter()
    workflow_payloads_by_id: dict[str, dict[str, Any]] = {}

    for source in document.sources:
        stat_handler.incr("aibom_sources_total")

        source_id = _stable_hash(f"{scan_id}|{source.source_key}")
        source_component_ids: list[str] = []
        source_workflow_ids: list[str] = []
        source_relationship_ids: list[str] = []

        source_status = (source.source_status or "completed").lower()
        if source_status == "completed" and manifest_digest:
            stat_handler.incr("aibom_sources_matched")
        elif source_status != "completed":
            stat_handler.incr("aibom_sources_skipped_incomplete")
            logger.info(
                "AIBOM source %s has non-completed status %s; loading provenance only",
                source.source_key,
                source_status,
            )
        else:
            stat_handler.incr("aibom_sources_unmatched")
            logger.warning(
                "AIBOM source %s (image URI %s) could not resolve digest; loading provenance only",
                source.source_key,
                document.image_uri,
            )

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

        should_load_components = source_status == "completed" and bool(manifest_digest)
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
                ]
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
                "name": component.name,
                "category": component.category,
                "instance_id": component.instance_id,
                "assigned_target": component.assigned_target,
                "file_path": component.file_path,
                "line_number": component.line_number,
                "model_name": component.model_name,
                "framework": component.framework,
                "label": component.label,
                "metadata_json": component.metadata_json,
                "manifest_digest": manifest_digest,
                "workflow_ids": workflow_ids,
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

            relationship_id = _stable_hash(
                "|".join(
                    [
                        source_id,
                        relationship.relationship_type,
                        source_component_id,
                        target_component_id,
                    ]
                ),
            )
            relationship_payloads_by_id[relationship_id] = {
                "id": relationship_id,
                "relationship_type": relationship.relationship_type,
                "source_component_id": source_component_id,
                "target_component_id": target_component_id,
                "raw_source_instance_id": relationship.source_instance_id,
                "raw_target_instance_id": relationship.target_instance_id,
                "raw_source_name": relationship.source_name,
                "raw_target_name": relationship.target_name,
                "raw_source_category": relationship.source_category,
                "raw_target_category": relationship.target_category,
            }
            source_relationship_ids.append(relationship_id)
            relationship_type_counts[relationship.relationship_type] += 1

        source_payloads_by_id[source_id] = {
            "id": source_id,
            "scan_id": scan_id,
            "source_key": source.source_key,
            "source_status": source.source_status,
            "source_kind": source.source_kind,
            "total_components": source.total_components,
            "total_workflows": source.total_workflows,
            "total_relationships": source.total_relationships,
            "category_summary_json": source.category_summary_json,
            "component_ids": sorted(set(source_component_ids)),
            "workflow_ids": sorted(set(source_workflow_ids)),
            "relationship_ids": sorted(set(source_relationship_ids)),
        }

    load(
        neo4j_session,
        AIBOMScanSchema(),
        [scan_payload],
        lastupdated=update_tag,
    )

    workflows = list(workflow_payloads_by_id.values())
    if workflows:
        load(
            neo4j_session,
            AIBOMWorkflowSchema(),
            workflows,
            lastupdated=update_tag,
        )

    components = list(component_payloads_by_id.values())
    if components:
        load(
            neo4j_session,
            AIBOMComponentSchema(),
            components,
            lastupdated=update_tag,
        )

    relationships = list(relationship_payloads_by_id.values())
    if relationships:
        load(
            neo4j_session,
            AIBOMRelationshipSchema(),
            relationships,
            lastupdated=update_tag,
        )

    sources = list(source_payloads_by_id.values())
    if sources:
        load(
            neo4j_session,
            AIBOMSourceSchema(),
            sources,
            lastupdated=update_tag,
        )

    for category, count in component_category_counts.items():
        stat_handler.incr(f"aibom_components_loaded_{category}", count)
    for relationship_type, count in relationship_type_counts.items():
        stat_handler.incr(
            f"aibom_relationships_loaded_{relationship_type.lower()}",
            count,
        )
