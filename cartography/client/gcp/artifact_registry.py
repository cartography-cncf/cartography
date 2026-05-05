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
    Queries the graph for all GCP Artifact Registry repository images with their canonical image digests.

    Returns 5-tuples similar to ECR to support both tag-based and digest-based matching:
    (location, tag, uri, repo_name, digest)

    For manifest-list images, this returns rows for both the manifest-list image
    and the child images reached through CONTAINS_IMAGE.

    :param neo4j_session: The neo4j session object.
    :return: 5-tuples of (location, tag, uri, repo_name, digest) for each GCP container image.
    """
    query = """
    MATCH (repo:GCPArtifactRegistryRepository)-[:CONTAINS]->
          (repo_img:GCPArtifactRegistryRepositoryImage)-[:IMAGE]->
          (root:GCPArtifactRegistryImage)
    WHERE repo_img.uri IS NOT NULL

    MATCH (root)-[:CONTAINS_IMAGE*0..1]->(image_node:GCPArtifactRegistryImage)
    WHERE image_node.digest IS NOT NULL

    RETURN DISTINCT
        repo.location AS location,
        repo_img.tag AS tag,
        repo_img.uri AS uri,
        repo.name AS repo_name,
        image_node.digest AS digest
    """
    return neo4j_session.execute_read(read_list_of_tuples_tx, query)
