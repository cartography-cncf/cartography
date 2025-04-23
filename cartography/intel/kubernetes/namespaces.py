import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from kubernetes.client.models import V1Namespace

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.namespaces import KubernetesNamespaceSchema
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
def get_namespaces(client: K8sClient) -> List[Dict[str, Any]]:
    return client.core.list_namespace().items


def transform_namespaces(namespaces: List[V1Namespace], cluster_name: str) -> List[Dict[str, Any]]:
    transformed_namespaces = []
    for namespace in namespaces:
        transformed_namespaces.append({
            "uid": namespace.metadata.uid,
            "name": namespace.metadata.name,
            "creation_timestamp": get_epoch(namespace.metadata.creation_timestamp),
            "deletion_timestamp": get_epoch(namespace.metadata.deletion_timestamp),
            "status_phase": namespace.status.phase,
            "cluster_name": cluster_name,
        })
    return transformed_namespaces


def load_namespaces(
    session: neo4j.Session,
    namespaces: List[Dict[str, Any]],
    update_tag: int,
    cluster_id: str,
) -> None:
    logger.info(f"Loading {len(namespaces)} kubernetes namespaces.")
    load(
        session,
        KubernetesNamespaceSchema(),
        namespaces,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
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
    transformed_namespaces = transform_namespaces(namespaces, client.name)
    load_namespaces(
        session,
        transformed_namespaces,
        update_tag,
        common_job_parameters.get("CLUSTER_ID"),
    )
    cleanup(session, common_job_parameters)
