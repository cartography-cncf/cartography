from typing import Set
from typing import Tuple

import neo4j

from cartography.client.core.tx import read_list_of_tuples_tx
from cartography.util import timeit


@timeit
def get_gcp_container_images(
    neo4j_session: neo4j.Session,
) -> Set[Tuple[str, str, str, str, str]]:
    """
    Queries the graph for all GCP Artifact Registry container images with their URIs and digests.

    Returns 5-tuples similar to ECR to support both tag-based and digest-based matching:
    (location, tag, uri, repo_name, digest)

    For multi-arch images, this returns rows for both:
    - Manifest list digests (from GCPArtifactRegistryContainerImage)
    - Platform-specific digests (from GCPArtifactRegistryPlatformImage)

    Tags are unwound so each tag gets its own row, plus rows with null tags for digest-only matching.

    :param neo4j_session: The neo4j session object.
    :return: 5-tuples of (location, tag, uri, repo_name, digest) for each GCP container image.
    """
    query = """
    // Match container images with their repository
    MATCH (repo:GCPArtifactRegistryRepository)-[:CONTAINS]->(img:GCPArtifactRegistryContainerImage)
    WHERE img.uri IS NOT NULL

    // Optionally get platform-specific images for multi-arch
    OPTIONAL MATCH (img)-[:HAS_MANIFEST]->(platform:GCPArtifactRegistryPlatformImage)

    // Collect all platform images per container image
    WITH img, repo, collect(platform) AS platforms

    // Create list of all image nodes (container image + platform images)
    WITH img, repo,
         CASE
             WHEN size(platforms) = 0 THEN [img]
             ELSE platforms + [img]
         END AS all_image_nodes

    // Extract base URI (without @digest)
    WITH img, repo, all_image_nodes,
         CASE
             WHEN img.uri CONTAINS '@' THEN split(img.uri, '@')[0]
             ELSE img.uri
         END AS base_uri

    // Unwind image nodes to get one row per image (manifest list + each platform)
    UNWIND all_image_nodes AS image_node

    // Create tags list: include all tags PLUS one null entry for digest-only matching
    WITH repo, base_uri, image_node, img,
         CASE
             WHEN img.tags IS NOT NULL AND size(img.tags) > 0 THEN img.tags + [null]
             ELSE [null]
         END AS tags_list

    UNWIND tags_list AS tag

    // Construct tag-based URI if tag exists, otherwise use base URI
    WITH repo.location AS location,
         tag AS tag,
         CASE
             WHEN tag IS NOT NULL THEN base_uri + ':' + tag
             ELSE base_uri
         END AS uri,
         repo.name AS repo_name,
         image_node.digest AS digest

    WHERE digest IS NOT NULL

    RETURN DISTINCT location, tag, uri, repo_name, digest
    """
    return neo4j_session.read_transaction(read_list_of_tuples_tx, query)
