import logging
from typing import Any

import boto3
import neo4j
import yaml
from botocore.exceptions import ClientError
from kubernetes.client.models import V1ConfigMap

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.groups import KubernetesGroupSchema
from cartography.models.kubernetes.oidc import KubernetesOIDCProviderSchema
from cartography.models.kubernetes.users import KubernetesUserSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_aws_auth_configmap(client: K8sClient) -> V1ConfigMap:
    """
    Get aws-auth ConfigMap from kube-system namespace.
    """
    logger.info(f"Retrieving aws-auth ConfigMap from cluster {client.name}")
    return client.core.read_namespaced_config_map(
        name="aws-auth", namespace="kube-system"
    )


def parse_aws_auth_map(configmap: V1ConfigMap) -> dict[str, list[dict[str, Any]]]:
    """
    Parse mapRoles and mapUsers from aws-auth ConfigMap.

    :param configmap: V1ConfigMap containing aws-auth data
    :return: Dictionary with 'roles' and 'users' keys containing their respective mappings
    """
    result: dict[str, list[dict[str, Any]]] = {"roles": [], "users": []}

    # Parse mapRoles
    if "mapRoles" in configmap.data:
        map_roles_yaml = configmap.data["mapRoles"]
        role_mappings = yaml.safe_load(map_roles_yaml) or []

        # Filter out templated entries for now (https://github.com/cartography-cncf/cartography/issues/1854)
        filtered_role_mappings = []
        for mapping in role_mappings:
            username = mapping.get("username", "")
            if "{{" in username:
                logger.debug(f"Skipping templated username in mapRoles: {username}")
                continue
            filtered_role_mappings.append(mapping)

        result["roles"] = filtered_role_mappings
        logger.info(
            f"Parsed {len(filtered_role_mappings)} role mappings from aws-auth ConfigMap"
        )
    else:
        logger.info("No mapRoles found in aws-auth ConfigMap")

    # Parse mapUsers
    if "mapUsers" in configmap.data:
        map_users_yaml = configmap.data["mapUsers"]
        user_mappings = yaml.safe_load(map_users_yaml) or []

        filtered_user_mappings = []
        for mapping in user_mappings:
            username = mapping.get("username", "")
            if "{{" in username:
                logger.debug(f"Skipping templated username in mapUsers: {username}")
                continue
            filtered_user_mappings.append(mapping)

        result["users"] = filtered_user_mappings
        logger.info(
            f"Parsed {len(filtered_user_mappings)} user mappings from aws-auth ConfigMap"
        )
    else:
        logger.info("No mapUsers found in aws-auth ConfigMap")

    return result


def transform_aws_auth_mappings(
    auth_mappings: dict[str, list[dict[str, Any]]], cluster_name: str
) -> dict[str, list[dict[str, Any]]]:
    """
    Transform both role and user mappings from aws-auth ConfigMap into combined user/group data.
    """
    all_users = []
    all_groups = []

    # Process role mappings if they exist
    if auth_mappings.get("roles"):
        for mapping in auth_mappings.get("roles", []):
            role_arn = mapping.get("rolearn")
            username = mapping.get("username")
            group_names = mapping.get("groups", [])

            if not role_arn:
                continue

            # Create user data with AWS role relationship (only if username is provided)
            if username:
                all_users.append(
                    {
                        "id": f"{cluster_name}/{username}",
                        "name": username,
                        "cluster_name": cluster_name,
                        "aws_role_arn": role_arn,
                    }
                )

            # Create group data with AWS role relationship for each group
            for group_name in group_names:
                all_groups.append(
                    {
                        "id": f"{cluster_name}/{group_name}",
                        "name": group_name,
                        "cluster_name": cluster_name,
                        "aws_role_arn": role_arn,
                    }
                )

    # Process user mappings if they exist
    if auth_mappings.get("users"):
        for mapping in auth_mappings.get("users", []):
            user_arn = mapping.get("userarn")
            username = mapping.get("username")
            group_names = mapping.get("groups", [])

            if not user_arn:
                continue

            # Create user data with AWS user relationship (only if username is provided)
            if username:
                all_users.append(
                    {
                        "id": f"{cluster_name}/{username}",
                        "name": username,
                        "cluster_name": cluster_name,
                        "aws_user_arn": user_arn,
                    }
                )

            # Create group data with AWS user relationship for each group
            for group_name in group_names:
                all_groups.append(
                    {
                        "id": f"{cluster_name}/{group_name}",
                        "name": group_name,
                        "cluster_name": cluster_name,
                        "aws_user_arn": user_arn,
                    }
                )

    # Count entries with vs without usernames for visibility
    role_entries_with_username = sum(
        1 for mapping in auth_mappings.get("roles", []) if mapping.get("username")
    )
    user_entries_with_username = sum(
        1 for mapping in auth_mappings.get("users", []) if mapping.get("username")
    )
    total_entries_with_username = (
        role_entries_with_username + user_entries_with_username
    )
    total_entries = len(auth_mappings.get("roles", [])) + len(
        auth_mappings.get("users", [])
    )
    entries_without_username = total_entries - total_entries_with_username

    logger.info(
        f"Transformed {len(all_users)} users (from {total_entries_with_username} entries with usernames) "
        f"and {len(all_groups)} groups from {len(auth_mappings.get('roles', []))} role mappings "
        f"and {len(auth_mappings.get('users', []))} user mappings "
        f"({entries_without_username} entries without usernames created groups only)"
    )

    return {"users": all_users, "groups": all_groups}


@timeit
@aws_handle_regions
def get_oidc_provider(
    boto3_session: boto3.session.Session,
    region: str,
    cluster_name: str,
) -> list[dict[str, Any]]:
    """
    Get external OIDC identity provider configurations for an EKS cluster.

    Returns raw AWS API responses for configured external identity providers.
    """
    client = boto3_session.client("eks", region_name=region)
    oidc_providers = []

    # Extract just the cluster name from ARN if needed
    # ARN format: arn:aws:eks:region:account:cluster/cluster-name
    if cluster_name.startswith("arn:aws:eks:"):
        cluster_name = cluster_name.split("/")[-1]

    # Get configured external identity provider configs
    configs_response = client.list_identity_provider_configs(clusterName=cluster_name)

    for config in configs_response["identityProviderConfigs"]:
        if config["type"] == "oidc":
            # Get detailed config for this OIDC provider
            detail_response = client.describe_identity_provider_config(
                clusterName=cluster_name,
                identityProviderConfig={"type": "oidc", "name": config["name"]},
            )

            oidc_providers.append(detail_response["identityProviderConfig"]["oidc"])

    return oidc_providers


@timeit
@aws_handle_regions
def get_access_entries(
    boto3_session: boto3.session.Session,
    region: str,
    cluster_name: str,
) -> list[dict[str, Any]]:
    """
    Get EKS Access Entries for a cluster.

    Access Entries are a newer way to grant IAM principals access to EKS clusters,
    providing an alternative to the aws-auth ConfigMap.

    Returns raw AWS API responses for each access entry.
    """
    client = boto3_session.client("eks", region_name=region)
    access_entries = []

    # Extract just the cluster name from ARN if needed
    # ARN format: arn:aws:eks:region:account:cluster/cluster-name
    if cluster_name.startswith("arn:aws:eks:"):
        cluster_name = cluster_name.split("/")[-1]

    paginator = client.get_paginator("list_access_entries")
    page_iterator = paginator.paginate(clusterName=cluster_name)

    # Get detailed information for each access entry
    for page in page_iterator:
        for principal_arn in page.get("accessEntries", []):
            try:
                detail_response = client.describe_access_entry(
                    clusterName=cluster_name, principalArn=principal_arn
                )
                access_entries.append(detail_response["accessEntry"])
            except ClientError as e:
                # If the access entry is not found, we can safely skip it.
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    logger.warning(
                        f"Access entry lookup failed for principal {principal_arn}: {e}"
                    )
                    continue
                # For other errors (e.g. AccessDenied, Throttling), we re-raise to avoid
                # returning partial data which could cause destructive cleanup.
                raise

    logger.info(
        f"Retrieved {len(access_entries)} access entries for cluster {cluster_name}"
    )
    return access_entries


def transform_oidc_provider(
    oidc_providers: list[dict[str, Any]],
    cluster_name: str,
) -> list[dict[str, Any]]:
    """
    Transform raw AWS OIDC provider data into standardized format.

    Takes raw AWS API responses and creates OIDC provider nodes that match
    the KubernetesOIDCProvider data model for infrastructure metadata.
    """
    transformed_providers = []

    for provider in oidc_providers:
        # Extract fields from raw AWS API response
        provider_name = provider["identityProviderConfigName"]
        issuer_url = provider["issuerUrl"]

        # Create a unique ID for the external OIDC provider
        # Format: cluster_name/oidc/provider_name
        provider_id = f"{cluster_name}/oidc/{provider_name}"

        transformed_provider = {
            "id": provider_id,
            "issuer_url": issuer_url,
            "cluster_name": cluster_name,
            "k8s_platform": "eks",
            "client_id": provider.get("clientId", ""),
            "status": provider.get("status", "UNKNOWN"),
            "name": provider_name,
        }

        transformed_providers.append(transformed_provider)

    return transformed_providers


def transform_access_entries(
    access_entries: list[dict[str, Any]], cluster_name: str
) -> dict[str, list[dict[str, Any]]]:
    """
    Transform EKS Access Entries into KubernetesUser and KubernetesGroup data.

    Access Entries map IAM principals (users or roles) to Kubernetes users and groups.
    Each access entry has:
    - principalArn: The IAM principal (user or role) ARN
    - username is populated by AWS. When no explicit username is configured, AWS sets it to the principal ARN.
    - kubernetesGroups: List of Kubernetes groups the user belongs to

    Returns a dictionary with 'users' and 'groups' keys containing transformed data.
    """
    all_users = []
    all_groups = []

    for entry in access_entries:
        principal_arn = entry["principalArn"]
        username = entry["username"]
        group_names = entry.get("kubernetesGroups", [])

        is_role = ":role/" in principal_arn
        is_user = ":user/" in principal_arn

        user_data = {
            "id": f"{cluster_name}/{username}",
            "name": username,
            "cluster_name": cluster_name,
        }

        # Add AWS relationship based on principal type
        if is_role:
            user_data["aws_role_arn"] = principal_arn
        elif is_user:
            user_data["aws_user_arn"] = principal_arn

        all_users.append(user_data)

        # Create group data for each Kubernetes group
        for group_name in group_names:
            group_data = {
                "id": f"{cluster_name}/{group_name}",
                "name": group_name,
                "cluster_name": cluster_name,
            }

            # Add AWS relationship based on principal type
            if is_role:
                group_data["aws_role_arn"] = principal_arn
            elif is_user:
                group_data["aws_user_arn"] = principal_arn

            all_groups.append(group_data)

    logger.info(
        f"Transformed {len(all_users)} users and {len(all_groups)} groups from {len(access_entries)} access entries"
    )

    return {"users": all_users, "groups": all_groups}


def load_oidc_provider(
    neo4j_session: neo4j.Session,
    oidc_providers: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    """
    Load OIDC providers and their relationships to users and groups into Neo4j.
    """
    logger.info(f"Loading {len(oidc_providers)} EKS OIDC providers")
    load(
        neo4j_session,
        KubernetesOIDCProviderSchema(),
        oidc_providers,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


def load_aws_auth_mappings(
    neo4j_session: neo4j.Session,
    users: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    """
    Load Kubernetes Users/Groups with AWS Role and User relationships into Neo4j using schema-based loading.
    """
    logger.info(f"Loading {len(users)} Kubernetes Users with AWS mappings")

    if users:
        load(
            neo4j_session,
            KubernetesUserSchema(),
            users,
            lastupdated=update_tag,
            CLUSTER_ID=cluster_id,
            CLUSTER_NAME=cluster_name,
        )

    logger.info(f"Loading {len(groups)} Kubernetes Groups with AWS mappings")

    if groups:
        load(
            neo4j_session,
            KubernetesGroupSchema(),
            groups,
            lastupdated=update_tag,
            CLUSTER_ID=cluster_id,
            CLUSTER_NAME=cluster_name,
        )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    logger.debug("Running cleanup job for EKS AWS Role and User relationships")

    cleanup_job = GraphJob.from_node_schema(
        KubernetesUserSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)

    cleanup_job = GraphJob.from_node_schema(
        KubernetesGroupSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)


def sync(
    neo4j_session: neo4j.Session,
    k8s_client: K8sClient,
    boto3_session: boto3.session.Session,
    region: str,
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    """
    Sync EKS identity providers:
    1. AWS IAM role and user mappings (aws-auth ConfigMap)
    2. EKS Access Entries (EKS API)
    3. External OIDC providers (EKS API)
    """
    logger.info(f"Starting EKS identity provider sync for cluster {cluster_name}")

    # 1. Sync AWS IAM mappings (aws-auth ConfigMap)
    logger.info("Syncing AWS IAM mappings from aws-auth ConfigMap")
    configmap = get_aws_auth_configmap(k8s_client)
    auth_mappings = parse_aws_auth_map(configmap)

    # Transform and load both role and user mappings
    if auth_mappings.get("roles") or auth_mappings.get("users"):
        transformed_data = transform_aws_auth_mappings(auth_mappings, cluster_name)
        load_aws_auth_mappings(
            neo4j_session,
            transformed_data["users"],
            transformed_data["groups"],
            update_tag,
            cluster_id,
            cluster_name,
        )
        logger.info(
            f"Successfully synced {len(auth_mappings.get('roles', []))} AWS IAM role mappings "
            f"and {len(auth_mappings.get('users', []))} AWS IAM user mappings"
        )
    else:
        logger.info("No role or user mappings found in aws-auth ConfigMap")

    # 2. Sync EKS Access Entries (EKS API)
    logger.info("Syncing EKS Access Entries from EKS API")

    # Get access entries from EKS API
    access_entries = get_access_entries(boto3_session, region, cluster_name)

    if access_entries:
        # Transform access entries into users and groups
        transformed_access_entries = transform_access_entries(
            access_entries, cluster_name
        )

        # Load users and groups from access entries
        load_aws_auth_mappings(
            neo4j_session,
            transformed_access_entries["users"],
            transformed_access_entries["groups"],
            update_tag,
            cluster_id,
            cluster_name,
        )
        logger.info(f"Successfully synced {len(access_entries)} EKS Access Entries")
    else:
        logger.info("No EKS Access Entries found for cluster")

    # 3. Sync External OIDC providers (EKS API)
    logger.info("Syncing external OIDC providers from EKS API")

    # Get OIDC providers from EKS API
    oidc_provider = get_oidc_provider(boto3_session, region, cluster_name)

    if oidc_provider:
        # Transform OIDC providers (infrastructure metadata only)
        transformed_oidc_provider = transform_oidc_provider(oidc_provider, cluster_name)

        # Load OIDC providers
        load_oidc_provider(
            neo4j_session,
            transformed_oidc_provider,
            update_tag,
            cluster_id,
            cluster_name,
        )
        logger.info(f"Successfully synced {len(oidc_provider)} external OIDC provider")
    else:
        logger.info("No external OIDC provider found for cluster")

    # Cleanup
    common_job_parameters = {
        "UPDATE_TAG": update_tag,
        "CLUSTER_ID": cluster_id,
    }
    cleanup(neo4j_session, common_job_parameters)

    logger.info(
        f"Successfully completed EKS identity provider sync for cluster {cluster_name}"
    )
