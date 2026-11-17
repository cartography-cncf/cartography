import logging
from typing import Any

import neo4j

from cartography.client.core.tx import read_list_of_values_tx
from cartography.client.core.tx import run_write_query
from cartography.helpers import batch
from cartography.util import timeit

logger = logging.getLogger(__name__)

DELETE_BATCH_SIZE = 1000

# An image's own HAS_LAYER, HEAD and TAIL edges do not keep it alive: its layers
# can outlive it when another image shares them.
_ORPHAN_IMAGE_PREDICATE = """
(n.lastupdated IS NULL OR n.lastupdated <> $UPDATE_TAG)
AND NOT exists {
    MATCH (n)-[r]-()
    WHERE NOT (startNode(r) = n AND type(r) IN ['HAS_LAYER', 'HEAD', 'TAIL'])
}
"""

_ORPHAN_LAYER_PREDICATE = """
(n.lastupdated IS NULL OR n.lastupdated <> $UPDATE_TAG)
AND NOT exists((:GCPProject)-[:RESOURCE]->(n))
"""


@timeit
def cleanup_orphans(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    batch_size: int = DELETE_BATCH_SIZE,
) -> None:
    """Delete GAR images and layers that nothing references any more.

    Images and layers are keyed by digest and shared across projects, so whether
    one is orphaned is a question about the whole graph. It is answered once, after
    every project has synced and removed its own stale links. Answering it per
    project scanned every image and layer in the graph once per project, and again
    after every batch of deletions.
    """
    update_tag = common_job_parameters["UPDATE_TAG"]
    _delete_orphans(
        neo4j_session,
        "GCPArtifactRegistryImage",
        _ORPHAN_IMAGE_PREDICATE,
        update_tag,
        batch_size,
    )
    _delete_orphans(
        neo4j_session,
        "GCPArtifactRegistryImageLayer",
        _ORPHAN_LAYER_PREDICATE,
        update_tag,
        batch_size,
    )


def _delete_orphans(
    neo4j_session: neo4j.Session,
    label: str,
    predicate: str,
    update_tag: int,
    batch_size: int,
) -> None:
    orphan_ids = neo4j_session.execute_read(
        read_list_of_values_tx,
        f"MATCH (n:{label}) WHERE {predicate} RETURN n.id",
        UPDATE_TAG=update_tag,
    )
    logger.info("Deleting %d orphaned %s nodes.", len(orphan_ids), label)
    # The predicate is checked again at delete time, so a node that gained a
    # reference after the scan survives.
    delete_query = f"""
    UNWIND $ids AS id
    MATCH (n:{label} {{id: id}})
    WHERE {predicate}
    DETACH DELETE n
    """
    for ids in batch(orphan_ids, size=batch_size):
        run_write_query(neo4j_session, delete_query, ids=ids, UPDATE_TAG=update_tag)
