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
from cartography.graph.job import GraphJob
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
    # Note: We use one_to_many relationships for HEAD/TAIL so multiple images can share layers
    records: List[Dict] = []
    for i, diff_id in enumerate(diff_ids):
        rec: Dict = {"diff_id": diff_id}

        # NEXT relationship to the next layer in the chain
        if i < len(diff_ids) - 1:
            rec["next_diff_id"] = diff_ids[i + 1]

        # HEAD relationship - this layer is the head of this image
        if i == 0:
            rec["head_image_ids"] = [image_digest]

        # TAIL relationship - this layer is the tail of this image
        if i == len(diff_ids) - 1:
            rec["tail_image_ids"] = [image_digest]

        records.append(rec)

    # Load layers to graph using the model's relationships
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
def compute_ecr_image_lineage(neo4j_session: Session, update_tag: int) -> None:
    """
    Compute BUILT_FROM relationships between ECR images.
    """
    # Get all ECR images with their layers by traversing from HEAD through NEXT
    query = """
    MATCH (img:ECRImage)-[:HEAD]->(head:ImageLayer)
    OPTIONAL MATCH path = (head)-[:NEXT*]->(tail:ImageLayer)
    WHERE NOT (tail)-[:NEXT]->()
    WITH img, head,
         CASE WHEN path IS NULL
              THEN [head]
              ELSE [head] + [n IN nodes(path) WHERE n:ImageLayer AND n <> head]
         END AS layer_nodes
    RETURN img.id AS image_id, [l IN layer_nodes | l.diff_id] AS layer_ids
    """

    result = neo4j_session.run(query)
    images_with_layers = [(r["image_id"], r["layer_ids"]) for r in result]

    if not images_with_layers:
        logger.info("No ECR images with layers found for lineage computation")
        return

    logger.info(f"Computing lineage for {len(images_with_layers)} ECR images")

    # Find parent-child relationships using the simple prefix algorithm
    relationships = []
    for i, (child_id, child_layers) in enumerate(images_with_layers):
        longest_parent = None
        longest_parent_length = 0

        for j, (parent_id, parent_layers) in enumerate(images_with_layers):
            if i != j and compute_image_lineage(parent_layers, child_layers):
                if len(parent_layers) > longest_parent_length:
                    longest_parent = parent_id
                    longest_parent_length = len(parent_layers)

        if longest_parent:
            relationships.append((child_id, longest_parent))
            logger.debug(f"Found lineage: {child_id} built from {longest_parent}")

    # Create BUILT_FROM relationships
    if relationships:
        logger.info(f"Creating {len(relationships)} BUILT_FROM relationships")
        neo4j_session.run(
            """
            UNWIND $rels AS rel
            MATCH (child:ECRImage {id: rel[0]})
            MATCH (parent:ECRImage {id: rel[1]})
            MERGE (child)-[r:BUILT_FROM]->(parent)
            SET r.lastupdated = $update_tag
            """,
            rels=relationships,
            update_tag=update_tag,
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
        compute_ecr_image_lineage(neo4j_session, update_tag)
        logger.info("ECR image lineage computation complete")


@timeit
def cleanup_stale_image_layers(neo4j_session: Session, update_tag: int) -> None:
    """
    Clean up stale image layers and relationships.

    Args:
        neo4j_session: Neo4j session
        update_tag: Current update tag
    """
    logger.info("Running image layer cleanup")

    # Use GraphJob for standard cleanup of ImageLayer nodes
    common_job_parameters = {"UPDATE_TAG": update_tag}
    GraphJob.from_node_schema(ImageLayerSchema(), common_job_parameters).run(
        neo4j_session
    )

    # Custom cleanup for ImageLayer graph: remove stale NEXT/HEAD/TAIL rels tied to layers touched this run
    # Remove stale NEXT edges among updated layers
    neo4j_session.run(
        """
        MATCH (a:ImageLayer)-[r:NEXT]->(b:ImageLayer)
        WHERE (a.lastupdated = $update_tag OR b.lastupdated = $update_tag)
          AND r.lastupdated <> $update_tag
        DELETE r
        """,
        update_tag=update_tag,
    )

    # Remove stale HEAD/TAIL edges from images to updated layers
    neo4j_session.run(
        """
        MATCH (:ECRImage)-[r:HEAD|TAIL]->(l:ImageLayer)
        WHERE l.lastupdated = $update_tag AND r.lastupdated <> $update_tag
        DELETE r
        """,
        update_tag=update_tag,
    )

    # Remove orphan layers that were not updated this run and have no links
    neo4j_session.run(
        """
        MATCH (l:ImageLayer)
        WHERE l.lastupdated <> $update_tag
          AND NOT (l)-[:NEXT]-()
          AND NOT ()-[:NEXT]->(l)
          AND NOT ()-[:HEAD]->(l)
          AND NOT ()-[:TAIL]->(l)
        DETACH DELETE l
        """,
        update_tag=update_tag,
    )

    # Remove stale BUILT_FROM relationships
    neo4j_session.run(
        """
        MATCH (:ECRImage)-[r:BUILT_FROM]->(:ECRImage)
        WHERE r.lastupdated < $update_tag
        DELETE r
        """,
        update_tag=update_tag,
    )
