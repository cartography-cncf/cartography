import json
import logging
from typing import Any

import neo4j
from kubernetes.client.exceptions import ApiException
from kubernetes.client.models import V1OwnerReference
from kubernetes.client.models import V1Secret

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.secrets import KubernetesSecretSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_secrets(client: K8sClient) -> list[V1Secret]:
    items = k8s_paginate(
        client.core.list_secret_for_all_namespaces,
        raise_on_forbidden=True,
    )
    return items


def _get_owner_references(
    owner_references: list[V1OwnerReference] | None,
) -> str | None:
    if owner_references:
        owner_references_list = []
        for owner_reference in owner_references:
            owner_references_list.append(
                {
                    "kind": owner_reference.kind,
                    "name": owner_reference.name,
                    "uid": owner_reference.uid,
                    "apiVersion": owner_reference.api_version,
                    "controller": owner_reference.controller,
                }
            )
        return json.dumps(owner_references_list)
    return None


def transform_secrets(
    secrets: list[V1Secret], cluster_name: str
) -> list[dict[str, Any]]:
    secrets_list = []
    for secret in secrets:
        secrets_list.append(
            {
                "composite_id": f"{cluster_name}/{secret.metadata.namespace}/{secret.metadata.name}",
                "uid": secret.metadata.uid,
                "name": secret.metadata.name,
                "creation_timestamp": get_epoch(secret.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(secret.metadata.deletion_timestamp),
                "owner_references": _get_owner_references(
                    secret.metadata.owner_references
                ),
                "namespace": secret.metadata.namespace,
                "type": secret.type,
            }
        )

    return secrets_list


@timeit
def load_secrets(
    session: neo4j.Session,
    secrets: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    load(
        session,
        KubernetesSecretSchema(),
        secrets,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


@timeit
def cleanup(session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    logger.debug("Running cleanup for KubernetesSecrets")
    cleanup_job = GraphJob.from_node_schema(
        KubernetesSecretSchema(),
        common_job_parameters,
    )
    cleanup_job.run(session)


@timeit
def sync_secrets(
    session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    try:
        secrets = get_secrets(client)
    except ApiException as e:
        if e.status in (401, 403):
            # Skipping load + cleanup is intentional: if the operator previously granted
            # `list secrets` and later revoked it, running cleanup would wipe the existing
            # KubernetesSecret subgraph for this cluster.
            logger.warning(
                "Cartography lacks permission to list secrets on cluster %s (status %s). "
                "Skipping secret sync and preserving previously synced secrets. "
                "If this is intentional (granting `list secrets` also exposes the base64 "
                "`data` field and you prefer not to grant it), you can ignore this warning.",
                client.name,
                e.status,
            )
            return
        raise
    transformed_secrets = transform_secrets(secrets, client.name)
    load_secrets(
        session=session,
        secrets=transformed_secrets,
        update_tag=update_tag,
        cluster_id=common_job_parameters["CLUSTER_ID"],
        cluster_name=client.name,
    )
    cleanup(session, common_job_parameters)
