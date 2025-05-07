import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from kubernetes.client.models import V1OwnerReference
from kubernetes.client.models import V1Secret

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.secrets import KubernetesSecretSchema
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
def get_secrets(client: K8sClient) -> List[V1Secret]:
    return client.core.list_secret_for_all_namespaces().items


def _get_owner_references(
    owner_references: Optional[V1OwnerReference],
) -> Optional[str]:
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


def transform_secrets(secrets: List[V1Secret]) -> List[Dict[str, Any]]:
    secrets_list = []
    for secret in secrets:
        secrets_list.append(
            {
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
    secrets_data: List[Dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    logger.info(f"Loading {len(secrets_data)} KubernetesSecrets")
    load(
        session,
        KubernetesSecretSchema(),
        secrets_data,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


@timeit
def cleanup(session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
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
    common_job_parameters: Dict[str, Any],
) -> None:
    secrets = get_secrets(client)
    transformed_secrets = transform_secrets(secrets)
    load_secrets(
        session=session,
        secrets_data=transformed_secrets,
        update_tag=update_tag,
        cluster_id=common_job_parameters["CLUSTER_ID"],
        cluster_name=client.name,
    )
    cleanup(session, common_job_parameters)
