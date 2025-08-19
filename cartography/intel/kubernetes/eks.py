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


def parse_role_mappings(configmap: V1ConfigMap) -> List[Dict[str, Any]]:
    """
    Parse mapRoles from aws-auth ConfigMap.

    :param configmap: V1ConfigMap containing aws-auth data
    :return: List of role mapping dictionaries
    """
    map_roles_yaml = configmap.data["mapRoles"]
    role_mappings = yaml.safe_load(map_roles_yaml) or []

    # Filter out templated entries because these are not real users
    filtered_mappings = []
    for mapping in role_mappings:
        username = mapping.get("username", "")
        if "{{" in username:
            logger.debug(f"Skipping templated username: {username}")
            continue
        filtered_mappings.append(mapping)

    logger.info(
        f"Parsed {len(filtered_mappings)} role mappings from aws-auth ConfigMap"
    )
    return filtered_mappings


def transform_aws_role_mappings(
    role_mappings: List[Dict[str, Any]], cluster_name: str
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Transform role mappings into user/group data with AWS role relationships.
    """
    users = []
    groups = []

    for mapping in role_mappings:
        role_arn = mapping.get("rolearn")
        username = mapping.get("username")
        group_names = mapping.get("groups", [])

        if not role_arn:
            continue

        # Create user data with AWS role relationship if present
        if username:
            users.append(
                {
                    "id": f"{cluster_name}/{username}",
                    "name": username,
                    "cluster_name": cluster_name,
                    "aws_role_arn": role_arn,  # For the AWS Role relationship
                }
            )

        # Create group data with AWS role relationship for each group
        for group_name in group_names:
            groups.append(
                {
                    "id": f"{cluster_name}/{group_name}",
                    "name": group_name,
                    "cluster_name": cluster_name,
                    "aws_role_arn": role_arn,  # For the AWS Role relationship
                }
            )

    logger.info(
        f"Transformed {len(users)} users and {len(groups)} groups with AWS role mappings"
    )

    return {"users": users, "groups": groups}


@timeit
def get_oidc_providers(
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


def transform_oidc_providers(
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
            "arn": provider.get("identityProviderConfigArn", ""),
        }

        transformed_providers.append(transformed_provider)

    return transformed_providers


def load_oidc_providers(
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


def load_aws_role_mappings(
    neo4j_session: neo4j.Session,
    users: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    """
    Load Kubernetes Users/Groups with AWS Role relationships into Neo4j using schema-based loading.
    """
    logger.info(f"Loading {len(users)} Kubernetes Users with AWS Role mappings")

    # Load Kubernetes Users with AWS Role relationships
    if users:
        load(
            neo4j_session,
            KubernetesUserSchema(),
            users,
            lastupdated=update_tag,
            CLUSTER_ID=cluster_id,
            CLUSTER_NAME=cluster_name,
        )

    logger.info(f"Loading {len(groups)} Kubernetes Groups with AWS Role mappings")

    # Load Kubernetes Groups with AWS Role relationships
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
    logger.debug("Running cleanup job for EKS AWS Role relationships")

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
    1. AWS IAM role mappings (aws-auth ConfigMap)
    2. External OIDC providers (EKS API)
    """
    logger.info(f"Starting EKS identity provider sync for cluster {cluster_name}")

    # 1. Sync AWS IAM role mappings (aws-auth ConfigMap)
    logger.info("Syncing AWS IAM role mappings from aws-auth ConfigMap")
    configmap = get_aws_auth_configmap(k8s_client)
    role_mappings = parse_role_mappings(configmap)

    if role_mappings:
        transformed_data = transform_aws_role_mappings(role_mappings, cluster_name)
        load_aws_role_mappings(
            neo4j_session,
            transformed_data["users"],
            transformed_data["groups"],
            update_tag,
            cluster_id,
            cluster_name,
        )
        logger.info(f"Successfully synced {len(role_mappings)} AWS IAM role mappings")
    else:
        logger.info("No role mappings found in aws-auth ConfigMap")

    # 2. Sync External OIDC providers (EKS API)
    logger.info("Syncing external OIDC providers from EKS API")

    # Get OIDC providers from EKS API
    oidc_providers = get_oidc_providers(boto3_session, region, cluster_name)

    if oidc_providers:
        # Transform OIDC providers (infrastructure metadata only)
        transformed_oidc_providers = transform_oidc_providers(
            oidc_providers, cluster_name
        )

        # Load OIDC providers
        load_oidc_providers(
            neo4j_session,
            transformed_oidc_providers,
            update_tag,
            cluster_id,
            cluster_name,
        )
        logger.info(
            f"Successfully synced {len(oidc_providers)} external OIDC providers"
        )
    else:
        logger.info("No external OIDC providers found for cluster")

    # Cleanup
    common_job_parameters = {
        "UPDATE_TAG": update_tag,
        "CLUSTER_ID": cluster_id,
    }
    cleanup(neo4j_session, common_job_parameters)

    logger.info(
        f"Successfully completed EKS identity provider sync for cluster {cluster_name}"
    )
