from typing import Set
from typing import Tuple

import neo4j

from cartography.client.core.tx import read_list_of_tuples_tx
from cartography.util import timeit


@timeit
def get_gitlab_container_images(
    neo4j_session: neo4j.Session,
) -> Set[Tuple[str, str]]:
    """
    Queries the graph for all GitLab container images with their URIs and digests.

    :param neo4j_session: The neo4j session object.
    :return: 2-tuples of (uri, digest) for each GitLab container image.
    """
    query = """
    MATCH (img:GitLabContainerImage)
    WHERE img.uri IS NOT NULL AND img.digest IS NOT NULL
    RETURN img.uri AS uri, img.digest AS digest
    """
    return neo4j_session.read_transaction(read_list_of_tuples_tx, query)


@timeit
def get_gitlab_container_tags(
    neo4j_session: neo4j.Session,
) -> Set[Tuple[str, str]]:
    """
    Queries the graph for all GitLab container repository tags with their locations and digests.

    :param neo4j_session: The neo4j session object.
    :return: 2-tuples of (location, digest) for each GitLab container repository tag.
    """
    query = """
    MATCH (tag:GitLabContainerRepositoryTag)
    WHERE tag.location IS NOT NULL
    RETURN tag.location AS location, tag.digest AS digest
    """
    return neo4j_session.read_transaction(read_list_of_tuples_tx, query)
