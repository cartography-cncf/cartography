"""
Build image lineage for container images using registry layer information.
Supports cross-registry lineage (ECR, GCR, Docker Hub, etc).
"""

import logging
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

from neo4j import Session

from cartography.client.core.tx import load
from cartography.intel.trivy.layers import compute_image_lineage
from cartography.intel.trivy.layers import get_image_layers_from_registry
from cartography.intel.trivy.layers import get_image_platforms
from cartography.models.trivy.image_layer import ImageLayerSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_all_ecr_images(neo4j_session: Session) -> List[Dict[str, str]]:
    """
    Get all ECR images from the graph.

    Returns:
        List of dicts with 'uri', 'digest', and 'region'
    """
    query = """
    MATCH (repo:ECRRepository)-[:REPO_IMAGE]->(img_node:ECRRepositoryImage)
    MATCH (img_node)-[:IMAGE]->(image:ECRImage)
    RETURN DISTINCT
        img_node.id AS uri,
        image.id AS digest,
        repo.region AS region
    """

    result = neo4j_session.run(query)
    return [dict(record) for record in result]


@timeit
def build_image_layers(
    neo4j_session: Session,
    image_uri: str,
    image_digest: str,
    platform: Optional[str],
    update_tag: int,
) -> Optional[List[str]]:
    """
    Fetch and store image layers for a specific ECR image and platform.

    Args:
        neo4j_session: Neo4j session
        image_uri: Full image URI
        image_digest: Image digest (sha256:...)
        platform: Target platform (e.g., "linux/amd64")
        update_tag: Update tag for tracking

    Returns:
        List of layer diff IDs if successful, None otherwise
    """
    # Get layers from registry
    diff_ids, registry_digest = get_image_layers_from_registry(
        image_uri, platform=platform
    )

    if not diff_ids:
        logger.debug(f"No layers found for {image_uri} platform {platform}")
        return None

    logger.info(f"Found {len(diff_ids)} layers for {image_uri} platform {platform}")

    # Build records for ImageLayerSchema
    records: List[Dict] = []
    for i, diff_id in enumerate(diff_ids):
        rec: Dict = {"diff_id": diff_id}
        if i < len(diff_ids) - 1:
            rec["next_diff_id"] = diff_ids[i + 1]
        if i == 0:
            rec["head_image_ids"] = [image_digest]
        if i == len(diff_ids) - 1:
            rec["tail_image_ids"] = [image_digest]
        records.append(rec)

    # Load layers to graph
    load(
        neo4j_session,
        ImageLayerSchema(),
        records,
        lastupdated=update_tag,
    )

    # Update ECRImage with length and platforms
    neo4j_session.run(
        """
        MATCH (img:ECRImage {id: $digest})
        SET img.length = $length
        WITH img
        UNWIND $platforms AS platform
        SET img.platforms = COALESCE(img.platforms, []) +
            CASE WHEN platform IN COALESCE(img.platforms, [])
                 THEN []
                 ELSE [platform]
            END
        """,
        digest=image_digest,
        length=len(diff_ids),
        platforms=[platform] if platform else ["linux/amd64"],
    )

    return diff_ids


@timeit
def compute_ecr_image_lineage(neo4j_session: Session) -> None:
    """
    Compute BUILT_FROM relationships between ECR images.
    """
    # Get all ECR images with their layers
    query = """
    MATCH (img:ECRImage)-[:HEAD]->(head:ImageLayer)
    WITH img, head
    MATCH path = (head)-[:NEXT*0..]->(layer:ImageLayer)
    WITH img, collect(layer.diff_id) AS layers
    WHERE size(layers) > 0
    RETURN img.id AS image_id, layers
    """

    result = neo4j_session.run(query)
    images_with_layers = [(r["image_id"], r["layers"]) for r in result]

    if not images_with_layers:
        logger.info("No ECR images with layers found for lineage computation")
        return

    logger.info(f"Computing lineage for {len(images_with_layers)} ECR images")

    # Find parent-child relationships
    relationships = []
    for i, (child_id, child_layers) in enumerate(images_with_layers):
        for j, (parent_id, parent_layers) in enumerate(images_with_layers):
            if i != j and compute_image_lineage(parent_layers, child_layers):
                relationships.append((child_id, parent_id))
                logger.debug(f"Found lineage: {child_id} built from {parent_id}")

    # Create BUILT_FROM relationships
    if relationships:
        logger.info(f"Creating {len(relationships)} BUILT_FROM relationships")
        neo4j_session.run(
            """
            UNWIND $rels AS rel
            MATCH (child:ECRImage {id: rel[0]})
            MATCH (parent:ECRImage {id: rel[1]})
            MERGE (child)-[:BUILT_FROM]->(parent)
            """,
            rels=relationships,
        )


@timeit
def build_ecr_image_lineage(
    neo4j_session: Session,
    update_tag: int,
    platform_filter: Optional[str] = None,
) -> None:
    """
    Build complete image lineage for all ECR images in the graph.

    Args:
        neo4j_session: Neo4j session
        update_tag: Update tag for tracking
        platform_filter: Optional platform to process (e.g., "linux/amd64")
    """
    # Get all ECR images
    all_images = get_all_ecr_images(neo4j_session)

    if not all_images:
        logger.info("No ECR images found in graph")
        return

    logger.info(f"Building lineage for {len(all_images)} ECR images")

    # Track images we successfully processed
    processed_images: Set[str] = set()

    for image_info in all_images:
        image_uri = image_info["uri"]
        image_digest = image_info["digest"]

        try:
            # Check if it's a multi-platform image
            platforms = get_image_platforms(image_uri)

            if platform_filter:
                # Only process specified platform
                if platform_filter in platforms:
                    layers = build_image_layers(
                        neo4j_session,
                        image_uri,
                        image_digest,
                        platform_filter,
                        update_tag,
                    )
                    if layers:
                        processed_images.add(image_digest)
            else:
                # Process first available platform (or all if needed)
                for platform in platforms:
                    layers = build_image_layers(
                        neo4j_session,
                        image_uri,
                        image_digest,
                        platform,
                        update_tag,
                    )
                    if layers:
                        processed_images.add(image_digest)
                        # Only need to process once per image for lineage
                        break

        except Exception as e:
            logger.warning(f"Failed to process {image_uri}: {e}")
            continue

    logger.info(f"Successfully processed {len(processed_images)} images")

    # Compute lineage relationships
    if processed_images:
        compute_ecr_image_lineage(neo4j_session)
        logger.info("ECR image lineage computation complete")


@timeit
def cleanup_stale_image_layers(neo4j_session: Session, update_tag: int) -> None:
    """
    Clean up stale image layers and relationships.

    Args:
        neo4j_session: Neo4j session
        update_tag: Current update tag
    """
    # Remove stale BUILT_FROM relationships
    neo4j_session.run(
        """
        MATCH (:ECRImage)-[r:BUILT_FROM]->(:ECRImage)
        WHERE r.lastupdated < $update_tag
        DELETE r
        """,
        update_tag=update_tag,
    )

    # Remove orphaned layers (not connected to any image)
    neo4j_session.run(
        """
        MATCH (layer:ImageLayer)
        WHERE NOT EXISTS((layer)<-[:HEAD|TAIL]-())
        AND layer.lastupdated < $update_tag
        DETACH DELETE layer
        """,
        update_tag=update_tag,
    )
