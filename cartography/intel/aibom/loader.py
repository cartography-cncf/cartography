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


def resolve_manifest_list_digests(
    neo4j_session: Session,
    image_uris: list[str],
) -> dict[str, list[dict[str, str]]]:
    if not image_uris:
        return {}

    query = """
    UNWIND $image_uris AS image_uri

    // Try tag-based lookup: ECRRepositoryImage.id == image_uri
    OPTIONAL MATCH (:ECRRepositoryImage {id: image_uri})-[:IMAGE]->(tag_img:ECRImage)
    WHERE tag_img.type IN ['manifest_list', 'image']
    WITH image_uri, collect(tag_img) AS tag_matches

    // If tag-based found nothing, try digest-based: repo@sha256:... -> ECRImage.digest
    CALL {
        WITH image_uri, tag_matches
        WITH image_uri, tag_matches WHERE size(tag_matches) = 0 AND image_uri CONTAINS '@'
        MATCH (digest_img:ECRImage)
        WHERE digest_img.digest = split(image_uri, '@')[1]
          AND digest_img.type IN ['manifest_list', 'image']
        RETURN collect(digest_img) AS digest_matches
        UNION
        WITH image_uri, tag_matches
        WITH image_uri, tag_matches WHERE size(tag_matches) > 0 OR NOT image_uri CONTAINS '@'
        RETURN [] AS digest_matches
    }
    WITH image_uri, tag_matches + digest_matches AS all_matches
    UNWIND CASE WHEN size(all_matches) = 0 THEN [null] ELSE all_matches END AS img
    WITH image_uri, img
    ORDER BY image_uri,
        CASE img.type
            WHEN 'manifest_list' THEN 0
            WHEN 'image' THEN 1
            ELSE 2
        END,
        img.digest
    WITH image_uri, [
        target IN collect({digest: img.digest, type: img.type})
        WHERE target.digest IS NOT NULL AND target.type IS NOT NULL
    ] AS image_targets
    RETURN image_uri, image_targets
    """

    rows = neo4j_session.run(query, image_uris=image_uris).data()
    resolved: dict[str, list[dict[str, str]]] = {}

    for row in rows:
        image_uri = row.get("image_uri")
        image_targets = row.get("image_targets")
        if not isinstance(image_uri, str):
            continue
        if not isinstance(image_targets, list):
            resolved[image_uri] = []
            continue
        normalized = [
            {
                "digest": target["digest"],
                "type": target["type"],
            }
            for target in image_targets
            if isinstance(target, dict)
            and isinstance(target.get("digest"), str)
            and isinstance(target.get("type"), str)
        ]
        resolved[image_uri] = normalized

    return resolved


def load_aibom_sources(
    neo4j_session: Session,
    sources: list[ParsedAIBOMSource],
    update_tag: int,
) -> None:
    eligible_sources: list[ParsedAIBOMSource] = []

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

        eligible_sources.append(source)

    image_uris = sorted(
        {source.image_uri for source in eligible_sources if source.image_uri}
    )
    manifest_digest_map = resolve_manifest_list_digests(neo4j_session, image_uris)

    workflow_payloads_by_id: dict[str, dict[str, Any]] = {}
    component_payloads_by_id: dict[str, dict[str, Any]] = {}
    component_category_counts: Counter[str] = Counter()

    for source in eligible_sources:
        if source.image_uri is None:
            continue

        image_targets = manifest_digest_map.get(source.image_uri, [])
        if not image_targets:
            logger.warning(
                "Skipping AIBOM source %s (image URI %s): no ECRImage match found",
                source.source_key,
                source.image_uri,
            )
            stat_handler.incr("aibom_sources_unmatched")
            continue

        if len(image_targets) > 1:
            logger.warning(
                "Found %d ECRImage matches for image URI %s; using %s digest %s",
                len(image_targets),
                source.image_uri,
                image_targets[0]["type"],
                image_targets[0]["digest"],
            )

        manifest_digest = image_targets[0]["digest"]
        image_type = image_targets[0]["type"]
        if image_type == "manifest_list":
            stat_handler.incr("aibom_sources_matched_manifest_list")
        else:
            stat_handler.incr("aibom_sources_matched_image")

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
