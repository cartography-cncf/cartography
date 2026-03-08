import hashlib
import logging
from collections import Counter
from typing import Any

from neo4j import Session

from cartography.client.core.tx import load
from cartography.intel.aibom.parser import ParsedAIBOMSource
from cartography.models.aibom import AIBOMComponentSchema
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
        return digest

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


def load_aibom_sources(
    neo4j_session: Session,
    sources: list[ParsedAIBOMSource],
    update_tag: int,
) -> None:
    workflow_payloads_by_id: dict[str, dict[str, Any]] = {}
    component_payloads_by_id: dict[str, dict[str, Any]] = {}
    component_category_counts: Counter[str] = Counter()

    for source in sources:
        stat_handler.incr("aibom_sources_total")

        source_status = (source.source_status or "completed").lower()
        if source_status != "completed":
            stat_handler.incr("aibom_sources_skipped_incomplete")
            logger.info(
                "Skipping AIBOM source %s because status is %s",
                source.source_key,
                source_status,
            )
            continue

        if source.image_uri is None:
            logger.warning(
                "Skipping AIBOM source %s because no image URI was resolved (%s)",
                source.source_key,
                source.skip_reason,
            )
            stat_handler.incr("aibom_sources_unmatched")
            continue

        # Transform: resolve image URI to an ECRImage digest.
        # For digest-based URIs (repo@sha256:...) this is pure string
        # splitting. For tag-based URIs it falls back to a graph lookup.
        # The data model (AIBOMComponentDetectedInRel) handles the actual
        # relationship creation via ECRImage.digest == manifest_digest.
        manifest_digest = _resolve_digest_for_source(
            neo4j_session,
            source.image_uri,
        )
        if not manifest_digest:
            logger.warning(
                "Skipping AIBOM source %s (image URI %s): could not resolve digest",
                source.source_key,
                source.image_uri,
            )
            stat_handler.incr("aibom_sources_unmatched")
            continue

        stat_handler.incr("aibom_sources_matched")

        workflow_id_map: dict[str, str] = {}
        for workflow in source.workflows:
            workflow_hash = _stable_hash(f"{manifest_digest}|{workflow.workflow_id}")
            workflow_id_map[workflow.workflow_id] = workflow_hash
            workflow_payloads_by_id[workflow_hash] = {
                "id": workflow_hash,
                "workflow_id": workflow.workflow_id,
                "function": workflow.function,
                "file_path": workflow.file_path,
                "line": workflow.line,
                "distance": workflow.distance,
            }

        for component in source.components:
            component_hash_input = "|".join(
                [
                    manifest_digest,
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
                "source_image_uri": source.image_uri,
                "scanner_name": source.scanner_name,
                "scanner_version": source.scanner_version,
                "scan_scope": source.scan_scope,
                "manifest_digest": manifest_digest,
                "workflow_ids": workflow_ids,
            }

    # Load phase: Cartography's load() builds the ingestion query from
    # the schema, creates indexes, and handles batching automatically.
    # The DETECTED_IN relationship to ECRImage is created by the model
    # via AIBOMComponentDetectedInRel matching ECRImage.digest == manifest_digest.
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

    for category, count in component_category_counts.items():
        stat_handler.incr(f"aibom_components_loaded_{category}", count)
