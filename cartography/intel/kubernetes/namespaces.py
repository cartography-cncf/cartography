import logging
from typing import Dict
from typing import List
from typing import Tuple

from neo4j import Session

from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import K8sClient
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def sync_namespaces(session: Session, client: K8sClient, update_tag: int) -> Dict:
    cluster, namespaces = get_namespaces(client)
    load_namespaces(session, cluster, namespaces, update_tag)
    merge_module_sync_metadata(
        session,
        group_type="KubernetesCluster",
        group_id=cluster["uid"],
        synced_type="KubernetesCluster",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
    return cluster


@timeit
def get_namespaces(client: K8sClient) -> Tuple[Dict, List[Dict]]:
    cluster = dict()
    namespaces = list()
    for namespace in client.core.list_namespace().items:
        namespaces.append(
            {
                "uid": namespace.metadata.uid,
                "name": namespace.metadata.name,
                "creation_timestamp": get_epoch(namespace.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(namespace.metadata.deletion_timestamp),
            },
        )
        if namespace.metadata.name == "kube-system":
            cluster = {"uid": namespace.metadata.uid, "name": client.name}
    return cluster, namespaces


def load_namespaces(
    session: Session,
    cluster: Dict,
    data: List[Dict],
    update_tag: int,
) -> None:
    ingestion_cypher_query = """
    MERGE (cluster:KubernetesCluster {id: $cluster_id})
    ON CREATE SET cluster.firstseen = timestamp()
    SET cluster.name = $cluster_name,
        cluster.lastupdated = $update_tag
    WITH cluster
    UNWIND $namespaces as namespace
        MERGE (space:KubernetesNamespace {id: namespace.uid})
        ON CREATE SET space.firstseen = timestamp()
        SET space.lastupdated = $update_tag,
            space.name = namespace.name,
            space.created_at = namespace.creation_timestamp,
            space.deleted_at = namespace.deletion_timestamp
        WITH cluster, space
        MERGE (cluster)-[rel1:HAS_NAMESPACE]->(space)
        ON CREATE SET rel1.firstseen = timestamp()
        SET rel1.lastupdated = $update_tag
    """
    logger.info(f"Loading {len(data)} kubernetes namespaces.")
    session.run(
        ingestion_cypher_query,
        namespaces=data,
        cluster_id=cluster["uid"],
        cluster_name=cluster["name"],
        update_tag=update_tag,
    )
