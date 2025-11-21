import logging
from typing import Any

import neo4j
from kubernetes.client.models import V1Namespace

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.namespaces import KubernetesNamespaceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_namespaces(client: K8sClient) -> list[V1Namespace]:
    items = k8s_paginate(client.core.list_namespace)
    return items


def transform_namespaces(namespaces: list[V1Namespace]) -> list[dict[str, Any]]:
    transformed_namespaces = []
    for namespace in namespaces:
        transformed_namespaces.append(
            {
                "uid": namespace.metadata.uid,
                "name": namespace.metadata.name,
                "creation_timestamp": get_epoch(namespace.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(namespace.metadata.deletion_timestamp),
                "status_phase": namespace.status.phase if namespace.status else None,
            }
        )
    return transformed_namespaces


def load_namespaces(
    session: neo4j.Session,
    namespaces: list[dict[str, Any]],
    update_tag: int,
    cluster_name: str,
    cluster_id: str,
) -> None:
    logger.info(f"Loading {len(namespaces)} kubernetes namespaces.")
    load(
        session,
        KubernetesNamespaceSchema(),
        namespaces,
        lastupdated=update_tag,
        cluster_name=cluster_name,
        CLUSTER_ID=cluster_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    logger.debug("Running cleanup job for KubernetesNamespace")
    cleanup_job = GraphJob.from_node_schema(
        KubernetesNamespaceSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync_namespaces(
    session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    namespaces = get_namespaces(client)
    transformed_namespaces = transform_namespaces(namespaces)
    cluster_id: str = common_job_parameters["CLUSTER_ID"]
    load_namespaces(
        session,
        transformed_namespaces,
        update_tag,
        client.name,
        cluster_id,
    )
    cleanup(session, common_job_parameters)
