import logging
from itertools import chain
from typing import Any
from typing import Dict
from typing import List

import neo4j
from kubernetes.client import V1ClusterRole
from kubernetes.client import V1ClusterRoleBinding
from kubernetes.client import V1Role
from kubernetes.client import V1RoleBinding
from kubernetes.client import V1ServiceAccount

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.clusterrolebindings import (
    KubernetesClusterRoleBindingSchema,
)
from cartography.models.kubernetes.clusterroles import KubernetesClusterRoleSchema
from cartography.models.kubernetes.groups import KubernetesGroupSchema
from cartography.models.kubernetes.rolebindings import KubernetesRoleBindingSchema
from cartography.models.kubernetes.roles import KubernetesRoleSchema
from cartography.models.kubernetes.serviceaccounts import KubernetesServiceAccountSchema
from cartography.models.kubernetes.users import KubernetesUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_service_accounts(k8s_client: K8sClient) -> List[V1ServiceAccount]:

    return k8s_paginate(k8s_client.core.list_service_account_for_all_namespaces)


@timeit
def get_roles(k8s_client: K8sClient) -> List[V1Role]:

    return k8s_paginate(k8s_client.rbac.list_role_for_all_namespaces)


@timeit
def get_role_bindings(k8s_client: K8sClient) -> List[V1RoleBinding]:

    return k8s_paginate(k8s_client.rbac.list_role_binding_for_all_namespaces)


@timeit
def get_cluster_roles(k8s_client: K8sClient) -> List[V1ClusterRole]:

    return k8s_paginate(k8s_client.rbac.list_cluster_role)


@timeit
def get_cluster_role_bindings(k8s_client: K8sClient) -> List[V1ClusterRoleBinding]:

    return k8s_paginate(k8s_client.rbac.list_cluster_role_binding)


def transform_service_accounts(
    service_accounts: List[V1ServiceAccount], cluster_name: str
) -> List[Dict[str, Any]]:
    """
    Transform Kubernetes ServiceAccounts into a list of dictionaries.
    Uses cluster-scoped IDs to prevent collisions across multiple clusters.
    """
    result = []
    for sa in service_accounts:
        result.append(
            {
                "id": f"{cluster_name}/{sa.metadata.namespace}/{sa.metadata.name}",
                "name": sa.metadata.name,
                "namespace": sa.metadata.namespace,
                "uid": sa.metadata.uid,
                "creation_timestamp": get_epoch(sa.metadata.creation_timestamp),
                "resource_version": sa.metadata.resource_version,
            }
        )
    return result


def transform_roles(roles: List[V1Role], cluster_name: str) -> List[Dict[str, Any]]:
    """
    Transform Kubernetes Roles into a list of dictionaries.
    Flattens rules into separate api_groups, resources, and verbs lists.
    """
    result = []
    for role in roles:
        # Flatten all rules into combined sets
        all_api_groups: set[str] = set()
        all_resources: set[str] = set()
        all_verbs: set[str] = set()

        for rule in role.rules or []:
            # Update api_groups, handling None and empty string cases
            all_api_groups.update(
                {
                    "core" if api_group == "" else api_group
                    for api_group in rule.api_groups or []
                }
            )
            all_resources.update(rule.resources or [])
            all_verbs.update(rule.verbs or [])

        result.append(
            {
                "id": f"{cluster_name}/{role.metadata.namespace}/{role.metadata.name}",
                "name": role.metadata.name,
                "namespace": role.metadata.namespace,
                "uid": role.metadata.uid,
                "creation_timestamp": get_epoch(role.metadata.creation_timestamp),
                "resource_version": role.metadata.resource_version,
                "api_groups": sorted(
                    all_api_groups
                ),  # sorts to keep consistent ordering and converts to list to appease neo4j
                "resources": sorted(all_resources),
                "verbs": sorted(all_verbs),
            }
        )
    return result


def transform_role_bindings(
    role_bindings: List[V1RoleBinding], cluster_name: str
) -> List[Dict[str, Any]]:
    """
    Transform Kubernetes RoleBindings into a list of dictionaries.
    Creates one RoleBinding node per Kubernetes RoleBinding with lists of subject IDs.
    """
    result = []
    for rb in role_bindings:
        # Collect all subjects by type
        service_account_subjects = [
            subject
            for subject in (rb.subjects or [])
            if subject.kind == "ServiceAccount"
        ]
        user_subjects = [
            subject for subject in (rb.subjects or []) if subject.kind == "User"
        ]
        group_subjects = [
            subject for subject in (rb.subjects or []) if subject.kind == "Group"
        ]

        # Only create a RoleBinding node if it has at least one subject
        if rb.subjects:
            result.append(
                {
                    "id": f"{cluster_name}/{rb.metadata.namespace}/{rb.metadata.name}",
                    "name": rb.metadata.name,
                    "namespace": rb.metadata.namespace,
                    "uid": rb.metadata.uid,
                    "creation_timestamp": get_epoch(rb.metadata.creation_timestamp),
                    "resource_version": rb.metadata.resource_version,
                    "role_name": rb.role_ref.name,
                    "role_kind": rb.role_ref.kind,
                    "service_account_ids": [
                        f"{cluster_name}/{subject.namespace}/{subject.name}"
                        for subject in service_account_subjects
                    ],
                    "user_ids": [
                        f"{cluster_name}/{subject.name}" for subject in user_subjects
                    ],
                    "group_ids": [
                        f"{cluster_name}/{subject.name}" for subject in group_subjects
                    ],
                    "role_id": f"{cluster_name}/{rb.metadata.namespace}/{rb.role_ref.name}",
                }
            )
    return result


def transform_cluster_roles(
    cluster_roles: List[V1ClusterRole], cluster_name: str
) -> List[Dict[str, Any]]:
    """
    Transform Kubernetes ClusterRoles into a list of dictionaries.
    Flattens rules into separate api_groups, resources, and verbs lists.
    """
    result = []
    for cluster_role in cluster_roles:
        # Flatten all rules into combined sets
        all_api_groups: set[str] = set()
        all_resources: set[str] = set()
        all_verbs: set[str] = set()

        for rule in cluster_role.rules or []:
            # Update api_groups, handling None and empty string cases
            all_api_groups.update(
                {
                    "core" if api_group == "" else api_group
                    for api_group in rule.api_groups or []
                }
            )
            all_resources.update(rule.resources or [])
            all_verbs.update(rule.verbs or [])

        result.append(
            {
                "id": f"{cluster_name}/{cluster_role.metadata.name}",
                "name": cluster_role.metadata.name,
                "uid": cluster_role.metadata.uid,
                "creation_timestamp": get_epoch(
                    cluster_role.metadata.creation_timestamp
                ),
                "resource_version": cluster_role.metadata.resource_version,
                "api_groups": sorted(
                    all_api_groups
                ),  # sorts to keep consistent ordering and converts to list to appease neo4j
                "resources": sorted(all_resources),
                "verbs": sorted(all_verbs),
            }
        )
    return result


def transform_cluster_role_bindings(
    cluster_role_bindings: List[V1ClusterRoleBinding], cluster_name: str
) -> List[Dict[str, Any]]:
    """
    Transform Kubernetes ClusterRoleBindings into a list of dictionaries.
    Creates one ClusterRoleBinding node per Kubernetes ClusterRoleBinding with lists of subject IDs.
    """
    result = []
    for crb in cluster_role_bindings:
        # Collect all subjects by type
        service_account_subjects = [
            subject
            for subject in (crb.subjects or [])
            if subject.kind == "ServiceAccount"
        ]
        user_subjects = [
            subject for subject in (crb.subjects or []) if subject.kind == "User"
        ]
        group_subjects = [
            subject for subject in (crb.subjects or []) if subject.kind == "Group"
        ]

        # Only create a ClusterRoleBinding node if it has at least one subject
        if crb.subjects:
            result.append(
                {
                    "id": f"{cluster_name}/{crb.metadata.name}",
                    "name": crb.metadata.name,
                    "uid": crb.metadata.uid,
                    "creation_timestamp": get_epoch(crb.metadata.creation_timestamp),
                    "resource_version": crb.metadata.resource_version,
                    "role_name": crb.role_ref.name,
                    "role_kind": crb.role_ref.kind,
                    "service_account_ids": [
                        f"{cluster_name}/{subject.namespace}/{subject.name}"
                        for subject in service_account_subjects
                    ],
                    "user_ids": [
                        f"{cluster_name}/{subject.name}" for subject in user_subjects
                    ],
                    "group_ids": [
                        f"{cluster_name}/{subject.name}" for subject in group_subjects
                    ],
                    "role_id": f"{cluster_name}/{crb.role_ref.name}",
                }
            )
    return result


def transform_users(
    role_bindings: List[V1RoleBinding],
    cluster_role_bindings: List[V1ClusterRoleBinding],
    cluster_name: str,
) -> List[Dict[str, Any]]:
    """
    Transform Kubernetes Users from RoleBindings and ClusterRoleBindings into a list of dicts.
    """
    # Extract all users from rolebindings and clusterrolebindings
    all_users = {
        subject.name
        for binding in chain(
            role_bindings, cluster_role_bindings
        )  # iterate through combined bindings and role bindings
        for subject in (
            binding.subjects or []
        )  # iterates through each binding's subjects to get unique users
        if subject.kind == "User"
    }

    return [
        {
            "id": f"{cluster_name}/{user_name}",
            "name": user_name,
            "cluster_name": cluster_name,
        }
        for user_name in sorted(all_users)
    ]


def transform_groups(
    role_bindings: List[V1RoleBinding],
    cluster_role_bindings: List[V1ClusterRoleBinding],
    cluster_name: str,
) -> List[Dict[str, Any]]:
    """
    Transform Kubernetes Groups from RoleBindings and ClusterRoleBindings into a list of dicts.
    """
    # Extract all groups from rolebindings and clusterrolebindings
    all_groups = {
        subject.name
        for binding in chain(role_bindings, cluster_role_bindings)
        for subject in (binding.subjects or [])
        if subject.kind == "Group"
    }

    return [
        {
            "id": f"{cluster_name}/{group_name}",
            "name": group_name,
            "cluster_name": cluster_name,
        }
        for group_name in sorted(all_groups)
    ]


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
def load_cluster_roles(
    session: neo4j.Session,
    cluster_roles: List[Dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    logger.info(f"Loading {len(cluster_roles)} KubernetesClusterRoles")
    load(
        session,
        KubernetesClusterRoleSchema(),
        cluster_roles,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


@timeit
def load_cluster_role_bindings(
    session: neo4j.Session,
    cluster_role_bindings: List[Dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    logger.info(f"Loading {len(cluster_role_bindings)} KubernetesClusterRoleBindings")
    load(
        session,
        KubernetesClusterRoleBindingSchema(),
        cluster_role_bindings,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


@timeit
def load_users(
    session: neo4j.Session,
    users: List[Dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    logger.info(f"Loading {len(users)} KubernetesUsers")
    load(
        session,
        KubernetesUserSchema(),
        users,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


@timeit
def load_groups(
    session: neo4j.Session,
    groups: List[Dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    logger.info(f"Loading {len(groups)} KubernetesGroups")
    load(
        session,
        KubernetesGroupSchema(),
        groups,
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

    cleanup_job = GraphJob.from_node_schema(
        KubernetesClusterRoleSchema(), common_job_parameters
    )
    cleanup_job.run(session)

    cleanup_job = GraphJob.from_node_schema(
        KubernetesClusterRoleBindingSchema(), common_job_parameters
    )
    cleanup_job.run(session)

    cleanup_job = GraphJob.from_node_schema(
        KubernetesUserSchema(), common_job_parameters
    )
    cleanup_job.run(session)

    cleanup_job = GraphJob.from_node_schema(
        KubernetesGroupSchema(), common_job_parameters
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

    # Get namespace-scoped resources
    service_accounts = get_service_accounts(client)
    roles = get_roles(client)
    role_bindings = get_role_bindings(client)

    # Get cluster-scoped resources
    cluster_roles = get_cluster_roles(client)
    cluster_role_bindings = get_cluster_role_bindings(client)

    # Transform namespace-scoped resources
    transformed_service_accounts = transform_service_accounts(
        service_accounts, client.name
    )
    transformed_roles = transform_roles(roles, client.name)
    transformed_role_bindings = transform_role_bindings(role_bindings, client.name)

    # Transform cluster-scoped resources
    transformed_cluster_roles = transform_cluster_roles(cluster_roles, client.name)
    transformed_cluster_role_bindings = transform_cluster_role_bindings(
        cluster_role_bindings, client.name
    )

    # Transform users from all bindings
    transformed_users = transform_users(
        role_bindings, cluster_role_bindings, client.name
    )

    # Transform groups from all bindings
    transformed_groups = transform_groups(
        role_bindings, cluster_role_bindings, client.name
    )

    cluster_id = common_job_parameters["CLUSTER_ID"]
    cluster_name = client.name

    load_users(
        session=session,
        users=transformed_users,
        update_tag=update_tag,
        cluster_id=cluster_id,
        cluster_name=cluster_name,
    )

    load_groups(
        session=session,
        groups=transformed_groups,
        update_tag=update_tag,
        cluster_id=cluster_id,
        cluster_name=cluster_name,
    )

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

    load_cluster_roles(
        session=session,
        cluster_roles=transformed_cluster_roles,
        update_tag=update_tag,
        cluster_id=cluster_id,
        cluster_name=cluster_name,
    )

    load_role_bindings(
        session=session,
        role_bindings=transformed_role_bindings,
        update_tag=update_tag,
        cluster_id=cluster_id,
        cluster_name=cluster_name,
    )

    load_cluster_role_bindings(
        session=session,
        cluster_role_bindings=transformed_cluster_role_bindings,
        update_tag=update_tag,
        cluster_id=cluster_id,
        cluster_name=cluster_name,
    )

    cleanup(session, common_job_parameters)
