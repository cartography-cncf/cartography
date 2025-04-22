import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.namespaces import KubernetesNamespaceSchema
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def get_namespaces(client: K8sClient) -> List[Dict[str, Any]]:
    namespaces = []
    for namespace in client.core.list_namespace().items:
        namespaces.append(
            {
                "uid": namespace.metadata.uid,
                "name": namespace.metadata.name,
                "creation_timestamp": get_epoch(namespace.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(namespace.metadata.deletion_timestamp),
                "status_phase": namespace.status.phase,
            },
        )

    return namespaces


def load_namespaces(
    session: neo4j.Session,
    namespaces: List[Dict[str, Any]],
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info(f"Loading {len(namespaces)} kubernetes namespaces.")
    load(
        session,
        KubernetesNamespaceSchema(),
        namespaces,
        lastupdated=update_tag,
        CLUSTER_ID=common_job_parameters.get("CLUSTER_ID"),
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    logger.debug("Running cleanup job for KubernetesNamespace")
    cleanup_job = GraphJob.from_node_schema(KubernetesNamespaceSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)


@timeit
def sync_namespaces(
    session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    namespaces = get_namespaces(client)
    load_namespaces(session, namespaces, update_tag, common_job_parameters)
    cleanup(session, common_job_parameters)
