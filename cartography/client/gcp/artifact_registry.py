from typing import Set
from typing import Tuple

import neo4j

from cartography.client.core.tx import read_list_of_tuples_tx
from cartography.util import timeit


@timeit
def get_gcp_container_images(
    neo4j_session: neo4j.Session,
) -> Set[Tuple[str, str]]:
    """
    Queries the graph for all GCP Artifact Registry container images with their URIs and digests.

    :param neo4j_session: The neo4j session object.
    :return: 2-tuples of (uri, digest) for each GCP container image.
    """
    query = """
    MATCH (img:GCPArtifactRegistryContainerImage)
    WHERE img.uri IS NOT NULL AND img.digest IS NOT NULL
    RETURN img.uri AS uri, img.digest AS digest
    """
    return neo4j_session.read_transaction(read_list_of_tuples_tx, query)
