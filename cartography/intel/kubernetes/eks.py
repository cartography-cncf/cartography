import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j
import yaml
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


def parse_aws_auth_map(configmap: V1ConfigMap) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parse mapRoles and mapUsers from aws-auth ConfigMap.

    :param configmap: V1ConfigMap containing aws-auth data
    :return: Dictionary with 'roles' and 'users' keys containing their respective mappings
    """
    result: Dict[str, List[Dict[str, Any]]] = {"roles": [], "users": []}

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
    auth_mappings: Dict[str, List[Dict[str, Any]]], cluster_name: str
) -> Dict[str, List[Dict[str, Any]]]:
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
) -> List[Dict[str, Any]]:
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


def transform_oidc_provider(
    oidc_providers: List[Dict[str, Any]],
    cluster_name: str,
) -> List[Dict[str, Any]]:
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


def load_oidc_provider(
    neo4j_session: neo4j.Session,
    oidc_providers: List[Dict[str, Any]],
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
    users: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    """
    Load Kubernetes Users/Groups with AWS Role and User relationships into Neo4j using schema-based loading.
    """
    logger.info(f"Loading {len(users)} Kubernetes Users with AWS mappings")

    # Load Kubernetes Users with AWS relationships
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

    # Load Kubernetes Groups with AWS relationships
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
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
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
    2. External OIDC providers (EKS API)
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

    # 2. Sync External OIDC providers (EKS API)
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
