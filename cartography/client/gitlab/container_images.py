from typing import Any
from typing import Set
from typing import Tuple

import neo4j

from cartography.client.core.tx import read_list_of_dicts_tx
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
    return neo4j_session.execute_read(read_list_of_tuples_tx, query)


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
    return neo4j_session.execute_read(read_list_of_tuples_tx, query)


@timeit
def get_gitlab_image_sources(
    neo4j_session: neo4j.Session,
    digests: list[str],
) -> dict[str, dict[str, Any]]:
    """
    Return the source fields each GitLab container image holds, keyed by digest.

    :param neo4j_session: The neo4j session object.
    :param digests: The image digests to look up.
    :return: Mapping of digest to its source_uri, source_revision and source_file.
    """
    if not digests:
        return {}
    query = """
    MATCH (img:GitLabContainerImage)
    WHERE img.id IN $digests
    RETURN img.digest AS digest, img.source_uri AS source_uri,
           img.source_revision AS source_revision, img.source_file AS source_file
    """
    records = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        query,
        digests=digests,
    )
    return {record["digest"]: record for record in records}
