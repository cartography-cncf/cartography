import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from kubernetes.client import V1Role
from kubernetes.client import V1RoleBinding
from kubernetes.client import V1ServiceAccount

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.rolebindings import KubernetesRoleBindingSchema
from cartography.models.kubernetes.roles import KubernetesRoleSchema
from cartography.models.kubernetes.serviceaccounts import KubernetesServiceAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_service_accounts(k8s_client: K8sClient) -> List[V1ServiceAccount]:
    """
    Get all ServiceAccounts across all namespaces.
    """
    return k8s_paginate(k8s_client.core.list_service_account_for_all_namespaces)


def get_roles(k8s_client: K8sClient) -> List[V1Role]:
    """
    Get all Roles across all namespaces.
    """
    return k8s_paginate(k8s_client.rbac.list_role_for_all_namespaces)


def get_role_bindings(k8s_client: K8sClient) -> List[V1RoleBinding]:
    """
    Get all RoleBindings across all namespaces.
    """
    return k8s_paginate(k8s_client.rbac.list_role_binding_for_all_namespaces)


def transform_service_accounts(
    service_accounts: List[V1ServiceAccount],
) -> List[Dict[str, Any]]:
    """
    Transform Kubernetes ServiceAccounts into a list of dictionaries for Neo4j ingestion.
    """
    result = []
    for sa in service_accounts:
        result.append(
            {
                "id": f"{sa.metadata.namespace}/{sa.metadata.name}",
                "name": sa.metadata.name,
                "namespace": sa.metadata.namespace,
                "uid": sa.metadata.uid,
                "creation_timestamp": get_epoch(sa.metadata.creation_timestamp),
                "resource_version": sa.metadata.resource_version,
            }
        )
    return result


def transform_roles(roles: List[V1Role]) -> List[Dict[str, Any]]:
    """
    Transform Kubernetes Roles into a list of dictionaries for Neo4j ingestion.
    Flattens rules into separate api_groups, resources, and verbs lists.
    """
    result = []
    for role in roles:
        # Flatten all rules into combined lists
        all_api_groups = []
        all_resources = []
        all_verbs = []

        for rule in role.rules or []:
            # Extend api_groups, handling None and empty string cases
            if rule.api_groups:
                for api_group in rule.api_groups:
                    # Empty string represents core API group
                    api_group_name = "core" if api_group == "" else api_group
                    if api_group_name not in all_api_groups:
                        all_api_groups.append(api_group_name)

            # Extend resources
            if rule.resources:
                for resource in rule.resources:
                    if resource not in all_resources:
                        all_resources.append(resource)

            # Extend verbs
            if rule.verbs:
                for verb in rule.verbs:
                    if verb not in all_verbs:
                        all_verbs.append(verb)

        result.append(
            {
                "id": f"{role.metadata.namespace}/{role.metadata.name}",
                "name": role.metadata.name,
                "namespace": role.metadata.namespace,
                "uid": role.metadata.uid,
                "creation_timestamp": get_epoch(role.metadata.creation_timestamp),
                "resource_version": role.metadata.resource_version,
                "api_groups": all_api_groups,
                "resources": all_resources,
                "verbs": all_verbs,
            }
        )
    return result


def transform_role_bindings(role_bindings: List[V1RoleBinding]) -> List[Dict[str, Any]]:
    """
    Transform Kubernetes RoleBindings into a list of dictionaries for Neo4j ingestion.
    Creates one record per ServiceAccount subject for cleaner relationships.
    """
    result = []
    for rb in role_bindings:
        # Only process ServiceAccount subjects
        service_account_subjects = [
            subject
            for subject in (rb.subjects or [])
            if subject.kind == "ServiceAccount"
        ]

        for subject in service_account_subjects:
            result.append(
                {
                    "id": f"{rb.metadata.namespace}/{rb.metadata.name}/{subject.namespace}/{subject.name}",  # same role binding can be used for different service accounts so need a unique id
                    "name": rb.metadata.name,
                    "namespace": rb.metadata.namespace,
                    "uid": rb.metadata.uid,
                    "creation_timestamp": get_epoch(rb.metadata.creation_timestamp),
                    "resource_version": rb.metadata.resource_version,
                    "role_name": rb.role_ref.name,
                    "role_kind": rb.role_ref.kind,
                    "subject_name": subject.name,
                    "subject_namespace": subject.namespace,
                    "subject_service_account_id": f"{subject.namespace}/{subject.name}",
                    "role_id": f"{rb.metadata.namespace}/{rb.role_ref.name}",
                }
            )
    return result


@timeit
def load_service_accounts(
    session: neo4j.Session,
    service_accounts: List[Dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    logger.info(f"Loading {len(service_accounts)} KubernetesServiceAccounts")
    load(
        session,
        KubernetesServiceAccountSchema(),
        service_accounts,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


@timeit
def load_roles(
    session: neo4j.Session,
    roles: List[Dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    logger.info(f"Loading {len(roles)} KubernetesRoles")
    load(
        session,
        KubernetesRoleSchema(),
        roles,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


@timeit
def load_role_bindings(
    session: neo4j.Session,
    role_bindings: List[Dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    logger.info(f"Loading {len(role_bindings)} KubernetesRoleBindings")
    load(
        session,
        KubernetesRoleBindingSchema(),
        role_bindings,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


@timeit
def cleanup(session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    logger.debug("Running cleanup job for Kubernetes RBAC resources")
    cleanup_job = GraphJob.from_node_schema(
        KubernetesServiceAccountSchema(), common_job_parameters
    )
    cleanup_job.run(session)

    cleanup_job = GraphJob.from_node_schema(
        KubernetesRoleSchema(), common_job_parameters
    )
    cleanup_job.run(session)

    cleanup_job = GraphJob.from_node_schema(
        KubernetesRoleBindingSchema(), common_job_parameters
    )
    cleanup_job.run(session)


@timeit
def sync_kubernetes_rbac(
    session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info(f"Syncing Kubernetes RBAC resources for cluster {client.name}")

    service_accounts = get_service_accounts(client)
    roles = get_roles(client)
    role_bindings = get_role_bindings(client)

    transformed_service_accounts = transform_service_accounts(service_accounts)
    transformed_roles = transform_roles(roles)
    transformed_role_bindings = transform_role_bindings(role_bindings)

    cluster_id = common_job_parameters["CLUSTER_ID"]
    cluster_name = client.name

    load_service_accounts(
        session=session,
        service_accounts=transformed_service_accounts,
        update_tag=update_tag,
        cluster_id=cluster_id,
        cluster_name=cluster_name,
    )

    load_roles(
        session=session,
        roles=transformed_roles,
        update_tag=update_tag,
        cluster_id=cluster_id,
        cluster_name=cluster_name,
    )

    # Load RoleBindings last (depends on ServiceAccounts and Roles)
    load_role_bindings(
        session=session,
        role_bindings=transformed_role_bindings,
        update_tag=update_tag,
        cluster_id=cluster_id,
        cluster_name=cluster_name,
    )

    cleanup(session, common_job_parameters)
