import logging
from typing import Any, Dict, List

from kubernetes.client import V1Role, V1RoleBinding, V1ServiceAccount

from cartography.util import get_epoch
from cartography.intel.kubernetes.util import k8s_paginate

logger = logging.getLogger(__name__)


def get_service_accounts(k8s_client, namespaces: List[str]) -> List[V1ServiceAccount]:
    """
    Get all ServiceAccounts across specified namespaces.
    """
    service_accounts = []
    for namespace in namespaces:
        namespace_service_accounts = k8s_paginate(
            k8s_client.CoreV1Api.list_namespaced_service_account,
            namespace=namespace,
        )
        service_accounts.extend(namespace_service_accounts)
    return service_accounts


def get_roles(k8s_client, namespaces: List[str]) -> List[V1Role]:
    """
    Get all Roles across specified namespaces.
    """
    roles = []
    for namespace in namespaces:
        namespace_roles = k8s_paginate(
            k8s_client.rbac.list_namespaced_role,
            namespace=namespace,
        )
        roles.extend(namespace_roles)
    return roles


def get_role_bindings(k8s_client, namespaces: List[str]) -> List[V1RoleBinding]:
    """
    Get all RoleBindings across specified namespaces.
    """
    role_bindings = []
    for namespace in namespaces:
        namespace_role_bindings = k8s_paginate(
            k8s_client.rbac.list_namespaced_role_binding,
            namespace=namespace,
        )
        role_bindings.extend(namespace_role_bindings)
    return role_bindings


def transform_service_accounts(service_accounts: List[V1ServiceAccount]) -> List[Dict[str, Any]]:
    """
    Transform Kubernetes ServiceAccounts into a list of dictionaries for Neo4j ingestion.
    """
    result = []
    for sa in service_accounts:
        result.append({
            "id": f"{sa.metadata.namespace}/{sa.metadata.name}",
            "name": sa.metadata.name,
            "namespace": sa.metadata.namespace,
            "uid": sa.metadata.uid,
            "creation_timestamp": get_epoch(sa.metadata.creation_timestamp),
            "resource_version": sa.metadata.resource_version,
        })
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
        
        result.append({
            "id": f"{role.metadata.namespace}/{role.metadata.name}",
            "name": role.metadata.name,
            "namespace": role.metadata.namespace,
            "uid": role.metadata.uid,
            "creation_timestamp": get_epoch(role.metadata.creation_timestamp),
            "resource_version": role.metadata.resource_version,
            "api_groups": all_api_groups,
            "resources": all_resources,
            "verbs": all_verbs,
        })
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
            subject for subject in (rb.subjects or [])
            if subject.kind == "ServiceAccount"
        ]
        
        for subject in service_account_subjects:
            result.append({
                "id": f"{rb.metadata.namespace}/{rb.metadata.name}/{subject.namespace}/{subject.name}",
                "name": rb.metadata.name,
                "namespace": rb.metadata.namespace,
                "uid": rb.metadata.uid,
                "creation_timestamp": get_epoch(rb.metadata.creation_timestamp),
                "resource_version": rb.metadata.resource_version,
                "role_name": rb.role_ref.name,
                "role_kind": rb.role_ref.kind,
                "subject_name": subject.name,
                "subject_namespace": subject.namespace,
            })
    return result 