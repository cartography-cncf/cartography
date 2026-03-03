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
) -> dict[str, list[str]]:
    if not image_uris:
        return {}

    query = """
    UNWIND $image_uris AS image_uri
    OPTIONAL MATCH (:ECRRepositoryImage {id: image_uri})-[:IMAGE]->
        (manifest:ECRImage {type: 'manifest_list'})
    WITH image_uri, manifest
    ORDER BY image_uri, manifest.digest
    WITH image_uri, [d IN collect(manifest.digest) WHERE d IS NOT NULL] AS manifest_digests
    RETURN image_uri, manifest_digests
    """

    rows = neo4j_session.run(query, image_uris=image_uris).data()
    resolved: dict[str, list[str]] = {}

    for row in rows:
        image_uri = row.get("image_uri")
        manifest_digests = row.get("manifest_digests")
        if not isinstance(image_uri, str):
            continue
        if not isinstance(manifest_digests, list):
            resolved[image_uri] = []
            continue
        normalized = [digest for digest in manifest_digests if isinstance(digest, str)]
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

        manifest_digests = manifest_digest_map.get(source.image_uri, [])
        if not manifest_digests:
            logger.warning(
                "Skipping AIBOM source %s (image URI %s): no manifest-list ECRImage match found",
                source.source_key,
                source.image_uri,
            )
            stat_handler.incr("aibom_sources_unmatched")
            continue

        if len(manifest_digests) > 1:
            logger.warning(
                "Found %d manifest-list matches for image URI %s; using first digest %s",
                len(manifest_digests),
                source.image_uri,
                manifest_digests[0],
            )

        manifest_digest = manifest_digests[0]
        stat_handler.incr("aibom_sources_matched_manifest_list")

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
