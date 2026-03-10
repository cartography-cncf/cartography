import logging

from neo4j import Session

from cartography.client.core.tx import load
from cartography.intel.aibom.parser import ParsedAIBOMDocument
from cartography.intel.aibom.transform import transform_aibom_document
from cartography.models.aibom import AIBOMComponentSchema
from cartography.models.aibom import AIBOMScanSchema
from cartography.models.aibom import AIBOMSourceSchema
from cartography.models.aibom import AIBOMWorkflowSchema
from cartography.stats import get_stats_client

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


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


def load_aibom_document(
    neo4j_session: Session,
    document: ParsedAIBOMDocument,
    update_tag: int,
) -> None:
    manifest_digest = _resolve_digest_for_source(
        neo4j_session,
        document.image_uri,
    )
    transformed_document = transform_aibom_document(document, manifest_digest)

    for source in document.sources:
        stat_handler.incr("aibom_sources_total")

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

    load(
        neo4j_session,
        AIBOMScanSchema(),
        [transformed_document.scan_payload],
        lastupdated=update_tag,
    )

    if transformed_document.workflow_payloads:
        load(
            neo4j_session,
            AIBOMWorkflowSchema(),
            transformed_document.workflow_payloads,
            lastupdated=update_tag,
        )

    if transformed_document.component_payloads:
        load(
            neo4j_session,
            AIBOMComponentSchema(),
            transformed_document.component_payloads,
            lastupdated=update_tag,
        )

    if transformed_document.source_payloads:
        load(
            neo4j_session,
            AIBOMSourceSchema(),
            transformed_document.source_payloads,
            lastupdated=update_tag,
        )

    for category, count in transformed_document.component_category_counts.items():
        stat_handler.incr(f"aibom_components_loaded_{category}", count)
    for (
        relationship_type,
        count,
    ) in transformed_document.relationship_type_counts.items():
        stat_handler.incr(
            f"aibom_relationships_loaded_{relationship_type.lower()}",
            count,
        )
